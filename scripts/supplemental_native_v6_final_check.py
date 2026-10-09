"""Supplement accepted V6 output proof; never launch science or alter native data.

Run only after the sole scientific owner has completed the four trees and the
existing V6 independent checker. This checks newly identified coverage gaps and
reuses that checker's certificate rather than reparsing 4,000 bootstrap trees.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import math
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

CHECKER_SHA256 = 'd075c4d53e506f10e328d627e2b2e24db19edb5256daa902ea610d5a06989d5d'
PARSER_SHA256 = '433e5b97fa6b90fd2e33b373f06df82abd717cb1c875e121f346c42155665efe'
NAMES = ('primary196', 'sensitivity162', 'sensitivity187_markers', 'sensitivity_complete155')
COUNTS = ((196, 100), (162, 100), (196, 88), (155, 100))
POLICY = 'EXPLICITLY_UNROOTED_NO_VALIDATED_OUTGROUP'
CAP = 3221225472
SOURCE_MEMBERS = {
    'scripts/stage04_native_windows_v6.py',
    'scripts/stage04_windows_job_v6.py',
    'scripts/stage04_windows_validate_v6.py',
    'config/host_inference_stage04_windows_v6.json',
}
REQUIRED_OUTPUTS = {
    'host.treefile', 'host.contree', 'host.log', 'host.iqtree', 'host.ufboot',
    'host.best_scheme.nex', 'unrooted.nwk', 'unrooted.nex',
    'unrooted_labeled.nwk', 'unrooted_labeled.nex', 'invocation.json',
}
REQUIRED_ATTEMPT = {'launch.json', 'exit.json', 'progress.json', 'stdout.txt', 'stderr.txt'}


def check(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            value.update(block)
    return value.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def contained(base, member):
    """Accept only normalized, contained POSIX manifest/receipt member names."""
    check(isinstance(member, str) and bool(member), 'Empty/non-text evidence member')
    parts = member.split('/')
    check('\\' not in member and ':' not in member and '\x00' not in member
          and not PurePosixPath(member).is_absolute()
          and all(part not in ('', '.', '..') for part in parts),
          'Unsafe evidence member: ' + repr(member))
    base = Path(base).resolve()
    candidate = base.joinpath(*parts)
    check(candidate.resolve().is_relative_to(base), 'Evidence path escapes root: ' + member)
    return candidate


def manifest_audit(directory, proof, required):
    manifest = proof.get('file_sha256')
    check(isinstance(manifest, dict) and required <= set(manifest),
          'Required immutable artifact/receipt omitted from manifest')
    for member, expected in manifest.items():
        path = contained(directory, member)
        check(path.is_file() and not path.is_symlink(), 'Missing/symlink immutable artifact: ' + member)
        check(isinstance(expected, str) and re.fullmatch(r'[0-9a-f]{64}', expected)
              and digest(path) == expected, 'Immutable artifact hash differs: ' + member)
    actual = set()
    for path in Path(directory).rglob('*'):
        check(not path.is_symlink(), 'Symlink in immutable output tree')
        if path.is_file() and path != Path(directory) / 'tree_complete.json':
            member = path.relative_to(directory).as_posix()
            contained(directory, member)
            actual.add(member)
    check(set(manifest) == actual, 'Immutable manifest omits/adds actual native or attempt evidence')
    return len(manifest)


def attempt_audit(directory, proof, expected_argv, exe_sha256):
    selected = proof.get('attempt')
    check(isinstance(selected, str) and re.fullmatch(r'attempt_[0-9]{4}', selected),
          'Unsafe/unknown selected attempt name')
    attempts = sorted(Path(directory).glob('attempt_*'))
    check(attempts and all(p.is_dir() and re.fullmatch(r'attempt_[0-9]{4}', p.name)
                           and not p.is_symlink() for p in attempts),
          'Missing/noncanonical attempt directory')
    successful, rows, required = [], [], set()
    for attempt in attempts:
        contained(directory, attempt.name)
        check(all((attempt / item).is_file() for item in REQUIRED_ATTEMPT),
              'Unfinished actual attempt lacks closure evidence: ' + attempt.name)
        launch, exited = read(attempt / 'launch.json'), read(attempt / 'exit.json')
        check(launch['argv'] == exited['argv'] == expected_argv,
              'Preserved attempt argv differs: ' + attempt.name)
        check(type(launch['child_pid']) is int and launch['child_pid'] > 0
              and launch['child_pid'] == exited['child_pid']
              and type(launch['child_creation_filetime']) is int
              and launch['child_creation_filetime'] > 0
              and launch['child_creation_filetime'] == exited['creation_filetime']
              == exited['child_creation_filetime'], 'Attempt PID/creation identity differs')
        check(exited['actual_launch_receipt_sha256'] == digest(attempt / 'launch.json'),
              'Attempt exit is not bound to its actual launch receipt')
        check(exited['process_exited'] is True and exited['job_active_processes'] == 0
              and exited['actual_job_process_ids'] == []
              and type(exited['exit_code']) is int
              and exited['exit_filetime'] >= launch['child_creation_filetime'],
              'Preserved attempt or descendants lack confirmed exit')
        for value in (launch, exited):
            check(value['job_bound_before_resume'] is True
                  and value['memory_kind'] == 'WINDOWS_COMMITTED_MEMORY_NOT_LINUX_RLIMIT_AS'
                  and value['process_committed_memory_cap_bytes']
                  == value['aggregate_job_committed_memory_cap_bytes'] == CAP
                  and value['job_limit_flags'] == 0x2310
                  and value['kill_child_job_on_owner_handle_close'] is True
                  and type(value['affinity_mask']) is int and value['affinity_mask'].bit_count() == 2
                  and value['allowed_logical_processors'] == 2
                  and value['actual_executable_sha256'] == exe_sha256,
                  'Preserved attempt Windows controls/tool identity differ')
        for key in ('peak_process_committed_bytes', 'peak_job_committed_bytes'):
            number = exited[key]
            check(type(number) is int and 0 <= number <= CAP, 'Invalid/exceeded actual committed-memory peak')
        for key in ('wall_seconds', 'cpu_seconds', 'job_cpu_seconds'):
            number = exited[key]
            check(type(number) in (int, float) and math.isfinite(number) and number >= 0,
                  'Invalid actual elapsed/CPU evidence')
        if exited['exit_code'] == 0:
            successful.append(attempt.name)
        required.update(attempt.name + '/' + member for member in REQUIRED_ATTEMPT)
        rows.append({'attempt': attempt.name, 'exit_code': exited['exit_code'],
                     'child_pid': launch['child_pid'],
                     'creation_filetime': launch['child_creation_filetime'],
                     'launch_sha256': digest(attempt / 'launch.json'),
                     'exit_sha256': digest(attempt / 'exit.json')})
    check(successful == [selected], 'Exactly one successful actual attempt must match selected proof')
    check(proof['actual_native_exit_sha256'] == digest(Path(directory) / selected / 'exit.json'),
          'Tree completion proof references a different native exit')
    return rows, required


def root_markers(text):
    """Read root metadata comments outside quoted labels; never regex labels."""
    comments, quote, index = [], None, 0
    while index < len(text):
        char = text[index]
        if quote:
            if char == quote:
                if index + 1 < len(text) and text[index + 1] == quote:
                    index += 1
                else:
                    quote = None
        elif char in ("'", '"'):
            quote = char
        elif char == '[':
            depth, content = 1, []
            index += 1
            while index < len(text) and depth:
                char = text[index]
                if char == '[':
                    depth += 1
                elif char == ']':
                    depth -= 1
                if depth:
                    content.append(char)
                index += 1
            check(depth == 0, 'Unclosed tree metadata comment')
            comments.append(''.join(content).strip())
            continue
        index += 1
    check(quote is None, 'Unclosed quoted tree label')
    return [match.group(1).upper() for item in comments
            if (match := re.match(r'^&\s*([RU])\s*$', item, re.I))]


def one_unrooted(path, fmt, parser):
    text = Path(path).read_text(encoding='utf-8-sig')
    markers = root_markers(text)
    check('R' not in markers, 'Explicit rooted metadata in unrooted output')
    if fmt == 'nexus':
        check(markers == ['U'], 'NEXUS export lacks exactly one explicit unrooted declaration')
    if fmt == 'nexus':
        # Bio.Nexus can misparse legal punctuation inside quoted tip labels.
        # Preserve syntax/numbers/root metadata, mask only quoted tokens, use
        # the same pinned finite parser, then restore exact decoded labels.
        masked, labels = mask_quoted_tokens(text)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                                             prefix='nexus_reader_', suffix='.nex',
                                             dir=Path(__file__).resolve().parent, delete=False) as stream:
                temporary = Path(stream.name).resolve()
                stream.write(masked)
            trees = list(parser(temporary, fmt))
            for tree in trees:
                for tip in tree.get_terminals():
                    if tip.name in labels:
                        tip.name = labels[tip.name]
        finally:
            if temporary is not None:
                check(temporary.parent == Path(__file__).resolve().parent,
                      'Unexpected temporary reader cleanup path')
                temporary.unlink(missing_ok=True)
    else:
        trees = list(parser(path, fmt))
    check(len(trees) == 1 and trees[0].rooted is False,
          'Native/exported tree is multiple or rooted')
    return trees[0]


def mask_quoted_tokens(text):
    parts, labels, index, depth = [], {}, 0, 0
    prefix = 'LABV6QUOTED_' + hashlib.sha256(text.encode('utf-8')).hexdigest()[:20] + '_'
    while index < len(text):
        char = text[index]
        if depth:
            parts.append(char)
            if char == '[':
                depth += 1
            elif char == ']':
                depth -= 1
        elif char == '[':
            depth = 1
            parts.append(char)
        elif char in ("'", '"'):
            quote, value, closed = char, [], False
            index += 1
            while index < len(text):
                char = text[index]
                if char == quote:
                    if index + 1 < len(text) and text[index + 1] == quote:
                        value.append(quote)
                        index += 2
                        continue
                    closed = True
                    break
                value.append(char)
                index += 1
            check(closed, 'Unclosed NEXUS quoted token')
            token = prefix + str(len(labels))
            while token in text or token in labels:
                token += '_'
            labels[token] = ''.join(value)
            parts.append(token)
        else:
            parts.append(char)
        index += 1
    check(depth == 0, 'Unclosed NEXUS comment')
    return ''.join(parts), labels


def labeled_audit(directory, label_rows, accessions, helpers):
    labels = {row['tree_label']: row['assembly_accession'] for row in label_rows}
    check(len(labels) == len(label_rows) == len(accessions)
          and len(set(labels.values())) == len(accessions)
          and set(labels.values()) == set(accessions), 'Frozen label map missing/duplicate/foreign join')
    native = one_unrooted(Path(directory) / 'host.treefile', 'newick', helpers.finite_tree_parse)
    names = [tip.name for tip in native.get_terminals()]
    check(len(names) == len(set(names)) == len(accessions) and set(names) == set(accessions),
          'Native reference tree exact cohort differs')
    expected_splits = helpers.split_sets(native, accessions)
    for member, fmt, mapped in (
        ('unrooted.nwk', 'newick', False), ('unrooted.nex', 'nexus', False),
        ('unrooted_labeled.nwk', 'newick', True), ('unrooted_labeled.nex', 'nexus', True),
    ):
        tree = one_unrooted(Path(directory) / member, fmt, helpers.finite_tree_parse)
        if mapped:
            for tip in tree.get_terminals():
                name = tip.name
                # Bio.Nexus can retain outer quote delimiters. Decode only a
                # quoted form that joins exactly to the accepted frozen map.
                if fmt == 'nexus' and name not in labels and isinstance(name, str) \
                        and len(name) >= 2 and name[0] == name[-1] == "'":
                    name = name[1:-1].replace("''", "'")
                check(name in labels, 'Labeled export contains a foreign/undecodable taxon')
                tip.name = labels[name]
        names = [tip.name for tip in tree.get_terminals()]
        check(len(names) == len(set(names)) == len(accessions) and set(names) == set(accessions),
              'Exported exact cohort/label membership differs: ' + member)
        check(helpers.split_sets(tree, accessions) == expected_splits,
              'Labeled/portable export changes native unrooted topology: ' + member)
    return {'labeled_and_accession_exports_verified': 4, 'exact_tips': len(accessions),
            'root_policy': POLICY}


def validate(root):
    root = Path(root).resolve()
    scripts = root / 'scripts'
    check(digest(scripts / 'stage04_windows_validate_v6.py') == CHECKER_SHA256
          and digest(scripts / 'stage04_inference_validate_v5.py') == PARSER_SHA256,
          'Reviewed V6 checker/pinned parser source drift; stop for explicit new review')
    # Import only independent checker/parser code after verifying its reviewed
    # identity. Do not import the producer or execute any biological gate/tool.
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(scripts))
    native = importlib.import_module('stage04_windows_validate_v6')
    check(Path(native.__file__).resolve() == (scripts / 'stage04_windows_validate_v6.py').resolve()
          and Path(native.V.__file__).resolve() == (scripts / 'stage04_inference_validate_v5.py').resolve()
          and native.ROOT.resolve() == root, 'Actually imported independent checker root differs')
    output = root / '.work/stage04_inference_windows_v6'
    frozen_path, adoption_path = output / 'inference_freeze.json', root / 'reports/stage04/native_windows_v6/adoption.json'
    frozen, adoption = read(frozen_path), read(adoption_path)
    identity = adoption['identity']
    check(adoption['status'] == 'REVIEWED_NATIVE_WINDOWS_V6_ADOPTED_BEFORE_TOPOLOGY'
          and frozen['adoption_sha256'] == digest(adoption_path)
          and all(frozen[key] == value for key, value in identity.items())
          and frozen['root_policy'] == POLICY, 'Native freeze/adoption binding differs')
    check(set(identity['code_sha256']) == SOURCE_MEMBERS, 'Adopted source coverage differs')
    for member, expected in identity['code_sha256'].items():
        check(digest(contained(root, member)) == expected, 'Frozen adopted source changed: ' + member)
    check(identity['config_sha256'] == identity['code_sha256']['config/host_inference_stage04_windows_v6.json'],
          'Frozen config identity differs')
    controls = root / 'reports/stage04/native_windows_v6_review/review.json'
    review = read(controls)
    check(digest(controls) == identity['actual_windows_control_review_sha256']
          and review['status'] == 'PASS_ACTUAL_WINDOWS_JOB_ASSIGN_BEFORE_RESUME_QUERYBACK_MEMORY_DENIAL_AND_AFFINITY'
          and review['biological_jobs_run'] == 0
          and review['helper_sha256'] == identity['code_sha256']['scripts/stage04_windows_job_v6.py']
          and review['test_source_sha256'] == digest(scripts / 'test_stage04_windows_job_v6.py'),
          'Existing Windows control certificate binding differs')
    # One certificate-only call closes the missing independent source/cohort
    # binding. It verifies existing hashes/certificates, never HMM/MAFFT/trees.
    accepted_source = native.source_gate()
    check(accepted_source == identity['source_identity'] == frozen['source_identity'],
          'Accepted source certificates/cohorts differ from native freeze/adoption')
    analyses = accepted_source['analyses']
    check(tuple(a['name'] for a in analyses) == NAMES
          and tuple((len(a['accessions']), len(a['markers'])) for a in analyses) == COUNTS,
          'Exact accepted four cohort/marker scopes differ')
    base_path = root / '.work/stage04_final_validation_windows_v6/validation_summary.json'
    base = read(base_path)
    check(base['status'] == 'PASS_HOST_PHYLOGENY_AND_SENSITIVITY_OUTPUT_INTEGRITY'
          and base['analyses_verified'] == 4 and base['primary_tip_ids'] == 196
          and base['checker_source_sha256'] == CHECKER_SHA256
          and base['inference_freeze_sha256'] == digest(frozen_path)
          and tuple(item['analysis'] for item in base['analyses']) == NAMES,
          'Completed four-tree independent base certificate missing/different')
    results = []
    for analysis, baseline in zip(analyses, base['analyses']):
        name = analysis['name']
        directory = output / 'analyses' / name / 'iqtree'
        proof = read(directory / 'tree_complete.json')
        check(proof['execution'] == 'NATIVE_OUTPUT_CONSTRUCTION_ONLY_INDEPENDENT_VALIDATION_REQUIRED'
              and proof['inference_freeze_sha256'] == digest(frozen_path),
              'Native completion proof/freeze differs')
        attempts, required = attempt_audit(directory, proof, native.expected_argv(frozen['executable'], name),
                                            frozen['tool_identity']['executable_sha256'])
        manifest_count = manifest_audit(directory, proof, REQUIRED_OUTPUTS | required)
        check(baseline['native_exit_sha256'] == proof['actual_native_exit_sha256']
              and baseline['file_sha256'] == proof['file_sha256']
              and baseline['tips'] == len(analysis['accessions'])
              and baseline['ufboot_trees_verified'] == 1000,
              'Reused base audit does not bind these immutable outputs/attempt')
        source = root / '.work/stage04_phylogeny_v2/analyses' / name
        with (source / 'tip_label_map.tsv').open(newline='', encoding='utf-8') as stream:
            rows = list(csv.DictReader(stream, delimiter='\t'))
        labels = labeled_audit(directory, rows, analysis['accessions'], native.V)
        with (source / 'partitions.tsv').open(newline='', encoding='utf-8') as stream:
            partitions = list(csv.DictReader(stream, delimiter='\t'))
        schemes = re.findall(r'charpartition\s+\S+\s*=\s*([^;]+);',
                             (directory / 'host.best_scheme.nex').read_text(), re.I)
        check(len(schemes) == 1, 'Missing/ambiguous selected model partition')
        assignments = [item.strip() for item in schemes[0].split(',')]
        check(len(assignments) == len(partitions)
              and all(':' in item and item.rsplit(':', 1)[0].strip() for item in assignments)
              and [item.rsplit(':', 1)[1].strip() for item in assignments]
              == [row['partition'] for row in partitions], 'Empty/different selected-model allocation')
        results.append({'analysis': name, **labels, 'manifest_members_verified': manifest_count,
                        'preserved_attempts_verified': attempts,
                        'tree_complete_sha256': digest(directory / 'tree_complete.json')})
    return {'status': 'PASS_SUPPLEMENTAL_NATIVE_V6_FINAL_EVIDENCE_COVERAGE',
            'utc': datetime.now(timezone.utc).isoformat(), 'supplemental_checker_sha256': digest(__file__),
            'base_final_validation_sha256': digest(base_path), 'base_checker_sha256': CHECKER_SHA256,
            'adoption_sha256': digest(adoption_path), 'inference_freeze_sha256': digest(frozen_path),
            'approved_primary_accessions': len(analyses[0]['accessions']), 'analyses': results,
            'new_biological_jobs_run': 0, 'bootstrap_support_audits_repeated': 0,
            'publication': 'NOT_VERIFIED_BY_THIS_SUPPLEMENT',
            'scientific_scope': 'Output provenance/coverage supplement, not model-adequacy or rooting evidence'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True,
                        help='New receipt path; must be outside immutable native tree and source directories')
    args = parser.parse_args()
    root, result_path = args.root.resolve(), args.output.resolve()
    check(not result_path.is_relative_to(root / '.work/stage04_inference_windows_v6')
          and not result_path.is_relative_to(root / 'scripts')
          and not result_path.is_relative_to(root / 'config'), 'Receipt would mutate frozen native/source data')
    check(not result_path.exists(), 'Supplemental receipt already exists; use a new explicit output path')
    value = validate(root)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation never replaces an accepted or prior failed receipt.
    with result_path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    print(value['status'])
    print(str(result_path))


if __name__ == '__main__':
    main()
