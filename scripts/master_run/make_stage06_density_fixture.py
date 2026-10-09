"""Write a196-tip, nonbiological layout fixture. Never use an approved panel."""
import argparse
import csv
import json
from pathlib import Path
from types import SimpleNamespace
from stage06_render import TYPES, digest, render, require
from check_stage06_outputs import check


def make(directory):
    require(not directory.exists(), "Synthetic fixture namespace must be new")
    directory.mkdir(parents=True)
    # Same character count and near Helvetica width as GCF_#########.1;
    # TEST labels cannot be confused with approved production accessions.
    tips = [f"TEST_{i:08d}.1" for i in range(1, 197)]
    serial = [0]
    def subtree(names, root=False):
        serial[0] += 1
        index = serial[0]
        length = 0 if index % 17 == 0 else 0.004 + (index % 9) * 0.003
        if len(names) == 1:
            return names[0] + f":{length:.3f}"
        middle = len(names) // 2
        text = "(" + subtree(names[:middle]) + "," + subtree(names[middle:]) + ")95/99"
        return text if root else text + f":{length:.3f}"
    (directory / "tree.nwk").write_text("[&U]" + subtree(tips, root=True) + ";\n", encoding="utf-8")
    (directory / "approved.txt").write_text("\n".join(reversed(tips)) + "\n", encoding="utf-8")
    with (directory / "matrix.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(["accession", *TYPES])
        writer.writerows((a, *[("1", "0", "NA")[(i + j) % 3] for j in range(4)]) for i, a in reversed(list(enumerate(tips))))
    with (directory / "state.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(["accession", "rm_type", "state", "complete_count", "partial_count", "candidate_count", "search_complete", "conflict", "review_ids", "positive_invalidated", "count_lower_bound"])
        for i, a in enumerate(tips):
            for j, t in enumerate(TYPES):
                value = ("1", "0", "NA")[(i + j) % 3]
                extra = value == "1" and i % 5 == 0
                state = {"1": "COMPLETE_PREDICTED_WITH_OTHER_PARTIAL" if extra else "COMPLETE_PREDICTED",
                         "0": "NOT_DETECTED_AFTER_SUCCESSFUL_SEARCH", "NA": "NOT_RUN_SYNTHETIC_UNKNOWN"}[value]
                writer.writerow([a, t.replace("Type_", ""), state, int(value == "1"), int(extra), 0, str(value != "NA" and not extra).lower(),
                                 "false", "[]", "false", str(value == "NA" or extra).lower()])
    args = SimpleNamespace(tree=directory / "tree.nwk", matrix=directory / "matrix.tsv", state=directory / "state.tsv",
                           approved=directory / "approved.txt", join=directory / "join.json",
                           tree_validation=directory / "tree_validation.json", output=directory / "render", synthetic=True, exception_manifest=None)
    args.curation_validation = directory / "curation_validation.json"
    args.curation_source_manifest = directory / "curation_source_manifest.json"
    hashes = {key + "_sha256": digest(getattr(args, key)) for key in ("tree", "matrix", "state", "approved")}
    args.join.write_text(json.dumps({"dataset_kind": "SYNTHETIC", "status": "PASS_SYNTHETIC_EXACT_JOIN", **hashes,
                                    "tip_count": 196, "accession_count": 196, "cell_count": 784, "exact_accession_join": True, "unique_tips": True}), encoding="utf-8")
    args.tree_validation.write_text(json.dumps({"scientific_state": "SYNTHETIC_VALIDATION_ONLY",
                                               "native_tree_sha256": hashes["tree_sha256"], "approved_accessions_sha256": hashes["approved_sha256"]}), encoding="utf-8")
    args.curation_source_manifest.write_text(json.dumps({"dataset_kind": "SYNTHETIC", "note": "Nonbiological layout fixture only; no review/source evidence exists."}), encoding="utf-8")
    args.curation_validation.write_text(json.dumps({"schema": "RM_INDEPENDENT_CURATION_ACCEPTANCE_V1", "status": "PASS_SYNTHETIC_CURATION_CONTRACT",
        "dataset_kind": "SYNTHETIC", "accepted_curation": False, "accession_count": 196, "cell_count": 784,
        **{k: hashes[k] for k in ("matrix_sha256", "state_sha256", "approved_sha256")},
        "curation_source_manifest_sha256": digest(args.curation_source_manifest), "functional_activity_claim": "NONE"}), encoding="utf-8")
    render(args)
    result = check(args.output)
    (directory / "artifact_validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(make(args.output), indent=2))
