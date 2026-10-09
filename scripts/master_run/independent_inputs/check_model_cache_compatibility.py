"""Read-only compatibility certificate, never scientific model/tree validation."""
import ast, csv, gzip, hashlib, json, math, re, struct, zlib
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
OLD=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
SNAP=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\referenced-chatgpt-conversation-this-is-an\outputs\stage04_v10_review\original_v10_reconciliation_20261009T090020')
PRIMARY=ROOT/'.work/stage04_phylogeny_v2/analyses/primary196'
CACHE=ROOT/'.work/stage04_inference_windows_v10/analyses/primary196/iqtree/host.model.gz'
LAUNCH=OLD/'.work/stage04_recovery_v10/production/LAB_RM_Stage04_V10_production_admission_v3_89dd19f4b57a/analyses/primary196/attempt_0001/launch.json'
EXE=OLD/'.tools/iqtree_windows_3_1_4/extracted/iqtree-3.1.4-Windows/bin/iqtree3.exe'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def require(b,msg):
    if not b: raise ValueError(msg)

launch=json.loads(LAUNCH.read_text())
expected=[str(EXE),'-s',str(PRIMARY/'concatenated.faa'),'--seqtype','AA','-p',str(PRIMARY/'partitions.nex'),
    '-m','MFP','-B','1000','--alrt','1000','--seed','1961008','-T','2','-keep-ident','--boot-trees','--prefix',str(CACHE)[:-9]]
require(launch['argv']==expected,'Original actual native argv differs from exact scientific contract')
require(sha(EXE)==launch['actual_executable_sha256']=='43c9bf3b0dc5e7d88c183a2582369d22c9d692b7585350038769334bb6fd9aed','Pinned native executable differs')
freeze=json.loads((SNAP/'v10_inference_freeze.json').read_text())
freeze_text=json.dumps(freeze)
alignment_hash=sha(PRIMARY/'concatenated.faa');partition_hash=sha(PRIMARY/'partitions.nex')
require(alignment_hash=='442742d083628ab5382a10cafc422c57084cd9bde45a4f2950f15e2c199e3307' and alignment_hash in freeze_text,'Original/current alignment hash differs')
require(partition_hash=='fa640e5e984b33e73a86b1ec7a7c18f7161a12252e68e9e3c6ceb2644eb7edc5' and partition_hash in freeze_text,'Original/current partition hash differs')
cache_bytes=CACHE.read_bytes();cache_hash=hashlib.sha256(cache_bytes).hexdigest()
require(cache_hash=='d20ef88dd11a7a2c7f5e9b99baef0108f05a21ec4a6b74226e547ce93afe8b42','Latest preserved cache hash differs')
require(sha(SNAP/'host.model.gz')==cache_hash,'Independent retained cache snapshot differs')
expanded=gzip.decompress(cache_bytes)
crc,isize=struct.unpack('<II',cache_bytes[-8:])
require(crc==(zlib.crc32(expanded)&0xffffffff) and isize==len(expanded),'Gzip CRC or full expansion size differs')
text=expanded.decode('utf-8')
require(text.splitlines()[0]=='--- # IQ-TREE Checkpoint ver >= 1.6','Native checkpoint header differs')
# Independent flat checkpoint parser with strict duplicate detection; no producer imports.
scope='';fields={};sections=set();section_occurrences={}
for lineno,line in enumerate(text.splitlines()[1:],2):
    if not line.strip():continue
    if not line.startswith(' '):scope=''
    line=line.lstrip(' \t').rstrip('\r\n\t')
    if line.endswith(':') and ': ' not in line:
        scope=line[:-1]
        section_occurrences[scope]=section_occurrences.get(scope,0)+1
        sections.add(scope);continue
    require(': ' in line,f'Malformed native checkpoint mapping at line {lineno}')
    key,value=line.split(': ',1);key=(scope+'!' if scope else '')+key
    require(key not in fields,f'Duplicate native checkpoint key at {lineno}: {key}')
    fields[key]=value
parts=list(csv.DictReader((PRIMARY/'partitions.tsv').open(newline=''),delimiter='\t'))
names={r['partition'] for r in parts}
cache_names={x for x in sections if re.fullmatch(r'p\d{4}',x)}
require(cache_names==names and len(names)==100,'Cache partition names differ from frozen partition map')
require(fields['partition_type']=='2' and 'PartitionModelPlen' in sections,'Cache must use edge-linked proportional partitions')
require(fields.get('finishedFastMLTree')=='true','Initial fast-ML completion flag missing')
# Reuse only this chat's independent Newick parser, extracted as a function AST.
tree=ast.parse((HERE/'independent_stage04a_check.py').read_text())
function=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='newick')
env={'re':re,'math':math};exec(compile(ast.Module(body=[function],type_ignores=[]),'independent_newick_function','exec'),env)
initial=env['newick'](fields['initTree'])
require(initial['tip_count']==196 and set(initial['tips'])=={str(i) for i in range(196)},'Cache initial-tree numeric tip map differs')
selected=[p for p in sorted(names) if p+'!best_model_BIC' in fields]
source_paths=['main/phylotesting.cpp','utils/checkpoint.cpp','utils/checkpoint.h','main/phyloanalysis.cpp']
source_files=[HERE/'iqtree314_source'/p.replace('/','__') for p in source_paths]
require(all(p.is_file() for p in source_files),'Reviewed pinned native sources missing')
certificate={
    'status':'PASS_COMPATIBLE_MODEL_CACHE_INPUTS','utc':datetime.now(timezone.utc).isoformat(),
    'scope':'Input, tool, command semantics and partial model-cache integrity compatibility only; not model ranking or scientific acceptance',
    'cache_sha256':cache_hash,'alignment_sha256':alignment_hash,'partitions_sha256':partition_hash,
    'executable_sha256':sha(EXE),'seed':1961008,'model_selection':'MFP_WITHOUT_MERGING','partition_option':'-p',
    'sequence_type':'AA','threads':2,'ultrafast_bootstrap_requested':1000,'sh_alrt_requested':1000,
    'keep_ident':True,'boot_trees':True,'native_general_checkpoint_imported':False,
    'cache_path':str(CACHE),'preserved_snapshot_path':str(SNAP/'host.model.gz'),
    'compressed_bytes':len(cache_bytes),'uncompressed_bytes':len(expanded),'crc32_hex':format(crc,'08x'),
    'gzip_complete_eof_crc_size_pass':True,'strict_mapping_keys':len(fields),'partition_sections':len(cache_names),
    'reopened_serialized_sections':{k:v for k,v in section_occurrences.items() if v>1},
    'selected_bic_records':len(selected),'selected_bic_partition_labels':selected,
    'initial_tree_tip_mapping':'numeric0..195 tied to identical original alignment bytes/order',
    'prefix_relocation':{
        'supported_by_pinned_source':True,
        'evidence':'runModelFinder sets model_info filename to current out_prefix+.model.gz, loads it, and checks partition_type. Checkpoint::load validates header then stores serialized keys without binding old prefix/path. Cache has no absolute path strings.',
        'allowed_changes':['output namespace','external native memory limits and host admission'],
        'required_actual_confirmation':'New native log must report restoration from new-prefix host.model.gz. Missing restoration is not cache reuse. Final full support and tree validation remain required.'},
    'no_absolute_path_strings_in_cache':not bool(re.search(r'[A-Za-z]:\\|/home/|/mnt/',text)),
    'general_checkpoint_claim':'Only partial .model.gz imported; no .ckp.gz, old process lifetime or successful final inference adopted',
    'evidence_files':[{'path':str(p),'sha256':sha(p)} for p in [LAUNCH,SNAP/'v10_inference_freeze.json',SNAP/'host.model.gz',PRIMARY/'concatenated.faa',PRIMARY/'partitions.nex',EXE,*source_files]],
    'checker_sha256':sha(Path(__file__)),'biological_inference_executed':False,
    'official_source_urls':['https://github.com/iqtree/iqtree3/blob/v3.1.4/'+p for p in source_paths]
}
out=HERE/'model_cache_compatibility.json';out.write_text(json.dumps(certificate,indent=2)+'\n')
print(json.dumps({'status':certificate['status'],'certificate':str(out),'sha256':sha(out),'checker_sha256':sha(Path(__file__)),'partition_sections':len(cache_names),'selected_bic_records':len(selected)}))
