"""Pure incremental-checker gate fixtures; no production input, runtime or native job."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import copy
import importlib.util
import unittest

spec = importlib.util.spec_from_file_location('single_genome_independent_wrapper', Path(__file__).with_name('validate_one_atomic_curation.py'))
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


class Contracts(unittest.TestCase):
    def fixture(self):
        panel = [f'GCF_{i:09d}.1' for i in range(196)]
        C = SimpleNamespace(STATES={'UNCERTAIN'})
        V = SimpleNamespace(PANEL_SHA='p'*64, SCOPE_SHA='s'*64, SOURCE_VALIDATION_SHA='v'*64,
                            CORE_SHA='c'*64, DEPENDENCY_PINS={'retained/fake.py':'d'*64},
                            core=Mock(return_value=C), native_provenance=Mock(return_value='r'*64))
        settings = {k:'/SYNTHETIC/'+k for k in ('root','source','source_validation','approved','policy','models','padloc_db',
                    'environment','reviews','producer_source','atomic_runner_source','supervisor_source','runtime_manifest','review_directory','genome_root')}
        settings.update(schema='RM_CURATION_AUDIT_SETTINGS_V1', dataset_kind='PRODUCTION')
        hashes = {str(M.HERE/'pinned_model_candidate_scope.json'):V.SCOPE_SHA,
                  str(M.HERE/'retained/fake.py'):'d'*64, settings['approved']:V.PANEL_SHA,
                  settings['source_validation']:V.SOURCE_VALIDATION_SHA, settings['producer_source']:M.PRODUCER_SHA,
                  str(M.HERE/'validate_atomic_curation.py'):M.CHECKER_SHA}
        hashes = {str(Path(k)):v for k,v in hashes.items()}
        digest = lambda p: hashes.get(str(Path(p)),'a'*64)
        source_validation = dict(status='PASS_SOURCE_LOCUS_INPUT_TRACEABILITY', complete_exact196_accounting=True,
                                 panel_sha256=V.PANEL_SHA, assemblies_passed=196)
        V.read = Mock(side_effect=lambda p: source_validation if str(p)==settings['source_validation'] else settings)
        with patch.object(M,'sha',side_effect=digest),patch.object(Path,'read_text',return_value='\n'.join(panel)):
            _,contract,entry=M.contract_from_settings(settings,panel[0],V)
        cells=[dict(assembly_accession=panel[0],rm_type=t,state='UNCERTAIN') for t in M.TYPES]
        V.atomic_one=Mock(return_value=(cells,{'synthetic':True}))
        return panel,C,V,settings,hashes,digest,source_validation,contract,entry,cells

    def test_exact_frozen_panel_and_selected_closed_entry(self):
        panel,C,V,settings,hashes,digest,source,contract,entry,cells=self.fixture()
        self.assertEqual(entry['accession'],panel[0])
        self.assertEqual(contract['producer_sha256'],M.PRODUCER_SHA)
        with patch.object(M,'sha',side_effect=digest),patch.object(Path,'read_text',return_value='\n'.join(panel)):
            with self.assertRaises(ValueError):M.contract_from_settings(settings,'GCF_999999999.1',V)

    def test_closed_only_rejects_selected_exception_and_missing_runtime(self):
        panel,C,V,settings,hashes,digest,source,contract,entry,cells=self.fixture()
        for change in ({'exception_records':{panel[0]:'SYNTHETIC'}},{'runtime_manifest':None}):
            with patch.object(M,'sha',side_effect=digest),patch.object(Path,'read_text',return_value='\n'.join(panel)),self.assertRaises(ValueError):
                M.contract_from_settings({**settings,**change},panel[0],V)

    def test_changed_producer_rejected_before_acceptance(self):
        panel,C,V,settings,hashes,digest,source,contract,entry,cells=self.fixture()
        hashes[str(Path(settings['producer_source']))]='x'*64
        with patch.object(M,'sha',side_effect=digest),patch.object(Path,'read_text',return_value='\n'.join(panel)),self.assertRaises(ValueError):
            M.contract_from_settings(settings,panel[0],V)

    def test_all_static_and_native_gates_are_required(self):
        panel,C,V,settings,hashes,digest,source,contract,entry,cells=self.fixture()
        with patch.object(M,'sha',side_effect=digest):
            actual,runtime=M.outer_gates(panel,contract,V)
        self.assertIs(actual,C);self.assertEqual(runtime,'r'*64);V.native_provenance.assert_called_once_with(contract)
        for path in (M.HERE/'pinned_model_candidate_scope.json',M.HERE/'retained/fake.py',settings['source_validation'],settings['approved']):
            path=Path(path);prior=hashes[str(path)];hashes[str(path)]='x'*64;V.native_provenance.reset_mock()
            with patch.object(M,'sha',side_effect=digest),self.assertRaises(ValueError):M.outer_gates(panel,contract,V)
            V.native_provenance.assert_not_called();hashes[str(path)]=prior

    def test_source_validation_state_and_runtime_failure_do_not_reach_atomic(self):
        panel,C,V,settings,hashes,digest,source,contract,entry,cells=self.fixture()
        source['complete_exact196_accounting']=False
        with patch.object(M,'sha',side_effect=digest),self.assertRaises(ValueError):M.outer_gates(panel,contract,V)
        V.native_provenance.assert_not_called();source['complete_exact196_accounting']=True
        V.native_provenance.side_effect=ValueError('SYNTHETIC changed native runtime')
        with patch.object(M,'sha',side_effect=digest),self.assertRaises(ValueError):M.outer_gates(panel,contract,V)
        V.atomic_one.assert_not_called()

    def test_exact_four_rejects_missing_duplicate_wrong_accession_and_state(self):
        panel,C,V,settings,hashes,digest,source,contract,entry,cells=self.fixture()
        M.exact_four(cells,panel[0],C)
        for wrong in (cells[:-1],cells[:-1]+[cells[0]],[{**c,'assembly_accession':'SYNTHETIC_OTHER'} for c in cells],
                      [{**c,'state':'FABRICATED'} for c in cells]):
            with self.assertRaises(ValueError):M.exact_four(wrong,panel[0],C)

    def test_gated_single_acceptance_cannot_claim_full_panel(self):
        panel,C,V,settings,hashes,digest,source,contract,entry,cells=self.fixture()
        with patch.object(M,'load_checker',return_value=V),patch.object(M,'sha',side_effect=digest),patch.object(Path,'read_text',return_value='\n'.join(panel)):
            receipt,manifest,actual=M.run('/SYNTHETIC/settings',panel[0])
        V.native_provenance.assert_called_once();V.atomic_one.assert_called_once()
        self.assertEqual(actual,cells);self.assertEqual(receipt['cell_count'],4)
        self.assertTrue(receipt['accepted_single_genome_curation'])
        self.assertFalse(receipt['full_panel_complete'] or receipt['final_matrix_acceptance'] or receipt['final_figure_acceptance'])
        self.assertNotEqual(receipt['schema'],'RM_INDEPENDENT_CURATION_ACCEPTANCE_V1')
        self.assertEqual(manifest['approved_accession_count'],196)


if __name__=='__main__':unittest.main()
