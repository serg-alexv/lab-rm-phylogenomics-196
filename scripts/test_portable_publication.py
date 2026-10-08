#!/usr/bin/env python3
"""Independent small publication mocks. No Git/GitHub/network invocation permitted."""
from __future__ import annotations
import argparse
from collections import Counter
from contextlib import redirect_stdout,redirect_stderr
from datetime import datetime,timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import runpy
import sys
import tempfile
import types
from unittest.mock import patch
import zipfile


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Harness:
    def __init__(self,root,source):
        self.root=root;root.mkdir(parents=True,exist_ok=True)
        self.staging=root/'release_staging';self.staging.mkdir()
        (root/'reports/mock').mkdir(parents=True);(root/'status').mkdir()
        self.manifest=root/'reports/mock/assets.json';self.notes=root/'reports/mock/NOTES.md'
        self.notes.write_text('Synthetic test only\n',encoding='utf-8')
        self.commit_counter=0;self.current_head=None;self.trees={};self.remote_plan=False
        self.release_present=False;self.release_head=None;self.remote={};self.next_id=100
        self.uploads=Counter();self.downloads=Counter();self.commits=[]
        self.crash_after_upload=None;self.fail_before_upload=None;self.fail_plan_commit=False
        self.w=types.ModuleType('production_resume');self.w.R=root;self.w.REPO='synthetic/mock-repository'
        self.w.digest=digest;self.w.now=lambda:'2026-10-08T00:00:00+00:00'
        self.w.atomic=self.atomic;self.w.js=lambda path,value:self.atomic(path,(json.dumps(value,indent=2)+'\n').encode())
        self.w.run=self.run
        publication=types.ModuleType('workflow_publication');publication.commit=self.commit
        with patch.dict(sys.modules,{'production_resume':self.w,'workflow_publication':publication}):
            spec=importlib.util.spec_from_file_location('isolated_portable_release',source)
            self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
        payload=root/'payload.txt';payload.write_text('Synthetic portable payload\n',encoding='utf-8')
        asset=self.module.make_zip(self.staging/'mock-payload.zip',[(payload,'tables/payload.txt')],'Synthetic fixture only\n')
        self.manifest.write_text(json.dumps({'assets':[asset]},indent=2)+'\n',encoding='utf-8')
        self.original_manifest=self.manifest.read_bytes();self.local_digest=asset['sha256'];self.asset=asset

    def atomic(self,path,value):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value)

    def commit(self,paths,message):
        self.commits.append({'paths':paths,'message':message})
        if self.fail_plan_commit and message.startswith('Record '):
            self.fail_plan_commit=False;raise RuntimeError('Synthetic plan commit/push interrupted')
        self.commit_counter+=1;self.current_head=str(self.commit_counter)*40
        self.trees[self.current_head]=self.manifest.read_bytes()
        if message.startswith(('Record ','Verify ')):self.remote_plan=True
        return self.current_head

    def advance_main(self):
        self.commit_counter+=1;self.current_head=str(self.commit_counter)*40
        self.trees[self.current_head]=self.manifest.read_bytes()

    def view(self,argv,**kwargs):
        assert argv[:3]==['gh','release','view'],'Unexpected subprocess/network invocation in mock'
        return subprocess.CompletedProcess(argv,0 if self.release_present else 1,stdout=b'',stderr=b'')

    def run(self,argv,**kwargs):
        if argv[:2]==['git','show']:
            head,path=argv[2].split(':',1)
            assert path=='reports/mock/assets.json'
            return self.trees[head].decode('utf-8')
        assert argv[0]=='gh','Unexpected real tool invocation in isolated mock'
        if argv[1:3]==['release','create']:
            assert not self.release_present
            self.release_present=True;self.release_head=argv[argv.index('--target')+1]
            return ''
        if argv[1]=='api' and '/commits/' in argv[2]:return self.release_head+'\n'
        if argv[1]=='api' and '/releases/tags/' in argv[2]:
            return json.dumps({'id':1,'html_url':'https://example.invalid/synthetic-release',
                               'assets':[{k:v for k,v in value.items() if k!='bytes'} for value in self.remote.values()]})
        if argv[1:3]==['release','upload']:
            file=Path(argv[4]);name=file.name;self.uploads[name]+=1
            if self.fail_before_upload==name:
                self.fail_before_upload=None;raise RuntimeError('Synthetic upload interrupted before bytes accepted')
            assert name not in self.remote,'Mock rejects attempted overwrite of existing remote asset'
            self.next_id+=1
            self.remote[name]={'name':name,'id':self.next_id,'size':file.stat().st_size,'digest':'sha256:'+digest(file),
                               'state':'uploaded','bytes':file.read_bytes()}
            if self.crash_after_upload==name:
                self.crash_after_upload=None;raise RuntimeError('Synthetic upload accepted but acknowledgement lost')
            return ''
        if argv[1:3]==['release','download']:
            name=argv[argv.index('--pattern')+1];directory=Path(argv[argv.index('--dir')+1])
            self.downloads[name]+=1;directory.mkdir(parents=True,exist_ok=True)
            (directory/name).write_bytes(self.remote[name]['bytes']);return ''
        raise AssertionError('Unexpected mock command: '+str(argv))

    def publish(self):
        # Only the metadata existence query uses subprocess in current producer.
        with patch.object(self.module.subprocess,'run',self.view):
            return self.module.publish_frozen('mock','stage-mock-v1',self.staging,self.manifest,
                    ['reports/mock/assets.json','reports/mock/NOTES.md'],'Synthetic test',self.notes)


def archive_fixture(path,names):
    manifest=[]
    with zipfile.ZipFile(path,'w') as archive:
        for name in names:
            data=b'Synthetic byte\n';archive.writestr(name,data)
            manifest.append(hashlib.sha256(data).hexdigest()+'  '+name+'\n')
        archive.writestr('SHA256SUMS.txt',''.join(manifest))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path('scripts/portable_release.py'))
    parser.add_argument('--output-dir',type=Path,default=Path('.work/review2/publication_review'))
    args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    snapshot=args.output_dir/'portable_release_snapshot.py';snapshot.write_bytes(args.source.read_bytes())
    tests=[];findings=[]
    with tempfile.TemporaryDirectory(prefix='publication_mock_',dir=args.output_dir) as folder:
        base=Path(folder)
        h=Harness(base/'normal',snapshot);receipt=h.publish()
        assert receipt['status']=='UPLOAD_VERIFIED' and receipt['payload_commit']==h.release_head=='1'*40
        assert h.uploads=={'mock-payload.zip':1,'mock-payload.zip.sha256':1} and h.downloads==h.uploads
        assert h.remote_plan and h.original_manifest==h.manifest.read_bytes()
        tests.append({'case':'normal_ZIP_and_sidecar_independent_upload_readback','observed':'PASS'})
        h=Harness(base/'lost_ack',snapshot);h.crash_after_upload='mock-payload.zip'
        try:h.publish()
        except RuntimeError:pass
        else:raise AssertionError('Interruption not exercised')
        h.advance_main();receipt=h.publish()
        assert receipt['payload_commit']==h.release_head=='1'*40 and h.current_head!=receipt['payload_commit']
        assert h.uploads=={'mock-payload.zip':1,'mock-payload.zip.sha256':1}
        assert h.downloads=={'mock-payload.zip':1,'mock-payload.zip.sha256':1}
        assert h.original_manifest==h.manifest.read_bytes()
        tests.append({'case':'lost_upload_ack_retry_reuses_existing_asset_and_original_payload_commit','observed':'PASS'})
        h=Harness(base/'sidecar_retry',snapshot);h.fail_before_upload='mock-payload.zip.sha256'
        try:h.publish()
        except RuntimeError:pass
        else:raise AssertionError('Sidecar interruption not exercised')
        h.advance_main();receipt=h.publish()
        assert receipt['payload_commit']=='1'*40 and h.uploads['mock-payload.zip']==1
        assert h.uploads['mock-payload.zip.sha256']==2 and h.downloads['mock-payload.zip.sha256']==1
        assert h.downloads['mock-payload.zip'] in (1,2),'Retry cached readback must be verified or fetched again'
        tests.append({'case':'ZIP_verified_sidecar_pending_retry_independent','observed':'PASS','zip_download_count':h.downloads['mock-payload.zip']})
        for mode in ('remote_wrong_size','remote_wrong_digest','remote_wrong_bytes_digest_absent','remote_wrong_sidecar'):
            h=Harness(base/mode,snapshot);h.publish();h.uploads.clear();h.downloads.clear()
            name='mock-payload.zip.sha256' if mode=='remote_wrong_sidecar' else 'mock-payload.zip'
            remote=h.remote[name]
            if mode=='remote_wrong_size':remote['size']+=1
            elif mode=='remote_wrong_digest':remote['digest']='sha256:'+'0'*64
            else:
                value=remote['bytes'];remote['bytes']=bytes([value[0]^1])+value[1:];remote['digest']=None
                remote['id']+=1000 # Replacement remote identity cannot reuse an old verified readback.
            try:h.publish()
            except ValueError:pass
            else:raise AssertionError('Remote mismatch silently accepted: '+mode)
            assert not h.uploads,'Remote mismatch attempted overwrite'
            tests.append({'case':mode,'observed':'REJECTED_WITHOUT_OVERWRITE'})
        for mode in ('remote_same_bytes_new_id','remote_digest_missing_correct_bytes','cached_readback_corrupted','cached_sidecar_missing'):
            h=Harness(base/mode,snapshot);h.publish();h.uploads.clear();h.downloads.clear()
            name='mock-payload.zip.sha256' if mode=='cached_sidecar_missing' else 'mock-payload.zip'
            if mode=='remote_same_bytes_new_id':h.remote[name]['id']+=1000
            elif mode=='remote_digest_missing_correct_bytes':h.remote[name]['digest']=None
            elif mode=='cached_readback_corrupted':
                cached=h.staging/'readback'/name;value=cached.read_bytes();cached.write_bytes(bytes([value[0]^1])+value[1:])
            else:(h.staging/'readback'/name).unlink()
            h.publish()
            assert h.downloads[name]==1 and not h.uploads,'Changed/missing cache was not independently fetched'
            tests.append({'case':mode,'observed':'PASS_FORCED_FRESH_READBACK'})
        h=Harness(base/'stale_progress_complete',snapshot);h.publish();h.uploads.clear();h.downloads.clear()
        h.remote['mock-payload.zip.sha256']['id']+=1000
        h.remote['mock-payload.zip.sha256']['digest']='sha256:'+'0'*64
        try:h.publish()
        except ValueError:pass
        else:raise AssertionError('Wrong replacement sidecar accepted')
        progress=json.loads((h.root/'reports/mock/publication_progress.json').read_text())
        if progress.get('complete'):
            findings.append({'case':'stale_progress_complete_after_sidecar_replacement',
                             'observed':'COMPLETE_TRUE_AFTER_CURRENT_SIDECAR_RECHECK_FAILED',
                             'fix':'Compute current verified count/completion from assets rechecked in this attempt, separately from historical reuse cache.'})
        else:tests.append({'case':'stale_progress_complete_after_sidecar_replacement','observed':'PASS_CURRENT_COMPLETION_FALSE'})
        h=Harness(base/'unexpected_cached_entry',snapshot);h.publish()
        progress_path=h.root/'reports/mock/publication_progress.json';progress=json.loads(progress_path.read_text())
        progress['verified_assets']['not-required.zip']={'remote_asset_id':99999,'sha256':'0'*64,'bytes':0,'download_readback_verified':True}
        progress_path.write_text(json.dumps(progress),encoding='utf-8');h.publish();progress=json.loads(progress_path.read_text())
        if progress.get('verified_files')!=2 or progress.get('complete') is not True:
            findings.append({'case':'unexpected_cached_asset_affects_completion',
                             'observed':{'verified_files':progress.get('verified_files'),'complete':progress.get('complete'),'required_files':2},
                             'fix':'Exclude unrelated/unvalidated historical cache entries from current publication progress.'})
        else:tests.append({'case':'unexpected_cached_entry','observed':'PASS_CURRENT_PROGRESS_EXACT_REQUIRED_SET'})
        h=Harness(base/'changed_payload',snapshot);h.publish();h.uploads.clear();h.downloads.clear()
        path=h.staging/'mock-payload.zip';old=path.read_bytes();path.write_bytes(old+b'changed')
        try:h.publish()
        except ValueError:pass
        else:raise AssertionError('Changed frozen local ZIP accepted')
        assert not h.uploads and not h.downloads
        tests.append({'case':'local_frozen_ZIP_changed','observed':'REJECTED_BEFORE_REMOTE_MUTATION'})
        h=Harness(base/'changed_manifest',snapshot);h.publish()
        h.manifest.write_bytes(h.original_manifest+b' ')
        try:h.publish()
        except ValueError:pass
        else:raise AssertionError('Changed frozen manifest accepted')
        tests.append({'case':'immutable_manifest_bytes_changed','observed':'REJECTED'})
        h=Harness(base/'unsafe_asset_path',snapshot)
        outside=h.root/'outside.zip';outside.write_bytes((h.staging/'mock-payload.zip').read_bytes())
        value=json.loads(h.manifest.read_text());value['assets'][0]['asset_name']='../outside.zip'
        h.manifest.write_text(json.dumps(value),encoding='utf-8')
        try:h.publish()
        except ValueError:tests.append({'case':'release_asset_outside_staging','observed':'REJECTED'})
        else:findings.append({'case':'release_asset_outside_staging','observed':'UPLOAD_VERIFIED_FOR_PARENT_PATH_ASSET',
                            'fix':'Require asset_name to be one safe basename ending .zip before joining staging.'})
        h=Harness(base/'duplicate_manifest_assets',snapshot)
        value=json.loads(h.manifest.read_text());value['assets'].append(dict(value['assets'][0]))
        h.manifest.write_text(json.dumps(value),encoding='utf-8')
        try:h.publish()
        except ValueError:tests.append({'case':'duplicate_manifest_asset_names','observed':'REJECTED'})
        else:findings.append({'case':'duplicate_manifest_asset_names','observed':'UPLOAD_VERIFIED_DUPLICATE_DECLARED_ASSET',
                            'fix':'Require unique nonempty asset basenames and exact expected ZIP member count.'})
        h=Harness(base/'wrong_manifest_member_count',snapshot)
        value=json.loads(h.manifest.read_text());value['assets'][0]['payload_members']+=1
        h.manifest.write_text(json.dumps(value),encoding='utf-8')
        try:h.publish()
        except ValueError:tests.append({'case':'manifest_ZIP_member_count_mismatch','observed':'REJECTED'})
        else:findings.append({'case':'manifest_ZIP_member_count_mismatch','observed':'UPLOAD_VERIFIED_WRONG_DECLARED_ZIP_MEMBERS',
                            'fix':'Compare verify_zip return count against immutable asset payload_members.'})
        h=Harness(base/'plan_commit_interrupted',snapshot);h.fail_plan_commit=True
        try:h.publish()
        except RuntimeError:pass
        else:raise AssertionError('Plan commit failure not exercised')
        receipt=h.publish()
        if not h.remote_plan:
            findings.append({'case':'plan_commit_interrupted_retry','observed':'UPLOAD_VERIFIED_WITHOUT_REPUBLISHING_RESTART_PLAN',
                             'fix':'On existing-plan resume, ensure the plan itself is committed/pushed while preserving its original payload_commit.'})
        else:tests.append({'case':'plan_commit_interrupted_retry','observed':'PASS_PLAN_REPUBLISHED'})
        checker=h.module.verify_zip
        unsafe=[('case_collision',['README.txt','readme.txt']),('trailing_dot',['README.txt','tables/data.']),
                ('trailing_space',['README.txt','tables/data ']),('reserved_device',['README.txt','tables/CON.txt']),
                ('windows_wildcard',['README.txt','tables/data?.txt']),('file_directory_collision',['README.txt','tables','tables/data.txt']),
                ('semantic_dot_alias',['README.txt','tables/data.txt','tables/./data.txt']),
                ('component_case_collision',['README.txt','Tables/one.txt','tables/two.txt'])]
        for case,names in unsafe:
            file=base/(case+'.zip');archive_fixture(file,names)
            try:checker(file)
            except (ValueError,KeyError):tests.append({'case':'archive_'+case,'observed':'REJECTED'})
            else:findings.append({'case':'archive_'+case,'observed':'ACCEPTED_NONPORTABLE_WINDOWS_ARCHIVE',
                                 'fix':'Validate canonical member path components, reserved Windows names and case-insensitive file/directory collisions.'})
        original_test=args.source.parent/'test_portable_release.py'
        original_results=None
        if original_test.is_file():
            captured=io.StringIO();warnings=io.StringIO()
            with patch.dict(sys.modules,{'portable_release':h.module}),patch.object(tempfile,'tempdir',str(base)),redirect_stdout(captured),redirect_stderr(warnings):
                runpy.run_path(str(original_test),run_name='__main__')
            original_results=json.loads(captured.getvalue())
            assert original_results['status']=='PASS_SYNTHETIC_ARCHIVE_TESTS'
            tests.append({'case':'original_test_portable_release_under_isolated_dependency_stubs',
                          'observed':'PASS','negative_cases':len(original_results['rejected']),'source_sha256':digest(original_test)})
    report={'status':'REVIEW_FOUND_ACTIONABLE_BUGS' if findings else 'PASS_INDEPENDENT_PUBLICATION_MOCKS',
            'completed_at_utc':datetime.now(timezone.utc).isoformat(),
            'source_sha256':digest(snapshot),'network_execution':'NOT_RUN','git_execution':'NOT_RUN',
            'biological_execution':'NOT_RUN','tests':tests,'findings':findings}
    (args.output_dir/'publication_review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    summary=(f'Independent portable publication review: {report["status"]}. {len(tests)} checks passed; {len(findings)} actionable findings remain. '
             'All Git/GitHub operations were replaced with local mocks; no network, repository mutation or biological computation ran.\n\n'
             'Checks cover lost upload acknowledgement, original payload commit across later main commits, independently resumed ZIP and SHA sidecar, '
             'cached bytes/remote ID/hash verification, replacement or missing-digest assets, corrupted cache, incomplete-current progress, '
             'manifest immutability, unpublished-plan recovery, complete member hashes and Windows extraction paths.\n\n'
             'Source SHA256: `'+report['source_sha256']+'`. Command: `python .work/review2/test_publication_retry_review.py`.\n')
    if findings:summary+='\nRemaining findings: '+', '.join(item['case'] for item in findings)+'.\n'
    (args.output_dir/'publication_review.md').write_text(summary,encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
