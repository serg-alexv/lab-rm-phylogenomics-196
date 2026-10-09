"""Opt-in nonscientific DriveFS primitives only; caller owns Windows byte lock.
Preserves tiny fixtures, spawns no children, and never authorizes scientific work.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, os, signal, sys, uuid

ROOT_TEXT = '/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196'
ROOT = Path(ROOT_TEXT)
SCOPE = 'NONSCIENTIFIC_DRIVEFS_FILESYSTEM_ONLY'

def require(value, message):
    if not value:
        raise RuntimeError(message)

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner-lock-receipt', type=Path)
    parser.add_argument('--owner-lock-sha256')
    parser.add_argument('--supervisor-sha256')
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    result = {'schema':'STAGE05_DRIVEFS_FILESYSTEM_SMOKE_V1', 'scope':SCOPE,
              'state':'PREPARED_NOT_RUN', 'root':ROOT_TEXT, 'scientific_adoption_authorized':False}
    if not args.run:
        print(json.dumps(result)); return 0
    directory = None
    try:
        require(sys.platform == 'linux', 'Actual Linux required')
        import fcntl
        import stage5_atomic_process as primitives
        require(sha(primitives.__file__) == args.supervisor_sha256, 'Reviewed primitive source hash differs')
        require(args.owner_lock_receipt and Path(__file__).resolve().parent in args.owner_lock_receipt.resolve().parents,
                'Caller lock receipt must be beneath the C chat work bridge')
        require(sha(args.owner_lock_receipt) == args.owner_lock_sha256, 'Caller Windows lock receipt bytes differ')
        require(isinstance(json.loads(args.owner_lock_receipt.read_text(encoding='utf-8-sig')), dict), 'Caller lock receipt missing')
        require(Path('/mnt/g').is_dir() and ROOT.is_dir() and (ROOT/'.work').is_dir(), 'Canonical G mount/project/.work unavailable')
        resolved = ROOT.resolve()
        require((ROOT/'.work').resolve().parent == resolved, 'Canonical .work resolves outside the project')
        mounts = [line for line in Path('/proc/self/mountinfo').read_text().splitlines()
                  if Path(line.split()[4].replace('\\040',' ')) in (resolved, *resolved.parents)]
        mount = max(mounts, key=lambda line:len(line.split()[4]))
        require(mount.split()[4].startswith('/mnt/g'), 'Canonical project does not resolve to a mounted G subtree')
        signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('Filesystem smoke deadline expired')))
        signal.alarm(30)
        nonce = uuid.uuid4().hex
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        directory = ROOT/'.work'/('stage05_atomic_filesystem_smoke_'+stamp+'_'+nonce[:8])
        directory.mkdir()
        payload = ('NONSCIENTIFIC DRIVEFS SMOKE\n'+nonce+'\n').encode()
        ordinary, target, pending = directory/'ordinary.bin', directory/'replaced.bin', directory/'replaced.bin.partial'
        for path, content in ((ordinary,payload), (target,b'OLD SYNTHETIC BYTES\n'), (pending,payload)):
            with path.open('xb') as stream:
                stream.write(content); stream.flush(); os.fsync(stream.fileno())
        require(ordinary.read_bytes() == payload, 'Ordinary fsync/readback mismatch')
        pending.replace(target)
        require(not pending.exists() and target.read_bytes() == payload, 'Atomic overwrite/readback mismatch')
        primitives.atomic_json(directory/'runner_atomic.json', {'scope':SCOPE, 'nonce':nonce})
        require(not (directory/'runner_atomic.json.partial').exists() and
                json.loads((directory/'runner_atomic.json').read_text()) == {'scope':SCOPE,'nonce':nonce}, 'Runner JSON atomic readback mismatch')
        guard, blocked = directory/'.native_runner.guard', False
        with guard.open('a+b') as first:
            fcntl.flock(first, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with guard.open('a+b') as second:
                try:
                    fcntl.flock(second, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    blocked = True
            require(blocked, 'Independent same-file flock did not exclude contender')
        with guard.open('a+b') as reopened:
            fcntl.flock(reopened, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result.update(state='PASS_NONSCIENTIFIC_FILESYSTEM_ONLY', nonce=nonce, mountinfo=mount,
            namespace_relative=directory.relative_to(ROOT).as_posix(), actual_root=str(resolved), root_device=resolved.stat().st_dev,
            caller_lock_receipt_sha256=args.owner_lock_sha256, script_sha256=sha(__file__), supervisor_sha256=sha(primitives.__file__),
            ordinary_write_fsync_readback=True, atomic_overwrite_readback=True, runner_atomic_json_readback=True,
            flock_contention_proven=True, flock_close_release_reacquire_proven=True,
            files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in directory.iterdir() if p.is_file()})
        primitives.atomic_json(directory/'result.json', result)
        result['result_sha256'] = sha(directory/'result.json')
    except BaseException as error:
        result.update(state='FAILED_NONSCIENTIFIC_FILESYSTEM_SMOKE', error=type(error).__name__+': '+str(error),
                      namespace_relative=None if directory is None else directory.relative_to(ROOT).as_posix())
    finally:
        if sys.platform == 'linux':
            signal.alarm(0)
    print(json.dumps(result, sort_keys=True))
    return 0 if result['state'] == 'PASS_NONSCIENTIFIC_FILESYSTEM_ONLY' else 2

if __name__ == '__main__':
    raise SystemExit(main())
