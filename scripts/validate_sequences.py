"""Independent reader for raw NCBI Datasets ZIPs; does not modify inputs."""
from pathlib import Path, PurePosixPath
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib, io, json, re, sys, zipfile, warnings
from urllib.parse import unquote
import Bio
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqFeature import ExactPosition

ROLES = {
    "GENOMIC_NUCLEOTIDE_FASTA": "genome",
    "PROTEIN_FASTA": "protein",
    "CDS_NUCLEOTIDE_FASTA": "cds",
    "GFF3": "gff",
    "GENBANK_FLAT_FILE": "gbff",
    "SEQUENCE_REPORT": "sequence_report",
}
DNA = set("ACGTRYSWKMBDHVN")
AA = set("ACDEFGHIKLMNPQRSTVWYBXZUOJ*")

def require(ok, message):
    if not ok:
        raise ValueError(message)

def hashfile(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()

def safe_member(name):
    p = PurePosixPath(name)
    require(name and not p.is_absolute() and ".." not in p.parts
            and "\\" not in name and ":" not in name,
            "Unsafe ZIP/catalog member: " + name)
    require(all(x not in ("", ".") for x in name.rstrip("/").split("/")),
            "Noncanonical ZIP member: " + name)

def fasta(text, protein=False):
    records, title, chunks = [], None, []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            if title is not None:
                require(chunks, "Empty FASTA record: " + title)
                records.append((title.split()[0], title, "".join(chunks).upper()))
            title, chunks = line[1:], []
            require(title and not title.startswith(" "), "Empty FASTA header")
        else:
            require(title is not None, "Sequence before FASTA header, line " + str(n))
            require(not any(c.isspace() for c in line), "Whitespace inside FASTA sequence")
            require(set(line.upper()) <= (AA if protein else DNA),
                    "Invalid FASTA alphabet, line " + str(n))
            chunks.append(line)
    if title is not None:
        require(chunks, "Empty FASTA record: " + title)
        records.append((title.split()[0], title, "".join(chunks).upper()))
    require(records, "No FASTA records")
    return records

def jsonlines(text):
    rows = [json.loads(x) for x in text.splitlines() if x.strip()]
    require(rows, "Empty JSONL report")
    require(all(isinstance(x, dict) for x in rows), "JSONL record is not an object")
    return rows

def attrs(text):
    d = {}
    if text == ".":
        return d
    for item in text.split(";"):
        if not item:
            continue
        require("=" in item, "Malformed GFF attribute: " + item)
        k, v = item.split("=", 1)
        require(k and k not in d, "Duplicate/empty GFF attribute: " + k)
        d[k] = unquote(v)
    return d

def cds_header_attrs(title):
    pairs = re.findall(r"\[([^=\]]+)=([^\]]*)\]", title)
    require(len(pairs) == len({k for k, v in pairs}),
            "Duplicate/conflicting CDS FASTA header attribute")
    return dict(pairs)

def parse_gff(text, genome_lengths):
    rows, regions, build = [], {}, None
    for lineno, raw in enumerate(text.splitlines(), 1):
        if raw.startswith("##FASTA"):
            break
        if raw.startswith("##sequence-region "):
            _, rep, start, end = raw.split()
            require(rep not in regions, "Duplicate GFF sequence-region: " + rep)
            regions[rep] = (int(start), int(end))
        if raw.startswith("#!genome-build-accession "):
            build = raw.split("NCBI_Assembly:", 1)[-1].strip()
        if not raw or raw.startswith("#"):
            continue
        x = raw.split("\t")
        require(len(x) == 9, "GFF must have nine columns, line " + str(lineno))
        rep, source, kind, first, last, score, strand, phase, attributes = x
        require(rep in genome_lengths, "Unknown GFF replicon: " + rep)
        start, end = int(first), int(last)
        require(1 <= start <= end, "Invalid GFF coordinates, line " + str(lineno))
        require(strand in ("+", "-", ".", "?"), "Invalid GFF strand")
        require(phase in (".", "0", "1", "2"), "Invalid GFF phase")
        rows.append({"replicon": rep, "kind": kind, "start": start, "end": end,
                     "strand": strand, "phase": phase, "attrs": attrs(attributes),
                     "line": lineno})
    require(rows, "Empty GFF")
    require(set(regions) == set(genome_lengths), "GFF sequence-region membership differs")
    for rep, length in genome_lengths.items():
        require(regions[rep] == (1, length), "GFF sequence-region length differs: " + rep)
    return rows, build

def intervals(start, end, length, circular):
    require(1 <= start <= end and end - start + 1 <= length,
            "GFF interval longer than replicon or invalid")
    if end <= length:
        return [(start - 1, end)]
    require(circular and end <= 2 * length, "Unjustified origin-spanning GFF coordinates")
    a, b = (start - 1) % length, (end - 1) % length + 1
    return [(a, b)] if a < b else [(a, length), (0, b)]

def protein_lookup(records):
    byid = defaultdict(list)
    for pid, title, sequence in records:
        byid[pid].append((title, sequence))
    for pid, rs in byid.items():
        require(len({s for _, s in rs}) == 1,
                "One protein accession has conflicting supplied sequences: " + pid)
    return byid

def validate_package(zip_path, expected_acc, expected_tax=None, expected_lineage=None):
    errors, reviews, files, loci, replicons = [], [], [], [], []
    stats = {}
    def review(code, detail, key=None):
        reviews.append({"code": code, "detail": detail, "locus_key": key})
    def fail(code, detail, key=None):
        errors.append({"code": code, "detail": detail, "locus_key": key})
    def assertion(condition, code, detail, key=None):
        if not condition:
            fail(code, detail, key)
        return condition
    zpath = Path(zip_path)
    sourcefile = Path(__file__) if "__file__" in globals() else None
    result = {
        "assembly_accession": expected_acc,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "raw_zip_path": zpath.as_posix(),
        "raw_zip_bytes": zpath.stat().st_size,
        "raw_zip_sha256": hashfile(zpath),
        "validator_source_path": sourcefile.as_posix() if sourcefile else None,
        "validator_source_sha256": hashfile(sourcefile) if sourcefile and sourcefile.is_file() else None,
        "python_version": sys.version.split()[0], "biopython_version": Bio.__version__,
        "errors": errors, "review_exceptions": reviews, "files": files,
        "loci": loci, "replicons": replicons, "metrics": stats,
        "evidence_limit": "File/annotation integrity and source consistency; no ANI, independent taxonomic certification or enzymatic activity."
    }
    try:
        require(re.fullmatch(r"GCF_\d{9}\.\d+", expected_acc), "Expected accession is not exact versioned GCF")
        with zipfile.ZipFile(zpath) as z:
            names = [i.filename for i in z.infolist() if not i.is_dir()]
            for i in z.infolist():
                safe_member(i.filename)
                require(not i.flag_bits & 1, "Encrypted ZIP member")
                require((i.external_attr >> 16) & 0o170000 != 0o120000, "Symlink ZIP member")
            require(len(names) == len(set(n.casefold() for n in names)),
                    "Duplicate/case-colliding ZIP member names")
            require(z.testzip() is None, "ZIP CRC failure")
            blob = {n: z.read(n) for n in names}
            for n, b in blob.items():
                files.append({"member": n, "bytes": len(b),
                              "sha256": hashlib.sha256(b).hexdigest()})
            catalogs = [n for n in names if PurePosixPath(n).name == "dataset_catalog.json"]
            require(len(catalogs) == 1, "Missing/ambiguous dataset catalog")
            catname = catalogs[0]
            catalog = json.loads(blob[catname])
            catdir = str(PurePosixPath(catname).parent)
            def resolve(name):
                safe_member(name)
                candidates = {name, catdir + "/" + name, catdir + "/data/" + name,
                              "ncbi_dataset/data/" + name}
                found = candidates & set(names)
                require(len(found) == 1, "Unresolved/ambiguous catalog path: " + name)
                return found.pop()
            assemblies = [a for a in catalog.get("assemblies", []) if a.get("accession")]
            require(sum(a["accession"] == expected_acc for a in assemblies) == 1,
                    "Catalog does not uniquely contain exact requested assembly")
            require(all(a["accession"].split(".")[0] == expected_acc.split(".")[0] for a in assemblies),
                    "Catalog includes a different assembly accession base")
            role_members, report_members = defaultdict(list), []
            for assembly in catalog.get("assemblies", []):
                archival = bool(assembly.get("accession") and assembly["accession"] != expected_acc)
                for entry in assembly.get("files", []):
                    if archival:
                        require(entry.get("fileType") in ("SEQUENCE_REPORT", "DATA_REPORT"),
                                "Catalog contains unapproved biological file version")
                        safe_member(entry["filePath"])
                        review("ARCHIVAL_METADATA_CATALOG_REFERENCE",
                               {"accession": assembly["accession"], "path": entry["filePath"],
                                "file_type": entry["fileType"],
                                "basis": "Same assembly base; metadata-only historical catalog reference returned by NCBI Datasets. Never used as approved biological input."})
                        continue
                    member = resolve(entry["filePath"])
                    if "uncompressedLengthBytes" in entry:
                        require(int(entry["uncompressedLengthBytes"]) == len(blob[member]),
                                "Catalog member byte length differs: " + member)
                    kind = entry.get("fileType")
                    if kind in ROLES:
                        require(assembly.get("accession") == expected_acc,
                                "Biological file in nonmatching catalog assembly")
                        role_members[ROLES[kind]].append(member)
                    elif kind == "DATA_REPORT":
                        report_members.append(member)
            for role in ROLES.values():
                require(len(role_members[role]) == 1, "Required file role missing/ambiguous: " + role)
                require(blob[role_members[role][0]], "Required file is empty: " + role)
            require(len(set(x[0] for x in role_members.values())) == 6,
                    "One member assigned conflicting biological roles")
            role = {k: v[0] for k, v in role_members.items()}
            actual_biological = {n for n in names if n.lower().endswith((".fna", ".faa", ".gff", ".gff3", ".gbff"))}
            require(actual_biological == {role[k] for k in ("genome", "protein", "cds", "gff", "gbff")},
                    "Unexpected/unapproved biological payload member")
            require(PurePosixPath(role["cds"]).name == "cds_from_genomic.fna",
                    "CDS role does not identify cds_from_genomic.fna")
            require(PurePosixPath(role["genome"]).name != "cds_from_genomic.fna",
                    "CDS incorrectly classified as genomic FASTA")
            md5files = [n for n in names if PurePosixPath(n).name == "md5sum.txt"]
            if md5files:
                require(len(md5files) == 1, "Ambiguous provider MD5 manifest")
                seen_md5 = set()
                for line in blob[md5files[0]].decode().splitlines():
                    if not line.strip():
                        continue
                    m = re.fullmatch(r"([a-fA-F0-9]{32})\s+[*]?(.+)", line)
                    require(m is not None, "Malformed provider MD5 line")
                    h, name = m.groups()
                    require(name in blob and name not in seen_md5, "Missing/duplicate MD5 member: " + name)
                    seen_md5.add(name)
                    require(hashlib.md5(blob[name]).hexdigest() == h.lower(),
                            "Provider MD5 mismatch: " + name)
                require(set(role.values()) <= seen_md5, "Provider MD5 omits required biological member")
                stats["provider_md5_members_verified"] = len(seen_md5)
            else:
                review("PROVIDER_MD5_NOT_SUPPLIED", "All local member SHA256 and ZIP CRC retained.")
            require(len(report_members) == 1, "Missing/ambiguous catalog assembly report")
            report = jsonlines(blob[report_members[0]].decode())
            require(len(report) == len({r.get("accession") for r in report}),
                    "Duplicate assembly report accession")
            selected_report = [r for r in report if r.get("accession") == expected_acc]
            require(len(selected_report) == 1, "Assembly report lacks unique exact requested accession")
            for historical in report:
                if historical.get("accession") != expected_acc:
                    require(str(historical.get("accession", "")).split(".")[0] == expected_acc.split(".")[0],
                            "Assembly report includes a different assembly accession base")
                    review("ARCHIVAL_ASSEMBLY_METADATA_REPORT",
                           {"accession": historical["accession"], "status": historical.get("assemblyInfo", {}).get("assemblyStatus"),
                            "basis": "Metadata-only extra; biological validation uses exact requested accession."})
            report = selected_report[0]
            returned_tax = str(report.get("organism", {}).get("taxId", ""))
            stats["reported_organism_tax_id"] = returned_tax
            require(returned_tax.isdigit(), "Assembly report lacks numeric organism TaxID")
            stats["taxonomy_evidence_class"] = "FROZEN_METADATA_COMPARISON_ONLY"
            stats["frozen_organism_tax_id"] = str(expected_tax) if expected_tax else None
            lineage = json.loads(expected_lineage) if isinstance(expected_lineage, str) else (expected_lineage or [])
            species_indices = [i for i, n in enumerate(lineage) if str(n.get("rank", "")).upper() == "SPECIES"]
            compatible = {str(n.get("tax_id")) for n in lineage[species_indices[0]:]
                          if str(n.get("tax_id", "")).isdigit()} if species_indices else set()
            if expected_tax and returned_tax != str(expected_tax):
                if returned_tax in compatible:
                    review("TAXID_COMPATIBLE_PRESERVED_LINEAGE",
                           {"downloaded_taxid": returned_tax, "frozen_taxid": str(expected_tax),
                            "basis": "Received taxid is species or descendant represented in preserved verified G0 lineage. No new identity certification."})
                else:
                    fail("TAXID_REQUIRES_LINEAGE_REVIEW",
                         "Downloaded TaxID " + returned_tax + "; frozen organism TaxID " + str(expected_tax)
                         + ". Numeric difference is not proof of incompatibility; provide preserved descendant/merged-taxid evidence.")
            elif not expected_tax:
                review("FROZEN_TAXID_NOT_SUPPLIED", "No frozen organism TaxID comparison requested.")
            sequence_report = jsonlines(blob[role["sequence_report"]].decode())
            require(all(r.get("assemblyAccession") == expected_acc for r in sequence_report),
                    "Sequence report assembly differs")
            genomic_records = fasta(blob[role["genome"]].decode())
            require(len(genomic_records) == len({r[0] for r in genomic_records}),
                    "Duplicate genomic FASTA ID")
            genome = {pid: sequence for pid, title, sequence in genomic_records}
            lengths = {pid: len(sequence) for pid, sequence in genome.items()}
            require(len(sequence_report) == len(genome), "Genome/sequence report record count differs")
            report_by_id = {}
            for sr in sequence_report:
                matches = {sr.get("refseqAccession"), sr.get("genbankAccession")} & set(genome)
                require(len(matches) == 1, "Sequence report cannot uniquely join genomic record")
                pid = matches.pop()
                require(pid not in report_by_id, "Repeated sequence-report FASTA join: " + pid)
                report_by_id[pid] = sr
                require(int(sr["length"]) == lengths[pid], "Sequence-report length differs: " + pid)
            require(set(report_by_id) == set(genome), "Sequence-report/genome membership differs")
            gb_records = list(SeqIO.parse(io.StringIO(blob[role["gbff"]].decode()), "genbank"))
            require(gb_records and len(gb_records) == len({r.id for r in gb_records}),
                    "Empty/duplicate GBFF records")
            gb = {r.id: r for r in gb_records}
            require(set(gb) == set(genome), "GBFF/genome replicon membership differs")
            for pid, rec in gb.items():
                require(str(rec.seq).upper() == genome[pid], "GBFF/genome sequence differs: " + pid)
                require("Assembly:" + expected_acc in rec.dbxrefs,
                        "GBFF record lacks expected Assembly DBLINK: " + pid)
                source_features = [f for f in rec.features if f.type == "source"]
                require(len(source_features) == 1, "Missing/ambiguous GBFF source feature: " + pid)
                source_taxids = [v.split(":", 1)[1] for v in source_features[0].qualifiers.get("db_xref", [])
                                 if v.startswith("taxon:")]
                require(len(source_taxids) == 1 and source_taxids[0].isdigit(),
                        "Missing/ambiguous numeric GBFF source TaxID: " + pid)
                source_taxid = source_taxids[0]
                assertion(source_taxid == returned_tax or source_taxid in compatible,
                          "GBFF_SOURCE_TAXID_REQUIRES_REVIEW",
                          {"replicon": pid, "gbff_source_taxid": source_taxid,
                           "reported_taxid": returned_tax, "frozen_taxid": str(expected_tax) if expected_tax else None,
                           "basis": "Exact report TaxID or species/descendant represented in preserved frozen lineage required."})
                if source_taxid != returned_tax and source_taxid in compatible:
                    review("GBFF_SOURCE_TAXID_COMPATIBLE_PRESERVED_LINEAGE",
                           {"replicon": pid, "gbff_source_taxid": source_taxid, "reported_taxid": returned_tax})
                counts = Counter(genome[pid])
                acgt = sum(counts[b] for b in "ACGT")
                rep = {"assembly_accession": expected_acc, "replicon": pid,
                       "length": lengths[pid], "sequence_sha256": hashlib.sha256(genome[pid].encode()).hexdigest(),
                       "gbff_topology": rec.annotations.get("topology", "unknown"),
                       "reported_role": report_by_id[pid].get("role"),
                       "reported_molecule_type": report_by_id[pid].get("assignedMoleculeLocationType", "Unknown"),
                       "reported_name": report_by_id[pid].get("chrName"),
                       "gbff_source_tax_id": source_taxid,
                       "gc_percent_acgt": 100 * (counts["G"] + counts["C"]) / acgt if acgt else None,
                       "n_count": counts["N"], "ambiguous_count": lengths[pid] - acgt}
                replicons.append(rep)
            rows, gff_build = parse_gff(blob[role["gff"]].decode(), lengths)
            require(gff_build == expected_acc, "GFF assembly build accession differs")
            genes = {(r["replicon"], r["attrs"].get("ID")): r
                     for r in rows if r["kind"] in ("gene", "pseudogene")}
            gff_loci = defaultdict(list)
            for row in rows:
                if row["kind"] != "CDS":
                    continue
                a = row["attrs"]
                parent = genes.get((row["replicon"], a.get("Parent", "")), {}).get("attrs", {})
                locus = a.get("locus_tag") or parent.get("locus_tag")
                require(locus, "GFF CDS lacks exact locus_tag, line " + str(row["line"]))
                row["locus"] = locus
                row["pseudo"] = a.get("pseudo") == "true" or parent.get("pseudo") == "true"
                gff_loci[(row["replicon"], locus)].append(row)
            require(gff_loci, "No GFF CDS")
            proteins = fasta(blob[role["protein"]].decode(), protein=True)
            protein_byid = protein_lookup(proteins)
            for pid, entries in protein_byid.items():
                if len(entries) > 1:
                    review("DUPLICATE_IDENTICAL_PROTEIN_ACCESSION",
                           {"protein_accession": pid, "fasta_records": len(entries)})
            cds_by_locus = {}
            for cid, title, sequence in fasta(blob[role["cds"]].decode()):
                tags = cds_header_attrs(title)
                m = re.match(r"^lcl\|(.+)_cds_", cid)
                require(m and m[1] in genome, "CDS FASTA lacks exact replicon mapping: " + cid)
                require(tags.get("locus_tag"), "CDS FASTA lacks locus_tag: " + cid)
                lk = (m[1], tags["locus_tag"])
                require(lk not in cds_by_locus, "Ambiguous CDS FASTA locus: " + str(lk))
                cds_by_locus[lk] = (cid, tags, sequence)
            gb_loci = {}
            pseudo_gene_loci = set()
            for pid, rec in gb.items():
                for feature in rec.features:
                    q = feature.qualifiers
                    locus = q.get("locus_tag", [None])[0]
                    if feature.type == "gene" and locus and ("pseudo" in q or "pseudogene" in q):

                        pseudo_gene_loci.add((pid, locus))
                    if feature.type != "CDS":
                        continue
                    require(locus and feature.location is not None, "GBFF CDS lacks locus/location")
                    lk = (pid, locus)
                    require(lk not in gb_loci, "Ambiguous GBFF CDS locus: " + str(lk))
                    gb_loci[lk] = feature
            assertion(set(gb_loci) == set(gff_loci), "GFF_GBFF_CDS_MEMBERSHIP",
                      {"gff_only": sorted(set(gff_loci) - set(gb_loci)),
                       "gbff_only": sorted(set(gb_loci) - set(gff_loci))})
            assertion(set(cds_by_locus) <= set(gb_loci), "UNMAPPED_CDS_FASTA",
                      sorted(set(cds_by_locus) - set(gb_loci)))
            used_proteins = set()
            translation_pass = 0
            for lk, feature in gb_loci.items():
                pid, locus = lk
                key = expected_acc + "|" + pid + "|" + locus
                q = feature.qualifiers
                pseudo = "pseudo" in q or "pseudogene" in q
                parts = list(feature.location.parts)
                fuzzy = any(not isinstance(p.start, ExactPosition) or not isinstance(p.end, ExactPosition)
                            for p in parts)
                first, last = parts[0], parts[-1]
                five_prime_partial = not isinstance(first.start if first.strand == 1 else first.end, ExactPosition)
                three_prime_partial = not isinstance(last.end if last.strand == 1 else last.start, ExactPosition)
                exceptions = {k: q[k] for k in ("exception", "transl_except", "ribosomal_slippage",
                                               "pseudo", "pseudogene") if k in q}
                expected_nt = str(feature.extract(gb[pid].seq)).upper()
                protein_id = q.get("protein_id", [None])[0]
                translation = q.get("translation", [None])[0]
                first_offset = int(q.get("codon_start", ["1"])[0]) - 1
                table = int(q.get("transl_table", ["1"])[0])
                row = {"assembly_accession": expected_acc, "replicon": pid, "locus_tag": locus,
                       "locus_key": key, "protein_accession": protein_id,
                       "gbff_location": str(feature.location),
                       "gbff_parts_zero_based": [[int(p.start), int(p.end), p.strand] for p in parts],
                       "codon_start": first_offset + 1, "translation_table": table,
                        "pseudo": pseudo, "partial_or_fuzzy": fuzzy, "source_exceptions": exceptions,
                        "five_prime_partial": five_prime_partial, "three_prime_partial": three_prime_partial,
                       "cds_nt_sha256": hashlib.sha256(expected_nt.encode()).hexdigest(),
                       "source_translation_sha256": hashlib.sha256(translation.encode()).hexdigest() if translation else None}
                loci.append(row)
                require(first_offset in (0, 1, 2), "Invalid GBFF codon_start: " + key)
                if lk in gff_loci:
                    gr = gff_loci[lk]
                    circular = gb[pid].annotations.get("topology") == "circular"
                    gcoords = []
                    for g in gr:
                        require(g["strand"] in ("+", "-"), "CDS GFF strand unspecified: " + key)
                        for a, b in intervals(g["start"], g["end"], lengths[pid], circular):
                            gcoords.append((a, b, 1 if g["strand"] == "+" else -1))
                    bcoords = [(int(p.start), int(p.end), p.strand) for p in parts]
                    assertion(sorted(gcoords) == sorted(bcoords), "GFF_GBFF_CDS_COORDINATES",
                              {"gff": gcoords, "gbff": bcoords}, key)
                    gpids = {g["attrs"].get("protein_id") for g in gr if g["attrs"].get("protein_id")}
                    assertion(gpids == ({protein_id} if protein_id else set()),
                              "GFF_GBFF_PROTEIN_ID", sorted(gpids), key)
                    assertion(all(g["pseudo"] == pseudo for g in gr), "GFF_GBFF_PSEUDO_FLAG",
                              "Pseudogene flags differ", key)
                    row["gff_source_lines"] = [g["line"] for g in gr]
                    row["gff_literal_parts_one_based"] = [
                        [g["start"], g["end"], g["strand"], g["phase"]] for g in gr]
                    assertion(all(g["phase"] in ("0", "1", "2") for g in gr),
                              "GFF_CDS_PHASE_MISSING", "CDS phase is not explicit", key)
                    assertion(all(int(g["attrs"].get("transl_table", "1")) == table for g in gr),
                              "GFF_GBFF_TRANSLATION_TABLE", "Translation tables differ", key)
                    prior_length = [sum(len(p) for p in parts[:i]) for i in range(len(parts))]
                    phase_exceptions = {k: q[k] for k in ("exception", "transl_except", "ribosomal_slippage") if k in q}
                    for g in gr:
                        normalized = intervals(g["start"], g["end"], lengths[pid], circular)
                        matching_indices = [i for i, p in enumerate(parts)
                                            if (int(p.start), int(p.end)) in normalized]
                        if not matching_indices:
                            continue  # Coordinate mismatch already failed independently above.
                        part_index = min(matching_indices)
                        expected_phase = (first_offset - prior_length[part_index]) % 3
                        if part_index == 0 or not phase_exceptions:
                            assertion(g["phase"] == str(expected_phase), "GFF_GBFF_CDS_PHASE",
                                      {"gff_line": g["line"], "gff_phase": g["phase"],
                                       "expected_phase": expected_phase, "gbff_part_index": part_index,
                                       "codon_start": first_offset + 1}, key)
                        else:
                            review("GFF_INTERNAL_PHASE_DOCUMENTED_EXCEPTION",
                                   {"gff_line": g["line"], "gff_phase": g["phase"],
                                    "nominal_expected_phase": expected_phase, "qualifiers": phase_exceptions}, key)
                if lk in cds_by_locus:
                    cid, tags, actual_nt = cds_by_locus[lk]
                    row["cds_fasta_id"] = cid
                    row["cds_fasta_nt_sha256"] = hashlib.sha256(actual_nt.encode()).hexdigest()
                    supplied_frame = int(tags.get("frame", "1"))
                    assertion(supplied_frame == first_offset + 1, "CDS_FASTA_GBFF_FRAME",
                              {"cds_frame": supplied_frame, "gbff_codon_start": first_offset + 1}, key)
                    assertion(actual_nt == expected_nt[first_offset:], "CDS_FASTA_GENOME_SEQUENCE",
                              {"check": "Supplied CDS equals biological GBFF extraction after source codon_start offset.",
                               "source_codon_start": first_offset + 1, "whole_feature_length": len(expected_nt),
                               "supplied_cds_length": len(actual_nt)}, key)
                    if first_offset:
                        review("SOURCE_CDS_CODON_START_OFFSET",
                               {"source_codon_start": first_offset + 1,
                                "basis": "CDS FASTA [frame] agrees with GBFF /codon_start; exact supplied nucleotides matched. No source sequence altered."}, key)
                    assertion(tags.get("protein_id") == protein_id, "CDS_FASTA_PROTEIN_ID",
                              {"cds": tags.get("protein_id"), "gbff": protein_id}, key)
                elif not pseudo:
                    fail("MISSING_NONPSEUDO_CDS_FASTA", "Annotated CDS absent from CDS FASTA", key)
                else:
                    review("PSEUDOGENE_NO_CDS_FASTA", "Source pseudogene retained; no sequence invented.", key)
                if protein_id:
                    used_proteins.add(protein_id)
                    if assertion(protein_id in protein_byid, "MISSING_PRIMARY_PROTEIN",
                                 "Annotated protein absent from primary FASTA", key):
                        supplied = protein_byid[protein_id][0][1]
                        row["protein_sequence_sha256"] = hashlib.sha256(supplied.encode()).hexdigest()
                        row["protein_fasta_record_count"] = len(protein_byid[protein_id])
                        assertion(translation is not None and supplied == translation,
                                  "PROTEIN_GBFF_TRANSLATION", "Primary protein differs from annotated translation", key)
                elif not pseudo:
                    fail("NONPSEUDO_CDS_NO_PROTEIN_ID", "No source protein accession", key)
                if pseudo or exceptions:
                    review("DOCUMENTED_ANNOTATION_EXCEPTION",
                           {"pseudo": pseudo, "qualifiers": exceptions,
                            "check": "Source CDS/feature/protein joins checked; naive translation not asserted."}, key)
                    row["computed_translation_check"] = "DOCUMENTED_EXCEPTION"
                elif translation:
                    nt = expected_nt[first_offset:]
                    try:
                        virtual_terminal_bases = 0
                        virtual_unknown_terminal_omitted = False
                        if fuzzy:
                            if len(nt) % 3:
                                require(three_prime_partial,
                                        "Incomplete codon without documented 3-prime partial endpoint")
                                virtual_terminal_bases = -len(nt) % 3
                            validation_nt = nt + "N" * virtual_terminal_bases
                            computed = str(Seq(validation_nt).translate(table=table)).rstrip("*")
                            biological_first = parts[0]
                            n_exact = isinstance(biological_first.start if biological_first.strand == 1
                                                 else biological_first.end, ExactPosition)
                            from Bio.Data import CodonTable
                            if n_exact and nt[:3] in CodonTable.unambiguous_dna_by_id[table].start_codons:
                                computed = "M" + computed[1:]
                            if (virtual_terminal_bases and computed.endswith("X")
                                    and computed[:-1] == translation):
                                # NCBI may omit an unresolved residue from a documented
                                # 3-prime partial codon. Complete codons must match exactly.
                                computed = computed[:-1]
                                virtual_unknown_terminal_omitted = True
                        else:
                            computed = str(Seq(nt).translate(table=table, cds=True))
                        if computed == translation:
                            translation_pass += 1
                            row["computed_translation_check"] = ("MATCH_PARTIAL_UNKNOWN_TERMINAL_OMITTED" if virtual_unknown_terminal_omitted
                                                                 else "MATCH_PARTIAL_TERMINAL_CODON" if virtual_terminal_bases else "MATCH")
                            if virtual_terminal_bases:
                                review("PARTIAL_TERMINAL_UNKNOWN_OMITTED" if virtual_unknown_terminal_omitted
                                       else "PARTIAL_TERMINAL_CODON_AMBIGUITY_VALIDATION",
                                       {"virtual_unknown_bases": virtual_terminal_bases,
                                        "known_terminal_bases": nt[-(len(nt) % 3):],
                                        "basis": ("Source 3-prime endpoint is partial; virtual terminal codon is unresolved X and omitted by source. All complete codons exactly match annotated and primary proteins."
                                                  if virtual_unknown_terminal_omitted else
                                                  "Source 3-prime endpoint is partial; virtual N ambiguity translation exactly matches annotated and primary proteins.")
                                                  + " Source nucleotides/proteins remain unmodified."}, key)
                        elif fuzzy:
                            fail("COMPUTED_PARTIAL_TRANSLATION_MISMATCH",
                                 "Partial-aware genomic translation differs from source translation; independent review required.", key)
                            row["computed_translation_check"] = "FAIL_REQUIRES_REVIEW"
                        else:
                            fail("COMPUTED_TRANSLATION_MISMATCH",
                                 "Genomic translation differs from source translation", key)
                            row["computed_translation_check"] = "FAIL"
                    except Exception as e:
                        if fuzzy:
                            fail("COMPUTED_PARTIAL_TRANSLATION_EXCEPTION", str(e), key)
                            row["computed_translation_check"] = "FAIL_REQUIRES_REVIEW"
                        else:
                            fail("COMPUTED_TRANSLATION_EXCEPTION", str(e), key)
                            row["computed_translation_check"] = "FAIL"
                    if fuzzy:
                        review("SOURCE_PARTIAL_OR_FUZZY_CDS", str(feature.location), key)
                elif not pseudo:
                    fail("MISSING_ANNOTATED_TRANSLATION", "No translation qualifier for nonpseudo CDS", key)
            assertion(set(protein_byid) == used_proteins, "UNMAPPED_PRIMARY_PROTEINS",
                      sorted(set(protein_byid) - used_proteins))
            for lk in sorted(pseudo_gene_loci - set(gb_loci)):
                review("PSEUDOGENE_GENE_WITHOUT_CDS",
                       "Source gene annotated as pseudogene without CDS; no sequence invented.",
                       expected_acc + "|" + lk[0] + "|" + lk[1])
            stats.update(genomic_records=len(genome), total_bases=sum(lengths.values()),
                         protein_fasta_records=len(proteins), unique_protein_accessions=len(protein_byid),
                         cds_fasta_records=len(cds_by_locus), gbff_cds_loci=len(gb_loci),
                         gff_cds_loci=len(gff_loci), pseudogene_cds=sum(r["pseudo"] for r in loci),
                         partial_or_fuzzy_cds=sum(r["partial_or_fuzzy"] for r in loci),
                         computed_translation_matches=translation_pass)
    except Exception as e:
        fail("PACKAGE_OR_PARSE_FAILURE", type(e).__name__ + ": " + str(e))
    result["status"] = ("FAIL" if errors else
                        "PASS_SEQUENCE_INTEGRITY_WITH_DOCUMENTED_EXCEPTIONS" if reviews else
                        "PASS_SEQUENCE_INTEGRITY")
    result["error_count"], result["review_exception_count"] = len(errors), len(reviews)
    return result

def selftest():
    cases = []
    def rejects(label, function):
        try:
            function()
        except (ValueError, KeyError):
            cases.append({"case": label, "result": "PASS_REJECTED"})
        else:
            raise AssertionError("Malformed input accepted: " + label)
    for name in ("../escape", "/absolute", "C:/drive", "a\\b", "a/./b"):
        rejects("unsafe_member_" + name, lambda n=name: safe_member(n))
    rejects("fasta_prefix", lambda: fasta("ACG\n>id\nACG"))
    rejects("empty_fasta", lambda: fasta(">id\n"))
    rejects("invalid_dna", lambda: fasta(">id\nACZ"))
    rejects("conflicting_protein_id", lambda: protein_lookup([("WP_1.1", "x", "MK"), ("WP_1.1", "y", "MA")]))
    rejects("conflicting_cds_header_attribute", lambda: cds_header_attrs("id [locus_tag=X] [locus_tag=Y]"))
    rejects("gff_columns", lambda: parse_gff("x\t1", {"x": 9}))
    rejects("gff_coordinate_zero", lambda: parse_gff("##sequence-region x 1 9\nx\ts\tCDS\t0\t9\t.\t+\t0\tID=c", {"x": 9}))
    rejects("gff_wrong_sequence_length", lambda: parse_gff("##sequence-region x 1 8\nx\ts\tCDS\t1\t9\t.\t+\t0\tID=c", {"x": 9}))
    rejects("gff_wrong_phase", lambda: parse_gff("##sequence-region x 1 9\nx\ts\tCDS\t1\t9\t.\t+\t3\tID=c", {"x": 9}))
    rejects("unjustified_circular_coordinates", lambda: intervals(8, 12, 9, False))
    require(intervals(8, 12, 9, True) == [(7, 9), (0, 3)], "Circular normalization failed")
    from Bio.SeqFeature import SeqFeature, FeatureLocation, CompoundLocation
    seq = Seq("ATGAAATAA")
    require(str(seq.translate(table=11, cds=True)) == "MK", "Complete translation failed")
    require(str(Seq("GTGAAATAA").translate(table=11, cds=True)) == "MK", "Alternative start validation failed")
    f = SeqFeature(FeatureLocation(0, 9, strand=-1), type="CDS")
    require(str(f.extract(seq)) == "TTATTTCAT", "Minus strand extraction failed")
    p = protein_lookup([("WP_1.1", "x", "MK"), ("WP_1.1", "y", "MK")])
    require(len(p["WP_1.1"]) == 2, "Identical duplicated WP IDs were lost")
    cases.append({"case": "circular_minus_strand_alternative_start_duplicate_wp_positive_cases", "result": "PASS"})
    return cases


def full196_main():
    import argparse, csv, os, time
    parser = argparse.ArgumentParser(description="Independent complete approved196 raw-package validation.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--raw-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--self-test-only", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    output = args.output_dir or root / "reports" / "stage02_validation"
    output.mkdir(parents=True, exist_ok=True)
    def atomic_json(path, value):
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    def write_tsv(path, rows, columns):
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=columns, delimiter="\t", lineterminator="\n", extrasaction="ignore")
            w.writeheader()
            for row in rows:
                w.writerow({k: json.dumps(v, ensure_ascii=False, sort_keys=True) if isinstance(v, (list, dict)) else v
                            for k, v in row.items()})
        os.replace(temporary, path)
    started = datetime.now(timezone.utc).isoformat()
    t0 = time.monotonic()
    tests = selftest()
    atomic_json(output / "negative_parser_tests.json", {"status": "PASS", "checks": tests,
                 "validator_source_sha256": hashfile(__file__), "biopython_version": Bio.__version__})
    if args.self_test_only:
        print(json.dumps({"status": "PASS_PARSER_TESTS", "checks": len(tests)}))
        return 0
    listpath = root / "config" / "approved_accessions.txt"
    accessions = listpath.read_text(encoding="utf-8-sig").split()
    approval = json.loads((root / "config" / "approval.json").read_text(encoding="utf-8"))
    require(len(accessions) == len(set(accessions)) == 196, "Approved panel is not unique exact196")
    require(all(re.fullmatch(r"GCF_\d{9}\.\d+", a) for a in accessions), "Unversioned panel accession")
    require(hashfile(listpath) == approval["panel_accessions_sha256"], "Approved panel input hash differs")
    require(approval["pilot"] is False and approval["approved_assembly_count"] == 196,
            "Approval does not authorize full196")
    ledgerpath = root / "evidence" / "g0" / "reports" / "taxonomy_verified_197.tsv"
    with ledgerpath.open(encoding="utf-8-sig", newline="") as f:
        ledger = list(csv.DictReader(f, delimiter="\t"))
    frozen = {r["original_accession"]: r for r in ledger}
    require(len(ledger) == len(frozen) == 197 and set(accessions) <= set(frozen),
            "Frozen G0 ledger is incomplete/ambiguous")
    raw = args.raw_root or root / "data" / "raw_ncbi"
    allqc, allexceptions, allerrors, allfiles, allreplicons = [], [], [], [], []
    observed = []
    locus_columns = ["locus_key", "assembly_accession", "replicon", "locus_tag", "protein_accession",
                     "cds_fasta_id", "gbff_location", "gbff_parts_zero_based", "gff_literal_parts_one_based",
                     "gff_source_lines", "codon_start", "translation_table", "pseudo", "partial_or_fuzzy",
                     "five_prime_partial", "three_prime_partial", "source_exceptions", "cds_nt_sha256", "cds_fasta_nt_sha256", "source_translation_sha256", "protein_sequence_sha256",
                     "protein_fasta_record_count", "computed_translation_check"]
    locus_temporary = output / "locus_protein_map.tsv.tmp"
    locus_rows_written = 0
    with locus_temporary.open("w", encoding="utf-8", newline="") as locus_stream:
        locus_writer = csv.DictWriter(locus_stream, fieldnames=locus_columns, delimiter="\t",
                                      lineterminator="\n", extrasaction="ignore")
        locus_writer.writeheader()
        for index, acc in enumerate(accessions, 1):
            zpath = raw / acc / (acc + ".ncbi.zip")
            per = output / "assemblies" / acc
            per.mkdir(parents=True, exist_ok=True)
            if zpath.is_file():
                fr = frozen[acc]
                result = validate_package(zpath, acc, fr["organism_tax_id"], fr["verified_taxonomic_lineage"])
                observed.append(acc)
            else:
                result = {"assembly_accession": acc, "status": "FAIL", "error_count": 1,
                          "review_exception_count": 0, "errors": [{"code": "PACKAGE_NOT_RETRIEVED",
                          "detail": str(zpath), "locus_key": None}], "review_exceptions": [],
                          "metrics": {}, "files": [], "loci": [], "replicons": [],
                          "raw_zip_path": zpath.as_posix(), "raw_zip_bytes": None, "raw_zip_sha256": None}
            result["approved_accessions_sha256"] = hashfile(listpath)
            result["frozen_taxonomy_ledger_sha256"] = hashfile(ledgerpath)
            atomic_json(per / "validation.json", result)
            qc = {k: result.get(k) for k in ("assembly_accession", "status", "raw_zip_bytes", "raw_zip_sha256",
                                            "error_count", "review_exception_count")}
            qc.update(result["metrics"])
            allqc.append(qc)
            for r in result["review_exceptions"]:
                allexceptions.append({"assembly_accession": acc, **r})
            for r in result["errors"]:
                allerrors.append({"assembly_accession": acc, **r})
            for r in result["files"]:
                allfiles.append({"assembly_accession": acc, **r})
            allreplicons.extend(result["replicons"])
            for row in result["loci"]:
                locus_writer.writerow({k: json.dumps(v, ensure_ascii=False, sort_keys=True)
                                       if isinstance(v, (list, dict)) else v for k, v in row.items()})
                locus_rows_written += 1
            print(str(index) + "/196 " + acc + " " + result["status"], flush=True)
    qc_columns = ["assembly_accession", "status", "raw_zip_bytes", "raw_zip_sha256", "error_count",
                  "review_exception_count", "provider_md5_members_verified", "reported_organism_tax_id",
                  "frozen_organism_tax_id", "taxonomy_evidence_class", "genomic_records", "total_bases",
                  "protein_fasta_records", "unique_protein_accessions", "cds_fasta_records",
                  "gbff_cds_loci", "gff_cds_loci", "pseudogene_cds", "partial_or_fuzzy_cds",
                  "computed_translation_matches"]
    write_tsv(output / "assembly_qc.tsv", allqc, qc_columns)
    write_tsv(output / "review_exceptions.tsv", allexceptions,
              ["assembly_accession", "locus_key", "code", "detail"])
    write_tsv(output / "errors.tsv", allerrors, ["assembly_accession", "locus_key", "code", "detail"])
    write_tsv(output / "member_sha256.tsv", allfiles, ["assembly_accession", "member", "bytes", "sha256"])
    write_tsv(output / "replicon_qc.tsv", allreplicons,
              ["assembly_accession", "replicon", "length", "sequence_sha256", "gbff_topology",
               "reported_role", "reported_molecule_type", "reported_name", "gbff_source_tax_id", "gc_percent_acgt", "n_count", "ambiguous_count"])
    os.replace(locus_temporary, output / "locus_protein_map.tsv")
    summary = {"status": "FAIL" if allerrors else "PASS_SEQUENCE_INTEGRITY_WITH_DOCUMENTED_EXCEPTIONS",
               "started_at_utc": started, "ended_at_utc": datetime.now(timezone.utc).isoformat(),
               "elapsed_seconds": time.monotonic() - t0, "approved_assemblies": 196,
               "raw_packages_present": len(observed), "assemblies_reported": len(allqc),
               "locus_map_rows_written": locus_rows_written,
               "assemblies_with_errors": sum(q["error_count"] > 0 for q in allqc),
               "error_count": len(allerrors), "review_exception_count": len(allexceptions),
               "exception_counts": dict(Counter(r["code"] for r in allexceptions)),
               "complete_exact196_accounting": [q["assembly_accession"] for q in allqc] == accessions,
               "approved_accessions_sha256": hashfile(listpath),
               "frozen_taxonomy_ledger_sha256": hashfile(ledgerpath),
               "validator_source_sha256": hashfile(__file__), "python_version": sys.version.split()[0],
               "biopython_version": Bio.__version__, "parser_test_count": len(tests),
               "evidence_limit": "Package/sequence/annotation integrity. Documented pseudogene, translation, partial and archive metadata exceptions remain explicit. No ANI or functional certification."}
    atomic_json(output / "validation_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 1 if allerrors else 0

if __name__ == "__main__":
    raise SystemExit(full196_main())
