#!/usr/bin/env python3
"""Validate completed five-marker MAFFT/IQ-TREE/ASTRAL pilot artifacts.

This validator reads the project and pilot outputs only. It refuses an incomplete
pilot before creating its fresh output directory. On success it preserves the raw
ASTRAL tree and writes a derived Newick whose numeric internal labels are ASTRAL
q1 quartet frequencies, plus one TSV row per unrooted informative split.

The project Stage 6 Newick parser is imported from scripts/master_run/stage06_render.py.
That module was inspected: it imports only the Python standard library at module
load and calls its renderer only behind the __main__ guard.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path


EXPECTED_MARKERS = 5
EXPECTED_TAXA = 196
ASTRAL_VERSION = "5.7.8"
REL_TOL = 1e-8
ABS_TOL = 1e-8
ASTRAL_SUM_TOL = 0.0011  # Embedded ASTRAL 5.7.8 source adjusts EN when |sum(f)-EN| > 0.001.
NUM = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
ANNOTATION_RE = re.compile(
    rf"\[q1=(?P<q1>{NUM});q2=(?P<q2>{NUM});q3=(?P<q3>{NUM})"
    rf";f1=(?P<f1>{NUM});f2=(?P<f2>{NUM});f3=(?P<f3>{NUM})"
    rf";pp1=(?P<pp1>{NUM});pp2=(?P<pp2>{NUM});pp3=(?P<pp3>{NUM})"
    rf";QC=(?P<qc>\d+);EN=(?P<en>{NUM})\]"
)
QUOTED_ANNOTATION_RE = re.compile(r"'(?P<label>\[q1=[^']+\])'")
ACCESSION_RE = re.compile(r"GCF_\d+\.\d+\Z")
IQTREE_COMPLETION_RE = re.compile(r"Analysis results written to\s*:", re.IGNORECASE)
IQTREE_SUPPORT_RE = re.compile(rf"{NUM}(?:/{NUM})*\Z")


class ValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def relative_name(path: Path, project: Path) -> str:
    try:
        return path.relative_to(project).as_posix()
    except ValueError:
        return str(path)


def load_project_newick(project: Path):
    parser_path = project / "scripts" / "master_run" / "stage06_render.py"
    require(parser_path.is_file(), f"Project Newick parser is missing: {parser_path}")
    spec = importlib.util.spec_from_file_location("lab_rm_stage06_render_for_pilot", parser_path)
    require(spec is not None and spec.loader is not None, "Could not load project Newick parser")
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves the defining module through sys.modules during import.
    sys.modules[spec.name] = module
    write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = write_bytecode
    require(hasattr(module, "Newick") and hasattr(module, "nodes"),
            "Project Newick parser does not expose Newick and nodes")
    return module


def parse_fasta(path: Path) -> dict[str, str]:
    require(path.is_file(), f"Missing FASTA: {path}")
    records: dict[str, list[str]] = {}
    current: str | None = None
    with path.open("r", encoding="utf-8-sig", newline=None) as stream:
        for line_number, raw in enumerate(stream, 1):
            line = raw.strip()
            if not line:
                continue
            if line.startswith(">"):
                header = line[1:].strip()
                require(bool(header), f"Empty FASTA header at {path}:{line_number}")
                key = header.split()[0]
                require(bool(ACCESSION_RE.fullmatch(key)),
                        f"FASTA header is not an exact versioned GCF accession at {path}:{line_number}: {header!r}")
                require(key not in records, f"Duplicate FASTA tip {key} in {path}")
                records[key] = []
                current = key
            else:
                require(current is not None, f"Sequence before first FASTA header at {path}:{line_number}")
                require(not any(ch.isspace() for ch in line),
                        f"Whitespace inside FASTA sequence at {path}:{line_number}")
                records[current].append(line)
    require(records, f"FASTA has no records: {path}")
    result: dict[str, str] = {}
    for key, chunks in records.items():
        sequence = "".join(chunks)
        require(sequence, f"Empty FASTA sequence for {key} in {path}")
        result[key] = sequence
    return result


def normalized_ungapped(sequence: str) -> str:
    return sequence.replace("-", "").replace(".", "").upper()


def load_approved(project: Path) -> tuple[list[str], Path]:
    path = project / "config" / "approved_accessions.txt"
    require(path.is_file(), f"Approved accession list is missing: {path}")
    values = [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    require(len(values) == EXPECTED_TAXA, f"Approved accession list has {len(values)} rows; expected {EXPECTED_TAXA}")
    require(len(set(values)) == len(values), "Approved accession list contains duplicates")
    require(all(ACCESSION_RE.fullmatch(value) for value in values),
            "Approved accession list must contain exact versioned GCF accessions")
    return values, path


def marker_inputs(project: Path) -> list[Path]:
    paths = sorted((project / "input_genes").glob("*.fasta"), key=lambda path: path.name)
    require(len(paths) == EXPECTED_MARKERS,
            f"Expected exactly {EXPECTED_MARKERS} pilot FASTAs; found {len(paths)}")
    return paths


def load_parser_tree(parser_module, path: Path):
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValidationError(f"Newick is not UTF-8: {path}: {error}") from error
    try:
        root = parser_module.Newick(text).parse()
    except (ValueError, TypeError) as error:
        raise ValidationError(f"Invalid Newick in {path}: {error}") from error
    return root, text, raw


def tree_walk(root):
    """Yield (node, child-index path, descendant-tip set) in preorder."""
    found = []

    def visit(node, path):
        if not node.children:
            desc = {node.label}
        else:
            desc = set()
            for index, child in enumerate(node.children):
                desc.update(visit(child, path + (index,)))
        node.descendants = sorted(desc)
        found.append((node, path, desc))
        return desc

    all_tips = visit(root, ())
    return found, all_tips


def path_text(path: tuple[int, ...]) -> str:
    return "root" if not path else "root/" + "/".join(str(part) for part in path)


def canonical_split(descendants: set[str], all_tips: set[str]):
    left = tuple(sorted(descendants))
    right = tuple(sorted(all_tips - descendants))
    sides = sorted((left, right), key=lambda side: (len(side), side))
    return sides[0], sides[1]


def split_id(split) -> str:
    payload = json.dumps([list(split[0]), list(split[1])], ensure_ascii=True,
                         separators=(",", ":")).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def parse_astral_annotation(label: str) -> dict | None:
    if not label:
        return None
    match = ANNOTATION_RE.fullmatch(label)
    if match is None:
        return None
    raw = match.groupdict()
    data = {key: float(raw[key]) for key in ("q1", "q2", "q3", "f1", "f2", "f3",
                                               "pp1", "pp2", "pp3", "en")}
    data["qc"] = int(raw["qc"])
    data["raw_q1"] = raw["q1"]
    return data


def close(left: float, right: float, abs_tol: float = ABS_TOL, rel_tol: float = REL_TOL) -> bool:
    return math.isclose(left, right, abs_tol=abs_tol, rel_tol=rel_tol)


def validate_annotation(data: dict, where: str) -> None:
    for key in ("q1", "q2", "q3", "pp1", "pp2", "pp3", "f1", "f2", "f3", "en"):
        require(math.isfinite(data[key]), f"Nonfinite ASTRAL {key} at {where}")
    for key in ("q1", "q2", "q3", "pp1", "pp2", "pp3"):
        require(-ABS_TOL <= data[key] <= 1 + ABS_TOL,
                f"ASTRAL {key} is outside [0,1] at {where}: {data[key]}")
    for key in ("f1", "f2", "f3"):
        require(data[key] >= -ABS_TOL, f"Negative ASTRAL {key} at {where}")
    require(data["en"] > 0, f"ASTRAL effective number of genes EN is not positive at {where}")
    require(data["qc"] >= 0, f"Negative ASTRAL quartet count QC at {where}")
    frequencies = ("q1", "q2", "q3")
    counts = ("f1", "f2", "f3")
    for q_key, f_key in zip(frequencies, counts):
        expected = data[f_key] / data["en"]
        require(close(data[q_key], expected, abs_tol=5e-9, rel_tol=5e-9),
                f"ASTRAL {q_key} != {f_key}/EN at {where}")
    f_total = data["f1"] + data["f2"] + data["f3"]
    require(abs(f_total - data["en"]) <= ASTRAL_SUM_TOL + 1e-10 * max(1.0, data["en"]),
            f"ASTRAL f1+f2+f3 differs from EN beyond ASTRAL 5.7.8 tolerance at {where}")
    q_total = data["q1"] + data["q2"] + data["q3"]
    require(close(q_total, f_total / data["en"], abs_tol=5e-9, rel_tol=5e-9),
            f"ASTRAL q1+q2+q3 differs from (f1+f2+f3)/EN at {where}")


def annotations_consistent(left: dict, right: dict) -> bool:
    for key in ("q1", "f1", "pp1", "en"):
        if not close(left[key], right[key]):
            return False
    if left["qc"] != right["qc"]:
        return False
    direct = all(close(left[a], right[b]) for a, b in
                 (("q2", "q2"), ("q3", "q3"), ("f2", "f2"), ("f3", "f3"),
                  ("pp2", "pp2"), ("pp3", "pp3")))
    swapped = all(close(left[a], right[b]) for a, b in
                  (("q2", "q3"), ("q3", "q2"), ("f2", "f3"), ("f3", "f2"),
                   ("pp2", "pp3"), ("pp3", "pp2")))
    return direct or swapped


def validate_astral_tree(parser_module, tree_path: Path, approved: set[str], text_override: str | None = None):
    if text_override is None:
        root, text, raw = load_parser_tree(parser_module, tree_path)
    else:
        root, text, raw = load_parser_tree_from_text(parser_module, text_override, tree_path)
    walked, all_tips = tree_walk(root)
    require(all_tips == approved, _tip_mismatch_message("ASTRAL species tree", all_tips, approved))
    leaf_count = sum(not node.children for node, _, _ in walked)
    require(leaf_count == len(all_tips), f"ASTRAL tree has duplicate tips: leaves={leaf_count}, unique={len(all_tips)}")
    require(len(all_tips) == len(approved),
            f"ASTRAL tree has {len(all_tips)} unique tips; expected {len(approved)}")

    for node, path, _ in walked:
        if node.length is not None:
            require(math.isfinite(node.length) and node.length >= 0,
                    f"ASTRAL branch length is nonfinite or negative at {path_text(path)}")

    all_annotations = []
    by_split = defaultdict(list)
    required_splits = {}
    for node, path, descendants in walked:
        if not node.children:
            continue
        if node is root:
            data = parse_astral_annotation(node.label)
            if data is not None:
                validate_annotation(data, "root")
                all_annotations.append((node, path, None, data))
            continue
        complement = all_tips - descendants
        split = canonical_split(descendants, all_tips)
        nontrivial = len(descendants) >= 2 and len(complement) >= 2
        data = parse_astral_annotation(node.label)
        if not nontrivial:
            require(data is None, f"Unexpected ASTRAL support annotation on a trivial split at {path_text(path)}")
            require(not node.label, f"Unexpected nonnumeric internal label on a trivial split at {path_text(path)}")
            continue
        required_splits[split] = True
        require(data is not None, f"Missing structured ASTRAL -t 2 annotation on informative split at {path_text(path)}")
        validate_annotation(data, path_text(path))
        require(node.length is not None, f"Annotated ASTRAL internal branch has no branch length at {path_text(path)}")
        by_split[split].append((node, path, data))
        all_annotations.append((node, path, split, data))

    missing_splits = [split for split in required_splits if not by_split.get(split)]
    require(not missing_splits, f"ASTRAL annotations missing for {len(missing_splits)} informative splits")
    for split, records in by_split.items():
        first = records[0][2]
        for _, path, data in records[1:]:
            require(annotations_consistent(first, data),
                    f"Duplicated root representation has inconsistent annotations at {path_text(path)}")

    derived_text, replacements = derive_q1_tree(text)
    expected_replacements = sum(1 for _, _, _, data in all_annotations if data is not None)
    require(replacements == expected_replacements,
            f"Could not convert every structured annotation to q1 labels ({replacements}/{expected_replacements})")
    derived_root, _, _ = load_parser_tree_from_text(parser_module, derived_text, tree_path)
    derived_walk, derived_tips = tree_walk(derived_root)
    require(derived_tips == all_tips, "Derived iTOL tree changed the ASTRAL tip set")
    require(_topology_length_signature(root) == _topology_length_signature(derived_root),
            "Derived iTOL tree changed topology or branch lengths")

    rows = []
    for split, records in sorted(by_split.items(), key=lambda item: item[0]):
        node, path, data = records[0]
        rows.append({
            "split_id_sha256": split_id(split),
            "side_a_accessions_json": json.dumps(list(split[0]), separators=(",", ":")),
            "side_b_accessions_json": json.dumps(list(split[1]), separators=(",", ":")),
            "representative_tree_node": path_text(path),
            "all_tree_nodes_json": json.dumps([path_text(record[1]) for record in records], separators=(",", ":")),
            "branch_lengths_by_tree_node_json": json.dumps(
                [{"node": path_text(record[1]), "length_coalescent_units": record[0].length} for record in records],
                separators=(",", ":")),
            "q1_quartet_frequency": repr(data["q1"]),
            "q2_alternative_quartet_frequency": repr(data["q2"]),
            "q3_alternative_quartet_frequency": repr(data["q3"]),
            "f1_quartet_frequency_mass": repr(data["f1"]),
            "f2_alternative_quartet_frequency_mass": repr(data["f2"]),
            "f3_alternative_quartet_frequency_mass": repr(data["f3"]),
            "pp1_local_posterior_probability": repr(data["pp1"]),
            "pp2_alternative_local_posterior_probability": repr(data["pp2"]),
            "pp3_alternative_local_posterior_probability": repr(data["pp3"]),
            "QC_total_quartets_around_branch": str(data["qc"]),
            "EN_effective_number_of_genes": repr(data["en"]),
        })

    lengths = [node.length for node, _, _ in walked if node.length is not None]
    return {
        "root": root,
        "raw_text": text,
        "raw_bytes": raw,
        "derived_text": derived_text,
        "support_rows": rows,
        "summary": {
            "tip_count": len(all_tips),
            "internal_node_count_including_root": sum(bool(node.children) for node, _, _ in walked),
            "annotated_node_count_including_root": len(all_annotations),
            "informative_unrooted_split_count": len(required_splits),
            "annotated_informative_split_count": len(by_split),
            "root_annotated": parse_astral_annotation(root.label) is not None,
            "branch_length_count": len(lengths),
            "branch_length_missing_count": sum(node.length is None for node, _, _ in walked),
            "branch_length_min": min(lengths) if lengths else None,
            "branch_length_max": max(lengths) if lengths else None,
        },
    }


def load_parser_tree_from_text(parser_module, text: str, source_path: Path):
    try:
        root = parser_module.Newick(text).parse()
    except (ValueError, TypeError) as error:
        raise ValidationError(f"Derived Newick is invalid (from {source_path}): {error}") from error
    return root, text, text.encode("utf-8")


def derive_q1_tree(text: str) -> tuple[str, int]:
    replacements = 0

    def replace(match):
        nonlocal replacements
        label = match.group("label")
        parsed = parse_astral_annotation(label)
        require(parsed is not None, "Malformed quoted ASTRAL annotation in source Newick")
        validate_annotation(parsed, "quoted Newick label")
        replacements += 1
        return parsed["raw_q1"]

    derived, count = QUOTED_ANNOTATION_RE.subn(replace, text)
    require(count == replacements, "ASTRAL label replacement count is inconsistent")
    return derived, replacements


def _topology_length_signature(root):
    if not root.children:
        return ("leaf", root.label, root.length)
    return ("node", tuple(_topology_length_signature(child) for child in root.children), root.length)


def _tip_mismatch_message(label: str, observed: set[str], expected: set[str]) -> str:
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    return (f"{label} accession set differs from approved panel; tips={len(observed)}, expected={len(expected)}, "
            f"missing={missing[:5]}, extra={extra[:5]}")


def check_tree_lengths(root, path: Path, require_all_edges: bool) -> None:
    walked, _ = tree_walk(root)
    for node, node_path, _ in walked:
        if node is root:
            continue
        require(node.length is not None or not require_all_edges,
                f"Missing branch length in {path} at {path_text(node_path)}")
        if node.length is not None:
            require(math.isfinite(node.length) and node.length >= 0,
                    f"Nonfinite or negative branch length in {path} at {path_text(node_path)}")


def validate_iqtree_support(root, path: Path) -> dict:
    walked, _ = tree_walk(root)
    supports = []
    for node, node_path, _ in walked:
        if not node.children or node is root:
            continue
        label = node.label.strip()
        require(bool(label), f"Missing IQ-TREE internal support label in {path} at {path_text(node_path)}")
        require(IQTREE_SUPPORT_RE.fullmatch(label) is not None,
                f"Unsupported IQ-TREE support label in {path} at {path_text(node_path)}: {label!r}")
        values = [float(value) for value in label.split("/")]
        require(all(math.isfinite(value) and 0 <= value <= 100 for value in values),
                f"IQ-TREE support outside [0,100] in {path} at {path_text(node_path)}: {label!r}")
        supports.extend(values)
    require(supports, f"No internal IQ-TREE support values found in {path}")
    return {"support_component_count": len(supports), "support_min": min(supports), "support_max": max(supports)}


def validate_marker_files(parser_module, project: Path, approved_order: list[str], approved: set[str]):
    inputs = marker_inputs(project)
    pilot = project / "pilot_output"
    align_dir = pilot / "alignments"
    tree_dir = pilot / "trees"
    reports = project / "reports" / "stage01"
    aggregate_iqtree = reports / "pilot_iqtree.log"
    mafft_log = reports / "pilot_mafft.log"
    astral_log = reports / "pilot_astral.log"
    require(aggregate_iqtree.is_file(), f"Missing aggregate IQ-TREE log: {aggregate_iqtree}")
    require(mafft_log.is_file(), f"Missing MAFFT log: {mafft_log}")
    require(astral_log.is_file(), f"Missing ASTRAL log: {astral_log}")

    aggregate_text = aggregate_iqtree.read_text(encoding="utf-8-sig", errors="replace")
    completion_count = len(IQTREE_COMPLETION_RE.findall(aggregate_text))
    require(completion_count >= EXPECTED_MARKERS,
            f"Aggregate IQ-TREE log has {completion_count} completion records; expected at least {EXPECTED_MARKERS}")
    astral_text = astral_log.read_text(encoding="utf-8-sig", errors="replace")
    require(f"ASTRAL version {ASTRAL_VERSION}" in astral_text,
            f"ASTRAL log does not identify the expected local version {ASTRAL_VERSION}")
    require(re.search(r"(?im)^\s*(?:Error:|Exception in thread)", astral_text) is None,
            "ASTRAL log contains a fatal Error/exception marker")

    marker_reports = []
    gene_tree_bytes = []
    union_tips: set[str] = set()
    source_hashes: dict[str, str] = {}
    marker_summaries = []
    for fasta_path in inputs:
        marker = fasta_path.stem
        input_records = parse_fasta(fasta_path)
        input_ids = set(input_records)
        require(input_ids <= approved,
                f"Input marker {marker} has accessions outside the approved panel: {sorted(input_ids-approved)[:5]}")
        aligned_path = align_dir / f"{marker}_aligned.fasta"
        aligned_records = parse_fasta(aligned_path)
        aligned_ids = set(aligned_records)
        require(aligned_ids == input_ids,
                _tip_mismatch_message(f"Aligned FASTA {aligned_path}", aligned_ids, input_ids))
        aligned_lengths = {len(sequence) for sequence in aligned_records.values()}
        require(len(aligned_lengths) == 1,
                f"Aligned FASTA sequences have unequal column counts for {marker}")
        for accession, original in input_records.items():
            require("-" not in original and "." not in original,
                    f"Ungapped input FASTA contains gap symbols for {marker}/{accession}")
            require(normalized_ungapped(original) == normalized_ungapped(aligned_records[accession]),
                    f"Aligned ungapped sequence differs from input for {marker}/{accession}")

        tree_path = tree_dir / f"{marker}.treefile"
        tree_log = tree_dir / f"{marker}.log"
        iqtree_report = tree_dir / f"{marker}.iqtree"
        require(tree_log.is_file() and tree_log.stat().st_size > 0,
                f"Missing/empty IQ-TREE native log: {tree_log}")
        require(iqtree_report.is_file() and iqtree_report.stat().st_size > 0,
                f"Missing/empty IQ-TREE report: {iqtree_report}")
        local_log_text = tree_log.read_text(encoding="utf-8-sig", errors="replace")
        report_text = iqtree_report.read_text(encoding="utf-8-sig", errors="replace")
        require(IQTREE_COMPLETION_RE.search(local_log_text + "\n" + report_text) is not None,
                f"No IQ-TREE successful completion marker for marker {marker}")

        tree_root, _, tree_bytes = load_parser_tree(parser_module, tree_path)
        tree_walked, tree_tips = tree_walk(tree_root)
        tree_leaf_count = sum(not node.children for node, _, _ in tree_walked)
        require(tree_leaf_count == len(tree_tips), f"IQ-TREE tree has duplicate tips for {marker}")
        require(tree_tips == input_ids,
                _tip_mismatch_message(f"IQ-TREE tree {tree_path}", tree_tips, input_ids))
        require(len(tree_tips) == len(input_ids), f"IQ-TREE tree has duplicate tips for {marker}")
        check_tree_lengths(tree_root, tree_path, require_all_edges=True)
        support_summary = validate_iqtree_support(tree_root, tree_path)
        gene_tree_bytes.append(tree_bytes)
        union_tips.update(input_ids)
        marker_summaries.append({
            "marker": marker,
            "input_fasta": relative_name(fasta_path, project),
            "tip_count": len(input_ids),
            "aligned_columns": next(iter(aligned_lengths)),
            "iqtree_tree_tip_count": len(tree_tips),
            "iqtree_internal_support": support_summary,
            "iqtree_log": relative_name(tree_log, project),
        })
        for path in (fasta_path, aligned_path, tree_path, tree_log, iqtree_report):
            source_hashes[relative_name(path, project)] = sha256_file(path)

    require(union_tips == approved,
            _tip_mismatch_message("Union of five pilot marker FASTAs", union_tips, approved))
    require(len(gene_tree_bytes) == EXPECTED_MARKERS, "Did not validate exactly five IQ-TREE gene trees")
    concatenated_path = pilot / "all_gene_trees.tre"
    require(concatenated_path.is_file(), f"Missing concatenated pilot gene trees: {concatenated_path}")
    expected_concat = b"".join(gene_tree_bytes)
    observed_concat = concatenated_path.read_bytes()
    require(observed_concat == expected_concat,
            "all_gene_trees.tre is not the exact byte concatenation of the five validated .treefile inputs")
    source_hashes[relative_name(concatenated_path, project)] = sha256_bytes(observed_concat)
    for path in (aggregate_iqtree, mafft_log, astral_log):
        source_hashes[relative_name(path, project)] = sha256_file(path)
    source_hashes[relative_name(project / "run_pipeline.sh", project)] = sha256_file(project / "run_pipeline.sh")
    source_hashes[relative_name(project / "scripts" / "master_run" / "stage06_render.py", project)] = sha256_file(
        project / "scripts" / "master_run" / "stage06_render.py")
    source_hashes[relative_name(project / "config" / "approved_accessions.txt", project)] = sha256_file(
        project / "config" / "approved_accessions.txt")
    return marker_summaries, source_hashes, astral_log


def write_support_tsv(rows: list[dict]) -> bytes:
    fields = [
        "split_id_sha256", "side_a_accessions_json", "side_b_accessions_json",
        "representative_tree_node", "all_tree_nodes_json", "branch_lengths_by_tree_node_json",
        "q1_quartet_frequency", "q2_alternative_quartet_frequency", "q3_alternative_quartet_frequency",
        "f1_quartet_frequency_mass", "f2_alternative_quartet_frequency_mass", "f3_alternative_quartet_frequency_mass",
        "pp1_local_posterior_probability", "pp2_alternative_local_posterior_probability",
        "pp3_alternative_local_posterior_probability", "QC_total_quartets_around_branch",
        "EN_effective_number_of_genes",
    ]
    from io import StringIO
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def build_validation(project: Path, output: Path):
    project = project.resolve(strict=True)
    output = output.resolve(strict=False)
    require(project.is_dir(), f"Project path is not a directory: {project}")
    require(not output.exists() and not output.is_symlink(), f"Output path must be a fresh, nonexistent directory: {output}")
    require(output.parent.is_dir(), f"Output parent directory must already exist: {output.parent}")
    require(output != project, "Validation output cannot be the project directory")
    try:
        output.relative_to(project)
    except ValueError:
        pass
    else:
        raise ValidationError("Validation output must be outside the project tree")

    approved_order, approved_path = load_approved(project)
    approved = set(approved_order)
    parser_module = load_project_newick(project)
    marker_summaries, input_hashes, astral_log = validate_marker_files(
        parser_module, project, approved_order, approved)

    astral_tree_path = project / "pilot_output" / "species_tree.newick"
    require(astral_tree_path.is_file() and astral_tree_path.stat().st_size > 0,
            f"Missing/empty ASTRAL species tree: {astral_tree_path}")
    astral = validate_astral_tree(parser_module, astral_tree_path, approved)
    input_hashes[relative_name(astral_tree_path, project)] = sha256_bytes(astral["raw_bytes"])
    input_hashes[relative_name(astral_log, project)] = sha256_file(astral_log)
    input_hashes[relative_name(approved_path, project)] = sha256_file(approved_path)

    raw_tree_name = "species_tree.newick"
    derived_tree_name = "species_tree.itol_quartet_frequency.newick"
    support_name = "astral_quartet_support_by_split.tsv"
    readme_name = "README.txt"
    outputs = {
        raw_tree_name: astral["raw_bytes"],
        derived_tree_name: astral["derived_text"].encode("utf-8"),
        support_name: write_support_tsv(astral["support_rows"]),
        readme_name: (
            "Five-marker pilot validation outputs.\n"
            "species_tree.newick is a byte-for-byte copy of the original ASTRAL result.\n"
            "species_tree.itol_quartet_frequency.newick is derived from that tree; each annotated internal node label is numeric q1, the ASTRAL quartet frequency for the main resolution.\n"
            "q1 is not pp1. pp1 is the local posterior probability for the main resolution. The TSV retains q1-q3, f1-f3, pp1-pp3, QC, and EN per unrooted informative split.\n"
            "No topology or branch lengths were inferred or changed. Duplicate root representations of one unrooted split are consolidated in the TSV; their annotation consistency was checked.\n"
            "This five-marker pilot validates data flow and output structure only; it does not establish production phylogenetic support.\n"
        ).encode("utf-8"),
    }
    artifact_hashes = {name: sha256_bytes(data) for name, data in outputs.items()}
    report = {
        "schema": "LAB_RM_FIVE_MARKER_PILOT_VALIDATION_V1",
        "status": "PASS",
        "validated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "project_root": str(project),
        "scope": {
            "marker_count": EXPECTED_MARKERS,
            "approved_taxon_count": EXPECTED_TAXA,
            "astral_version_from_log": ASTRAL_VERSION,
            "interpretation": "workflow and file-format validation only; five loci do not establish production topology/support reliability",
        },
        "marker_results": marker_summaries,
        "astral_result": astral["summary"],
        "checks": [
            "exact five source FASTAs and one-to-one source/alignment tip and ungapped sequence equality",
            "all pilot FASTA IDs are approved and their union is exactly the approved196 panel",
            "five IQ-TREE logs/reports complete and each gene tree exactly matches its alignment tips with support in range",
            "all_gene_trees.tre is byte-identical to the concatenation of the five validated gene-tree files",
            "ASTRAL tree is parseable, contains exactly the approved196 tips, and each informative unrooted split has valid structured numeric -t 2 annotations",
            "ASTRAL q_i=f_i/EN, f totals agree with EN within source tolerance, posterior/frequency ranges are valid, and present branch lengths are finite and nonnegative",
            "derived q1-labeled tree preserves topology and branch lengths; raw ASTRAL tree is copied byte-for-byte",
        ],
        "input_sha256": dict(sorted(input_hashes.items())),
        "artifact_sha256": dict(sorted(artifact_hashes.items())),
    }
    report_bytes = (json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")
    outputs["validation_report.json"] = report_bytes
    sums = "".join(f"{sha256_bytes(data)}  {name}\n" for name, data in sorted(outputs.items()))
    outputs["SHA256SUMS"] = sums.encode("ascii")
    return output, outputs, report


def emit(output: Path, files: dict[str, bytes]) -> None:
    # This is the first filesystem mutation. Every scientific/file validation has passed.
    output.mkdir()
    for name, data in files.items():
        (output / name).write_bytes(data)


def parser_smoke_check(parser_module) -> None:
    fixture = (
        "((A:0.1,B:0.2)'[q1=0.7;q2=0.2;q3=0.1;f1=7;f2=2;f3=1;"
        "pp1=0.9;pp2=0.07;pp3=0.03;QC=1;EN=10]':0.3,"
        "(C:0.4,D:0.5)'[q1=0.7;q2=0.1;q3=0.2;f1=7;f2=1;f3=2;"
        "pp1=0.9;pp2=0.03;pp3=0.07;QC=1;EN=10]':0.6);\n"
    )
    fake_path = Path("<structured-label fixture>")
    result = validate_astral_tree(parser_module, fake_path, {"A", "B", "C", "D"}, text_override=fixture)
    require(result["summary"]["informative_unrooted_split_count"] == 1,
            "Parser fixture did not consolidate the root duplicate split")
    require(len(result["support_rows"]) == 1, "Parser fixture TSV did not emit one unique split")
    require(result["support_rows"][0]["q1_quartet_frequency"] == "0.7",
            "Parser fixture did not preserve q1 quartet frequency")
    derived_root, _, _ = load_parser_tree_from_text(parser_module, result["derived_text"], fake_path)
    internal_labels = [node.label for node in parser_module.nodes(derived_root) if node.children and node is not derived_root]
    require(internal_labels and all(re.fullmatch(NUM, label) for label in internal_labels),
            "Parser fixture q1-derived labels are not numeric")


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--project", type=Path, required=True, help="LAB_RM project root containing input_genes and pilot_output")
    cli.add_argument("--output", type=Path, required=True, help="Fresh output directory outside the project tree")
    args = cli.parse_args(argv)
    try:
        # Parser smoke fixture exercises the imported parser/annotation convention in memory only.
        project = args.project.resolve(strict=True)
        module = load_project_newick(project)
        parser_smoke_check(module)
        output, files, report = build_validation(project, args.output)
        emit(output, files)
    except (ValidationError, OSError, ImportError, AttributeError, TypeError, KeyError, ValueError) as error:
        print(f"Pilot validation refused: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "output": str(output),
                      "artifacts": sorted(files), "astral": report["astral_result"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
