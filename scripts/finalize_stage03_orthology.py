"""Publish original search evidence and independently curated host markers."""
from pathlib import Path
import json,msvcrt,os,shutil
import production_resume as w
import finalize_stage03 as original
from workflow_publication import commit,check
from portable_release import make_zip,publish_frozen

R=w.R;PUBLIC=R/'reports/stage03';STAGING=R/'release_staging/stage03'
RAW=R/'.work/stage03_markers_v1';VIEW=R/'.work/stage03_orthology_v2'
GATE=R/'.work/stage03_curated_validation';SOURCE=R/'.work/source_locus_inputs_v1'
ORTHOLOGY_CONFIG=R/'config/host_orthology_stage03_v2.json'
w.LOG=PUBLIC/'publication_commands.jsonl'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def require(ok,why):
    if not ok:raise ValueError(why)

def science():
    v1,passed=original.scientific_state(True)
    require(not passed and v1['scientific_stage_status']=='HOST_ORTHOLOGY_DUPLICATE_SIGNAL_REVIEW_REQUIRED'
            and v1['same_locus_multiple_profile_candidates']==192 and v1['scientific_blockers']==[],
            'Original executed numeric/source proof or duplicate-review outcome differs')
    v=read(GATE/'validation_summary.json');inventory=read(VIEW/'inventory_summary.json')
    require(v['status']=='PASS_MARKER_SOURCE_AND_FIXED_FILTERS'
            and v['scientific_stage_status']=='PASS_HOST_MARKER_INVENTORY'
            and v['curation_status']=='PASS_TOPOLOGY_BLIND_ORTHOLOGY_DEDUPLICATION'
            and v['approved_assemblies']==v['independently_verified_searches']==196
            and v['profiles_searched']==119 and v['primary_markers']==100 and v['accepted_marker_sequences']==19359
            and v['same_locus_multiple_profile_candidates']==0 and v['scientific_blockers']==[],
            'Independent curated scientific gates are incomplete or failed')
    binds={'inventory_summary_sha256':VIEW/'inventory_summary.json',
           'accepted_sequence_manifest_sha256':VIEW/'accepted_sequence_manifest.tsv',
           'primary_marker_order_sha256':VIEW/'primary_marker_order.txt',
           'config_sha256':R/'config/host_primary_stage03_v1.json','profile_sha256':R/'.tools/Firmicutes.hmm',
           'original_validation_summary_sha256':original.VALIDATION/'validation_summary.json',
           'orthology_curation_config_sha256':ORTHOLOGY_CONFIG,
           'orthology_curation_receipt_sha256':VIEW/'curation_receipt.json',
           'validator_source_sha256':R/'scripts/validate_stage03_orthology.py'}
    for key,path in binds.items():require(v.get(key)==w.digest(path),'Curated evidence/code changed: '+key)
    require(v['producer_identity']==v1['producer_identity']==inventory['identity'],'Original native provenance differs')
    function=v['host_function_review']
    require(function['state']=='REVIEWED_CONSERVED_HOST_PROFILE_SCOPE_WITH_DOCUMENTED_LIMITS'
            and function['unresolved_rm_candidates']==0 and function['profiles_accounted']==119
            and function['review_sha256']==w.digest(PUBLIC/'host_profile_scope_review_orthology_v2.json'),
            'Current curated source-family review differs')
    receipt=read(VIEW/'curation_receipt.json')
    require(receipt['identity']['builder_source_sha256']==w.digest(R/'scripts/stage03_curate_orthology.py')
            and receipt['identity']['config_sha256']==w.digest(ORTHOLOGY_CONFIG), 'Curator code/config differs')
    for path,h in receipt['output_sha256'].items():require(w.digest(VIEW/path)==h,'Curated payload changed: '+path)
    provenance={'scientific_stage_status':v['scientific_stage_status'],'curation_status':v['curation_status'],
                'approved_assemblies':196,'profiles_searched':119,'primary_markers':100,
                'original_scientific_provenance':original.scientific_provenance(v1),
                **{key:w.digest(path) for key,path in binds.items()},
                'host_profile_scope_review_sha256':function['review_sha256'],
                'marker_validation_summary_sha256':w.digest(GATE/'validation_summary.json'),
                'curator_source_sha256':w.digest(R/'scripts/stage03_curate_orthology.py'),
                'finalizer_source_sha256':w.digest(Path(__file__))}
    return v,provenance

def files_under(base,prefix,excluded=()):
    return [(p,prefix+'/'+p.relative_to(base).as_posix()) for p in base.rglob('*')
            if p.is_file() and p.relative_to(base).parts[0] not in excluded
            and not p.name.endswith(('.ssi','.idx','.partial'))]

def prepare(v,provenance):
    STAGING.mkdir(parents=True,exist_ok=True)
    for name in original.COMPACT:
        shutil.copyfile(RAW/name,PUBLIC/('original_'+name))
        shutil.copyfile(VIEW/name,PUBLIC/name)
    shutil.copyfile(GATE/'validation_summary.json',PUBLIC/'marker_validation_summary.json')
    shutil.copyfile(GATE/'validation_summary.json',PUBLIC/'curated_marker_validation_summary.json')
    shutil.copyfile(original.VALIDATION/'validation_summary.json',PUBLIC/'original_marker_validation_summary.json')
    shutil.copyfile(original.SOURCE_VALIDATION/'assembly_audit.json',PUBLIC/'source_locus_assembly_audit.json')
    shutil.copyfile(R/'.work/stage03_host_time.txt',PUBLIC/'host_process_time.txt')
    w.js(PUBLIC/'scientific_provenance.json',provenance)
    guide=('Stage03 standard Windows ZIPs. Biological text files open without WSL. Raw NCBI packages/metadata remain separately available in Stage02/Stage01 releases.\n'
           'source_locus_inputs/ exact assembly|replicon|locus protein and ordered detector preparations; no detector searches have run.\n'
           'search_evidence/ complete original GToTree/HMM outputs and rename crosswalks; plaintext .tmp names preserved for checkpoint joins; binary indexes omitted.\n'
           'original_marker_inventory/ retains original119-profile/101-marker outputs and their duplicate-signal scientific block.\n'
           'curated_marker_inventory/ retains the separately independently validated100-marker topology input. IPT selects192 complete MiaA proteins already included by IPPT; its exclusion prevents double weighting. No biological search reran or approved genome changed.\n'
           'independent_original_validation/ and independent_curated_validation/ preserve both outcomes. All ZIP members have SHA256 hashes; plans/status/publication receipts remain outside immutable scientific payload manifests.\n'
           'Reconstruct .work/source_locus_inputs_v1, .work/stage03_markers_v1 and .work/stage03_orthology_v2 respectively from the named namespaces to rerun checkers, or use explicit CLI paths. Absolute paths in commands describe the original WD execution.\n')
    report=('# Stage03: all196 conserved host markers\n\n'
            'Actual GToTree1.8.10/HMMER3.4 searches completed for all196 using the pinned119 Firmicutes profiles. Independent source/fixed-filter checks verified22984 qualifying hits and23628 domains. All398537 source protein loci and2120 source genomic sequence records were independently mapped. These boundary keys include chromosomes, plasmids and scaffold/contig records; they are not2120 proven complete biological replicons.\n\n'
            'The original frozen filters retained101 marker profiles and19551 source sequences, but independent orthology review blocked this inventory: IPPT/PF01715 and IPT/PF01745 select the same complete MiaA protein at192 exact source loci. Raw evidence and this blocked outcome remain preserved.\n\n'
            'Before any alignment or topology, an explicit second freeze excludes only the redundant IPT family. IPPT retains the MiaA protein once in each of196 genomes. Independent projection checks verify100 retained markers,19359 exact sequences, zero duplicated whole-protein loci and unchanged cohort membership. No search, sequence prediction or download was repeated.\n\n'
            'The original GA/multicopy/median-length/177-of196 occupancy filters remain intact. Initial recovery still requires96/119; the additional unique-locus initial gate also passes (minimum102). Post-occupancy recovery requires80/100 and the observed minimum is93. No cutoff was relaxed. The original101-profile results remain distinct from the curated100-marker topology input.\n\n'
            'Scientific status: PASS_HOST_MARKER_INVENTORY for the independently curated view. Family/source annotations support predicted host scope; unknown functions and lack of approved-strain activity evidence remain explicit. Neither RNA methylases nor general nucleases are equated with DNA R-M activity.\n\n'
            'Searches ran serially with two CPU cores/threads and2GiB address-space cap. Runtime help/package/program/profile/source hashes, commands/PIDs, elapsed/CPU/maxRSS, all HMM tables and both independent validator outputs are retained. No alignment, tree or R-M detector result is claimed here.\n\n'
            '[GToTree](https://github.com/AstrobioMike/GToTree), [pinned profile archive](https://zenodo.org/records/13858489), '
            '[Pfam IPPT](https://www.ebi.ac.uk/interpro/entry/pfam/PF01715/), [Pfam IPT](https://www.ebi.ac.uk/interpro/entry/pfam/PF01745/) and '
            '[primary MiaA structural work, PMID19158097](https://pubmed.ncbi.nlm.nih.gov/19158097/) provide method/family context. Reference experiments do not establish activity in the approved strains.\n\n'
            'Portable release payloads and sidecars are uploaded, downloaded back, CRC/member-hash checked and bound to the immutable tag commit. Publication receipts and live status are separate from payload manifests.\n')
    w.atomic(PUBLIC/'REPORT.md',report.encode());w.atomic(PUBLIC/'RELEASE_NOTES.md',(report+'\n'+guide).encode())
    assets=[];panel=(R/'config/approved_accessions.txt').read_text().split()
    for start in range(0,196,20):
        group=panel[start:start+20];members=[]
        for acc in group:
            members+=files_under(SOURCE/'assemblies'/acc,'source_locus_inputs/assemblies/'+acc)
            for space in ('evidence','searches'):
                members+=files_under(RAW/space/acc,'search_evidence/'+space+'/'+acc)
        asset=make_zip(STAGING/f'stage03-source-and-search-{start+1:03}-{start+len(group):03}.zip',members,guide)
        asset['assemblies']=group;assets.append(asset);print('ZIP_VALIDATED',asset['asset_name'],asset['bytes'],flush=True)
    members=files_under(RAW,'original_marker_inventory',('evidence','searches','shims'))
    members+=files_under(VIEW,'curated_marker_inventory')
    for directory,prefix in [(original.VALIDATION,'independent_original_validation'),(GATE,'independent_curated_validation'),
                             (original.SOURCE_VALIDATION,'independent_source_validation')]:members+=files_under(directory,prefix)
    members+=[(p,'source_locus_inputs/'+p.name) for p in SOURCE.iterdir() if p.is_file()]
    members+=[(R/'.tools/Firmicutes.hmm','profiles/Firmicutes.hmm')]
    members+=[(p,'profile_annotation_snapshots/'+p.name) for p in (R/'.work/host_profile_annotations').glob('*.json')]
    assets.append(make_zip(STAGING/'stage03-full196-original-and-curated-markers.zip',members,guide))
    script_names=['build_locus_inputs.py','validate_locus_inputs.py','stage03_source_inputs.py','stage03_validate_source.py',
       'stage03_markers.py','gtotree_evidence.py','stage03_run_markers.py','run_stage03_host.sh','validate_stage03_markers.py',
       'stage03_validate_markers.py','record_host_profile_scope_review.py','summarize_accepted_host_scope.py',
       'stage03_curate_orthology.py','validate_stage03_orthology.py','stage03_validate_orthology.py','test_stage03_orthology.py',
       'finalize_stage03.py','finalize_stage03_orthology.py','portable_release.py','test_portable_release.py',
       'test_portable_publication.py','test_stage03_finalizer_gates.py','workflow_publication.py','production_resume.py','wsl_project.sh']
    paths=['scripts/'+n for n in script_names]
    paths+=['config/'+n for n in ['approved_accessions.txt','approval.json','host_primary_stage03_v1.json','host_orthology_stage03_v2.json']]
    reports=original.COMPACT+['original_'+n for n in original.COMPACT]
    reports+=['REPORT.md','RELEASE_NOTES.md','marker_validation_summary.json','original_marker_validation_summary.json',
       'curated_marker_validation_summary.json','source_locus_assembly_audit.json','scientific_provenance.json',
       'host_process_time.txt','host_profile_scope_review.json','host_profile_scope_review_orthology_v2.json',
       'source_locus_validation_summary.json','source_construction_summary.json','marker_start_resources.json',
       'start_resources.json','source_process_resource_snapshot.json','source_locus_synthetic_tests.json',
       'source_locus_validator_synthetic_tests.json','marker_filter_synthetic_tests.json','marker_validator_synthetic_tests.json',
       'orthology_validator_synthetic_tests.json','orthology_curation_receipt.json','hmm_evidence_wrapper_synthetic_tests.txt',
       'portable_archive_synthetic_tests.json','portable_publication_independent_tests.json','PORTABLE_PUBLICATION_REVIEW.md',
       'finalizer_independent_tests.json','FINALIZER_REVIEW.md']
    paths+=['reports/stage03/'+n for n in reports]
    check(paths)
    assets.append(make_zip(STAGING/'stage03-methods-and-reports.zip',[(R/p,p) for p in paths],guide))
    w.js(PUBLIC/'asset_manifest.json',{'stage':'stage03','approved_assemblies':196,'scientific_validation':v['scientific_stage_status'],
         'scientific_provenance':provenance,'original_markers':101,'curated_markers':100,'assets':assets,
         'publication_receipts_separate':True})
    paths.append('reports/stage03/asset_manifest.json')
    w.atomic(PUBLIC/'SHA256SUMS.txt',''.join(w.digest(R/p)+'  '+p+'\n' for p in sorted(set(paths))).encode())
    paths.append('reports/stage03/SHA256SUMS.txt');w.js(STAGING/'payload_paths.json',paths)
    return paths

def main():
    w.run(['git','fetch','origin','main']);w.run(['git','pull','--ff-only','origin','main'])
    v,provenance=science();plan=R/'status/stage03_publication_plan.json'
    if plan.exists():
        require(read(PUBLIC/'asset_manifest.json')['scientific_provenance']==provenance,'Frozen science changed; preserve prior payload')
        require(read(PUBLIC/'scientific_provenance.json')==provenance,'Frozen public scientific provenance changed')
        require(w.digest(PUBLIC/'marker_validation_summary.json')==provenance['marker_validation_summary_sha256'],
                'Frozen public validator bytes differ')
        paths=read(STAGING/'payload_paths.json')
    else:paths=prepare(v,provenance)
    w.status('3_markers','VALIDATED','PASS_HOST_MARKER_INVENTORY','UPLOADING',
             'All196 original search evidence and independently curated100-marker view validated. Portable Stage03 ZIP publication/readback is running; no dependent topology starts before remote verification.')
    commit(['STATUS.md','status/stages.tsv'],'Record validated full196 conserved markers and portable publication start')
    receipt=publish_frozen('stage03','stage03-hostmarkers196-v1',STAGING,PUBLIC/'asset_manifest.json',paths,
                          'Stage03: full196 host markers and reviewed MiaA deduplication',PUBLIC/'RELEASE_NOTES.md')
    receipt.update(scientific_validation=v['scientific_stage_status'],approved_assemblies=196,primary_markers=100,
                   scientific_provenance_sha256=w.digest(PUBLIC/'scientific_provenance.json'),
                   curated_validation_summary_sha256=w.digest(GATE/'validation_summary.json'),
                   original_validation_summary_sha256=w.digest(original.VALIDATION/'validation_summary.json'),
                   orthology_curation_config_sha256=w.digest(ORTHOLOGY_CONFIG),
                   orthology_curation_receipt_sha256=w.digest(VIEW/'curation_receipt.json'))
    w.js(PUBLIC/'publication_receipt.json',receipt)
    w.status('3_markers','COMPLETED','PASS_HOST_MARKER_INVENTORY','UPLOAD_VERIFIED',
             'All196 host searches, independent source/filter/function checks and reviewed100-marker orthology view completed. Every Stage03 ZIP/sidecar downloaded and hash-verified against its immutable tag; continuing automatically to Stage04.')
    commit(['reports/stage03/publication_receipt.json','reports/stage03/publication_progress.json',
            'reports/stage03/publication_commands.jsonl','reports/stage03/commands.jsonl','STATUS.md','status/stages.tsv'],
           'Verify Stage03 Release bytes and independently curated full196 host markers')
    print('STAGE03_SCIENTIFIC_AND_PUBLICATION_GATES_COMPLETE',flush=True)

if __name__=='__main__':
    lock=(w.WORK/'workflow.lock').open('a+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    w.js(w.WORK/'workflow_owner.json',{'pid':os.getpid(),'utc':w.now(),'script':str(Path(__file__)),
                                     'scope':'Stage03 original and curated evidence publication'})
    try:main()
    except Exception as e:
        w.js(R/'status/stage03_publication_failure.json',{'utc':w.now(),'error':str(e),'outputs_preserved':True})
        w.status('3_markers','FINALIZATION_STOPPED','SEE_INDEPENDENT_VALIDATION','FAILED_OR_INCOMPLETE',
                 str(e)+'. Scientific evidence and immutable payloads preserved; dependent stage gated.')
        commit(['status/stage03_publication_failure.json','STATUS.md','status/stages.tsv'],'Record explicit Stage03 publication failure')
        raise
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()
