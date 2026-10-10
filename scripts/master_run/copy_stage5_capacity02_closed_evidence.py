"""C-only exact snapshot after actual capacity02 natural termination; no WSL launch."""
from pathlib import Path
import datetime,hashlib,json,stat
W=Path(__file__).resolve().parent
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    owner=W/'stage5_owner_GCF_000009425_1_backing_capacity_02'
    result=json.loads((owner/'result.json').read_bytes());assert result['state']=='DEFERRED_RESOURCE'
    end=result['genome_results'][0]
    assert end['actual_wsl_client_exit']['exited'] and end['actual_wsl_client_exit']['exit_code']==75
    assert (owner/'lock_released.json').is_file()
    backing=Path(r'\\wsl.localhost\Ubuntu\var\tmp\lab_rm_stage05_atomic_v1')
    root=backing/'GCF_000009425.1';out=W/'stage5_capacity02_closed_native_copy';out.mkdir()
    members=[];rows={};inventory=[]
    for p in sorted(backing.rglob('*')):
        relative=p.relative_to(backing).as_posix();info=p.lstat()
        assert not p.is_symlink() and not getattr(info,'st_file_attributes',0)&0x400
        row={'member':relative,'windows_unc_mode_projection':info.st_mode,
          'windows_unc_uid_projection':info.st_uid,'windows_unc_gid_projection':info.st_gid,
          'windows_unc_inode_projection':info.st_ino,'windows_unc_nlink_projection':info.st_nlink,
          'metadata_scope':'WINDOWS_UNC_PROJECTION_NOT_INDEPENDENT_PRIOR_LINUX_POSIX_ATTESTATION'}
        if p.is_dir():row['kind']='directory'
        else:
            assert stat.S_ISREG(info.st_mode) and info.st_size<32*1024**2
            raw=p.read_bytes();after=p.lstat();assert (info.st_ino,info.st_size,info.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns)
            row.update(kind='file',bytes=len(raw),sha256=sha(raw))
        inventory.append(row)
        if relative.startswith('GCF_000009425.1/'):members.append(relative.split('/',1)[1])
    assert {p.name for p in backing.iterdir()}=={'.native_runner.guard','GCF_000009425.1'}
    assert not any(p.endswith('.launch_intent.json') or p.endswith('.native_launch.json') for p in members)
    selected=['status.json','scientific_identity.json','execution_freeze.json',
      'transactions/attempt_0002/status.json','transactions/attempt_0002/latest_admission.json',
      'transactions/attempt_0002/initial_owner_lease.json','transactions/attempt_0002/work_storage_proof.json']
    selected += [p for p in members if p.startswith('execution/') and (root/p).is_file()]
    for relative in sorted(set(selected)):
        source=root/relative
        if relative=='execution_freeze.json' and not source.is_file():
            continue
        raw=source.read_bytes();dest=out/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as stream:stream.write(raw)
        assert dest.read_bytes()==raw
        rows[relative]={'bytes':len(raw),'sha256':sha(raw)}
    status=json.loads((out/'status.json').read_bytes())
    assert sha((out/'status.json').read_bytes())==end['status_sha256']
    assert status['state']=='DEFERRED_RESOURCE' and status['owned_closure_proven'] is True and status['no_native_launch_in_this_invocation'] is True
    assert sha((out/'scientific_identity.json').read_bytes())=='bb9b7b355a55758a9085ca014eff4fbdb14a93ff5e795773b89a0e5d9ee8ee74'
    value={'state':'PASS_EXACT_C_COPY_CLOSED_CAPACITY02_WITH_PREPARED_BACKING_HASH_INVENTORY',
      'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':sha(Path(__file__).read_bytes()),
      'source_backing':str(backing),'members':members,'backing_inventory':inventory,'files':rows,
      'owner_result_sha256':sha((owner/'result.json').read_bytes()),'native_launch_intents_observed':0,
      'prior_linux_posix_identity_source':'Exact transactions/attempt_0002/work_storage_proof.json; fresh Linux metadata must be observed after reboot.'}
    with (out/'snapshot.json').open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':value['state'],'members':len(members),'backing_objects':len(inventory),'files':len(rows)}))
if __name__=='__main__':main()
