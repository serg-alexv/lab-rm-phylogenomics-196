#!/usr/bin/env python3
"""Read-only validator for the full100 MAFFT alignment outputs."""
import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def parse_fasta(path):
    records = {}
    header = None
    chunks = []
    errors = []
    def finish():
        if header is None:
            return
        seq = ''.join(chunks).upper()
        if not seq:
            errors.append(f'{path.name}: empty sequence for {header}')
        if header in records:
            errors.append(f'{path.name}: duplicate header {header}')
        else:
            records[header] = seq
    with path.open('r', encoding='utf-8', newline=None) as stream:
        for line_no, raw in enumerate(stream, 1):
            line = raw.strip()
            if not line:
                continue
            if line.startswith('>'):
                finish()
                header = line[1:].split()[0] if line[1:].split() else ''
                chunks = []
                if not header:
                    errors.append(f'{path.name}:{line_no}: empty FASTA header')
            else:
                if header is None:
                    errors.append(f'{path.name}:{line_no}: sequence before first header')
                else:
                    chunks.append(''.join(line.split()))
    finish()
    return records, errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--input-manifest', required=True, type=Path)
    ap.add_argument('--accepted-audit', required=True, type=Path)
    args = ap.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    root = args.root
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    inputs = root / 'input_genes'
    alignments = root / 'pipeline_output' / 'alignments'
    order_path = root / 'reports' / 'stage03' / 'primary_marker_order.txt'
    approved_path = root / 'config' / 'approved_accessions.txt'
    errors = []
    order = [x.strip() for x in order_path.read_text(encoding='utf-8').splitlines() if x.strip()]
    approved = {x.strip() for x in approved_path.read_text(encoding='utf-8').splitlines() if x.strip()}
    manifest_sha = sha256(args.input_manifest)
    accepted_sha = sha256(args.accepted_audit)
    accepted_audit = json.loads(args.accepted_audit.read_text(encoding='utf-8'))
    expected_manifest_sha = 'c4f5d8c7c9a1622c4cad2ef943e3c03db0ee592aa9389d43bf28b206ff745a62'
    if manifest_sha != expected_manifest_sha:
        errors.append(f'accepted marker manifest SHA mismatch: {manifest_sha}')
    with args.input_manifest.open('r', encoding='utf-8', newline='') as stream:
        manifest_rows = list(csv.DictReader(stream, delimiter='\t'))
    manifest_by_marker = {row['marker']: row['sha256'].lower() for row in manifest_rows}
    audit_sources = accepted_audit.get('identity_sources', {})
    if audit_sources.get('primary_marker_order_sha256') != sha256(order_path):
        errors.append('primary marker order hash differs from accepted input audit')
    if audit_sources.get('approved_accessions_sha256') != sha256(approved_path):
        errors.append('approved accession hash differs from accepted input audit')
    if accepted_audit.get('source_fastas', {}).get('per_marker_manifest_sha256') != manifest_sha:
        errors.append('marker manifest hash differs from accepted input audit')
    input_paths = {p.name[:-6]: p for p in inputs.glob('*.fasta') if p.is_file()}
    alignment_paths = {p.name[:-14]: p for p in alignments.glob('*_aligned.fasta') if p.is_file()}
    if len(order) != 100 or len(set(order)) != 100:
        errors.append(f'primary marker order must contain exactly 100 unique markers; observed {len(order)} rows/{len(set(order))} unique')
    if len(approved) != 196:
        errors.append(f'approved accession list must contain 196 unique IDs; observed {len(approved)}')
    if set(input_paths) != set(order):
        errors.append(f'input marker set mismatch: missing={sorted(set(order)-set(input_paths))}; extra={sorted(set(input_paths)-set(order))}')
    if set(alignment_paths) != set(order):
        errors.append(f'alignment marker set mismatch: missing={sorted(set(order)-set(alignment_paths))}; extra={sorted(set(alignment_paths)-set(order))}')
    rows = []
    total_records = 0
    total_columns = 0
    union_ids = set()
    before_hashes = {}
    for marker in order:
        if marker not in input_paths or marker not in alignment_paths:
            continue
        ip = input_paths[marker]
        apath = alignment_paths[marker]
        ih0, ah0 = sha256(ip), sha256(apath)
        before_hashes[marker] = (ih0, ah0)
        if ih0 != manifest_by_marker.get(marker):
            errors.append(f'{marker}: input SHA-256 differs from accepted marker_sources.tsv')
        original, input_errors = parse_fasta(ip)
        aligned, alignment_errors = parse_fasta(apath)
        errors.extend(input_errors)
        errors.extend(alignment_errors)
        input_ids, aligned_ids = set(original), set(aligned)
        if input_ids != aligned_ids:
            errors.append(f'{marker}: ID set mismatch; missing_from_alignment={sorted(input_ids-aligned_ids)[:10]}; extra_in_alignment={sorted(aligned_ids-input_ids)[:10]}')
        lengths = {len(seq) for seq in aligned.values()}
        if len(lengths) != 1:
            errors.append(f'{marker}: aligned sequences have unequal lengths {sorted(lengths)}')
        columns = next(iter(lengths)) if len(lengths) == 1 else 0
        for seq_id in sorted(input_ids & aligned_ids):
            if aligned[seq_id].replace('-', '') != original[seq_id]:
                errors.append(f'{marker}/{seq_id}: ungapped aligned sequence differs from input')
        union_ids.update(input_ids)
        total_records += len(original)
        total_columns += columns
        rows.append({'marker': marker, 'records': len(original), 'columns': columns,
                     'input_sha256_before': ih0, 'alignment_sha256_before': ah0})
    if total_records != 19359:
        errors.append(f'record count mismatch: expected 19359, observed {total_records}')
    if union_ids != approved:
        errors.append(f'approved accession union mismatch: missing={sorted(approved-union_ids)[:20]}; unapproved={sorted(union_ids-approved)[:20]}; observed_union={len(union_ids)}')
    for row in rows:
        marker = row['marker']
        ih1, ah1 = sha256(input_paths[marker]), sha256(alignment_paths[marker])
        row['input_sha256_after'] = ih1
        row['alignment_sha256_after'] = ah1
        row['input_stable'] = ih1 == row['input_sha256_before']
        row['alignment_stable'] = ah1 == row['alignment_sha256_before']
        if not row['input_stable']:
            errors.append(f'{marker}: input changed during audit')
        if not row['alignment_stable']:
            errors.append(f'{marker}: alignment changed during audit')
    result = {
        'audit': 'full100_mafft_alignment_integrity',
        'started_utc': started,
        'state': 'PASS' if not errors else 'FAIL',
        'expected_markers': 100, 'observed_input_markers': len(input_paths),
        'input_manifest_sha256': manifest_sha,
        'accepted_input_audit_sha256': accepted_sha,
        'sequence_normalization': 'FASTA sequence lines concatenated after whitespace removal and uppercased; aligned gaps removed with replace("-", "") before exact comparison',
        'observed_alignment_markers': len(alignment_paths),
        'expected_records': 19359, 'observed_records': total_records,
        'approved_accessions_expected': 196, 'observed_accession_union': len(union_ids),
        'union_exactly_approved': union_ids == approved,
        'alignment_columns_sum_across_markers': total_columns,
        'alignment_column_min': min((r['columns'] for r in rows), default=0),
        'alignment_column_max': max((r['columns'] for r in rows), default=0),
        'per_marker_file_hashes_stable_during_audit': all(r['input_stable'] and r['alignment_stable'] for r in rows),
        'errors': errors,
    }
    (out / 'per_marker.tsv').write_text(
        'marker\trecords\tcolumns\tinput_sha256_before\tinput_sha256_after\talignment_sha256_before\talignment_sha256_after\tinput_stable\talignment_stable\n' +
        ''.join(f"{r['marker']}\t{r['records']}\t{r['columns']}\t{r['input_sha256_before']}\t{r['input_sha256_after']}\t{r['alignment_sha256_before']}\t{r['alignment_sha256_after']}\t{str(r['input_stable']).lower()}\t{str(r['alignment_stable']).lower()}\n" for r in rows),
        encoding='utf-8')
    result['finished_utc'] = datetime.now(timezone.utc).isoformat()
    (out / 'audit.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1

if __name__ == '__main__':
    sys.exit(main())

