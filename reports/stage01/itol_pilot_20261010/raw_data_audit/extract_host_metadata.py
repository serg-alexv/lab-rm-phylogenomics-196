#!/usr/bin/env python3
"""Create a read-only-source, raw NCBI BioSample host metadata audit."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_COLUMNS = [
    "assembly_accession", "display_label", "operational_group",
    "biosample_host_raw", "biosample_isolation_source_raw",
    "biosample_hostDisease_raw", "report_accession", "report_currentAccession",
    "source_report_selected_record_line", "source_report_relative_path", "source_report_sha256",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def raw_text(value: object, accession: str, field: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{accession}: {field} is not string/null")
    return value


def write_exclusive(path: Path, data: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path,
                        default=Path(r"G:\My Drive\LAB_RM\lab-rm-phylogenomics-196"))
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root = args.project_root.resolve(strict=True)
    output = args.output_dir.resolve(strict=True)
    if output == root or root in output.parents:
        raise ValueError("output directory must be outside the canonical project tree")
    for name in ("host_metadata_raw.tsv", "audit.json", "README.md"):
        if (output / name).exists():
            raise FileExistsError(output / name)

    panel_path = root / "config" / "approved_panel.tsv"
    stages_path = root / "status" / "stages.tsv"
    with panel_path.open(encoding="utf-8-sig", newline="") as stream:
        panel = list(csv.DictReader(stream, delimiter="\t"))
    required = {"assembly_accession", "display_label", "operational_group"}
    if not panel or not required.issubset(panel[0]):
        raise ValueError("approved panel lacks required identity/display fields")
    accessions = [row["assembly_accession"] for row in panel]
    if len(panel) != 196 or len(set(accessions)) != 196:
        raise ValueError("approved panel must contain 196 unique accessions")

    with stages_path.open(encoding="utf-8-sig", newline="") as stream:
        stage_rows = list(csv.DictReader(stream, delimiter="\t"))
    stage_matches = [row for row in stage_rows if row.get("stage") == "5_rm_inventory"]
    if len(stage_matches) != 1:
        raise ValueError("expected one stage5 row in status/stages.tsv")
    stage5 = stage_matches[0]
    if any(stage5.get(field) != "NOT_RUN" for field in ("execution", "validation", "publication")):
        raise ValueError(f"stage5 state is not the expected NOT_RUN status: {stage5}")

    joined = []
    source_reports = []
    old_aliases = []
    for row in panel:
        accession = row["assembly_accession"]
        report_path = (root / "data" / "raw_ncbi" / accession / "package" /
                       "ncbi_dataset" / "data" / "assembly_data_report.jsonl")
        records = [json.loads(line) for line in report_path.read_text(encoding="utf-8").splitlines()]
        matching = [(index, report) for index, report in enumerate(records, start=1)
                    if report.get("currentAccession") == accession]
        if not matching:
            raise ValueError(f"{accession}: no JSONL record has the exact currentAccession")
        relpath = report_path.relative_to(root).as_posix()
        for index, candidate in matching:
            if candidate.get("accession") != accession:
                old_aliases.append({"approved_accession": accession,
                                    "report_accession": candidate.get("accession"),
                                    "currentAccession": candidate.get("currentAccession"),
                                    "record_line": index,
                                    "source_report_relative_path": relpath})
        exact = [(index, candidate) for index, candidate in matching
                 if candidate.get("accession") == accession]
        if len(exact) == 1:
            selected_line, report = exact[0]
        elif not exact and len(matching) == 1:
            selected_line, report = matching[0]
        else:
            raise ValueError(f"{accession}: ambiguous current report records")
        current = report["currentAccession"]
        report_accession = report.get("accession") or ""
        biosample = (report.get("assemblyInfo") or {}).get("biosample") or {}
        report_hash = sha256(report_path)
        joined.append({
            "assembly_accession": accession,
            "display_label": row["display_label"],
            "operational_group": row["operational_group"],
            "biosample_host_raw": raw_text(biosample.get("host"), accession, "biosample.host"),
            "biosample_isolation_source_raw": raw_text(biosample.get("isolationSource"), accession, "biosample.isolationSource"),
            "biosample_hostDisease_raw": raw_text(biosample.get("hostDisease"), accession, "biosample.hostDisease"),
            "report_accession": report_accession,
            "report_currentAccession": current,
            "source_report_selected_record_line": selected_line,
            "source_report_relative_path": relpath,
            "source_report_sha256": report_hash,
        })
        source_reports.append({"assembly_accession": accession, "path": relpath, "sha256": report_hash})
    if [item["assembly_accession"] for item in joined] != accessions:
        raise AssertionError("output order differs from approved panel")

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=OUTPUT_COLUMNS, delimiter="\t",
                            lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    writer.writerows(joined)
    table = buffer.getvalue().encode("utf-8")
    table_sha = hashlib.sha256(table).hexdigest()

    def stats(column: str) -> dict[str, int]:
        vals = [item[column] for item in joined]
        present = [value for value in vals if value.strip()]
        return {
            "nonempty_raw_strings_including_literal_missing": len(present),
            "literal_string_missing": sum(value.strip().casefold() == "missing" for value in present),
            "unique_nonempty_raw_strings": len(set(present)),
            "blank_cells_from_null_or_absent_source_value": len(vals) - len(present),
        }

    script_path = Path(__file__).resolve()
    evidence = {
        "audit_kind": "raw_ncbi_biosample_host_metadata_join",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "interpretation": "Raw source-reported metadata only; no taxonomy reclassification, host-category inference, defense calls, or biological-absence values.",
        "join": {
            "approved_panel_key": "assembly_accession",
            "source_report_key": "currentAccession",
            "comparison": "exact string equality; all 196 passed",
            "approved_panel_rows": len(panel),
            "unique_approved_accessions": len(set(accessions)),
        },
        "stage5_state_evidence": {
            "path": stages_path.relative_to(root).as_posix(),
            "sha256": sha256(stages_path),
            "row": stage5,
            "meaning": "Stage 5 is marked NOT_RUN in execution, validation, and publication columns; this is status evidence, not a biological absence call.",
        },
        "approved_panel_source": {
            "path": panel_path.relative_to(root).as_posix(),
            "sha256": sha256(panel_path),
        },
        "source_report_count": len(source_reports),
        "source_reports": source_reports,
        "older_report_accession_aliases": old_aliases,
        "older_report_accession_alias_record_count": len(old_aliases),
        "older_report_accession_alias_source_file_count": len({item["source_report_relative_path"] for item in old_aliases}),
        "raw_field_summary": {
            "biosample.host": stats("biosample_host_raw"),
            "biosample.isolationSource": stats("biosample_isolation_source_raw"),
            "biosample.hostDisease": stats("biosample_hostDisease_raw"),
        },
        "output": {
            "path": "host_metadata_raw.tsv",
            "rows_excluding_header": len(joined),
            "columns": OUTPUT_COLUMNS,
            "bytes": len(table),
            "sha256": table_sha,
            "null_handling": "JSON null or absent field becomes an empty TSV cell; literal strings such as 'missing' are retained verbatim.",
        },
        "reproduction_source": {"path": script_path.name, "sha256": sha256(script_path)},
    }
    readme = f"""# Raw NCBI host metadata audit

This is a one-to-one join of the canonical 196 approved accessions to downloaded NCBI `assembly_data_report.jsonl` BioSample fields. It is metadata evidence only: it contains no DefenseFinder, PADLOC, or other defense-system calls, and creates no defense 0/1/unknown matrix.

`host_metadata_raw.tsv` joins `approved_panel.tsv:assembly_accession` to each report's `currentAccession` by exact string equality. It copies `biosample.host`, `biosample.isolationSource`, and `biosample.hostDisease` as source-reported strings. JSON null or absent values become blank cells; literal source strings such as `missing` are retained. No host-category inference or taxonomy reclassification is performed.

`audit.json` records SHA-256 provenance for the approved panel, `status/stages.tsv`, and all 196 source reports. Three source files contain older `accession` aliases (four alias records total); the exact current-accession record is selected when a report contains multiple records, and aliases are preserved in the audit with source line numbers. Stage 5 is recorded NOT_RUN for execution, validation, and publication. That is workflow status, not biological absence.

Reproduce with Python 3 (the extractor refuses to overwrite any result file):

```powershell
python .\\extract_host_metadata.py --project-root 'G:\\My Drive\\LAB_RM\\lab-rm-phylogenomics-196' --output-dir .
```

Extractor SHA-256: `{sha256(script_path)}`  
TSV SHA-256: `{table_sha}`
"""
    write_exclusive(output / "host_metadata_raw.tsv", table)
    write_exclusive(output / "audit.json", (json.dumps(evidence, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    write_exclusive(output / "README.md", readme.encode("utf-8"))
    print(json.dumps({
        "output_dir": str(output), "rows": len(joined),
        "host": evidence["raw_field_summary"]["biosample.host"],
        "isolationSource": evidence["raw_field_summary"]["biosample.isolationSource"],
        "hostDisease": evidence["raw_field_summary"]["biosample.hostDisease"],
        "stage5": stage5, "tsv_sha256": table_sha,
        "script_sha256": sha256(script_path),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
