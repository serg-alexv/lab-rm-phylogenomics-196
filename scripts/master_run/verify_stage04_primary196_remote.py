"""Independent fresh Stage4 Release readback and accepted-science byte audit.

No producer imports, inference, source mutation, extraction, WSL or Git writes.
Default no-op; --verify needs this reader's immutable published source commit.
"""
from pathlib import Path, PurePosixPath
from io import StringIO, TextIOWrapper
from types import SimpleNamespace
import argparse, collections, csv, hashlib, importlib.util, json, math, os, re, stat, sys, time, uuid
import zipfile
from Bio import Phylo

sys.dont_write_bytecode = True
WORK = Path(__file__).resolve().parent
EXACT_WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
REPORT = 'reports/stage04/primary196_atomic_20261009/'
FREEZE = '.work/stage04_primary196_atomic_20261009/'
EXPECTED_NAME = 'stage04_remote_expected.json'
EXPECTED_SHA = '0c9d0dc5ceee4e7e200d5f910c1656f356e7106467ceabdc1b0af737bba62a25'
EXPECTED_REMOTE = 'reports/master_run/20261009/preparation/' + EXPECTED_NAME
HELPERS = {
    'verify_public_conda_packages01_remote.py': 'cadeda01183522be585b0f42f240fcaab8bc7a5335937e03b209a04e5ff216ed',
    'verify_master_public_components01_remote.py': '6825690d52292b8bbb2f9d5aa0cfcb1fbd8d8863601d890559a05adf3c3d7691',
    'verify_master_original_sidecars.py': '090e8068d9f2ee0a21631541681a835de5f97bd1cf695b06537aabeb4bf24841',
}
PANEL = '85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6'
ALIGNMENT = '442742d083628ab5382a10cafc422c57084cd9bde45a4f2950f15e2c199e3307'
PARTITIONS = 'fa640e5e984b33e73a86b1ec7a7c18f7161a12252e68e9e3c6ceb2644eb7edc5'
NATIVE_TREE = 'f886c0134ab662a05aae2b1c1a26ed364749af250400f769ce6e63f1f7a8ba19'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_reader():
    for name, pin in HELPERS.items():
        require(sha((WORK/name).read_bytes()) == pin, 'Pinned independent helper differs: '+name)
    path = WORK/'verify_public_conda_packages01_remote.py'
    spec = importlib.util.spec_from_file_location('independent_owned_readback_only', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def distribution_rows(raw):
    lines = raw.decode('utf-8-sig').splitlines()
    require(lines and lines[0] == 'path\tsha256\tbytes', 'Accepted distribution header differs')
    rows = {}
    for line in lines[1:]:
        fields = line.split('\t'); require(len(fields) == 3, 'Malformed distribution row')
        name, digest, size = fields; path = PurePosixPath(name)
        require(len(path.parts) == 1 and path.as_posix() == name and name not in ('.','..')
                and '\\' not in name and ':' not in name and name not in rows
                and re.fullmatch('[a-f0-9]{64}', digest) and re.fullmatch('[0-9]+', size),
                'Unsafe/duplicate distribution row')
        rows[name] = {'sha256':digest, 'bytes':int(size)}
    return rows


def tree_facts(tree, panel, supports):
    tips = [n.name for n in tree.get_terminals()]
    require(len(tips) == len(set(tips)) == len(panel) and set(tips) == panel, 'Exact tree tips differ')
    lengths, pairs = [], []
    for node in tree.find_clades():
        if node is tree.root:
            require(node.branch_length is None or math.isfinite(node.branch_length) and node.branch_length >= 0,
                    'Invalid root stem')
            continue
        require(node.branch_length is not None and math.isfinite(node.branch_length) and node.branch_length >= 0,
                'Missing/nonfinite/negative tree edge')
        lengths.append(node.branch_length)
        if supports and not node.is_terminal():
            values = str(node.name or '').split('/')
            require(len(values) == 2, 'Missing paired SH-aLRT/UFBoot label')
            values = list(map(float, values))
            require(all(math.isfinite(x) and 0 <= x <= 100 for x in values), 'Invalid paired support')
            pairs.append(values)
    return {'tips':len(tips), 'edges':len(lengths), 'paired_supported_internal_edges':len(pairs),
            'total_branch_length':sum(lengths), 'minimum_branch_length':min(lengths), 'maximum_branch_length':max(lengths)}


def signature(tree):
    return sorted((tuple(sorted(x.name for x in n.get_terminals())),
                   n.branch_length if n is not tree.root else None, n.name or '', n.confidence)
                  for n in tree.find_clades())


def alignment_duplicate_facts(raw, panel):
    sequences, name, parts = {}, None, []
    for line in raw.decode('ascii').splitlines():
        if line.startswith('>'):
            if name is not None:
                require(name not in sequences, 'Duplicate FASTA accession'); sequences[name] = ''.join(parts)
            name, parts = line[1:].split()[0], []
        else:
            require(name is not None and line and not any(c.isspace() for c in line), 'Malformed aligned FASTA')
            parts.append(line)
    require(name is not None and name not in sequences, 'Missing/duplicate last FASTA accession')
    sequences[name] = ''.join(parts)
    require(set(sequences) == panel and len(sequences) == 196 and {len(x) for x in sequences.values()} == {17456},
            'Accepted alignment dimensions/accessions differ')
    grouped = collections.defaultdict(list)
    for accession, sequence in sequences.items(): grouped[sequence].append(accession)
    return {tuple(sorted(names)):sha(sequence.encode('ascii')) for sequence, names in grouped.items() if len(names)>1}, len(grouped)


def science(z, observed, expected, guard):
    cert_raw = z.read('accepted/independent_validation.json'); cert = json.loads(cert_raw)
    require(sha(cert_raw) == expected['validation_sha256'] and cert['schema'] == 'STAGE04_PRIMARY_ACCEPTANCE_V1'
            and cert['state'] == cert['scientific_state'] == 'COMPLETE_VALIDATED'
            and cert['unique_tips'] == 196 and cert['branch_lengths_valid'] is True and cert['support_completed'] is True
            and cert['mode'] == 'partitioned' and cert['seed'] == 1961008
            and cert['approved_accessions_sha256'] == PANEL and cert['accepted_alignment_sha256'] == ALIGNMENT
            and cert['native_tree_sha256'] == NATIVE_TREE, 'Accepted scientific certificate differs')
    accepted = {}
    for name, digest in cert['files'].items():
        pure = PurePosixPath(name)
        require(name.startswith(FREEZE) and pure.as_posix() == name and len(pure.parts) == 3
                and pure.name not in accepted, 'Accepted certificate scientific namespace differs')
        accepted['accepted/'+pure.name] = digest
    accepted['accepted/independent_validation.json'] = expected['validation_sha256']
    require({n for n in observed if n.startswith('accepted/')} == set(accepted)|{'accepted/input_output_sha256_manifest.tsv'},
            'Accepted scientific ZIP set is not exhaustive')
    for name, digest in accepted.items(): require(observed[name]['sha256'] == digest, 'Scientific member SHA differs: '+name)
    distribution = distribution_rows(z.read('accepted/input_output_sha256_manifest.tsv'))
    require(set(distribution) == {PurePosixPath(n).name for n in accepted}, 'Accepted distribution set differs')
    for name, pin in distribution.items():
        require(all(observed['accepted/'+name][k] == value for k, value in pin.items()), 'Distribution SHA/size differs')
    panel_raw = z.read('accepted/accepted_approved_accessions.txt'); panel_lines = panel_raw.decode('ascii').splitlines()
    panel = set(panel_lines)
    require(sha(panel_raw) == PANEL and len(panel) == len(panel_lines) == 196
            and all(re.fullmatch(r'GCF_[0-9]+\.[0-9]+', x) for x in panel)
            and z.read('inputs/approved_accessions.txt') == panel_raw, 'Exact versioned approved196 panel differs')
    alignment = z.read('accepted/accepted_primary196_concatenated.faa')
    require(sha(alignment) == ALIGNMENT and sha(z.read('accepted/accepted_primary196_partitions.nex')) == PARTITIONS,
            'Frozen Stage4a input bytes differ')
    raw_tree = z.read('accepted/primary196_host_tree.nwk')
    require(sha(raw_tree) == NATIVE_TREE and raw_tree == z.read('accepted/host.treefile'), 'Authoritative/native tree bytes differ')
    trees = list(Phylo.parse(StringIO(raw_tree.decode('utf-8-sig')), 'newick')); require(len(trees) == 1, 'Multiple native trees')
    facts = tree_facts(trees[0], panel, True)
    require(facts['tips'] == 196 and facts['edges'] == 389 and facts['paired_supported_internal_edges'] == 193
            and facts['total_branch_length'] == cert['tree']['total_branch_length'], 'Actual tree support/length facts differ')
    nexus = list(Phylo.parse(StringIO(z.read('accepted/primary196_host_tree.nex').decode()), 'nexus'))
    require(len(nexus) == 1 and nexus[0].rooted is False and signature(nexus[0]) == signature(trees[0]),
            'NEXUS topology/branch/support/unrooted roundtrip differs')
    replicates = 0
    with z.open('accepted/host.ufboot') as raw:
        with TextIOWrapper(raw, encoding='ascii') as stream:
            for tree in Phylo.parse(stream, 'newick'):
                names = [n.name for n in tree.get_terminals()]
                require(len(names) == len(set(names)) == 196 and set(names) == panel, 'Bootstrap exact196 tip set differs')
                replicates += 1; require(replicates <= 1000, 'Extra bootstrap trees'); guard()
    require(replicates == cert['ufboot_replicates'] == 1000, 'Actual1000 bootstrap trees missing')
    consensus = list(Phylo.parse(StringIO(z.read('accepted/host.contree').decode()), 'newick'))
    require(len(consensus) == 1 and len(consensus[0].get_terminals()) == 196
            and {n.name for n in consensus[0].get_terminals()} == panel, 'Consensus exact196 differs')
    report = z.read('accepted/host.iqtree').decode(); logs = [z.read('accepted/'+name).decode() for name in ('host.log','stdout.txt')]
    pattern = re.compile(r'^Testing tree branches by SH-like aLRT with 1000 replicates\.\.\.\n([0-9]+(?:\.[0-9]+)?) sec\.\nCreating bootstrap support values\.\.\.$', re.M)
    durations = [pattern.findall(text.replace('\r\n','\n')) for text in logs]
    require(durations == [['79.923'],['79.923']] and 'Numbers in parentheses are SH-aLRT support (%) / ultrafast bootstrap support (%)' in report,
            'Actual completed native SH-aLRT/paired-support interpretation differs')
    exit_receipt = json.loads(z.read('accepted/exit.json')); launch = json.loads(z.read('accepted/launch.json'))
    native = exit_receipt['native']; born = launch['native']
    require(native['pid'] == born['pid'] == 4768 and native['creation_filetime'] == born['creation_filetime'] == 134360369876207076
            and native['exited'] is True and native['exit_code'] == 0 and native['exit_filetime'] > native['creation_filetime']
            and exit_receipt['state'] == 'VALIDATION_REQUIRED' and exit_receipt['job_active_processes'] == 0 and exit_receipt['job_pids'] == []
            and exit_receipt['launch_sha256'] == observed['accepted/launch.json']['sha256'], 'Accepted native closure differs')
    require(launch['argv'] == cert['native_command'] and launch['argv'].count('--alrt') == 1
            and launch['argv'].count('-B') == 1 and '-keep-ident' in launch['argv'] and '--boot-trees' in launch['argv']
            and not any(x in ('-redo','--redo') for x in launch['argv']), 'Actual native command differs')
    power = json.loads(z.read('accepted/execution_state_restored.json'))
    require(power['actual_api_success'] is True and power['requested_flags'] == 0x80000000
            and json.loads(z.read('accepted/lock_released.json'))['state'] == 'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED', 'Power/lock closure differs')
    groups, unique = alignment_duplicate_facts(alignment, panel); qa = json.loads(z.read('alignment_qa/exact_alignment_duplicates.json'))
    recorded = {tuple(sorted(row['accessions'])):row['aligned_sequence_sha256'] for row in qa['groups']}
    require(recorded == groups and len(qa['groups']) == len(groups) == 8 and sum(map(len,groups)) == 22 and unique == 182
            and qa['alignment_sha256'] == ALIGNMENT and qa['taxa'] == 196 and qa['columns'] == 17456,
            'Independent exact-alignment duplicate QA differs')
    return {'tree':facts, 'ufboot_replicates':replicates, 'nexus_exact_unrooted_roundtrip':True,
            'actual_native_exit0_empty_job':True, 'completed_SH_aLRT_seconds':79.923,
            'alignment_duplicate_groups':8, 'taxa_in_duplicate_groups':22, 'unique_aligned_sequences':unique,
            'native_warnings_retained':True, 'R_M_or_final_figure_acceptance':False}


def inspect_zip(path, expected, B):
    require(path.stat().st_size == expected['asset']['bytes'] and B.file_sha(path) == expected['asset']['sha256'], 'Exact outer ZIP differs')
    observed = {}
    with zipfile.ZipFile(path) as z:
        names = z.namelist(); B.A.safe_names(names)
        require(len(names) == expected['total_members'] == 56 and set(names) == set(expected['members']), 'Exact56 ZIP set differs')
        require(sum(i.file_size for i in z.infolist()) == expected['logical_bytes'], 'ZIP logical byte bound differs')
        checks = {}
        for line in z.read('SHA256SUMS.txt').decode('ascii').splitlines():
            match = re.fullmatch(r'([a-f0-9]{64})  (.+)',line)
            require(match and match[2] not in checks, 'Malformed/duplicate SUMS row'); checks[match[2]] = match[1]
        require(set(checks) == set(names)-{'SHA256SUMS.txt'} and len(checks) == 55, 'Exhaustive55 SUMS differ')
        for info in z.infolist():
            require(not info.is_dir() and not info.flag_bits & 1 and stat.S_IFMT(info.external_attr>>16) in (0,stat.S_IFREG), 'Unsafe ZIP type/encryption')
            pin = expected['members'][info.filename]
            require(info.file_size == pin['bytes'] and f'{info.CRC:08x}' == pin['crc32'], 'Expected member size/CRC differs')
            with z.open(info) as stream: count, digest = B.streamed_sha(stream)
            require(count == pin['bytes'] and digest == pin['sha256'] and (info.filename == 'SHA256SUMS.txt' or digest == checks[info.filename]),
                    'Actual member EOF CRC/SHA/SUMS differs: '+info.filename)
            observed[info.filename] = dict(member=info.filename,bytes=count,sha256=digest,crc32=f'{info.CRC:08x}',crc_verified=True)
        facts = science(z, observed, expected, B.guard)
    return list(observed.values()), facts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(); mode.add_argument('--verify',action='store_true'); mode.add_argument('--local-inspect',action='store_true')
    parser.add_argument('--source-commit'); args = parser.parse_args()
    if not args.verify and not args.local_inspect:
        print('{"state":"PREPARED_NO_REMOTE_OR_SCIENTIFIC_READBACK"}'); return 0
    require(WORK == EXACT_WORK and os.name == 'nt', 'Exact current Windows C reader required')
    require(not args.verify or re.fullmatch('[a-f0-9]{40}',args.source_commit or ''), 'Immutable reader publication commit required')
    raw = (WORK/EXPECTED_NAME).read_bytes(); require(sha(raw) == EXPECTED_SHA, 'Independent expected source pins changed')
    expected = json.loads(raw); B = load_reader(); A = B.A
    B.DEADLINE = time.monotonic()+1800; B.RESOURCE = B.ResourceReader(); B.guard()
    out = WORK/('stage04_primary196_independent_readback_'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'_'+uuid.uuid4().hex[:8]); out.mkdir()
    B.COMMAND_OUT = out/'command_io'; B.COMMAND_OUT.mkdir(); A.run = B.monitored_run; A.digest = B.file_sha
    result = {'schema':'STAGE04_PRIMARY196_INDEPENDENT_REMOTE_READBACK_V1','state':'STARTED','started_utc':A.utc(),
              'mode':'FRESH_REMOTE' if args.verify else 'LOCAL_INSPECTION','verifier_sha256':sha(Path(__file__).read_bytes()),
              'expected_manifest_sha256':EXPECTED_SHA,'validation_sha256':expected['validation_sha256'],
              'publication_sha256':expected['publication_sha256'],'source_commit':args.source_commit,
              'publication_commit':expected['publication_commit'],'native_tree_sha256':NATIVE_TREE,
              'G_writes':0,'WSL_starts':0,'inference_runs':0,'producer_imports':0,'Git_writes':0}
    try:
        release = selected = None
        if args.verify:
            controls = {}; values = A.get_controls(SimpleNamespace(local_inspect=False,source_commit=args.source_commit),{},
                {**HELPERS,Path(__file__).name:result['verifier_sha256']},'',WORK,out,controls,
                extras={EXPECTED_REMOTE:(WORK/EXPECTED_NAME,EXPECTED_SHA)})
            result['reader_source_readback'] = controls['authoritative_control_readback']
            publication_controls = {}
            control_dir = out/'publication'; control_dir.mkdir()
            values = A.get_controls(SimpleNamespace(local_inspect=False,source_commit=expected['publication_commit']),{}, {},'',WORK,control_dir,publication_controls,
                extras={name:(Path('UNUSED_REMOTE_ONLY'),pin['sha256']) for name,pin in expected['published_controls'].items()})
            result['publication_source_readback'] = publication_controls['authoritative_control_readback']
            cert = json.loads(values[REPORT+'independent_validation.json']); pub = json.loads(values[REPORT+'publication_receipt.json'])
            require(pub['status'] == 'UPLOAD_VERIFIED' and pub['remote_tag_commit_verified'] is True
                    and pub['payload_commit'] == expected['tag_commit'] and pub['final_validation_summary_sha256'] == expected['validation_sha256']
                    and len(pub['assets']) == 1 and all(pub['assets'][0][k] is True for k in ('download_readback_verified','all_zip_member_hashes_verified','sidecar_readback_verified')),
                    'Original publication receipt contract differs')
            require(cert['state'] == 'COMPLETE_VALIDATED', 'Remote compact acceptance incomplete')
            status = json.loads(values['status/stage04_execution.json'])
            rows = list(csv.DictReader(StringIO(values['status/stages.tsv'].decode()),delimiter='\t'))
            stages = [r for r in rows if r['stage'] == '4_phylogeny']
            require(status['state'] == 'COMPLETE_VALIDATED' and len(stages) == 1
                    and [stages[0][k] for k in ('execution','validation','publication')] == ['COMPLETED','PASS_PRIMARY196_HOST_TREE','UPLOAD_VERIFIED'],
                    'Canonical Stage4 status row differs')
            release_args = SimpleNamespace(tag=expected['tag'],expected_tag_commit=expected['tag_commit'],source_commit=args.source_commit)
            release, selected = B.S.begin(A,release_args,[expected['asset']],[expected['sidecar']],out,result)
            archive = out/expected['asset']['name']
        else:
            archive = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196\release_staging\primary196_atomic_20261009')/expected['asset']['name']
        members, facts = inspect_zip(archive,expected,B)
        result.update(members=members,scientific_readback=facts,total_zip_members=56,payload_members=55,
                      unique_tips=196,ufboot_replicates=1000,asset_sha256=expected['asset']['sha256'],asset_readback_sha256=B.file_sha(archive))
        if args.verify:
            A.end_release(release_args,release,selected,result)
        result.update(state='PASS_FRESH_REMOTE_ACCEPTED_PRIMARY196_FULL_PAYLOAD' if args.verify else 'PASS_LOCAL_ACCEPTED_PRIMARY196_PAYLOAD_NOT_REMOTE',
                      independent_remote_gate_passed=args.verify,prior_scientific_acceptance_preserved=True,
                      new_inference_or_RM_or_final_figure_acceptance=False)
        return 0
    except BaseException as error:
        result.update(state='FAILED_INDEPENDENT_STAGE04_READBACK_NO_ADOPTION',independent_remote_gate_passed=False,
                      error={'kind':type(error).__name__,'message':str(error)}); raise
    finally:
        result.update(finished_utc=A.utc(),owned_GitHub_commands=B.COMMANDS,resource_minima=B.RESOURCE_MIN)
        receipt = out/'receipt.json'
        with receipt.open('x',encoding='utf-8',newline='\n') as stream: json.dump(result,stream,sort_keys=True,indent=2); stream.write('\n')
        print(json.dumps({'state':result['state'],'receipt':str(receipt)}))


if __name__ == '__main__':
    raise SystemExit(main())
