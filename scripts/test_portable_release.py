"""Synthetic archive tests, including checksum coverage and deterministic bytes."""
from pathlib import Path
import json,tempfile,zipfile
from portable_release import make_zip,verify_zip,validate_member_names

def main():
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp);source=p/'source.txt';source.write_bytes(b'Portable UTF-8 source\n')
        a=make_zip(p/'a.zip',[(source,'payload/source.txt')],'Guide\n')
        source.touch()
        b=make_zip(p/'b.zip',[(source,'payload/source.txt')],'Guide\n')
        assert a['sha256']==b['sha256'],'Archive depends on source mtime'
        rejected=[]
        for mode in ('unhashed_member','unsafe_name','wrong_hash','duplicate_member'):
            bad=p/(mode+'.zip')
            with zipfile.ZipFile(bad,'w') as z:
                z.writestr('README.txt','x')
                z.writestr('SHA256SUMS.txt',('0'*64+'  README.txt\n') if mode=='wrong_hash' else '2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881  README.txt\n')
                if mode=='unhashed_member':z.writestr('extra.txt','x')
                if mode=='unsafe_name':z.writestr('../outside.txt','x')
                if mode=='duplicate_member':z.writestr('README.txt','x')
            try:verify_zip(bad)
            except (ValueError,KeyError):rejected.append(mode)
            else:raise AssertionError('Accepted malformed archive: '+mode)
        path_cases={'case_alias':['README.txt','readme.txt'],
                    'directory_case_alias':['Tables/one.txt','tables/two.txt'],
                    'trailing_dot':['table.'],'trailing_space':['table '],
                    'reserved_device':['data/CON.txt'],'wildcard':['data/*.txt'],
                    'file_directory_alias':['data/file','data/file/child.txt'],
                    'backslash':['data\\file.txt'],'normalized_slash_alias':['data//file.txt']}
        for label,names in path_cases.items():
            try:validate_member_names(names)
            except ValueError:rejected.append(label)
            else:raise AssertionError('Invalid Windows paths accepted: '+label)
    print(json.dumps({'status':'PASS_SYNTHETIC_ARCHIVE_TESTS','deterministic_after_source_mtime_change':True,'rejected':rejected},indent=2))

if __name__=='__main__':main()
