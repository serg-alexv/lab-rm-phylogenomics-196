from pathlib import Path
from collections import defaultdict
import argparse
import csv
import re

def read_fasta(path):
    seqs = {}
    current = None
    parts = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip()
            if line.startswith(">"):
                if current is not None:
                    seqs[current] = "".join(parts)
                current = line[1:].split()[0]
                parts = []
            else:
                parts.append(line.strip())
        if current is not None:
            seqs[current] = "".join(parts)
    return seqs

def attrs_dict(text):
    out = {}
    for field in text.split(";"):
        if "=" in field:
            k, v = field.split("=", 1)
            out[k] = v
    return out

ap = argparse.ArgumentParser()
ap.add_argument("--assembly", required=True)
ap.add_argument("--faa", required=True)
ap.add_argument("--gff", required=True)
ap.add_argument("--outdir", required=True)
args = ap.parse_args()

assembly = args.assembly
outdir = Path(args.outdir)
outdir.mkdir(parents=True, exist_ok=True)

seqs = read_fasta(args.faa)

groups = defaultdict(list)
seq_order = []
seen_seq = set()

with open(args.gff, encoding="utf-8") as f:
    for line in f:
        if line.startswith("##sequence-region "):
            seqid = line.split()[1]
            if seqid not in seen_seq:
                seq_order.append(seqid)
                seen_seq.add(seqid)
            continue
        if line.startswith("#"):
            continue
        c = line.rstrip("\n").split("\t")
        if len(c) < 9 or c[2] != "CDS":
            continue
        a = attrs_dict(c[8])
        protein_id = a.get("protein_id")
        if not protein_id:
            continue
        seqid = c[0]
        if seqid not in seen_seq:
            seq_order.append(seqid)
            seen_seq.add(seqid)
        locus_tag = a.get("locus_tag") or a.get("ID")
        if not locus_tag:
            locus_tag = f"{seqid}:{c[3]}-{c[4]}:{c[6]}:{protein_id}"
        key = (seqid, locus_tag, protein_id)
        groups[key].append({
            "start": int(c[3]),
            "end": int(c[4]),
            "strand": c[6],
            "cds_id": a.get("ID", ""),
        })

missing = sorted({k[2] for k in groups if k[2] not in seqs})
if missing:
    raise SystemExit(f"ERROR: {len(missing)} GFF protein IDs absent from FAA; first={missing[0]}")

seq_rank = {s:i for i,s in enumerate(seq_order)}
records = []

for (seqid, locus_tag, protein_id), parts in groups.items():
    strands = sorted({p["strand"] for p in parts})
    if len(strands) != 1:
        raise SystemExit(
            f"ERROR: locus has mixed strands: {seqid} {locus_tag} "
            f"{protein_id} {strands}"
        )
    records.append({
        "seqid": seqid,
        "locus_tag": locus_tag,
        "protein_id": protein_id,
        "start": min(p["start"] for p in parts),
        "end": max(p["end"] for p in parts),
        "strand": strands[0],
        "segments": len(parts),
        "cds_ids": ",".join(p["cds_id"] for p in parts if p["cds_id"]),
    })

records.sort(
    key=lambda r: (
        seq_rank.get(r["seqid"], 10**9),
        r["start"],
        r["end"],
        r["locus_tag"],
        r["protein_id"],
    )
)

positions = defaultdict(int)

faa_out = outdir / "defensefinder_gembase.faa"
map_out = outdir / "defensefinder_protein_map.tsv"

with open(faa_out, "w", encoding="utf-8", newline="\n") as fo, \
     open(map_out, "w", encoding="utf-8", newline="") as mo:

    fields = [
        "generated_id","assembly_id","seqid","position",
        "protein_id","locus_tag","start","end","strand",
        "segments","cds_ids"
    ]
    writer = csv.DictWriter(mo, fieldnames=fields, delimiter="\t")
    writer.writeheader()

    generated = set()

    for r in records:
        positions[r["seqid"]] += 1
        pos = positions[r["seqid"]]
        gid = f"{r['seqid']}_{pos:06d}"

        if gid in generated:
            raise SystemExit(f"ERROR: duplicate generated ID: {gid}")
        generated.add(gid)

        seq = seqs[r["protein_id"]]
        fo.write(f">{gid}\n")
        for i in range(0, len(seq), 80):
            fo.write(seq[i:i+80] + "\n")

        writer.writerow({
            "generated_id": gid,
            "assembly_id": assembly,
            "seqid": r["seqid"],
            "position": pos,
            "protein_id": r["protein_id"],
            "locus_tag": r["locus_tag"],
            "start": r["start"],
            "end": r["end"],
            "strand": r["strand"],
            "segments": r["segments"],
            "cds_ids": r["cds_ids"],
        })

print(f"ASSEMBLY={assembly}")
print(f"FAA_UNIQUE_SEQUENCES={len(seqs)}")
print(f"OUTPUT_LOCI={len(records)}")
print(f"SEQUENCE_RECORDS={len(positions)}")
print(f"MULTISEGMENT_LOCI={sum(r['segments'] > 1 for r in records)}")
print(f"REUSED_PROTEIN_IDS={sum(1 for p in set(r['protein_id'] for r in records) if sum(x['protein_id']==p for x in records) > 1)}")
print(f"FASTA={faa_out}")
print(f"MAP={map_out}")
