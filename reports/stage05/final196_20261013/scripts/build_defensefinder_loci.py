import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


def read_tsv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def write_tsv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=fields,
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )
        w.writeheader()
        w.writerows(rows)


def split_field(value):
    return [x for x in (value or "").split(";") if x]


def uniq(values):
    return sorted({v for v in values if v not in ("", None)})


def main():
    root = Path.home() / "LAB_RM_STAGE5"
    indir = root / "results" / "stage05_raw"
    systems_path = indir / "rm_systems_raw.tsv"

    rows = [
        r for r in read_tsv(systems_path)
        if r["detector"] == "DefenseFinder"
    ]

    if len(rows) != 382:
        raise RuntimeError(
            f"Expected 382 raw DefenseFinder R-M rows, got {len(rows)}"
        )

    # ------------------------------------------------------------
    # 1. Collapse only literal duplicate detector emissions.
    #    The original 382-row raw table remains untouched.
    # ------------------------------------------------------------
    exact_groups = defaultdict(list)

    for r in rows:
        key = (
            r["assembly_id"],
            r["raw_system_id"],
            r["generated_ids"],
        )
        exact_groups[key].append(r)

    unique_calls = []

    invariant_fields = [
        "detector_type",
        "detector_subtype",
        "broad_type",
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
    ]

    for key, group in exact_groups.items():
        first = group[0]

        for field in invariant_fields:
            vals = {r[field] for r in group}
            if len(vals) != 1:
                raise RuntimeError(
                    f"Non-identical duplicate group {key}: "
                    f"field {field} has {vals}"
                )

        r = dict(first)
        r["native_duplicate_count"] = str(len(group))
        unique_calls.append(r)

    if len(unique_calls) != 342:
        raise RuntimeError(
            f"Expected 342 exact-deduplicated DF calls, got {len(unique_calls)}"
        )

    # ------------------------------------------------------------
    # 2. Verify that no protein is shared across different broad
    #    R-M classes. If that occurs, automatic graph merging is
    #    scientifically unsafe.
    # ------------------------------------------------------------
    protein_owners = defaultdict(list)

    for i, r in enumerate(unique_calls):
        for gid in split_field(r["generated_ids"]):
            protein_owners[(r["assembly_id"], gid)].append(i)

    for key, owners in protein_owners.items():
        broad = {unique_calls[i]["broad_type"] for i in owners}
        if len(broad) > 1:
            raise RuntimeError(
                f"Cross-broad-type shared protein {key}: {sorted(broad)}"
            )

    # ------------------------------------------------------------
    # 3. Union-find: systems from the same assembly and broad type
    #    that share >=1 generated protein ID belong to one connected
    #    physical detector locus.
    # ------------------------------------------------------------
    parent = list(range(len(unique_calls)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    owners_by_protein = defaultdict(list)

    for i, r in enumerate(unique_calls):
        for gid in split_field(r["generated_ids"]):
            owners_by_protein[
                (r["assembly_id"], r["broad_type"], gid)
            ].append(i)

    for owners in owners_by_protein.values():
        for i in owners[1:]:
            union(owners[0], i)

    components = defaultdict(list)
    for i in range(len(unique_calls)):
        components[find(i)].append(i)

    # ------------------------------------------------------------
    # 4. Build one physical-locus row per connected component,
    #    plus a membership/provenance table preserving every
    #    contributing DefenseFinder model call.
    # ------------------------------------------------------------
    loci = []
    members = []

    sorted_components = sorted(
        components.values(),
        key=lambda inds: (
            unique_calls[inds[0]]["assembly_id"],
            unique_calls[inds[0]]["broad_type"],
            min(int(unique_calls[i]["locus_start"]) for i in inds),
        ),
    )

    per_assembly_counter = Counter()

    for inds in sorted_components:
        source = [unique_calls[i] for i in inds]

        assemblies = {r["assembly_id"] for r in source}
        broad_types = {r["broad_type"] for r in source}
        replicons = {r["replicon"] for r in source}

        if len(assemblies) != 1:
            raise RuntimeError("Component spans multiple assemblies")
        if len(broad_types) != 1:
            raise RuntimeError("Component spans multiple broad R-M types")
        if len(replicons) != 1:
            raise RuntimeError("Component spans multiple replicons")

        acc = next(iter(assemblies))
        broad = next(iter(broad_types))
        replicon = next(iter(replicons))

        per_assembly_counter[acc] += 1
        locus_id = f"DFLOC:{acc}:{per_assembly_counter[acc]:03d}"

        # Reconstruct positional protein evidence.
        proteins = {}

        for r in source:
            gids = split_field(r["generated_ids"])
            pids = split_field(r["protein_ids"])
            tags = split_field(r["locus_tags"])
            names = split_field(r["gene_names"])
            strands = split_field(r["strands"])

            lengths = {len(gids), len(pids), len(tags), len(names), len(strands)}
            if len(lengths) != 1:
                raise RuntimeError(
                    f"{r['raw_system_id']}: misaligned per-gene fields"
                )

            for gid, pid, tag, name, strand in zip(
                gids, pids, tags, names, strands
            ):
                if gid not in proteins:
                    proteins[gid] = {
                        "protein_id": pid,
                        "locus_tag": tag,
                        "strand": strand,
                        "gene_names": set(),
                    }
                else:
                    old = proteins[gid]
                    if (
                        old["protein_id"] != pid
                        or old["locus_tag"] != tag
                        or old["strand"] != strand
                    ):
                        raise RuntimeError(
                            f"{locus_id}: inconsistent mapping for {gid}"
                        )

                proteins[gid]["gene_names"].add(name)

        ordered_gids = sorted(
            proteins,
            key=lambda gid: (
                int(gid.rsplit("_", 1)[1])
                if gid.rsplit("_", 1)[1].isdigit()
                else 10**12,
                gid,
            ),
        )

        loci.append({
            "df_locus_id": locus_id,
            "assembly_id": acc,
            "broad_type": broad,
            "replicon": replicon,
            "locus_start": min(int(r["locus_start"]) for r in source),
            "locus_end": max(int(r["locus_end"]) for r in source),
            "unique_model_calls": len(source),
            "native_raw_rows": sum(
                int(r["native_duplicate_count"]) for r in source
            ),
            "cross_model_merge": "1" if len(source) > 1 else "0",
            "source_system_ids": ";".join(
                uniq(r["raw_system_id"] for r in source)
            ),
            "source_types": ";".join(
                uniq(r["detector_type"] for r in source)
            ),
            "source_subtypes": ";".join(
                uniq(r["detector_subtype"] for r in source)
            ),
            "generated_ids": ";".join(ordered_gids),
            "protein_ids": ";".join(
                proteins[g]["protein_id"] for g in ordered_gids
            ),
            "locus_tags": ";".join(
                proteins[g]["locus_tag"] for g in ordered_gids
            ),
            "strands": ";".join(
                proteins[g]["strand"] for g in ordered_gids
            ),
            "gene_evidence": ";".join(
                f"{g}:{'|'.join(sorted(proteins[g]['gene_names']))}"
                for g in ordered_gids
            ),
        })

        for r in sorted(
            source,
            key=lambda x: (
                int(x["locus_start"]),
                x["raw_system_id"],
            ),
        ):
            members.append({
                "df_locus_id": locus_id,
                "assembly_id": acc,
                "broad_type": broad,
                "raw_system_id": r["raw_system_id"],
                "detector_type": r["detector_type"],
                "detector_subtype": r["detector_subtype"],
                "native_duplicate_count": r["native_duplicate_count"],
                "replicon": r["replicon"],
                "locus_start": r["locus_start"],
                "locus_end": r["locus_end"],
                "generated_ids": r["generated_ids"],
                "protein_ids": r["protein_ids"],
                "gene_names": r["gene_names"],
                "sys_wholeness": r["sys_wholeness"],
                "sys_score": r["sys_score"],
            })

    outdir = root / "results" / "stage05_normalized"
    outdir.mkdir(parents=True, exist_ok=True)

    locus_fields = [
        "df_locus_id",
        "assembly_id",
        "broad_type",
        "replicon",
        "locus_start",
        "locus_end",
        "unique_model_calls",
        "native_raw_rows",
        "cross_model_merge",
        "source_system_ids",
        "source_types",
        "source_subtypes",
        "generated_ids",
        "protein_ids",
        "locus_tags",
        "strands",
        "gene_evidence",
    ]

    member_fields = [
        "df_locus_id",
        "assembly_id",
        "broad_type",
        "raw_system_id",
        "detector_type",
        "detector_subtype",
        "native_duplicate_count",
        "replicon",
        "locus_start",
        "locus_end",
        "generated_ids",
        "protein_ids",
        "gene_names",
        "sys_wholeness",
        "sys_score",
    ]

    write_tsv(
        outdir / "defensefinder_loci.tsv",
        loci,
        locus_fields,
    )

    write_tsv(
        outdir / "defensefinder_locus_members.tsv",
        members,
        member_fields,
    )

    summary = {
        "raw_defensefinder_rows": len(rows),
        "exact_deduplicated_model_calls": len(unique_calls),
        "physical_defensefinder_loci": len(loci),
        "collapsed_literal_duplicate_rows":
            len(rows) - len(unique_calls),
        "cross_model_connected_loci":
            sum(1 for r in loci if r["cross_model_merge"] == "1"),
        "loci_by_broad_type":
            dict(sorted(Counter(r["broad_type"] for r in loci).items())),
    }

    with (
        outdir / "defensefinder_loci_summary.json"
    ).open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
