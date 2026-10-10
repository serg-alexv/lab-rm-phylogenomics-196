"""C-only pin refresh, receipt-join and pure namespace contracts; no WSL."""
from pathlib import Path
from unittest.mock import patch
import ast, contextlib, copy, hashlib, io, json, unittest
import stage5_gdrive_view_postrepair as G

ORIGINAL_SHA='42db8fe44fb2e6c4b8300c2415dc45a6aec20b115449bf76ad002eda34354fb8'
BOOT='f9be2168-b511-4a09-8f4d-bdb88934c414'
REVIEW='stage5_toolchain06_postrepair_independent_review.json'
CHANGES=[
 ('stage5_setup_toolchain_actual_postiq_05','stage5_setup_toolchain_actual_postiq_06'),
 ('stage5_toolchain05_postboot_independent_review.json',REVIEW),
 ('43ad814d2cb055fbcc0578862d3e75f3d236452025a0512250e5914a7f7aef43','e5b9f9517a333bf72b0d21f16eefa18496d5cfc8a670cbf10b9b6155971600d4'),
 ('daa80ec0b44bcca53388cb77651eecdecf40da7c0877fdce5fc2f540cd62e289','44c0129ab2fb3c669b1741d1fba147b15139c3c6d9f0a314552f41fb6ca0e46f'),
 ('106e1bc310f11d34d78f0d7bdc2b311a2b457e5c68c0e32aad3f8fc0a718446c','09b09eab302c843cc1e15a8e4f51fd028159287f135bc2b9bb7ee6085fe4ea19'),
 ('f21021be37d99278eda829deb6830cc145425b8d3a031f34fcef7db23d676b04','bea462ec47f79d402b246a6f18a84ce3175b8854efcc204581c031df3e2a018b'),
 ('531943141ccfee0ea36ef72c4e94d3e19b13ed723ebf086f52883bb11089e46f','a16285fdf373561aeefa52b3443f71fa892d40dd5685a1103c5e17a9ab14b5cd'),
 ('2c542838c2a929bd59b86d1674e90bae52406d6583a9121a554da9909cd25516','09762391f9552f38ce44e59dc31763717d44e6bd9bf7b64f967a728e6e4407bb')]


class PostrepairContracts(unittest.TestCase):
    def test_only_exact_pin_and_path_replacements(self):
        original=(G.WORK/'stage5_gdrive_view_session.py').read_bytes()
        actual=Path(G.__file__).read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),ORIGINAL_SHA)
        for before,after in CHANGES:
            self.assertNotIn(after.encode(),original)
            actual=actual.replace(after.encode(),before.encode())
        self.assertEqual(actual,original)

    def test_all_function_asts_except_review_lookup_identical(self):
        original=ast.parse((G.WORK/'stage5_gdrive_view_session.py').read_bytes())
        actual=ast.parse(Path(G.__file__).read_bytes())
        class NormalizeReview(ast.NodeTransformer):
            def visit_Constant(self,node):
                if node.value==REVIEW:node.value='stage5_toolchain05_postboot_independent_review.json'
                return node
        actual=NormalizeReview().visit(actual)
        def functions(tree):
            return {n.name:ast.dump(n,include_attributes=False) for n in tree.body
                    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        self.assertEqual(functions(actual),functions(original))

    def test_default_noop_even_with_mount_flag(self):
        with (patch('sys.argv',['stage5_gdrive_view_postrepair.py','--mount']),
              patch.object(G,'windows_main',side_effect=AssertionError('Actual owner forbidden')),
              contextlib.redirect_stdout(io.StringIO()) as output):
            self.assertEqual(G.main(),0)
        self.assertEqual(json.loads(output.getvalue()),{'state':'PREPARED_NOT_RUN','WSL_launches':0,'mounts':0})

    def test_exact_closed_toolchain06_and_reject_prior_boot_route(self):
        path=G.WORK/G.FRESH_TOOLCHAIN_DIR/'toolchain_proof.json'
        pin=G.FRESH_PINS[G.FRESH_TOOLCHAIN_DIR+'/toolchain_proof.json']
        self.assertEqual(G.fresh_toolchain_gate(G.WORK,path,pin),BOOT)
        for wrong_path,wrong_pin in [(path,'0'*64),(path,None),
                (G.WORK/'stage5_setup_toolchain_actual_postiq_05/toolchain_proof.json',pin)]:
            with self.subTest(path=wrong_path,pin=wrong_pin),self.assertRaises(ValueError):
                G.fresh_toolchain_gate(G.WORK,wrong_path,wrong_pin)

    def test_self_consistent_hashes_do_not_override_receipt_joins(self):
        prefix=G.FRESH_TOOLCHAIN_DIR+'/'
        mutations=[(prefix+'linux_terminal.json',lambda x:x.update(owner_nonce='changed')),
                   (prefix+'lock_released.json',lambda x:x.update(released=False)),
                   (REVIEW,lambda x:x['detail'].update(candidate_sha256='0'*64)),
                   (prefix+'wsl_exit.json',lambda x:x['terminal'].update(exit_code=1))]
        tiny,sha=G.tiny,G.sha
        for name,mutate in mutations:
            value=json.loads(tiny(G.WORK/name));mutate(value);raw=json.dumps(value).encode()
            pins=copy.deepcopy(G.FRESH_PINS);pins[name]=hashlib.sha256(raw).hexdigest()
            selected=G.WORK/name
            with (self.subTest(name=name),patch.object(G,'FRESH_PINS',pins),
                  patch.object(G,'tiny',side_effect=lambda p,*a:raw if Path(p)==selected else tiny(p,*a)),
                  patch.object(G,'sha',side_effect=lambda p:pins[name] if Path(p)==selected else sha(p)),
                  self.assertRaises(ValueError)):
                G.fresh_toolchain_gate(G.WORK,G.WORK/G.FRESH_TOOLCHAIN_DIR/'toolchain_proof.json',
                                       pins[prefix+'toolchain_proof.json'])

    def test_session_parent_guards_retained(self):
        good={'self':'mnt:[200]','parent':'mnt:[200]','pid1':'mnt:[100]',
          'parent_pid':7,'parent_executable':'/init',
          'parent_record':{'pid':7,'ppid':1,'start_ticks':'10','state':'S'},
          'current_record':{'pid':8,'ppid':7,'start_ticks':'20','state':'R'}}
        self.assertEqual(G.session_namespace_gate(good)['parent_pid'],7)
        for change in ['namespace','parent_executable','parent_birth']:
            value=copy.deepcopy(good)
            if change=='namespace':value['parent']='mnt:[201]'
            if change=='parent_executable':value['parent_executable']='/bin/bash'
            if change=='parent_birth':value['parent_record']['start_ticks']='11'
            with self.subTest(change=change),self.assertRaises(ValueError):
                G.session_namespace_gate(value,good)


if __name__=='__main__':unittest.main()
