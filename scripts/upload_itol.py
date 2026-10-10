#!/usr/bin/env python3
"""Direct official iTOL batch upload and circular SVG/PDF export.

API contract: https://itol.embl.de/help.cgi#batch
The key stays in /mnt/c/itol.api-key.txt and is never included in the ZIP.
Uploads are never retried automatically because a timeout may follow success.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import time
import zipfile

import requests


UPLOAD_URL = "https://itol.embl.de/batch_uploader.cgi"
EXPORT_URL = "https://itol.embl.de/batch_downloader.cgi"


def dataset_ids(data, kind, columns=None):
    lines = data.decode("utf-8-sig").splitlines()
    if not lines or lines[0] != kind or "SEPARATOR\tTAB" not in lines:
        raise ValueError(f"Expected a tab-separated {kind} dataset")
    if "DATA" not in lines:
        raise ValueError(f"Missing DATA section in {kind}")
    ids = []
    for line in lines[lines.index("DATA") + 1:]:
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if columns is not None and len(fields) != columns:
            raise ValueError(f"Wrong data column count in {kind}")
        if len(fields) < 2 or not fields[0]:
            raise ValueError(f"Invalid data row in {kind}")
        if kind == "DATASET_BINARY" and any(x not in {"0", "1"} for x in fields[1:]):
            raise ValueError("Defense values must be 0 or 1; unknown is not absence")
        ids.append(fields[0])
    if not ids or len(ids) != len(set(ids)):
        raise ValueError(f"Empty or duplicate IDs in {kind}")
    return set(ids)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    project = args.project.resolve()
    output = project / "pipeline_output" / "itol"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing upload evidence: {output}")

    raw_tree = (project / "species_tree.newick").read_bytes()
    validation_dir = project / "reports" / "stage01" / "validation_full"
    validation = json.loads((validation_dir / "validation_report.json").read_text(encoding="utf-8"))
    if validation.get("status") != "PASS" or validation.get("mode") != "full":
        raise ValueError("A successful full-pipeline validation receipt is required before upload")
    if validation.get("input_sha256", {}).get("species_tree.newick") != hashlib.sha256(raw_tree).hexdigest():
        raise ValueError("Final ASTRAL tree no longer matches the validated source hash")
    flat_name = "species_tree.itol_quartet_frequency.newick"
    tree = (validation_dir / flat_name).read_bytes()
    if validation.get("artifact_sha256", {}).get(flat_name) != hashlib.sha256(tree).hexdigest():
        raise ValueError("Flat q1-frequency tree no longer matches the validation receipt")
    text = tree.decode("utf-8-sig").strip()
    if not text.startswith("(") or not text.endswith(";"):
        raise ValueError("species_tree.newick is not a nonempty Newick tree")
    # This project uses exact versioned GCF accessions as terminal identifiers.
    tips = re.findall(r"GCF_\d+\.\d+", text)
    approved = set((project / "config" / "approved_accessions.txt").read_text().splitlines())
    if len(approved) != 196 or len(tips) != 196 or len(set(tips)) != 196 or set(tips) != approved:
        raise ValueError("Final tree must contain exactly the approved 196 unique accessions")

    preferred = project / "pipeline_output" / "defense_systems.txt"
    legacy = project / "pipeline_output" / "defense_systems_heatmap.txt"
    if preferred.exists() and legacy.exists() and preferred.read_bytes() != legacy.read_bytes():
        raise ValueError("The two defense dataset filenames contain different data")
    defense_path = preferred if preferred.exists() else legacy
    defense = defense_path.read_bytes()
    if dataset_ids(defense, "DATASET_BINARY", 7) != approved:
        raise ValueError("Defense dataset IDs must exactly match the final tree")
    expected_labels = "FIELD_LABELS\tRM\tCas\tAbi2\tCBASS\tBREX\tSeptu"
    if expected_labels not in defense.decode("utf-8-sig").splitlines():
        raise ValueError("Defense system fields do not match the approved six-column order")

    assets = {"species_tree.tree": tree, "01_defense_systems.txt": defense}
    host_path = project / "pipeline_output" / "host_colorstrip.txt"
    host = host_path.read_bytes()
    if dataset_ids(host, "DATASET_COLORSTRIP", 3) != approved:
        raise ValueError("Host dataset IDs must exactly match the final tree")
    assets["02_host_colorstrip.txt"] = host

    with open("/mnt/c/itol.api-key.txt", "r", encoding="utf-8-sig") as handle:
        token = handle.read().strip()
    if not token or any(char.isspace() for char in token):
        raise ValueError("The iTOL key file must contain one nonempty token")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in assets.items():
            archive.writestr(name, content)
    package = buffer.getvalue()
    output.mkdir()
    with (output / "upload.zip").open("xb") as handle:
        handle.write(package)
    manifest = {name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                for name, data in assets.items()}
    manifest["source_species_tree.newick"] = {"bytes": len(raw_tree), "sha256": hashlib.sha256(raw_tree).hexdigest(),
                                            "note": "Raw ASTRAL preserved locally; ZIP contains validated flat q1-frequency derivative."}
    with (output / "assets.json").open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")

    # APIkey is case-sensitive; the official uploader accepts one ZIP file.
    response = requests.post(
        UPLOAD_URL,
        data={"APIkey": token, "projectName": "LAB_Phylogenomics_196",
              "treeName": "Species_Tree_Final"},
        files={"zipFile": ("species_tree.zip", package, "application/zip")},
        timeout=(30, 300),
        allow_redirects=False,
    )
    clean_response = response.text.replace(token, "[REDACTED]")
    with (output / "upload_response.txt").open("x", encoding="utf-8") as handle:
        handle.write(clean_response)
    if not 200 <= response.status_code < 300:
        raise ValueError(f"iTOL upload returned HTTP {response.status_code}; no automatic retry")
    lines = [line.strip() for line in clean_response.splitlines() if line.strip()]
    if any(line.startswith("ERR") for line in lines):
        raise ValueError("iTOL upload failed: " + " | ".join(lines)[:1000])
    success = re.fullmatch(r"SUCCESS:\s*(\d+)", lines[-1]) if lines else None
    if success is None:
        raise ValueError("iTOL returned no valid SUCCESS record; no automatic retry")
    tree_id = success.group(1)
    url = "https://itol.embl.de/tree/" + tree_id
    with (output / "tree_url.txt").open("x", encoding="utf-8") as handle:
        handle.write(url + "\n")
    print(url, flush=True)
    for warning in lines[:-1]:
        print(warning, file=sys.stderr)

    # Circular mode is an export option, not a documented upload parameter.
    for extension in ("svg", "pdf"):
        time.sleep(3)
        exported = requests.post(
            EXPORT_URL,
            data={"tree": tree_id, "format": extension, "display_mode": "2"},
            timeout=(30, 300),
            allow_redirects=False,
        )
        content = exported.content
        if not 200 <= exported.status_code < 300:
            raise ValueError(f"iTOL {extension} export returned HTTP {exported.status_code}")
        if extension == "pdf" and not content.startswith(b"%PDF-"):
            raise ValueError("iTOL returned an error or invalid PDF export")
        if extension == "svg":
            from xml.etree import ElementTree
            try:
                root = ElementTree.fromstring(content)
            except ElementTree.ParseError:
                raise ValueError("iTOL returned an error or invalid SVG export") from None
            if root.tag not in {"svg", "{http://www.w3.org/2000/svg}svg"}:
                raise ValueError("iTOL export is not an SVG document")
        with (output / f"species_tree.circular.{extension}").open("xb") as handle:
            handle.write(content)


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as error:
        print(f"iTOL network failure ({type(error).__name__}); no automatic retry", file=sys.stderr)
        raise SystemExit(1)
    except (OSError, ValueError) as error:
        print(f"iTOL failure: {error}", file=sys.stderr)
        raise SystemExit(1)
