#!/usr/bin/env python3
import os
import csv
import sys

# CONFIG
INPUT_FILE = "cell_mapping.tsv"  
OUT_DIR = "pipeline_output"
os.makedirs(OUT_DIR, exist_ok=True)

# 1. DEFENSE SYSTEMS (DATASET_BINARY)
def write_defenses(rows):
    outfile = os.path.join(OUT_DIR, "defense_systems.txt")
    with open(outfile, 'w') as f:
        f.write("DATASET_BINARY\nSEPARATOR\tTAB\nDATASET_LABEL\tDefense Systems\nCOLOR\t#000000\n")
        f.write("FIELD_SHAPES\t1\t1\t1\t1\t1\t1\n")
        f.write("FIELD_COLORS\t#008080\t#2e8b57\t#ffa500\t#8b0000\t#ff1493\t#0000ff\n")
        f.write("FIELD_LABELS\tRM\tCas\tAbi2\tCBASS\tBREX\tSeptu\n")
        f.write("LEGEND_TITLE\tDefense Systems\n")
        f.write("LEGEND_SHAPES\t1\t1\t1\t1\t1\t1\n")
        f.write("LEGEND_COLORS\t#008080\t#2e8b57\t#ffa500\t#8b0000\t#ff1493\t#0000ff\n")
        f.write("LEGEND_LABELS\tRM\tCas\tAbi2\tCBASS\tBREX\tSeptu\n")
        f.write("DATA\n")
        
        for r in rows:
            if len(r) < 8:
                print(f"WARNING: Skipping row with insufficient columns: {r}")
                continue
            # genome_id is r[0], systems are r[2] through r[7]
            line = [r[0]] + r[2:8] 
            f.write("\t".join(line) + "\n")
    print(f"Created {outfile}")

# 2. HOST STRIP (DATASET_COLORSTRIP)
def write_hosts(rows):
    outfile = os.path.join(OUT_DIR, "host_strip.txt")
    
    hosts = sorted(list(set(r[1] for r in rows if len(r) > 1 and r[1])))
    palette = ["#E41A1C", "#377EB8", "#4DAF4A", "#984EA3", "#FF7F00", "#FFFF33", "#A65628", "#F781BF"]
    host_colors = {h: palette[i % len(palette)] for i, h in enumerate(hosts)}

    with open(outfile, 'w') as f:
        f.write("DATASET_COLORSTRIP\nSEPARATOR\tTAB\nDATASET_LABEL\tHost\nCOLOR\t#000000\n")
        f.write("STRIP_WIDTH\t25\nMARGIN\t0\n")
        f.write("LEGEND_TITLE\tHost Source\n")
        f.write("LEGEND_SHAPES\t" + "\t".join(["1"] * len(hosts)) + "\n")
        f.write("LEGEND_COLORS\t" + "\t".join([host_colors[h] for h in hosts]) + "\n")
        f.write("LEGEND_LABELS\t" + "\t".join(hosts) + "\n")
        f.write("DATA\n")
        
        for r in rows:
            if len(r) > 1 and r[1] in host_colors:
                f.write(f"{r[0]}\t{host_colors[r[1]]}\n")
    print(f"Created {outfile}")

# EXECUTION
if not os.path.exists(INPUT_FILE):
    print(f"ERROR: Could not find {INPUT_FILE}. Please ensure it is in the current directory.")
    sys.exit(1)

try:
    with open(INPUT_FILE, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader) # Skip header
        data = [r for r in reader if r]
        
    write_defenses(data)
    write_hosts(data)
    print("SUCCESS: Annotation files generated.")
except Exception as e:
    print(f"ERROR: {e}")