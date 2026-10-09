"""Source-derived IQ-TREE v3.1.4 memory estimate; no executable inference."""
import hashlib, json, math
from pathlib import Path
BASE=Path(__file__).resolve().parent
ALN=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196\.work\stage04_phylogeny_v2\analyses\primary196\concatenated.faa')
BIN=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.tools\iqtree_windows_3_1_4\extracted\iqtree-3.1.4-Windows\bin\iqtree3.exe')
GiB=2**30
seq=[]
for line in ALN.read_text().splitlines():
    if line.startswith('>'): seq.append('')
    elif line: seq[-1]+=line.strip()
patterns=len(set(zip(*seq)))
round_to=lambda n,k:((n+k-1)//k)*k
# Native historical log reports AVX+FMA: four doubles/eight floats per vector.
N=len(seq);P=round_to(patterns,4)+round_to(20,4)
# 127 is deliberately conservative unknown-state bound, not a measured alignment state.
unknown_bound=127
tip_bytes=round_to(20*(unknown_bound+1),4)*8
ufboot_bytes=1000*round_to(patterns,8)*4
def estimate(cats,mem=None):
    slot=P*cats*(20*8+1)
    fixed=tip_bytes+ufboot_bytes
    slots=N-2
    if mem is not None:
        slots=min(slots,int((mem-fixed)//slot)-2)
        slots=max(slots,min(int(math.log2(N)+1),N-2))
    core=fixed+(slots+2)*slot
    # Major arrays omitted by getMemoryRequired(): G_matrix, theta, pattern-category,
    # frequency/scaling arrays; conservatively oversized packet and parsimony buffers.
    outside={
        'G_matrix_bytes':(2*N-3)*P*8,
        'theta_all_bytes':P*20*cats*8,
        'pattern_category_bytes':P*cats*8,
        'seven_pattern_arrays_bytes':7*P*8,
        'traversal_packet_and_parsimony_allowance_bytes':128*2**20,
    }
    major=core+sum(outside.values())
    return {'rate_categories':cats,'lh_slots':slots,'source_core_estimator_bytes':core,
        'source_core_estimator_gib':core/GiB,'major_outside_estimator':outside,
        'core_plus_major_allowances_bytes':major,'core_plus_major_allowances_gib':major/GiB}
result={
    'method':'Independent translation of pinned v3.1.4 PhyloTree::getMemoryRequired; structural upper allowance, not measured peak or complete heap proof',
    'alignment_sha256':hashlib.sha256(ALN.read_bytes()).hexdigest(),
    'native_binary_sha256':hashlib.sha256(BIN.read_bytes()).hexdigest(),
    'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'taxa':N,'columns':len(seq[0]),'unique_column_patterns':patterns,'padded_patterns_plus_states':P,
    'ufboot1000_bytes':ufboot_bytes,
    'normal_mode':[estimate(c) for c in (1,4,10)],
    'mem2G_mode':[estimate(c,2*GiB) for c in (1,4,10)],
    'recommendation':{
        'native_mem_flag':'--mem 2G','candidate_thread_mode':'--thread-site','threads':2,
        'hard_process_and_aggregate_job_commit_bytes':int(3.5*GiB),
        'host_physical_and_commit_admission_reserve_bytes':int(1.5*GiB),
        'minimum_physical_and_commit_headroom_bytes':5*GiB,
        'reserve_above_core_memory_target_bytes':int(1.5*GiB),
        'scope':'Single unpartitioned same-data MFP only; no candidate restriction, dataset reduction or support reduction',
        'qualification':'A justified bounded allocation policy, not evidence of successful completion. Unknown fragmentation/runtime overhead is bounded by native job caps; allocation failure remains explicit.'},
    'memcheck':{'available_in_parser':True,'documented_in_native_help':False,'safe_no_inference_for_MFP':False,
        'reason':'startTreeReconstruction calls runModelFinder and computeFastMLTree before runTreeReconstruction checks memCheck and exits'},
    'data_bearing_native_invocation_executed':False,
    'sources':[{'relative_path':str(p.relative_to(BASE)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
        'url':'https://raw.githubusercontent.com/iqtree/iqtree3/v3.1.4/'+p.name.replace('__','/')} for p in sorted((BASE/'iqtree314_source').glob('*'))]
}
(BASE/'fallback_memory_evidence.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('taxa','columns','unique_column_patterns','normal_mode','mem2G_mode','recommendation','memcheck')}))
