#!/usr/bin/env python3
"""Synthetic V2/source-acceptance guards; never issue a production certificate."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,unittest
import stage05_curation_atomic as A
import validate_atomic_curation as V

HERE=Path(__file__).resolve().parent

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True)+'\n',encoding='utf-8')

class SourceIdentityV2(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory(dir=HERE);self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.root=self.base/'canonical';self.here=self.base/'checker'
        self.root.mkdir();self.here.mkdir()
        self.panel=['TEST_'+str(i).zfill(8)+'.1' for i in range(196)];self.acc=self.panel[0]
        self.approved=self.root/'config/approved_accessions.txt';self.approved.parent.mkdir()
        self.approved.write_text('\n'.join(self.panel)+'\n',encoding='ascii');self.panel_sha=A.sha(self.approved)
        self.source=self.root/'.work/source';self.receipt=self.source/'assemblies'/self.acc/'build_receipt.json'
        write(self.receipt,{'dataset_kind':'SYNTHETIC','assembly_accession':self.acc,'payload':'original'})
        control=self.root/'reports/accepted_source.json';write(control,{'synthetic_accepted_source_control':True})
        self.witness={'sha256':A.sha(self.receipt),'bytes':self.receipt.stat().st_size,
            'member':'SYNTHETIC/source/'+self.acc+'/build_receipt.json','asset_name':'SYNTHETIC.zip',
            'asset_sha256':'a'*64,'remote_asset_id':1,'release_tag':'SYNTHETIC',
            'remote_asset_url':'https://example.invalid/SYNTHETIC.zip'}
        self.pins={'schema':'STAGE05_ACCEPTED_SOURCE_PINS_V1','approved_accessions_sha256':self.panel_sha,
            'accepted_files':{'reports/accepted_source.json':A.sha(control),'config/approved_accessions.txt':self.panel_sha},
            'source_receipts':{acc:deepcopy(self.witness) for acc in self.panel}}
        self.pinfile=self.here/'accepted_source_pins.json';write(self.pinfile,self.pins);self.pinsha=A.sha(self.pinfile)
        self.identity={'schema':'STAGE05_SINGLE_GENOME_SCIENTIFIC_IDENTITY_V2','accession':self.acc,
            'panel_sha256':self.panel_sha,'source_receipt_sha256':A.sha(self.receipt),
            'methods':'FULL_PADLOC5027_DF3_THREE_NATIVE_FAMILIES_RAW_INTEGRITY_ONLY',
            'source_acceptance':{'source_pins_sha256':self.pinsha,'accepted_files':deepcopy(self.pins['accepted_files']),
                                 'released_source_member':deepcopy(self.witness)}}
        for module,panelname in [(A,'PINNED_PANEL'),(V,'PANEL_SHA')]:
            for name,value in [('HERE',self.here),('SOURCE_PINS_SHA',self.pinsha),(panelname,self.panel_sha)]:
                p=patch.object(module,name,value);p.start();self.addCleanup(p.stop)

    def both(self,identity=None):
        identity=self.identity if identity is None else identity
        A.accepted_source_gate(self.root,identity,self.acc,self.receipt)
        V.verify_source_acceptance(identity,self.acc,self.root,self.receipt)

    def rejects_both(self,identity=None):
        identity=self.identity if identity is None else identity
        with self.assertRaises(ValueError):A.accepted_source_gate(self.root,identity,self.acc,self.receipt)
        with self.assertRaises(ValueError):V.verify_source_acceptance(identity,self.acc,self.root,self.receipt)

    def test_v2_source_acceptance_does_not_need_tree(self):
        self.both();self.assertNotIn('upstream',self.identity)
        self.assertFalse(list(self.root.rglob('*.nwk')))

    def test_old_or_missing_identity_schema_rejected(self):
        for schema in ['STAGE05_SINGLE_GENOME_SCIENTIFIC_IDENTITY_V1',None]:
            identity=deepcopy(self.identity)
            if schema is None:identity.pop('schema')
            else:identity['schema']=schema
            self.rejects_both(identity)

    def test_source_acceptance_is_exact_and_mandatory(self):
        for action in ['missing','receipt_witness','accepted_control']:
            identity=deepcopy(self.identity)
            if action=='missing':identity.pop('source_acceptance')
            elif action=='receipt_witness':identity['source_acceptance']['released_source_member']['sha256']='b'*64
            else:identity['source_acceptance']['accepted_files']['reports/accepted_source.json']='c'*64
            self.rejects_both(identity)

    def test_self_consistent_receipt_and_identity_replacement_rejected(self):
        write(self.receipt,{'dataset_kind':'SYNTHETIC','assembly_accession':self.acc,'payload':'replacement'})
        identity=deepcopy(self.identity);identity['source_receipt_sha256']=A.sha(self.receipt)
        identity['source_acceptance']['released_source_member'].update(sha256=A.sha(self.receipt),bytes=self.receipt.stat().st_size)
        self.rejects_both(identity)

    def test_pinfile_tampering_rejected_even_with_identity_replacement(self):
        pins=deepcopy(self.pins);pins['source_receipts'][self.acc]['sha256']='d'*64;write(self.pinfile,pins)
        identity=deepcopy(self.identity);identity['source_acceptance']['source_pins_sha256']=A.sha(self.pinfile)
        self.rejects_both(identity)

    def test_canonical_control_drift_rejected(self):
        write(self.root/'reports/accepted_source.json',{'synthetic_accepted_source_control':'replaced'})
        self.rejects_both()

    def test_documented_exception_source_uses_same_released_pin(self):
        V.verify_released_source(self.acc,self.root,self.receipt)
        write(self.receipt,{'dataset_kind':'SYNTHETIC','assembly_accession':self.acc,'payload':'replacement'})
        with self.assertRaises(ValueError):V.verify_released_source(self.acc,self.root,self.receipt)

    def test_full_atomic_bridge_accepts_v2_without_tree(self):
        genome=self.root/'.work/native'/self.acc;inv=genome/'inventory/attempt_0001/assemblies'/self.acc
        for name in A.INVENTORY_FILES:
            path=inv/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('SYNTHETIC_ONLY\n',encoding='ascii')
        freeze=genome/'execution/execution_freeze.json';write(freeze,{'scientific_identity':self.identity,'panel_sha256':self.panel_sha})
        raw=genome/'raw_validation/attempt_0001/validation.json'
        write(raw,{'status':'PASS_FULL_NATIVE_SEARCH_AND_SOURCE_ACCOUNTING_ONLY','architecture_curation':'NOT_RUN',
                   'assembly_accession':self.acc,'execution_freeze_sha256':A.sha(freeze)})
        files={p.relative_to(genome).as_posix():A.sha(p) for p in [*inv.iterdir(),freeze,raw]}
        complete={'schema':'STAGE05_ATOMIC_GENOME_COMPLETE_V1','state':'COMPLETE_VALIDATED','accession':self.acc,
            'validation_scope':'NATIVE_SEARCH_SOURCE_AND_RAW_INTEGRITY_ONLY','curation':'NOT_RUN','biological_absence_claim':'NONE',
            'scientific_identity':self.identity,'scientific_identity_sha256':A.object_sha(self.identity),'files':files,
            'inventory_directory':inv.relative_to(genome).as_posix(),'raw_validation_file':raw.relative_to(genome).as_posix()}
        write(genome/'complete.json',complete)
        self.assertEqual(A.atomic_gate(self.root,genome,self.acc,self.approved,self.source)[0],inv.parents[1])
        complete['scientific_identity']['schema']='STAGE05_SINGLE_GENOME_SCIENTIFIC_IDENTITY_V1'
        complete['scientific_identity_sha256']=A.object_sha(complete['scientific_identity']);write(genome/'complete.json',complete)
        with self.assertRaises(ValueError):A.atomic_gate(self.root,genome,self.acc,self.approved,self.source)

if __name__=='__main__':unittest.main()
