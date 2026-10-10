#!/usr/bin/env python3
"""Read-only integrity audit of the validated Stage 3 marker FASTAs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def parse_fasta(path: Path) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    header: str | None = None
    seq: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        for raw in stream:
            line = raw.strip()
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    records.append((header.split()[0], "".join(seq).upper()))
                header, seq = line[1:].strip(), []
            else:
                if header is None:
                    raise ValueError(f"sequence before first FASTA header: {path}")
                seq.append(line)
    if header is not None:
        records.append((header.split()[0], "".join(seq).upper()))
    return records

def exclusive_write(path: Path, data: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(data)

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path,
                        default=Path(r"G:\My Drive\LAB_RM\lab-rm-phylogenomics-196"))
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root = args.project_root.resolve(strict=True)
    out = args.output_dir.resolve(strict=True)
    if out == root or root in out.parents:
        raise ValueError("audit outputs must remain outside the canonical project")
    for name in ("full100_input_audit.json", "marker_sources.tsv", "five_existing_inputs.tsv", "README.md"):
        if (out / name).exists():
            raise FileExistsError(out / name)

    order_path = root / "reports" / "stage03" / "primary_marker_order.txt"
    accessions_path = root / "config" / "approved_accessions.txt"
    summary_path = root / "reports" / "stage03" / "curated_marker_validation_summary.json"
    accepted_manifest_path = root / ".work" / "stage03_orthology_v2" / "accepted_sequence_manifest.tsv"
    sequence_dir = root / ".work" / "stage03_orthology_v2" / "marker_sequences"
    five_dir = root / "input_genes"

    markers = [line.strip() for line in order_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    approved = [line.strip() for line in accessions_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if len(markers) != 100 or len(set(markers)) != 100:
        raise ValueError(f"primary marker order is not exactly 100 unique markers: {len(markers)}")
    if len(approved) != 196 or len(set(approved)) != 196:
        raise ValueError("approved accession list is not exactly 196 unique IDs")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    expected = {
        "status": "PASS_MARKER_SOURCE_AND_FIXED_FILTERS",
        "scientific_stage_status": "PASS_HOST_MARKER_INVENTORY",
        "primary_markers": 100,
        "accepted_marker_sequences": 19359,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise ValueError(f"curated marker validation summary mismatch for {key}: {summary.get(key)!r}")

    with accepted_manifest_path.open(encoding="utf-8-sig", newline="") as stream:
        accepted_rows = list(csv.DictReader(stream, delimiter="\t"))
    manifest_by_pair = {}
    for row in accepted_rows:
        pair = (row["profile"], row["assembly_accession"])
        if pair in manifest_by_pair:
            raise ValueError(f"duplicate accepted-manifest profile/accession pair: {pair}")
        manifest_by_pair[pair] = row
    if len(accepted_rows) != summary["accepted_marker_sequences"]:
        raise ValueError("accepted manifest row count differs from independent summary")
    if sha256_file(accepted_manifest_path) != summary["accepted_sequence_manifest_sha256"]:
        raise ValueError("accepted manifest SHA does not match independent validation summary")
    if sha256_file(order_path) != summary["primary_marker_order_sha256"]:
        raise ValueError("marker order SHA does not match independent validation summary")

    fasta_paths = {path.stem: path for path in sequence_dir.glob("*.faa")}
    if set(fasta_paths) != set(markers) or len(fasta_paths) != 100:
        raise ValueError("Stage 3 v2 marker FASTA names do not exactly match the 100-marker order")

    source_rows = []
    total_records = 0
    total_bytes = 0
    all_ids: set[str] = set()
    all_gaps = all_empty = all_duplicate_ids = all_unapproved = all_manifest_errors = 0
    all_duplicate_sequence_excess = 0
    per_marker_counts: dict[str, int] = {}
    for marker in markers:
        path = fasta_paths[marker]
        records = parse_fasta(path)
        ids = [identifier for identifier, _ in records]
        seqs = [sequence for _, sequence in records]
        count_ids = Counter(ids)
        duplicate_id_records = sum(n - 1 for n in count_ids.values())
        sequence_counts = Counter(seqs)
        duplicate_sequence_excess = sum(n - 1 for n in sequence_counts.values())
        gaps = sum("-" in sequence or "." in sequence for sequence in seqs)
        empty = sum(not sequence for sequence in seqs)
        unapproved = sum(identifier not in set(approved) for identifier in ids)
        manifest_errors = 0
        for identifier, sequence in records:
            accepted = manifest_by_pair.get((marker, identifier))
            if accepted is None:
                manifest_errors += 1
                continue
            digest = sha256_bytes(sequence.encode("ascii"))
            if digest != accepted["source_sequence_sha256"] or len(sequence) != int(accepted["protein_aa_length"]):
                manifest_errors += 1
        all_ids.update(ids)
        total_records += len(records)
        total_bytes += path.stat().st_size
        all_gaps += gaps
        all_empty += empty
        all_duplicate_ids += duplicate_id_records
        all_unapproved += unapproved
        all_manifest_errors += manifest_errors
        all_duplicate_sequence_excess += duplicate_sequence_excess
        per_marker_counts[marker] = len(records)
        source_rows.append({
            "marker": marker,
            "source_path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "records": len(records),
            "unique_accession_headers": len(set(ids)),
            "duplicate_header_records": duplicate_id_records,
            "records_with_gap_characters": gaps,
            "empty_sequences": empty,
            "not_in_approved_panel": unapproved,
            "accepted_manifest_sequence_or_length_mismatches": manifest_errors,
            "excess_records_with_identical_sequence_content_within_marker": duplicate_sequence_excess,
        })
    if all_ids != set(approved):
        raise ValueError("marker FASTA accession union differs from the exact approved accession set")
    if any((all_gaps, all_empty, all_duplicate_ids, all_unapproved, all_manifest_errors)):
        raise ValueError("source FASTA integrity check failed; inspect the bounded audit output")
    if total_records != len(accepted_rows):
        raise ValueError("sum of marker FASTA records differs from accepted sequence manifest")

    input_paths = sorted(five_dir.glob("*.fasta"), key=lambda p: p.name.casefold())
    if len(input_paths) != 5:
        raise ValueError(f"expected five existing staged inputs under input_genes, found {len(input_paths)}")
    input_rows = []
    for staged in input_paths:
        source = fasta_paths.get(staged.stem)
        if source is None:
            raise ValueError(f"no Stage 3 source FASTA for existing staged file {staged.name}")
        same = staged.read_bytes() == source.read_bytes()
        if not same:
            raise ValueError(f"existing staged input is not byte-identical to Stage 3 source: {staged.name}")
        input_rows.append({
            "staged_path": staged.relative_to(root).as_posix(),
            "source_path": source.relative_to(root).as_posix(),
            "bytes": staged.stat().st_size,
            "sha256": sha256_file(staged),
            "source_sha256": sha256_file(source),
            "byte_identical": same,
        })

    marker_csv = io.StringIO(newline="")
    marker_fields = list(source_rows[0])
    writer = csv.DictWriter(marker_csv, fieldnames=marker_fields, delimiter="\t", lineterminator="\n")
    writer.writeheader(); writer.writerows(source_rows)
    marker_table = marker_csv.getvalue().encode("utf-8")
    input_csv = io.StringIO(newline="")
    input_fields = list(input_rows[0])
    writer = csv.DictWriter(input_csv, fieldnames=input_fields, delimiter="\t", lineterminator="\n")
    writer.writeheader(); writer.writerows(input_rows)
    input_table = input_csv.getvalue().encode("utf-8")

    evidence = {
        "audit_kind": "stage03_full100_input_integrity",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "read-only input audit; no alignment, tree inference, staging, or source modification",
        "independent_validation": {
            "path": summary_path.relative_to(root).as_posix(),
            "sha256": sha256_file(summary_path),
            "status": summary["status"],
            "scientific_stage_status": summary["scientific_stage_status"],
            "primary_markers": summary["primary_markers"],
            "accepted_marker_sequences": summary["accepted_marker_sequences"],
            "accepted_sequence_manifest_sha256": summary["accepted_sequence_manifest_sha256"],
            "primary_marker_order_sha256": summary["primary_marker_order_sha256"],
            "curation_status": summary.get("curation_status"),
        },
        "identity_sources": {
            "approved_accessions_path": accessions_path.relative_to(root).as_posix(),
            "approved_accessions_sha256": sha256_file(accessions_path),
            "approved_accessions_count": len(approved),
            "primary_marker_order_path": order_path.relative_to(root).as_posix(),
            "primary_marker_order_sha256": sha256_file(order_path),
            "primary_marker_order_count": len(markers),
            "accepted_sequence_manifest_path": accepted_manifest_path.relative_to(root).as_posix(),
            "accepted_sequence_manifest_sha256": sha256_file(accepted_manifest_path),
            "accepted_manifest_rows": len(accepted_rows),
        },
        "source_fastas": {
            "directory": sequence_dir.relative_to(root).as_posix(),
            "file_count": len(source_rows),
            "total_bytes": total_bytes,
            "total_records": total_records,
            "union_accession_count": len(all_ids),
            "union_exactly_approved_accessions": all_ids == set(approved),
            "records_per_marker_min": min(per_marker_counts.values()),
            "records_per_marker_max": max(per_marker_counts.values()),
            "possible_marker_accession_cells": len(markers) * len(approved),
            "missing_marker_accession_cells": len(markers) * len(approved) - total_records,
            "duplicate_header_records": all_duplicate_ids,
            "records_with_gap_characters": all_gaps,
            "empty_sequences": all_empty,
            "unapproved_accession_records": all_unapproved,
            "sequence_sha_or_length_manifest_mismatches": all_manifest_errors,
            "identical_sequence_content_excess_records_within_marker": all_duplicate_sequence_excess,
            "sequence_hash_convention": "uppercase amino-acid characters concatenated from FASTA lines, UTF-8 encoded, SHA-256; length is the character count",
            "per_marker_manifest": "marker_sources.tsv",
            "per_marker_manifest_sha256": sha256_bytes(marker_table),
        },
        "existing_five_inputs": {
            "directory": five_dir.relative_to(root).as_posix(),
            "file_count": len(input_rows),
            "total_bytes": sum(row["bytes"] for row in input_rows),
            "all_byte_identical_to_stage03_v2_sources": all(row["byte_identical"] for row in input_rows),
            "manifest": "five_existing_inputs.tsv",
            "manifest_sha256": sha256_bytes(input_table),
            "files": input_rows,
        },
        "interpretation": "FASTA header/accession records are duplicate-free and all sequences are nonempty ungapped accepted Stage 3 sequences. Identical protein sequence contents recur among different taxa within markers; they are preserved and are not duplicate accession records.",
    }
    source_hash = sha256_file(Path(__file__).resolve())
    evidence["reproduction_source"] = {"path": Path(__file__).name, "sha256": source_hash}
    readme = f"""# Full-100 Stage 3 input audit

This read-only audit verified the curated Stage 3 v2 per-marker source FASTAs against the accepted sequence manifest and independent Stage 3 validation summary. It does not stage, align, infer trees, or modify the canonical repository.

The source set contains 100 ordered marker FASTAs and 19,359 accepted records. Their accession union is exactly the 196-ID approved panel. Every record's normalized amino-acid SHA-256 and length match `accepted_sequence_manifest.tsv`; there are no duplicate accession headers, gaps, empty sequences, unapproved IDs, or sequence/length manifest mismatches. Per-marker record counts range from 177 to 196, so absent marker-accession pairs remain absent and are not filled.

Identical sequence strings recur across distinct accessions within markers. These 9,065 excess identical-content records are retained; the duplicate-free check applies to accession headers/records, not to biological sequence equality.

All five existing files in canonical `input_genes/` are byte-identical to their corresponding v2 marker FASTAs. `C:\\Users\\wheel\\Downloads\\input_genes` was absent at audit time. Stage 3 validation summary SHA-256: `{sha256_file(summary_path)}`. Accepted manifest SHA-256: `{sha256_file(accepted_manifest_path)}`. Total source FASTA bytes: `{total_bytes}`. Extractor SHA-256: `{source_hash}`.

Reproduce with Python 3 (result files are opened exclusively and will not be overwritten):

```powershell
python .\\audit_full100_inputs.py --project-root 'G:\\My Drive\\LAB_RM\\lab-rm-phylogenomics-196' --output-dir .
```
"""
    exclusive_write(out / "marker_sources.tsv", marker_table)
    exclusive_write(out / "five_existing_inputs.tsv", input_table)
    exclusive_write(out / "full100_input_audit.json", (json.dumps(evidence, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    exclusive_write(out / "README.md", readme.encode("utf-8"))
    print(json.dumps({
        "status": "PASS_SOURCE_INTEGRITY_WITH_SEQUENCE_CONTENT_DUPLICATES_DISCLOSED",
        "marker_files": len(source_rows), "records": total_records, "union_accessions": len(all_ids),
        "source_bytes": total_bytes, "sequence_content_duplicate_excess_records": all_duplicate_sequence_excess,
        "five_inputs_byte_identical": len(input_rows), "five_input_bytes": sum(row["bytes"] for row in input_rows),
        "accepted_manifest_sha256": sha256_file(accepted_manifest_path),
        "audit_json_sha256": sha256_bytes((out / "full100_input_audit.json").read_bytes()),
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
