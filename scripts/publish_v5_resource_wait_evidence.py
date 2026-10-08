"""Snapshot actual V5 admission measurements independently of mutable status."""
from pathlib import Path
import csv, hashlib, io, subprocess
import stage04_controller as C
import production_resume as w
from workflow_publication import commit
from wait_migration_v5_headroom_v2 import serialized_writer
ROOT=Path(__file__).resolve().parents[1]
HISTORY=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
OUT=ROOT/'reports/stage04/resource_wait_evidence_v5'
CONTROL=ROOT/'.work/stage04_inference_controller_v5'

def main():
    w.LOG=OUT/'publication_commands.jsonl'
    with serialized_writer():
        C.reconcile(ROOT)
        C.check(not (ROOT/'reports/stage04/inference_v5_adoption.json').exists(),'Adoption has advanced; preserve prior wait evidence and report a new observation')
        observations=sorted((CONTROL/'resource_preflight_measurements').glob('measurement_*.json'))
        C.check(observations,'Actual measurement files required')
        rows=[];OUT.mkdir(parents=True,exist_ok=True)
        for path in observations:
            value=C.load(path)
            C.check(value['required_windows_available_bytes']==4831838208 and value['required_linux_available_bytes']==4294967296
                    and value['outer_address_space_limit_bytes']==3758096384 and value['native_address_space_limit_bytes']==3221225472
                    and value['scientific_validation']=='NOT_RUN_RESOURCE_MEASUREMENT_ONLY','Admission policy/scope changed')
            before=value['windows_before_wsl']['available_bytes'];after=value['windows_after_wsl']['available_bytes'];linux=value['linux']['linux_available_bytes']
            passed=before>=4831838208 and after>=4831838208 and linux>=4294967296
            destination=OUT/'measurements'/path.name;destination.parent.mkdir(parents=True,exist_ok=True)
            if destination.exists():C.check(C.digest(destination)==C.digest(path),'Immutable previous measurement snapshot changed')
            else:destination.write_bytes(path.read_bytes())
            rows.append({'utc':value['utc'],'windows_before_bytes':before,'windows_after_bytes':after,'linux_available_bytes':linux,
                         'windows_required_bytes':4831838208,'linux_required_bytes':4294967296,'memory_admission_passed':passed,
                         'linux_boot_id':value['linux']['boot_id'],'original_data_relative_path':path.relative_to(ROOT).as_posix(),
                         'measurement_sha256':C.digest(path)})
        buffer=io.StringIO();writer=csv.DictWriter(buffer,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(rows)
        C.atomic(OUT/'admission_measurements.tsv',buffer.getvalue())
        current=C.windows_snapshot(ROOT,pid=8200)
        C.atomic(OUT/'summary.json',{'status':'ACTUAL_MEASURED_RESOURCE_WAIT_EVIDENCE_SNAPSHOT_ONLY','utc':C.now(),
            'actual_measurements':len(rows),'memory_admissions_passed':sum(r['memory_admission_passed'] for r in rows),
            'last_actual_admission_measurement':rows[-1],'followup_windows_snapshot':current,
            'producer_resource_ready_report_exists':(ROOT/'reports/stage04/migration_v5_ready_for_adoption.json').exists(),
            'adopted_inference_receipt_exists':False,'v5_inference_freeze_exists':(ROOT/'.work/stage04_inference_v5/inference_freeze.json').exists(),
            'full_stage04':'INCOMPLETE','stage05_stage06_stage07':'NOT_RUN',
            'watcher_resource_metrics_scope':'Measured observer only; not IQ-TREE or biological search CPU/RAM',
            'source_report_sha256':C.digest(ROOT/'reports/stage04/migration_v5_native_source_check.json'),
            'postboot_release_receipt_sha256':C.digest(ROOT/'reports/stage00r/publication_receipt.json'),
            'preparation_release_url':C.load(ROOT/'reports/stage00r/publication_receipt.json')['url']})
        last=rows[-1]
        (OUT/'REPORT.md').write_text('# Actual V5 admission measurements\n\n'
            f"Snapshot of {len(rows)} actual preflight measurements; {sum(r['memory_admission_passed'] for r in rows)} passed the full numeric memory admission. Last check at {last['utc']}: Windows {last['windows_before_bytes']} bytes before WSL and {last['windows_after_bytes']} afterward; required4831838208bytes at both observations. Linux {last['linux_available_bytes']} bytes; required4294967296. All original JSON bytes and SHA256 are preserved.\n\n"
            'Brief Windows-only availability above the threshold does not establish admission. The production gate includes both Windows readings and Linux; no gate was relaxed. The observer waits under its separate stable C guard and serializes with the shared writer byte lock. No unrelated process, preference/auth setting, reboot or automatic usage reset was performed by this task.\n\n'
            'All196 raw/QC/protein evidence, all196/100 host markers and100 alignments/four concatenations remain independently validated and published. Actual G source/CLI/bootstrap checks and synthetic installed-native selection review are in Stage00r portable ZIP. That ZIP was extracted by native Windows and downloaded from GitHub with every member/sidecar hash checked. It is not a completed phylogeny or R-M inventory.\n\n'
            'Required next steps remain: actual measured producer resource binding; exact reviewed V5 adoption/publication; four native IQ-TREE inferences and a distinct output checker; migration-aware full Stage04 portable Release/readback; both full196 PADLOC and DefenseFinder searches with source/architecture/partial review;196-tip/784-cell figure; independent final handoff. Finalizer and Stage05-07 migration integration remain separate required preparation and actual evidence gates. No future computation is claimed complete.\n',encoding='utf-8')
        detail=f"Full196 source/bootstrap/argv checks and postboot portable ZIP are verified. Latest actual admission: Windows{last['windows_before_bytes']}/{last['windows_after_bytes']}bytes before/after WSL against4831838208; Linux{last['linux_available_bytes']}against4294967296. Measured waiter8200 continues under stable C guards; V5 adoption/inference and both full196 detectors/curation/figure/final validation remain pending."
        w.status('4_phylogeny','WAITING_MEASURED_WINDOWS_HEADROOM_V5','PASS_ALIGNMENTS_PHYLOGENY_INCOMPLETE',
                 'STAGE04A_STAGE04B_AND_POSTBOOT_PRECONDITIONS_UPLOAD_VERIFIED_FULL_STAGE04_PENDING',detail)
        paths=['scripts/publish_v5_resource_wait_evidence.py','reports/stage04/resource_wait_evidence_v5/measurements',
               'reports/stage04/resource_wait_evidence_v5/admission_measurements.tsv','reports/stage04/resource_wait_evidence_v5/summary.json',
               'reports/stage04/resource_wait_evidence_v5/REPORT.md','status/postboot_review_publication_receipt.json','STATUS.md','status/stages.tsv']
        head=commit(paths,'Publish exact V5 admission evidence and verified preparation without biological completion claims')
        C.command(ROOT,['git','fetch','origin','main'])
        for item in paths:
            path=ROOT/item
            for file in ([path] if path.is_file() else [p for p in path.rglob('*') if p.is_file()]):
                name=file.relative_to(ROOT).as_posix();remote=subprocess.run(['git','show','origin/main:'+name],cwd=ROOT,capture_output=True,check=True).stdout
                C.check(hashlib.sha256(remote).hexdigest()==C.digest(file),'Remote measured evidence differs: '+name)
        print('REMOTE_ACTUAL_RESOURCE_MEASUREMENTS_ALL_BYTES_VERIFIED '+head,flush=True)

if __name__=='__main__':main()
