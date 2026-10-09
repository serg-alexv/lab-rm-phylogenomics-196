"""Synthetic owned C trees only; no runtime, G, WSL or original payload access."""
from pathlib import Path
from unittest.mock import patch
import base64, hashlib, json, tempfile, unittest, zipfile
import stage5_closed_genome_recovery as R
import stage5_closed_genome_archive_linux as B
from test_stage5_closed_genome_archive import fixture
from test_stage5_closed_genome_archive_owner import fixture as owner_fixture


def sha(data):return hashlib.sha256(data).hexdigest()


def captured(data):return {'bytes':len(data),'sha256':sha(data),'base64_original_bytes':base64.b64encode(data).decode()}


def sample(root):
    genome,_=fixture(root);runtime=b'{"synthetic":"NO_RUNTIME"}\n';source=b'{"synthetic":"NO_ACCEPTANCE"}\n'
    panel=(genome.name+'\n').encode();config=b'{"synthetic":"NO_NATIVE_CONFIG"}\n'
    complete=json.loads((genome/'complete.json').read_bytes());identity=complete['scientific_identity']
    identity.update(source_acceptance={'source_pins_sha256':sha(source)},runtime_manifest_sha256=sha(runtime))
    complete['scientific_identity_sha256']=sha(json.dumps(identity,sort_keys=True,separators=(',',':')).encode())
    (genome/'scientific_identity.json').write_bytes(B.json_bytes(identity));(genome/'complete.json').write_bytes(B.json_bytes(complete))
    complete_sha=B.S.sha(genome/'complete.json');nonce='a'*32
    (genome/'status.json').write_bytes(B.json_bytes({'state':'COMPLETE_VALIDATED','accession':genome.name,
        'owner_nonce':nonce,'owned_closure_proven':True,'complete_receipt_sha256':complete_sha}))
    _,values=owner_fixture();row=values[genome.name+'.exit.json']
    row.update(status_sha256=B.S.sha(genome/'status.json'),stdout_sha256=sha(b'SYNTHETIC_STDOUT'),stderr_sha256=sha(b''))
    values['result.json']['config_sha256']=sha(config)
    originals={name:captured(B.json_bytes(value)) for name,value in values.items()}
    originals[genome.name+'.stdout.txt']=captured(b'SYNTHETIC_STDOUT');originals[genome.name+'.stderr.txt']=captured(b'')
    owner={'schema':'STAGE05_CLOSED_GENOME_ARCHIVE_OWNER_SOURCE_V1','accession':genome.name,
        'config_sha256':sha(config),'complete_sha256':complete_sha,'status_sha256':B.S.sha(genome/'status.json'),
        'prior_owner_nonce':nonce,'original_owner_files':originals}
    owner_bytes=B.json_bytes(owner)
    metadata={'closed_owner_proof':owner,'closed_owner_proof_sha256':sha(owner_bytes),'actual_metadata_files':{
        'config.json':captured(config),'runtime_manifest.json':captured(runtime),'accepted_source_pins.json':captured(source),
        'approved_accessions.txt':captured(panel),'storage_proof.json':captured(b'{"synthetic":true}\n'),
        'closed_owner_proof.json':captured(owner_bytes)}}
    asset=root/'raw.zip';report=B.build_zip(genome,asset,complete_sha,metadata,lambda:None)
    return genome,asset,report,{'SOURCE_PINS':sha(source),'PANEL_SHA':sha(panel)}


def changed_zip(original,target,transform):
    with zipfile.ZipFile(original) as archive:
        payload={i.filename:archive.read(i) for i in archive.infolist()};infos={i.filename:i for i in archive.infolist()}
    transform(payload)
    payload['SHA256SUMS.txt']=''.join(sha(data)+'  '+name+'\n' for name,data in sorted(payload.items()) if name!='SHA256SUMS.txt').encode()
    with zipfile.ZipFile(target,'w') as archive:
        for name,data in payload.items():archive.writestr(infos.get(name,B.zip_info(name)),data)


class Contracts(unittest.TestCase):
    def test_independent_full_zip_and_new_raw_tree_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);genome,asset,build,pins=sample(root)
            with patch.multiple(R,**pins):
                checked=R.verify_archive(asset,build['asset_sha256'],build['complete_sha256'],genome.name)
                result=R.restore_fresh(asset,(root/'fresh_tree').resolve(),build['asset_sha256'],build['complete_sha256'],genome.name)
            self.assertFalse(checked['eviction_authorized']);self.assertFalse(result['canonical_path_matches_manifest'])
            self.assertEqual(result['native_cache_adoption'],'NOT_TESTED');self.assertTrue(genome.exists())
            self.assertEqual((root/'fresh_tree/bundle/raw.tsv').read_bytes(),(genome/'bundle/raw.tsv').read_bytes())
            self.assertTrue((root/'fresh_tree/execution/empty_attempt_0002').is_dir());self.assertEqual((root/'fresh_tree/.guard').stat().st_size,0)

    def test_regenerated_self_consistent_wrong_hit_cannot_replace_selected_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);genome,asset,build,pins=sample(root);wrong=root/'wrong.zip'
            def change(payload):
                name='genome/bundle/raw.tsv';payload[name]=b'X'*len(payload[name])
                manifest=json.loads(payload['_recovery/manifest.json']);manifest['files']['bundle/raw.tsv']['sha256']=sha(payload[name])
                payload['_recovery/manifest.json']=B.json_bytes(manifest)
            changed_zip(asset,wrong,change)
            with patch.multiple(R,**pins),self.assertRaisesRegex(ValueError,'complete native payload'):
                R.verify_archive(wrong,B.S.sha(wrong),build['complete_sha256'],genome.name)

    def test_wrong_external_complete_and_unlisted_member_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);genome,asset,build,pins=sample(root);extra=root/'extra.zip'
            changed_zip(asset,extra,lambda p:p.update({'genome/../outside.txt':b'SYNTHETIC_OUTSIDE'}))
            with patch.multiple(R,**pins):
                with self.assertRaises(ValueError):R.verify_archive(asset,build['asset_sha256'],'f'*64,genome.name)
                with self.assertRaises(ValueError):R.verify_archive(extra,B.S.sha(extra),build['complete_sha256'],genome.name)

    def test_replaced_owner_proof_bytes_reject_even_with_regenerated_outer_sums(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);genome,asset,build,pins=sample(root);wrong=root/'wrong_owner.zip'
            def change(payload):
                manifest=json.loads(payload['_recovery/manifest.json'])
                manifest['provenance']['actual_metadata_files']['closed_owner_proof.json']=captured(b'{}')
                payload['_recovery/manifest.json']=B.json_bytes(manifest)
            changed_zip(asset,wrong,change)
            with patch.multiple(R,**pins),self.assertRaisesRegex(ValueError,'closed-owner/config proof'):
                R.verify_archive(wrong,B.S.sha(wrong),build['complete_sha256'],genome.name)

    def test_existing_output_and_resource_stop_preserve_originals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);genome,asset,build,pins=sample(root);output=(root/'partial_tree').resolve()
            def stop():
                if output.exists():raise RuntimeError('SYNTHETIC_COLD_OWNER_STOP')
            with patch.multiple(R,**pins):
                with self.assertRaisesRegex(ValueError,'New absolute'):
                    R.restore_fresh(asset,genome.resolve(),build['asset_sha256'],build['complete_sha256'],genome.name)
                with self.assertRaisesRegex(RuntimeError,'OWNER_STOP'):
                    R.restore_fresh(asset,output,build['asset_sha256'],build['complete_sha256'],genome.name,stop)
            self.assertTrue(genome.exists());self.assertTrue(asset.exists());self.assertTrue(output.exists())


if __name__=='__main__':unittest.main()
