import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

PADLOC_BROAD = {
    "RM_type_I":   "Type_I",
    "RM_type_II":  "Type_II",
    "RM_type_IIG": "Type_II",
    "RM_type_III": "Type_III",
    "RM_type_IV":  "Type_IV",
    "RM_type_HNH": "UNRESOLVED",
}

DF_MODEL_BROAD = {
    ("RM", "RM_Type_I"): "Type_I",
    ("RM_Type_I", "N6_RM_Type_I"): "Type_I",

    ("RM", "RM_Type_II"): "Type_II",
    ("RM", "RM_Type_IIG"): "Type_II",
    ("RM", "RM_Type_IIG_2"): "Type_II",
    ("RM_Type_II", "DNA_met_RM_Type_II_PDDEXK"): "Type_II",
    ("RM_Type_II", "D12_RM_Type_II_PDDEXK"): "Type_II",
    ("RM_Type_II", "N6_N4_RM_Type_II_PDDEXK"): "Type_II",
    ("RM_Type_II", "DNA_met_RM_Type_II_PLD"): "Type_II",
    ("RM_Type_II", "N6_RM_Type_II_PDDEXK"): "Type_II",
    ("RM_Type_II", "DNA_met_RM_Type_II_HATPase"): "Type_II",
    ("RM_Type_II", "N6_N4_RM_Type_II_HATPase"): "Type_II",

    ("RM", "RM_Type_III"): "Type_III",
    ("RM_Type_III", "N6_N4_RM_Type_III"): "Type_III",

    ("RM", "RM_Type_IV"): "Type_IV",
    ("GmrSD_RM_Type_IV", "GmrSD_RM_Type_IV"): "Type_IV",
}

def defensefinder_rm_like(row):
    text = f"{row.get('type', '')} {row.get('subtype', '')}".lower()
    return ("rm" in text) or ("restriction" in text)

SYSTEM_FIELDS = [
    "detector",
    "assembly_id",
    "raw_system_id",
    "detector_type",
    "detector_subtype",
    "broad_type",
    "mapping_state",
    "replicon",
    "locus_start",
    "locus_end",
    "gene_count",
    "generated_ids",
    "protein_ids",
    "locus_tags",
    "gene_names",
    "strands",
    "sys_wholeness",
    "sys_score",
    "padloc_contig_end",
    "source_system_file",
]

GENE_FIELDS = [
    "detector",
    "assembly_id",
    "raw_system_id",
    "detector_type",
    "detector_subtype",
    "broad_type",
    "replicon",
    "generated_id",
    "protein_id",
    "locus_tag",
    "start",
    "end",
    "strand",
    "gene_name",
    "hmm_name",
    "relative_position",
    "hit_i_eval",
    "hit_score",
    "hit_profile_cov",
    "hit_seq_cov",
]

def read_table(path, delimiter):
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=delimiter))

def write_tsv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t",
                           extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

def as_int(x):
    return int(x) if x not in (None, "") else None

def joined(values):
    return ";".join("" if v is None else str(v) for v in values)

def unique_one(values, label):
    vals = {v for v in values if v not in (None, "")}
    if len(vals) != 1:
        raise RuntimeError(f"{label}: expected exactly one value, got {sorted(vals)}")
    return next(iter(vals))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    args = ap.parse_args()

    root = Path(args.root)
    manifest_path = root / "reference" / "genome_manifest.tsv"
    manifest = read_table(manifest_path, "\t")

    accessions = [r["assembly_id"] for r in manifest]
    if len(accessions) != 196 or len(set(accessions)) != 196:
        raise RuntimeError(
            f"Manifest must contain exactly 196 unique assemblies; got "
            f"{len(accessions)} rows / {len(set(accessions))} unique"
        )

    system_rows = []
    gene_rows = []
    validation = []

    for acc in accessions:
        padloc_file = root / "results" / acc / "padloc" / "protein_padloc.csv"
        df_dir = root / "results" / acc / "defensefinder"
        df_systems_file = df_dir / "defensefinder_gembase_defense_finder_systems.tsv"
        df_genes_file = df_dir / "defensefinder_gembase_defense_finder_genes.tsv"
        df_map_file = root / "defensefinder_input" / acc / "defensefinder_protein_map.tsv"

        for p in [padloc_file, df_systems_file, df_genes_file, df_map_file]:
            if not p.exists():
                raise RuntimeError(f"{acc}: missing required file: {p}")

        # Reversible positional map generated before DefenseFinder.
        map_rows = read_table(df_map_file, "\t")
        by_generated = {}
        by_exact_locus = {}

        for r in map_rows:
            gid = r["generated_id"]
            if gid in by_generated:
                raise RuntimeError(f"{acc}: duplicate generated_id {gid}")
            by_generated[gid] = r

            key = (
                r["seqid"],
                r["protein_id"],
                as_int(r["start"]),
                as_int(r["end"]),
            )
            if key in by_exact_locus:
                raise RuntimeError(f"{acc}: duplicate exact locus mapping {key}")
            by_exact_locus[key] = r

        # ---------------- PADLOC ----------------
        padloc = read_table(padloc_file, ",")
        padloc_rm = [r for r in padloc if r["system"].startswith("RM_")]

        padloc_groups = defaultdict(list)
        for r in padloc_rm:
            n = r["system.number"]
            if not n:
                raise RuntimeError(f"{acc}: PADLOC R-M row without system.number")
            padloc_groups[n].append(r)

        padloc_count = 0
        for sysnum, rows in padloc_groups.items():
            sysname = unique_one([r["system"] for r in rows],
                                 f"{acc}/PADLOC/{sysnum}/system")

            if sysname not in PADLOC_BROAD:
                raise RuntimeError(
                    f"{acc}: unexpected PADLOC R-M system label: {sysname}"
                )

            rows = sorted(
                rows,
                key=lambda r: (
                    as_int(r["relative.position"]) or 10**12,
                    as_int(r["start"]) or 10**12,
                ),
            )

            replicon = unique_one(
                [r["seqid"] for r in rows],
                f"{acc}/PADLOC/{sysnum}/replicon"
            )

            mapped = []
            for r in rows:
                key = (
                    r["seqid"],
                    r["target.name"],
                    as_int(r["start"]),
                    as_int(r["end"]),
                )
                m = by_exact_locus.get(key)
                if m is None:
                    raise RuntimeError(
                        f"{acc}: PADLOC protein could not be mapped exactly: {key}"
                    )
                mapped.append(m)

            broad = PADLOC_BROAD[sysname]
            state = "UNRESOLVED_HNH" if sysname == "RM_type_HNH" else "MAPPED"

            raw_id = f"PADLOC:{acc}:{sysnum}"
            starts = [as_int(r["start"]) for r in rows]
            ends = [as_int(r["end"]) for r in rows]

            system_rows.append({
                "detector": "PADLOC",
                "assembly_id": acc,
                "raw_system_id": raw_id,
                "detector_type": sysname,
                "detector_subtype": sysname,
                "broad_type": broad,
                "mapping_state": state,
                "replicon": replicon,
                "locus_start": min(starts),
                "locus_end": max(ends),
                "gene_count": len(rows),
                "generated_ids": joined([m["generated_id"] for m in mapped]),
                "protein_ids": joined([r["target.name"] for r in rows]),
                "locus_tags": joined([m["locus_tag"] for m in mapped]),
                "gene_names": joined([r["protein.name"] for r in rows]),
                "strands": joined([r["strand"] for r in rows]),
                "sys_wholeness": "",
                "sys_score": "",
                "padloc_contig_end": joined(sorted({
                    r["contig.end"] for r in rows if r["contig.end"]
                })),
                "source_system_file": str(padloc_file.relative_to(root)),
            })

            for r, m in zip(rows, mapped):
                gene_rows.append({
                    "detector": "PADLOC",
                    "assembly_id": acc,
                    "raw_system_id": raw_id,
                    "detector_type": sysname,
                    "detector_subtype": sysname,
                    "broad_type": broad,
                    "replicon": r["seqid"],
                    "generated_id": m["generated_id"],
                    "protein_id": r["target.name"],
                    "locus_tag": m["locus_tag"],
                    "start": r["start"],
                    "end": r["end"],
                    "strand": r["strand"],
                    "gene_name": r["protein.name"],
                    "hmm_name": r["hmm.name"],
                    "relative_position": r["relative.position"],
                    "hit_i_eval": r["domain.iE.value"],
                    "hit_score": "",
                    "hit_profile_cov": r["hmm.coverage"],
                    "hit_seq_cov": r["target.coverage"],
                })

            padloc_count += 1

        # ---------------- DefenseFinder ----------------
        dfs = read_table(df_systems_file, "\t")
        dfg = read_table(df_genes_file, "\t")

        df_gene_groups = defaultdict(list)
        for r in dfg:
            if r["sys_id"]:
                df_gene_groups[r["sys_id"]].append(r)

        df_count = 0
        for s in dfs:
            if not defensefinder_rm_like(s):
                continue

            subtype = s["subtype"]
            model_key = (s["type"], subtype)
            if model_key not in DF_MODEL_BROAD:
                raise RuntimeError(
                    f"{acc}: unexpected DefenseFinder R-M model: "
                    f"type={s['type']!r}, subtype={subtype!r}"
                )

            sys_id = s["sys_id"]
            rows = df_gene_groups.get(sys_id, [])
            if not rows:
                raise RuntimeError(
                    f"{acc}: DefenseFinder R-M system {sys_id} has no gene rows"
                )

            rows = sorted(
                rows,
                key=lambda r: as_int(r["hit_pos"]) or 10**12
            )

            mapped = []
            for r in rows:
                gid = r["hit_id"]
                if gid not in by_generated:
                    raise RuntimeError(
                        f"{acc}: DefenseFinder hit_id absent from positional map: {gid}"
                    )
                mapped.append(by_generated[gid])

            replicon = unique_one(
                [m["seqid"] for m in mapped],
                f"{acc}/DefenseFinder/{sys_id}/replicon"
            )

            summary_ids = {
                x for x in s["protein_in_syst"].split(",") if x
            }
            gene_ids = {r["hit_id"] for r in rows}
            protein_set_match = (summary_ids == gene_ids)

            expected_gene_count = as_int(s["genes_count"])
            gene_count_match = (
                expected_gene_count is None or expected_gene_count == len(rows)
            )

            broad = DF_MODEL_BROAD[model_key]
            starts = [as_int(m["start"]) for m in mapped]
            ends = [as_int(m["end"]) for m in mapped]

            system_rows.append({
                "detector": "DefenseFinder",
                "assembly_id": acc,
                "raw_system_id": sys_id,
                "detector_type": s["type"],
                "detector_subtype": subtype,
                "broad_type": broad,
                "mapping_state": "MAPPED",
                "replicon": replicon,
                "locus_start": min(starts),
                "locus_end": max(ends),
                "gene_count": len(rows),
                "generated_ids": joined([r["hit_id"] for r in rows]),
                "protein_ids": joined([m["protein_id"] for m in mapped]),
                "locus_tags": joined([m["locus_tag"] for m in mapped]),
                "gene_names": joined([r["gene_name"] for r in rows]),
                "strands": joined([m["strand"] for m in mapped]),
                "sys_wholeness": unique_one(
                    [r["sys_wholeness"] for r in rows],
                    f"{acc}/DefenseFinder/{sys_id}/sys_wholeness"
                ),
                "sys_score": unique_one(
                    [r["sys_score"] for r in rows],
                    f"{acc}/DefenseFinder/{sys_id}/sys_score"
                ),
                "padloc_contig_end": "",
                "source_system_file": str(df_systems_file.relative_to(root)),
            })

            for r, m in zip(rows, mapped):
                gene_rows.append({
                    "detector": "DefenseFinder",
                    "assembly_id": acc,
                    "raw_system_id": sys_id,
                    "detector_type": r["type"],
                    "detector_subtype": r["subtype"],
                    "broad_type": broad,
                    "replicon": m["seqid"],
                    "generated_id": r["hit_id"],
                    "protein_id": m["protein_id"],
                    "locus_tag": m["locus_tag"],
                    "start": m["start"],
                    "end": m["end"],
                    "strand": m["strand"],
                    "gene_name": r["gene_name"],
                    "hmm_name": r["gene_name"],
                    "relative_position": r["hit_pos"],
                    "hit_i_eval": r["hit_i_eval"],
                    "hit_score": r["hit_score"],
                    "hit_profile_cov": r["hit_profile_cov"],
                    "hit_seq_cov": r["hit_seq_cov"],
                })

            validation.append({
                "assembly_id": acc,
                "sys_id": sys_id,
                "protein_set_match": protein_set_match,
                "gene_count_match": gene_count_match,
            })

            df_count += 1

    outdir = root / "results" / "stage05_raw"
    outdir.mkdir(parents=True, exist_ok=True)

    system_rows.sort(
        key=lambda r: (
            r["assembly_id"],
            r["detector"],
            r["replicon"],
            int(r["locus_start"]),
            r["raw_system_id"],
        )
    )

    gene_rows.sort(
        key=lambda r: (
            r["assembly_id"],
            r["detector"],
            r["replicon"],
            int(r["start"]),
            r["raw_system_id"],
        )
    )

    write_tsv(outdir / "rm_systems_raw.tsv", system_rows, SYSTEM_FIELDS)
    write_tsv(outdir / "rm_system_genes_raw.tsv", gene_rows, GENE_FIELDS)

    bad_validation = [
        r for r in validation
        if not r["protein_set_match"] or not r["gene_count_match"]
    ]

    summary = {
        "assemblies": len(accessions),
        "raw_systems_total": len(system_rows),
        "raw_gene_rows_total": len(gene_rows),
        "systems_by_detector": dict(Counter(r["detector"] for r in system_rows)),
        "systems_by_detector_subtype": dict(
            Counter(f'{r["detector"]}:{r["detector_subtype"]}' for r in system_rows)
        ),
        "systems_by_broad_type": dict(
            Counter(r["broad_type"] for r in system_rows)
        ),
        "unresolved_systems": sum(
            1 for r in system_rows if r["broad_type"] == "UNRESOLVED"
        ),
        "defensefinder_validation_mismatches": len(bad_validation),
    }

    with (outdir / "rm_systems_raw_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)

    if bad_validation:
        write_tsv(
            outdir / "defensefinder_raw_validation_mismatches.tsv",
            bad_validation,
            ["assembly_id", "sys_id", "protein_set_match", "gene_count_match"],
        )
        raise RuntimeError(
            f"DefenseFinder system/gene validation mismatches: {len(bad_validation)}"
        )

    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"SYSTEMS={outdir / 'rm_systems_raw.tsv'}")
    print(f"GENES={outdir / 'rm_system_genes_raw.tsv'}")

if __name__ == "__main__":
    main()
