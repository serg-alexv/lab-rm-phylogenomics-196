#!/usr/bin/env python3
"""Full196 actual GToTree serial extraction and independently parsed marker inventory.

Invoke in Linux through scripts/wsl_project.sh host; root owns the workflow lock.
No alignment, tree or detector computation is performed. Independent stage-wide
validation/publication are separate from this producer's inventory construction.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
try:
    import resource
except ImportError:  # Windows pure synthetic fixtures; production is Linux only.
    resource = None
import shlex
import shutil
import statistics
import subprocess
import sys
import time
import zipfile


def require(ok, detail):
    if not ok:
        raise ValueError(detail)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def seqsha(sequence):
    return hashlib.sha256(sequence.encode('ascii')).hexdigest()


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + '.partial')
    partial.write_bytes(data if isinstance(data, bytes) else data.encode('utf-8'))
    partial.replace(path)


def save_json(path, data):
    write(path, json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def tsv(path, rows, columns):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, columns, delimiter='\t', lineterminator='\n', extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        writer.writerow({k: json.dumps(v, separators=(',', ':')) if isinstance(v, (dict, list)) else v
                         for k, v in row.items()})
    write(path, stream.getvalue())


def fasta(data, duplicate_ids=False):
    rows, title, chunks = [], None, []
    text = data.decode('ascii') if isinstance(data, bytes) else data
    def append():
        require(chunks, 'Empty FASTA sequence')
        sequence = ''.join(chunks)
        require(set(sequence) <= set('ACDEFGHIKLMNPQRSTVWYBXZUOJ*'), 'Invalid/case-changed protein sequence')
        rows.append((title.split()[0], title, sequence))
    for line in text.splitlines():
        if not line:
            continue
        if line.startswith('>'):
            if title is not None:
                append()
            title, chunks = line[1:], []
            require(title and not title[0].isspace(), 'Invalid FASTA header')
        else:
            require(title is not None and not any(c.isspace() for c in line), 'Malformed FASTA sequence')
            chunks.append(line)
    if title is not None:
        append()
    require(rows, 'No FASTA records')
    require(duplicate_ids or len(rows) == len({r[0] for r in rows}), 'Repeated FASTA target IDs')
    return rows


def profiles(path):
    rows = []
    for block in path.read_text(encoding='ascii').split('//'):
        if not block.strip():
            continue
        fields = {}
        for line in block.splitlines():
            pieces = line.split(maxsplit=1)
            if len(pieces) == 2 and pieces[0] in ('NAME', 'ACC', 'DESC', 'LENG', 'GA'):
                require(pieces[0] not in fields, 'Duplicate HMM metadata field')
                fields[pieces[0]] = pieces[1]
        require(set(fields) == {'NAME', 'ACC', 'DESC', 'LENG', 'GA'}, 'Incomplete pinned profile metadata')
        require(re.fullmatch(r'[A-Za-z0-9_.-]+', fields['NAME']), 'Unsafe profile NAME')
        ga = fields['GA'].replace(';', '').split()
        require(len(ga) == 2, 'Invalid profile GA cutoffs')
        description = fields['DESC'].lower()
        unresolved = (any(x in description for x in ('unknown', 'uncharacter', 'predicted spout'))
                      or fields['NAME'] in {'ATP_bind_2', 'CTP_transf_1', 'Cytidylate_kin2', 'DHOase',
                                           'Ham1p_like', 'IPPT', 'IPT', 'NifU_N', 'UPF0052', 'UPF0054',
                                           'YbbR', 'YGGT', 'YbaB_DNA_bd'})
        explicit_rm = bool(re.search(r'restriction|dna.*methyl|methyl.*dna', description))
        review = ('EXPLICIT_RM_OR_DNA_METHYLASE_DESCRIPTION_REVIEW_REQUIRED' if explicit_rm else
                  'GENERIC_OR_UNCHARACTERIZED_FAMILY_REVIEW_REQUIRED' if unresolved else
                  'PROFILE_DESCRIPTION_HAS_HOST_FUNCTION_NO_EXPLICIT_RM_DESCRIPTION')
        rows.append({'profile': fields['NAME'], 'profile_accession': fields['ACC'],
                     'profile_description': fields['DESC'], 'profile_length': int(fields['LENG']),
                     'ga_sequence': float(ga[0]), 'ga_domain': float(ga[1]), 'source_ga_text': fields['GA'],
                     'annotation_review_state': review,
                     'review_limit': 'Profile/source annotations require review; absence of explicit RM words is not proof of protein function'})
    require(len(rows) == len({r['profile'] for r in rows}) == 119, 'Pinned HMM requires 119 unique profiles')
    return rows


def raw_source_proteins(root, accession, validation, host_faa):
    """Different reader from locus-input producer: raw primary FAA plus Stage2 exact locus evidence."""
    path = root / 'data/raw_ncbi' / accession / (accession + '.ncbi.zip')
    require(sha(path) == validation['raw_zip_sha256'], 'Raw source changed after Stage2 validation')
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        catalog_names = [n for n in names if PurePosixPath(n).name == 'dataset_catalog.json']
        require(len(catalog_names) == 1, 'Ambiguous raw source catalog')
        catalog_name = catalog_names[0]
        selected = [a for a in json.loads(z.read(catalog_name))['assemblies'] if a.get('accession') == accession]
        require(len(selected) == 1, 'Exact raw catalog assembly missing/duplicate')
        entries = [e for e in selected[0]['files'] if e['fileType'] == 'PROTEIN_FASTA']
        require(len(entries) == 1, 'Raw primary protein role missing/duplicate')
        name, base = entries[0]['filePath'], str(PurePosixPath(catalog_name).parent)
        found = {name, base + '/' + name, base + '/data/' + name, 'ncbi_dataset/data/' + name} & set(names)
        require(len(found) == 1, 'Raw primary protein role unresolved')
        source_rows = fasta(z.read(found.pop()), duplicate_ids=True)
    primary = defaultdict(list)
    for pid, title, sequence in source_rows:
        primary[pid].append((title, sequence))
    require(all(len({s for _, s in rows}) == 1 for rows in primary.values()), 'Conflicting repeated source accession')
    source = {}
    for row in validation['loci']:
        pid, key = row.get('protein_accession'), row['locus_key']
        if not pid:
            continue
        require(key not in source and pid in primary, 'Ambiguous/unmapped independently validated source locus')
        sequence = primary[pid][0][1]
        require(seqsha(sequence) == row['protein_sequence_sha256'] == row['source_translation_sha256'],
                'Raw primary protein differs from independently validated GBFF translation')
        source[key] = {**row, 'sequence': sequence,
                       'source_primary_headers': [title for title, _ in primary[pid]]}
    wanted = fasta(host_faa.read_bytes())
    require({row[0] for row in wanted} == set(source), 'Host locus input does not retain all source protein-bearing loci')
    for key, _, sequence in wanted:
        require(sequence == source[key]['sequence'], 'Host locus input changed source sequence')
    return source, wanted


def table_rows(path, columns):
    lines = path.read_text(encoding='utf-8').splitlines()
    require(lines and lines[0].startswith('#') and lines[-1].strip() == '# [ok]', 'Incomplete native HMM table: ' + str(path))
    result = []
    for number, line in enumerate(lines, 1):
        if line.startswith('#') or not line.strip():
            continue
        values = line.split(maxsplit=columns)
        require(len(values) >= columns, 'Truncated HMM row at ' + str(number))
        result.append((number, values))
    return result


def inspect_search(accession, evidence, attempt, source, wanted, profile_rows, identity):
    """Reparse raw HMM outputs and source joins independently of GToTree extraction logic."""
    rename, search = read_json(evidence / 'rename_receipt.json'), read_json(evidence / 'hmm_receipt.json')
    require(rename['status'] == 'RENAMING_IDENTITY_VERIFIED'
            and rename['wrapper_sha256'] == identity['wrapper_sha256'], 'Rename receipt incomplete/different')
    require(search['status'] == 'HMM_OUTPUTS_PRESERVED' and search['exit_code'] == 0
            and search['identity']['profile_sha256'] == identity['profile_sha256']
            and search['identity']['binary_sha256'] == identity['hmmsearch_sha256']
            and search['identity']['wrapper_sha256'] == identity['wrapper_sha256'], 'HMM search failed/not run/different')
    require(set(search['output_sha256']) == {'hmm.tblout', 'hmm.domtblout', 'hmm.stdout.txt', 'hmm.stderr.txt'}, 'Required HMM evidence digest missing')
    for name, expected in search['output_sha256'].items():
        require(sha(evidence / name) == expected, 'HMM evidence bytes changed')
    queries = re.findall(r'^Query:\s+(\S+)\s+\[M=\d+\]', (evidence / 'hmm.stdout.txt').read_text(), re.M)
    require(queries == [r['profile'] for r in profile_rows], 'Incomplete/out-of-order HMM profile search')
    original = fasta((evidence / 'unaltered_locus_input.faa').read_bytes())
    expected = [r for r in wanted if len(r[2]) <= 99999]
    require(original == expected, 'Actual GToTree input guard differs from declared source >99999-aa exclusion')
    require(sha(evidence / 'unaltered_locus_input.faa') == rename['input_sha256'], 'Preserved rename input differs')
    require(sha(evidence / 'gtotree_search_input.faa') == rename['renamed_input_sha256'] == search['identity']['input_sha256'], 'Preserved search input differs')
    renamed = fasta((evidence / 'gtotree_search_input.faa').read_bytes())
    with (evidence / 'target_locus_map.tsv').open(encoding='utf-8', newline='') as stream:
        crosswalk = list(csv.DictReader(stream, delimiter='\t'))
    require(len(crosswalk) == len(renamed) == len(original), 'Actual rename counts differ')
    target_to_locus = {}
    for index, (mapping, new, old) in enumerate(zip(crosswalk, renamed, original), 1):
        target = accession + '_' + str(index)
        require(mapping['gtotree_target_id'] == new[0] == target and mapping['exact_locus_key'] == old[0]
                and new[2] == old[2] == source[old[0]]['sequence']
                and mapping['unaltered_sequence_sha256'] == seqsha(new[2]), 'Exact source/rename target join failed')
        target_to_locus[target] = old[0]
    profile = {r['profile']: r for r in profile_rows}
    hits, seen, copies = [], set(), defaultdict(list)
    for number, x in table_rows(evidence / 'hmm.tblout', 18):
        target, name = x[0], x[2]
        require(target in target_to_locus and name in profile and (target, name) not in seen, 'Unknown/duplicate HMM target/query pair')
        require(x[3] == profile[name]['profile_accession'], 'HMM query accession differs from pinned profile')
        seen.add((target, name))
        key = target_to_locus[target]
        row = {'assembly_accession': accession, 'profile': name, 'profile_accession': x[3],
               'target_id': target, 'locus_key': key, 'protein_accession': source[key]['protein_accession'],
               'source_sequence_sha256': seqsha(source[key]['sequence']), 'protein_aa_length': len(source[key]['sequence']),
               'full_evalue': float(x[4]), 'full_score': float(x[5]), 'full_bias': float(x[6]),
               'best_domain_evalue': float(x[7]), 'best_domain_score': float(x[8]),
               'source_tblout_line': number, 'source_partial_or_fuzzy': source[key]['partial_or_fuzzy'],
               'source_pseudo': source[key]['pseudo'], 'source_exceptions': source[key]['source_exceptions'],
               'source_primary_headers': source[key]['source_primary_headers'],
               'gbff_location': source[key]['gbff_location'], 'gbff_parts_zero_based': source[key]['gbff_parts_zero_based'],
               'sequence': source[key]['sequence']}
        require(row['full_score'] + 0.051 >= profile[name]['ga_sequence'], 'Reported full score conflicts with GA reporting threshold')
        hits.append(row)
        copies[name].append(row)
    domains = []
    for number, x in table_rows(evidence / 'hmm.domtblout', 22):
        target, name = x[0], x[3]
        require((target, name) in seen and x[4] == profile[name]['profile_accession'], 'Domain row lacks matching source HMM hit')
        key, length = target_to_locus[target], len(source[target_to_locus[target]]['sequence'])
        require(int(x[2]) == length and int(x[5]) == profile[name]['profile_length'], 'HMM domain source/profile length differs')
        hf, ht, af, at, ef, et = map(int, x[15:21])
        require(1 <= hf <= ht <= int(x[5]) and 1 <= ef <= af <= at <= et <= length, 'HMM domain coordinate outside source sequence/profile')
        domains.append({'assembly_accession': accession, 'profile': name, 'profile_accession': x[4],
                        'target_id': target, 'locus_key': key, 'protein_accession': source[key]['protein_accession'],
                        'source_domtblout_line': number, 'domain_number': int(x[9]), 'domains_on_target': int(x[10]),
                        'conditional_evalue': float(x[11]), 'independent_evalue': float(x[12]), 'domain_score': float(x[13]),
                        'hmm_from': hf, 'hmm_to': ht, 'ali_from': af, 'ali_to': at, 'env_from': ef, 'env_to': et,
                        'hmm_coverage': (ht - hf + 1) / int(x[5]), 'source_sequence_coverage': (at - af + 1) / length,
                        'domain_accuracy': float(x[21])})
    counts_path = attempt / 'helper_output/SCG_hit_counts.tsv'
    native_order = (attempt / 'temporary/uniq_hmm_names.tmp').read_text().splitlines()
    require(native_order == [p['profile'] for p in profile_rows], 'Actual native uniq-file profile order differs')
    lines = [line.split('\t') for line in counts_path.read_text().splitlines() if line.strip()]
    require(len(lines) == 1 and lines[0][0] == accession and len(lines[0]) == 120, 'GToTree copy count table incomplete/duplicated')
    for p, observed in zip(profile_rows, lines[0][1:]):
        require(int(observed) == len(copies[p['profile']]), 'GToTree copy count differs from independent tblout parser')
        native = attempt / 'temporary' / (p['profile'] + '_hits.faa')
        if len(copies[p['profile']]) == 1:
            values = fasta(native.read_bytes())
            require(len(values) == 1 and values[0][0] == accession
                    and values[0][2] == copies[p['profile']][0]['sequence'], 'Native GToTree extracted source sequence differs')
        else:
            require(not native.exists() or native.stat().st_size == 0, 'GToTree retained a missing/multicopy marker')
    exclusions = [{'assembly_accession': accession, 'locus_key': key, 'protein_accession': source[key]['protein_accession'],
                   'protein_aa_length': len(sequence), 'source_sequence_sha256': seqsha(sequence),
                   'reason': 'ACTUAL_GTOTREE_INPUT_GUARD_GT99999_AA'} for key, _, sequence in wanted if len(sequence) > 99999]
    return hits, domains, exclusions


def apply_filters(accessions, names, hits, config, native_bounds=None):
    by_cell = defaultdict(list)
    for row in hits:
        by_cell[(row['assembly_accession'], row['profile'])].append(row)
    medians = {}
    for name in names:
        lengths = [rows[0]['protein_aa_length'] for (a, m), rows in by_cell.items() if m == name and len(rows) == 1]
        if lengths:
            median = Decimal(str(statistics.median(lengths)))
            # Exact arithmetic fallback is for synthetic filter fixtures only.
            # Production supplies bounds from actual installed median/bc/printf.
            medians[name] = (float(median), int((median * Decimal('0.8')).quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)),
                             int((median * Decimal('1.2')).quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)))
    if native_bounds is not None:
        require(set(native_bounds) == set(medians), 'Native median length accounting differs')
        medians = native_bounds
    cells, occupancy, pre = [], defaultdict(int), defaultdict(int)
    for accession in accessions:
        for name in names:
            values = by_cell[(accession, name)]
            state, accepted = 'NO_QUALIFYING_HIT_AFTER_SUCCESSFUL_SEARCH', False
            if len(values) > 1:
                state = 'MULTICOPY_MISSING'
            elif len(values) == 1:
                _median, lower, upper = medians[name]
                accepted = lower <= values[0]['protein_aa_length'] <= upper
                state = 'LENGTH_ACCEPTED_SINGLE_COPY' if accepted else 'LENGTH_EXCLUDED'
            cell = {'assembly_accession': accession, 'profile': name, 'qualifying_distinct_loci': len(values),
                    'state': state, 'length_accepted': accepted,
                    'locus_key': values[0]['locus_key'] if len(values) == 1 else None,
                    'all_locus_keys': [v['locus_key'] for v in values]}
            cells.append(cell)
            if accepted:
                occupancy[name] += 1
                pre[accession] += 1
    retained = sorted(name for name in names if occupancy[name] >= config['marker_minimum_accepted_genomes'])
    post = defaultdict(int)
    accepted_sequences = []
    for cell in cells:
        if cell['length_accepted'] and cell['profile'] in retained:
            cell['state'] = 'PRIMARY_ACCEPTED'
            post[cell['assembly_accession']] += 1
            accepted_sequences.append(by_cell[(cell['assembly_accession'], cell['profile'])][0])
        elif cell['length_accepted']:
            cell['state'] = 'MARKER_LOW_OCCUPANCY'
    required_post = math.ceil(Decimal(str(config['post_occupancy_genome_recovery_minimum'])) * len(retained))
    blockers = []
    if not retained:
        blockers.append({'scope': 'marker_set', 'reason': 'NO_MARKER_PASSES_FIXED196_OCCUPANCY', 'observed': 0, 'required': 1})
    genomes = []
    for accession in accessions:
        if pre[accession] < config['genome_minimum_accepted_markers']:
            blockers.append({'scope': accession, 'reason': 'RECOVERY_BELOW_FIXED119_MINIMUM', 'observed': pre[accession],
                             'required': config['genome_minimum_accepted_markers']})
        if post[accession] < required_post:
            blockers.append({'scope': accession, 'reason': 'RECOVERY_BELOW_POST_OCCUPANCY_MINIMUM', 'observed': post[accession], 'required': required_post})
        genomes.append({'assembly_accession': accession, 'length_accepted_markers': pre[accession], 'recovery_fixed119': pre[accession] / 119,
                        'primary_accepted_markers': post[accession], 'primary_marker_denominator': len(retained),
                        'post_occupancy_recovery': post[accession] / len(retained) if retained else None, 'post_minimum_markers': required_post})
    markers = [{'profile': name, 'median_single_copy_source_aa_length': medians.get(name, (None, None, None))[0],
                'inclusive_minimum_aa_length': medians.get(name, (None, None, None))[1],
                'inclusive_maximum_aa_length': medians.get(name, (None, None, None))[2],
                'accepted_genomes_fixed196': occupancy[name], 'occupancy_fixed196': occupancy[name] / 196,
                'primary_retained': name in retained} for name in sorted(names)]
    return cells, markers, genomes, retained, accepted_sequences, blockers


NATIVE_BOUNDS_SCRIPT = '''set -euo pipefail
median=$(gtt-get-median.sh "$1")
buff=$(echo "$median * 0.2" | bc)
min_len=$(echo "$median - $buff" | bc)
min_len_rnd=$(printf "%.0f\\n" "$min_len")
max_len=$(echo "$median + $buff" | bc)
max_len_rnd=$(printf "%.0f\\n" "$max_len")
printf '%s\\t%s\\t%s\\t%s\\t%s\\n' "$median" "$min_len" "$max_len" "$min_len_rnd" "$max_len_rnd"
'''


def native_length_bounds(args, names, hits, environment):
    by_cell = defaultdict(list)
    for row in hits:
        by_cell[(row['assembly_accession'], row['profile'])].append(row)
    bounds, receipts = {}, []
    write(args.output / 'length_method/native_bounds.sh', NATIVE_BOUNDS_SCRIPT)
    for name in names:
        lengths = [values[0]['protein_aa_length'] for (_, marker), values in by_cell.items()
                   if marker == name and len(values) == 1]
        if not lengths:
            continue
        path = args.output / 'length_method' / (name + '.singleton_lengths.txt')
        write(path, '\n'.join(map(str, lengths)) + '\n')
        argv = ['bash', str(args.output / 'length_method/native_bounds.sh'), str(path)]
        result = subprocess.run(argv, env=environment, capture_output=True, text=True, timeout=30)
        require(result.returncode == 0 and not result.stderr, 'Actual GToTree median/bc/printf computation failed')
        fields = result.stdout.strip().split('\t')
        require(len(fields) == 5, 'Incomplete actual median/bounds output')
        median, raw_minimum, raw_maximum, minimum, maximum = fields
        bounds[name] = (float(median), int(minimum), int(maximum))
        receipts.append({'profile': name, 'argv': argv, 'source_singleton_count': len(lengths),
                         'lengths_sha256': sha(path), 'native_median_text': median,
                         'bc_minimum_text': raw_minimum, 'bc_maximum_text': raw_maximum,
                         'printf_inclusive_minimum': int(minimum), 'printf_inclusive_maximum': int(maximum),
                         'exit_code': result.returncode})
    save_json(args.output / 'length_method/native_bounds_receipts.json', receipts)
    return bounds


def runtime_capture(args, environment):
    """Actual installed executable/help/source bytes; no biological invocation."""
    output = args.output / 'runtime'
    commands = [('gtotree_version', 'GToTree', ['--version']), ('gtotree_help', 'GToTree', ['-h']),
                ('hmmer_help_version', 'hmmsearch', ['-h']), ('sfetch_help_version', 'esl-sfetch', ['-h']),
                ('rename_help', 'gtt-rename-fasta-headers', ['-h']),
                ('filter_help', 'gtt-filter-seqs-by-length', ['-h']),
                ('mafft_version', 'mafft', ['--version']), ('mafft_help', 'mafft', ['--help']),
                ('trimal_version', 'trimal', ['--version']), ('trimal_help', 'trimal', ['-h']),
                ('iqtree3_version', 'iqtree3', ['--version']), ('iqtree3_help', 'iqtree3', ['-h'])]
    receipts = []
    for label, name, options in commands:
        binary = args.host_env / 'bin' / name
        require(binary.is_file(), 'Required actual native host executable absent: ' + name)
        argv = [str(binary), *options]
        result = subprocess.run(argv, cwd=args.root, env=environment, capture_output=True, timeout=45)
        write(output / (label + '.stdout.txt'), result.stdout)
        write(output / (label + '.stderr.txt'), result.stderr)
        require(result.stdout or result.stderr, 'Runtime help/version command returned no evidence: ' + name)
        require(result.returncode in (0, 1), 'Runtime help/version command failed: ' + name)
        receipts.append({'name': name, 'argv': argv, 'exit_code': result.returncode,
                         'binary_sha256': sha(binary), 'resolved_binary_sha256': sha(binary.resolve()),
                         'stdout_sha256': sha(output / (label + '.stdout.txt')),
                         'stderr_sha256': sha(output / (label + '.stderr.txt'))})
    sources = {}
    for name in ['GToTree', 'gtt-amino-acid-serial.sh', 'gtt-get-median.sh',
                 'gtt-rename-fasta-headers', 'gtt-filter-seqs-by-length']:
        source = args.host_env / 'bin' / name
        write(output / ('source_' + name + '.txt'), source.read_bytes())
        sources[name] = sha(source)
    programs = {}
    for name in ['GToTree', 'gtt-amino-acid-serial.sh', 'gtt-get-median.sh', 'gtt-rename-fasta-headers',
                 'gtt-filter-seqs-by-length', 'hmmsearch', 'esl-sfetch', 'mafft', 'trimal', 'iqtree3',
                 'bash', 'bc', 'awk', 'sort', 'grep', 'paste', 'sed', 'file']:
        found = str(args.host_env / 'bin' / name) if (args.host_env / 'bin' / name).is_file() else shutil.which(name, path=environment['PATH'])
        require(found, 'Required extraction/method runtime missing: ' + name)
        path = Path(found).resolve()
        programs[name] = {'path': str(path), 'sha256': sha(path)}
    packages = []
    for path in sorted((args.host_env / 'conda-meta').glob('*.json')):
        data = read_json(path)
        packages.append({k: data.get(k) for k in ['name', 'version', 'build', 'subdir', 'fn', 'sha256', 'md5']})
    save_json(output / 'installed_packages.json', packages)
    receipt = {'status': 'ACTUAL_INSTALLED_RUNTIME_HELP_AND_BYTES_CAPTURED', 'utc': datetime.now(timezone.utc).isoformat(),
               'python_version': sys.version, 'python_binary': sys.executable, 'python_binary_sha256': sha(sys.executable),
               'commands': receipts, 'programs': programs, 'source_sha256': sources,
               'packages_sha256': sha(output / 'installed_packages.json'), 'scientific_validation': 'NOT_RUN'}
    save_json(output / 'runtime_receipt.json', receipt)
    return receipt


def run_helper(args, identity, accession, input_path, profile_rows, environment):
    per = args.output / 'searches' / accession
    per.mkdir(parents=True, exist_ok=True)
    complete = per / 'search_complete.json'
    if complete.exists():
        record = read_json(complete)
        require(record['identity'] == identity and record['input_sha256'] == sha(input_path), 'Different cached search identity/input')
        for name, value in record['file_sha256'].items():
            path = per / name
            require(per.resolve() in path.resolve().parents and sha(path) == value, 'Cached helper evidence changed')
        return per / record['attempt']
    attempts = sorted(p for p in per.glob('attempt_*') if p.is_dir())
    attempt = per / ('attempt_' + f'{len(attempts) + 1:04d}')
    attempt.mkdir()
    temporary, output = attempt / 'temporary', attempt / 'helper_output'
    temporary.mkdir(); output.mkdir()
    write(temporary / 'uniq_hmm_names.tmp', '\n'.join(p['profile'] for p in profile_rows) + '\n')
    input_list = attempt / 'amino_acid_list.txt'
    write(input_list, str(input_path) + '\n')
    argv = ['bash', str(args.host_env / 'bin/gtt-amino-acid-serial.sh'), str(input_list), str(temporary), str(args.profile),
            '196', '2', '119', str(output), 'false', 'false', 'false', 'none']
    started = time.monotonic()
    child_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    with (attempt / 'helper.stdout.txt').open('wb') as stdout, (attempt / 'helper.stderr.txt').open('wb') as stderr:
        process = subprocess.Popen(argv, cwd=args.root, env=environment, stdout=stdout, stderr=stderr)
        save_json(attempt / 'launch_receipt.json', {'execution': 'ACTUAL_GTOTREE_SERIAL_HELPER_STARTED',
                  'utc': datetime.now(timezone.utc).isoformat(), 'runner_pid': os.getpid(), 'helper_pid': process.pid,
                  'assembly_accession': accession, 'argv': argv, 'scientific_validation': 'NOT_RUN'})
        exit_code = process.wait()
    child_after = resource.getrusage(resource.RUSAGE_CHILDREN)
    record = {'utc': datetime.now(timezone.utc).isoformat(), 'assembly_accession': accession, 'argv': argv,
              'exit_code': exit_code, 'elapsed_seconds': time.monotonic() - started,
              'runner_pid': os.getpid(), 'helper_pid': process.pid,
              'child_cpu_seconds': child_after.ru_utime + child_after.ru_stime - child_before.ru_utime - child_before.ru_stime,
              'children_peak_rss_bytes_cumulative': child_after.ru_maxrss * 1024,
              'measurement_reason': 'Linux child CPU delta and cumulative child maximum RSS; outer /usr/bin/time records whole runner resources',
              'identity': identity, 'input_sha256': sha(input_path), 'attempt': attempt.name}
    save_json(attempt / 'command_receipt.json', record)
    with (args.output / 'commands.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record) + '\n')
    require(exit_code == 0, 'Actual GToTree helper process failed: ' + accession)
    return attempt


def production(args):
    require(sys.platform == 'linux', 'Use scripts/wsl_project.sh host with installed Linux Python')
    args.root = args.root.resolve(); args.output = args.output.resolve(); args.inputs = args.inputs.resolve()
    args.validation = args.validation.resolve(); args.host_env = args.host_env.resolve(); args.profile = args.profile.resolve(); args.wrapper = args.wrapper.resolve()
    args.config = args.config.resolve(); args.locus_validation = args.locus_validation.resolve()
    require(args.root == Path.cwd().resolve() and args.root in args.output.parents, 'Dedicated WD repository/output required')
    accessions_path = args.root / 'config/approved_accessions.txt'
    accessions = accessions_path.read_text().split()
    config = read_json(args.config)
    require(len(accessions) == len(set(accessions)) == 196 and sha(accessions_path) == config['approved_accessions_sha256'], 'Exact approved196 mismatch')
    require(config['frozen_before_marker_search_and_topology'] is True
            and config['profile_count_independently_measured'] == config['genome_recovery_fixed_denominator'] == 119
            and config['genome_minimum_accepted_markers'] == 96 and config['marker_occupancy_fixed_denominator'] == 196
            and config['marker_minimum_accepted_genomes'] == 177 and config['genome_recovery_minimum'] == 0.8
            and config['marker_occupancy_minimum'] == 0.9 and '20' in config['length_filter']
            and config['post_occupancy_genome_recovery_denominator'] == 'retained_primary_markers'
            and config['post_occupancy_genome_recovery_minimum'] == 0.8, 'Frozen filters changed/unsupported')
    require(sha(args.profile) == config['profile_sha256'], 'Pinned HMM hash differs')
    profile_rows = profiles(args.profile)
    validation = read_json(args.validation / 'validation_summary.json')
    construction = read_json(args.inputs / 'construction_summary.json')
    require(validation['status'] == 'PASS_SEQUENCE_INTEGRITY_WITH_DOCUMENTED_EXCEPTIONS'
            and validation['complete_exact196_accounting'] is True and validation['error_count'] == 0
            and validation['approved_accessions_sha256'] == config['approved_accessions_sha256'], 'Stage2 full196 validation gate failed')
    require(construction['status'] == 'SOURCE_LOCUS_INPUTS_CONSTRUCTED' and construction['constructed_assemblies'] == 196
            and construction['identity']['panel_sha256'] == config['approved_accessions_sha256'], 'All196 locus inputs required')
    independent = read_json(args.locus_validation)
    require(independent['status'] == 'PASS_SOURCE_LOCUS_INPUT_TRACEABILITY'
            and independent['required_assemblies'] == independent['assemblies_audited'] == independent['assemblies_passed'] == 196
            and independent['failed_assemblies'] == [] and independent['global_errors'] == []
            and independent['complete_exact196_accounting'] is True
            and independent['panel_sha256'] == config['approved_accessions_sha256']
            and independent['builder_identity'] == construction['identity']
            and independent['builder_identity']['stage02_validation_summary_sha256'] == sha(args.validation / 'validation_summary.json'),
            'Independent full196 source-locus checker PASS/hash gate failed')
    identity = {'approved_accessions_sha256': sha(accessions_path), 'config_sha256': sha(args.config),
                'profile_sha256': sha(args.profile), 'runner_sha256': sha(__file__), 'wrapper_sha256': sha(args.wrapper),
                'source_construction_summary_sha256': sha(args.inputs / 'construction_summary.json'),
                'stage02_validation_summary_sha256': sha(args.validation / 'validation_summary.json'),
                'independent_source_locus_validation_summary_sha256': sha(args.locus_validation),
                'helper_sha256': sha(args.host_env / 'bin/gtt-amino-acid-serial.sh'),
                'hmmsearch_sha256': sha(args.host_env / 'bin/hmmsearch'),
                'rename_sha256': sha(args.host_env / 'bin/gtt-rename-fasta-headers')}
    args.output.mkdir(parents=True, exist_ok=True)
    if (args.output / 'input_identity.json').exists():
        require(read_json(args.output / 'input_identity.json') == identity, 'Output namespace has different code/input/environment')
    else:
        require(not list(args.output.iterdir()), 'Unowned output directory')
        save_json(args.output / 'input_identity.json', identity)
    environment = dict(os.environ)
    shims = args.output / 'shims'; shims.mkdir(exist_ok=True)
    for name, mode in [('gtt-rename-fasta-headers', 'rename'), ('hmmsearch', 'hmmsearch')]:
        script = shims / name
        write(script, '#!/bin/sh\nexec ' + shlex.quote(sys.executable) + ' ' + shlex.quote(str(args.wrapper)) + ' ' + mode + ' "$@"\n')
        script.chmod(0o755)
    environment.update(PATH=str(shims) + ':' + str(args.host_env / 'bin') + ':/usr/bin:/bin',
                       GTT_EVIDENCE_DIR=str(args.output / 'evidence'), GTT_REAL_RENAME=str(args.host_env / 'bin/gtt-rename-fasta-headers'),
                       GTT_REAL_HMMSEARCH=str(args.host_env / 'bin/hmmsearch'), OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2', LC_ALL='C')
    runtime = runtime_capture(args, environment)
    save_json(args.output / 'runner_launch_receipt.json', {'execution': 'ACTUAL_LINUX_RUNNER_STARTED_SOURCE_GATES_PASSED',
              'utc': datetime.now(timezone.utc).isoformat(), 'runner_pid': os.getpid(), 'parent_pid': os.getppid(),
              'argv': sys.argv, 'cwd': str(args.root), 'identity': identity, 'runtime_receipt_sha256': sha(args.output / 'runtime/runtime_receipt.json'),
              'cpu_affinity': sorted(os.sched_getaffinity(0)), 'rlimit_address_space': list(resource.getrlimit(resource.RLIMIT_AS)),
              'threads': 2, 'required_assemblies': 196, 'completed_searches': 0, 'scientific_validation': 'NOT_RUN'})
    save_json(args.output / 'execution_progress.json', {'execution': 'RUNNING', 'scientific_validation': 'NOT_RUN',
              'completed_searches': 0, 'required_assemblies': 196, 'remaining': 196, 'pid': os.getpid(),
              'source_gate': 'INDEPENDENT_FULL196_PASS', 'runtime_gate': runtime['status']})
    hits, domains, excluded_inputs, completed = [], [], [], []
    try:
        for index, accession in enumerate(accessions, 1):
            validated = read_json(args.validation / 'assemblies' / accession / 'validation.json')
            require(validated['error_count'] == 0 and validated['assembly_accession'] == accession, 'Failed/missing Stage2 exact assembly')
            input_path = args.inputs / 'assemblies' / accession / (accession + '.faa')
            builder_receipt = read_json(input_path.parent / 'build_receipt.json')
            require(builder_receipt['raw_zip_sha256'] == validated['raw_zip_sha256'], 'Locus construction source hash differs')
            source, wanted = raw_source_proteins(args.root, accession, validated, input_path)
            attempt = run_helper(args, identity, accession, input_path, profile_rows, environment)
            current_hits, current_domains, current_excluded = inspect_search(accession, args.output / 'evidence' / accession,
                                                                          attempt, source, wanted, profile_rows, identity)
            complete_path = attempt.parent / 'search_complete.json'
            if not complete_path.exists():
                record = read_json(attempt / 'command_receipt.json')
                record['file_sha256'] = {p.relative_to(attempt.parent).as_posix(): sha(p) for p in sorted(attempt.rglob('*')) if p.is_file()}
                save_json(complete_path, record)
            hits.extend(current_hits); domains.extend(current_domains); excluded_inputs.extend(current_excluded)
            completed.append(accession)
            save_json(args.output / 'execution_progress.json', {'execution': 'RUNNING', 'scientific_validation': 'NOT_RUN',
                      'completed_searches': len(completed), 'required_assemblies': 196, 'remaining': 196 - len(completed),
                      'pid': os.getpid(), 'last_assembly': accession})
            print(str(index) + '/196 ' + accession + ' ACTUAL_GTOTREE_SEARCH_INVENTORY_CHECKED hits=' + str(len(current_hits)), flush=True)
    except Exception as error:
        save_json(args.output / 'execution_failure.json', {'execution': 'FAILED', 'scientific_validation': 'NOT_PASS',
                  'completed_searches': len(completed), 'required_assemblies': 196, 'error': str(error),
                  'not_run_assemblies': accessions[len(completed):], 'outputs_preserved': True})
        raise
    require(completed == accessions, 'Full196 executed-search accounting differs')
    names = [p['profile'] for p in profile_rows]
    native_bounds = native_length_bounds(args, names, hits, environment)
    cells, marker_qc, genome_qc, retained, accepted, blockers = apply_filters(accessions, names, hits, config, native_bounds)
    rm_candidates = []
    for row in accepted:
        for title in row['source_primary_headers']:
            if re.search(r'restriction|DNA.*methyl|(?:adenine|cytosine).*DNA.*methyl|Hsd[MSR]', title, re.I):
                rm_candidates.append({'assembly_accession': row['assembly_accession'], 'profile': row['profile'],
                                      'locus_key': row['locus_key'], 'source_primary_header': title,
                                      'state': 'SOURCE_PRODUCT_POTENTIAL_RM_REVIEW_REQUIRED'})
    annotation_review = [p for p in profile_rows if 'REVIEW_REQUIRED' in p['annotation_review_state']]
    tsv(args.output / 'rm_marker_source_review_candidates.tsv', rm_candidates,
        ['assembly_accession', 'profile', 'locus_key', 'source_primary_header', 'state'])
    save_json(args.output / 'host_marker_annotation_review.json', {
        'status': 'REVIEW_REQUIRED_BEFORE_STAGE04_TOPOLOGY', 'profiles_audited': 119,
        'explicit_source_annotation_candidates': len(rm_candidates), 'ambiguous_profile_count': len(annotation_review),
        'ambiguous_profiles': annotation_review,
        'method': 'Preserve pinned NAME/ACC/DESC/GA and all hit source primary FAA headers; flag generic families and potential RM product annotations.',
        'limit': 'Filename alone is not functional evidence. RNA/tRNA methyltransferase descriptions are distinct from DNA restriction-modification methylases; broad methyltransferase/unknown profiles require independent source/family review. No profile or hit is silently removed.'})
    tsv(args.output / 'profiles.tsv', profile_rows, list(profile_rows[0]))
    tsv(args.output / 'hmm_hits.tsv', hits, [k for k in hits[0] if k != 'sequence'] if hits else
        ['assembly_accession', 'profile', 'target_id', 'locus_key', 'protein_accession'])
    tsv(args.output / 'hmm_domains.tsv', domains, list(domains[0]) if domains else ['assembly_accession', 'profile', 'locus_key'])
    tsv(args.output / 'input_guard_exclusions.tsv', excluded_inputs,
        ['assembly_accession', 'locus_key', 'protein_accession', 'protein_aa_length', 'source_sequence_sha256', 'reason'])
    tsv(args.output / 'copy_occupancy_matrix.tsv', cells, list(cells[0]))
    tsv(args.output / 'marker_qc.tsv', marker_qc, list(marker_qc[0]))
    tsv(args.output / 'genome_recovery.tsv', genome_qc, list(genome_qc[0]))
    tsv(args.output / 'scientific_blockers.tsv', blockers, ['scope', 'reason', 'observed', 'required'])
    write(args.output / 'primary_marker_order.txt', '\n'.join(retained) + ('\n' if retained else ''))
    accepted.sort(key=lambda row: (row['profile'], accessions.index(row['assembly_accession'])))
    tsv(args.output / 'accepted_sequence_manifest.tsv', accepted, [k for k in accepted[0] if k != 'sequence'] if accepted else
        ['assembly_accession', 'profile', 'locus_key', 'source_sequence_sha256'])
    for name in retained:
        marker = [row for row in accepted if row['profile'] == name]
        write(args.output / 'marker_sequences' / (name + '.faa'), ''.join('>' + r['assembly_accession'] + '\n' + r['sequence'] + '\n' for r in marker))
    for accession in accessions:
        proteins = [r for r in accepted if r['assembly_accession'] == accession]
        if proteins:
            write(args.output / 'accepted_by_genome' / (accession + '.faa'), ''.join('>' + r['locus_key'] + ' marker=' + r['profile'] + '\n' + r['sequence'] + '\n' for r in proteins))
    summary = {'execution': 'COMPLETED_ALL196_SEARCHES', 'inventory': 'SCIENTIFIC_BLOCKER' if blockers else 'MARKER_INVENTORY_CONSTRUCTED',
               'scientific_validation': 'NOT_RUN_INDEPENDENT_STAGE_CHECK_REQUIRED', 'approved_assemblies': 196,
               'successful_searches': 196, 'profiles_searched': 119, 'marker_cells': len(cells), 'primary_markers': len(retained),
               'accepted_marker_sequences': len(accepted), 'blocker_count': len(blockers), 'blockers': blockers,
               'fixed_genome_recovery_denominator': 119, 'fixed_marker_occupancy_denominator': 196,
               'post_occupancy_denominator': len(retained),
               'length_integer_rounding': 'Actual installed gtt-get-median.sh output then bc +/-0.2 median and bash printf %.0f; inclusive bounds. Raw numeric inputs/results and tool hashes retained.',
               'host_marker_annotation_review': 'REVIEW_REQUIRED_BEFORE_STAGE04_TOPOLOGY',
               'alignment_execution': 'NOT_RUN_RESERVED_STAGE04', 'identity': identity,
               'evidence_limit': 'Profile prediction/orthology inventory and source integrity; no phylogeny, ANI or functional evidence.'}
    save_json(args.output / 'inventory_summary.json', summary)
    save_json(args.output / 'execution_progress.json', {'execution': 'COMPLETED_ALL196_SEARCHES', 'inventory': summary['inventory'],
              'scientific_validation': summary['scientific_validation'], 'completed_searches': 196, 'remaining': 0, 'pid': os.getpid()})
    if blockers:
        raise RuntimeError('Scientific blocker: frozen host recovery/occupancy requirements fail; all approved genomes retained in evidence')


def self_test():
    accessions, names = ['A' + str(i) for i in range(196)], ['M' + str(i) for i in range(119)]
    config = {'marker_minimum_accepted_genomes': 177, 'genome_minimum_accepted_markers': 96,
              'post_occupancy_genome_recovery_minimum': 0.8}
    hits = [{'assembly_accession': a, 'profile': name, 'locus_key': a + '|' + name,
             'protein_aa_length': 100, 'sequence': 'M' * 100} for a in accessions for name in names]
    require(not apply_filters(accessions, names, hits, config)[-1], 'Complete synthetic matrix failed')
    short = [r for r in hits if not (r['assembly_accession'] == 'A0' and int(r['profile'][1:]) >= 95)]
    require(any(b['reason'] == 'RECOVERY_BELOW_FIXED119_MINIMUM' and b['observed'] == 95 for b in apply_filters(accessions, names, short, config)[-1]), '95/119 not blocked')
    multi = [*hits, {**hits[0], 'locus_key': 'A0|M0_copy2'}]
    cells = apply_filters(accessions, names, multi, config)[0]
    require(next(c for c in cells if c['assembly_accession'] == 'A0' and c['profile'] == 'M0')['state'] == 'MULTICOPY_MISSING', 'Multicopy arbitrarily selected')
    low_occupancy = [r for r in hits if not (r['profile'] == 'M0' and int(r['assembly_accession'][1:]) >= 176)]
    require('M0' not in apply_filters(accessions, names, low_occupancy, config)[3], '176/196 marker accepted')
    post_short = [r for r in hits if not
                  ((int(r['profile'][1:]) >= 100 and int(r['assembly_accession'][1:]) >= 176)
                   or (r['assembly_accession'] == 'A0' and int(r['profile'][1:]) < 21))]
    post_result = apply_filters(accessions, names, post_short, config)
    require(next(g for g in post_result[2] if g['assembly_accession'] == 'A0')['length_accepted_markers'] == 98
            and any(b['scope'] == 'A0' and b['reason'] == 'RECOVERY_BELOW_POST_OCCUPANCY_MINIMUM'
                    and b['observed'] == 79 and b['required'] == 80 for b in post_result[-1]),
            'Post-occupancy retained-marker denominator shortfall not blocked')
    length_bad = [{**r, 'protein_aa_length': 150} if r is hits[0] else r for r in hits]
    cells = apply_filters(accessions, names, length_bad, config)[0]
    require(next(c for c in cells if c['assembly_accession'] == 'A0' and c['profile'] == 'M0')['state'] == 'LENGTH_EXCLUDED', 'Length outlier not retained as exclusion')
    try:
        fasta(b'>same\nMK\n>same\nMK\n')
    except ValueError:
        pass
    else:
        raise AssertionError('Duplicate target IDs accepted')
    print(json.dumps({'status': 'PASS_SYNTHETIC_MARKER_FILTER_FIXTURES', 'biological_execution': 'NOT_RUN',
                      'fixtures': ['complete_fixed196_fixed119', 'fixed119_count_shortfall', 'multicopy_missing',
                                   'fixed196_occupancy_shortfall', 'retained_marker_recovery_shortfall',
                                   'length_exclusion', 'duplicate_target_rejected']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--config', type=Path, default=Path('config/host_primary_stage03_v1.json'))
    parser.add_argument('--inputs', type=Path, default=Path('.work/source_locus_inputs_v1'))
    parser.add_argument('--validation', type=Path, default=Path('.work/stage02_validated'))
    parser.add_argument('--locus-validation', type=Path, default=Path('.work/stage03_source_validation/validation_summary.json'))
    parser.add_argument('--output', type=Path, default=Path('.work/stage03_markers_v1'))
    parser.add_argument('--host-env', type=Path, default=Path('.tools/linux/host_env'))
    parser.add_argument('--profile', type=Path, default=Path('.tools/Firmicutes.hmm'))
    parser.add_argument('--wrapper', type=Path, default=Path('scripts/gtotree_evidence.py'))
    args = parser.parse_args()
    self_test() if args.self_test else production(args)
