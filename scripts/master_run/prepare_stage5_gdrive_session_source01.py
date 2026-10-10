"""Create a separate session-parent-aware G owner; never edit prior source."""
from pathlib import Path
import hashlib

W=Path(__file__).resolve().parent
old=W/'stage5_gdrive_view_postboot.py';new=W/'stage5_gdrive_view_session.py'
original=old.read_bytes()
assert hashlib.sha256(original).hexdigest()=='a0b903970844e33d1e938a9d388b62981333e54991d4b5e86f8129651e3b4f06'
assert not new.exists()
source=original.decode()
addition='''def session_namespace_gate(value,expected=None):
    current=value['current_record'];parent=value['parent_record'];pid=value['parent_pid']
    need(type(pid) is int and pid>0 and parent['pid']==pid and current['ppid']==pid
         and int(parent['start_ticks'])>0 and int(current['start_ticks'])>0
         and parent['state'] not in ('Z','X','x') and value['parent_executable']=='/init',
         'Exact live WSL /init session-parent identity required')
    need(re.fullmatch(r'mnt:\\[[0-9]+\\]',value['self']) is not None
         and value['parent']==value['self'],'WSL session parent and current mount namespaces differ')
    if expected is not None:
        need(value['parent_pid']==expected['parent_pid']
             and value['parent_executable']==expected['parent_executable']
             and value['self']==expected['self'] and value['parent']==expected['parent']
             and all(current[k]==expected['current_record'][k] for k in ('pid','ppid','start_ticks'))
             and all(parent[k]==expected['parent_record'][k] for k in ('pid','start_ticks')),
             'WSL session parent birth/executable/namespace changed')
    return value


def session_namespace_observation(process_helper):
    current=process_helper.proc_record(os.getpid());pid=os.getppid()
    value={'self':os.readlink('/proc/self/ns/mnt'),'parent':os.readlink(f'/proc/{pid}/ns/mnt'),
           'pid1':os.readlink('/proc/1/ns/mnt'),'pid1_role':'DIAGNOSTIC_ONLY_NOT_SESSION_IDENTITY',
           'parent_pid':pid,'parent_record':process_helper.proc_record(pid),
           'parent_executable':os.readlink(f'/proc/{pid}/exe'),'current_record':current,
           'future_storage_and_UNC_visibility':'REQUIRES_SEPARATE_FRESH_GATES'}
    return session_namespace_gate(value)


'''
anchor='def linux_main(args):\n'
assert source.count(anchor)==1;source=source.replace(anchor,addition+anchor)
before="        namespace={'self':os.readlink('/proc/self/ns/mnt'),'pid1':os.readlink('/proc/1/ns/mnt')}\n        result['mount_namespace']=namespace;need(namespace['self']==namespace['pid1'],'Isolated mount namespace cannot establish future WSL view')"
after="        namespace=session_namespace_observation(P)\n        result['mount_namespace']=namespace;result['session_parent_initial_verified']=True\n        result['future_storage_and_UNC_visibility']='REQUIRES_SEPARATE_FRESH_GATES'"
assert source.count(before)==1;source=source.replace(before,after)
before="            supervisor.prelaunch_check=lambda *_: mount_prelaunch_gate(rows(),before,empty_directory(MOUNTPOINT),\n                result['linux_empty_mount_underlay'],exists(LROOT))"
after="            def session_prelaunch(*_):\n                session_namespace_gate(session_namespace_observation(P),namespace)\n                return mount_prelaunch_gate(rows(),before,empty_directory(MOUNTPOINT),\n                    result['linux_empty_mount_underlay'],exists(LROOT))\n            supervisor.prelaunch_check=session_prelaunch"
assert source.count(before)==1;source=source.replace(before,after)
before="        supervisor.check_owner()\n        need(sha(request)==args.request_sha256 and sha(__file__)==value['source_sha256']"
after="        supervisor.check_owner()\n        result['session_parent_final']=session_namespace_gate(session_namespace_observation(P),namespace)\n        result['session_parent_final_verified']=True\n        need(sha(request)==args.request_sha256 and sha(__file__)==value['source_sha256']"
assert source.count(before)==1;source=source.replace(before,after)
compile(source,str(new),'exec')
with new.open('x',encoding='utf-8',newline='\n') as stream:stream.write(source)
assert old.read_bytes()==original
print(hashlib.sha256(new.read_bytes()).hexdigest())
