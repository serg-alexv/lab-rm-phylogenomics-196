"""Create a separate opt-in postboot G-view owner; preserve original source."""
from pathlib import Path
import hashlib

W=Path(__file__).resolve().parent
old=W/'stage5_gdrive_view.py';new=W/'stage5_gdrive_view_postboot.py'
original=old.read_bytes()
assert hashlib.sha256(original).hexdigest()=='edc02834f889cdd9bed8bce350d2b9fe2bbd79347f65a0ae124afdaec9f4dfa8'
assert not new.exists()
source=original.decode().replace('\r\n','\n')
addition='''FRESH_TOOLCHAIN_DIR='stage5_setup_toolchain_actual_postiq_05'
LINUX_SETUP_SHA='24aab72b74dd0aab6c58cac4951c30e6b1bfc9462460486748b546e50ec92e27'
FRESH_PINS={
 'stage5_setup_toolchain_actual_postiq_05/result.json':'43ad814d2cb055fbcc0578862d3e75f3d236452025a0512250e5914a7f7aef43',
 'stage5_setup_toolchain_actual_postiq_05/lock_released.json':'daa80ec0b44bcca53388cb77651eecdecf40da7c0877fdce5fc2f540cd62e289',
 'stage5_setup_toolchain_actual_postiq_05/toolchain_proof.json':'106e1bc310f11d34d78f0d7bdc2b311a2b457e5c68c0e32aad3f8fc0a718446c',
 'stage5_setup_toolchain_actual_postiq_05/linux_terminal.json':'f21021be37d99278eda829deb6830cc145425b8d3a031f34fcef7db23d676b04',
 'stage5_setup_toolchain_actual_postiq_05/wsl_exit.json':'531943141ccfee0ea36ef72c4e94d3e19b13ed723ebf086f52883bb11089e46f',
 'stage5_toolchain05_postboot_independent_review.json':'2c542838c2a929bd59b86d1674e90bae52406d6583a9121a554da9909cd25516'}


def fresh_toolchain_gate(base,path,pin):
    base=Path(base);path=Path(path);directory=base/FRESH_TOOLCHAIN_DIR
    need(path==directory/'toolchain_proof.json' and path==path.resolve()
         and re.fullmatch('[a-f0-9]{64}',pin or '') is not None,'Exact explicit fresh toolchain05 proof/SHA required')
    plain_chain(directory)
    need(pin==FRESH_PINS[FRESH_TOOLCHAIN_DIR+'/toolchain_proof.json'],'Fresh selected proof pin differs')
    values={name:json.loads(tiny(base/name)) for name in FRESH_PINS}
    need(all(sha(base/name)==digest for name,digest in FRESH_PINS.items()),'Fresh published toolchain evidence changed')
    prefix=FRESH_TOOLCHAIN_DIR+'/'
    result=values[prefix+'result.json'];proof=values[prefix+'toolchain_proof.json']
    terminal=values[prefix+'linux_terminal.json'];unlock=values[prefix+'lock_released.json'];client=values[prefix+'wsl_exit.json']
    review=values['stage5_toolchain05_postboot_independent_review.json'];boot=proof['boot_id']
    need(result['state']=='PASS_NONSCIENTIFIC_SETUP_AND_WINDOWS_READBACK' and result['step']=='toolchain'
         and result['source_sha256']==PINS['stage5_setup_windows.py'] and result['linux_source_sha256']==LINUX_SETUP_SHA
         and result['owned_closure_proven'] is True and result['unknown_closure_stop_preserved'] is False,
         'Fresh actual setup/source/closure differs')
    need(terminal['state']=='PASS_NONSCIENTIFIC_SETUP_STEP' and terminal['step']=='toolchain'
         and terminal['source_sha256']==LINUX_SETUP_SHA and terminal['owner_nonce']==result['owner_nonce']
         and terminal['owned_closure_proven'] is True and terminal['remaining_direct_children']==[]
         and terminal['bootstrap']['boot_id']==boot and terminal['toolchain_proof_sha256']==pin
         and result['linux_terminal_sha256']==FRESH_PINS[prefix+'linux_terminal.json'],'Fresh Linux/toolchain proof binding differs')
    need(proof['schema']=='STAGE05_TOOLCHAIN_LOOP_PROOF_V1' and proof['helper_sha256']==LINUX_SETUP_SHA
         and proof['mount']['filesystem']=='ext4' and re.fullmatch('[a-f0-9-]{36}',boot) is not None
         and boot!='64d6e318-170c-4bef-9538-90fd218881af','Fresh toolchain proof boot/filesystem differs')
    end=client['terminal'];birth=client['birth']
    need(result['actual_wsl_exit']==end and client['owner_nonce']==result['owner_nonce']
         and result['wsl_exit_receipt_sha256']==FRESH_PINS[prefix+'wsl_exit.json']
         and end['exited'] is True and end['exit_code']==0 and end['pid']==birth['pid']
         and end['creation_filetime']==birth['creation_filetime'] and end['exit_filetime']>end['creation_filetime'],
         'Fresh retained Windows WSL closure differs')
    need(unlock['state']=='EXPLICIT_OS_BYTE_UNLOCK_COMPLETED' and unlock['released'] is True,
         'Fresh original byte unlock missing')
    need(review['state']=='PASS_COMPLETED_POSTBOOT_GATE_EXACT_SOURCE_CLOSURE_AND_BYTES' and review['kind']=='toolchain'
         and review['actual_result_sha256']==FRESH_PINS[prefix+'result.json']
         and review['unlock_sha256']==FRESH_PINS[prefix+'lock_released.json']
         and review['detail']['linux_boot_id']==boot and review['detail']['candidate_sha256']==pin,
         'Fresh independent actual toolchain acceptance differs')
    return boot


'''
anchor='def imports(base,names):\n'
assert source.count(anchor)==1;source=source.replace(anchor,addition+anchor)
source=source.replace("    boot=prior_gate(prior)\n","    historical_boot=prior_gate(prior)\n    boot=fresh_toolchain_gate(WORK,args.fresh_toolchain_proof,args.fresh_toolchain_proof_sha256)\n")
source=source.replace("        'boot_id':boot,'scientific_adoption_authorized':False,'lease_replace_stats':{}}",
"        'boot_id':boot,'historical_boot_id_preserved':historical_boot,'fresh_toolchain_pins':FRESH_PINS,\n        'fresh_toolchain_proof':str(args.fresh_toolchain_proof),'fresh_toolchain_proof_sha256':args.fresh_toolchain_proof_sha256,\n        'scientific_adoption_authorized':False,'lease_replace_stats':{}}")
source=source.replace("                'boot_id':boot,'linux_root':str(LROOT),'allow_mount':args.mount,'mount_argv':MOUNT_ARGV,",
"                'boot_id':boot,'linux_root':str(LROOT),'allow_mount':args.mount,'mount_argv':MOUNT_ARGV,\n                'fresh_toolchain_proof':str(LWORK/FRESH_TOOLCHAIN_DIR/'toolchain_proof.json'),\n                'fresh_toolchain_proof_sha256':args.fresh_toolchain_proof_sha256,'fresh_toolchain_pins':FRESH_PINS,")
source=source.replace("    need(boot==value['boot_id'],'Actual Linux boot differs from current closed setup')",
"    need(value['fresh_toolchain_pins']==FRESH_PINS and fresh_toolchain_gate(LWORK,value['fresh_toolchain_proof'],\n         value['fresh_toolchain_proof_sha256'])==boot==value['boot_id'],'Actual Linux boot differs from fresh closed setup')")
source=source.replace("        need(sha(request)==args.request_sha256 and sha(__file__)==value['source_sha256'],'Request/source changed')",
"        need(sha(request)==args.request_sha256 and sha(__file__)==value['source_sha256']\n             and fresh_toolchain_gate(LWORK,value['fresh_toolchain_proof'],value['fresh_toolchain_proof_sha256'])==boot,\n             'Request/source/fresh toolchain proof changed')")
source=source.replace("                 and sha(__file__)==source_sha,'Source/closed evidence changed')",
"                 and fresh_toolchain_gate(WORK,args.fresh_toolchain_proof,args.fresh_toolchain_proof_sha256)==boot\n                 and sha(__file__)==source_sha,'Source/closed fresh evidence changed')")
source=source.replace("    parser.add_argument('--linux',action='store_true');parser.add_argument('--request');parser.add_argument('--request-sha256')",
"    parser.add_argument('--linux',action='store_true');parser.add_argument('--request');parser.add_argument('--request-sha256')\n    parser.add_argument('--fresh-toolchain-proof');parser.add_argument('--fresh-toolchain-proof-sha256')")
compile(source,str(new),'exec')
with new.open('x',encoding='utf-8',newline='\n') as stream:stream.write(source)
assert old.read_bytes()==original
print(hashlib.sha256(new.read_bytes()).hexdigest())
