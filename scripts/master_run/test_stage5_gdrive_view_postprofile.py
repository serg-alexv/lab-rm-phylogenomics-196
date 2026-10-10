"""C-only pin refresh, receipt-join and pure namespace contracts; no WSL."""
from pathlib import Path
from unittest.mock import patch
import ast, contextlib, copy, hashlib, io, json, unittest
import stage5_gdrive_view_postprofile as G

ORIGINAL_SHA='a69a755dd044d72cfdfc49d85c150a43057ad69e9b4d70253792222410e41125'
BOOT='f0ffcebc-4901-479d-9559-89d45e9cfa38'
REVIEW='stage5_toolchain07_postprofile_independent_review.json'
CHANGES=[('stage5_setup_toolchain_actual_postiq_06', 'stage5_setup_toolchain_actual_postiq_07'), ('stage5_toolchain06_postrepair_independent_review.json', 'stage5_toolchain07_postprofile_independent_review.json'), ('e5b9f9517a333bf72b0d21f16eefa18496d5cfc8a670cbf10b9b6155971600d4', '24b12359a603b0cc942681427c241bca8dce402ababeacbe52672da129847239'), ('44c0129ab2fb3c669b1741d1fba147b15139c3c6d9f0a314552f41fb6ca0e46f', '08770432cb1a314e7cf48affd6c4c4e3c0e995ba41d083a1c12fdfe489830516'), ('09b09eab302c843cc1e15a8e4f51fd028159287f135bc2b9bb7ee6085fe4ea19', 'be4c1d96c5b4d73cfdfc334e3b72e6dbb7f641451ded01b7d2c28910eb6d7af7'), ('bea462ec47f79d402b246a6f18a84ce3175b8854efcc204581c031df3e2a018b', '795ad1d9bd694be53f574f0044222723ec0769acc32c02476cc88e86c0b45ceb'), ('a16285fdf373561aeefa52b3443f71fa892d40dd5685a1103c5e17a9ab14b5cd', 'c9dffa018920feee0c90b59cd1d6e4dfe7dcfc2fbb3daa979a66293473220dfb'), ('09762391f9552f38ce44e59dc31763717d44e6bd9bf7b64f967a728e6e4407bb', '16c63985e3cf1e2d64a8e526da8699eda0e0c5ae9c1009aace0e39dddd8e965f')]


class PostrepairContracts(unittest.TestCase):
    def test_only_exact_pin_and_path_replacements(self):
        original=(G.WORK/'stage5_gdrive_view_postrepair.py').read_bytes()
        actual=Path(G.__file__).read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),ORIGINAL_SHA)
        for before,after in CHANGES:
            self.assertNotIn(after.encode(),original)
            actual=actual.replace(after.encode(),before.encode())
        self.assertEqual(actual,original)

    def test_all_function_asts_except_review_lookup_identical(self):
        original=ast.parse((G.WORK/'stage5_gdrive_view_postrepair.py').read_bytes())
        actual=ast.parse(Path(G.__file__).read_bytes())
        class NormalizeReview(ast.NodeTransformer):
            def visit_Constant(self,node):
                if node.value==REVIEW:node.value='stage5_toolchain06_postrepair_independent_review.json'
                return node
        actual=NormalizeReview().visit(actual)
        def functions(tree):
            return {n.name:ast.dump(n,include_attributes=False) for n in tree.body
                    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        self.assertEqual(functions(actual),functions(original))

    def test_default_noop_even_with_mount_flag(self):
        with (patch('sys.argv',['stage5_gdrive_view_postprofile.py','--mount']),
              patch.object(G,'windows_main',side_effect=AssertionError('Actual owner forbidden')),
              contextlib.redirect_stdout(io.StringIO()) as output):
            self.assertEqual(G.main(),0)
        self.assertEqual(json.loads(output.getvalue()),{'state':'PREPARED_NOT_RUN','WSL_launches':0,'mounts':0})

    def test_exact_closed_toolchain07_and_reject_prior_boot_route(self):
        path=G.WORK/G.FRESH_TOOLCHAIN_DIR/'toolchain_proof.json'
        pin=G.FRESH_PINS[G.FRESH_TOOLCHAIN_DIR+'/toolchain_proof.json']
        self.assertEqual(G.fresh_toolchain_gate(G.WORK,path,pin),BOOT)
        for wrong_path,wrong_pin in [(path,'0'*64),(path,None),
                (G.WORK/'stage5_setup_toolchain_actual_postiq_06/toolchain_proof.json',pin)]:
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
