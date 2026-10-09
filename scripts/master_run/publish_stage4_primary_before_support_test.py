"""Publish an already accepted Stage4 primary payload and verify readback.

No inference or acceptance is performed here. Reuses the retained project
publication implementation under the original identity-checked writer lock.
"""
from pathlib import Path, PurePosixPath
import argparse
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
import atomic_iqtree_windows as A

ROOT = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
REPO = 'serg-alexv/lab-rm-phylogenomics-196'
CHAT = Path(__file__).resolve().parents[1]


def atomic_bytes(path, payload):
    """Preserve exact UTF-8 text bytes; A.atomic remains the JSON-only writer."""
    path = Path(path)
    A.require(isinstance(payload, bytes) and ROOT.resolve() in path.resolve().parents,
              'Byte publication must stay inside the canonical repository')
    fd, temporary = tempfile.mkstemp(prefix='.'+path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def command(argv):
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=90, check=True)
    return result.stdout.decode('utf-8-sig').strip()


def verify_prepared_science(report, staging, manifest, validation):
    A.require(validation.get('schema') == 'STAGE04_PRIMARY_ACCEPTANCE_V1'
        and validation.get('state') == validation.get('scientific_state') == 'COMPLETE_VALIDATED'
        and validation.get('approved_accessions_sha256') == A.EXPECTED_PANEL
        and validation.get('unique_tips') == 196 and validation.get('branch_lengths_valid') is True
        and validation.get('support_completed') is True
        and validation.get('mode') in ('partitioned','single_model'),
        'Actual primary196 acceptance schema/panel/tree/support required')
    freeze = Path(validation['frozen_output_directory']).resolve()
    A.require(ROOT.resolve() in freeze.parents
        and A.sha256(freeze/'independent_validation.json') == A.sha256(report/'independent_validation.json'),
        'Compact certificate differs from authoritative accepted freeze')
    members = validation.get('files')
    A.require(isinstance(members,dict) and members, 'Accepted scientific member pins missing')
    pins = {}
    for name, digest in members.items():
        pure = PurePosixPath(name)
        path = ROOT.joinpath(*pure.parts)
        A.require(not pure.is_absolute() and pure.as_posix() == name and '..' not in pure.parts
            and '\\' not in name and ':' not in name and not path.is_symlink()
            and path.resolve().parent == freeze and A.sha256(path) == digest,
            'Authoritative accepted scientific member changed: '+name)
        pins['accepted/'+path.name] = digest
    required = {'primary196_host_tree.nwk','primary196_host_tree.nex',
                'accepted_primary196_concatenated.faa','accepted_original_config.json',
                'accepted_approved_accessions.txt'}
    A.require(required <= {PurePosixPath(name).name for name in members},
              'Accepted certificate lacks required primary artifacts')
    pins['accepted/independent_validation.json'] = A.sha256(report/'independent_validation.json')
    distribution_name = 'input_output_sha256_manifest.tsv'
    distribution_bytes = (freeze/distribution_name).read_bytes()
    distribution_sha = hashlib.sha256(distribution_bytes).hexdigest()
    A.require(distribution_sha == A.sha256(report/distribution_name),
              'Compact distribution manifest differs from authoritative accepted freeze')
    lines = distribution_bytes.decode('utf-8-sig').splitlines()
    A.require(lines and lines[0] == 'path\tsha256\tbytes', 'Accepted distribution manifest schema differs')
    distribution = {}
    for line in lines[1:]:
        fields = line.split('\t')
        A.require(len(fields) == 3, 'Accepted distribution manifest row malformed')
        name, digest, size = fields
        pure = PurePosixPath(name)
        A.require(name not in distribution and len(pure.parts) == 1 and pure.as_posix() == name
            and '\\' not in name and ':' not in name and name not in ('.','..')
            and re.fullmatch('[a-f0-9]{64}',digest) is not None
            and re.fullmatch('[0-9]+',size) is not None,
            'Accepted distribution manifest member invalid or duplicated')
        distribution[name] = (digest,int(size))
    expected_names = {PurePosixPath(name).name for name in pins}
    A.require(set(distribution) == expected_names
        and {p.name for p in freeze.iterdir() if p.is_file()} == expected_names | {distribution_name},
        'Accepted distribution manifest does not exhaustively cover certificate-bound payload')
    for name, (digest,size) in distribution.items():
        path = freeze/name
        A.require(not path.is_symlink() and path.resolve().parent == freeze
            and digest == pins['accepted/'+name] and path.stat().st_size == size,
            'Accepted distribution manifest hash/size differs from certificate-bound payload: '+name)
    pins['accepted/'+distribution_name] = distribution_sha
    assets = manifest.get('assets')
    A.require(isinstance(assets,list) and len(assets) == 1
        and assets[0].get('asset_name') == 'stage04-primary196-accepted.zip',
        'Exact prepared Stage4 portable ZIP required')
    asset = assets[0]
    archive = staging/asset['asset_name']
    A.require(A.sha256(archive) == asset['sha256'] and archive.stat().st_size == asset['bytes'],
              'Prepared ZIP bytes/hash changed')
    with zipfile.ZipFile(archive) as zipped:
        A.require(len(zipped.namelist()) == len(set(zipped.namelist())), 'Duplicate ZIP member')
        A.require({name for name in zipped.namelist() if name.startswith('accepted/')} == set(pins),
                  'ZIP accepted member set differs from the authoritative scientific freeze')
        for name, digest in pins.items():
            with zipped.open(name) as stream:
                A.require(hashlib.file_digest(stream,'sha256').hexdigest() == digest,
                          'ZIP scientific member differs from accepted certificate: '+name)


def update_status(validation, receipt, report):
    path = ROOT/'status/stages.tsv'
    rows = list(csv.DictReader(io.StringIO(path.read_text()), delimiter='\t'))
    matches = [row for row in rows if row['stage'] == '4_phylogeny']
    A.require(len(matches) == 1, 'Exactly one canonical Stage4 status row required')
    matches[0].update(execution='COMPLETED', validation='PASS_PRIMARY196_HOST_TREE',
                      publication='UPLOAD_VERIFIED', observation_as_of_utc=A.utc(),
                      native_pid='', native_creation_filetime='')
    content = io.StringIO()
    writer = csv.DictWriter(content, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    atomic_bytes(path, content.getvalue().encode('utf-8'))
    A.atomic(ROOT/'status/stage04_execution.json', {
        'utc':A.utc(), 'state':'COMPLETE_VALIDATED', 'scientific_status':'ACCEPTED_PRIMARY196_HOST_TREE',
        'active_inference_found':False, 'actual_native_exit':0,
        'accepted_output_directory':validation['frozen_output_directory'],
        'validation_report':str((Path(validation['frozen_output_directory'])/'independent_validation.json').relative_to(ROOT).as_posix()),
        'compact_validation_copy':str((report/'independent_validation.json').relative_to(ROOT).as_posix()),
        'publication_receipt':str((report/'publication_receipt.json').relative_to(ROOT).as_posix()),
        'native_tree_sha256':validation['native_tree_sha256'],
        'previous_V10_outcome':'UNKNOWN_PRESERVED',
        'historical_evidence':'reports/stage04/atomic_resume_20261009/previous_stage04_execution.json',
        'optional_sensitivities':'SEPARATE_NOT_COMPLETION_GATES'})
    text = ('# Current execution status\n\nUpdated '+A.utc()+'.\n\n'
        'The full approved196 primary host phylogeny is independently accepted and its portable '
        'release has been downloaded and hash-verified. Accepted Stage4a inputs were preserved. '
        'Stage5 R-M detection/curation and Stage6 figure remain pending.\n\n'
        'Direct user continuation remains active; automatic resume is disabled. Historical failed '
        'attempts and unknown exits are preserved; see reports/stage04/atomic_resume_20261009/.\n\n'
        'Accepted host tree: '+report.relative_to(ROOT).as_posix()+'/REPORT.md.\n'
        'Release: '+receipt['url']+'.\n\n'
        'All196 taxa remain; 8 exact-alignment groups contain22 taxa. These host markers cannot '
        'resolve member ordering within each group. Native composition/model warnings are retained.\n\n'
        '| Stage | Execution | Validation | Publication |\n|---|---|---|---|\n')
    text += ''.join('| '+' | '.join(row[key] for key in ['stage','execution','validation','publication'])+' |\n' for row in rows)
    atomic_bytes(ROOT/'STATUS.md',text.encode('utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-name', required=True)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--tag', default='stage04-primary196-atomic-v1')
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    A.require(args.report_name.replace('_','').isalnum(), 'Simple new report namespace required')
    report = ROOT/'reports/stage04'/args.report_name
    staging = ROOT/'release_staging'/args.report_name
    manifest_path = report/'portable_payload_manifest.json'
    if not args.run:
        print(json.dumps({'state':'PREPARED_NOT_RUN','report':str(report),'tag':args.tag}))
        return
    A.require(not A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json').exists(),
              'Durable local closure stop exists; reconcile before publication')
    with A.WorkflowLock(A.Win()) as lock:
        A.require(command(['git','rev-parse','HEAD']) == args.expected_head
            == command(['gh','api','repos/'+REPO+'/commits/main','--jq','.sha']),
            'Reconcile canonical local/remote HEAD before publication')
        A.require(not command(['git','diff','--cached','--name-only']), 'Pre-existing staged work must be preserved')
        manifest = A.read_json(manifest_path)
        validation = A.read_json(report/'independent_validation.json')
        A.require(validation.get('state') == 'COMPLETE_VALIDATED'
            and manifest.get('scientific_state') == 'COMPLETE_VALIDATED'
            and manifest.get('final_validation_summary_sha256') == A.sha256(report/'independent_validation.json'),
            'Actual independent accepted primary certificate/payload binding required')
        verify_prepared_science(report,staging,manifest,validation)
        notes = CHAT/'work/stage04_release_notes.md'
        method = ('Partition-aware' if validation['mode'] == 'partitioned' else 'Single-model concatenated')
        notes.write_text('Accepted primary196 host phylogeny from the validated100-marker,17456-aa '
            'Stage4a matrix. '+method+' IQ-TREE3.1.4, MFP,1000UFBoot and1000SH-aLRT, '
            'seed1961008, all196 taxa retained, explicitly unrooted.\n\n'
            'Portable ZIP includes authoritative Newick/NEXUS, all native outputs, support trees, '
            'input/cache bytes, command/exit/closure receipts, independent validation, checksums '
            'and sequence-identity limitations. R-M analysis and final figure are later stages.\n',
            encoding='utf-8',newline='\n')
        sys.path.insert(0,str(ROOT/'scripts'))
        import portable_release
        import workflow_publication
        # Keep this publication's command log out of the accepted Stage0 record.
        portable_release.w.LOG = CHAT/'work/stage04_publish_commands.jsonl'
        code = ['scripts/'+name for name in [
            'atomic_iqtree_windows.py','test_atomic_iqtree_windows.py','smoke_atomic_iqtree_windows.py',
            'independent_tree_check.py','test_independent_tree_check.py',
            'test_stage4_freeze_copy_integration.py','prepare_stage4_publication.py',
            'publish_stage4_primary.py','test_stage4_publish_science.py','test_stage4_publication_text.py']]
        payload_paths = [report.relative_to(ROOT).as_posix(), *code]
        receipt = portable_release.publish_frozen('stage04/'+args.report_name,args.tag,staging,
            manifest_path,payload_paths,'Stage4: accepted primary196 host phylogeny',notes)
        receipt.update(final_validation_summary_sha256=manifest['final_validation_summary_sha256'],
                       scientific_state='COMPLETE_VALIDATED', workflow_lock=lock.identity)
        A.atomic(report/'publication_receipt.json',receipt)
        report_path = report/'REPORT.md'
        report_text = report_path.read_text(encoding='utf-8').replace(
            'Scientific validation: COMPLETE_VALIDATED. Publication: prepared; upload/readback pending.',
            'Scientific validation: COMPLETE_VALIDATED. Publication: UPLOAD_VERIFIED; '
            'see publication_receipt.json for downloaded ZIP/member hash verification.')
        report_text += '\nVerified release: '+receipt['url']+'\n'
        atomic_bytes(report_path,report_text.encode('utf-8'))
        update_status(validation,receipt,report)
        final_head = workflow_publication.commit([
            report.relative_to(ROOT).as_posix(),'STATUS.md','status/stages.tsv',
            'status/stage04_execution.json'], 'Verify accepted primary196 host tree release and record completion')
        A.require(command(['gh','api','repos/'+REPO+'/commits/main','--jq','.sha']) == final_head,
                  'Final current remote main readback differs')
        A.atomic(CHAT/'work/stage04_publication_final.json', {
            'utc':A.utc(),'state':'UPLOAD_VERIFIED','current_main':final_head,
            'receipt_path':str(report/'publication_receipt.json'),
            'receipt_sha256':A.sha256(report/'publication_receipt.json'),'release':receipt['url']})
        print(json.dumps({'state':'UPLOAD_VERIFIED','current_main':final_head,'release':receipt['url']}))


if __name__ == '__main__':
    main()
