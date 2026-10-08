"""Execute independent full196 sequence validation under the production lock."""
from pathlib import Path
import os,sys,time,msvcrt
import production_resume as w
from workflow_publication import commit

R=w.R
w.LOG=R/'reports/stage02/validation_commands.jsonl'
lock=(w.WORK/'workflow.lock').open('a+b')
lock.seek(0)
for attempt in range(20):
    try:
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        break
    except OSError:
        if attempt==19:raise SystemExit('Existing workflow still active; validation not launched')
        time.sleep(1)
w.js(w.WORK/'workflow_owner.json',{'pid':os.getpid(),'utc':w.now(),'script':str(Path(__file__)),'scope':'independent full196 validation'})
try:
    w.run(['git','fetch','origin','main']);w.run(['git','pull','--ff-only','origin','main'])
    accessions=(R/'config/approved_accessions.txt').read_text().split()
    assert len(accessions)==len(set(accessions))==196
    assert all((R/'data/raw_ncbi'/a/(a+'.ncbi.zip')).is_file() for a in accessions)
    w.status('2_sequences','VALIDATING','RUNNING','PROGRESS_PUBLISHED','All196 exact raw packages retrieved and provider-MD5 audited. Independent full196 FASTA/CDS/protein/GFF/GBFF/sequence-report validation is RUNNING. No marker job has started.')
    commit(['scripts/validate_sequences.py','scripts/validate_stage02_locked.py','reports/stage02/validator_review_evidence.json','reports/stage02/VALIDATOR_REVIEW.md','STATUS.md','status/stages.tsv'],'Start independent full196 sequence and annotation validation')
    result=w.run([str(R/'.tools/validation_env/Scripts/python.exe'),'-u',str(R/'scripts/validate_sequences.py'),'--repo-root',str(R),'--output-dir',str(R/'.work/stage02_validated')],timeout=3600,check=False)
    print(result,flush=True)
finally:
    lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()
