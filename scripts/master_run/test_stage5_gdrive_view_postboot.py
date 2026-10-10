"""Three focused C-only postboot provenance contracts; no WSL/native owner."""
from pathlib import Path
from unittest.mock import patch
import contextlib, copy, hashlib, io, json, unittest
import stage5_gdrive_view_postboot as G


class PostbootContracts(unittest.TestCase):
    def test_default_noop_without_fresh_proof_even_with_mount_flag(self):
        with (patch('sys.argv',['stage5_gdrive_view_postboot.py','--mount']),
              patch.object(G,'windows_main',side_effect=AssertionError('No actual owner allowed')),
              contextlib.redirect_stdout(io.StringIO()) as output):
            self.assertEqual(G.main(),0)
        self.assertEqual(json.loads(output.getvalue()),{'state':'PREPARED_NOT_RUN','WSL_launches':0,'mounts':0})

    def test_exact_published_toolchain05_selected_and_old04_rejected(self):
        path=G.WORK/G.FRESH_TOOLCHAIN_DIR/'toolchain_proof.json'
        pin=G.FRESH_PINS[G.FRESH_TOOLCHAIN_DIR+'/toolchain_proof.json']
        self.assertEqual(G.fresh_toolchain_gate(G.WORK,path,pin),'e93cddc2-2ddf-4152-be46-ceef5227c922')
        for wrong_path,wrong_pin in [(path,'0'*64),
            (G.WORK/'stage5_setup_toolchain_actual_postiq_04/toolchain_proof.json',pin),
            (path,None)]:
            with self.subTest(path=wrong_path,pin=wrong_pin),self.assertRaises(ValueError):
                G.fresh_toolchain_gate(G.WORK,wrong_path,wrong_pin)

    def test_self_consistent_altered_file_hashes_cannot_break_receipt_joins(self):
        prefix=G.FRESH_TOOLCHAIN_DIR+'/'
        mutations=[(prefix+'linux_terminal.json',lambda x:x.update(owner_nonce='different')),
                   (prefix+'lock_released.json',lambda x:x.update(released=False)),
                   ('stage5_toolchain05_postboot_independent_review.json',
                    lambda x:x['detail'].update(candidate_sha256='0'*64))]
        tiny,sha=G.tiny,G.sha
        for name,mutate in mutations:
            value=json.loads(tiny(G.WORK/name));mutate(value);raw=json.dumps(value).encode()
            pins=copy.deepcopy(G.FRESH_PINS);pins[name]=hashlib.sha256(raw).hexdigest()
            selected=G.WORK/name
            with (self.subTest(name=name),patch.object(G,'FRESH_PINS',pins),
                  patch.object(G,'tiny',side_effect=lambda p,*a:raw if Path(p)==selected else tiny(p,*a)),
                  patch.object(G,'sha',side_effect=lambda p:pins[name] if Path(p)==selected else sha(p)),
                  self.assertRaises(ValueError)):
                G.fresh_toolchain_gate(G.WORK,G.WORK/G.FRESH_TOOLCHAIN_DIR/'toolchain_proof.json',
                                       pins[prefix+'toolchain_proof.json'])


if __name__=='__main__':unittest.main()
