"""Strict completed native log evidence contracts; no native inputs or inference."""
import unittest
from independent_tree_check import support_execution_check
REPORT='Numbers in parentheses are SH-aLRT support (%) / ultrafast bootstrap support (%)\n'
EXECUTED=('Testing tree branches by SH-like aLRT with 1000 replicates...\n'
          '79.923 sec.\nCreating bootstrap support values...\n')
class SupportExecution(unittest.TestCase):
 def test_actual_iqtree314_emitted_format(self):
  value=support_execution_check(REPORT,EXECUTED,EXECUTED)
  self.assertEqual(value['replicates'],1000);self.assertEqual(value['completed_native_duration_seconds']['native_log'],79.923)
 def test_windows_line_endings(self):support_execution_check(REPORT,EXECUTED.replace('\n','\r\n'),EXECUTED)
 def test_command_or_report_alone_not_execution(self):
  with self.assertRaises(ValueError):support_execution_check(REPORT,'--alrt 1000\n','SH-aLRT 1000 replicates\n')
 def test_wrong_replicate_count(self):
  with self.assertRaises(ValueError):support_execution_check(REPORT,EXECUTED.replace('1000','999'),EXECUTED)
 def test_unfinished_test_missing_duration(self):
  with self.assertRaises(ValueError):support_execution_check(REPORT,EXECUTED.replace('79.923 sec.\n',''),EXECUTED)
 def test_unfinished_test_missing_subsequent_stage(self):
  with self.assertRaises(ValueError):support_execution_check(REPORT,EXECUTED.replace('Creating bootstrap support values...\n',''),EXECUTED)
 def test_two_stream_duration_disagreement(self):
  with self.assertRaises(ValueError):support_execution_check(REPORT,EXECUTED.replace('79.923','1.0'),EXECUTED)
 def test_missing_paired_support_interpretation(self):
  with self.assertRaises(ValueError):support_execution_check('',EXECUTED,EXECUTED)
 def test_duplicate_or_nonfinite_execution_records(self):
  with self.assertRaises(ValueError):support_execution_check(REPORT,EXECUTED*2,EXECUTED)
  with self.assertRaises(ValueError):support_execution_check(REPORT,EXECUTED.replace('79.923','9'*400),EXECUTED)
if __name__=='__main__':unittest.main()
