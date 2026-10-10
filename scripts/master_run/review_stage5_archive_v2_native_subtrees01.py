"""C-only AST check of retained native archive main subtrees."""
from pathlib import Path
import ast, hashlib, json
W=Path(__file__).resolve().parent
PINS={'stage5_closed_genome_archive_windows.py':'249b9de14219d8c0a5f1e7e88e48f6c80694bd04699c7c3e506b50a0980fab45',
      'stage5_closed_genome_archive_windows_checked_unlock_v2.py':'f0d3456dbfd02fa46e127f9dc93f8da7083cd777380561031de8c565cde738e4'}
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    trees=[]
    for name,pin in PINS.items():
        path=W/name
        if digest(path)!=pin:raise ValueError('Frozen source differs')
        trees.append(next(n for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='main'))
    def dumps(nodes):return [ast.dump(n,include_attributes=False) for n in nodes]
    checks={}
    selectors={
      'fixed_native_argv':lambda t:[n for n in ast.walk(t) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='argv' for x in n.targets) and isinstance(n.value,ast.List)],
      'Popen_and_retained_exit_and_terminal_calls':lambda t:[n for n in ast.walk(t) if isinstance(n,ast.Call) and ((isinstance(n.func,ast.Attribute) and n.func.attr in ('Popen','persist_wsl_exit')) or isinstance(n.func,ast.Name) and n.func.id=='closed_terminal')],
      'Windows_resource_predicate':lambda t:[n for n in ast.walk(t) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and any(isinstance(x,ast.Constant) and x.value=='Actual archive Windows resource admission failed' for x in n.args)],
      'native_client_closure_finalizer':lambda t:[n for n in ast.walk(t) if isinstance(n,ast.If) and ast.dump(n.test)==ast.dump(ast.parse('child is not None and not closure',mode='eval').body)],
      'power_restoration_finalizer':lambda t:[n for n in ast.walk(t) if isinstance(n,ast.If) and ast.dump(n.test)==ast.dump(ast.parse('idle_previous is not None',mode='eval').body)],
      'inactive_lease_finalizer':lambda t:[n for n in ast.walk(t) if isinstance(n,ast.Try) and any(isinstance(x,ast.Expr) and isinstance(x.value,ast.Call) and isinstance(x.value.func,ast.Name) and x.value.func.id=='lease' and x.value.args and isinstance(x.value.args[0],ast.Constant) and x.value.args[0].value is False for x in n.body)]}
    for label,select in selectors.items():
        old,new=map(select,trees)
        if not old or dumps(old)!=dumps(new):raise ValueError('Native subtree changed: '+label)
        checks[label]={'original_and_v2_AST_identical':True,'subtrees':len(old)}
    out=W/'stage5_archive_checked_unlock_v2_native_subtrees_independent_review01.json'
    value={'schema':'STAGE05_ARCHIVE_MAIN_NATIVE_SUBTREE_INDEPENDENT_V1','state':'PASS_RETAINED_MAIN_NATIVE_ARGV_CALLS_RESOURCE_AND_CLOSURE_SUBTREES_IDENTICAL','source_pins':PINS,'reviewer_source_sha256':digest(Path(__file__)),'checks':checks,'actual_operations':'NOT_RUN_SOURCE_ONLY'}
    with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':value['state'],'report':str(out),'sha256':digest(out),'checker_sha256':digest(Path(__file__))}))
if __name__=='__main__':main()
