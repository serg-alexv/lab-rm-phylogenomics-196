"""Default NOOP; append the reviewed checked-unlock lifecycle to actual G08 pins.

Only C source preparation. Never invokes G, WSL, process handles or workflow locks.
"""
from pathlib import Path
import argparse,ast,hashlib,importlib.util,json,os

WORK=Path(__file__).resolve().parent
RECIPE='prepare_stage5_gdrive_postfallback_source.py'
RECIPE_SHA='d8fb432cceb2d09e636d154de48b9f18b54a956ab8f2c722b5963f4c21724042'
PROFILE='stage5_wsl_host_profile_fallback_owner.py'
PROFILE_SHA='49596d3e9c0ef684978d0cbb05bc57d97b100f08ab77a7a4ece598abc2221299'
BASE='stage5_gdrive_view_postprofile.py'
BASE_SHA='1ec2380d218128e325954552057ed1215268297862e2910550b2eb7c46a112e9'
INPUT='stage5_gdrive_view_postfallback.py'
OUTPUT='stage5_gdrive_view_postfallback_checked_unlock.py'
PENDING='G_DRIVE_VIEW_VALIDATED_PENDING_EXPLICIT_UNLOCK'
PASS='PASS_NONSCIENTIFIC_G_DRIVE_VIEW_HELPER'

def need(ok,message):
    if not ok:raise ValueError(message)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
def functions(raw):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)}
def fresh_pins(raw):
    return next(ast.literal_eval(n.value) for n in ast.parse(raw).body if isinstance(n,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id=='FRESH_PINS' for t in n.targets))

def finalizer(profile):
    need(digest(profile)==PROFILE_SHA,'Exact reviewed49596 profile source required')
    tree=ast.parse(profile);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='finish_after_unlock')
    source=ast.get_source_segment(profile.decode(),node)
    replacements={
        'HOST_PROFILE_VALIDATED_PENDING_EXPLICIT_UNLOCK':PENDING,
        'PASS_NONSCIENTIFIC_WINDOWS_HOST_PROFILE_CHANGED_AND_ALL_DISTROS_STOPPED':PASS,
        'STAGE05_HOST_PROFILE_FINAL_PUBLICATION_FAILURE_V1':'STAGE05_G_DRIVE_FINAL_PUBLICATION_FAILURE_V1',
        'Profile-owned stop changed; preserve':'G-owned stop changed; preserve',
        'Profile publication failure receipt readback differs':'G publication failure receipt readback differs',
        'digest(path.read_bytes())':'sha(path)',
        'digest(stop.read_bytes())':'sha(stop)',
    }
    for before,after in replacements.items():
        need(before in source,'Reviewed finalizer substitution missing');source=source.replace(before,after)
    return source

TAIL='''        record.update(owned_closure_proven=closed,retained_client_terminal=terminal,
                      log_hash_scope='CLOSED_FULL_LOGS' if closed else 'PARTIAL_UNPROVEN_WRITER',
                      elapsed_seconds=time.monotonic()-start,utc=A.utc())
        try:
            for n in ['wsl.stdout.txt','wsl.stderr.txt']:
                if exists(out/n):record[n+'_sha256']=sha(out/n)
        except BaseException as error:
            record.update(state='FAILED',retained_client_finalizer_error={'kind':type(error).__name__,'scope':'LOG_HASH'})
        record['retained_client_handle_closed']=child is None
        if child is not None:
            try:
                need(terminal is not None and terminal['exited'] is True,'Retained client terminal missing before handle close')
                child._handle.Close()
                need(getattr(child._handle,'closed',False) is True,'Retained client handle close unproven')
                record['retained_client_handle_closed']=True
            except BaseException as error:
                record.update(state='FAILED',retained_client_finalizer_error={'kind':type(error).__name__,'scope':'HANDLE_CLOSE'})
        finish_after_unlock(A,lock,out,record,stop,stop_sha,nonce,closed)
'''

def render(raw,baseline,profile,recipe):
    need(digest(baseline)==BASE_SHA,'Frozen G1ec baseline required')
    need(recipe.render(baseline,fresh_pins(raw))==raw,'Input must be exactly the frozen six-pin G08 transform')
    source=raw.decode();old=baseline.decode()
    begin=old.index('        if closed and stop_sha is not None:\n')
    end=old.index("    print(json.dumps({'state':record['state'],'result':str(out/'result.json')}))",begin)
    old_tail=old[begin:end]
    need(source.count(old_tail)==1,'One original G Windows lifecycle tail required')
    source=source.replace(old_tail,TAIL)
    assignment="record['state']='"+PASS+"'"
    need(source.count(assignment)==1,'One G pre-unlock success assignment required')
    source=source.replace(assignment,"record['state']='"+PENDING+"'")
    old_return="return 0 if record['state'].startswith('PASS_') and closed and lock.released else 2"
    need(source.count(old_return)==1,'One original G Windows return required')
    source=source.replace(old_return,"return 0 if record['state']=='"+PASS+"' and closed and lock.released and record.get('original_unlock_receipt_proven') is True and record.get('owned_stop_cleared_after_unlock') is True and record.get('retained_client_handle_closed') is True else 2")
    helper=finalizer(profile)
    marker='def windows_main(args):'
    need(source.count(marker)==1,'One G Windows owner definition required')
    source=source.replace(marker,helper+'\n\n\n'+marker)
    compile(source,OUTPUT,'exec')
    before=functions(raw);after=functions(source)
    need(set(after)==set(before)|{'finish_after_unlock'},'Only one finalizer function may be added')
    need(all(after[k]==v for k,v in before.items() if k!='windows_main'),'Non-Windows G function changed')
    return source.encode()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--input-sha256');args=parser.parse_args()
    if not args.prepare:
        print(json.dumps({'state':'NO_OP_G08_CHECKED_UNLOCK_SOURCE_PREPARATION','source_written':False,'G_invocations':0,'WSL_launches':0}));return 0
    need(digest((WORK/RECIPE).read_bytes())==RECIPE_SHA,'Frozen G08 pin recipe differs')
    R=module('_frozen_G08_pin_recipe',WORK/RECIPE)
    baseline=R.read_plain(WORK/BASE);profile=R.read_plain(WORK/PROFILE);raw=R.read_plain(WORK/INPUT)
    need(digest(raw)==args.input_sha256,'Explicit actual generated G08 source pin required')
    candidate=render(raw,baseline,profile,R);pins=fresh_pins(raw)
    actual={name:R.read_plain(WORK/name) for name in pins}
    need(all(digest(actual[name])==pin for name,pin in pins.items()),'Actual six fresh08 receipts/review differ')
    namespace={'__name__':'_G08_checked_unlock_source_validation','__file__':str(WORK/OUTPUT)}
    exec(compile(candidate,str(WORK/OUTPUT),'exec'),namespace)
    proof=WORK/R.NEW_DIR/'toolchain_proof.json'
    boot=namespace['fresh_toolchain_gate'](WORK,proof,pins[R.NEW_DIR+'/toolchain_proof.json'])
    need(boot!=R.OLD_BOOT,'A genuinely new independently accepted boot is required')
    need(R.read_plain(WORK/BASE)==baseline and R.read_plain(WORK/PROFILE)==profile and R.read_plain(WORK/INPUT)==raw
         and digest(R.read_plain(WORK/RECIPE))==RECIPE_SHA and all(R.read_plain(WORK/name)==data for name,data in actual.items()),'Final input/source drift')
    output=WORK/OUTPUT;need(not output.exists() and not output.is_symlink(),'Preserve existing checked source')
    with output.open('xb') as stream:need(stream.write(candidate)==len(candidate),'Short checked G source write');stream.flush();os.fsync(stream.fileno())
    need(output.read_bytes()==candidate,'Checked G source readback differs')
    print(json.dumps({'state':'PASS_C_G08_PIN_AND_CHECKED_UNLOCK_SOURCE_ONLY','source':str(output),'sha256':digest(candidate),
        'input_source_sha256':digest(raw),'actual_boot':boot,'fresh_pins':pins,'actual_G_invocation':'NOT_RUN',
        'adoption':'Independent generated-source review and root publication required before G invocation'}));return 0

if __name__=='__main__':raise SystemExit(main())
