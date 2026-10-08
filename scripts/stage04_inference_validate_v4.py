#!/usr/bin/env python3
"""Independent resumed Stage04 inference audit; no producer imports or inference.

Reuses the independent format/source-column parser logic while explicitly
binding immutable Stage04a alignments, the failed v3 attempt, and separately
capped native v4 attempts under a newly measured resource budget.
No biological searches, alignments, or tree inference are computed here.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import tempfile
from Bio import AlignIO, Phylo, SeqIO
from Bio.Align import MultipleSeqAlignment
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
import Bio
import math
from types import SimpleNamespace

NAMES = ['primary196', 'sensitivity162', 'sensitivity187_markers', 'sensitivity_complete155']
LIMIT = 3221225472
OUTER = 3758096384
WINDOWS_MIN = 4831838208
LINUX_MIN = 4294967296
FINAL_STATUS = 'PASS_HOST_PHYLOGENY_AND_SENSITIVITY_OUTPUT_INTEGRITY'


def check(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            value.update(block)
    return value.hexdigest()


def json_read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def tsv_read(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def records(path, aligned=False, format='fasta'):
    if aligned:
        alignment = AlignIO.read(path, format)
        result = {row.id: str(row.seq) for row in alignment}
        check(len(result) == len(alignment) and alignment.get_alignment_length() > 0, 'Duplicate/empty format alignment')
    else:
        parsed = list(SeqIO.parse(path, 'fasta'))
        result = {row.id: str(row.seq) for row in parsed}
        check(result and len(result) == len(parsed), 'Duplicate/empty source FASTA')
    return result


def compare_formats(directory, stem, expected_ids):
    expected = records(directory / (stem + '.faa'), aligned=True)
    check(list(expected) == expected_ids, 'FASTA ID membership/order differs')
    for suffix, format in [('clw', 'clustal'), ('phy', 'phylip-relaxed'), ('nex', 'nexus')]:
        parsed = records(directory / (stem + '.' + suffix), aligned=True, format=format)
        check(list(parsed) == expected_ids and parsed == expected, 'Independent ' + format + ' parsing differs from FASTA')
    return expected


def native_columns(path):
    text = path.read_text(encoding='utf-8')
    lines = re.findall(r'^#ColumnsMap\t([0-9, ]+)\s*$', text, re.M)
    check(len(lines) == 1, 'Native trimAl column mapping absent/ambiguous')
    values = [int(value) for value in lines[0].split(',')]
    check(values == sorted(set(values)), 'Native trimAl column mapping is not strictly ascending')
    return values


def marker_audit(directory, source_path, expected):
    source = records(source_path)
    original = records(directory / 'original.faa')
    check(original == source and list(original) == list(source), 'Preserved original marker differs from validated Stage3 source')
    check(set(source) == set(expected), 'Source marker membership differs from accepted source manifest')
    for key, sequence in source.items():
        check(hashlib.sha256(sequence.encode('ascii')).hexdigest() == expected[key]['source_sequence_sha256'], 'Stage3 source sequence hash differs')
    raw = compare_formats(directory, 'raw', list(source))
    trimmed = compare_formats(directory, 'trimmed', list(source))
    check(all(raw[key].replace('-', '') == source[key] for key in source), 'Raw aligned sequence changed untrimmed source bytes')
    mapping = native_columns(directory / 'trimal_column_numbering.txt')
    raw_width, trim_width = len(next(iter(raw.values()))), len(next(iter(trimmed.values())))
    check(len(mapping) == trim_width and mapping and mapping[-1] < raw_width, 'Column map outside raw/trimmed dimensions')
    crosswalk = tsv_read(directory / 'trimmed_to_raw_columns.tsv')
    check([(int(row['trimmed_column_one_based']), int(row['raw_column_one_based'])) for row in crosswalk]
          == list(enumerate([n + 1 for n in mapping], 1)), 'Exported source-column crosswalk differs from native evidence')
    for key in source:
        check(''.join(raw[key][column] for column in mapping) == trimmed[key], 'Trimmed residues/gaps do not reconstruct from native raw columns')
    complete = json_read(directory / 'alignment_complete.json')
    check(complete['execution'] == 'COMPUTATION_OUTPUTS_CHECKED', 'Missing complete actual alignment receipt')
    for name, value in complete['file_sha256'].items():
        check(digest(directory / name) == value, 'Alignment evidence changed: ' + name)
    return trimmed, {'raw_columns': raw_width, 'trimmed_columns': trim_width, 'taxa': len(source),
                      'trimmed_all_residue_sequences': sum(set(seq) == {'-'} for seq in trimmed.values())}


def partition_audit(directory, analysis, marker_alignments, accepted):
    accessions = analysis['accessions']
    concatenated = compare_formats(directory, 'concatenated', accessions)
    width = len(next(iter(concatenated.values())))
    partitions = tsv_read(directory / 'partitions.tsv')
    check([row['profile'] for row in partitions] == analysis['markers'], 'Partition marker order differs from frozen list')
    native = re.findall(r'CHARSET\s+(\S+)\s*=\s*(\d+)-(\d+)\s*;', (directory / 'partitions.nex').read_text(), re.I)
    raxml = re.findall(r'^AA,\s+(\S+)\s*=\s*(\d+)-(\d+)\s*$', (directory / 'partitions.raxml.txt').read_text(), re.M)
    expected = [(row['partition'], row['start_one_based'], row['end_one_based']) for row in partitions]
    check(native == expected == raxml, 'NEXUS/RAxML coordinate partitions differ')
    check((directory / 'accessions.txt').read_text().splitlines() == accessions
          and (directory / 'marker_order.txt').read_text().splitlines() == analysis['markers'], 'Exported exact input lists differ')
    block_rows = tsv_read(directory / 'source_block_mapping.tsv')
    blocks = {(row['assembly_accession'], row['profile']): row for row in block_rows}
    check(len(blocks) == len(block_rows) == len(accessions) * len(partitions), 'Source-block crosswalk duplicates/missing cells')
    last = 0
    for row in partitions:
        first, end, length = int(row['start_one_based']), int(row['end_one_based']), int(row['length'])
        check(first == last + 1 and end >= first and length == end - first + 1, 'Partition overlap/gap/reversed coordinates')
        marker = row['profile']
        check(row['source_trimmed_alignment_sha256'] == digest(directory.parents[1] / 'markers' / marker / 'trimmed.faa'), 'Partition source hash differs')
        source_alignment = marker_alignments[marker]
        check(length == len(next(iter(source_alignment.values()))), 'Partition length differs from actual source alignment')
        for key in accessions:
            source = accepted.get((key, marker))
            block = concatenated[key][first - 1:end]
            expected_block = source_alignment[key] if source is not None else '-' * length
            check(block == expected_block, 'Concatenation block differs from source; spacer/residue/missing gap corruption')
            mapping = blocks[(key, marker)]
            state = 'PRESENT_TRIMMED_ALL_RESIDUES' if source and set(block) == {'-'} else 'PRESENT_ACCEPTED_MARKER' if source else 'MISSING_MARKER_GAP_BLOCK'
            check(mapping['state'] == state and int(mapping['start_one_based']) == first and int(mapping['end_one_based']) == end,
                  'Source-block state/coordinates differ')
            check(mapping['locus_key'] == (source['locus_key'] if source else '')
                  and mapping['source_sequence_sha256'] == (source['source_sequence_sha256'] if source else '')
                  and mapping['block_sha256'] == hashlib.sha256(block.encode('ascii')).hexdigest(), 'Source-locus/block hash joins differ')
        last = end
    check(last == width and all(sequence.replace('-', '') for sequence in concatenated.values()), 'Partitions not exhaustive or all-gap taxon')
    return {'analysis': analysis['name'], 'tips': len(accessions), 'partitions': len(partitions), 'columns': width,
            'blocks_reconstructed': len(blocks)}


def split_sets(tree, selected):
    result, selected = set(), frozenset(selected)
    for clade in tree.find_clades():
        left = frozenset(n.name for n in clade.get_terminals()) & selected
        right = selected - left
        if len(left) >= 2 and len(right) >= 2:
            result.add(min(tuple(sorted(left)), tuple(sorted(right))))
    return result


def branch_support_states(tree, alignment):
    support_nodes, omitted_identical_nodes = 0, []
    for node in tree.get_nonterminals():
        if node is tree.root:
            continue
        label = node.name or (str(node.confidence) if node.confidence is not None else '')
        fields = label.split('/')
        if not label:
            descendants = [tip.name for tip in node.get_terminals()]
            check(node.branch_length == 0 and len({alignment[key] for key in descendants}) == 1,
                  'Native branch support omitted outside zero-length identical-alignment group')
            omitted_identical_nodes.append({'tips': descendants, 'branch_length': 0,
                                           'support_state': 'NOT_REPORTED_BY_NATIVE_TOOL_IDENTICAL_ALIGNMENT_GROUP'})
            continue
        check(len(fields) == 2, 'Combined SH-aLRT/UFBoot support missing from internal branch')
        check(all(0 <= float(value) <= 100 for value in fields), 'Branch support outside0..100')
        support_nodes += 1
    check(support_nodes > 0, 'No combined internal branch supports reported')
    return support_nodes, omitted_identical_nodes


def upstream_marker_gate(args, identity, stage03):
    """Independent cross-stage certificate reader; producer code is not imported."""
    validation = json_read(args.marker_validation)
    config = json_read(args.config)
    check(identity['runner_sha256'] == digest(args.producer_source)
          and identity['marker_validation_sha256'] == digest(args.marker_validation)
          and identity['config_sha256'] == digest(args.config)
          and identity['inventory_summary_sha256'] == digest(stage03 / 'inventory_summary.json')
          and validation['status'] == 'PASS_MARKER_SOURCE_AND_FIXED_FILTERS'
          and validation['scientific_stage_status'] == 'PASS_HOST_MARKER_INVENTORY'
          and validation['approved_assemblies'] == validation['independently_verified_searches'] == 196
          and validation['profiles_searched'] == 119 and validation['marker_cells'] == 23324
          and validation['scientific_blockers'] == [] and validation['same_locus_multiple_profile_candidates'] == 0
          and validation['config_sha256'] == digest(args.config)
          and validation['inventory_summary_sha256'] == digest(stage03 / 'inventory_summary.json')
          and validation['accepted_sequence_manifest_sha256'] == digest(stage03 / 'accepted_sequence_manifest.tsv')
          and validation['primary_marker_order_sha256'] == digest(stage03 / 'primary_marker_order.txt'),
          'Current executed scientific Stage3 certificate/source bytes differ')
    review = validation['host_function_review']
    check(review['state'] == 'REVIEWED_CONSERVED_HOST_PROFILE_SCOPE_WITH_DOCUMENTED_LIMITS'
          and review['profiles_accounted'] == 119 and review['unresolved_rm_candidates'] == 0,
          'Executed source host-function review is incomplete')
    check(config['genome_recovery_fixed_denominator'] == 119 and config['genome_minimum_accepted_markers'] == 96
          and config['marker_occupancy_fixed_denominator'] == 196 and config['marker_minimum_accepted_genomes'] == 177
          and config['post_occupancy_genome_recovery_minimum'] == .8, 'Frozen initial119/196 numeric filters changed')
    if args.orthology_config is None:
        check('orthology_curation_config_sha256' not in identity and 'curation_status' not in validation,
              'Curated source cannot use the uncurated certificate route')
        return {'view': 'ORIGINAL_INDEPENDENTLY_VALIDATED', 'marker_validation_sha256': digest(args.marker_validation)}
    check(args.original_markers and args.original_marker_validation, 'Explicit original evidence paths required for curated view')
    old = json_read(args.original_marker_validation)
    policy = json_read(args.orthology_config)
    check(identity['orthology_curation_config_sha256'] == digest(args.orthology_config)
          and identity['original_marker_validation_sha256'] == digest(args.original_marker_validation)
          and identity['orthology_curation_receipt_sha256'] == digest(stage03 / 'curation_receipt.json')
          and validation['original_validation_summary_sha256'] == digest(args.original_marker_validation)
          and validation['orthology_curation_config_sha256'] == digest(args.orthology_config)
          and validation['orthology_curation_receipt_sha256'] == digest(stage03 / 'curation_receipt.json')
          and validation['curation_status'] == 'PASS_TOPOLOGY_BLIND_ORTHOLOGY_DEDUPLICATION'
          and validation['primary_markers'] == identity['primary_marker_count'] == 100
          and validation['accepted_marker_sequences'] == identity['accepted_marker_sequence_count'] == 19359
          and validation['minimum_unique_initial_length_markers'] >= 96 and validation['biological_search_reexecuted'] is False,
          'Current orthology policy/independent projection/source uniqueness certificate changed')
    check(old['status'] == 'PASS_MARKER_SOURCE_AND_FIXED_FILTERS'
          and old['scientific_stage_status'] == 'HOST_ORTHOLOGY_DUPLICATE_SIGNAL_REVIEW_REQUIRED'
          and old['approved_assemblies'] == old['independently_verified_searches'] == 196
          and old['profiles_searched'] == 119 and old['marker_cells'] == 23324
          and old['primary_markers'] == 101 and old['accepted_marker_sequences'] == 19551
          and old['same_locus_multiple_profile_candidates'] == 192 and old['scientific_blockers'] == []
          and old['producer_identity'] == validation['producer_identity']
          and old['inventory_summary_sha256'] == digest(args.original_markers / 'inventory_summary.json')
          and old['accepted_sequence_manifest_sha256'] == digest(args.original_markers / 'accepted_sequence_manifest.tsv')
          and old['primary_marker_order_sha256'] == digest(args.original_markers / 'primary_marker_order.txt')
          and old['config_sha256'] == digest(args.config), 'Original executed integrity proof/orthology blockage changed')
    check(policy['revision'] == 'stage03-orthology-v2' and policy['frozen_before_alignment_and_topology'] is True
          and policy['no_biological_search_rerun'] is True and policy['excluded_primary_profiles'] == ['IPT']
          and policy['retained_corresponding_profile'] == 'IPPT'
          and policy['unchanged_thresholds'] == {'candidate_profiles':119, 'initial_minimum':96, 'assemblies':196,
                                               'occupancy_minimum':177, 'post_recovery_fraction':.8},
          'Curation no longer preserves fixed gates/exact excluded family')
    original = tsv_read(args.original_markers / 'accepted_sequence_manifest.tsv')
    retained = tsv_read(stage03 / 'accepted_sequence_manifest.tsv')
    old_order = (args.original_markers / 'primary_marker_order.txt').read_text().splitlines()
    order = (stage03 / 'primary_marker_order.txt').read_text().splitlines()
    check(len(original) == 19551 and len(retained) == 19359 and retained == [r for r in original if r['profile'] != 'IPT']
          and len(old_order) == 101 and len(order) == 100 and 'IPPT' in order
          and order == [name for name in old_order if name != 'IPT']
          and len({r['locus_key'] for r in retained}) == len(retained), 'Curation source exact subtraction/locus uniqueness changed')
    return {'view': 'INDEPENDENTLY_CURATED_TOPOLOGY_BLIND_ORTHOLOGY', 'original_scientific_status': old['scientific_stage_status'],
            'original_marker_validation_sha256': digest(args.original_marker_validation),
            'marker_validation_sha256': digest(args.marker_validation), 'orthology_curation_config_sha256': digest(args.orthology_config),
            'retained_profiles': 100, 'retained_source_sequences': 19359, 'biological_search_reexecuted': False}


def safe_member(root, name):
    check(isinstance(name, str) and name and '\\' not in name, 'Unsafe receipt member')
    relative = Path(name)
    check(not relative.is_absolute() and '..' not in relative.parts, 'Receipt member escapes namespace')
    path = root / relative
    check(not path.is_symlink() and root.resolve() in path.resolve().parents, 'Receipt member symlink/escape')
    return path


def verify_files(root, mapping):
    check(isinstance(mapping, dict) and mapping, 'Empty payload hash map')
    for name, value in mapping.items():
        check(re.fullmatch('[0-9a-f]{64}', value or '') and digest(safe_member(root, name)) == value,
              'Immutable payload/source bytes changed: ' + name)


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def policy_gate(policy):
    expected = {'status': 'FROZEN_RESUMED_INFERENCE_PROTOCOL_BEFORE_TOPOLOGY', 'approved_assemblies': 196,
        'iqtree_address_space_limit_bytes': LIMIT, 'outer_address_space_limit_bytes': OUTER,
        'maximum_compute_threads': 2, 'native_memory_option': 'OMITTED_UNSUPPORTED_WITH_PARTITION_MODELS',
        'windows_minimum_available_bytes': WINDOWS_MIN, 'linux_minimum_available_bytes': LINUX_MIN,
        'windows_reserve_bytes': 1073741824,
        'alignment_reexecution': False, 'partition_option': '-p', 'model_selection': 'MFP_WITHOUT_MERGING',
        'ultrafast_bootstrap_replicates': 1000, 'sh_alrt_replicates': 1000, 'seed': 1961008,
        'root_policy': 'EXPLICITLY_UNROOTED_NO_VALIDATED_OUTGROUP'}
    check(all(type(policy.get(k)) is type(v) and policy.get(k) == v for k, v in expected.items()),
          'Resumed policy relaxes scope/models/support/resource bounds')


def publication_gate(publication, gate_sha):
    check(publication['status'] == 'UPLOAD_VERIFIED' and publication['remote_tag_commit_verified'] is True
          and publication['scientific_validation'] == 'PASS_ALIGNMENT_FORMATS_AND_PARTITIONS'
          and publication['whole_stage04_phylogeny'] == 'NOT_COMPLETED'
          and publication['approved_assemblies'] == 196 and publication['alignment_validation_sha256'] == gate_sha
          and re.fullmatch('[0-9a-f]{40}', publication['payload_commit']), 'Stage04a current science/publication binding differs')
    assets = publication['assets']
    check(len(assets) == 2 and len({a['asset_name'] for a in assets}) == 2
          and {a['asset_name'] for a in assets} == {'stage04a-full196-validated-alignments.zip', 'stage04a-methods-and-independent-evidence.zip'},
          'Stage04a verified standalone asset coverage differs')
    for asset in assets:
        check(asset['bytes'] > 0 and asset['payload_members'] > 0 and re.fullmatch('[0-9a-f]{64}', asset['sha256'])
              and all(asset[k] is True for k in ('download_readback_verified', 'all_zip_member_hashes_verified', 'sidecar_readback_verified')),
              'Stage04a asset bytes were not completely verified')


def original_phase_gate(args, original_identity):
    state = json_read(args.source_control / 'state.json')
    check(set(state['completed']) == {'align', 'validate_alignment'}, 'Original controller falsely claims completed trees/final validation')
    current_sources = {'scripts/stage04_controller.py': args.source_controller,
                      'scripts/stage04_phylogeny.py': args.source_producer,
                      'scripts/stage04_validate.py': args.source_validator,
                      'scripts/stage04_linux_launcher.py': args.original_observer_source,
                      'scripts/wsl_project.sh': args.wsl_wrapper}
    for name, path in current_sources.items():
        check(state['identity']['file_sha256'].get(name) == digest(path), 'Actually executed original source hash missing/different: ' + name)
    verify_files(args.root, state['identity']['file_sha256'])
    phase_sha = {}
    for phase in ('align', 'validate_alignment'):
        item = state['completed'][phase]
        path = safe_member(args.root, item['actual_exit_receipt'])
        exited = json_read(path)
        check(digest(path) == item['actual_exit_receipt_sha256'] and item['actual_exit_code'] == exited['exit_code'] == 0
              and exited['execution'] == 'ACTUAL_LINUX_PHASE_CHILD_EXITED' and exited['phase'] == phase
              and exited['identity'] == state['identity'] and exited['invocation_id'] == item['invocation_id']
              and exited['job_pid'] == item['linux_job_pid'] and exited['launcher_pid'] == item['linux_launcher_pid'],
              'Original actual successful phase receipt differs')
        check(digest(safe_member(args.root, item['gate']['path'])) == item['gate']['sha256'], 'Original phase gate bytes changed')
        for field in ('elapsed_seconds', 'child_cpu_seconds', 'children_max_rss_bytes'):
            check(math.isfinite(float(exited[field])) and exited[field] >= 0, 'Original execution resource measurement invalid')
        phase_sha[phase] = digest(path)
    native = json_read(args.failed_attempt)
    stderr = args.failed_attempt.parent / 'iqtree3.stderr.txt'
    check(native['exit_code'] == 2 and native['child_pid'] > 0 and '--mem' in native['argv'] and '-p' in native['argv']
          and native['identity']['stage04_identity'] == original_identity
          and stderr.read_text().strip() == '-mem option does not work with partition models yet'
          and not (args.failed_attempt.parent.parent / 'tree_complete.json').exists(), 'Preserved failed native evidence changed')
    current = state['current']
    check(current['phase'] == 'trees' and current['identity'] == state['identity'], 'Original failed tree phase missing')
    failure_path = safe_member(args.root, current['receipt_directory']) / 'linux_exit_receipt.json'
    failed = json_read(failure_path)
    check(failed['execution'] == 'ACTUAL_LINUX_PHASE_CHILD_EXITED' and failed['exit_code'] != 0
          and failed['identity'] == state['identity'] and failed['invocation_id'] == current['invocation_id'],
          'Original failure lacks actual exit; original runner may remain active')
    return phase_sha, digest(failure_path), digest(stderr)


def alignment_gate(args):
    source = args.alignment_input
    frozen = json_read(source / 'analysis_freeze.json')
    summary = json_read(source / 'alignment_summary.json')
    manifest = json_read(source / 'analysis_alignment_manifest.json')
    gate = json_read(args.alignment_validation)
    old = frozen['identity']
    check(frozen['status'] == 'FROZEN_BEFORE_STAGE04_ALIGNMENT_AND_TOPOLOGY'
          and summary['execution'] == 'ALL_PRIMARY_ALIGNMENTS_AND_FOUR_CONCATENATIONS_CONSTRUCTED'
          and gate['status'] == 'PASS_ALIGNMENT_FORMATS_AND_PARTITIONS' and gate['analyses_verified'] == 4
          and gate['primary_tip_ids'] == 196 and gate['profiles_aligned'] == 100
          and old == summary['identity'] == gate['producer_identity'], 'Original executed alignment certificate differs')
    for key, name in [('analysis_freeze_sha256', 'analysis_freeze.json'), ('alignment_summary_sha256', 'alignment_summary.json'),
                      ('analysis_manifest_sha256', 'analysis_alignment_manifest.json')]:
        check(gate[key] == digest(source / name), 'Original alignment certificate hash changed: ' + key)
    check(gate['validator_source_sha256'] == digest(args.source_validator) and old['runner_sha256'] == digest(args.source_producer),
          'Original executed producer/independent checker changed')
    approval = json_read(args.root / 'config/approval.json')
    check(approval['human_approval'] == 'APPROVED_FOR_SEQUENCE_ANALYSIS' and approval['approved_assembly_count'] == 196
          and approval['pilot'] is False and approval['panel_accessions_sha256'] == digest(args.root / 'config/approved_accessions.txt'),
          'Approved full196 contract changed')
    paths = {'approved_accessions_sha256': args.root / 'config/approved_accessions.txt',
        'approved_metadata_sha256': args.root / 'config/approved_panel.tsv', 'config_sha256': args.host_config,
        'sensitivity162_source_sha256': args.root / 'evidence/g0/reports/sensitivity162_accessions.txt',
        'marker_qc_sha256': args.markers / 'marker_qc.tsv', 'stage03_runtime_receipt_sha256': args.markers / 'runtime/runtime_receipt.json',
        'resource_receipt_sha256': args.original_resource_receipt, 'mafft_sha256': args.host_env / 'bin/mafft',
        'trimal_sha256': args.host_env / 'bin/trimal', 'iqtree3_sha256': args.host_env / 'bin/iqtree3'}
    check(all(old[k] == digest(p) for k, p in paths.items()), 'Frozen upstream panel/source/tool/resource bytes changed')
    upstream_args = SimpleNamespace(root=args.root, marker_validation=args.marker_validation, config=args.host_config,
        producer_source=args.source_producer, orthology_config=args.orthology_config,
        original_markers=args.original_markers, original_marker_validation=args.original_marker_validation)
    upstream = upstream_marker_gate(upstream_args, old, args.markers)
    analyses = frozen['analyses']
    panel = (args.root / 'config/approved_accessions.txt').read_text().split()
    check(len(panel) == len(set(panel)) == 196 and [a['name'] for a in analyses] == NAMES
          and [len(a['accessions']) for a in analyses] == [196, 162, 196, 155]
          and analyses[0]['accessions'] == analyses[2]['accessions'] == panel, 'Approved primary/sensitivity scopes changed')
    check(all(len(a['accessions']) == len(set(a['accessions'])) and set(a['accessions']) <= set(panel) for a in analyses),
          'Duplicate/foreign sensitivity accession')
    sensitivity = (args.root / 'evidence/g0/reports/sensitivity162_accessions.txt').read_text().split()
    metadata = tsv_read(args.root / 'config/approved_panel.tsv')
    complete = {r['assembly_accession'] for r in metadata if r['assembly_level'] in ('Complete Genome', 'Chromosome')}
    check(set(analyses[1]['accessions']) == set(sensitivity) and len(set(sensitivity)) == 162
          and set(analyses[3]['accessions']) == complete and len(complete) == 155, 'Sensitivity source membership changed')
    names = (args.markers / 'primary_marker_order.txt').read_text().splitlines()
    qc = {r['profile']: int(r['accepted_genomes_fixed196']) for r in tsv_read(args.markers / 'marker_qc.tsv')}
    check(len(names) == len(set(names)) == 100 and analyses[0]['markers'] == analyses[1]['markers'] == analyses[3]['markers'] == names
          and analyses[2]['markers'] == [n for n in names if qc[n] >= 187] and len(analyses[2]['markers']) == 88,
          'Frozen marker sensitivities changed')
    accepted_rows = tsv_read(args.markers / 'accepted_sequence_manifest.tsv')
    accepted = {(r['assembly_accession'], r['profile']): r for r in accepted_rows}
    check(len(accepted) == len(accepted_rows) == 19359, 'Accepted source cell duplicates/missing')
    marker_alignments, marker_checks = {}, []
    for name in names:
        expected = {key: row for (key, marker), row in accepted.items() if marker == name}
        aligned, outcome = marker_audit(source / 'markers' / name, args.markers / 'marker_sequences' / (name + '.faa'), expected)
        marker_alignments[name] = aligned
        marker_checks.append({'profile': name, **outcome})
    outcomes = [partition_audit(source / 'analyses' / a['name'], a, marker_alignments, accepted) for a in analyses]
    check(outcomes == gate['alignment_checks'] and marker_checks == gate['marker_checks'], 'Independent current source/partition reconstruction differs from original gate')
    check(manifest == summary['analyses'] and [m['name'] for m in manifest] == NAMES, 'Original four payload manifests differ')
    required = {'concatenated.faa', 'concatenated.clw', 'concatenated.phy', 'concatenated.nex', 'partitions.tsv', 'partitions.nex',
                'partitions.raxml.txt', 'source_block_mapping.tsv', 'accessions.txt', 'marker_order.txt', 'identical_alignment_groups.json', 'tip_label_map.tsv'}
    for item, a, outcome in zip(manifest, analyses, outcomes):
        check(set(item['file_sha256']) == required and item['taxa'] == len(a['accessions']) and item['markers'] == len(a['markers'])
              and item['columns'] == outcome['columns'], 'Original exhaustive alignment payload accounting differs')
        verify_files(source / 'analyses' / item['name'], item['file_sha256'])
    publication_gate(json_read(args.alignment_publication), digest(args.alignment_validation))
    phases, failed_exit_sha, failed_stderr_sha = original_phase_gate(args, old)
    return frozen, gate, outcomes, upstream, phases, failed_exit_sha, failed_stderr_sha


def previous_failure_gate(args, original):
    """Distinct failed-v3 source/receipt reader; never grants tree completion."""
    check(args.previous_input != args.input and args.previous_control != args.source_control, 'Preserved failed namespace must remain separate')
    frozen_path = args.previous_input / 'inference_freeze.json'
    frozen = json_read(frozen_path)
    old = frozen['identity']
    state_path = args.previous_control / 'state.json'
    state = json_read(state_path)
    check(frozen['status'] == 'FROZEN_RESUMED_INFERENCE_BEFORE_TOPOLOGY' and frozen['alignment_reexecution'] is False
          and frozen['analyses'] == original['analyses'] and old['alignment_producer_identity'] == original['identity']
          and old['alignment_validation_sha256'] == digest(args.alignment_validation)
          and old['iqtree_address_space_limit_bytes'] == 1610612736 and old['outer_address_space_limit_bytes'] == 2147483648,
          'Actual previous v3 freeze/source/caps differ')
    check(state['scope'] == 'full196' and state['completed'] == {} and state['current']['phase'] == 'trees'
          and state['identity']['inference_identity'] == old, 'Previous failed v3 phase must not be certified complete')
    prior_sources = {'resumed_producer_sha256': args.root / 'scripts/stage04_inference_v3.py',
        'resumed_controller_sha256': args.root / 'scripts/stage04_inference_controller_v3.py',
        'resumed_validator_sha256': args.root / 'scripts/stage04_inference_validate_v3.py',
        'limit_helper_sha256': args.root / 'scripts/stage04_iqtree_limit_v3.py',
        'observer_sha256': args.original_observer_source, 'config_sha256': args.root / 'config/host_inference_stage04_v3.json',
        'resource_receipt_sha256': args.root / 'reports/stage04/resumed_inference_resource_preflight_v3.json'}
    for field, path in prior_sources.items():
        relative = path.relative_to(args.root).as_posix()
        check(old[field] == state['identity']['file_sha256'].get(relative) == digest(path),
              'Actually executed previous source hash missing/changed: ' + field)
    verify_files(args.root, state['identity']['file_sha256'])
    phase_path = safe_member(args.root, state['current']['receipt_directory']) / 'linux_exit_receipt.json'
    exited = json_read(phase_path)
    launch = json_read(phase_path.parent / 'linux_launch_receipt.json')
    check(exited['execution'] == 'ACTUAL_LINUX_PHASE_CHILD_EXITED' and exited['exit_code'] != 0
          and exited['identity'] == launch['identity'] == state['identity']
          and exited['invocation_id'] == launch['invocation_id'] == state['current']['invocation_id']
          and exited['job_pid'] == launch['job_pid'] > 0 and exited['launcher_pid'] == launch['launcher_pid'] > 0
          and launch['address_space_limit_bytes'] == 2147483648, 'Previous phase actual failure/observer/outer cap differs')
    attempt = args.previous_failed_attempt.parent
    native_args = SimpleNamespace(alignment_input=args.alignment_input, input=args.previous_input, host_env=args.host_env)
    argv = exact_argv(native_args, frozen['analyses'][0])
    proof = attempt_audit(attempt, argv, old, args.host_env, prior_sources['limit_helper_sha256'],
                          required_exit=2, native_limit=1610612736, outer_limit=2147483648)
    stderr = attempt / 'iqtree3.stderr.txt'
    check('allocation of 2084933760 bytes failed' in stderr.read_text()
          and not (attempt.parent / 'tree_complete.json').exists()
          and not (args.previous_input / 'phylogeny_summary.json').exists(), 'Previous actual resource failure is absent or falsely completed')
    evidence_path = args.root / 'reports/stage04b/failure_evidence_validation.json'
    evidence = json_read(evidence_path)
    check(evidence['status'] == 'ACTUAL_FAILED_INFERENCE_EVIDENCE_VERIFIED_ONLY' and evidence['scientific_stage04'] == 'INCOMPLETE'
          and evidence['completed_native_trees'] == 0 and evidence['native_exit'] == 2
          and evidence['native_pid'] == proof['child_pid'] and evidence['native_address_space_cap_bytes'] == 1610612736
          and evidence['failed_single_allocation_bytes'] == 2084933760
          and evidence['native_command_receipt_sha256'] == digest(args.previous_failed_attempt)
          and evidence['actual_phase_exit_receipt_sha256'] == digest(phase_path)
          and evidence['native_limit_receipt_sha256'] == digest(attempt / 'iqtree3.limit.json')
          and evidence['exact_failed_job_and_observer_absent'] is True, 'Distinct actual failure-only evidence binding differs')
    pub = json_read(args.previous_publication)
    bindings = {'failed_native_attempt_sha256': digest(args.previous_failed_attempt), 'failed_native_stderr_sha256': digest(stderr),
        'previous_inference_freeze_sha256': digest(frozen_path), 'failed_phase_exit_sha256': digest(phase_path),
        'failure_evidence_validation_sha256': digest(evidence_path)}
    check(pub['status'] == 'UPLOAD_VERIFIED' and pub['scientific_validation'] == 'INCOMPLETE_ACTUAL_RESOURCE_FAILURE'
          and pub['approved_assemblies'] == 196 and pub['whole_stage04_phylogeny'] == 'NOT_COMPLETED'
          and pub['remote_tag_commit_verified'] is True and all(pub.get(k) == v for k, v in bindings.items())
          and re.fullmatch('[0-9a-f]{40}', pub['payload_commit']), 'Previous failure publication not verified/current')
    check(len(pub['assets']) == 1 and pub['release_tag'] == 'stage04b-inference-resource-failure196-v1', 'Previous standalone failure Release scope differs')
    for asset in pub['assets']:
        check(asset['bytes'] > 0 and asset['payload_members'] > 0 and re.fullmatch('[0-9a-f]{64}', asset['sha256'])
              and all(asset[k] is True for k in ('download_readback_verified', 'all_zip_member_hashes_verified', 'sidecar_readback_verified')),
              'Previous failed-namespace portable bytes not verified')
    return {'previous_inference_identity': old, 'previous_inference_freeze_sha256': digest(frozen_path),
        'previous_controller_state_sha256': digest(state_path), 'previous_failed_native_attempt_sha256': bindings['failed_native_attempt_sha256'],
        'previous_failed_native_stderr_sha256': bindings['failed_native_stderr_sha256'], 'previous_failed_phase_exit_sha256': bindings['failed_phase_exit_sha256'],
        'previous_failure_evidence_validation_sha256': bindings['failure_evidence_validation_sha256'],
        'previous_inference_file_sha256': {p.relative_to(args.previous_input).as_posix(): digest(p) for p in args.previous_input.rglob('*') if p.is_file()},
        'previous_source_sha256': {p.relative_to(args.root).as_posix(): digest(p) for p in prior_sources.values()},
        'previous_input': args.previous_input.relative_to(args.root).as_posix(), 'previous_control': args.previous_control.relative_to(args.root).as_posix(),
        'previous_failed_attempt': args.previous_failed_attempt.relative_to(args.root).as_posix(),
        'previous_failure_release_tag': pub['release_tag'], 'previous_failure_payload_commit': pub['payload_commit'],
        'windows_minimum_available_bytes': WINDOWS_MIN, 'linux_minimum_available_bytes': LINUX_MIN, 'windows_reserve_bytes': 1073741824}


def resource_gate(receipt, identity):
    before = receipt['windows_before_wsl_resources']['available_bytes']
    after = receipt['windows_after_wsl_resources']['available_bytes']
    check(receipt['maximum_compute_threads'] == 2 and receipt['iqtree_memory_mib'] == 3072
          and receipt['process_address_space_limit_bytes'] == OUTER and receipt['iqtree_address_space_limit_bytes'] == LIMIT
          and receipt['native_memory_option'] == identity['native_memory_option']
          and receipt['windows_minimum_available_bytes'] == WINDOWS_MIN and receipt['linux_minimum_available_bytes'] == LINUX_MIN
          and receipt['windows_reserve_bytes'] == 1073741824
          and receipt['measured_windows_available_bytes'] == min(before, after)
          and min(before, after) >= WINDOWS_MIN
          and receipt['measured_windows_available_bytes'] >= WINDOWS_MIN and receipt['measured_linux_available_bytes'] >= LINUX_MIN,
          'Measured explicit new envelope/headroom/reserve receipt differs')


def inference_gate(args, original, phases, failed_exit_sha, failed_stderr_sha):
    frozen = json_read(args.input / 'inference_freeze.json')
    identity = frozen['identity']
    check(frozen['status'] == 'FROZEN_RESUMED_INFERENCE_BEFORE_TOPOLOGY' and frozen['alignment_reexecution'] is False
          and frozen['analyses'] == original['analyses'] and identity['alignment_producer_identity'] == original['identity'],
          'Separate resumed namespace changes original analyses/identity')
    policy_gate(json_read(args.config))
    check(args.checker_source.resolve() == Path(__file__).resolve(), 'Executed checker path differs from controller-bound checker')
    paths = {'resumed_producer_sha256': args.producer_source, 'resumed_controller_sha256': args.controller_source,
        'resumed_validator_sha256': Path(__file__), 'limit_helper_sha256': args.limit_helper,
        'source_producer_sha256': args.source_producer, 'source_validator_sha256': args.source_validator,
        'source_controller_sha256': args.source_controller, 'observer_sha256': args.observer_source,
        'original_observer_sha256': args.original_observer_source,
        'wsl_wrapper_sha256': args.wsl_wrapper, 'config_sha256': args.config, 'resource_receipt_sha256': args.resource_receipt,
        'original_analysis_freeze_sha256': args.alignment_input / 'analysis_freeze.json',
        'original_alignment_summary_sha256': args.alignment_input / 'alignment_summary.json',
        'original_analysis_manifest_sha256': args.alignment_input / 'analysis_alignment_manifest.json',
        'alignment_validation_sha256': args.alignment_validation, 'failed_native_attempt_sha256': args.failed_attempt,
        'iqtree3_sha256': args.host_env / 'bin/iqtree3'}
    check(all(identity[k] == digest(p) for k, p in paths.items()), 'Current executed resumed freeze/source/tool/config hashes differ')
    previous = previous_failure_gate(args, original)
    check(all(identity.get(k) == v for k, v in previous.items()), 'Previous applied-cap/failure/publication provenance differs from current v4 identity')
    check(identity['original_successful_phase_exit_sha256'] == phases and identity['original_failed_phase_exit_sha256'] == failed_exit_sha
          and identity['failed_native_stderr_sha256'] == failed_stderr_sha
          and identity['source_alignment_input'] == args.alignment_input.relative_to(args.root).as_posix()
          and identity['source_control'] == args.source_control.relative_to(args.root).as_posix()
          and identity['failed_native_attempt'] == args.failed_attempt.relative_to(args.root).as_posix()
          and identity['maximum_compute_threads'] == 2 and identity['outer_address_space_limit_bytes'] == OUTER
          and identity['iqtree_address_space_limit_bytes'] == LIMIT
          and identity['native_memory_option'] == 'OMITTED_UNSUPPORTED_WITH_PARTITION_MODELS'
          and identity['root_policy'] == 'EXPLICITLY_UNROOTED_NO_VALIDATED_OUTGROUP', 'Resumed executed scope/resource/failure provenance differs')
    resource = json_read(args.resource_receipt)
    resource_gate(resource, identity)
    launch = json_read(args.input / 'runner_launch_receipt.json')
    check(launch['identity'] == identity and launch['outer_AS'] == [OUTER, OUTER]
          and 1 <= len(set(launch['cpu_affinity'])) <= 2 and launch['runner_pid'] > 0 and launch['parent_pid'] > 0,
          'Actual resumed runner outer resource proof missing')
    return identity


def exact_argv(args, analysis):
    source = args.alignment_input / 'analyses' / analysis['name']
    tree = args.input / 'analyses' / analysis['name'] / 'iqtree'
    return [str(args.host_env / 'bin/iqtree3'), '-s', str(source / 'concatenated.faa'), '--seqtype', 'AA',
            '-p', str(source / 'partitions.nex'), '-m', 'MFP', '-B', '1000', '--alrt', '1000', '--seed', '1961008',
            '-T', '2', '-keep-ident', '--boot-trees', '--prefix', str(tree / 'host')]


def attempt_audit(attempt, argv, identity, host_env, helper, required_exit=0, native_limit=LIMIT, outer_limit=OUTER):
    command = json_read(attempt / 'iqtree3.command.json')
    launch = json_read(attempt / 'iqtree3.launch.json')
    limit_path = attempt / 'iqtree3.limit.json'
    limited = json_read(limit_path)
    observed = json_read(attempt / 'iqtree3.actual_exe.json')
    check(command['execution'] == 'ACTUAL_NATIVE_CHILD_EXITED' and command['exit_code'] == required_exit
          and command['actual_native_executable_observed'] is True and command['limit_receipt_sha256'] == digest(limit_path)
          and command['identity'] == launch['identity'] == limited['identity'] == observed['identity'] == identity,
          'Actual native successful attempt/limit identity missing')
    wrapper = [str(host_env / 'bin/python'), '-u', str(helper), '--receipt-file', str(limit_path),
               '--identity-file', str(attempt / 'identity.json'), '--', *argv]
    check(command['argv'] == launch['argv'] == limited['argv'] == argv
          and command['wrapper_argv'] == launch['wrapper_argv'] == wrapper
          and json_read(attempt / 'identity.json') == identity and launch['execution'] == 'ACTUAL_EXTERNAL_LIMIT_HELPER_STARTED',
          'Actual native argv/helper input differs')
    check(command['child_pid'] == launch['child_pid'] == limited['pid'] == observed['pid'] > 0
          and command['runner_pid'] == launch['runner_pid'] == limited['parent_pid'] > 0
          and limited['start_ticks'] == observed['start_ticks'] > 0
          and limited['boot_id'] == observed['boot_id'] and re.fullmatch('[0-9a-f-]{36}', limited['boot_id']),
          'Native PID/start/boot identity differs across exec')
    check(limited['execution'] == 'ACTUAL_LIMIT_SET_IMMEDIATELY_BEFORE_NATIVE_EXEC'
          and limited['outer_address_space_soft_hard_bytes'] == [outer_limit, outer_limit]
          and limited['native_address_space_soft_hard_bytes'] == [native_limit, native_limit]
          and 1 <= len(set(limited['cpu_affinity'])) <= 2
          and limited['limit_helper_source_sha256'] == identity['limit_helper_sha256']
          and limited['binary_sha256'] == observed['binary_sha256'] == identity['iqtree3_sha256']
          and observed['execution'] == 'ACTUAL_PINNED_NATIVE_EXECUTABLE_OBSERVED', 'Actually applied native hard resource/executable proof differs')
    for key in ('elapsed_seconds', 'child_cpu_seconds', 'children_peak_rss_bytes_cumulative'):
        check(math.isfinite(float(command[key])) and command[key] >= 0, 'Invalid actual native resource measurement')
    for name in ('iqtree3.stdout.txt', 'iqtree3.stderr.txt'):
        check((attempt / name).is_file(), 'Actual native command stream missing')
    return {'attempt': attempt.name, 'child_pid': command['child_pid'], 'start_ticks': limited['start_ticks'],
            'boot_id': limited['boot_id'], 'command_sha256': digest(attempt / 'iqtree3.command.json'),
            'limit_sha256': digest(limit_path), 'actual_exe_sha256': digest(attempt / 'iqtree3.actual_exe.json'),
            'elapsed_seconds': command['elapsed_seconds'], 'child_cpu_seconds': command['child_cpu_seconds'],
            'children_peak_rss_bytes_cumulative': command['children_peak_rss_bytes_cumulative']}


def finite_tree_parse(path, format):
    """Reject malformed/nonfinite branch tokens before Biopython can relabel them.

    Quoted labels (including doubled quote escapes) and nested comments are
    excluded from token inspection; colons inside those are not branch syntax.
    """
    text = Path(path).read_text()
    visible = []
    quote, comments, index = None, 0, 0
    while index < len(text):
        char = text[index]
        if comments:
            if char == '[': comments += 1
            elif char == ']': comments -= 1
            visible.append(' ')
        elif quote:
            visible.append(' ')
            if char == quote:
                if index + 1 < len(text) and text[index + 1] == quote:
                    visible.append(' '); index += 1
                else: quote = None
        elif char in ("'", '"'):
            quote = char; visible.append(' ')
        elif char == '[':
            comments = 1; visible.append(' ')
        else:
            visible.append(char)
        index += 1
    check(quote is None and comments == 0, 'Unclosed quoted tree label/comment')
    syntax = ''.join(visible)
    number = r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?'
    for colon in re.finditer(':', syntax):
        token = re.match(r'\s*(' + number + r')(?=\s*[,();]|\s*$)', syntax[colon.end():])
        check(token is not None, 'Malformed/nonfinite raw tree branch token')
        value = float(token.group(1))
        check(math.isfinite(value) and value >= 0, 'Nonfinite/negative raw tree branch length')
    for tree in Phylo.parse(io.StringIO(text), format):
        check(all(node.branch_length is None or (math.isfinite(node.branch_length) and node.branch_length >= 0)
                  for node in tree.find_clades()), 'Nonfinite/negative parsed tree branch length')
        yield tree


def resumed_tree_audit(args, analysis, identity, completed):
    source = args.alignment_input / 'analyses' / analysis['name']
    tree_dir = args.input / 'analyses' / analysis['name'] / 'iqtree'
    receipt = json_read(tree_dir / 'tree_complete.json')
    expected_identity = {'stage04_identity': identity, 'concat_sha256': digest(source / 'concatenated.faa'),
                         'partitions_sha256': digest(source / 'partitions.nex'), 'alignment_validation_sha256': digest(args.alignment_validation)}
    check(receipt['execution'] == 'COMPUTATION_OUTPUTS_CHECKED' and receipt['identity'] == expected_identity,
          'Resumed tree computation/source receipt differs')
    required = {'host.treefile', 'host.contree', 'host.log', 'host.iqtree', 'host.ufboot', 'host.best_scheme.nex',
                'unrooted.nwk', 'unrooted.nex', 'unrooted_labeled.nwk', 'unrooted_labeled.nex'}
    check(required <= set(receipt['file_sha256']), 'Resumed native report/tree/portable coverage missing')
    actual_members = {p.relative_to(tree_dir).as_posix() for p in tree_dir.rglob('*') if p.is_file() and p != tree_dir / 'tree_complete.json'}
    check(set(receipt['file_sha256']) == actual_members, 'Tree immutable manifest omits/adds actual native/attempt evidence')
    verify_files(tree_dir, receipt['file_sha256'])
    ids = analysis['accessions']
    alignment = records(source / 'concatenated.faa', aligned=True)
    trees = list(finite_tree_parse(tree_dir / 'host.treefile', 'newick'))
    check(len(trees) == 1 and trees[0].rooted is False, 'Final native tree rooted/multiple')
    tree = trees[0]
    for file, format in [('host.treefile', 'newick'), ('host.contree', 'newick'), ('unrooted.nwk', 'newick'), ('unrooted.nex', 'nexus')]:
        parsed = list(finite_tree_parse(tree_dir / file, format))
        check(len(parsed) == 1, 'Portable/native tree must contain one tree')
        labels = [n.name for n in parsed[0].get_terminals()]
        check(len(labels) == len(set(labels)) == len(ids) and set(labels) == set(ids), 'Tree exact-tip membership changed')
        check(all(n.branch_length is None or (math.isfinite(n.branch_length) and n.branch_length >= 0) for n in parsed[0].find_clades()),
              'Nonfinite/negative tree branch length')
        if file.startswith('unrooted'):
            check(split_sets(parsed[0], ids) == split_sets(tree, ids), 'Portable unrooted export changes native splits')
    supports, omitted = branch_support_states(tree, alignment)
    count = 0
    for replicate in finite_tree_parse(tree_dir / 'host.ufboot', 'newick'):
        labels = [n.name for n in replicate.get_terminals()]
        check(len(labels) == len(set(labels)) == len(ids) and set(labels) == set(ids), 'Native UFBoot replicate missing/duplicate/foreign tip')
        check(all(n.branch_length is None or (math.isfinite(n.branch_length) and n.branch_length >= 0) for n in replicate.find_clades()), 'Invalid bootstrap branch length')
        count += 1
    check(count == 1000, 'Native1000 UFBoot replicates not present')
    report = (tree_dir / 'host.iqtree').read_text()
    check(re.search(r'1000.*(?:ultrafast|bootstrap)|(?:ultrafast|bootstrap).*1000', report, re.I)
          and re.search(r'SH-aLRT|SH-like|SH approximate', report, re.I), 'Native report lacks actual requested support methods')
    schemes = (tree_dir / 'host.best_scheme.nex').read_text()
    partitions = tsv_read(source / 'partitions.tsv')
    expected_coords = [(r['partition'], r['start_one_based'], r['end_one_based']) for r in partitions]
    check(re.findall(r'charset\s+(\S+)\s*=\s*(\d+)\s*-\s*(\d+)\s*;', schemes, re.I) == expected_coords,
          'Actual ModelFinder scheme merged/reordered/resized frozen partitions')
    model_lines = re.findall(r'charpartition\s+\S+\s*=\s*([^;]+);', schemes, re.I)
    check(len(model_lines) == 1, 'Actual selected model partition absent/ambiguous')
    assignments = [p.strip() for p in model_lines[0].split(',')]
    check(len(assignments) == len(partitions) and [p.rsplit(':', 1)[1].strip() for p in assignments] == [r['partition'] for r in partitions]
          and all(p.rsplit(':', 1)[0].strip() for p in assignments), 'Actual ModelFinder model allocation incomplete/different')
    attempts = []
    if receipt['execution_source'] == 'ACTUAL_IQTREE3_EXTERNAL_RLIMIT_WITH_NATIVE_RESUMABLE_CHECKPOINTS':
        argv = exact_argv(args, analysis)
        invocation = json_read(tree_dir / 'inference_identity.json')
        check(invocation == {'identity': expected_identity, 'argv': argv, 'external_cap_bytes': LIMIT}, 'Frozen exact native argv differs')
        check('--mem' not in argv and '-mem' not in argv, 'Unsupported memory option reintroduced')
        for attempt in sorted(tree_dir.glob('attempt_*')):
            path = attempt / 'iqtree3.command.json'
            check(path.is_file(), 'Unfinished attempt lacks actual exit; no final PASS')
            command = json_read(path)
            check(command['identity'] == identity and command['argv'] == argv, 'Prior resumable native attempt identity differs')
            if command['exit_code'] == 0:
                attempt_files = {'identity.json', 'iqtree3.command.json', 'iqtree3.launch.json', 'iqtree3.limit.json',
                                 'iqtree3.actual_exe.json', 'iqtree3.stdout.txt', 'iqtree3.stderr.txt'}
                check(all(attempt.name + '/' + f in receipt['file_sha256'] for f in attempt_files), 'Completed native attempt evidence omitted from frozen manifest')
                attempts.append(attempt_audit(attempt, argv, identity, args.host_env, args.limit_helper))
        check(len(attempts) == 1, 'Exactly one actual native successful attempt required')
    else:
        check(receipt['execution_source'] == 'REUSED_EXACT_IDENTICAL_ALIGNMENT_PARTITION_INFERENCE'
              and receipt['source_analysis'] in completed, 'Reuse lacks independently completed source inference')
        origin = args.alignment_input / 'analyses' / receipt['source_analysis']
        check(digest(origin / 'concatenated.faa') == digest(source / 'concatenated.faa')
              and digest(origin / 'partitions.nex') == digest(source / 'partitions.nex'), 'Reuse source alignment/partitions not byte-identical')
        origin_tree = args.input / 'analyses' / receipt['source_analysis'] / 'iqtree'
        check(receipt['source_tree_complete_sha256'] == digest(origin_tree / 'tree_complete.json'), 'Reused source completed inference receipt changed')
        for file in required:
            check(digest(origin_tree / file) == digest(tree_dir / file), 'Reused inference bytes differ from independently audited source')
    labels = tsv_read(source / 'tip_label_map.tsv')
    label_map = {r['tree_label']: r['assembly_accession'] for r in labels}
    check(len(label_map) == len(labels) == len(ids) and set(label_map.values()) == set(ids), 'Labeled tip map duplicates/missing')
    for name, format in [('unrooted_labeled.nwk', 'newick'), ('unrooted_labeled.nex', 'nexus')]:
        exported = list(finite_tree_parse(tree_dir / name, format))
        check(len(exported) == 1, 'Labeled export contains multiple trees')
        # Bio.Nexus can retain the Newick quote delimiters in taxon names.
        # Decode only its quoted form that exactly matches the frozen label map.
        if format == 'nexus':
            for tip in exported[0].get_terminals():
                name = tip.name
                if name not in label_map and isinstance(name, str) and len(name) >= 2 and name[0] == name[-1] == "'":
                    decoded = name[1:-1].replace("''", "'")
                    check(decoded in label_map, 'Quoted NEXUS taxon is outside the exact label map')
                    tip.name = decoded
        tips = [n.name for n in exported[0].get_terminals()]
        check(len(tips) == len(set(tips)) == len(ids) and set(tips) == set(label_map), 'Labeled exported tips differ')
        for tip in exported[0].get_terminals(): tip.name = label_map[tip.name]
        check(split_sets(exported[0], ids) == split_sets(tree, ids), 'Labeled export changed native topology')
    return tree, {'analysis': analysis['name'], 'tips': len(ids), 'support_nodes': supports,
        'native_omitted_identical_group_supports': omitted, 'actual_ufboot_replicates': count,
        'root_policy': 'UNROOTED_ANALYTICAL_POLICY_NO_VALIDATED_OUTGROUP', 'native_attempts': attempts,
        'execution_source': receipt['execution_source'], 'tree_complete_sha256': digest(tree_dir / 'tree_complete.json')}


def validation(args):
    original, gate, alignments, upstream, phases, failed_exit_sha, failed_stderr_sha = alignment_gate(args)
    identity = inference_gate(args, original, phases, failed_exit_sha, failed_stderr_sha)
    report = {'status': 'PASS_RESUMED_INFERENCE_PRECONDITIONS_PHYLOGENY_NOT_RUN', 'utc': datetime.now(timezone.utc).isoformat(),
        'producer_identity': original['identity'], 'inference_identity': identity, 'validator_source_sha256': digest(__file__),
        'inference_freeze_sha256': digest(args.input / 'inference_freeze.json'),
        'original_analysis_freeze_sha256': digest(args.alignment_input / 'analysis_freeze.json'),
        'original_alignment_summary_sha256': digest(args.alignment_input / 'alignment_summary.json'),
        'original_analysis_manifest_sha256': digest(args.alignment_input / 'analysis_alignment_manifest.json'),
        'alignment_summary_sha256': digest(args.alignment_input / 'alignment_summary.json'),
        'analysis_freeze_sha256': digest(args.alignment_input / 'analysis_freeze.json'),
        'analysis_manifest_sha256': digest(args.alignment_input / 'analysis_alignment_manifest.json'),
        'alignment_validation_sha256': digest(args.alignment_validation), 'alignment_publication_sha256': digest(args.alignment_publication),
        'original_successful_phase_exit_sha256': phases, 'original_failed_phase_exit_sha256': failed_exit_sha,
        'failed_native_attempt_sha256': digest(args.failed_attempt), 'failed_native_stderr_sha256': failed_stderr_sha,
        'upstream_marker_gate': upstream, 'analyses_verified': 4, 'primary_tip_ids': 196, 'profiles_aligned': 100,
        'previous_inference_freeze_sha256': identity['previous_inference_freeze_sha256'],
        'previous_failed_native_attempt_sha256': identity['previous_failed_native_attempt_sha256'],
        'previous_failed_native_stderr_sha256': identity['previous_failed_native_stderr_sha256'],
        'previous_failed_phase_exit_sha256': identity['previous_failed_phase_exit_sha256'],
        'previous_failure_evidence_validation_sha256': identity['previous_failure_evidence_validation_sha256'],
        'alignment_checks': alignments, 'tree_execution': 'NOT_RUN_PRECONDITION_CHECK_ONLY',
        'biopython_version': Bio.__version__, 'publication': 'NOT_CHECKED_FULL_STAGE04'}
    if args.phase == 'final':
        summary = json_read(args.input / 'phylogeny_summary.json')
        check(summary['execution'] == 'ALL_PRIMARY_AND_SENSITIVITY_INFERENCES_COMPLETED' and summary['identity'] == identity
              and summary['inference_freeze_sha256'] == report['inference_freeze_sha256']
              and summary['alignment_validation_sha256'] == report['alignment_validation_sha256']
              and [a['analysis'] for a in summary['analyses']] == NAMES
              and summary['root_policy'] == identity['root_policy'] and summary['optional_concordance'] == 'NOT_RUN',
              'Actual completed new-namespace phylogeny summary differs')
        trees, outcomes, done = {}, [], set()
        for a, declared in zip(original['analyses'], summary['analyses']):
            tree, outcome = resumed_tree_audit(args, a, identity, done)
            check(declared['tree_complete_sha256'] == outcome['tree_complete_sha256'] and declared['tips'] == outcome['tips']
                  and declared['bootstrap_trees_verified'] == 1000, 'Native summary differs from independently checked files')
            trees[a['name']] = tree; outcomes.append(outcome); done.add(a['name'])
        comparisons = []
        for a in original['analyses'][1:]:
            left, right = split_sets(trees['primary196'], a['accessions']), split_sets(trees[a['name']], a['accessions'])
            distance, denominator = len(left ^ right), len(left) + len(right)
            comparisons.append({'analysis': a['name'], 'common_tips': len(a['accessions']), 'unrooted_robinson_foulds': distance,
                'observed_split_denominator': denominator, 'normalized_rf_observed_splits': distance / denominator if denominator else 0,
                'method': 'Restrict edge bipartitions to common taxa, remove trivial/duplicate splits; topology only, no branch-length or root comparison'})
        metadata = tsv_read(args.root / 'config/approved_panel.tsv'); group_checks = []
        for a in original['analyses']:
            scope = set(a['accessions']); splits = split_sets(trees[a['name']], scope)
            for group in sorted({r['operational_group'] for r in metadata}):
                members = {r['assembly_accession'] for r in metadata if r['operational_group'] == group} & scope; other = scope - members
                separated = len(members) < 2 or len(other) < 2 or min(tuple(sorted(members)), tuple(sorted(other))) in splits
                group_checks.append({'analysis': a['name'], 'operational_group': group, 'members': len(members),
                    'group_separated_by_unrooted_edge': separated,
                    'interpretation': 'Metadata/topology comparison only; no manual tree edits or sequence taxonomic certification'})
        report.update(status=FINAL_STATUS, tree_execution='INDEPENDENTLY_CHECKED', tree_checks=outcomes,
            sensitivity_comparisons=comparisons, taxonomy_split_comparisons=group_checks,
            phylogeny_summary_sha256=digest(args.input / 'phylogeny_summary.json'), optional_concordance='NOT_RUN',
            root_policy='EXPLICITLY_UNROOTED_NO_VALIDATED_OUTGROUP', scientific_blockers=[],
            alignment_reexecution=False, original_failed_inference_claimed_complete=False)
    atomic_json(args.output / 'validation_summary.json', report)
    print(json.dumps({'status': report['status'], 'analyses_verified': 4, 'primary_tip_ids': 196}))


def parse():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['preflight', 'final'], default='final')
    defaults = {'root': Path.cwd(), 'input': '.work/stage04_inference_v4', 'alignment_input': '.work/stage04_phylogeny_v2',
        'alignment_validation': '.work/stage04_alignment_validation/validation_summary.json',
        'alignment_publication': 'reports/stage04a/publication_receipt.json', 'source_control': '.work/stage04_controller',
        'config': 'config/host_inference_stage04_v4.json', 'resource_receipt': 'reports/stage04/resumed_inference_resource_preflight_v4.json',
        'host_env': '.tools/linux/host_env', 'producer_source': 'scripts/stage04_inference_v4.py',
        'controller_source': 'scripts/stage04_inference_controller_v4.py', 'limit_helper': 'scripts/stage04_iqtree_limit_v4.py',
        'checker_source': 'scripts/stage04_inference_validate_v4.py',
        'source_producer': 'scripts/stage04_phylogeny.py', 'source_validator': 'scripts/stage04_validate.py',
        'source_controller': 'scripts/stage04_controller.py', 'observer_source': 'scripts/stage04_linux_launcher_v4.py', 'original_observer_source': 'scripts/stage04_linux_launcher.py',
        'wsl_wrapper': 'scripts/wsl_project.sh', 'host_config': 'config/host_primary_stage03_v1.json',
        'original_resource_receipt': 'reports/stage04/resource_preflight.json', 'markers': '.work/stage03_orthology_v2',
        'marker_validation': '.work/stage03_curated_validation/validation_summary.json',
        'orthology_config': 'config/host_orthology_stage03_v2.json', 'original_markers': '.work/stage03_markers_v1',
        'original_marker_validation': '.work/stage03_marker_validation/validation_summary.json',
        'output': '.work/stage04_final_validation_v4'}
    defaults.update(previous_input='.work/stage04_inference_v3', previous_control='.work/stage04_inference_controller_v3',
        previous_publication='reports/stage04b/publication_receipt.json',
        previous_failed_attempt='.work/stage04_inference_v3/analyses/primary196/iqtree/attempt_0001/iqtree3.command.json')
    for name, value in defaults.items(): parser.add_argument('--' + name.replace('_', '-'), type=Path, default=Path(value))
    parser.add_argument('--failed-attempt', type=Path, required=True)
    args = parser.parse_args(); args.root = args.root.resolve()
    for name, value in vars(args).copy().items():
        if isinstance(value, Path):
            value = value.resolve() if value.is_absolute() else (args.root / value).resolve()
            check(value == args.root or args.root in value.parents, 'Dedicated repository path required')
            setattr(args, name, value)
    check(args.input != args.alignment_input and args.alignment_input not in args.input.parents
          and args.output not in (args.input, args.alignment_input), 'Separate inference/validation namespaces required')
    return args


if __name__ == '__main__':
    args = parse()
    try:
        validation(args)
    except Exception as error:
        atomic_json(args.output / 'validation_failure.json', {'status': 'FAIL', 'phase': args.phase,
            'error': str(error), 'outputs_preserved': True, 'scientific_stage04_complete': False})
        raise


