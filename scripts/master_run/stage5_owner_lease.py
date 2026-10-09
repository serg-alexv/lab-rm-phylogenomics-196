"""Write only owned C owner_lease.json; bounded retries only for its os.replace."""
from pathlib import Path
import json, os, stat, tempfile, time

WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
RETRY_SECONDS=0.250
TRANSIENT_WINERRORS={5,32,33}


class LeaseReplaceDeadlineExceeded(TimeoutError):
    pass


def _replace_owned(temporary,target,stats,replace=os.replace,clock=time.monotonic,sleep=time.sleep):
    """Pure retry contract. Caller created and closed this exact temporary."""
    started=clock();deadline=started+RETRY_SECONDS;attempts=0;retries=0;delay=0.005;last=None
    stats.setdefault('retries',0);stats.setdefault('transient_failures',0);stats.setdefault('transient_winerrors',{})
    try:
        while True:
            if attempts and clock()>=deadline:
                raise LeaseReplaceDeadlineExceeded('Owned C lease replace retry budget250ms expired') from last
            if attempts:
                retries+=1;stats['retries']+=1
            attempts+=1
            try:
                replace(temporary,target)
                return
            except OSError as error:
                code=getattr(error,'winerror',None)
                if code not in TRANSIENT_WINERRORS:raise
                last=error;stats['transient_failures']=stats.get('transient_failures',0)+1
                counts=stats.setdefault('transient_winerrors',{});counts[str(code)]=counts.get(str(code),0)+1
                remaining=deadline-clock()
                if remaining<=0:
                    raise LeaseReplaceDeadlineExceeded('Owned C lease replace retry budget250ms expired') from error
                sleep(min(delay,remaining));delay=min(delay*2,0.050)
    finally:
        stats['last_replace_attempts']=attempts;stats['last_replace_retries']=retries
        elapsed=clock()-started;stats['last_replace_seconds']=elapsed
        stats['maximum_replace_seconds']=max(stats.get('maximum_replace_seconds',0),elapsed)


def atomic_owner_lease(path,value,stats):
    """No retry for creation, writing, fsync, validation or any other file."""
    path=Path(path)
    if not (os.name=='nt' and path.is_absolute() and path==path.resolve() and WORK in path.parents
            and path.name=='owner_lease.json' and value.get('schema')=='STAGE05_WINDOWS_OWNER_LEASE_V1'):
        raise ValueError('Only exact current C owned lease writes are permitted')
    for item in (path.parent,*path.parent.parents):
        info=item.lstat()
        if item.is_symlink() or getattr(info,'st_file_attributes',0)&0x400:
            raise ValueError('Owned C lease ancestor alias/reparse forbidden')
    if path.exists():
        info=path.lstat()
        if path.is_symlink() or not stat.S_ISREG(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
            raise ValueError('Owned C lease target must be regular and non-reparse')
    if not isinstance(stats,dict):raise ValueError('Owned lease retry stats must be a mutable receipt dictionary')
    stats.setdefault('schema','STAGE05_OWNED_C_LEASE_REPLACE_STATS_V1');stats['calls']=stats.get('calls',0)+1
    temporary=None
    try:
        descriptor,name=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent);temporary=Path(name)
        with os.fdopen(descriptor,'w',encoding='utf-8',newline='\n') as stream:
            json.dump(value,stream,indent=2,ensure_ascii=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        _replace_owned(temporary,path,stats)
        stats['successful_calls']=stats.get('successful_calls',0)+1
    except BaseException as error:
        stats['failed_calls']=stats.get('failed_calls',0)+1
        stats['last_failure']={'kind':type(error).__name__,'message':str(error),'winerror':getattr(error,'winerror',None)}
        raise
    finally:
        # Only this invocation's exclusive-create temporary; never the lease.
        if temporary is not None and temporary.exists():temporary.unlink()
