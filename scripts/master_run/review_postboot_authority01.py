"""Read-only immutable GitHub authority and local continuation source audit."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import ast, base64, datetime, hashlib, json, subprocess

WORK=Path(__file__).resolve().parent
OUT=WORK/'postboot_authority_review01'
REPORT=WORK/'postboot_authority_review01.json'
REPO='serg-alexv/lab-rm-phylogenomics-196'
AUTHORITY=['AGENTS.md','WORK_ORDER.md','STATUS.md','status/stages.tsv','status/master_run_20261009.json','status/run_control.json']
SOURCES=['atomic_iqtree_windows.py','stage5_setup_windows.py','stage5_setup_linux.py','stage5_atomic.py',
         'stage5_atomic_process.py','stage5_build_actual_config.py','stage5_unc_bind_probe.py',
         'stage5_interop_smoke_windows.py','stage5_interop_linux_fixture.py','stage5_windows_owner.py',
         'stage5_gdrive_view.py','stage5_owner_lease.py','stage5_runtime_discovery.py','stage5_work_storage.py',
         'stage5_drivefs_filesystem_smoke.py','stage5_atomic_config.template.json','observe_iqtree_controller_exit.py']
def sha(data):return hashlib.sha256(data).hexdigest()
def api(route):
    p=subprocess.run(['gh','api','repos/'+REPO+'/'+route],capture_output=True,check=True,timeout=60)
    return json.loads(p.stdout)
def download(path,head):
    value=api('contents/'+path+'?ref='+head)
    assert value['encoding']=='base64'
    data=base64.b64decode(value['content'])
    assert len(data)==value['size'] and hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==value['sha']
    dest=OUT/path;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(data)
    return {'repository_path':path,'local_path':str(dest),'bytes':len(data),'sha256':sha(data),'git_blob':value['sha']}
def pins(path):
    if path.suffix!='.py':return {}
    for node in ast.parse(path.read_text()).body:
        if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='PINS' for x in node.targets):
            return ast.literal_eval(node.value)
    return {}
def main():
    assert not OUT.exists() and not REPORT.exists()
    OUT.mkdir()
    head=api('git/ref/heads/main')['object']['sha']
    with ThreadPoolExecutor(max_workers=4) as pool:authority=list(pool.map(lambda p:download(p,head),AUTHORITY))
    tree=api('git/trees/'+head+'?recursive=1');assert tree['truncated'] is False
    members=[x for x in tree['tree'] if x['type']=='blob']
    rows=[]
    for name in SOURCES:
        path=WORK/name;data=path.read_bytes();digest=sha(data)
        oid=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        exact=[{'repository_path':x['path'],'git_blob':x['sha']} for x in members if x['sha']==oid]
        declared=pins(path)
        checks=[{'source':n,'expected_sha256':v,'actual_sha256':sha((WORK/n).read_bytes()),'match':sha((WORK/n).read_bytes())==v} for n,v in declared.items()]
        rows.append({'name':name,'bytes':len(data),'sha256':digest,'git_blob':oid,'exact_published_locations':exact,'all_declared_pins_match':all(x['match'] for x in checks),'declared_pins':checks})
    final=api('git/ref/heads/main')['object']['sha']
    result={'schema':'MASTER_POSTBOOT_AUTHORITY_INDEPENDENT_READONLY_V1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'state':'PASS_CURRENT_AUTHORITY_AND_LOCAL_PUBLISHED_SOURCES' if final==head and all(x['exact_published_locations'] and x['all_declared_pins_match'] for x in rows) else 'RECONCILE_AUTHORITY_OR_SOURCE_DRIFT',
      'repository':REPO,'initial_remote_main':head,'final_remote_main':final,'authority':authority,'sources':rows,
      'read_only_scope':{'wsl_launched':False,'stop_changed':False,'process_or_service_mutation':False,'image_mutation':False,'git_ref_write':False,'private_boot_namespace_read':False},
      'accepted_stage4':{'must_rerun':False,'tree_sha256':'f886c0134ab662a05aae2b1c1a26ed364749af250400f769ce6e63f1f7a8ba19'},
      'gate_order':['fresh new Windows boot and independent current quiescence; reconcile exact preserved old STOP under original lock','toolchain fresh current source setup gate','runtime fresh candidate discovery, after toolchain','interop three fixtures fresh current native runtime','inspect actual G topology before restoring storage; never blind repeat existing-mount helper','storage fresh actual ext4 bind proof','drivefs fresh Linux atomic I/O and corrected retained Windows worker closure','UNC exact bidirectional sentinel with runtime/storage manifest pins','build exact actual config from six fresh gates and five finite documented resource budgets','first approved full-method genome GCF_000009425.1','independent four-cell curation and closed raw archive with fresh GitHub recovery before eviction','resumable full196 queue; accepted tree plus full784 explicit join before production figures'],
      'approvals':{'direct_user_continuation_already_authorized':True,'remote_main_is_authority':True,'automatic_resume_remains_false':True,'no_new_user_approval_needed_for_authorized_gates':True,'capacity_admission_is_runtime_condition_not_permission':True},
      'limitations':['This audit does not prove a new Windows boot, clear STOP, prove current native closure or run any gate.','Historical DriveFS02 terminal/job closure remains unrecorded; new boot can qualify current scope without rewriting the old failure.']}
    with REPORT.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'state':result['state'],'main':head,'final_main':final,'authority_files':len(authority),'source_count':len(rows),'unpublished_sources':[r['name'] for r in rows if not r['exact_published_locations']],'pin_mismatches':[r['name'] for r in rows if not r['all_declared_pins_match']],'report':str(REPORT),'report_sha256':sha(REPORT.read_bytes())},indent=2))
if __name__=='__main__':main()
