#!/usr/bin/env python3
"""Producer exports tested by a separate parser on synthetic fixture data only."""
from collections import defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import stage04_phylogeny as producer
import stage04_validate as reviewer


results = []
def rejects(name, operation):
    try:
        operation()
    except (ValueError, KeyError):
        results.append(name)
        return
    raise AssertionError('Malformed fixture accepted: ' + name)


with tempfile.TemporaryDirectory(prefix='stage04-synthetic-', dir=Path(__file__).parent) as temp:
    root = Path(temp)
    ids = ['SYNTHETIC_1.1', 'SYNTHETIC_2.1', 'SYNTHETIC_3.1', 'SYNTHETIC_4.1']
    alignments = {'M1': {key: 'MKR' for key in ids[:3]}, 'M2': {key: 'GHT' for key in ids}}
    accepted = {(key, marker): {'locus_key': key + '|SYNREP|SYN_' + marker,
                'source_sequence_sha256': hashlib.sha256(sequence.encode()).hexdigest()}
                for marker, alignment in alignments.items() for key, sequence in alignment.items()}
    for marker, alignment in alignments.items():
        producer.export_formats(root / 'markers' / marker, 'trimmed', alignment, list(alignment))
    analysis = {'name': 'SYNTHETIC_ONLY', 'accessions': ids, 'markers': ['M1', 'M2']}
    args = SimpleNamespace(output=root)
    producer.concatenate(args, analysis, alignments, accepted)
    directory = root / 'analyses' / analysis['name']
    check = lambda: reviewer.partition_audit(directory, analysis, alignments, accepted)
    report = check()
    assert report['columns'] == 6 and report['blocks_reconstructed'] == 8
    results.append('producer_exports_independent_full_block_reconstruction')
    source = reviewer.records(directory / 'concatenated.faa', aligned=True)
    assert source[ids[3]] == '---GHT'
    results.append('only_missing_marker_creates_explicit_gap_block')
    original_parts = reviewer.tsv_read(directory / 'partitions.tsv')
    def parts_export(parts):
        producer.table(directory / 'partitions.tsv', parts, list(parts[0]))
        (directory / 'partitions.nex').write_text('#NEXUS\nBEGIN SETS;\n' + ''.join(' CHARSET ' + p['partition'] + ' = ' + str(p['start_one_based']) + '-' + str(p['end_one_based']) + ';\n' for p in parts) + 'END;\n')
        (directory / 'partitions.raxml.txt').write_text(''.join('AA, ' + p['partition'] + ' = ' + str(p['start_one_based']) + '-' + str(p['end_one_based']) + '\n' for p in parts))
    gap = [dict(p) for p in original_parts]
    gap[0].update(end_one_based='2', length='2')
    parts_export(gap)
    rejects('partition_coverage_gap', check)
    overlap = [dict(p) for p in original_parts]
    overlap[1].update(start_one_based='3', length='4')
    parts_export(overlap)
    rejects('partition_coordinate_overlap', check)
    parts_export(original_parts)
    changed = dict(source); changed[ids[3]] = 'QQQGHT'
    producer.export_formats(directory, 'concatenated', changed, ids)
    rejects('invented_missing_marker_residues', check)
    spacer = {key: seq[:3] + 'XXXXX' + seq[3:] for key, seq in source.items()}
    producer.export_formats(directory, 'concatenated', spacer, ids)
    rejects('synthetic_concatenation_spacer', check)
    producer.export_formats(directory, 'concatenated', source, ids)
    original_blocks = reviewer.tsv_read(directory / 'source_block_mapping.tsv')
    corrupt = [dict(row) for row in original_blocks]
    corrupt[0]['locus_key'] = 'SYNTHETIC_WRONG_SOURCE'
    producer.table(directory / 'source_block_mapping.tsv', corrupt, list(corrupt[0]))
    rejects('incorrect_source_locus_join', check)
    producer.table(directory / 'source_block_mapping.tsv', original_blocks, list(original_blocks[0]))
    assert check() == report
    results.append('original_fixture_restored_and_reverified')
    raw = {ids[0]: 'M-KR', ids[1]: 'MAKR'}
    trimmed = {ids[0]: 'MKR', ids[1]: 'MKR'}
    assert producer.column_map('#ColumnsMap\t0, 2, 3\n', raw, trimmed, ids[:2]) == [0, 2, 3]
    results.append('producer_native_column_reconstruction')
    rejects('wrong_trimmed_source_column', lambda: producer.column_map('#ColumnsMap\t0, 1, 3\n', raw, trimmed, ids[:2]))
    native = root / 'native'
    native.mkdir()
    (native / 'raw.faa').write_text('>' + ids[0] + '\nM-\nKR\n>' + ids[1] + '\nMA\nKR\n')
    native_hash = producer.sha(native / 'raw.faa')
    producer.export_formats(native, 'raw', raw, ids[:2], preserve_native_fasta=True)
    assert producer.sha(native / 'raw.faa') == native_hash
    reviewer.compare_formats(native, 'raw', ids[:2])
    results.append('native_fasta_bytes_preserved_during_format_exports')

print(json.dumps({'status': 'PASS_SYNTHETIC_STAGE04_PRODUCER_AND_INDEPENDENT_PARTITION_CHECKS',
                  'biological_execution': 'NOT_RUN', 'fixtures': results}, indent=2))
