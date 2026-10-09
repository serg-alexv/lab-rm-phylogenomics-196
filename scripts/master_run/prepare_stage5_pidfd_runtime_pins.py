"""One C-only active-source pin refresh after the separately reviewed runner."""
from pathlib import Path
import argparse, hashlib, json, re

WORK=Path(__file__).resolve().parent
EXACT=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
OLD_RUNNER='2d7414fd33fe6216b95cfd549cee743d8b7057db698aced509f9a7ffefa77fc0'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runner-sha256',required=True)
    args=parser.parse_args();new=args.runner_sha256
    assert WORK==EXACT and re.fullmatch('[a-f0-9]{64}',new) and new!=OLD_RUNNER
    assert sha(WORK/'stage5_atomic.py')==new
    ledger=WORK/'stage5_pidfd_compat_pin_refresh.json'
    assert sha(ledger)=='60ea1033ce127c6875ec61d1b2e75fe577683c7dd1a2f356741920ccbc85fb55'
    changes=[]
    def update(name,expected,replacements):
        path=WORK/name;raw=path.read_bytes();assert sha(path)==expected
        original=path.with_name(path.stem+'_after_pidfd_before_runtime_sha.py')
        assert not original.exists();original.write_bytes(raw)
        transformed=raw
        for before,after in replacements:
            assert before!=after and before.encode() in transformed
            transformed=transformed.replace(before.encode(),after.encode())
        path.write_bytes(transformed)
        changes.append({'path':name,'original':original.name,'before_sha256':expected,
                        'after_sha256':sha(path),'replacements':dict(replacements)})
        return sha(path)
    discovery=update('stage5_runtime_discovery.py','bddfe32251f095c9be3e091287a574f248a51b19861a74c3ce1cf0b508a9269a',[(OLD_RUNNER,new)])
    linux=update('stage5_setup_linux.py','746202253f486f8cc7f1a4a164368e677223087d2cddf1c98a21350a64efb94f',
                 [('bddfe32251f095c9be3e091287a574f248a51b19861a74c3ce1cf0b508a9269a',discovery)])
    windows=update('stage5_setup_windows.py','f0522a1e8197139e0116d1b9f84aef1f525a8f1e0e8c50e90902ab6e82341cc0',
                   [('bddfe32251f095c9be3e091287a574f248a51b19861a74c3ce1cf0b508a9269a',discovery)])
    archive=update('stage5_closed_genome_archive_linux.py','314bfba257089afe108d1032b7a2136b4040aee30344484b7ddaf2941592a60b',[(OLD_RUNNER,new)])
    update('stage5_closed_genome_archive_windows.py','830d7c1e14ebea599c4e2b456aa11292338327482c18fe155aeba5667278974e',
           [(OLD_RUNNER,new),('f0522a1e8197139e0116d1b9f84aef1f525a8f1e0e8c50e90902ab6e82341cc0',windows),
            ('314bfba257089afe108d1032b7a2136b4040aee30344484b7ddaf2941592a60b',archive)])
    update('stage5_build_actual_config.py','c5b84a4ad45682db5b3b1fd43f0138db2a9c4bc60b2f4105db0271f348757393',
           [(OLD_RUNNER,new),('746202253f486f8cc7f1a4a164368e677223087d2cddf1c98a21350a64efb94f',linux),
            ('f0522a1e8197139e0116d1b9f84aef1f525a8f1e0e8c50e90902ab6e82341cc0',windows)])
    path=WORK/'stage5_pidfd_runtime_pin_refresh.json';assert not path.exists()
    path.write_text(json.dumps({'schema':'STAGE05_PIDFD_RUNTIME_ACTIVE_PIN_REFRESH_V1','changes':changes,
        'runner_sha256':new,'previous_pidfd_ledger_sha256':sha(ledger),
        'actual_execution':'NOT_RUN','historical_receipts_modified':False},indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(changes,indent=2))


if __name__=='__main__':main()
