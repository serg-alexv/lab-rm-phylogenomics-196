import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

TEST_ROOT = Path(__file__).resolve().parent / "fixtures_run02"
TEST_ROOT.mkdir(parents=True, exist_ok=False)
SCRIPT = Path(r"G:\My Drive\LAB_RM\lab-rm-phylogenomics-196\scripts\upload_itol.py")
PYTHON = Path(r"C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe")
DUMMY = "DUMMY_KEY_NEVER_USE_91d3b65f"
FAKE = TEST_ROOT / "fake_modules"
FAKE.mkdir()

(FAKE / "sitecustomize.py").write_text(r'''import builtins, io, os
_real_open = builtins.open
def _fake_key_open(file, *args, **kwargs):
    try:
        path = os.fspath(file)
    except TypeError:
        path = None
    if path == "/mnt/c/itol.api-key.txt":
        marker = os.environ.get("KEY_READ_MARKER")
        if marker:
            with _real_open(marker, "w", encoding="utf-8") as f:
                f.write("intercepted exact key path; dummy only")
        return io.StringIO(os.environ["DUMMY_ITOL_KEY"])
    return _real_open(file, *args, **kwargs)
builtins.open = _fake_key_open
''', encoding="utf-8")

(FAKE / "requests.py").write_text(r'''import json, os
from pathlib import Path
class RequestException(Exception):
    pass
class Response:
    def __init__(self, status_code=200, text="", content=None):
        self.status_code = status_code
        self.text = text
        self.content = content if content is not None else text.encode("utf-8")
def post(url, data=None, files=None, timeout=None, allow_redirects=None):
    log_path = Path(os.environ["MOCK_CALL_LOG"])
    calls = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else []
    call = {"url":url, "timeout":list(timeout) if isinstance(timeout, tuple) else timeout,
            "allow_redirects":allow_redirects, "data_keys":sorted(data.keys()) if data else [],
            "api_key_received":bool(data and data.get("APIkey") == os.environ["DUMMY_ITOL_KEY"])}
    mode = os.environ["MOCK_MODE"]
    if url.endswith("batch_uploader.cgi"):
        call["projectName"] = data.get("projectName")
        call["treeName"] = data.get("treeName")
        call["zip_field"] = sorted(files.keys()) if files else []
        filename, package, mime = files["zipFile"]
        call["upload_filename"] = filename
        call["upload_mime"] = mime
        call["package_bytes"] = len(package)
        with open(os.environ["CAPTURE_ZIP"], "wb") as f:
            f.write(package)
        if mode == "network_exception":
            calls.append(call); log_path.write_text(json.dumps(calls), encoding="utf-8")
            raise RequestException("simulated connection issue containing " + os.environ["DUMMY_ITOL_KEY"])
        calls.append(call); log_path.write_text(json.dumps(calls), encoding="utf-8")
        if mode == "http500": return Response(500, "fake server error")
        if mode == "err": return Response(200, "ERR: fake upload failure")
        if mode == "no_success": return Response(200, "upload queued without result ID")
        return Response(200, "notice with token " + os.environ["DUMMY_ITOL_KEY"] + "\nSUCCESS: 73421\n")
    call["tree"] = data.get("tree")
    call["format"] = data.get("format")
    call["display_mode"] = data.get("display_mode")
    calls.append(call); log_path.write_text(json.dumps(calls), encoding="utf-8")
    if mode == "export_http500" and data.get("format") == "svg": return Response(500, "fake export error")
    if data.get("format") == "svg":
        if mode == "malformed_svg": return Response(200, "not svg", b"<html>error</html>")
        return Response(200, "", b'<svg xmlns="http://www.w3.org/2000/svg"><text>fixture</text></svg>')
    return Response(200, "", b"%PDF-1.4\nfixture\n%%EOF\n")
''', encoding="utf-8")

IDS = [f"GCF_{i:09d}.1" for i in range(1,197)]

def write_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

ANNOTATION = "[q1=0.7;q2=0.2;q3=0.1;f1=7;f2=2;f3=1;pp1=0.9;pp2=0.07;pp3=0.03;QC=1;EN=10]"
FLAT_LABEL = "0.7"
FLAT_NAME = "species_tree.itol_quartet_frequency.newick"

def make_project(case, preexisting=False, missing_host=False, receipt_mode="full",
                 bad_raw_hash=False, bad_flat_hash=False):
    project = case / "project"
    pipeline = project / "pipeline_output"
    pipeline.mkdir(parents=True)
    raw_text = "((" + f"{IDS[0]}:0.1,{IDS[1]}:0.1)'{ANNOTATION}':0.2," + ",".join(
        f"{x}:0.1" for x in IDS[2:]) + ");\n"
    flat_text = raw_text.replace("'" + ANNOTATION + "'", FLAT_LABEL)
    raw_tree = raw_text.encode("ascii")
    flat_tree = flat_text.encode("ascii")
    accessions = ("\n".join(IDS) + "\n").encode("ascii")
    binary_lines = ["DATASET_BINARY", "SEPARATOR\tTAB", "DATASET_LABEL\tDefense Systems",
                    "FIELD_LABELS\tRM\tCas\tAbi2\tCBASS\tBREX\tSeptu", "DATA"]
    for i, accession in enumerate(IDS):
        binary_lines.append(accession + "\t" + "\t".join(str((i + j) % 2) for j in range(6)))
    defense = ("\n".join(binary_lines) + "\n").encode("utf-8")
    host_lines = ["DATASET_COLORSTRIP", "SEPARATOR\tTAB", "DATASET_LABEL\tHost", "DATA"]
    for i, accession in enumerate(IDS):
        host_lines.append(f"{accession}\t#336699\tSynthetic host {i % 3}")
    host = ("\n".join(host_lines) + "\n").encode("utf-8")
    write_bytes(project / "species_tree.newick", raw_tree)
    write_bytes(project / "config" / "approved_accessions.txt", accessions)
    write_bytes(pipeline / "defense_systems.txt", defense)
    if not missing_host:
        write_bytes(pipeline / "host_colorstrip.txt", host)
    validation_dir = project / "reports" / "stage01" / "validation_full"
    write_bytes(validation_dir / FLAT_NAME, flat_tree)
    receipt = {
        "status": "PASS",
        "mode": receipt_mode,
        "input_sha256": {"species_tree.newick": hashlib.sha256(raw_tree).hexdigest()},
        "artifact_sha256": {FLAT_NAME: hashlib.sha256(flat_tree).hexdigest()},
    }
    if bad_raw_hash:
        receipt["input_sha256"]["species_tree.newick"] = "0" * 64
    if bad_flat_hash:
        receipt["artifact_sha256"][FLAT_NAME] = "f" * 64
    write_bytes(validation_dir / "validation_report.json",
                (json.dumps(receipt, sort_keys=True) + "\n").encode("utf-8"))
    if preexisting:
        out = pipeline / "itol"
        out.mkdir()
        write_bytes(out / "sentinel.txt", b"keep this exact existing content\n")
    expected = {"species_tree.tree": flat_tree, "01_defense_systems.txt": defense}
    if not missing_host:
        expected["02_host_colorstrip.txt"] = host
    return project, expected, raw_tree, flat_tree

def run_case(name, mode="success", preexisting=False, **fixture_options):
    case = TEST_ROOT / name
    case.mkdir()
    project, expected_assets, raw_tree, flat_tree = make_project(case, preexisting, **fixture_options)
    output = project / "pipeline_output" / "itol"
    env = os.environ.copy()
    env.update({"PYTHONPATH":str(FAKE), "MOCK_MODE":mode, "DUMMY_ITOL_KEY":DUMMY,
                "MOCK_CALL_LOG":str(case / "calls.json"), "CAPTURE_ZIP":str(case / "captured_upload.zip"),
                "KEY_READ_MARKER":str(case / "key_intercepted.txt")})
    proc = subprocess.run([str(PYTHON), str(SCRIPT), "--project", str(project)], capture_output=True, text=True, env=env)
    files = {p.name:p for p in output.iterdir()} if output.exists() else {}
    calls = json.loads((case / "calls.json").read_text(encoding="utf-8")) if (case / "calls.json").exists() else []
    return case, project, output, expected_assets, proc, files, calls, raw_tree, flat_tree

results = []
# Success: exact ZIP membership/raw bytes, form fields, HTTP settings, URL, SVG/PDF, and dummy-key containment.
case, project, output, assets, proc, files, calls, raw_tree, flat_tree = run_case("success_complete", "success")
assert proc.returncode == 0, (proc.stdout, proc.stderr)
assert proc.stdout.strip() == "https://itol.embl.de/tree/73421"
assert set(files) == {"upload.zip", "assets.json", "upload_response.txt", "tree_url.txt", "species_tree.circular.svg", "species_tree.circular.pdf"}
assert len(calls) == 3
up = calls[0]
assert up["url"] == "https://itol.embl.de/batch_uploader.cgi"
assert up["data_keys"] == ["APIkey", "projectName", "treeName"] and up["api_key_received"]
assert up["projectName"] == "LAB_Phylogenomics_196" and up["treeName"] == "Species_Tree_Final"
assert up["zip_field"] == ["zipFile"] and up["upload_filename"] == "species_tree.zip" and up["upload_mime"] == "application/zip"
assert up["timeout"] == [30,300] and up["allow_redirects"] is False
for c in calls[1:]:
    assert c["url"] == "https://itol.embl.de/batch_downloader.cgi"
    assert c["tree"] == "73421" and c["display_mode"] == "2" and c["timeout"] == [30,300] and c["allow_redirects"] is False
assert [c["format"] for c in calls[1:]] == ["svg", "pdf"]
with zipfile.ZipFile(case / "captured_upload.zip") as z:
    assert z.namelist() == ["species_tree.tree", "01_defense_systems.txt", "02_host_colorstrip.txt"]
    for name, data in assets.items(): assert z.read(name) == data
    assert all(DUMMY.encode() not in z.read(name) for name in z.namelist())
    assert z.read("species_tree.tree") == flat_tree and z.read("species_tree.tree") != raw_tree
manifest = json.loads((output / "assets.json").read_text(encoding="utf-8"))
assert manifest["source_species_tree.newick"]["sha256"] == hashlib.sha256(raw_tree).hexdigest()
assert manifest["species_tree.tree"]["sha256"] == hashlib.sha256(flat_tree).hexdigest()
assert raw_tree.decode("ascii").replace("'" + ANNOTATION + "'", FLAT_LABEL).encode("ascii") == flat_tree
assert (output / "upload.zip").read_bytes() == (case / "captured_upload.zip").read_bytes()
assert (output / "tree_url.txt").read_text(encoding="utf-8") == "https://itol.embl.de/tree/73421\n"
assert b"[REDACTED]" in (output / "upload_response.txt").read_bytes()
assert DUMMY.encode() not in (output / "upload_response.txt").read_bytes()
assert (output / "species_tree.circular.svg").read_bytes().startswith(b"<svg")
assert (output / "species_tree.circular.pdf").read_bytes().startswith(b"%PDF-")
assert DUMMY not in proc.stdout and DUMMY not in proc.stderr
assert (case / "key_intercepted.txt").exists()
results.append({"case":"success_complete","pass":True,"returncode":0,"zip_members":["species_tree.tree","01_defense_systems.txt","02_host_colorstrip.txt"],"raw_asset_bytes_preserved":True,"dummy_key_excluded_from_zip":True,"upload_form_and_export_parameters_verified":True,"redirects_disabled":True,"timeout":[30,300],"success_url_printed":True,"svg_pdf_written":True,"response_key_redacted":True,"key_open_intercepted":True})

# Upload errors and malformed responses must not expose the dummy key or begin exports.
for name, mode in [("upload_ERR","err"),("upload_HTTP500","http500"),("upload_no_SUCCESS","no_success")]:
    case, project, output, assets, proc, files, calls, raw_tree, flat_tree = run_case(name, mode)
    assert proc.returncode != 0 and DUMMY not in proc.stdout and DUMMY not in proc.stderr
    assert len(calls) == 1 and all(c["url"].endswith("batch_uploader.cgi") for c in calls)
    assert not any(p.name.startswith("species_tree.circular.") for p in files.values())
    if mode == "err": assert "upload failed" in proc.stderr.lower()
    if mode == "http500": assert "HTTP 500" in proc.stderr
    if mode == "no_success": assert "no valid SUCCESS" in proc.stderr
    results.append({"case":name,"pass":True,"returncode":proc.returncode,"calls":len(calls),"exports_started":False,"dummy_key_leaked":False})

# Invalid SVG and export HTTP failure leave no invalid export file and no key leak.
for name, mode, message in [("bad_svg","malformed_svg","not an SVG"),("export_HTTP500","export_http500","HTTP 500")]:
    case, project, output, assets, proc, files, calls, raw_tree, flat_tree = run_case(name, mode)
    assert proc.returncode != 0 and message.lower() in proc.stderr.lower()
    assert DUMMY not in proc.stdout and DUMMY not in proc.stderr
    assert not (output / "species_tree.circular.svg").exists()
    results.append({"case":name,"pass":True,"returncode":proc.returncode,"svg_saved":False,"dummy_key_leaked":False})

# Network exception includes fake key in exception text; script must suppress it.
case, project, output, assets, proc, files, calls, raw_tree, flat_tree = run_case("network_exception", "network_exception")
assert proc.returncode != 0 and "network failure" in proc.stderr.lower()
assert "RequestException" in proc.stderr and DUMMY not in proc.stdout and DUMMY not in proc.stderr
assert len(calls) == 1 and DUMMY not in (case / "calls.json").read_text(encoding="utf-8")
results.append({"case":"network_exception","pass":True,"returncode":proc.returncode,"dummy_key_leaked":False,"exception_type_only":True})

# Existing evidence folder is refused before reading even the dummy key or making a request.
case, project, output, assets, proc, files, calls, raw_tree, flat_tree = run_case("refuse_existing_output", "success", preexisting=True)
assert proc.returncode != 0 and "Refusing to overwrite" in proc.stderr
assert not calls and not (case / "key_intercepted.txt").exists()
assert sorted(p.name for p in output.iterdir()) == ["sentinel.txt"]
assert (output / "sentinel.txt").read_bytes() == b"keep this exact existing content\n"
results.append({"case":"refuse_existing_output","pass":True,"returncode":proc.returncode,"network_calls":0,"key_read":False,"sentinel_preserved":True})

# Receipt and mandatory-host gates must refuse before reading the fake credential or calling HTTP.
refusal_cases = [
    ("bad_raw_source_hash", {"bad_raw_hash": True}, "source hash"),
    ("bad_flat_artifact_hash", {"bad_flat_hash": True}, "flat q1-frequency tree"),
    ("pilot_receipt_refused", {"receipt_mode": "pilot"}, "full-pipeline validation receipt"),
    ("missing_host_refused", {"missing_host": True}, "host_colorstrip.txt"),
]
for name, fixture_options, message in refusal_cases:
    case, project, output, assets, proc, files, calls, raw_tree, flat_tree = run_case(
        name, "success", **fixture_options)
    assert proc.returncode != 0 and message.lower() in proc.stderr.lower(), (name, proc.stdout, proc.stderr)
    assert not calls and not (case / "key_intercepted.txt").exists(), (name, calls)
    assert not output.exists(), f"{name}: output dir created before prerequisite refusal"
    results.append({"case":name,"pass":True,"returncode":proc.returncode,
                    "network_calls":0,"key_read":False,"output_created":False})

receipt = {"receipt_type":"synthetic_itol_upload_api_tests","schema_version":2,"tested_source":str(SCRIPT),"source_sha256":hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),"python_executable":str(PYTHON),"network":"No real network calls; requests imported from local fake module.","key_handling":"Only a synthetic dummy token was supplied by sitecustomize intercepting exactly /mnt/c/itol.api-key.txt; real key was never read.","synthetic_tip_count":len(IDS),"structured_raw_tree_sha256":hashlib.sha256(raw_tree).hexdigest(),"flat_q1_tree_sha256":hashlib.sha256(flat_tree).hexdigest(),"structured_to_flat_proof":"The same synthetic topology and lengths were used; only the one quoted structured ASTRAL annotation was replaced with numeric q1=0.7. ZIP species_tree.tree was byte-checked against flat artifact, while manifest source hash matches raw tree.","cases":results,"all_passed":all(r["pass"] for r in results),"review_concerns":["Uploader writes upload.zip/assets.json before the HTTP request and upload_response/tree_url before exports; failure leaves partial evidence without a terminal status manifest.","Exports are written sequentially; a PDF failure can leave the SVG, and later runs are blocked by output-directory existence.","Success output tree URL is not itself proof that both exports completed; callers need exit status/output checks."]}
(TEST_ROOT / "results.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, indent=2))
