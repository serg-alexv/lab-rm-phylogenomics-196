"""Existing-owner helpers: Windows deny-write/delete image handle and raw parts.

No CLI, controller, mount, lock, WSL process, upload, deletion or eviction.
The existing original WorkflowLock owner calls these functions only after its
independently verified clean unmount/detach (toolchain) or WSL shutdown (VHDX).
CreateFile sharing is a real retained Windows handle, not a JSON freeze claim.
Its Linux/DrvFS effectiveness still requires a real fixture before adoption.
Raw public parts additionally require actual whole-file public review, including
unallocated/deleted bytes. Three-role logical review cannot authorize VM bytes.
"""
from pathlib import Path
from contextlib import contextmanager
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
import os
import re
import stat

SHARD_LIMIT = 448*1024**2
CHUNK = 256*1024
WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
IMAGE_PATHS = {
    'toolchain_ext4': r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.tools\toolchain.ext4',
    'ubuntu_vhdx': r'C:\Users\wheel\AppData\Local\wsl\{d58ba874-ce79-4d09-aa37-9d9d8539a6a7}\ext4.vhdx',
}
LABELS = {'toolchain_ext4': 'toolchain-installed-runtime-whole-ext4',
          'ubuntu_vhdx': 'ubuntu-os-project-workspace-whole-vhdx'}
LOCK = {'path': r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.work\workflow.lock',
        'volume_serial': 2430728143, 'file_index': 844424932784519,
        'creation_filetime': 134359335921635133, 'locked_byte': 0}


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(value):
    return isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) is not None


def owner_context(value):
    """Validate the original owner's fresh callback result, not acquire a lock."""
    need(isinstance(value, dict) and value.get('workflow_lock_held') is True,
         'Original owner must continuously retain its lock')
    lock = value.get('workflow_lock')
    need(isinstance(lock, dict) and set(lock) == set(LOCK)
         and all(type(lock[k]) is type(v) and lock[k] == v for k, v in LOCK.items()),
         'Exact immutable original lock identity required')
    need(type(value.get('owner_pid')) is int and value['owner_pid'] > 0
         and isinstance(value.get('owner_creation_filetime'), str)
         and re.fullmatch('[0-9]+', value['owner_creation_filetime'])
         and int(value['owner_creation_filetime']) > 0
         and isinstance(value.get('nonce'), str) and re.fullmatch('[a-f0-9]{32}', value['nonce']),
         'Current retained owner birth and nonce required')
    return value['owner_pid'], value['owner_creation_filetime'], value['nonce']


def image_identity(role, value):
    need(role in IMAGE_PATHS and isinstance(value, dict), 'Known image role and actual identity required')
    keys = {'path', 'volume_serial', 'file_index', 'creation_filetime', 'written_filetime', 'bytes', 'links', 'attributes'}
    need(set(value) == keys and value['path'] == IMAGE_PATHS[role], 'Exact image path/identity fields required')
    need(all(type(value[k]) is int and value[k] >= 0 for k in keys-{'path'})
         and value['file_index'] > 0 and value['creation_filetime'] > 0 and value['bytes'] > 0
         and value['links'] == 1 and not value['attributes'] & (0x400 | 0x10),
         'Regular single-link nonreparse image identity required')
    return value


class ImageReadLease:
    """Callable existing-owner component; no new workflow owner or process.

    GENERIC_READ/FILE_SHARE_READ/OPEN_EXISTING denies write and delete sharing.
    Existing incompatible writer handles cause an error; never force them shut.
    The owner callback must enforce real closure, current resources and deadline.
    This helper proves only its retained handle/identity, not those outer gates.
    """
    def __init__(self, api, role, expected, guard):
        need(os.name == 'nt' and callable(guard), 'Actual Windows existing-owner callback required')
        self.api, self.role, self.expected, self.guard = api, role, image_identity(role, expected), guard
        self.handle = None
        self.context = None
        def bind(name, restype, args):
            fn = getattr(api.K, name); fn.restype = restype; fn.argtypes = args; return fn
        self.create = bind('CreateFileW', w.HANDLE, [w.LPCWSTR, w.DWORD, w.DWORD, c.c_void_p, w.DWORD, w.DWORD, w.HANDLE])
        self.final_path = bind('GetFinalPathNameByHandleW', w.DWORD, [w.HANDLE, w.LPWSTR, w.DWORD, w.DWORD])
        self.file_type = bind('GetFileType', w.DWORD, [w.HANDLE])
        self.read_file = bind('ReadFile', w.BOOL, [w.HANDLE, c.c_void_p, w.DWORD, c.POINTER(w.DWORD), c.c_void_p])
    def check(self):
        context = owner_context(self.guard())
        need(self.context is None or context == self.context, 'Existing owner identity changed')
        self.context = context
        actual_owner = self.api.identity(self.api.current(), os.getpid())
        need(actual_owner['pid'] == context[0] and str(actual_owner['creation_filetime']) == context[1],
             'Image lease must remain in the original retained Windows owner process')
        if self.handle is not None:
            need(self.identity() == self.expected, 'Retained image identity changed')
    def identity(self):
        need(self.handle is not None, 'Actual retained image handle required')
        info = self.api.FILEINFO()
        self.api.ok(self.api.file_info(self.handle, c.byref(info)), 'Image GetFileInformationByHandle')
        name = c.create_unicode_buffer(32768)
        length = self.final_path(self.handle, name, len(name), 0)
        self.api.ok(length, 'Image GetFinalPathNameByHandleW')
        need(length < len(name) and name.value == '\\\\?\\'+IMAGE_PATHS[self.role]
             and self.file_type(self.handle) == 1, 'Retained image final path/type differs')
        return image_identity(self.role, {'path': IMAGE_PATHS[self.role], 'volume_serial': info.volume,
            'file_index': (info.indexHigh << 32) | info.indexLow, 'creation_filetime': self.api.ft(info.created),
            'written_filetime': self.api.ft(info.written), 'bytes': (info.sizeHigh << 32) | info.sizeLow,
            'links': info.links, 'attributes': info.attributes})
    def __enter__(self):
        self.check()
        path = Path(IMAGE_PATHS[self.role])
        need(path.is_absolute() and path.resolve() == path, 'Exact nonaliased image path required')
        for node in [path, *path.parents]:
            info = node.lstat()
            need(not node.is_symlink() and not getattr(info, 'st_file_attributes', 0) & 0x400,
                 'Image or ancestor is reparse/aliased')
        handle = self.create(str(path), 0x80000000, 0x1, None, 3, 0x00200000 | 0x08000000, None)
        need(handle not in (None, 0, c.c_void_p(-1).value), 'Image writer/delete exclusion failed; preserve and stop')
        self.handle = handle
        try:
            self.check()
            return self
        except BaseException:
            self.api.close(self.handle); self.handle = None
            raise
    def read(self, count):
        need(type(count) is int and 0 < count <= CHUNK, 'Bounded retained-handle read required')
        self.check(); buffer = c.create_string_buffer(count); copied = w.DWORD()
        self.api.ok(self.read_file(self.handle, buffer, count, c.byref(copied), None), 'Image ReadFile')
        need(copied.value <= count, 'Image read grew beyond requested block')
        self.check()
        return buffer.raw[:copied.value]
    def __exit__(self, *unused):
        try:
            if self.handle is not None:
                self.check()
        finally:
            if self.handle is not None:
                self.api.ok(self.api.close(self.handle), 'Close owned image read handle')
                self.handle = None


def public_review(role, identity, value):
    """A syntactic gate; the owner must independently execute/verify the review."""
    image_identity(role, identity)
    need(isinstance(value, dict) and value.get('schema') == 'STAGE05_OFFLINE_IMAGE_WHOLE_BYTE_PUBLIC_REVIEW_V1'
         and value.get('role') == role and value.get('source_identity') == identity
         and type(value.get('complete_file_bytes_reviewed')) is int
         and value['complete_file_bytes_reviewed'] == identity['bytes']
         and value.get('allocated_and_unallocated_bytes_reviewed') is True
         and type(value.get('private_or_unknown_bytes_remaining')) is int
         and value['private_or_unknown_bytes_remaining'] == 0
         and value.get('decision') == 'PUBLIC_ORIGINAL_BYTES'
         and isinstance(value.get('reviewer_id'), str) and value['reviewer_id'].strip()
         and sha(value.get('whole_file_sha256')), 'Actual whole-image public byte review required; logical scope is insufficient')
    return value['whole_file_sha256']


def partition_stream(reader, open_part, size, expected_sha, label, snapshot, guard, limit=SHARD_LIMIT):
    """Bounded stream primitive; no source opening, paths, networking or deletion.

    open_part(name) returns an exclusive writable context manager. Partial files
    remain on failure. This pure primitive is NOT independent public review.
    """
    need(callable(reader) and callable(open_part) and callable(guard), 'Owned stream/write/admission callbacks required')
    need(type(size) is int and 0 < size <= 128*1024**3 and sha(expected_sha), 'Finite source bytes and external whole SHA required')
    need(type(limit) is int and 0 < limit <= SHARD_LIMIT and label in LABELS.values()
         and isinstance(snapshot, str) and re.fullmatch('[0-9]{8}-v[1-9][0-9]*', snapshot), 'Exact labels/snapshot/part cap required')
    total = 0; whole = hashlib.sha256(); rows = []
    while total < size:
        guard(); name = 'stage05-image-'+label+'-'+snapshot+'.part'+str(len(rows)+1).zfill(4)
        remaining = min(limit, size-total); part = hashlib.sha256(); count = 0; offset = total
        with open_part(name) as output:
            while count < remaining:
                guard(); wanted = min(CHUNK, remaining-count); block = reader(wanted)
                need(isinstance(block, bytes) and 0 < len(block) <= wanted, 'Image truncated or reader exceeded bound')
                need(output.write(block) == len(block), 'Short local part write')
                part.update(block); whole.update(block); total += len(block); count += len(block)
            output.flush()
        rows.append({'name': name, 'offset': offset, 'bytes': count, 'sha256': part.hexdigest()})
    guard(); need(reader(1) == b'' and whole.hexdigest() == expected_sha, 'Actual full image size/SHA differs from audited bytes')
    return {'parts': rows, 'bytes': total, 'whole_file_sha256': whole.hexdigest(), 'maximum_asset_bytes': limit}


def split_public_image(lease, review, output, snapshot, source_sha256):
    """Existing-owner opt-in raw split; requires actual independently public bytes.

    Clean unmount/shutdown, original WorkflowLock and current resources are
    required by the owner's guard, not invented by this helper. No remote or
    restore claim results. Prefer semantic three-role logical capture.
    """
    need(isinstance(lease, ImageReadLease) and lease.handle is not None, 'Original owner retained image lease required')
    need(sha(source_sha256) and hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == source_sha256,
         'Explicit reviewed offline-helper source pin required')
    lease.check(); expected = public_review(lease.role, lease.expected, review)
    output = Path(output)
    need(output.is_absolute() and output.parent == WORK and output == output.resolve()
         and not output.exists() and re.fullmatch('stage5_offline_image_parts_[A-Za-z0-9_]+', output.name),
         'Fresh direct C offline-image output required')
    for parent in [WORK, *WORK.parents]:
        info = parent.lstat()
        need(stat.S_ISDIR(info.st_mode) and not parent.is_symlink() and not getattr(info, 'st_file_attributes', 0) & 0x400,
             'Plain output ancestry required')
    output.mkdir()
    @contextmanager
    def open_part(name):
        with (output/name).open('xb') as stream:
            yield stream
            stream.flush(); os.fsync(stream.fileno())
    result = partition_stream(lease.read, open_part, lease.expected['bytes'], expected,
                              LABELS[lease.role], snapshot, lease.check)
    lease.check()
    need(hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == source_sha256,
         'Offline-helper source drifted during raw split')
    result.update(schema='STAGE05_OFFLINE_PUBLIC_IMAGE_PARTS_V1', state='LOCAL_PARTS_PENDING_INDEPENDENT_REMOTE_READBACK',
                  role=lease.role, original_path=IMAGE_PATHS[lease.role], source_identity=lease.expected,
                  whole_byte_public_review=review, source_sha256=source_sha256,
                  reassembly='Concatenate parts in listed offset order; exact original bytes and SHA only.',
                  remote_recovery='NOT_RUN', cold_restore='NOT_RUN', eviction_authorized=False)
    for row in result['parts']:
        with (output/(row['name']+'.sha256')).open('x', encoding='ascii', newline='\n') as stream:
            stream.write(row['sha256']+'  '+row['name']+'\n'); stream.flush(); os.fsync(stream.fileno())
    with (output/'index.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2, sort_keys=True); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    return result
