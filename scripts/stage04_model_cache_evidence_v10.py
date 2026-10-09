"""Strict actual tool messages distinguish copied bytes from observed cache use."""
from pathlib import Path
import stage04_controller as C

def check_cache_log(log,new_prefix):
    restore='NOTE: Restoring information from model checkpoint file '+str(new_prefix)+'.model.gz'
    fast='CHECKPOINT: Tree restored, LogL:'
    C.check(restore in log,'Exact new-prefix model checkpoint load message missing')
    C.check(fast in log,'Saved fast-ML tree was not observed restored')
    C.check('-mredo' not in log.split('Command:')[-1].splitlines()[0] if 'Command:' in log else True,'Model redo request conflicts with recovery')
    return {'actual_model_checkpoint_load':True,'actual_fast_ml_tree_restore':True,
      'whole_partition_skip':'NOT_INFERRED_FROM_PROGRESS_COUNTS','native_output_acceptance':'SEPARATE_SCIENTIFIC_CHECKS_REQUIRED'}
