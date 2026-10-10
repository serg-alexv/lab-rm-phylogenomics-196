"""Pure UNC03 byte preparation contracts; no future candidate reads or probe."""
from pathlib import Path
from unittest.mock import patch
import contextlib, copy, io, json, unittest
import prepare_stage5_unc_postprofile03 as M

HERE=Path(__file__).resolve().parent


class Tests(unittest.TestCase):
    def fixture(self):
        raw=(HERE/M.TEMPLATE).read_bytes();template=json.loads(raw)
        roots={k:template['runtime'][k] for k in ('environment_dir','models_dir','padloc_db')}
        runtime={'schema':'STAGE05_PINNED_RUNTIME_V1','scope':'Hash/version discovery only; execution/interoperability NOT_RUN',
                 'roots':roots,'files':{k:{'synthetic.bin':'a'*64} for k in roots}}
        backing={'filesystem':'ext4','options':'rw,relatime','mount_id':1,'parent_id':0,'major_minor':'8:48',
                 'source':'/dev/sdd','mountpoint':'/','root':'/'}
        target={**backing,'mount_id':2,'parent_id':1,'mountpoint':M.TARGET,'root':M.BACKING}
        storage={'schema':'STAGE05_EXT4_BIND_STORAGE_PROOF_V1','canonical_root':M.ROOT,'canonical_target':M.TARGET,
                 'backing':M.BACKING,'boot_id':M.BOOT,'helper_sha256':M.PINS['stage5_work_storage.py'],
                 'directory_device':2096,'directory_inode':33554542,'filesystem_uuid':'3370e495-79b5-4136-9c6b-d31c7cb6a6be',
                 'target_mount':target,'backing_mount':backing}
        return raw,runtime,storage

    def build(self,raw=None,runtime=None,storage=None):
        original,r,s=self.fixture();raw=original if raw is None else raw
        r=json.dumps(r if runtime is None else runtime).encode();s=json.dumps(s if storage is None else storage).encode()
        return M.build_config(raw,r,s,M.digest(r),M.digest(s))

    def test_only_four_path_and_hash_fields_change_and_all_biological_budgets_remain_null(self):
        raw,_,_=self.fixture();old=json.loads(raw);value=self.build();restored=copy.deepcopy(value)
        for key,prefix in [('runtime','manifest'),('work_storage','proof')]:
            for suffix in ['path','sha256']:restored[key][prefix+'_'+suffix]=old[key][prefix+'_'+suffix]
        self.assertEqual(restored,old);self.assertEqual(value['resource_policy'],old['resource_policy'])
        self.assertTrue(all(value['resource_policy'][k] is None for k in M.FIELDS))
        self.assertEqual(value['runtime']['manifest_path'],M.linux_path(M.RUNTIME_NAME))
        self.assertEqual(value['work_storage']['proof_path'],M.linux_path(M.STORAGE_NAME))
        self.assertEqual(self.build(),value)

    def test_supplied_sha_must_match_the_same_candidate_bytes(self):
        raw,r,s=self.fixture();r=json.dumps(r).encode();s=json.dumps(s).encode()
        for a,b in [('0'*64,M.digest(s)),(M.digest(r),'0'*64),(None,M.digest(s)),(M.digest(r),'A'*64)]:
            with self.subTest(a=a,b=b),self.assertRaises(ValueError):M.build_config(raw,r,s,a,b)
        with self.assertRaises(ValueError):M.build_config(raw+b'\n',r,s,M.digest(r),M.digest(s))

    def test_runtime_scope_roles_and_manifest_paths_reject_tamper(self):
        for change in ['scope','root','file_hash','traversal','missing_role']:
            raw,r,s=self.fixture()
            if change=='scope':r['scope']='BIOLOGICAL_RESULT'
            if change=='root':r['roots']['environment_dir']='/elsewhere'
            if change=='file_hash':r['files']['models_dir']['synthetic.bin']='bad'
            if change=='traversal':r['files']['models_dir']={'../unknown':'a'*64}
            if change=='missing_role':r['files'].pop('padloc_db')
            with self.subTest(change=change),self.assertRaises(ValueError):self.build(raw,r,s)

    def test_old_boot_nonext4_wrong_bind_and_false_numeric_identity_reject(self):
        for change in ['boot','helper','target','readonly','device_float','inode_bool','uuid','different_device','wrong_backing_root']:
            raw,r,s=self.fixture()
            if change=='boot':s['boot_id']='e93cddc2-2ddf-4152-be46-ceef5227c922'
            if change=='helper':s['helper_sha256']='0'*64
            if change=='target':s['target_mount']['mountpoint']='/elsewhere'
            if change=='readonly':s['target_mount']['options']='ro,relatime'
            if change=='device_float':s['directory_device']=2096.0
            if change=='inode_bool':s['directory_inode']=True
            if change=='uuid':s['filesystem_uuid']='00000000-0000-0000-0000-000000000000'
            if change=='different_device':s['target_mount']['major_minor']='8:64'
            if change=='wrong_backing_root':s['target_mount']['root']='/unknown'
            with self.subTest(change=change),self.assertRaises(ValueError):self.build(raw,r,s)

    def test_no_arbitrary_candidate_route_and_preserved_old_sources(self):
        self.assertEqual(M.RUNTIME_NAME,'stage5_runtime_actual_postiq_08.json')
        self.assertEqual(M.STORAGE_NAME,'stage5_storage_actual_postiq_06.json')
        for name,pin in M.PINS.items():self.assertEqual(M.digest((HERE/name).read_bytes()),pin)
        for bad in ['stage5_runtime_actual_postiq_06.json','../outside.json','arbitrary.json']:
            with self.assertRaises(ValueError):M.linux_path(bad)

    def test_default_noop_does_not_read_evidence_or_write_config(self):
        with (patch('sys.argv',['prepare_stage5_unc_postprofile03.py']),
              patch.object(M,'read_plain',side_effect=AssertionError('No reads')),
              patch.object(M,'build_config',side_effect=AssertionError('No constructor')),
              contextlib.redirect_stdout(io.StringIO()) as output):self.assertEqual(M.main(),0)
        self.assertEqual(json.loads(output.getvalue()),{'state':'PREPARED_NOT_RUN','configs_written':0,'WSL_launches':0,
            'UNC_actions':0,'scientific_admission':'NOT_AUTHORIZED'})


if __name__=='__main__':unittest.main()
