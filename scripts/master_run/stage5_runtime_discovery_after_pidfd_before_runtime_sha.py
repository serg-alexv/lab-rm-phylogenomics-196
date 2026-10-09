#!/usr/bin/env python3
"""Pinned read-only runtime discovery, independent of unset job budgets.

Default: inspect this C deployment's fixed control bytes and print NOT_RUN.
--discover: Linux only; call the existing runner's hash/version discovery.
Never calls load_config, run_genome, a shell, WSL, installation or inference.
"""
from pathlib import Path
import argparse
import hashlib
import importlib
import json
import re
import sys

sys.dont_write_bytecode = True
WORK = Path('/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work')
ROOT = '/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196'
TOOLS = '/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux'
PINS = {
    'stage5_atomic.py': '2d7414fd33fe6216b95cfd549cee743d8b7057db698aced509f9a7ffefa77fc0',
    'stage5_atomic_process.py': 'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e',
    'stage5_work_storage.py': '7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f',
    'stage5_accepted_source_pins.json': 'a63e9c2b987ecabaa7457d4ab26ad0d6e086cc2488066a92647e72207542de84',
    'stage5_atomic_config.template.json': '94137787139276a70cd10e0c85e13597c860950c2fba04c5c05580601ddc11cf',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def controls(directory):
    """Read only five exact reviewed deployment files; never import runtime."""
    for name, digest in PINS.items():
        path = directory / name
        require(path.is_file() and not path.is_symlink() and sha(path) == digest,
                'Missing/changed reviewed discovery input: ' + name)
    value = json.loads((directory / 'stage5_atomic_config.template.json').read_text())
    expected = {'environment_dir': TOOLS + '/detector_env',
                'models_dir': TOOLS + '/defense_models', 'padloc_db': TOOLS + '/padloc_db'}
    require(value.get('schema') == 'STAGE05_ATOMIC_CONFIG_V2'
            and value.get('root') == ROOT and value.get('source') == ROOT + '/.work/source_locus_inputs_v1'
            and value.get('source_validation') == ROOT + '/.work/stage03_source_validation/validation_summary.json'
            and value.get('output_root') == ROOT + '/.work/stage05_atomic_v1'
            and all(value['runtime'].get(k) == v for k, v in expected.items()),
            'Exact V2 source/runtime discovery path roles required')
    return value


def output_path(value):
    path = Path(value)
    require(path.is_absolute() and '..' not in path.parts and str(path) == path.as_posix()
            and path.parent == WORK and path.resolve() == path
            and re.fullmatch(r'stage5_runtime_actual_[A-Za-z0-9_]+\.json', path.name),
            'Use a new direct C-work stage5_runtime_actual_<unique>.json path')
    require(not path.exists() and not path.is_symlink(), 'Preserve existing discovery outputs')
    require(path.parent.is_dir(), 'Existing C work bridge required')
    return path


def discover(directory, config, output):
    require(sys.platform == 'linux', 'Actual discovery requires the mounted retained Linux interpreter')
    require(directory == WORK and directory.resolve() == WORK, 'Use the exact reviewed C-mounted deployment')
    output = output_path(output)
    # Import only after fixed source bytes pass. Plain CLI execution starts with
    # this directory on sys.path. Reject a preloaded/shadowed module as well.
    runner = importlib.import_module('stage5_atomic')
    for name in ['stage5_atomic', 'stage5_atomic_process', 'stage5_work_storage']:
        loaded = Path(sys.modules[name].__file__).resolve()
        require(loaded == directory / (name + '.py') and sha(loaded) == PINS[name + '.py'],
                'Discovery module import shadowed/changed: ' + name)
    require(config['support_source_sha256'] == runner.SOURCE_FILES,
            'Reviewed retained helper identities changed')
    controls(directory)
    runner.pin_runtime(config, output)
    controls(directory)
    value = json.loads(output.read_text())
    require(value.get('schema') == 'STAGE05_PINNED_RUNTIME_V1'
            and value.get('scope') == 'Hash/version discovery only; execution/interoperability NOT_RUN',
            'Unexpected runtime discovery result scope')
    return {'state': 'RUNTIME_HASH_DISCOVERY_ONLY', 'scientific_execution': 'NOT_RUN',
            'output': str(output), 'sha256': sha(output), 'discovery_control_sha256': PINS}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--discover', action='store_true', help='Inspect actual mounted Linux runtime; no detector launch')
    parser.add_argument('--output', help='New direct C-mounted work JSON; required only for --discover')
    args = parser.parse_args(argv)
    directory = Path(__file__).resolve().parent
    config = controls(directory)
    if not args.discover:
        result = {'state': 'PREPARED_NOT_RUN', 'scope': 'READ_ONLY_RUNTIME_HASH_DISCOVERY_ENTRYPOINT',
                  'discovery_control_sha256': PINS,
                  'runtime_roots': {k: config['runtime'][k] for k in ['environment_dir', 'models_dir', 'padloc_db']},
                  'resource_policy': 'UNFILLED_JOB_POLICY_IS_NOT_USED_OR_ADOPTED_BY_DISCOVERY',
                  'actual_runtime': 'NOT_RUN', 'native_execution': 'NOT_RUN'}
    else:
        require(args.output, '--discover requires --output')
        result = discover(directory, config, args.output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
