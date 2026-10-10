"""Focused fake namespace/parent contracts; no WSL, /proc or native owner."""
from unittest.mock import patch
import contextlib, copy, io, json, unittest
import stage5_gdrive_view_session as G


class SessionParentContracts(unittest.TestCase):
    def observation(self):
        return {'self':'mnt:[200]','parent':'mnt:[200]','pid1':'mnt:[100]',
          'parent_pid':7,'parent_executable':'/init',
          'parent_record':{'pid':7,'ppid':1,'start_ticks':'10','state':'S'},
          'current_record':{'pid':8,'ppid':7,'start_ticks':'20','state':'R'}}

    def test_pid1_difference_is_diagnostic_and_default_stays_noop(self):
        self.assertEqual(G.session_namespace_gate(self.observation())['parent_pid'],7)
        with (patch('sys.argv',['stage5_gdrive_view_session.py','--mount']),
              patch.object(G,'windows_main',side_effect=AssertionError('No owner')),
              contextlib.redirect_stdout(io.StringIO()) as output):
            self.assertEqual(G.main(),0)
        self.assertEqual(json.loads(output.getvalue())['WSL_launches'],0)

    def test_unknown_parent_or_namespace_cannot_admit(self):
        for change in [{'parent_executable':'/bin/bash'},{'parent':'mnt:[201]'},
                       {'parent_pid':0},{'parent_executable':'/init (deleted)'},
                       {'self':'unknown','parent':'unknown'}]:
            value=self.observation();value.update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):G.session_namespace_gate(value)
        value=self.observation();value['parent_record']['state']='Z'
        with self.assertRaises(ValueError):G.session_namespace_gate(value)

    def test_final_parent_birth_or_namespace_drift_cannot_admit(self):
        original=self.observation();same=copy.deepcopy(original);same['parent_record']['state']='R'
        self.assertEqual(G.session_namespace_gate(same,original)['parent_pid'],7)
        for change in ('birth','parent_pid','namespace','current_birth'):
            value=copy.deepcopy(original)
            if change=='birth':value['parent_record']['start_ticks']='11'
            if change=='parent_pid':
                value['parent_pid']=9;value['parent_record']['pid']=9;value['current_record']['ppid']=9
            if change=='namespace':value['self']=value['parent']='mnt:[201]'
            if change=='current_birth':value['current_record']['start_ticks']='21'
            with self.subTest(change=change),self.assertRaises(ValueError):G.session_namespace_gate(value,original)


if __name__=='__main__':unittest.main()
