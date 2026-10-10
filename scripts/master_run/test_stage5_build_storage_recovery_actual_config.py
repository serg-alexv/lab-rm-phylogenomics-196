"""Pure storage-only builder adaptation checks; no actual gates/lock/native calls."""
from pathlib import Path
from unittest.mock import patch
import ast, copy, hashlib, json, tempfile, unittest
import stage5_build_storage_recovery_actual_config as B
import stage5_build_backing_actual_config as O
import test_stage5_build_backing_actual_config as T


def functions(path):
    return {node.name:ast.dump(node,include_attributes=False)
            for node in ast.parse(path.read_bytes()).body if isinstance(node,ast.FunctionDef)}


class LegacyContracts(T.Contracts):
    def setUp(self):
        self.swap=patch.object(T,'B',B);self.swap.start();self.addCleanup(self.swap.stop)

    def test_only_reviewed_transport_pins_and_wait_changed(self):
        self.assertEqual(B.sha(B.WORK/'stage5_build_backing_actual_config.py'),
                         'e1b7b4782be7cb4faa84cf546884075e860d2d010a1774ba7d61846bfff7905c')
        self.assertEqual(B.PINS,O.PINS)
        old=functions(B.WORK/'stage5_build_backing_actual_config.py')
        new=functions(B.WORK/'stage5_build_storage_recovery_actual_config.py')
        self.assertEqual(old.keys(),new.keys())
        self.assertEqual([name for name in old if old[name]!=new[name]],['checked_gate','main'])
        self.assertEqual(set(B.STORAGE_RECOVERY_PINS),{
            'stage5_setup_storage_recovery_windows.py','stage5_setup_storage_recovery_linux.py'})
        for name,pin in B.STORAGE_RECOVERY_PINS.items():self.assertEqual(B.sha(B.WORK/name),pin)


def gate(work,name='storage',new=True):
    directory=work/name;directory.mkdir()
    value,terminal,spec,write=T.gate(directory)
    value['step']=terminal['step']=name
    value['scope']=terminal['scope']='NONSCIENTIFIC_STAGE5_SETUP_ONLY'
    if new:
        value['source_sha256']=B.STORAGE_RECOVERY_PINS['stage5_setup_storage_recovery_windows.py']
        value['linux_source_sha256']=terminal['source_sha256']=B.STORAGE_RECOVERY_PINS['stage5_setup_storage_recovery_linux.py']
    value.update(original_lock_explicitly_released=True,original_unlock_receipt_proven=True,
                 owned_stop_cleared_after_unlock=True,lock_release_receipt_sha256=spec['unlock_sha256'])
    def commit():
        value['linux_terminal_sha256']=write('linux_terminal.json',terminal)
        spec['sha256']=write('result.json',value)
    commit()
    return value,terminal,spec,commit


class StorageContracts(unittest.TestCase):
    def test_new_pair_only_storage_accepts(self):
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp);value,_,spec,_=gate(work)
            with patch.object(B,'WORK',work):self.assertEqual(B.checked_gate('storage',spec)[1],value)

    def test_old_pair_cannot_be_selected_for_storage(self):
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp);_,_,spec,_=gate(work,new=False)
            with patch.object(B,'WORK',work),self.assertRaises(ValueError):B.checked_gate('storage',spec)

    def test_new_pair_rejected_for_each_original_setup_gate(self):
        for name in ('toolchain','runtime','drivefs'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                work=Path(tmp);_,_,spec,_=gate(work,name)
                with patch.object(B,'WORK',work),self.assertRaises(ValueError):B.checked_gate(name,spec)

    def test_original_pair_retained_for_each_original_setup_gate(self):
        for name in ('toolchain','runtime','drivefs'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                work=Path(tmp);value,_,spec,_=gate(work,name,new=False)
                with patch.object(B,'WORK',work):self.assertEqual(B.checked_gate(name,spec)[1],value)

    def test_storage_exact_scope_and_checked_unlock_reject_tamper(self):
        cases=[('scope','OTHER'),('original_lock_explicitly_released',False),
               ('original_unlock_receipt_proven',1),('owned_stop_cleared_after_unlock',False),
               ('lock_release_receipt_sha256','0'*64),('source_sha256','0'*64),
               ('linux_source_sha256','0'*64)]
        for field,bad in cases:
            with self.subTest(field=field),tempfile.TemporaryDirectory() as tmp:
                work=Path(tmp);value,_,spec,commit=gate(work);value[field]=bad;commit()
                with patch.object(B,'WORK',work),self.assertRaises(ValueError):B.checked_gate('storage',spec)

    def test_terminal_scope_or_source_tamper_rejects(self):
        for field,bad in [('scope','OTHER'),('source_sha256',O.PINS['stage5_setup_linux.py'])]:
            with self.subTest(field=field),tempfile.TemporaryDirectory() as tmp:
                work=Path(tmp);_,terminal,spec,commit=gate(work);terminal[field]=bad;commit()
                with patch.object(B,'WORK',work),self.assertRaises(ValueError):B.checked_gate('storage',spec)

    def test_native_admission_lock_config_load_calls_preserved(self):
        def calls(path):
            tree=ast.parse(path.read_bytes());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
            names={'api.resources','A.Win','A.WorkflowLock','S.load_config','explicit_policy','pinned','linux_path'}
            return sorted(ast.dump(n,include_attributes=False) for n in ast.walk(main)
                          if isinstance(n,ast.Call) and ast.unparse(n.func) in names)
        self.assertEqual(calls(B.WORK/'stage5_build_backing_actual_config.py'),
                         calls(B.WORK/'stage5_build_storage_recovery_actual_config.py'))

    def test_both_initial_and_final_pin_checks_cover_originals_and_pair(self):
        tree=ast.parse((B.WORK/'stage5_build_storage_recovery_actual_config.py').read_bytes())
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        calls=[n for n in ast.walk(main) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)
               and n.func.id=='require']
        guards=[n for n in calls if any(isinstance(x,ast.Name) and x.id=='STORAGE_RECOVERY_PINS' for x in ast.walk(n))]
        self.assertEqual(len(guards),2)
        for guard in guards:self.assertTrue(any(isinstance(x,ast.Name) and x.id=='PINS' for x in ast.walk(guard)))


if __name__=='__main__':unittest.main()
