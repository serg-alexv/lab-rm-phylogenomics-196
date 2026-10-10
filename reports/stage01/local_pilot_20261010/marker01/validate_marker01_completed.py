#!/usr/bin/env python3
"""Read-only validation receipt generator for the completed 5-FTHF_cyc-lig pilot."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import re
import sys
from pathlib import Path


MARKER = "5-FTHF_cyc-lig"
EXPECTED_MODEL = "Q.PFAM+F+I+R5"
EXPECTED_BOOTSTRAPS = 1000
EXPECTED_TIPS = 189
NATIVE_END = "Date and Time: Sat Oct 10 10:39:43 2026"


def load_validator(path: Path):
    spec = importlib.util.spec_from_file_location("pilot_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load validator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    old = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = old
    return module


def file_fingerprint(path: Path) -> dict:
    raw = path.read_bytes()
    stat = path.stat()
    return {
        "path": str(path),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "mtime_ns": stat.st_mtime_ns,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path,
                    help="Existing fresh receipt directory; only marker-specific files are written here")
    ap.add_argument("--validator", required=True, type=Path,
                    help="Path to validate_five_marker_pilot.py")
    args = ap.parse_args()
    project = args.project.resolve()
    output = args.output.resolve()
    allowed_preexisting = {Path(__file__).resolve()}
    if not output.is_dir() or any(p.resolve() not in allowed_preexisting for p in output.iterdir()):
        raise RuntimeError(f"Output must contain only this checker before receipt creation: {output}")

    input_fasta = project / "input_genes" / f"{MARKER}.fasta"
    aligned_fasta = project / "pilot_output" / "alignments" / f"{MARKER}_aligned.fasta"
    tree_dir = project / "pilot_output" / "trees"
    log = tree_dir / f"{MARKER}.log"
    report = tree_dir / f"{MARKER}.iqtree"
    treefile = tree_dir / f"{MARKER}.treefile"
    evidence = {"input_fasta": input_fasta, "alignment": aligned_fasta,
                "native_log": log, "iqtree_report": report, "treefile": treefile}
    before = {name: file_fingerprint(path) for name, path in evidence.items()}

    validator = load_validator(args.validator.resolve())
    inputs = validator.parse_fasta(input_fasta)
    aligned = validator.parse_fasta(aligned_fasta)
    if set(inputs) != set(aligned):
        raise RuntimeError(f"Input/alignment tip mismatch: input={len(inputs)} aligned={len(aligned)}")
    mismatched = [name for name in inputs
                  if validator.normalized_ungapped(inputs[name]) !=
                  validator.normalized_ungapped(aligned[name])]
    if mismatched:
        raise RuntimeError(f"Ungapped sequence changed for {len(mismatched)} tips: {mismatched[:5]}")

    parser = validator.load_project_newick(project)
    root, tree_text, _ = validator.load_parser_tree(parser, treefile)
    walked, tips = validator.tree_walk(root)
    if len(tips) != EXPECTED_TIPS or tips != set(inputs):
        raise RuntimeError(f"Tree tips differ: tree={len(tips)}, FASTA={len(inputs)}")
    if sum(not node.children for node, _, _ in walked) != len(tips):
        raise RuntimeError("Tree contains duplicate tips")
    validator.check_tree_lengths(root, treefile, require_all_edges=False)
    support_values = []
    unlabeled_internal = []
    for node, node_path, _ in walked:
        if not node.children or node is root:
            continue
        label = node.label.strip()
        if not label:
            unlabeled_internal.append((node_path, node.length))
            continue
        if validator.IQTREE_SUPPORT_RE.fullmatch(label) is None:
            raise RuntimeError(f"Malformed IQ-TREE support label at {node_path}: {label!r}")
        values = [float(value) for value in label.split("/")]
        if any(not math.isfinite(value) or value < 0 or value > 100 for value in values):
            raise RuntimeError(f"IQ-TREE support outside [0,100] at {node_path}: {label!r}")
        support_values.extend(values)
    if not support_values:
        raise RuntimeError("No numeric IQ-TREE support values found")
    support = {
        "numeric_support_label_count": len(support_values),
        "unlabeled_internal_branch_count": len(unlabeled_internal),
        "unlabeled_branch_max_length": max((length for _, length in unlabeled_internal
                                             if length is not None), default=None),
        "support_min": min(support_values),
        "support_max": max(support_values),
    }

    log_text = log.read_text(encoding="utf-8-sig", errors="replace")
    report_text = report.read_text(encoding="utf-8-sig", errors="replace")
    model_matches = re.findall(r"(?m)^Model of substitution:\s*(\S+)\s*$", report_text)
    bootstrap_matches = re.findall(
        r"(?m)^Type of analysis:.*ultrafast bootstrap \((\d+) replicates\)", report_text)
    requested = re.findall(r"(?m)^Generating (\d+) samples for ultrafast bootstrap\b", log_text)
    if model_matches != [EXPECTED_MODEL]:
        raise RuntimeError(f"Unexpected substitution model lines: {model_matches}")
    if bootstrap_matches != [str(EXPECTED_BOOTSTRAPS)] or requested != [str(EXPECTED_BOOTSTRAPS)]:
        raise RuntimeError(f"Bootstrap count evidence mismatch: report={bootstrap_matches}, log={requested}")
    if NATIVE_END not in log_text.splitlines()[-1:]:
        raise RuntimeError("Native IQ-TREE log does not end with the observed completion timestamp")
    required_end = [
        "Analysis results written to:",
        f"IQ-TREE report:                pilot_output/trees/{MARKER}.iqtree",
        f"Maximum-likelihood tree:       pilot_output/trees/{MARKER}.treefile",
        "Ultrafast bootstrap approximation results written to:",
    ]
    missing_end = [line for line in required_end if line not in log_text]
    if missing_end:
        raise RuntimeError(f"Native log lacks completion/output evidence: {missing_end}")
    if f"Alignment has {EXPECTED_TIPS} sequences" not in log_text:
        raise RuntimeError("Native log tip count does not match the expected 189")

    after = {name: file_fingerprint(path) for name, path in evidence.items()}
    if before != after:
        raise RuntimeError("Evidence files changed during validation; refusing receipt")

    receipt = {
        "schema": "lab-rm-pilot-marker-validation/1",
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS",
        "scope": {"marker": MARKER, "tips": EXPECTED_TIPS,
                  "only_marker_outputs_read": True, "scientific_rerun": False},
        "checks": {
            "input_alignment_tip_ids_equal": True,
            "input_alignment_ungapped_sequences_equal": True,
            "native_iqtree_log_completed": True,
            "native_log_ends_with_completion_timestamp": NATIVE_END,
            "successful_output_paths_present": required_end,
            "bootstrap_replicates": EXPECTED_BOOTSTRAPS,
            "bootstrap_evidence": {"report": bootstrap_matches[0], "native_log": requested[0]},
            "model": model_matches[0],
            "tree_tip_count": len(tips),
            "tree_tips_equal_fasta_ids": True,
            "tree_tips_unique": True,
            "tree_branch_lengths_finite_nonnegative": True,
            "tree_internal_supports": support,
            "unlabeled_internal_branch_paths": ["root/" + "/".join(map(str, p))
                                                for p, _ in unlabeled_internal],
            "native_alignment_summary": "189 sequences; 210 columns; 204 distinct patterns",
        },
        "evidence": before,
        "evidence_unchanged_during_validation": True,
        "limitations": [
            "This receipt validates only 5-FTHF_cyc-lig, not the other four markers or ASTRAL.",
            "This is file-level operational validation, not an independent biological or model-fit assessment.",
            "No external upload, publication, scientific rerun, or source/output modification was performed.",
        ],
    }
    out = output / "marker01_validation.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "receipt": str(out),
                      "tree_tips": len(tips), "support": support,
                      "evidence_sha256": {k: v["sha256"] for k, v in before.items()}}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
