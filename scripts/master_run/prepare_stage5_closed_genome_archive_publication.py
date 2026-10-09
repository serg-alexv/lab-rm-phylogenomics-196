"""C-only metadata freeze for inactive raw archive/recovery sources."""
from pathlib import Path
import ast, hashlib, json

WORK=Path(__file__).resolve().parent
REPORT=WORK/'stage5_closed_genome_archive_preparation.json'
PREFIX='reports/master_run/20261009/stage5/closed_genome_archive/'
SOURCES=['stage5_closed_genome_archive_linux.py','stage5_closed_genome_archive_windows.py',
    'stage5_closed_genome_recovery.py','test_stage5_closed_genome_archive.py',
    'test_stage5_closed_genome_archive_owner.py','test_stage5_closed_genome_recovery.py',
    'stage5_closed_genome_archive_linux_before_closure_veto.py',
    'stage5_closed_genome_archive_windows_before_closure_veto.py',
    'stage5_closed_genome_archive_windows_before_pass_flags.py',
    'stage5_closed_genome_archive_linux_before_pidfd_compat.py',
    'stage5_closed_genome_archive_windows_before_pidfd_compat.py',
    'stage5_closed_genome_archive_linux_after_pidfd_before_runtime_sha.py',
    'stage5_closed_genome_archive_windows_after_pidfd_before_runtime_sha.py',
    'stage5_closed_genome_recovery_before_drive_path_fix.py',
    'test_stage5_closed_genome_recovery_before_drive_path_fix.py',Path(__file__).name]
CONTROLS=['STAGE5_CLOSED_GENOME_OPERATIONAL_METHODS.md',
    'stage5_closed_genome_archive_source_review_attempt01.json',
    'stage5_closed_genome_archive_corrected_independent_review.json',
    'stage5_closed_genome_recovery_independent_source_review.json']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert WORK==Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work') and not REPORT.exists()
    base=WORK/'stage5_pidfd_runtime_preparation.json'
    assert sha(base)=='cb52bf39e07d6c39e79d90ec8b19c0b4561e70553349ea448a07c7cab61a69c8'
    checked=[]
    for name in SOURCES[:2]:
        for node in ast.parse((WORK/name).read_text()).body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PINS' for t in node.targets):
                for member,expected in ast.literal_eval(node.value).items():
                    assert sha(WORK/member)==expected,(name,member)
                    checked.append({'consumer':name,'member':member,'sha256':expected})
    files=[]
    for name in SOURCES+CONTROLS:
        path=WORK/name;assert path.parent==WORK and path.is_file() and not path.is_symlink()
        files.append({'local_path':str(path),'bytes':path.stat().st_size,'sha256':sha(path),
                      'suggested_remote_path':('scripts/master_run/' if name in SOURCES else PREFIX)+name})
    value={'schema':'STAGE05_CLOSED_GENOME_RAW_ARCHIVE_SOURCE_PREPARATION_V1',
        'state':'SOURCE_PEERS_AND_PURE_TESTS_PASS_ACTUAL_ARCHIVE_NOT_RUN','files':files,
        'current_dependency_source_map':{'path':str(base),'sha256':sha(base)},'active_source_pin_checks':checked,
        'tests':{'passed':26,'scope':'11 raw archive +9 owner +6 recovery pure C synthetic contracts; also included in final combined125/2.143s exit0'},
        'independent_reviews':{name:sha(WORK/name) for name in CONTROLS[1:]},
        'producer_review_scope':'Full original functional sources1ecd/8655; later changes are exact dependency-pin substitutions byte-proved in linked combined map',
        'recovery_review_scope':'Independent full source6603 and exact colon/drive/ADS correction; original7d725 and tests retained',
        'raw_asset_limits':{'files':100000,'logical_bytes':16*1024**3,'asset_bytes':448*1024**2,'linux_seconds':1800,'client_seconds':1830},
        'actual_genome_archive':'NOT_RUN','actual_canonical_rehydration':'NOT_RUN','actual_fresh_remote_payload_readback':'NOT_RUN',
        'curation_products':'Separate qualified review/result/witness archive required; raw complete.files stays immutable',
        'eviction_authorized':False,'new_scientific_acceptance':False,
        'remaining_operational_work':'Actual first closed genome and footprint; raw archive owner execution; independent full fresh remote reader; real storage-gated canonical rehydration/adoption; separate curation witness preservation. Originals stay until all recovery proofs.',
        'report_suggested_remote_path':PREFIX+REPORT.name}
    REPORT.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'path':str(REPORT),'sha256':sha(REPORT),'bytes':REPORT.stat().st_size,'files':len(files),'pins':len(checked)}))


if __name__=='__main__':main()
