#!/usr/bin/env python3
"""Preserve one GToTree production search's exact protein/HMM evidence.
Two PATH shims invoke this same file with mode 'rename' or 'hmmsearch'.
Set GTT_EVIDENCE_DIR, GTT_REAL_RENAME, GTT_REAL_HMMSEARCH to absolute paths.
No markers, thresholds, or selected sequences are changed. Scientific validation
is deliberately separate from the preserved-evidence receipts written here.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def fasta_records(path: Path):
    """Match SimpleFastaParser sequence whitespace behavior; never infer by hash."""
    header = None
    fragments = []
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            if line.startswith('>'):
                if header is not None:
                    yield header, ''.join(fragments).replace(' ', '').replace('\r', '')
                header = line[1:].rstrip()
                fragments = []
            elif header is not None:
                fragments.append(line.rstrip())
            elif line.strip():
                raise ValueError('Text precedes first FASTA header')
    if header is not None:
        yield header, ''.join(fragments).replace(' ', '').replace('\r', '')


def option(args: list[str], names: tuple[str, ...]) -> str | None:
    found = []
    for index, value in enumerate(args):
        if value in names:
            if index + 1 == len(args):
                raise ValueError('Option without value: ' + value)
            found.append(args[index + 1])
    if len(found) > 1:
        raise ValueError('Repeated option: ' + ','.join(names))
    return found[0] if found else None


def receipt(path: Path, data: dict):
    # A different input must never silently overwrite an earlier preserved run.
    content = json.dumps(data, indent=2, ensure_ascii=False) + '\n'
    partial = path.with_suffix(path.suffix + '.partial')
    partial.write_text(content, encoding='utf-8', newline='\n')
    partial.replace(path)


def paths(assembly: str):
    if not re.fullmatch(r'GCF_[0-9]{9}\.[0-9]+', assembly):
        raise ValueError('Expected exact versioned assembly ID: ' + assembly)
    root = Path(os.environ['GTT_EVIDENCE_DIR'])
    if not root.is_absolute():
        raise ValueError('Evidence root must be absolute')
    root = root.resolve()
    out = root / assembly
    out.mkdir(parents=True, exist_ok=True)
    return out


def real_binary(variable: str) -> Path:
    path = Path(os.environ[variable])
    if not path.is_absolute():
        raise ValueError('Real executable path must be absolute')
    path = path.resolve()
    if not path.is_file():
        raise ValueError('Real executable absent: ' + str(path))
    if path == Path(sys.argv[0]).resolve():
        raise ValueError('Wrapper recursion')
    return path


def rename(args: list[str]) -> int:
    binary = real_binary('GTT_REAL_RENAME')
    source = option(args, ('-i', '--input-fasta'))
    target = option(args, ('-o', '--output-fasta'))
    assembly = option(args, ('-w', '--wanted-name'))
    if not source or not target or not assembly:
        return subprocess.call([str(binary), *args])
    out = paths(assembly)
    source_path, target_path = Path(source), Path(target)
    source_hash = digest(source_path)
    previous = out / 'rename_receipt.json'
    if previous.exists():
        old = json.loads(previous.read_text(encoding='utf-8'))
        if (old['input_sha256'] != source_hash or old['real_binary_sha256'] != digest(binary)
                or old['wrapper_sha256'] != digest(Path(__file__))):
            raise ValueError('Different rename input/tool at existing evidence path')
    exit_code = subprocess.call([str(binary), *args])
    if exit_code:
        return exit_code
    original = list(fasta_records(source_path))
    renamed = list(fasta_records(target_path))
    if not original or len(original) != len(renamed):
        raise ValueError('Rename record count mismatch/empty input')
    identifiers = [header.split()[0] for header, _seq in original]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError('Locus input IDs are not unique')
    rows = []
    for index, ((header, sequence), (new_header, new_sequence)) in enumerate(zip(original, renamed), 1):
        expected = assembly + '_' + str(index)
        if new_header != expected or sequence != new_sequence:
            raise ValueError('Unexpected rename/sequence mutation at ordinal ' + str(index))
        locus_key = header.split()[0]
        parts = locus_key.split('|')
        if len(parts) != 3 or parts[0] != assembly or any(not part for part in parts):
            raise ValueError('Expected assembly|replicon|locus input key')
        rows.append([assembly, expected, locus_key, index, len(sequence),
                     hashlib.sha256(sequence.encode('ascii')).hexdigest(), header])
    shutil.copyfile(source_path, out / 'unaltered_locus_input.faa')
    shutil.copyfile(target_path, out / 'gtotree_search_input.faa')
    with (out / 'target_locus_map.tsv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, delimiter='\t', lineterminator='\n')
        writer.writerow(['assembly', 'gtotree_target_id', 'exact_locus_key', 'filtered_input_ordinal',
                         'aa_length', 'unaltered_sequence_sha256', 'input_header'])
        writer.writerows(rows)
    receipt(previous, {'status': 'RENAMING_IDENTITY_VERIFIED', 'scientific_validation': 'NOT_RUN',
                      'assembly': assembly, 'input_sha256': source_hash,
                      'renamed_input_sha256': digest(target_path), 'records': len(rows),
                      'real_binary_sha256': digest(binary), 'wrapper_sha256': digest(Path(__file__)),
                      'argv': [str(binary), *args]})
    return 0



def require_hmm_outputs(out: Path, recorded_hashes: dict | None = None):
    """Every successful/cached receipt preserves exactly four native evidence files."""
    tables = {'hmm.tblout', 'hmm.domtblout'}
    required = tables | {'hmm.stdout.txt', 'hmm.stderr.txt'}
    if recorded_hashes is not None and set(recorded_hashes) != required:
        raise ValueError('Cached HMM receipt must include all four mandatory evidence digests')
    for filename in required:
        if not (out / filename).is_file():
            raise ValueError('HMM evidence file absent: ' + filename)
    for filename in tables:
        path = out / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError('HMM evidence table absent/empty: ' + filename)
        lines = path.read_text(encoding='utf-8').splitlines()
        if not lines or not lines[0].startswith('#') or lines[-1].strip() != '# [ok]':
            raise ValueError('HMM table lacks complete native header/trailer: ' + filename)
    if recorded_hashes is not None:
        for filename, file_hash in recorded_hashes.items():
            if digest(out / filename) != file_hash:
                raise ValueError('Cached HMM evidence hash mismatch: ' + filename)

def hmmsearch(args: list[str]) -> int:
    binary = real_binary('GTT_REAL_HMMSEARCH')
    table = option(args, ('--tblout',))
    if not table:
        return subprocess.call([str(binary), *args])
    if option(args, ('--domtblout',)):
        raise ValueError('Only the inspected GToTree tblout-only invocation is supported')
    suffix = '_curr_hmm_hits.tmp'
    name = Path(table).name
    if not name.endswith(suffix) or len(args) < 2:
        raise ValueError('Unexpected GToTree HMM argument layout')
    assembly = name[:-len(suffix)]
    out = paths(assembly)
    profile, protein = Path(args[-2]), Path(args[-1])
    if not profile.is_file() or not protein.is_file():
        raise ValueError('Expected HMM/FASTA final positional arguments')
    rename_data = json.loads((out / 'rename_receipt.json').read_text(encoding='utf-8'))
    if digest(protein) != rename_data['renamed_input_sha256']:
        raise ValueError('Search protein input differs from preserved rename input')
    identity = {'input_sha256': digest(protein), 'profile_sha256': digest(profile),
                'binary_sha256': digest(binary), 'wrapper_sha256': digest(Path(__file__)),
                # Normalize only transient path arguments, retaining all scoring/cpu options.
                'options': args[:-2][:]}
    idx = identity['options'].index('--tblout')
    identity['options'][idx + 1] = '<GToTree-temporary-tblout>'
    finished = out / 'hmm_receipt.json'
    if finished.exists():
        old = json.loads(finished.read_text(encoding='utf-8'))
        if (old.get('exit_code') != 0 or old.get('identity') != identity
                or old.get('status') != 'HMM_OUTPUTS_PRESERVED'):
            raise ValueError('Failed/different existing HMM evidence; root must choose new run namespace')
        require_hmm_outputs(out, old.get('output_sha256', {}))
        shutil.copyfile(out / 'hmm.tblout', Path(table))
        print('Reused verified HMM evidence for ' + assembly, file=sys.stderr)
        return 0
    argv = [str(binary), '--domtblout', str(out / 'hmm.domtblout'), *args]
    started = time.monotonic()
    with (out / 'hmm.stdout.txt').open('wb') as stdout, (out / 'hmm.stderr.txt').open('wb') as stderr:
        process = subprocess.Popen(argv, stdout=stdout, stderr=stderr)
        receipt(out / 'hmm_launch_receipt.json', {'status': 'ACTUAL_HMMSEARCH_PROCESS_STARTED',
                'utc': datetime.now(timezone.utc).isoformat(), 'wrapper_pid': os.getpid(),
                'hmmsearch_pid': process.pid, 'argv': argv, 'identity': identity,
                'scientific_validation': 'NOT_RUN'})
        exit_code = process.wait()
    output_hashes = {}
    if Path(table).is_file():
        shutil.copyfile(Path(table), out / 'hmm.tblout')
    for filename in ('hmm.tblout', 'hmm.domtblout', 'hmm.stdout.txt', 'hmm.stderr.txt'):
        path = out / filename
        if path.is_file():
            output_hashes[filename] = digest(path)
    evidence_error = None
    if exit_code == 0:
        try:
            require_hmm_outputs(out, output_hashes)
            profiles = re.findall(r'^NAME\s+(\S+)', profile.read_text(encoding='ascii'), re.M)
            queries = re.findall(r'^Query:\s+(\S+)\s+\[M=\d+\]',
                                 (out / 'hmm.stdout.txt').read_text(encoding='utf-8'), re.M)
            if queries != profiles:
                raise ValueError('HMM stdout does not account for all profile queries in exact order')
        except ValueError as e:
            evidence_error = str(e)
    receipt_status = ('HMMSEARCH_FAILED' if exit_code != 0 else
                      'HMM_EVIDENCE_INCOMPLETE' if evidence_error else 'HMM_OUTPUTS_PRESERVED')
    receipt(finished, {'status': receipt_status,
                       'scientific_validation': 'NOT_RUN', 'assembly': assembly, 'identity': identity,
                       'argv': argv, 'exit_code': exit_code,
                       'hmmsearch_pid': process.pid, 'wrapper_pid': os.getpid(),
                       'elapsed_seconds': round(time.monotonic() - started, 3),
                       'output_sha256': output_hashes, 'evidence_validation_error': evidence_error})
    if evidence_error:
        raise ValueError(evidence_error)
    return exit_code


def self_test() -> int:
    # Pure argument/key fixtures only; no biological jobs/files.
    assert option(['-i', 'x', '-w', 'GCF_000009425.1', '-o', 'y'], ('-i',)) == 'x'
    assert option(['--cpu', '2'], ('--tblout',)) is None
    try:
        option(['--tblout', 'x', '--tblout', 'y'], ('--tblout',))
    except ValueError:
        pass
    else:
        raise AssertionError('Duplicate option not rejected')
    assert re.fullmatch(r'GCF_[0-9]{9}\.[0-9]+', 'GCF_000009425.1')
    assert not re.fullmatch(r'GCF_[0-9]{9}\.[0-9]+', '../GCF_000009425.1')
    import tempfile
    with tempfile.TemporaryDirectory(prefix='gtt-evidence-synthetic-') as directory:
        fixture = Path(directory)
        (fixture / 'hmm.tblout').write_text('# synthetic tblout\n# [ok]\n', encoding='utf-8')
        (fixture / 'hmm.stdout.txt').write_text('# synthetic stdout\n', encoding='utf-8')
        (fixture / 'hmm.stderr.txt').write_text('', encoding='utf-8')
        def reject_missing(label, function):
            try:
                function()
            except ValueError:
                return
            raise AssertionError('Invalid HMM evidence accepted: ' + label)
        reject_missing('absent domtblout', lambda: require_hmm_outputs(fixture))
        (fixture / 'hmm.domtblout').write_text('# synthetic domtblout\n# [ok]\n', encoding='utf-8')
        reject_missing('receipt omits domtblout', lambda: require_hmm_outputs(
            fixture, {'hmm.tblout': digest(fixture / 'hmm.tblout')}))
        reject_missing('receipt omits stdout/stderr', lambda: require_hmm_outputs(
            fixture, {n: digest(fixture / n) for n in ('hmm.tblout', 'hmm.domtblout')}))
        recorded = {n: digest(fixture / n) for n in ('hmm.tblout', 'hmm.domtblout', 'hmm.stdout.txt', 'hmm.stderr.txt')}
        require_hmm_outputs(fixture, recorded)
        (fixture / 'hmm.domtblout').write_text('# changed synthetic table\n# [ok]\n', encoding='utf-8')
        reject_missing('changed domtblout', lambda: require_hmm_outputs(fixture, recorded))
        (fixture / 'hmm.domtblout').write_text('# truncated table\n', encoding='utf-8')
        reject_missing('missing completion trailer', lambda: require_hmm_outputs(fixture))
        prior = os.environ.get('GTT_EVIDENCE_DIR')
        os.environ['GTT_EVIDENCE_DIR'] = 'synthetic_relative_path'
        reject_missing('relative root', lambda: paths('GCF_000000001.1'))
        if prior is None:
            del os.environ['GTT_EVIDENCE_DIR']
        else:
            os.environ['GTT_EVIDENCE_DIR'] = prior
    print('PURE_ARGUMENT_AND_HMM_CACHE_FIXTURES_PASS; no biological/HMMER process executed')
    return 0


if __name__ == '__main__':
    try:
        mode, *arguments = sys.argv[1:]
        handler = {'rename': rename, 'hmmsearch': hmmsearch, '--self-test': lambda _a: self_test()}[mode]
        raise SystemExit(handler(arguments))
    except Exception as error:
        # This tool has no network/authentication responsibility; never dump environment.
        print('Evidence wrapper failure: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
