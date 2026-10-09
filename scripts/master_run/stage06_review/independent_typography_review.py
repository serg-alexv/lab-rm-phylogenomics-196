"""Read existing synthetic vector proof; creates only a local review receipt."""
from pathlib import Path
import hashlib,json,math
from pypdf import PdfReader
from reportlab.pdfbase.pdfmetrics import getAscentDescent

ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'work'
V4=WORK/'stage06_density_synthetic_v4';V3=WORK/'stage06_density_synthetic_v3'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def demand(ok,msg):
    if not ok:raise ValueError(msg)

source=PdfReader(V4/'render/circular_rm.pdf');proof=PdfReader(V4/'print_proof_180mm.pdf')
demand(len(source.pages)==len(proof.pages)==1,'Single-page source/proof required')
original,printed=source.pages[0],proof.pages[0]
ops=printed.get_contents().operations;scale=180*72/25.4/1100
demand(ops[0]==([],b'q') and ops[1][1]==b'cm' and ops[-1]==([],b'Q'),'Unexpected proof wrappers')
demand(all(math.isclose(float(a),b,abs_tol=1e-8) for a,b in zip(ops[1][0],(scale,0,0,scale,0,0))),'Nonuniform print scaling')
demand(ops[2:-1]==original.get_contents().operations,'Proof changes source vector/text operators')
demand(math.isclose(float(printed.mediabox.width),180*72/25.4,abs_tol=1e-6)
       and math.isclose(float(printed.mediabox.height),1180*scale,abs_tol=1e-6),'Wrong physical proof dimensions')
for page in (original,printed):demand(not page['/Resources'].get('/XObject'),'Proof contains an unexpected raster/form replacement')
scene=load(V4/'render/scene.json');old=load(V3/'render/scene.json')
roles={'phylogenetic_edge','topology_connector','nonphylogenetic_tip_leader','ring_cell'}
def geometry(s):return [{k:p[k] for k in ('kind','role','points','stroke','fill','width','dash') if k in p}
                       for p in s['primitives'] if p['role'] in roles]
demand(geometry(scene)==geometry(old),'Biological geometry/color changed in typography delta')
tips={p['text']:p for p in scene['primitives'] if p['role']=='tip_label'}
demand(len(tips)==196 and all(t.startswith('TEST_') for t in tips),'Synthetic realistic-width IDs required')
observed=[]
def visit(text,cm,tm,font,size):
    if text.strip():observed.append((text.strip(),cm,tm,font.get('/BaseFont'),size))
original.extract_text(visitor_text=visit)
demand(len(observed)==206,'Actual PDF text count differs')
count=0;ascent,descent=getAscentDescent('Helvetica',12)
for text,cm,tm,font,size in observed:
    demand(font=='/Helvetica' and size>=11,'Actual font/size differs')
    if text not in tips:continue
    demand(size==12,'Actual tip font differs');p=tips[text];angle=math.radians(p['rotation'])
    # In scene coordinates the font metric center must lie on its radial anchor.
    center=(cm[4] + (ascent+descent)/2*math.sin(angle),1180-cm[5] - (ascent+descent)/2*math.cos(angle))
    demand(all(math.isclose(a,b,abs_tol=.001) for a,b in zip(center,p['radial_anchor'])),'Actual PDF tip baseline is not metric-centered')
    count+=1
demand(count==196,'Actual PDF labels omitted')
report={'schema':'STAGE06_INDEPENDENT_TYPOGRAPHY_SOURCE_PROOF_REVIEW_V1','status':'PASS_SYNTHETIC_SOURCE_VECTOR_AND_VISUAL_REVIEW',
        'dataset_kind':'SYNTHETIC','actual_scientific_figure':'NOT_RUN','biological_jobs':0,'WSL_starts':0,'canonical_repository_mutations':0,
        'actual_PDF_text_objects':len(observed),'actual_tip_labels':count,'source_vector_operator_identity_after_uniform_print_scaling':True,
        'v3_v4_branches_connectors_leaders_and_ring_geometry_colors_identical':True,'actual_metric_centered_tip_baselines':True,
        'print_width_mm':180,'actual_tip_font_print_points':12*scale,'actual_note_font_print_points':11*scale,
        'visual_review':'Inspected existing 300dpi proof at 2126x2281: all tip labels distinct, no visible collisions/clipping, rings and legend clear. Small 180mm physical text size is explicitly reported.',
        'source_review':'Helvetica metric rectangle transforms and separating-axis overlap tests are coherent; independent checker binds actual SVG attributes and actual PDF Helvetica transforms/fonts before bounds/overlap checks.',
        'operational_limitations':'Synthetic visual/layout review only. iTOL server/UI import and actual accepted biological render remain NOT_RUN.',
        'files':{str(p.relative_to(ROOT)):sha(p) for p in (WORK/'stage06_render.py',WORK/'check_stage06_outputs.py',
                   V4/'render/circular_rm.pdf',V4/'print_proof_180mm.pdf',V4/'print_proof_180mm_300dpi.png',V4/'artifact_validation_typography.json')}}
(Path(__file__).parent/'source_proof_review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
