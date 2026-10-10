"""C-only frozen source/pure-check peer; never signals or accesses actual Linux."""
from pathlib import Path
import ast, datetime, hashlib, json, subprocess, sys
import review_stage5_postboot_gate as R
W=Path(__file__).resolve().parent
PINS={'stage5_cancel_exact_waiting_bootstrap.py':'7b02c2f05750371dbb9dca9026a86318054f41cdb0214aa22182bbf34da6c63b',
      'test_stage5_cancel_exact_waiting_bootstrap.py':'818903fc39bd00507807760800a50124040b4d3ae9f354cafc57e8f4b0c6bf1e'}
def main():
    out=W/'stage5_cancel_exact_waiting_linux_source_independent_review01.json';R.require(not out.exists(),'Preserve cancellation peer')
    value={'schema':'STAGE05_EXACT_WAITING_CANCEL_LINUX_SOURCE_PEER_V1','state':'FAILED_SOURCE_REVIEW','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'reviewer_source_sha256':R.sha(Path(__file__)),'actual_signal_WSL_API_lock_process_effects':'NOT_RUN','target_termination_or_original_owner_unlock_proven':False,
           'method':'C-only frozen source/dependency/current fixed C owner/launch bytes and AST review,10 synthetic fake-proc/fake-pidfd tests plus default NOOP. No actual Linux /proc, UNC/G, WSL, lock or signal.'}
    try:
        for name,pin in PINS.items():R.require(R.sha(W/name)==pin,'Frozen cancellation member differs')
        tree=ast.parse(R.data(W/'stage5_cancel_exact_waiting_bootstrap.py'))
        assignments={target.id:ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) for target in node.targets if isinstance(target,ast.Name) and target.id in ('BOOT','NONCE','WINDOWS_OWNER','PINS','LOCK')}
        for name,pin in assignments['PINS'].items():R.require(R.sha(W/name)==pin,'Exact cancellation source/config/active owner/launch differs')
        R.require(assignments['BOOT']=='f0ffcebc-4901-479d-9559-89d45e9cfa38' and assignments['NONCE']=='1439a454dde8448f8f9606b6de6ac702'
                  and assignments['WINDOWS_OWNER']==(24488,'134360766940521715'),'Selected current scope differs')
        R.lock(assignments['LOCK'])
        attrs=[n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
        R.require(attrs.count('verified_pidfd')==attrs.count('send_pidfd_signal')==1 and not set(attrs)&{'kill','killpg','Popen','run','system','fork','WorkflowLock'},'Cancellation has extra signal/child/lock route')
        signal_call=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='send_pidfd_signal')
        R.require(ast.dump(signal_call.args[1])==ast.dump(ast.parse('signal.SIGTERM',mode='eval').body),'Cancellation signal is not exact SIGTERM')
        checks=[]
        for name,count in [('test_stage5_cancel_exact_waiting_bootstrap.py',10),('stage5_cancel_exact_waiting_bootstrap.py',0)]:
            p=subprocess.run([sys.executable,'-B',str(W/name)],cwd=W,capture_output=True,text=True,timeout=30)
            R.require(p.returncode==0,'Pure cancellation checks failed: '+p.stderr[-2500:])
            if count:R.require('Ran 10 tests' in p.stderr,'Focused cancellation count differs')
            else:R.require(json.loads(p.stdout)['state']=='PREPARED_NOT_RUN' and json.loads(p.stdout)['signal_count']==0,'Default cancellation NOOP differs')
            checks.append({'name':name,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        value.update(state='PASS_EXACT_WAITING_LINUX_PIDFD_SIGTERM_SOURCE_ONLY',frozen_sources=PINS,checks=checks,source_dependencies_and_exact_active_owner_launch_pins=assignments['PINS'],reviewed_contracts=['One fixed current Linux boot, config30a86, original Windows owner PID24488/birth134360766940521715, nonce1439 and exact original lock/lease identity','Fresh <=6s denied admission, exact typed policy and owner lease, initial transaction0001 only; execution/bundle/identity/complete/status/admission/owner-final paths must be absent','Unique full-argv target, pinned actual interpreter bytes/real executable, no child, live bounded /init ancestry and process births repeatedly compared','Unchanged P.verified_pidfd retains matching bootstrap birth; same full target identity and current waiting conditions rechecked around durable signal intent; one pidfd SIGTERM only, no numeric PID fallback/retry','Finite20s Linux alarm; explicit pidfd close result; C output never claims target termination, successful native scope closure or original owner unlock','Any absent/ambiguous/drifted target/precondition yields no signal and natural1800s admission expiry fallback; signal attempt uncertainty requires original owner terminal reconciliation'],native_zero_launch_interpretation='Fresh observed precondition; check/signal is not an atomic freeze of the target. Actual original runner status/no_native_launch/closure and retained client exit/unlock remain mandatory.',unchanged_runner_signal_semantics='Pinned R500dc handles SIGTERM as Retryable; pinned P.e5be closes any exact native scope before normal failed terminal. Actual evidence is required before a new config/run.',pending_Windows_wrapper='Separate retained original U0664 Windows Job launcher source/peer and actual gate must be accepted before root operation; this report does not adopt an unreviewed wrapper.',old_waiting_scope_unchanged_by_review=True)
        for name,pin in {**PINS,**assignments['PINS']}.items():R.require(R.sha(W/name)==pin,'Frozen cancellation control drifted')
    except BaseException as error:value['error']={'kind':type(error).__name__,'message':str(error)}
    value['checked_files']=R.CHECKED
    with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':value['state'],'error':value.get('error'),'report':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checker_sha256':R.sha(Path(__file__))}))
    return 0 if value['state'].startswith('PASS_') else 1
if __name__=='__main__':raise SystemExit(main())
