"""Pure profile/failure/retained-owner source contracts; no WSL or config writes."""
from pathlib import Path
from unittest.mock import patch
import ast, contextlib, copy, hashlib, io, json, unittest
import stage5_wsl_host_profile_owner as M

HERE=Path(__file__).resolve().parent


class Tests(unittest.TestCase):
    def test_exact_two_line_transform_preserves_mixed_newlines_comments_and_all_other_bytes(self):
        raw=(HERE/M.PREIMAGE_NAME).read_bytes();after=M.transform_profile(raw)
        self.assertEqual(after,raw.replace(b'memory=4GB\n',b'memory=3GB\n').replace(b'autoMemoryReclaim=gradual\n',b'autoMemoryReclaim=dropCache\n'))
        self.assertEqual(len(after),681);self.assertEqual(after.count(b'\r\n'),raw.count(b'\r\n'))
        self.assertEqual(sum(a!=b for a,b in zip(raw.splitlines(),after.splitlines())),2)
        self.assertIn(b'# Release unused page cache gradually when compute is idle.',after)
        for bad in (after,raw+b'\n',raw.replace(b'processors=4',b'processors=2')):
            with self.assertRaises(ValueError):M.transform_profile(bad)

    def test_wrong_sections_or_target_reject_even_if_preimage_digest_is_rebased(self):
        raw=(HERE/M.PREIMAGE_NAME).read_bytes()
        for bad in (raw.replace(b'[wsl2]',b'[xxxx]'),raw.replace(b'[experimental]',b'[experimentaX]'),
                    raw.replace(b'memory=4GB',b'memory=4gb')):
            with self.subTest(raw=bad[-20:]),patch.object(M,'PREIMAGE_SHA',M.digest(bad)),self.assertRaises(ValueError):
                M.transform_profile(bad)

    def test_default_noop_does_not_load_owner_or_read_profile(self):
        with (patch('sys.argv',['stage5_wsl_host_profile_owner.py']),
              patch.object(M,'windows_main',side_effect=AssertionError('Owner forbidden')),
              patch.object(M,'load_base',side_effect=AssertionError('Source reads forbidden')),
              contextlib.redirect_stdout(io.StringIO()) as output):
            self.assertEqual(M.main(),0)
        self.assertEqual(json.loads(output.getvalue()),{'state':'PREPARED_NOT_RUN','WSL_launches':0,'profile_changes':0,'shutdowns':0})

    def failed(self):
        return {n:json.loads((HERE/M.FAILED_DIR/n).read_bytes()) for n in M.FAILED_PINS if n.endswith('.json')}

    def test_exact_failed_scope_is_accepted_only_as_failed(self):
        values=self.failed();self.assertEqual(M.failed_gate(values)['state'],'FAILED')
        for n,h in M.FAILED_PINS.items():self.assertEqual(hashlib.sha256((HERE/M.FAILED_DIR/n).read_bytes()).hexdigest(),h)
        self.assertFalse((HERE/'stage5_runtime_actual_postiq_07.json').exists())

    def test_failed_scope_mismatch_unknown_closure_or_false_success_rejects(self):
        changes=[('result.json','state','PASS_OTHER'),('result.json','owned_closure_proven',False),
                 ('result.json','unknown_closure_stop_preserved',True),('result.json','failed_scope_closed',False),
                 ('linux_terminal.json','remaining_direct_children',[99]),('linux_terminal.json','owned_command_count',True),
                 ('lock_released.json','released',False),('commands/runtime_discovery.closure.json','survivors',[99]),
                 ('commands/runtime_discovery.closure.json','root_exit_code',-15.0),
                 ('commands/runtime_discovery.closure.json','group_empty',False)]
        for name,key,bad in changes:
            values=self.failed();values[name][key]=bad
            with self.subTest(name=name,key=key),self.assertRaises(ValueError):M.failed_gate(values)
        values=self.failed();values['wsl_exit.json']['terminal']['creation_filetime']+=1
        with self.assertRaises(ValueError):M.failed_gate(values)

    def test_reviewed_framework_hash_and_no_linux_or_cleanup_adoption(self):
        self.assertEqual(hashlib.sha256((HERE/M.BASE_NAME).read_bytes()).hexdigest(),M.BASE_SHA)
        tree=ast.parse(Path(M.__file__).read_bytes())
        names={n.name for n in tree.body if isinstance(n,ast.FunctionDef)}
        self.assertNotIn('linux_main',names);self.assertNotIn('exact_failed_sentinel_cleanup',names)
        text=Path(M.__file__).read_text()
        self.assertNotIn("fixed_argv('set_default_user')",text)
        self.assertEqual(M.RESERVE,1610612736)

    def test_retained_client_functions_match_reviewed_owner_except_scope_reason(self):
        old=ast.parse((HERE/M.BASE_NAME).read_bytes());new=ast.parse(Path(M.__file__).read_bytes())
        def nested(tree,name):
            owner=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='windows_main')
            return copy.deepcopy(next(x for x in owner.body if isinstance(x,ast.FunctionDef) and x.name==name))
        class NormalizeReason(ast.NodeTransformer):
            def visit_Constant(self,node):
                if isinstance(node.value,str) and node.value in (
                    'WSL config maintenance launch intent; current retained Linux/Windows clients require closure',
                    'Windows profile maintenance retained-client launch intent; closure required'):
                    node.value='OWNED_CLIENT_LAUNCH_INTENT'
                return node
        for name in ['finish_client','run']:
            with self.subTest(name=name):
                self.assertEqual(ast.dump(NormalizeReason().visit(nested(old,name)),include_attributes=False),
                                 ast.dump(NormalizeReason().visit(nested(new,name)),include_attributes=False))


if __name__=='__main__':unittest.main()
