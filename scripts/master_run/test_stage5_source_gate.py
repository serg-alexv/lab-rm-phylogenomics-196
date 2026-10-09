"""Focused synthetic source/cache gates; no native launch, WSL or genome data."""
from pathlib import Path
from unittest import mock
import copy, tempfile, unittest
import stage5_atomic as R
from stage5_atomic_process import Fatal, atomic_json, read_json


class SourceGate(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='stage5_source_synthetic_',dir=Path(__file__).parent)
        self.root=Path(self.tmp.name).resolve();self.accession='GCF_000000001.1'
        panel=['GCF_'+str(i).zfill(9)+'.1' for i in range(1,197)]
        (self.root/'config').mkdir();self.panel=self.root/'config/approved_accessions.txt'
        self.panel.write_text('\n'.join(panel)+'\n',encoding='ascii')
        self.panel_patch=mock.patch.object(R,'PINNED_PANEL',R.sha(self.panel));self.panel_patch.start()
        self.write('config/approval.json',{'human_approval':'APPROVED_FOR_SEQUENCE_ANALYSIS',
            'approved_assembly_count':196,'pilot':False,'panel_accessions_sha256':R.PINNED_PANEL})
        self.write('reports/stage02/validation_summary.json',{'status':'PASS_SEQUENCE_INTEGRITY_WITH_DOCUMENTED_EXCEPTIONS',
            'approved_assemblies':196,'raw_packages_present':196,'assemblies_reported':196,
            'complete_exact196_accounting':True,'error_count':0,'assemblies_with_errors':0,'approved_accessions_sha256':R.PINNED_PANEL})
        for stage,tag in [('stage02','stage02-sequences196-v1'),('stage03','stage03-hostmarkers196-v1')]:
            self.write('reports/'+stage+'/publication_receipt.json',{'status':'UPLOAD_VERIFIED','release_tag':tag,
                'approved_assemblies':196,'remote_tag_commit_verified':True,
                'assets':[{'download_readback_verified':True,'all_zip_member_hashes_verified':True}]})
        self.builder={'panel_sha256':R.PINNED_PANEL,'stage02_validation_summary_sha256':R.sha(self.root/'reports/stage02/validation_summary.json')}
        self.validation=self.write('.work/stage03_source_validation/validation_summary.json',{'status':'PASS_SOURCE_LOCUS_INPUT_TRACEABILITY',
            'assemblies_passed':196,'assemblies_audited':196,'required_assemblies':196,'complete_exact196_accounting':True,
            'panel_sha256':R.PINNED_PANEL,'failed_assemblies':[],'global_errors':[],'builder_identity':self.builder})
        self.source=self.root/'.work/source_locus_inputs_v1/assemblies'/self.accession;self.source.mkdir(parents=True)
        self.payload=self.source/'synthetic_source.txt';self.payload.write_text('SYNTHETIC NO BIOLOGICAL SEQUENCE')
        self.receipt=self.source/'build_receipt.json'
        atomic_json(self.receipt,{'status':'SOURCE_LOCUS_INPUTS_CONSTRUCTED','assembly_accession':self.accession,'identity':self.builder,
            'output_files':[{'path':self.payload.name,'bytes':self.payload.stat().st_size,'sha256':R.sha(self.payload)}]})
        accepted=['config/approved_accessions.txt','config/approval.json','reports/stage02/validation_summary.json',
                  'reports/stage02/publication_receipt.json','reports/stage03/publication_receipt.json',
                  '.work/stage03_source_validation/validation_summary.json']
        witness={'sha256':R.sha(self.receipt),'bytes':self.receipt.stat().st_size,'member':'SYNTHETIC_MEMBER'}
        self.pins={'accepted_files':{name:R.sha(self.root/name) for name in accepted},
                   'source_receipts':{a:copy.deepcopy(witness) for a in panel}}
        self.config={'schema':'STAGE05_ATOMIC_CONFIG_V2','source':str(self.root/'.work/source_locus_inputs_v1'),
                     'source_validation':str(self.validation),'runtime':{'manifest_sha256':'a'*64},
                     'stage4_primary':{'state':'NOT_RUN','validation_path':'MUST_NOT_BE_OPENED'},'resource_policy':{'reserve':1}}
        self.pin_patch=mock.patch.object(R,'accepted_source_pins',return_value=self.pins);self.pin_patch.start()

    def tearDown(self):
        self.pin_patch.stop();self.panel_patch.stop();self.tmp.cleanup()

    def write(self,relative,value):
        path=self.root/relative;path.parent.mkdir(parents=True,exist_ok=True);atomic_json(path,value);return path

    def gate(self):return R.validate_genome_inputs(self.config,self.root,self.accession)

    def test_accepted_source_passes_with_final_stage4_not_run_or_absent(self):
        with mock.patch.object(R,'validate_upstream',side_effect=AssertionError('No tree dependency')):
            source,gate,receipt,acceptance=self.gate();self.assertEqual(source,self.source)
            self.assertEqual(acceptance['released_source_member']['sha256'],R.sha(self.receipt))
            del self.config['stage4_primary'];self.gate()

    def test_self_consistent_source_replacement_rejects_original_released_receipt_pin(self):
        self.payload.write_text('CHANGED SYNTHETIC PAYLOAD')
        receipt=read_json(self.receipt);receipt['output_files'][0].update(bytes=self.payload.stat().st_size,sha256=R.sha(self.payload))
        atomic_json(self.receipt,receipt)
        with self.assertRaisesRegex(Fatal,'released member'):self.gate()

    def test_source_payload_hash_drift_rejects(self):
        self.payload.write_text('CHANGED')
        with self.assertRaisesRegex(Fatal,'Hash drift'):self.gate()

    def test_changed_global_source_acceptance_rejects(self):
        changed=read_json(self.validation);changed['assemblies_passed']=195;atomic_json(self.validation,changed)
        with self.assertRaisesRegex(Fatal,'Hash drift'):self.gate()

    def test_sequence_acceptance_claim_cannot_override_failed_integrity(self):
        path=self.root/'reports/stage02/validation_summary.json';value=read_json(path);value['error_count']=1;atomic_json(path,value)
        self.pins['accepted_files']['reports/stage02/validation_summary.json']=R.sha(path)
        with self.assertRaisesRegex(Fatal,'Stage2 sequence'):self.gate()

    def test_incomplete_existing_source_publication_rejects(self):
        relative='reports/stage03/publication_receipt.json';path=self.root/relative;value=read_json(path)
        value['assets'][0]['download_readback_verified']=False;atomic_json(path,value);self.pins['accepted_files'][relative]=R.sha(path)
        with self.assertRaisesRegex(Fatal,'release/readback'):self.gate()

    def test_unapproved_accession_cannot_enter_source_gate(self):
        with self.assertRaisesRegex(Fatal,'outside'):R.validate_genome_inputs(self.config,self.root,'GCF_999999999.1')

    def test_source_roles_cannot_point_at_other_cache(self):
        self.config['source']=str(self.root/'old_cache')
        with self.assertRaisesRegex(Fatal,'source roles'):self.gate()

    def test_source_directory_symlink_is_not_an_accepted_alias(self):
        with mock.patch.object(Path,'is_symlink',autospec=True,side_effect=lambda path:path==self.source):
            with self.assertRaisesRegex(Fatal,'symlinks'):self.gate()

    def test_native_identity_ignores_host_tree_and_operational_resource_changes(self):
        acceptance=self.gate()[3]
        first=R.genome_scientific_identity(self.config,self.accession,R.sha(self.receipt),acceptance)
        self.config.update(stage4_primary={'state':'COMPLETE_VALIDATED','tree_sha256':'b'*64},resource_policy={'reserve':999,'timeout':800})
        second=R.genome_scientific_identity(self.config,self.accession,R.sha(self.receipt),acceptance)
        self.assertEqual(first,second);self.assertEqual(first['schema'],'STAGE05_SINGLE_GENOME_SCIENTIFIC_IDENTITY_V2')
        self.assertNotIn('upstream',first);self.assertNotIn('resource_policy',first)
        self.config['runtime']['manifest_sha256']='c'*64
        self.assertNotEqual(first,R.genome_scientific_identity(self.config,self.accession,R.sha(self.receipt),acceptance))
        self.assertNotEqual(first,R.genome_scientific_identity(self.config,self.accession,'d'*64,acceptance))


class FrozenSourceAcceptance(unittest.TestCase):
    def test_actual_standalone_source_manifest_pins_all196_released_receipts(self):
        pins=R.accepted_source_pins();self.assertEqual(len(pins['source_receipts']),196)
        self.assertEqual(pins['source_validation_release_member']['sha256'],
                         pins['accepted_files']['.work/stage03_source_validation/validation_summary.json'])
        self.assertTrue(all(row['release_tag']=='stage03-hostmarkers196-v1' and row['member']==
            'source_locus_inputs/assemblies/'+accession+'/build_receipt.json' for accession,row in pins['source_receipts'].items()))

    def test_old_tree_coupled_native_config_is_not_silently_adopted(self):
        config=read_json(Path(R.__file__).with_name('stage5_atomic_config.template.json'))
        config['schema']='STAGE05_ATOMIC_CONFIG_V1'
        with tempfile.TemporaryDirectory(prefix='stage5_old_config_synthetic_',dir=Path(__file__).parent) as folder:
            path=Path(folder)/'config.json';atomic_json(path,config)
            with self.assertRaisesRegex(Fatal,'source-gated native V2'):R.load_config(path)


if __name__=='__main__':unittest.main()
