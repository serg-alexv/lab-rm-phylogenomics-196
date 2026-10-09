"""Hash-guarded new repair revision; V9 and V6 source bytes remain unchanged."""
from pathlib import Path
import json
import stage04_controller as C
import stage04_recovery_support_v9 as OLD

def main():
    with C.WorkflowLock(OLD.LOCK):
        proposal=OLD.ROOT/'config/host_inference_stage04_recovery_v9_freeze.json'
        C.check(C.digest(proposal)=='7812e27efea0b28861115ca5ba4ad698f8331ff5d59d141b43a2583b757e856e','V9 frozen proposal changed')
        value=C.load(proposal);outputs={}
        for key,sha in value['required_review_artifacts'].items():
            if not key.startswith('data:scripts/') or '_v9.' not in key:continue
            rel=key.split(':',1)[1];source=OLD.ROOT/rel;C.check(C.digest(source)==sha,'Frozen V9 source changed')
            dest=OLD.ROOT/rel.replace('_v9.','_v10.');C.check(not dest.exists(),'V10 candidate already exists; never overwrite a new frozen revision')
            text=source.read_text(encoding='utf-8').replace('_v9','_v10').replace('V9','V10').replace('windows_v9','windows_v10').replace('recovery_v9','recovery_v10')
            dest.write_text(text,encoding='utf-8',newline='\n');outputs[dest.relative_to(OLD.ROOT).as_posix()]=C.digest(dest)
        # Negative evidence remains in its original immutable V9 report namespace.
        s=OLD.ROOT/'scripts/stage04_recovery_support_v10.py';text=s.read_text();text=text.replace("OLD=ROOT/", "NEGATIVE=ROOT/'reports/stage04/recovery_v9/failed_attempt_reconciliation_v1.json'\nOLD=ROOT/")
        s.write_text(text,encoding='utf-8',newline='\n')
        for rel in outputs:
            p=OLD.ROOT/rel;text=p.read_text(encoding='utf-8').replace("S.REPORT/'failed_attempt_reconciliation_v1.json'","S.NEGATIVE")
            p.write_text(text,encoding='utf-8',newline='\n');outputs[rel]=C.digest(p)
        C.atomic(OLD.ROOT/'reports/stage04/recovery_v10/build_origin.json',{'utc':C.now(),'status':'NEW_REPAIR_CANDIDATES_ONLY_NOT_ADOPTED',
          'immutable_v9_freeze_sha256':C.digest(proposal),'v9_required_source_hashes':{k:v for k,v in value['required_review_artifacts'].items() if k.startswith('data:scripts/')},
          'initial_v10_sources':outputs,'old_v6_negative_history':'UNCHANGED','biological_jobs':0})
        print(json.dumps({'status':'NEW_V10_CANDIDATES_CREATED_OLD_SOURCES_UNCHANGED','files':len(outputs)}))

if __name__=='__main__':main()
