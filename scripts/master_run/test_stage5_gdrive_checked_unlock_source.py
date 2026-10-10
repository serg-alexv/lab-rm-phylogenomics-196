"""Pure source transforms and fake unlock/publication lifecycle tests only."""
from pathlib import Path
import ast,contextlib,io,json,sys,tempfile,unittest
from unittest.mock import patch
import prepare_stage5_gdrive_checked_unlock_source as P

class CheckedG(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe=P.module('_test_frozen_G08_recipe',P.WORK/P.RECIPE)
        cls.baseline=(P.WORK/P.BASE).read_bytes();cls.profile=(P.WORK/P.PROFILE).read_bytes()
        cls.pins={cls.recipe.NEW_DIR+'/'+n:str(i+1)*64 for i,n in enumerate(cls.recipe.LEAVES)}
        cls.pins[cls.recipe.NEW_REVIEW]='6'*64
        cls.raw=cls.recipe.render(cls.baseline,cls.pins)
        cls.candidate=P.render(cls.raw,cls.baseline,cls.profile,cls.recipe)

    def namespace(self):
        ns={'__name__':'_fake_source_only','__file__':str(P.WORK/P.OUTPUT)}
        exec(compile(self.candidate,P.OUTPUT,'exec'),ns);return ns

    def fake(self,fail=None,closed=True):
        self.tmp=tempfile.TemporaryDirectory(dir=P.WORK);self.addCleanup(self.tmp.cleanup)
        out=Path(self.tmp.name);stop=out/'STOP.json';stop.write_text(json.dumps({'owner_nonce':'fixture'}))
        self.events=[];outer=self
        class Lock:
            released=False
            def __exit__(self,*args):
                outer.events.append('unlock');assert stop.exists()
                if fail=='unlock':raise OSError('fake unlock failure')
                self.released=True
        class A:
            @staticmethod
            def utc():return '2026-10-10T00:00:00+00:00'
            @staticmethod
            def atomic(path,value):
                outer.events.append(path.name)
                if path.name=='lock_released.json':assert stop.exists() and lock.released
                if path.name==fail:raise OSError('fake persistence failure')
                path.write_text(json.dumps(value))
            @staticmethod
            def read_json(path):return json.loads(path.read_text())
        lock=Lock();record={'state':P.PENDING}
        self.namespace()['finish_after_unlock'](A,lock,out,record,stop,P.digest(stop.read_bytes()),'fixture',closed)
        return out,stop,record,lock

    def test_default_NOOP_never_reads_source_or_receipts(self):
        with patch.object(sys,'argv',['preparer']),patch.object(Path,'read_bytes',side_effect=AssertionError('no reads')),contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(P.main(),0)
        self.assertFalse(json.loads(out.getvalue())['source_written'])

    def test_exact_six_pin_input_and_unrelated_AST_preserved(self):
        before=P.functions(self.raw);after=P.functions(self.candidate)
        self.assertEqual(set(after),set(before)|{'finish_after_unlock'})
        self.assertTrue(all(after[k]==v for k,v in before.items() if k!='windows_main'))
        self.assertEqual(P.fresh_pins(self.candidate),self.pins)
        with self.assertRaisesRegex(ValueError,'exactly the frozen six-pin'):
            P.render(self.raw+b'\n# unrelated change\n',self.baseline,self.profile,self.recipe)

    def test_old_baseline_profile_or_pin_gap_rejected(self):
        for raw,base,profile in [(self.raw,self.baseline+b'\n',self.profile),(self.raw,self.baseline,self.profile+b'\n')]:
            with self.assertRaises(ValueError):P.render(raw,base,profile,self.recipe)
        pins=dict(self.pins);pins.pop(self.recipe.NEW_REVIEW)
        with self.assertRaises(ValueError):self.recipe.render(self.baseline,pins)

    def test_handle_close_precedes_finalizer_and_success_waits_unlock(self):
        tree=ast.parse(self.candidate);f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='windows_main')
        calls={ast.unparse(n.func):n.lineno for n in ast.walk(f) if isinstance(n,ast.Call)}
        self.assertLess(calls['child._handle.Close'],calls['finish_after_unlock'])
        source=ast.get_source_segment(self.candidate.decode(),f)
        self.assertNotIn('stop.unlink()',source);self.assertNotIn("record['state']='"+P.PASS+"'",source)
        self.assertIn("record['state']='"+P.PENDING+"'",source)
        self.assertIn("record.get('original_unlock_receipt_proven') is True",source)

    def test_success_unlock_receipt_precedes_stop_clear(self):
        out,stop,record,lock=self.fake()
        self.assertEqual(record['state'],P.PASS);self.assertFalse(stop.exists())
        self.assertEqual(self.events,['unlock','lock_released.json','result.json'])
        self.assertTrue(record['owned_stop_cleared_after_unlock']);self.assertTrue(record['original_unlock_receipt_proven'])

    def test_unlock_and_receipt_failure_preserve_stop(self):
        for name in ('unlock','lock_released.json'):
            with self.subTest(name=name):
                out,stop,record,lock=self.fake(name)
                self.assertEqual(record['state'],'FAILED');self.assertTrue(stop.exists())

    def test_unclosed_scope_preserves_stop_and_no_pass(self):
        out,stop,record,lock=self.fake(closed=False)
        self.assertEqual(record['state'],'FAILED');self.assertTrue(stop.exists())
        self.assertTrue(record['original_unlock_receipt_proven']);self.assertFalse(record['owned_closure_proven'])

    def test_final_publication_failure_keeps_proved_facts_and_returns_failed(self):
        out,stop,record,lock=self.fake('result.json')
        self.assertEqual(record['state'],'FAILED');self.assertFalse(stop.exists())
        failure=json.loads((out/'publication_failure.json').read_text())
        self.assertEqual(failure['schema'],'STAGE05_G_DRIVE_FINAL_PUBLICATION_FAILURE_V1')
        self.assertTrue(failure['owned_closure_proven']);self.assertTrue(failure['original_unlock_receipt_proven'])
        self.assertFalse(failure['closure_facts_reclassified_as_unknown'])
        self.assertTrue(record['master_publication_reconciliation_required'])

    def test_generated_default_NOOP(self):
        ns=self.namespace()
        with patch.object(sys,'argv',['generated']),contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(ns['main'](),0)
        self.assertEqual(json.loads(out.getvalue())['WSL_launches'],0)

if __name__=='__main__':unittest.main()
