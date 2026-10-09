"""Independent read-only batch03 post-purge check. Run only after COMPLETE/STOP.

No producer imports, cleanup, upload, G writes, WSL or scientific execution.
Reads the fixed published mapping as a stream, joins each exact journal record,
and independently hashes all 838 retained originals plus 12 protected files.
"""
from pathlib import Path, PurePosixPath
import argparse, ctypes, datetime, hashlib, json, os, re, stat, time, uuid, zipfile
from ctypes import wintypes as W

WORK = Path(__file__).resolve().parent
OLD = Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
PINS = {
 'master_batch03_leaf_purge_proposed.json': '3f291dc20bb7051a9586aaefc75b7c57c463fba03e87d5ea8c9cdd2dc2ffd952',
 'master_batch03_mapping01/master_batch03_scientific_cache_mapping01.zip': 'f6d7e0558953d2542ca085552a6cd8219a4ec1acde4072ce6f03d12dd953178e',
 'master_batch03_protected_before.json': '22d307f5bba8a98dbd060e3d1d091e22c7f70dc85b40e77ada04c0eef36ce1a7',
 'master_batch03_purge_remote_readback.json': 'b4cca6490a1261bf5d9badfbc4bec96ff46473fb436394e7f3be1e36e735b412',
}
COMMIT = '2b0edf16fe3224d33155ac67f2a8a0d2177d78a5'
MAP_SHA = 'df770f9e49e869c64f61db5720030aceff3b3282d53ee964aae02d228d7c3f64'
KEEP_SHA = 'bca12c16ff092b2e2fb612608186db728518d0ebf07fad80e1b401ed43ff0593'
SCOPES = ('data', '.work/review2', '.work/stage02_validated', '.work/source_locus_inputs_v1',
          '.work/stage03_markers_v1', '.work/stage04a_windows_alignments_v1', '.work/stage04_phylogeny_v2')
OWNERS = ((4768, 134360369876207076), (27048, 134360369803845506))
MAX_RUNTIME = 900
MAX_HASH_BYTES = 2 * 1024**3

def require(value, message):
    if not value: raise ValueError(message)
def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def signature(s): return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_nlink)
def expected_signature(r): return tuple(r[k] for k in ('device', 'file_id', 'bytes', 'mtime_ns', 'link_count'))
def digest(path):
    with path.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def target(row):
    rel = row['relative_path']; p = PurePosixPath(rel)
    require(p.as_posix() == rel and not p.is_absolute() and '\\' not in rel and ':' not in rel
            and all(x not in ('', '.', '..') and not x.endswith((' ', '.')) for x in rel.split('/')),
            'Noncanonical source path')
    require(row['scope'] in SCOPES and rel.startswith(row['scope']+'/')
            and not {'.tools', '.git', '.private_run', '.codex'}.intersection(p.parts), 'Scope/protected path')
    path = OLD.joinpath(*p.parts)
    require(str(path) == row['path'], 'Literal old C root mismatch')
    return path

def join_candidate(next_event, row, line_number, deleted, deleted_bytes):
    """One ordered intent/outcome pair. STOP is preserved, never synthesized success."""
    event = next_event()
    if event.get('event') == 'STOP': return None, event
    require(event.get('event') == 'VERIFIED_INTENT', 'Expected ordered verified intent')
    for key, value in {'line': line_number, 'path': row['path'], 'bytes': row['bytes'], 'sha256': row['sha256']}.items():
        require(event.get(key) == value, 'Journal intent binding differs: '+key)
    for key in ('device', 'file_id', 'mtime_ns'):
        require(event.get(key) == str(row[key]), 'Journal inventory identity differs: '+key)
    outcome = next_event()
    if outcome.get('event') == 'STOP': return event, outcome
    require(outcome.get('event') == 'REMOVED', 'Expected ordered removed outcome')
    for key in ('line', 'path', 'bytes', 'sha256'):
        require(outcome.get(key) == event[key], 'Journal intent/removal join differs: '+key)
    require(outcome.get('deleted') == deleted+1 and outcome.get('deleted_bytes') == deleted_bytes+row['bytes'],
            'Journal cumulative deletion accounting differs')
    return event, outcome

def check_complete(event, files, size, expected_files=47429, expected_bytes=6565902818):
    require(event.get('event') == 'COMPLETE' and event.get('state') == 'PASS_EXACT_47429_COLD_LEAVES_REMOVED'
            and event.get('deleted') == files == expected_files and event.get('deleted_bytes') == size == expected_bytes
            and event.get('held_files') == 219 and event.get('unmatched_preserved') == 619
            and event.get('recursive_deletes') == 0, 'Terminal completion accounting differs')

class Owners:
    """Retain exact Windows kernel handles, rather than infer identity from reusable PIDs."""
    def __init__(self, pairs=OWNERS):
        self.k = ctypes.WinDLL('kernel32', use_last_error=True); self.handles=[]
        self.k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD]; self.k.OpenProcess.restype=W.HANDLE
        self.k.GetProcessTimes.argtypes=[W.HANDLE,*([ctypes.POINTER(W.FILETIME)]*4)]; self.k.GetProcessTimes.restype=W.BOOL
        self.k.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD]; self.k.WaitForSingleObject.restype=W.DWORD
        self.k.CloseHandle.argtypes=[W.HANDLE];self.k.CloseHandle.restype=W.BOOL
        try:
            for pid,birth in pairs:
                h=self.k.OpenProcess(0x100000|0x1000,False,pid)
                require(h,'Cannot retain exact process handle: '+str(pid));self.handles.append((h,pid,birth))
            self.check()
        except BaseException:self.close();raise
    def check(self):
        records=[]
        for h,pid,birth in self.handles:
            times=[W.FILETIME() for _ in range(4)]
            require(self.k.GetProcessTimes(h,*[ctypes.byref(t) for t in times]),'Cannot read process birth')
            actual=(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime
            require(actual==birth and self.k.WaitForSingleObject(h,0)==258,'Native/controller closed or birth differs')
            records.append({'pid':pid,'creation_filetime':str(actual),'alive':True,'retained_handle':True})
        return records
    def close(self):
        for h,_,_ in self.handles:self.k.CloseHandle(h)
        self.handles=[]

class Reads:
    def __init__(self, owners): self.owners=owners;self.started=time.monotonic();self.bytes=0;self.parents={}
    def guard(self):
        require(time.monotonic()-self.started<MAX_RUNTIME,'Bounded verifier deadline exceeded');self.owners.check()
    def plain_parents(self,path):
        for p in reversed(path.parents):
            if p in self.parents:continue
            s=p.lstat();require(stat.S_ISDIR(s.st_mode) and not s.st_file_attributes&stat.FILE_ATTRIBUTE_REPARSE_POINT,
                               'Missing/non-directory/reparse ancestor')
            require(p.absolute()==p.resolve(),'Ancestor alias')
            self.parents[p]=(s.st_dev,s.st_ino)
    def absent(self,path):
        self.plain_parents(path)
        try:path.lstat()
        except FileNotFoundError:return
        raise ValueError('Journalled removed candidate still exists: '+str(path))
    def retained(self,row, full=True):
        path=target(row);self.guard();self.plain_parents(path);before=path.lstat()
        require(stat.S_ISREG(before.st_mode) and not before.st_file_attributes&stat.FILE_ATTRIBUTE_REPARSE_POINT
                and signature(before)==expected_signature(row),'Retained original identity/metadata differs: '+str(path))
        if not full:return {'path':str(path),'metadata_equal':True,'full_sha':'NOT_READ_PARTIAL_STOP_REMAINDER'}
        h=hashlib.sha256();count=0
        with path.open('rb') as f:
            require(signature(os.fstat(f.fileno()))==signature(before),'Retained opened-file identity changed')
            for block in iter(lambda:f.read(1024**2),b''):
                self.bytes+=len(block);count+=len(block)
                require(self.bytes<=MAX_HASH_BYTES,'Retained-byte read budget exceeded');h.update(block)
                if count%(8*1024**2)<1024**2:self.guard()
            require(signature(os.fstat(f.fileno()))==signature(before),'Retained handle changed during full hash')
        require(signature(path.lstat())==signature(before) and count==row['bytes'] and h.hexdigest()==row['sha256'],
                'Retained original SHA/identity differs: '+str(path))
        return {'path':str(path),'bytes':count,'sha256':h.hexdigest(),'identity_equal':True}

def verify(journal_path,result):
    require(os.name=='nt' and os.environ.get('COMPUTERNAME','').casefold()=='wd','WD Windows verifier required')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentProcess.restype=W.HANDLE;kernel.SetPriorityClass.argtypes=[W.HANDLE,W.DWORD]
    require(kernel.SetPriorityClass(kernel.GetCurrentProcess(),0x4000),'Own below-normal priority request failed')
    for name,pin in PINS.items():require(digest(WORK/name)==pin,'Frozen post-purge control differs: '+name)
    published=json.loads((WORK/'master_batch03_purge_remote_readback.json').read_bytes())
    require(published['state']=='PASS_ALL_REMOTE_BYTES_SHA256_VERIFIED' and published['expected_commit']==COMMIT,
            'Published exact proposal readback missing')
    plan=json.loads((WORK/'master_batch03_leaf_purge_proposed.json').read_bytes())
    require(journal_path.absolute()==WORK/'master_batch03_leaf_purge_20261009_receipt.jsonl','Unexpected journal path')
    # First bounded scan requires an existing terminal record before any source payload reads.
    first=journal_path.lstat()
    require(stat.S_ISREG(first.st_mode) and first.st_nlink==1
            and not first.st_file_attributes&stat.FILE_ATTRIBUTE_REPARSE_POINT,'Journal nonregular/reparse/hardlink')
    tail=None;records=0;jh=hashlib.sha256()
    with journal_path.open('rb') as f:
        for line in f:jh.update(line);tail=json.loads(line);records+=1
    require(tail and tail.get('event') in ('COMPLETE','STOP'),'Journal is still running; no post-purge verification')
    require(signature(journal_path.stat())==signature(first),'Journal changed during terminal precheck')
    result.update(journal_sha256=jh.hexdigest(),journal_records=records,journal_terminal=tail)
    owners=Owners();reads=Reads(owners);result['owners_before']=owners.check()
    removed=removed_bytes=held=held_bytes=remaining=0;remaining_details=[];retained=[];stopped=None
    try:
        with zipfile.ZipFile(WORK/'master_batch03_mapping01/master_batch03_scientific_cache_mapping01.zip') as z, journal_path.open('rb') as jf:
            assessment=json.loads(z.read('control/conservative_leaf_assessment.json'));holds={r['path'].casefold() for r in assessment['files_preserved']}
            require(len(holds)==219,'Exact conservative holds changed')
            journal_count=0;journal_hash=hashlib.sha256()
            def next_event():
                nonlocal journal_count
                line=jf.readline();require(bool(line),'Unexpected journal EOF');journal_hash.update(line);journal_count+=1
                return json.loads(line)
            begin=next_event()
            require(begin.get('event')=='BEGIN' and begin.get('schema')=='MASTER_BATCH03_LEAF_APPEND_RECEIPT_V1'
                    and begin.get('plan_sha256')==PINS['master_batch03_leaf_purge_proposed.json']
                    and begin.get('proposal_commit')==COMMIT and begin.get('mapping_sha256')==MAP_SHA
                    and begin.get('recovery_receipt_sha256')==plan['recovery_receipt']['sha256'],'Journal BEGIN authority differs')
            mh=hashlib.sha256();n=total=0
            with z.open('mapping/batch03/file_allowlist.jsonl') as mapping:
                for line_number,line in enumerate(mapping,1):
                    mh.update(line);row=json.loads(line);path=target(row);n+=1;total+=row['bytes']
                    if row['path'].casefold() in holds:
                        retained.append(reads.retained(row));held+=1;held_bytes+=row['bytes'];continue
                    if stopped is None:
                        intent,outcome=join_candidate(next_event,row,line_number,removed,removed_bytes)
                        if outcome['event']=='STOP':stopped=outcome
                        else:
                            reads.absent(path);removed+=1;removed_bytes+=row['bytes']
                            if removed%5000==0:print(json.dumps({'phase':'REMOVAL_JOURNAL_AND_ABSENCE','verified':removed}),flush=True)
                            continue
                    # STOP preserves remainder; an unreceipted missing leaf is explicit uncertainty.
                    try:reads.retained(row,full=False)
                    except FileNotFoundError:remaining_details.append({'path':str(path),'state':'UNRECEIPTED_ABSENCE_REQUIRES_RECONCILIATION'})
                    remaining+=1
            require(mh.hexdigest()==MAP_SHA and (n,total,held,held_bytes)==(47648,6568632074,219,2729256),
                    'Actual mapped/hold accounting differs')
            terminal=stopped if stopped is not None else next_event()
            if terminal.get('event')=='COMPLETE':check_complete(terminal,removed,removed_bytes)
            else:require(terminal.get('event')=='STOP','Unexpected terminal event');stopped=terminal
            require(not jf.read(1) and journal_hash.hexdigest()==result['journal_sha256'] and journal_count==records,
                    'Journal trailing rows/change or missing ordered join')
            kh=hashlib.sha256();kept_count=kept_bytes=0
            with z.open('mapping/batch03/preserve_unmatched_or_excluded.jsonl') as keep:
                for line in keep:
                    kh.update(line);row=json.loads(line);retained.append(reads.retained(row));kept_count+=1;kept_bytes+=row['bytes']
                    if kept_count%100==0:print(json.dumps({'phase':'FULL_RETAINED_ORIGINAL_HASH','verified_unmatched':kept_count,'bytes_read':reads.bytes}),flush=True)
            require(kh.hexdigest()==KEEP_SHA and (kept_count,kept_bytes)==(619,981198193),'Unmatched original preservation accounting differs')
        require(signature(journal_path.stat())==signature(first),'Terminal journal changed during verification')
        protected=json.loads((WORK/'master_batch03_protected_before.json').read_bytes())['files'];require(len(protected)==12,'Protected exact12 set differs')
        protected_results=[]
        for row in protected:
            path=Path(row['path']);reads.guard();reads.plain_parents(path);before=path.lstat()
            require(stat.S_ISREG(before.st_mode) and not before.st_file_attributes&stat.FILE_ATTRIBUTE_REPARSE_POINT
                    and before.st_size==row['bytes'],'Protected file type/size differs')
            actual=digest(path);require(actual==row['sha256'] and signature(path.lstat())==signature(before),'Protected actual SHA/identity drift')
            protected_results.append({'path':str(path),'bytes':row['bytes'],'sha256':actual,'unchanged':True})
        for path,identity in reads.parents.items():
            current=path.lstat()
            require((current.st_dev,current.st_ino)==identity and stat.S_ISDIR(current.st_mode)
                    and not current.st_file_attributes&stat.FILE_ATTRIBUTE_REPARSE_POINT
                    and path.absolute()==path.resolve(),'Observed ancestor identity/reparse changed during verification')
        result.update(state='PASS_EXACT47429_REMOVED_838_ORIGINALS_AND12_PROTECTED_UNCHANGED' if stopped is None else 'PARTIAL_STOP_REMOVALS_VERIFIED_REMAINDER_REQUIRES_RECONCILIATION',
                      removed_files=removed,removed_bytes=removed_bytes,held_files=held,held_bytes=held_bytes,
                      unmatched_files=kept_count,unmatched_bytes=kept_bytes,retained_originals=retained,
                      protected_files=protected_results,owners_after=owners.check(),retained_original_bytes_hashed=reads.bytes,
                      remaining_after_stop=remaining,unreceipted_absences=remaining_details)
    finally:owners.close()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journal',type=Path,default=WORK/'master_batch03_leaf_purge_20261009_receipt.jsonl')
    args=parser.parse_args()
    require(os.name=='nt' and os.environ.get('COMPUTERNAME','').casefold()=='wd'
            and WORK==Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work').resolve(),
            'WD exact C-work verifier namespace required before creating any output')
    out=WORK/('master_batch03_postverify_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir()
    result={'schema':'MASTER_BATCH03_INDEPENDENT_POST_PURGE_VERIFY_V1','state':'IN_PROGRESS_READ_ONLY','started_utc':utc(),
            'verifier_sha256':digest(Path(__file__)),'control_pins':PINS,'source_deletions':0,'network_calls':0,'g_writes':0,
            'wsl_starts':0,'scientific_jobs':0,'deadline_seconds':MAX_RUNTIME,'maximum_retained_hash_bytes':MAX_HASH_BYTES}
    try:verify(args.journal,result)
    except BaseException as error:
        result.update(state='FAILED_POST_PURGE_VERIFY_NO_NEW_CLEANUP_AUTHORITY',error={'kind':type(error).__name__,'message':str(error)})
        raise
    finally:
        result['finished_utc']=utc()
        with (out/'receipt.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
        print(json.dumps({'state':result['state'],'receipt':str(out/'receipt.json')}),flush=True)

if __name__=='__main__':main()
