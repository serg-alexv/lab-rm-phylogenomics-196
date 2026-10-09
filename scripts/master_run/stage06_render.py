"""Circular phylogram, explicit four-state rings, and honest iTOL exports.

No inference, rooting, taxon sorting, imputation, or matrix classification.
Production rendering requires independent tree, curation and join receipts. All files
must be supplied explicitly; the output directory must be new.
"""
from __future__ import annotations
import argparse
import csv
from dataclasses import dataclass, field
import hashlib
import html
import json
import math
from pathlib import Path
import re
import shutil
import platform

TYPES = ("Type_I", "Type_II", "Type_III", "Type_IV")
STATE_TO_COLUMN = dict(zip(("I", "II", "III", "IV"), TYPES))
EXPECTED_PANEL = "85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6"
LABELS = ("I", "II (including IIG)", "III", "IV")
COLORS = dict(zip(TYPES, ("#26828e", "#e6a100", "#9467bd", "#d55e00")))
UNKNOWN = "#9e9e9e"
WHITE = "#ffffff"
WIDTH, HEIGHT = 1100, 1180
CX, CY = 550.0, 550.0
TREE_RADIUS = 320.0
RING_INNER, RING_WIDTH, RING_GAP = 334.0, 12.0, 3.0
TIP_FONT_SIZE, NOTE_FONT_SIZE, INTENDED_PRINT_WIDTH_MM = 12.0, 11.0, 180.0


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


@dataclass
class Node:
    label: str = ""
    length: float | None = None
    children: list[Node] = field(default_factory=list)
    index: int = -1
    depth: float = 0
    angle: float = 0
    descendants: list[str] = field(default_factory=list)


class Newick:
    """Strict single-tree parser. Original bytes remain the canonical export.

    Supports quoted labels (including doubled quotes), comments, internal
    support labels and scientific-notation lengths. Does not interpret support
    labels as topology or use a support value to collapse a branch.
    """
    def __init__(self, text):
        self.text, self.i = text.lstrip("\ufeff"), 0

    def skip(self):
        while self.i < len(self.text):
            if self.text[self.i].isspace():
                self.i += 1
            elif self.text[self.i] == "[":
                depth = 1
                self.i += 1
                while self.i < len(self.text) and depth:
                    depth += (self.text[self.i] == "[") - (self.text[self.i] == "]")
                    self.i += 1
                require(depth == 0, "Unterminated Newick comment")
            else:
                break

    def label(self):
        self.skip()
        if self.i < len(self.text) and self.text[self.i] == "'":
            self.i += 1
            result = ""
            while self.i < len(self.text):
                c = self.text[self.i]
                self.i += 1
                if c == "'":
                    if self.i < len(self.text) and self.text[self.i] == "'":
                        result += "'"
                        self.i += 1
                    else:
                        return result
                else:
                    result += c
            raise ValueError("Unterminated quoted Newick label")
        start = self.i
        while self.i < len(self.text) and self.text[self.i] not in "(),:;[" and not self.text[self.i].isspace():
            self.i += 1
        return self.text[start:self.i]

    def node(self):
        self.skip()
        require(self.i < len(self.text), "Unexpected end of Newick")
        n = Node()
        if self.text[self.i] == "(":
            self.i += 1
            n.children.append(self.node())
            while True:
                self.skip()
                require(self.i < len(self.text), "Unclosed Newick subtree")
                c = self.text[self.i]
                self.i += 1
                if c == ")":
                    break
                require(c == ",", "Expected Newick comma or close parenthesis")
                n.children.append(self.node())
            require(len(n.children) >= 2, "Unary Newick nodes are not accepted")
        n.label = self.label()
        require(n.children or n.label, "Unnamed terminal")
        self.skip()
        if self.i < len(self.text) and self.text[self.i] == ":":
            self.i += 1
            token = self.label()
            n.length = float(token)
            require(math.isfinite(n.length) and n.length >= 0, "Nonfinite or negative branch length")
        return n

    def parse(self):
        n = self.node()
        self.skip()
        require(self.i < len(self.text) and self.text[self.i] == ";", "Newick must end with a semicolon")
        self.i += 1
        self.skip()
        require(self.i == len(self.text), "Exactly one Newick tree required")
        return n


def nodes(root):
    yield root
    for child in root.children:
        yield from nodes(child)


def curation_gate(curated, hashes, source_manifest, synthetic, exception_manifest=None):
    kind = "SYNTHETIC" if synthetic else "PRODUCTION"
    statuses = ("PASS_SYNTHETIC_CURATION_CONTRACT",) if synthetic else (
        "PASS_INDEPENDENT_RM_CURATION", "PASS_INDEPENDENT_RM_CURATION_WITH_DOCUMENTED_EXCEPTIONS")
    require(curated.get("schema") == "RM_INDEPENDENT_CURATION_ACCEPTANCE_V1" and
            curated.get("dataset_kind") == kind and curated.get("status") in statuses,
            "Independent scientific curation acceptance is missing or belongs to another dataset kind")
    require(curated.get("accepted_curation") is (not synthetic), "Synthetic curation cannot authorize a production claim")
    require(all(curated.get(key) == hashes[key] for key in ("matrix_sha256", "state_sha256", "approved_sha256")),
            "Curation acceptance input hashes differ")
    curation_sources = read_json(source_manifest)
    require(curated.get("curation_source_manifest_sha256") == digest(source_manifest) and
            isinstance(curation_sources, dict) and curation_sources,
            "Detailed scientific curation manifest is missing or changed")
    require(curated.get("functional_activity_claim") == "NONE", "Predicted architecture does not establish functional activity")
    if not synthetic:
        require(curated.get("operational_closure_verified") is True,
                "Production scientific curation requires proven operational closure")
        require(all(curated.get(key) is True for key in ("all_actual_review_records_checked", "source_native_bindings_verified",
                    "complete_and_partial_architectures_checked")), "Independent source/native/review/architecture audit is incomplete")
    exceptional = curated["status"] == "PASS_INDEPENDENT_RM_CURATION_WITH_DOCUMENTED_EXCEPTIONS"
    qualification = {"curation_status": curated["status"], "documented_exception_count": 0}
    if exceptional:
        count = curated.get("documented_exception_count")
        require(type(count) is int and count > 0 and exception_manifest is not None,
                "Qualified curation needs documented exceptions and their detailed manifest")
        details = read_json(exception_manifest)
        require(isinstance(details, dict) and details and digest(exception_manifest) == curated.get("exception_manifest_sha256"),
                "Documented exception manifest is missing or changed")
        require(details.get("schema") == "RM_DOCUMENTED_CURATION_EXCEPTIONS_V1" and details.get("dataset_kind") == "PRODUCTION" and
                details.get("approved_sha256") == hashes["approved_sha256"], "Exception manifest schema/panel differs")
        entries = details.get("entries")
        require(isinstance(entries, list) and len(entries) == count and 1 <= count <= 196 and
                len({e["accession"] for e in entries}) == count, "Exception count/accession uniqueness differs")
        for entry in entries:
            require(re.fullmatch(r"GCF_\d+\.\d+", entry.get("accession", "")) and entry.get("execution_state") in
                    ("FAILED_FATAL", "FAILED_RETRYABLE", "DEFERRED_RESOURCE", "NOT_RUN") and
                    isinstance(entry.get("reason"), str) and entry["reason"].strip(), "Invalid documented exception accession/state/reason")
            for key in ("source_receipt_sha256", "exception_record_sha256"):
                require(isinstance(entry.get(key), str) and re.fullmatch(r"[a-f0-9]{64}", entry[key]), "Exception source/record hash missing")
            terminal = entry.get("current_terminal_receipt_sha256")
            require((terminal is None and entry["execution_state"] == "NOT_RUN") or
                    (isinstance(terminal, str) and re.fullmatch(r"[a-f0-9]{64}", terminal)), "Exception current terminal receipt is missing")
            require(type(entry.get("accepted_complete_positive_count")) is int and entry["accepted_complete_positive_count"] >= 0,
                    "Exception accepted-positive count is invalid")
        qualification.update(documented_exception_count=count, exception_manifest_sha256=digest(exception_manifest))
    else:
        require(exception_manifest is None, "Exception manifest requires qualified independent acceptance")
    return qualification


def parse_inputs(tree, matrix, state, approved, join, tree_validation, curation_validation, curation_source_manifest,
                 synthetic=False, exception_manifest=None):
    paths = {"tree": tree, "matrix": matrix, "state": state, "approved": approved}
    hashes = {key + "_sha256": digest(path) for key, path in paths.items()}
    receipt, accepted = read_json(join), read_json(tree_validation)
    curated = read_json(curation_validation)
    kind = "SYNTHETIC" if synthetic else "PRODUCTION"
    expected_status = "PASS_SYNTHETIC_EXACT_JOIN" if synthetic else "PASS_EXACT_196_784_JOIN"
    require(receipt.get("status") == expected_status, "Independent join receipt has not accepted this dataset kind")
    require(receipt.get("dataset_kind", "PRODUCTION") == kind, "Synthetic receipts cannot authorize production")
    qualification = curation_gate(curated, hashes, curation_source_manifest, synthetic, exception_manifest)
    require(accepted.get("scientific_state") == ("SYNTHETIC_VALIDATION_ONLY" if synthetic else "COMPLETE_VALIDATED"),
            "Independent tree acceptance is missing or is synthetic")
    require(accepted.get("native_tree_sha256") == hashes["tree_sha256"] and
            accepted.get("approved_accessions_sha256") == hashes["approved_sha256"], "Tree acceptance hashes differ")
    require(all(receipt.get(key) == value for key, value in hashes.items()), "Join receipt input hashes differ")
    require(receipt.get("exact_accession_join") is True and receipt.get("unique_tips") is True,
            "Join exactness and uniqueness were not accepted")
    approved_names = Path(approved).read_text(encoding="utf-8-sig").splitlines()
    require(approved_names and all(x == x.strip() and x for x in approved_names), "Malformed approved accession list")
    require(len(set(approved_names)) == len(approved_names), "Duplicate approved accession")
    if not synthetic:
        require(hashes["approved_sha256"] == EXPECTED_PANEL and len(approved_names) == 196 and
                all(re.fullmatch(r"GCF_\d+\.\d+", x) for x in approved_names),
                "Production requires the frozen approved196 versioned GCF panel")
    else:
        require(2 <= len(approved_names) <= 196, "Synthetic fixture must have2-196 tips")
    if qualification["documented_exception_count"]:
        require({e["accession"] for e in read_json(exception_manifest)["entries"]} <= set(approved_names),
                "Documented exception accession is outside approved panel")
    tree_text = Path(tree).read_text(encoding="utf-8-sig")
    root = Newick(tree_text).parse()
    all_nodes = list(nodes(root))
    leaves = [n for n in all_nodes if not n.children]
    tip_names = [n.label for n in leaves]
    require(len(tip_names) == len(set(tip_names)) and set(tip_names) == set(approved_names), "Tree tip/accession join differs")
    for n in all_nodes[1:]:
        require(n.length is not None, "Every phylogenetic edge needs its input branch length")
    with Path(matrix).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        require(reader.fieldnames == ["accession", *TYPES], "Matrix schema differs")
        matrix_rows = list(reader)
    require(len(matrix_rows) == len(approved_names) and len({r["accession"] for r in matrix_rows}) == len(matrix_rows), "Duplicate/missing matrix accession")
    cells = {r["accession"]: {t: r[t] for t in TYPES} for r in matrix_rows}
    require(set(cells) == set(approved_names), "Matrix/accession join differs")
    require(all(v in ("1", "0", "NA") for r in cells.values() for v in r.values()), "Matrix needs exact1/0/NA values")
    with Path(state).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        required = {"accession", "rm_type", "state", "complete_count", "partial_count", "candidate_count", "search_complete", "conflict", "review_ids", "positive_invalidated", "count_lower_bound"}
        require(required.issubset(reader.fieldnames or []), "State table schema differs")
        states = {}
        for row in reader:
            require(row["rm_type"] in STATE_TO_COLUMN, "State rm_type must be exactly I,II,III,IV")
            key = (row["accession"], STATE_TO_COLUMN[row["rm_type"]])
            require(key not in states, "Duplicate state cell")
            require(row["state"].strip(), "Each cell requires explicit state provenance")
            states[key] = row
    require(set(states) == {(a, t) for a in approved_names for t in TYPES}, "State table/accession/type join differs")
    n = len(approved_names)
    require(receipt.get("tip_count") == receipt.get("accession_count") == n and receipt.get("cell_count") == n * 4, "Join receipt counts differ")
    require(curated.get("accession_count") == n and curated.get("cell_count") == n * 4, "Curation acceptance counts differ")
    for (a, t), row in states.items():
        counts = [int(row[k]) for k in ("complete_count", "partial_count", "candidate_count")]
        require(all(x >= 0 for x in counts), "State counts must be nonnegative")
        for key in ("search_complete", "conflict", "positive_invalidated", "count_lower_bound"):
            require(row[key].lower() in ("true", "false", "1", "0"), "Invalid state boolean: " + key)
        reviews = json.loads(row["review_ids"])
        require(isinstance(reviews, list) and all(isinstance(x, str) and x for x in reviews) and len(set(reviews)) == len(reviews),
                "review_ids must be an explicit JSON list of unique review identifiers")
        if cells[a][t] == "1":
            require(counts[0] > 0 and row["positive_invalidated"].lower() in ("false", "0"),
                    "Present needs at least one unambiguously accepted complete predicted architecture")
        elif cells[a][t] == "0":
            require(counts == [0, 0, 0] and row["search_complete"].lower() in ("true", "1") and
                    row["conflict"].lower() in ("false", "0") and not reviews,
                    "Nondetection cell has incomplete or unresolved evidence")
            require(row["state"] == "NOT_DETECTED_AFTER_SUCCESSFUL_SEARCH" and
                    row["positive_invalidated"].lower() in ("false", "0") and row["count_lower_bound"].lower() in ("false", "0"),
                    "Nondetection needs the explicit successful-search state without a lower-bound caveat")
    return root, leaves, cells, states, {"dataset_kind": kind, **hashes, **qualification,
        "join_validation_sha256": digest(join), "tree_validation_sha256": digest(tree_validation),
        "curation_validation_sha256": digest(curation_validation), "curation_source_manifest_sha256": digest(curation_source_manifest)}, tree_text


def point(radius, angle):
    return (CX + radius * math.cos(angle), CY + radius * math.sin(angle))


def arc_points(radius, start, end):
    steps = max(1, math.ceil(abs(end - start) / math.radians(2)))
    return [point(radius, start + (end - start) * k / steps) for k in range(steps + 1)]


def text_rectangle(p):
    """Conservative Helvetica advance/ascent/descent bounds in scene coordinates."""
    from reportlab.pdfbase.pdfmetrics import getAscentDescent, stringWidth
    width = stringWidth(p["text"], "Helvetica", p["size"])
    ascent, descent = getAscentDescent("Helvetica", p["size"])
    left = {"middle": -width / 2, "end": -width}.get(p.get("anchor"), 0)
    angle = math.radians(p.get("rotation", 0))
    x, y = p["point"]
    return [(x + a * math.cos(angle) - b * math.sin(angle), y + a * math.sin(angle) + b * math.cos(angle))
            for a, b in ((left, -ascent), (left + width, -ascent), (left + width, -descent), (left, -descent))]


def rectangles_overlap(a, b):
    for polygon in (a, b):
        for first, second in zip(polygon, polygon[1:] + polygon[:1]):
            axis = (first[1] - second[1], second[0] - first[0])
            pa = [x * axis[0] + y * axis[1] for x, y in a]
            pb = [x * axis[0] + y * axis[1] for x, y in b]
            if max(pa) <= min(pb) + 1e-8 or max(pb) <= min(pa) + 1e-8:
                return False
    return True


def typography_check(primitives):
    texts = [(p, text_rectangle(p)) for p in primitives if p["kind"] == "text"]
    for p, rectangle in texts:
        require(all(0 <= x <= WIDTH and 0 <= y <= HEIGHT for x, y in rectangle), "Text clips the page: " + p["text"])
    for i, (p, rectangle) in enumerate(texts):
        for other, bounds in texts[:i]:
            require(not rectangles_overlap(rectangle, bounds), "Text bounds overlap: " + p["text"] + " / " + other["text"])
        for swatch in (x for x in primitives if x["role"] == "legend_swatch"):
            require(not rectangles_overlap(rectangle, swatch["points"]), "Text overlaps a legend swatch: " + p["text"])
    tips = [(p, rectangle) for p, rectangle in texts if p["role"] == "tip_label"]
    tip_corners = [corner for _, rectangle in tips for corner in rectangle]
    annotation_bottom = max(y for p, rectangle in texts if p["role"] == "annotation" for _, y in rectangle)
    legend_top = min(y for p, rectangle in texts if p["role"] == "legend" for _, y in rectangle)
    scale = INTENDED_PRINT_WIDTH_MM * 72 / 25.4 / WIDTH
    return {"intended_print_width_mm": INTENDED_PRINT_WIDTH_MM, "print_scale": scale,
            "tip_font_source_points": TIP_FONT_SIZE, "tip_font_print_points": TIP_FONT_SIZE * scale,
            "note_font_source_points": NOTE_FONT_SIZE, "note_font_print_points": NOTE_FONT_SIZE * scale,
            "conservative_text_bounds": "Helvetica advance width and font ascent/descent; rotated rectangles",
            "all_text_inside_page": True, "text_overlap_count": 0, "legend_swatch_text_overlap_count": 0,
            "tip_north_y": min(y for _, y in tip_corners), "tip_south_y": max(y for _, y in tip_corners),
            "header_to_tip_clearance_points": min(y for _, y in tip_corners) - annotation_bottom,
            "tip_to_footer_clearance_points": legend_top - max(y for _, y in tip_corners)}


def scene(root, leaves, cells, states, provenance):
    primitives, branches, mapping = [], [], []
    for i, leaf in enumerate(leaves):
        leaf.angle = -math.pi / 2 + 2 * math.pi * i / len(leaves)
        leaf.descendants = [leaf.label]
    def position(n, depth=0):
        require(math.isfinite(depth), "Cumulative branch depth is nonfinite")
        n.depth = depth
        if n.children:
            for child in n.children:
                position(child, depth + child.length)
            n.angle = (n.children[0].angle + n.children[-1].angle) / 2
            n.descendants = [a for child in n.children for a in child.descendants]
    position(root)
    maximum = max(n.depth for n in leaves)
    require(maximum > 0, "An all-zero phylogram cannot show a branch-length scale")
    scale = TREE_RADIUS / maximum
    require(math.isfinite(scale), "Branch-length scale is nonfinite")
    indexed = list(nodes(root))
    for i, n in enumerate(indexed):
        n.index = i
    for i, n in enumerate(nodes(root)):
        if n.children:
            if n.depth > 0:
                primitives.append({"kind": "line", "points": arc_points(n.depth * scale, n.children[0].angle, n.children[-1].angle),
                                   "stroke": "#263238", "width": 0.65, "role": "topology_connector", "node": i})
            for child in n.children:
                edge = {"kind": "line", "points": [point(n.depth * scale, child.angle), point(child.depth * scale, child.angle)],
                        "stroke": "#263238", "width": 0.65, "role": "phylogenetic_edge", "node": child.index}
                primitives.append(edge)
    for n in indexed[1:]:
        branches.append({"node": n.index, "input_branch_length": n.length, "input_label": n.label,
                         "descendant_accessions": n.descendants, "radial_end": n.depth * scale,
                         "radial_start": (n.depth - n.length) * scale, "angle_degrees": math.degrees(n.angle)})
    from reportlab.pdfbase.pdfmetrics import getAscentDescent
    ascent, descent = getAscentDescent("Helvetica", TIP_FONT_SIZE)
    offset = (ascent + descent) / 2
    step = 2 * math.pi / len(leaves)
    for leaf in leaves:
        primitives.append({"kind": "line", "points": [point(leaf.depth * scale, leaf.angle), point(RING_INNER - 2, leaf.angle)],
                           "stroke": "#c5c9cb", "width": 0.35, "dash": True, "role": "nonphylogenetic_tip_leader", "accession": leaf.label})
        for ring, rm_type in enumerate(TYPES):
            value = cells[leaf.label][rm_type]
            color = COLORS[rm_type] if value == "1" else WHITE if value == "0" else UNKNOWN
            inner = RING_INNER + ring * (RING_WIDTH + RING_GAP)
            start, end = leaf.angle - step * 0.46, leaf.angle + step * 0.46
            polygon = arc_points(inner, start, end) + list(reversed(arc_points(inner + RING_WIDTH, start, end)))
            p = {"kind": "polygon", "points": polygon, "fill": color, "stroke": "#b0b0b0", "width": 0.2,
                 "role": "ring_cell", "accession": leaf.label, "rm_type": rm_type, "value": value, "ring": ring + 1}
            primitives.append(p)
            mapping.append({"accession": leaf.label, "rm_type": rm_type, "inner_to_outer_ring": ring + 1,
                            "value": value, "fill": color, "state": states[(leaf.label, rm_type)]["state"],
                            "angle_degrees": math.degrees(leaf.angle), "inner_radius": inner,
                            "outer_radius": inner + RING_WIDTH})
            mapping[-1].update({key: states[(leaf.label, rm_type)][key] for key in
                               ("complete_count", "partial_count", "candidate_count", "search_complete", "conflict", "review_ids", "positive_invalidated", "count_lower_bound")})
        angle = math.degrees(leaf.angle)
        left = math.cos(leaf.angle) < -1e-12
        rotation = angle + (180 if left else 0)
        x, y = point(399, leaf.angle)
        baseline = (x - offset * math.sin(math.radians(rotation)), y + offset * math.cos(math.radians(rotation)))
        primitives.append({"kind": "text", "point": baseline, "radial_anchor": (x, y), "text": leaf.label,
                           "size": TIP_FONT_SIZE, "rotation": rotation, "anchor": "end" if left else "start",
                           "fill": "#263238", "role": "tip_label", "accession": leaf.label})
    synthetic = provenance["dataset_kind"] == "SYNTHETIC"
    title = "SYNTHETIC TEST ONLY - circular R-M rendering" if synthetic else "Host phylogeny and predicted R-M systems"
    if provenance["documented_exception_count"]:
        title = "Host phylogeny and R-M predictions - documented exceptions"
        primitives.append({"kind": "text", "point": (50, 1143), "text":
            f"Qualified panel accounting: {provenance['documented_exception_count']} documented search exceptions; see exception_manifest.json. Grey preserves missing/unresolved evidence.",
            "size": NOTE_FONT_SIZE, "fill": "#455a64", "role": "qualification"})
    primitives.extend([
        {"kind": "text", "point": (550, 20), "text": title, "size": 15, "anchor": "middle", "fill": "#263238", "role": "title"},
        {"kind": "text", "point": (550, 36), "text": "Unrooted phylogeny; serialization anchor is a display choice. Radial distances retain input branch lengths.", "size": NOTE_FONT_SIZE, "anchor": "middle", "fill": "#455a64", "role": "annotation"},
        {"kind": "text", "point": (50, 1070), "text": "Rings, inner to outer: I | II (including IIG) | III | IV", "size": NOTE_FONT_SIZE, "fill": "#263238", "role": "legend"},
        {"kind": "text", "point": (50, 1108), "text": "White: screened nondetection. Grey: unknown / incomplete / unresolved. Presence: complete predicted architecture.", "size": NOTE_FONT_SIZE, "fill": "#455a64", "role": "legend"},
        {"kind": "text", "point": (50, 1125), "text": "Accession-keyed cells; no unresolved result is treated as biological absence. Dashed leaders are not phylogenetic edges.", "size": NOTE_FONT_SIZE, "fill": "#455a64", "role": "legend"},
    ])
    for i, t in enumerate(TYPES):
        x = 50 + i * 180
        primitives.extend([
            {"kind": "polygon", "points": [(x, 1080), (x + 12, 1080), (x + 12, 1092), (x, 1092)], "fill": COLORS[t], "stroke": "#777777", "width": 0.3, "role": "legend_swatch"},
            {"kind": "text", "point": (x + 18, 1089), "text": LABELS[i], "size": NOTE_FONT_SIZE, "fill": "#263238", "role": "legend"},
        ])
    scale_value = 10 ** math.floor(math.log10(maximum / 4))
    for multiplier in (5, 2, 1):
        if scale_value * multiplier <= maximum / 3:
            scale_value *= multiplier
            break
    bar = scale_value * scale
    primitives.extend([
        {"kind": "line", "points": [(850, 1084), (850 + bar, 1084)], "stroke": "#263238", "width": 1.2, "role": "scale"},
        {"kind": "text", "point": (850, 1100), "text": f"{scale_value:g} substitutions/site", "size": NOTE_FONT_SIZE, "fill": "#263238", "role": "scale"},
    ])
    return {"schema": "stage06-vector-scene-v1", "width": WIDTH, "height": HEIGHT,
            "provenance": provenance, "tip_order": [n.label for n in leaves], "ring_order": list(TYPES),
            "rooting": "UNROOTED_NO_VALIDATED_OUTGROUP", "branch_length_units": "substitutions/site",
            "radial_points_per_unit": scale, "tree_root_stem_not_a_phylogenetic_edge": root.length,
            "branches": branches, "cell_mapping": mapping, "primitives": primitives, "typography": typography_check(primitives)}


def svg_export(data, path, scene_hash):
    esc = lambda x: html.escape(str(x), quote=True)
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}pt" height="{HEIGHT}pt" viewBox="0 0 {WIDTH} {HEIGHT}">',
             '<title>' + esc("Circular unrooted phylogram with four explicit R-M state rings") + '</title>',
             '<metadata>' + esc(canonical({"scene_sha256": scene_hash, **data["provenance"]})) + '</metadata>',
             f'<rect width="{WIDTH}" height="{HEIGHT}" fill="white"/>']
    for p in data["primitives"]:
        attrs = f' data-role="{esc(p["role"])}"'
        for key in ("accession", "rm_type", "value", "ring", "node"):
            if key in p:
                attrs += f' data-{key.replace("_", "-")}="{esc(p[key])}"'
        if p["kind"] in ("line", "polygon"):
            points = " ".join(f"{x:.6f},{y:.6f}" for x, y in p["points"])
            tag = "polyline" if p["kind"] == "line" else "polygon"
            dash = ' stroke-dasharray="1.5,2"' if p.get("dash") else ""
            lines.append(f'<{tag} points="{points}" fill="{p.get("fill", "none")}" stroke="{p["stroke"]}" stroke-width="{p["width"]}"{dash}{attrs}/>')
        else:
            x, y = p["point"]
            rotation = p.get("rotation", 0)
            lines.append(f'<text x="{x:.6f}" y="{y:.6f}" font-family="Helvetica,Arial,sans-serif" font-size="{p["size"]}" fill="{p["fill"]}" text-anchor="{p.get("anchor", "start")}" transform="rotate({rotation:.6f} {x:.6f} {y:.6f})"{attrs}>{esc(p["text"])}</text>')
    lines.append("</svg>")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def pdf_export(data, path, scene_hash):
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    c = canvas.Canvas(str(path), pagesize=(WIDTH, HEIGHT), invariant=1, pageCompression=1)
    c.setTitle("Circular unrooted host phylogram and R-M states")
    c.setAuthor("LAB R-M phylogenomics reproducible Stage6 renderer")
    c.setSubject(canonical({"scene_sha256": scene_hash, **data["provenance"]}))
    for p in data["primitives"]:
        c.saveState()
        if p["kind"] in ("line", "polygon"):
            c.setStrokeColor(HexColor(p["stroke"]))
            c.setLineWidth(p["width"])
            if p.get("dash"):
                c.setDash(1.5, 2)
            path_obj = c.beginPath()
            for i, (x, y) in enumerate(p["points"]):
                (path_obj.moveTo if i == 0 else path_obj.lineTo)(x, HEIGHT - y)
            if p["kind"] == "polygon":
                path_obj.close()
                c.setFillColor(HexColor(p["fill"]))
            c.drawPath(path_obj, stroke=1, fill=int(p["kind"] == "polygon"))
        else:
            x, y = p["point"]
            c.translate(x, HEIGHT - y)
            c.rotate(-p.get("rotation", 0))
            c.setFont("Helvetica", p["size"])
            c.setFillColor(HexColor(p["fill"]))
            method = {"middle": c.drawCentredString, "end": c.drawRightString}.get(p.get("anchor"), c.drawString)
            method(0, 0, p["text"])
        c.restoreState()
    c.showPage()
    c.save()


def itol_exports(out, data, cells):
    tips = data["tip_order"]
    binary = ["DATASET_BINARY", "SEPARATOR TAB", "DATASET_LABEL\tR-M binary convenience (NA omitted)", "COLOR\t#26828e",
              "FIELD_SHAPES\t1\t1\t1\t1", "FIELD_LABELS\t" + "\t".join(LABELS),
              "FIELD_COLORS\t" + "\t".join(COLORS[t] for t in TYPES), "DATA"]
    binary += [a + "\t" + "\t".join("-1" if cells[a][t] == "NA" else cells[a][t] for t in TYPES) for a in tips]
    (out / "itol_binary_convenience.txt").write_text("\n".join(binary) + "\n", encoding="utf-8", newline="\n")
    for i, t in enumerate(TYPES):
        lines = ["DATASET_COLORSTRIP", "SEPARATOR TAB", "DATASET_LABEL\t" + LABELS[i] + " (full state)", "COLOR\t" + COLORS[t],
                 "COLOR_BRANCHES\t0", "STRIP_WIDTH\t12", "MARGIN\t3", "BORDER_WIDTH\t0.2", "BORDER_COLOR\t#b0b0b0",
                 "LEGEND_TITLE\t" + LABELS[i], "LEGEND_SHAPES\t1\t1\t1",
                 "LEGEND_COLORS\t" + COLORS[t] + "\t" + WHITE + "\t" + UNKNOWN,
                 "LEGEND_LABELS\tComplete predicted architecture\tScreened nondetection\tUnknown / incomplete / unresolved", "DATA"]
        for a in tips:
            v = cells[a][t]
            color = COLORS[t] if v == "1" else WHITE if v == "0" else UNKNOWN
            lines.append("\t".join((a, color, "present" if v == "1" else "screened nondetection" if v == "0" else "unknown")))
        (out / f"itol_{i + 1:02d}_{t}_full_state.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def render(args):
    import reportlab
    root, leaves, cells, states, prov, original = parse_inputs(args.tree, args.matrix, args.state, args.approved,
        args.join, args.tree_validation, args.curation_validation, args.curation_source_manifest, args.synthetic, args.exception_manifest)
    require(not args.output.exists(), "Output namespace must be new; no overwrite is permitted")
    data = scene(root, leaves, cells, states, prov)
    scene_hash = hashlib.sha256(canonical(data).encode()).hexdigest()
    args.output.mkdir(parents=True)
    out = args.output
    (out / "scene.json").write_text(canonical(data) + "\n", encoding="utf-8", newline="\n")
    for name, source in (("host_tree.nwk", args.tree), ("rm_type_presence_absence.tsv", args.matrix), ("rm_type_state.tsv", args.state),
                         ("approved_accessions.txt", args.approved), ("join_validation.json", args.join), ("tree_validation.json", args.tree_validation)):
        shutil.copyfile(source, out / name)
    shutil.copyfile(args.curation_validation, out / "curation_validation.json")
    shutil.copyfile(args.curation_source_manifest, out / "curation_source_manifest.json")
    if args.exception_manifest is not None:
        shutil.copyfile(args.exception_manifest, out / "exception_manifest.json")
    (out / "host_tree_unrooted.nex").write_text("#NEXUS\nBegin trees;\nTree host = [&U] " + original.strip() + "\nEnd;\n", encoding="utf-8", newline="\n")
    with (out / "cell_mapping.tsv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(data["cell_mapping"][0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(data["cell_mapping"])
    (out / "branch_mapping.json").write_text(json.dumps(data["branches"], indent=2) + "\n", encoding="utf-8", newline="\n")
    svg_export(data, out / "circular_rm.svg", scene_hash)
    pdf_export(data, out / "circular_rm.pdf", scene_hash)
    itol_exports(out, data, cells)
    (out / "README.txt").write_text(
        "DATASET: " + prov["dataset_kind"] + "\n" +
        "Tree topology and child order are unchanged. No biological root is asserted; root stem is not an incoming phylogenetic edge.\n" +
        "Radial branch distances preserve input lengths; circular connectors and dashed tip leaders are display geometry.\n" +
        "Rings inner to outer: I, II (including IIG), III, IV. Coloured=complete predicted architecture; white=screened nondetection; grey=unknown/incomplete/unresolved.\n" +
        "For the intended iTOL four-ring view, upload host_tree.nwk and the four numbered full_state COLORSTRIP files, ordered01to04 inner to outer.\n" +
        "Use circular phylogram, retain branch lengths, disable leaf sorting and do not reroot. Set dataset order explicitly in the iTOL editor.\n" +
        "itol_binary_convenience.txt is an alternative convenience dataset. Its -1 cells are completely omitted by iTOL; it cannot display grey uncertainty.\n" +
        "Do not use binary alone for a figure with unknowns, or stack binary and full-state strips as eight rings. The four full-state strips encode every cell.\n" +
        "Sources: https://itol.embl.de/help/dataset_binary_template.txt ; https://itol.embl.de/help/dataset_color_strip_template.txt ; https://itol.embl.de/help.cgi\n" +
        "SVG and PDF derive from the exact same scene.json. Hashes, accession-keyed cell_mapping.tsv and branch_mapping.json provide provenance.\n" +
        "Production additionally requires independent scientific curation acceptance and a pinned detailed source/model/code/review manifest; accounting-only joins are insufficient.\n" +
        "Curation status: " + prov["curation_status"] + "; documented exception count: " + str(prov["documented_exception_count"]) + ". Qualified accounting never asserts completion of an excepted detector job.\n" +
        "The renderer validates an acceptance gate; it does not create a scientific acceptance decision. Run the separate checker before publication.\n",
        encoding="utf-8", newline="\n")
    manifest = {"schema": "stage06-export-v1", "dataset_kind": prov["dataset_kind"], "scene_sha256": scene_hash,
                "renderer_sha256": digest(__file__), "provenance": prov, "tip_count": len(leaves), "cell_count": len(leaves) * 4,
                "runtime": {"python": platform.python_version(), "reportlab": reportlab.Version},
                "branch_count": len(data["branches"]), "outputs": {p.name: digest(p) for p in sorted(out.iterdir()) if p.is_file()}}
    (out / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("tree", "matrix", "state", "approved", "join", "tree-validation", "curation-validation", "curation-source-manifest", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--synthetic", action="store_true", help="Explicitly permit small synthetic fixtures; never authorizes production")
    p.add_argument("--exception-manifest", type=Path, help="Required only for independently accepted documented exceptions")
    args = p.parse_args()
    try:
        print(json.dumps(render(args), indent=2))
    except (ValueError, KeyError, OSError, TypeError) as error:
        p.exit(2, "Renderer refused: " + str(error) + "\n")


if __name__ == "__main__":
    main()
