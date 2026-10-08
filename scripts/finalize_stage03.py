"""Freeze and publish independently reviewed all196 conserved host markers."""
from pathlib import Path
import argparse,json,msvcrt,os,shutil
import production_resume as w
from workflow_publication import commit,check
from portable_release import make_zip,publish_frozen

R=w.R;PUBLIC=R/'reports/stage03';MARKERS=R/'.work/stage03_markers_v1'
SOURCE=R/'.work/source_locus_inputs_v1';VALIDATION=R/'.work/stage03_marker_validation'
SOURCE_VALIDATION=R/'.work/stage03_source_validation';STAGE02_VALIDATION=R/'.work/stage02_validated'
STAGING=R/'release_staging/stage03';w.LOG=PUBLIC/'publication_commands.jsonl'
COMPACT=['profiles.tsv','marker_qc.tsv','genome_recovery.tsv','copy_occupancy_matrix.tsv',
         'scientific_blockers.tsv','primary_marker_order.txt','inventory_summary.json','host_marker_annotation_review.json',
         'rm_marker_source_review_candidates.tsv','input_guard_exclusions.tsv','input_identity.json']

def require(condition,detail):
    if not condition:raise ValueError(detail)

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def provenance_paths():
    return {'panel_sha256':R/'config/approved_accessions.txt','approval_sha256':R/'config/approval.json',
            'config_sha256':R/'config/host_primary_stage03_v1.json','profile_sha256':R/'.tools/Firmicutes.hmm',
            'marker_validator_source_sha256':R/'scripts/validate_stage03_markers.py',
            'source_validator_source_sha256':R/'scripts/validate_locus_inputs.py',
            'builder_source_sha256':R/'scripts/build_locus_inputs.py',
            'runner_source_sha256':R/'scripts/stage03_markers.py','wrapper_source_sha256':R/'scripts/gtotree_evidence.py',
            'source_construction_summary_sha256':SOURCE/'construction_summary.json',
            'source_validation_summary_sha256':SOURCE_VALIDATION/'validation_summary.json',
            'source_assembly_audit_sha256':SOURCE_VALIDATION/'assembly_audit.json',
            'stage02_validation_summary_sha256':STAGE02_VALIDATION/'validation_summary.json',
            'marker_validation_summary_sha256':VALIDATION/'validation_summary.json',
            'inventory_summary_sha256':MARKERS/'inventory_summary.json',
            'marker_input_identity_sha256':MARKERS/'input_identity.json',
            'accepted_sequence_manifest_sha256':MARKERS/'accepted_sequence_manifest.tsv',
            'primary_marker_order_sha256':MARKERS/'primary_marker_order.txt',
            'host_profile_scope_review_sha256':PUBLIC/'host_profile_scope_review.json'}

def scientific_provenance(v):
    return {'scientific_stage_status':v['scientific_stage_status'],
            'approved_assemblies':196,'profiles_searched':119,
            **{key:w.digest(path) for key,path in provenance_paths().items()}}

def scientific_state(allow_blocker):
    v=read(VALIDATION/'validation_summary.json');p=scientific_provenance(v)
    require(v['status']=='PASS_MARKER_SOURCE_AND_FIXED_FILTERS'
            and v['approved_assemblies']==v['independently_verified_searches']==196
            and v['profiles_searched']==119 and v['marker_cells']==196*119,
            'Independent exact196 marker/source integrity is incomplete or failed')
    panel=(R/'config/approved_accessions.txt').read_text(encoding='ascii').split()
    approval=read(R/'config/approval.json')
    require(len(panel)==len(set(panel))==196 and approval.get('approved_assembly_count')==196
            and approval.get('pilot') is False and approval.get('human_approval')=='APPROVED_FOR_SEQUENCE_ANALYSIS'
            and approval.get('panel_accessions_sha256')==p['panel_sha256'],'Approved full196 panel/hash differs')
    inventory=read(MARKERS/'inventory_summary.json');identity=read(MARKERS/'input_identity.json')
    require(inventory.get('execution')=='COMPLETED_ALL196_SEARCHES'
            and inventory.get('approved_assemblies')==inventory.get('successful_searches')==196
            and inventory.get('profiles_searched')==119 and inventory.get('marker_cells')==196*119
            and inventory.get('identity')==identity==v['producer_identity'], 'Current complete native-search inventory/provenance differs')
    for key in ('inventory_summary_sha256','accepted_sequence_manifest_sha256','primary_marker_order_sha256','config_sha256','profile_sha256'):
        require(v.get(key)==p[key], 'Independent marker evidence changed after validation: '+key)
    require(v.get('validator_source_sha256')==p['marker_validator_source_sha256']
            and v.get('source_reader_sha256')==p['source_validator_source_sha256'], 'Current independent checker source differs from executed validation')
    bindings={'approved_accessions_sha256':'panel_sha256','config_sha256':'config_sha256','profile_sha256':'profile_sha256',
              'runner_sha256':'runner_source_sha256','wrapper_sha256':'wrapper_source_sha256',
              'source_construction_summary_sha256':'source_construction_summary_sha256',
              'stage02_validation_summary_sha256':'stage02_validation_summary_sha256',
              'independent_source_locus_validation_summary_sha256':'source_validation_summary_sha256'}
    for key,source_key in bindings.items():require(identity.get(key)==p[source_key], 'Executed producer input/code hash differs: '+key)
    source=read(SOURCE_VALIDATION/'validation_summary.json');construction=read(SOURCE/'construction_summary.json')
    require(source.get('status')=='PASS_SOURCE_LOCUS_INPUT_TRACEABILITY'
            and source.get('required_assemblies')==source.get('assemblies_audited')==source.get('assemblies_passed')==196
            and source.get('complete_exact196_accounting') is True and source.get('failed_assemblies')==[] and source.get('global_errors')==[]
            and source.get('panel_sha256')==p['panel_sha256']
            and source.get('validator_source_sha256')==p['source_validator_source_sha256'], 'Independent full196 source-locus gate differs')
    require(construction.get('status')=='SOURCE_LOCUS_INPUTS_CONSTRUCTED' and construction.get('constructed_assemblies')==196
            and construction.get('identity')==source.get('builder_identity')
            and construction['identity'].get('panel_sha256')==p['panel_sha256']
            and construction['identity'].get('builder_source_sha256')==p['builder_source_sha256']
            and construction['identity'].get('stage02_validation_summary_sha256')==p['stage02_validation_summary_sha256'],
            'Executed source builder code/inputs changed after independent validation')
    audit=read(SOURCE_VALIDATION/'assembly_audit.json')
    require([row['assembly_accession'] for row in audit]==panel
            and all(row.get('status')=='PASS_SOURCE_LOCUS_INPUT_TRACEABILITY' for row in audit),
            'Flat source assembly audit does not account for exact approved196 order/membership')
    for field in ('source_gbff_cds_loci','source_context_loci','protein_bearing_loci','gene_only_pseudogenes','gbff_replicons'):
        require(sum(row[field] for row in audit)==source[field], 'Flat source audit/summary count differs: '+field)
    function=v.get('host_function_review',{})
    require(function.get('review_sha256')==p['host_profile_scope_review_sha256']
            and function.get('profiles_accounted')==119, 'Function-scope review changed or was not bound to executed checker')
    require(v['scientific_stage_status'] in {'PASS_HOST_MARKER_INVENTORY','SCIENTIFIC_BLOCKER',
            'HOST_ORTHOLOGY_DUPLICATE_SIGNAL_REVIEW_REQUIRED','HOST_FUNCTION_SCOPE_REVIEW_REQUIRED'}, 'Unknown scientific stage status')
    passed=v['scientific_stage_status']=='PASS_HOST_MARKER_INVENTORY'
    if passed:
        require(v.get('scientific_blockers')==[] and v.get('same_locus_multiple_profile_candidates')==0
                and function.get('state')=='REVIEWED_CONSERVED_HOST_PROFILE_SCOPE_WITH_DOCUMENTED_LIMITS'
                and function.get('unresolved_rm_candidates')==0 and inventory.get('inventory')=='MARKER_INVENTORY_CONSTRUCTED'
                and inventory.get('blocker_count')==0, 'PASS label conflicts with unresolved scientific gates')
    if not passed and not allow_blocker:raise RuntimeError('Independent scientific gates unresolved: '+v['scientific_stage_status'])
    return v,passed

def require_frozen_scientific_provenance(v):
    """A blocked frozen release cannot later be relabeled as new scientific PASS."""
    manifest=read(PUBLIC/'asset_manifest.json')
    current=scientific_provenance(v)
    require(manifest.get('scientific_validation')==v['scientific_stage_status']
            and manifest.get('scientific_provenance')==current,
            'Frozen Stage03 scientific outcome/bytes changed. Preserve the prior release and use a distinct reviewed publication namespace/tag for new evidence.')
    require(w.digest(PUBLIC/'marker_validation_summary.json')==current['marker_validation_summary_sha256']
            and read(PUBLIC/'scientific_provenance.json')==current,
            'Frozen public scientific evidence differs from the current executed validation')

def prepare(v,passed):
    STAGING.mkdir(parents=True,exist_ok=True)
    for name in COMPACT:shutil.copyfile(MARKERS/name,PUBLIC/name)
    shutil.copyfile(VALIDATION/'validation_summary.json',PUBLIC/'marker_validation_summary.json')
    shutil.copyfile(SOURCE_VALIDATION/'assembly_audit.json',PUBLIC/'source_locus_assembly_audit.json')
    shutil.copyfile(SOURCE_VALIDATION/'validation_summary.json',PUBLIC/'source_locus_validation_summary.json')
    provenance=scientific_provenance(v);w.js(PUBLIC/'scientific_provenance.json',provenance)
    time_path=R/'.work/stage03_host_time.txt'
    if time_path.exists():shutil.copyfile(time_path,PUBLIC/'host_process_time.txt')
    guide=('Stage03 all196 host-marker evidence. Standard ZIP and UTF-8 files; opening biological files requires no WSL.\n'
           'source_locus_inputs/ retains primary NCBI proteins, one exact assembly|replicon|locus target per protein-bearing CDS, '
           'source context and per-replicon ordered PADLOC/DefenseFinder inputs. These detector inputs are preparation; detector searches have not run.\n'
           'marker_inventory/ contains full qualifying hits/domains, copy/occupancy/recovery/exclusion tables, exact original sequence hashes and marker FASTAs.\n'
           'search_evidence/ retains unaltered source inputs, native GToTree rename crosswalks, complete HMM tables/stdout, commands and success/failure evidence. '
           'Binary search indexes are cache-only. Plaintext .tmp evidence keeps its original filename so checkpoint paths remain valid; open it in a text editor.\n'
           'The inventory ZIP retains the complete flat independent source-validation reports and independent marker-validation reports. '
           'Methods include the exact panel and approval. Raw NCBI ZIPs and frozen taxonomy/metadata are the separately published Stage02 and Stage01 prerequisites. '
           'To run the Python checkers, reconstruct the source_locus_inputs/, marker_inventory/, search_evidence/ and independent-validation namespaces '
           'at their documented project paths or pass explicit CLI input directories; absolute command paths are original WD execution provenance.\n'
           'All payload files are covered by SHA256SUMS.txt. Predictions are separate from proven biological function. '
           'No alignment, ML tree or R-M detector result is supplied by Stage03.\n')
    report=('# Stage03: executed conserved host markers for approved196\n\n'
            f'Actual GToTree1.8.10 serial extraction and HMMER3.4 searches completed for all196 with the pinned119-profile Firmicutes set. '
            f'Independent source/fixed-filter integrity status: {v["status"]}. Scientific stage status: {v["scientific_stage_status"]}. '
            f'The inventory retains {v["primary_markers"]} primary markers and {v["accepted_marker_sequences"]} exact original protein sequences. No genome was omitted or replaced.\n\n'
            'Source-locus construction and an independent raw ZIP/GBFF/FAA/GFF reader accounted for398537 protein-bearing loci on2120 replicons. '
            'WP accessions remain source annotations; exact assembly+replicon+locus keys identify genes. Raw NCBI evidence remains separately published in Stage02.\n\n'
            'Before searches, primary filters were frozen: stored HMM GA cutoffs, initial genome recovery>=96/119, '
            'distinct-locus multicopy ambiguity missing, native GToTree median protein length +/-20%, marker occupancy>=177/196. '
            'The additional post-occupancy genome gate uses80% of the retained primary marker count and never replaces96/119. '
            'Actual native median/bc/printf inputs, outputs and program hashes are preserved.\n\n'
            'The actual GToTree extraction helper was used separately from alignment to preserve all renamed inputs and native full HMM/domain tables, '
            'verify copy counts independently and resolve quality gates before topology. Stage04 uses the predeclared MAFFT/trimAl method; '
            'no tree topology or synthetic spacer residues influenced Stage03 filtering.\n\n'
            'Independent validation rereads provider proteins/GBFF translations, preserved search targets, tblout/domtblout coordinates, '
            'native extracted sequences, copy counts, fixed filters, accepted manifests and marker FASTAs. '
            'Function-scope review is separate from integrity. Generic and functionally uncharacterized profiles remain explicit; '
            'family annotations do not demonstrate activity in the approved strains. Potential R-M source annotations or duplicate full-protein marker signals require resolution before topology.\n\n'
            'One serial full196 production search used two CPU cores/threads and a2GiB per-process address-space limit. '
            'Actual tool help, package versions, executable/source/profile hashes, Linux/Windows PIDs, elapsed/CPU/maxRSS where measured are preserved. '
            'The WSL mount wrapper was repaired to serialize project-local mount checks and accept existing stacked ext4 entries; no active mounts or unrelated processes were removed.\n\n'
            'Publication and scientific status are separate. Every standalone ZIP and checksum sidecar is verified against the frozen payload commit, '
            'downloaded back and checked. Mutable publication plans/progress/receipts are outside immutable payload hash manifests.\n\n'
            '[GToTree source](https://github.com/AstrobioMike/GToTree) and [pinned Firmicutes profile source](https://zenodo.org/records/13858489) document the method. '
            'The current Pfam annotation snapshots and primary RNA-family references used during scope review are retained separately from the pinned model.\n')
    w.atomic(PUBLIC/'REPORT.md',report.encode());w.atomic(PUBLIC/'RELEASE_NOTES.md',(report+'\n'+guide).encode())
    assets=[];accessions=(R/'config/approved_accessions.txt').read_text().split()
    assert len(accessions)==len(set(accessions))==196
    for start in range(0,196,20):
        group=accessions[start:start+20];files=[]
        for acc in group:
            base=SOURCE/'assemblies'/acc
            files.extend((p,'source_locus_inputs/assemblies/'+acc+'/'+p.relative_to(base).as_posix()) for p in base.rglob('*') if p.is_file())
            for namespace in ('evidence','searches'):
                base=MARKERS/namespace/acc
                for p in base.rglob('*'):
                    if not p.is_file() or p.name.endswith(('.ssi','.idx','.partial')):continue
                    rel=p.relative_to(base).as_posix()
                    files.append((p,'search_evidence/'+namespace+'/'+acc+'/'+rel))
        a=make_zip(STAGING/f'stage03-source-and-search-{start+1:03}-{start+len(group):03}.zip',files,guide)
        a['assemblies']=group;assets.append(a);print('ZIP_VALIDATED',a['asset_name'],a['bytes'],flush=True)
    files=[]
    for p in MARKERS.rglob('*'):
        if p.is_file() and p.relative_to(MARKERS).parts[0] not in ('searches','evidence','shims') and not p.name.endswith('.partial'):
            files.append((p,'marker_inventory/'+p.relative_to(MARKERS).as_posix()))
    for p in SOURCE.iterdir():
        if p.is_file():files.append((p,'source_locus_inputs/'+p.name))
    for p in VALIDATION.rglob('*'):
        if p.is_file():files.append((p,'independent_marker_validation/'+p.relative_to(VALIDATION).as_posix()))
    for p in SOURCE_VALIDATION.rglob('*'):
        if p.is_file():files.append((p,'independent_source_validation/'+p.relative_to(SOURCE_VALIDATION).as_posix()))
    files.append((R/'.tools/Firmicutes.hmm','profiles/Firmicutes.hmm'))
    files.extend((p,'profile_annotation_snapshots/'+p.name) for p in (R/'.work/host_profile_annotations').glob('*.json'))
    assets.append(make_zip(STAGING/'stage03-full196-marker-inventory.zip',files,guide))
    scripts=['build_locus_inputs.py','validate_locus_inputs.py','stage03_source_inputs.py','stage03_validate_source.py',
             'stage03_markers.py','gtotree_evidence.py','stage03_run_markers.py','run_stage03_host.sh',
             'validate_stage03_markers.py','record_host_profile_scope_review.py','finalize_stage03.py',
             'portable_release.py','test_portable_release.py','test_portable_publication.py','stage03_validate_markers.py',
             'workflow_publication.py','production_resume.py','wsl_project.sh']
    paths=['scripts/'+n for n in scripts]+['config/host_primary_stage03_v1.json','config/approved_accessions.txt','config/approval.json']
    paths+=['reports/stage03/'+n for n in COMPACT+['REPORT.md','RELEASE_NOTES.md','marker_validation_summary.json','host_profile_scope_review.json',
          'source_locus_validation_summary.json','source_construction_summary.json','marker_start_resources.json','start_resources.json',
          'source_process_resource_snapshot.json','source_locus_synthetic_tests.json','source_locus_validator_synthetic_tests.json',
          'marker_filter_synthetic_tests.json','marker_validator_synthetic_tests.json','hmm_evidence_wrapper_synthetic_tests.txt',
          'portable_archive_synthetic_tests.json','portable_publication_independent_tests.json','PORTABLE_PUBLICATION_REVIEW.md',
          'source_locus_assembly_audit.json','scientific_provenance.json']]
    if (PUBLIC/'host_process_time.txt').exists():paths.append('reports/stage03/host_process_time.txt')
    check(paths)
    assets.append(make_zip(STAGING/'stage03-methods-and-reports.zip',[(R/p,p) for p in paths],guide))
    w.js(PUBLIC/'asset_manifest.json',{'stage':'stage03','approved_assemblies':196,'scientific_validation':v['scientific_stage_status'],
                                    'scientific_provenance':provenance,'assets':assets,'publication_receipts_separate':True})
    paths.append('reports/stage03/asset_manifest.json')
    w.atomic(PUBLIC/'SHA256SUMS.txt',''.join(w.digest(R/p)+'  '+p+'\n' for p in sorted(set(paths))).encode())
    paths.append('reports/stage03/SHA256SUMS.txt')
    w.js(STAGING/'payload_paths.json',paths)
    return paths

def main(allow_blocker):
    w.run(['git','fetch','origin','main']);w.run(['git','pull','--ff-only','origin','main'])
    v,passed=scientific_state(allow_blocker)
    plan=R/'status/stage03_publication_plan.json'
    if plan.exists():
        require_frozen_scientific_provenance(v)
        paths=read(STAGING/'payload_paths.json')
    else:paths=prepare(v,passed)
    w.status('3_markers','VALIDATED' if passed else 'BLOCKED_SCIENTIFIC_VALIDATION',v['scientific_stage_status'],'UPLOADING',
             'All196 host marker searches and independent integrity review completed. Portable Stage03 evidence is being uploaded and read back; no dependent topology starts before scientific PASS and verified publication.')
    commit(['STATUS.md','status/stages.tsv'],'Record Stage03 scientific outcome and portable publication start')
    receipt=publish_frozen('stage03','stage03-hostmarkers196-v1',STAGING,PUBLIC/'asset_manifest.json',paths,
                          'Stage03: full196 conserved host marker evidence',PUBLIC/'RELEASE_NOTES.md')
    receipt.update(scientific_validation=v['scientific_stage_status'],approved_assemblies=196)
    w.js(PUBLIC/'publication_receipt.json',receipt)
    w.status('3_markers','COMPLETED' if passed else 'BLOCKED_SCIENTIFIC_VALIDATION',v['scientific_stage_status'],'UPLOAD_VERIFIED',
             'All196 Stage03 marker evidence ZIPs and sidecars verified against the frozen commit and remote bytes. '+
             ('Conserved host markers passed independent scientific checks; continuing automatically to Stage04 alignment and supported ML phylogeny.' if passed else
              'Scientific gates remain blocked as documented; no dependent alignment/tree is permitted.'))
    commit(['reports/stage03/publication_receipt.json','reports/stage03/publication_progress.json','reports/stage03/publication_commands.jsonl',
            'reports/stage03/commands.jsonl','STATUS.md','status/stages.tsv'],'Verify Stage03 portable Release bytes and record independent scientific outcome')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--blocker-evidence',action='store_true');args=parser.parse_args()
    lock=(w.WORK/'workflow.lock').open('a+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    w.js(w.WORK/'workflow_owner.json',{'pid':os.getpid(),'utc':w.now(),'script':str(Path(__file__)),'scope':'Stage03 verified portable publication'})
    try:main(args.blocker_evidence)
    except Exception as e:
        w.js(R/'status/stage03_publication_failure.json',{'utc':w.now(),'error':str(e),'outputs_preserved':True})
        w.status('3_markers','FINALIZATION_STOPPED','SEE_INDEPENDENT_VALIDATION','FAILED_OR_INCOMPLETE',str(e)+'. Immutable payloads and scientific evidence preserved; no dependent stage permitted.')
        commit(['status/stage03_publication_failure.json','STATUS.md','status/stages.tsv'],'Record explicit Stage03 finalization/publication failure')
        raise
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()
