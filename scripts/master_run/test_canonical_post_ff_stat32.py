"""Pure C control/negative contracts; no Git, G, lock or native API calls."""
from pathlib import Path
import copy
import json
import unittest
import repair_canonical_post_ff_stat32 as S
R=S.helper();W=Path(__file__).resolve().parent


def controls():
    p=json.loads((W/'canonical_post_ff_stat32_plan.json').read_bytes())
    r=json.loads((W/'canonical_git_metadata_repair_20261009T230357Z_7bd50c6d/receipt.json').read_bytes())
    return p,r


class Exact32(unittest.TestCase):
    def test_actual_closed_source_control_join(self):
        p,r=controls();self.assertEqual(R.sha(W/'canonical_post_ff_stat32_plan.json'),S.PLAN_SHA)
        a,b=S.validate_controls(p,r,R);self.assertEqual((len(a),len(b)),(32,6))

    def test_unknown_or_duplicate_path_rejected(self):
        for mutation in ('duplicate','unknown'):
            p,r=controls();p['refresh_paths'][0]['path']=p['refresh_paths'][1]['path'] if mutation=='duplicate' else 'unexpected.txt'
            with self.subTest(mutation=mutation),self.assertRaises((ValueError,KeyError)):S.validate_controls(p,r,R)

    def test_native_closure_or_ff_missing_rejected(self):
        for key in ('all_created_git_scopes_closed','original_lock_explicitly_released','fast_forward_command_exit0'):
            p,r=controls();r[key]=False
            with self.subTest(key=key),self.assertRaises(ValueError):S.validate_controls(p,r,R)

    def test_actual_proof_pin_tamper_rejected(self):
        p,r=controls();p['refresh_paths'][0]['sha256']='a'*64
        with self.assertRaises(ValueError):S.validate_controls(p,r,R)

    def test_staged_and_duplicate_status_rejected(self):
        for raw in (b'M  x\0',b' M x\0 M x\0'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):S.status_scope(raw,R)


if __name__=='__main__':unittest.main()
