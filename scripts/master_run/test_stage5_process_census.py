"""Pure C-work byte/mock contracts; no native process or WSL calls."""
from pathlib import Path
import contextlib
import ctypes as c
import ast
import importlib.util
import io
import json
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

SOURCE = Path(__file__).with_name('stage5_process_census.py')
spec = importlib.util.spec_from_file_location('census_under_test', SOURCE)
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)


def record(pid, name='synthetic.exe', base=0x100000, offset=0, next_record=False):
    text = name.encode('utf-16-le') if name is not None else b''
    size = c.sizeof(M.SPI) + c.sizeof(M.STI) + len(text) + (2 if text else 0)
    size = (size + 7) // 8 * 8
    data = bytearray(size)
    row = M.SPI(); row.UniqueProcessId = pid; row.NumberOfThreads = 1; row.SessionId = 1
    row.NextEntryOffset = size if next_record else 0
    if text:
        row.ImageName.Length = len(text); row.ImageName.MaximumLength = len(text) + 2
        row.ImageName.Buffer = base + offset + c.sizeof(M.SPI) + c.sizeof(M.STI)
    data[:c.sizeof(row)] = bytes(row)
    thread = M.STI(); thread.ClientId.UniqueProcess = pid; thread.ClientId.UniqueThread = pid + 1
    data[c.sizeof(row):c.sizeof(row)+c.sizeof(thread)] = bytes(thread)
    data[c.sizeof(row)+c.sizeof(thread):c.sizeof(row)+c.sizeof(thread)+len(text)] = text
    return data


def change_header(data, **changes):
    row = M.SPI.from_buffer_copy(data)
    for name, value in changes.items(): setattr(row, name, value)
    data[:c.sizeof(row)] = bytes(row)
    return data


class Contracts(unittest.TestCase):
    def test_actual_a80_public_interface_is_win_and_wintypes_filetime(self):
        tree=ast.parse(SOURCE.with_name('atomic_iqtree_windows.py').read_bytes())
        self.assertIn('Win',[x.name for x in tree.body if isinstance(x,ast.ClassDef)])
        source_tree=ast.parse(SOURCE.read_bytes())
        calls=[x.func for x in ast.walk(source_tree) if isinstance(x,ast.Call)]
        self.assertTrue(any(isinstance(x,ast.Attribute) and isinstance(x.value,ast.Name)
                            and x.value.id=='A' and x.attr=='Win' for x in calls))
        self.assertFalse(any(isinstance(x,ast.Attribute) and isinstance(x.value,ast.Name)
                             and x.value.id=='api' and x.attr=='FILETIME' for x in calls))

    def test_retained_birth_queries_use_querylimited_only_and_real_filetime_type(self):
        access=[]
        class Open:
            def __call__(self,mask,inherit,pid):access.append((mask,inherit,pid));return 123
        def times(handle,*values):
            self.assertEqual(handle,123)
            for value in values:self.assertIsInstance(value._obj,M.w.FILETIME)
            values[0]._obj.dwHighDateTime=1;values[0]._obj.dwLowDateTime=7
            return True
        api=SimpleNamespace(K=SimpleNamespace(OpenProcess=Open()),times=times,
                            ft=lambda x:(x.dwHighDateTime<<32)|x.dwLowDateTime,
                            ok=lambda value,reason:self.assertTrue(value),close=lambda handle:True)
        rows,handles=M.retained_births(api,{0,42},lambda:None)
        self.assertEqual(access,[(0x1000,False,42)])
        self.assertEqual(rows[1]['creation_filetime'],(1<<32)|7)
        self.assertFalse(rows[1]['kernel_exit_or_liveness_proven'])
        self.assertEqual(handles,[(42,123)])

    def test_public_abi_and_no_birth_reinterpretation(self):
        M.validate_abi()
        self.assertEqual(c.sizeof(M.SPI), 256)
        self.assertEqual(c.sizeof(M.STI), 80)
        self.assertNotIn('CreateTime', dict(M.SPI._fields_))

    def test_valid_two_records_and_idle(self):
        first = record(0, None, next_record=True)
        second = record(1234, offset=len(first))
        rows = M.parse_native(bytes(first+second), 0x100000)
        self.assertEqual([r['pid'] for r in rows], [0, 1234])
        self.assertEqual(rows[1]['image_name'], 'synthetic.exe')
        self.assertIsNone(rows[1]['creation_filetime'])

    def test_opaque_reserved_birth_bytes_stay_opaque(self):
        data = record(12)
        data[8:56] = b'\xff'*48
        self.assertIsNone(M.parse_native(bytes(data), 0x100000)[0]['creation_filetime'])

    def test_bad_next_offset(self):
        for offset in (8, 257, 8000000):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                M.parse_native(bytes(change_header(record(1), NextEntryOffset=offset)), 0x100000)

    def test_truncated_thread_array(self):
        with self.assertRaises(ValueError):
            M.parse_native(bytes(change_header(record(1), NumberOfThreads=2)), 0x100000)

    def test_wrong_thread_owner(self):
        data = record(1); thread = M.STI.from_buffer_copy(data, c.sizeof(M.SPI))
        thread.ClientId.UniqueProcess = 2
        data[c.sizeof(M.SPI):c.sizeof(M.SPI)+c.sizeof(M.STI)] = bytes(thread)
        with self.assertRaises(ValueError): M.parse_native(bytes(data), 0x100000)

    def test_duplicate_pid(self):
        first = record(1, next_record=True); second = record(1, offset=len(first))
        with self.assertRaises(ValueError): M.parse_native(bytes(first+second), 0x100000)

    def test_name_pointer_never_reads_outside_returned_record(self):
        for address in (0, 0x100001, 0x200000):
            data = record(1); row = M.SPI.from_buffer_copy(data); row.ImageName.Buffer = address
            data[:c.sizeof(row)] = bytes(row)
            with self.subTest(address=address), self.assertRaises(ValueError):
                M.parse_native(bytes(data), 0x100000)

    def test_odd_unicode_length(self):
        data = record(1); row = M.SPI.from_buffer_copy(data); row.ImageName.Length = 3
        data[:c.sizeof(row)] = bytes(row)
        with self.assertRaises(ValueError): M.parse_native(bytes(data), 0x100000)

    def test_native_growth_and_returned_bytes(self):
        calls=[]
        def query(kind, buffer, size, return_length):
            self.assertEqual(kind, 5); calls.append(size)
            if len(calls)==1:
                return_length._obj.value = 100000
                return -1073741820
            data = record(33, base=c.addressof(buffer)); c.memmove(buffer, bytes(data), len(data))
            return_length._obj.value=len(data); return 0
        with tempfile.TemporaryDirectory(dir=SOURCE.parent) as tmp:
            value=M.native_snapshot(query, lambda: None, Path(tmp), 'synthetic')
            self.assertEqual(len(calls), 2)
            self.assertEqual(value['records'][0]['pid'],33)
            self.assertEqual(Path(value['raw_file']).stat().st_size,value['raw_bytes'])

    def test_native_allocation_cap_and_bad_status(self):
        def huge(kind, buffer, size, length):
            length._obj.value=M.MAX_BUFFER+1;return -1073741820
        def bad(kind, buffer, size, length): return -1
        with tempfile.TemporaryDirectory(dir=SOURCE.parent) as tmp:
            for query in (huge,bad):
                with self.assertRaises(ValueError): M.native_snapshot(query,lambda:None,Path(tmp),'bad')

    def test_bad_actual_record_preserves_returned_raw_metadata_and_parse_error(self):
        def query(kind,buffer,size,length):
            data=change_header(record(3,base=c.addressof(buffer)),NumberOfThreads=65535)
            c.memmove(buffer,bytes(data),len(data));length._obj.value=len(data);return 0
        with tempfile.TemporaryDirectory(dir=SOURCE.parent) as tmp:
            directory=Path(tmp)
            with self.assertRaises(ValueError):M.native_snapshot(query,lambda:None,directory,'rejected')
            self.assertTrue((directory/'rejected.spi.bin').is_file())
            meta=json.loads((directory/'rejected.spi_metadata.json').read_bytes())
            self.assertEqual(meta['raw_sha256'],M.sha(directory/'rejected.spi.bin'))
            self.assertTrue((directory/'rejected.spi_parse_error.json').is_file())

    def test_enum_grows_on_exact_buffer_and_rejects_max_truncation(self):
        calls=[]
        def enum(values, size, used):
            calls.append(size)
            if len(calls)==1: used._obj.value=size
            else: values[0]=0;values[1]=7;used._obj.value=8
            return 1
        self.assertEqual(M.enum_pids(enum,lambda:None),[0,7])
        def full(values,size,used):used._obj.value=size;return 1
        with self.assertRaises(ValueError):M.enum_pids(full,lambda:None)

    def test_birth_window_and_inclusive_candidates(self):
        old={'actual_windows_owner':{'pid':M.OLD_PID,'creation_filetime':M.OLD_BIRTH},'utc':'2026-10-09T23:54:25.561454+00:00'}
        window=M.birth_window(old)
        self.assertEqual(window['inclusive_lower_filetime'],M.OLD_BIRTH-600000000)
        rows=[{'pid':1,'creation_filetime':window['inclusive_lower_filetime']},
              {'pid':2,'creation_filetime':window['inclusive_upper_filetime']},
              {'pid':3,'creation_filetime':window['inclusive_upper_filetime']+1},
              {'pid':4,'creation_filetime':None}]
        self.assertEqual([x['pid'] for x in M.candidates(rows,window)],[1,2])
        old['actual_windows_owner']['pid']=123
        with self.assertRaises(ValueError):M.birth_window(old)

    def test_cim_matches_mismatch_unknown_duplicates(self):
        rows=[{'pid':1,'creation_filetime':1000},{'pid':2,'creation_filetime':2000}]
        supplement={'schema':'STAGE05_PROCESS_CENSUS_CIM_CLOCK_SUPPLEMENT_V1','process_census':{'rows':[
            {'pid':1,'birth_filetime':1009},{'pid':2,'birth_filetime':9000},{'pid':3,'birth_filetime':None}]}}
        states=[r['state'] for r in M.crossvalidate_cim(rows,supplement)]
        self.assertEqual(states,['MATCH_WITHIN_CIM_MICROSECOND_PRECISION','MISMATCH_OR_PID_REUSE','NO_RETAINED_KERNEL_BIRTH_FOR_CROSSCHECK'])
        supplement['process_census']['rows'].append({'pid':1,'birth_filetime':1000})
        with self.assertRaises(ValueError):M.crossvalidate_cim(rows,supplement)

    def test_default_noop_even_with_cim(self):
        with patch.object(sys_module:=M.sys,'argv',['census','--with-cim']), patch.object(M,'collect') as collect:
            output=io.StringIO()
            with contextlib.redirect_stdout(output):self.assertEqual(M.main(),0)
            self.assertEqual(json.loads(output.getvalue())['Windows_queries'],0)
            collect.assert_not_called()


if __name__=='__main__':unittest.main()
