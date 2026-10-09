"""Finalize local preparation/source-review inventory; never scientific output."""
from pathlib import Path
import ast,hashlib,json

ROOT=Path(__file__).resolve().parents[2]
PACKAGE=ROOT/'work/stage05_curation'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')

doc=PACKAGE/'CLASSIFICATION_CONTRACT.md'
text=doc.read_text(encoding='utf-8')
text=text.replace('`python -B test_stage05_curation.py` and `python -B test_independent_curation.py`.',
                  '`python -B test_stage05_curation.py`, `python -B test_independent_curation.py` and `python -B test_multipart_type_ii.py`.')
text=text.replace('record23 producer-component tests and23 independent-checker component tests,',
                  'record23 producer-component tests and23 independent-checker component tests; `multipart_synthetic_validation.json` records12 additional family-path regressions,')
text=text.replace('records11 additional family-path regressions','records12 additional family-path regressions')
doc.write_text(text,encoding='utf-8',newline='\n')
py=list(PACKAGE.rglob('*.py'))
for p in py:ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
reports=[json.loads((PACKAGE/n).read_text()) for n in ('synthetic_validation.json','independent_synthetic_validation.json','multipart_synthetic_validation.json')]
assert all(r['failures']==r['errors']==0 and r['biological_jobs']==0 for r in reports)
review={'schema':'STAGE05_MULTIPART_SOURCE_REVIEW_V1','state':'PASS_SOURCE_REVIEW_AND_SYNTHETIC_REGRESSION_ONLY',
        'dataset_kind':'PREPARATION_NOT_SCIENTIFIC_OUTPUT','biological_jobs':0,'WSL_starts':0,'canonical_repository_mutations':0,
        'actual_panel_architecture_curation':'NOT_RUN','production_certificates_written':0,
        'primary_sources':[
          {'doi':'10.1371/journal.pone.0018819','url':'https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0018819',
           'evidence':'Results/Fig5: comparative-genomic TypeIIG architecture can include fused RM and a separate S. Predicted architecture does not establish biochemical activity.'},
          {'doi':'10.3389/fmicb.2022.888435','url':'https://www.frontiersin.org/journals/microbiology/articles/10.3389/fmicb.2022.888435/full',
           'evidence':'Primary BsaXI experiment explicitly classifies TypeIIB and reconstitutes activity using separate RM fusion and S. Do not call it IIG from fusion alone.'},
          {'doi':'10.1093/nar/gkg274','url':'https://doi.org/10.1093/nar/gkg274',
           'evidence':'Original nomenclature allows overlapping TypeII designations; fusion alone does not establish IIG.'}],
        'model_scope_sha256':sha(PACKAGE/'pinned_model_candidate_scope.json'),
        'model_limit':'No exact retained BcgI/BsaXI assignment or demonstrated separate-S family mapping for numbered IIG/FAM profiles. Native labels are candidate proposals.',
        'concrete_rejection_reproduced':'Original retained independent architecture rejects complete two-gene synthetic IIG solely through obsolete one-gene condition.',
        'fix':'Producer and independently authored wrapper require separately executed exact family/source/AA/native-domain review for fused RM plus cognate separate S. Wrapper retains core source/domain/role/context checks and native/reviewed subtype provenance.',
        'tests_run':sum(r['tests_run'] for r in reports),'failures':0,'errors':0,'python_sources_parsed':len(py),
        'retained_bytes_unchanged':{n:sha(PACKAGE/n) for n in ('retained/stage05_curation_adapter.py','retained/stage05_evidence.py','retained/independent_curated_v2.py','retained/stage05_architecture_policy_original.py')},
        'tree_freeze_review':{'path':str(ROOT/'work/independent_tree_check.py'),'sha256':sha(ROOT/'work/independent_tree_check.py'),
          'state':'PASS_READ_ONLY_COPY_INTEGRITY_SOURCE_REVIEW','tests_by_this_review':0,
          'findings':['Parsed captured tree bytes equal prevalidation native pin','Authoritative NWK equals captured parsed hash; NEXUS built from same bytes and signatures compared',
                      'Every native freeze copy equals captured native pin; native membership checked','Accepted input/config/panel/partition/cache copies equal previously captured expected hashes']},
        'drivefs_smoke_review':{'path':str(ROOT/'work/stage5_drivefs_filesystem_smoke.py'),'sha256':sha(ROOT/'work/stage5_drivefs_filesystem_smoke.py'),
          'state':'PASS_READ_ONLY_SCOPE_AND_INTEGRITY_SOURCE_REVIEW','actual_Linux_interoperability':'NOT_RUN',
          'limit':'Byte-pinned Windows caller lock receipt does not independently prove live Windows lease ownership; caller owns the actual lock.'}}
write(Path(__file__).parent/'source_review.json',review)
report_path=PACKAGE/'preparation_report.json';report=json.loads(report_path.read_text())
report.update(tests_run=review['tests_run'],python_sources_parsed=len(py),failures=0,errors=0)
capability='Independently family-supported fused-RM plus separate-S TypeII path with explicit subtype basis; original native singlechain path preserved'
if capability not in report['capabilities']:report['capabilities'].append(capability)
report['multipart_source_review']={'path':'../stage05_curation_review/source_review.json','sha256':sha(Path(__file__).parent/'source_review.json'),
                                  'actual_family_assignments':'NOT_RUN','additional_synthetic_tests':reports[-1]['tests_run']}
files=sorted(p for p in PACKAGE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ('preparation_report.json','SHA256SUMS'))
report['artifacts']={p.relative_to(PACKAGE).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in files}
write(report_path,report)
files.append(report_path)
(PACKAGE/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.relative_to(PACKAGE).as_posix()+'\n' for p in sorted(files)),encoding='utf-8',newline='\n')
print(json.dumps({'tests_run':review['tests_run'],'python_sources_parsed':len(py),'artifacts':{str(p.relative_to(ROOT)):sha(p) for p in
    (PACKAGE/'stage05_architecture_policy.py',PACKAGE/'stage05_curation_atomic.py',PACKAGE/'validate_atomic_curation.py',PACKAGE/'CLASSIFICATION_CONTRACT.md',
     PACKAGE/'FOLLOW_ON_METHODS.md',PACKAGE/'test_multipart_type_ii.py',PACKAGE/'preparation_report.json',PACKAGE/'SHA256SUMS',Path(__file__).parent/'source_review.json')}},indent=2))
