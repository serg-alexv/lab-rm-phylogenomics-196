"""Short synthetic process tree only; no biological inputs or tools."""
import argparse, os, subprocess, time
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S

def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);p.add_argument('--grandchild',action='store_true');a=p.parse_args()
    directory=Path(a.runtime);C.check(directory.is_relative_to(S.RUNTIME),'Fixture C runtime required')
    if a.grandchild:
        time.sleep(112);return
    child=subprocess.Popen([str(S.PYTHON),str(Path(__file__).resolve()),'--runtime',str(directory),'--grandchild'],creationflags=0x08000000)
    C.atomic(directory/'fixture_grandchild.json',S.process_identity(child.pid))
    start=time.monotonic();tick=0
    while time.monotonic()-start<120:
        tick+=1;C.atomic(directory/'fixture_ticks.json',{'utc':C.now(),'tick':tick,'pid':os.getpid(),'wall_seconds':time.monotonic()-start})
        time.sleep(2)
    C.check(child.wait(timeout=5)==0,'Fixture grandchild failed')
    C.atomic(directory/'fixture_child_complete.json',{'utc':C.now(),'status':'SYNTHETIC_CHILD_AND_GRANDCHILD_EXIT0','ticks':tick})

if __name__=='__main__':main()
