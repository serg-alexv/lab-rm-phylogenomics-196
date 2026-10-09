"""Pure recovery ZIP contracts. No WSL, G, native tools or original inputs."""
from pathlib import Path
import hashlib, json, os, stat, tempfile, unittest, zipfile
import stage5_closed_genome_archive_linux as V


def fixture(root):
    genome=root/'GCF_1.1';genome.mkdir();(genome/'execution/failed_attempt_0001').mkdir(parents=True)
    (genome/'execution/failed_attempt_0001/error.txt').write_bytes(b'SYNTHETIC FAILED NATIVE HISTORY\n')
    (genome/'execution/empty_attempt_0002').mkdir();(genome/'bundle').mkdir()
    data=b'SYNTHETIC RAW HMM HIT\n';(genome/'bundle/raw.tsv').write_bytes(data);(genome/'.guard').write_bytes(b'')
    identity={'schema':'STAGE05_SINGLE_GENOME_SCIENTIFIC_IDENTITY_V2','accession':genome.name,'synthetic_fixture':True}
    complete={'schema':'STAGE05_ATOMIC_GENOME_COMPLETE_V1','state':'COMPLETE_VALIDATED','accession':genome.name,
              'scientific_identity':identity,'scientific_identity_sha256':V.S.fingerprint(identity),
              'files':{'bundle/raw.tsv':hashlib.sha256(data).hexdigest()}}
    (genome/'complete.json').write_bytes(V.json_bytes(complete))
    (genome/'scientific_identity.json').write_bytes(V.json_bytes(identity))
    (genome/'status.json').write_bytes(V.json_bytes({'state':'COMPLETE_VALIDATED','synthetic_fixture':True}))
    return genome,V.S.sha(genome/'complete.json')


class Contracts(unittest.TestCase):
    def test_closure_veto_retains_unproven_prior_scopes(self):
        self.assertTrue(V.closure_proven([],False,False,False))
        self.assertTrue(V.closure_proven([],True,True,False))
        self.assertFalse(V.closure_proven([],True,True,True))
        self.assertFalse(V.closure_proven([],True,False,False))
        self.assertFalse(V.closure_proven([123],True,True,False))

    def test_exact_raw_bytes_failed_history_empty_dirs_and_no_eviction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);genome,pin=fixture(root);output=root/'raw.zip'
            report=V.build_zip(genome,output,pin,{'synthetic':True},lambda:None)
            self.assertFalse(report['eviction_authorized']);self.assertFalse(report['new_scientific_acceptance'])
            with zipfile.ZipFile(output) as archive:
                manifest=json.loads(archive.read('_recovery/manifest.json'))
                self.assertIn('execution/empty_attempt_0002',manifest['directories_to_restore'])
                self.assertIn('genome/execution/failed_attempt_0001/error.txt',archive.namelist())
                self.assertEqual(manifest['omitted_empty_lock_files'],['.guard'])
                self.assertEqual(archive.read('genome/bundle/raw.tsv'),(genome/'bundle/raw.tsv').read_bytes())
                actual_mode=stat.S_IMODE((genome/'bundle/raw.tsv').stat().st_mode)
                self.assertEqual(manifest['files']['bundle/raw.tsv']['mode'],actual_mode)
                self.assertEqual(archive.getinfo('genome/bundle/raw.tsv').external_attr>>16,stat.S_IFREG|actual_mode)
            side=output.with_name(output.name+'.sha256').read_bytes()
            self.assertTrue(side.endswith(b'\n'));self.assertNotIn(b'\r',side);self.assertTrue((genome/'.guard').exists())

    def test_same_fixed_source_and_metadata_yields_same_zip_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);genome,pin=fixture(root)
            for name in ('one.zip','two.zip'):V.build_zip(genome,root/name,pin,{'synthetic':True},lambda:None)
            self.assertEqual(V.S.sha(root/'one.zip'),V.S.sha(root/'two.zip'))

    def test_existing_sidecar_refuses_before_any_archive_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);genome,pin=fixture(root);side=root/'raw.zip.sha256';side.write_bytes(b'PRESERVE ORIGINAL SIDECAR\n')
            with self.assertRaisesRegex(ValueError,'sidecar already exists'):
                V.build_zip(genome,root/'raw.zip',pin,{},lambda:None)
            self.assertEqual(side.read_bytes(),b'PRESERVE ORIGINAL SIDECAR\n')
            self.assertFalse((root/'raw.zip').exists());self.assertFalse((root/'raw.zip.partial').exists())

    def test_changed_selected_hit_rejects_and_retains_originals_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);genome,pin=fixture(root);(genome/'bundle/raw.tsv').write_bytes(b'DRIFT')
            with self.assertRaisesRegex(ValueError,'member SHA'):V.build_zip(genome,root/'raw.zip',pin,{},lambda:None)
            self.assertFalse((root/'raw.zip').exists());self.assertTrue((root/'raw.zip.partial').exists())
            self.assertEqual((genome/'bundle/raw.tsv').read_bytes(),b'DRIFT')

    def test_v1_identity_and_unknown_root_payload_cannot_archive(self):
        for mode in ('v1','unknown','wrong_accession','changed_identity'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);genome,pin=fixture(root)
                if mode=='unknown':(genome/'unclassified_private.bin').write_bytes(b'UNKNOWN')
                elif mode=='changed_identity':(genome/'scientific_identity.json').write_text('{}')
                else:
                    path=genome/'complete.json';value=json.loads(path.read_bytes())
                    if mode=='v1':value['scientific_identity']['schema']='STAGE05_SINGLE_GENOME_SCIENTIFIC_IDENTITY_V1'
                    else:value['accession']='GCF_2.1'
                    value['scientific_identity_sha256']=V.S.fingerprint(value['scientific_identity'])
                    path.write_bytes(V.json_bytes(value));pin=V.S.sha(path)
                with self.assertRaises(ValueError):V.build_zip(genome,root/'raw.zip',pin,{},lambda:None)
                self.assertFalse((root/'raw.zip').exists())

    def test_file_logical_and_compressed_caps_preserve_without_final_asset(self):
        for limits in ({'max_files':1},{'max_logical':10},{'max_asset':32}):
            with self.subTest(limits=limits),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);genome,pin=fixture(root)
                with self.assertRaises(ValueError):V.build_zip(genome,root/'raw.zip',pin,{},lambda:None,**limits)
                self.assertFalse((root/'raw.zip').exists());self.assertEqual(V.S.sha(genome/'complete.json'),pin)

    def test_lease_resource_stop_does_not_change_source_or_complete_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);genome,pin=fixture(root)
            def stopped():raise RuntimeError('SYNTHETIC OWNER LEASE EXPIRED')
            with self.assertRaisesRegex(RuntimeError,'LEASE EXPIRED'):V.build_zip(genome,root/'raw.zip',pin,{},stopped)
            self.assertFalse((root/'raw.zip').exists());self.assertEqual(V.S.sha(genome/'complete.json'),pin)

    def test_raw_file_replacement_during_inventory_copy_boundary_rejects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);genome,pin=fixture(root);changed=False
            def drift():
                nonlocal changed
                if (root/'raw.zip.partial').exists() and not changed:
                    changed=True;(genome/'bundle/raw.tsv').write_bytes(b'CONCURRENT SYNTHETIC DRIFT')
            with self.assertRaisesRegex(ValueError,'identity changed'):
                V.build_zip(genome,root/'raw.zip',pin,{},drift)
            self.assertFalse((root/'raw.zip').exists());self.assertTrue(changed)

    def test_hardlink_alias_is_preserved_and_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);genome,pin=fixture(root);os.link(genome/'bundle/raw.tsv',root/'alias.tsv')
            with self.assertRaisesRegex(ValueError,'one link'):
                V.build_zip(genome,root/'raw.zip',pin,{},lambda:None)
            self.assertTrue((root/'alias.tsv').exists());self.assertTrue((genome/'bundle/raw.tsv').exists())

    def test_full_member_readback_rejects_self_consistent_wrong_expected_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/'fixture.zip'
            with zipfile.ZipFile(path,'w') as archive:archive.writestr('safe.txt',b'ACTUAL')
            with self.assertRaisesRegex(ValueError,'CRC/size/SHA'):
                V.zip_reopen(path,{'safe.txt':{'bytes':6,'sha256':hashlib.sha256(b'WRONG!').hexdigest()}},lambda:None)


if __name__=='__main__':unittest.main()
