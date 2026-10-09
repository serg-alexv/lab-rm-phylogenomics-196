"""Actual local file-format regression for the Stage4 publication boundary."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import csv,json,unittest
import publish_stage4_primary as P

class PublicationText(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory(prefix='synthetic_publication_text_',dir=Path(__file__).resolve().parent)
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        assert self.root.is_relative_to(Path(__file__).resolve().parent)
        self.patch=patch.object(P,'ROOT',self.root);self.patch.start();self.addCleanup(self.patch.stop)

    def test_text_bytes_and_json_are_written_in_correct_formats(self):
        (self.root/'status').mkdir();(self.root/'reports/stage04/synthetic').mkdir(parents=True)
        fields=['stage','execution','validation','publication','observation_as_of_utc','native_pid','native_creation_filetime']
        with (self.root/'status/stages.tsv').open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fields,delimiter='\t');writer.writeheader()
            writer.writerow({'stage':'4_phylogeny','execution':'RUNNING'})
        P.update_status({'frozen_output_directory':str(self.root/'synthetic_accepted'),'native_tree_sha256':'0'*64},
                        {'url':'https://example.invalid/synthetic-no-network'},self.root/'reports/stage04/synthetic')
        with (self.root/'status/stages.tsv').open(encoding='utf-8') as stream:
            rows=list(csv.DictReader(stream,delimiter='\t'))
        self.assertEqual(rows[0]['execution'],'COMPLETED');self.assertEqual(rows[0]['publication'],'UPLOAD_VERIFIED')
        self.assertTrue((self.root/'STATUS.md').read_bytes().startswith(b'# Current execution status\n'))
        self.assertNotIn(b'\r\n',(self.root/'STATUS.md').read_bytes())
        self.assertEqual(json.loads((self.root/'status/stage04_execution.json').read_bytes())['actual_native_exit'],0)

    def test_failed_replace_preserves_original_and_removes_only_own_temporary(self):
        path=self.root/'REPORT.md';path.write_bytes(b'original\n')
        with patch.object(P.os,'replace',side_effect=OSError('synthetic replace failure')):
            with self.assertRaises(OSError):P.atomic_bytes(path,b'changed\n')
        self.assertEqual(path.read_bytes(),b'original\n')
        self.assertEqual({x.name for x in self.root.iterdir()},{'REPORT.md'})

    def test_outside_repository_and_nonbytes_rejected(self):
        with self.assertRaises(ValueError):P.atomic_bytes(self.root.parent/'outside.md',b'no\n')
        with self.assertRaises(ValueError):P.atomic_bytes(self.root/'REPORT.md',{'no':'json'})

if __name__=='__main__':unittest.main()
