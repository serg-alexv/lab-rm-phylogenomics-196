"""Owned C temporary lease integration only; Popen is never allowed to run."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import os, tempfile, unittest
import stage5_interop_smoke_windows as W


class Contracts(unittest.TestCase):
    def fixture(self, directory):
        api=SimpleNamespace(resources=lambda paths:{'physical_available_bytes':9*1024**3,
            'commit_headroom_bytes':9*1024**3,'disk_available_bytes':{'C:':99*1024**3}})
        args=SimpleNamespace(output=directory,distribution='Ubuntu',linux_python='/SYNTHETIC_NO_EXEC/python')
        return args,api,SimpleNamespace(identity={'synthetic':'NO_OS_LOCK'}),{'pid':1,'creation_filetime':1}

    def test_only_owned_lease_writer_retries_then_preserves_failure_stats(self):
        with tempfile.TemporaryDirectory(dir=W.WORK) as tmp:
            directory=Path(tmp);args,api,lock,owner=self.fixture(directory);pairs=[];denied=[True]
            original=W.L._replace_owned
            def replacing(source,target):
                pairs.append((Path(source),Path(target)))
                if denied[0]:
                    denied[0]=False;error=OSError('SYNTHETIC_SHARING_ONLY');error.winerror=5;raise error
                os.replace(source,target)
            def retry(source,target,stats):original(source,target,stats,replace=replacing)
            with patch.object(W.L,'_replace_owned',side_effect=retry),patch.object(W.subprocess,'Popen',side_effect=OSError('SYNTHETIC_NO_CHILD')) as launch:
                result=W.fixture(args,api,lock,owner,'exit0','synthetic_worker','synthetic_supervisor')
            self.assertEqual(launch.call_count,1)
            self.assertEqual(result['state'],'FAILED_NONSCIENTIFIC_FIXTURE')
            self.assertFalse(result['owned_closure_proven'])
            self.assertEqual(result['lease_helper_sha256'],W.LEASE_HELPER_SHA256)
            self.assertEqual(result['lease_replace_stats']['calls'],3)
            self.assertEqual(result['lease_replace_stats']['transient_winerrors'],{'5':1})
            self.assertEqual(result['lease_replace_stats']['retries'],1)
            self.assertEqual(pairs[0],pairs[1])
            self.assertTrue(all(target==directory/'exit0/owner_lease.json' for _,target in pairs))
            self.assertFalse(list((directory/'exit0').glob('.owner_lease.json*')))

    def test_fatal_lease_write_blocks_any_launch_and_keeps_explicit_failure(self):
        with tempfile.TemporaryDirectory(dir=W.WORK) as tmp:
            directory=Path(tmp);args,api,lock,owner=self.fixture(directory)
            with patch.object(W.L,'_replace_owned',side_effect=OSError('SYNTHETIC_FATAL_NO_RETRY')),patch.object(W.subprocess,'Popen') as launch:
                result=W.fixture(args,api,lock,owner,'exit0','synthetic_worker','synthetic_supervisor')
            launch.assert_not_called()
            self.assertEqual(result['state'],'FAILED_NONSCIENTIFIC_FIXTURE')
            self.assertEqual(result['lease_replace_stats']['failed_calls'],3)
            self.assertTrue((directory/'INTEROP_UNPROVEN_STOP.json').is_file())
            self.assertFalse(list((directory/'exit0').glob('.owner_lease.json*')))


if __name__=='__main__':unittest.main()
