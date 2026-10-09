"""Production-only policy delta; tested V10 lifetime/source bytes stay unchanged.

The WSL platform service is classified by fresh bracketed SCM/CIM evidence,
never by basename or PID alone. Native access denial remains UNKNOWN. Static
anonymous outer controls are compared without assuming job ownership.
"""
import ctypes as c,json,os
from ctypes import wintypes as t
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S

FIELDS=('limit_flags','process_committed_cap_bytes','aggregate_job_committed_cap_bytes','affinity_mask')
CANONICAL=r'C:\Program Files\WSL\wslservice.exe'
FIXTURE_SHA='ce77c4ce4882aa5c1d16bb69967d891c20b9625ba80c97924a7ecf14d1d55470'
POLICY_PATH=S.ROOT/'config/host_inference_stage04_production_admission_policy_v1.json'

def static_controls(observation):
    flag=observation.get('is_process_in_job_null');C.check(type(flag) is bool,'Actual outer-job membership flag missing')
    if not flag:
        C.check(observation.get('actual_outer_job') is None,'False outer membership must not fabricate zero-valued controls')
        return None
    value=observation.get('actual_outer_job');C.check(isinstance(value,dict),'Missing actual anonymous outer controls')
    controls={key:value.get(key) for key in FIELDS}
    C.check(all(type(v) is int and v>=0 for v in controls.values()),'Static controls must be actual non-boolean integers')
    return controls

def outer_decision(observation,baseline):
    C.check(set(baseline)==set(FIELDS) and all(type(v) is int and v==0 for v in baseline.values()),'Reviewed fixture baseline must be exact four integer zeros')
    actual=static_controls(observation)
    if actual is None:return {'status':'PASS_ACTUALLY_OBSERVED_NO_OUTER_JOB','actual_static_controls':None,'anonymous_outer_owner':'NOT_IDENTIFIED'}
    C.check(actual==baseline,'Actual anonymous outer static controls differ from reviewed fixture baseline')
    return {'status':'PASS_EXACT_REVIEWED_STATIC_ANONYMOUS_OUTER_CONTROLS','actual_static_controls':actual,'anonymous_outer_owner':'NOT_IDENTIFIED'}

def positively_identified_service(before,services,after):
    """Pure role predicate; failed association leaves the null-cmdline gate closed."""
    C.check(before.get('Name')=='wslservice.exe','Only exact platform service basename may be classified')
    pid=before.get('ProcessId');creation=before.get('creation_filetime_microsecond_precision')
    C.check(type(pid) is int and pid>0 and type(creation) is int and creation>0,'Missing actual CIM service identity')
    C.check(len(services)==1 and len(after)==1,'Absent/ambiguous service association')
    service=services[0];later=after[0]
    C.check(service.get('Name')=='WSLService' and service.get('StartName')=='LocalSystem' and service.get('State')=='Running' and
      service.get('ProcessId')==pid and service.get('PathName') in (CANONICAL,'"'+CANONICAL+'"'), 'Wrong SCM name/account/state/PID/configured binary')
    C.check(later.get('Name')=='wslservice.exe' and later.get('ProcessId')==pid and
      later.get('creation_filetime_microsecond_precision')==creation,'Service PID/CIM creation changed across association query')
    return {'role':'POSITIVELY_IDENTIFIED_WSL_PLATFORM_SERVICE_NOT_USER_SCIENTIFIC_RUNNER',
      'before_cim_process':before,'scm_association':service,'after_cim_process':later,
      'identity_precision':'CIM_MICROSECONDS_NOT_NATIVE_100NS','configured_binary_is_observed_image':False}

def classify_inventory(snapshot):
    rows=snapshot['before'];services=snapshot['services'];after=snapshot['after'];included=[];roles=[]
    for row in rows:
        if row.get('Name')=='wslservice.exe':
            proof=positively_identified_service(row,services,[r for r in after if r.get('ProcessId')==row['ProcessId']])
            roles.append(proof)
        else:
            C.check(row.get('CommandLine') is not None,'Unresolved user-scientific runner command line; role exception not applicable')
            included.append(row)
    return included,roles

def fresh_runner_inventory():
    # This ordinary provider query inherits the existing bounded source-checker
    # job. No elevation, guest boot, service stop, security change or fixed PID.
    ps="$ErrorActionPreference='Stop'; $select=@('ProcessId','Name','CommandLine','ExecutablePath',@{n='creation_filetime_microsecond_precision';e={if($_.CreationDate){$_.CreationDate.ToUniversalTime().ToFileTimeUtc()}else{$null}}}); $before=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -match 'iqtree|python|wsl|bash|Rscript|hmmscan|hmmsearch'} | Select-Object $select); $services=@(Get-CimInstance Win32_Service | Where-Object {$_.Name -eq 'WSLService'} | Select-Object Name,State,StartName,PathName,ProcessId); $after=@(Get-CimInstance Win32_Process -Filter \"Name='wslservice.exe'\" | Select-Object $select); [pscustomobject]@{before=$before;services=$services;after=$after} | ConvertTo-Json -Depth 6 -Compress"
    snapshot=json.loads(S.command(['powershell.exe','-NoProfile','-NonInteractive','-Command',ps],timeout=30).decode('utf-8-sig'))
    candidates,roles=classify_inventory(snapshot)
    for proof in roles:
        pid=proof['before_cim_process']['ProcessId']
        try:
            actual=S.process_identity(pid)
            C.check(actual['state']=='RUNNING','Platform service exited/reused during gate')
            proof['native_query']={'status':'ACTUAL_NATIVE_QUERY_AVAILABLE','identity':actual}
        except OSError as error:
            C.check(error.winerror==5,'Unexpected native platform-service query error; classification blocked')
            proof['native_query']={'status':'ACCESS_ERROR_NOT_ABSENCE','winerror':5,
              'observed_native_image':'UNKNOWN','actual_100ns_creation_filetime':'UNKNOWN'}
    matching=[r for r in candidates if 'iqtree' in r['Name'].lower() or
      ('lab-rm-phylogenomics-196' in r['CommandLine'].lower() and any(n in r['CommandLine'].lower()
        for n in ['stage04_native','recovery_controller','stage05_detectors','continue_stage04','hmmscan','hmmsearch']))]
    return {'utc':C.now(),'matching_scientific_candidates':matching,'positive_platform_service_roles':roles,
      'other_null_commandlines':'FAIL_CLOSED','queries':'FRESH_CIM_BEFORE_SCM_ASSOCIATION_CIM_AFTER','scientific_jobs_started':0}

def validate_policy(proposal):
    C.check(C.digest(POLICY_PATH)==proposal['production_admission_policy_sha256'],'Accepted admission policy bytes changed')
    policy=C.load(POLICY_PATH);fixture=S.REPORT/'scheduler_fixture.json'
    C.check(policy['schema']=='V10_PRODUCTION_ONLY_ADMISSION_POLICY_V1' and policy['completed_lifetime_fixture_sha256']==FIXTURE_SHA==
      proposal['scheduler_fixture_sha256']==C.digest(fixture),'Admission baseline is not the completed preserved lifetime fixture')
    C.check(policy['false_outer_job']=='HONEST_NO_OUTER_OBSERVATION_INNER_CONTROLS_STILL_REQUIRED' and
      policy['anonymous_outer_owner']=='NOT_IDENTIFIED','No-outer/anonymous policy changed')
    baseline=static_controls(C.load(fixture)['scheduler_isolation'])
    C.check(policy['reviewed_static_outer_controls']==baseline,'Policy differs from actual completed fixture static baseline')
    return policy

def actual_outer_observation():
    flag=t.BOOL();S.J.ok(S.in_job(S.J.current(),None,c.byref(flag)),'Fresh actual outer-job membership')
    controls=None
    if flag.value:
        value=S.J.EXTENDED();S.J.ok(S.J.query_job(None,9,c.byref(value),c.sizeof(value),None),'Fresh actual static outer controls')
        controls={'limit_flags':int(value.BasicLimitInformation.LimitFlags),'process_committed_cap_bytes':int(value.ProcessMemoryLimit),
          'aggregate_job_committed_cap_bytes':int(value.JobMemoryLimit),'affinity_mask':int(value.BasicLimitInformation.Affinity)}
    return {'utc':C.now(),'controller':S.process_identity(os.getpid()),'is_process_in_job_null':bool(flag.value),
      'actual_outer_job':controls,'anonymous_outer_owner':'NOT_IDENTIFIED'}

def record_compatibility(observation,proposal,path,evidence_path=None):
    policy=validate_policy(proposal);decision=outer_decision(observation,policy['reviewed_static_outer_controls'])
    path=Path(path)
    if evidence_path is None:
        evidence_path=path.with_name('actual_outer_static_observation.json');C.atomic(evidence_path,observation)
    else:C.check(C.load(evidence_path)==observation,'Actual isolation evidence differs')
    actor=observation['controller'];receipt={**decision,'utc':C.now(),'actor':{'pid':actor['pid'],'creation_filetime':actor['creation_filetime']},
      'actual_isolation_path':str(evidence_path),'actual_isolation_sha256':C.digest(evidence_path),'fixture_baseline_sha256':FIXTURE_SHA,
      'policy_source_sha256':C.digest(__file__),'policy_config_sha256':C.digest(POLICY_PATH),
      'native_controls':'UNCHANGED_NESTED_OWNED_JOB_3GIB_MASK5_NO_BREAKAWAY','dynamic_outer_pids_counts':'NOT_COMPARED'}
    C.atomic(path,receipt);return receipt

def verify_compatibility_receipt(path,proposal,expected_actor):
    receipt=C.load(path);policy=validate_policy(proposal);source=Path(receipt['actual_isolation_path'])
    C.check(source.resolve().is_relative_to(S.RUNTIME.resolve()) and C.digest(source)==receipt['actual_isolation_sha256'],'Bound actual outer evidence changed')
    observation=C.load(source);decision=outer_decision(observation,policy['reviewed_static_outer_controls'])
    C.check(all(receipt.get(k)==v for k,v in decision.items()) and receipt['fixture_baseline_sha256']==FIXTURE_SHA and
      receipt['policy_source_sha256']==C.digest(__file__) and receipt['policy_config_sha256']==C.digest(POLICY_PATH),'Outer compatibility direct policy/fixture/source joins differ')
    actor={'pid':expected_actor['pid'],'creation_filetime':expected_actor['creation_filetime']}
    C.check(receipt['actor']==actor=={k:observation['controller'][k] for k in actor},'Actual outer observation actor differs from bound controller')
    return receipt
