"""Meaningful tamper/recovery compatibility cases; only synthetic bytes."""
import copy
import hashlib
import io
import json
import unittest
import stage5_runtime_transport_alias as T


def raw(value):
    return json.dumps(value, sort_keys=True).encode()


class AliasTests(unittest.TestCase):
    def setUp(self):
        self.payload = b'synthetic gzip-part bytes\x00\xff'
        self.index = {'schema': 'STAGE05_RUNTIME_LOGICAL_ARCHIVE_INDEX_V1', 'source_sha256': T.CAPTURE_SHA,
                      'roots': T.ROOTS, 'maximum_asset_bytes': T.LIMIT,
                      'installed_build_equivalence': 'NOT_ESTABLISHED', 'cleanup_authority': False,
                      'shards': [{'name': 'stage5-installed-runtime-01.part0001', 'bytes': len(self.payload), 'sha256': T.digest(self.payload)}],
                      'compressed_bytes': len(self.payload), 'compressed_stream_sha256': T.digest(self.payload)}
        self.index_raw = raw(self.index); self.index_sha = T.digest(self.index_raw)
        self.plan = T.make_plan(self.index_raw, self.index_sha, '20261010-v1')
        self.plan_raw = raw(self.plan); self.plan_sha = T.digest(self.plan_raw)
        self.metadata = [{'id': number, 'name': row['remote_name'], 'bytes': row['bytes'], 'sha256': row['sha256']}
                         for number, row in enumerate(self.plan['assets'], 1)]

    def bind(self, before=None, after=None):
        return T.bind_assets(self.plan_raw, self.plan_sha, self.index_raw, self.index_sha,
                             self.metadata if before is None else before, self.metadata if after is None else after)

    def test_labels_bind_exact_original_reader_names_and_bytes(self):
        rows = self.bind(); guards = []
        sidecar = (T.digest(self.payload)+'  stage5-installed-runtime-01.part0001\n').encode()
        self.assertTrue(rows[0]['remote_name'].startswith(T.LABEL+'-20261010-v1.'))
        self.assertEqual(rows[0]['local_name'], self.index['shards'][0]['name'])
        for row, payload in zip(rows, [self.payload, sidecar]):
            result = T.verify_stream(io.BytesIO(payload), row, lambda: guards.append(True))
            self.assertTrue(result['full_stream_verified'])
            self.assertFalse(result['fresh_download_proven_by_this_function'])
        self.assertGreaterEqual(len(guards), 4)

    def test_corrupt_short_long_and_renamed_sidecar_are_rejected(self):
        rows = self.bind()
        for payload in [self.payload[:-1], self.payload+b'x', b'x'+self.payload[1:]]:
            with self.assertRaises(ValueError): T.verify_stream(io.BytesIO(payload), rows[0], lambda: None)
        wrong_sidecar = (T.digest(self.payload)+'  '+rows[0]['remote_name']+'\n').encode()
        with self.assertRaises(ValueError): T.verify_stream(io.BytesIO(wrong_sidecar), rows[1], lambda: None)

    def test_remote_drift_duplicate_id_missing_asset_rejected(self):
        changed = copy.deepcopy(self.metadata); changed[0]['id'] += 10
        with self.assertRaises(ValueError): self.bind(after=changed)
        duplicate = copy.deepcopy(self.metadata); duplicate[1]['id'] = duplicate[0]['id']
        with self.assertRaises(ValueError): self.bind(duplicate, duplicate)
        with self.assertRaises(ValueError): self.bind(self.metadata[:-1], self.metadata[:-1])

    def test_alias_tamper_rehash_still_rejected_against_index(self):
        changed = copy.deepcopy(self.plan); changed['assets'][0]['local_name'] = '../escape'
        altered = raw(changed)
        with self.assertRaises(ValueError): T.validate_plan(altered, T.digest(altered), self.index_raw, self.index_sha)

    def test_noncanonical_shard_order_and_middle_short_part_rejected(self):
        changed = copy.deepcopy(self.index); changed['shards'][0]['name'] = 'stage5-installed-runtime-01.part0002'
        data = raw(changed)
        with self.assertRaises(ValueError): T.make_plan(data, T.digest(data), '20261010-v1')
        changed = copy.deepcopy(self.index); changed['shards'].append({**changed['shards'][0], 'name': 'stage5-installed-runtime-01.part0002'})
        changed['compressed_bytes'] *= 2; data = raw(changed)
        with self.assertRaises(ValueError): T.make_plan(data, T.digest(data), '20261010-v1')

    def test_duplicate_json_snapshot_traversal_and_wrong_pin_rejected(self):
        with self.assertRaises(ValueError): T.strict_json(b'{"a":1,"a":2}')
        with self.assertRaises(ValueError): T.make_plan(self.index_raw, self.index_sha, '../v1')
        with self.assertRaises(ValueError): T.make_plan(self.index_raw, '0'*64, '20261010-v1')

    def test_owner_guard_failure_propagates_without_recovery_claim(self):
        def fail(): raise RuntimeError('Owner lease expired')
        with self.assertRaisesRegex(RuntimeError, 'Owner lease expired'):
            T.verify_stream(io.BytesIO(self.payload), self.bind()[0], fail)


if __name__ == '__main__':
    unittest.main()
