#!/usr/bin/env python3
"""Independent BioPython format, source-column, partition and tree checks.

Does not import the producer. Reads exported formats separately and reconstructs
every concatenation block from actual trimmed alignments and source manifests.
No alignments or phylogenetic inference are computed by this checker.
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


def tree_audit(directory, analysis, identity):
    ids = analysis['accessions']
    tree_dir = directory / 'iqtree'
    receipt = json_read(tree_dir / 'tree_complete.json')
    check(receipt['execution'] == 'COMPUTATION_OUTPUTS_CHECKED' and receipt['identity']['stage04_identity'] == identity,
          'Actual tree receipt missing/different')
    check(receipt['identity']['concat_sha256'] == digest(directory / 'concatenated.faa')
          and receipt['identity']['partitions_sha256'] == digest(directory / 'partitions.nex'), 'Tree input identity differs')
    for name, value in receipt['file_sha256'].items():
        check(digest(tree_dir / name) == value, 'Tree evidence bytes changed')
    trees = list(Phylo.parse(tree_dir / 'host.treefile', 'newick'))
    check(len(trees) == 1, 'Final Newick contains multiple/no trees')
    tree = trees[0]
    for file, format in [('host.treefile', 'newick'), ('unrooted.nwk', 'newick'), ('unrooted.nex', 'nexus'), ('host.contree', 'newick')]:
        parsed = list(Phylo.parse(tree_dir / file, format))
        check(len(parsed) == 1, 'Tree export does not contain exactly one tree')
        labels = [tip.name for tip in parsed[0].get_terminals()]
        check(len(labels) == len(set(labels)) == len(ids) and set(labels) == set(ids), 'Tree export exact-tip membership differs')
        check(all(n.branch_length is None or n.branch_length >= 0 for n in parsed[0].find_clades()), 'Negative branch length')
        if file in ('unrooted.nwk', 'unrooted.nex'):
            check(split_sets(parsed[0], ids) == split_sets(tree, ids), 'Portable tree export changed topology')
    alignment = records(directory / 'concatenated.faa', aligned=True)
    support_nodes, omitted_identical_nodes = branch_support_states(tree, alignment)
    count = 0
    for replicate in Phylo.parse(tree_dir / 'host.ufboot', 'newick'):
        tips = [node.name for node in replicate.get_terminals()]
        check(len(tips) == len(set(tips)) == len(ids) and set(tips) == set(ids), 'Actual UFBoot replicate tip membership differs')
        count += 1
    check(count == 1000, 'Actual UFBoot replicate count differs')
    report = (tree_dir / 'host.iqtree').read_text(encoding='utf-8')
    check(re.search(r'1000.*(?:ultrafast|bootstrap)|(?:ultrafast|bootstrap).*1000', report, re.I)
          and re.search(r'SH-aLRT|SH-like|SH approximate', report, re.I), 'Executed support methods absent in native report')
    if receipt['execution_source'] == 'ACTUAL_IQTREE3_WITH_NATIVE_RESUMABLE_CHECKPOINTS':
        invocation = json_read(tree_dir / 'inference_identity.json')
        argv = invocation['argv']
        options = {'-s': str(directory / 'concatenated.faa'), '-p': str(directory / 'partitions.nex'), '--seqtype': 'AA',
                   '-m': 'MFP', '-B': '1000', '--alrt': '1000', '--seed': '1961008', '-T': '2',
                   '--mem': str(identity['iqtree_memory_mib']) + 'M'}
        for flag, expected in options.items():
            check(argv.count(flag) == 1 and argv[argv.index(flag) + 1] == expected, 'Actual IQ-TREE option differs: ' + flag)
        check('-keep-ident' in argv and '--boot-trees' in argv
              and not any(x in argv for x in ['-o', '--merge', '--redo', '--redo-tree', '-g']), 'Unfrozen/root/merge/redo IQ-TREE argument')
        commands = list(tree_dir.glob('attempt_*/iqtree3.command.json'))
        check(any(json_read(path)['exit_code'] == 0 and json_read(path)['argv'] == argv for path in commands), 'No actual completed IQ-TREE command receipt')
        schemes = list(tree_dir.glob('host.best_scheme.nex'))
        check(len(schemes) == 1, 'Actual per-partition ModelFinder scheme file missing')
        scheme = schemes[0].read_text()
        names = re.findall(r'charset\s+(\S+)\s*=', scheme, re.I)
        check(names == [row['partition'] for row in tsv_read(directory / 'partitions.tsv')], 'ModelFinder removed/merged/reordered partitions')
        check(re.search(r'charpartition\s+\S+\s*=\s*[^;]+:', scheme, re.I), 'Actual selected partition model mapping absent')
    else:
        check(receipt['execution_source'] == 'REUSED_EXACT_IDENTICAL_ALIGNMENT_PARTITION_INFERENCE', 'Unknown tree provenance')
        source = directory.parent / receipt['source_analysis']
        check(digest(source / 'concatenated.faa') == digest(directory / 'concatenated.faa')
              and digest(source / 'partitions.nex') == digest(directory / 'partitions.nex'), 'Reused inference input is not byte-identical')
    label_rows = tsv_read(directory / 'tip_label_map.tsv')
    label_ids = {row['tree_label']: row['assembly_accession'] for row in label_rows}
    check(len(label_ids) == len(label_rows) == len(ids) and set(label_ids.values()) == set(ids), 'Labeled tree exact-ID map differs')
    for name, format in [('unrooted_labeled.nwk', 'newick'), ('unrooted_labeled.nex', 'nexus')]:
        exported = list(Phylo.parse(tree_dir / name, format))
        check(len(exported) == 1, 'Labeled portable file must contain one tree')
        labels = [tip.name for tip in exported[0].get_terminals()]
        check(len(labels) == len(set(labels)) == len(ids) and set(labels) == set(label_ids), 'Labeled portable tree tip names differ')
        for tip in exported[0].get_terminals():
            tip.name = label_ids[tip.name]
        check(split_sets(exported[0], ids) == split_sets(tree, ids), 'Labeled tree export changed topology')
    return tree, {'analysis': analysis['name'], 'tips': len(ids), 'support_nodes': support_nodes,
                  'native_omitted_identical_group_supports': omitted_identical_nodes,
                  'actual_ufboot_replicates': count, 'root_policy': 'UNROOTED_ANALYTICAL_POLICY_NO_VALIDATED_OUTGROUP'}


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


def validation(args):
    output, stage03 = args.input.resolve(), args.markers.resolve()
    for name in ['root', 'marker_validation', 'config', 'producer_source', 'orthology_config', 'original_markers', 'original_marker_validation', 'host_env', 'resource_receipt']:
        if getattr(args, name) is not None:
            setattr(args, name, getattr(args, name).resolve())
    frozen = json_read(output / 'analysis_freeze.json')
    summary = json_read(output / 'alignment_summary.json')
    identity = frozen['identity']
    upstream = upstream_marker_gate(args, identity, stage03)
    current_files = {'approved_accessions_sha256': args.root / 'config/approved_accessions.txt',
        'approved_metadata_sha256': args.root / 'config/approved_panel.tsv',
        'sensitivity162_source_sha256': args.root / 'evidence/g0/reports/sensitivity162_accessions.txt',
        'marker_qc_sha256': stage03 / 'marker_qc.tsv', 'stage03_runtime_receipt_sha256': stage03 / 'runtime/runtime_receipt.json',
        'resource_receipt_sha256': args.resource_receipt,
        'mafft_sha256': args.host_env / 'bin/mafft', 'trimal_sha256': args.host_env / 'bin/trimal',
        'iqtree3_sha256': args.host_env / 'bin/iqtree3'}
    check(all(identity[name] == digest(path) for name, path in current_files.items()),
          'Current frozen panel/metadata/sensitivity/QC/runtime/resource/tool bytes changed')
    check(summary['identity'] == identity and frozen['status'] == 'FROZEN_BEFORE_STAGE04_ALIGNMENT_AND_TOPOLOGY', 'Frozen stage4 identity differs')
    accessions = (args.root / 'config/approved_accessions.txt').read_text().split()
    check(len(accessions) == len(set(accessions)) == 196 and frozen['analyses'][0]['accessions'] == accessions,
          'Primary exact196 membership differs')
    check(identity['accepted_manifest_sha256'] == digest(stage03 / 'accepted_sequence_manifest.tsv')
          and identity['primary_marker_order_sha256'] == digest(stage03 / 'primary_marker_order.txt'), 'Stage3 source manifest/order changed')
    analyses = frozen['analyses']
    check([a['name'] for a in analyses] == ['primary196', 'sensitivity162', 'sensitivity187_markers', 'sensitivity_complete155'], 'Sensitivity analyses missing/reordered')
    check([len(a['accessions']) for a in analyses] == [196, 162, 196, 155], 'Sensitivity cohort counts differ')
    sensitivity = (args.root / 'evidence/g0/reports/sensitivity162_accessions.txt').read_text().split()
    check(set(analyses[1]['accessions']) == set(sensitivity) and len(set(sensitivity)) == 162, 'Exact G0 sensitivity162 membership differs')
    metadata = tsv_read(args.root / 'config/approved_panel.tsv')
    complete = {r['assembly_accession'] for r in metadata if r['assembly_level'] in ('Complete Genome', 'Chromosome')}
    check(set(analyses[3]['accessions']) == complete and len(complete) == 155, 'High-contiguity frozen metadata sensitivity differs')
    names = (stage03 / 'primary_marker_order.txt').read_text().splitlines()
    qc = {r['profile']: int(r['accepted_genomes_fixed196']) for r in tsv_read(stage03 / 'marker_qc.tsv')}
    check(analyses[0]['markers'] == analyses[1]['markers'] == analyses[3]['markers'] == names
          and analyses[2]['markers'] == [name for name in names if qc[name] >= 187], 'Sensitivity marker lists differ from fixed thresholds')
    accepted_rows = tsv_read(stage03 / 'accepted_sequence_manifest.tsv')
    accepted = {(r['assembly_accession'], r['profile']): r for r in accepted_rows}
    check(len(accepted) == len(accepted_rows), 'Repeated source-manifest cell')
    marker_alignments, marker_outcomes = {}, []
    for name in names:
        expected = {a: row for (a, marker), row in accepted.items() if marker == name}
        alignment, outcome = marker_audit(output / 'markers' / name, stage03 / 'marker_sequences' / (name + '.faa'), expected)
        marker_alignments[name] = alignment
        marker_outcomes.append({'profile': name, **outcome})
    alignment_outcomes = [partition_audit(output / 'analyses' / analysis['name'], analysis, marker_alignments, accepted) for analysis in analyses]
    manifest = json_read(output / 'analysis_alignment_manifest.json')
    check(len(manifest) == 4, 'Analysis payload manifest missing cohort')
    for item in manifest:
        for name, value in item['file_sha256'].items():
            check(digest(output / 'analyses' / item['name'] / name) == value, 'Concatenation manifest bytes changed')
    report = {'status': 'PASS_ALIGNMENT_FORMATS_AND_PARTITIONS', 'utc': datetime.now(timezone.utc).isoformat(),
              'analyses_verified': 4, 'primary_tip_ids': 196, 'profiles_aligned': len(names),
              'alignment_summary_sha256': digest(output / 'alignment_summary.json'),
              'analysis_freeze_sha256': digest(output / 'analysis_freeze.json'),
              'analysis_manifest_sha256': digest(output / 'analysis_alignment_manifest.json'),
              'producer_identity': identity, 'validator_source_sha256': digest(__file__), 'biopython_version': Bio.__version__,
              'upstream_marker_gate': upstream,
              'marker_checks': marker_outcomes, 'alignment_checks': alignment_outcomes,
              'tree_execution': 'NOT_CHECKED_ALIGNMENT_PHASE', 'publication': 'NOT_CHECKED'}
    if args.phase == 'final':
        trees, outcomes = {}, []
        for analysis in analyses:
            tree, outcome = tree_audit(output / 'analyses' / analysis['name'], analysis, identity)
            trees[analysis['name']] = tree
            outcomes.append(outcome)
        comparisons = []
        for analysis in analyses[1:]:
            common = analysis['accessions']
            primary_splits = split_sets(trees['primary196'], common)
            alternative_splits = split_sets(trees[analysis['name']], common)
            observed = len(primary_splits ^ alternative_splits)
            denominator = len(primary_splits) + len(alternative_splits)
            comparisons.append({'analysis': analysis['name'], 'common_tips': len(common), 'unrooted_robinson_foulds': observed,
                 'observed_split_denominator': denominator, 'normalized_rf_observed_splits': observed / denominator if denominator else 0,
                 'method': 'Restrict edge bipartitions to common taxa, remove trivial/duplicate splits; topology only, no branch-length or root comparison'})
        group_checks = []
        for analysis in analyses:
            scope = set(analysis['accessions'])
            splits = split_sets(trees[analysis['name']], scope)
            for group in sorted({r['operational_group'] for r in metadata}):
                members = {r['assembly_accession'] for r in metadata if r['operational_group'] == group} & scope
                opposite = scope - members
                compatible = len(members) < 2 or len(opposite) < 2 or min(tuple(sorted(members)), tuple(sorted(opposite))) in splits
                group_checks.append({'analysis': analysis['name'], 'operational_group': group, 'members': len(members),
                     'group_separated_by_unrooted_edge': compatible, 'interpretation': 'Metadata/topology comparison only; no manual tree edits or sequence taxonomic certification'})
        report.update(status='PASS_HOST_PHYLOGENY_AND_SENSITIVITY_OUTPUT_INTEGRITY', tree_execution='INDEPENDENTLY_CHECKED',
                      tree_checks=outcomes, sensitivity_comparisons=comparisons, taxonomy_split_comparisons=group_checks,
                      phylogeny_summary_sha256=digest(output / 'phylogeny_summary.json'),
                      optional_concordance='NOT_RUN', root_policy='EXPLICITLY_UNROOTED_NO_VALIDATED_OUTGROUP')
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'validation_summary.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'analyses_verified': 4, 'primary_tip_ids': 196}, indent=2))


def self_test():
    # Synthetic fixtures are not a biological subset or phylogenetic computation.
    results = []
    def reject(name, operation):
        try:
            operation()
        except (ValueError, AssertionError, KeyError):
            results.append(name)
            return
        raise AssertionError('Malformed synthetic fixture accepted: ' + name)
    with tempfile.TemporaryDirectory(prefix='stage04-independent-synthetic-') as temp:
        directory = Path(temp)
        ids = ['SYNTHETIC_1.1', 'SYNTHETIC_2.1', 'SYNTHETIC_3.1', 'SYNTHETIC_4.1']
        alignment = MultipleSeqAlignment([SeqRecord(Seq('MA--KR'), id=key, description='', annotations={'molecule_type': 'protein'}) for key in ids])
        for suffix, format in [('faa', 'fasta'), ('clw', 'clustal'), ('phy', 'phylip-relaxed'), ('nex', 'nexus')]:
            AlignIO.write(alignment, directory / ('toy.' + suffix), format)
        check(compare_formats(directory, 'toy', ids) == {key: 'MA--KR' for key in ids}, 'Synthetic format agreement failed')
        results.append('independent_fasta_clustal_phylip_nexus_parsers')
        (directory / 'toy.phy').write_text('4 6\n' + '\n'.join(key + ' MA--KQ' for key in ids) + '\n')
        reject('cross_format_residue_mismatch', lambda: compare_formats(directory, 'toy', ids))
        (directory / 'duplicate.faa').write_text('>same\nMK\n>same\nMK\n')
        reject('duplicate_fasta_target', lambda: records(directory / 'duplicate.faa'))
        (directory / 'map.txt').write_text('#ColumnsMap\t0, 1, 4, 5\n')
        check(native_columns(directory / 'map.txt') == [0, 1, 4, 5], 'Synthetic native map parsing failed')
        results.append('native_trim_column_map')
        (directory / 'map.txt').write_text('#ColumnsMap\t0, 1, 1, 5\n')
        reject('repeated_native_column', lambda: native_columns(directory / 'map.txt'))
        first = Phylo.read(io.StringIO('((A:1,B:1)90/95:1,(C:1,D:1)85/96:1);'), 'newick')
        rotated = Phylo.read(io.StringIO('(D:1,(B:1,A:1)90/95:1,C:1);'), 'newick')
        changed = Phylo.read(io.StringIO('((A:1,C:1):1,(B:1,D:1):1);'), 'newick')
        check(split_sets(first, list('ABCD')) == split_sets(rotated, list('ABCD')), 'Unrooted rotation changed canonical splits')
        results.append('unrooted_split_rotation_invariance')
        check(len(split_sets(first, list('ABCD')) ^ split_sets(changed, list('ABCD'))) == 2, 'Synthetic RF mismatch')
        results.append('unrooted_topology_difference')
        identical = Phylo.read(io.StringIO('((A:0,B:0):0,(C:1,D:1)80/90:1);'), 'newick')
        sequences = {'A': 'MKR', 'B': 'MKR', 'C': 'MKN', 'D': 'AKR'}
        count, omitted = branch_support_states(identical, sequences)
        check(count == 1 and len(omitted) == 1 and omitted[0]['support_state'].startswith('NOT_REPORTED'), 'Native missing identical-group support invented')
        results.append('native_zero_identical_group_support_omission_preserved')
        rejects_missing = Phylo.read(io.StringIO('((A:0,C:0):0,(B:1,D:1)80/90:1);'), 'newick')
        reject('missing_support_outside_identical_group', lambda: branch_support_states(rejects_missing, sequences))
    print(json.dumps({'status': 'PASS_SYNTHETIC_INDEPENDENT_STAGE04_FIXTURES', 'fixtures': results,
                      'biological_execution': 'NOT_RUN'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--phase', choices=['alignment', 'final'], default='alignment')
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--input', type=Path, default=Path('.work/stage04_phylogeny_v1'))
    parser.add_argument('--markers', type=Path, default=Path('.work/stage03_markers_v1'))
    parser.add_argument('--marker-validation', type=Path, default=Path('.work/stage03_marker_validation/validation_summary.json'))
    parser.add_argument('--config', type=Path, default=Path('config/host_primary_stage03_v1.json'))
    parser.add_argument('--producer-source', type=Path, default=Path('scripts/stage04_phylogeny.py'))
    parser.add_argument('--host-env', type=Path, default=Path('.tools/linux/host_env'))
    parser.add_argument('--resource-receipt', type=Path, default=Path('reports/stage04/resource_preflight.json'))
    parser.add_argument('--orthology-config', type=Path)
    parser.add_argument('--original-markers', type=Path)
    parser.add_argument('--original-marker-validation', type=Path)
    parser.add_argument('--output', type=Path, default=Path('.work/stage04_alignment_validation'))
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        try:
            validation(args)
        except Exception as error:
            args.output.mkdir(parents=True, exist_ok=True)
            (args.output / 'validation_failure.json').write_text(json.dumps({'status': 'FAIL', 'phase': args.phase,
                 'error': str(error), 'outputs_preserved': True}, indent=2) + '\n')
            raise
