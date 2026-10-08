"""Freeze human-approved196 metadata on WD. Not sequence/functional validation."""
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, json, re, shutil, socket
ROOT=Path(__file__).resolve().parents[1]
SRC=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\referenced-chatgpt-conversation-this-is-an')
G0=SRC/'outputs/gate_g0'
NOW=datetime.now(timezone.utc).isoformat()
assert socket.gethostname().lower()=='wd'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def readtab(p):
    with p.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f,delimiter='\t'))
def tab(p,rows,delimiter='\t'):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=delimiter,lineterminator='\n'); w.writeheader(); w.writerows(rows)
def js(p,o):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
for d in ['config','evidence/g0/reports','evidence/g0/raw','evidence/g0/inputs','reports/stage01','status','docs','.private_run']: (ROOT/d).mkdir(parents=True,exist_ok=True)
ids=[x.strip() for x in (G0/'proposed_accessions.txt').read_text(encoding='utf-8-sig').splitlines() if x.strip()]
ledger=readtab(G0/'taxonomy_verified_197.tsv'); byid={r['original_accession']:r for r in ledger}; tests=[]
def check(name,ok):
    tests.append({'check':name,'result':'PASS' if ok else 'FAIL'})
    if not ok:
        js(ROOT/'reports/stage01/validation_results.json',{'status':'FAIL','checks':tests}); raise ValueError(name)
check('196_unique_versioned_ids',len(ids)==len(set(ids))==196 and all(re.fullmatch(r'GCF_\d{9}\.\d+',x) for x in ids))
check('held_id_excluded','GCF_000056065.1' not in ids)
check('197_unique_g0_ledger',len(ledger)==len(byid)==197)
check('exact_approved_proposal_membership',set(ids)=={r['original_accession'] for r in ledger if r['proposed_disposition']=='PROPOSED_FOR_INCLUSION'})
selected=[byid[x] for x in ids]; counts={}
expected={'Lacticaseibacillus':19,'Lactiplantibacillus':22,'Lactobacillus':19,'Lactococcus':23,'Leuconostoc':19,'Limosilactobacillus':20,'Oenococcus':15,'Pediococcus':18,'Streptococcus':23,'Weissella':18}
for r in selected:
    a=r['original_accession']; counts[r['verified_genus']]=counts.get(r['verified_genus'],0)+1
    check(a+':exact_current',r['current_accession']==a and r['assembly_status']=='current')
    check(a+':g0_taxonomy_status',r['taxonomy_verification_status']=='PASS_TAXONOMY' and r['enterococcus_exclusion_status']=='PASS_ENTEROCOCCUS_EXCLUSION')
    lin=json.loads(r['verified_taxonomic_lineage']); genus=[n for n in lin if str(n.get('rank','')).upper()=='GENUS']
    check(a+':ranked_genus',len(genus)==1 and genus[0]['scientific_name']==r['verified_genus'] and str(genus[0]['tax_id'])==r['verified_genus_tax_id'])
    check(a+':no_enterococcus_g0_lineage',all(n.get('scientific_name')!='Enterococcus' and str(n.get('tax_id'))!='1350' for n in lin))
    check(a+':reported_quality_only',r['checkm_completeness']!='' and r['checkm_contamination']!='' and r['contig_count']!='' and float(r['checkm_completeness'])>=95 and float(r['checkm_contamination'])<=5 and 1<=int(r['contig_count'])<=100)
    check(a+':streptococcus_species_scope',r['verified_genus']!='Streptococcus' or r['species_tax_id']=='1308')
check('genus_counts',counts==expected)
check('110_species',len({r['species_tax_id'] for r in selected})==110)
check('24_source_anchors',sum(r['historical_anchor'].lower()=='true' for r in selected)==24)
provenance=[]
def copy(src,dst):
    shutil.copy2(src,dst); check('copy_hash:'+dst.relative_to(ROOT).as_posix(),sha(src)==sha(dst))
    provenance.append({'source_wd_path':str(src),'repository_path':dst.relative_to(ROOT).as_posix(),'size_bytes':src.stat().st_size,'sha256':sha(src),'evidence_class':'G0_SOURCE_COPY_NOT_SEQUENCE_VALIDATION'})
for n in ['proposed_accessions.txt','taxonomy_verified_197.tsv','proposed_final_panel.tsv','proposed_policy.json','panel_review_report.md','panel_comparison.tsv','panel_exceptions.tsv','historical_replacements.tsv','genus_species_summary.tsv','sensitivity162_accessions.txt','enterococcus_exclusion_report.md','G0_acceptance_report.md','independent_review.md','response_receipts.json','retrieval_versions.tsv','sources.json']:
    if (G0/n).is_file(): copy(G0/n,ROOT/'evidence/g0/reports'/n)
for p in sorted((SRC/'work/g0/raw').glob('R*')):
    if p.suffix in ['.json','.xml']: copy(p,ROOT/'evidence/g0/raw'/p.name)
for n in ['selected_accessions_stage1.txt','frozen_accessions_150.tsv','anchor_replacements.tsv','literature_anchor_manifest.tsv','taxa.tsv']: copy(SRC/'work/g0/inputs'/n,ROOT/'evidence/g0/inputs'/n)
tab(ROOT/'evidence/g0/source_manifest.tsv',provenance)
(ROOT/'config/approved_accessions.txt').write_text('\n'.join(ids)+'\n',encoding='utf-8')
master=[]
for r in selected:
    label=r['organism_name']+((' '+r['strain']) if r['strain'] and r['strain'] not in r['organism_name'] else '')
    master.append({'assembly_accession':r['original_accession'],'operational_group':r['source_operational_group'],'official_organism_name':r['organism_name'],'species_name':r['species_name'],'species_tax_id':r['species_tax_id'],'genus_name':r['verified_genus'],'genus_tax_id':r['verified_genus_tax_id'],'strain':r['strain'],'biosample':r['biosample'],'assembly_level':r['assembly_level'],'source_reported_completeness':r['checkm_completeness'],'source_reported_contamination':r['checkm_contamination'],'source_contig_count':r['contig_count'],'historical_anchor':r['historical_anchor'],'display_label':label,'human_approval':'APPROVED_FOR_SEQUENCE_ANALYSIS','sequence_validation_status':'NOT_RUN','g0_evidence_locator':r['external_evidence_reference']})
tab(ROOT/'config/approved_panel.tsv',master); tab(ROOT/'config/approved_panel.csv',master,',')
tab(ROOT/'config/tip_labels.tsv',[{k:r[k] for k in ['assembly_accession','display_label','operational_group']} for r in master])
tab(ROOT/'reports/stage01/genus_counts.tsv',[{'genus':g,'assembly_count':n} for g,n in sorted(counts.items())])
js(ROOT/'config/approval.json',{'recorded_at_utc':NOW,'authorization_basis':'User manually approved union196, then approved full WD execution with no pilot and GitHub publication after every stage, automatic progression.','human_approval':'APPROVED_FOR_SEQUENCE_ANALYSIS','approved_assembly_count':196,'panel_accessions_sha256':sha(ROOT/'config/approved_accessions.txt'),'source_exact_bytes_sha256':sha(G0/'proposed_accessions.txt'),'source_policy_id':'G0_UNION196_INCLUSIVE_STRICT_METADATA_PROPOSAL_V2','pilot':False,'routine_stage_human_wait':False,'automatic_progression_requires':['scientific validation','verified GitHub publication'],'held_accessions':['GCF_000056065.1'],'evidence_limit':'Reported G0 metadata only; no new sequence/ANI/CheckM or R-M validation.'})
js(ROOT/'reports/stage01/validation_results.json',{'status':'PASS_APPROVED_PANEL_FREEZE','recorded_at_utc':NOW,'host':socket.gethostname(),'assertions':len(tests),'checks':tests,'sequence_analysis_performed':False,'ncbi_refetch_performed':False})
tab(ROOT/'reports/stage01/validation_results.tsv',tests)
(ROOT/'reports/stage01/REPORT.md').write_text(f'# Stage 1: approved panel freeze\n\nPASS_APPROVED_PANEL_FREEZE at {NOW} on WD.\n\n196 unique exact-version accessions,110 named species,24 source-derived anchors. {len(tests)} executed assertions; source-copy hashes checked. Held GCF_000056065.1 excluded.\n\nThis freezes approved G0 metadata, not sequence identity or R-M function. Old G0 PENDING labels are preserved; config/approval.json records the later user approval. No pilot biological cohort.\n\nAccession SHA256: {sha(ROOT/"config/approved_accessions.txt")}\n\nNext: full196 sequence acquisition.\n',encoding='utf-8')
tab(ROOT/'status/stages.tsv',[{'stage':'0_environment','execution':'STARTING','validation':'NOT_RUN','publication':'PENDING'},{'stage':'1_panel_freeze','execution':'COMPLETED','validation':'PASS_APPROVED_PANEL_FREEZE','publication':'PENDING'}]+[{'stage':f'{i}_{n}','execution':'NOT_RUN','validation':'NOT_RUN','publication':'NOT_RUN'} for i,n in [(2,'sequences'),(3,'markers'),(4,'phylogeny'),(5,'rm_inventory'),(6,'figure'),(7,'final_review')]])
(ROOT/'STATUS.md').write_text('# Current execution status\n\nStage1 approved-panel freeze executed on WD: validation PASS; publication pending verification. Environment setup starting. Stages2-7 NOT_RUN. Full196 only, no pilot. See status/stages.tsv and reports/stage01/.\n',encoding='utf-8')
(ROOT/'README.md').write_text('# LAB R-M phylogenomics: approved196\n\nCanonical WD working repository for the host phylogeny and independent R-M Type I-IV annotation.\n\n- STATUS.md reports actual execution, not planned results.\n- WORK_ORDER.md records authorized full196 execution, no pilot, automatic progression after validation/publication.\n- config/approved_accessions.txt and approved_panel.tsv define the cohort.\n- evidence/g0/ preserves raw NCBI metadata and historical reconciliation, not new sequence results.\n- reports/stage01/ contains executed panel-freeze tests.\n- Large datasets will be portable ZIP Release assets; compact TSV/CSV/FASTA/CLW/Newick/NEXUS, scripts and reports stay in Git where practical.\n\nOnly concise rationale/method summaries and sanitized execution evidence are published. No hidden chain-of-thought, private sessions or credentials. Computation is on WD; GitHub is collaboration/provenance storage, not a replacement for primary biological evidence.\n',encoding='utf-8')
(ROOT/'.gitignore').write_text('.private_run/\n__pycache__/\n*.pyc\n.env\n.env.*\n*credentials*\n*token_cache*\n*.pem\n*.key\n.tools/\n.micromamba/\n.work/\n.cache/\ndata/raw_ncbi/\nrelease_staging/\n',encoding='utf-8')
(ROOT/'.gitattributes').write_text('* text=auto\n*.md text eol=lf\n*.tsv text eol=lf\n*.csv text eol=lf\n*.py text eol=lf\n*.sh text eol=lf\n*.ps1 text eol=lf\n*.fasta text eol=lf\n*.faa text eol=lf\n*.clw text eol=lf\n*.nwk text eol=lf\n*.nex text eol=lf\nevidence/g0/** -text\n',encoding='utf-8')
allowed=[p for d in ['evidence','config','reports','status'] for p in (ROOT/d).rglob('*') if p.is_file()]
secret=re.compile(rb'(github_pat_[A-Za-z0-9_]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|sk-(?:proj-)?[A-Za-z0-9_-]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')
for p in allowed:
    if secret.search(p.read_bytes()): raise ValueError('Credential-like string; withhold: '+str(p.relative_to(ROOT)))
with (ROOT/'reports/stage01/SHA256SUMS.txt').open('w',encoding='utf-8',newline='\n') as f:
    for p in sorted(allowed):
        if p.name!='SHA256SUMS.txt': f.write(sha(p)+'  '+p.relative_to(ROOT).as_posix()+'\n')
print(json.dumps({'status':'PASS_APPROVED_PANEL_FREEZE','host':socket.gethostname(),'assemblies':196,'species':110,'copied_sources':len(provenance),'assertions':len(tests),'accessions_sha256':sha(ROOT/'config/approved_accessions.txt'),'sequence_analysis_started':False}))
