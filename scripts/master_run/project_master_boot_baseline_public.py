"""Project exactly four safe baseline fields; never outputs the session control.

Authorized one-time C metadata projection only. No reboot, resume, network,
startup registration, private manifest hashing, STOP or project mutation.
"""
from pathlib import Path
import datetime, hashlib, json, os

WORK=Path(__file__).resolve().parent
PRIVATE=WORK/'private_master_boot_resume01/PRIVATE_HANDOFF_DO_NOT_PUBLISH.json'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write_new(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())

def main():
    data=json.loads(PRIVATE.read_bytes())
    raw=data['baseline']
    baseline={name:raw[name] for name in ('last_boot_utc','tick_before_ms','tick_after_ms','observed_utc')}
    for key in ('last_boot_utc','observed_utc'):
        assert isinstance(baseline[key],str) and datetime.datetime.fromisoformat(baseline[key]).tzinfo is not None
    assert all(type(baseline[k]) is int and baseline[k]>=0 for k in ('tick_before_ms','tick_after_ms'))
    assert baseline['tick_before_ms']<=baseline['tick_after_ms']
    # No session ID, private manifest path/content/hash or other private fields.
    path=WORK/'master_boot_resume_preboot_baseline.json';write_new(path,baseline)
    original=WORK/'master_one_shot_boot_resume_preparation.json'
    old=json.loads(original.read_bytes())
    rows=old['files']
    for row in rows:
        source=Path(row['local']);row.update(bytes=source.stat().st_size,sha256=sha(source))
    for name,remote in (
        ('master_boot_resume_preboot_baseline.json','reports/master_run/20261009/stage05_boot_resume01/PREBOOT_BASELINE.json'),
        ('project_master_boot_baseline_public.py','scripts/master_run/project_master_boot_baseline_public.py'),
        ('MASTER_ONE_SHOT_BOOT_RESUME_METHODS_before_prepared_instruction_fix.md','docs/master_run/history/MASTER_ONE_SHOT_BOOT_RESUME_METHODS_before_prepared_instruction_fix.md'),
        ('master_one_shot_boot_resume_preparation.json','reports/master_run/20261009/stage05_boot_resume01/history/PREPARATION_BEFORE_PUBLIC_BASELINE.json'),
    ):
        source=WORK/name;rows.append({'local':str(source),'path':remote,'bytes':source.stat().st_size,'sha256':sha(source)})
    old.update(state='PREPARED_PRIVATE_HANDOFF_COMPLETE_NOT_REGISTERED_OR_REBOOTED',files=rows,
        safe_public_boot_baseline=baseline, public_boot_baseline_sha256=sha(path),
        previous_preparation_sha256=sha(original),private_preparation_do_not_repeat=True,
        actual_runonce_registration=False,actual_restart=False)
    final=WORK/'master_one_shot_boot_resume_final_preparation.json';write_new(final,old)
    rows=[*rows,{'local':str(final),'path':'reports/master_run/20261009/stage05_boot_resume01/PREPARATION.json',
        'bytes':final.stat().st_size,'sha256':sha(final)}]
    mapping={'schema':'MASTER_ONE_SHOT_BOOT_RESUME_PUBLIC_MAPPING_V1','state':'PUBLIC_ALLOWLIST_ONLY_EXCLUDES_ALL_PRIVATE_HANDOFF',
        'files':[{'local_path':row['local'],'suggested_repository_path':row['path'],
            'bytes':row['bytes'],'sha256':row['sha256']} for row in rows],
        'private_directory_EXCLUDE_ALL_CONTENTS':'work/private_master_boot_resume01/',
        'actual_registration_or_restart_or_resume':False}
    target=WORK/'master_one_shot_boot_resume_PUBLIC_MAPPING.json';write_new(target,mapping)
    print(json.dumps({'public_baseline':str(path),'baseline_sha256':sha(path),
        'final_preparation_sha256':sha(final),'mapping_path':str(target),'mapping_sha256':sha(target),
        'public_files':len(rows),'session_ID_or_private_manifest_hash_exposed':False}))

if __name__=='__main__':main()
