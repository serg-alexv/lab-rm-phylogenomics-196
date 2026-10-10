"""Synthetic independent review guards; actual recovered storage NOT_RUN."""
from pathlib import Path
import copy, hashlib, json, runpy, stat, sys, unittest
from unittest.mock import patch
import review_stage5_storage_recovery_actual as R

WORK=Path(__file__).resolve().parent


def fixture():
    snapshot=json.loads((WORK/R.SNAPSHOT).read_text())
    proof={'boot_id':'new-synthetic-boot','filesystem_uuid':R.UUID,'directory_inode':R.INODE,'directory_device':1234}
    before={'state':'PASS_EXACT_PREPARED_BACKING_CONTENTS_PRESERVED_FRESH_LINUX_OBSERVATION',
            'snapshot_sha256':R.SNAPSHOT_SHA,'closure_peer_sha256':R.CLOSURE_SHA,'old_boot_id':R.OLD_BOOT,
            'new_boot_id':proof['boot_id'],'filesystem_uuid':R.UUID,'directory_inode':R.INODE,'fresh_directory_device':1234,
            'fresh_directory_metadata':{'uid':0,'gid':0,'mode':stat.S_IFDIR|0o700,'nlink':3},
            'deletions':0,'moves':0,'detector_launches':0,'members':{},'file_bytes_read':0}
    for item in snapshot['backing_inventory']:
        row={'device':1234,'inode':item['windows_unc_inode_projection'],'uid':0,'gid':0,
             'mode':(stat.S_IFREG|0o600) if item['kind']=='file' else (stat.S_IFDIR|0o700),
             'nlink':1 if item['kind']=='file' else 2,'kind':item['kind']}
        if row['kind']=='file':
            row.update(bytes=item['bytes'],sha256=item['sha256']);before['file_bytes_read']+=row['bytes']
        before['members'][item['member']]=row
    return before,copy.deepcopy(before),proof,snapshot


class Guards(unittest.TestCase):
    def test_complete_synthetic_preservation_accepted(self):
        result=R.recovery_join(*fixture());self.assertEqual(result['members'],52);self.assertEqual(result['genome_members'],50)

    def test_stale_boot_uuid_and_device_rejected(self):
        for key,value in [('boot_id',R.OLD_BOOT),('filesystem_uuid','other'),('directory_device',999),('directory_inode',999)]:
            before,after,proof,snapshot=fixture();proof[key]=value
            with self.assertRaises(ValueError):R.recovery_join(before,after,proof,snapshot)

    def test_full_membership_payload_inode_or_link_tamper_rejected(self):
        baseline=fixture();file=next(n for n,r in baseline[0]['members'].items() if r['kind']=='file')
        for key,value in [('bytes',-1),('sha256','0'*64),('inode',0),('nlink',2),('mode',stat.S_IFLNK|0o777),('device',2),('inode',float(baseline[0]['members'][file]['inode']))]:
            before,after,proof,snapshot=fixture();before['members'][file][key]=value;after=copy.deepcopy(before)
            with self.assertRaises(ValueError):R.recovery_join(before,after,proof,snapshot)
        before,after,proof,snapshot=fixture();before['members'].pop(file);after=copy.deepcopy(before)
        with self.assertRaises(ValueError):R.recovery_join(before,after,proof,snapshot)

    def test_before_after_change_or_scope_action_rejected(self):
        before,after,proof,snapshot=fixture();after['file_bytes_read']+=1
        with self.assertRaises(ValueError):R.recovery_join(before,after,proof,snapshot)
        for key in ('moves','deletions','detector_launches'):
            before,after,proof,snapshot=fixture();before[key]=1;after=copy.deepcopy(before)
            with self.assertRaises(ValueError):R.recovery_join(before,after,proof,snapshot)

    def test_projection_type_and_hash_count_rejected(self):
        before,after,proof,snapshot=fixture();snapshot['backing_inventory'][0]['windows_unc_inode_projection']=float(snapshot['backing_inventory'][0]['windows_unc_inode_projection'])
        with self.assertRaises(ValueError):R.recovery_join(before,after,proof,snapshot)
        before,after,proof,snapshot=fixture();before['file_bytes_read']-=1;after=copy.deepcopy(before)
        with self.assertRaises(ValueError):R.recovery_join(before,after,proof,snapshot)

    def test_original_closure_helpers_are_pinned(self):
        self.assertEqual(hashlib.sha256((WORK/'review_stage5_postboot_gate.py').read_bytes()).hexdigest(),R.GENERIC_SHA)
        self.assertIs(R.native,R.G.native);self.assertIs(R.terminal,R.G.terminal);self.assertIs(R.lock,R.G.lock)
        self.assertEqual(hashlib.sha256((WORK/R.WINDOWS).read_bytes()).hexdigest(),R.WINDOWS_SHA)
        self.assertEqual(hashlib.sha256((WORK/R.LINUX).read_bytes()).hexdigest(),R.LINUX_SHA)

    def test_explicit_source_review_and_pair_hash_required(self):
        for value in ('',None,'A'*64):
            with self.assertRaises(ValueError):R.source_review(value)
        peer={'state':'FAILED_SOURCE_ONLY','checked_files':{}}
        with patch.object(R,'pinned',return_value=peer):
            with self.assertRaises(ValueError):R.source_review('1'*64)

    def test_actual_main_default_noop(self):
        with patch.object(sys,'argv',['review_stage5_storage_recovery_actual.py']):
            with self.assertRaises(SystemExit) as result:runpy.run_path(str(WORK/'review_stage5_storage_recovery_actual.py'),run_name='__main__')
            self.assertEqual(result.exception.code,0)


if __name__=='__main__':unittest.main()
