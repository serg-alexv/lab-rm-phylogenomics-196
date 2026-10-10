"""Pure request construction and default-NOOP contracts; no actual gate reads."""
from pathlib import Path
from unittest.mock import patch
import ast,contextlib,copy,io,json,unittest
import prepare_stage5_first_actual_request_v3 as M

HERE=Path(__file__).resolve().parent


class Tests(unittest.TestCase):
    def artifacts(self):
        result={}
        for key,name in M.CANDIDATES.items():
            result[name]=json.dumps({'schema':'STAGE05_PINNED_RUNTIME_V1' if key=='runtime_manifest' else 'STAGE05_EXT4_BIND_STORAGE_PROOF_V1'}).encode()
        for kind,name in M.GATES.items():
            result[name+'/result.json']=b'{"state":"PASS_SYNTHETIC_SOURCE_CONTRACT_ONLY"}'
            result[name+'/lock_released.json']=json.dumps({'state':'EXPLICIT_ORIGINAL_OS_BYTE_UNLOCK' if kind=='unc' else 'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED','released':True}).encode()
        return result

    def template(self):return (HERE/'stage5_actual_config_request.template.json').read_bytes()

    def build(self,artifacts=None):
        artifacts=self.artifacts() if artifacts is None else artifacts
        return M.build_request(self.template(),artifacts.__getitem__)

    def test_only_exact_postrestart_paths_are_requested(self):
        expected={'toolchain':'stage5_setup_toolchain_actual_postiq_07','runtime':'stage5_setup_runtime_actual_postiq_08',
          'interop':'stage5_interop_actual_postiq_05','storage':'stage5_setup_storage_actual_postiq_06',
          'drivefs':'stage5_setup_drivefs_actual_postiq_04','unc':'stage5_unc_bind_actual_postiq_03'}
        self.assertEqual(M.GATES,expected);visited=[];artifacts=self.artifacts()
        def reader(name):visited.append(name);return artifacts[name]
        request=M.build_request(self.template(),reader)
        self.assertEqual(set(visited),set(artifacts))
        for kind,name in expected.items():self.assertEqual(request['gates'][kind]['path'],str(M.EXACT_WORK/name/'result.json'))
        self.assertEqual(request['runtime_manifest']['path'],str(M.EXACT_WORK/'stage5_runtime_actual_postiq_08.json'))
        self.assertEqual(request['storage_proof']['path'],str(M.EXACT_WORK/'stage5_storage_actual_postiq_06.json'))

    def test_finite_capacity_unchanged_and_basis_only_wsl_ceiling_changed(self):
        original=(HERE/'prepare_stage5_first_actual_request.py').read_bytes();self.assertEqual(M.digest(original),M.ORIGINAL_SHA)
        values={}
        for node in ast.walk(ast.parse(original)):
            if isinstance(node,ast.Assign):
                for target in node.targets:
                    if isinstance(target,ast.Subscript) and isinstance(target.slice,ast.Constant) and target.slice.value in ('native_resource_bytes','resource_basis'):
                        values[target.slice.value]=ast.literal_eval(node.value)
        self.assertEqual(M.NATIVE_RESOURCE_BYTES,values['native_resource_bytes']);self.assertEqual(M.RESOURCE_BASIS,values['resource_basis'].replace('Keep the WSL global 4GB memory setting.','Keep the WSL global 3GB memory setting.'))
        self.assertTrue(all(type(value) is int and value>0 for value in M.NATIVE_RESOURCE_BYTES.values()))
        self.assertEqual(M.NATIVE_RESOURCE_BYTES['commit_requirement_bytes'],1610612736+M.NATIVE_RESOURCE_BYTES['incremental_windows_requirement_bytes'])
        self.assertLessEqual(M.NATIVE_RESOURCE_BYTES['sampled_rss_stop_bytes'],M.NATIVE_RESOURCE_BYTES['linux_job_requirement_bytes'])

    def test_deterministic_pins_and_scientific_template_semantics(self):
        original=json.loads(self.template());first=self.build();second=self.build()
        self.assertEqual(json.dumps(first,indent=2),json.dumps(second,indent=2));self.assertEqual(json.loads(self.template()),original)
        self.assertEqual(first['schema'],original['schema']);self.assertEqual(first['purpose'],original['purpose'])
        for kind,name in M.GATES.items():
            self.assertEqual(first['gates'][kind]['sha256'],M.digest(self.artifacts()[name+'/result.json']))
            self.assertEqual(first['gates'][kind]['unlock_sha256'],M.digest(self.artifacts()[name+'/lock_released.json']))

    def test_any_unpassed_gate_or_bad_unlock_prevents_request(self):
        for kind,name in M.GATES.items():
            for broken in ('gate','unlock','released'):
                values=self.artifacts()
                if broken=='gate':values[name+'/result.json']=b'{"state":"FAILED"}'
                if broken=='unlock':values[name+'/lock_released.json']=b'{"state":"UNKNOWN","released":true}'
                if broken=='released':
                    value=json.loads(values[name+'/lock_released.json']);value['released']=False;values[name+'/lock_released.json']=json.dumps(value).encode()
                with self.subTest(kind=kind,broken=broken),self.assertRaises(ValueError):self.build(values)

    def test_bad_candidate_role_or_template_bytes_reject(self):
        for key,name in M.CANDIDATES.items():
            values=self.artifacts();values[name]=b'{"schema":"OTHER"}'
            with self.subTest(key=key),self.assertRaises(ValueError):self.build(values)
        with self.assertRaises(ValueError):M.build_request(self.template()+b'\n',self.artifacts().__getitem__)

    def test_default_noop_reads_no_actual_gate_and_writes_nothing(self):
        with (patch('sys.argv',['prepare_stage5_first_actual_request_v3.py']),patch.object(M,'read_plain',side_effect=AssertionError('No read')),
              contextlib.redirect_stdout(io.StringIO()) as output):self.assertEqual(M.main(),0)
        value=json.loads(output.getvalue());self.assertEqual(value['gates_executed'],0);self.assertEqual(value['requests_written'],0)


if __name__=='__main__':unittest.main()
