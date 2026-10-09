"""Pure owner predicates/default; no Win API, original lock, WSL or G execution."""
import contextlib,copy,io,sys,unittest
from unittest.mock import patch
import stage5_memory_observation_owner as V


def fixture():
    birth={'pid':1,'creation_filetime':2,'executable':V.WSL,'session_id':1}
    terminal=dict(birth,exited=True,exit_code=2,exit_filetime=3)
    return {'result.json':{'scope':'NONSCIENTIFIC_STAGE5_SETUP_ONLY','step':'runtime','state':'FAILED',
        'owned_closure_proven':True,'failed_scope_closed':True,'unknown_closure_stop_preserved':False,
        'owner_nonce':'a'*32,'actual_wsl_exit':terminal},
        'lock_released.json':{'state':'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED','released':True},
        'linux_terminal.json':{'schema':'STAGE05_SETUP_LINUX_TERMINAL_V1','state':'FAILED','owner_nonce':'a'*32,
            'owned_closure_proven':True,'remaining_direct_children':[],'scientific_adoption_authorized':False,
            'bootstrap':{'boot_id':'00000000-0000-0000-0000-000000000001'}},
        'wsl_exit.json':{'owner_nonce':'a'*32,'birth':birth,'terminal':terminal}}


class Contracts(unittest.TestCase):
    def test_default_noop_never_imports_operational_modules(self):
        with (patch.object(sys,'argv',['test']),patch.object(V,'load',side_effect=AssertionError('NO IMPORT')),
              contextlib.redirect_stdout(io.StringIO()) as output):
            self.assertEqual(V.main(),0)
        self.assertIn('PREPARED_NOT_RUN',output.getvalue())

    def test_closed_failed_runtime04_is_not_success(self):
        value=fixture();self.assertEqual(V.prior_gate(value),value['linux_terminal.json']['bootstrap']['boot_id'])
        self.assertEqual(value['result.json']['state'],'FAILED')

    def test_prior_unclosed_or_unreleased_scope_rejected(self):
        for location,key,bad in [('result.json','owned_closure_proven',False),
            ('result.json','unknown_closure_stop_preserved',True),('result.json','failed_scope_closed',False),
            ('lock_released.json','released',False),('linux_terminal.json','remaining_direct_children',[123])]:
            value=fixture();value[location][key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):V.prior_gate(value)

    def test_prior_exact_client_birth_replacement_rejected(self):
        value=copy.deepcopy(fixture());value['wsl_exit.json']['birth']['creation_filetime']=9
        with self.assertRaises(ValueError):V.prior_gate(value)

    def test_retained_actual_exit_required(self):
        value=fixture()['wsl_exit.json'];V.exit_gate(value['birth'],value['terminal'])
        for key,bad in [('pid',9),('creation_filetime',9),('exited',False),('exit_filetime',1),('session_id',9)]:
            terminal=dict(value['terminal']);terminal[key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):V.exit_gate(value['birth'],terminal)

    def test_linux_observation_exact_nonce_source_and_zero_effects(self):
        value={'schema':'STAGE05_READ_ONLY_LINUX_MEMORY_OBSERVATION_V1','state':'OBSERVATION_ONLY_NO_RECLAMATION',
            'nonce':'a'*32,'source_sha256':V.OBS_SHA,'cache_reclamation_calls':0,'native_children_launched':0,
            'runtime_payload_bytes_read':0,'boot_id':'00000000-0000-0000-0000-000000000001','self_pid':1}
        V.observation_gate(value,'a'*32)
        for key,bad in [('nonce','b'*32),('source_sha256','b'*64),('cache_reclamation_calls',1),
                        ('native_children_launched',1),('runtime_payload_bytes_read',1)]:
            changed=dict(value);changed[key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):V.observation_gate(changed,'a'*32)

    def test_unavailable_stop_path_is_not_absence(self):
        class Unknown:
            def lstat(self):raise PermissionError('SYNTHETIC UNAVAILABLE')
        with self.assertRaises(PermissionError):V.absent(Unknown())


if __name__=='__main__':unittest.main()
