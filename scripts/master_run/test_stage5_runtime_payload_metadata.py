"""Pure memory/SQLite metadata predicates; no tar/archive/image/runtime execution."""
import copy
import io
import json
import sqlite3
import unittest
import verify_stage5_runtime_logical_payload as V
from test_stage5_runtime_recovery_contract import fixture,row


class Lines:
    def __init__(self,rows):self.rows=rows
    def open(self,*args,**kwargs):return io.StringIO(''.join(json.dumps(r)+'\n' for r in self.rows))


class Metadata(unittest.TestCase):
    def db(self):
        db=sqlite3.connect(':memory:');self.addCleanup(db.close)
        db.execute('CREATE TABLE entries(name TEXT PRIMARY KEY,kind TEXT,row_json TEXT,seen INTEGER)');return db
    def test_full_three_root_metadata(self):
        rows,_=fixture();self.assertEqual(V.store_manifest(self.db(),Lines(rows)),(5,3))
    def test_missing_plain_parent(self):
        rows,_=fixture();rows=[r for r in rows if r['path']!='bin']
        with self.assertRaises(ValueError):V.store_manifest(self.db(),Lines(rows))
    def test_order_duplicate(self):
        rows,_=fixture()
        for value in [list(reversed(rows)),rows+[rows[-1]]]:
            with self.assertRaises(ValueError):V.store_manifest(self.db(),Lines(value))
    def test_external_symlink(self):
        rows,_=fixture();rows.append(row('models_dir','bad','symlink',link_target='/etc/passwd'))
        rows.sort(key=lambda r:r['role']+'/'+r['path'])
        with self.assertRaises(ValueError):V.store_manifest(self.db(),Lines(rows))
    def test_link_resolution_and_dangling(self):
        rows,_=fixture();rows.append(row('models_dir','python','symlink',link_target=V.ROOTS['environment_dir']+'/bin/python'))
        rows.sort(key=lambda r:r['role']+'/'+r['path']);db=self.db();V.store_manifest(db,Lines(rows))
        self.assertEqual(V.node_for_original(db,V.ROOTS['models_dir']+'/python')['kind'],'regular')
        with self.assertRaises(ValueError):V.node_for_original(db,V.ROOTS['models_dir']+'/missing')
    def test_link_cycle(self):
        rows,_=fixture();rows.append(row('models_dir','cycle','symlink',link_target='cycle'))
        rows.sort(key=lambda r:r['role']+'/'+r['path']);db=self.db();V.store_manifest(db,Lines(rows))
        with self.assertRaises(ValueError):V.node_for_original(db,V.ROOTS['models_dir']+'/cycle')
    def test_hardlink_wrong_source_id(self):
        rows,_=fixture();original=next(r for r in rows if r['path']=='bin/python')
        alias=copy.deepcopy(original);alias.update(path='bin/python3',kind='hardlink',link_target='environment_dir/bin/python',source_ino=original['source_ino']+1)
        rows.append(alias);rows.sort(key=lambda r:r['role']+'/'+r['path'])
        with self.assertRaises(ValueError):V.store_manifest(self.db(),Lines(rows))


if __name__=='__main__':unittest.main()
