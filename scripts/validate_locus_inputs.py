#!/usr/bin/env python3
"""Independent source traceability audit of the full196 locus-input construction.

Reads raw NCBI ZIP/catalog/GBFF/FAA/GFF and generated portable inputs. It does
not import the builder during production validation, predict sequences, search
markers, or run defense detectors. Synthetic tests alone call the producer to
construct fixtures and then corrupt outputs while updating checkpoint hashes.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
import time
from urllib.parse import unquote
import zipfile

import Bio
from Bio import SeqIO
from Bio.SeqFeature import ExactPosition

LOCUS_FIELDS = ['assembly_accession','replicon','locus_tag','locus_key','row_kind',
 'protein_accession','protein_target_present','protein_aa_length',
 'primary_faa_sequence_sha256','gbff_translation_sha256','primary_faa_record_ordinals',
 'primary_faa_headers','gbff_feature_ordinal','gbff_gene_feature_ordinals','gbff_location',
 'gbff_parts_zero_based_biological_order','gbff_strand','gbff_cds_pseudo','gbff_gene_pseudo',
 'source_pseudo_any','partial_or_fuzzy','codon_start','translation_table',
 'gbff_qualifiers_without_translation','source_gene_qualifiers','gff_source_lines',
 'gff_literal_segments_one_based','source_cds_ordinal_on_replicon','protein_ordinal_on_replicon',
 'padloc_target_id','padloc_gff_id','defensefinder_target_id',
 'derived_linear_order_start_one_based','derived_linear_order_end_one_based',
 'derived_gff_geometry','origin_spanning','requires_coordinate_review']
GENE_FIELDS = ['assembly_accession','replicon','locus_tag','locus_key',
 'gbff_feature_ordinal','gbff_feature_type','gbff_location','source_qualifiers']
COUNT_LINKS = {'genomic_records':'gbff_replicons','gbff_cds_loci':'source_gbff_cds_loci',
 'protein_fasta_records':'primary_faa_records','unique_protein_accessions':'primary_faa_unique_accessions',
 'pseudogene_cds':'gbff_pseudogene_cds_loci'}
LIMIT = ('Source sequence, locus and replicon traceability only. No host marker search, '
         'phylogenetic inference, defense detector result or functional validation.')


def check(condition, message):
    if not condition:
        raise ValueError(message)


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def csv_value(value):
    if value is None:
        return ''
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    return str(value)


def tsv_rows(path, expected_fields=None):
    with Path(path).open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream, delimiter='\t')
        check(reader.fieldnames and len(set(reader.fieldnames)) == len(reader.fieldnames),
              'Missing/duplicate TSV columns: ' + Path(path).name)
        if expected_fields is not None:
            check(reader.fieldnames == expected_fields, 'TSV column contract differs: ' + Path(path).name)
        rows = list(reader)
    check(all(None not in row and all(v is not None for v in row.values()) for row in rows),
          'TSV row width differs: ' + Path(path).name)
    return rows


def compare_tsv(path, expected, fields):
    actual = tsv_rows(path, fields)
    check(len(actual) == len(expected), 'TSV row count differs: ' + Path(path).name)
    for number, (row, source) in enumerate(zip(actual, expected), 1):
        for key in fields:
            check(row[key] == csv_value(source.get(key)),
                  f'Source/crosswalk differs: {path.name} row={number} field={key} locus={source.get("locus_key", "")}')


def qualifier(feature, key, default=None):
    values = feature.qualifiers.get(key, [])
    check(len(values) <= 1, 'Conflicting source qualifier: ' + key)
    return values[0] if values else default


def attrs(value):
    parsed = {}
    if value == '.':
        return parsed
    for pair in value.split(';'):
        if not pair:
            continue
        key, separator, item = pair.partition('=')
        check(separator and key and key not in parsed, 'Invalid/duplicate GFF attribute')
        parsed[key] = unquote(item)
    return parsed


def parse_gff(data):
    rows, intervals = [], {}
    for number, line in enumerate(data.decode('utf-8').splitlines(), 1):
        if line == '##FASTA':
            break
        if line.startswith('##sequence-region '):
            words = line.split()
            check(len(words) == 4 and words[1] not in intervals, 'Invalid/duplicate sequence-region')
            intervals[words[1]] = (int(words[2]), int(words[3]))
        if not line or line.startswith('#'):
            continue
        fields = line.split('\t')
        check(len(fields) == 9, 'GFF width differs at line ' + str(number))
        row = {'replicon':fields[0], 'source':fields[1], 'kind':fields[2],
               'start':int(fields[3]), 'end':int(fields[4]), 'score':fields[5],
               'strand':fields[6], 'phase':fields[7], 'attrs':attrs(fields[8]), 'line':number}
        check(1 <= row['start'] <= row['end'], 'Invalid GFF coordinates')
        rows.append(row)
    return rows, intervals


def parse_faa(data):
    text = data.decode('ascii')
    # SeqIO independently parses the builder's handwritten FASTA implementation.
    rows = list(SeqIO.parse(io.StringIO(text), 'fasta'))
    check(rows, 'Empty FASTA')
    check(all(str(r.seq) and set(str(r.seq)) <= set('ACDEFGHIKLMNPQRSTVWYBXZUOJ*') for r in rows),
          'Invalid primary protein characters')
    return [{'id':r.id, 'header':r.description, 'sequence':str(r.seq), 'ordinal':i}
            for i, r in enumerate(rows, 1)]


def raw_sources(zip_path, accession):
    roles = {'GENBANK_FLAT_FILE':'gbff','PROTEIN_FASTA':'protein','GFF3':'gff'}
    data, manifest = {}, {}
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        check(len(names) == len(set(names)), 'Duplicate raw ZIP entry')
        for name in names:
            path = PurePosixPath(name)
            check(not path.is_absolute() and '..' not in path.parts and '\\' not in name and ':' not in name,
                  'Unsafe raw ZIP member')
        check(archive.testzip() is None, 'Raw ZIP CRC failure')
        catalogs = [n for n in names if PurePosixPath(n).name == 'dataset_catalog.json']
        check(len(catalogs) == 1, 'Dataset catalog missing/ambiguous')
        catalog_name = catalogs[0]
        candidates = [a for a in json.loads(archive.read(catalog_name)).get('assemblies', [])
                      if a.get('accession') == accession]
        check(len(candidates) == 1, 'Exact accession/version absent/duplicate in catalog')
        for entry in candidates[0].get('files', []):
            role = roles.get(entry.get('fileType'))
            if role is None:
                continue
            check(role not in data, 'Duplicate source catalog role')
            name = entry['filePath']
            base = str(PurePosixPath(catalog_name).parent)
            choices = set(names) & {name, base+'/'+name, base+'/data/'+name, 'ncbi_dataset/data/'+name}
            check(len(choices) == 1, 'Source catalog member unresolved/ambiguous')
            member = next(iter(choices))
            check(accession in PurePosixPath(member).parts, 'Catalog source belongs to another assembly')
            payload = archive.read(member)
            check(payload and ('uncompressedLengthBytes' not in entry
                  or len(payload) == int(entry['uncompressedLengthBytes'])), 'Source member size differs')
            data[role] = payload
            manifest[role] = {'zip_member':member,'bytes':len(payload),'sha256':sha_bytes(payload)}
    check(set(data) == {'gbff','protein','gff'}, 'Source catalog role incomplete')
    return data, manifest


def coordinates(feature, gff_rows, length, circular):
    check(feature.location is not None, 'Missing source location')
    segments = list(feature.location.parts)
    check(segments and all(p.ref is None and p.ref_db is None for p in segments), 'Remote source location')
    check(all(0 <= int(p.start) < int(p.end) <= length for p in segments), 'Source feature outside replicon')
    strands = {p.strand for p in segments}
    check(len(strands) == 1 and next(iter(strands)) in (1,-1), 'Mixed/missing source strand')
    fuzzy = any(not isinstance(p.start, ExactPosition) or not isinstance(p.end, ExactPosition) for p in segments)
    high = [int(p.start)+1 for p in segments if int(p.end) == length]
    low = [int(p.end) for p in segments if int(p.start) == 0]
    overflow = [r for r in gff_rows if r['end'] > length]
    origin = bool(overflow or (circular and len(segments)>1 and high and low))
    if origin:
        check(circular and high and low, 'Undocumented/impossible origin-spanning feature')
        start = min(r['start'] for r in overflow) if overflow else min(high)
        end = max(r['end'] for r in overflow) if overflow else length+max(low)
        check(1 <= start <= length < end <= 2*length, 'Invalid origin envelope')
        kind = 'ORIGIN_SPANNING_UNROLLED_ENVELOPE_FOR_ORDER_ONLY'
    else:
        start, end = min(int(p.start) for p in segments)+1, max(int(p.end) for p in segments)
        kind = 'EXACT_SINGLE_SEGMENT' if len(segments)==1 else 'MULTIPART_ENVELOPE_FOR_ORDER_ONLY'
    return {'gbff_parts_zero_based_biological_order':[[int(p.start),int(p.end),p.strand] for p in segments],
            'gbff_strand':next(iter(strands)), 'partial_or_fuzzy':fuzzy, 'origin_spanning':origin,
            'derived_linear_order_start_one_based':start,'derived_linear_order_end_one_based':end,
            'derived_gff_geometry':kind, 'requires_coordinate_review':bool(origin or fuzzy or len(segments)>1)}


def source_truth(accession, data):
    proteins = parse_faa(data['protein'])
    by_pid = defaultdict(list)
    for protein in proteins:
        by_pid[protein['id']].append(protein)
    check(all(len({r['sequence'] for r in repeats}) == 1 for repeats in by_pid.values()),
          'Conflicting primary FAA duplicates')
    records = list(SeqIO.parse(io.StringIO(data['gbff'].decode('utf-8')), 'genbank'))
    check(records and len(records) == len({r.id for r in records}), 'Empty/duplicate source replicons')
    gff, regions = parse_gff(data['gff'])
    lengths = {r.id:len(r.seq) for r in records}
    check(regions == {rep:(1,length) for rep,length in lengths.items()}, 'Source GFF replicon intervals differ')
    check(all(r['replicon'] in lengths for r in gff), 'Source GFF refers to foreign replicon')
    parents = {}
    for row in gff:
        if row['kind'] in ('gene','pseudogene') and row['attrs'].get('ID'):
            key = (row['replicon'],row['attrs']['ID'])
            check(key not in parents, 'Ambiguous source GFF parent')
            parents[key] = row['attrs']
    cds_gff = defaultdict(list)
    for row in gff:
        if row['kind'] != 'CDS':
            continue
        parent_id = row['attrs'].get('Parent')
        check(not parent_id or ',' not in parent_id, 'Multiple source GFF CDS parents')
        locus = row['attrs'].get('locus_tag') or parents.get((row['replicon'],parent_id),{}).get('locus_tag')
        check(locus, 'Missing source GFF locus')
        cds_gff[(row['replicon'],locus)].append(row)
    loci, genes, reps, used = [], [], [], set()
    def is_pseudo(feature):
        return feature.type == 'pseudogene' or any(k in feature.qualifiers for k in ('pseudo','pseudogene'))
    for ordinal, record in enumerate(records,1):
        rep, length = record.id, len(record.seq)
        check([x.partition(':')[2].strip() for x in record.dbxrefs if x.startswith('Assembly:')] == [accession],
              'Source GBFF assembly version differs')
        topo = record.annotations.get('topology','unknown').lower()
        check(topo in ('linear','circular','unknown'), 'Unrecognized source topology')
        observations = [{'source_line':r['line'],'Is_circular':r['attrs']['Is_circular']} for r in gff
                        if r['replicon']==rep and r['kind']=='region' and 'Is_circular' in r['attrs']]
        check(all(o['Is_circular'].lower() in ('true','false') for o in observations), 'Unknown source circularity')
        check(topo=='unknown' or all((o['Is_circular'].lower()=='true') == (topo=='circular') for o in observations),
              'Source GBFF/GFF topology contradiction')
        circular = topo=='circular' or any(o['Is_circular'].lower()=='true' for o in observations)
        rep_meta = {'assembly_accession':accession,'replicon':rep,'gbff_record_ordinal':ordinal,
                    'replicon_directory':f'rep{ordinal:06d}','gbff_length':length,'gbff_topology':topo,
                    'gff_topology_observations':observations,'documented_circular':circular,
                    'defensefinder_requested_topology':'circular' if circular else 'linear'}
        grouped_genes = defaultdict(list)
        for index, feature in enumerate(record.features,1):
            if feature.type not in ('gene','pseudogene'):
                continue
            locus = qualifier(feature,'locus_tag')
            if not locus:
                continue
            grouped_genes[locus].append((index,feature))
            genes.append({'assembly_accession':accession,'replicon':rep,'locus_tag':locus,
                          'locus_key':'|'.join((accession,rep,locus)), 'gbff_feature_ordinal':index,
                          'gbff_feature_type':feature.type,'gbff_location':str(feature.location),
                          'source_qualifiers':feature.qualifiers})
        source_cds = set()
        for index, feature in enumerate(record.features,1):
            if feature.type != 'CDS':
                continue
            locus = qualifier(feature,'locus_tag')
            check(locus and locus not in source_cds, 'Missing/duplicate source CDS locus')
            source_cds.add(locus)
            q, key = feature.qualifiers, '|'.join((accession,rep,locus))
            linked = cds_gff.get((rep,locus),[])
            check(linked, 'Source CDS missing GFF representation')
            shape = coordinates(feature,linked,length,circular)
            pid, translation = qualifier(feature,'protein_id'), qualifier(feature,'translation')
            hits = by_pid.get(pid,[])
            pseudo_cds, pseudo_gene = is_pseudo(feature), any(is_pseudo(f) for _,f in grouped_genes[locus])
            check(pid or pseudo_cds or pseudo_gene, 'Source nonpseudo CDS missing primary protein')
            if pid:
                check(hits and translation == hits[0]['sequence'], 'Primary FAA/GBFF translation differs')
                sequence = hits[0]['sequence']
                used.add(pid)
            else:
                check(translation is None, 'Source translation missing primary protein mapping')
                sequence = None
            check({r['attrs']['protein_id'] for r in linked if r['attrs'].get('protein_id')} == ({pid} if pid else set()),
                  'Source GFF/GBFF protein mapping differs')
            check(all(r['strand'] == ('+' if shape['gbff_strand']==1 else '-') for r in linked),
                  'Source GFF strand differs')
            row = {'assembly_accession':accession,'replicon':rep,'locus_tag':locus,'locus_key':key,'row_kind':'CDS',
                   'protein_accession':pid,'protein_target_present':sequence is not None,
                   'protein_aa_length':len(sequence) if sequence is not None else None,
                   'primary_faa_sequence_sha256':sha_bytes(sequence.encode('ascii')) if sequence is not None else None,
                   'gbff_translation_sha256':sha_bytes(translation.encode('ascii')) if translation else None,
                   'primary_faa_record_ordinals':[r['ordinal'] for r in hits],
                   'primary_faa_headers':[r['header'] for r in hits], 'gbff_feature_ordinal':index,
                   'gbff_gene_feature_ordinals':[i for i,_ in grouped_genes[locus]],'gbff_location':str(feature.location),
                   'gbff_cds_pseudo':pseudo_cds,'gbff_gene_pseudo':pseudo_gene,'source_pseudo_any':pseudo_cds or pseudo_gene,
                   'codon_start':int(qualifier(feature,'codon_start','1')),
                   'translation_table':int(qualifier(feature,'transl_table','1')),
                   'gbff_qualifiers_without_translation':{k:v for k,v in q.items() if k!='translation'},
                   'source_gene_qualifiers':[f.qualifiers for _,f in grouped_genes[locus]],
                   'gff_source_lines':[r['line'] for r in linked],
                   'gff_literal_segments_one_based':[[r['start'],r['end'],r['strand'],r['phase']] for r in linked],
                   '_sequence':sequence,**shape}
            check(row['codon_start'] in (1,2,3), 'Invalid source codon_start')
            loci.append(row)
        for locus, features in grouped_genes.items():
            if locus in source_cds or not any(is_pseudo(f) for _,f in features):
                continue
            check(len(features)==1, 'Ambiguous gene-only pseudogene')
            index, feature = features[0]
            loci.append({'assembly_accession':accession,'replicon':rep,'locus_tag':locus,
                         'locus_key':'|'.join((accession,rep,locus)),'row_kind':'PSEUDOGENE_GENE_WITHOUT_CDS',
                         'protein_accession':None,'protein_target_present':False,'gbff_feature_ordinal':index,
                         'gbff_gene_feature_ordinals':[index],'gbff_location':str(feature.location),
                         'gbff_cds_pseudo':None,'gbff_gene_pseudo':True,'source_pseudo_any':True,
                         'source_gene_qualifiers':[feature.qualifiers],'_sequence':None,
                         **coordinates(feature,[],length,circular)})
        current = sorted((r for r in loci if r['replicon']==rep),
                         key=lambda r:(r['derived_linear_order_start_one_based'],r['gbff_feature_ordinal'],r['locus_tag']))
        cds_count = protein_count = 0
        for row in current:
            if row['row_kind']=='CDS':
                cds_count += 1
                row['source_cds_ordinal_on_replicon'] = cds_count
            if row['protein_target_present']:
                protein_count += 1
                row.update(protein_ordinal_on_replicon=protein_count,padloc_target_id=row['locus_key'],
                           padloc_gff_id='cds-'+row['locus_key'],defensefinder_target_id=f'DF{protein_count:08d}')
        rep_meta.update(source_cds_loci=cds_count,source_context_loci=len(current),primary_protein_targets=protein_count,
                        untranslated_source_loci=len(current)-protein_count,
                        origin_spanning_loci=sum(r['origin_spanning'] for r in current),
                        coordinate_review_loci=sum(r['requires_coordinate_review'] for r in current),
                        detector_task_eligibility='READY_PRIMARY_PROTEIN_TARGETS' if protein_count else 'NO_PRIMARY_PROTEIN_TARGETS_REVIEW')
        reps.append(rep_meta)
    check(used==set(by_pid), 'Unmapped primary FAA accession')
    check(set(cds_gff)=={(r['replicon'],r['locus_tag']) for r in loci if r['row_kind']=='CDS'}, 'Extra source GFF CDS')
    check(len(loci)==len({r['locus_key'] for r in loci}), 'Duplicate source context key')
    metrics = {'gbff_replicons':len(records),'source_gff_rows':len(gff),
               'source_gbff_cds_loci':sum(r['row_kind']=='CDS' for r in loci),'source_context_loci':len(loci),
               'primary_faa_records':len(proteins),'primary_faa_unique_accessions':len(by_pid),
               'protein_bearing_loci':sum(r['protein_target_present'] for r in loci),
               'gbff_pseudogene_cds_loci':sum(r.get('gbff_cds_pseudo') is True for r in loci),
               'gene_only_pseudogenes':sum(r['row_kind']!='CDS' for r in loci),
               'repeated_primary_faa_accessions':sum(len(hits)>1 for hits in by_pid.values())}
    return loci, genes, reps, metrics


def compare_faa(path, expected, key_field):
    actual = parse_faa(Path(path).read_bytes())
    check(len(actual)==len(expected), 'Detector/host FAA target count differs: '+Path(path).name)
    for index, (found, source) in enumerate(zip(actual,expected),1):
        check(found['id']==source[key_field] and found['header']==source[key_field]
              and found['sequence']==source['_sequence'],
              f'Detector/host FAA identity/order/sequence differs: {path.name} target={index}')


def compare_gff(path, rep, expected, key_field):
    rows, intervals = parse_gff(Path(path).read_bytes())
    check(intervals=={rep['replicon']:(1,rep['gbff_length'])}, 'Derived GFF replicon interval differs')
    check(len(rows)==len(expected), 'Derived GFF target count differs')
    for index, (row, locus) in enumerate(zip(rows,expected),1):
        expected_attrs = {'ID':locus[key_field],'locus_tag':locus['locus_tag'],
                          'protein_id':locus['protein_accession'],'source_locus_key':locus['locus_key'],
                          'source_geometry':locus['derived_gff_geometry'],
                          'source_origin_spanning':str(locus['origin_spanning']).lower(),
                          'source_pseudo':str(locus['source_pseudo_any']).lower()}
        check(row['replicon']==rep['replicon'] and row['source']=='NCBI_GBFF_DERIVED' and row['kind']=='CDS'
              and row['start']==locus['derived_linear_order_start_one_based']
              and row['end']==locus['derived_linear_order_end_one_based'] and row['score']=='.'
              and row['strand']==('+' if locus['gbff_strand']==1 else '-')
              and row['phase']==str(locus['codon_start']-1) and row['attrs']==expected_attrs,
              f'Derived GFF source geometry/ID/phase/order differs: {path.name} target={index}')


def checkpoint_files(folder, receipt):
    check(not folder.is_symlink() and not folder.is_junction(), 'Linked assembly directory')
    expected, total = set(), 0
    for entry in receipt['output_files']:
        relative = entry['path']
        portable = PurePosixPath(relative)
        check(not portable.is_absolute() and '..' not in portable.parts and '\\' not in relative and ':' not in relative,
              'Unsafe checkpoint path')
        check(relative not in expected and relative.lower() not in {p.lower() for p in expected},
              'Duplicate/case-colliding checkpoint path')
        expected.add(relative)
        file = folder / relative
        check(folder.resolve() in file.resolve().parents and file.is_file() and not file.is_symlink(),
              'Missing/escaped/symlink checkpoint file: '+relative)
        check(file.stat().st_size==entry['bytes'] and file_hash(file)==entry['sha256'],
              'Checkpoint byte/hash differs: '+relative)
        total += entry['bytes']
    actual = set()
    for file in folder.rglob('*'):
        check(not file.is_symlink() and not file.is_junction()
              and folder.resolve() in file.resolve().parents, 'Linked/escaped file inside generated assembly')
        if file.is_file() and file.relative_to(folder).as_posix() != 'build_receipt.json':
            actual.add(file.relative_to(folder).as_posix())
    check(actual==expected, 'Checkpoint file coverage differs')
    return len(expected), total


def validate_assembly(accession, zip_path, folder, stage02, identity):
    receipt = load_json(folder/'build_receipt.json')
    raw_hash = file_hash(zip_path)
    check(receipt.get('status')=='SOURCE_LOCUS_INPUTS_CONSTRUCTED'
          and receipt.get('scientific_validation')=='NOT_RUN'
          and receipt.get('assembly_accession')==accession and receipt.get('identity')==identity,
          'Failed/different assembly construction receipt')
    check(stage02.get('assembly_accession')==accession and stage02.get('error_count')==0
          and raw_hash==stage02.get('raw_zip_sha256')==receipt.get('raw_zip_sha256'),
          'Raw source hash/version differs from Stage 2 and checkpoint')
    file_count, file_bytes = checkpoint_files(folder, receipt)
    data, members = raw_sources(zip_path,accession)
    check(load_json(folder/'source_member_manifest.json')==members, 'Source member manifest differs')
    check((folder/'primary_ncbi_protein.faa').read_bytes()==data['protein'], 'Original primary FAA bytes changed')
    loci, genes, reps, metrics = source_truth(accession,data)
    check(receipt.get('metrics')==metrics, 'Receipt counts differ from independent raw source enumeration')
    for old, new in COUNT_LINKS.items():
        check(stage02['metrics'].get(old)==metrics[new], 'Independent Stage 2 source count differs: '+old)
    compare_tsv(folder/'locus_crosswalk.tsv',loci,LOCUS_FIELDS)
    compare_tsv(folder/'source_gene_features.tsv',genes,GENE_FIELDS)
    manifest = load_json(folder/'replicon_manifest.json')
    check(len(manifest)==len(reps), 'Replicon manifest count differs')
    ordered = []
    tasks = []
    for rep, published in zip(reps,manifest):
        for field, value in rep.items():
            check(published.get(field)==value, 'Source replicon manifest differs: '+rep['replicon']+' '+field)
        for field in ('topology_evidence_source','protein_order_basis','padloc_boundary_semantics'):
            check(isinstance(published.get(field),str) and bool(published[field].strip()), 'Missing replicon interpretation note')
        directory = folder/'replicons'/rep['replicon_directory']
        check(load_json(directory/'source_topology.json')==published, 'Replicon topology copy differs')
        current = sorted((r for r in loci if r['replicon']==rep['replicon']),
                         key=lambda r:(r['derived_linear_order_start_one_based'],r['gbff_feature_ordinal'],r['locus_tag']))
        compare_tsv(directory/'locus_crosswalk.tsv',current,LOCUS_FIELDS)
        targets = [r for r in current if r['protein_target_present']]
        ordered.extend(targets)
        if targets:
            compare_faa(directory/'padloc.faa',targets,'padloc_target_id')
            compare_faa(directory/'defensefinder.faa',targets,'defensefinder_target_id')
            compare_gff(directory/'padloc.gff',rep,targets,'padloc_gff_id')
            compare_gff(directory/'defensefinder.gff',rep,targets,'defensefinder_target_id')
        else:
            check(not any((directory/name).exists() for name in ('padloc.faa','padloc.gff','defensefinder.faa','defensefinder.gff')),
                  'Untranslated replicon has spurious detector input')
        tasks.append({**published,'assembly_directory':'assemblies/'+accession,
                      'replicon_path':'assemblies/'+accession+'/replicons/'+rep['replicon_directory']})
    compare_faa(folder/(accession+'.faa'),ordered,'locus_key')
    expected_files = {'primary_ncbi_protein.faa',accession+'.faa','locus_crosswalk.tsv','source_gene_features.tsv',
                      'source_member_manifest.json','replicon_manifest.json'}
    for rep in reps:
        prefix = 'replicons/'+rep['replicon_directory']+'/'
        expected_files |= {prefix+'source_topology.json',prefix+'locus_crosswalk.tsv'}
        if rep['primary_protein_targets']:
            expected_files |= {prefix+name for name in ('padloc.faa','padloc.gff','defensefinder.faa','defensefinder.gff')}
    check({entry['path'] for entry in receipt['output_files']}==expected_files, 'Generated file set differs from source topology/targets')
    return {'assembly_accession':accession,'status':'PASS_SOURCE_LOCUS_INPUT_TRACEABILITY',
            **metrics,'output_files_verified':file_count,'output_bytes_verified':file_bytes,
            'origin_spanning_loci':sum(r['origin_spanning_loci'] for r in reps),
            'coordinate_review_loci':sum(r['coordinate_review_loci'] for r in reps)}, tasks


def production(args):
    started = time.monotonic()
    root, inputs, stage02, out = args.root.resolve(), args.inputs.resolve(), args.stage02_dir.resolve(), args.output_dir.resolve()
    check(root in out.parents and not any(p in ('data','config','scripts') for p in out.relative_to(root).parts),
          'Audit output must be a dedicated derived directory inside this repository')
    check(out!=inputs and inputs not in out.parents and out!=stage02 and stage02 not in out.parents,
          'Audit reports must be separate from source and generated inputs')
    panel_path = root/'config/approved_accessions.txt'
    panel = panel_path.read_text(encoding='ascii').split()
    check(len(panel)==len(set(panel))==196 and all(re.fullmatch(r'GCF_[0-9]{9}\.[0-9]+',a) for a in panel), 'Exact full196 panel required')
    approval, summary = load_json(root/'config/approval.json'), load_json(stage02/'validation_summary.json')
    panel_sha = file_hash(panel_path)
    check(approval.get('approved_assembly_count')==196 and approval.get('pilot') is False
          and approval.get('human_approval')=='APPROVED_FOR_SEQUENCE_ANALYSIS'
          and approval.get('panel_accessions_sha256')==panel_sha, 'Full196 approval differs')
    check(summary.get('status')=='PASS_SEQUENCE_INTEGRITY_WITH_DOCUMENTED_EXCEPTIONS'
          and summary.get('approved_assemblies')==summary.get('assemblies_reported')==196
          and summary.get('error_count')==summary.get('assemblies_with_errors')==0
          and summary.get('complete_exact196_accounting') is True
          and summary.get('approved_accessions_sha256')==panel_sha, 'Independent full196 Stage 2 gate failed')
    identity = load_json(inputs/'builder_identity.json')
    check(identity.get('panel_sha256')==panel_sha
          and identity.get('stage02_validation_summary_sha256')==file_hash(stage02/'validation_summary.json')
          and identity.get('builder_source_sha256')==file_hash(args.builder_script)
          and identity.get('python_version')==sys.version.split()[0]
          and identity.get('biopython_version')==Bio.__version__, 'Builder provenance differs from current source/gate/environment')
    construct = load_json(inputs/'construction_summary.json')
    check(construct.get('status')=='SOURCE_LOCUS_INPUTS_CONSTRUCTED' and construct.get('scientific_validation')=='NOT_RUN'
          and construct.get('identity')==identity and construct.get('approved_assemblies')==construct.get('constructed_assemblies')==196,
          'Full196 construction is incomplete/failed')
    actual_assemblies = [p.name for p in (inputs/'assemblies').iterdir() if p.is_dir()]
    check(set(actual_assemblies)==set(panel), 'Unexpected/missing constructed assembly directory')
    raw_root = (args.raw_root or root/'data/raw_ncbi').resolve()
    outcomes, tasks = [], []
    for index, accession in enumerate(panel,1):
        try:
            outcome, assembly_tasks = validate_assembly(accession,raw_root/accession/(accession+'.ncbi.zip'),
                inputs/'assemblies'/accession,load_json(stage02/'assemblies'/accession/'validation.json'),identity)
            tasks.extend(assembly_tasks)
        except Exception as error:
            outcome = {'assembly_accession':accession,'status':'FAIL','error':str(error)}
        outcomes.append(outcome)
        print(f'{index}/196 {accession} {outcome["status"]}',flush=True)
    failures = [r for r in outcomes if r['status']=='FAIL']
    global_errors = []
    if not failures:
        try:
            check(load_json(inputs/'detector_task_manifest.json')==tasks, 'Global detector task manifest differs from per-replicon source joins')
            check((inputs/'host_input_paths.txt').read_text(encoding='utf-8').splitlines()
                  == ['assemblies/'+a+'/'+a+'.faa' for a in panel], 'Host input path order/membership differs')
            counts = tsv_rows(inputs/'assembly_input_counts.tsv')
            check(len(counts)==196, 'Global input count rows differ')
            for published, source in zip(counts,outcomes):
                check(published.get('assembly_accession')==source['assembly_accession'], 'Global input count assembly order differs')
                for field in COUNT_LINKS.values():
                    check(published.get(field)==str(source[field]), 'Global input source count differs: '+field)
                for field in ('source_gff_rows','source_context_loci','protein_bearing_loci','gene_only_pseudogenes','repeated_primary_faa_accessions'):
                    check(published.get(field)==str(source[field]), 'Global input source count differs: '+field)
            check(construct.get('protein_bearing_loci')==sum(r['protein_bearing_loci'] for r in outcomes)
                  and construct.get('replicon_tasks')==len(tasks), 'Construction summary totals differ')
        except Exception as error:
            global_errors.append(str(error))
    report = {'status':'PASS_SOURCE_LOCUS_INPUT_TRACEABILITY' if not failures and not global_errors else 'FAIL',
              'completed_at_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-started,
              'required_assemblies':196,'assemblies_audited':len(outcomes),'assemblies_passed':196-len(failures),
              'failed_assemblies':failures,'global_errors':global_errors,'complete_exact196_accounting':len(outcomes)==196,
              'panel_sha256':panel_sha,'builder_identity':identity,'validator_source_sha256':file_hash(__file__),
              'python_version':sys.version.split()[0],'biopython_version':Bio.__version__,'evidence_limit':LIMIT}
    if not failures:
        for field in ('source_gbff_cds_loci','source_context_loci','protein_bearing_loci','gene_only_pseudogenes',
                      'gbff_replicons','output_files_verified','output_bytes_verified','origin_spanning_loci','coordinate_review_loci'):
            report[field] = sum(r[field] for r in outcomes)
    save_json(out/'validation_summary.json',report)
    save_json(out/'assembly_audit.json',outcomes)
    check(report['status']=='PASS_SOURCE_LOCUS_INPUT_TRACEABILITY', 'Independent source locus audit failed; see preserved reports')
    print(json.dumps(report,indent=2),flush=True)


def synthetic_tests(args):
    from Bio.Seq import Seq
    from Bio.SeqFeature import SeqFeature, SimpleLocation, CompoundLocation
    from Bio.SeqRecord import SeqRecord
    spec = importlib.util.spec_from_file_location('synthetic_fixture_producer',args.builder_script)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    accession = 'GCF_000000001.1'
    dna = list('A'*120)
    normal = 'ATGAAAAAATAA'
    for start,strand in [(15,1),(30,1),(45,-1)]:
        dna[start:start+12] = str(Seq(normal).reverse_complement()) if strand==-1 else normal
    dna[105:120],dna[0:3] = list('GTG'+'AAA'*4),list('TAA')
    first = SeqRecord(Seq(''.join(dna)),id='SYNTH1.1',name='SYNTH1',description='Synthetic source preservation fixture')
    first.annotations = {'molecule_type':'DNA','topology':'circular'}
    first.dbxrefs = ['Assembly: '+accession]
    first.features = [SeqFeature(SimpleLocation(0,120),type='source',qualifiers={'organism':['synthetic fixture']})]
    def pair(locus,start,end,strand=1,pid='WP_SHARED.1',translation='MKK',pseudo=False,parts=None):
        loc = CompoundLocation(parts) if parts else SimpleLocation(start,end,strand=strand)
        gene_q,cds_q = {'locus_tag':[locus]},{'locus_tag':[locus],'codon_start':['1'],'transl_table':['11']}
        if pseudo:
            gene_q['pseudo'],cds_q['pseudo'] = [''],['']
        if pid:
            cds_q.update(protein_id=[pid],translation=[translation])
        first.features.extend([SeqFeature(loc,type='gene',qualifiers=gene_q),SeqFeature(loc,type='CDS',qualifiers=cds_q)])
    pair('A',15,27)
    pair('B',30,42)
    pair('MINUS',45,57,-1)
    first.features.append(SeqFeature(SimpleLocation(60,72,strand=1),type='gene',qualifiers={'locus_tag':['PSEUDO_GENE'],'pseudogene':['unknown']}))
    pair('PSEUDO_CDS',75,87,pid=None,translation=None,pseudo=True)
    pair('WRAP',105,120,pid='WP_WRAP.1',translation='MKKKK',parts=[SimpleLocation(105,120,strand=1),SimpleLocation(0,3,strand=1)])
    second = SeqRecord(Seq('A'*20),id='SYNTH2.1',name='SYNTH2',description='Synthetic no-protein replicon')
    second.annotations = {'molecule_type':'DNA','topology':'linear'}
    second.dbxrefs = ['Assembly: '+accession]
    second.features = [SeqFeature(SimpleLocation(0,20),type='source',qualifiers={'organism':['synthetic fixture']})]
    stream = io.StringIO()
    SeqIO.write([first,second],stream,'genbank')
    data = {'gbff':stream.getvalue().encode('utf-8'),
            'protein':b'>WP_SHARED.1 primary first\nMKK\n>WP_SHARED.1 repeated identical\nMKK\n>WP_WRAP.1 circular wrap\nMKKKK\n',
            'gff':('##gff-version 3\n##sequence-region SYNTH1.1 1 120\n##sequence-region SYNTH2.1 1 20\n'
                   'SYNTH1.1\tNCBI\tregion\t1\t120\t.\t+\t.\tID=r1;Is_circular=true\n'
                   'SYNTH2.1\tNCBI\tregion\t1\t20\t.\t+\t.\tID=r2;Is_circular=false\n'
                   'SYNTH1.1\tNCBI\tCDS\t16\t27\t.\t+\t0\tlocus_tag=A;protein_id=WP_SHARED.1\n'
                   'SYNTH1.1\tNCBI\tCDS\t31\t42\t.\t+\t0\tlocus_tag=B;protein_id=WP_SHARED.1\n'
                   'SYNTH1.1\tNCBI\tCDS\t46\t57\t.\t-\t0\tlocus_tag=MINUS;protein_id=WP_SHARED.1\n'
                   'SYNTH1.1\tNCBI\tCDS\t76\t87\t.\t+\t0\tlocus_tag=PSEUDO_CDS;pseudo=true\n'
                   'SYNTH1.1\tNCBI\tCDS\t106\t123\t.\t+\t0\tlocus_tag=WRAP;protein_id=WP_WRAP.1\n').encode('utf-8')}
    fixture_metrics = {'genomic_records':2,'gbff_cds_loci':5,'protein_fasta_records':3,'unique_protein_accessions':2,'pseudogene_cds':1}
    results = []
    args.output_dir.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='synthetic_locus_',dir=args.output_dir) as temporary:
        base = Path(temporary)
        zip_path = base/(accession+'.ncbi.zip')
        catalog = {'assemblies':[{'accession':accession,'files':[]}]}
        types = {'gbff':'GENBANK_FLAT_FILE','protein':'PROTEIN_FASTA','gff':'GFF3'}
        members = {}
        with zipfile.ZipFile(zip_path,'w') as archive:
            for role,payload in data.items():
                member = 'ncbi_dataset/data/'+accession+'/source.'+role
                archive.writestr(member,payload)
                catalog['assemblies'][0]['files'].append({'fileType':types[role],'filePath':accession+'/source.'+role,'uncompressedLengthBytes':len(payload)})
                members[role] = {'zip_member':member,'bytes':len(payload),'sha256':sha_bytes(payload)}
            archive.writestr('ncbi_dataset/data/dataset_catalog.json',json.dumps(catalog))
        original = base/'original'
        metrics,reps,files = builder.build_assembly(accession,data,members,original,fixture_metrics)
        identity = {'fixture':'synthetic_only'}
        receipt = {'status':'SOURCE_LOCUS_INPUTS_CONSTRUCTED','scientific_validation':'NOT_RUN','identity':identity,
                   'assembly_accession':accession,'raw_zip_sha256':file_hash(zip_path),'metrics':metrics,'output_files':files}
        save_json(original/'build_receipt.json',receipt)
        gate = {'assembly_accession':accession,'error_count':0,'raw_zip_sha256':file_hash(zip_path),'metrics':fixture_metrics}
        result,_ = validate_assembly(accession,zip_path,original,gate,identity)
        check(result['protein_bearing_loci']==4 and result['source_context_loci']==6 and result['gbff_replicons']==2,
              'Synthetic positive counts unexpected')
        results.append({'case':'repeated_WP_distinct_loci_minus_strand_origin_and_no_protein_replicon','expected':'PASS','observed':'PASS'})
        def replace_file(folder,relative,old,new):
            path = folder/relative
            content = path.read_bytes()
            check(old in content,'Synthetic mutation target missing')
            path.write_bytes(content.replace(old,new,1))
        def change_topology(folder):
            path = folder/'replicon_manifest.json'
            changed = load_json(path)
            changed[0]['documented_circular'] = False
            changed[0]['defensefinder_requested_topology'] = 'linear'
            save_json(path,changed)
            save_json(folder/'replicons/rep000001/source_topology.json',changed[0])
        def collapse_wp(folder):
            path = folder/(accession+'.faa')
            records = path.read_text().splitlines()
            path.write_text('\n'.join(records[:2]+records[4:])+'\n',encoding='ascii')
        def reorder_df(folder):
            path = folder/'replicons/rep000001/defensefinder.faa'
            lines = path.read_text().splitlines()
            path.write_text('\n'.join(lines[2:4]+lines[:2]+lines[4:])+'\n',encoding='ascii')
        def delete_context(folder):
            path = folder/'replicons/rep000001/locus_crosswalk.tsv'
            lines = path.read_text(encoding='utf-8').splitlines()
            path.write_text('\n'.join(line for line in lines if '|PSEUDO_GENE\t' not in line)+'\n',encoding='utf-8')
        def changed_part_order(folder):
            path = folder/'locus_crosswalk.tsv'
            rows = tsv_rows(path,LOCUS_FIELDS)
            wrap = next(r for r in rows if r['locus_tag']=='WRAP')
            wrap['gbff_parts_zero_based_biological_order'] = '[[0,3,1],[105,120,1]]'
            with path.open('w',encoding='utf-8',newline='') as stream:
                writer = csv.DictWriter(stream,fieldnames=LOCUS_FIELDS,delimiter='\t',lineterminator='\n')
                writer.writeheader();writer.writerows(rows)
        mutations = [
            ('host_sequence_mutation',lambda f:replace_file(f,accession+'.faa',b'\nMKK\n',b'\nMKT\n')),
            ('WP_locus_collapse',collapse_wp),('DF_order_changed',reorder_df),
            ('PADLOC_coordinate_changed',lambda f:replace_file(f,'replicons/rep000001/padloc.gff',b'\t16\t27\t',b'\t17\t27\t')),
            ('PADLOC_strand_changed',lambda f:replace_file(f,'replicons/rep000001/padloc.gff',b'\t46\t57\t.\t-',b'\t46\t57\t.\t+')),
            ('DF_crosswalk_ID_changed',lambda f:replace_file(f,'replicons/rep000001/defensefinder.gff',b'ID=DF00000001',b'ID=DF00000009')),
            ('wrong_topology',change_topology),('lost_gene_only_pseudogene',delete_context),
            ('changed_join_part_order',changed_part_order),
            ('primary_source_header_changed',lambda f:replace_file(f,'primary_ncbi_protein.faa',b'primary first',b'primary other')),
            ('foreign_replicon_GFF',lambda f:replace_file(f,'replicons/rep000001/defensefinder.gff',b'\nSYNTH1.1\t',b'\nSYNTH2.1\t')),
            ('wrong_locus_key',lambda f:replace_file(f,'replicons/rep000001/padloc.faa',b'|SYNTH1.1|A\n',b'|SYNTH1.1|B\n')),
            ('untranslated_replicon_spurious_input',lambda f:(f/'replicons/rep000002/padloc.faa').write_bytes(b'>fake\nMKK\n')),
        ]
        for name,mutation in mutations:
            folder = base/name
            shutil.copytree(original,folder)
            mutation(folder)
            changed_receipt = load_json(folder/'build_receipt.json')
            changed_receipt['output_files'] = [{'path':p.relative_to(folder).as_posix(),'bytes':p.stat().st_size,'sha256':file_hash(p)}
                for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='build_receipt.json']
            save_json(folder/'build_receipt.json',changed_receipt)
            try:
                validate_assembly(accession,zip_path,folder,gate,identity)
            except ValueError as error:
                results.append({'case':name,'expected':'REJECT','observed':'REJECT','error':str(error)})
            else:
                raise AssertionError('Corrupted source-derived fixture accepted: '+name)
        wrong_gate = {**gate,'raw_zip_sha256':'0'*64}
        try:
            validate_assembly(accession,zip_path,original,wrong_gate,identity)
        except ValueError as error:
            results.append({'case':'raw_checkpoint_source_hash_mismatch','expected':'REJECT','observed':'REJECT','error':str(error)})
        else:
            raise AssertionError('Wrong Stage 2 raw source hash accepted')
    report = {'status':'PASS_SYNTHETIC_INDEPENDENT_LOCUS_CHECKS','tests':len(results),'cases':results,
              'checkpoint_hashes_refreshed_after_content_mutations':True,'biological_execution':'NOT_RUN',
              'validator_source_sha256':file_hash(__file__),'builder_fixture_source_sha256':file_hash(args.builder_script)}
    save_json(args.output_dir/'synthetic_tests.json',report)
    print(json.dumps(report,indent=2),flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--inputs',type=Path)
    parser.add_argument('--stage02-dir',type=Path)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--raw-root',type=Path)
    parser.add_argument('--builder-script',type=Path,default=Path('scripts/build_locus_inputs.py'))
    parser.add_argument('--self-test-only',action='store_true')
    args = parser.parse_args()
    if args.self_test_only:
        synthetic_tests(args)
    else:
        check(args.inputs is not None and args.stage02_dir is not None,'--inputs and --stage02-dir required')
        try:
            production(args)
        except Exception as error:
            save_json(args.output_dir/'execution_failure.json',{'status':'FAILED','error':str(error),
                      'outputs_preserved':True,'evidence_limit':LIMIT})
            raise


if __name__=='__main__':
    main()
