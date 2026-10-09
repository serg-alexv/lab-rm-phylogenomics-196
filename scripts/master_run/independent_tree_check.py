"""Independent acceptance of native IQ-TREE outputs; no inference or plotting."""
from pathlib import Path
import argparse
import hashlib
from io import StringIO
import json
import math
import re
import shutil
import datetime as dt
from Bio import Phylo
import Bio

ALIGNMENT = '442742d083628ab5382a10cafc422c57084cd9bde45a4f2950f15e2c199e3307'
PANEL = '85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6'
PARTITIONS = 'fa640e5e984b33e73a86b1ec7a7c18f7161a12252e68e9e3c6ceb2644eb7edc5'
EXECUTABLE = '43c9bf3b0dc5e7d88c183a2582369d22c9d692b7585350038769334bb6fd9aed'
CANONICAL_COMMIT = '160498a6af156b563c7680910945da13b4d245c0'

def require(value, message):
    if not value:
        raise ValueError(message)

def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write_certificate_and_manifest(directory, record):
    """Certificate pins scientific files; distribution manifest also pins it."""
    report = directory/'independent_validation.json'
    manifest = directory/'input_output_sha256_manifest.tsv'
    report.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
    manifest.write_text('path\tsha256\tbytes\n'+''.join(
        f'{p.name}\t{digest(p)}\t{p.stat().st_size}\n' for p in sorted(directory.iterdir())
        if p.is_file() and p != manifest),encoding='utf-8',newline='\n')

def command_binding(cfg, launch, attempt, approved_path, config_source):
    """Check the actual original config, inputs and complete exact command.

    The producer persisted a copy augmented with _config_sha256; that copy's
    byte hash is intentionally different from the original launch input.
    """
    attempt = attempt.resolve()
    source = load(config_source)
    require(digest(config_source) == cfg.get('_config_sha256') == launch.get('config_sha256'),
            'Original config/retained launch hash differs')
    require(source == {key:value for key,value in cfg.items() if key != '_config_sha256'},
            'Persisted configuration differs from actual original config')
    require(cfg.get('schema') == 'LAB_RM_ATOMIC_IQTREE_V1' and cfg.get('mode') in ('partitioned','single_model'),
            'Unknown native configuration schema/mode')
    require(cfg.get('canonical_commit') == CANONICAL_COMMIT
            and launch.get('authority',{}).get('canonical_commit') == CANONICAL_COMMIT,
            'Accepted canonical continuation commit differs')
    require(cfg.get('threads') == 2 and cfg.get('seed') == 1961008, 'Config scientific thread/seed differs')
    require(Path(cfg['output_directory']).resolve() == attempt
            and Path(launch['cwd']).resolve() == attempt, 'Actual output directory/cwd differs')
    require(Path(cfg['approved_accessions']['path']).resolve() == approved_path.resolve()
            and cfg['approved_accessions']['sha256'] == PANEL, 'Configured approved panel differs')
    exe, alignment = Path(cfg['executable']['path']).resolve(), Path(cfg['alignment']['path']).resolve()
    require(digest(exe) == cfg['executable']['sha256'] == launch.get('executable_sha256') == EXECUTABLE,
            'Pinned actual executable bytes differ')
    require(Path(launch['native']['executable']).resolve() == exe, 'Retained native executable image differs')
    require(digest(alignment) == cfg['alignment']['sha256'] == ALIGNMENT, 'Accepted alignment provenance differs')
    expected = [str(exe),'-s',str(alignment),'--seqtype','AA']
    sources = {'alignment': {'path':str(alignment),'sha256':ALIGNMENT},
               'executable': {'path':str(exe),'sha256':EXECUTABLE},
               'original_config': {'path':str(config_source.resolve()),'sha256':digest(config_source)}}
    if cfg['mode'] == 'partitioned':
        partitions = Path(cfg['partitions']['path']).resolve()
        require(digest(partitions) == cfg['partitions']['sha256'] == PARTITIONS, 'Accepted Stage4a partition bytes differ')
        expected += ['-p',str(partitions)]
        sources['partitions'] = {'path':str(partitions),'sha256':PARTITIONS}
    else:
        require('partitions' not in cfg and 'cache_import' not in cfg, 'Single-model fallback contains partition/cache inputs')
    expected += ['-m','MFP','-B','1000','--alrt','1000','--seed','1961008','-T','2',
                 '-keep-ident','--boot-trees','--prefix',str(attempt/'host')]
    if cfg['mode'] == 'single_model':
        expected += ['--mem','2G','--thread-site']
    argv = launch['argv']
    require(isinstance(argv,list) and all(isinstance(value,str) for value in argv), 'Malformed native argv')
    require(not any(value in ('-redo','--redo') or value.startswith(('-redo=','--redo=')) for value in argv),
            'Forbidden redo alias in actual command')
    require(argv == expected, 'Actual command differs: executable/flags/duplicates/input/cwd/prefix/mode')
    if 'cache_import' in cfg:
        cache = Path(cfg['cache_import']['path']).resolve()
        require(digest(cache) == cfg['cache_import']['sha256'], 'Original model-cache input bytes changed')
        copied = load(attempt/'cache_import.json')
        require(Path(copied['source']).resolve() == cache and copied['sha256'] == cfg['cache_import']['sha256'],
                'Initial cache-copy receipt differs from exact input')
        sources['model_cache'] = {'path':str(cache),'sha256':cfg['cache_import']['sha256']}
    return sources

def tree_check(text, expected, supports):
    trees = list(Phylo.parse(StringIO(text), 'newick'))
    require(len(trees) == 1, 'Exactly one parseable Newick tree required')
    tree = trees[0]
    tips = [n.name for n in tree.get_terminals()]
    require(len(tips) == len(set(tips)) == 196 and set(tips) == expected, 'Tree accession membership/uniqueness differs')
    lengths = []
    internal_support = []
    for clade in tree.find_clades():
        if clade is tree.root:
            if clade.branch_length is not None:
                require(math.isfinite(clade.branch_length) and clade.branch_length >= 0, 'Invalid root stem length')
            continue
        require(clade.branch_length is not None and math.isfinite(clade.branch_length) and clade.branch_length >= 0,
                'Missing/nonfinite/negative branch length')
        lengths.append(clade.branch_length)
        if supports and not clade.is_terminal():
            label = str(clade.name or '')
            values = label.split('/')
            require(len(values) == 2, 'Internal branch lacks paired SH-aLRT/UFBoot supports')
            pair = [float(x) for x in values]
            require(all(math.isfinite(x) and 0 <= x <= 100 for x in pair), 'Invalid support range')
            internal_support.append(pair)
    if supports:
        require(len(internal_support) > 0, 'Supported internal branches required')
    return tree, {'tips':len(tips),'branches_with_valid_lengths':len(lengths),
        'paired_supported_internal_branches':len(internal_support),
        'tree_display_root':'EXPLICITLY_UNROOTED_NO_VALIDATED_OUTGROUP',
        'total_branch_length':sum(lengths),'minimum_branch_length':min(lengths),'maximum_branch_length':max(lengths)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt',type=Path,required=True)
    parser.add_argument('--approved',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--freeze',type=Path)
    parser.add_argument('--config-source',type=Path,required=True,
                        help='Actual unaugmented config supplied to the native producer')
    args = parser.parse_args()
    # These guards precede try/finally: failure must not overwrite an earlier
    # accepted report, including a report passed inside an existing freeze.
    require(not args.report.exists() and not args.report.is_symlink(), 'Use a new external validation report path')
    if args.freeze:
        require(args.report.resolve() != args.freeze.resolve()
                and args.freeze.resolve() not in args.report.resolve().parents,
                'External report must be outside the accepted freeze namespace')
    created_freeze = False
    record = {'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'checker_sha256':digest(Path(__file__)),
        'parser':'Biopython '+Bio.__version__,'scientific_state':'FAILED_FATAL','checks':[]}
    try:
        require(digest(args.approved) == PANEL, 'Frozen approved panel hash differs')
        approved = args.approved.read_text().splitlines()
        require(len(approved) == len(set(approved)) == 196, 'Approved panel not exactly196 unique accessions')
        cfg = load(args.attempt/'config.json'); launch = load(args.attempt/'launch.json')
        exit_receipt = load(args.attempt/'exit.json'); result = load(args.attempt/'result.json')
        release = load(args.attempt/'lock_released.json')
        require(result['state'] == exit_receipt['state'] == 'VALIDATION_REQUIRED', 'Native producer did not exit successfully')
        native = exit_receipt['native']
        require(native['exited'] and native['exit_code'] == 0 and native['exit_filetime'] > native['creation_filetime'], 'Missing actual exact native exit0')
        require(native['pid'] == launch['native']['pid'] and native['creation_filetime'] == launch['native']['creation_filetime'], 'Native birth identity differs')
        require(Path(native['executable']).resolve() == Path(launch['native']['executable']).resolve(),
                'Exited native executable image differs from launch')
        require(exit_receipt['job_active_processes'] == 0 and exit_receipt['job_pids'] == [], 'New owned descendants not closed')
        require(release['state'] == 'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED', 'Workflow lock not explicitly released')
        require(exit_receipt['launch_sha256'] == digest(args.attempt/'launch.json'), 'Exit/launch receipt hash mismatch')
        accepted_sources = command_binding(cfg,launch,args.attempt,args.approved,args.config_source)
        argv = launch['argv']
        native_pins = {p.name:digest(p) for p in args.attempt.iterdir() if p.is_file()}
        report = (args.attempt/'host.iqtree').read_text(encoding='utf-8-sig')
        log = (args.attempt/'host.log').read_text(encoding='utf-8-sig')
        stdout = (args.attempt/'stdout.txt').read_text(encoding='utf-8-sig')
        combined = report+'\n'+log+'\n'+stdout
        require(re.search(r'^IQ-TREE\s+version\s+3\.1\.4(?:\s|$)',combined,re.M)
                and re.search(r'^Seed:\s*1961008(?:\s|$)',combined,re.M), 'Executed native version/seed header missing')
        require(re.search(r'(?:SH.aLRT[^\n]{0,150}1000|1000[^\n]{0,150}SH.aLRT)',combined,re.I), 'Executed1000SH-aLRT support record missing')
        if 'cache_import' in cfg:
            require('Restoring information from model checkpoint file' in combined, 'Native partial model-cache restoration unobserved')
        raw_tree_bytes = (args.attempt/'host.treefile').read_bytes()
        validated_tree_sha = hashlib.sha256(raw_tree_bytes).hexdigest()
        require(validated_tree_sha == native_pins['host.treefile'], 'Native tree changed before parsing')
        raw_tree = raw_tree_bytes.decode('utf-8-sig')
        tree, facts = tree_check(raw_tree,set(approved),True)
        if (args.attempt/'host.contree').exists():
            consensus = list(Phylo.parse(args.attempt/'host.contree','newick'))
            require(len(consensus) == 1 and len(consensus[0].get_terminals()) == 196 and
                    {n.name for n in consensus[0].get_terminals()} == set(approved), 'Consensus tip set differs')
        replicates = list(Phylo.parse(args.attempt/'host.ufboot','newick'))
        require(len(replicates) == 1000, 'Required1000ultrafast bootstrap trees missing')
        for i, replicate in enumerate(replicates):
            names = [n.name for n in replicate.get_terminals()]
            require(len(names) == len(set(names)) == 196 and set(names) == set(approved), 'Bootstrap accession membership differs: '+str(i))
        record.update(schema='STAGE04_PRIMARY_ACCEPTANCE_V1',state='COMPLETE_VALIDATED',
            scientific_state='COMPLETE_VALIDATED',unique_tips=196,branch_lengths_valid=True,support_completed=True,
            tree=facts, ufboot_replicates=len(replicates),accepted_sources=accepted_sources,
            accepted_alignment_sha256=ALIGNMENT, approved_accessions_sha256=PANEL,
            native_report_sha256=native_pins['host.iqtree'], native_tree_sha256=validated_tree_sha,
            mode=cfg['mode'], model_report='host.iqtree', seed=1961008, native_command=argv,
            scientific_limitations='Computational host phylogeny; unrooted; native composition/model warnings retained; optional sensitivities separately not run')
        record['checks'] = ['EXACT196_APPROVED_TIPS','FINITE_NONNEGATIVE_BRANCH_LENGTHS','PAIRED_BRANCH_SUPPORTS',
            'ACTUAL1000_UFBOOT_TREES','EXECUTED1000_SH_ALRT','EXACT_STAGE04A_PROVENANCE','EXACT_NEW_NATIVE_EXIT0',
            'EMPTY_NEW_OWNED_JOB','EXPLICIT_LOCK_RELEASE','EXACT_COMMAND_VERSION_SEED','PINNED_EXECUTABLE_BYTES',
            'ORIGINAL_CONFIG_HASH_AND_CONTENT','EXACT_CWD_PREFIX_MODE_AND_NO_DUPLICATE_FLAGS',
            'PINNED_PARTITIONS_IF_USED','NATIVE_CACHE_RESTORATION_IF_USED']
        if args.freeze:
            require(Path(cfg['repository_path']).resolve() in args.freeze.resolve().parents,
                    'Accepted freeze must use a new canonical project namespace after lock release')
            require(not args.freeze.exists(), 'Accepted output namespace must be new')
            args.freeze.mkdir(parents=True)
            created_freeze = True
            for path in args.attempt.iterdir():
                if path.is_file():
                    require(path.name not in {'independent_validation.json','input_output_sha256_manifest.tsv',
                        'primary196_host_tree.nwk','primary196_host_tree.nex','accepted_original_config.json',
                        'accepted_approved_accessions.txt','accepted_primary196_concatenated.faa',
                        'accepted_primary196_partitions.nex','original_input_model_cache.gz'},
                        'Native attempt contains a reserved freeze member')
                    shutil.copyfile(path,args.freeze/path.name)
                    require(path.name in native_pins and digest(args.freeze/path.name) == native_pins[path.name],
                            'Frozen native member differs from validated snapshot: '+path.name)
            require({p.name for p in args.attempt.iterdir() if p.is_file()} == set(native_pins),
                    'Closed native attempt membership changed during validation/freeze')
            shutil.copyfile(args.attempt/'host.treefile',args.freeze/'primary196_host_tree.nwk')
            nexus = '#NEXUS\nBegin trees;\nTree primary196_host_tree = [&U] '+raw_tree.strip()+'\nEnd;\n'
            (args.freeze/'primary196_host_tree.nex').write_text(nexus,encoding='utf-8',newline='\n')
            imported = list(Phylo.parse(args.freeze/'primary196_host_tree.nex','nexus'))
            require(len(imported) == 1 and {n.name for n in imported[0].get_terminals()} == set(approved), 'NEXUS export round-trip differs')
            def signature(t):
                # Nexus parser supplies a zero for an absent root stem. The
                # unrooted display root has no incoming phylogenetic edge.
                return sorted((tuple(sorted(x.name for x in n.get_terminals())),n.branch_length if n is not t.root else None,
                    n.name or '',n.confidence) for n in t.find_clades())
            require(signature(imported[0]) == signature(tree) and imported[0].rooted is False,
                    'NEXUS topology/branch/support/unrooted-state round-trip differs')
            require(digest(args.freeze/'primary196_host_tree.nwk') == validated_tree_sha,
                    'Authoritative Newick bytes differ from the actually parsed tree')
            shutil.copyfile(Path(cfg['alignment']['path']),args.freeze/'accepted_primary196_concatenated.faa')
            shutil.copyfile(args.config_source,args.freeze/'accepted_original_config.json')
            shutil.copyfile(args.approved,args.freeze/'accepted_approved_accessions.txt')
            if cfg['mode'] == 'partitioned':
                shutil.copyfile(Path(cfg['partitions']['path']),args.freeze/'accepted_primary196_partitions.nex')
            if 'cache_import' in cfg:
                shutil.copyfile(Path(cfg['cache_import']['path']),args.freeze/'original_input_model_cache.gz')
            frozen_bindings = {'accepted_primary196_concatenated.faa':'alignment',
                'accepted_original_config.json':'original_config', 'accepted_approved_accessions.txt':None}
            if cfg['mode'] == 'partitioned':
                frozen_bindings['accepted_primary196_partitions.nex'] = 'partitions'
            if 'cache_import' in cfg:
                frozen_bindings['original_input_model_cache.gz'] = 'model_cache'
            for frozen_name, source_name in frozen_bindings.items():
                expected = accepted_sources[source_name]['sha256'] if source_name else PANEL
                require(digest(args.freeze/frozen_name) == expected,
                        'Frozen accepted input differs from validated source: '+frozen_name)
            record['frozen_output_directory'] = str(args.freeze)
            # Immutable certificate excludes its own bytes and the later
            # relative distribution manifest; neither creates a self-hash cycle.
            project = Path(cfg['repository_path']).resolve()
            record['files'] = {p.resolve().relative_to(project).as_posix():digest(p)
                               for p in sorted(args.freeze.iterdir()) if p.is_file()}
            record['frozen_sources'] = {'alignment':(args.freeze/'accepted_primary196_concatenated.faa').resolve().relative_to(project).as_posix(),
                'original_config':(args.freeze/'accepted_original_config.json').resolve().relative_to(project).as_posix(),
                'approved_accessions':(args.freeze/'accepted_approved_accessions.txt').resolve().relative_to(project).as_posix()}
            if cfg['mode'] == 'partitioned':
                record['frozen_sources']['partitions'] = (args.freeze/'accepted_primary196_partitions.nex').resolve().relative_to(project).as_posix()
            write_certificate_and_manifest(args.freeze,record)
        else:
            record['state'] = record['scientific_state'] = 'VALIDATION_REQUIRED'
            record['publication_eligible'] = False
            record['reason'] = 'Scientific checks passed; a new canonical project freeze is required for acceptance'
    except Exception as error:
        record['state'] = 'FAILED_FATAL'
        record['scientific_state'] = 'FAILED_FATAL'
        record['error'] = {'kind':type(error).__name__,'message':str(error)}
        if created_freeze:
            (args.freeze/'independent_validation.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
        raise
    finally:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(record))

if __name__ == '__main__':
    main()
