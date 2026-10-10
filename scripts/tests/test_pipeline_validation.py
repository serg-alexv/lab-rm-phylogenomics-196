#!/usr/bin/env python3
"""Synthetic-only end-to-end tests for scripts/validate_pipeline.py.

Run from the requested Python environment with --project-root and --test-root.
All generated scientific-looking records are synthetic and stay below test-root.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument("--project-root", type=Path, required=True)
p.add_argument("--test-root", type=Path, required=True)
p.add_argument("--run-name", default="run01")
a = p.parse_args()
real_project = a.project_root.resolve()
test_root = a.test_root.resolve()
run_root = test_root / a.run_name
if run_root.exists():
    raise SystemExit(f"Refusing existing run fixture directory: {run_root}")
run_root.mkdir(parents=True)
validator = real_project / "scripts" / "validate_pipeline.py"
core_path = real_project / "scripts" / "master_run" / "validate_five_marker_pilot_v2.py"
parser_source = real_project / "scripts" / "master_run" / "stage06_render.py"
source_paths = {"validate_pipeline.py": validator, "validate_five_marker_pilot_v2.py": core_path,
                "stage06_render.py": parser_source}
source_before = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in source_paths.items()}

# Narrow real-project snapshot: approved list, pilot input and completed first-marker artifacts,
# plus the run script. ADK and all other potentially active marker outputs are deliberately excluded.
real_snapshot_paths = [
    "config/approved_accessions.txt",
    "input_genes/5-FTHF_cyc-lig.fasta",
    "pilot_output/alignments/5-FTHF_cyc-lig_aligned.fasta",
    "pilot_output/trees/5-FTHF_cyc-lig.treefile",
    "pilot_output/trees/5-FTHF_cyc-lig.log",
    "pilot_output/trees/5-FTHF_cyc-lig.iqtree",
    "run_pipeline.sh",
]
def snapshot_real():
    result = {}
    for rel in real_snapshot_paths:
        path = real_project / rel
        result[rel] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    return result
real_before = snapshot_real()

approved = [f"GCF_{i:09d}.1" for i in range(1, 197)]
ANNOT = "[q1=0.7;q2=0.2;q3=0.1;f1=7;f2=2;f3=1;pp1=0.9;pp2=0.07;pp3=0.03;QC=1;EN=10]"
MARKERS5 = ["marker_01", "marker_02", "marker_03", "marker_04", "marker_05"]
PILOT_IDS = [approved[0:4], approved[1:5], [approved[0], *approved[2:5]],
             [approved[0], approved[1], approved[3], approved[4]],
             [approved[0], approved[1], approved[2], approved[4]]]

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))

def install_project_parser(project):
    target = project / "scripts" / "master_run" / "stage06_render.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(parser_source, target)
    write(project / "run_pipeline.sh", b"#!/bin/sh\n# synthetic test fixture only\n")

def make_gene_tree(ids):
    # A supported 2-versus-rest split ensures IQ-TREE support parsing is exercised.
    return "((" + ids[0] + ":0.1," + ids[1] + ":0.1)95:0.2," + ",".join(x + ":0.1" for x in ids[2:]) + ");\n"

def marker_artifacts(project, mode, marker_names, marker_ids):
    root = project / ("pilot_output" if mode == "pilot" else "pipeline_output")
    align = root / "alignments"
    trees = root / "trees"
    align.mkdir(parents=True, exist_ok=True)
    trees.mkdir(parents=True, exist_ok=True)
    raw_trees = []
    for marker, ids in zip(marker_names, marker_ids):
        fasta = "".join(f">{g}\nACDEFG\n" for g in ids).encode("utf-8")
        write(project / "input_genes" / (marker + ".fasta"), fasta)
        write(align / (marker + "_aligned.fasta"), fasta)
        tree = make_gene_tree(ids).encode("utf-8")
        write(trees / (marker + ".treefile"), tree)
        write(trees / (marker + ".log"),
              f"Generating 1000 samples for ultrafast bootstrap (seed: 1)\nAnalysis results written to: {marker}.treefile\nDate and Time: synthetic-fixture\n")
        write(trees / (marker + ".iqtree"), "ultrafast bootstrap (1000 replicates)\n")
        raw_trees.append(tree)
    write(root / "all_gene_trees.tre", b"".join(raw_trees))
    write(project / "reports" / "stage01" / ("pilot_iqtree.log" if mode == "pilot" else "iqtree.log"),
          ("Analysis results written to: synthetic\n" * len(marker_names)))
    write(project / "reports" / "stage01" / ("pilot_mafft.log" if mode == "pilot" else "mafft.log"), "Synthetic MAFFT fixture\n")
    if mode == "pilot":
        tree = (f"(({approved[0]}:0.1,{approved[1]}:0.1)'{ANNOT}':0.2,"
                f"({approved[2]}:0.1,{approved[3]}:0.1)'{ANNOT}':0.2,{approved[4]}:0.1);\n")
        write(root / "species_tree.newick", tree)
        astral_log = project / "reports" / "stage01" / "pilot_astral.log"
    else:
        # Full mode uses a 196-tip star ASTRAL tree, which has no nontrivial splits.
        tree = "(" + ",".join(x + ":0.1" for x in approved) + ");\n"
        write(project / "species_tree.newick", tree)
        astral_log = project / "reports" / "stage01" / "astral_run.log"
    write(astral_log, "ASTRAL version 5.7.8\nSynthetic fixture completed\n")
    return root

def make_project(name, full=False, astral_mutation=None):
    project = run_root / "fixtures" / name / "project"
    project.mkdir(parents=True)
    install_project_parser(project)
    write(project / "config" / "approved_accessions.txt", "\n".join(approved) + "\n")
    if full:
        names = [f"marker_{i:03d}" for i in range(1, 101)]
        ids = [approved[:] for _ in names]
        marker_artifacts(project, "full", names, ids)
    else:
        names = MARKERS5
        marker_artifacts(project, "pilot", names, PILOT_IDS)
        if astral_mutation:
            tree_path = project / "pilot_output" / "species_tree.newick"
            text = tree_path.read_text(encoding="utf-8")
            if astral_mutation == "truncated":
                text = text[:-2]  # malformed Newick copied only inside this synthetic fixture
            elif astral_mutation == "duplicate":
                text = text.replace(approved[4] + ":0.1", approved[3] + ":0.1")
            elif astral_mutation == "missing":
                text = text.replace("," + approved[4] + ":0.1", "")
            elif astral_mutation == "extra":
                text = text.replace(");", ",GCF_999999999.1:0.1);")
            tree_path.write_text(text, encoding="utf-8", newline="\n")
    return project

def invoke(project, mode, report_name):
    report = run_root / "reports" / report_name
    proc = subprocess.run([sys.executable, "-B", str(validator), "--project", str(project),
                           "--mode", mode, "--report-dir", str(report)],
                          capture_output=True, text=True,
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    summary = report / "validation_summary.tsv"
    report_json = report / "validation_report.json"
    parsed = json.loads(report_json.read_text(encoding="utf-8")) if report_json.exists() else None
    tsv = summary.read_text(encoding="utf-8") if summary.exists() else ""
    return proc, report, parsed, tsv

cases = []
# Positive pilot: five sorted markers, four tips each, union five; supported gene trees and exact concatenation.
project = make_project("pilot_pass")
proc, report, parsed, tsv = invoke(project, "pilot", "pilot_pass")
assert proc.returncode == 0 and "GLOBAL_PIPELINE_STATUS: PASS" in proc.stdout, (proc.stdout, proc.stderr, tsv)
assert parsed["status"] == "PASS" and parsed["mode"] == "pilot"
assert parsed["results"]["approved_taxa"] == 196
assert parsed["results"]["expected_astral_taxa_from_validated_marker_union"] == 5
assert parsed["results"]["evidence_unchanged_during_validation"] is True
derived = report / "species_tree.itol_quartet_frequency.newick"
assert derived.is_file()
assert parsed["input_sha256"]["pilot_output/species_tree.newick"] == hashlib.sha256((project / "pilot_output" / "species_tree.newick").read_bytes()).hexdigest()
assert parsed["artifact_sha256"][derived.name] == hashlib.sha256(derived.read_bytes()).hexdigest()
assert (report / "species_tree.itol_quartet_frequency.newick").is_file()
cases.append({"case":"pilot_pass","pass":True,"exit_code":proc.returncode,"status":parsed["status"],"markers":len(parsed["results"]["markers"]),"approved_taxa":196,"union_taxa":5,"astral_summary":parsed["results"]["astral"],"derived_tree_written":True,"evidence_unchanged":True})
# Reuse refusal must preserve every byte and create no sibling outputs.
before = {x.name: hashlib.sha256(x.read_bytes()).hexdigest() for x in report.iterdir() if x.is_file()}
reuse = subprocess.run([sys.executable, "-B", str(validator), "--project", str(project), "--mode", "pilot", "--report-dir", str(report)], capture_output=True, text=True)
after = {x.name: hashlib.sha256(x.read_bytes()).hexdigest() for x in report.iterdir() if x.is_file()}
assert reuse.returncode == 1 and "Refusing to overwrite validation evidence" in reuse.stderr and before == after
cases.append({"case":"output_reuse_refused","pass":True,"exit_code":reuse.returncode,"existing_evidence_hashes_unchanged":True})

# Negative ASTRAL cases: malformed/truncated, duplicate, missing, extra tips.
for mutation in ("truncated", "duplicate", "missing", "extra"):
    project = make_project("astral_" + mutation, astral_mutation=mutation)
    proc, report, parsed, tsv = invoke(project, "pilot", "astral_" + mutation)
    assert proc.returncode == 1 and parsed["status"] == "FAIL", (mutation, proc.stdout, proc.stderr, tsv)
    assert "FAIL" in tsv and "pipeline\tFAIL" in tsv
    assert not (report / "species_tree.itol_quartet_frequency.newick").exists()
    cases.append({"case":"astral_"+mutation,"pass":True,"exit_code":proc.returncode,"status":parsed["status"],"fail_tsv":True,"derived_tree_withheld":True,"failure_row":next(line for line in tsv.splitlines() if "FAIL" in line)})

# Full mode against pilot-only five-marker input must fail count gate even with pilot_output present.
project = make_project("full_rejects_pilot", full=False)
proc, report, parsed, tsv = invoke(project, "full", "full_rejects_pilot")
assert proc.returncode == 1 and parsed["status"] == "FAIL"
assert "full needs 100 marker FASTAs; found 5" in tsv
assert (project / "pilot_output").is_dir()
cases.append({"case":"full_rejects_pilot","pass":True,"exit_code":proc.returncode,"status":parsed["status"],"failure":"full needs 100 marker FASTAs; found 5","pilot_output_present":True})

# Positive full mode fixture: 100 markers x 196 taxa; five strict completions are a subset of 100.
project = make_project("full_pass_100x196", full=True)
proc, report, parsed, tsv = invoke(project, "full", "full_pass_100x196")
assert proc.returncode == 0 and parsed["status"] == "PASS", (proc.stdout, proc.stderr, tsv)
assert parsed["mode"] == "full" and len(parsed["results"]["markers"]) == 100
assert parsed["results"]["approved_taxa"] == 196
assert parsed["results"]["expected_astral_taxa_from_validated_marker_union"] == 196
assert parsed["results"]["evidence_unchanged_during_validation"] is True
cases.append({"case":"full_pass_100x196","pass":True,"exit_code":proc.returncode,"status":parsed["status"],"markers":100,"approved_taxa":196,"union_taxa":196,"evidence_unchanged":True,"astral_summary":parsed["results"]["astral"]})

real_after = snapshot_real()
real_unchanged = real_before == real_after
source_after = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in source_paths.items()}
receipt = {
    "receipt_type": "synthetic_pipeline_validation_tests",
    "schema_version": 1,
    "synthetic_only": True,
    "real_data_used_as_fixture": False,
    "inference_or_network": False,
    "python": sys.executable,
    "project_root_argument": str(real_project),
    "validator_source_sha256_before": source_before,
    "validator_source_sha256_after": source_after,
    "source_unchanged": source_before == source_after,
    "real_project_readonly_snapshot_before": real_before,
    "real_project_readonly_snapshot_after": real_after,
    "real_snapshot_unchanged": real_unchanged,
    "snapshot_scope_note": "Only approved accession list, completed 5-FTHF_cyc-lig input/alignment/tree/log/report if present, and run_pipeline.sh were hashed. Active ADK and all other potentially active marker outputs were excluded.",
    "cases": cases,
    "all_passed": all(item["pass"] for item in cases) and real_unchanged and source_before == source_after,
}
result_path = run_root / "results.json"
result_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
if not receipt["all_passed"]:
    raise SystemExit("One or more tests or read-only stability checks failed; see results.json")
print(json.dumps(receipt, indent=2, sort_keys=True))
