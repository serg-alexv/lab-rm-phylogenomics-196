#!/usr/bin/env python3
"""Resumable full196 marker alignment, fixed concatenation and IQ-TREE3 inference.

Run phases align -> independent alignment validator -> trees -> independent
final validator -> publication. The caller owns the single workflow lock.
No root/outgroup is imposed. Sensitivities reuse primary marker alignments.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


def require(ok, detail):
    if not ok:
        raise ValueError(detail)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda: stream.read(1048576), b''):
            digest.update(data)
    return digest.hexdigest()


def write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.partial')
    temporary.write_bytes(text if isinstance(text, bytes) else text.encode('utf-8'))
    temporary.replace(path)


def save(path, data):
    write(path, json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def rows(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def table(path, values, columns):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, columns, delimiter='\t', lineterminator='\n', extrasaction='ignore')
    writer.writeheader()
    for value in values:
        writer.writerow({k: json.dumps(v, separators=(',', ':')) if isinstance(v, (list, dict)) else v for k, v in value.items()})
    write(path, stream.getvalue())


def proteins(path, aligned=False):
    entries, key, fragments = {}, None, []
    def append():
        require(key not in entries and fragments, 'Repeated/empty FASTA entry')
        sequence = ''.join(fragments)
        require(set(sequence) <= set('ACDEFGHIKLMNPQRSTVWYBXZUOJ*' + ('-' if aligned else '')), 'Changed/invalid protein alphabet')
        entries[key] = sequence
    for line in Path(path).read_text(encoding='ascii').splitlines():
        if not line:
            continue
        if line.startswith('>'):
            if key is not None:
                append()
            key, fragments = line[1:].split()[0], []
        else:
            require(key is not None and not any(c.isspace() for c in line), 'Malformed FASTA sequence')
            fragments.append(line)
    if key is not None:
        append()
    require(entries, 'Empty FASTA')
    if aligned:
        require(len({len(s) for s in entries.values()}) == 1, 'Ragged alignment')
    return entries


def export_formats(directory, stem, alignment, ids, preserve_native_fasta=False):
    require(ids and set(ids) == set(alignment), 'Format export membership differs')
    lengths = {len(alignment[k]) for k in ids}
    require(len(lengths) == 1 and next(iter(lengths)) > 0, 'Format export empty/ragged alignment')
    width = next(iter(lengths))
    fasta = ''.join('>' + key + '\n' + alignment[key] + '\n' for key in ids)
    if preserve_native_fasta:
        native = proteins(directory / (stem + '.faa'), aligned=True)
        require(list(native) == ids and native == alignment, 'Native alignment order/residues differ from portable exports')
    else:
        write(directory / (stem + '.faa'), fasta)
    name_width = max(map(len, ids)) + 2
    clustal = 'CLUSTAL W multiple sequence alignment\n\n'
    for start in range(0, width, 60):
        clustal += ''.join(key.ljust(name_width) + alignment[key][start:start + 60] + '\n' for key in ids) + '\n'
    write(directory / (stem + '.clw'), clustal)
    write(directory / (stem + '.phy'), str(len(ids)) + ' ' + str(width) + '\n' +
          ''.join(key + '  ' + alignment[key] + '\n' for key in ids))
    nexus = '#NEXUS\nBEGIN DATA;\n DIMENSIONS NTAX=' + str(len(ids)) + ' NCHAR=' + str(width) + ';\n'
    nexus += ' FORMAT DATATYPE=PROTEIN GAP=- MISSING=?;\n MATRIX\n'
    nexus += ''.join(" '" + key.replace("'", "''") + "' " + alignment[key] + '\n' for key in ids)
    nexus += ' ;\nEND;\n'
    write(directory / (stem + '.nex'), nexus)
    return width


def column_map(text, raw, trimmed, ids):
    lines = [line for line in text.splitlines() if line.startswith('#ColumnsMap')]
    require(len(lines) == 1, 'Missing/ambiguous actual trimAl column mapping')
    values = lines[0].split('\t', 1)
    require(len(values) == 2 and re.fullmatch(r'\d+(?:,\s*\d+)*', values[1]), 'Malformed native trimAl column map')
    mapping = [int(x.strip()) for x in values[1].split(',')]
    require(len(mapping) == len(next(iter(trimmed.values()))) and mapping == sorted(set(mapping)), 'TrimAl column map length/order differs')
    require(mapping and mapping[-1] < len(next(iter(raw.values()))), 'TrimAl mapped column outside raw alignment')
    for key in ids:
        require(''.join(raw[key][j] for j in mapping) == trimmed[key], 'TrimAl sequence mutation or incorrect column mapping')
    return mapping


def process(args, directory, label, argv, identity, stdout_path=None):
    """Run once with immutable launch identity, actual PID and separate logs."""
    import resource
    directory.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    with (stdout_path or directory / (label + '.stdout.txt')).open('wb') as out, (directory / (label + '.stderr.txt')).open('wb') as error:
        child = subprocess.Popen(argv, cwd=args.root, env=args.environment, stdout=out, stderr=error)
        save(directory / (label + '.launch.json'), {'execution': 'ACTUAL_PROCESS_STARTED', 'utc': datetime.now(timezone.utc).isoformat(),
             'runner_pid': os.getpid(), 'child_pid': child.pid, 'argv': argv, 'identity': identity, 'scientific_validation': 'NOT_RUN'})
        code = child.wait()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'argv': argv, 'runner_pid': os.getpid(), 'child_pid': child.pid,
               'exit_code': code, 'elapsed_seconds': time.monotonic() - started,
               'child_cpu_seconds': after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
               'children_peak_rss_bytes_cumulative': after.ru_maxrss * 1024, 'identity': identity,
               'measurement_limit': 'Child CPU delta and cumulative child peak RSS; outer /usr/bin/time supplies full runner measurement'}
    save(directory / (label + '.command.json'), receipt)
    with (args.output / 'commands.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(receipt) + '\n')
    require(code == 0, label + ' process failed; exact outputs preserved')
    return receipt


def verify_receipt(directory, path, identity):
    data = load(path)
    require(data['identity'] == identity and data['execution'] == 'COMPUTATION_OUTPUTS_CHECKED', 'Different/incomplete cached computation')
    for relative, expected in data['file_sha256'].items():
        location = directory / relative
        require(directory.resolve() in location.resolve().parents and sha(location) == expected, 'Cached computation bytes changed')
    return data


def finished_attempt(attempts, label, identity):
    """Recover an actual exit0 receipt before any post-process checkpoint write."""
    for attempt in reversed(attempts):
        path = attempt / (label + '.command.json')
        if path.is_file():
            record = load(path)
            require(record['identity'] == identity, 'Different prior executed command identity')
            if record['exit_code'] == 0:
                return attempt
    return None


def align_one(args, marker, original):
    directory = args.output / 'markers' / marker
    identity = {'input_sha256': sha(original), 'stage04_identity': args.identity, 'marker': marker}
    complete = directory / 'alignment_complete.json'
    if complete.exists():
        verify_receipt(directory, complete, identity)
        return proteins(directory / 'trimmed.faa', aligned=True)
    directory.mkdir(parents=True, exist_ok=True)
    source = proteins(original)
    ids = [key for key in args.accessions if key in source]
    require(set(ids) == set(source) and len(ids) >= 177, 'Primary marker input has unexpected membership/occupancy')
    write(directory / 'original.faa', original.read_bytes())
    mafft_identity = {'input_sha256': identity['input_sha256'], 'mafft_sha256': args.identity['mafft_sha256'],
                      'argv_options': ['--auto', '--thread', '2'], 'runner_sha256': args.identity['runner_sha256']}
    mafft_done = directory / 'mafft_complete.json'
    if mafft_done.exists():
        verify_receipt(directory, mafft_done, mafft_identity)
    else:
        attempts = sorted(p for p in directory.glob('mafft_attempt_*') if p.is_dir())
        attempt = finished_attempt(attempts, 'mafft', mafft_identity)
        recovered = attempt is not None
        attempt = attempt or directory / ('mafft_attempt_' + str(len(attempts) + 1).zfill(4))
        output = attempt / 'raw.faa'
        if not recovered:
            process(args, attempt, 'mafft', [str(args.host_env / 'bin/mafft'), '--auto', '--thread', '2', str(original)], mafft_identity, output)
        aligned = proteins(output, aligned=True)
        require(set(aligned) == set(source), 'MAFFT removed/renamed source sequences')
        require(all(aligned[key].replace('-', '') == source[key] for key in ids), 'MAFFT changed original sequence bytes')
        write(directory / 'raw.faa', output.read_bytes())
        save(mafft_done, {'execution': 'COMPUTATION_OUTPUTS_CHECKED', 'scientific_validation': 'NOT_RUN',
             'identity': mafft_identity, 'file_sha256': {'raw.faa': sha(directory / 'raw.faa')}, 'attempt': attempt.name})
    raw = proteins(directory / 'raw.faa', aligned=True)
    trim_identity = {'raw_sha256': sha(directory / 'raw.faa'), 'trimal_sha256': args.identity['trimal_sha256'],
                     'argv_options': ['-automated1', '-fasta', '-keepheader', '-keepseqs', '-colnumbering'],
                     'runner_sha256': args.identity['runner_sha256']}
    trim_done = directory / 'trimal_complete.json'
    if trim_done.exists():
        verify_receipt(directory, trim_done, trim_identity)
    else:
        attempts = sorted(p for p in directory.glob('trimal_attempt_*') if p.is_dir())
        attempt = finished_attempt(attempts, 'trimal', trim_identity)
        recovered = attempt is not None
        attempt = attempt or directory / ('trimal_attempt_' + str(len(attempts) + 1).zfill(4))
        output = attempt / 'trimmed.faa'
        argv = [str(args.host_env / 'bin/trimal'), '-in', str(directory / 'raw.faa'), '-out', str(output),
                '-automated1', '-fasta', '-keepheader', '-keepseqs', '-colnumbering']
        if not recovered:
            process(args, attempt, 'trimal', argv, trim_identity)
        trimmed = proteins(output, aligned=True)
        require(set(trimmed) == set(source), 'trimAl removed/renamed source sequences')
        mapping = column_map((attempt / 'trimal.stdout.txt').read_text(), raw, trimmed, ids)
        write(directory / 'trimmed.faa', output.read_bytes())
        write(directory / 'trimal_column_numbering.txt', (attempt / 'trimal.stdout.txt').read_bytes())
        table(directory / 'trimmed_to_raw_columns.tsv', [{'trimmed_column_one_based': i + 1, 'raw_column_one_based': j + 1}
             for i, j in enumerate(mapping)], ['trimmed_column_one_based', 'raw_column_one_based'])
        save(trim_done, {'execution': 'COMPUTATION_OUTPUTS_CHECKED', 'scientific_validation': 'NOT_RUN', 'identity': trim_identity,
             'file_sha256': {name: sha(directory / name) for name in ['trimmed.faa', 'trimal_column_numbering.txt', 'trimmed_to_raw_columns.tsv']},
             'attempt': attempt.name})
    trimmed = proteins(directory / 'trimmed.faa', aligned=True)
    mapping = column_map((directory / 'trimal_column_numbering.txt').read_text(), raw, trimmed, ids)
    export_formats(directory, 'raw', raw, ids, preserve_native_fasta=True)
    export_formats(directory, 'trimmed', trimmed, ids, preserve_native_fasta=True)
    table(directory / 'sequence_alignment_qc.tsv', [{'assembly_accession': key, 'source_aa_length': len(source[key]),
          'raw_alignment_residues': len(raw[key].replace('-', '')), 'trimmed_residues': len(trimmed[key].replace('-', '')),
          'trimmed_gaps': trimmed[key].count('-'), 'trimmed_all_residues': set(trimmed[key]) == {'-'}} for key in ids],
          ['assembly_accession', 'source_aa_length', 'raw_alignment_residues', 'trimmed_residues', 'trimmed_gaps', 'trimmed_all_residues'])
    filenames = ['original.faa', 'raw.faa', 'raw.clw', 'raw.phy', 'raw.nex', 'trimmed.faa', 'trimmed.clw', 'trimmed.phy', 'trimmed.nex',
                 'trimal_column_numbering.txt', 'trimmed_to_raw_columns.tsv', 'sequence_alignment_qc.tsv', 'mafft_complete.json', 'trimal_complete.json']
    save(complete, {'execution': 'COMPUTATION_OUTPUTS_CHECKED', 'scientific_validation': 'NOT_RUN', 'identity': identity,
         'raw_columns': len(next(iter(raw.values()))), 'trimmed_columns': len(mapping), 'taxa': len(ids),
         'file_sha256': {name: sha(directory / name) for name in filenames}})
    return trimmed


def concatenate(args, analysis, alignments, accepted):
    directory = args.output / 'analyses' / analysis['name']
    directory.mkdir(parents=True, exist_ok=True)
    concat = {key: '' for key in analysis['accessions']}
    partitions, mapping, offset = [], [], 0
    for ordinal, marker in enumerate(analysis['markers'], 1):
        alignment = alignments[marker]
        width = len(next(iter(alignment.values())))
        require(width > 0, 'Frozen marker has no retained columns')
        name = 'p' + str(ordinal).zfill(4)
        partitions.append({'partition': name, 'profile': marker, 'start_one_based': offset + 1,
                           'end_one_based': offset + width, 'length': width,
                           'source_trimmed_alignment_sha256': sha(args.output / 'markers' / marker / 'trimmed.faa')})
        for key in analysis['accessions']:
            present = key in alignment
            block = alignment[key] if present else '-' * width
            source = accepted.get((key, marker))
            require(present == (source is not None), 'Missing-marker gap block differs from accepted source manifest')
            concat[key] += block
            mapping.append({'analysis': analysis['name'], 'assembly_accession': key, 'profile': marker, 'partition': name,
                'state': 'PRESENT_TRIMMED_ALL_RESIDUES' if present and set(block) == {'-'} else
                         'PRESENT_ACCEPTED_MARKER' if present else 'MISSING_MARKER_GAP_BLOCK',
                'locus_key': source['locus_key'] if source else None,
                'source_sequence_sha256': source['source_sequence_sha256'] if source else None,
                'start_one_based': offset + 1, 'end_one_based': offset + width,
                'block_sha256': hashlib.sha256(block.encode('ascii')).hexdigest()})
        offset += width
    require(all(sequence.replace('-', '') for sequence in concat.values()), 'All-gap concatenated taxon; approved membership cannot be pruned')
    export_formats(directory, 'concatenated', concat, analysis['accessions'])
    table(directory / 'partitions.tsv', partitions, list(partitions[0]))
    table(directory / 'source_block_mapping.tsv', mapping, list(mapping[0]))
    nexus = '#NEXUS\nBEGIN SETS;\n' + ''.join(' CHARSET ' + p['partition'] + ' = ' + str(p['start_one_based']) + '-' + str(p['end_one_based']) + ';\n' for p in partitions) + 'END;\n'
    write(directory / 'partitions.nex', nexus)
    write(directory / 'partitions.raxml.txt', ''.join('AA, ' + p['partition'] + ' = ' + str(p['start_one_based']) + '-' + str(p['end_one_based']) + '\n' for p in partitions))
    write(directory / 'accessions.txt', '\n'.join(analysis['accessions']) + '\n')
    write(directory / 'marker_order.txt', '\n'.join(analysis['markers']) + '\n')
    if hasattr(args, 'metadata_by_id'):
        labels = []
        for key in analysis['accessions']:
            metadata = args.metadata_by_id[key]
            display = metadata['display_label']
            # Portable display normalization only; exact metadata is retained.
            tree_label = display.replace("'", '\u2019').replace('\r', ' ').replace('\n', ' ') + ' | ' + key
            labels.append({'assembly_accession': key, 'source_display_label': display, 'tree_label': tree_label,
                           'operational_group': metadata['operational_group']})
        table(directory / 'tip_label_map.tsv', labels, list(labels[0]))
    duplicates = defaultdict(list)
    for key, sequence in concat.items():
        duplicates[hashlib.sha256(sequence.encode()).hexdigest()].append(key)
    save(directory / 'identical_alignment_groups.json', {'groups': [ids for ids in duplicates.values() if len(ids) > 1],
         'policy': 'Keep all exact assembly tips with IQ-TREE -keep-ident; identical host data cannot independently resolve their relative strain placements'})
    files = ['concatenated.faa', 'concatenated.clw', 'concatenated.phy', 'concatenated.nex', 'partitions.tsv', 'partitions.nex',
             'partitions.raxml.txt', 'source_block_mapping.tsv', 'accessions.txt', 'marker_order.txt', 'identical_alignment_groups.json']
    if hasattr(args, 'metadata_by_id'):
        files.append('tip_label_map.tsv')
    return {'name': analysis['name'], 'taxa': len(concat), 'markers': len(partitions), 'columns': offset,
            'file_sha256': {name: sha(directory / name) for name in files}}


def orthology_gate(args, validation, inventory, config):
    """Accept a strict projection only with preserved executed original proof."""
    if args.orthology_config is None:
        require(args.original_marker_validation is None and args.original_markers is None
                and 'curation_status' not in validation, 'Curated view requires explicit independent curation paths')
        return {}
    require(args.original_marker_validation and args.original_markers, 'Original full196 marker evidence paths required for curation')
    old = load(args.original_marker_validation)
    policy = load(args.orthology_config)
    receipt = load(args.markers / 'curation_receipt.json')
    require(old['status'] == 'PASS_MARKER_SOURCE_AND_FIXED_FILTERS'
            and old['scientific_stage_status'] == 'HOST_ORTHOLOGY_DUPLICATE_SIGNAL_REVIEW_REQUIRED'
            and old['approved_assemblies'] == old['independently_verified_searches'] == 196
            and old['profiles_searched'] == 119 and old['marker_cells'] == 23324
            and old['primary_markers'] == 101 and old['accepted_marker_sequences'] == 19551
            and old['same_locus_multiple_profile_candidates'] == 192 and old['scientific_blockers'] == []
            and old['producer_identity'] == validation['producer_identity'] == inventory['identity']
            and old['inventory_summary_sha256'] == sha(args.original_markers / 'inventory_summary.json')
            and old['accepted_sequence_manifest_sha256'] == sha(args.original_markers / 'accepted_sequence_manifest.tsv')
            and old['primary_marker_order_sha256'] == sha(args.original_markers / 'primary_marker_order.txt')
            and old['config_sha256'] == sha(args.config) and old['profile_sha256'] == config['profile_sha256'],
            'Original executed full119/full196 integrity and duplicate blockade changed')
    require(policy['revision'] == 'stage03-orthology-v2' and policy['frozen_before_alignment_and_topology'] is True
            and policy['no_biological_search_rerun'] is True and policy['excluded_primary_profiles'] == ['IPT']
            and policy['retained_corresponding_profile'] == 'IPPT' and policy['original_duplicate_loci'] == 192
            and policy['unchanged_thresholds'] == {'candidate_profiles': 119, 'initial_minimum': 96, 'assemblies': 196,
                                                 'occupancy_minimum': 177, 'post_recovery_fraction': 0.8}
            and policy['original_config_sha256'] == sha(args.config)
            and policy['original_validation_summary_sha256'] == sha(args.original_marker_validation)
            and policy['original_inventory_summary_sha256'] == sha(args.original_markers / 'inventory_summary.json')
            and policy['original_accepted_sequence_manifest_sha256'] == sha(args.original_markers / 'accepted_sequence_manifest.tsv'),
            'Topology-blind orthology policy/source/fixed119/196 filters changed')
    require(validation['curation_status'] == 'PASS_TOPOLOGY_BLIND_ORTHOLOGY_DEDUPLICATION'
            and validation['original_validation_summary_sha256'] == sha(args.original_marker_validation)
            and validation['orthology_curation_config_sha256'] == sha(args.orthology_config)
            and validation['orthology_curation_receipt_sha256'] == sha(args.markers / 'curation_receipt.json')
            and validation['primary_markers'] == inventory['primary_markers'] == 100
            and validation['accepted_marker_sequences'] == inventory['accepted_marker_sequences'] == 19359
            and validation['minimum_unique_initial_length_markers'] >= 96
            and validation['biological_search_reexecuted'] is False
            and validation['original_scientific_stage_status_preserved'] == old['scientific_stage_status']
            and receipt['no_hmm_or_alignment_job_run'] is True,
            'Independent strict100-marker projection certificate/source uniqueness gate failed')
    original_order = (args.original_markers / 'primary_marker_order.txt').read_text().splitlines()
    curated_order = (args.markers / 'primary_marker_order.txt').read_text().splitlines()
    require(len(original_order) == 101 and 'IPPT' in original_order and 'IPT' in original_order
            and curated_order == [name for name in original_order if name != 'IPT'], 'Curated family list changes more than redundant IPT')
    old_rows = rows(args.original_markers / 'accepted_sequence_manifest.tsv')
    curated = rows(args.markers / 'accepted_sequence_manifest.tsv')
    require(curated == [row for row in old_rows if row['profile'] != 'IPT'] and len(curated) == 19359
            and len({row['locus_key'] for row in curated}) == len(curated), 'Curated source rows altered or retain repeated biological loci')
    for name, expected in receipt['output_sha256'].items():
        path = args.markers / name
        require(not Path(name).is_absolute() and '..' not in Path(name).parts and '\\' not in name
                and args.markers in path.resolve().parents and sha(path) == expected, 'Current curation payload changed: ' + name)
    return {'orthology_curation_config_sha256': sha(args.orthology_config),
            'orthology_curation_receipt_sha256': sha(args.markers / 'curation_receipt.json'),
            'original_marker_validation_sha256': sha(args.original_marker_validation),
            'original_marker_validation_path': args.original_marker_validation.relative_to(args.root).as_posix(),
            'original_markers_path': args.original_markers.relative_to(args.root).as_posix(),
            'orthology_curation_config_path': args.orthology_config.relative_to(args.root).as_posix(),
            'orthology_policy': 'One whole redundant IPT family removed; original119/196 filters preserved, additionalunique96 gate',
            'primary_marker_count': 100, 'accepted_marker_sequence_count': 19359}


def input_gates(args):
    config = load(args.config)
    args.accessions = (args.root / 'config/approved_accessions.txt').read_text().split()
    require(len(args.accessions) == len(set(args.accessions)) == 196 and
            sha(args.root / 'config/approved_accessions.txt') == config['approved_accessions_sha256'], 'Approved full196 list differs')
    inventory = load(args.markers / 'inventory_summary.json')
    validation = load(args.marker_validation)
    review = validation.get('host_function_review', {})
    require(validation['status'] == 'PASS_MARKER_SOURCE_AND_FIXED_FILTERS'
            and validation['scientific_stage_status'] == 'PASS_HOST_MARKER_INVENTORY'
            and validation['approved_assemblies'] == validation['independently_verified_searches'] == 196
            and validation['profiles_searched'] == 119 and validation['marker_cells'] == 23324
            and validation['producer_identity'] == inventory['identity']
            and validation['inventory_summary_sha256'] == sha(args.markers / 'inventory_summary.json')
            and validation['accepted_sequence_manifest_sha256'] == sha(args.markers / 'accepted_sequence_manifest.tsv')
            and validation['primary_marker_order_sha256'] == sha(args.markers / 'primary_marker_order.txt')
            and validation['scientific_blockers'] == [] and validation['same_locus_multiple_profile_candidates'] == 0
            and validation['config_sha256'] == sha(args.config)
            and validation['profile_sha256'] == config['profile_sha256']
            and review['state'] == 'REVIEWED_CONSERVED_HOST_PROFILE_SCOPE_WITH_DOCUMENTED_LIMITS'
            and review['profiles_accounted'] == 119 and review['unresolved_rm_candidates'] == 0,
            'Independent full196 marker integrity/filter/host-function gate failed')
    require(inventory['execution'] == 'COMPLETED_ALL196_SEARCHES' and inventory['blocker_count'] == 0
            and inventory['inventory'] == 'MARKER_INVENTORY_CONSTRUCTED', 'Marker inventory has a scientific blocker')
    orthology = orthology_gate(args, validation, inventory, config)
    publication = load(args.marker_publication)
    require(publication['status'] == 'UPLOAD_VERIFIED' and publication['remote_tag_commit_verified'] is True
            and publication['approved_assemblies'] == 196 and publication.get('assets')
            and all(a['download_readback_verified'] is True and a['all_zip_member_hashes_verified'] is True
                    and a['bytes'] > 0 and re.fullmatch(r'[a-f0-9]{64}', a['sha256']) for a in publication['assets']),
            'Stage3 remote publication verification gate failed')
    if orthology:
        require(publication['curated_validation_summary_sha256'] == sha(args.marker_validation)
                and publication['original_validation_summary_sha256'] == sha(args.original_marker_validation)
                and publication['orthology_curation_config_sha256'] == sha(args.orthology_config)
                and publication['orthology_curation_receipt_sha256'] == sha(args.markers / 'curation_receipt.json'),
                'Verified Stage3 release does not bind both original and current independently curated payload')
    args.publication_gate_sha256 = sha(args.marker_publication)
    tree = config['iqtree']
    require(tree['ultrafast_bootstrap_replicates'] == tree['sh_alrt_replicates'] == 1000 and tree['seed'] == 1961008
            and tree['threads_maximum'] == 2 and 'MFP' in tree['model_selection'] and 'without partition merging' in tree['model_selection'], 'Frozen IQ-TREE settings differ')
    args.identity = {'runner_sha256': sha(__file__), 'config_sha256': sha(args.config),
        'stage03_runtime_receipt_sha256': sha(args.markers / 'runtime/runtime_receipt.json'),
        'approved_accessions_sha256': sha(args.root / 'config/approved_accessions.txt'),
        'approved_metadata_sha256': sha(args.root / 'config/approved_panel.tsv'),
        'marker_validation_sha256': sha(args.marker_validation),
        'inventory_summary_sha256': sha(args.markers / 'inventory_summary.json'),
        'accepted_manifest_sha256': sha(args.markers / 'accepted_sequence_manifest.tsv'),
        'primary_marker_order_sha256': sha(args.markers / 'primary_marker_order.txt'),
        'marker_qc_sha256': sha(args.markers / 'marker_qc.tsv'),
        'sensitivity162_source_sha256': sha(args.root / 'evidence/g0/reports/sensitivity162_accessions.txt'),
        'mafft_sha256': sha(args.host_env / 'bin/mafft'), 'trimal_sha256': sha(args.host_env / 'bin/trimal'),
        'iqtree3_sha256': sha(args.host_env / 'bin/iqtree3'), 'iqtree_memory_mib': args.iqtree_memory_mib,
        'root_policy': 'UNROOTED_NO_OUTGROUP_REFERENCE_SEQUENCES_RETRIEVED_OR_VALIDATED',
        'resource_receipt_sha256': sha(args.resource_receipt),
        'marker_validation_path': args.marker_validation.relative_to(args.root).as_posix(),
        'host_config_path': args.config.relative_to(args.root).as_posix(), **orthology}
    runtime = load(args.markers / 'runtime/runtime_receipt.json')
    require(runtime['status'] == 'ACTUAL_INSTALLED_RUNTIME_HELP_AND_BYTES_CAPTURED'
            and all(runtime['programs'][name]['sha256'] == sha(args.host_env / 'bin' / name)
                    for name in ['mafft', 'trimal', 'iqtree3']), 'Stage3 actually inspected host tools changed before Stage4')
    resource = load(args.resource_receipt)
    require(resource['maximum_compute_threads'] == 2 and resource['iqtree_memory_mib'] == args.iqtree_memory_mib
            and 256 <= args.iqtree_memory_mib <= 1536 and resource['process_address_space_limit_bytes'] == 2147483648
            and resource['measured_windows_available_bytes'] > 2147483648
            and resource['measured_linux_available_bytes'] > 2147483648,
            'Measured resource/headroom gate failed; root must publish actual measurements')
    names = (args.markers / 'primary_marker_order.txt').read_text().splitlines()
    require(names == sorted(set(names)) and 1 <= len(names) <= 119, 'Frozen primary marker order differs')
    subset162 = (args.root / 'evidence/g0/reports/sensitivity162_accessions.txt').read_text().split()
    require(len(subset162) == len(set(subset162)) == 162 and set(subset162) <= set(args.accessions), 'Exact G0 sensitivity162 differs')
    metadata = rows(args.root / 'config/approved_panel.tsv')
    require(len(metadata) == 196 and {r['assembly_accession'] for r in metadata} == set(args.accessions), 'Frozen metadata membership differs')
    args.metadata_by_id = {row['assembly_accession']: row for row in metadata}
    complete = {r['assembly_accession'] for r in metadata if r['assembly_level'] in ('Complete Genome', 'Chromosome')}
    require(len(complete) == 155, 'Frozen high-contiguity metadata must yield155 assemblies')
    qc = rows(args.markers / 'marker_qc.tsv')
    occupancy = {r['profile']: int(r['accepted_genomes_fixed196']) for r in qc}
    high = [name for name in names if occupancy[name] >= 187]
    require(high, 'No marker satisfies frozen187/196 sensitivity; report scientific blocker')
    analyses = [{'name': 'primary196', 'accessions': args.accessions, 'markers': names, 'scope': 'Approved full196 primary'},
        {'name': 'sensitivity162', 'accessions': [a for a in args.accessions if a in set(subset162)], 'markers': names, 'scope': 'Exact preserved G0 sensitivity162'},
        {'name': 'sensitivity187_markers', 'accessions': args.accessions, 'markers': high, 'scope': 'Marker occupancy at least187/196; fixed196 denominator'},
        {'name': 'sensitivity_complete155', 'accessions': [a for a in args.accessions if a in complete], 'markers': names, 'scope': 'Frozen metadata Complete Genome or Chromosome155'}]
    freeze = {'status': 'FROZEN_BEFORE_STAGE04_ALIGNMENT_AND_TOPOLOGY', 'identity': args.identity, 'analyses': analyses,
              'alignment_protocol': ['MAFFT --auto --thread 2', 'trimAl -automated1 -fasta -keepheader -keepseqs -colnumbering'],
              'iqtree_protocol': ['--seqtype AA', '-p edge-linked proportional partitions', '-m MFP', '-B 1000', '--alrt 1000',
                                  '--seed 1961008', '-T 2', '--mem ' + str(args.iqtree_memory_mib) + 'M', '-keep-ident', '--boot-trees'],
              'root_policy': args.identity['root_policy'], 'optional_concordance': 'NOT_RUN_OPTIONAL_NOT_REQUIRED_FOR_STAGE_COMPLETION'}
    args.output.mkdir(parents=True, exist_ok=True)
    frozen_path = args.output / 'analysis_freeze.json'
    if frozen_path.exists():
        require(load(frozen_path) == freeze, 'Frozen analysis namespace differs; no silent overwrite or redo')
    else:
        require(not list(args.output.iterdir()), 'Unowned Stage4 output namespace')
        save(frozen_path, freeze)
    accepted = {}
    for row in rows(args.markers / 'accepted_sequence_manifest.tsv'):
        key = row['assembly_accession'], row['profile']
        require(key not in accepted and key[0] in args.accessions and key[1] in names, 'Accepted source manifest duplicates/unexpected cell')
        accepted[key] = row
    for marker in names:
        original = proteins(args.markers / 'marker_sequences' / (marker + '.faa'))
        require(set(original) == {a for a, m in accepted if m == marker}, 'Original marker FASTA and source manifest differ')
        for key, sequence in original.items():
            require(hashlib.sha256(sequence.encode('ascii')).hexdigest() == accepted[(key, marker)]['source_sequence_sha256'], 'Source marker sequence hash changed')
    return analyses, accepted


def align_phase(args, analyses, accepted):
    names = analyses[0]['markers']
    alignments = {}
    for index, marker in enumerate(names, 1):
        alignments[marker] = align_one(args, marker, args.markers / 'marker_sequences' / (marker + '.faa'))
        save(args.output / 'execution_progress.json', {'execution': 'RUNNING_ALIGNMENT', 'completed_markers': index,
             'required_markers': len(names), 'runner_pid': os.getpid(), 'last_marker': marker, 'scientific_validation': 'NOT_RUN'})
        print(str(index) + '/' + str(len(names)) + ' ALIGNMENT_OUTPUT_CHECKED ' + marker, flush=True)
    manifest = [concatenate(args, analysis, alignments, accepted) for analysis in analyses]
    save(args.output / 'analysis_alignment_manifest.json', manifest)
    summary = {'execution': 'ALL_PRIMARY_ALIGNMENTS_AND_FOUR_CONCATENATIONS_CONSTRUCTED', 'scientific_validation': 'NOT_RUN',
               'github_publication': 'NOT_RUN', 'identity': args.identity, 'aligned_markers': len(names),
               'analyses': manifest, 'analysis_freeze_sha256': sha(args.output / 'analysis_freeze.json'),
               'analysis_manifest_sha256': sha(args.output / 'analysis_alignment_manifest.json'),
               'tree_execution': 'NOT_RUN_INDEPENDENT_ALIGNMENT_GATE_REQUIRED'}
    save(args.output / 'alignment_summary.json', summary)
    save(args.output / 'execution_progress.json', {'execution': summary['execution'], 'tree_execution': summary['tree_execution'],
         'scientific_validation': 'NOT_RUN', 'runner_pid': os.getpid()})


def tree_tip_checks(directory, expected):
    from Bio import Phylo
    path = directory / 'host.treefile'
    trees = list(Phylo.parse(path, 'newick'))
    require(len(trees) == 1 and trees[0].rooted is False, 'Final tree parse/root state differs')
    labels = [n.name for n in trees[0].get_terminals()]
    require(len(labels) == len(set(labels)) == len(expected) and set(labels) == set(expected), 'Final tree missing/duplicate/unexpected exact tips')
    require(all(n.branch_length is None or n.branch_length >= 0 for n in trees[0].find_clades()), 'Negative tree branch length')
    count = 0
    for tree in Phylo.parse(directory / 'host.ufboot', 'newick'):
        labels = [n.name for n in tree.get_terminals()]
        require(len(labels) == len(set(labels)) == len(expected) and set(labels) == set(expected), 'Bootstrap replicate membership differs')
        count += 1
    require(count == 1000, 'Actual bootstrap tree count differs from1000')
    report = (directory / 'host.iqtree').read_text()
    require('1000' in report and re.search(r'SH-aLRT|SH-like|SH approximate', report, re.I)
            and re.search(r'ultrafast|UFBoot', report, re.I), 'IQ-TREE support methods absent from report')
    return {'tips': len(expected), 'bootstrap_trees_verified': count, 'root_policy': 'EXPLICITLY_UNROOTED',
            'scientific_validation': 'NOT_RUN_INDEPENDENT_TREE_CHECK_REQUIRED'}


def trees_phase(args, analyses):
    gate = load(args.alignment_validation)
    require(gate['status'] == 'PASS_ALIGNMENT_FORMATS_AND_PARTITIONS' and gate['analyses_verified'] == 4
            and gate['primary_tip_ids'] == 196 and gate['alignment_summary_sha256'] == sha(args.output / 'alignment_summary.json')
            and gate['analysis_freeze_sha256'] == sha(args.output / 'analysis_freeze.json')
            and gate['analysis_manifest_sha256'] == sha(args.output / 'analysis_alignment_manifest.json'),
            'Independent alignment/partition gate failed')
    manifest = load(args.output / 'analysis_alignment_manifest.json')
    for analysis in manifest:
        directory = args.output / 'analyses' / analysis['name']
        for name, expected in analysis['file_sha256'].items():
            require(sha(directory / name) == expected, 'Validated concatenation payload changed')
    completed, identical_jobs = [], {}
    for analysis in analyses:
        directory = args.output / 'analyses' / analysis['name']
        output = directory / 'iqtree'; output.mkdir(exist_ok=True)
        identity = {'stage04_identity': args.identity, 'concat_sha256': sha(directory / 'concatenated.faa'),
                    'partitions_sha256': sha(directory / 'partitions.nex'), 'alignment_validation_sha256': sha(args.alignment_validation)}
        completed_path = output / 'tree_complete.json'
        key = identity['concat_sha256'], identity['partitions_sha256']
        if completed_path.exists():
            verify_receipt(output, completed_path, identity)
            result = tree_tip_checks(output, analysis['accessions'])
        elif key in identical_jobs:
            original = identical_jobs[key]
            source_receipt = load(original / 'tree_complete.json')
            for name in source_receipt['file_sha256']:
                if name.startswith('host.') or name.startswith('unrooted'):
                    write(output / name, (original / name).read_bytes())
            result = tree_tip_checks(output, analysis['accessions'])
            save(completed_path, {'execution': 'COMPUTATION_OUTPUTS_CHECKED', 'identity': identity, **result,
                 'execution_source': 'REUSED_EXACT_IDENTICAL_ALIGNMENT_PARTITION_INFERENCE', 'source_analysis': original.parent.name,
                 'file_sha256': {p.name: sha(p) for p in output.iterdir() if p.is_file() and p.name != completed_path.name}})
        else:
            argv = [str(args.host_env / 'bin/iqtree3'), '-s', str(directory / 'concatenated.faa'), '--seqtype', 'AA',
                    '-p', str(directory / 'partitions.nex'), '-m', 'MFP', '-B', '1000', '--alrt', '1000', '--seed', '1961008',
                    '-T', '2', '--mem', str(args.iqtree_memory_mib) + 'M', '-keep-ident', '--boot-trees', '--prefix', str(output / 'host')]
            invocation = output / 'inference_identity.json'
            if invocation.exists():
                require(load(invocation) == {'identity': identity, 'argv': argv}, 'Existing IQ-TREE checkpoint has different code/input/options')
            else:
                require(not list(output.iterdir()), 'Unowned IQ-TREE namespace; preserve before resolving')
                save(invocation, {'identity': identity, 'argv': argv})
            # Native checkpoint restoration uses the same argv/prefix; no --redo or --redo-tree.
            attempts = sorted(p for p in output.glob('attempt_*') if p.is_dir())
            attempt = finished_attempt(attempts, 'iqtree3', identity)
            if attempt is None:
                attempt = output / ('attempt_' + str(len(attempts) + 1).zfill(4))
                process(args, attempt, 'iqtree3', argv, identity)
            required = ['host.treefile', 'host.iqtree', 'host.log', 'host.contree', 'host.ufboot']
            require(all((output / name).is_file() and (output / name).stat().st_size for name in required), 'IQ-TREE required report/tree/support output missing')
            result = tree_tip_checks(output, analysis['accessions'])
            write(output / 'unrooted.nwk', (output / 'host.treefile').read_bytes())
            newick = (output / 'host.treefile').read_text().strip()
            write(output / 'unrooted.nex', '#NEXUS\nBEGIN TREES;\n TREE host = [&U] ' + newick + '\nEND;\n')
            labels = {row['assembly_accession']: row['tree_label'] for row in rows(directory / 'tip_label_map.tsv')}
            seen = []
            def label_tip(match):
                key = match.group()
                require(key in labels, 'Labeled tree encountered unknown assembly')
                seen.append(key)
                return "'" + labels[key] + "'"
            labeled = re.sub(r'(?<![A-Za-z0-9_.])GCF_[0-9]{9}\.[0-9]+(?![A-Za-z0-9_.])', label_tip, newick)
            require(len(seen) == len(set(seen)) == len(analysis['accessions']) and set(seen) == set(analysis['accessions']), 'Labeled tree ID replacement accounting differs')
            write(output / 'unrooted_labeled.nwk', labeled + '\n')
            write(output / 'unrooted_labeled.nex', '#NEXUS\nBEGIN TREES;\n TREE host = [&U] ' + labeled + '\nEND;\n')
            save(completed_path, {'execution': 'COMPUTATION_OUTPUTS_CHECKED', 'identity': identity, **result,
                 'execution_source': 'ACTUAL_IQTREE3_WITH_NATIVE_RESUMABLE_CHECKPOINTS',
                 'file_sha256': {p.name: sha(p) for p in output.iterdir() if p.is_file() and p.name != completed_path.name}})
        identical_jobs[key] = output
        completed.append({'analysis': analysis['name'], **result, 'tree_complete_sha256': sha(completed_path)})
        save(args.output / 'execution_progress.json', {'execution': 'RUNNING_INFERENCE', 'completed_analyses': completed,
             'required_analyses': 4, 'runner_pid': os.getpid(), 'scientific_validation': 'NOT_RUN'})
        print(analysis['name'] + ' ACTUAL_TREE_OUTPUT_CHECKED tips=' + str(result['tips']), flush=True)
    save(args.output / 'phylogeny_summary.json', {'execution': 'ALL_PRIMARY_AND_SENSITIVITY_INFERENCES_COMPLETED',
         'scientific_validation': 'NOT_RUN_INDEPENDENT_FINAL_STAGE04_CHECK_REQUIRED', 'github_publication': 'NOT_RUN',
         'identity': args.identity, 'alignment_validation_sha256': sha(args.alignment_validation), 'analyses': completed,
         'root_policy': 'EXPLICITLY_UNROOTED_NO_VALIDATED_OUTGROUP_REFERENCE',
         'optional_concordance': 'NOT_RUN', 'evidence_limit': 'Host protein phylogenetic estimates and support; no R-M functional evidence or independent ANI certification'})


def main(args):
    require(sys.platform == 'linux', 'Actual production tools run only on WD Linux/WSL')
    for name in ['root', 'markers', 'marker_validation', 'marker_publication', 'config', 'output', 'host_env',
                 'resource_receipt', 'alignment_validation']:
        setattr(args, name, getattr(args, name).resolve())
    for name in ['orthology_config', 'original_markers', 'original_marker_validation']:
        if getattr(args, name) is not None:
            setattr(args, name, getattr(args, name).resolve())
    require(args.root == Path.cwd().resolve() and args.root in args.output.parents, 'Dedicated WD repository required')
    args.environment = dict(os.environ)
    args.environment.update(PATH=str(args.host_env / 'bin') + ':/usr/bin:/bin', LC_ALL='C',
         OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2', TMPDIR=str(args.output / 'temporary'))
    analyses, accepted = input_gates(args)
    (args.output / 'temporary').mkdir(exist_ok=True)
    import resource
    limit = resource.getrlimit(resource.RLIMIT_AS)
    require(limit[0] == 2147483648, 'Caller must apply declared2GiB process address-space limit')
    require(len(os.sched_getaffinity(0)) <= 2, 'Caller must bound CPU affinity to at most2 cores')
    save(args.output / 'runner_launch_receipt.json', {'utc': datetime.now(timezone.utc).isoformat(), 'runner_pid': os.getpid(),
         'parent_pid': os.getppid(), 'argv': sys.argv, 'phase': args.phase, 'identity': args.identity,
         'stage03_publication_gate_receipt_sha256': args.publication_gate_sha256,
         'cpu_affinity': sorted(os.sched_getaffinity(0)), 'rlimit_address_space': list(limit), 'scientific_validation': 'NOT_RUN'})
    try:
        align_phase(args, analyses, accepted) if args.phase == 'align' else trees_phase(args, analyses)
    except Exception as error:
        save(args.output / 'execution_failure.json', {'execution': 'FAILED', 'phase': args.phase, 'error': str(error),
             'runner_pid': os.getpid(), 'outputs_preserved': True, 'scientific_validation': 'NOT_PASS'})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['align', 'trees'], required=True)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--markers', type=Path, default=Path('.work/stage03_markers_v1'))
    parser.add_argument('--marker-validation', type=Path, default=Path('.work/stage03_marker_validation/validation_summary.json'))
    parser.add_argument('--marker-publication', type=Path, default=Path('reports/stage03/publication_receipt.json'))
    parser.add_argument('--config', type=Path, default=Path('config/host_primary_stage03_v1.json'))
    parser.add_argument('--orthology-config', type=Path)
    parser.add_argument('--original-markers', type=Path)
    parser.add_argument('--original-marker-validation', type=Path)
    parser.add_argument('--output', type=Path, default=Path('.work/stage04_phylogeny_v1'))
    parser.add_argument('--host-env', type=Path, default=Path('.tools/linux/host_env'))
    parser.add_argument('--resource-receipt', type=Path, default=Path('reports/stage04/resource_preflight.json'))
    parser.add_argument('--alignment-validation', type=Path, default=Path('.work/stage04_alignment_validation/validation_summary.json'))
    parser.add_argument('--iqtree-memory-mib', type=int, default=1536)
    main(parser.parse_args())
