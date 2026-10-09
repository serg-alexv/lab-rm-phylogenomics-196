from pathlib import Path
import hashlib,json,math,re,datetime
from io import StringIO
from Bio import Phylo
import Bio
w=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work');a=w/'iqtree_attempts/partitioned_20261009T162904Z'
cfg=json.loads((w/'stage04_partitioned_config.json').read_text());ap=Path(cfg['approved_accessions']['path']);panel=ap.read_bytes();assert hashlib.sha256(panel).hexdigest()==cfg['approved_accessions']['sha256'];approved=set(panel.decode().splitlines());assert len(approved)==196
raw=(a/'host.treefile').read_bytes();trees=list(Phylo.parse(StringIO(raw.decode()),'newick'));assert len(trees)==1;t=trees[0];tips=[c.name for c in t.get_terminals()];assert len(tips)==len(set(tips))==196 and set(tips)==approved
lengths=[];pairs=[]
for c in t.find_clades():
 if c is t.root:
  assert c.branch_length is None or math.isfinite(c.branch_length) and c.branch_length>=0
  continue
 assert c.branch_length is not None and math.isfinite(c.branch_length) and c.branch_length>=0;lengths.append(c.branch_length)
 if not c.is_terminal():
  p=(c.name or '').split('/');assert len(p)==2;p=list(map(float,p));assert all(math.isfinite(v) and 0<=v<=100 for v in p);pairs.append(p)
count=0
for b in Phylo.parse(a/'host.ufboot','newick'):
 names=[c.name for c in b.get_terminals()];assert len(names)==len(set(names))==196 and set(names)==approved;count+=1
assert count==1000
cs=list(Phylo.parse(a/'host.contree','newick'));assert len(cs)==1 and len(cs[0].get_terminals())==196 and {c.name for c in cs[0].get_terminals()}==approved
nex='#NEXUS\nBegin trees;\nTree primary196_host_tree = [&U] '+raw.decode().strip()+'\nEnd;\n';nn=list(Phylo.parse(StringIO(nex),'nexus'));assert len(nn)==1 and nn[0].rooted is False
def sig(t):return sorted((tuple(sorted(x.name for x in n.get_terminals())),n.branch_length if n is not t.root else None,n.name or '',n.confidence) for n in t.find_clades())
assert sig(nn[0])==sig(t)
report=(a/'host.iqtree').read_text();log=(a/'host.log').read_text();out=(a/'stdout.txt').read_text();combined=report+'\n'+log+'\n'+out
assert re.search(r'^IQ-TREE\s+version\s+3\.1\.4(?:\s|$)',combined,re.M) and re.search(r'^Seed:\s*1961008(?:\s|$)',combined,re.M)
assert 'Restoring information from model checkpoint file' in combined
phrase='Testing tree branches by SH-like aLRT with 1000 replicates...';assert phrase in log and phrase in out
r={'schema':'STAGE04_ACTUAL_NATIVE_FORMAT_READ_ONLY_AUDIT_V1','state':'PASS_READ_ONLY_ACTUAL_FORMAT_AUDIT_NOT_ACCEPTANCE','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'parser':'Biopython '+Bio.__version__,'attempt':str(a),'approved_sha256':hashlib.sha256(panel).hexdigest(),'files':{n:{'sha256':hashlib.sha256((a/n).read_bytes()).hexdigest(),'bytes':(a/n).stat().st_size} for n in ['host.treefile','host.ufboot','host.contree','host.iqtree','host.log','stdout.txt','exit.json','launch.json']},'actual_tips':196,'finite_nonnegative_edges':len(lengths),'paired_supported_internal_edges':len(pairs),'sum_edge_lengths':sum(lengths),'minimum_edge_length':min(lengths),'maximum_edge_length':max(lengths),'actual_bootstrap_trees':count,'all_bootstrap_tips_exact_panel':True,'consensus_tips_exact_panel':True,'in_memory_nexus_topology_branch_support_roundtrip_exact':True,'in_memory_nexus_explicit_unrooted':True,'native_version_seed_cache_restore_phrases_present':True,'exact_SH_aLRT_executed_phrase':phrase,'phrase_present_both_log_stdout':True,'old_regex_matches':bool(re.search(r'(?:SH.aLRT[^\n]{0,150}1000|1000[^\n]{0,150}SH.aLRT)',combined,re.I)),'first_failed_acceptance_preserved':True,'scientific_acceptance':False,'freeze_created':False,'inference_or_native_rerun':False,'original_outputs_modified':False,'G_writes':0,'WSL_starts':0}
p=w/'stage04_actual_native_format_audit.json';p.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({'receipt':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'counts':[len(tips),len(lengths),len(pairs),count],'nexus_exact':True}))
