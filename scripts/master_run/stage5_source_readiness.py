#!/usr/bin/env python3
"""Serial current canonical source byte check; no tree/runtime/native execution.

Uses the exact reviewed V2 validate_genome_inputs function only. This is current
source readiness evidence, not a new upstream, detector or curation acceptance.
All outputs are a new direct child directory of this C chat's work directory.
"""
from pathlib import Path
import argparse
import ctypes
import hashlib
import importlib
import json
import os
import sys
import time

sys.dont_write_bytecode = True
WORK = Path(__file__).resolve().parent
EXPECTED_WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
ROOT = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
PINS = {
    'stage5_atomic.py': '2d7414fd33fe6216b95cfd549cee743d8b7057db698aced509f9a7ffefa77fc0',
    'stage5_atomic_process.py': 'fdcc8d3b4337209b64ffa3732a8182bf832f2fa05d1e95fcdfb32964d4ad4a34',
    'stage5_work_storage.py': '7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f',
    'stage5_accepted_source_pins.json': 'a63e9c2b987ecabaa7457d4ab26ad0d6e086cc2488066a92647e72207542de84',
}


class SourceMutationObserved(ValueError):
    """Stop the whole read-only pass if source ownership appears contested."""


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_controls():
    for name, value in PINS.items():
        path = WORK / name
        require(path.is_file() and not path.is_symlink() and digest(path) == value,
                'Changed/missing pinned source checker input: ' + name)


def file_identity(info):
    return {'device': info.st_dev, 'inode': info.st_ino, 'bytes': info.st_size,
            'mtime_ns': info.st_mtime_ns}


def bounded_sha(path, records):
    path = Path(path)
    resolved = path.resolve()
    canonical = ROOT.resolve() in resolved.parents
    active_control = resolved == WORK / 'stage5_accepted_source_pins.json' and not path.is_symlink()
    require(canonical or active_control, 'Source-only hash escaped canonical G or exact active C source pin')
    with path.open('rb') as stream:
        initial = file_identity(os.fstat(stream.fileno()))
        value = hashlib.file_digest(stream, 'sha256').hexdigest()
        final = file_identity(os.fstat(stream.fileno()))
    if initial != final or initial != file_identity(path.stat()):
        raise SourceMutationObserved('Source changed while hashing: ' + str(path))
    if active_control:
        require(value == PINS['stage5_accepted_source_pins.json'], 'Exact standalone source pin control changed')
    records.append({'path': str(path), 'sha256': value,
                    'role': 'ACTIVE_C_ACCEPTED_SOURCE_PIN_CONTROL' if active_control else 'CANONICAL_G_SOURCE',
                    **initial})
    return value


def checked_output(output):
    require(sys.platform == 'win32', 'Run this source-only checker on Windows; never boots WSL')
    require(WORK == EXPECTED_WORK and WORK.resolve() == EXPECTED_WORK,
            'Exact current C chat work deployment required')
    output = Path(output).absolute()
    require(output.parent == WORK and output.resolve() == output and not output.exists(),
            'New direct C work output directory required')
    return output


def verify_all(output):
    output = checked_output(output)
    verify_controls()
    output.mkdir()
    initial = {'schema': 'STAGE05_CURRENT_SOURCE_BYTE_READINESS_V1',
               'status': 'STARTED_NOT_ACCEPTED', 'source_checker_sha256': digest(__file__),
               'input_code_sha256': PINS, 'detector_execution': 'NOT_RUN',
               'workflow_lock_acquired': False, 'scientific_output_mutated': False}
    (output / 'started.json').write_text(json.dumps(initial, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    try:
        return verify_prepared(output)
    except BaseException as error:
        failure = {**initial, 'status': 'FAILED_OR_INTERRUPTED_PARTIAL_SOURCE_READINESS',
                   'error': {'kind': type(error).__name__, 'message': str(error)},
                   'files': {path.name: digest(path) for path in output.iterdir() if path.is_file()}}
        with (output / 'failure_receipt.json').open('x', encoding='utf-8') as stream:
            json.dump(failure, stream, indent=2, sort_keys=True); stream.write('\n')
        raise


def verify_prepared(output):
    code_sha = digest(__file__)
    verify_controls()
    source = importlib.import_module('stage5_atomic')
    for name in ['stage5_atomic', 'stage5_atomic_process', 'stage5_work_storage']:
        path = Path(sys.modules[name].__file__).resolve()
        require(path == WORK / (name + '.py') and digest(path) == PINS[name + '.py'],
                'Loaded source checker code shadowed/changed: ' + name)
    # Dedicated checker process, one file reader. This sets only our scheduling
    # priority; no detector resource requirement is substituted or inferred.
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.GetCurrentProcess.restype = ctypes.c_void_p
    api.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    api.SetPriorityClass.restype = ctypes.c_int
    api.GetPriorityClass.argtypes = [ctypes.c_void_p]
    api.GetPriorityClass.restype = ctypes.c_uint32
    handle = api.GetCurrentProcess()
    require(api.SetPriorityClass(handle, 0x4000) and api.GetPriorityClass(handle) == 0x4000,
            'Could not establish own BELOW_NORMAL_PRIORITY_CLASS')
    panel_path = ROOT / 'config/approved_accessions.txt'
    require(digest(panel_path) == source.PINNED_PANEL, 'Frozen panel changed')
    panel = panel_path.read_text(encoding='ascii').split()
    require(len(panel) == len(set(panel)) == 196, 'Exact196 required')
    config = {'root': str(ROOT), 'source': str(ROOT / '.work/source_locus_inputs_v1'),
              'source_validation': str(ROOT / '.work/stage03_source_validation/validation_summary.json')}
    began = time.monotonic()
    counts = {'accessions_checked': 0, 'passed': 0, 'failed': 0,
              'declared_source_files': 0, 'declared_source_bytes': 0}
    results = []
    with (output / 'actual_file_hashes.jsonl').open('x', encoding='utf-8') as files, \
         (output / 'per_accession.jsonl').open('x', encoding='utf-8') as rows:
        for accession in panel:
            records = []
            original_sha = source.sha
            source.sha = lambda path: bounded_sha(path, records)
            try:
                actual, gate, receipt, acceptance = source.validate_genome_inputs(config, ROOT.resolve(), accession)
                item = {'accession': accession, 'status': 'PASS_CURRENT_ACCEPTED_SOURCE_BYTES_ONLY',
                        'source_receipt_sha256': acceptance['released_source_member']['sha256'],
                        'source_files': len(receipt['output_files']),
                        'source_bytes': sum(x['bytes'] for x in receipt['output_files'])}
                counts['passed'] += 1
                counts['declared_source_files'] += item['source_files']
                counts['declared_source_bytes'] += item['source_bytes']
            except Exception as error:
                if isinstance(error, SourceMutationObserved):
                    raise
                item = {'accession': accession, 'status': 'FAILED_CURRENT_SOURCE_CHECK',
                        'error': {'kind': type(error).__name__, 'message': str(error)}}
                counts['failed'] += 1
            finally:
                source.sha = original_sha
            verify_controls()
            require(digest(__file__) == code_sha, 'Source checker source drift')
            for record in records:
                files.write(json.dumps({'accession': accession, **record}, sort_keys=True) + '\n')
            rows.write(json.dumps(item, sort_keys=True) + '\n')
            files.flush(); rows.flush()
            results.append(item)
            counts['accessions_checked'] += 1
            print(json.dumps({'accession': accession, 'status': item['status'], **counts}), flush=True)
    verify_controls()
    require(digest(__file__) == code_sha, 'Final checker source drift')
    result = {'schema': 'STAGE05_CURRENT_SOURCE_BYTE_READINESS_V1',
              'status': 'PASS_CURRENT_CANONICAL_SOURCE_BYTES_ONLY' if counts['failed'] == 0 else 'FAIL_CURRENT_SOURCE_READINESS',
              'scope': 'EXACT196_CANONICAL_SOURCE_OUTPUT_HASH_SIZE_AND_RELEASED_RECEIPT_CHECK_ONLY',
              'reader_count': 1, 'process_priority': 'BELOW_NORMAL_PRIORITY_CLASS',
              'root': str(ROOT), 'source_checker_sha256': code_sha, 'input_code_sha256': PINS,
              'approved_accessions_sha256': source.PINNED_PANEL, **counts,
              'elapsed_seconds': time.monotonic() - began,
              'files': {name: digest(output / name) for name in ['actual_file_hashes.jsonl', 'per_accession.jsonl']},
              'upstream_acceptance_created': False, 'detector_execution': 'NOT_RUN',
              'runtime_discovery': 'NOT_RUN', 'stage4_tree_consumed': False, 'curation': 'NOT_RUN',
              'scientific_output_mutated': False, 'workflow_lock_acquired': False}
    (output / 'receipt.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.verify:
        verify_controls()
        print(json.dumps({'state': 'PREPARED_NOT_RUN', 'approved_genomes': 196,
                          'scope': 'SERIAL_CANONICAL_SOURCE_BYTE_READINESS_ONLY', 'code_pins': PINS}))
        return 0
    require(args.output, '--verify requires --output')
    result = verify_all(args.output)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result['failed'] == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
