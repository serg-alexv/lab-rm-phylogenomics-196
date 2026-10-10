"""Pure config/identity/failed-sentinel guard tests; no WSL/native/config action."""
from pathlib import Path, PurePosixPath
from unittest.mock import patch
import contextlib, copy, io, json, stat, unittest
import stage5_wsl_config_owner as M

HERE=Path(__file__).resolve().parent


class Tests(unittest.TestCase):
    def test_exact_transform_changes_only_two_lines_and_preserves_every_other_byte(self):
        raw=(HERE/M.PREIMAGE_NAME).read_bytes();after=M.transform_config(raw)
        expected=raw.replace(b'systemd=true\n',b'systemd=false\n').replace(b'default=gns3\n',b'default=root\n')
        self.assertEqual(after,expected);self.assertEqual(len(after),322)
        self.assertEqual(sum(a!=b for a,b in zip(raw.splitlines(),after.splitlines())),2)
        for bad in (after,raw+b'\n',raw.replace(b'protectBinfmt=true',b'protectBinfmt=nope')):
            with self.assertRaises(ValueError):M.transform_config(bad)

    def test_section_specific_guard_rejects_wrong_sections_and_wrong_exact_target(self):
        raw=(HERE/M.PREIMAGE_NAME).read_bytes()
        for bad in (raw.replace(b'[boot]',b'[user]'),raw.replace(b'[user]',b'[boot]'),raw.replace(b'systemd=true',b'systemd=TRUE')):
            with patch.object(M,'PREIMAGE_SHA',M.digest(bad)),self.assertRaises(ValueError):M.transform_config(bad)

    def test_default_noop_and_linux_paths_remain_posix_on_windows(self):
        with (patch('sys.argv',['stage5_wsl_config_owner.py']),patch.object(M,'windows_main',side_effect=AssertionError('No owner')),
              contextlib.redirect_stdout(io.StringIO()) as output):
            self.assertEqual(M.main(),0)
        value=json.loads(output.getvalue());self.assertEqual(value['WSL_launches'],0);self.assertEqual(value['config_changes'],0)
        self.assertIsInstance(M.LWORK,PurePosixPath);self.assertTrue(str(M.LWORK/'stage5_wsl_config_owner.py').startswith('/mnt/c/'))
        self.assertNotIn('\\',str(M.LWORK/'stage5_wsl_config_owner.py'))

    def registration(self,uid):
        return dict(DistributionName='Ubuntu',Version=2,DefaultUid=uid,Flags=15,BasePath=M.UBUNTU_BASE)

    def test_registry_exact_identity_and_uid_transition(self):
        before=self.registration(1000);self.assertEqual(M.registry_gate(before,1000),before)
        self.assertEqual(M.registry_gate(self.registration(0),0,before)['DefaultUid'],0)
        for key,bad in [('DefaultUid',False),('DefaultUid',0.0),('Version',2.0),('Flags',15.0),('DistributionName','Other'),('BasePath',r'C:\Other')]:
            value=self.registration(0);value[key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):M.registry_gate(value,0,before)

    def test_running_query_decode_and_no_automatic_launch_commands(self):
        for raw in (b'',b'\r\n','\r\n'.encode('utf-16'),'\r\n'.encode('utf-16-le')):
            self.assertEqual(M.running_gate(raw)['decoded_names'],[])
        for raw in (b'Ubuntu\r\n','Ubuntu\r\n'.encode('utf-16'),b'Error',b'\x00',b'x'*65537):
            with self.assertRaises(ValueError):M.running_gate(raw)
        self.assertEqual(M.fixed_argv('set_default_user'),[M.WSL,'--manage','Ubuntu','--set-default-user','root'])
        self.assertEqual(M.fixed_argv('shutdown'),[M.WSL,'--shutdown'])
        self.assertEqual(M.fixed_argv('running_after'),[M.WSL,'--list','--running','--quiet'])
        with self.assertRaises(ValueError):M.fixed_argv('relaunch')

    def test_exact_disabled_tasks_and_owner_census(self):
        value={'selected':[],'helpers':[],'tasks':[dict(name='LAB_RM_'+str(i),state='Disabled') for i in range(18)]}
        self.assertEqual(M.census_gate(value),value)
        for kind in ('owner','helper','enabled','missing','duplicate'):
            bad=copy.deepcopy(value)
            if kind=='owner':bad['selected']=[dict(pid=5)]
            if kind=='helper':bad['helpers']=[dict(pid=6)]
            if kind=='enabled':bad['tasks'][0]['state']='Ready'
            if kind=='missing':bad['tasks'].pop()
            if kind=='duplicate':bad['tasks'][1]=bad['tasks'][0]
            with self.subTest(kind=kind),self.assertRaises(ValueError):M.census_gate(bad)
        argv=M.census_argv(12345);self.assertEqual(argv[0],M.POWERSHELL);self.assertIn('$r.ProcessId -eq 12345',argv[-1])
        self.assertIn('$r.ProcessId -eq $PID',argv[-1]);self.assertNotIn('ChatGPT.exe',argv[-1])
        with self.assertRaises(ValueError):M.census_argv(True)

    def sentinel(self,windows=False):
        request=json.loads((HERE/'stage5_unc_bind_actual_postiq_02/request.json').read_bytes())
        prepared=json.loads((HERE/'stage5_unc_bind_actual_postiq_02/prepared.json').read_bytes())
        directory=dict(device=2096,inode=33554545,mode=stat.S_IFDIR|0o700,uid=0,gid=0,nlink=2,bytes=4096,mtime_ns=1,ctime_ns=1)
        files={}
        for name,key in [('linux.bin','linux_payload_hex')]+([('windows.bin','windows_payload_hex')] if windows else []):
            data=bytes.fromhex(request[key]);receipt=copy.deepcopy(prepared['linux_file']) if name=='linux.bin' else dict(device=2096,inode=9999,bytes=len(data),sha256=M.digest(data),mtime_ns=2)
            info=dict(device=receipt['device'],inode=receipt['inode'],mode=stat.S_IFREG|0o644,uid=0,gid=0,nlink=1,bytes=len(data),mtime_ns=receipt['mtime_ns'],ctime_ns=1)
            files[name]={'metadata':info,'tiny_read_receipt':receipt,'payload_hex':data.hex()}
        return directory,list(files),files,request,prepared

    def test_known_failed_sentinel_with_optional_windows_leaf_is_recoverable(self):
        self.assertTrue(M.sentinel_guard(*self.sentinel(False)));self.assertTrue(M.sentinel_guard(*self.sentinel(True)))

    def test_unknown_or_changed_sentinel_rejects_before_any_delete(self):
        for change in ('unknown','missing_linux','wrong_nonce','inode','device_float','mode','owner','payload','hardlink','linux_birth','window_payload'):
            directory,names,files,request,prepared=self.sentinel(True)
            if change=='unknown':names.append('unknown.bin')
            if change=='missing_linux':names.remove('linux.bin');files.pop('linux.bin')
            if change=='wrong_nonce':request['nonce']='a'*32
            if change=='inode':directory['inode']+=1
            if change=='device_float':directory['device']=2096.0
            if change=='mode':directory['mode']=stat.S_IFDIR|0o755
            if change=='owner':directory['uid']=1000
            if change=='payload':files['linux.bin']['payload_hex']='00'
            if change=='hardlink':files['linux.bin']['metadata']['nlink']=2
            if change=='linux_birth':files['linux.bin']['tiny_read_receipt']['mtime_ns']+=1
            if change=='window_payload':files['windows.bin']['payload_hex']='00'
            with self.subTest(change=change),self.assertRaises(ValueError):M.sentinel_guard(directory,names,files,request,prepared)

    def test_terminal_scope_native_child_and_failure_exit_guards(self):
        value=dict(schema='STAGE05_WSL_CONFIG_LINUX_TERMINAL_V1',scope=M.SCOPE,owner_nonce='a'*32,request_sha256='b'*64,
            source_sha256='c'*64,boot_id='boot',owned_closure_proven=True,remaining_direct_children=[],owned_command_count=0,
            scientific_adoption_authorized=False,state='PASS_EXACT_TWO_LINE_CONFIG_REPLACED_READBACK')
        args=('a'*32,'b'*64,'c'*64,'boot',0);self.assertTrue(M.terminal_gate(value,*args))
        for key,bad in [('owned_command_count',True),('owned_command_count',1),('remaining_direct_children',[99]),('owned_closure_proven',False),('scope','OTHER'),('error',{})]:
            changed=copy.deepcopy(value);changed[key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):M.terminal_gate(changed,*args)
        changed=copy.deepcopy(value);changed['state']='FAILED';self.assertFalse(M.terminal_gate(changed,*args[:-1],2))


if __name__=='__main__':unittest.main()
