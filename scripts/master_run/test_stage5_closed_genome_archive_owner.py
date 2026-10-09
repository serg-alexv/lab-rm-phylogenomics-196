"""Pure closed-owner/terminal gates and own C metadata; never runs WSL or Win APIs."""
from pathlib import Path
from unittest.mock import patch
import copy, json, tempfile, unittest
import stage5_closed_genome_archive_windows as V

ACC='GCF_1.1';NONCE='a'*32


def fixture():
    config={'runtime':{'environment_dir':'/SYNTHETIC_NOT_AN_INSTALL'}}
    owner={'pid':1,'creation_filetime':2}
    birth={'pid':3,'creation_filetime':4,'executable':V.WSL,'session_id':1}
    row={'accession':ACC,'state':'COMPLETE_VALIDATED','status_sha256':'b'*64,
         'actual_wsl_client_exit':dict(birth,exited=True,exit_code=0,exit_filetime=5)}
    values={'result.json':{'state':'COMPLETE_VALIDATED','scope':'ONE_APPROVED_GENOME','selected_accessions':[ACC],
        'approved_genomes':196,'full_panel_complete':False,'genome_results':[row],'owner':owner,
        'linux_script_sha256':V.PINS['stage5_atomic.py'],'linux_supervisor_sha256':V.PINS['stage5_atomic_process.py'],
        'storage_helper_sha256':V.PINS['stage5_work_storage.py'],'lease_helper_sha256':V.PINS['stage5_owner_lease.py']},
        'owner.json':{'owner':owner,'selected_accessions':[ACC],'workflow_lock':{'synthetic':'NO_OS_LOCK'}},
        'owner_lease.json':{'nonce':NONCE,'owner_pid':1,'owner_creation_filetime':'2','workflow_lock':{'synthetic':'NO_OS_LOCK'}},
        'progress.json':{'finished':1,'total':1,'approved_genomes':196,'latest':row,'genome_results':[row]},
        'lock_released.json':{'state':'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED'},ACC+'.exit.json':row,
        ACC+'.launch.json':{'native_wsl_client':birth,'owner_nonce':NONCE,'argv':[V.WSL,'-d','Ubuntu','-u','root','--exec',
            config['runtime']['environment_dir']+'/bin/python','-B',V.LINUX_WORK+'/stage5_atomic.py','--config',
            '/SYNTHETIC_CONFIG','run','--accession',ACC,'--owner-lease','/SYNTHETIC_LEASE','--owner-nonce',NONCE]}}
    return config,values


def terminal(state='FAILED'):
    argv=[V.WSL,'-d','Ubuntu','-u','root','--exec','/usr/bin/python3','-B','/SYNTHETIC_HELPER','--output','/SYNTHETIC_OUTPUT']
    value={'schema':'STAGE05_CLOSED_GENOME_ARCHIVE_LINUX_TERMINAL_V1','scope':V.SCOPE,'owner_nonce':NONCE,
           'source_sha256':'c'*64,'native_launch_count':0,'owned_closure_proven':True,'remaining_direct_children':[],
           'observed_prior_closure_unproven':False,'prior_scope_check_entered':True,'prior_scope_check_complete':True,
           'state':state,'bootstrap':{'argv':argv[8:],'executable':argv[6],
               'boot_id':'00000000-0000-0000-0000-000000000001','identity':{'pid':1,'start_ticks':'2'}}}
    return argv,value


class Contracts(unittest.TestCase):
    def test_bound_closed_single_genome_owner_accepts(self):
        config,values=fixture();result=V.prior_contract(config,ACC,values)
        self.assertEqual(result,{'prior_owner_nonce':NONCE,'status_sha256':'b'*64})

    def test_foreign_nonce_reused_birth_and_unreleased_owner_reject(self):
        for mutate in (lambda v:v['owner_lease.json'].update(nonce='d'*32),
                       lambda v:v[ACC+'.launch.json']['native_wsl_client'].update(creation_filetime=9),
                       lambda v:v['lock_released.json'].update(state='FAILED'),
                       lambda v:v['progress.json'].update(finished=0),
                       lambda v:v['result.json'].update(finalizer_errors=['SYNTHETIC_UNCLOSED_FINALIZER'])):
            config,values=fixture();values=copy.deepcopy(values);mutate(values)
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):V.prior_contract(config,ACC,values)

    def test_panel_or_command_scope_expansion_and_source_replacement_reject(self):
        for mutate in (lambda v:v['result.json'].update(scope='FULL196'),
                       lambda v:v[ACC+'.launch.json']['argv'].append('--EXTRA'),
                       lambda v:v['result.json'].update(linux_script_sha256='f'*64)):
            config,values=fixture();mutate(values)
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):V.prior_contract(config,ACC,values)

    def test_closed_failed_terminal_is_closure_only_never_a_success(self):
        argv,value=terminal();V.closed_terminal(value,argv,NONCE,'c'*64,2)
        self.assertEqual(value['state'],'FAILED')
        with self.assertRaises(ValueError):V.closed_terminal(value,argv,NONCE,'c'*64,0)

    def test_terminal_wrong_invocation_survivor_or_execution_claim_reject(self):
        for key,bad in [('owner_nonce','d'*32),('source_sha256','d'*64),('native_launch_count',1),
                        ('owned_closure_proven',False),('remaining_direct_children',[123])]:
            argv,value=terminal();value[key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):V.closed_terminal(value,argv,NONCE,'c'*64,2)

    def test_observed_prior_unclosed_scope_cannot_clear_stop(self):
        for changes in ({'observed_prior_closure_unproven':True},
                        {'prior_scope_check_entered':True,'prior_scope_check_complete':False}):
            argv,value=terminal();value.update(changes)
            with self.subTest(changes=changes),self.assertRaises(ValueError):V.closed_terminal(value,argv,NONCE,'c'*64,2)

    def test_pass_requires_completed_scope_while_closed_preflight_failure_stays_failed(self):
        argv,value=terminal('PASS_RAW_RECOVERY_ZIP_BYTES_ONLY');value.update(prior_scope_check_entered=False,prior_scope_check_complete=False)
        with self.assertRaisesRegex(ValueError,'Successful archive'):V.closed_terminal(value,argv,NONCE,'c'*64,0)
        value['state']='FAILED';V.closed_terminal(value,argv,NONCE,'c'*64,2)

    def test_terminal_bootstrap_argv_and_interpreter_exact(self):
        for key,bad in [('argv',['OTHER']),('executable','/OTHER/python'),('boot_id','OTHER')]:
            argv,value=terminal();value['bootstrap'][key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):V.closed_terminal(value,argv,NONCE,'c'*64,2)

    def test_actual_own_c_metadata_capture_and_mutation_refusal(self):
        with tempfile.TemporaryDirectory(dir=V.WORK) as tmp:
            path=Path(tmp)/'fixture.json';path.write_bytes(b'{"synthetic":true}\n')
            raw,pin=V.captured_file(path);self.assertEqual(raw,path.read_bytes());self.assertEqual(pin['sha256'],V.sha(path))
            actual=V.os.fstat
            def changed(fd):
                info=actual(fd);values=list(info);values[6]+=1;return V.os.stat_result(values)
            with patch.object(V.os,'fstat',side_effect=changed),self.assertRaises(ValueError):V.captured_file(path)


if __name__=='__main__':unittest.main()
