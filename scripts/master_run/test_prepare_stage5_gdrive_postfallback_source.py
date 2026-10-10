"""Pure source rendering/guard tests; future hashes below are synthetic only."""
from pathlib import Path
from unittest.mock import patch
import ast, contextlib, io, json, unittest
import prepare_stage5_gdrive_postfallback_source as M

class Tests(unittest.TestCase):
    def pins(self):return {M.NEW_DIR+'/'+leaf:format(i+1,'064x') for i,leaf in enumerate(M.LEAVES)}|{M.NEW_REVIEW:'f'*64}
    def test_only_directory_review_and_six_pins_change(self):
        raw=(M.WORK/M.BASE).read_bytes();after=M.render(raw,self.pins())
        self.assertEqual(M.digest(raw),M.BASE_SHA);self.assertNotIn(M.OLD_DIR.encode(),after)
        self.assertNotIn(M.OLD_REVIEW.encode(),after)
        old=ast.parse(raw);new=ast.parse(after)
        def assignments(tree):return {n.targets[0].id:ast.literal_eval(n.value) for n in tree.body
            if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)
            and n.targets[0].id in ('FRESH_PINS','FRESH_TOOLCHAIN_DIR')}
        actual=assignments(new);self.assertEqual(actual['FRESH_PINS'],self.pins());self.assertEqual(actual['FRESH_TOOLCHAIN_DIR'],M.NEW_DIR)
        self.assertEqual(len(assignments(old)['FRESH_PINS']),6)
    def test_bad_source_pin_incomplete_extra_and_malformed_future_pins_reject(self):
        raw=(M.WORK/M.BASE).read_bytes()
        with self.assertRaises(ValueError):M.render(raw+b'\n',self.pins())
        for action in ('missing','extra','none','uppercase'):
            pins=self.pins()
            if action=='missing':pins.pop(M.NEW_REVIEW)
            elif action=='extra':pins['unknown']='a'*64
            elif action=='none':pins[M.NEW_REVIEW]=None
            else:pins[M.NEW_REVIEW]='F'*64
            with self.subTest(action=action),self.assertRaises(ValueError):M.render(raw,pins)
    def test_function_asts_identical_except_exact_review_lookup(self):
        raw=(M.WORK/M.BASE).read_bytes();new=ast.parse(M.render(raw,self.pins()))
        class Normalize(ast.NodeTransformer):
            def visit_Constant(self,node):
                if node.value==M.NEW_REVIEW:node.value=M.OLD_REVIEW
                return node
        functions=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
        self.assertEqual(functions(Normalize().visit(new)),functions(ast.parse(raw)))
    def test_default_noop_has_no_reads_or_writes(self):
        with (patch('sys.argv',['prepare']),patch.object(M,'read_plain',side_effect=AssertionError('No reads')),
             contextlib.redirect_stdout(io.StringIO()) as output):
            self.assertEqual(M.main(),0)
        self.assertEqual(json.loads(output.getvalue()),{'state':'PREPARED_NOT_RUN','source_written':False,'future_pins':'NOT_GUESSED','WSL_launches':0})

if __name__=='__main__':unittest.main()
