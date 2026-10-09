"""Own C bytes and pure mount/closure contracts; no WSL, G or native APIs."""
from pathlib import Path
from unittest.mock import patch
import contextlib,copy,hashlib,io,json,tempfile,unittest
import stage5_gdrive_view as G


class Contracts(unittest.TestCase):
    def row(self,**changes):
        row={'mountpoint':'/mnt/g','source':'G:\\','root':'/','filesystem':'9p',
             'options':'rw,noatime','super_options':'rw,aname=drvfs;path=G:\\;uid=0'}
        row.update(changes);return row

    def terminal(self):
        return {'schema':'STAGE05_GDRIVE_LINUX_TERMINAL_V1','scope':G.SCOPE,'owner_nonce':'nonce',
            'request_sha256':'request','source_sha256':'source','boot_id':'boot','owned_closure_proven':True,
            'remaining_direct_children':[],'scientific_adoption_authorized':False,
            'owned_command_count':0,'state':'PASS_DIAGNOSIS_G_DRIVE_NOT_MOUNTED_NO_REPAIR'}

    def gate(self,value,**kwargs):return G.terminal_gate(value,'nonce','request','source','boot',kwargs.get('exit_code',0),kwargs.get('allow_mount',False))

    def test_default_is_noop_even_with_mount_flag(self):
        with (patch('sys.argv',['stage5_gdrive_view.py','--mount']),
              patch.object(G,'windows_main',side_effect=AssertionError('NO OWNER')),
              contextlib.redirect_stdout(io.StringIO()) as out):
            self.assertEqual(G.main(),0)
        self.assertEqual(json.loads(out.getvalue())['WSL_launches'],0)

    def test_exact_posix_request_paths_on_windows(self):
        self.assertEqual(str(G.LROOT),'/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196')
        self.assertEqual(str(G.LWORK/'stage5_gdrive_view.py'),'/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/stage5_gdrive_view.py')
        self.assertEqual(G.MOUNT_ARGV,['/usr/bin/mount','-t','drvfs','G:','/mnt/g'])

    def test_exact_g_mounts_only(self):
        self.assertIsNone(G.drive_mount([]));self.assertEqual(G.drive_mount([self.row()]),self.row())
        self.assertEqual(G.drive_mount([self.row(filesystem='drvfs',source='G:',super_options='rw')])['source'],'G:')
        for row in [self.row(source='C:\\'),self.row(root='/unknown'),self.row(filesystem='ext4'),
                    self.row(options='ro'),self.row(super_options='rw,aname=unrelated')]:
            with self.subTest(row=row),self.assertRaises(ValueError):G.drive_mount([row])

    def test_unknown_nested_or_stacked_mount_preserved(self):
        with self.assertRaises(ValueError):G.drive_mount([self.row(),self.row()])
        with self.assertRaises(ValueError):G.drive_mount([self.row(mountpoint='/mnt/g/unknown')])

    def test_empty_only_and_tiny_exact_own_c_bytes(self):
        with tempfile.TemporaryDirectory(prefix='gdrive_view_fixture_',dir=Path(__file__).parent) as name:
            root=Path(name);self.assertEqual(G.empty_directory(root)['entries'],[])
            data=b'OWN_SYNTHETIC\x00\r\n';(root/'control').write_bytes(data)
            self.assertEqual(G.tiny(root/'control'),data)
            with self.assertRaises(ValueError):G.empty_directory(root)
            with self.assertRaises(ValueError):G.tiny(root/'control',2)

    def test_control_authority_panel_approval_and_raw_hashes(self):
        panel=('\n'.join('GCF_'+str(i).zfill(9)+'.1' for i in range(196))+'\n').encode('ascii')
        pin=hashlib.sha256(panel).hexdigest()
        raw={G.CONTROLS[0]:json.dumps({'state':'ACTIVE_DIRECT_USER_CONTINUATION','automatic_resume':False}).encode(),
             G.CONTROLS[1]:panel,G.CONTROLS[2]:json.dumps({'human_approval':'APPROVED_FOR_SEQUENCE_ANALYSIS',
             'approved_assembly_count':196,'pilot':False,'panel_accessions_sha256':pin}).encode()}
        with patch.object(G,'PANEL_SHA',pin):
            self.assertEqual(G.control_gate(raw)[G.CONTROLS[1]],pin)
            wrong=copy.deepcopy(raw);wrong[G.CONTROLS[0]]=b'{"state":"ACTIVE_DIRECT_USER_CONTINUATION","automatic_resume":true}'
            with self.assertRaises(ValueError):G.control_gate(wrong)
            wrong=copy.deepcopy(raw);wrong[G.CONTROLS[1]]+=b'EXTRA'
            with self.assertRaises(ValueError):G.control_gate(wrong)

    def test_closed_no_command_diagnosis_and_mount_count(self):
        self.assertEqual(self.gate(self.terminal()),0)
        mounted=self.terminal();mounted.update(owned_command_count=1,state='PASS_EXACT_WINDOWS_LINUX_G_CONTROL_BYTES_AND_EMPTY_UNDERLAY')
        self.assertEqual(self.gate(mounted,allow_mount=True),1)
        with self.assertRaises(ValueError):self.gate(mounted)

    def test_unproven_or_wrong_terminal_never_closes_scope(self):
        for change in [{'owned_closure_proven':False},{'remaining_direct_children':[1]},
                       {'owner_nonce':'other'},{'boot_id':'other'},{'scientific_adoption_authorized':True},
                       {'owned_command_count':2},{'owned_command_count':True}]:
            bad=self.terminal();bad.update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):self.gate(bad)
        with self.assertRaises(ValueError):self.gate(self.terminal(),exit_code=2)


if __name__=='__main__':unittest.main()
