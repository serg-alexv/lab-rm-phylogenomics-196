"""Read-only independent audit. No project modules or inference tools imported/run."""
import csv, hashlib, io, json, math, re, shutil, subprocess, sys, zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
OUT = Path(__file__).resolve().parent
BASE = ROOT / '.work/stage04_phylogeny_v2'
PRIMARY = BASE / 'analyses/primary196'
SCOPES = [ROOT,
    Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196'),
    Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\referenced-chatgpt-conversation-this-is-an')]

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as stream:
        for b in iter(lambda: stream.read(1048576), b''): h.update(b)
    return h.hexdigest()

def fasta(text):
    result, name, seq = {}, None, []
    def add():
        if name is not None:
            if name in result: raise ValueError('duplicate FASTA ID: ' + name)
            if not seq: raise ValueError('empty FASTA sequence: ' + name)
            result[name] = ''.join(seq)
    for line in text.splitlines():
        line = line.strip()
        if not line: continue
        if line.startswith('>'):
            add(); name, seq = line[1:].split()[0], []
        else:
            if name is None: raise ValueError('sequence before header')
            if re.search(r'\s', line): raise ValueError('whitespace within sequence')
            seq.append(line)
    add()
    if not result: raise ValueError('empty FASTA')
    return result

def partitions(rows, width):
    seen, names = bytearray(width), set()
    for row in rows:
        a, b, n = [int(row[k]) for k in ('start_one_based', 'end_one_based', 'length')]
        if row['partition'] in names: raise ValueError('duplicate partition')
        names.add(row['partition'])
        if not 1 <= a <= b <= width or b - a + 1 != n: raise ValueError('bad partition range')
        if any(seen[a-1:b]): raise ValueError('partition overlap')
        seen[a-1:b] = bytes([1]) * n
    if not all(seen): raise ValueError('partition gap')
    return sum(seen)

def newick(text):
    # Recursive-descent parser, independent of the producer's BioPython path.
    text = re.sub(r'\[[^\]]*\]', '', text).strip()
    tokens = re.findall(r"'(?:[^']|'')*'|[(),:;]|[^\s(),:;]+", text)
    index, leaves, branches, supports = 0, [], [], []
    def node():
        nonlocal index
        if index >= len(tokens): raise ValueError('truncated Newick')
        internal = tokens[index] == '('
        if internal:
            index += 1; node(); count = 1
            while index < len(tokens) and tokens[index] == ',': index += 1; node(); count += 1
            if count < 2 or index >= len(tokens) or tokens[index] != ')': raise ValueError('malformed internal node')
            index += 1
        label = None
        if index < len(tokens) and tokens[index] not in ('(', ')', ',', ':', ';'):
            label = tokens[index].strip("'"); index += 1
        if internal and label: supports.append(label)
        if not internal:
            if not label: raise ValueError('missing leaf label')
            leaves.append(label)
        if index < len(tokens) and tokens[index] == ':':
            index += 1
            if index >= len(tokens): raise ValueError('missing branch length')
            length = float(tokens[index]); index += 1
            if not math.isfinite(length) or length < 0: raise ValueError('invalid branch length')
            branches.append(length)
    node()
    if index != len(tokens)-1 or tokens[index] != ';': raise ValueError('Newick must end in one semicolon')
    if len(leaves) != len(set(leaves)): raise ValueError('duplicate tips')
    return {'tip_count': len(leaves), 'tips': leaves, 'branch_lengths': len(branches), 'support_labels': len(supports)}

def write_json(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, ensure_ascii=True)+'\n', encoding='utf-8')

report = {'utc': datetime.now(timezone.utc).isoformat(), 'checker_sha256': sha(__file__),
    'python': sys.version, 'root': str(ROOT), 'mutation_scope': 'chat work/independent_inputs only',
    'scientific_recomputation': False, 'checks': [], 'failures': []}
def check(name, truth, details=None):
    report['checks'].append({'check':name, 'pass':bool(truth), 'details':details})
    if not truth: report['failures'].append(name)

# Meaningful malformed-input checks of this independent parser path.
negative = []
for label, function in [('duplicate FASTA', lambda: fasta('>x\nA\n>x\nA')),
    ('sequence before header', lambda: fasta('AA\n>x\nA')),
    ('partition gap', lambda: partitions([{'partition':'a','start_one_based':'1','end_one_based':'1','length':'1'}],2)),
    ('negative branch', lambda: newick('(x:-1,y:1);')),
    ('duplicate tree tips', lambda: newick('(x:1,x:1);')),
    ('truncated Newick', lambda: newick('(x:1,y:1)'))]:
    try: function(); negative.append({'case':label,'rejected':False})
    except (ValueError, IndexError): negative.append({'case':label,'rejected':True})
report['negative_tests'] = negative
check('malformed_inputs_rejected', all(x['rejected'] for x in negative))

summary_path = ROOT/'reports/stage04a/alignment_summary.json'
summary = json.loads(summary_path.read_text())
accepted = next(x for x in summary['analyses'] if x['name']=='primary196')
panel_path = ROOT/'config/approved_accessions.txt'
panel = panel_path.read_text().split()
check('approved_panel_hash_matches_stage04a', sha(panel_path)==summary['identity']['approved_accessions_sha256'], sha(panel_path))
check('196_unique_versioned_approved_accessions', len(panel)==len(set(panel))==196 and all(re.fullmatch(r'GCF_\d+\.\d+',x) for x in panel))
report['input_files'] = []
for file, expected in accepted['file_sha256'].items():
    path = PRIMARY/file
    actual = sha(path)
    report['input_files'].append({'path':str(path),'bytes':path.stat().st_size,'sha256':actual,'expected_sha256':expected,'pass':actual==expected})
check('all_12_primary_input_hashes_match_repository_summary', len(report['input_files'])==12 and all(x['pass'] for x in report['input_files']))
alignment = fasta((PRIMARY/'concatenated.faa').read_text())
widths = Counter(map(len, alignment.values()))
chars = Counter(''.join(alignment.values()))
check('fasta_196_exact_approved_taxa', len(alignment)==196 and set(alignment)==set(panel), {'missing':sorted(set(panel)-set(alignment)),'extra':sorted(set(alignment)-set(panel))})
check('fasta_17456_equal_columns', dict(widths)=={17456:196}, dict(widths))
check('protein_alignment_alphabet', set(chars)<=set('ACDEFGHIKLMNPQRSTVWYBXZJUO-?'), dict(sorted(chars.items())))
check('no_all_gap_taxa', all(set(x)-set('-?') for x in alignment.values()))
check('primary_accessions_membership', (PRIMARY/'accessions.txt').read_text().split()==list(alignment) and set(alignment)==set(panel))

# Independent portable-format equivalence, read directly without producer helpers.
phy_lines = (PRIMARY/'concatenated.phy').read_text().splitlines()
phy = {fields[0]:''.join(fields[1:]) for line in phy_lines[1:] if (fields:=line.split())}
check('phylip_equivalence', phy_lines[0].split()==['196','17456'] and phy==alignment)
clw = {}
for line in (PRIMARY/'concatenated.clw').read_text().splitlines()[1:]:
    fields=line.split()
    if fields and fields[0].startswith('GCF_'): clw[fields[0]]=clw.get(fields[0],'')+fields[1]
check('clustal_equivalence', clw==alignment)
nex_text=(PRIMARY/'concatenated.nex').read_text()
nex_match=re.search(r'(?is)\bmatrix\s+(.*?);',nex_text)
nex={}
for line in nex_match.group(1).splitlines():
    fields=line.split()
    if fields: nex[fields[0].strip("'")]=''.join(fields[1:])
check('nexus_equivalence', nex==alignment and bool(re.search(r'(?i)ntax\s*=\s*196',nex_text)) and bool(re.search(r'(?i)nchar\s*=\s*17456',nex_text)))

rows=list(csv.DictReader((PRIMARY/'partitions.tsv').open(newline=''),delimiter='\t'))
covered=partitions(rows,17456)
check('100_partitions_exhaustive_nonoverlapping',len(rows)==100 and covered==17456)
nex_parts={m.group(1):(int(m.group(2)),int(m.group(3))) for m in re.finditer(r'(?i)charset\s+(\S+)\s*=\s*(\d+)-(\d+)\s*;', (PRIMARY/'partitions.nex').read_text())}
check('nexus_partition_equivalence',nex_parts=={r['partition']:(int(r['start_one_based']),int(r['end_one_based'])) for r in rows})
check('marker_order_equivalence',[r['profile'] for r in rows]==(PRIMARY/'marker_order.txt').read_text().splitlines())
blocks, source_hashes, source_mismatch = 0, [], []
for row in rows:
    trim=BASE/'markers'/row['profile']/'trimmed.faa'
    source_hashes.append(sha(trim)==row['source_trimmed_alignment_sha256'])
    source=fasta(trim.read_text())
    a,b=int(row['start_one_based'])-1,int(row['end_one_based'])
    for tip,seq in alignment.items():
        expected=source.get(tip,'-'*(b-a))
        if seq[a:b]!=expected: source_mismatch.append([row['profile'],tip])
        blocks+=1
check('100_source_trimmed_alignment_hashes',all(source_hashes))
check('19600_source_blocks_exact',blocks==19600 and not source_mismatch,{'blocks':blocks,'mismatches':source_mismatch})

report['release_assets']=[]
assets=json.loads((ROOT/'reports/stage04a/asset_manifest.json').read_text())['assets']
for asset in assets:
    path=ROOT/'release_staging/stage04a'/asset['asset_name']
    actual=sha(path)
    with zipfile.ZipFile(path) as archive:
        candidates=[n for n in archive.namelist() if n.endswith('analyses/primary196/concatenated.faa')]
        member_hash=hashlib.sha256(archive.read(candidates[0])).hexdigest() if candidates else None
    report['release_assets'].append({'path':str(path),'bytes':path.stat().st_size,'sha256':actual,'expected_sha256':asset['sha256'],'pass':actual==asset['sha256'],'primary_fasta_member_sha256':member_hash})
check('both_existing_release_assets_hash_match',all(x['pass'] for x in report['release_assets']))
check('release_primary_fasta_matches_local',report['release_assets'][0]['primary_fasta_member_sha256']==accepted['file_sha256']['concatenated.faa'])

# Enumerate retained tree/checkpoint evidence; do not run any controller or inference tool.
rg=shutil.which('rg')
patterns=['*.treefile','*.contree','*.nwk','*.newick','*tree*.nex','*.iqtree','host.log','*.model.gz','*.ckp.gz','*.ufboot','*.boottrees','*.raxml.bestTree']
inventory, scan_errors=[],[]
for scope in SCOPES:
    command=[rg,'--files','--hidden','--no-ignore','--glob','!**/.git/**','--glob','!**/.tools/**','--glob','!**/.private_run/**']
    for pattern in patterns: command+=['--glob',pattern]
    command+=[str(scope)]
    result=subprocess.run(command,capture_output=True,text=True,timeout=100)
    if result.returncode not in (0,1): scan_errors.append({'scope':str(scope),'stderr':result.stderr,'exit_code':result.returncode})
    for filename in result.stdout.splitlines():
        path=Path(filename)
        item={'path':filename,'bytes':path.stat().st_size,'sha256':sha(path)}
        is_tree=path.suffix.lower() in ('.treefile','.contree','.nwk','.newick') or filename.endswith('.raxml.bestTree')
        if is_tree:
            try:
                parsed=newick(path.read_text())
                tips=set(parsed.pop('tips'))
                parsed.update({'exact_approved196':len(tips)==196 and tips==set(panel),'missing_approved':len(set(panel)-tips),'extra_tips':len(tips-set(panel))})
                item['newick']=parsed
            except Exception as error: item['newick_error']=str(error)
        if path.name=='host.log':
            lines=path.read_text(errors='replace').splitlines()
            item['last_lines']=lines[-12:]
        item['synthetic_path']='synthetic' in filename.lower() or 'fixture' in filename.lower()
        inventory.append(item)
report['tree_search']={'scopes':[str(p) for p in SCOPES], 'excluded_directories':['.git','.tools','.private_run'], 'patterns':patterns, 'scan_errors':scan_errors,'inventory_count':len(inventory), 'exact_196_tree_candidates':[x['path'] for x in inventory if x.get('newick',{}).get('exact_approved196')], 'complete_final_tree_found':False}
# Existence alone would still require provenance, completed supports and final IQ-TREE report.
report['tree_search']['conclusion']='NO_COMPLETE_VALID_FINAL_TREE_FOUND' if not report['tree_search']['exact_196_tree_candidates'] and not scan_errors else 'FURTHER_CANDIDATE_REVIEW_REQUIRED'
report['status']='PASS_ACCEPTED_STAGE04A_INPUTS' if not report['failures'] else 'FAIL_INPUT_GATE'
write_json('tree_inventory.json',inventory)
write_json('independent_input_validation.json',report)
with (OUT/'input_sha256.tsv').open('w',newline='',encoding='utf-8') as stream:
    writer=csv.writer(stream,delimiter='\t');writer.writerow(['sha256','bytes','path'])
    writer.writerow([sha(panel_path),panel_path.stat().st_size,str(panel_path)])
    for x in report['input_files']+report['release_assets']: writer.writerow([x['sha256'],x['bytes'],x['path']])
print(json.dumps({'status':report['status'],'checks':len(report['checks']),'failures':report['failures'],'tree_search':report['tree_search'],'report':str(OUT/'independent_input_validation.json'),'report_sha256':sha(OUT/'independent_input_validation.json'),'inventory_sha256':sha(OUT/'tree_inventory.json'),'checker_sha256':sha(__file__)}))
