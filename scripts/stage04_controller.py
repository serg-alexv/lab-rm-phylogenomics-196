#!/usr/bin/env python3
"""One WD Windows owner, four measured/validated Stage4 phases, verified progress.

Draft for root adoption. No biological job is run by --self-test. The controller
waits for actual exits and independent gates; it never kills or duplicates jobs.
Stage4 release packaging/readback is a separate mandatory root-owned next step.
"""
from __future__ import annotations
import argparse
import ast
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import socket
import subprocess
import sys
import tempfile
import time
import uuid

LIMIT = 2147483648
PHASES = ('align', 'validate_alignment', 'trees', 'validate_final')
PUBLIC = ('STATUS.md', 'status/stages.tsv', 'status/stage04_execution.json',
          'reports/stage04/progress.json', 'reports/stage04/resource_preflight.json')
SECRET = re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?i:authorization\s*[:=]\s*["\x27]?bearer\s+[A-Za-z0-9._-]{20,})')


def check(ok, message):
    if not ok:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            result.update(block)
    return result.hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False) + '\n'
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '.', suffix='.tmp', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        for attempt in range(8):
            try:
                os.replace(temporary, path)
                return
            except OSError:
                if attempt == 7:
                    raise
                time.sleep(min(.025 * 2 ** attempt, 1))
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


class WorkflowLock:
    """Use an OS byte lock, preserving the parent's separate session lock."""
    def __init__(self, path):
        self.path, self.stream = Path(path), None

    def __enter__(self):
        import msvcrt
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = self.path.open('a+b')
        self.stream.seek(0)
        try:
            msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            self.stream.close()
            self.stream = None
            raise ValueError('Actual workflow byte lock is held; no competing launch permitted')
        return self

    def __exit__(self, *unused):
        import msvcrt
        self.stream.seek(0)
        msvcrt.locking(self.stream.fileno(), msvcrt.LK_UNLCK, 1)
        self.stream.close()


def command(root, argv, timeout=180):
    """Never put credential-helper output into public logs or exceptions."""
    result = subprocess.run(argv, cwd=root, capture_output=True, timeout=timeout)
    check(result.returncode == 0, 'Command failed exit=' + str(result.returncode) + ': ' + str(argv[0]) + ' ' + str(argv[1:3]))
    output = result.stdout.decode('utf-8', errors='replace').replace('\x00', '').strip()
    check(not SECRET.search(output.encode()), 'Credential-like command output withheld')
    return output


def reconcile(root):
    check(command(root, ['git', 'branch', '--show-current']) == 'main', 'Production main branch required')
    remote = command(root, ['git', 'remote', 'get-url', 'origin'])
    check(remote in ('https://github.com/serg-alexv/lab-rm-phylogenomics-196.git',
                     'https://github.com/serg-alexv/lab-rm-phylogenomics-196',
                     'git@github.com:serg-alexv/lab-rm-phylogenomics-196.git'), 'Unexpected canonical origin')
    command(root, ['git', 'fetch', 'origin', 'main'])
    command(root, ['git', 'pull', '--ff-only', 'origin', 'main'])
    return command(root, ['git', 'rev-parse', 'HEAD'])


def publish_progress(root):
    """Exact explicit files; no recursive staging, no force, remote bytes verified."""
    allowed = set(PUBLIC)
    check(set(command(root, ['git', 'diff', '--cached', '--name-only']).splitlines()) <= allowed,
          'Pre-existing staged changes outside progress allowlist; preserved')
    for name in PUBLIC:
        content = (root / name).read_bytes()
        check(len(content) <= 1024 * 1024 and not SECRET.search(content), 'Unsafe progress publication file: ' + name)
    command(root, ['git', 'add', '--', *PUBLIC])
    staged = set(command(root, ['git', 'diff', '--cached', '--name-only']).splitlines())
    check(staged <= allowed, 'Staged paths escaped progress allowlist')
    if staged:
        command(root, ['git', 'commit', '-m', 'Record actual bounded Stage04 execution and independent gate progress'])
    command(root, ['git', 'push', 'origin', 'main'])
    head = command(root, ['git', 'rev-parse', 'HEAD'])
    check(command(root, ['git', 'ls-remote', 'origin', 'refs/heads/main']).split()[0] == head,
          'Remote main commit verification failed')
    command(root, ['git', 'fetch', 'origin', 'main'])
    check(command(root, ['git', 'rev-parse', 'origin/main']) == head, 'Fetched remote main commit differs')
    # Commit identity alone is not readback. Compare all five sanitized bytes.
    for name in PUBLIC:
        remote_bytes = subprocess.run(['git', 'show', 'origin/main:' + name], cwd=root, capture_output=True, check=True).stdout
        check(hashlib.sha256(remote_bytes).hexdigest() == digest(root / name), 'Remote progress bytes differ: ' + name)
    return head


def linux_path(path):
    path = Path(path).resolve()
    check(path.drive and not str(path).startswith('\\\\'), 'WD local drive path required')
    return '/mnt/' + path.drive[0].lower() + '/' + '/'.join(path.parts[1:])


def wsl(args, child):
    # No shell interpolation; path conversion performed explicitly.
    return ['wsl', '-d', args.distribution, '--', 'bash', 'scripts/wsl_project.sh', 'host', *child]


def windows_snapshot(root, pid=None):
    # Numeric PID is the only dynamic PowerShell expression.
    statement = "$stageOs=Get-CimInstance Win32_OperatingSystem; $stageDisk=Get-PSDrive -Name '" + root.drive[0] + "'; "
    statement += "$stageProc=" + ("Get-CimInstance Win32_Process -Filter 'ProcessId=" + str(int(pid)) + "'" if pid is not None else '$null') + '; '
    statement += "[pscustomobject]@{utc=[DateTime]::UtcNow.ToString('o');host=[Environment]::MachineName;available_bytes=([int64]$stageOs.FreePhysicalMemory*1024);disk_available_bytes=$stageDisk.Free;pid=$stageProc.ProcessId;creation_utc=if($stageProc){$stageProc.CreationDate.ToUniversalTime().ToString('o')}else{$null};working_set_bytes=if($stageProc){[int64]$stageProc.WorkingSetSize}else{$null};cpu_seconds=if($stageProc){([double]$stageProc.UserModeTime+[double]$stageProc.KernelModeTime)/10000000}else{$null}}|ConvertTo-Json -Compress"
    return json.loads(command(root, ['powershell', '-NoProfile', '-Command', statement], timeout=30))


def inside(args, path):
    path = Path(path).resolve()
    check(path == args.root or args.root in path.parents, 'Path outside dedicated project')
    return path.relative_to(args.root).as_posix()


def supported_flags(script):
    tree = ast.parse(script.read_text(encoding='utf-8-sig'))
    return {arg.value for node in ast.walk(tree) if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute) and node.func.attr == 'add_argument'
            for arg in node.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str)}


def input_identity(args):
    paths = [Path(__file__), args.producer, args.validator, args.linux_launcher, args.root / 'scripts/wsl_project.sh',
             args.config, args.marker_validation, args.root / 'config/approval.json',
             args.root / 'config/approved_accessions.txt', args.root / 'config/approved_panel.tsv',
             args.root / 'evidence/g0/reports/sensitivity162_accessions.txt', args.markers / 'accepted_sequence_manifest.tsv',
             args.markers / 'primary_marker_order.txt', args.markers / 'inventory_summary.json', args.markers / 'marker_qc.tsv',
             args.markers / 'runtime/runtime_receipt.json', args.resource_receipt]
    paths += [p for p in (args.orthology_config, args.original_marker_validation, args.original_marker_publication) if p]
    if args.original_markers:
        paths += [args.original_markers / name for name in ('inventory_summary.json', 'accepted_sequence_manifest.tsv', 'primary_marker_order.txt')]
    # Mutable publication receipt is independently rechecked, not part of science hash.
    return {'scope': 'Exact full196 Stage4; no pilot', 'file_sha256': {inside(args, p): digest(p) for p in paths},
            'marker_view': inside(args, args.markers), 'output': inside(args, args.output),
            'maximum_compute_threads': 2, 'address_space_limit_bytes': LIMIT,
            'iqtree_memory_mib': args.iqtree_memory_mib}


def input_gate(args):
    approval = load(args.root / 'config/approval.json')
    check(approval['human_approval'] == 'APPROVED_FOR_SEQUENCE_ANALYSIS' and approval['approved_assembly_count'] == 196
          and approval['pilot'] is False and approval['routine_stage_human_wait'] is False, 'Full196 execution authorization differs')
    check(digest(args.root / 'config/approved_accessions.txt') == approval['panel_accessions_sha256'], 'Panel bytes changed')
    validation = load(args.marker_validation)
    check(validation['status'] == 'PASS_MARKER_SOURCE_AND_FIXED_FILTERS'
          and validation['scientific_stage_status'] == 'PASS_HOST_MARKER_INVENTORY'
          and validation['approved_assemblies'] == validation['independently_verified_searches'] == 196
          and validation['profiles_searched'] == 119 and validation['marker_cells'] == 23324
          and validation['scientific_blockers'] == [] and validation['same_locus_multiple_profile_candidates'] == 0,
          'Current independent Stage3 scientific gate failed')
    if args.orthology_config:
        check(args.original_marker_validation is not None and args.original_markers is not None, 'Orthology view requires original v1 integrity certificate and marker files')
        original = load(args.original_marker_validation)
        check(original['status'] == 'PASS_MARKER_SOURCE_AND_FIXED_FILTERS'
              and original['approved_assemblies'] == original['independently_verified_searches'] == 196
              and original['profiles_searched'] == 119 and original['marker_cells'] == 23324
              and original['scientific_stage_status'] == 'HOST_ORTHOLOGY_DUPLICATE_SIGNAL_REVIEW_REQUIRED'
              and original['primary_markers'] == 101 and original['accepted_marker_sequences'] == 19551
              and original['same_locus_multiple_profile_candidates'] == 192,
              'Original v1 executed full119/full196 integrity proof missing')
        check(validation['curation_status'] == 'PASS_TOPOLOGY_BLIND_ORTHOLOGY_DEDUPLICATION'
              and validation['original_validation_summary_sha256'] == digest(args.original_marker_validation)
              and validation['orthology_curation_config_sha256'] == digest(args.orthology_config)
              and validation['orthology_curation_receipt_sha256'] == digest(args.markers / 'curation_receipt.json')
              and validation['primary_markers'] == 100 and validation['accepted_marker_sequences'] == 19359
              and validation['minimum_unique_initial_length_markers'] >= 96,
              'Independent orthology projection/original-integrity hash gate failed')
        check(validation['producer_identity'] == original['producer_identity'], 'Curation changed original search identity')
        needed = {'--orthology-config', '--original-marker-validation', '--original-markers'}
        check(needed <= supported_flags(args.producer), 'Adopted producer lacks explicit strict orthology-v2 gate arguments; no launch')
        check(needed | {'--marker-validation', '--config', '--producer-source'} <= supported_flags(args.validator),
              'Adopted independent Stage4 checker lacks explicit current curation paths; no launch')
    for path in [args.marker_publication] + ([args.original_marker_publication] if args.original_marker_publication else []):
        receipt = load(path)
        check(receipt['status'] == 'UPLOAD_VERIFIED' and receipt['remote_tag_commit_verified'] is True
              and receipt['approved_assemblies'] == 196 and receipt['assets']
              and all(a['download_readback_verified'] is True and a['all_zip_member_hashes_verified'] is True
                      and a['bytes'] > 0 and re.fullmatch('[a-f0-9]{64}', a['sha256']) for a in receipt['assets']),
              'Stage3 verified publication gate failed: ' + inside(args, path))
        if args.orthology_config:
            check(receipt['curated_validation_summary_sha256'] == digest(args.marker_validation)
                  and receipt['original_validation_summary_sha256'] == digest(args.original_marker_validation)
                  and receipt['orthology_curation_config_sha256'] == digest(args.orthology_config)
                  and receipt['orthology_curation_receipt_sha256'] == digest(args.markers / 'curation_receipt.json'),
                  'Stage3 verified receipt does not bind both preserved original and curated evidence')


def resource_preflight(args):
    windows = windows_snapshot(args.root)
    linux = json.loads(command(args.root, wsl(args, [linux_path(args.host_env / 'bin/python'), '-u',
        linux_path(args.linux_launcher), '--mode', 'resources']), timeout=60))
    check(windows['available_bytes'] > LIMIT and linux['linux_available_bytes'] > LIMIT,
          'Measured current Windows/Linux headroom insufficient; no launch')
    check(windows['disk_available_bytes'] > 5 * 1024 ** 3, 'Less than5GiB measured local disk headroom')
    check(len(linux['cpu_affinity_available']) >= 2, 'Less than two available compute CPUs')
    if not args.resource_receipt.exists():
        atomic(args.resource_receipt, {'utc': now(), 'host': 'WD', 'maximum_compute_threads': 2,
              'iqtree_memory_mib': args.iqtree_memory_mib, 'process_address_space_limit_bytes': LIMIT,
              'measured_windows_available_bytes': windows['available_bytes'],
              'measured_linux_available_bytes': linux['linux_available_bytes'],
              'measured_windows_disk_available_bytes': windows['disk_available_bytes'],
              'linux_cpu_affinity_available': linux['cpu_affinity_available'],
              'resource_scope': 'Frozen launch preflight; current live measurements stored separately'})
    receipt = load(args.resource_receipt)
    check(receipt['maximum_compute_threads'] == 2 and receipt['iqtree_memory_mib'] == args.iqtree_memory_mib
          and receipt['process_address_space_limit_bytes'] == LIMIT
          and receipt['measured_windows_available_bytes'] > LIMIT and receipt['measured_linux_available_bytes'] > LIMIT,
          'Immutable resource receipt differs or lacks sufficient actual measurements')
    return {'windows': windows, 'linux': linux}


def phase_command(args, phase):
    python = linux_path(args.host_env / 'bin/python')
    common = ['--root', linux_path(args.root), '--markers', linux_path(args.markers)]
    if phase in ('align', 'trees'):
        argv = [python, '-u', linux_path(args.producer), '--phase', phase, *common,
                '--marker-validation', linux_path(args.marker_validation), '--marker-publication', linux_path(args.marker_publication),
                '--config', linux_path(args.config), '--output', linux_path(args.output), '--host-env', linux_path(args.host_env),
                '--resource-receipt', linux_path(args.resource_receipt), '--alignment-validation', linux_path(args.alignment_validation / 'validation_summary.json'),
                '--iqtree-memory-mib', str(args.iqtree_memory_mib)]
        if args.orthology_config:
            argv += ['--orthology-config', linux_path(args.orthology_config),
                     '--original-marker-validation', linux_path(args.original_marker_validation), '--original-markers', linux_path(args.original_markers)]
        return argv
    destination = args.alignment_validation if phase == 'validate_alignment' else args.final_validation
    argv = [python, '-u', linux_path(args.validator), '--phase', 'alignment' if phase == 'validate_alignment' else 'final',
            *common, '--input', linux_path(args.output), '--output', linux_path(destination), '--marker-validation', linux_path(args.marker_validation),
            '--config', linux_path(args.config), '--producer-source', linux_path(args.producer)]
    argv += ['--host-env', linux_path(args.host_env), '--resource-receipt', linux_path(args.resource_receipt)]
    if args.orthology_config:
        argv += ['--orthology-config', linux_path(args.orthology_config), '--original-markers', linux_path(args.original_markers),
                 '--original-marker-validation', linux_path(args.original_marker_validation)]
    return argv


def result_gate(args, phase):
    if phase == 'align':
        path = args.output / 'alignment_summary.json'
        value = load(path)
        check(value['execution'] == 'ALL_PRIMARY_ALIGNMENTS_AND_FOUR_CONCATENATIONS_CONSTRUCTED'
              and len(value['analyses']) == 4 and value['analysis_freeze_sha256'] == digest(args.output / 'analysis_freeze.json')
              and value['analysis_manifest_sha256'] == digest(args.output / 'analysis_alignment_manifest.json'), 'Actual alignment construction incomplete')
    elif phase == 'trees':
        path = args.output / 'phylogeny_summary.json'
        value = load(path)
        check(value['execution'] == 'ALL_PRIMARY_AND_SENSITIVITY_INFERENCES_COMPLETED' and len(value['analyses']) == 4
              and value['alignment_validation_sha256'] == digest(args.alignment_validation / 'validation_summary.json'), 'Actual inference construction incomplete')
    else:
        path = (args.alignment_validation if phase == 'validate_alignment' else args.final_validation) / 'validation_summary.json'
        value = load(path)
        wanted = 'PASS_ALIGNMENT_FORMATS_AND_PARTITIONS' if phase == 'validate_alignment' else 'PASS_HOST_PHYLOGENY_AND_SENSITIVITY_OUTPUT_INTEGRITY'
        check(value['status'] == wanted and value['analyses_verified'] == 4 and value['primary_tip_ids'] == 196,
              'Independent Stage4 gate failed for ' + phase)
        check(value['analysis_freeze_sha256'] == digest(args.output / 'analysis_freeze.json')
              and value['alignment_summary_sha256'] == digest(args.output / 'alignment_summary.json')
              and value['analysis_manifest_sha256'] == digest(args.output / 'analysis_alignment_manifest.json')
              and value['validator_source_sha256'] == digest(args.validator), 'Independent Stage4 gate hash binding failed')
        if phase == 'validate_final':
            check(value['phylogeny_summary_sha256'] == digest(args.output / 'phylogeny_summary.json'), 'Final inference binding failed')
    return {'path': inside(args, path), 'sha256': digest(path), 'scientific_gate': value.get('status', 'CONSTRUCTION_ONLY_INDEPENDENT_GATE_REQUIRED')}


def state_update(args, state):
    state['updated_utc'] = now()
    atomic(args.control / 'state.json', state)


def progress(args, state, execution, failure=None):
    """Select only scientific process/command/resource evidence for public files."""
    reconcile(args.root)
    if failure is None:
        check(input_identity(args) == state['identity'], 'Input/code correction arrived before progress publication; dependent continuation blocked')
    current = state.get('current') or {}
    directory = args.root / current['receipt_directory'] if current else None
    linux = load(directory / 'linux_progress.json') if directory and (directory / 'linux_progress.json').is_file() else None
    launch = load(directory / 'linux_launch_receipt.json') if directory and (directory / 'linux_launch_receipt.json').is_file() else None
    values = {'utc': now(), 'execution': execution, 'phase': current.get('phase'), 'controller_pid': os.getpid(),
              'windows_wsl_launcher_pid': current.get('windows_wsl_launcher_pid'),
              'windows_wsl_launcher_creation_utc': current.get('windows_wsl_launcher_creation_utc'),
              'linux_launcher_pid': launch['launcher_pid'] if launch else None,
              'linux_job_pid': launch['job_pid'] if launch else None,
              'actual_argv': launch['argv'] if launch else current.get('child_argv'),
              'actual_linux_process_measurements': linux, 'phase_receipt_directory': current.get('receipt_directory'),
              'stdout_log': current.get('stdout_log'), 'stderr_log': current.get('stderr_log'),
              'completed_phases': state['completed'], 'scientific_input_identity': state['identity'],
              'scientific_validation': 'PASS_HOST_PHYLOGENY_AND_SENSITIVITY_OUTPUT_INTEGRITY' if execution == 'ALL_FOUR_PHASES_INDEPENDENTLY_VALIDATED' else 'INCOMPLETE',
              'github_publication': 'PROGRESS_COMMIT_ONLY_RELEASE_PENDING',
              'failure': failure, 'outputs_preserved': True}
    producer_progress = args.output / 'execution_progress.json'
    if producer_progress.is_file():
        values['producer_progress'] = load(producer_progress)
    atomic(args.root / 'status/stage04_execution.json', values)
    atomic(args.root / 'reports/stage04/progress.json', values)
    path = args.root / 'status/stages.tsv'
    with path.open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream, delimiter='\t'))
    target = [row for row in rows if row['stage'] == '4_phylogeny']
    check(len(target) == 1, 'Stage4 status row missing/duplicated')
    target[0].update(execution=execution, validation=values['scientific_validation'], publication='PROGRESS_PUBLISHED_RELEASE_PENDING')
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    atomic(path, buffer.getvalue())
    detail = ('Stage4 actual alignment/inference and both independent validation phases completed. Portable release packaging and remote byte verification remain required beforeStage5.'
              if execution == 'ALL_FOUR_PHASES_INDEPENDENTLY_VALIDATED' else
              'Stage4 '+ execution + '. Current phase=' + str(current.get('phase')) + '. All196 primary tips required; no scientific completion or verified final Release is claimed.')
    if failure:
        detail += ' Blocker: ' + failure
    text = '# Current execution status\n\nUpdated ' + now() + '. Full approved196 production cohort; no pilot.\n\n' + detail + '\n\n'
    text += '| Stage | Execution | Validation | Publication |\n|---|---|---|---|\n'
    text += ''.join('| ' + ' | '.join(row.values()) + ' |\n' for row in rows)
    text += '\nSee stage reports and separate publication receipts. Raw private session logs are excluded.\n'
    atomic(args.root / 'STATUS.md', text)
    head = publish_progress(args.root)
    atomic(args.control / 'last_progress_publication.json', {'utc': now(), 'status': 'REMOTE_COMMIT_AND_FIVE_FILE_BYTES_VERIFIED', 'commit': head})


def exit_gate(directory, identity, invocation):
    value = load(directory / 'linux_exit_receipt.json')
    check(value['identity'] == identity and value['invocation_id'] == invocation, 'Actual exit receipt identity differs')
    check(value['execution'] == 'ACTUAL_LINUX_PHASE_CHILD_EXITED' and value['exit_code'] == 0,
          'Actual native phase exit=' + str(value.get('exit_code')) + '; outputs preserved')
    return value


def monitor(directory, identity, invocation, process, inspect, periodic, period=300, interval=5):
    """Wait through publication failures to preserve/measure the existing child."""
    next_publish = time.monotonic()
    publication_failure = None
    while True:
        final = directory / 'linux_exit_receipt.json'
        if final.is_file():
            exit_value = exit_gate(directory, identity, invocation)
            if process is not None:
                try:
                    windows_exit = process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    raise ValueError('Native child exited, Windows WSL launcher still active beyond30s; no duplicate launch')
                check(windows_exit == 0, 'Windows WSL wrapper exit=' + str(windows_exit))
            check(publication_failure is None, 'Progress publication failed while existing phase completed: ' + str(publication_failure))
            return exit_value
        if time.monotonic() >= next_publish:
            try:
                periodic()
            except Exception as error:
                publication_failure = str(error)
                atomic(directory / 'progress_publication_failure.json', {'utc': now(), 'error': publication_failure,
                       'action': 'Continue monitoring existing actual child to exit; no dependent launch'})
            next_publish = time.monotonic() + period
        launch = directory / 'linux_launch_receipt.json'
        if launch.is_file():
            checked = inspect()
            check(checked['identity'] == identity and checked['invocation_id'] == invocation, 'Resume actual PID receipt identity differs')
            if checked['status'] == 'NO_ACTIVE_MATCHING_PID_AND_NO_EXIT_RECEIPT_BLOCKER':
                # Re-read after inspect to avoid the actual exit-write race.
                check(final.is_file(), 'No active exact Linux child and no actual exit receipt; no duplicate permitted')
            elif checked['status'] == 'ACTIVE_EXACT_JOB_BUT_LAUNCHER_LOST_NO_DUPLICATE_PERMITTED':
                raise ValueError('Exact Linux child remains active but observer launcher lost; preserve process, no duplicate/no invented exit')
        elif process is not None and process.poll() is not None:
            raise ValueError('Windows WSL wrapper exited before actual Linux launch receipt; inspect native logs; no scientific PASS')
        time.sleep(interval)


def native_inspect(args, directory):
    return json.loads(command(args.root, wsl(args, [linux_path(args.host_env / 'bin/python'), '-u',
          linux_path(args.linux_launcher), '--mode', 'inspect', '--receipt-dir', linux_path(directory)]), timeout=60))


def execute(args, state, phase):
    current = state.get('current')
    process, streams = None, []
    if current:
        check(current['phase'] == phase and current['identity'] == state['identity'], 'Pending actual phase/input identity changed; inspect preserved job')
        directory = args.root / current['receipt_directory']
        if not (directory / 'linux_launch_receipt.json').is_file() and not (directory / 'linux_exit_receipt.json').is_file():
            snapshot = windows_snapshot(args.root, current['windows_wsl_launcher_pid']) if current.get('windows_wsl_launcher_pid') else {}
            if snapshot.get('pid') and snapshot.get('creation_utc') == current.get('windows_wsl_launcher_creation_utc'):
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline and not (directory / 'linux_launch_receipt.json').is_file():
                    time.sleep(1)
            check((directory / 'linux_launch_receipt.json').is_file(), 'Interrupted pre-launch receipt without verified actual Linux job; manual evidence reconciliation required, no automatic duplicate')
    else:
        resource_preflight(args)
        invocation = str(uuid.uuid4())
        directory = args.control / ('phase_' + phase + '_' + invocation)
        identity_path = args.control / ('identity_' + invocation + '.json')
        atomic(identity_path, state['identity'])
        child = phase_command(args, phase)
        current = {'phase': phase, 'invocation_id': invocation, 'identity': state['identity'],
                   'receipt_directory': inside(args, directory), 'started_utc': now(), 'child_argv': child,
                   'stdout_log': inside(args, args.control / (phase + '_' + invocation + '.stdout.log')),
                   'stderr_log': inside(args, args.control / (phase + '_' + invocation + '.stderr.log'))}
        state['current'] = current
        state_update(args, state)  # Before spawn: interrupted launch is explicit, never guessed.
        argv = wsl(args, [linux_path(args.host_env / 'bin/python'), '-u', linux_path(args.linux_launcher),
                 '--root', linux_path(args.root), '--phase', phase, '--invocation-id', invocation,
                 '--receipt-dir', linux_path(directory), '--identity-file', linux_path(identity_path), '--', *child])
        streams = [(args.root / current[name]).open('ab') for name in ('stdout_log', 'stderr_log')]
        process = subprocess.Popen(argv, cwd=args.root, stdin=subprocess.DEVNULL, stdout=streams[0], stderr=streams[1])
        snapshot = windows_snapshot(args.root, process.pid)
        current.update(windows_wsl_launcher_pid=process.pid, windows_wsl_launcher_creation_utc=snapshot['creation_utc'], windows_argv=argv)
        current['windows_wsl_launcher_measurement'] = snapshot
        current['windows_creation_measurement_limit'] = None if snapshot['creation_utc'] else 'WSL wrapper exited before its CIM creation-time snapshot'
        state_update(args, state)
        print('ACTUAL_STAGE04_PHASE_STARTED ' + phase + ' windows_wsl_launcher_pid=' + str(process.pid), flush=True)
    def periodic():
        progress(args, state, 'RUNNING_' + phase.upper())
    try:
        result = monitor(directory, state['identity'], current['invocation_id'], process,
                         lambda: native_inspect(args, directory), periodic, args.publish_seconds, args.poll_seconds)
    finally:
        for stream in streams:
            stream.close()
    evidence = result_gate(args, phase)
    state['completed'][phase] = {'actual_exit_receipt': inside(args, directory / 'linux_exit_receipt.json'),
                               'actual_exit_receipt_sha256': digest(directory / 'linux_exit_receipt.json'),
                               'gate': evidence, 'elapsed_seconds': result['elapsed_seconds'],
                               'child_cpu_seconds': result['child_cpu_seconds'], 'children_max_rss_bytes': result['children_max_rss_bytes'],
                               'linux_job_pid': result['job_pid'], 'linux_launcher_pid': result['launcher_pid'],
                               'actual_exit_code': result['exit_code'], 'invocation_id': current['invocation_id'],
                               'windows_wsl_launcher_pid': current.get('windows_wsl_launcher_pid'),
                               'windows_wsl_launcher_creation_utc': current.get('windows_wsl_launcher_creation_utc'),
                               'windows_creation_measurement_limit': current.get('windows_creation_measurement_limit'),
                               'stdout_log': current['stdout_log'], 'stderr_log': current['stderr_log'],
                               'actual_argv': result['argv'], 'sampled_tree_peak_rss_bytes': result['sampled_tree_peak_rss_bytes'],
                               'resource_measurement_limit': result['peak_measurement_limit']}
    state['current'] = None
    state_update(args, state)


def main(args):
    check(sys.platform == 'win32' and socket.gethostname().lower() == 'wd', 'Production controller is WD Windows only')
    check(Path.cwd().resolve() == args.root, 'Run in the dedicated repository')
    with WorkflowLock(args.root / '.work/workflow.lock'):
        atomic(args.root / '.work/workflow_owner.json', {'pid': os.getpid(), 'utc': now(), 'script': inside(args, Path(__file__)),
               'scope': 'Sequential actual Stage04 align/check/tree/check with bounded resources'})
        state = None
        try:
            reconcile(args.root)
            input_gate(args)
            existing_state = args.control / 'state.json'
            if not existing_state.is_file() or not load(existing_state).get('current'):
                resource_preflight(args)
            identity = input_identity(args)
            state_path = args.control / 'state.json'
            if state_path.exists():
                state = load(state_path)
                check(state['identity'] == identity, 'Resumed controller identity differs; preserved state requires review')
            else:
                state = {'scope': 'full196', 'started_utc': now(), 'identity': identity, 'completed': {}, 'current': None}
                state_update(args, state)
            for phase in PHASES:
                reconcile(args.root)
                input_gate(args)
                check(input_identity(args) == state['identity'], 'Frozen input/code changed before phase; preserve outputs')
                if phase in state['completed']:
                    receipt = state['completed'][phase]
                    path = args.root / receipt['actual_exit_receipt']
                    check(digest(path) == receipt['actual_exit_receipt_sha256'] and load(path)['exit_code'] == 0, 'Completed actual exit evidence changed')
                    check(result_gate(args, phase) == receipt['gate'], 'Completed phase gate changed; no sentinel reuse')
                else:
                    execute(args, state, phase)
                progress(args, state, 'COMPLETED_' + phase.upper())
            progress(args, state, 'ALL_FOUR_PHASES_INDEPENDENTLY_VALIDATED')
            atomic(args.control / 'controller_complete.json', {'utc': now(), 'execution': 'ALL_FOUR_PHASES_INDEPENDENTLY_VALIDATED',
                   'identity': state['identity'], 'completed': state['completed'], 'publication': 'STAGE04_RELEASE_AND_READBACK_REQUIRED'})
            print('STAGE04_ACTUAL_COMPUTATION_AND_INDEPENDENT_CHECKS_COMPLETE; RELEASE_PACKAGING_AND_REMOTE_READBACK_REQUIRED', flush=True)
        except Exception as error:
            failure = {'utc': now(), 'error': str(error), 'outputs_preserved': True, 'controller_pid': os.getpid(),
                       'dependent_stage_action': 'BLOCKED; no biological retry/panel pruning/resource relaxation'}
            atomic(args.control / 'controller_failure.json', failure)
            if state:
                try:
                    progress(args, state, 'STOPPED_WITH_EXPLICIT_BLOCKER', str(error))
                except Exception as publication_error:
                    atomic(args.control / 'failure_publication_failure.json', {'utc': now(), 'error': str(publication_error), 'scientific_failure': failure})
            raise


def parse():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--markers', type=Path, required=False)
    parser.add_argument('--marker-validation', type=Path)
    parser.add_argument('--marker-publication', type=Path)
    parser.add_argument('--original-marker-validation', type=Path)
    parser.add_argument('--original-markers', type=Path)
    parser.add_argument('--original-marker-publication', type=Path)
    parser.add_argument('--orthology-config', type=Path)
    parser.add_argument('--config', type=Path, default=Path('config/host_primary_stage03_v1.json'))
    parser.add_argument('--producer', type=Path, default=Path('scripts/stage04_phylogeny.py'))
    parser.add_argument('--validator', type=Path, default=Path('scripts/stage04_validate.py'))
    parser.add_argument('--linux-launcher', type=Path, default=Path('scripts/stage04_linux_launcher.py'))
    parser.add_argument('--host-env', type=Path, default=Path('.tools/linux/host_env'))
    parser.add_argument('--output', type=Path, default=Path('.work/stage04_phylogeny_v2'))
    parser.add_argument('--alignment-validation', type=Path, default=Path('.work/stage04_alignment_validation'))
    parser.add_argument('--final-validation', type=Path, default=Path('.work/stage04_final_validation'))
    parser.add_argument('--control', type=Path, default=Path('.work/stage04_controller'))
    parser.add_argument('--resource-receipt', type=Path, default=Path('reports/stage04/resource_preflight.json'))
    parser.add_argument('--distribution', default='Ubuntu')
    parser.add_argument('--iqtree-memory-mib', type=int, default=1536)
    parser.add_argument('--publish-seconds', type=float, default=300)
    parser.add_argument('--poll-seconds', type=float, default=5)
    args = parser.parse_args()
    if args.self_test:
        return args
    check(all((args.markers, args.marker_validation, args.marker_publication)), 'Explicit current marker/validation/publication paths required')
    check(256 <= args.iqtree_memory_mib <= 1536 and args.publish_seconds >= 60 and 1 <= args.poll_seconds <= 30, 'Bounded resources/progress cadence required')
    args.root = args.root.resolve()
    for name, value in vars(args).copy().items():
        if isinstance(value, Path):
            setattr(args, name, value.resolve() if value.is_absolute() else (args.root / value).resolve())
            inside(args, getattr(args, name))
    return args


if __name__ == '__main__':
    args = parse()
    if args.self_test:
        import stage04_controller_synthetic
        stage04_controller_synthetic.run()
    else:
        main(args)
