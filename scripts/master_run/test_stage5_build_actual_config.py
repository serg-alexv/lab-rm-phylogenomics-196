"""Pure first-config contracts; no Windows resource/lock, G or WSL calls."""
from pathlib import Path
from unittest.mock import patch
import copy, hashlib, json, tempfile, unittest
import stage5_build_actual_config as B


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
    def test_valid_budget_preserves_method_and_disables_resource_wait(self):
        original,request=fixture();before=copy.deepcopy(original);actual=B.explicit_policy(original,request)
        self.assertEqual(original,before);self.assertEqual(actual['support_source_sha256'],original['support_source_sha256'])
        self.assertEqual(actual['root'],original['root']);self.assertEqual(actual['resource_policy']['threads'],2)
        self.assertEqual(actual['resource_policy']['resource_wait_seconds'],0)

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
