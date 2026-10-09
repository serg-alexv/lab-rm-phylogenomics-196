"""One fixed C-work source pin refresh; never touches receipts or runs Linux."""
from pathlib import Path
import hashlib, json

WORK=Path(__file__).resolve().parent
EXACT=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
OLD='fdcc8d3b4337209b64ffa3732a8182bf832f2fa05d1e95fcdfb32964d4ad4a34'
NEW='e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert WORK==EXACT and sha(WORK/'stage5_atomic_process.py')==NEW
    changes=[]
    def update(name,expected,replacements):
        path=WORK/name;raw=path.read_bytes();assert sha(path)==expected
        original=path.with_name(path.stem+'_before_pidfd_compat.py')
        assert not original.exists();original.write_bytes(raw)
        transformed=raw
        for before,after in replacements:
            assert before!=after and before.encode() in transformed
            transformed=transformed.replace(before.encode(),after.encode())
        path.write_bytes(transformed)
        changes.append({'path':name,'original':original.name,'before_sha256':expected,
                        'after_sha256':sha(path),'replacements':dict(replacements)})
        return sha(path)
    unc=update('stage5_unc_bind_probe.py','70bbd9b0ae04ad90f3b1595d49d844ba899b93aefad6d2edf37ec675a99c9830',[(OLD,NEW)])
    discovery=update('stage5_runtime_discovery.py','32e85b6f0d58d7e2ce4d92b8aab74d103ff64fa7a08928299363f30fd04be6ad',[(OLD,NEW)])
    linux=update('stage5_setup_linux.py','7c50648cb3d32f4c372a933815f10c385774038aab8f8ea324d49de6c264d2e6',
                 [(OLD,NEW),('32e85b6f0d58d7e2ce4d92b8aab74d103ff64fa7a08928299363f30fd04be6ad',discovery)])
    windows=update('stage5_setup_windows.py','cc49de69a7c0c0701eb484d80fe048479b42a11086ab39a475d61de499eafda2',
                   [(OLD,NEW),('32e85b6f0d58d7e2ce4d92b8aab74d103ff64fa7a08928299363f30fd04be6ad',discovery),
                    ('70bbd9b0ae04ad90f3b1595d49d844ba899b93aefad6d2edf37ec675a99c9830',unc)])
    archive=update('stage5_closed_genome_archive_linux.py','1ecd31137703469e073d3815f834d8f1b5dc8059c2d285bbfdba2fd773d291c8',[(OLD,NEW)])
    update('stage5_closed_genome_archive_windows.py','8655e5646ed37b1436f0c95c0e8bedf5d07ed1175085871d464b7876fe23ef29',
           [(OLD,NEW),('cc49de69a7c0c0701eb484d80fe048479b42a11086ab39a475d61de499eafda2',windows),
            ('1ecd31137703469e073d3815f834d8f1b5dc8059c2d285bbfdba2fd773d291c8',archive)])
    update('stage5_build_actual_config.py','482800bf5bd15f7e87234e9448ac9c165df67f768af408305a6e7ee56f897cb1',
           [(OLD,NEW),('cc49de69a7c0c0701eb484d80fe048479b42a11086ab39a475d61de499eafda2',windows),
            ('7c50648cb3d32f4c372a933815f10c385774038aab8f8ea324d49de6c264d2e6',linux),
            ('70bbd9b0ae04ad90f3b1595d49d844ba899b93aefad6d2edf37ec675a99c9830',unc)])
    path=WORK/'stage5_pidfd_compat_pin_refresh.json';assert not path.exists()
    path.write_text(json.dumps({'schema':'STAGE05_PIDFD_COMPAT_ACTIVE_PIN_REFRESH_V1','changes':changes,
        'unchanged_dynamic_consumers':['stage5_atomic.py','stage5_windows_owner.py','stage5_interop_smoke_windows.py',
                                       'stage5_interop_linux_fixture.py','stage5_closed_genome_recovery.py'],
        'actual_execution':'NOT_RUN','historical_receipts_modified':False},indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(changes,indent=2))


if __name__=='__main__':main()
