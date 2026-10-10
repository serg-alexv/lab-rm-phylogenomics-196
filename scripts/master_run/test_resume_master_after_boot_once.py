"""Pure/local-C one-shot handoff contracts. No actual ID/network/WSL/CLI launch."""
import contextlib, copy, importlib.util, io, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('resume_once',Path(__file__).with_name('resume_master_after_boot_once.py'))
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)

class Contracts(unittest.TestCase):
    def setUp(self):
        self.before={'last_boot_utc':'2026-10-09T00:00:00+00:00','tick_before_ms':100000000,'tick_after_ms':100000010}
        self.after={'last_boot_utc':'2026-10-10T00:00:00+00:00','tick_before_ms':100000,'tick_after_ms':100010}
    def test_new_boot_both_actual_markers_required(self):
        M.new_boot(self.before,self.after)
        for name,value in (('last_boot_utc',self.before['last_boot_utc']),('tick_after_ms',100000010)):
            changed=copy.deepcopy(self.after);changed[name]=value
            with self.assertRaises(ValueError):M.new_boot(self.before,changed)
    def test_no_old_boot_or_delayed_replay(self):
        for after in ({**self.after,'last_boot_utc':'2026-10-08T00:00:00+00:00'},
                      {**self.after,'tick_after_ms':7200000}, {**self.after,'tick_before_ms':100011}):
            with self.assertRaises(ValueError):M.new_boot(self.before,after)
    def test_single_use_create_new_preserves_first_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'claim.json';M.write_new(path,{'state':'FIRST'})
            captured=path.read_bytes()
            with self.assertRaises(FileExistsError):M.write_new(path,{'state':'SECOND'})
            self.assertEqual(path.read_bytes(),captured)
    def test_exact_thread_never_uses_last_and_pins_policy(self):
        thread='01234567-89ab-4cde-8f01-234567890abc';argv=M.cli_command(thread)
        self.assertEqual(argv[-2:],[thread,'-']);self.assertNotIn('--last',argv)
        self.assertIn('approval_policy="never"',argv);self.assertIn('sandbox_mode="danger-full-access"',argv)
        with self.assertRaises((ValueError,AttributeError)):M.cli_command('--------------------invalid----------')
    def test_default_noop_never_reads_private_or_starts_child(self):
        with patch('sys.argv',['helper']),patch.object(M,'prepare_private',side_effect=AssertionError),\
             patch.object(M,'resume_once',side_effect=AssertionError),contextlib.redirect_stdout(io.StringIO()) as out:
            M.main()
        self.assertEqual(json.loads(out.getvalue())['state'],'PREPARED_DEFAULT_NOOP')
    def test_non_descendant_authority_refuses_before_snapshot(self):
        with patch.object(M,'fetch',side_effect=[json.dumps({'object':{'sha':'a'*40}}).encode(),b'{"status":"diverged"}']):
            with self.assertRaisesRegex(ValueError,'descendant'):M.fresh_authority({'published_anchor':'b'*40})
    def test_invalid_new_boot_cannot_consume_or_launch(self):
        with patch.object(M,'WORK',Path(__file__).resolve().parent),patch.object(M,'no_alias'),\
             patch.object(Path,'stat') as stat,patch.object(Path,'read_bytes',return_value=json.dumps({
                 'schema':'PRIVATE_MASTER_BOOT_RESUME_HANDOFF_V1','thread_id':'01234567-89ab-4cde-8f01-234567890abc',
                 'published_anchor':'a'*40,'codex_sha256':'s','python_sha256':'s','helper_sha256':'s','launcher_sha256':'s',
                 'baseline':self.before}).encode()),patch.object(M,'sha',return_value='s'),\
             patch.object(M,'boot_observation',return_value=self.before),patch.object(M,'write_new') as write,\
             patch.object(M.subprocess,'Popen') as popen:
            stat.return_value.st_size=100
            with self.assertRaisesRegex(ValueError,'did not advance'):M.resume_once()
            write.assert_not_called();popen.assert_not_called()

if __name__=='__main__':unittest.main()
