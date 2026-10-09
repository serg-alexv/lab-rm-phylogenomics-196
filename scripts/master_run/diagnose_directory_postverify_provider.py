"""Exact protected12 metadata-only diagnostic; no payload/owner/lock queries."""
from pathlib import Path
from ctypes import wintypes as W
import argparse
import ctypes
import hashlib
import json
import os
import stat
import time

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
PIN = 'a20c9c87d42816355434eb3abbd9ffd082c8c1b73557d773901bb3eb1329a082'
CONTROL = WORK / 'master_history02_postverify_20261009T201921Z_f90337c5/receipt.json'


class Basic(ctypes.Structure):
    _fields_ = [(key, ctypes.c_longlong) for key in ('birth', 'access', 'write', 'change')] + [('attrs', W.DWORD)]


class ID(ctypes.Structure):
    _fields_ = [('volume', ctypes.c_ulonglong), ('identifier', ctypes.c_ubyte * 16)]


class Legacy(ctypes.Structure):
    _fields_ = [('attrs', W.DWORD), ('birth', W.FILETIME), ('access', W.FILETIME), ('write', W.FILETIME),
                ('volume', W.DWORD), ('size_hi', W.DWORD), ('size_lo', W.DWORD), ('links', W.DWORD),
                ('id_hi', W.DWORD), ('id_lo', W.DWORD)]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inspect():
    assert os.name == 'nt' and Path(__file__).resolve().parent == WORK
    assert sha(CONTROL) == PIN
    output = WORK / 'directory_postverify_provider_diagnostic01.json'
    assert not output.exists()
    records = json.loads(CONTROL.read_text())['protected_files']
    assert len(records) == 12
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    k.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, W.LPVOID, W.DWORD, W.DWORD, W.HANDLE]
    k.CreateFileW.restype = W.HANDLE
    k.CloseHandle.argtypes = [W.HANDLE]
    k.GetFileInformationByHandleEx.argtypes = [W.HANDLE, ctypes.c_int, W.LPVOID, W.DWORD]
    k.GetFileInformationByHandle.argtypes = [W.HANDLE, ctypes.POINTER(Legacy)]
    k.GetFinalPathNameByHandleW.argtypes = [W.HANDLE, W.LPWSTR, W.DWORD, W.DWORD]
    rows = []
    began = time.monotonic()
    for original in records:
        assert time.monotonic() - began < 60
        path = Path(original['path'])
        before = path.lstat()
        record = {'path': str(path), 'expected_bytes': original['bytes'], 'expected_sha256': original['sha256'],
                  'lstat': {'regular': stat.S_ISREG(before.st_mode), 'links': before.st_nlink,
                            'attributes': before.st_file_attributes, 'device': str(before.st_dev), 'inode': str(before.st_ino),
                            'bytes': before.st_size, 'mtime_ns': str(before.st_mtime_ns),
                            'birthtime_ns': str(before.st_birthtime_ns)}}
        handle = k.CreateFileW(str(path), 0x80, 7, None, 3, 0x00200000, None)
        if handle == ctypes.c_void_p(-1).value:
            record['native_open_error'] = ctypes.get_last_error()
            rows.append(record)
            continue
        try:
            basic, ident, legacy = Basic(), ID(), Legacy()
            basic_ok = bool(k.GetFileInformationByHandleEx(handle, 0, ctypes.byref(basic), ctypes.sizeof(basic)))
            basic_error = None if basic_ok else ctypes.get_last_error()
            id_ok = bool(k.GetFileInformationByHandleEx(handle, 18, ctypes.byref(ident), ctypes.sizeof(ident)))
            id_error = None if id_ok else ctypes.get_last_error()
            legacy_ok = bool(k.GetFileInformationByHandle(handle, ctypes.byref(legacy)))
            legacy_error = None if legacy_ok else ctypes.get_last_error()
            buf = ctypes.create_unicode_buffer(32768)
            length = k.GetFinalPathNameByHandleW(handle, buf, len(buf), 0)
            record.update(native_basic={'success': basic_ok, 'error': basic_error, 'attributes': basic.attrs,
                                        'birth': str(basic.birth), 'write': str(basic.write), 'change': str(basic.change)},
                          native_id128={'success': id_ok, 'error': id_error, 'volume': str(ident.volume),
                                        'file_id_128': bytes(ident.identifier).hex()},
                          native_legacy={'success': legacy_ok, 'error': legacy_error, 'attributes': legacy.attrs,
                                         'links': legacy.links, 'volume': legacy.volume,
                                         'file_id': str((legacy.id_hi << 32) | legacy.id_lo),
                                         'bytes': (legacy.size_hi << 32) | legacy.size_lo},
                          final_handle_path=buf.value if length else None,
                          original_guard_would_pass=basic_ok and legacy_ok and not basic.attrs & (0x10 | 0x400) and legacy.links == 1)
        finally:
            k.CloseHandle(handle)
        after = path.lstat()
        record['path_metadata_unchanged'] = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_nlink) == (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_nlink)
        rows.append(record)
    result = {'schema': 'MASTER_DIRECTORY_POSTVERIFY_EXACT12_PROVIDER_DIAGNOSTIC_V1',
              'state': 'ACTUAL_READ_ONLY_METADATA_DIAGNOSTIC_NOT_ACCEPTANCE', 'source_sha256': sha(Path(__file__)),
              'control_sha256': PIN, 'rows': rows, 'files': len(rows), 'payload_bytes_read': 0,
              'owner_or_lock_queries': 0, 'g_writes': 0, 'source_mutations': 0, 'wsl_starts': 0,
              'first_original_guard_rejection': next((row['path'] for row in rows if not row.get('original_guard_would_pass', False)), None),
              'elapsed_seconds': time.monotonic() - began}
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'receipt': str(output), 'sha256': sha(output), 'first_original_guard_rejection': result['first_original_guard_rejection'],
                      'native_legacy_link_counts': [row.get('native_legacy', {}).get('links') for row in rows]}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect', action='store_true')
    if parser.parse_args().inspect:
        inspect()
    else:
        print(json.dumps({'state': 'PREPARED_NO_METADATA_DIAGNOSTIC'}))
