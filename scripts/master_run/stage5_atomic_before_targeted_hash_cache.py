#!/usr/bin/env python3
"""One approved genome, upstream Linux detectors, independent raw audit.

BUILD ONLY until actual retained WSL/toolchain/DriveFS integration is tested.
No Stage05 V7 adoption guard is imported, altered, or satisfied by this runner.
COMPLETE_VALIDATED means native search/source integrity; R-M curation is separate.
"""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
import argparse, hashlib, importlib.metadata, importlib.util, json, math, os, re, shutil, signal, sys, time
from stage5_atomic_process import (Deferred, Fatal, Retryable, Supervisor, atomic_json,
                                   check_lease, read_json, require, utc)
from stage5_work_storage import validate_storage

PINNED_PANEL = '85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6'
PINNED_ALIGNMENT = '442742d083628ab5382a10cafc422c57084cd9bde45a4f2950f15e2c199e3307'
PINNED_PARTITIONS = 'fa640e5e984b33e73a86b1ec7a7c18f7161a12252e68e9e3c6ceb2644eb7edc5'
PINNED_SOURCE_ACCEPTANCE = 'a63e9c2b987ecabaa7457d4ab26ad0d6e086cc2488066a92647e72207542de84'
PINNED_PADLOC_R = 'd21ba942e80720d80027aa1740d756322560feaeb168bfa2890640d88950d4c0'
PINNED_PADLOC_HMM = 'a03df990d47ef40d2573a04d9a0f513e70999c3b9104216e3f6656a9bef8d5da'
VERSIONS = {'mdmparis-defense-finder': '3.0.0', 'MacSyFinder': '2.1.4',
            'pyhmmer': '0.12.3', 'pyrodigal': '3.7.1'}
AMBIENT_ENV_KEYS = ('HOME','VIRTUAL_ENV','MACSY_CONF','PYTHONPATH','PYTHONHOME')
PADLOC_R_LIBRARIES = ('tidyverse','getopt','yaml','dplyr','tidyr','readr','purrr',
                     'tibble','stringr','forcats','ggplot2','lubridate')
SOURCE_FILES = {
    '.work/detector_review/build_detector_bundles.py': '75596259fbadcfb3be76d60f2ff02baac8aa69b133f5116ef38fcb889ce45f53',
    '.work/detector_review/validate_detector_bundles.py': '0551333595baf30676de6f3a53508da4b1422166dbc282d16bd46722344439fe',
    '.work/detector_review/stage05_detectors.py': '20eeb3ef8be0a6c4ee493c557d863dfad66aed34618a9ce92ddc73e8571b7723',
    '.work/detector_review/stage05_evidence.py': '7582d1a37980d89669159e3926f5b459e8d68abfde530ea0b8fc13b991d4363e',
    '.work/detector_review/native_df_scope.py': 'dd903c7bd4a186d05d1d3a65bbb5213e560c94a52fd06689a6abd9d9da1f712c',
    '.work/detector_review/native_df_posttreat.py': '27d7193036795c96370d0e2323b86c9a58aa70efdeae5dff29e4a40d2e6124aa',
    '.work/detector_review/stage05_inventory.py': 'cd55d50befb8b6529a3419e42b98c1dd7b3831203630a0010d95bb39e33896c0',
    'scripts/validate_stage05_raw_v6.py': '95efdff562db5fb0678e0c3e8ab8648c2268ddd1091dee5935957576844eabc7',
    'scripts/stage05_posttreatment_audit_v6.py': '9d2be1174e68fb1854c83b9773fb56e18005c040053a9522bd3e24cdb2735c03',
}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def safe_member(root, relative, internal_links=False):
    pure = PurePosixPath(relative)
    require(pure.parts and pure.as_posix() == relative and not pure.is_absolute()
            and '..' not in pure.parts and '\\' not in relative, 'Unsafe manifest member')
    path = root.joinpath(*pure.parts)
    require(root.resolve() in path.resolve().parents, 'Manifest member resolves outside its root')
    if not internal_links:
        require(not any(item.is_symlink() for item in [path, *list(path.parents)[:len(pure.parts)-1]]),
                'Scientific/model source symlinks are forbidden')
    return path


def check_manifest(root, members, internal_links=False):
    require(isinstance(members, dict) and members, 'Empty hash manifest')
    for relative, digest in members.items():
        require(isinstance(digest, str) and re.fullmatch('[a-f0-9]{64}', digest), 'Unfilled/invalid hash pin')
        path = safe_member(root, relative, internal_links)
        require(path.is_file() and sha(path) == digest, 'Hash drift/missing pinned member: ' + str(path))


def payload_manifest(genome, directories):
    result = {}
    for directory in directories:
        for path in sorted(directory.rglob('*')):
            if path.is_file() and path.name not in {'.runner.guard', '.guard'}:
                relative = path.relative_to(genome).as_posix()
                safe_member(genome, relative)
                result[relative] = sha(path)
    require(result, 'Empty payload cannot validate a genome job')
    return result


def load_config(path):
    value = read_json(path)
    require(value.get('schema') == 'STAGE05_ATOMIC_CONFIG_V2', 'Unknown config schema; use source-gated native V2')
    require(value.get('support_source_sha256') == SOURCE_FILES, 'Required preserved source identities differ')
    policy = value['resource_policy']
    for field in ['windows_reserve_bytes', 'incremental_windows_requirement_bytes', 'commit_requirement_bytes',
                  'linux_job_requirement_bytes', 'linux_reserve_bytes', 'minimum_disk_free_bytes',
                  'process_address_space_limit_bytes', 'sampled_rss_stop_bytes', 'lease_max_age_seconds',
                  'command_timeout_seconds', 'job_timeout_seconds', 'termination_grace_seconds', 'drain_timeout_seconds']:
        require(type(policy.get(field)) in (int, float) and math.isfinite(policy[field]) and policy[field] > 0,
                'Explicit finite positive resource policy required: ' + field)
    require(type(policy.get('resource_wait_seconds')) in (int, float) and math.isfinite(policy['resource_wait_seconds'])
            and 0 <= policy['resource_wait_seconds'] <= 1800,
            'Resource wait must be finite and no more than 30 minutes')
    require(policy.get('threads') == 2 and policy['lease_max_age_seconds'] <= 60,
            'Retained native methods use two workers; owner lease must be bounded')
    require(policy['command_timeout_seconds'] <= policy['job_timeout_seconds'] <= 86400
            and policy['termination_grace_seconds'] <= 60 and policy['drain_timeout_seconds'] <= 60,
            'Finite command/job deadlines must fit 24 hours and closure waits 60 seconds')
    return value


def approved_accession(root, accession):
    panel_path = root / 'config/approved_accessions.txt'
    panel = panel_path.read_text(encoding='ascii').split()
    require(sha(panel_path) == PINNED_PANEL and len(panel) == len(set(panel)) == 196,
            'Exact approved196 panel changed')
    require(re.fullmatch(r'GCF_[0-9]+\.[0-9]+', accession) and accession in panel,
            'Requested accession is outside the approved196 panel')
    approval = read_json(root / 'config/approval.json')
    require(approval['human_approval'] == 'APPROVED_FOR_SEQUENCE_ANALYSIS'
            and approval['approved_assembly_count'] == 196 and approval['pilot'] is False
            and approval['panel_accessions_sha256'] == PINNED_PANEL, 'Panel authorization differs')
    return panel


def validate_upstream(config, root):
    """Strict final host-tree/publication gate for join/render, not native search."""
    stage = config['stage4_primary']
    validation_path = Path(stage['validation_path'])
    publication_path = Path(stage['publication_path'])
    for path in [validation_path, publication_path]:
        require(root in path.resolve().parents and path.is_file(), 'Actual new project upstream receipt required')
    require(sha(validation_path) == stage['validation_sha256']
            and sha(publication_path) == stage['publication_sha256'], 'Stage4 accepted receipt hashes changed/unfilled')
    validation, publication = read_json(validation_path), read_json(publication_path)
    # New primary-only receipt, not a fabricated four-scope V6 certificate.
    require(validation.get('schema') == 'STAGE04_PRIMARY_ACCEPTANCE_V1'
            and validation.get('state') == 'COMPLETE_VALIDATED'
            and validation.get('approved_accessions_sha256') == PINNED_PANEL
            and validation.get('unique_tips') == 196
            and validation.get('branch_lengths_valid') is True
            and validation.get('support_completed') is True,
            'New independently accepted primary196 tree certificate incomplete')
    require(publication.get('status') == 'UPLOAD_VERIFIED'
            and publication.get('final_validation_summary_sha256') == sha(validation_path)
            and publication.get('remote_tag_commit_verified') is True
            and publication.get('assets') and all(item.get('download_readback_verified') is True
                and item.get('all_zip_member_hashes_verified') is True for item in publication['assets']),
            'Accepted primary196 publication/readback is incomplete')
    members = validation.get('files')
    require(isinstance(members, dict) and members, 'Primary acceptance lacks scientific file pins')
    check_manifest(root, members)
    freeze = validation_path.parent
    require(all(safe_member(root, name).parent == freeze for name in members),
            'Stage4 scientific certificate must bind this exact accepted project freeze')
    for name in ['primary196_host_tree.nwk', 'primary196_host_tree.nex',
                 'accepted_primary196_concatenated.faa', 'accepted_original_config.json',
                 'accepted_approved_accessions.txt']:
        relative = (freeze / name).relative_to(root).as_posix()
        require(relative in members, 'Required accepted primary artifact absent: ' + name)
    require(members[(freeze/'primary196_host_tree.nwk').relative_to(root).as_posix()]
            == validation['native_tree_sha256'], 'Authoritative accepted native tree hash differs')
    require(members[(freeze/'accepted_primary196_concatenated.faa').relative_to(root).as_posix()]
            == validation.get('accepted_alignment_sha256') == PINNED_ALIGNMENT
            and members[(freeze/'accepted_approved_accessions.txt').relative_to(root).as_posix()] == PINNED_PANEL,
            'Frozen accepted alignment/panel source bytes differ')
    if validation.get('mode') == 'partitioned':
        require(members.get((freeze/'accepted_primary196_partitions.nex').relative_to(root).as_posix())
                == PINNED_PARTITIONS, 'Frozen accepted partition bytes differ')
    else:
        require(validation.get('mode') == 'single_model', 'Unknown accepted primary analysis mode')
    return {'validation_sha256': sha(validation_path), 'publication_sha256': sha(publication_path),
            'accepted_scientific_files': members}


def accepted_source_pins():
    path = Path(__file__).with_name('stage5_accepted_source_pins.json')
    require(path.is_file() and not path.is_symlink() and sha(path) == PINNED_SOURCE_ACCEPTANCE,
            'Exact released source acceptance pins missing/changed')
    pins = read_json(path)
    require(pins.get('schema') == 'STAGE05_ACCEPTED_SOURCE_PINS_V1'
            and pins.get('approved_accessions_sha256') == PINNED_PANEL
            and len(pins.get('source_receipts', {})) == 196,
            'Exact approved196 source acceptance manifest required')
    return pins


def validate_genome_inputs(config, root, accession):
    """Reopen existing published panel/source acceptance and this genome's bytes.

    No host alignment, tree, Stage4 terminal state or Stage4 publication is read.
    Global acceptance is pinned; a self-consistently edited source receipt is
    rejected against its exact previously verified released ZIP member.
    """
    panel = approved_accession(root, accession)
    pins = accepted_source_pins()
    require(set(pins['source_receipts']) == set(panel), 'Released source panel differs')
    check_manifest(root, pins['accepted_files'])
    source_root, validation = Path(config['source']).resolve(), Path(config['source_validation']).resolve()
    require(source_root == root / '.work/source_locus_inputs_v1'
            and validation == root / '.work/stage03_source_validation/validation_summary.json',
            'Use retained accepted source roles')
    stage2 = read_json(root/'reports/stage02/validation_summary.json')
    require(stage2.get('status') == 'PASS_SEQUENCE_INTEGRITY_WITH_DOCUMENTED_EXCEPTIONS'
            and stage2.get('approved_assemblies') == stage2.get('raw_packages_present') == stage2.get('assemblies_reported') == 196
            and stage2.get('complete_exact196_accounting') is True and stage2.get('error_count') == 0
            and stage2.get('assemblies_with_errors') == 0 and stage2.get('approved_accessions_sha256') == PINNED_PANEL,
            'Accepted Stage2 sequence/package integrity differs')
    for stage, tag in [('stage02','stage02-sequences196-v1'),('stage03','stage03-hostmarkers196-v1')]:
        publication = read_json(root/'reports'/stage/'publication_receipt.json')
        require(publication.get('status') == 'UPLOAD_VERIFIED' and publication.get('release_tag') == tag
                and publication.get('approved_assemblies') == 196 and publication.get('remote_tag_commit_verified') is True
                and publication.get('assets') and all(item.get('download_readback_verified') is True
                    and item.get('all_zip_member_hashes_verified') is True for item in publication['assets']),
                'Existing accepted source release/readback differs: '+stage)
    gate = read_json(validation)
    require(gate.get('status') == 'PASS_SOURCE_LOCUS_INPUT_TRACEABILITY'
            and gate.get('assemblies_passed') == gate.get('assemblies_audited') == gate.get('required_assemblies') == 196
            and gate.get('complete_exact196_accounting') is True and gate.get('panel_sha256') == PINNED_PANEL
            and gate.get('failed_assemblies') == [] and gate.get('global_errors') == []
            and gate['builder_identity']['stage02_validation_summary_sha256']
                == pins['accepted_files']['reports/stage02/validation_summary.json'],
            'Accepted source traceability/Stage2 lineage differs')
    source = source_root/'assemblies'/accession
    witness = pins['source_receipts'][accession]
    receipt_path = safe_member(root, '.work/source_locus_inputs_v1/assemblies/'+accession+'/build_receipt.json')
    require(receipt_path.is_file() and receipt_path.stat().st_size == witness['bytes']
            and sha(receipt_path) == witness['sha256'], 'Genome source receipt differs from actual released member')
    receipt = read_json(receipt_path)
    require(receipt.get('status') == 'SOURCE_LOCUS_INPUTS_CONSTRUCTED'
            and receipt.get('assembly_accession') == accession and receipt.get('identity') == gate['builder_identity'],
            'Genome source receipt/accepted source identity differs')
    members = receipt['output_files']
    require(len({item['path'] for item in members}) == len(members), 'Duplicate source manifest member')
    check_manifest(source, {item['path']:item['sha256'] for item in members})
    require(all(type(item['bytes']) is int and safe_member(source,item['path']).stat().st_size == item['bytes'] for item in members),
            'Genome source file sizes differ from accepted receipt')
    acceptance = {'source_pins_sha256':PINNED_SOURCE_ACCEPTANCE, 'accepted_files':pins['accepted_files'],
                  'released_source_member':witness}
    return source, gate, receipt, acceptance


def genome_scientific_identity(config, accession, receipt_sha256, acceptance):
    # Operational reserves/deadlines/owner/mount proofs remain attempt receipts.
    # Changing or publishing an unrelated host tree cannot invalidate detectors.
    return {'schema':'STAGE05_SINGLE_GENOME_SCIENTIFIC_IDENTITY_V2', 'accession':accession,
            'panel_sha256':PINNED_PANEL, 'source_receipt_sha256':receipt_sha256,
            'source_validation_sha256':acceptance['accepted_files']['.work/stage03_source_validation/validation_summary.json'],
            'source_acceptance':acceptance, 'runtime_manifest_sha256':config['runtime']['manifest_sha256'],
            'support_source_sha256':SOURCE_FILES, 'runner_sha256':sha(__file__),
            'supervisor_sha256':sha(Path(__file__).with_name('stage5_atomic_process.py')),
            'storage_helper_sha256':sha(Path(__file__).with_name('stage5_work_storage.py')), 'threads':2,
            'methods':'FULL_PADLOC5027_DF3_THREE_NATIVE_FAMILIES_RAW_INTEGRITY_ONLY'}


def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def runtime_roots(config):
    return {name: Path(config['runtime'][name]).resolve() for name in ['environment_dir', 'models_dir', 'padloc_db']}


def config_presence(path):
    path = Path(path).absolute()
    require(not path.exists() or path.is_file(), 'Native config path is not a regular file: '+str(path))
    require(path.exists() or not path.is_symlink(), 'Broken native config symlink: '+str(path))
    return {'path':str(path),'resolved_path':str(path.resolve()),'present':path.is_file(),
            'sha256':sha(path) if path.is_file() else None}


def ambient_configuration(root, environment_dir):
    """Mirror installed MacSy2.1.4 Config's actual ambient lookup roles."""
    values = {name:os.environ.get(name) for name in AMBIENT_ENV_KEYS}
    for name in ['HOME','VIRTUAL_ENV','MACSY_CONF']:
        require(not values[name] or Path(values[name]).is_absolute(), 'Relative native configuration override rejected: '+name)
    home = Path('~').expanduser().resolve()
    virtual = values['VIRTUAL_ENV']
    selected = Path(virtual)/'etc/macsyfinder/macsyfinder.conf' if virtual else (
        Path(values['MACSY_CONF']) if values['MACSY_CONF'] else Path('/etc/macsyfinder/macsyfinder.conf'))
    files = {'prefix_etc':config_presence(environment_dir/'etc/macsyfinder/macsyfinder.conf'),
             'selected_system':config_presence(selected),
             'home_user':config_presence(home/'.macsyfinder/macsyfinder.conf'),
             'project_root_cwd':config_presence(root/'macsyfinder.conf')}
    require(files['project_root_cwd']['present'] is False, 'Unapproved project-root MacSy configuration present')
    return {'schema':'STAGE05_AMBIENT_NATIVE_CONFIGURATION_V1','environment':values,
            'actual_linux_home':str(home),'files':files,
            'defensefinder_cli_environment':'CLI/model-update/version-cache path NOT_INVOKED; native MacSy and post-treatment only'}


def check_ambient_configuration(manifest, root, environment_dir):
    actual = ambient_configuration(root, environment_dir)
    require(manifest.get('ambient_configuration') == actual, 'Native ambient config presence/hash/home/override changed')
    return actual


def prepare_detector_environment(environment_dir):
    # A directly executed conda Python does not activate its executable PATH.
    # Scope computation happens in this process as well as native children.
    os.environ.update(PATH=str(environment_dir/'bin')+':/usr/bin:/bin',
                      OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',
                      LC_ALL='C',PYTHONDONTWRITEBYTECODE='1')
    sys.dont_write_bytecode = True
    found = shutil.which('hmmsearch')
    require(found and Path(found).resolve() == (environment_dir/'bin/hmmsearch').resolve(),
            'In-process native scope must resolve the pinned HMMER executable')


def check_installed_package_locations(environment_dir):
    site = (environment_dir/'lib/python3.11/site-packages').resolve()
    for name in ['macsypy','defense_finder','defense_finder_posttreat','pyhmmer','pyrodigal']:
        spec = importlib.util.find_spec(name)
        require(spec is not None and spec.origin and site in Path(spec.origin).resolve().parents,
                'Actual native package import is missing/shadowed outside retained environment: '+name)


def native_configuration_guard(manifest, root, environment_dir, cwd_configs):
    def guard(args, cwd, argv):
        actual = check_ambient_configuration(manifest,root,environment_dir)
        require({name:args.environment.get(name) for name in AMBIENT_ENV_KEYS} == actual['environment'],
                'Child native configuration environment differs from pinned parent scope')
        cwd = Path(cwd).resolve()
        require(cwd in cwd_configs, 'Unapproved native command working directory')
        observed = config_presence(cwd/'macsyfinder.conf')
        require(observed['sha256'] == cwd_configs[cwd], 'Native task cwd config changed/missing/unexpected')
        found = shutil.which('hmmsearch',path=args.environment['PATH'])
        require(found and Path(found).resolve() == (environment_dir/'bin/hmmsearch').resolve(),
                'Child native HMMER resolution differs from pinned environment')
        return {'ambient_configuration_sha256':fingerprint(actual),'cwd_configuration':observed,
                'effective_native_config':'Preserved raw macsyfinder.conf and independently compared in raw audit'}
    return guard


def storage_configuration_guard(config, configuration_guard):
    def guard(args, cwd, argv):
        storage = validate_storage(config)
        return dict(configuration_guard(args, cwd, argv), work_storage=storage)
    return guard


def pin_runtime(config, output):
    """Read-only runtime discovery; writes one explicit manifest candidate only."""
    require(sys.platform == 'linux', 'Runtime pinning must inspect the actual retained Linux environment')
    roots = runtime_roots(config)
    env = roots['environment_dir']
    prepare_detector_environment(env)
    check_installed_package_locations(env)
    ambient = ambient_configuration(Path(config['root']).resolve(),env)
    require(Path(sys.executable).resolve() == (env / 'bin/python').resolve(), 'Use the retained detector interpreter')
    versions = {name: importlib.metadata.version(name) for name in VERSIONS}
    require(versions == VERSIONS, 'Installed detector package versions changed')
    env_files = {}
    for name in ['python', 'padloc', 'padloc.R', 'hmmsearch', 'macsyfinder', 'Rscript']:
        path = env / 'bin' / name
        require(path.is_file() and env in path.resolve().parents, 'Required native executable missing/outside environment')
        env_files['bin/' + name] = sha(path)
    for directory in [env / 'conda-meta', env / 'lib/python3.11/site-packages/macsypy',
                      env / 'lib/python3.11/site-packages/defense_finder',
                      env / 'lib/python3.11/site-packages/defense_finder_cli',
                      env / 'lib/python3.11/site-packages/defense_finder_posttreat']:
        require(directory.is_dir(), 'Required installed source/package receipts missing: ' + str(directory))
        for path in sorted(directory.rglob('*')):
            if path.is_file() and path.suffix in {'.py', '.json'}:
                env_files[path.relative_to(env).as_posix()] = sha(path)
    site = env/'lib/python3.11/site-packages'
    for package in ['pyhmmer','pyrodigal']:
        package_roots = [path for path in [site/package,site/(package+'.libs')] if path.is_dir()]
        require(site/package in package_roots, 'Actual native Python package directory missing: '+package)
        binaries = []
        for directory in package_roots:
            for path in sorted(directory.rglob('*')):
                if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                    env_files[path.relative_to(env).as_posix()] = sha(path)
                    if '.so' in path.name: binaries.append(path)
        for path in sorted(site.glob('*'+package+'*.so')):
            env_files[path.relative_to(env).as_posix()] = sha(path); binaries.append(path)
        require(binaries, 'Actual native extension bytes absent: '+package)
    r_versions = {}
    for package in PADLOC_R_LIBRARIES:
        description = env/'lib/R/library'/package/'DESCRIPTION'
        require(description.is_file(), 'Retained PADLOC R package metadata missing: '+package)
        match = re.search(r'^Version:\s*(\S+)',description.read_text(),re.M)
        require(match, 'Malformed retained R package version: '+package)
        r_versions[package] = match.group(1)
        env_files[description.relative_to(env).as_posix()] = sha(description)
    for path in [env/'lib/R/bin/exec/R',env/'lib/R/lib/libR.so']:
        require(path.is_file(), 'Actual retained R interpreter/library missing: '+str(path))
        env_files[path.relative_to(env).as_posix()] = sha(path)
    for path in sorted((env/'lib/R/library').glob('*/libs/*.so')):
        env_files[path.relative_to(env).as_posix()] = sha(path)
    metadata = [read_json(path) for path in (env / 'conda-meta').glob('*.json')]
    for name, version in [('padloc', '2.0.0'), ('hmmer', '3.4'), ('r-base', '4.3.1')]:
        require(any(row.get('name') == name and row.get('version') == version for row in metadata),
                'Pinned conda version missing: ' + name)
    manifests = {'environment_dir': env_files}
    for name in ['models_dir', 'padloc_db']:
        manifests[name] = {path.relative_to(roots[name]).as_posix(): sha(path)
                           for path in sorted(roots[name].rglob('*')) if path.is_file()}
        check_manifest(roots[name], manifests[name])
    require(manifests['environment_dir']['bin/padloc.R'] == PINNED_PADLOC_R
            and manifests['padloc_db']['hmm/padlocdb.hmm'] == PINNED_PADLOC_HMM,
            'Retained PADLOC source/compiled database identity changed')
    require(not output.exists(), 'Preserve an existing runtime pin candidate')
    atomic_json(output, {'schema': 'STAGE05_PINNED_RUNTIME_V1', 'versions': versions,
                         'roots': {k: str(v) for k, v in roots.items()}, 'files': manifests,
                         'ambient_configuration':ambient,'padloc_R_library_versions':r_versions,
                         'scope': 'Hash/version discovery only; execution/interoperability NOT_RUN'})


def validate_runtime(config):
    roots = runtime_roots(config)
    prepare_detector_environment(roots['environment_dir'])
    path = Path(config['runtime']['manifest_path'])
    require(path.is_file() and sha(path) == config['runtime']['manifest_sha256'], 'Actual runtime manifest missing/unfilled/changed')
    manifest = read_json(path)
    check_ambient_configuration(manifest,Path(config['root']).resolve(),roots['environment_dir'])
    require(manifest.get('schema') == 'STAGE05_PINNED_RUNTIME_V1' and manifest['versions'] == VERSIONS
            and manifest['roots'] == {k: str(v) for k, v in roots.items()}, 'Runtime manifest/version/path roles differ')
    for name, root in roots.items():
        check_manifest(root, manifest['files'][name], internal_links=(name == 'environment_dir'))
    require(manifest['files']['environment_dir']['bin/padloc.R'] == PINNED_PADLOC_R
            and manifest['files']['padloc_db']['hmm/padlocdb.hmm'] == PINNED_PADLOC_HMM, 'Pinned PADLOC identity differs')
    require({name: importlib.metadata.version(name) for name in VERSIONS} == VERSIONS,
            'Actual interpreter package versions differ')
    require(Path(sys.executable).resolve() == (roots['environment_dir'] / 'bin/python').resolve(), 'Wrong native interpreter')
    check_installed_package_locations(roots['environment_dir'])
    return roots, manifest


def load_modules(root):
    check_manifest(root, SOURCE_FILES)
    review = root / '.work/detector_review'
    sys.path[:0] = [str(review), str(root / 'scripts')]
    modules = {}
    for name, filename in [('builder', 'build_detector_bundles.py'), ('bundle_checker', 'validate_detector_bundles.py'),
                           ('native', 'stage05_detectors.py'), ('inventory', 'stage05_inventory.py')]:
        modules[name] = import_file('stage5_retained_' + name, review / filename)
    modules['raw_checker'] = import_file('stage5_retained_raw_checker', root / 'scripts/validate_stage05_raw_v6.py')
    for name in ['stage05_evidence', 'native_df_scope']:
        require(Path(sys.modules[name].__file__).resolve().parent == review, 'Imported support code shadowed: ' + name)
    return modules


def next_directory(root, stem):
    root.mkdir(parents=True, exist_ok=True)
    numbers = [int(path.name.rsplit('_', 1)[1]) for path in root.glob(stem + '_*') if path.is_dir()]
    path = root / (stem + '_' + str(max(numbers, default=0) + 1).zfill(4))
    path.mkdir()
    return path


def run_genome(config, accession, lease_path, owner_nonce):
    import fcntl, resource
    require(sys.platform == 'linux', 'This runner executes upstream Linux tools on WD only')
    storage = validate_storage(config)  # Before directories, cache reads or closure adoption.
    root = Path(config['root']).resolve()
    approved_accession(root, accession)
    output_root = Path(config['output_root']).resolve()
    require(root in output_root.parents and '.work' in output_root.relative_to(root).parts
            and 'stage05_atomic_v1' in output_root.parts, 'Separate new project Stage5 output namespace required')
    source_root, source_validation = Path(config['source']).resolve(), Path(config['source_validation']).resolve()
    require(source_root == root / '.work/source_locus_inputs_v1'
            and source_validation == root / '.work/stage03_source_validation/validation_summary.json', 'Use retained accepted source roles')
    genome = output_root / accession
    genome.mkdir(parents=True, exist_ok=True)
    # Serial native runner plus genome guard. Caller separately owns the actual
    # stable Windows workflow lock; Linux flock is not claimed to prove it.
    with (output_root / '.native_runner.guard').open('a+b') as global_guard, (genome / '.guard').open('a+b') as guard:
        for stream in [global_guard, guard]:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise Fatal('Another native Stage5 owner holds the runner/genome guard') from error
        transaction = next_directory(genome / 'transactions', 'attempt')
        transaction_relative = transaction.relative_to(genome).as_posix()
        status_path = transaction / 'status.json'
        began = time.monotonic()
        supervisor = None
        stable_identity = None
        prior_closure_checked = False
        def deadline(signum, frame):
            raise Retryable('Atomic genome job runtime deadline expired')
        old_alarm, old_term, old_int = signal.getsignal(signal.SIGALRM), signal.getsignal(signal.SIGTERM), signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGALRM, deadline)
        signal.signal(signal.SIGTERM, deadline)
        signal.signal(signal.SIGINT, deadline)
        signal.setitimer(signal.ITIMER_REAL, config['resource_policy']['job_timeout_seconds'])
        try:
            lease = check_lease(lease_path, owner_nonce, config['resource_policy'])
            atomic_json(transaction / 'initial_owner_lease.json', lease)
            atomic_json(transaction / 'work_storage_proof.json', storage)
            supervisor = Supervisor(lease_path, owner_nonce, config['resource_policy'], genome, sha)
            # A crashed job on a different genome must not release admission
            # for another child merely because its Python flock disappeared.
            for prior in output_root.glob('*/execution/**/*.launch_intent.json'):
                supervisor.assert_intent_closed(prior)
            for prior in output_root.glob('*/execution/**/*.launch.json'):
                supervisor.assert_closed(read_json(prior))
            prior_closure_checked = True
            supervisor.admission(transaction)
            source, gate, source_receipt, acceptance = validate_genome_inputs(config, root, accession)
            roots, runtime = validate_runtime(config)
            modules = load_modules(root)
            supervisor.check_owner()
            stable_identity = genome_scientific_identity(config, accession, sha(source/'build_receipt.json'), acceptance)
            identity_sha = fingerprint(stable_identity)
            complete_path = genome / 'complete.json'
            if complete_path.exists():
                complete = read_json(complete_path)
                require(complete.get('state') == 'COMPLETE_VALIDATED' and complete['scientific_identity'] == stable_identity,
                        'Completed genome scientific/code/model/policy identity changed')
                check_manifest(genome, complete['files'])
                for path in (genome / 'execution').rglob('*.launch.json'):
                    supervisor.assert_closed(read_json(path))
                check_ambient_configuration(runtime,root,roots['environment_dir'])
                validate_storage(config)
                supervisor.check_owner()
                result = {'state': 'COMPLETE_VALIDATED', 'accession': accession, 'cache': 'HASH_VERIFIED_REUSED',
                          'complete_receipt_sha256': sha(complete_path), 'curation': 'NOT_RUN',
                          'owner_nonce': owner_nonce, 'transaction': transaction_relative, 'owned_closure_proven': True}
                atomic_json(status_path, result)
                atomic_json(genome/'status.json',result)
                return result
            identity_path = genome / 'scientific_identity.json'
            if identity_path.exists():
                require(read_json(identity_path) == stable_identity, 'Unfinished genome namespace identity changed; preserve and use a new version')
            else:
                atomic_json(identity_path, stable_identity)
            bundle_root = genome / 'bundle'
            modules['builder'].resume_one(source, bundle_root, accession, identity_sha)
            bundle = bundle_root / 'assemblies' / accession
            bundle_audit = next_directory(genome / 'bundle_audit', 'attempt')
            modules['bundle_checker'].audit_one(source, bundle, bundle_audit)
            # Runtime limits apply to this dedicated Python process and its
            # children. RLIMIT_AS is per-process, not an aggregate kernel cap.
            policy = config['resource_policy']
            resource.setrlimit(resource.RLIMIT_AS, (int(policy['process_address_space_limit_bytes']),) * 2)
            cpus = sorted(os.sched_getaffinity(0))[:2]
            require(cpus, 'No permitted logical CPUs')
            os.sched_setaffinity(0, cpus)
            native = modules['native']
            native.execute, native.fresh_attempt, native.assert_dead = supervisor.execute, supervisor.fresh_attempt, supervisor.assert_closed
            execution = genome / 'execution'
            execution.mkdir(exist_ok=True)
            profiles = []
            for path in sorted((roots['padloc_db'] / 'hmm').glob('*.hmm')):
                if path.name == 'padlocdb.hmm':
                    continue
                text = path.read_text().splitlines()
                profiles.append({'query_name': next(line.split(maxsplit=1)[1] for line in text if line.startswith('NAME ')),
                                 'length': int(next(line.split()[1] for line in text if line.startswith('LENG '))),
                                 'profile_path': str(path), 'profile_sha256': sha(path)})
            require(len(profiles) == len({item['query_name'] for item in profiles}) == 5027, 'Active PADLOC scope changed')
            frozen = {'scientific_identity': stable_identity, 'panel_sha256': PINNED_PANEL, 'threads': 2,
                      'padloc_profiles': profiles, 'versions': VERSIONS,
                      'tools': {Path(name).name: digest for name, digest in runtime['files']['environment_dir'].items() if name.startswith('bin/')},
                      'padloc_metadata_system_files': {name: digest for name, digest in runtime['files']['padloc_db'].items() if not name.endswith('.hmm')},
                      'native_df_model_files': runtime['files']['models_dir']}
            freeze_path = execution / 'execution_freeze.json'
            if freeze_path.exists():
                require(read_json(freeze_path) == frozen, 'Native per-genome scientific freeze changed')
            else:
                atomic_json(freeze_path, frozen)
            freeze_sha = sha(freeze_path)
            args = SimpleNamespace(root=root, output=execution, freeze_sha=freeze_sha, padloc_profiles=profiles,
                                   tools=frozen['tools'], **roots)
            args.environment = dict(os.environ, PATH=str(roots['environment_dir'] / 'bin') + ':/usr/bin:/bin',
                                    OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2', LC_ALL='C', PYTHONDONTWRITEBYTECODE='1')
            cwd_configs = {root:None}
            bundle_pins = {item['path']:item['sha256'] for item in read_json(bundle/'bundle_receipt.json')['output_files']}
            for task in read_json(bundle/'detector_task_manifest.json'):
                if task['tool'] == 'DefenseFinder':
                    folder = safe_member(bundle,task['task']).resolve()
                    relative = task['task']+'/macsyfinder.conf'
                    require(relative in bundle_pins and sha(folder/'macsyfinder.conf') == bundle_pins[relative],
                            'Task config differs from independently audited bundle')
                    cwd_configs[folder] = bundle_pins[relative]
            supervisor.prelaunch_check = storage_configuration_guard(config,
                native_configuration_guard(runtime,root,roots['environment_dir'],cwd_configs))
            rows = native.E.table(bundle / 'locus_crosswalk.tsv')
            proteins = [row for row in rows if row['protein_target_present'] == 'True']
            require(proteins, 'Genome has no validated protein targets; cannot claim successful screening')
            native_directory = execution / 'assemblies' / accession
            native.run_padloc(args, bundle, native_directory / 'padloc', {row['padloc_bundle_target_id']: row for row in proteins})
            tasks = [task for task in read_json(bundle / 'detector_task_manifest.json') if task['tool'] == 'DefenseFinder']
            require(tasks, 'No boundary-safe DefenseFinder task')
            for task in tasks:
                mapping = {row['df_bundle_target_id']: row for row in proteins if row['df_bundle_task'] == task['task']}
                native.run_df(args, bundle / task['task'], native_directory / task['task'], mapping, task['db_type'])
            inventory_root = next_directory(genome / 'inventory', 'attempt')
            inventory_dir = inventory_root / 'assemblies' / accession
            inventory = modules['inventory']
            roles = inventory.rm_role_map(roots['padloc_db'] / 'model_role_manifest.tsv')
            metadata = {row['hmm.name']: row for row in native.E.table(roots['padloc_db'] / 'hmm_meta.txt')}
            summary = inventory.inventory_one(bundle, native_directory, inventory_dir, frozen, freeze_sha, roles, metadata)
            require(summary['padloc_complete'] and summary['defensefinder_complete'], 'Inventory lacks complete native search')
            atomic_json(inventory_root / 'summary.json', summary)
            checker = modules['raw_checker']
            scopes = checker.model_scopes(roots['models_dir'], frozen)
            audit_args = SimpleNamespace(source=source_root, bundle=bundle_root, execution=execution,
                                         inventory=inventory_root, padloc_db=roots['padloc_db'])
            report = checker.audit_assembly(audit_args, accession, frozen, freeze_sha, scopes, gate, roles, metadata, checker.Hasher())
            require(report['status'] == 'PASS_FULL_NATIVE_SEARCH_AND_SOURCE_ACCOUNTING_ONLY'
                    and report['architecture_curation'] == 'NOT_RUN', 'Independent raw audit incomplete')
            raw_audit = next_directory(genome / 'raw_validation', 'attempt')
            atomic_json(raw_audit / 'validation.json', report)
            # Reopen every launch closure before any genome success checkpoint.
            for path in execution.rglob('*.launch.json'):
                supervisor.assert_closed(read_json(path))
            check_ambient_configuration(runtime,root,roots['environment_dir'])
            validate_storage(config)
            supervisor.check_owner()
            result = {'schema': 'STAGE05_ATOMIC_GENOME_COMPLETE_V1',
                      'state': 'COMPLETE_VALIDATED', 'accession': accession, 'scientific_identity': stable_identity,
                      'scientific_identity_sha256': identity_sha,
                      'inventory_directory': inventory_dir.relative_to(genome).as_posix(),
                      'raw_validation_file': (raw_audit/'validation.json').relative_to(genome).as_posix(),
                      'validation_scope': 'NATIVE_SEARCH_SOURCE_AND_RAW_INTEGRITY_ONLY', 'curation': 'NOT_RUN',
                      'biological_absence_claim': 'NONE', 'utc': utc(),
                      'files': payload_manifest(genome, [bundle_root, execution, bundle_audit, inventory_root, raw_audit])}
            atomic_json(complete_path, result)
            atomic_json(status_path, {'state': result['state'], 'accession': accession, 'utc': utc(),
                                      'curation': 'NOT_RUN', 'elapsed_seconds': time.monotonic() - began,
                                      'complete_receipt_sha256': sha(complete_path), 'owner_nonce': owner_nonce,
                                      'transaction': transaction_relative, 'owned_closure_proven': True})
            atomic_json(genome/'status.json',read_json(status_path))
            return {'state': result['state'], 'accession': accession, 'curation': 'NOT_RUN', 'receipt': str(complete_path)}
        except BaseException as error:
            if isinstance(error, Deferred):
                state = 'DEFERRED_RESOURCE'
            elif isinstance(error, Fatal):
                state = 'FAILED_FATAL'
            elif isinstance(error, Retryable):
                state = 'FAILED_RETRYABLE'
            else:
                state = 'FAILED_FATAL'
            result = {'state': state, 'accession': accession, 'utc': utc(), 'error': type(error).__name__ + ': ' + str(error),
                      'elapsed_seconds': time.monotonic() - began, 'curation': 'NOT_RUN', 'biological_absence_claim': 'NONE',
                      'outputs_preserved': True, 'scientific_identity': stable_identity, 'owner_nonce': owner_nonce,
                      'transaction': transaction_relative,
                      'owned_closure_proven': bool(prior_closure_checked and supervisor
                                                  and not supervisor.closure_unproven),
                      'no_native_launch_in_this_invocation': not (supervisor and supervisor.native_launch_count)}
            atomic_json(status_path, result)
            atomic_json(genome/'status.json',result)
            return result
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_alarm)
            signal.signal(signal.SIGTERM, old_term)
            signal.signal(signal.SIGINT, old_int)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    subparsers = parser.add_subparsers(dest='mode', required=True)
    pin = subparsers.add_parser('pin-runtime', help='Hash retained runtime/models only; no scientific search')
    pin.add_argument('--output', type=Path, required=True)
    run = subparsers.add_parser('run')
    run.add_argument('--accession', required=True)
    run.add_argument('--owner-lease', type=Path, required=True)
    run.add_argument('--owner-nonce', required=True)
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        if args.mode == 'pin-runtime':
            pin_runtime(config, args.output.resolve())
            result = {'state': 'COMPLETE_VALIDATED', 'scope': 'RUNTIME_HASH_DISCOVERY_ONLY_NOT_BIOLOGY', 'manifest': str(args.output)}
        else:
            result = run_genome(config, args.accession, args.owner_lease.resolve(), args.owner_nonce)
    except BaseException as error:
        result = {'state': 'FAILED_FATAL', 'error': type(error).__name__ + ': ' + str(error), 'biological_absence_claim': 'NONE'}
    print(json.dumps(result, indent=2))
    return {'COMPLETE_VALIDATED': 0, 'DEFERRED_RESOURCE': 75, 'FAILED_RETRYABLE': 1, 'FAILED_FATAL': 2}[result['state']]


if __name__ == '__main__':
    raise SystemExit(main())
