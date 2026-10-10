#!/usr/bin/env python3
"""Offline fake-HTTP tests for upload_itol_pilot.py using the real itolapi writer."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import zipfile
from unittest.mock import patch

from itolapi import ItolExport as RealItolExport


SOURCE = Path("/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196/scripts/upload_itol_pilot.py")
KEY_PATH = "/mnt/c/itol.api-key.txt"
DUMMY = "SYNTHETIC+KEY/84=never-real"
IDS = [f"GCF_{i:09d}.1" for i in range(1, 197)]
FLAT_NAME = "species_tree.itol_quartet_frequency.newick"
ANNOTATION = "[q1=0.7;q2=0.2;q3=0.1;f1=7;f2=2;f3=1;pp1=0.9;pp2=0.07;pp3=0.03;QC=1;EN=10]"


class FakeResponse:
    def __init__(self, status_code=200, text="", content=b""):
        self.status_code = status_code
        self.text = text
        self.content = content


def load_source():
    spec = importlib.util.spec_from_file_location("upload_itol_pilot_under_test", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import uploader source: {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if module.ItolExport is not RealItolExport:
        raise AssertionError("Uploader did not import the installed real ItolExport class")
    return module


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def make_project(case: Path, bad_hash=False, existing=False):
    project = case / "project"
    (project / "pilot_output").mkdir(parents=True)
    raw_text = "((" + f"{IDS[0]}:0.1,{IDS[1]}:0.1)'{ANNOTATION}':0.2," + ",".join(
        f"{value}:0.1" for value in IDS[2:]) + ");\n"
    flat_text = raw_text.replace("'" + ANNOTATION + "'", "0.7")
    raw = raw_text.encode("ascii")
    flat = flat_text.encode("ascii")
    write_bytes(project / "pilot_output" / "species_tree.newick", raw)
    write_bytes(project / "pilot_output" / FLAT_NAME, flat)
    report = {
        "status": "PASS",
        "marker_results": [{"marker": f"marker{i}"} for i in range(5)],
        "astral_result": {"tip_count": 196},
        "artifact_sha256": {
            "species_tree.newick": hashlib.sha256(raw).hexdigest(),
            FLAT_NAME: hashlib.sha256(flat).hexdigest(),
        },
    }
    if bad_hash:
        report["artifact_sha256"][FLAT_NAME] = "0" * 64
    validation_dir = project / "reports" / "stage01" / "local_pilot_20261010" / "completed"
    write_bytes(validation_dir / "validation_report.json",
                (json.dumps(report, sort_keys=True) + "\n").encode("utf-8"))
    output = project / "pilot_output" / "itol"
    if existing:
        output.mkdir(parents=True)
        write_bytes(output / "sentinel.txt", b"preserve existing pilot upload\n")
    return project, output, raw, flat


def run_case(module, case: Path, behavior="success", bad_hash=False, existing=False):
    project, output, raw, flat = make_project(case, bad_hash=bad_hash, existing=existing)
    calls = []
    key_reads = []
    captured_stdout, captured_stderr = io.StringIO(), io.StringIO()
    real_open = open

    def fake_open(file, *args, **kwargs):
        try:
            path = os.fspath(file)
        except TypeError:
            path = None
        if path == KEY_PATH:
            key_reads.append(path)
            return io.StringIO(DUMMY)
        return real_open(file, *args, **kwargs)

    def fake_post(url, data=None, files=None, timeout=None, allow_redirects=None):
        call = {"url": url, "data": dict(data or {}), "timeout": timeout,
                "allow_redirects": allow_redirects}
        if files:
            filename, package, mime = files["zipFile"]
            call["file"] = {"name": filename, "bytes": len(package), "mime": mime}
            if url.endswith("batch_uploader.cgi"):
                call["zip_bytes"] = package
        calls.append(call)
        if url.endswith("batch_uploader.cgi"):
            if behavior == "err":
                encoded = __import__("urllib.parse", fromlist=["quote"]).quote(DUMMY, safe="")
                return FakeResponse(200, f"ERR: fake rejection {DUMMY} {encoded}\n")
            return FakeResponse(200, f"notice {DUMMY}\nSUCCESS: 84021\n")
        extension = data["format"]
        if behavior == "malformed_export":
            return FakeResponse(200, content=b"<html>bad export</html>")
        if extension == "svg":
            return FakeResponse(200, content=b'<svg xmlns="http://www.w3.org/2000/svg"><text>mock</text></svg>')
        return FakeResponse(200, content=b"%PDF-1.4\nmock export\n%%EOF\n")

    result = None
    exception = None
    sys_argv = [str(SOURCE), "--project", str(project)]
    with (patch.object(sys, "argv", sys_argv),
          patch.object(module.time, "sleep", lambda *_: None),
          patch.object(module.requests, "post", side_effect=fake_post),
          patch("builtins.open", new=fake_open),
          redirect_stdout(captured_stdout), redirect_stderr(captured_stderr)):
        try:
            result = module.main()
        except Exception as error:
            exception = error
    return {
        "case": case.name, "project": project, "output": output, "raw": raw, "flat": flat,
        "result": result, "exception": exception, "calls": calls, "key_reads": key_reads,
        "stdout": captured_stdout.getvalue(), "stderr": captured_stderr.getvalue(),
    }


def run_all(root: Path) -> dict:
    if root.exists():
        raise FileExistsError(f"Refusing to reuse existing fixture directory: {root}")
    root.mkdir(parents=True)
    module = load_source()
    cases = []

    success = run_case(module, root / "success")
    assert success["exception"] is None and success["result"] == 0, success
    assert success["stdout"].strip() == "https://itol.embl.de/tree/84021"
    assert len(success["key_reads"]) == 1 and len(success["calls"]) == 3
    assert success["calls"][0]["data"]["APIkey"] == DUMMY
    assert [call["data"].get("format") for call in success["calls"][1:]] == ["svg", "pdf"]
    assert all(call["timeout"] == (30, 300) and call["allow_redirects"] is False
               for call in success["calls"])
    package = success["calls"][0]["zip_bytes"]
    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        assert archive.namelist() == ["pilot_5_markers_196_taxa.tree"]
        assert archive.read(archive.namelist()[0]) == success["flat"]
        assert DUMMY.encode() not in archive.read(archive.namelist()[0])
    out = success["output"]
    assert (out / "pilot_species_tree.circular.svg").read_bytes().startswith(b"<svg")
    assert (out / "pilot_species_tree.circular.pdf").read_bytes().startswith(b"%PDF-")
    assert (out / "tree_url.txt").read_text(encoding="utf-8") == "https://itol.embl.de/tree/84021\n"
    terminal = json.loads((out / "terminal.json").read_text(encoding="utf-8"))
    assert terminal["state"] == "UPLOAD_AND_EXPORTS_COMPLETE"
    assert terminal["toolkit"] == "itolapi==4.1.6"
    assert set(terminal["exports"]) == {"pilot_species_tree.circular.svg", "pilot_species_tree.circular.pdf"}
    all_files = [path for path in out.rglob("*") if path.is_file()]
    assert all(DUMMY.encode() not in path.read_bytes() for path in all_files)
    assert all(DUMMY not in success["stdout"] + success["stderr"] for _ in [0])
    cases.append({"case": "success_real_toolkit_writer_fake_transport", "passed": True,
                  "calls": len(success["calls"]), "key_read": True,
                  "zip_contains_flat_tree": True, "toolkit_writer_created_svg_pdf": True,
                  "terminal_complete": True, "dummy_absent_from_all_output_files": True})

    err = run_case(module, root / "err_response", behavior="err")
    assert err["exception"] is None and err["result"] == 1
    assert len(err["calls"]) == 1 and len(err["key_reads"]) == 1
    assert "ERR: fake rejection" in err["stderr"]
    assert DUMMY not in err["stderr"] and DUMMY not in (err["output"] / "upload_response.txt").read_text()
    assert not (err["output"] / "pilot_species_tree.circular.svg").exists()
    err_terminal = json.loads((err["output"] / "terminal.json").read_text(encoding="utf-8"))
    assert err_terminal["state"] == "UPLOAD_REQUEST_STARTED"
    assert DUMMY not in json.dumps(err_terminal)
    cases.append({"case": "ERR_response_redacted_stops_exports", "passed": True,
                  "calls": 1, "key_redacted": True, "exports_started": False})

    bad = run_case(module, root / "bad_hash", bad_hash=True)
    assert isinstance(bad["exception"], ValueError) and "validation receipt" in str(bad["exception"]).lower()
    assert not bad["calls"] and not bad["key_reads"] and not bad["output"].exists()
    cases.append({"case": "bad_flat_hash_refused_pre_key_http", "passed": True,
                  "network_calls": 0, "key_reads": 0, "output_created": False})

    existing = run_case(module, root / "existing_output", existing=True)
    assert isinstance(existing["exception"], FileExistsError)
    assert not existing["calls"] and not existing["key_reads"]
    assert (existing["output"] / "sentinel.txt").read_bytes() == b"preserve existing pilot upload\n"
    cases.append({"case": "existing_output_refused_unmodified", "passed": True,
                  "network_calls": 0, "key_reads": 0, "sentinel_preserved": True})

    malformed = run_case(module, root / "malformed_export", behavior="malformed_export")
    assert malformed["exception"] is None and malformed["result"] == 1
    assert len(malformed["calls"]) == 2 and len(malformed["key_reads"]) == 1
    assert not (malformed["output"] / "pilot_species_tree.circular.svg").exists()
    malformed_terminal = json.loads((malformed["output"] / "terminal.json").read_text(encoding="utf-8"))
    assert malformed_terminal["state"] == "UPLOADED_EXPORT_PENDING"
    cases.append({"case": "malformed_export_not_saved", "passed": True,
                  "upload_and_one_export_call": True, "malformed_svg_not_written": True})

    return {
        "schema": "itol_pilot_upload_offline_tests_v1",
        "status": "PASS",
        "tested_source": str(SOURCE),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "python": sys.version,
        "itolapi_version": importlib.metadata.version("itolapi"),
        "real_itol_export_class": str(RealItolExport),
        "http": "All requests.post calls replaced by local fake; no network used.",
        "credential": "builtins.open intercepted only for exact /mnt/c/itol.api-key.txt; dummy value only.",
        "structured_raw_and_flat_tree": {
            "raw_sha256": hashlib.sha256(success["raw"]).hexdigest(),
            "flat_q1_sha256": hashlib.sha256(success["flat"]).hexdigest(),
            "same_topology_lengths_only_internal_label_changed": success["raw"].decode("ascii").replace(
                "'" + ANNOTATION + "'", "0.7").encode("ascii") == success["flat"],
        },
        "cases": cases,
        "all_passed": all(case["passed"] for case in cases),
    }


if __name__ == "__main__":
    fixture_root = Path(__file__).resolve().parent / "fixtures_run01"
    result = run_all(fixture_root)
    receipt_path = Path(__file__).resolve().parent / "results.json"
    if receipt_path.exists():
        raise FileExistsError(f"Refusing to overwrite test receipt: {receipt_path}")
    receipt_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
