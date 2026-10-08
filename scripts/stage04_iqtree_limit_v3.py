#!/usr/bin/env python3
"""Set a strict1536MiB native-child address-space limit, record it, then exec.

The caller owns workflow/process identity and scientific validation. This
helper is not scientific PASS; a recorded limit cannot substitute for outputs.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

LIMIT=1610612736


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda:stream.read(1048576),b''):h.update(data)
    return h.hexdigest()


def execute(identity,receipt,argv):
    if sys.platform!='linux' or not argv:raise ValueError('Native Linux argv required')
    import resource
    binary=Path(argv[0]).resolve()
    if identity['iqtree_address_space_limit_bytes']!=LIMIT or identity['maximum_compute_threads']!=2:
        raise ValueError('Frozen1536MiB/two-thread policy differs')
    if digest(binary)!=identity['iqtree3_sha256']:raise ValueError('Pinned native executable changed')
    if len(os.sched_getaffinity(0))>2 or any(os.environ.get(k)!='2' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')):
        raise ValueError('Caller CPU/thread bounds missing')
    before=resource.getrlimit(resource.RLIMIT_AS)
    if before[0]!=2147483648 or before[1]!=2147483648:raise ValueError('Outer2GiB soft/hard bounds missing')
    resource.setrlimit(resource.RLIMIT_AS,(LIMIT,LIMIT))
    after=resource.getrlimit(resource.RLIMIT_AS)
    if after!=(LIMIT,LIMIT):raise ValueError('Actual native1536MiB bounds not applied')
    stat=Path('/proc/self/stat').read_text();start_ticks=int(stat[stat.rfind(')')+2:].split()[19])
    value={'execution':'ACTUAL_LIMIT_SET_IMMEDIATELY_BEFORE_NATIVE_EXEC','utc':datetime.now(timezone.utc).isoformat(),
           'pid':os.getpid(),'parent_pid':os.getppid(),'start_ticks':start_ticks,
           'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'argv':argv,
           'binary_sha256':digest(binary),'identity':identity,'cpu_affinity':sorted(os.sched_getaffinity(0)),
           'outer_address_space_soft_hard_bytes':list(before),'native_address_space_soft_hard_bytes':list(after),
           'limit_helper_source_sha256':digest(__file__),'scientific_validation':'NOT_RUN_NATIVE_EXEC_AND_INDEPENDENT_OUTPUT_GATE_REQUIRED'}
    receipt=Path(receipt);receipt.parent.mkdir(parents=True,exist_ok=True)
    if receipt.exists():raise ValueError('Preserve an existing limit receipt; choose a fresh attempt')
    temporary=receipt.with_suffix('.json.partial');temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');temporary.replace(receipt)
    os.execve(str(binary),argv,dict(os.environ))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt-file',type=Path,required=True)
    p.add_argument('--identity-file',type=Path,required=True);p.add_argument('argv',nargs=argparse.REMAINDER)
    a=p.parse_args();argv=a.argv[1:] if a.argv[:1]==['--'] else a.argv
    execute(json.loads(a.identity_file.read_text()),a.receipt_file,argv)
