"""Pure first-config contracts; no Windows resource/lock, G or WSL calls."""
from pathlib import Path
from unittest.mock import patch
import contextlib, copy, hashlib, io, json, tempfile, unittest
import stage5_build_backing_actual_config as B


def fixture():
    template=json.loads((B.WORK/'stage5_atomic_config.template.json').read_bytes())
    request={'schema':'STAGE05_ACTUAL_CONFIG_REQUEST_V1','purpose':'FIRST_APPROVED_GENOME_RESOURCE_MEASUREMENT',
             'resource_basis':'SYNTHETIC TEST BUDGET ONLY; actual detector resources remain unmeasured.',
             'native_resource_bytes':dict(zip(B.FIELDS,[2*1024**3,4*1024**3,2*1024**3,3*1024**3,2*1024**3]))}
    return template,request


def gate(directory):
    value={'state':'PASS_NONSCIENTIFIC_SETUP_AND_WINDOWS_READBACK','step':'runtime',
           'source_sha256':B.PINS['stage5_setup_windows.py'],'linux_source_sha256':B.PINS['stage5_setup_linux.py'],
           'owned_closure_proven':True,'unknown_closure_stop_preserved':False,'owner_nonce':'synthetic',
           'actual_wsl_exit':{'exited':True,'exit_code':0}}
    terminal={'owner_nonce':'synthetic','step':'runtime','source_sha256':B.PINS['stage5_setup_linux.py'],
              'owned_closure_proven':True,'state':'PASS_NONSCIENTIFIC_SETUP_STEP','owned_command_count':1}
    def write(name,obj):
        path=directory/name;path.write_text(json.dumps(obj));return hashlib.sha256(path.read_bytes()).hexdigest()
    value['linux_terminal_sha256']=write('linux_terminal.json',terminal)
    spec={'path':str(directory/'result.json'),'sha256':write('result.json',value),
          'unlock_sha256':write('lock_released.json',{'state':'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED','released':True})}
    return value,terminal,spec,write


class Contracts(unittest.TestCase):
    def test_only_reviewed_transport_pins_and_wait_changed(self):
        original=(B.WORK/'stage5_build_actual_config.py').read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),'15dd2d4de4646d154ebfe503ae91f765d15f9f3cbd9e75099fbbfe703ffa2daa')
        current=(B.WORK/'stage5_build_backing_actual_config.py').read_bytes()
        changes={b"'stage5_windows_owner.py'":b"'stage5_windows_backing_owner.py'",
          b'8851bc4fc48ad3069d4ffabe410e159004ef4fc8d6d0755213fc14c22fe0603d':b'296492aa4205f64058846b9901a7bb3a3458f99eda1c7ff388a6e33cdc38b834',
          b"'stage5_unc_bind_probe.py'":b"'stage5_unc_backing_probe.py'",
          b'0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d':b'779502c38c5db06b68e796abc6e1bd99db72d8f97b1129f9057a3f6b0c4221d5',
          b"result['resource_policy']['resource_wait_seconds']=0":b"result['resource_policy']['resource_wait_seconds']=1800"}
        for before,after in changes.items():current=current.replace(after,before)
        self.assertEqual(current,original)
        for name in ('stage5_unc_backing_probe.py','stage5_windows_backing_owner.py'):
            self.assertEqual(B.sha(B.WORK/name),B.PINS[name])
        self.assertNotIn('stage5_unc_bind_probe.py',B.PINS);self.assertNotIn('stage5_windows_owner.py',B.PINS)

    def test_backing_unc_gate_still_requires_exact_source_cleanup_and_phases(self):
        for field in (None,'source','cleanup','phase','state'):
            with self.subTest(field=field),tempfile.TemporaryDirectory() as tmp:
                work=Path(tmp);directory=work/'unc';directory.mkdir()
                value={'state':'PASS_NONSCIENTIFIC_EXACT_EXT4_BIND_UNC_VISIBILITY',
                  'source_sha256':B.PINS['stage5_unc_backing_probe.py'],'exact_owned_cleanup':True,
                  'steps':[{'phase':p} for p in ('linux-prepare','windows-io','linux-finalize')]}
                if field=='source':value['source_sha256']='0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d'
                if field=='cleanup':value['exact_owned_cleanup']=False
                if field=='phase':value['steps'][1]['phase']='readonly-diagnosis'
                if field=='state':value['state']='PREPARED_NOT_RUN'
                result=directory/'result.json';result.write_text(json.dumps(value))
                unlock=directory/'lock_released.json';unlock.write_text(json.dumps({'state':'EXPLICIT_ORIGINAL_OS_BYTE_UNLOCK','released':True}))
                spec={'path':str(result),'sha256':B.sha(result),'unlock_sha256':B.sha(unlock)}
                with patch.object(B,'WORK',work):
                    if field is None:self.assertEqual(B.checked_gate('unc',spec)[1],value)
                    else:
                        with self.assertRaises(ValueError):B.checked_gate('unc',spec)

    def test_default_noop_does_not_read_gates_import_native_api_or_build(self):
        with (patch('sys.argv',['stage5_build_backing_actual_config.py']),
              patch.object(B,'sha',side_effect=AssertionError('No actual pin read')),
              patch.object(B,'read',side_effect=AssertionError('No actual gate read')),
              patch.object(B.importlib,'import_module',side_effect=AssertionError('No native import')),
              contextlib.redirect_stdout(io.StringIO()) as output):
            self.assertEqual(B.main(),0)
        self.assertEqual(json.loads(output.getvalue())['native_execution'],'NOT_RUN')

    def test_valid_budget_preserves_method_and_sets_finite_resource_wait(self):
        original,request=fixture();before=copy.deepcopy(original);actual=B.explicit_policy(original,request)
        self.assertEqual(original,before);self.assertEqual(actual['support_source_sha256'],original['support_source_sha256'])
        self.assertEqual(actual['root'],original['root']);self.assertEqual(actual['resource_policy']['threads'],2)
        self.assertEqual(actual['resource_policy']['resource_wait_seconds'],1800)

    def test_missing_noninteger_infinite_and_nonpositive_budget_reject(self):
        original,request=fixture()
        for value in (None,0,-1,float('inf'),True,2.5):
            changed=copy.deepcopy(request);changed['native_resource_bytes'][B.FIELDS[0]]=value
            with self.subTest(value=value),self.assertRaises(ValueError):B.explicit_policy(original,changed)
        request['native_resource_bytes'].pop(B.FIELDS[-1])
        with self.assertRaises(ValueError):B.explicit_policy(original,request)

    def test_commit_reserve_rss_and_windows_budget_consistency(self):
        original,request=fixture()
        for key,value in [('commit_requirement_bytes',2*1024**3),('sampled_rss_stop_bytes',3*1024**3),
                          ('process_address_space_limit_bytes',1024**3),('incremental_windows_requirement_bytes',1024**3)]:
            changed=copy.deepcopy(request);changed['native_resource_bytes'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):B.explicit_policy(original,changed)

    def test_prepared_failed_unclosed_and_no_helper_gate_reject(self):
        for field,bad in [('state','PREPARED_NOT_RUN'),('owned_closure_proven',False),
                          ('unknown_closure_stop_preserved',True),('source_sha256','f'*64),('native_exit',1),('no_helper',0)]:
            with self.subTest(field=field),tempfile.TemporaryDirectory() as tmp:
                work=Path(tmp);directory=work/'runtime';directory.mkdir();value,terminal,spec,write=gate(directory)
                with patch.object(B,'WORK',work):B.checked_gate('runtime',spec)
                if field=='native_exit':value['actual_wsl_exit']['exit_code']=bad
                elif field=='no_helper':
                    terminal['owned_command_count']=bad;value['linux_terminal_sha256']=write('linux_terminal.json',terminal)
                else:value[field]=bad
                spec['sha256']=write('result.json',value)
                with patch.object(B,'WORK',work),self.assertRaises(ValueError):B.checked_gate('runtime',spec)

    def test_hash_pin_and_unlock_replacement_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp);directory=work/'runtime';directory.mkdir();_,_,spec,write=gate(directory)
            write('lock_released.json',{'state':'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED','released':False})
            with patch.object(B,'WORK',work),self.assertRaises(ValueError):B.checked_gate('runtime',spec)
            spec['unlock_sha256']=B.sha(directory/'lock_released.json')
            with patch.object(B,'WORK',work),self.assertRaises(ValueError):B.checked_gate('runtime',spec)


if __name__=='__main__':unittest.main()
