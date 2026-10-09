#!/usr/bin/env python3
"""Independent closed-genome R-M curation acceptance; no final-panel acceptance.

Reuses the frozen independent checker's complete outer source/runtime/dependency
gates and atomic_one. No producer import, detector launch or final-tree input.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import time

HERE = Path(__file__).resolve().parent
CHECKER_SHA = '89a42d63401ef1ef3479690546a3c8cad4da679517aa2ed7da6b4e6716b6af0c'
PRODUCER_SHA = '20e860b58737e74061a0e7a8b4c8ac21a8e6d95aa1a0685cfbc5bc54ced0deb0'
TYPES = ('I', 'II', 'III', 'IV')


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def objsha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def load_checker():
    path = HERE / 'validate_atomic_curation.py'
    require(sha(path) == CHECKER_SHA, 'Frozen independent checker source changed')
    spec = importlib.util.spec_from_file_location('pinned_independent_atomic_genome_checker', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(sha(path) == CHECKER_SHA, 'Independent checker source drifted during loading')
    return module


def contract_from_settings(settings, accession, V):
    require(settings.get('schema') == 'RM_CURATION_AUDIT_SETTINGS_V1' and settings.get('dataset_kind') == 'PRODUCTION',
            'Actual production audit settings required')
    approved = Path(settings['approved'])
    panel = approved.read_text(encoding='ascii').split()
    require(sha(approved) == V.PANEL_SHA and len(panel) == len(set(panel)) == 196 and accession in panel,
            'Selected accession must belong to exact frozen approved196 panel')
    require(accession not in settings.get('exception_records', {}), 'Selected genome must be closed complete, not an exception')
    keys = ('root', 'source', 'source_validation', 'approved', 'policy', 'models', 'padloc_db', 'environment', 'reviews', 'producer_source')
    contract = {key: settings[key] for key in keys}
    contract.update(schema='RM_ATOMIC_INDEPENDENT_CURATION_CHECK_V1', dataset_kind='PRODUCTION', producer_sha256=sha(settings['producer_source']))
    require(contract['producer_sha256'] == PRODUCER_SHA, 'Exact reviewed curation producer source changed')
    for key in ('atomic_runner', 'supervisor'):
        contract[key + '_source'] = settings[key + '_source']
        contract[key + '_sha256'] = sha(settings[key + '_source'])
    contract['runtime_manifest'] = settings.get('runtime_manifest')
    require(contract['runtime_manifest'], 'Actual pinned native runtime manifest required')
    contract['runtime_manifest_sha256'] = sha(contract['runtime_manifest'])
    directory = Path(settings['review_directory']) / accession
    entry = dict(accession=accession, genome=str(Path(settings['genome_root']) / accession),
                 prepared=str(directory / 'prepare/prepared.json'), review=str(directory / 'executed_review.json'),
                 result=str(directory / 'apply/curated_candidate.json'))
    return panel, contract, entry


def outer_gates(panel, contract, V):
    """Same mandatory outer gates as the frozen full196 checker run()."""
    C = V.core()
    require(sha(HERE / 'pinned_model_candidate_scope.json') == V.SCOPE_SHA, 'Exact model lookup changed')
    require(sha(contract['approved']) == V.PANEL_SHA and len(panel) == len(set(panel)) == 196,
            'Exact approved196 panel changed')
    source_validation = V.read(contract['source_validation'])
    require(sha(contract['source_validation']) == V.SOURCE_VALIDATION_SHA
            and source_validation.get('status') == 'PASS_SOURCE_LOCUS_INPUT_TRACEABILITY'
            and source_validation.get('complete_exact196_accounting') is True
            and source_validation.get('panel_sha256') == V.PANEL_SHA and source_validation.get('assemblies_passed') == 196,
            'Accepted source traceability receipt changed')
    require(sha(contract['producer_source']) == contract['producer_sha256'] == PRODUCER_SHA,
            'Exact reviewed producer source changed')
    for name, digest in V.DEPENDENCY_PINS.items():
        require(sha(HERE / name) == digest, 'Retained producer dependency changed: ' + name)
    runtime_sha = V.native_provenance(contract)  # Actual versions, root agreement, all runtime/model bytes, runner/supervisor pins.
    return C, runtime_sha


def exact_four(cells, accession, C):
    require(len(cells) == 4 and {(row['assembly_accession'], row['rm_type']) for row in cells}
            == {(accession, t) for t in TYPES} and all(row['state'] in C.STATES for row in cells),
            'Independent selected-genome four-cell product differs')


def run(settings_path, accession):
    began = time.perf_counter()
    V = load_checker()
    settings_sha = sha(settings_path)
    settings = V.read(settings_path)
    panel, contract, entry = contract_from_settings(settings, accession, V)
    C, runtime_sha = outer_gates(panel, contract, V)
    pinned = {name: sha(path) for name, path in entry.items() if name in ('prepared', 'review', 'result')}
    complete_path = Path(entry['genome']) / 'complete.json'
    complete_sha = sha(complete_path)
    cells, audit = V.atomic_one(entry, contract, C)  # Reopens source/native/domain/reviews and every manifest-pinned launch+closure.
    exact_four(cells, accession, C)
    require(all(sha(entry[name]) == digest for name, digest in pinned.items()) and sha(complete_path) == complete_sha
            and sha(settings_path) == settings_sha and sha(HERE / 'validate_atomic_curation.py') == CHECKER_SHA,
            'Selected immutable scientific/control input drifted during independent check')
    manifest = dict(schema='RM_SINGLE_GENOME_INDEPENDENT_CURATION_SOURCE_MANIFEST_V1', dataset_kind='PRODUCTION',
                    accession=accession, settings_sha256=settings_sha, contract=contract, contract_sha256=objsha(contract),
                    entry=entry, audit=audit, approved_sha256=V.PANEL_SHA, approved_accession_count=196,
                    source_validation_sha256=V.SOURCE_VALIDATION_SHA, runtime_manifest_sha256=runtime_sha,
                    producer_sha256=PRODUCER_SHA, independent_checker_sha256=CHECKER_SHA,
                    independent_core_sha256=V.CORE_SHA, candidate_scope_sha256=V.SCOPE_SHA,
                    wrapper_sha256=sha(__file__), functional_activity_claim='NONE', biological_searches_repeated=0)
    receipt = dict(schema='RM_SINGLE_GENOME_INDEPENDENT_CURATION_ACCEPTANCE_V1',
                   status='PASS_INDEPENDENT_SINGLE_GENOME_RM_CURATION', dataset_kind='PRODUCTION', accession=accession,
                   accepted_single_genome_curation=True, accession_count=1, cell_count=4, approved_accession_count=196,
                   approved_sha256=V.PANEL_SHA, complete_receipt_sha256=complete_sha,
                   independent_checker_sha256=CHECKER_SHA, wrapper_sha256=sha(__file__),
                   per_genome_owned_native_closure_verified=True,
                   operational_closure_scope='SELECTED_GENOME_MANIFEST_PINNED_LINUX_NATIVE_LAUNCHES_ONLY',
                   full_panel_complete=False, final_matrix_acceptance=False, final_figure_acceptance=False,
                   functional_activity_claim='NONE', biological_searches_repeated=0, elapsed_seconds=time.perf_counter()-began,
                   evidence_limit='Four cells independently reconstructed from actual closed source/native/domain/review evidence. Final196/784 audit and accepted-tree join/render gates remain mandatory.')
    return receipt, manifest, cells


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--accession', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Preserve prior independent audit namespace')
    try:
        receipt, manifest, cells = run(args.settings, args.accession)
        code = 0
    except Exception as error:
        receipt = dict(schema='RM_SINGLE_GENOME_INDEPENDENT_CURATION_ACCEPTANCE_V1',
                       status='FAIL_INDEPENDENT_SINGLE_GENOME_RM_CURATION', accession=args.accession,
                       accepted_single_genome_curation=False, full_panel_complete=False, final_matrix_acceptance=False,
                       error=type(error).__name__ + ': ' + str(error), biological_searches_repeated=0)
        manifest = cells = None
        code = 1
    args.output.mkdir(parents=True)
    if cells is not None:
        target = args.output / 'independently_reconstructed_cells.json'
        target.write_text(json.dumps(cells, indent=2) + '\n', encoding='utf-8')
        receipt['cells_sha256'] = sha(target)
    if manifest is not None:
        target = args.output / 'single_genome_source_manifest.json'
        target.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        receipt['source_manifest_sha256'] = sha(target)
    (args.output / 'single_genome_curation_validation.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(receipt['status'])
    return code


if __name__ == '__main__':
    raise SystemExit(main())
