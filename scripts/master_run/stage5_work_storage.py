"""Observe/verify the one Stage5 ext4 bind mount; never mount or alter storage."""
from pathlib import Path
import argparse, hashlib, json, os, re, stat, sys, uuid
from stage5_atomic_process import read_json, require

BACKING = Path('/var/tmp/lab_rm_stage05_atomic_v1')
SCHEMA = 'STAGE05_EXT4_BIND_STORAGE_PROOF_V1'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def canonical(path):
    path = Path(path)
    require(path.is_absolute() and str(path) == path.as_posix() and '..' not in path.parts,
            'Absolute canonical POSIX storage path required')
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'Storage path symlink forbidden')
    require(path == path.resolve(), 'Storage path resolves to a different location')
    return path


def mount_rows(text):
    def decode(value):
        return re.sub(r'\\([0-7]{3})', lambda match: chr(int(match[1], 8)), value)
    result = []
    for line in text.splitlines():
        left, right = line.split(' - ', 1)
        a, b = left.split(), right.split()
        require(len(a) >= 6 and len(b) == 3, 'Malformed Linux mountinfo')
        result.append({'mount_id': int(a[0]), 'parent_id': int(a[1]), 'major_minor': a[2],
                       'root': decode(a[3]), 'mountpoint': decode(a[4]), 'options': a[5],
                       'optional_fields': a[6:], 'filesystem': b[0], 'source': decode(b[1]),
                       'super_options': b[2]})
    return result


def ext4_uuid(source, device):
    # Root-owned WSL reads 120 superblock bytes, without invoking blkid or mounting.
    fd = os.open(source, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        require(stat.S_ISBLK(info.st_mode) and info.st_rdev == device, 'Mount source block device differs')
        block = os.pread(fd, 120, 1024)
        require(len(block) == 120 and block[56:58] == b'\x53\xef', 'Ext4 superblock magic absent')
        value = uuid.UUID(bytes=block[104:120])
        require(value.int != 0, 'Ext4 filesystem UUID missing')
        return str(value)
    finally:
        os.close(fd)


def observe(root, output_root):
    require(sys.platform == 'linux', 'Storage proof must inspect actual Linux mounts')
    root, target, backing = canonical(root), canonical(output_root), canonical(BACKING)
    require(target == root / '.work/stage05_atomic_v1', 'Exact canonical Stage5 bind target required')
    require(target.is_dir() and backing.is_dir(), 'Already mounted target/backing directories required')
    mountinfo = Path('/proc/self/mountinfo').read_text()
    rows = mount_rows(mountinfo)
    exact = [row for row in rows if Path(row['mountpoint']) == target]
    require(len(exact) == 1, 'One actual mount at the exact Stage5 target required')
    enclosing = [row for row in rows if backing == Path(row['mountpoint']) or Path(row['mountpoint']) in backing.parents]
    require(enclosing, 'Backing filesystem mount missing')
    backing_mount = max(enclosing, key=lambda row: len(Path(row['mountpoint']).parts))
    target_mount = exact[0]
    for base in (target, backing):
        require(not any(base in Path(row['mountpoint']).parents for row in rows), 'Nested Stage5 storage mount forbidden')
    for row in (target_mount, backing_mount):
        require(row['filesystem'] == 'ext4' and 'rw' in row['options'].split(','), 'Writable native ext4 storage required')
    a, b = target.stat(), backing.stat()
    require((a.st_dev, a.st_ino) == (b.st_dev, b.st_ino), 'Target is not the exact bound backing directory')
    device = str(os.major(a.st_dev)) + ':' + str(os.minor(a.st_dev))
    require(target_mount['major_minor'] == backing_mount['major_minor'] == device, 'Mount/device identity differs')
    expected_root = Path(backing_mount['root']) / backing.relative_to(backing_mount['mountpoint'])
    require(Path(target_mount['root']) == expected_root, 'Mount root does not identify the fixed backing directory')
    filesystem_uuid = ext4_uuid(target_mount['source'], a.st_dev)
    require(Path('/proc/self/mountinfo').read_text() == mountinfo
            and (target.stat().st_dev, target.stat().st_ino) == (a.st_dev, a.st_ino)
            and (backing.stat().st_dev, backing.stat().st_ino) == (b.st_dev, b.st_ino), 'Storage changed during observation')
    return {'schema': SCHEMA, 'canonical_root': str(root), 'canonical_target': str(target), 'backing': str(backing),
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'filesystem_uuid': filesystem_uuid, 'directory_device': a.st_dev, 'directory_inode': a.st_ino,
            'target_mount': target_mount, 'backing_mount': backing_mount, 'helper_sha256': sha(__file__)}


def proof_location(path):
    path = canonical(path)
    require(Path('/mnt/c') in path.parents, 'Storage proof must be a separate C-mounted Linux file')
    return path


def validate_storage(config):
    value = config.get('work_storage', {})
    require(isinstance(value, dict) and isinstance(value.get('proof_path'), str)
            and isinstance(value.get('proof_sha256'), str)
            and re.fullmatch('[a-f0-9]{64}', value['proof_sha256']), 'Filled storage proof path/SHA required for run')
    path = proof_location(value['proof_path'])
    require(path.is_file() and sha(path) == value['proof_sha256'], 'Storage proof bytes changed/missing')
    frozen = read_json(path)
    actual = observe(config['root'], config['output_root'])
    require(frozen == actual and sha(path) == value['proof_sha256'], 'Current mount/boot/device/inode/UUID/helper differs from storage proof')
    return {'proof_path': str(path), 'proof_sha256': value['proof_sha256'], **actual}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    commands = parser.add_subparsers(dest='mode', required=True)
    record = commands.add_parser('record', help='Observe an existing mount and exclusively create a proof')
    record.add_argument('--output', required=True)
    validate = commands.add_parser('validate')
    validate.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'record':
        path = proof_location(args.output)
        value = observe(args.root, Path(args.root) / '.work/stage05_atomic_v1')
        with path.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(value, indent=2, sort_keys=True) + '\n')
            stream.flush(); os.fsync(stream.fileno())
        print(json.dumps({'state': 'MOUNT_OBSERVED_ONLY_NOT_BIOLOGY', 'proof_path': str(path), 'proof_sha256': sha(path)}))
    else:
        config = read_json(args.config)
        require(config.get('root') == args.root, 'CLI/config root differs')
        print(json.dumps(validate_storage(config), indent=2))


if __name__ == '__main__':
    main()
