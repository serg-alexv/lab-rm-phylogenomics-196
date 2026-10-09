"""Bounded pure metadata/in-memory fixtures; no Linux, shard or tree restore."""
from pathlib import Path
from unittest import mock
import copy, ctypes, datetime as dt, hashlib, json, sqlite3, tarfile, tempfile, types, unittest
import stage5_runtime_safe_extract as E

C,R,T=E.helpers()


def raw(value):return (json.dumps(value,sort_keys=True)+'\n').encode()


def fixture():
    controls={key:hashlib.sha256(key.encode()).hexdigest() for key in E.CONTROL_ORDER}
    index=dict(schema='STAGE05_RUNTIME_LOGICAL_ARCHIVE_INDEX_V1',roots=C.ROOTS,maximum_asset_bytes=C.SHARD_LIMIT,
        source_sha256=E.CAPTURE_SHA,installed_build_equivalence='NOT_ESTABLISHED',cleanup_authority=False,
        shards=[dict(name='stage5-installed-runtime-01.part0001',bytes=1,sha256=E.digest(b'x'))],
        compressed_bytes=1,compressed_stream_sha256=E.digest(b'x'),uncompressed_tar_bytes=10240,
        entry_count=3,regular_bytes=0,control_sha256=controls)
    index_raw=raw(index);plan=E.remote_plan(index_raw,'a'*40,'SYNTHETIC_ONLY','b'*40)
    payload=dict(state='PASS_LOCAL_FULL_RUNTIME_PAYLOAD_AND_POSIX_MANIFEST_FRESH_REMOTE_NOT_PROVEN',
        dataset_kind='SYNTHETIC',index_sha256=E.digest(index_raw),compressed_stream_sha256=index['compressed_stream_sha256'],
        shards=1,entry_count=3,all_regular_file_sha_verified=True,all_control_sha_verified=True,
        all_gzip_crc_verified=True,complete_internal_symlink_graph_verified=True,extraction=False,
        installed_build_equivalence='NOT_ESTABLISHED')
    payload_raw=raw(payload);now=dt.datetime(2026,10,10,tzinfo=dt.timezone.utc)
    remote={key:plan[key] for key in ('repository','source_commit','release_tag','tag_target_commit','index_sha256',
                                    'capture_control_sha256','helper_source_sha256')}
    assets=[dict(id=i+1,**item) for i,item in enumerate(plan['assets'])]
    inputs=dict(schema='STAGE05_INSTALLED_RUNTIME_CAPTURE_INPUTS_V1',state='REVIEWED_COLD_CAPTURE_READY',
        roots=C.ROOTS,original_prefix_required=True,all_required_runtime_files_public_and_covered=True,
        all_special_metadata_resolved=True,installed_build_equivalence='NOT_ESTABLISHED',
        complete_inventory_sha256=controls['manifest'],actual_runtime_manifest_sha256=controls['runtime'],
        whole_file_public_review_sha256=controls['public_review'],cold_exclusive_capture_receipt_sha256=controls['cold_proof'],
        license_source_notice_review_sha256=controls['notices'],published_capture_source_sha256=E.CAPTURE_SHA)
    remote.update(schema='STAGE05_INSTALLED_RUNTIME_FRESH_REMOTE_RECOVERY_V1',dataset_kind='SYNTHETIC',
        state='PASS_SYNTHETIC_REMOTE_GATE_CONTRACT',accepted_remote=False,remote_verifier_source_sha256='c'*64,
        independent_payload_receipt_sha256=E.digest(payload_raw),all_git_control_bytes_verified=True,
        all_asset_bytes_verified=True,all_sidecars_exact=True,asset_metadata_stable_before_after=True,
        owned_download_clients_closed=True,fresh_unique_download_namespace=True,assets_before=assets,
        assets_after=copy.deepcopy(assets),verified_at_utc=now.isoformat(),capture_inputs=inputs)
    return index_raw,remote,payload_raw,now


def gate(index_raw,remote,payload_raw,now,**kwargs):
    remote_raw=raw(remote)
    return E.remote_gate(index_raw,remote_raw,E.digest(remote_raw),payload_raw,E.digest(payload_raw),
                         'a'*40,'SYNTHETIC_ONLY','b'*40,'c'*64,now=now,synthetic=True,**kwargs)


def node(role,path='.',kind='directory',**changes):
    row=dict(role=role,path=path,kind=kind,mode=0o755,uid=1000,gid=1000,mtime_ns=10**18,
        bytes=0,sha256=None,link_target=None,xattrs={},source_dev=999,
        source_ino=int.from_bytes(hashlib.sha256((role+path).encode()).digest()[:6],'big'),
        source_nlink=1,source_ctime_ns=10**18)
    if kind=='regular':row.update(bytes=3,sha256=E.digest(b'abc'))
    row.update(changes);return row


class Contracts(unittest.TestCase):
    def test_plan_is_only_pending_and_exact_original_lf_sidecar(self):
        index_raw,_,_,_=fixture();p=E.remote_plan(index_raw,'a'*40,'SYNTHETIC_ONLY','b'*40)
        self.assertFalse(p['accepted_remote']);self.assertEqual(p['actual_download'],'NOT_RUN')
        line=(p['assets'][0]['sha256']+'  '+p['assets'][0]['name']+'\n').encode()
        self.assertEqual(p['assets'][1]['sha256'],E.digest(line))

    def test_synthetic_gate_contract_never_authorizes_production(self):
        index,remote,payload,now=fixture();self.assertEqual(gate(index,remote,payload,now)[0]['entry_count'],3)
        with self.assertRaisesRegex(ValueError,'Actual independent fresh'):
            E.remote_gate(index,raw(remote),E.digest(raw(remote)),payload,E.digest(payload),
                'a'*40,'SYNTHETIC_ONLY','b'*40,'c'*64,now=now)

    def test_receipt_age_owner_closure_asset_drift_and_source_reject(self):
        for change in ('age','closure','asset','source','public'):
            index,remote,payload,now=fixture()
            if change=='age':remote['verified_at_utc']=(now-dt.timedelta(minutes=16)).isoformat()
            elif change=='closure':remote['owned_download_clients_closed']=False
            elif change=='asset':remote['assets_after'][0]['sha256']='0'*64
            elif change=='source':remote['helper_source_sha256']={}
            else:remote['capture_inputs']['all_required_runtime_files_public_and_covered']=False
            with self.subTest(change=change),self.assertRaises(ValueError):gate(index,remote,payload,now)

    def test_pending_full_payload_and_external_hash_tamper_reject(self):
        index,remote,payload,now=fixture();value=json.loads(payload);value['all_gzip_crc_verified']=False
        payload=raw(value);remote['independent_payload_receipt_sha256']=E.digest(payload)
        with self.assertRaisesRegex(ValueError,'exhaustive local'):gate(index,remote,payload,now)
        with self.assertRaisesRegex(ValueError,'External remote'):
            E.remote_gate(index,raw(remote),'0'*64,payload,E.digest(payload),'a'*40,'SYNTHETIC_ONLY','b'*40,'c'*64,now=now,synthetic=True)

    def test_absolute_traversal_drive_ads_unicode_and_alias_names_reject(self):
        for value in ('/etc/passwd','../x','a/../x','a//x','a/./x','a\\x','C:/outside','D:leaf',
                      'x/file:stream','a\x00b','e\u0301','.'):
            with self.subTest(value=value),self.assertRaises(ValueError):E.relative(value)

    def test_duplicate_json_keys_reject(self):
        with self.assertRaisesRegex(ValueError,'Duplicate JSON'):E.strict_json(b'{"key":1,"key":2}')

    def ledger(self,rows,check):
        with tempfile.TemporaryDirectory(prefix='runtime_ledger_synthetic_',dir=E.W) as temporary:
            path=Path(temporary)/'manifest.jsonl';path.write_bytes(b''.join(raw(x) for x in rows))
            db=sqlite3.connect(':memory:')
            try:return check(db,path)
            finally:db.close()

    def test_internal_hardlink_and_empty_dir_ledger_and_original_graph(self):
        rows=[node(role) for role in C.ROOTS];source=node('environment_dir','a','regular',source_nlink=2)
        alias=copy.deepcopy(source);alias.update(path='b',kind='hardlink',link_target='environment_dir/a')
        rows.extend([source,alias,node('environment_dir','empty')]);rows.sort(key=lambda r:r['role']+'/'+r['path'])
        result=self.ledger(rows,lambda db,p:E.load_ledger(p,db,C,R,lambda:None))
        self.assertEqual(result,(6,3))
        alias['source_ino']+=1
        with self.assertRaisesRegex(ValueError,'inode alias'):self.ledger(rows,lambda db,p:E.load_ledger(p,db,C,R,lambda:None))

    def test_duplicate_conflicting_parent_and_external_symlink_reject(self):
        cases=[];base=[node(role) for role in C.ROOTS]
        cases.append(base+[copy.deepcopy(base[0])])
        cases.append(base+[node('environment_dir','x','symlink',mode=0o777,link_target='.'),node('environment_dir','x/file','regular')])
        cases.append(base+[node('environment_dir','outside','symlink',mode=0o777,link_target='/etc/passwd')])
        for rows in cases:
            rows.sort(key=lambda r:r['role']+'/'+r['path'])
            with self.subTest(rows=len(rows)),self.assertRaises(ValueError):self.ledger(rows,lambda db,p:E.load_ledger(p,db,C,R,lambda:None))

    def test_exact_captured_bytes_remain_authoritative_after_source_reopen_change(self):
        rows=[node(role) for role in C.ROOTS]+[node('environment_dir','a','regular')]
        rows.sort(key=lambda r:r['role']+'/'+r['path'])
        def check(db,path):
            original=path.read_bytes();metadata=path.lstat()
            # Linux-only API: Windows fstat/lstat ctime semantics differ. This
            # explicitly synthetic adapter supplies consistent Linux metadata;
            # the actual original bytes still stream through the real read fd.
            with mock.patch.object(E.os,'fstat',return_value=metadata):
                captured=E.exact_control(path,E.digest(original),lambda:None,True)
            path.write_bytes(b'UNTRUSTED_REOPEN_BYTES\n')
            return E.load_ledger(path,db,C,R,lambda:None,captured)
        self.assertEqual(self.ledger(rows,check),(4,3))

    def test_reviewed_absolute_internal_symlink_text_preserved_and_non777_rejects(self):
        rows=[node(role) for role in C.ROOTS]+[node('environment_dir','a','regular'),
             node('models_dir','link','symlink',mode=0o777,link_target=C.ROOTS['environment_dir']+'/a')]
        rows.sort(key=lambda r:r['role']+'/'+r['path'])
        def check(db,path):
            result=E.load_ledger(path,db,C,R,lambda:None)
            self.assertEqual(R.node_for_original(db,C.ROOTS['models_dir']+'/link')['sha256'],E.digest(b'abc'))
            return result
        self.assertEqual(self.ledger(rows,check),(5,3))
        next(row for row in rows if row['kind']=='symlink')['mode']=0o755
        with self.assertRaisesRegex(ValueError,'symlink mode'):self.ledger(rows,check)

    def test_tar_header_type_link_and_sparse_mismatch_reject(self):
        row=node('environment_dir','file','regular');item=tarfile.TarInfo(R.member_for(row))
        item.mode=row['mode'];item.uid=row['uid'];item.gid=row['gid'];item.size=3;item.mtime=10**9
        E.tar_member(item,row,R)
        for change in ('type','link','sparse','name'):
            value=copy.deepcopy(item)
            if change=='type':value.type=tarfile.FIFOTYPE
            elif change=='link':value.linkname='outside'
            elif change=='sparse':value.sparse=[(0,3)]
            else:value.name='payload/environment_dir/file:stream'
            with self.subTest(change=change),self.assertRaises(ValueError):E.tar_member(value,row,R)

    def test_nested_same_device_mount_and_original_device_requirements(self):
        stage='/var/tmp/lab_rm_runtime_restore_SYNTHETIC'
        raw=b'1 0 8:64 / / rw - ext4 /dev/test rw\n'
        self.assertEqual(T.mount_topology(raw,stage)['major_minor'],'8:64')
        with self.assertRaisesRegex(ValueError,'Nested mount'):
            T.mount_topology(raw+('2 1 8:64 / '+stage+'/nested rw - ext4 /dev/test rw\n').encode(),stage)

    def test_openat2_abi_flags_and_exact_inode_hardlink_serialization_only(self):
        calls=[];api=E.SafeLinux.__new__(E.SafeLinux)
        def syscall(number,parent,name,how,size):
            value=ctypes.cast(how,ctypes.POINTER(E.SafeLinux.How)).contents
            calls.append((number.value,parent.value,name.value,value.flags,value.mode,value.resolve,size.value));return 91
        links=[];api.libc=types.SimpleNamespace(syscall=syscall,linkat=lambda *args:links.append(args) or 0)
        with mock.patch.object(E,'os',types.SimpleNamespace(O_NOFOLLOW=0x20000,O_CLOEXEC=0x80000)):
            self.assertEqual(api.opened(7,'environment_dir/file',2|0x40|0x80,0o600),91)
        self.assertEqual(calls[0][0],437);self.assertEqual(calls[0][5],0x0f);self.assertEqual(calls[0][6],24)
        api.linked(91,7,'alias');self.assertEqual(links,[(91,b'',7,b'alias',0x1000)])

    def test_actual_extractor_unavailable_before_any_windows_action(self):
        with mock.patch.object(E,'os',types.SimpleNamespace(name='nt')):
            with self.assertRaisesRegex(ValueError,'Reviewed Linux'):
                E.extract(*([None]*14))


if __name__=='__main__':unittest.main()
