"""Independent frozen-source and disposable-C preview review; no real rendering."""
from pathlib import Path
import ast, contextlib, csv, hashlib, importlib, io, json, runpy, sys
import unittest
from unittest.mock import patch

WORK = Path(__file__).resolve().parent
PINS = {
    'stage06_live_preview.py': '49171dd82ed050d3f35daf82217c6ac747ef137c125691787c4f3bb0526034b8',
    'test_stage06_live_preview.py': 'dc3239dea5b82d47a3dcb15eb4533d70662402af80847f9e1fe861c8d0ce63f4',
    'STAGE06_LIVE_PREVIEW_PREPARATION01.md': 'ad999331a47d43a80c32c72095a5e18e87cf2ffd63b1a8da98bbe72e57370a80',
    'stage06_render.py': '55cdbed8829296379d4c8a114885643fc7debc3c98382be177e9adeb7edfb1cc',
    'stage05_curation/rm_matrix.py': '7716f722f25b582af990469d4e5120d4de22828b87c89cf334d2d9f9723c7db9',
    'check_stage06_outputs.py': '3a23f3de7d971bea6210cd2405c57af48fa5ba3ae2ba4bb66ee4357aa3644818',
    'stage05_curation/validate_one_atomic_curation.py': 'cdd81d2870dbc7c03845721199a98d4f6b51a23fb94ebb19fa71311bb9e2ed66',
    'stage05_curation/validate_atomic_curation.py': '89a42d63401ef1ef3479690546a3c8cad4da679517aa2ed7da6b4e6716b6af0c',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for name, pin in PINS.items():
        assert digest(WORK/name) == pin, name
    sys.path.insert(0, str(WORK))
    P = importlib.import_module('stage06_live_preview')
    T = importlib.import_module('test_stage06_live_preview')
    log = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromModule(T)
    result = unittest.TextTestRunner(stream=log).run(suite)
    assert result.wasSuccessful() and result.testsRun == 6, log.getvalue()
    checks = []

    def fixture(label, action):
        t = T.Preview('test_default_NOOP_does_not_read_inputs')
        try:
            t.setUp()
            action(t)
            checks.append(label)
        finally:
            t.doCleanups()

    def rejected(t, message):
        try:
            P.inputs(*t.snapshot())
        except ValueError as error:
            assert message in str(error), str(error)
        else:
            raise AssertionError('Expected rejection: ' + message)

    def zero(t):
        data = P.inputs(*t.snapshot())
        wide, states, reviews = data[4:7]
        assert len(wide) == 196 and len(states) == 784 and len(reviews) == 196
        assert all(row['Type_'+kind] == 'NA' for row in wide for kind in P.KINDS)
        assert all(row['state'] == 'NOT_RUN' and row['search_complete'] == 'False' for row in states)
        assert all(row['review_state'] == 'PENDING_SCIENTIFIC_COMPLETION' for row in reviews)
        out = t.work/'independent_zero_preview'
        manifest = P.render(*t.snapshot(), out)
        assert manifest['dataset_kind'] == 'PROVISIONAL' and manifest['accepted_genome_count'] == 0
        assert manifest['tip_count'] == 196 and manifest['cell_count'] == 784
        assert all(manifest[key] is False for key in ('full_panel_complete', 'final_matrix_acceptance', 'final_figure_acceptance'))
        scene = json.loads((out/'scene.json').read_text())
        assert len(scene['cell_mapping']) == 784
        assert all(row['value'] == 'NA' and row['fill'] == data[0].UNKNOWN for row in scene['cell_mapping'])
        assert (out/'host_tree.nwk').read_bytes() == (t.work/'tree.nwk').read_bytes()
        assert P.WATERMARK in (out/'preview_circular_rm.svg').read_text()
        from pypdf import PdfReader
        assert P.WATERMARK in PdfReader(out/'preview_circular_rm.pdf').pages[0].extract_text()
        assert len(list(out.glob('itol_*.txt'))) == 5
        assert all(P.WATERMARK in path.read_text() for path in out.glob('itol_*.txt'))
        assert not (out/'curation_validation.json').exists() and not (out/'provenance.json').exists()
    fixture('zero accepted genomes: exact196/784, all pending cells grey NA, shared vector/iTOL export watermark and false final flags', zero)

    def overlap(t):
        t.accepted();t.doc['pending'][0]['accession'] = t.panel[0]
        rejected(t, 'Explicit unique pending')
    fixture('accepted accession cannot also be pending', overlap)
    def duplicate(t):
        t.doc['pending'] *= 2;rejected(t, 'Explicit unique pending')
    fixture('duplicate pending accession rejected', duplicate)
    def outpanel(t):
        t.doc['pending'][0]['accession'] = 'GCF_999999999.1';rejected(t, 'Explicit unique pending')
    fixture('out of panel queue metadata rejected', outpanel)
    def invalid_state(t):
        t.doc['pending'][0]['execution_state'] = 'COMPLETE_VALIDATED';rejected(t, 'Explicit unique pending')
    fixture('raw completion cannot become accepted queue state', invalid_state)
    for reason in (' ', 'a'*1001):
        def bad_reason(t, reason=reason):
            t.doc['pending'][0]['reason'] = reason;rejected(t, 'Explicit unique pending')
        fixture('blank or over-bound queue reason rejected: length '+str(len(reason)), bad_reason)
    for key, value in [('dataset_kind', 'SYNTHETIC'), ('full_panel_complete', True), ('cell_count', 4.0)]:
        def bad_receipt(t, key=key, value=value):
            cert, entry = t.accepted();cert[key] = value
            t.write('accepted/receipt.json', cert);entry['receipt'] = t.spec('accepted/receipt.json')
            rejected(t, 'accepted closed four-cell')
        fixture('receipt rejects '+key+'='+str(value), bad_receipt)
    def bad_manifest(t):
        cert, entry = t.accepted()
        path = t.work/'accepted/manifest.json';manifest = json.loads(path.read_bytes())
        manifest['audit']['complete_sha256'] = '2'*64;t.write('accepted/manifest.json', manifest)
        entry['source_manifest'] = t.spec('accepted/manifest.json')
        cert['source_manifest_sha256'] = entry['source_manifest']['sha256']
        t.write('accepted/receipt.json', cert);entry['receipt'] = t.spec('accepted/receipt.json')
        rejected(t, 'Accepted source manifest identity')
    fixture('matching file pins do not bypass complete receipt identity join', bad_manifest)
    def bad_cell(t):
        cert, entry = t.accepted();path = t.work/'accepted/cells.json'
        rows = json.loads(path.read_bytes());rows[0]['complete_predicted_count'] = True
        t.write('accepted/cells.json', rows);entry['cells'] = t.spec('accepted/cells.json')
        cert['cells_sha256'] = entry['cells']['sha256']
        t.write('accepted/receipt.json', cert);entry['receipt'] = t.spec('accepted/receipt.json')
        rejected(t, 'Nonnegative integer count')
    fixture('matching file pins do not bypass unchanged strict cell serializer', bad_cell)

    stdout = io.StringIO()
    with patch.object(sys, 'argv', ['preview']), contextlib.redirect_stdout(stdout):
        try:runpy.run_path(str(WORK/'stage06_live_preview.py'), run_name='__main__')
        except SystemExit as exit:assert exit.code == 0
    assert json.loads(stdout.getvalue())['state'] == 'NO_OP_PROVISIONAL_STAGE06_PREVIEW'
    checks.append('actual __main__ default NOOP')
    tree = ast.parse((WORK/'stage06_live_preview.py').read_text())
    flags = [arg.value for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == 'add_argument'
             for arg in node.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str)]
    assert '--synthetic' not in flags and '--render' in flags
    calls = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    assert {'R.scene', 'R.svg_export', 'R.pdf_export', 'R.itol_exports', 'M.normalize'} <= calls
    checks.append('no synthetic CLI; existing scene/vector/iTOL/serializer calls retained')
    for name, pin in PINS.items():assert digest(WORK/name) == pin, name
    report = dict(schema='RM_LIVE_PREVIEW_INDEPENDENT_SOURCE_REVIEW_V1', state='PASS_SOURCE_ONLY',
        source_pins=PINS, reviewer_source_sha256=digest(Path(__file__)),
        authored_tests=dict(count=result.testsRun, status='PASS', runtime=sys.executable),
        independent_checks=checks, independent_check_count=len(checks),
        standard_python_attempt='Installed standard Python3.14: five passed, vector test could not import reportlab. No source change or dependency installation. Existing bundled C Python has reportlab/pypdf and passes all six.',
        conclusion='Separate explicit provisional adapter retains exact accepted196 production tree/panel/readback pins. Pending queue metadata remains separate from all784 scientific cells; absent accepted snapshots are NOT_RUN/NA. Optional accepted cells require strict independently accepted production closed-genome three-file joins. Original final renderer/checker/serializer/curation source pins unchanged. Distinct manifest and visible vector/iTOL watermark keep all final acceptance flags false.',
        scope='Frozen source plus disposable C synthetic unit-test exports and default NOOP only. No actual accepted-tree preview rendering, biological search, native owner, WSL, UNC, workflow lock, image, Git or cleanup action.',
        actual_master_render='NOT_RUN', actual_preview_independent_artifact_review='NOT_RUN',
        final_scientific_acceptance=False, final_figure_acceptance=False, blockers=[],
        limitations=['Source peer does not independently accept future biological receipts or claim final matrix/figure validation.',
                     'Root must use a C Python containing existing reportlab/pypdf; installed standard Python lacks reportlab.',
                     'Actual provisional artifact geometry/serialization review and GitHub byte readback remain pending.'])
    output = WORK/'stage06_live_preview_source_independent_review01.json'
    raw = (json.dumps(report, indent=2)+'\n').encode()
    with output.open('xb') as handle:handle.write(raw)
    print(json.dumps(dict(path=str(output), sha256=hashlib.sha256(raw).hexdigest(),
        state=report['state'], authored_tests=6, independent_checks=len(checks), reviewer_sha256=report['reviewer_source_sha256'])))


if __name__ == '__main__':main()
