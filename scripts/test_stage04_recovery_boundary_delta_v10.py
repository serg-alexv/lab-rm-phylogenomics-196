"""New narrow drift/cache fixtures; no accepted input or biological job mutation."""
import copy,csv,gzip,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import stage04_controller as C
import stage04_recovery_support_v10 as S
import stage04_recovery_controller_v10 as P
from stage04_model_cache_evidence_v10 import checkpoint_map,completed_records,check_cache_records

class Delta(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='v10_boundary_delta_',dir=S.RUNTIME)
        self.root=Path(self.temp.name);self.accepted=S.OLD/'analyses/primary196/iqtree/host.model.gz'
        self.ids=['p'+str(n).zfill(4) for n in range(1,101)]
        self.old=completed_records(checkpoint_map(self.accepted),self.ids)
    def tearDown(self):
        C.check(self.root.resolve().is_relative_to(S.RUNTIME.resolve()) and self.root.name.startswith('v10_boundary_delta_'),'Synthetic cleanup target containment failed')
        self.temp.cleanup()
    def final(self,records=None,duplicate=False):
        rows={pid:{'best_model_BIC':'LG','best_score_BIC':'31','selected_candidate_logL_df_tree_length':'-10 2 1'} for pid in self.ids}
        rows.update(copy.deepcopy(self.old))
        if records is not None:rows=records
        text='--- # IQ-TREE Checkpoint ver >= 1.6\n'
        for pid,row in rows.items():
            model=row['best_model_BIC'];text+=pid+':\n best_model_BIC: '+model+'\n best_score_BIC: '+row['best_score_BIC']+'\n '+model+': '+row['selected_candidate_logL_df_tree_length']+'\n'
        if duplicate:text+='p0001:\n best_model_BIC: LG\n'
        path=self.root/'SYNTHETIC_ONLY.model.gz'
        with gzip.open(path,'wt',encoding='utf-8') as stream:stream.write(text)
        return path,rows
    def check(self,path):return check_cache_records(self.accepted,path,self.ids,S.CACHE_SHA)
    def test_actual_retained14_decisions_readonly(self):self.assertEqual(len(self.old),14)
    def test_synthetic_exact100_with14_preserved86_new(self):
        path,_=self.final();result=self.check(path);self.assertEqual(len(result['new_decision_ids']),86)
    def test_changed_inherited_candidate_rejected(self):
        _,rows=self.final();pid=next(iter(self.old));rows[pid]['selected_candidate_logL_df_tree_length']='-999 2 1'
        self.assertRaises(ValueError,self.check,self.final(rows)[0])
    def test_changed_inherited_BIC_rejected(self):
        _,rows=self.final();rows[next(iter(self.old))]['best_score_BIC']='999'
        self.assertRaises(ValueError,self.check,self.final(rows)[0])
    def test_incomplete_new_partition_rejected(self):
        _,rows=self.final();rows.pop(next(pid for pid in self.ids if pid not in self.old))
        self.assertRaises(ValueError,self.check,self.final(rows)[0])
    def test_foreign_partition_rejected(self):
        _,rows=self.final();rows['p0101']=copy.deepcopy(rows['p0001']);self.assertRaises(ValueError,self.check,self.final(rows)[0])
    def test_duplicate_decision_rejected(self):self.assertRaises(ValueError,self.check,self.final(duplicate=True)[0])
    def test_nonfinite_candidate_rejected(self):
        _,rows=self.final();rows[next(pid for pid in self.ids if pid not in self.old)]['selected_candidate_logL_df_tree_length']='nan 2 1'
        self.assertRaises(ValueError,self.check,self.final(rows)[0])
    def test_missing_selected_candidate_rejected(self):
        path,_=self.final()
        text=gzip.open(path,'rt').read().replace(' LG: -10 2 1\n','',1)
        with gzip.open(path,'wt') as stream:stream.write(text)
        self.assertRaises(ValueError,self.check,path)
    def bindings(self):
        root=self.root/'DATA';old=root/'OLD';old.mkdir(parents=True)
        source=root/'.work/stage04_phylogeny_v2/analyses/primary196';source.mkdir(parents=True)
        exe=self.root/'TOOLS/iqtree.exe';exe.parent.mkdir();exe.write_bytes(b'SYNTHETIC_EXECUTABLE_NEVER_LAUNCHED')
        dll=exe.parent/'libiomp5md.dll';dll.write_bytes(b'SYNTHETIC_DLL_NEVER_LOADED')
        matrix=source/'concatenated.faa';matrix.write_bytes(b'SYNTHETIC_MATRIX_NEVER_ANALYZED')
        partition=source/'partitions.nex';partition.write_bytes(b'SYNTHETIC_PARTITION_NEVER_ANALYZED')
        label=source/'tip_label_map.tsv';label.write_bytes(b'SYNTHETIC_LABELS_NEVER_RENDERED')
        original={'executable':str(exe),'tool_identity':{'executable_sha256':C.digest(exe),'openmp_dll_sha256':C.digest(dll)},
          'seed':1961008,'source_identity':{'file_sha256':{'data:'+p.relative_to(root).as_posix():C.digest(p) for p in [matrix,partition,label]}}}
        C.atomic(old/'inference_freeze.json',original)
        return root,old,original,matrix,dll
    def scope_drift(self,which):
        root,old,original,matrix,dll=self.bindings()
        with patch.object(S,'ROOT',root),patch.object(S,'OLD',old):
            before=S.scope_binding('primary196');(matrix if which=='matrix' else dll).write_bytes(b'CHANGED_SYNTHETIC_BYTES')
            self.assertRaises(ValueError,S.scope_binding,'primary196')
    def test_changed_matrix_after_precheck_rejected(self):self.scope_drift('matrix')
    def test_changed_DLL_after_precheck_rejected(self):self.scope_drift('dll')
    def test_changed_adopted_validator_rejected(self):
        root=self.root/'DATA';path=root/'scripts/validator.py';path.parent.mkdir(parents=True);path.write_text('synthetic checker')
        expected={'data:scripts/validator.py':C.digest(path)}
        with patch.object(S,'ROOT',root):
            P.verify_artifacts(expected);path.write_text('changed synthetic checker');self.assertRaises(ValueError,P.verify_artifacts,expected)
    def test_changed_copied_seed_field_rejected(self):
        root,old,original,*_=self.bindings()
        with patch.object(S,'OLD',old),patch.object(S,'FREEZE_SHA',C.digest(old/'inference_freeze.json')):
            S.original_freeze_fields({**original,'recovery_protocol':'SYNTHETIC'})
            changed={**original,'seed':999};self.assertRaises(ValueError,S.original_freeze_fields,changed)
    def test_changed_retained_freeze_bytes_rejected(self):
        root,old,original,*_=self.bindings()
        with patch.object(S,'OLD',old),patch.object(S,'FREEZE_SHA',C.digest(old/'inference_freeze.json')):
            C.atomic(old/'inference_freeze.json',{**original,'seed':999});self.assertRaises(ValueError,S.original_freeze_fields,original)

if __name__=='__main__':
    S.RUNTIME.mkdir(parents=True,exist_ok=True)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Delta);result=unittest.TextTestRunner(verbosity=2).run(suite)
    with C.WorkflowLock(S.LOCK) as lock:
        S.held_lock_matches_negative(lock)
        C.atomic(S.REPORT/'boundary_cache_delta_tests.json',{'utc':C.now(),'status':'PASS_NARROW_DRIFT_AND_CACHE_FIXTURES' if result.wasSuccessful() else 'FAIL',
          'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'source_sha256':C.digest(__file__),
          'checked_source_sha256':{name:C.digest(S.ROOT/'scripts'/name) for name in ['stage04_recovery_support_v10.py','stage04_recovery_controller_v10.py',
            'stage04_model_cache_evidence_v10.py','stage04_recovery_validate_v10.py','final_check_stage04_recovery_v10.py']},
          'retained_cache_readonly_sha256':C.digest(S.OLD/'analyses/primary196/iqtree/host.model.gz'),
          'scientific_jobs':0,'limitations':'Final100-record fixture is SYNTHETIC, not a production checkpoint or scientific validation. Actual final cache reuse remains NOT_RUN.'})
    raise SystemExit(0 if result.wasSuccessful() else 1)
