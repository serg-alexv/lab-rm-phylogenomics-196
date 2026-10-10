#!/usr/bin/env python3
"""Build a reviewable iTOL label/color bundle from approved LAB R-M metadata."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

PROJECT = Path(r"G:\My Drive\LAB_RM\lab-rm-phylogenomics-196")
OUT = Path(__file__).resolve().parent
PANEL = PROJECT / "config" / "approved_panel.tsv"
ACCESSIONS = PROJECT / "config" / "approved_accessions.txt"
LABEL_TEMPLATE = "https://itol.embl.de/help/labels_template.txt"
COLOR_TEMPLATE = "https://itol.embl.de/help/colors_styles_template.txt"
COLORS = {
    "Lacticaseibacillus": "#0072B2",
    "Lactiplantibacillus": "#E69F00",
    "Lactobacillus_sensu_stricto": "#009E73",
    "Lactococcus": "#CC79A7",
    "Leuconostoc": "#56B4E9",
    "Limosilactobacillus": "#D55E00",
    "Oenococcus": "#F0E442",
    "Pediococcus": "#332288",
    "Streptococcus_thermophilus": "#AA4499",
    "Weissella": "#44AA99",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_text(name, text):
    path = OUT / name
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


with PANEL.open(encoding="utf-8-sig", newline="") as f:
    panel = list(csv.DictReader(f, delimiter="\t"))
approved = [line.strip() for line in ACCESSIONS.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
if len(panel) != 196 or len(approved) != 196 or len(set(approved)) != 196:
    raise SystemExit("Expected 196 panel rows and 196 unique approved accessions")
if set(COLORS) != {r["operational_group"] for r in panel}:
    raise SystemExit("Color palette groups do not exactly match panel operational groups")
if set(approved) != {r["assembly_accession"] for r in panel}:
    raise SystemExit("Approved accession membership differs from panel")
if any(not r["display_label"].strip() for r in panel):
    raise SystemExit("Panel contains an empty display_label")

rows = []
for r in panel:
    accession = r["assembly_accession"].strip()
    group = r["operational_group"].strip()
    # Preserve the approved display label verbatim and append accession for unique tips.
    label = f'{r["display_label"].strip()} [{accession}]'
    rows.append((accession, label, group, COLORS[group]))
if len({x[1] for x in rows}) != 196:
    raise SystemExit("Disambiguated display labels are not unique")

mapping = write_text("cell_mapping.tsv", "assembly_accession\tdisplay_label\toperational_group\tcolor\n" + "".join("\t".join(x) + "\n" for x in rows))
labels = write_text("itol_labels.txt", "LABELS\nSEPARATOR TAB\nDATA\n" + "".join(f"{a}\t{label}\n" for a, label, _, _ in rows))
colors = write_text("itol_group_colors.txt", "TREE_COLORS\nSEPARATOR TAB\nDATA\n" + "".join(f"{a}\tlabel\t{color}\n" for a, _, _, color in rows))
counts = Counter(group for _, _, group, _ in rows)
legend = write_text("color_legend.tsv", "operational_group\tcolor\taccession_count\n" + "".join(f"{g}\t{COLORS[g]}\t{counts[g]}\n" for g in COLORS))

files = {}
for path in (mapping, labels, colors, legend):
    files[path.name] = {"bytes": path.stat().st_size, "sha256": sha(path)}
manifest = {
    "receipt_type": "itol_label_color_preparation",
    "schema_version": 1,
    "source_project": str(PROJECT),
    "source_files": {
        "config/approved_panel.tsv": {"bytes": PANEL.stat().st_size, "sha256": sha(PANEL)},
        "config/approved_accessions.txt": {"bytes": ACCESSIONS.stat().st_size, "sha256": sha(ACCESSIONS)},
    },
    "source_columns": ["assembly_accession", "display_label", "operational_group"],
    "approved_accession_count": len(approved),
    "panel_row_count": len(panel),
    "exact_accession_membership": True,
    "unique_disambiguated_labels": len({x[1] for x in rows}),
    "group_counts": dict(counts),
    "label_rule": "Approved display_label preserved verbatim, followed by space and [assembly_accession].",
    "taxonomy_policy": "Operational group and historical panel metadata copied as supplied; no taxonomy reclassification or source-claim changes.",
    "itol_templates": {"labels": LABEL_TEMPLATE, "tree_colors": COLOR_TEMPLATE},
    "files": files,
    "limitations": ["Prepared annotations only; exact compatibility with actual tree tip IDs has not been validated."],
}
manifest_path = OUT / "manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"output": str(OUT), "rows": len(rows), "groups": dict(counts), "files": files, "manifest_sha256": sha(manifest_path)}, indent=2))