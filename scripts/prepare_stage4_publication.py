"""Prepare portable Stage4 payload only after independent primary acceptance.

No inference, release upload, or Git mutation. The stable writer lock is required.
Use retained portable_release ZIP/member verification rather than a new archive format.
"""
from pathlib import Path, PurePosixPath
import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
import zipfile
import atomic_iqtree_windows as A

ROOT = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
HISTORY = Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
CHAT = Path(__file__).resolve().parents[1]


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--accepted', type=Path, required=True)
    parser.add_argument('--validation', type=Path, required=True)
    parser.add_argument('--report-name', required=True)
    args = parser.parse_args()
    accepted, validation_path = args.accepted.resolve(), args.validation.resolve()
    if ROOT.resolve() not in accepted.parents or validation_path.parent != accepted:
        raise ValueError('Use the newly accepted canonical project freeze and its independent report')
    if not args.report_name.replace('_', '').isalnum():
        raise ValueError('Use a simple new report namespace')
    with A.WorkflowLock(A.Win()) as lock:
        validation = json.loads(validation_path.read_text(encoding='utf-8-sig'))
        if (validation.get('schema') != 'STAGE04_PRIMARY_ACCEPTANCE_V1'
                or validation.get('state') != 'COMPLETE_VALIDATED'
                or validation.get('unique_tips') != 196
                or validation.get('branch_lengths_valid') is not True
                or validation.get('support_completed') is not True):
            raise ValueError('Actual independent primary196 acceptance required')
        # Every frozen member must agree with the post-validation relative manifest.
        manifest_bytes = (accepted / 'input_output_sha256_manifest.tsv').read_bytes()
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        rows = manifest_bytes.decode('utf-8-sig').splitlines()
        if not rows or rows[0] != 'path\tsha256\tbytes':
            raise ValueError('Unexpected frozen manifest schema')
        expected = {}
        for row in rows[1:]:
            name, digest, size = row.split('\t')
            path = accepted / name
            if (name in expected or len(PurePosixPath(name).parts) != 1
                    or '\\' in name or ':' in name or not re.fullmatch('[a-f0-9]{64}', digest)
                    or path.resolve().parent != accepted or path.is_symlink()):
                raise ValueError('Unsafe frozen member')
            if sha(path) != digest or path.stat().st_size != int(size):
                raise ValueError('Frozen payload drift: ' + name)
            expected[name] = digest
        actual = {p.name for p in accepted.iterdir() if p.is_file()}
        if actual != set(expected) | {'input_output_sha256_manifest.tsv'}:
            raise ValueError('Frozen relative manifest does not exhaustively cover payload')
        if validation_path.name not in expected:
            raise ValueError('Post-validation manifest must include independent report')
        members = validation.get('files')
        if not isinstance(members, dict) or not members:
            raise ValueError('Independent scientific file pins are required')
        for name, digest in members.items():
            pure = PurePosixPath(name)
            path = ROOT.joinpath(*pure.parts)
            if (pure.is_absolute() or pure.as_posix() != name or '..' in pure.parts
                    or '\\' in name or ':' in name or path.resolve().parent != accepted
                    or path.is_symlink() or not re.fullmatch('[a-f0-9]{64}', digest)
                    or sha(path) != digest):
                raise ValueError('Independent certificate scientific file drift: ' + name)
        required = {'primary196_host_tree.nwk', 'primary196_host_tree.nex',
                    'accepted_primary196_concatenated.faa', 'accepted_original_config.json',
                    'accepted_approved_accessions.txt'}
        if not required <= {PurePosixPath(name).name for name in members}:
            raise ValueError('Independent certificate lacks required accepted scientific members')
        report = ROOT / 'reports/stage04' / args.report_name
        staging = ROOT / 'release_staging' / args.report_name
        if report.exists() or staging.exists():
            raise ValueError('Publication preparation requires new namespaces; preserve any prior payload')
        compact = ['primary196_host_tree.nwk', 'primary196_host_tree.nex', 'host.iqtree',
                   'config.json', 'launch.json', 'exit.json', 'result.json', 'lock_released.json',
                   'input_output_sha256_manifest.tsv', validation_path.name]
        for name in compact:
            source = accepted / name
            if not source.is_file():
                raise ValueError('Required compact accepted artifact missing: ' + name)
        code = ['atomic_iqtree_windows.py', 'test_atomic_iqtree_windows.py',
                'smoke_atomic_iqtree_windows.py', 'independent_tree_check.py',
                'test_independent_tree_check.py', 'test_stage4_freeze_copy_integration.py',
                'prepare_stage4_publication.py', 'publish_stage4_primary.py',
                'test_stage4_publish_science.py', 'test_stage4_publication_text.py', 'test_stage4_support_execution.py']
        if sha(CHAT/'work/independent_tree_check.py') != validation.get('checker_sha256'):
            raise ValueError('Packaged checker differs from actual independent acceptance code')
        launch = json.loads((accepted/'launch.json').read_text(encoding='utf-8-sig'))
        if sha(CHAT/'work/atomic_iqtree_windows.py') != launch.get('runner_sha256'):
            raise ValueError('Packaged native producer differs from actual executed source')
        for name in code:
            source = CHAT / 'work' / name
            destination = ROOT / 'scripts' / name
            if not source.is_file() or source.is_symlink():
                raise ValueError('Missing or unexpected publication code source: ' + name)
            if destination.exists() and sha(destination) != sha(source):
                raise ValueError('Preserve existing different script: ' + name)
        duplicate_source = CHAT / 'work/independent_inputs/exact_alignment_duplicates.json'
        duplicate_checker = CHAT / 'work/independent_inputs/exact_alignment_duplicates.py'
        duplicates = json.loads(duplicate_source.read_text(encoding='utf-8-sig'))
        if (duplicates.get('status') != 'PASS_EXACT_ACCEPTED_ALIGNMENT_DUPLICATE_QA'
                or duplicates.get('alignment_sha256') != sha(accepted/'accepted_primary196_concatenated.faa')
                or duplicates.get('checker_sha256') != sha(duplicate_checker)
                or duplicates.get('taxa') != 196 or duplicates.get('columns') != 17456):
            raise ValueError('Exact accepted-alignment sequence-identity QA differs')
        qa_sources = [(duplicate_source, 'exact_alignment_duplicates.json'),
                      (duplicate_checker, 'exact_alignment_duplicates.py'),
                      (CHAT/'work/iqtree_identical_support_source_review.md', 'identical_sequence_support_review.md'),
                      (CHAT/'work/iqtree_3_1_4_source_review/source_pin.json', 'iqtree_support_source_pin.json')]
        for source, _ in qa_sources:
            if not source.is_file() or source.is_symlink():
                raise ValueError('Missing sequence-identity QA source: ' + str(source))
        report.mkdir(parents=True)
        staging.mkdir(parents=True)
        for name in compact:
            shutil.copyfile(accepted / name, report / name)
            frozen_hash = (manifest_sha256 if name == 'input_output_sha256_manifest.tsv'
                           else expected[name])
            if sha(report/name) != frozen_hash:
                raise ValueError('Compact report copy differs from accepted bytes: ' + name)
        for source, name in qa_sources:
            shutil.copyfile(source, report/name)
        for name in code:
            source = CHAT / 'work' / name
            destination = ROOT / 'scripts' / name
            if not destination.exists():
                shutil.copyfile(source, destination)
        approved = accepted / 'accepted_approved_accessions.txt'
        files = [(p, 'accepted/' + p.name) for p in sorted(accepted.iterdir()) if p.is_file()]
        files += [(ROOT / 'scripts' / name, 'scripts/' + name) for name in code]
        files += [(approved, 'inputs/approved_accessions.txt')]
        files += [(report/name, 'alignment_qa/'+name) for _, name in qa_sources]
        payload_pins = {name:sha(path) for path, name in files}
        if payload_pins['accepted/input_output_sha256_manifest.tsv'] != manifest_sha256:
            raise ValueError('Parsed accepted manifest bytes changed before ZIP construction')
        for name, digest in expected.items():
            if payload_pins['accepted/'+name] != digest:
                raise ValueError('Accepted payload drift before ZIP construction: ' + name)
        mode = validation['mode']
        guide = ('Stage4 primary196 accepted host phylogeny.\n\n'
                 'Exact approved196 taxa; accepted100-marker17456-aa Stage4a alignment.\n'
                 'IQ-TREE3.1.4; analysis mode ' + mode + '; ModelFinder MFP;\n'
                 '1000 ultrafast bootstrap trees;1000 SH-aLRT replicates;\n'
                 'seed1961008;two threads;keep-ident;explicit unrooted tree.\n'
                 'The final selected model(s), fit statistics and warnings are in accepted/host.iqtree.\n'
                 'Native logs, exact command, source input hashes, actual native exit and\n'
                 'independent acceptance report are retained in accepted/.\n'
                 'The original partial model cache, when used, is a byte-preserved input;\n'
                 'it does not constitute a previously accepted complete tree.\n'
                 'All bootstrap trees and native support outputs are included.\n'
                 'Newick is authoritative; NEXUS preserves topology/length/support and unrooted state.\n'
                 'Composition/model warnings are retained; computational inference does not establish function.\n'
                 'Optional sensitivity analyses are separate and have not been used as completion gates.\n'
                 'R-M screening, curation, joining and final graphics belong to later stages.\n')
        guide += ('\nThe accepted alignment contains ' + str(duplicates['unique_full_aligned_sequences'])
                  + ' distinct full aligned strings among all196 retained taxa. '
                  + str(duplicates['duplicate_group_count']) + ' exact-identity groups contain '
                  + str(duplicates['taxa_in_duplicate_groups']) + ' taxa.\n'
                  'Within each exact-identity group, these host-marker data cannot resolve member ordering.\n'
                  'Displayed bifurcations or computed support do not supply distinguishing characters.\n'
                  'All196 genomes remain in the tree and subsequent genome-level R-M analysis.\n'
                  'The exact groups, checker, source review and source pins are in alignment_qa/.\n')
        portable = ['iqtree3', '-s', 'accepted/accepted_primary196_concatenated.faa', '--seqtype', 'AA']
        if mode == 'partitioned':
            portable += ['-p', 'accepted/accepted_primary196_partitions.nex']
        portable += ['-m', 'MFP', '-B', '1000', '--alrt', '1000', '--seed', '1961008',
                     '-T', '2', '-keep-ident', '--boot-trees', '--prefix', 'rerun/host']
        if mode == 'single_model':
            portable += ['--mem', '2G', '--thread-site']
        guide += ('\nPortable command, relative to the extracted ZIP root:\n'
                  'Create the new rerun directory and use the recorded IQ-TREE3.1.4 executable.\n'
                  + ' '.join(portable) + '\n')
        if mode == 'partitioned':
            guide += ('To reproduce the recorded cache recovery, copy accepted/original_input_model_cache.gz\n'
                      'unchanged to rerun/host.model.gz before launch; confirm its recorded SHA-256.\n')
        sys.path.insert(0, str(ROOT / 'scripts'))
        import portable_release
        archive = staging / 'stage04-primary196-accepted.zip'
        asset = portable_release.make_zip(archive, files, guide)
        # Archive self-consistency does not establish equivalence to the
        # accepted snapshot: compare the bytes actually emitted to its pins.
        with zipfile.ZipFile(archive) as zipped:
            if set(zipped.namelist()) != set(payload_pins) | {'README.txt', 'SHA256SUMS.txt'}:
                raise ValueError('Emitted ZIP payload membership differs')
            for name, digest in payload_pins.items():
                with zipped.open(name) as stream:
                    if hashlib.file_digest(stream, 'sha256').hexdigest() != digest:
                        raise ValueError('Emitted ZIP differs from accepted/source pins: ' + name)
        summary = {'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                   'stage': 'stage04_primary196', 'scientific_state': 'COMPLETE_VALIDATED',
                   'publication_state': 'PREPARED_NOT_UPLOADED',
                   'accepted_directory': str(accepted),
                   'final_validation_summary_sha256': expected[validation_path.name],
                   'workflow_lock': lock.identity,
                   'emitted_zip_source_pins_verified': True,
                   'assets': [asset]}
        save(report / 'portable_payload_manifest.json', summary)
        (report / 'REPORT.md').write_text('# Stage4 primary196 host phylogeny\n\n' + guide
            + '\nScientific validation: COMPLETE_VALIDATED. Publication: prepared; upload/readback pending.\n',
            encoding='utf-8', newline='\n')
        save(CHAT / 'work/stage04_publication_preparation.json', {
            **summary, 'report_directory': str(report), 'staging_directory': str(staging),
            'payload_manifest_sha256': sha(report / 'portable_payload_manifest.json')})
        print(json.dumps({'state': 'PORTABLE_PAYLOAD_PREPARED_NOT_UPLOADED',
                          'report': str(report), 'archive': str(archive), **asset}))


if __name__ == '__main__':
    main()
