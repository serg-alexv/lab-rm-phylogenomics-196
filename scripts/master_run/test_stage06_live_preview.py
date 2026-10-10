"""Pure disposable-C synthetic contracts; no real biological acceptance or WSL."""
from pathlib import Path
import contextlib, copy, io, json, shutil, sys, tempfile, unittest
from unittest.mock import patch
import stage06_live_preview as P

class Preview(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=P.WORK);self.addCleanup(self.tmp.cleanup)
        self.work=Path(self.tmp.name);self.patch=patch.object(P,'WORK',self.work);self.patch.start();self.addCleanup(self.patch.stop)
        for relative in P.PINS:
            source=Path(__file__).resolve().parent/relative;target=self.work/relative
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        self.panel=[f'GCF_{i:09d}.1' for i in range(1,197)]
        self.write('approved.txt','\n'.join(self.panel)+'\n',raw=True)
        self.write('tree.nwk','('+','.join(a+':0.1' for a in self.panel)+');\n',raw=True)
        self.panel_sha=P.sha((self.work/'approved.txt').read_bytes());self.tree_sha=P.sha((self.work/'tree.nwk').read_bytes())
        self.write('tree_acceptance.json',{'state':'PASS_FRESH_REMOTE_ACCEPTED_PRIMARY196_FULL_PAYLOAD','independent_remote_gate_passed':True,
          'members':[{'member':'accepted/host.treefile','sha256':self.tree_sha,'crc_verified':True},
          {'member':'accepted/accepted_approved_accessions.txt','sha256':self.panel_sha,'crc_verified':True}]})
        for name,value in [('PANEL_SHA',self.panel_sha),('TREE_SHA',self.tree_sha),('TREE_ACCEPTANCE_SHA',P.sha((self.work/'tree_acceptance.json').read_bytes()))]:
            patcher=patch.object(P,name,value);patcher.start();self.addCleanup(patcher.stop)
        self.doc={'schema':'RM_LIVE_PREVIEW_SNAPSHOT_V1','tree':self.spec('tree.nwk'),'approved':self.spec('approved.txt'),
          'tree_acceptance':self.spec('tree_acceptance.json'),'accepted_genomes':[],
          'pending':[{'accession':self.panel[1],'execution_state':'DEFERRED_RESOURCE','reason':'Synthetic queue metadata; no actual run.'}]}

    def write(self,name,value,raw=False):
        path=self.work/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(value if raw else json.dumps(value),encoding='utf-8',newline='\n');return path

    def spec(self,name):
        path=self.work/name;return {'path':str(path),'sha256':P.sha(path.read_bytes())}

    def snapshot(self):
        path=self.write('snapshot.json',self.doc);return path,P.sha(path.read_bytes())

    def accepted(self):
        a=self.panel[0];M=P.module('preview_test_serializer','stage05_curation/rm_matrix.py');rows=[M.initial(a,t) for t in P.KINDS]
        for row in rows:row['required_detector_completion']={'PADLOC':M.SEARCH,'DefenseFinder':M.SEARCH};row['review_execution']='COMPLETE_ALL_REQUIRED_EVIDENCE_REVIEW'
        rows[0].update(state='COMPLETE_PREDICTED',complete_predicted_count=1,candidate_counts={'COMPLETE_PREDICTED':1},candidate_ids=['synthetic-positive'],coverage_unresolved=False)
        rows[1].update(state='NOT_DETECTED_AFTER_SUCCESSFUL_SEARCH',coverage_unresolved=False)
        rows[2].update(state='UNCERTAIN',candidate_counts={'UNCERTAIN':1},candidate_ids=['synthetic-uncertain'])
        rows[3].update(state='CURATED_PARTIAL',curated_partial_count=1,candidate_counts={'CURATED_PARTIAL':1},candidate_ids=['synthetic-partial'])
        self.write('accepted/cells.json',rows)
        manifest={'schema':'RM_SINGLE_GENOME_INDEPENDENT_CURATION_SOURCE_MANIFEST_V1','dataset_kind':'PRODUCTION','accession':a,
          'approved_sha256':self.panel_sha,'wrapper_sha256':P.WRAPPER_SHA,'independent_checker_sha256':P.CURATION_CHECKER_SHA,
          'functional_activity_claim':'NONE','audit':{'complete_sha256':'1'*64}}
        self.write('accepted/manifest.json',manifest)
        cert={'schema':'RM_SINGLE_GENOME_INDEPENDENT_CURATION_ACCEPTANCE_V1','status':'PASS_INDEPENDENT_SINGLE_GENOME_RM_CURATION',
          'dataset_kind':'PRODUCTION','accession':a,'accepted_single_genome_curation':True,'accession_count':1,'cell_count':4,
          'approved_accession_count':196,'approved_sha256':self.panel_sha,'cells_sha256':self.spec('accepted/cells.json')['sha256'],
          'source_manifest_sha256':self.spec('accepted/manifest.json')['sha256'],'wrapper_sha256':P.WRAPPER_SHA,
          'independent_checker_sha256':P.CURATION_CHECKER_SHA,'per_genome_owned_native_closure_verified':True,
          'operational_closure_scope':'SELECTED_GENOME_MANIFEST_PINNED_LINUX_NATIVE_LAUNCHES_ONLY','full_panel_complete':False,
          'final_matrix_acceptance':False,'final_figure_acceptance':False,'functional_activity_claim':'NONE','biological_searches_repeated':0,'complete_receipt_sha256':'1'*64}
        self.write('accepted/receipt.json',cert)
        entry={'accession':a,'receipt':self.spec('accepted/receipt.json'),'cells':self.spec('accepted/cells.json'),'source_manifest':self.spec('accepted/manifest.json')}
        self.doc['accepted_genomes']=[entry];return cert,entry

    def test_default_NOOP_does_not_read_inputs(self):
        with patch.object(sys,'argv',['preview']),patch.object(P,'inputs',side_effect=AssertionError('must not read')),contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(P.main(),0)
        self.assertEqual(json.loads(stdout.getvalue())['state'],'NO_OP_PROVISIONAL_STAGE06_PREVIEW')

    def test_partial_exact196_join_pending_remains_NA(self):
        self.accepted();*_,wide,long,reviews,pins,paths,sources=P.inputs(*self.snapshot())
        self.assertEqual((len(wide),len(long)),(196,784));self.assertEqual([wide[0]['Type_'+t] for t in P.KINDS],['1','0','NA','NA'])
        self.assertTrue(all(row['Type_'+t]=='NA' for row in wide[1:] for t in P.KINDS))
        self.assertEqual(reviews[1]['reported_execution_state'],'DEFERRED_RESOURCE')

    def test_raw_or_unclosed_receipt_cannot_be_accepted(self):
        cert,entry=self.accepted()
        for key,value in [('status','COMPLETE_VALIDATED'),('accepted_single_genome_curation',False),('per_genome_owned_native_closure_verified',False),('final_figure_acceptance',True),('accession_count',True)]:
            bad=dict(cert);bad[key]=value;self.write('accepted/receipt.json',bad);entry['receipt']=self.spec('accepted/receipt.json')
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'accepted closed four-cell'):
                P.inputs(*self.snapshot())

    def test_changed_cells_and_duplicate_accession_rejected(self):
        _,entry=self.accepted();self.write('accepted/cells.json',[])
        with self.assertRaisesRegex(ValueError,'SHA differs'):P.inputs(*self.snapshot())
        self.accepted();self.doc['accepted_genomes']*=2
        with self.assertRaisesRegex(ValueError,'Duplicate'):P.inputs(*self.snapshot())

    def test_changed_tree_or_nonapproved_panel_rejected(self):
        self.write('tree.nwk','(bad:1,other:1);',raw=True);self.doc['tree']=self.spec('tree.nwk')
        with self.assertRaisesRegex(ValueError,'accepted tree/panel'):P.inputs(*self.snapshot())

    def test_vector_exports_explicit_preview_no_final_certificates(self):
        self.accepted();snapshot,pin=self.snapshot();out=self.work/'preview'
        manifest=P.render(snapshot,pin,out)
        self.assertEqual(manifest['schema'],'RM_PROVISIONAL_STAGE06_EXPORT_V1');self.assertFalse(manifest['final_figure_acceptance'])
        self.assertEqual(manifest['accepted_genome_count'],1);self.assertEqual(manifest['cell_count'],784)
        self.assertIn(P.WATERMARK,(out/'preview_circular_rm.svg').read_text())
        from pypdf import PdfReader
        self.assertIn(P.WATERMARK,PdfReader(out/'preview_circular_rm.pdf').pages[0].extract_text())
        self.assertEqual((out/'host_tree.nwk').read_bytes(),(self.work/'tree.nwk').read_bytes())
        self.assertFalse((out/'curation_validation.json').exists());self.assertFalse((out/'provenance.json').exists())
        self.assertTrue(all(P.WATERMARK in p.read_text() for p in out.glob('itol_*.txt')))

if __name__=='__main__':unittest.main()
