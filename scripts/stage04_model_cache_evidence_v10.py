"""Strict actual tool messages distinguish copied bytes from observed cache use."""
from pathlib import Path
import gzip, hashlib, json, math, re
import stage04_controller as C

def check_cache_log(log,new_prefix):
    restore='NOTE: Restoring information from model checkpoint file '+str(new_prefix)+'.model.gz'
    fast='CHECKPOINT: Tree restored, LogL:'
    C.check(restore in log,'Exact new-prefix model checkpoint load message missing')
    C.check(fast in log,'Saved fast-ML tree was not observed restored')
    C.check('-mredo' not in log.split('Command:')[-1].splitlines()[0] if 'Command:' in log else True,'Model redo request conflicts with recovery')
    return {'actual_model_checkpoint_load':True,'actual_fast_ml_tree_restore':True,
      'whole_partition_skip':'NOT_INFERRED_FROM_PROGRESS_COUNTS','native_output_acceptance':'SEPARATE_SCIENTIFIC_CHECKS_REQUIRED'}

def checkpoint_map(path):
    """Parse IQ-TREE's flat checkpoint namespace, without YAML interpretation.

    Trees and numbers stay literal strings. Duplicate keys, deeper indentation
    and malformed lines block acceptance instead of selecting a last value.
    """
    with gzip.open(path,'rt',encoding='utf-8') as stream:text=stream.read(16*1024**2+1)
    C.check(len(text)<=16*1024**2 and text.startswith('--- # IQ-TREE Checkpoint ver >= 1.6'), 'Unexpected checkpoint format/size')
    result={};section=None
    for line in text.splitlines()[1:]:
        if not line:continue
        C.check(': ' in line or line.endswith(':'),'Malformed checkpoint line')
        key,_,value=line.partition(':');value=value.strip()
        if line.startswith(' '):
            C.check(section is not None and not line.startswith('  '),'Unexpected checkpoint nesting')
            key=section+'/'+key.strip()
        elif not value:
            section=key;continue
        else:section=None
        C.check(key not in result,'Duplicate checkpoint key: '+key);result[key]=value
    return result

def completed_records(items,expected_ids):
    completed={k.split('/')[0] for k in items if k.endswith('/best_model_BIC')}
    C.check(completed<=set(expected_ids),'Foreign completed checkpoint partition')
    result={}
    for pid in sorted(completed):
        model=items[pid+'/best_model_BIC'];candidate=items.get(pid+'/'+model)
        C.check(candidate is not None and len(candidate.split())==3,'Missing selected candidate likelihood/df/tree length')
        logl,df,length=candidate.split()
        C.check(all(math.isfinite(float(x)) for x in (logl,df,length)) and float(df).is_integer() and float(df)>=0 and float(length)>=0,
          'Invalid selected candidate tuple')
        score=items.get(pid+'/best_score_BIC')
        C.check(score is not None and math.isfinite(float(score)),'Missing/nonfinite BIC decision')
        result[pid]={'best_model_BIC':model,'best_score_BIC':score,'selected_candidate_logL_df_tree_length':candidate}
    return result

def check_cache_records(retained,final,expected_ids,retained_sha256):
    C.check(C.digest(retained)==retained_sha256,'Retained model cache hash changed')
    C.check(len(expected_ids)==len(set(expected_ids))==100,'Expected primary partition IDs are not exactly100')
    old=completed_records(checkpoint_map(retained),expected_ids)
    new=completed_records(checkpoint_map(final),expected_ids)
    C.check(len(old)==14,'Retained complete decision count differs from14')
    C.check(set(new)==set(expected_ids),'Final cache lacks exact100 completed primary partitions')
    C.check(all(new[pid]==record for pid,record in old.items()),'Inherited complete candidate/decision record changed')
    added=sorted(set(new)-set(old));C.check(len(added)==86,'New completion count differs from86')
    digest=lambda row:hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {'retained_cache_sha256':retained_sha256,'final_cache_sha256':C.digest(final),
      'retained_decision_ids':sorted(old),'new_decision_ids':added,'final_completed_ids':sorted(new),
      'retained_decisions_sha256':digest(old),'final_decisions_sha256':digest(new),
      'inherited_selected_candidate_and_BIC_records':'EXACT_LITERAL_VALUES_UNCHANGED',
      'progress_queue_start':'INFORMATIONAL_ZERO_OF100_ALLOWED','scientific_acceptance':'SEPARATE_TREE_SUPPORT_CHECKS_REQUIRED'}
