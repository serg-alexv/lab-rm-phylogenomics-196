"""Preserve dirty files and publish only current bootstrap evidence under stable lock."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import msvcrt
import shutil
import subprocess
import sys

CHAT = Path(__file__).resolve().parents[1]
ROOT = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
HISTORY = Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
REPORT = ROOT / 'reports/stage04/atomic_resume_20261009'
EXPECTED = '2a7552bc5556d5ff82cc44602bc366e51e25ff47'

def sha(path):
    return hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True, encoding='utf-8').strip()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

def main():
    lock = (HISTORY / '.work/workflow.lock').open('r+b')
    lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    try:
        assert git('rev-parse', 'HEAD') == EXPECTED, 'Local commit changed; reconcile first'
        assert git('rev-parse', 'origin/main') == EXPECTED, 'Remote ref changed; reconcile first'
        stamp = dt.datetime.now(dt.timezone.utc).isoformat()
        baseline = CHAT / 'work/bootstrap/dirty_tracked_snapshot'
        for name in git('diff', '--name-only').splitlines():
            target = baseline / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        REPORT.mkdir(parents=True, exist_ok=True)
        old_control = ROOT / 'status/run_control.json'
        shutil.copyfile(old_control, REPORT / 'previous_run_control.json')
        shutil.copyfile(ROOT / 'status/stage04_execution.json', REPORT / 'previous_stage04_execution.json')
        for name in ('independent_input_validation.json', 'input_sha256.tsv', 'tree_inventory.json'):
            shutil.copyfile(CHAT / 'work/independent_inputs' / name, REPORT / name)
        shutil.copyfile(CHAT / 'work/independent_inputs/independent_stage04a_check.py', ROOT / 'scripts/independent_stage04a_check_20261009.py')
        cleanup = sorted((CHAT / 'work/bootstrap').glob('resource_cleanup_*.json'))[-1]
        shutil.copyfile(cleanup, REPORT / 'resource_cleanup.json')
        shutil.copyfile(CHAT / 'work/bootstrap/wsl_toolchain_probe_final.txt', REPORT / 'wsl_toolchain_probe.txt')
        save(ROOT / 'status/run_control.json', {
            'schema': 'DIRECT_HUMAN_RUN_CONTROL_V2', 'utc': stamp,
            'state': 'ACTIVE_DIRECT_USER_CONTINUATION', 'automatic_resume': False,
            'authority': 'Current direct human full-study continuation request and scoped resource/WSL repair authorization',
            'scope': 'Primary196 Stage4 inference, per-genome Stage5, four-ring figure and independent validation/publication',
            'previous_control_sha256': sha(REPORT / 'previous_run_control.json'),
            'old_V10_exit_and_job_closure': 'UNKNOWN_PRESERVED',
            'historical_scheduled_tasks': 'REMAIN_DISABLED',
            'recurring_automation': 'NOT_AUTHORIZED_OR_CREATED',
        })
        save(ROOT / 'status/atomic_continuation_20261009.json', {
            'utc': stamp, 'bootstrap': 'PASS_ACCEPTED_STAGE04A_INPUTS',
            'scientific_stage4': 'INCOMPLETE_NO_ACCEPTED_TREE',
            'execution_stage4': 'BOUNDED_RESOURCE_ADMISSION_PREPARATION',
            'scientific_stage5': 'NOT_RUN', 'scientific_stage6': 'NOT_RUN', 'scientific_stage7': 'NOT_RUN',
            'biology_launched': False,
            'canonical_commit_before_bootstrap': EXPECTED,
            'dirty_previous_work': 'PRESERVED_NOT_BLANKET_STAGED',
            'admission_policy': {'preferred_job_commit_gib': 4.5, 'host_reserve_gib': 1.5,
                'fresh_minimum_physical_available_gib': 6, 'fresh_minimum_system_commit_headroom_gib': 6,
                'preferred_wait_minutes': 30, 'threads': 2,
                'basis': 'Historical nearly3GiB aggregate peak plus50percent margin and1.5GiB host reserve; sufficiency not guaranteed'},
            'wsl_configuration': {'memory_gib': 6, 'processors': 4, 'swap_gib': 8,
                'backup_sha256': sha(CHAT / 'work/bootstrap/wslconfig.before'),
                'new_sha256': sha(Path(r'C:\Users\wheel\.wslconfig')),
                'live_probe': 'PASS_INSTALLED_LINUX_TOOLS', 'state_after_probe': 'STOPPED'},
        })
        save(ROOT / 'status/stage04_execution.json', {
            'utc': stamp, 'state': 'BOUNDED_RESOURCE_ADMISSION_PREPARATION',
            'scientific_status': 'INCOMPLETE_NO_ACCEPTED_TREE', 'actual_native_pid': None,
            'active_inference_found': False, 'previous_V10_outcome': 'UNKNOWN_PRESERVED',
            'previous_execution_record': 'reports/stage04/atomic_resume_20261009/previous_stage04_execution.json',
            'input_gate': 'PASS_ACCEPTED_STAGE04A_INPUTS',
            'new_biological_inference_launched': False,
        })
        report = '''# Fresh atomic continuation bootstrap, 2026-10-09

The current direct human request resumes the previously halted full196 study. It accepts the existing validated Stage4a alignment, makes optional sensitivity analyses nonblocking, requests simple atomic tasks and explicitly authorizes scoped resource cleanup and WSL configuration repair. Historical failures and unknown original V10 exits remain unchanged.

## Verified scientific state

Independent checker: PASS_ACCEPTED_STAGE04A_INPUTS,19 checks. Exact196 approved taxa,17456 amino-acid columns,100 exhaustive nonoverlapping marker partitions. All12 primary artifact hashes, all100 trimmed marker hashes,19600 source blocks and both already-local Stage04a ZIP hashes match. No upstream biological stage was rerun and no accepted release input was downloaded again.

FASTA SHA256 `442742d083628ab5382a10cafc422c57084cd9bde45a4f2950f15e2c199e3307`; partition SHA256 `fa640e5e984b33e73a86b1ec7a7c18f7161a12252e68e9e3c6ceb2644eb7edc5`.

No completed exact196 tree was found in scoped G/C project inventories or canonical releases. Retained partial model cache790572bytes/SHA256 `d20ef88dd11a7a2c7f5e9b99baef0108f05a21ec4a6b74226e547ce93afe8b42` is preserved. It is not a completed ModelFinder/tree result. Stage4 remains scientifically incomplete; Stages5–7 remain NOT_RUN.

## Host repair and next gate

Twenty optional idle MCP leaf services were stopped using retained native handles, exact process creation/image checks, sampled inactivity and fresh no-child checks. The receipt records actual exits; it does not claim continuous absence of activity. No scientific process, Codex/control connection, unrelated user application or accepted file was terminated/deleted. Cleanup-boundary available RAM rose4.24→5.16GiB; actual system commit headroom after cleanup6.94GiB. Later launch must use a fresh measurement.

Backed-up `.wslconfig` now limits WSL to6GiB RAM,4CPUs,8GiB swap with gradual reclamation. Existing networking, firewall, nested virtualization and GUI options are preserved. Ubuntu was started only to verify retained tools, then its tool image was synced/unmounted and Ubuntu stopped. Actual root ext4 free1032086183936bytes is virtual filesystem headroom backed by C; toolchain ext4 free1442689024bytes. Neither is additional physical disk capacity.

Current executed Linux versions: Python3.11.17, PADLOC2.0.0, mdmparis-defense-finder3.0.0, MacSyFinder2.1.4, HMMER3.4, R4.3.1, pyhmmer0.12.3, pyrodigal3.7.1. No detector model update or scientific search was run. Windows IQ-TREE3.1.4 executable SHA256 `43c9bf3b0dc5e7d88c183a2582369d22c9d692b7585350038769334bb6fd9aed` matches its pin.

Preferred new atomic attempt:2threads, same accepted partitioned AA/MFP scientific input/seed/supports;4.5GiB owned-job commit budget plus1.5GiB host reserve, requiring fresh6GiB available RAM and6GiB actual system commit headroom. Historical3GiB caps had essentially no margin. Preferred admission is bounded30minutes; a lower-memory single-model fallback needs supported native memory-saving controls/evidence, not an invented smaller requirement. Existing old controllers and scheduled tasks are not reactivated.

## Remaining work

Complete and independently validate/freeze/publish the primary196 tree. Then run resumable per-accession PADLOC/DefenseFinder jobs from the retained validated source/context inputs, curate R-M architecture and subtype/state evidence, validate784 exact accession-joined cells, render SVG/PDF/iTOL with rings I,II including IIG,III,IV, and independently validate/publish. The existing V7 detector preparation is not an executed screening result or operational per-genome runner.

Scientific validation and GitHub publication are separate states. This report is bootstrap evidence, not a completed scientific Stage4 release.
'''
        (REPORT / 'REPORT.md').write_text(report, encoding='utf-8')
        status = ROOT / 'STATUS.md'
        old_status = status.read_text(encoding='utf-8')
        status.write_text('# Current execution status\n\n## Direct user continuation — ' + stamp + '\n\n**ACTIVE_DIRECT_USER_CONTINUATION.** Bootstrap and accepted Stage4a inputs independently validated; bounded resource admission is being prepared for one new atomic native inference attempt. No new biological job has started. Stage4 remains incomplete and Stages5–7 NOT_RUN. Historical tasks remain disabled and historical unknown exits remain preserved. See `reports/stage04/atomic_resume_20261009/REPORT.md` and `status/atomic_continuation_20261009.json`.\n\n' + old_status.removeprefix('# Current execution status\n\n'), encoding='utf-8')
        stages = ROOT / 'status/stages.tsv'
        lines = stages.read_text(encoding='utf-8').splitlines()
        for i, line in enumerate(lines):
            if line.startswith('4_phylogeny\t'):
                parts = line.split('\t'); parts[1] = 'BOUNDED_RESOURCE_ADMISSION_PREPARATION'; parts[4] = stamp
                parts[5:] = ['', '']; lines[i] = '\t'.join(parts)
        stages.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        order = ROOT / 'WORK_ORDER.md'
        with order.open('a', encoding='utf-8') as f:
            f.write('\n\n## Current direct human atomic continuation, 2026-10-09\n\nThe latest direct human instruction resumes the full scientific study after the halt. Reuse accepted Stages0–4a. Primary196 tree acceptance is sufficient to advance Stage5; optional sensitivities must not delay it. Prefer one simple partition-aware native IQ-TREE job with fresh resource margins and bounded admission; then same-data single-model IQ-TREE fallback, and only one alternative ML implementation if genuinely required. Do not blindly reuse1.5/3GiB caps or obsolete controller hierarchies. Stage5 must be resumable per genome. The same user explicitly authorizes necessary scoped additional-resource cleanup and WSL reconfiguration; preserve source data/checkpoints and backup configuration. Current user instructions supersede incompatible old controller/mandatory-sensitivity gates; historical evidence and unknown outcomes remain preserved. No routine approval pause or recurring automation is introduced.\n')
        manifest = {p.relative_to(ROOT).as_posix(): sha(p) for p in REPORT.iterdir() if p.is_file()}
        save(REPORT / 'sha256_manifest.json', manifest)
        allow = ['STATUS.md', 'WORK_ORDER.md', 'status/run_control.json', 'status/stages.tsv',
            'status/atomic_continuation_20261009.json', 'status/stage04_execution.json', 'scripts/independent_stage04a_check_20261009.py']
        allow += [p.relative_to(ROOT).as_posix() for p in REPORT.iterdir() if p.is_file()]
        # Current scientific/control files only; old dirty logs and untracked preparations remain untouched.
        subprocess.run(['git', '-C', str(ROOT), 'add', '--', *allow], check=True)
        staged = git('diff', '--cached', '--name-only').splitlines()
        assert set(staged) == set(allow), 'Unexpected preexisting staged files; do not commit'
        subprocess.run(['git', '-C', str(ROOT), 'diff', '--cached', '--check'], check=True)
        subprocess.run(['git', '-C', str(ROOT), 'commit', '-m', 'Resume atomic full196 continuation and verify retained inputs'], check=True)
        new_commit = git('rev-parse', 'HEAD')
        subprocess.run(['git', '-C', str(ROOT), 'push', 'origin', 'main'], check=True)
        remote_commit = git('ls-remote', 'origin', 'refs/heads/main').split()[0]
        assert remote_commit == new_commit, 'Remote branch readback differs'
        tree = json.loads(subprocess.check_output(['gh', 'api', f'repos/serg-alexv/lab-rm-phylogenomics-196/git/trees/{new_commit}?recursive=1'], text=True, encoding='utf-8'))
        assert not tree.get('truncated'), 'Remote tree response truncated'
        remote_blobs = {entry['path']: entry['sha'] for entry in tree['tree'] if entry['type'] == 'blob'}
        verified = []
        for name in allow:
            blob = git('hash-object', '--', name)
            assert remote_blobs.get(name) == blob, f'Remote blob mismatch: {name}'
            verified.append({'path': name, 'git_blob': blob, 'sha256': sha(ROOT / name)})
        save(CHAT / 'work/bootstrap/publication_receipt.json', {'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
            'state': 'UPLOAD_VERIFIED_GIT_BLOBS', 'commit': new_commit, 'remote_commit': remote_commit,
            'files': verified, 'scientific_stage4': 'INCOMPLETE', 'scientific_stages5_to7': 'NOT_RUN'})
        print(json.dumps({'published': True, 'verified_files': len(verified), 'commit': new_commit, 'utc': stamp}))
    finally:
        lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1); lock.close()

if __name__ == '__main__':
    main()
