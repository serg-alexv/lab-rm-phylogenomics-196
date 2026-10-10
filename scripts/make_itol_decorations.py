#!/usr/bin/env python3
"""Export two iTOL datasets from a strictly validated cell_mapping.tsv.

Uses the user-approved DATASET_BINARY correction: 1 fills a colored square;
0 draws an empty square (white on a white canvas). Missing is never absence.
Templates: https://itol.embl.de/help/dataset_binary_template.txt
https://itol.embl.de/help/dataset_color_strip_template.txt
"""

import argparse
import colorsys
import csv
import hashlib
from pathlib import Path
import sys


SYSTEM_COLORS = {
    "RM": "#008080",
    "Cas": "#2e8b57",
    "Abi2": "#ffa500",
    "CBASS": "#8b0000",
    "BREX": "#ff1493",
    "Septu": "#0000ff",
}


def read_matrix(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t", strict=True)
        header = next(reader, None)
        if not header:
            raise ValueError("Input is empty; a TSV header is required.")
        if len(header) != len(set(header)):
            raise ValueError("Duplicate header names are not allowed.")
        required = {"GenomeID", "Host", *SYSTEM_COLORS}
        missing = required.difference(header)
        if missing:
            raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
        systems = list(SYSTEM_COLORS)
        records = []
        seen = set()
        for values in reader:
            if not values:
                continue
            line = reader.line_num
            if len(values) != len(header):
                raise ValueError(f"Line {line}: wrong number of TSV fields.")
            row = dict(zip(header, values))
            for name in required:
                value = row[name]
                if any(ord(char) < 32 or ord(char) == 127 for char in value):
                    raise ValueError(f"Line {line}: control character in {name}.")
                row[name] = value.strip()
                if not row[name]:
                    raise ValueError(f"Line {line}: {name} is missing.")
            genome = row["GenomeID"]
            if genome.startswith("#") or any(char.isspace() for char in genome):
                raise ValueError(f"Line {line}: invalid GenomeID {genome!r}.")
            if genome in seen:
                raise ValueError(f"Line {line}: duplicate GenomeID {genome!r}.")
            seen.add(genome)
            for system in systems:
                if row[system] not in {"0", "1"}:
                    raise ValueError(
                        f"Line {line}: {system} must be exactly 0 or 1; "
                        f"received {row[system]!r}."
                    )
            records.append(row)
    if not records:
        raise ValueError("Input contains no genome records.")
    return systems, records


def host_palette(hosts):
    result = {}
    used = {"#ffffff"}
    for host in sorted(set(hosts)):
        for attempt in range(65536):
            digest = hashlib.sha256(
                f"{host}\0{attempt}".encode("utf-8")
            ).digest()
            hue = int.from_bytes(digest[:4], "big") / 2**32
            saturation = 0.60 + digest[4] / 255 * 0.20
            lightness = 0.40 + digest[5] / 255 * 0.15
            rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
            color = "#" + "".join(f"{round(value * 255):02x}" for value in rgb)
            if color not in used:
                result[host] = color
                used.add(color)
                break
        else:
            raise ValueError("Unable to assign unique host colors.")
    return result


def render_rows(rows):
    return "\n".join("\t".join(str(value) for value in row) for row in rows) + "\n"


def build_datasets(systems, records):
    colors = [SYSTEM_COLORS[system] for system in systems]
    defense = [
        ["DATASET_BINARY"],
        ["SEPARATOR", "TAB"],
        ["DATASET_LABEL", "Defense Systems"],
        ["COLOR", "#000000"],
        [],
        ["# Enforce tabs uniformly across all array parameters to prevent upload crashes"],
        ["FIELD_SHAPES", *([1] * len(systems))],
        ["FIELD_COLORS", *colors],
        ["FIELD_LABELS", *systems],
        [],
        ["LEGEND_TITLE", "Defense Systems"],
        ["LEGEND_SHAPES", *([1] * len(systems))],
        ["LEGEND_COLORS", *colors],
        ["LEGEND_LABELS", *systems],
        [],
        ["DATA"],
        ["# Each column must be strictly tab-delimited (\\t)"],
    ]
    defense.extend([row["GenomeID"], *(row[s] for s in systems)] for row in records)

    palette = host_palette(row["Host"] for row in records)
    hosts = list(palette)
    host_strip = [
        ["DATASET_COLORSTRIP"],
        ["SEPARATOR", "TAB"],
        ["DATASET_LABEL", "Host"],
        ["COLOR", "#666666"],
        ["COLOR_BRANCHES", 0],
        ["LEGEND_TITLE", "Host traits"],
        ["LEGEND_SHAPES", *([1] * len(hosts))],
        ["LEGEND_COLORS", *(palette[host] for host in hosts)],
        ["LEGEND_LABELS", *hosts],
        ["DATA"],
    ]
    host_strip.extend(
        [row["GenomeID"], palette[row["Host"]], row["Host"]] for row in records
    )
    return {
        "defense_systems_heatmap.txt": render_rows(defense),
        "host_colorstrip.txt": render_rows(host_strip),
    }


def main():
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=root / "cell_mapping.tsv")
    parser.add_argument("--output-dir", type=Path, default=root / "pipeline_output")
    args = parser.parse_args()
    systems, records = read_matrix(args.input)
    datasets = build_datasets(systems, records)
    targets = [args.output_dir / name for name in datasets]
    for target in targets:
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"Refusing to overwrite {target}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in datasets.items():
        with (args.output_dir / name).open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, csv.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
