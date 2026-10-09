"""Independent artifact/provenance checker; does not accept scientific inputs."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import math
import re
import xml.etree.ElementTree as ET

TYPES = ("Type_I", "Type_II", "Type_III", "Type_IV")
COLORS = dict(zip(TYPES, ("#26828e", "#e6a100", "#9467bd", "#d55e00")))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def actual_pdf_typography(page, scene):
    """Reopen actual PDF font sizes and text transforms, then bound the text."""
    from reportlab.pdfbase.pdfmetrics import getAscentDescent, stringWidth
    observed = []
    def visitor(text, cm, tm, font, size):
        if text.strip():
            # Extraction may add separator spaces around rotated text. Exact
            # text bytes are independently checked against the Tj operators.
            observed.append((text.strip(), tuple(cm), tuple(tm), font.get("/BaseFont"), size))
    page.extract_text(visitor_text=visitor)
    expected = [p for p in scene["primitives"] if p["kind"] == "text"]
    require(len(observed) == len(expected), "PDF text transform count differs")
    rectangles = []
    for (text, cm, tm, font, size), primitive in zip(observed, expected):
        require(text == primitive["text"] and font == "/Helvetica" and size == primitive["size"], "PDF actual font/text differs")
        angle = math.radians(primitive.get("rotation", 0))
        x, y = primitive["point"]
        wanted = (math.cos(angle), -math.sin(angle), math.sin(angle), math.cos(angle), x, scene["height"] - y)
        require(all(math.isclose(a, b, abs_tol=0.001) for a, b in zip(cm, wanted)), "PDF actual text position/rotation differs")
        width = stringWidth(text, "Helvetica", size)
        anchor = {"end": -width, "middle": -width / 2}.get(primitive.get("anchor"), 0)
        require(all(math.isclose(a, b, abs_tol=0.001) for a, b in zip(tm, (1, 0, 0, 1, anchor, 0))), "PDF actual text anchor differs")
        require(size == 12 if primitive["role"] == "tip_label" else size >= 11, "Typography below intended print size")
        ascent, descent = getAscentDescent("Helvetica", size)
        corners = [(cm[0] * u + cm[2] * v + cm[4], cm[1] * u + cm[3] * v + cm[5])
                   for u, v in ((tm[4], descent), (tm[4] + width, descent), (tm[4] + width, ascent), (tm[4], ascent))]
        require(all(0 <= a <= scene["width"] and 0 <= b <= scene["height"] for a, b in corners), "Actual PDF text clips the page")
        rectangles.append((primitive, corners))
    def intersect(first, second):
        for rectangle in (first, second):
            for i in range(4):
                start, end = rectangle[i], rectangle[(i + 1) % 4]
                nx, ny = start[1] - end[1], end[0] - start[0]
                a = [nx * x + ny * y for x, y in first]
                b = [nx * x + ny * y for x, y in second]
                if max(a) <= min(b) + 1e-8 or max(b) <= min(a) + 1e-8:
                    return False
        return True
    swatches = [[(x, scene["height"] - y) for x, y in p["points"]]
                for p in scene["primitives"] if p["role"] == "legend_swatch"]
    for i, (primitive, corners) in enumerate(rectangles):
        require(not any(intersect(corners, other) for _, other in rectangles[:i]), "Actual PDF text bounds overlap: " + primitive["text"])
        require(not any(intersect(corners, swatch) for swatch in swatches), "Actual PDF text overlaps a legend swatch")
    scale = 180 * 72 / 25.4 / scene["width"]
    return {"actual_text_count": len(rectangles), "actual_font_and_transform_bindings_verified": True,
            "conservative_pdf_text_bounds_inside_page": True, "actual_text_overlap_count": 0,
            "intended_print_width_mm": 180, "tip_font_at_print_points": 12 * scale,
            "minimum_annotation_font_at_print_points": 11 * scale}


def check(out):
    from pypdf import PdfReader
    from pypdf.generic import ContentStream
    m = load(out / "provenance.json")
    require(m["schema"] == "stage06-export-v1", "Unknown manifest schema")
    for name, expected in m["outputs"].items():
        require(Path(name).name == name and sha(out / name) == expected, "Output hash differs: " + name)
    scene = load(out / "scene.json")
    canonical = json.dumps(scene, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    require(hashlib.sha256(canonical).hexdigest() == m["scene_sha256"], "Scene content hash differs")
    require(scene["ring_order"] == list(TYPES) and scene["rooting"] == "UNROOTED_NO_VALIDATED_OUTGROUP", "Order/rooting differs")
    keys = {"tree_sha256": "host_tree.nwk", "matrix_sha256": "rm_type_presence_absence.tsv", "state_sha256": "rm_type_state.tsv",
            "approved_sha256": "approved_accessions.txt", "join_validation_sha256": "join_validation.json", "tree_validation_sha256": "tree_validation.json",
            "curation_validation_sha256": "curation_validation.json", "curation_source_manifest_sha256": "curation_source_manifest.json"}
    if "exception_manifest_sha256" in m["provenance"]:
        keys["exception_manifest_sha256"] = "exception_manifest.json"
    require(all(sha(out / name) == m["provenance"][key] == scene["provenance"][key] for key, name in keys.items()), "Input/certificate hashes differ")
    join, acceptance = load(out / "join_validation.json"), load(out / "tree_validation.json")
    synthetic = m["dataset_kind"] == "SYNTHETIC"
    curation = load(out / "curation_validation.json")
    require(curation.get("schema") == "RM_INDEPENDENT_CURATION_ACCEPTANCE_V1" and
            curation.get("dataset_kind") == m["dataset_kind"] and curation.get("accepted_curation") is (not synthetic) and
            curation.get("status") in (("PASS_SYNTHETIC_CURATION_CONTRACT",) if synthetic else
                ("PASS_INDEPENDENT_RM_CURATION", "PASS_INDEPENDENT_RM_CURATION_WITH_DOCUMENTED_EXCEPTIONS")),
            "Scientific curation acceptance differs")
    require(curation.get("curation_source_manifest_sha256") == sha(out / "curation_source_manifest.json") and
            curation.get("functional_activity_claim") == "NONE", "Curation source/activity provenance differs")
    require(all(curation.get(key) == m["provenance"][key] for key in ("matrix_sha256", "state_sha256", "approved_sha256")),
            "Curation matrix/state/panel hashes differ")
    if not synthetic:
        require(curation.get("operational_closure_verified") is True, "Production curation operational closure is unproven")
        require(all(curation.get(key) is True for key in ("all_actual_review_records_checked", "source_native_bindings_verified",
                    "complete_and_partial_architectures_checked")), "Independent scientific review is incomplete")
    require(join["status"] == ("PASS_SYNTHETIC_EXACT_JOIN" if synthetic else "PASS_EXACT_196_784_JOIN"), "Join receipt status differs")
    require(acceptance["scientific_state"] == ("SYNTHETIC_VALIDATION_ONLY" if synthetic else "COMPLETE_VALIDATED"), "Tree acceptance status differs")
    require(acceptance.get("native_tree_sha256") == m["provenance"]["tree_sha256"] and
            acceptance.get("approved_accessions_sha256") == m["provenance"]["approved_sha256"], "Accepted tree/panel hashes differ")
    require(all(join.get(key) == m["provenance"][key] for key in ("tree_sha256", "matrix_sha256", "state_sha256", "approved_sha256")) and
            join.get("exact_accession_join") is True and join.get("unique_tips") is True, "Join acceptance hashes/exactness differ")
    approved = (out / "approved_accessions.txt").read_text(encoding="utf-8-sig").splitlines()
    require(len(approved) == len(set(approved)) == m["tip_count"] and set(approved) == set(scene["tip_order"]), "Tip uniqueness differs")
    require(synthetic or (len(approved) == 196 and sha(out / "approved_accessions.txt") ==
        "85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6"), "Production must use the frozen approved196 panel")
    require(join.get("tip_count") == join.get("accession_count") == curation.get("accession_count") == len(approved) and
            join.get("cell_count") == curation.get("cell_count") == 4 * len(approved), "Independent acceptance counts differ")
    require(m["provenance"].get("curation_status") == curation["status"], "Curation qualification status differs")
    qualified = curation["status"] == "PASS_INDEPENDENT_RM_CURATION_WITH_DOCUMENTED_EXCEPTIONS"
    if qualified:
        count = curation.get("documented_exception_count")
        require(type(count) is int and 1 <= count <= 196 and count == m["provenance"].get("documented_exception_count"), "Exception count differs")
        exceptions = load(out / "exception_manifest.json")
        require(sha(out / "exception_manifest.json") == curation.get("exception_manifest_sha256") and
                exceptions.get("schema") == "RM_DOCUMENTED_CURATION_EXCEPTIONS_V1" and exceptions.get("dataset_kind") == "PRODUCTION" and
                exceptions.get("approved_sha256") == m["provenance"]["approved_sha256"], "Exception source/panel manifest differs")
        entries = exceptions.get("entries", [])
        require(len(entries) == len({x["accession"] for x in entries}) == count and {x["accession"] for x in entries} <= set(approved),
                "Exception accession/count accounting differs")
        for entry in entries:
            require(entry.get("execution_state") in ("FAILED_FATAL", "FAILED_RETRYABLE", "DEFERRED_RESOURCE", "NOT_RUN") and
                    isinstance(entry.get("reason"), str) and entry["reason"].strip(), "Exception state/reason missing")
            require(all(isinstance(entry.get(key), str) and re.fullmatch("[a-f0-9]{64}", entry[key]) for key in
                        ("source_receipt_sha256", "exception_record_sha256")), "Exception source/record hash missing")
            terminal = entry.get("current_terminal_receipt_sha256")
            require((terminal is None and entry["execution_state"] == "NOT_RUN") or
                    (isinstance(terminal, str) and re.fullmatch("[a-f0-9]{64}", terminal)), "Exception terminal receipt is missing")
            require(type(entry.get("accepted_complete_positive_count")) is int and entry["accepted_complete_positive_count"] >= 0,
                    "Exception accepted-positive count invalid")
    else:
        require(m["provenance"].get("documented_exception_count") == 0 and not (out / "exception_manifest.json").exists(),
                "Unqualified figure has unexpected exception manifest/count")
    with (out / "rm_type_presence_absence.tsv").open(encoding="utf-8-sig", newline="") as f:
        matrix_rows = list(csv.DictReader(f, delimiter="\t"))
    matrix = {(row["accession"], t): row[t] for row in matrix_rows for t in TYPES}
    expected_keys = {(a, t) for a in approved for t in TYPES}
    require(len(matrix_rows) == len(approved) and set(matrix) == expected_keys, "Matrix has duplicate/foreign/missing accessions")
    with (out / "rm_type_state.tsv").open(encoding="utf-8-sig", newline="") as f:
        state_rows = list(csv.DictReader(f, delimiter="\t"))
    type_columns = dict(zip(("I", "II", "III", "IV"), TYPES))
    states = {(row["accession"], type_columns[row["rm_type"]]): row for row in state_rows}
    require(len(state_rows) == len(states) == len(expected_keys) and set(states) == expected_keys, "State cell identity/uniqueness differs")
    with (out / "cell_mapping.tsv").open(encoding="utf-8-sig", newline="") as f:
        mapping_rows = list(csv.DictReader(f, delimiter="\t"))
    mapping = {(r["accession"], r["rm_type"]): r for r in mapping_rows}
    require(len(mapping_rows) == len(mapping) == len(matrix) == m["cell_count"] == 4 * len(approved), "Cell count/uniqueness differs")
    for key, value in matrix.items():
        expected = COLORS[key[1]] if value == "1" else "#ffffff" if value == "0" else "#9e9e9e"
        row = mapping[key]
        require(row["value"] == value and row["fill"] == expected and int(row["inner_to_outer_ring"]) == TYPES.index(key[1]) + 1, "Cell mapping differs: " + str(key))
        require(all(row[field] == states[key][field] for field in ("state", "complete_count", "partial_count", "candidate_count",
                    "search_complete", "conflict", "review_ids", "positive_invalidated", "count_lower_bound")), "Cell mapping lost state/count/review provenance")
    xml = ET.parse(out / "circular_rm.svg").getroot()
    metadata = json.loads(next(x.text for x in xml if x.tag.endswith("metadata")))
    require(metadata["scene_sha256"] == m["scene_sha256"], "SVG scene provenance differs")
    svg_cells = [x for x in xml if x.get("data-role") == "ring_cell"]
    require(len(svg_cells) == len(mapping), "SVG missing or extra cells")
    seen = set()
    for cell in svg_cells:
        key = (cell.get("data-accession"), cell.get("data-rm-type"))
        require(key not in seen and key in mapping, "SVG cell identity differs")
        seen.add(key)
        require(cell.get("fill") == mapping[key]["fill"] and cell.get("data-value") == matrix[key] and
                cell.get("data-ring") == mapping[key]["inner_to_outer_ring"], "SVG colour/state/ring differs")
    svg_tips = [x for x in xml if x.get("data-role") == "tip_label"]
    require([x.text for x in svg_tips] == scene["tip_order"] and len(svg_tips) == len(approved), "SVG tip/order differs")
    branches = load(out / "branch_mapping.json")
    edges = [x for x in xml if x.get("data-role") == "phylogenetic_edge"]
    require(len(branches) == len(edges) == m["branch_count"] and len({x.get("data-node") for x in edges}) == len(edges), "SVG branches omitted or duplicated")
    for branch in branches:
        length = branch["input_branch_length"]
        require(math.isfinite(length) and length >= 0 and math.isclose(
            (branch["radial_end"] - branch["radial_start"]) / scene["radial_points_per_unit"], length, abs_tol=1e-12), "Radial branch length changed")
    primitives = scene["primitives"]
    actual_shapes = [x for x in xml if x.get("data-role")]
    require(len(actual_shapes) == len(primitives), "SVG/scene primitive count differs")
    for shape, primitive in zip(actual_shapes, primitives):
        require(shape.get("data-role") == primitive["role"], "SVG/scene role differs")
        if primitive["kind"] in ("line", "polygon"):
            expected_points = " ".join(f"{x:.6f},{y:.6f}" for x, y in primitive["points"])
            require(shape.get("points") == expected_points, "SVG coordinates differ from shared vector scene")
        else:
            x, y = primitive["point"]
            rotation = primitive.get("rotation", 0)
            require(shape.text == primitive["text"] and float(shape.get("font-size")) == primitive["size"] and
                    shape.get("x") == f"{x:.6f}" and shape.get("y") == f"{y:.6f}" and
                    shape.get("transform") == f"rotate({rotation:.6f} {x:.6f} {y:.6f})" and
                    shape.get("text-anchor") == primitive.get("anchor", "start"), "SVG text/font/position differs from scene")
    pdf = PdfReader(str(out / "circular_rm.pdf"))
    require(len(pdf.pages) == 1, "PDF page count differs")
    require(json.loads(pdf.metadata.subject)["scene_sha256"] == m["scene_sha256"], "PDF scene provenance differs")
    page = pdf.pages[0]
    require(float(page.mediabox.width) == scene["width"] and float(page.mediabox.height) == scene["height"], "PDF geometry differs")
    require(not page.images, "PDF unexpectedly rasterized")
    typography = actual_pdf_typography(page, scene)
    text = page.extract_text()
    # Dense rotated text can be merged onto a line by extraction heuristics.
    # Inspect actual vector text operators instead of interpreting line breaks.
    ops = ContentStream(page.get_contents(), pdf).operations
    vector_text = [str(operands[0]) for operands, operator in ops if operator == b"Tj"]
    require(vector_text == [p["text"] for p in primitives if p["kind"] == "text"], "PDF vector text differs from shared scene")
    require(all(vector_text.count(a) == 1 for a in approved), "PDF accession labels missing/duplicated")
    require("Unrooted phylogeny" in text and "Grey: unknown" in text, "PDF uncertainty/rooting annotation missing")
    if synthetic:
        require("SYNTHETIC TEST ONLY" in text, "Synthetic PDF lacks explicit label")
    if qualified:
        require("Qualified panel accounting" in text and "documented exceptions" in text, "Qualified figure annotation is missing")
    pdf_fills = sum(operator in (b"B", b"B*", b"b", b"b*", b"f", b"f*") for _, operator in ops)
    require(pdf_fills == sum(p["kind"] == "polygon" for p in primitives), "PDF vector cell/swatch count differs")
    geometry = iter(p for p in primitives if p["kind"] in ("line", "polygon"))
    path_points, path_closed, fill_color, painted = [], False, None, 0
    for operands, operator in ops:
        if operator == b"n":
            path_points, path_closed = [], False
        elif operator in (b"m", b"l"):
            path_points.append(tuple(map(float, operands)))
        elif operator == b"h":
            path_closed = True
        elif operator == b"rg":
            fill_color = tuple(map(float, operands))
        elif operator in (b"S", b"B", b"B*", b"b", b"b*", b"f", b"f*"):
            p = next(geometry, None)
            require(p is not None, "PDF has extra vector paths")
            expected_points = [(x, scene["height"] - y) for x, y in p["points"]]
            require(len(path_points) == len(expected_points) and all(
                math.isclose(v, wanted, abs_tol=0.001) for actual, expected in zip(path_points, expected_points)
                for v, wanted in zip(actual, expected)), "PDF coordinates differ from shared scene")
            require(path_closed == (p["kind"] == "polygon"), "PDF path closure differs")
            if p["kind"] == "polygon":
                rgb = tuple(int(p["fill"][start:start + 2], 16) / 255 for start in (1, 3, 5))
                require(fill_color is not None and all(math.isclose(a, b, abs_tol=1e-6) for a, b in zip(fill_color, rgb)),
                        "PDF cell/swatch color differs from shared scene")
            painted += 1
            path_points, path_closed = [], False
    require(painted == sum(p["kind"] in ("line", "polygon") for p in primitives), "PDF has missing vector paths")
    original = (out / "host_tree.nwk").read_text(encoding="utf-8-sig").strip()
    require((out / "host_tree_unrooted.nex").read_text() == "#NEXUS\nBegin trees;\nTree host = [&U] " + original + "\nEnd;\n", "Unrooted NEXUS export changed tree")
    for i, t in enumerate(TYPES):
        lines = (out / f"itol_{i+1:02d}_{t}_full_state.txt").read_text().splitlines()
        require(lines[0] == "DATASET_COLORSTRIP" and "COLOR_BRANCHES\t0" in lines, "iTOL full-state dataset schema differs")
        rows = [line.split("\t") for line in lines[lines.index("DATA") + 1:]]
        require(len(rows) == len(approved) and [r[0] for r in rows] == scene["tip_order"], "iTOL full-state tips/order differs")
        require(all(r[1] == mapping[(r[0], t)]["fill"] for r in rows), "iTOL full-state colors differ")
    binary = (out / "itol_binary_convenience.txt").read_text().splitlines()
    binary_rows = [line.split("\t") for line in binary[binary.index("DATA") + 1:]]
    require(len(binary_rows) == len(approved), "Binary iTOL row count differs")
    require(all(row[1:] == ["-1" if matrix[(row[0], t)] == "NA" else matrix[(row[0], t)] for t in TYPES] for row in binary_rows), "Binary uncertainty mapping differs")
    return {"status": "PASS_SYNTHETIC_ARTIFACT_CHECK" if synthetic else "PASS_STAGE06_ARTIFACT_CHECK",
            "dataset_kind": m["dataset_kind"], "tip_count": len(approved), "cell_count": len(mapping),
            "branch_count": len(branches), "svg_pdf_vector": True, "pdf_pages": 1,
            "typography": typography,
            "scene_sha256": m["scene_sha256"], "provenance_sha256": sha(out / "provenance.json"),
            "checker_sha256": sha(__file__), "limitations": "Artifact consistency check only; scientific acceptance remains the separate input receipts. iTOL server import/UI visual verification not performed."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    require(not args.report.exists(), "Checker report must be new")
    report = check(args.output)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
