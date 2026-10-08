#!/usr/bin/env python3
"""Full196 source-derived locus inputs, with no sequence prediction.

The production CLI requires successful independent Stage 2 validation for all196.
It rereads raw NCBI ZIP/catalog/GBFF/FAA/GFF, preserves primary amino-acid bytes,
and derives one search target for each protein-bearing biological CDS locus.
No marker or detector job is performed. --self-test uses synthetic fixtures only.
The root workflow owns the production lock; this builder does not acquire another.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
import time
from urllib.parse import quote, unquote
import zipfile

import Bio
from Bio import SeqIO
from Bio.SeqFeature import ExactPosition

ROLES = {'GENBANK_FLAT_FILE': 'gbff', 'PROTEIN_FASTA': 'protein', 'GFF3': 'gff'}
AA = set('ACDEFGHIKLMNPQRSTVWYBXZUOJ*')
LOCUS_COLUMNS = [
    'assembly_accession', 'replicon', 'locus_tag', 'locus_key', 'row_kind',
    'protein_accession', 'protein_target_present', 'protein_aa_length',
    'primary_faa_sequence_sha256', 'gbff_translation_sha256',
    'primary_faa_record_ordinals', 'primary_faa_headers',
    'gbff_feature_ordinal', 'gbff_gene_feature_ordinals',
    'gbff_location', 'gbff_parts_zero_based_biological_order', 'gbff_strand',
    'gbff_cds_pseudo', 'gbff_gene_pseudo', 'source_pseudo_any',
    'partial_or_fuzzy', 'codon_start', 'translation_table',
    'gbff_qualifiers_without_translation', 'source_gene_qualifiers',
    'gff_source_lines', 'gff_literal_segments_one_based',
    'source_cds_ordinal_on_replicon', 'protein_ordinal_on_replicon',
    'padloc_target_id', 'padloc_gff_id', 'defensefinder_target_id',
    'derived_linear_order_start_one_based', 'derived_linear_order_end_one_based',
    'derived_gff_geometry', 'origin_spanning', 'requires_coordinate_review',
]


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def atomic_bytes(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + '.partial')
    partial.write_bytes(value)
    partial.replace(path)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def write_tsv(path, rows, columns):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=columns, delimiter='\t', lineterminator='\n')
    writer.writeheader()
    for row in rows:
        values = {}
        for key in columns:
            value = row.get(key)
            values[key] = (json.dumps(value, ensure_ascii=False, separators=(',', ':'))
                           if isinstance(value, (dict, list)) else value)
        writer.writerow(values)
    atomic_bytes(path, stream.getvalue().encode('utf-8'))


def one_qualifier(qualifiers, key, required=False, default=None):
    values = qualifiers.get(key, [])
    require(len(values) <= 1, 'Ambiguous GBFF qualifier: ' + key)
    value = values[0] if values else default
    require(not required or bool(value), 'Required GBFF qualifier absent: ' + key)
    return value


def token(value, label):
    require(value and not any(c.isspace() for c in value)
            and not any(c in value for c in '|;%\t\r\n'), 'Unsafe/nonunique ' + label + ': ' + str(value))
    return value


def source_faa(data):
    """Retain sequence characters exactly; duplicate accession requires equality."""
    records, header, chunks = [], None, []
    def save():
        require(chunks, 'Empty primary FAA record: ' + str(header))
        sequence = ''.join(chunks)
        require(sequence and set(sequence) <= AA, 'Primary FAA has noncanonical characters/case')
        records.append({'protein_accession': header.split()[0], 'header': header,
                        'sequence': sequence, 'ordinal': len(records) + 1})
    for number, raw in enumerate(data.decode('ascii').splitlines(), 1):
        if not raw:
            continue
        if raw.startswith('>'):
            if header is not None:
                save()
            header, chunks = raw[1:], []
            require(header and not header[0].isspace(), 'Malformed primary FAA header')
        else:
            require(header is not None, 'Primary FAA sequence before header: ' + str(number))
            require(not any(c.isspace() for c in raw), 'Whitespace in primary FAA sequence')
            chunks.append(raw)
    if header is not None:
        save()
    require(records, 'Primary FAA has no records')
    by_accession = defaultdict(list)
    for row in records:
        by_accession[row['protein_accession']].append(row)
    for accession, repeated in by_accession.items():
        require(len({r['sequence'] for r in repeated}) == 1,
                'Repeated protein accession has conflicting sequences: ' + accession)
    return records, by_accession


def attributes(value):
    result = {}
    if value == '.':
        return result
    for item in value.split(';'):
        if not item:
            continue
        require('=' in item, 'Malformed GFF attribute')
        key, encoded = item.split('=', 1)
        require(key and key not in result, 'Duplicate/empty GFF attribute')
        result[key] = unquote(encoded)
    return result


def source_gff(data, replicon_lengths):
    rows, regions, region_topology = [], {}, defaultdict(list)
    for number, line in enumerate(data.decode('utf-8').splitlines(), 1):
        if line == '##FASTA':
            break
        if line.startswith('##sequence-region '):
            _, replicon, start, end = line.split()
            require(replicon not in regions, 'Duplicate GFF sequence-region')
            regions[replicon] = (int(start), int(end))
        if not line or line.startswith('#'):
            continue
        fields = line.split('\t')
        require(len(fields) == 9, 'GFF requires nine columns, source line ' + str(number))
        replicon, source, kind, start, end, score, strand, phase, attrs = fields
        require(replicon in replicon_lengths, 'GFF references unknown GBFF replicon')
        start, end = int(start), int(end)
        require(1 <= start <= end, 'Invalid GFF coordinates')
        row = {'replicon': replicon, 'source': source, 'kind': kind, 'start': start,
               'end': end, 'score': score, 'strand': strand, 'phase': phase,
               'attributes': attributes(attrs), 'line': number}
        rows.append(row)
        if kind == 'region' and 'Is_circular' in row['attributes']:
            literal = row['attributes']['Is_circular']
            require(literal.lower() in ('true', 'false'), 'Unrecognized source GFF circularity')
            region_topology[replicon].append({'source_line': number, 'Is_circular': literal})
    require(set(regions) == set(replicon_lengths), 'GFF/GBFF replicon membership differs')
    for replicon, length in replicon_lengths.items():
        require(regions[replicon] == (1, length), 'GFF/GBFF replicon lengths differ')
    parents = {}
    for row in rows:
        if row['kind'] in ('gene', 'pseudogene') and row['attributes'].get('ID'):
            key = (row['replicon'], row['attributes']['ID'])
            require(key not in parents, 'Duplicate GFF gene ID on one replicon')
            parents[key] = row['attributes']
    cds = defaultdict(list)
    for row in rows:
        if row['kind'] != 'CDS':
            continue
        attrs = row['attributes']
        parent_id = attrs.get('Parent')
        require(not parent_id or ',' not in parent_id, 'Ambiguous multiple GFF parents')
        parent = parents.get((row['replicon'], parent_id), {})
        locus = attrs.get('locus_tag') or parent.get('locus_tag')
        require(locus, 'GFF CDS lacks locus tag')
        row['locus_tag'] = locus
        cds[(row['replicon'], locus)].append(row)
    return rows, cds, dict(region_topology)


def source_payload(zip_path, accession):
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), 'Duplicate raw ZIP names')
        for name in names:
            part = PurePosixPath(name)
            require(not part.is_absolute() and '..' not in part.parts
                    and '\\' not in name and ':' not in name, 'Unsafe ZIP member')
        require(archive.testzip() is None, 'Raw ZIP CRC failure')
        catalogs = [n for n in names if PurePosixPath(n).name == 'dataset_catalog.json']
        require(len(catalogs) == 1, 'Ambiguous/missing dataset catalog')
        catalog_name = catalogs[0]
        catalog = json.loads(archive.read(catalog_name))
        selected = [a for a in catalog.get('assemblies', []) if a.get('accession') == accession]
        require(len(selected) == 1, 'Exact assembly absent/duplicate in catalog')
        payload, members = {}, {}
        for entry in selected[0].get('files', []):
            role = ROLES.get(entry.get('fileType'))
            if not role:
                continue
            require(role not in payload, 'Duplicate source role: ' + role)
            name = entry['filePath']
            base = str(PurePosixPath(catalog_name).parent)
            found = {name, base + '/' + name, base + '/data/' + name,
                     'ncbi_dataset/data/' + name} & set(names)
            require(len(found) == 1, 'Unresolved/ambiguous catalog member: ' + name)
            member = found.pop()
            require('/' + accession + '/' in '/' + member, 'Source role outside exact assembly directory')
            value = archive.read(member)
            require(value, 'Empty source role: ' + role)
            if 'uncompressedLengthBytes' in entry:
                require(len(value) == int(entry['uncompressedLengthBytes']), 'Catalog source byte-length mismatch')
            payload[role] = value
            members[role] = {'zip_member': member, 'bytes': len(value), 'sha256': sha_bytes(value)}
        require(set(payload) == set(ROLES.values()), 'Required source roles missing')
    return payload, members


def locus_geometry(feature, source_rows, length, circular):
    parts = list(feature.location.parts)
    require(parts and all(p.ref is None and p.ref_db is None for p in parts), 'Remote CDS location is unsupported')
    require(all(0 <= int(p.start) < int(p.end) <= length for p in parts), 'GBFF feature outside replicon')
    strands = {p.strand for p in parts}
    require(len(strands) == 1 and strands <= {1, -1}, 'Mixed/unspecified CDS strand')
    coords = [[int(p.start), int(p.end), p.strand] for p in parts]
    fuzzy = any(not isinstance(p.start, ExactPosition) or not isinstance(p.end, ExactPosition) for p in parts)
    wraps_gff = [r for r in source_rows if r['end'] > length]
    touches_both_ends = (len(parts) > 1 and any(int(p.start) == 0 for p in parts)
                         and any(int(p.end) == length for p in parts))
    origin = bool(wraps_gff or (circular and touches_both_ends))
    require(not wraps_gff or circular, 'Origin-spanning source GFF on undocumented circular replicon')
    if origin:
        # Anchor at the high-coordinate physical segment; preserve biological part order separately.
        high_starts = [int(p.start) + 1 for p in parts if int(p.end) == length]
        low_ends = [int(p.end) for p in parts if int(p.start) == 0]
        require(high_starts and low_ends, 'Cannot anchor origin-spanning compound CDS')
        start = min(r['start'] for r in wraps_gff) if wraps_gff else min(high_starts)
        end = max(r['end'] for r in wraps_gff) if wraps_gff else length + max(low_ends)
        require(1 <= start <= length < end <= 2 * length, 'Invalid derived origin envelope')
        geometry = 'ORIGIN_SPANNING_UNROLLED_ENVELOPE_FOR_ORDER_ONLY'
    else:
        start, end = min(int(p.start) for p in parts) + 1, max(int(p.end) for p in parts)
        geometry = 'EXACT_SINGLE_SEGMENT' if len(parts) == 1 else 'MULTIPART_ENVELOPE_FOR_ORDER_ONLY'
    return {'gbff_parts_zero_based_biological_order': coords,
            'gbff_strand': next(iter(strands)), 'partial_or_fuzzy': fuzzy,
            'origin_spanning': origin, 'derived_linear_order_start_one_based': start,
            'derived_linear_order_end_one_based': end, 'derived_gff_geometry': geometry,
            'requires_coordinate_review': bool(origin or len(parts) > 1 or fuzzy)}


def derive_loci(accession, gbff_data, faa_data, gff_data):
    faa_records, protein_by_accession = source_faa(faa_data)
    records = list(SeqIO.parse(io.StringIO(gbff_data.decode('utf-8')), 'genbank'))
    require(records and len(records) == len({r.id for r in records}), 'Empty/duplicate GBFF replicons')
    gbff_by_id = {record.id: record for record in records}
    lengths = {r.id: len(r.seq) for r in records}
    gff_rows, gff_cds, gff_topology = source_gff(gff_data, lengths)
    loci, source_genes, replicons, used_proteins, cds_keys = [], [], [], set(), set()
    for replicon_ordinal, record in enumerate(records, 1):
        replicon = token(record.id, 'replicon')
        assembly_links = [x.split(':', 1)[1].strip() for x in record.dbxrefs if x.startswith('Assembly:')]
        require(assembly_links == [accession], 'GBFF Assembly DBLINK differs from exact input')
        topology = record.annotations.get('topology', 'unknown').lower()
        require(topology in ('unknown', 'linear', 'circular'), 'Unknown GBFF topology value')
        source_gff_topology = gff_topology.get(replicon, [])
        for observation in source_gff_topology:
            if topology in ('linear', 'circular'):
                require((observation['Is_circular'].lower() == 'true') == (topology == 'circular'),
                        'GBFF/GFF topology contradiction: ' + replicon)
        documented_circular = topology == 'circular' or any(
            observation['Is_circular'].lower() == 'true' for observation in source_gff_topology)
        replicons.append({'assembly_accession': accession, 'replicon': replicon,
                         'gbff_record_ordinal': replicon_ordinal, 'replicon_directory': 'rep' + f'{replicon_ordinal:06d}',
                         'gbff_length': lengths[replicon], 'gbff_topology': topology,
                         'gff_topology_observations': source_gff_topology,
                         'topology_evidence_source': 'NCBI GBFF LOCUS / source GFF region Is_circular when supplied',
                         'documented_circular': documented_circular,
                         'defensefinder_requested_topology': 'circular' if documented_circular else 'linear',
                         'protein_order_basis': 'Increasing physical start; source GBFF feature ordinal resolves coordinate ties; origin-spanning loci anchored at high-coordinate segment',
                         'padloc_boundary_semantics': 'One isolated replicon in linear coordinate order; circular wrap requires separate reviewed handling'})
        genes_by_locus = defaultdict(list)
        for feature_ordinal, feature in enumerate(record.features, 1):
            if feature.type not in ('gene', 'pseudogene'):
                continue
            locus = one_qualifier(feature.qualifiers, 'locus_tag')
            if not locus:
                continue
            token(locus, 'locus_tag')
            genes_by_locus[locus].append((feature_ordinal, feature))
            source_genes.append({'assembly_accession': accession, 'replicon': replicon,
                                 'locus_tag': locus, 'locus_key': accession + '|' + replicon + '|' + locus,
                                 'gbff_feature_ordinal': feature_ordinal, 'gbff_feature_type': feature.type,
                                 'gbff_location': str(feature.location), 'source_qualifiers': feature.qualifiers})
        replicon_cds_loci = set()
        for feature_ordinal, feature in enumerate(record.features, 1):
            if feature.type != 'CDS':
                continue
            q = feature.qualifiers
            locus = token(one_qualifier(q, 'locus_tag', required=True), 'locus_tag')
            key = accession + '|' + replicon + '|' + locus
            require(feature.location is not None and key not in cds_keys, 'Missing/duplicate CDS biological locus: ' + key)
            cds_keys.add(key)
            replicon_cds_loci.add(locus)
            source_rows = gff_cds.get((replicon, locus), [])
            require(source_rows, 'GBFF CDS lacks matching source GFF locus: ' + key)
            geometry = locus_geometry(feature, source_rows, lengths[replicon], documented_circular)
            pid = one_qualifier(q, 'protein_id')
            translation = one_qualifier(q, 'translation')
            source_cds_pseudo = 'pseudo' in q or 'pseudogene' in q
            source_gene_pseudo = any('pseudo' in f.qualifiers or 'pseudogene' in f.qualifiers
                                     or f.type == 'pseudogene' for _, f in genes_by_locus[locus])
            require(pid or source_cds_pseudo or source_gene_pseudo, 'Nonpseudo CDS has no primary protein ID: ' + key)
            sequence, repeated = None, []
            if pid:
                require(pid in protein_by_accession, 'GBFF protein absent from primary FAA: ' + key)
                repeated = protein_by_accession[pid]
                sequence = repeated[0]['sequence']
                require(translation is not None and sequence == translation,
                        'Primary FAA sequence differs from exact GBFF /translation: ' + key)
                require('cds-' not in key, 'PADLOC cdsprefix normalization conflicts with exact locus key: ' + key)
                used_proteins.add(pid)
            else:
                require(translation is None, 'Unmapped GBFF translation lacks protein accession: ' + key)
            source_gff_pids = {r['attributes']['protein_id'] for r in source_rows if r['attributes'].get('protein_id')}
            require(source_gff_pids == ({pid} if pid else set()), 'GFF/GBFF source protein accessions differ: ' + key)
            strand_label = '+' if geometry['gbff_strand'] == 1 else '-'
            require(all(r['strand'] == strand_label for r in source_rows), 'GFF/GBFF strand differs: ' + key)
            row = {'assembly_accession': accession, 'replicon': replicon, 'locus_tag': locus, 'locus_key': key,
                   'row_kind': 'CDS', 'protein_accession': pid, 'protein_target_present': bool(sequence),
                   'protein_aa_length': len(sequence) if sequence else None,
                   'primary_faa_sequence_sha256': sha_bytes(sequence.encode('ascii')) if sequence else None,
                   'gbff_translation_sha256': sha_bytes(translation.encode('ascii')) if translation else None,
                   'primary_faa_record_ordinals': [r['ordinal'] for r in repeated],
                   'primary_faa_headers': [r['header'] for r in repeated],
                   'gbff_feature_ordinal': feature_ordinal,
                   'gbff_gene_feature_ordinals': [i for i, _ in genes_by_locus[locus]],
                   'gbff_location': str(feature.location), 'gbff_cds_pseudo': source_cds_pseudo,
                   'gbff_gene_pseudo': source_gene_pseudo, 'source_pseudo_any': source_cds_pseudo or source_gene_pseudo,
                   'codon_start': int(one_qualifier(q, 'codon_start', default='1')),
                   'translation_table': int(one_qualifier(q, 'transl_table', default='1')),
                   'gbff_qualifiers_without_translation': {k: v for k, v in q.items() if k != 'translation'},
                   'source_gene_qualifiers': [f.qualifiers for _, f in genes_by_locus[locus]],
                   'gff_source_lines': [r['line'] for r in source_rows],
                   'gff_literal_segments_one_based': [[r['start'], r['end'], r['strand'], r['phase']] for r in source_rows],
                   '_sequence': sequence, **geometry}
            require(row['codon_start'] in (1, 2, 3), 'Invalid source codon_start')
            loci.append(row)
        for locus, gene_features in genes_by_locus.items():
            pseudo = any('pseudo' in f.qualifiers or 'pseudogene' in f.qualifiers
                         or f.type == 'pseudogene' for _, f in gene_features)
            if not pseudo or locus in replicon_cds_loci:
                continue
            require(len(gene_features) == 1, 'Ambiguous pseudogene-only locus: ' + locus)
            feature_ordinal, feature = gene_features[0]
            key = accession + '|' + replicon + '|' + locus
            geometry = locus_geometry(feature, [], lengths[replicon], documented_circular)
            loci.append({'assembly_accession': accession, 'replicon': replicon, 'locus_tag': locus,
                         'locus_key': key, 'row_kind': 'PSEUDOGENE_GENE_WITHOUT_CDS',
                         'protein_accession': None, 'protein_target_present': False,
                         'gbff_feature_ordinal': feature_ordinal, 'gbff_gene_feature_ordinals': [feature_ordinal],
                         'gbff_location': str(feature.location), 'gbff_cds_pseudo': None,
                         'gbff_gene_pseudo': True, 'source_pseudo_any': True,
                         'source_gene_qualifiers': [feature.qualifiers], '_sequence': None, **geometry})
    require(set(gff_cds) == {(row['replicon'], row['locus_tag']) for row in loci if row['row_kind'] == 'CDS'},
            'Unmapped/extra source GFF CDS loci')
    require(used_proteins == set(protein_by_accession), 'Primary FAA accessions not mapped to GBFF CDS loci')
    require(len(loci) == len({row['locus_key'] for row in loci}), 'Duplicate exact locus keys')
    require(any(row['protein_target_present'] for row in loci), 'Assembly has no primary protein targets')
    for replicon in replicons:
        current = sorted([row for row in loci if row['replicon'] == replicon['replicon']],
                         key=lambda row: (row['derived_linear_order_start_one_based'],
                                          row['gbff_feature_ordinal'], row['locus_tag']))
        protein_ordinal, cds_ordinal = 0, 0
        for row in current:
            if row['row_kind'] == 'CDS':
                cds_ordinal += 1
                row['source_cds_ordinal_on_replicon'] = cds_ordinal
            if row['protein_target_present']:
                protein_ordinal += 1
                row['protein_ordinal_on_replicon'] = protein_ordinal
                row['padloc_target_id'] = row['locus_key']
                row['padloc_gff_id'] = 'cds-' + row['locus_key']
                row['defensefinder_target_id'] = 'DF' + f'{protein_ordinal:08d}'
        replicon.update(source_cds_loci=cds_ordinal, source_context_loci=len(current),
                        primary_protein_targets=protein_ordinal,
                        untranslated_source_loci=sum(not row['protein_target_present'] for row in current),
                        origin_spanning_loci=sum(row['origin_spanning'] for row in current),
                        coordinate_review_loci=sum(row['requires_coordinate_review'] for row in current),
                        detector_task_eligibility='READY_PRIMARY_PROTEIN_TARGETS' if protein_ordinal else 'NO_PRIMARY_PROTEIN_TARGETS_REVIEW')
    metrics = {'gbff_replicons': len(records), 'source_gff_rows': len(gff_rows),
               'source_gbff_cds_loci': len(cds_keys), 'source_context_loci': len(loci),
               'primary_faa_records': len(faa_records), 'primary_faa_unique_accessions': len(protein_by_accession),
               'protein_bearing_loci': sum(row['protein_target_present'] for row in loci),
               'gbff_pseudogene_cds_loci': sum(row['gbff_cds_pseudo'] is True for row in loci),
               'gene_only_pseudogenes': sum(row['row_kind'] == 'PSEUDOGENE_GENE_WITHOUT_CDS' for row in loci),
               'repeated_primary_faa_accessions': sum(len(rows) > 1 for rows in protein_by_accession.values())}
    return loci, source_genes, replicons, metrics


def fasta_bytes(rows, id_field):
    return ''.join('>' + row[id_field] + '\n' + row['_sequence'] + '\n' for row in rows).encode('ascii')


def gff_bytes(replicon, rows, id_field):
    lines = ['##gff-version 3', '##sequence-region ' + replicon['replicon'] + ' 1 ' + str(replicon['gbff_length']),
             '# Derived single-row CDS geometry is for detector ordering; exact source parts are in locus_crosswalk.tsv.',
             '# PADLOC processes this isolated replicon linearly; circular-origin candidates require separate context review.']
    for row in rows:
        attrs = {'ID': row[id_field], 'locus_tag': row['locus_tag'],
                 'protein_id': row['protein_accession'], 'source_locus_key': row['locus_key'],
                 'source_geometry': row['derived_gff_geometry'],
                 'source_origin_spanning': str(row['origin_spanning']).lower(),
                 'source_pseudo': str(row['source_pseudo_any']).lower()}
        encoded = ';'.join(k + '=' + quote(str(v), safe='|_-.') for k, v in attrs.items())
        lines.append('\t'.join([replicon['replicon'], 'NCBI_GBFF_DERIVED', 'CDS',
                               str(row['derived_linear_order_start_one_based']), str(row['derived_linear_order_end_one_based']),
                               '.', '+' if row['gbff_strand'] == 1 else '-', str(row['codon_start'] - 1), encoded]))
    return ('\n'.join(lines) + '\n').encode('utf-8')


def build_assembly(accession, payload, members, destination, expected_metrics):
    loci, genes, replicons, metrics = derive_loci(accession, payload['gbff'], payload['protein'], payload['gff'])
    count_pairs = {'genomic_records': 'gbff_replicons', 'gbff_cds_loci': 'source_gbff_cds_loci',
                   'protein_fasta_records': 'primary_faa_records', 'unique_protein_accessions': 'primary_faa_unique_accessions',
                   'pseudogene_cds': 'gbff_pseudogene_cds_loci'}
    for stage02_key, producer_key in count_pairs.items():
        require(expected_metrics.get(stage02_key) == metrics[producer_key],
                'Count differs from independent Stage 2 validator: ' + stage02_key)
    destination.mkdir(parents=True, exist_ok=True)
    atomic_bytes(destination / 'primary_ncbi_protein.faa', payload['protein'])
    # GBFF replicon record order and deterministic physical CDS order; no WP-only identity.
    ordered = []
    for replicon in replicons:
        rows = sorted([row for row in loci if row['replicon'] == replicon['replicon'] and row['protein_target_present']],
                      key=lambda row: row['protein_ordinal_on_replicon'])
        ordered.extend(rows)
        folder = destination / 'replicons' / replicon['replicon_directory']
        folder.mkdir(parents=True, exist_ok=True)
        atomic_bytes(folder / 'source_topology.json', json_bytes(replicon))
        if rows:
            atomic_bytes(folder / 'padloc.faa', fasta_bytes(rows, 'padloc_target_id'))
            atomic_bytes(folder / 'padloc.gff', gff_bytes(replicon, rows, 'padloc_gff_id'))
            atomic_bytes(folder / 'defensefinder.faa', fasta_bytes(rows, 'defensefinder_target_id'))
            atomic_bytes(folder / 'defensefinder.gff', gff_bytes(replicon, rows, 'defensefinder_target_id'))
        current = sorted([row for row in loci if row['replicon'] == replicon['replicon']],
                         key=lambda row: (row['derived_linear_order_start_one_based'],
                                          row['gbff_feature_ordinal'], row['locus_tag']))
        write_tsv(folder / 'locus_crosswalk.tsv', current, LOCUS_COLUMNS)
    atomic_bytes(destination / (accession + '.faa'), fasta_bytes(ordered, 'locus_key'))
    write_tsv(destination / 'locus_crosswalk.tsv', loci, LOCUS_COLUMNS)
    write_tsv(destination / 'source_gene_features.tsv', genes,
              ['assembly_accession', 'replicon', 'locus_tag', 'locus_key', 'gbff_feature_ordinal',
               'gbff_feature_type', 'gbff_location', 'source_qualifiers'])
    atomic_bytes(destination / 'source_member_manifest.json', json_bytes(members))
    atomic_bytes(destination / 'replicon_manifest.json', json_bytes(replicons))
    files = [{'path': path.relative_to(destination).as_posix(), 'bytes': path.stat().st_size, 'sha256': digest(path)}
             for path in sorted(destination.rglob('*')) if path.is_file()
             and path.name not in ('build_receipt.json',) and not path.name.endswith('.partial')]
    return metrics, replicons, files


def production(args):
    root, output, stage02 = args.root.resolve(), args.output.resolve(), args.validated_stage02_dir.resolve()
    require(root == Path.cwd().resolve(), 'Run from this dedicated WD repository')
    require(root in output.parents and not any(x in output.relative_to(root).parts for x in ('data', 'config', 'scripts')),
            'Output must be a dedicated derived path inside the repository, outside raw/config/scripts')
    accessions_path = root / 'config/approved_accessions.txt'
    accessions = accessions_path.read_text(encoding='ascii').split()
    approval = json.loads((root / 'config/approval.json').read_text(encoding='utf-8-sig'))
    panel_hash = digest(accessions_path)
    require(len(accessions) == len(set(accessions)) == 196
            and all(re.fullmatch(r'GCF_[0-9]{9}\.[0-9]+', a) for a in accessions), 'Full exact196 panel required')
    require(approval['approved_assembly_count'] == 196 and approval['pilot'] is False
            and approval['human_approval'] == 'APPROVED_FOR_SEQUENCE_ANALYSIS'
            and approval['panel_accessions_sha256'] == panel_hash, 'Full196 approval/hash mismatch')
    validation = json.loads((stage02 / 'validation_summary.json').read_text(encoding='utf-8'))
    require(validation.get('status') == 'PASS_SEQUENCE_INTEGRITY_WITH_DOCUMENTED_EXCEPTIONS'
            and validation.get('approved_assemblies') == validation.get('assemblies_reported') == 196
            and validation.get('error_count') == validation.get('assemblies_with_errors') == 0
            and validation.get('complete_exact196_accounting') is True
            and validation.get('approved_accessions_sha256') == panel_hash,
            'Independent full196 Stage 2 validation must finish before locus inputs')
    identity = {'panel_sha256': panel_hash, 'builder_source_sha256': digest(__file__),
                'stage02_validation_summary_sha256': digest(stage02 / 'validation_summary.json'),
                'python_version': sys.version.split()[0], 'biopython_version': Bio.__version__}
    output.mkdir(parents=True, exist_ok=True)
    identity_path = output / 'builder_identity.json'
    if identity_path.exists():
        require(json.loads(identity_path.read_text()) == identity, 'Different builder inputs/code/environment at existing output path')
    else:
        require(not list(output.iterdir()), 'Existing unowned output directory')
        atomic_bytes(identity_path, json_bytes(identity))
    completed, tasks, started = [], [], time.monotonic()
    try:
        for index, accession in enumerate(accessions, 1):
            zip_path = root / 'data/raw_ncbi' / accession / (accession + '.ncbi.zip')
            expected = json.loads((stage02 / 'assemblies' / accession / 'validation.json').read_text())
            require(expected.get('error_count') == 0 and expected.get('assembly_accession') == accession,
                    'Missing/failed exact assembly Stage 2 validation')
            require(zip_path.is_file() and digest(zip_path) == expected['raw_zip_sha256'],
                    'Source raw ZIP changed after independent validation: ' + accession)
            per = output / 'assemblies' / accession
            receipt_path = per / 'build_receipt.json'
            if receipt_path.is_file():
                receipt = json.loads(receipt_path.read_text())
                require(receipt.get('identity') == identity and receipt.get('raw_zip_sha256') == expected['raw_zip_sha256']
                        and receipt.get('status') == 'SOURCE_LOCUS_INPUTS_CONSTRUCTED', 'Failed/different cached assembly output')
                for entry in receipt['output_files']:
                    file = per / entry['path']
                    require(per.resolve() in file.resolve().parents, 'Unsafe cached output path')
                    require(file.is_file() and file.stat().st_size == entry['bytes'] and digest(file) == entry['sha256'],
                            'Cached source-derived file hash mismatch: ' + str(file))
                replicons = json.loads((per / 'replicon_manifest.json').read_text())
            else:
                payload, members = source_payload(zip_path, accession)
                metrics, replicons, files = build_assembly(accession, payload, members, per, expected['metrics'])
                receipt = {'status': 'SOURCE_LOCUS_INPUTS_CONSTRUCTED', 'scientific_validation': 'NOT_RUN',
                           'identity': identity, 'assembly_accession': accession,
                           'raw_zip_sha256': expected['raw_zip_sha256'], 'metrics': metrics, 'output_files': files,
                           'sequence_basis': 'Exact primary FAA sequence equals GBFF /translation; one target per biological protein-bearing CDS locus',
                           'independent_validation_required': 'Re-read source and compare all locus/ordinal/sequence/coordinate joins'}
                atomic_bytes(receipt_path, json_bytes(receipt))
            completed.append(receipt)
            tasks.extend({**replicon, 'assembly_directory': per.relative_to(output).as_posix(),
                          'replicon_path': (per / 'replicons' / replicon['replicon_directory']).relative_to(output).as_posix()}
                         for replicon in replicons)
            print(str(index) + '/196 ' + accession + ' SOURCE_LOCUS_INPUTS_CONSTRUCTED targets=' + str(receipt['metrics']['protein_bearing_loci']), flush=True)
    except Exception as error:
        atomic_bytes(output / 'construction_failure.json', json_bytes({
            'status': 'FAILED', 'completed_assemblies': len(completed), 'required_assemblies': 196,
            'error': str(error), 'scientific_validation': 'NOT_RUN', 'outputs_preserved': True}))
        raise
    require([r['assembly_accession'] for r in completed] == accessions, 'Full196 construction incomplete')
    atomic_bytes(output / 'detector_task_manifest.json', json_bytes(tasks))
    # Portable paths are relative to the constructed output root, not WD/WSL-specific.
    atomic_bytes(output / 'host_input_paths.txt', ('\n'.join((Path('assemblies') / a / (a + '.faa')).as_posix()
                                                            for a in accessions) + '\n').encode('utf-8'))
    write_tsv(output / 'assembly_input_counts.tsv', [{'assembly_accession': r['assembly_accession'], **r['metrics']} for r in completed],
              ['assembly_accession', *completed[0]['metrics'].keys()])
    atomic_bytes(output / 'construction_summary.json', json_bytes({
        'status': 'SOURCE_LOCUS_INPUTS_CONSTRUCTED', 'scientific_validation': 'NOT_RUN',
        'approved_assemblies': 196, 'constructed_assemblies': len(completed),
        'protein_bearing_loci': sum(r['metrics']['protein_bearing_loci'] for r in completed),
        'replicon_tasks': len(tasks), 'elapsed_seconds': time.monotonic() - started,
        'historical_failure_receipt_preserved': (output / 'construction_failure.json').exists(),
        'identity': identity, 'completed_at_utc': datetime.now(timezone.utc).isoformat(),
        'evidence_limit': 'Source-preserving parser construction only. No marker search, detector search or functional evidence.'}))


def self_test():
    from Bio.Seq import Seq
    from Bio.SeqFeature import SeqFeature, SimpleLocation, CompoundLocation
    from Bio.SeqRecord import SeqRecord
    accession, replicon = 'GCF_000000001.1', 'SYNTHETIC.1'
    record = SeqRecord(Seq('A' * 120), id=replicon, name='SYNTHETIC', description='Synthetic parser fixture')
    record.annotations = {'molecule_type': 'DNA', 'topology': 'circular'}
    record.dbxrefs = ['Assembly: ' + accession]
    def cds(locus, start, end, pid=None, translation=None, pseudo=False):
        q = {'locus_tag': [locus], 'codon_start': ['1'], 'transl_table': ['11']}
        if pid:
            q.update(protein_id=[pid], translation=[translation])
        if pseudo:
            q['pseudo'] = ['']
        return SeqFeature(SimpleLocation(start, end, strand=1), type='CDS', qualifiers=q)
    record.features = [cds('LOCUS_A', 0, 12, 'WP_SYNTHETIC.1', 'MKAA'),
                       cds('LOCUS_B', 15, 27, 'WP_SYNTHETIC.1', 'MKAA'),
                       cds('LOCUS_PSEUDO', 30, 42, pseudo=True),
                       SeqFeature(SimpleLocation(45, 54, strand=1), type='gene',
                                  qualifiers={'locus_tag': ['GENE_ONLY_PSEUDO'], 'pseudogene': ['unknown']})]
    wrapped = cds('LOCUS_WRAP', 105, 120, 'WP_WRAP.1', 'MKAA')
    wrapped.location = CompoundLocation([SimpleLocation(105, 120, strand=1), SimpleLocation(0, 9, strand=1)])
    record.features.append(wrapped)
    stream = io.StringIO()
    SeqIO.write([record], stream, 'genbank')
    gbff = stream.getvalue().encode('utf-8')
    faa = b'>WP_SYNTHETIC.1 source A\nMKAA\n>WP_SYNTHETIC.1 repeated source\nMKAA\n>WP_WRAP.1 source wrap\nMKAA\n'
    gff = ('##gff-version 3\n##sequence-region SYNTHETIC.1 1 120\n'
           'SYNTHETIC.1\tNCBI\tregion\t1\t120\t.\t+\t.\tID=region;Is_circular=true\n'
           'SYNTHETIC.1\tNCBI\tCDS\t1\t12\t.\t+\t0\tlocus_tag=LOCUS_A;protein_id=WP_SYNTHETIC.1\n'
           'SYNTHETIC.1\tNCBI\tCDS\t16\t27\t.\t+\t0\tlocus_tag=LOCUS_B;protein_id=WP_SYNTHETIC.1\n'
           'SYNTHETIC.1\tNCBI\tCDS\t31\t42\t.\t+\t0\tlocus_tag=LOCUS_PSEUDO;pseudo=true\n'
           'SYNTHETIC.1\tNCBI\tCDS\t106\t129\t.\t+\t0\tlocus_tag=LOCUS_WRAP;protein_id=WP_WRAP.1\n').encode('utf-8')
    loci, genes, replicons, metrics = derive_loci(accession, gbff, faa, gff)
    require(metrics['protein_bearing_loci'] == 3 and metrics['source_gbff_cds_loci'] == 4
            and metrics['gene_only_pseudogenes'] == 1, 'Synthetic locus counts failed')
    shared = [row for row in loci if row['protein_accession'] == 'WP_SYNTHETIC.1']
    require(len(shared) == 2 and shared[0]['locus_key'] != shared[1]['locus_key'], 'Repeated WP incorrectly collapsed loci')
    wrap = next(row for row in loci if row['locus_tag'] == 'LOCUS_WRAP')
    require(wrap['derived_linear_order_start_one_based'] == 106 and wrap['derived_linear_order_end_one_based'] == 129
            and wrap['origin_spanning'], 'Origin envelope incorrectly became whole replicon')
    require({row['defensefinder_target_id'] for row in loci if row['protein_target_present']}
            == {'DF00000001', 'DF00000002', 'DF00000003'}, 'DF ordinal mapping failed')
    rejected = []
    for name, broken_faa in [('conflicting_repeat', faa.replace(b'repeated source\nMKAA', b'repeated source\nMKTT')),
                             ('source_translation_mismatch', faa.replace(b'WP_WRAP.1 source wrap\nMKAA', b'WP_WRAP.1 source wrap\nMKTT')),
                             ('unmapped_primary_protein', faa + b'>WP_UNMAPPED.1\nMKAA\n')]:
        try:
            derive_loci(accession, gbff, broken_faa, gff)
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError('Malformed synthetic input accepted: ' + name)
    duplicate_record = record[:]
    duplicate_record.features = [*record.features, record.features[0]]
    duplicate_stream = io.StringIO()
    SeqIO.write([duplicate_record], duplicate_stream, 'genbank')
    try:
        derive_loci(accession, duplicate_stream.getvalue().encode(), faa, gff)
    except ValueError:
        rejected.append('duplicate_biological_locus')
    else:
        raise AssertionError('Duplicate synthetic biological locus accepted')
    try:
        derive_loci(accession, gbff, faa, gff.replace(b'Is_circular=true', b'Is_circular=false'))
    except ValueError:
        rejected.append('contradictory_source_topology')
    else:
        raise AssertionError('Contradictory synthetic source topology accepted')
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
        payload = {'gbff': gbff, 'protein': faa, 'gff': gff}
        expected_metrics = {'genomic_records': 1, 'gbff_cds_loci': 4, 'protein_fasta_records': 3,
                            'unique_protein_accessions': 2, 'pseudogene_cds': 1}
        _, _, files = build_assembly(accession, payload, {}, Path(folder), expected_metrics)
        require(files and (Path(folder) / 'primary_ncbi_protein.faa').read_bytes() == faa, 'Primary source bytes changed')
        targets = source_faa((Path(folder) / (accession + '.faa')).read_bytes())[0]
        require(len(targets) == 3 and len({r['protein_accession'] for r in targets}) == 3, 'Host targets not locus-unique')
    print(json.dumps({'status': 'PASS_SYNTHETIC_SOURCE_MAPPING_FIXTURES', 'biological_execution': 'NOT_RUN',
                      'fixtures': ['repeated_identical_WP_distinct_loci', 'untranslated_CDS_pseudogene',
                                   'gene_only_pseudogene', 'origin_spanning_order', 'DF_ordinal_crosswalk',
                                   'primary_FAA_bytes_preserved', *rejected]}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path)
    parser.add_argument('--validated-stage02-dir', type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        require(args.output and args.validated_stage02_dir, '--output and --validated-stage02-dir are required')
        production(args)
