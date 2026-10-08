"""Explicit two-root migration contract. Candidate; adoption is a separate gate.

This module never launches jobs or moves files. Historical evidence is read at
its original physical root; new inference data must remain at the declared root.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

ROOTS = {
    'data_windows': r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196',
    'data_linux': '/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196',
    'historical_windows': r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196',
    'historical_linux': '/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196',
}
OLD_ADOPTION = 'reports/stage04/inference_v4_adoption.json'
OLD_ADOPTION_SHA = '3a311e8492f2832538160bd3c6a0607091dae3c73f324cc3e3f9f519e6f4c76c'
HISTORY_ROLES = {
    'source_control': '.work/stage04_controller',
    'failed_attempt': '.work/stage04_phylogeny_v2/analyses/primary196/iqtree/attempt_0001/iqtree3.command.json',
    'previous_input': '.work/stage04_inference_v3',
    'previous_control': '.work/stage04_inference_controller_v3',
    'previous_failed_attempt': '.work/stage04_inference_v3/analyses/primary196/iqtree/attempt_0001/iqtree3.command.json',
    'previous_publication': 'reports/stage04b/publication_receipt.json',
    'original_observer_source': 'scripts/stage04_linux_launcher.py',
    'host_env': '.tools/linux/host_env',
}
DATA_ROLES = {
    'alignment_input': '.work/stage04_phylogeny_v2',
    'alignment_validation': '.work/stage04_alignment_validation/validation_summary.json',
    'alignment_publication': 'reports/stage04a/publication_receipt.json',
    'input': '.work/stage04_inference_v5',
    'output': '.work/stage04_inference_v5',
    'control': '.work/stage04_inference_controller_v5',
    'final_validation': '.work/stage04_final_validation_v5',
    'config': 'config/host_inference_stage04_v5.json',
    'resource_receipt': 'reports/stage04/resumed_inference_resource_preflight_v5.json',
    'source_producer': 'scripts/stage04_phylogeny.py',
    'source_validator': 'scripts/stage04_validate.py',
    'source_controller': 'scripts/stage04_controller.py',
    'wsl_wrapper': 'scripts/wsl_project.sh',
    'producer': 'scripts/stage04_inference_v5.py',
    'producer_source': 'scripts/stage04_inference_v5.py',
    'controller_source': 'scripts/stage04_inference_controller_v5.py',
    'validator': 'scripts/stage04_inference_validate_v5.py',
    'checker_source': 'scripts/stage04_inference_validate_v5.py',
    'limit_helper': 'scripts/stage04_iqtree_limit_v4.py',
    'linux_launcher': 'scripts/stage04_linux_launcher_v4.py',
    'observer_source': 'scripts/stage04_linux_launcher_v4.py',
    'host_config': 'config/host_primary_stage03_v1.json',
    'markers': '.work/stage03_orthology_v2',
    'marker_validation': '.work/stage03_curated_validation/validation_summary.json',
    'orthology_config': 'config/host_orthology_stage03_v2.json',
    'original_markers': '.work/stage03_markers_v1',
    'original_marker_validation': '.work/stage03_marker_validation/validation_summary.json',
    'original_resource_receipt': 'reports/stage04/resource_preflight.json',
}
# These are G copies for new output/exports. Only the old gates receive C paths.
HISTORICAL_GATE_ROLES = {
    'alignment_input', 'alignment_validation', 'alignment_publication',
    'source_producer', 'source_validator', 'source_controller', 'wsl_wrapper',
    'host_config', 'original_resource_receipt', 'markers', 'marker_validation',
    'orthology_config', 'original_markers', 'original_marker_validation',
}
STATIC_COPIES = (
    'config/approval.json', 'config/approved_accessions.txt', 'config/approved_panel.tsv',
    'evidence/g0/reports/sensitivity162_accessions.txt',
    '.work/stage04_phylogeny_v2/analysis_freeze.json',
    '.work/stage04_phylogeny_v2/alignment_summary.json',
    '.work/stage04_phylogeny_v2/analysis_alignment_manifest.json',
    '.work/stage04_alignment_validation/validation_summary.json',
    'reports/stage04a/publication_receipt.json',
)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def member(root, relative):
    """Reject escape syntax and links, rather than normalize unsafe receipt keys."""
    p = PurePosixPath(relative)
    require(isinstance(relative, str) and relative and '\\' not in relative
            and ':' not in relative and not p.is_absolute()
            and all(x not in ('', '.', '..') for x in relative.split('/')),
            'Unsafe migration-relative path')
    root = Path(root).resolve()
    value = root.joinpath(*p.parts)
    for ancestor in [value, *value.parents]:
        if ancestor == root:
            break
        require(not ancestor.is_symlink() and not getattr(ancestor, 'is_junction', lambda: False)(),
                'Linked migration member is forbidden')
    resolved = value.resolve()
    require(root in resolved.parents, 'Migration member escapes its declared root')
    return resolved


def roots():
    suffix = 'windows' if os.name == 'nt' else 'linux'
    data, historical = (Path(ROOTS[key + '_' + suffix]) for key in ('data', 'historical'))
    require(data.resolve() == data and historical.resolve() == historical,
            'Declared physical roots must not resolve through another root')
    require(data != historical and data not in historical.parents and historical not in data.parents,
            'Historical and current roots must be disjoint')
    return data, historical


def normalize(args):
    data, historical = roots()
    require(args.root.resolve() == data, 'V5 executes only from the explicitly declared G data root')
    args.root = data
    for name, value in vars(args).copy().items():
        if not isinstance(value, Path) or name == 'root':
            continue
        if name in HISTORY_ROLES:
            expected = member(historical, HISTORY_ROLES[name])
            requested = value.resolve() if value.is_absolute() else member(historical, value.as_posix())
            require(requested == expected, 'Historical/tool role must retain its exact C path: ' + name)
            setattr(args, name, expected)
        else:
            require(name in DATA_ROLES, 'Unrecognized path role: ' + name)
            expected_relative = ('.work/stage04_final_validation_v5'
                                 if name == 'output' and hasattr(args, 'input') else DATA_ROLES[name])
            resolved = value.resolve() if value.is_absolute() else member(data, value.as_posix())
            require(resolved == member(data, expected_relative), 'New role must retain its exact V5 G path: ' + name)
            # Check every component rather than relying on resolve alone.
            require(member(data, resolved.relative_to(data).as_posix()) == resolved, 'Invalid G member')
            setattr(args, name, resolved)
    args.historical_root = historical
    args.workflow_lock = member(historical, '.work/workflow.lock')
    args.workflow_owner = member(historical, '.work/workflow_owner.json')
    args.bootstrap = member(historical, '.private_run/migration_runtime_v5/stage04_migration_wsl_v5.sh')
    return args


def historical_namespace(args):
    """Only this bounded namespace is passed to unchanged historical gates."""
    values = vars(args).copy()
    values['root'] = args.historical_root
    for role in HISTORICAL_GATE_ROLES:
        if role in values:
            relative = values[role].relative_to(args.root).as_posix()
            values[role] = member(args.historical_root, relative)
    for role, relative in HISTORY_ROLES.items():
        if role in values:
            require(values[role] == member(args.historical_root, relative), 'Historical role drift: ' + role)
    return SimpleNamespace(**values)


def qualified(args, path):
    path = Path(path).resolve()
    if args.root in path.parents:
        return 'data:' + path.relative_to(args.root).as_posix()
    if args.historical_root in path.parents:
        return 'historical:' + path.relative_to(args.historical_root).as_posix()
    raise ValueError('Unqualified file outside both declared namespaces')


def declared_copy_manifest(args):
    """Expected hashes come from retained evidence, never from destination labels."""
    historical = args.historical_root
    adoption_path = member(historical, OLD_ADOPTION)
    require(sha(adoption_path) == OLD_ADOPTION_SHA, 'Pinned prior adoption changed')
    adoption = read(adoption_path)
    require(len(adoption['sources']) == 27, 'Expected all27 prior adopted source records')
    result = {OLD_ADOPTION: OLD_ADOPTION_SHA}
    for row in adoption['sources']:
        name = row['path']
        require(name not in result and sha(member(historical, name)) == row['sha256'], 'Prior source changed or duplicated: ' + name)
        result[name] = row['sha256']
    for name in STATIC_COPIES:
        result[name] = sha(member(historical, name))
    manifest = read(member(historical, '.work/stage04_phylogeny_v2/analysis_alignment_manifest.json'))
    require([r['name'] for r in manifest] == ['primary196', 'sensitivity162', 'sensitivity187_markers', 'sensitivity_complete155'],
            'Four fixed source analyses required')
    for row in manifest:
        require(len(row['file_sha256']) == 12, 'Exhaustive twelve-format alignment manifest required')
        for name, expected in row['file_sha256'].items():
            relative = '.work/stage04_phylogeny_v2/analyses/' + row['name'] + '/' + name
            require(relative not in result and sha(member(historical, relative)) == expected, 'Historical alignment manifest differs')
            result[relative] = expected
    return dict(sorted(result.items()))


def migration_identity(args):
    config = read(args.config)
    require(config['migration_roots'] == ROOTS and config['migration_revision'] == 'V5_EXPLICIT_DATA_AND_HISTORICAL_ROOTS',
            'Explicit frozen migration policy missing/different')
    expected = declared_copy_manifest(args)
    for relative, digest in expected.items():
        require(sha(member(args.root, relative)) == digest, 'G copy differs from pinned historical input: ' + relative)
    support = member(args.root, 'scripts/stage04_migration_support_v5.py')
    bootstrap = member(args.root, 'scripts/stage04_migration_wsl_v5.sh')
    require(sha(support) == sha(Path(__file__)), 'Imported migration support differs from adopted G source')
    require(sha(bootstrap) == sha(args.bootstrap), 'Actual C bootstrap differs from published G source')
    return {'revision': config['migration_revision'], 'roots': ROOTS,
            'prior_adoption_sha256': OLD_ADOPTION_SHA,
            'copied_input_sha256': expected, 'support_sha256': sha(support),
            'bootstrap_sha256': sha(bootstrap),
            'workflow_lock': 'historical:.work/workflow.lock',
            'tool_prefix': 'historical:.tools/linux/host_env',
            'historical_gates': 'UNCHANGED_CHECKS_AGAINST_PHYSICAL_C_SOURCE_EVIDENCE',
            'new_native_data': 'G_INPUTS_AND_OUTPUTS_WITH_EXACT_C_TOOL_IDENTITY'}
