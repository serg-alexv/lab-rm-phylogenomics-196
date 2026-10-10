#!/usr/bin/env python3
"""Read-only scientific checks; write new validation receipts, never repair results."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from master_run import validate_five_marker_pilot_v2 as core


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--mode', choices=('pilot', 'full'), required=True)
    parser.add_argument('--report-dir', type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    report_dir = args.report_dir or project / 'reports/stage01'
    names = ('validation_summary.tsv', 'validation_report.json',
             'species_tree.itol_quartet_frequency.newick')
    if any((report_dir / name).exists() for name in names):
        print('GLOBAL_PIPELINE_STATUS: FAIL\nRefusing to overwrite validation evidence; choose a fresh --report-dir.', file=sys.stderr)
        return 1
    rows, hashes, details = [], {}, {}

    def read(path):
        raw = path.read_bytes()
        hashes[str(path.relative_to(project))] = hashlib.sha256(raw).hexdigest()
        return raw

    def check(name, action):
        try:
            result = action()
            rows.append((name, 'PASS', 'verified'))
            return result
        except (OSError, ValueError, KeyError, TypeError) as error:
            rows.append((name, 'FAIL', str(error)))
            return None

    try:
        approved_order, approved_path = core.load_approved(project)
        approved = set(approved_order)
        read(approved_path)
        module = core.load_project_newick(project)
        inputs = sorted((project / 'input_genes').glob('*.fasta'))
        expected_count = 5 if args.mode == 'pilot' else 100
        selected = inputs[:5] if args.mode == 'pilot' else inputs
        core.require(len(selected) == expected_count,
                     f'{args.mode} needs {expected_count} marker FASTAs; found {len(selected)}')
        root = project / ('pilot_output' if args.mode == 'pilot' else 'pipeline_output')
        union, trees = set(), []
        marker_details = []
        for fasta in selected:
            def validate_marker(fasta=fasta):
                marker = fasta.stem
                read(fasta)
                original = core.parse_fasta(fasta)
                core.require(set(original) <= approved, f'{marker}: unapproved input accessions')
                alignment = root / 'alignments' / (marker + '_aligned.fasta')
                read(alignment)
                aligned = core.parse_fasta(alignment)
                core.require(set(aligned) == set(original), f'{marker}: alignment taxa differ from FASTA')
                core.require(len({len(v) for v in aligned.values()}) == 1,
                             f'{marker}: unequal alignment row lengths')
                for accession, sequence in original.items():
                    core.require('-' not in sequence and '.' not in sequence,
                                 f'{marker}/{accession}: input sequence already has gaps')
                    core.require(core.normalized_ungapped(aligned[accession]) == sequence.upper(),
                                 f'{marker}/{accession}: ungapped alignment changed sequence')
                tree_path = root / 'trees' / (marker + '.treefile')
                raw = read(tree_path)
                tree, _, _ = core.load_parser_tree(module, tree_path)
                walked, tips = core.tree_walk(tree)
                core.require(sum(not n.children for n, _, _ in walked) == len(tips),
                             f'{marker}: duplicate gene-tree tips')
                core.require(tips == set(original), f'{marker}: gene-tree taxa differ from FASTA')
                core.check_tree_lengths(tree, tree_path, require_all_edges=True)
                support = core.validate_iqtree_support(tree, tree_path)
                native = read(root / 'trees' / (marker + '.log')).decode('utf-8-sig')
                iqreport = read(root / 'trees' / (marker + '.iqtree')).decode('utf-8-sig')
                core.require(core.IQTREE_COMPLETION_RE.search(native) is not None,
                             f'{marker}: native IQ-TREE completion absent')
                core.require(re.search(r'(?m)^Date and Time:', native) is not None,
                             f'{marker}: native completion timestamp absent')
                core.require(re.search(r'Generating\s+1000\s+samples\s+for\s+ultrafast\s+bootstrap', native, re.I) is not None,
                             f'{marker}: native log evidence of 1000 bootstrap samples absent')
                core.require(re.search(r'ultrafast\s+bootstrap\s*\(1000\s+replicates\)', iqreport, re.I) is not None,
                             f'{marker}: report evidence of 1000 bootstrap replicates absent')
                union.update(original)
                trees.append(raw)
                marker_details.append({'marker': marker, 'tips': len(tips),
                                       'alignment_columns': len(next(iter(aligned.values()))), 'support': support})
            check('marker:' + fasta.stem, validate_marker)
        details['markers'] = marker_details
        details['approved_taxa'] = len(approved)
        details['expected_astral_taxa_from_validated_marker_union'] = len(union)
        if any(status == 'FAIL' for _, status, _ in rows):
            raise ValueError('Marker validation incomplete; ASTRAL acceptance withheld')
        if args.mode == 'full':
            core.require(union == approved, 'Full marker union must equal all 196 approved taxa')
        core.require(union, 'Empty marker taxon union')
        core.require(read(root / 'all_gene_trees.tre') == b''.join(trees),
                     'Concatenated trees differ from the selected validated gene-tree files')
        astral_path = root / 'species_tree.newick' if args.mode == 'pilot' else project / 'species_tree.newick'
        read(astral_path)
        astral = core.validate_astral_tree(module, astral_path, union)
        astral_log = project / 'reports/stage01' / ('pilot_astral.log' if args.mode == 'pilot' else 'astral_run.log')
        log = read(astral_log).decode('utf-8-sig')
        core.require('ASTRAL version 5.7.8' in log, 'ASTRAL native version evidence missing')
        core.require(re.search(r'(?im)^\s*(?:Error:|Exception in thread)', log) is None,
                     'ASTRAL native error present')
        for name, expected_hash in hashes.items():
            core.require(hashlib.sha256((project / name).read_bytes()).hexdigest() == expected_hash,
                         f'Evidence changed during validation: {name}')
        details['evidence_unchanged_during_validation'] = True
        details['astral'] = astral['summary']
        rows.append(('ASTRAL', 'PASS', f'exactly {len(union)} unique taxa from selected marker union'))
    except (OSError, ValueError, KeyError, TypeError, ImportError) as error:
        rows.append(('pipeline', 'FAIL', str(error)))
    passed = bool(rows) and all(status == 'PASS' for _, status, _ in rows)
    report_dir.mkdir(parents=True, exist_ok=True)
    with (report_dir / names[0]).open('x', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle, delimiter='\t', lineterminator='\n')
        writer.writerow(('check', 'status', 'details'))
        writer.writerows(rows)
    with (report_dir / names[1]).open('x', encoding='utf-8') as handle:
        json.dump({'status': 'PASS' if passed else 'FAIL', 'mode': args.mode,
                   'checks': rows, 'results': details, 'input_sha256': hashes,
                   'artifact_sha256': ({names[2]: hashlib.sha256(astral['derived_text'].encode('utf-8')).hexdigest()} if passed else {}),
                   'scope': 'Data integrity and workflow validation; biological reliability requires scientific review.'},
                  handle, indent=2)
        handle.write('\n')
    if passed:
        with (report_dir / names[2]).open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(astral['derived_text'])
    print('GLOBAL_PIPELINE_STATUS: ' + ('PASS' if passed else 'FAIL'))
    for name, status, message in rows:
        if status == 'FAIL':
            print('\t'.join((name, status, message)))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
