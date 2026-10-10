import importlib.util, json, sys
from datetime import datetime, timezone
from pathlib import Path
base = Path(__file__).resolve().parent.parent
src = base / 'audit_completed_locus.py'
spec = importlib.util.spec_from_file_location('locus_audit', src)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
root = Path(__file__).resolve().parent
cases = ['missing_semicolon.nwk', 'nonfinite_branch.nwk', 'negative_branch.nwk', 'unterminated_quote.nwk']
results = {}
for name in cases:
    try:
        module.parse_newick(root / name)
        results[name] = 'FAIL_ACCEPTED_INVALID_TREE'
    except ValueError as e:
        results[name] = 'PASS_REJECTED: ' + str(e)
        continue
    raise SystemExit(1)
valid = root / 'valid.nwk'
valid.write_text('(A:0.1,B:0.2);\n', encoding='utf-8')
parsed = module.parse_newick(valid)
if sorted(parsed['leaves']) != ['A', 'B']:
    raise SystemExit('valid fixture failed')
results['valid.nwk'] = 'PASS'
out = {'state':'PASS','checked_utc':datetime.now(timezone.utc).isoformat(),'cases':results}
(root / 'fixture_receipt.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8')
print(json.dumps(out, indent=2))
