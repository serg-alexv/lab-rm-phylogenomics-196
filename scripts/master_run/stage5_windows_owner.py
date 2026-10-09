"""Serial Windows lock owner and fresh resource lease for WSL genome jobs.

BUILD ONLY until actual WSL/process/lease integration has passed. No scientific
job runs without --run. Linux owns native detector closure and per-genome caches;
this process owns the stable Windows writer lock and the WSL client handle.
"""
from pathlib import Path, PurePosixPath
import argparse
import json
import os
import subprocess
import time
import uuid
import atomic_iqtree_windows as A
import stage5_atomic as S
import stage5_work_storage as W

ROOT = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
WSL = r'C:\Windows\System32\wsl.exe'
LOCAL_CLOSURE_STOP = A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json')
EXIT_STATES = {'COMPLETE_VALIDATED': 0, 'FAILED_RETRYABLE': 1,
               'FAILED_FATAL': 2, 'DEFERRED_RESOURCE': 75}


def linux_path(path):
    path = Path(path).resolve()
    A.require(path.drive and len(path.drive) == 2, 'Explicit local drive path required')
    return '/mnt/' + path.drive[0].lower() + '/' + '/'.join(path.parts[1:])


def terminal_binding(status, accession, nonce, code):
    A.require(status.get('accession') == accession and status.get('owner_nonce') == nonce,
              'Stale or different Linux terminal invocation receipt')
    A.require(status.get('state') in EXIT_STATES and EXIT_STATES[status['state']] == code,
              'Linux terminal state differs from actual retained WSL client exit')


def evidence_view(config, helper_hash):
    """Read the native bind through WSL, never the covered Windows G directory."""
    value = config.get('work_storage', {})
    proof = PurePosixPath(value.get('proof_path') or '')
    A.require(proof.is_absolute() and proof.parts[:3] == ('/', 'mnt', 'c')
              and '..' not in proof.parts and '\\' not in str(proof)
              and str(proof) == value.get('proof_path'), 'Exact C-mounted storage proof required')
    windows_proof = Path('C:/').joinpath(*proof.parts[3:])
    A.require(windows_proof.is_file() and A.sha256(windows_proof) == value.get('proof_sha256'),
              'Windows storage proof readback differs')
    frozen = A.read_json(windows_proof)
    target = linux_path(ROOT) + '/.work/stage05_atomic_v1'
    A.require(config.get('output_root') == target and frozen.get('schema') == W.SCHEMA
              and frozen.get('canonical_root') == linux_path(ROOT)
              and frozen.get('canonical_target') == target and frozen.get('backing') == W.BACKING.as_posix()
              and frozen.get('helper_sha256') == helper_hash,
              'Storage proof/config/helper identity differs')
    A.require(frozen.get('filesystem_uuid') and frozen.get('boot_id')
              and frozen.get('target_mount', {}).get('filesystem') == 'ext4',
              'Actual ext4 observation missing from storage proof')
    return Path(r'\\wsl.localhost\Ubuntu').joinpath(*PurePosixPath(target).parts[1:])


def fresh_authority():
    A.require(not LOCAL_CLOSURE_STOP.exists(),
              'Durable local owned-closure stop exists; reconcile exact native scope before launch')
    control = A.read_json(ROOT / 'status/run_control.json')
    A.require(control.get('state') == 'ACTIVE_DIRECT_USER_CONTINUATION'
              and control.get('automatic_resume') is False,
              'Fresh direct continuation authority is absent or halted')
    return control


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--linux-script', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    cfg = S.load_config(args.config)
    A.require(cfg.get('schema') == 'STAGE05_ATOMIC_CONFIG_V1', 'Unknown Linux job config')
    A.require(cfg.get('root') == linux_path(ROOT), 'Canonical Linux scientific root differs')
    prefix = linux_path(ROOT) + '/.work/stage05_atomic_v1'
    A.require(cfg.get('output_root') == prefix or cfg.get('output_root', '').startswith(prefix + '/'),
              'New canonical Stage5 scientific namespace required')
    output_relative = cfg['output_root'][len(linux_path(ROOT)) + 1:]
    A.require('..' not in output_relative.split('/') and '\\' not in output_relative,
              'Unsafe Linux scientific output path')
    output_root = ROOT.joinpath(*output_relative.split('/')).resolve()
    A.require(ROOT.resolve() in output_root.parents, 'Scientific output path escapes canonical project')
    panel_path = ROOT / 'config/approved_accessions.txt'
    panel = panel_path.read_text().split()
    A.require(A.sha256(panel_path) == A.EXPECTED_PANEL and len(panel) == len(set(panel)) == 196,
              'Exact frozen approved196 panel required')
    control = fresh_authority()
    A.require(args.config.is_file() and args.linux_script.is_file(), 'Prepared Linux code/config required')
    A.require(args.linux_script.resolve() == Path(__file__).with_name('stage5_atomic.py').resolve(),
              'Use the same reviewed Linux runner that supplied policy validation')
    supervisor = args.linux_script.with_name('stage5_atomic_process.py')
    A.require(supervisor.is_file(), 'Actual Linux process supervisor missing')
    storage_helper = args.linux_script.with_name('stage5_work_storage.py')
    A.require(storage_helper.is_file(), 'Reviewed native storage verifier missing')
    if not args.run:
        print(json.dumps({'state': 'PREPARED_NOT_RUN', 'genomes': len(panel),
                          'config_sha256': A.sha256(args.config), 'linux_script_sha256': A.sha256(args.linux_script)}))
        return 0
    A.require(not args.output.exists(), 'Use a new owner spool; preserve prior receipts')
    A.require(Path(__file__).resolve().parent in args.output.resolve().parents,
              'Scope temporary Windows owner spool beneath this chat work directory')
    args.output.mkdir(parents=True)
    api = A.Win()
    owner = api.identity(api.current(), os.getpid())
    cfg_hash, script_hash = A.sha256(args.config), A.sha256(args.linux_script)
    supervisor_hash = A.sha256(supervisor)
    storage_helper_hash = A.sha256(storage_helper)
    native_output_root = evidence_view(cfg, storage_helper_hash)
    nonce, lease_path = uuid.uuid4().hex, args.output / 'owner_lease.json'
    policy = cfg['resource_policy']
    ttl = policy['lease_max_age_seconds']
    A.require(10 <= ttl <= 60, 'Finite fresh owner lease required')
    results, active_child, idle_previous, last_resources = [], None, None, None
    native_scope_closed = True
    batch = {'state': 'FAILED_FATAL', 'utc': A.utc(), 'owner': owner,
             'config_sha256': cfg_hash, 'linux_script_sha256': script_hash,
             'linux_supervisor_sha256': supervisor_hash,
             'storage_helper_sha256': storage_helper_hash,
             'native_evidence_view': str(native_output_root),
             'approved_accessions_sha256': A.EXPECTED_PANEL, 'genome_results': results}
    with A.WorkflowLock(api) as lock:
        fresh_authority()
        A.require(native_output_root.is_dir(), 'Native WSL UNC output view unavailable')
        def lease(active=True):
            nonlocal last_resources
            if active:
                fresh_authority()
                last_resources = api.resources([ROOT, args.output])
            resources = last_resources or {'physical_available_bytes': 0, 'commit_headroom_bytes': 0,
                                           'disk_available_bytes': {}}
            now = time.time()
            A.atomic(lease_path, {'schema': 'STAGE05_WINDOWS_OWNER_LEASE_V1', 'nonce': nonce,
                'workflow_lock_held': active, 'workflow_lock': lock.identity,
                'owner_pid': owner['pid'], 'owner_creation_filetime': str(owner['creation_filetime']),
                'measured_unix': now, 'expires_unix': now + ttl if active else now,
                'windows_available_bytes': resources['physical_available_bytes'],
                'windows_commit_headroom_bytes': resources['commit_headroom_bytes'],
                'disk_available_bytes': resources['disk_available_bytes'], 'utc': A.utc()})
        try:
            idle_previous = api.execution_state(0x80000001)
            A.require(idle_previous, 'Transient idle-sleep prevention failed')
            lease()
            A.atomic(args.output / 'owner.json', {**batch, 'workflow_lock': lock.identity,
                'linux_closure_scope': 'Native pidfd/subreaper closure is required by each Linux job; WSL client exit alone is insufficient'})
            for index, accession in enumerate(panel, 1):
                A.require(A.sha256(args.config) == cfg_hash and A.sha256(args.linux_script) == script_hash,
                          'Running batch code/config drift; preserve prior completed genomes')
                A.require(A.sha256(supervisor) == supervisor_hash, 'Running Linux supervisor bytes changed')
                A.require(A.sha256(storage_helper) == storage_helper_hash,
                          'Running native storage verifier bytes changed')
                A.require(evidence_view(cfg, storage_helper_hash) == native_output_root,
                          'Native evidence view/proof drift')
                lease()
                argv = [WSL, '-d', 'Ubuntu', '-u', 'root', '--exec',
                        cfg['runtime']['environment_dir'] + '/bin/python', '-B', linux_path(args.linux_script),
                        '--config', linux_path(args.config), 'run', '--accession', accession,
                        '--owner-lease', linux_path(lease_path), '--owner-nonce', nonce]
                start = time.monotonic()
                with (args.output / (accession + '.stdout.txt')).open('wb') as stdout, (args.output / (accession + '.stderr.txt')).open('wb') as stderr:
                    active_child = subprocess.Popen(argv, stdout=stdout, stderr=stderr)
                    native_scope_closed = False
                    birth = api.identity(int(active_child._handle), active_child.pid,
                                         retained_image=WSL, retained_session=owner['session_id'])
                    A.atomic(args.output / (accession + '.launch.json'), {'utc': A.utc(), 'argv': argv,
                        'native_wsl_client': birth, 'owner_nonce': nonce, 'index': index})
                    last_lease = time.monotonic()
                    deadline = start + policy['job_timeout_seconds'] + policy['resource_wait_seconds'] + 120
                    while active_child.poll() is None:
                        if time.monotonic() >= deadline:
                            lease(False)
                            raise A.OwnedClosureFailure('WSL client exceeded bounded Linux job/closure deadline; no next genome')
                        if time.monotonic() - last_lease >= min(3, ttl / 4):
                            lease()
                            last_lease = time.monotonic()
                        time.sleep(0.25)
                    exact_exit = api.identity(int(active_child._handle), active_child.pid,
                                              retained_image=birth['executable'], retained_session=birth['session_id'])
                    A.require(exact_exit['creation_filetime'] == birth['creation_filetime']
                              and exact_exit['exited'] and exact_exit['exit_filetime'] > exact_exit['creation_filetime'],
                              'Actual retained WSL client exit identity differs')
                status_path = native_output_root / accession / 'status.json'
                A.require(status_path.is_file(), 'Linux genome terminal receipt missing; no next genome')
                status = A.read_json(status_path)
                terminal_binding(status, accession, nonce, exact_exit['exit_code'])
                A.require(status.get('owned_closure_proven') is True,
                          'Linux terminal invocation does not establish actual native closure')
                native_scope_closed = True
                if status['state'] == 'COMPLETE_VALIDATED':
                    A.require(exact_exit['exit_code'] == 0 and (native_output_root/accession/'complete.json').is_file(),
                              'Linux complete status lacks actual exit0/checkpoint')
                    A.require(A.sha256(native_output_root/accession/'complete.json') == status.get('complete_receipt_sha256'),
                              'Current successful invocation does not bind the exact completed scientific checkpoint')
                result = {'accession': accession, 'state': status['state'], 'actual_wsl_client_exit': exact_exit,
                          'elapsed_seconds': time.monotonic() - start, 'status_sha256': A.sha256(status_path),
                          'stdout_sha256': A.sha256(args.output/(accession+'.stdout.txt')),
                          'stderr_sha256': A.sha256(args.output/(accession+'.stderr.txt'))}
                results.append(result)
                A.atomic(args.output / (accession + '.exit.json'), result)
                A.atomic(args.output / 'progress.json', {'utc': A.utc(), 'finished': len(results), 'total': 196,
                                                       'latest': result, 'genome_results': results})
                print(json.dumps({'accession': accession, 'state': status['state'], 'finished': len(results), 'total': 196}), flush=True)
                active_child = None
                if status['state'] in ('FAILED_FATAL', 'DEFERRED_RESOURCE'):
                    batch['state'] = status['state']
                    break
            else:
                batch['state'] = 'COMPLETE_VALIDATED' if all(r['state'] == 'COMPLETE_VALIDATED' for r in results) else 'FAILED_RETRYABLE'
        except BaseException as error:
            batch.update(state='FAILED_FATAL', error={'kind': type(error).__name__, 'message': str(error)})
            try:
                lease(False)
            except BaseException as failure:
                batch.setdefault('finalizer_errors', []).append('lease invalidation: ' + str(failure))
            if active_child is not None and active_child.poll() is None:
                # The Linux owner-lease expiry path closes only its retained
                # native descendants. Keep the writer lock until the client exits.
                try:
                    active_child.wait(timeout=ttl + policy['termination_grace_seconds'] + policy['drain_timeout_seconds'] + 15)
                except subprocess.TimeoutExpired:
                    batch['closure'] = 'UNPROVEN_STOP_NO_DUPLICATE_LAUNCH'
            if not native_scope_closed:
                # WSL client exit alone does not establish native closure.
                # Finite fatal return may release the OS lock; block all new
                # authorized runners until exact owned closure is reconciled.
                A.atomic(LOCAL_CLOSURE_STOP, {'schema':'STAGE05_UNPROVEN_CLOSURE_STOP_V1',
                    'utc':A.utc(), 'owner':owner, 'owner_nonce':nonce,
                    'evidence':str(args.output.resolve()), 'automatic_resume':False,
                    'reason':'Native WSL scope closure unproven; no new scientific launch until reconciliation'})
                current = A.read_json(ROOT/'status/run_control.json')
                A.atomic(args.output / 'run_control_before_closure_block.json', current)
                A.atomic(ROOT/'status/run_control.json', {**current,
                    'state': 'FAILED_FATAL_OWNED_CLOSURE' if current.get('state') == 'ACTIVE_DIRECT_USER_CONTINUATION' else current.get('state'),
                    'automatic_resume': False, 'owned_closure_unproven': True,
                    'updated_utc': A.utc(), 'closure_evidence': str(args.output),
                    'reason': 'Owned WSL/native closure unproven; reconcile before any new scientific launch'})
            raise
        finally:
            try:
                lease(False)
            except BaseException as failure:
                batch.setdefault('finalizer_errors', []).append('final lease invalidation: ' + str(failure))
            batch['utc'] = A.utc()
            try:
                if idle_previous is not None:
                    A.require(api.execution_state(idle_previous), 'Transient power-state restore failed')
            except BaseException as failure:
                batch.setdefault('finalizer_errors', []).append('power restoration: ' + str(failure))
                batch['state'] = 'FAILED_FATAL'
            A.atomic(args.output / 'result.json', batch)
    A.atomic(args.output / 'lock_released.json', {'utc': A.utc(), 'state': 'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED'})
    return 0 if batch['state'] == 'COMPLETE_VALIDATED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
