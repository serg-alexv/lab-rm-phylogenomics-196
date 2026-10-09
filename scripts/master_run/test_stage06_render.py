"""Small synthetic fixtures only. No real host tree or scientific matrix read."""
import csv
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import stage06_render as render
import check_stage06_outputs as artifact_checker


def fixture(folder):
    folder.mkdir(parents=True, exist_ok=True)
    a = ["GCF_000000001.1", "GCF_000000002.1", "GCF_000000003.1", "GCF_000000004.1"]
    (folder / "tree.nwk").write_text(f"[&U](({a[0]}:0.1,{a[1]}:0.2)91/99:0.1,{a[2]}:0.3,{a[3]}:0.0);\n")
    (folder / "approved.txt").write_text("\n".join(a) + "\n")
    values = [("1", "0", "NA", "1"), ("0", "1", "1", "NA"), ("NA", "NA", "0", "0"), ("0", "0", "NA", "1")]
    with (folder / "matrix.tsv").open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(["accession", *render.TYPES])
        # Deliberately reverse rows: display must join by accession, never row position.
        writer.writerows(reversed([(x, *v) for x, v in zip(a, values)]))
    with (folder / "state.tsv").open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(["accession", "rm_type", "state", "complete_count", "partial_count", "candidate_count", "search_complete", "conflict", "review_ids", "positive_invalidated", "count_lower_bound"])
        for accession, row in zip(a, values):
            for rm_type, value in zip(render.TYPES, row):
                writer.writerow([accession, rm_type.replace("Type_", ""), {"1": "COMPLETE_PREDICTED", "0": "NOT_DETECTED_AFTER_SUCCESSFUL_SEARCH", "NA": "PARTIAL_OR_UNRESOLVED"}[value],
                                 int(value == "1"), int(value == "NA"), 0, str(value != "NA").lower(), "false", "[]", "false", str(value == "NA").lower()])
    args = SimpleNamespace(tree=folder / "tree.nwk", matrix=folder / "matrix.tsv", state=folder / "state.tsv", approved=folder / "approved.txt",
                           join=folder / "join.json", tree_validation=folder / "tree_validation.json",
                           curation_validation=folder / "curation_validation.json", curation_source_manifest=folder / "curation_source_manifest.json",
                           synthetic=True, output=folder / "output", exception_manifest=None)
    hashes = {k + "_sha256": render.digest(getattr(args, k)) for k in ("tree", "matrix", "state", "approved")}
    args.join.write_text(json.dumps({"dataset_kind": "SYNTHETIC", "status": "PASS_SYNTHETIC_EXACT_JOIN", **hashes,
                                    "tip_count": 4, "accession_count": 4, "cell_count": 16, "exact_accession_join": True, "unique_tips": True}))
    args.tree_validation.write_text(json.dumps({"scientific_state": "SYNTHETIC_VALIDATION_ONLY", "native_tree_sha256": hashes["tree_sha256"],
                                               "approved_accessions_sha256": hashes["approved_sha256"]}))
    args.curation_source_manifest.write_text(json.dumps({"dataset_kind": "SYNTHETIC", "note": "Nonbiological test fixture only; no review/source evidence exists."}))
    args.curation_validation.write_text(json.dumps({"schema": "RM_INDEPENDENT_CURATION_ACCEPTANCE_V1", "status": "PASS_SYNTHETIC_CURATION_CONTRACT",
        "dataset_kind": "SYNTHETIC", "accepted_curation": False, "accession_count": 4, "cell_count": 16,
        **{k: hashes[k] for k in ("matrix_sha256", "state_sha256", "approved_sha256")},
        "curation_source_manifest_sha256": render.digest(args.curation_source_manifest), "functional_activity_claim": "NONE"}))
    return args


class Gates(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.args = fixture(Path(self.temp.name))

    def tearDown(self):
        self.temp.cleanup()

    def inputs(self):
        a = self.args
        return render.parse_inputs(a.tree, a.matrix, a.state, a.approved, a.join, a.tree_validation,
                                   a.curation_validation, a.curation_source_manifest, a.synthetic)

    def resign_fixture(self):
        a = self.args
        join = json.loads(a.join.read_text())
        for key in ("tree", "matrix", "state", "approved"):
            join[key + "_sha256"] = render.digest(getattr(a, key))
        a.join.write_text(json.dumps(join))
        accepted = json.loads(a.tree_validation.read_text())
        accepted.update(native_tree_sha256=join["tree_sha256"], approved_accessions_sha256=join["approved_sha256"])
        a.tree_validation.write_text(json.dumps(accepted))
        curation = json.loads(a.curation_validation.read_text())
        curation.update({k: join[k] for k in ("matrix_sha256", "state_sha256", "approved_sha256")})
        a.curation_validation.write_text(json.dumps(curation))

    def test_accession_join_not_matrix_order(self):
        root, tips, cells, *_ = self.inputs()
        self.assertEqual([x.label for x in tips], ["GCF_000000001.1", "GCF_000000002.1", "GCF_000000003.1", "GCF_000000004.1"])
        self.assertEqual(cells[tips[0].label]["Type_I"], "1")
        self.assertEqual(root.children[0].label, "91/99")

    def test_synthetic_cannot_authorize_production(self):
        self.args.synthetic = False
        with self.assertRaisesRegex(ValueError, "dataset kind"):
            self.inputs()

    def test_hash_mismatch_fails_before_output(self):
        self.args.matrix.write_text(self.args.matrix.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "hashes differ"):
            render.render(self.args)
        self.assertFalse(self.args.output.exists())

    def test_no_tree_acceptance(self):
        self.args.tree_validation.write_text("{}")
        with self.assertRaisesRegex(ValueError, "acceptance"):
            self.inputs()

    def test_no_join_acceptance(self):
        self.args.join.write_text("{}")
        with self.assertRaisesRegex(ValueError, "join receipt"):
            self.inputs()

    def test_accounting_join_cannot_replace_scientific_curation(self):
        self.args.curation_validation.write_text("{}")
        with self.assertRaisesRegex(ValueError, "scientific curation"):
            self.inputs()

    def test_qualified_curation_needs_pinned_exception_manifest(self):
        curated = json.loads(self.args.curation_validation.read_text())
        curated.update(status="PASS_INDEPENDENT_RM_CURATION_WITH_DOCUMENTED_EXCEPTIONS", dataset_kind="PRODUCTION", accepted_curation=True,
                       all_actual_review_records_checked=True, source_native_bindings_verified=True, complete_and_partial_architectures_checked=True,
                       documented_exception_count=1, operational_closure_verified=True)
        hashes = json.loads(self.args.join.read_text())
        with self.assertRaisesRegex(ValueError, "detailed manifest"):
            render.curation_gate(curated, hashes, self.args.curation_source_manifest, False)
        path = Path(self.temp.name) / "exceptions.json"
        path.write_text(json.dumps({"schema": "RM_DOCUMENTED_CURATION_EXCEPTIONS_V1", "dataset_kind": "PRODUCTION",
            "approved_sha256": hashes["approved_sha256"], "entries": [{"accession": "GCF_000000001.1", "execution_state": "NOT_RUN",
            "reason": "Synthetic contract test only; no actual exception acceptance.", "source_receipt_sha256": "1" * 64,
            "exception_record_sha256": "2" * 64, "current_terminal_receipt_sha256": None, "accepted_complete_positive_count": 0}]}))
        curated["exception_manifest_sha256"] = render.digest(path)
        qualified = render.curation_gate(curated, hashes, self.args.curation_source_manifest, False, path)
        self.assertEqual(qualified["documented_exception_count"], 1)
        curated["exception_manifest_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "missing or changed"):
            render.curation_gate(curated, hashes, self.args.curation_source_manifest, False, path)

    def test_production_curation_cannot_authorize_unproven_operational_closure(self):
        curated = json.loads(self.args.curation_validation.read_text())
        curated.update(status="PASS_INDEPENDENT_RM_CURATION", dataset_kind="PRODUCTION", accepted_curation=True,
                       all_actual_review_records_checked=True, source_native_bindings_verified=True, complete_and_partial_architectures_checked=True)
        hashes = json.loads(self.args.join.read_text())
        for value in (None, False):
            curated["operational_closure_verified"] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "operational closure"):
                render.curation_gate(curated, hashes, self.args.curation_source_manifest, False)

    def test_incomplete_search_cannot_be_nondetection(self):
        text = self.args.state.read_text().replace("NOT_DETECTED_AFTER_SUCCESSFUL_SEARCH\t0\t0\t0\ttrue", "NOT_DETECTED_AFTER_SUCCESSFUL_SEARCH\t0\t0\t0\tfalse", 1)
        self.args.state.write_text(text)
        self.resign_fixture()
        with self.assertRaisesRegex(ValueError, "Nondetection"):
            self.inputs()

    def test_accepted_positive_retains_presence_with_other_partial_candidate(self):
        self.args.state.write_text(self.args.state.read_text().replace(
            "COMPLETE_PREDICTED\t1\t0\t0\ttrue\tfalse\t[]\tfalse\tfalse",
            "COMPLETE_PREDICTED_WITH_OTHER_UNRESOLVED_CANDIDATE\t1\t1\t1\tfalse\ttrue\t[\"review-1\"]\tfalse\ttrue", 1))
        self.resign_fixture()
        _, _, cells, *_ = self.inputs()
        self.assertEqual(cells["GCF_000000001.1"]["Type_I"], "1")

    def test_invalidated_positive_cannot_be_presence(self):
        self.args.state.write_text(self.args.state.read_text().replace(
            "COMPLETE_PREDICTED\t1\t0\t0\ttrue\tfalse\t[]\tfalse\tfalse",
            "INVALIDATED_POSITIVE\t1\t0\t0\ttrue\tfalse\t[]\ttrue\tfalse", 1))
        self.resign_fixture()
        with self.assertRaisesRegex(ValueError, "unambiguously accepted"):
            self.inputs()

    def test_missing_tip_branch_length_rejected(self):
        self.args.tree.write_text(self.args.tree.read_text().replace("GCF_000000001.1:0.1", "GCF_000000001.1"))
        self.resign_fixture()
        with self.assertRaisesRegex(ValueError, "branch length"):
            self.inputs()

    def test_duplicate_tip_rejected(self):
        self.args.tree.write_text(self.args.tree.read_text().replace("GCF_000000002.1", "GCF_000000001.1"))
        self.resign_fixture()
        with self.assertRaisesRegex(ValueError, "tip/accession"):
            self.inputs()

    def test_parser_negative_missing_nonfinite_multiple(self):
        for text in ("(a:-1,b:0.1);", "(a:nan,b:0.1);", "(a:inf,b:0.1);", "(a:0.1,b:0.1);(c:0.1,d:0.1);", "(a:0.1);", "(a:0.1,b:0.1)["):
            with self.subTest(text=text), self.assertRaises(ValueError):
                render.Newick(text).parse()

    def test_quoted_support_comments(self):
        root = render.Newick("[&U]('tip''one':1e-3,tip_two[comment]:0.2)90/100;").parse()
        self.assertEqual(root.children[0].label, "tip'one")
        self.assertEqual(root.children[0].length, 0.001)
        self.assertEqual(root.label, "90/100")

    def test_zero_length_edges_still_unique(self):
        root, leaves, cells, states, prov, _ = self.inputs()
        data = render.scene(root, leaves, cells, states, prov)
        edge_nodes = [p["node"] for p in data["primitives"] if p["role"] == "phylogenetic_edge"]
        self.assertEqual(len(edge_nodes), len(set(edge_nodes)))
        self.assertEqual(len(edge_nodes), 5)
        self.assertEqual(len(data["cell_mapping"]), 16)
        self.assertTrue(any(x["fill"] == render.UNKNOWN for x in data["cell_mapping"]))

    def test_output_namespace_new(self):
        self.args.output.mkdir()
        with self.assertRaisesRegex(ValueError, "namespace"):
            render.render(self.args)


class Typography(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.args = fixture(Path(self.temp.name))
        render.render(self.args)
        self.data = json.loads((self.args.output / "scene.json").read_text())

    def test_actual_label_clip_is_rejected(self):
        tip = next(p for p in self.data["primitives"] if p["role"] == "tip_label")
        tip["text"] = "UNRENDERABLE_SYNTHETIC_LABEL_" * 30
        with self.assertRaisesRegex(ValueError, "clips the page"):
            render.typography_check(self.data["primitives"])

    def test_actual_svg_font_drift_is_rejected_even_after_hash_rebinding(self):
        path = self.args.output / "circular_rm.svg"
        xml = ET.parse(path)
        next(p for p in xml.getroot() if p.get("data-role") == "tip_label").set("font-size", "6.3")
        xml.write(path, encoding="utf-8", xml_declaration=True)
        manifest_path = self.args.output / "provenance.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["outputs"][path.name] = render.digest(path)
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "SVG text/font/position"):
            artifact_checker.check(self.args.output)

    def test_actual_pdf_font_drift_is_rejected(self):
        from io import BytesIO
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import ContentStream, FloatObject
        writer = PdfWriter(clone_from=self.args.output / "circular_rm.pdf")
        page = writer.pages[0]
        stream = ContentStream(page.get_contents(), writer)
        changed = 0
        for operands, operator in stream.operations:
            if operator == b"Tf" and float(operands[1]) == 12:
                operands[1] = FloatObject(6.3)
                changed += 1
        self.assertGreater(changed, 0)
        page.replace_contents(stream)
        altered = BytesIO()
        writer.write(altered)
        altered.seek(0)
        actual = PdfReader(altered).pages[0]
        with self.assertRaisesRegex(ValueError, "PDF actual font/text"):
            artifact_checker.actual_pdf_typography(actual, self.data)


if __name__ == "__main__":
    unittest.main()
