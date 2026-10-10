#!/usr/bin/env python3
"""Focused offline tests for v2 IQ-TREE support handling and marker03 evidence."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path


MARKER = "ATP-synt"
EXPECTED_MODEL = "Q.YEAST+I+G4"
EXPECTED_BOOTSTRAPS = 1000
EXPECTED_TIPS = 196
NATIVE_END = "Date and Time: Sat Oct 10 11:12:07 2026"
HERE = Path(__file__).resolve().parent
DEFAULT_PROJECT = Path(r"G:\My Drive\LAB_RM\lab-rm-phylogenomics-196")
DEFAULT_VALIDATOR = HERE.parent / "validate_five_marker_pilot_v2.py"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("pilot_validator_v2", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import validator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    old = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = old
    return module


def fingerprint(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "mtime_ns": path.stat().st_mtime_ns}


def must_fail(label: str, call, expected_fragment: str) -> str:
    try:
        call()
    except Exception as error:
        if expected_fragment.lower() not in str(error).lower():
            raise AssertionError(f"{label}: wrong failure: {error}") from error
        return f"rejected: {error}"
    raise AssertionError(f"{label}: invalid fixture unexpectedly passed")


def main() -> int:
    project = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_PROJECT
    validator_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else DEFAULT_VALIDATOR
    if len(sys.argv) > 3:
        raise SystemExit("usage: test_marker03_validator.py [PROJECT [VALIDATOR]]")
    v = load_module(validator_path)
    tree_dir = project / "pilot_output" / "trees"
    evidence = {
        "input_fasta": project / "input_genes" / f"{MARKER}.fasta",
        "alignment": project / "pilot_output" / "alignments" / f"{MARKER}_aligned.fasta",
        "native_log": tree_dir / f"{MARKER}.log",
        "iqtree_report": tree_dir / f"{MARKER}.iqtree",
        "treefile": tree_dir / f"{MARKER}.treefile",
    }
    before = {name: fingerprint(path) for name, path in evidence.items()}

    input_records = v.parse_fasta(evidence["input_fasta"])
    aligned_records = v.parse_fasta(evidence["alignment"])
    if set(input_records) != set(aligned_records):
        raise AssertionError("Input and aligned FASTA IDs differ")
    changed = [name for name, seq in input_records.items()
               if v.normalized_ungapped(seq) != v.normalized_ungapped(aligned_records[name])]
    if changed:
        raise AssertionError(f"Ungapped sequence mismatch: {changed[:5]}")

    parser = v.load_project_newick(project)
    root, _, _ = v.load_parser_tree(parser, evidence["treefile"])
    walked, tips = v.tree_walk(root)
    if len(tips) != EXPECTED_TIPS or tips != set(input_records):
        raise AssertionError(f"Tree tips mismatch: {len(tips)} versus {len(input_records)}")
    if sum(not node.children for node, _, _ in walked) != len(tips):
        raise AssertionError("Tree has duplicate tips")
    v.check_tree_lengths(root, evidence["treefile"], require_all_edges=False)
    support = v.validate_iqtree_support(root, evidence["treefile"])
    if support["unlabeled_internal_branch_count"] != len(support["unlabeled_internal_branches"]):
        raise AssertionError("Unlabeled branch count does not match the recorded path/length list")
    if support["support_component_count"] <= 0:
        raise AssertionError("Actual tree contains no numeric support values")

    log_text = evidence["native_log"].read_text(encoding="utf-8-sig", errors="replace")
    report_text = evidence["iqtree_report"].read_text(encoding="utf-8-sig", errors="replace")
    model = re.findall(r"(?m)^Model of substitution:\s*(\S+)\s*$", report_text)
    boot_report = re.findall(r"(?m)^Type of analysis:.*ultrafast bootstrap \((\d+) replicates\)", report_text)
    boot_log = re.findall(r"(?m)^Generating (\d+) samples for ultrafast bootstrap\b", log_text)
    if model != [EXPECTED_MODEL] or boot_report != [str(EXPECTED_BOOTSTRAPS)] or boot_log != [str(EXPECTED_BOOTSTRAPS)]:
        raise AssertionError(f"Model/bootstrap evidence mismatch: model={model}, report={boot_report}, log={boot_log}")
    if log_text.splitlines()[-1:] != [NATIVE_END]:
        raise AssertionError("Native log completion timestamp mismatch")
    if f"Alignment has {EXPECTED_TIPS} sequences" not in log_text:
        raise AssertionError("Native log does not report 189 alignment sequences")

    def parsed(newick: str):
        return parser.Newick(newick).parse()

    malformed_non_numeric = must_fail(
        "nonnumeric support",
        lambda: v.validate_iqtree_support(parsed("((A:0.1,B:0.2)bad:0.3,C:0.4);"), Path("<bad-support>")),
        "unsupported IQ-TREE support")
    malformed_range = must_fail(
        "out-of-range support",
        lambda: v.validate_iqtree_support(parsed("((A:0.1,B:0.2)101:0.3,C:0.4);"), Path("<bad-range>")),
        "outside [0,100]")
    no_numeric_support = must_fail(
        "all support absent",
        lambda: v.validate_iqtree_support(parsed("((A:0.1,B:0.2):0.3,C:0.4);"), Path("<no-support>")),
        "No internal IQ-TREE support values")
    negative_branch = must_fail(
        "negative branch length",
        lambda: v.check_tree_lengths(parsed("((A:-0.1,B:0.2)80:0.3,C:0.4);"), Path("<negative-length>"), False),
        "negative")

    after = {name: fingerprint(path) for name, path in evidence.items()}
    if before != after:
        raise AssertionError("Evidence changed during focused validation")

    receipt = {
        "schema": "LAB_RM_MARKER03_V2_VALIDATOR_TEST_V1",
        "status": "PASS",
        "validated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scope": {"marker": MARKER, "tips": len(tips), "scientific_rerun": False,
                  "other_marker_or_astral_outputs_read": False},
        "native_evidence": {
            "input_alignment_tip_ids_equal": True,
            "ungapped_sequences_preserved": True,
            "model": model[0],
            "bootstrap_replicates_report": int(boot_report[0]),
            "bootstrap_replicates_native_log": int(boot_log[0]),
            "native_log_end": NATIVE_END,
            "tree_tip_count": len(tips),
            "tree_tips_unique_and_exact": True,
            "branch_lengths_finite_nonnegative": True,
            "support_validation": support,
        },
        "synthetic_negative_tests": {
            "nonnumeric_support": malformed_non_numeric,
            "out_of_range_support": malformed_range,
            "all_support_absent": no_numeric_support,
            "negative_branch_length": negative_branch,
        },
        "evidence": before,
        "evidence_unchanged_during_validation": True,
        "limitations": [
            "Focused marker03 file-level validation only; no claim about other markers, ASTRAL, or biological validity.",
            "All unlabeled internal branches are recorded individually with path and branch length; no support value is imputed.",
            "No project files were modified and no network/API operation was performed.",
        ],
    }
    output = HERE / "marker03_v2_validation.json"
    if output.exists():
        raise RuntimeError(f"Refusing to overwrite existing receipt: {output}")
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "receipt": str(output),
                      "support": {k: support[k] for k in (
                          "support_component_count", "support_min", "support_max",
                          "unlabeled_internal_branch_count")},
                      "evidence_sha256": {k: v["sha256"] for k, v in before.items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


