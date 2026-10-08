"""Synthetic negative/regression cases plus an installed-native R oracle input."""
import copy
import json
from pathlib import Path
import unittest
import stage05_padloc_selection_v3 as S

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.work/stage05_selection_v3_review'
OUT.mkdir(parents=True, exist_ok=True)
CASES = []


def source(key='A|R|L1', lo=1, hi=99, strand=1):
    a, r, l = key.split('|')
    return {'assembly_accession': a, 'replicon': r, 'locus_tag': l,
            'derived_linear_order_start_one_based': str(lo), 'derived_linear_order_end_one_based': str(hi),
            'gbff_strand': str(strand)}


def hit(profile='P', ie=1e-20, key='A|R|L1', roles=('core_genes',), model='M', passed=True,
        hlo=1, hhi=80, alo=1, ahi=160):
    return {'detector': 'PADLOC', 'locus_key': key, 'profile_name': profile, 'target_length': 200,
            'native_role_threshold_passed': passed,
            'native_model_roles': [{'model': model, 'role_class': role, 'role': profile} for role in roles],
            'domain': {'target_name': key, 'profile_name': profile, 'independent_evalue': str(ie),
                       'profile_length': '100', 'hmm_from': str(hlo), 'hmm_to': str(hhi),
                       'alignment_from': str(alo), 'alignment_to': str(ahi)}}


def oracle_case(name, hits, sources, expected, native_roles=None, aliases=None):
    original = copy.deepcopy(hits)
    S.padloc_selection_facts(hits, sources)
    selected = sorted(k for k, v in hits.items() if v['native_role_threshold_passed'])
    if selected != sorted(expected):
        raise AssertionError((name, selected, expected))
    models = sorted({r['model'] for v in original.values() for r in v['native_model_roles']})
    for model in models:
        roles = {c: [] for c in S.ROLE_CLASSES}
        rows = []
        metadata = []
        for hid, h in original.items():
            if h['detector'] != 'PADLOC':
                continue
            d = h['domain']; src = sources[h['locus_key']]
            for assignment in h['native_model_roles']:
                if assignment['model'] == model:
                    roles[assignment['role_class']].append(h['profile_name'])
            hcov = (int(d['hmm_to'])-int(d['hmm_from']))/int(d['profile_length'])
            tcov = (int(d['alignment_to'])-int(d['alignment_from']))/h['target_length']
            rows.append({'fixture_hit_id': hid, 'seqid': src['replicon'],
                         'start': int(src['derived_linear_order_start_one_based']),
                         'end': int(src['derived_linear_order_end_one_based']),
                         'strand': src['gbff_strand'], 'target.name': h['locus_key'],
                         'protein.name': h['profile_name'], 'hmm.name': h['profile_name'],
                         'hmm.accession': h['profile_name'], 'domain.number': 1,
                         'domain.iE.value': float(d['independent_evalue']),
                         'hmm.coverage': round(hcov, 3), 'target.coverage': round(tcov, 3),
                         'hmm.coverage.threshold': 0 if h['native_role_threshold_passed'] else 2,
                         'target.coverage.threshold': 0, 'e.value.threshold': 1,
                         'combined.coverage': hcov+tcov, 'target.description': 'SYNTHETIC_ONLY'})
            metadata.append({'system.definition.shortcut': h['profile_name'], 'protein.name': h['profile_name']})
        if native_roles is not None:
            roles = native_roles
        if aliases is not None:
            metadata = aliases
        # Native selection is per assembly. Separate assemblies are separate
        # PADLOC invocations, not one synthetic merged input to the R oracle.
        if len({sources[v['locus_key']]['assembly_accession'] for v in original.values()}) > 1:
            continue
        CASES.append({'case_id': name+'/'+model, 'system_param': dict(roles, maximum_separation=1, minimum_core=1, minimum_total=1),
                      'native_rows': rows, 'hmm_meta': metadata,
                      'expected_hit_ids': sorted(k for k, h in hits.items() if model in h.get('native_selected_model_ids', []))})


class SelectionTests(unittest.TestCase):
    def check_case(self, name, hits, expected, sources=None, **kwargs):
        sources = sources or {v['locus_key']: source(v['locus_key']) for v in hits.values()}
        oracle_case(name, hits, sources, expected, **kwargs)

    def test_min_domain_before_numerical_filter(self):
        self.check_case('min_domain_before_filter', {'low': hit(passed=False), 'high': hit(ie=1e-10)}, [])

    def test_top5_before_priority(self):
        h = {str(i): hit(profile='P'+str(i), ie=10**(-20+i), roles=('secondary_genes',) if i<5 else ('core_genes',)) for i in range(6)}
        self.check_case('top5_before_priority', h, ['0'])

    def test_top5_ties(self):
        h = {str(i): hit(profile='P'+str(i), roles=('secondary_genes',) if i<5 else ('core_genes',)) for i in range(6)}
        self.check_case('top5_ties', h, ['5'])

    def test_core_precedes_secondary(self):
        self.check_case('core_precedes_secondary', {'c': hit(ie=1e-10), 's': hit(profile='Q', roles=('secondary_genes',))}, ['c'])

    def test_coincident_distinct_loci_grouped(self):
        self.check_case('coincident_loci', {'a': hit(), 'b': hit(profile='Q', key='A|R|L2', ie=1e-10)}, ['a'])

    def test_coincident_opposite_strands_grouped(self):
        self.check_case('opposite_strands', {'a': hit(), 'b': hit(profile='Q', key='A|R|L2', ie=1e-10)}, ['a'],
                        {'A|R|L1': source(), 'A|R|L2': source('A|R|L2', strand=-1)})

    def test_same_profile_coincident_loci_minimum(self):
        self.check_case('same_profile_coincident', {'a': hit(), 'b': hit(key='A|R|L2', ie=1e-10)}, ['a'])

    def test_different_replicons_preserved(self):
        self.check_case('different_replicons', {'a': hit(), 'b': hit(key='A|R2|L1')}, ['a', 'b'])

    def test_different_coordinates_preserved(self):
        self.check_case('different_coordinates', {'a': hit(), 'b': hit(key='A|R|L2')}, ['a', 'b'],
                        {'A|R|L1': source(), 'A|R|L2': source('A|R|L2', lo=100, hi=200)})

    def test_different_assemblies_preserved(self):
        self.check_case('different_assemblies', {'a': hit(), 'b': hit(key='B|R|L1')}, ['a', 'b'])

    def test_model_scopes_separate(self):
        self.check_case('models_separate', {'a': hit(model='M1'), 'b': hit(profile='Q', model='M2')}, ['a', 'b'])

    def test_prohibited_removes_secondary(self):
        self.check_case('prohibited_removes_secondary', {'p': hit(roles=('secondary_genes', 'prohibited_genes')),
                                                       'n': hit(profile='Q', roles=('neutral_genes',), ie=1e-10)}, ['n'])

    def test_prohibited_removes_neutral(self):
        self.check_case('prohibited_removes_neutral', {'p': hit(roles=('neutral_genes', 'prohibited_genes')),
                                                     'n': hit(profile='Q', roles=('neutral_genes',), ie=1e-10)}, ['n'])

    def test_core_removes_prohibited(self):
        self.check_case('core_removes_prohibited', {'c': hit(roles=('core_genes', 'prohibited_genes'), ie=1e-10),
                                                  's': hit(profile='Q', roles=('secondary_genes',))}, ['c'])

    def test_alias_expansion_matches_effective_roles(self):
        self.check_case('alias_expansion', {'c': hit(ie=1e-10), 's': hit(profile='Q', roles=('secondary_genes',))}, ['c'],
                        native_roles={'core_genes': ['CORE_ALIAS'], 'secondary_genes': ['Q'], 'neutral_genes': [], 'prohibited_genes': []},
                        aliases=[{'system.definition.shortcut': 'CORE_ALIAS', 'protein.name': 'P'},
                                 {'system.definition.shortcut': 'Q', 'protein.name': 'Q'}])

    def test_coverage_before_stable_order(self):
        self.check_case('combined_coverage', {'a': hit(hhi=75), 'b': hit(profile='Q', hhi=80)}, ['b'])

    def test_stable_order_final_tie(self):
        self.check_case('stable_order', {'a': hit(), 'b': hit(profile='Q')}, ['a'])

    def test_unknown_profile_not_selected(self):
        self.check_case('unmapped_profile', {'a': hit(roles=())}, [])

    def test_source_target_disagreement_rejects(self):
        h = hit(); h['domain']['target_name'] = 'A|R|L2'
        with self.assertRaises(ValueError): S.padloc_selection_facts({'a': h}, {'A|R|L1': source()})

    def test_missing_source_rejects(self):
        with self.assertRaises(ValueError): S.padloc_selection_facts({'a': hit()}, {})

    def test_invalid_source_geometry_rejects(self):
        for lo, hi in [(0,99),(100,99),(True,99)]:
            with self.subTest(lo=lo, hi=hi), self.assertRaises(ValueError):
                S.padloc_selection_facts({'a':hit()}, {'A|R|L1':source(lo=lo,hi=hi)})

    def test_nonfinite_negative_evalues_reject(self):
        for ie in [float('nan'), float('inf'), -1]:
            with self.subTest(ie=ie), self.assertRaises(ValueError):
                S.padloc_selection_facts({'a':hit(ie=ie)}, {'A|R|L1':source()})

    def test_unknown_role_rejects(self):
        with self.assertRaises(ValueError): S.padloc_selection_facts({'a':hit(roles=('invented',))}, {'A|R|L1':source()})

    def test_nonboolean_filter_rejects(self):
        with self.assertRaises(ValueError): S.padloc_selection_facts({'a':hit(passed='True')}, {'A|R|L1':source()})


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SelectionTests))
    if result.wasSuccessful():
        (OUT/'native_oracle_fixtures.json').write_text(json.dumps({'status':'SYNTHETIC_ONLY_NO_BIOLOGICAL_JOBS','cases':CASES}, indent=2)+'\n', encoding='utf-8')
    (OUT/'python_test_results.json').write_text(json.dumps({'status':'PASS_SYNTHETIC_ONLY' if result.wasSuccessful() else 'FAILED_SYNTHETIC_ONLY',
                'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'native_cases_prepared':len(CASES),
                'production_adoption':'NOT_ADOPTED','biological_HMM_searches':0}, indent=2)+'\n', encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)
