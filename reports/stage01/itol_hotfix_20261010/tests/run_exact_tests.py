import csv
import hashlib
import json
import subprocess
from pathlib import Path

SCRIPT = Path(r"G:\My Drive\LAB_RM\lab-rm-phylogenomics-196\scripts\make_itol_decorations.py")
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
PYTHON = Path(r"C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe")
SYSTEMS = ["RM", "Cas", "Abi2", "CBASS", "BREX", "Septu"]
COLORS = ["#008080", "#2e8b57", "#ffa500", "#8b0000", "#ff1493", "#0000ff"]
HEADER = ["GenomeID", "Host", "Septu", "CBASS", "RM", "BREX", "Cas", "Abi2"]
# The system fields intentionally arrive in a reordered input header.
ROWS = [
    ["GCF_000006945.1", "Synthetic Host A", "0", "0", "1", "1", "1", "0"],
    ["GCF_000009505.1", "Synthetic Host B", "1", "0", "0", "0", "1", "1"],
    ["GCF_001299935.1", "Synthetic Host C", "0", "1", "1", "0", "0", "1"],
]
EXPECTED_NAMES = {"defense_systems_heatmap.txt", "host_colorstrip.txt"}

def write_tsv(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)

def execute(name, header, rows, sentinel=None):
    case = OUT / name
    case.mkdir()
    src = case / "input.tsv"
    write_tsv(src, header, rows)
    target = case / "output"
    if sentinel:
        target.mkdir()
        (target / sentinel[0]).write_bytes(sentinel[1])
    proc = subprocess.run([str(PYTHON), str(SCRIPT), "--input", str(src), "--output-dir", str(target)], capture_output=True, text=True)
    files = sorted(p.name for p in target.iterdir() if p.is_file()) if target.exists() else []
    return target, proc, files

expected_binary = (
    "DATASET_BINARY\n"
    "SEPARATOR\tTAB\n"
    "DATASET_LABEL\tDefense Systems\n"
    "COLOR\t#000000\n"
    "\n"
    "# Enforce tabs uniformly across all array parameters to prevent upload crashes\n"
    "FIELD_SHAPES\t1\t1\t1\t1\t1\t1\n"
    "FIELD_COLORS\t#008080\t#2e8b57\t#ffa500\t#8b0000\t#ff1493\t#0000ff\n"
    "FIELD_LABELS\tRM\tCas\tAbi2\tCBASS\tBREX\tSeptu\n"
    "\n"
    "LEGEND_TITLE\tDefense Systems\n"
    "LEGEND_SHAPES\t1\t1\t1\t1\t1\t1\n"
    "LEGEND_COLORS\t#008080\t#2e8b57\t#ffa500\t#8b0000\t#ff1493\t#0000ff\n"
    "LEGEND_LABELS\tRM\tCas\tAbi2\tCBASS\tBREX\tSeptu\n"
    "\n"
    "DATA\n"
    "# Each column must be strictly tab-delimited (\\t)\n"
    "GCF_000006945.1\t1\t1\t0\t0\t1\t0\n"
    "GCF_000009505.1\t0\t1\t1\t0\t0\t1\n"
    "GCF_001299935.1\t1\t0\t1\t1\t0\t0\n"
).encode("utf-8")

target, proc, files = execute("exact_template_reordered_header", HEADER, ROWS)
assert proc.returncode == 0, proc.stderr
assert set(files) == EXPECTED_NAMES, files
actual_binary = (target / "defense_systems_heatmap.txt").read_bytes()
assert actual_binary == expected_binary, "Binary output differs byte-for-byte from fixed expected template"
assert actual_binary.endswith(b"\n")
assert (target / "host_colorstrip.txt").read_text(encoding="utf-8").startswith("DATASET_COLORSTRIP\nSEPARATOR\tTAB\nDATASET_LABEL\tHost\n")
strip_lines = (target / "host_colorstrip.txt").read_text(encoding="utf-8").splitlines()
strip_rows = [line.split("\t") for line in strip_lines[strip_lines.index("DATA") + 1:]]
assert len(strip_rows) == 3 and all(len(row) == 3 for row in strip_rows)
assert [row[0] for row in strip_rows] == [row[0] for row in ROWS]
assert len({row[1] for row in strip_rows}) == 3
host_labels = next(line for line in strip_lines if line.startswith("LEGEND_LABELS\t")).split("\t")[1:]
host_colors = next(line for line in strip_lines if line.startswith("LEGEND_COLORS\t")).split("\t")[1:]
assert len(host_labels) == len(host_colors) == 3 and len(set(host_colors)) == 3
assert dict(zip(host_labels, host_colors)) == {row[2]: row[1] for row in strip_rows}
results = [{"case":"exact_template_reordered_header","pass":True,"exit_code":0,"output_files":files,"exact_binary_byte_match":True,"binary_data_rows":3,"binary_fields_including_id":7,"canonical_field_order":SYSTEMS,"host_color_count":3,"host_legend_matches_data":True}]

invalids = []
missing_header = [x for x in HEADER if x != "Septu"]
missing_rows = [[r[HEADER.index(x)] for x in missing_header] for r in ROWS]
invalids.append(("invalid_missing_column", missing_header, missing_rows))
invalids.append(("invalid_duplicate_id", HEADER, [ROWS[0], ROWS[0], ROWS[2]]))
blank_rows = [r[:] for r in ROWS]; blank_rows[0][HEADER.index("Cas")] = ""
invalids.append(("invalid_blank_defense", HEADER, blank_rows))
na_rows = [r[:] for r in ROWS]; na_rows[1][HEADER.index("RM")] = "NA"
invalids.append(("invalid_NA", HEADER, na_rows))
extra_rows = [r[:] for r in ROWS]; extra_rows[2].append("EXTRA")
invalids.append(("invalid_extra_row_field", HEADER, extra_rows))
for name, header, rows in invalids:
    _, proc, files = execute(name, header, rows)
    assert proc.returncode != 0 and not files, {"case":name,"exit":proc.returncode,"files":files}
    results.append({"case":name,"pass":True,"exit_code":proc.returncode,"output_files":files,"stderr":proc.stderr.strip()})

sentinel = b"existing bytes stay unchanged\n"
target, proc, files = execute("refuse_existing_output", HEADER, ROWS, ("defense_systems_heatmap.txt", sentinel))
assert proc.returncode != 0
assert (target / "defense_systems_heatmap.txt").read_bytes() == sentinel
assert not (target / "host_colorstrip.txt").exists()
assert files == ["defense_systems_heatmap.txt"]
results.append({"case":"refuse_existing_output","pass":True,"exit_code":proc.returncode,"preserved_existing_target":True,"sibling_created":False,"stderr":proc.stderr.strip()})

receipt = {
    "receipt_type":"synthetic_itol_exact_template_tests",
    "schema_version":1,
    "script_path":str(SCRIPT),
    "script_sha256":hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
    "python_executable":str(PYTHON),
    "synthetic_only":True,
    "real_data_used":False,
    "fixed_system_order":SYSTEMS,
    "fixed_field_colors":COLORS,
    "exact_binary_expected_sha256":hashlib.sha256(expected_binary).hexdigest(),
    "cases":results,
    "all_passed":all(r["pass"] for r in results),
    "review_notes":["The binary dataset filename still contains 'heatmap' although the file declares DATASET_BINARY.","Preflight protects existing output files, but multi-file writes are not transactional if a later create/write fails.","The default output directory remains project-root pipeline_output; use explicit --output-dir for bounded runs."]
}
result_path = OUT / "results.json"
result_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, indent=2))