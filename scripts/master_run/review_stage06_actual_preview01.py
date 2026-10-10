"""Read-only independent review of this exact provisional accepted-tree export."""
from pathlib import Path
import csv,hashlib,importlib.util,json,math,re,xml.etree.ElementTree as ET
from pypdf import PdfReader
from pypdf.generic import ContentStream
W=Path(__file__).resolve().parent
OUT=W/'stage06_actual_preview01'
SNAP=W/'stage06_actual_snapshot01'
MANIFEST_SHA='1da4f757a1841c5bbd662f43cb24f434ee20243369a70562d0b9077b2c85848e'
SNAP_SHA='78efd7dd06475404acc24a38b54ec8894eb88a3ac2337efc80d2a1037d5aab91'
TREE_SHA='f886c0134ab662a05aae2b1c1a26ed364749af250400f769ce6e63f1f7a8ba19'
PANEL_SHA='85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6'
CHECKER_SHA='3a23f3de7d971bea6210cd2405c57af48fa5ba3ae2ba4bb66ee4357aa3644818'
MARK='PREVIEW_PENDING_SCIENTIFIC_COMPLETION'
TYPES=('Type_I','Type_II','Type_III','Type_IV')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
def table(name):
    with (OUT/name).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter='\t'))
def close(a,b,tol=1e-9):return math.isclose(a,b,rel_tol=1e-9,abs_tol=tol)

def parse_newick(raw):
    tokens=re.findall(r'[(),:;]|[^(),:;\s]+',raw);position=0
    def node():
        nonlocal position
        children=[];name='';length=None
        if tokens[position]=='(':
            position+=1;children.append(node())
            while tokens[position]==',':position+=1;children.append(node())
            assert tokens[position]==')';position+=1
        if tokens[position] not in ',):;':name=tokens[position];position+=1
        if tokens[position]==':':position+=1;length=float(tokens[position]);position+=1
        return dict(name=name,length=length,children=children)
    root=node();assert tokens[position:]==[';'];return root

def main():
    assert sha(OUT/'preview_manifest.json')==MANIFEST_SHA and sha(SNAP/'snapshot.json')==SNAP_SHA
    m=load(OUT/'preview_manifest.json');snapshot=load(SNAP/'snapshot.json')
    checked={}
    def bind(p,pin):
        assert p.is_file() and not p.is_symlink() and p.stat().st_size<=32*1024**2
        assert sha(p)==pin,str(p);checked[str(p.relative_to(W))]={'bytes':p.stat().st_size,'sha256':pin}
    bind(OUT/'preview_manifest.json',MANIFEST_SHA)
    for name,pin in m['outputs'].items():assert Path(name).name==name;bind(OUT/name,pin)
    assert {p.name for p in OUT.iterdir()}==set(m['outputs'])|{'preview_manifest.json'}
    for path,pin in m['inputs'].items():assert Path(path).parent==SNAP;bind(Path(path),pin)
    assert m['schema']=='RM_PROVISIONAL_STAGE06_EXPORT_V1' and m['state']==MARK and m['dataset_kind']=='PROVISIONAL'
    assert m['adapter_sha256']==sha(W/'stage06_live_preview.py')=='49171dd82ed050d3f35daf82217c6ac747ef137c125691787c4f3bb0526034b8'
    assert m['accepted_genome_count']==0 and m['tip_count']==196 and m['cell_count']==784
    assert all(m[k] is False for k in ('full_panel_complete','final_matrix_acceptance','final_figure_acceptance'))
    assert snapshot['accepted_genomes']==[] and snapshot['pending']==[{'accession':'GCF_000009425.1','execution_state':'RUNNING','reason':'Prepared inputs; bounded first PADLOC admission pending at snapshot creation; no native search accepted.'}]
    assert sha(OUT/'host_tree.nwk')==TREE_SHA and sha(OUT/'approved_accessions.txt')==PANEL_SHA
    assert (OUT/'host_tree.nwk').read_bytes()==(SNAP/'host.treefile').read_bytes()
    scene=load(OUT/'scene.json');canonical=json.dumps(scene,sort_keys=True,ensure_ascii=True,separators=(',',':')).encode()
    assert hashlib.sha256(canonical).hexdigest()==m['scene_sha256']
    assert scene['ring_order']==list(TYPES) and scene['rooting']=='UNROOTED_NO_VALIDATED_OUTGROUP'
    assert scene['provenance']['dataset_kind']=='PROVISIONAL' and scene['provenance']['accepted_genome_count']==0
    assert all(scene['provenance'][k] is False for k in ('full_panel_complete','final_matrix_acceptance','final_figure_acceptance'))
    panel=(OUT/'approved_accessions.txt').read_text().split();assert len(panel)==len(set(panel))==196
    root=parse_newick((OUT/'host_tree.nwk').read_text());edges={};tips=[]
    def walk(n,depth=0):
        if not n['children']:tips.append(n['name']);desc=[n['name']]
        else:
            desc=[]
            for child in n['children']:
                assert child['length'] is not None and math.isfinite(child['length']) and child['length']>=0
                child_desc=walk(child,depth+child['length'])
                edges[tuple(child_desc)]=(child['name'],child['length'],depth,depth+child['length']);desc+=child_desc
        return desc
    walk(root);assert tips==scene['tip_order'] and set(tips)==set(panel)
    branches=load(OUT/'branch_mapping.json');assert branches==scene['branches'] and len(branches)==len(edges)
    for b in branches:
        name,length,start,end=edges[tuple(b['descendant_accessions'])]
        assert b['input_label']==name and b['input_branch_length']==length
        assert close(b['radial_start']/scene['radial_points_per_unit'],start) and close(b['radial_end']/scene['radial_points_per_unit'],end)
    wide=table('rm_type_presence_absence.tsv');states=table('rm_type_state.tsv');mapping=table('cell_mapping.tsv');review=table('preview_review_state.tsv')
    expected={(a,t) for a in panel for t in TYPES}
    assert len(wide)==196 and {r['accession'] for r in wide}==set(panel) and all(r[t]=='NA' for r in wide for t in TYPES)
    assert len(states)==784 and {(r['accession'],'Type_'+r['rm_type']) for r in states}==expected
    assert all(r['state']=='NOT_RUN' and r['search_complete']=='False' and r['complete_count']==r['partial_count']==r['candidate_count']=='0' for r in states)
    assert len(mapping)==784 and {(r['accession'],r['rm_type']) for r in mapping}==expected
    assert all(r['value']=='NA' and r['fill']=='#9e9e9e' and r['state']=='NOT_RUN' for r in mapping)
    assert len(review)==196 and {r['accession'] for r in review}==set(panel)
    assert all(r['review_state']=='PENDING_SCIENTIFIC_COMPLETION' and r['receipt_sha256']=='' for r in review)
    running=[r for r in review if r['reported_execution_state']=='RUNNING'];assert len(running)==1 and running[0]['accession']=='GCF_000009425.1'
    assert all(r['reported_execution_state']=='NOT_RUN' for r in review if r['accession']!='GCF_000009425.1')
    xml=ET.parse(OUT/'preview_circular_rm.svg').getroot();metadata=json.loads(next(x.text for x in xml if x.tag.endswith('metadata')))
    assert metadata['scene_sha256']==m['scene_sha256'] and metadata['dataset_kind']=='PROVISIONAL'
    primitives=scene['primitives'];shapes=[x for x in xml if x.get('data-role')];assert len(shapes)==len(primitives)
    for shape,p in zip(shapes,primitives):
        assert shape.get('data-role')==p['role']
        if p['kind'] in ('line','polygon'):assert shape.get('points')==' '.join(f'{x:.6f},{y:.6f}' for x,y in p['points'])
        else:
            x,y=p['point'];assert shape.text==p['text'] and shape.get('x')==f'{x:.6f}' and shape.get('y')==f'{y:.6f}' and float(shape.get('font-size'))==p['size']
    svg_cells=[x for x in shapes if x.get('data-role')=='ring_cell'];assert len(svg_cells)==784
    assert {(x.get('data-accession'),x.get('data-rm-type')) for x in svg_cells}==expected
    assert all(x.get('fill')=='#9e9e9e' and x.get('data-value')=='NA' for x in svg_cells)
    assert [x.text for x in shapes if x.get('data-role')=='tip_label']==tips
    assert MARK in ''.join(x.text or '' for x in xml)
    assert sha(W/'check_stage06_outputs.py')==CHECKER_SHA
    spec=importlib.util.spec_from_file_location('unchanged_final_artifact_checker',W/'check_stage06_outputs.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
    pdf=PdfReader(OUT/'preview_circular_rm.pdf');assert len(pdf.pages)==1 and json.loads(pdf.metadata.subject)['scene_sha256']==m['scene_sha256']
    page=pdf.pages[0];assert not page.images and float(page.mediabox.width)==scene['width'] and float(page.mediabox.height)==scene['height']
    typography=C.actual_pdf_typography(page,scene);ops=ContentStream(page.get_contents(),pdf).operations
    text=[str(args[0]) for args,op in ops if op==b'Tj'];assert text==[p['text'] for p in primitives if p['kind']=='text'] and MARK in text
    assert all(text.count(a)==1 for a in panel)
    geometry=iter(p for p in primitives if p['kind'] in ('line','polygon'));points=[];closed=False;fill=None;painted=0
    for args,op in ops:
        if op==b'n':points=[];closed=False
        elif op in (b'm',b'l'):points.append(tuple(map(float,args)))
        elif op==b'h':closed=True
        elif op==b'rg':fill=tuple(map(float,args))
        elif op in (b'S',b'B',b'B*',b'b',b'b*',b'f',b'f*'):
            p=next(geometry,None);assert p is not None
            wanted=[(x,scene['height']-y) for x,y in p['points']]
            assert len(points)==len(wanted) and all(close(a,b,.001) for pair,target in zip(points,wanted) for a,b in zip(pair,target))
            assert closed==(p['kind']=='polygon')
            if closed:assert all(close(a,int(p['fill'][i:i+2],16)/255,1e-6) for a,i in zip(fill,(1,3,5)))
            painted+=1;points=[];closed=False
    assert next(geometry,None) is None
    for i,t in enumerate(TYPES):
        lines=(OUT/f'itol_{i+1:02d}_{t}_full_state.txt').read_text().splitlines();rows=[x.split('\t') for x in lines[lines.index('DATA')+1:]]
        assert lines[0]=='DATASET_COLORSTRIP' and any(x.startswith('DATASET_LABEL\t'+MARK) for x in lines)
        assert [r[0] for r in rows]==tips and all(r[1:] == ['#9e9e9e','unknown'] for r in rows)
    lines=(OUT/'itol_binary_convenience.txt').read_text().splitlines();rows=[x.split('\t') for x in lines[lines.index('DATA')+1:]]
    assert [r[0] for r in rows]==tips and all(r[1:]==['-1']*4 for r in rows) and any(x.startswith('DATASET_LABEL\t'+MARK) for x in lines)
    assert not (OUT/'provenance.json').exists() and not (OUT/'curation_validation.json').exists()
    for name,item in checked.items():assert sha(W/name)==item['sha256']
    report={'schema':'RM_PROVISIONAL_ACTUAL_STAGE06_INDEPENDENT_ARTIFACT_REVIEW_V1','state':'PASS_ACTUAL_PROVISIONAL_ARTIFACT_CONSISTENCY_ONLY',
      'reviewer_source_sha256':sha(__file__),'checked_files':checked,'accepted_tree_sha256':TREE_SHA,'snapshot_sha256':SNAP_SHA,
      'preview_manifest_sha256':MANIFEST_SHA,'scene_sha256':m['scene_sha256'],'tip_count':196,'cell_count':784,'accepted_genomes':0,
      'pending_NA_cells':784,'independent_newick_branch_count':len(edges),'actual_shared_vector_paths_checked':painted,
      'svg_pdf_same_scene_geometry':True,'actual_pdf_typography':typography,'iTOL_full_state_grey_NA_and_binary_omitted':True,
      'visible_preview_watermark':True,'pending_queue_state_scope':'Immutable 04:34 snapshot reports first genome RUNNING at admission; this does not assert any native search or result acceptance.',
      'full_panel_complete':False,'final_matrix_acceptance':False,'final_figure_acceptance':False,'functional_activity_claim':'NONE',
      'visual_raster_observation':'Separate optional reviewer observation; programmatic actual vector geometry/text checks PASS.',
      'original_final_artifact_checker_sha256':CHECKER_SHA,'original_final_production_gates_unchanged':True,
      'limitations':['Provisional artifact consistency only; no new biological acceptance.','No iTOL server import/UI verification.','GitHub publication/readback pending root.'],
      'effects':{'detector_execution':False,'WSL_or_UNC_or_native_owner':False,'original_artifact_changes':False,'Git_mutation':False}}
    path=W/'stage06_actual_preview01_independent_review.json'
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps({'path':str(path),'sha256':sha(path),'state':report['state'],'files':len(checked),'branches':len(edges),'reviewer_sha256':sha(__file__)}))
if __name__=='__main__':main()
