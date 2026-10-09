"""Own C synthetic bytes and mocked cache hints; no runtime/WSL/cache action."""
from pathlib import Path
from unittest.mock import patch
import hashlib,os,tempfile,types,unittest
import stage5_atomic as S


class HashCache(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='stage5_hash_fixture_',dir=Path(__file__).resolve().parent)
        cls.root=Path(cls.temp.name);cls.large=cls.root/'large.bin';cls.small=cls.root/'small.bin';cls.aligned=cls.root/'aligned.bin'
        expected=hashlib.sha256();block=bytes(range(256))*4096
        with cls.large.open('xb') as stream:
            for _ in range(17):stream.write(block);expected.update(block)
            stream.write(b'FINAL_PARTIAL_SYNTHETIC_PAGE');expected.update(b'FINAL_PARTIAL_SYNTHETIC_PAGE')
        cls.expected=expected.hexdigest();cls.small.write_bytes(b'SYNTHETIC\r\nEXACT\x00BYTES\n')
        with cls.aligned.open('xb') as stream:
            for _ in range(16):stream.write(block)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def proxy(self,advice=None):
        actual=os;calls=[];opened=[];closed=[];paths={}
        def open_read(path,flags):
            opened.append(flags);fd=actual.open(path,flags & ~0x20000);paths[fd]=Path(path);return fd
        def linux_fstat(fd):
            # Windows fstat/pathstat expose different ctime fields. Simulate the
            # Linux inode metadata contract without weakening production guards.
            # Actual own-file bytes still flow through the readonly real fd.
            value=paths[fd].lstat()
            return types.SimpleNamespace(**{k:getattr(value,k) for k in
                ['st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_nlink']})
        def hint(fd,offset,length,kind):
            self.assertLessEqual(offset+length,actual.lseek(fd,0,os.SEEK_CUR))
            calls.append((fd,offset,length,kind))
            if advice: return advice(fd,offset,length,kind)
            return None
        def close(fd):closed.append(fd);actual.close(fd)
        return types.SimpleNamespace(name='posix',O_RDONLY=os.O_RDONLY,O_NOFOLLOW=0x20000,
            O_BINARY=getattr(os,'O_BINARY',0),POSIX_FADV_DONTNEED=4,open=open_read,fdopen=os.fdopen,
            fstat=linux_fstat,close=close,sysconf=lambda _:4096,posix_fadvise=hint),calls,opened,closed

    def run_target(self,path=None,advice=None):
        proxy,calls,opened,closed=self.proxy(advice)
        with patch.object(S,'os',proxy),patch.object(S,'HASH_CACHE_ROOTS',(self.root,)):
            result=S.sha(path or self.large)
        return result,calls,opened,closed

    def test_large_exact_sha_readonly_metadata_and_closed_fd(self):
        before=self.large.stat();result,calls,opened,closed=self.run_target()
        self.assertEqual(result,self.expected);self.assertTrue(calls)
        self.assertEqual(len(opened),1);self.assertEqual(opened[0]&3,os.O_RDONLY)
        self.assertTrue(opened[0]&0x20000);self.assertEqual(len(closed),1)
        after=self.large.stat();self.assertEqual((before.st_size,before.st_mtime_ns),(after.st_size,after.st_mtime_ns))

    def test_completed_contiguous_full_pages_only_and_final_page_retained(self):
        _,calls,_,_=self.run_target();cursor=0;last_page=((self.large.stat().st_size-1)//4096)*4096
        for _,offset,length,kind in calls:
            self.assertEqual(offset,cursor);self.assertEqual(offset%4096,0);self.assertEqual(length%4096,0)
            self.assertGreater(length,0);self.assertLessEqual(length,8*1024**2);self.assertEqual(kind,4);cursor+=length
        self.assertEqual(cursor,last_page)

    def test_aligned_eof_still_retains_entire_last_page(self):
        result,calls,_,_=self.run_target(self.aligned)
        self.assertEqual(result,hashlib.sha256(self.aligned.read_bytes()).hexdigest())
        self.assertEqual(sum(row[2] for row in calls),self.aligned.stat().st_size-4096)
        self.assertTrue(all(offset+length<=self.aligned.stat().st_size-4096 for _,offset,length,_ in calls))

    def test_small_file_legacy_exact_digest_without_hint_or_raw_open(self):
        result,calls,opened,closed=self.run_target(self.small)
        self.assertEqual(result,hashlib.sha256(self.small.read_bytes()).hexdigest())
        self.assertEqual((calls,opened,closed),([],[],[]))

    def test_other_scope_large_file_keeps_legacy_digest(self):
        proxy,calls,opened,closed=self.proxy()
        with patch.object(S,'os',proxy),patch.object(S,'HASH_CACHE_ROOTS',(self.root/'unselected',)):
            self.assertEqual(S.sha(self.large),self.expected)
        self.assertEqual((calls,opened,closed),([],[],[]))

    def test_unsupported_and_error_advice_fail_closed(self):
        proxy,calls,opened,closed=self.proxy();proxy.posix_fadvise=None
        with patch.object(S,'os',proxy),patch.object(S,'HASH_CACHE_ROOTS',(self.root,)),self.assertRaises(S.Fatal):
            S.sha(self.large)
        self.assertEqual(opened,[])
        def denied(*_):raise OSError('SYNTHETIC UNSUPPORTED ADVICE')
        with self.assertRaisesRegex(OSError,'UNSUPPORTED'):self.run_target(advice=denied)

    def test_non_none_advice_result_fails_closed(self):
        with self.assertRaises(S.Fatal):self.run_target(advice=lambda *_:22)

    def test_opened_identity_swap_fails_before_any_hint_and_closes_fd(self):
        proxy,calls,opened,closed=self.proxy();actual=proxy.fstat
        def changed(fd):
            value=actual(fd)
            return types.SimpleNamespace(**{k:getattr(value,k) for k in ['st_dev','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_nlink']},st_ino=value.st_ino+1)
        proxy.fstat=changed
        with patch.object(S,'os',proxy),patch.object(S,'HASH_CACHE_ROOTS',(self.root,)),self.assertRaises(S.Fatal):S.sha(self.large)
        self.assertEqual(calls,[]);self.assertEqual(len(closed),1)

    def test_postread_metadata_drift_fails(self):
        proxy,calls,opened,closed=self.proxy();actual=proxy.fstat;seen=0
        def changed(fd):
            nonlocal seen
            seen+=1;value=actual(fd)
            return types.SimpleNamespace(**{k:getattr(value,k) for k in ['st_dev','st_ino','st_size','st_ctime_ns','st_mode','st_nlink']},st_mtime_ns=value.st_mtime_ns+(1 if seen>1 else 0))
        proxy.fstat=changed
        with patch.object(S,'os',proxy),patch.object(S,'HASH_CACHE_ROOTS',(self.root,)),self.assertRaises(S.Fatal):S.sha(self.large)
        self.assertTrue(calls);self.assertEqual(len(closed),1)


if __name__=='__main__':unittest.main()
