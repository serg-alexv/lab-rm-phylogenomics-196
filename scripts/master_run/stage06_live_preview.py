"""Explicit provisional Stage6 snapshot from accepted tree and accepted closed genomes.

No inference, detector execution, final curation acceptance or final-figure gate.
Default NOOP; --render consumes only pinned immutable C-work snapshot files.
"""
from pathlib import Path
import argparse, csv, datetime, hashlib, importlib.util, json, math, re, shutil, stat

WORK=Path(__file__).resolve().parent
PANEL_SHA='85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6'
TREE_SHA='f886c0134ab662a05aae2b1c1a26ed364749af250400f769ce6e63f1f7a8ba19'
TREE_ACCEPTANCE_SHA='f14b097aac1705c2632307eaadf423febdc3154cafe370aace78dd8196044d49'
WRAPPER_SHA='cdd81d2870dbc7c03845721199a98d4f6b51a23fb94ebb19fa71311bb9e2ed66'
CURATION_CHECKER_SHA='89a42d63401ef1ef3479690546a3c8cad4da679517aa2ed7da6b4e6716b6af0c'
PINS={'stage06_render.py':'55cdbed8829296379d4c8a114885643fc7debc3c98382be177e9adeb7edfb1cc',
      'stage05_curation/rm_matrix.py':'7716f722f25b582af990469d4e5120d4de22828b87c89cf334d2d9f9723c7db9'}
WATERMARK='PREVIEW_PENDING_SCIENTIFIC_COMPLETION'
KINDS=('I','II','III','IV')

def require(ok,message):
    if not ok:raise ValueError(message)

def sha(raw):return hashlib.sha256(raw).hexdigest()

def plain(path):
    path=Path(path)
    require(path.is_absolute() and WORK in path.parents and path==path.resolve(),'Direct immutable C-work snapshot path required')
    for node in (path,*path.parents):
        info=node.lstat()
        require(not node.is_symlink() and not getattr(info,'st_file_attributes',0)&0x400,'Snapshot reparse/alias rejected')
    info=path.stat();require(stat.S_ISREG(info.st_mode) and info.st_size<=32*1024**2,'Bounded regular snapshot file required')
    return path

def pinned(spec):
    require(isinstance(spec,dict) and set(spec)=={'path','sha256'} and re.fullmatch('[a-f0-9]{64}',spec['sha256']),'Exact path/SHA snapshot specification required')
    path=plain(spec['path']);raw=path.read_bytes();require(sha(raw)==spec['sha256'],'Snapshot file SHA differs: '+path.name)
    return path,raw

def module(name,relative):
    path,raw=pinned({'path':str(WORK/relative),'sha256':PINS[relative]})
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    # dataclasses resolves its defining module during the normal import.
    import sys
    sys.modules[name]=value;spec.loader.exec_module(value)
    require(sha(path.read_bytes())==sha(raw),'Frozen renderer/serializer changed during import')
    return value

def inputs(snapshot,snapshot_sha):
    snapshot_path,raw=pinned({'path':str(snapshot),'sha256':snapshot_sha});doc=json.loads(raw)
    require(doc.get('schema')=='RM_LIVE_PREVIEW_SNAPSHOT_V1' and set(doc)<=
      {'schema','tree','approved','tree_acceptance','accepted_genomes','pending'},'Explicit preview snapshot schema required')
    paths={};pins={}
    for role,expected in [('tree',TREE_SHA),('approved',PANEL_SHA),('tree_acceptance',TREE_ACCEPTANCE_SHA)]:
        path,data=pinned(doc[role]);require(sha(data)==expected,'Current accepted tree/panel/readback pin differs')
        paths[role]=path;pins[str(path)]=sha(data)
    accepted=json.loads(paths['tree_acceptance'].read_bytes())
    require(accepted['state']=='PASS_FRESH_REMOTE_ACCEPTED_PRIMARY196_FULL_PAYLOAD' and accepted['independent_remote_gate_passed'] is True,'Independent accepted Stage4 readback missing')
    members={r['member']:r for r in accepted['members']}
    require(members['accepted/host.treefile']['sha256']==TREE_SHA and members['accepted/host.treefile']['crc_verified'] is True
      and members['accepted/accepted_approved_accessions.txt']['sha256']==PANEL_SHA
      and members['accepted/accepted_approved_accessions.txt']['crc_verified'] is True,'Accepted release tree/panel members differ')
    R=module('live_preview_frozen_renderer','stage06_render.py');M=module('live_preview_frozen_serializer','stage05_curation/rm_matrix.py')
    panel=M.approved(paths['approved']);root=R.Newick(paths['tree'].read_text(encoding='utf-8-sig')).parse()
    all_nodes=list(R.nodes(root));leaves=[n for n in all_nodes if not n.children]
    require(len(leaves)==196 and len({n.label for n in leaves})==196 and {n.label for n in leaves}==set(panel),'Accepted full196 tree/accession join differs')
    require(all(n.length is not None and math.isfinite(n.length) and n.length>=0 for n in all_nodes[1:]),'Accepted tree branch length missing/invalid')
    entries=doc.get('accepted_genomes',[]);require(isinstance(entries,list) and len(entries)<=196,'Bounded accepted-genome list required')
    cells={(a,t):M.initial(a,t) for a in panel for t in KINDS};review={};sources=[];total=0
    for entry in entries:
        require(isinstance(entry,dict) and set(entry)=={'accession','receipt','cells','source_manifest'},'Exact accepted-genome snapshot fields required')
        a=entry['accession'];require(a in panel and a not in review,'Duplicate/out-of-panel accepted genome')
        opened={}
        for role in ('receipt','cells','source_manifest'):
            path,data=pinned(entry[role]);total+=len(data);require(total<=256*1024**2,'Bounded total accepted snapshots exceeded')
            pins[str(path)]=sha(data);opened[role]=json.loads(data)
            sources.append((path,'accepted/'+a+'/'+{'receipt':'single_genome_curation_validation.json','cells':'independently_reconstructed_cells.json','source_manifest':'single_genome_source_manifest.json'}[role]))
        cert=opened['receipt'];rows=opened['cells'];manifest=opened['source_manifest']
        require(cert.get('schema')=='RM_SINGLE_GENOME_INDEPENDENT_CURATION_ACCEPTANCE_V1'
          and cert.get('status')=='PASS_INDEPENDENT_SINGLE_GENOME_RM_CURATION' and cert.get('dataset_kind')=='PRODUCTION'
          and cert.get('accession')==a and cert.get('accepted_single_genome_curation') is True
          and all(type(cert.get(k)) is int for k in ('accession_count','cell_count','approved_accession_count','biological_searches_repeated'))
          and cert.get('accession_count')==1 and cert.get('cell_count')==4 and cert.get('approved_accession_count')==196
          and cert.get('approved_sha256')==PANEL_SHA and cert.get('cells_sha256')==entry['cells']['sha256']
          and cert.get('source_manifest_sha256')==entry['source_manifest']['sha256']
          and cert.get('wrapper_sha256')==WRAPPER_SHA and cert.get('independent_checker_sha256')==CURATION_CHECKER_SHA
          and cert.get('per_genome_owned_native_closure_verified') is True
          and cert.get('operational_closure_scope')=='SELECTED_GENOME_MANIFEST_PINNED_LINUX_NATIVE_LAUNCHES_ONLY'
          and all(cert.get(k) is False for k in ('full_panel_complete','final_matrix_acceptance','final_figure_acceptance'))
          and cert.get('functional_activity_claim')=='NONE' and cert.get('biological_searches_repeated')==0
          and re.fullmatch('[a-f0-9]{64}',cert.get('complete_receipt_sha256','')),'Genuine independently accepted closed four-cell receipt required')
        require(manifest.get('schema')=='RM_SINGLE_GENOME_INDEPENDENT_CURATION_SOURCE_MANIFEST_V1'
          and manifest.get('dataset_kind')=='PRODUCTION' and manifest.get('accession')==a
          and manifest.get('approved_sha256')==PANEL_SHA and manifest.get('wrapper_sha256')==WRAPPER_SHA
          and manifest.get('independent_checker_sha256')==CURATION_CHECKER_SHA
          and manifest.get('functional_activity_claim')=='NONE'
          and manifest.get('audit',{}).get('complete_sha256')==cert['complete_receipt_sha256'],'Accepted source manifest identity differs')
        require(isinstance(rows,list) and len(rows)==4 and {(r['assembly_accession'],r['rm_type']) for r in rows}=={(a,t) for t in KINDS},'Exactly four accepted accession/type cells required')
        for row in rows:M.normalize(row,a);cells[(a,row['rm_type'])]=row
        review[a]={'accession':a,'review_state':'INDEPENDENT_SINGLE_GENOME_ACCEPTED','reported_execution_state':'CLOSED_COMPLETE',
          'reason':'Actual independently accepted four-cell snapshot; accepted NA remains unresolved.', 'receipt_sha256':entry['receipt']['sha256']}
    pending=doc.get('pending',[]);require(isinstance(pending,list) and len(pending)<=196,'Bounded pending metadata required')
    pending_by={}
    for row in pending:
        require(isinstance(row,dict) and set(row)=={'accession','execution_state','reason'} and row['accession'] in panel
          and row['accession'] not in review and row['accession'] not in pending_by
          and row['execution_state'] in {'NOT_RUN','PREPARED','RUNNING','DEFERRED_RESOURCE','FAILED_RETRYABLE','FAILED_FATAL','RAW_COMPLETE_PENDING_CURATION','CURATION_PENDING'}
          and isinstance(row['reason'],str) and 0<len(row['reason'].strip())<=1000,'Explicit unique pending state/reason required')
        pending_by[row['accession']]=row
    wide=[];long=[]
    for a in panel:
        output={'accession':a}
        for t in KINDS:state,value=M.normalize(cells[(a,t)],a);long.append(state);output['Type_'+t]=value
        wide.append(output)
        if a not in review:
            pending_row=pending_by.get(a,{'execution_state':'NOT_RUN','reason':'No independently accepted closed four-cell snapshot supplied.'})
            review[a]={'accession':a,'review_state':'PENDING_SCIENTIFIC_COMPLETION','reported_execution_state':pending_row['execution_state'],
              'reason':pending_row['reason'],'receipt_sha256':''}
    require(len(wide)==196 and len(long)==784,'Preview exact full-panel product differs')
    pins[str(snapshot_path)]=snapshot_sha
    return R,M,root,leaves,wide,long,[review[a] for a in panel],pins,paths,sources

def render(snapshot,snapshot_sha,output):
    R,M,root,leaves,wide,long,reviews,pins,paths,sources=inputs(snapshot,snapshot_sha)
    output=Path(output);require(output.is_absolute() and output.parent==WORK and output==output.resolve() and not output.exists(),'Fresh direct C-work preview output required')
    count=sum(r['review_state']=='INDEPENDENT_SINGLE_GENOME_ACCEPTED' for r in reviews)
    provenance={'dataset_kind':'PROVISIONAL','curation_status':WATERMARK,'documented_exception_count':0,
      'snapshot_sha256':snapshot_sha,'tree_sha256':TREE_SHA,'approved_sha256':PANEL_SHA,'accepted_genome_count':count,
      'full_panel_complete':False,'final_matrix_acceptance':False,'final_figure_acceptance':False,'functional_activity_claim':'NONE'}
    values={r['accession']:{t:r[t] for t in R.TYPES} for r in wide};states={(r['accession'],'Type_'+r['rm_type']):r for r in long}
    scene=R.scene(root,leaves,values,states,provenance)
    for primitive in scene['primitives']:
        if primitive.get('role')=='title':primitive.update(text=WATERMARK,size=13)
        if primitive.get('role')=='annotation':primitive['text']=f'Accepted unrooted196-tip tree; {count}/196 genomes independently curated. Provisional snapshot; pending cells remain NA.'
    scene['typography']=R.typography_check(scene['primitives']);scene_sha=sha(R.canonical(scene).encode())
    # Reopen every immutable input before creating any output; no live native path is read.
    for path,pin in pins.items():require(sha(plain(path).read_bytes())==pin,'Snapshot drift before export')
    output.mkdir()
    for role,name in [('tree','host_tree.nwk'),('approved','approved_accessions.txt'),('tree_acceptance','accepted_stage04_readback.json')]:
        shutil.copyfile(paths[role],output/name)
        require(sha((output/name).read_bytes())==pins[str(paths[role])],'Copied accepted tree/panel/readback differs')
    shutil.copyfile(snapshot,output/'preview_snapshot.json')
    require(sha((output/'preview_snapshot.json').read_bytes())==snapshot_sha,'Copied preview snapshot differs')
    for path,relative in sources:
        dest=output/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
        require(sha(dest.read_bytes())==pins[str(path)],'Copied accepted snapshot differs')
    M.table(output/'rm_type_presence_absence.tsv',wide,['accession',*R.TYPES]);M.table(output/'rm_type_state.tsv',long,M.STATE_FIELDS)
    M.table(output/'preview_review_state.tsv',reviews,['accession','review_state','reported_execution_state','reason','receipt_sha256'])
    M.table(output/'cell_mapping.tsv',scene['cell_mapping'],list(scene['cell_mapping'][0]))
    (output/'scene.json').write_text(R.canonical(scene)+'\n',encoding='utf-8',newline='\n')
    (output/'branch_mapping.json').write_text(json.dumps(scene['branches'],indent=2)+'\n',encoding='utf-8',newline='\n')
    R.svg_export(scene,output/'preview_circular_rm.svg',scene_sha);R.pdf_export(scene,output/'preview_circular_rm.pdf',scene_sha)
    R.itol_exports(output,scene,values)
    # Every convenience export also carries explicit provisional metadata.
    for path in output.glob('itol_*.txt'):
        text=path.read_text(encoding='utf-8');text=re.sub(r'(?m)^DATASET_LABEL\t', 'DATASET_LABEL\t'+WATERMARK+' | ',text)
        path.write_text(text,encoding='utf-8',newline='\n')
    (output/'README.txt').write_text(WATERMARK+'\nImmutable accepted tree and accepted closed-genome cells only. Missing curations are NOT_RUN/NA.\nReported execution states/reasons are queue metadata, not independently accepted biological results.\nColoured: accepted complete predicted architecture. White: reviewed full-search nondetection. Grey: pending/partial/unresolved.\nThis snapshot never accepts the final matrix, curation or figure. Unchanged final196/784 audit and renderer remain mandatory.\nThe four iTOL full-state strips retain grey NA; binary convenience omits NA. No iTOL server import occurred.\n',encoding='utf-8',newline='\n')
    require(len(scene['tip_order'])==196 and len(scene['cell_mapping'])==784
      and all(values[r['accession']][t]=='NA' for r in reviews if r['review_state']=='PENDING_SCIENTIFIC_COMPLETION' for t in R.TYPES), 'Preview pending cell/self-check failed')
    for path,pin in pins.items():require(sha(plain(path).read_bytes())==pin,'Snapshot drift during export')
    manifest={'schema':'RM_PROVISIONAL_STAGE06_EXPORT_V1','state':WATERMARK,'dataset_kind':'PROVISIONAL',
      'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'adapter_sha256':sha(Path(__file__).read_bytes()),'helper_pins':PINS,
      **provenance,'tip_count':196,'cell_count':784,'scene_sha256':scene_sha,'inputs':pins,
      'artifact_check_scope':'PRODUCER_SERIALIZATION_SELF_CHECK_ONLY; independent preview review required; no final scientific acceptance.',
      'outputs':{p.relative_to(output).as_posix():sha(p.read_bytes()) for p in sorted(output.rglob('*')) if p.is_file()}}
    (output/'preview_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    return manifest

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render',action='store_true')
    parser.add_argument('--snapshot',type=Path);parser.add_argument('--snapshot-sha256');parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if not args.render:print(json.dumps({'state':'NO_OP_PROVISIONAL_STAGE06_PREVIEW','final_figure_acceptance':False}));return 0
    require(args.snapshot and args.snapshot_sha256 and args.output,'Explicit pinned snapshot and fresh output required')
    result=render(args.snapshot,args.snapshot_sha256,args.output)
    print(json.dumps({'state':result['state'],'accepted_genome_count':result['accepted_genome_count'],'output':str(args.output)}));return 0

if __name__=='__main__':raise SystemExit(main())
