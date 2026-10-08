#!/usr/bin/env python3
"""Read-only compact/accounting and extracted-byte audit after sequence validation."""
import argparse
from collections import Counter,defaultdict
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import time


def require(value,message):
    if not value:
        raise ValueError(message)


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def rows(path):
    with path.open(encoding='utf-8',newline='') as stream:
        return list(csv.DictReader(stream,delimiter='\t'))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path.cwd())
    p.add_argument('--validated',type=Path,default=Path('.work/stage02_validated'))
    p.add_argument('--output',type=Path,default=Path('.work/review2/full196_independent_audit.json'))
    a=p.parse_args();started=time.monotonic()
    panelpath=a.root/'config/approved_accessions.txt'
    panel=panelpath.read_text().split()
    require(len(panel)==len(set(panel))==196,'Exact196 panel required')
    summary=json.loads((a.validated/'validation_summary.json').read_text())
    require(summary['approved_accessions_sha256']==sha(panelpath),'Approved panel hash differs')
    require(summary['validator_source_sha256']==sha(a.root/'scripts/validate_sequences.py'),'Validator source hash differs')
    qc=rows(a.validated/'assembly_qc.tsv');errors=rows(a.validated/'errors.tsv')
    reviews=rows(a.validated/'review_exceptions.tsv');reps=rows(a.validated/'replicon_qc.tsv')
    members=rows(a.validated/'member_sha256.tsv')
    require([r['assembly_accession'] for r in qc]==panel,'QC approved order/membership differs')
    require(all(r['status']=='PASS_SEQUENCE_INTEGRITY_WITH_DOCUMENTED_EXCEPTIONS' and r['error_count']=='0' for r in qc)
            and not errors and summary['error_count']==0,'Sequence integrity errors present')
    require(dict(Counter(r['code'] for r in reviews))==summary['exception_counts'],'Exception accounting differs')
    grouped=defaultdict(list)
    for row in reps:grouped[row['assembly_accession']].append(row)
    require(set(grouped)==set(panel),'Replicon approved membership differs')
    for row in qc:
        per=grouped[row['assembly_accession']]
        require(len(per)==int(row['genomic_records']) and sum(int(r['length']) for r in per)==int(row['total_bases']),
                'Replicon count/length differs from assembly QC')
        require(len(per)==len({r['replicon'] for r in per}),'Duplicate replicon ID')
    expected=defaultdict(set);byte_count=0
    for row in members:
        accession=row['assembly_accession'];require(accession in panel,'Unknown member assembly')
        name=row['member'];require(name not in expected[accession],'Duplicate extracted member')
        expected[accession].add(name)
        package=a.root/'data/raw_ncbi'/accession/'package';path=package/name
        require(package.resolve() in path.resolve().parents and not path.is_symlink() and not path.is_junction(), 'Unsafe extracted member path')
        require(path.is_file() and path.stat().st_size==int(row['bytes']) and sha(path)==row['sha256'], 'Extracted member byte/hash mismatch')
        byte_count+=int(row['bytes'])
    for accession in panel:
        package=a.root/'data/raw_ncbi'/accession/'package'
        actual={f.relative_to(package).as_posix() for f in package.rglob('*') if f.is_file()}
        require(actual==expected[accession],'Unexpected/missing extracted package file')
    compact_elapsed=time.monotonic()-started;locus_started=time.monotonic()
    loci=set();counts=Counter();translations=Counter();protein_count=0
    with (a.validated/'locus_protein_map.tsv').open(encoding='utf-8',newline='') as stream:
        for row in csv.DictReader(stream,delimiter='\t'):
            key=row['locus_key'];acc=row['assembly_accession']
            require(acc in panel and key=='|'.join((acc,row['replicon'],row['locus_tag'])) and key not in loci,
                    'Duplicate/incorrect exact locus key')
            loci.add(key);counts[acc]+=1;protein_count+=bool(row['protein_accession'])
            translations[row['computed_translation_check']]+=1
    require(set(counts)==set(panel),'Locus table approved membership differs')
    for row in qc:require(counts[row['assembly_accession']]==int(row['gbff_cds_loci']),'Locus count differs from assembly QC')
    require(len(loci)==summary['locus_map_rows_written'],'Locus count differs from validation summary')
    require(set(translations)<={'MATCH','DOCUMENTED_EXCEPTION','MATCH_PARTIAL_UNKNOWN_TERMINAL_OMITTED','MATCH_PARTIAL_TERMINAL_CODON'},
            'Unexpected translation integrity state')
    report={'status':'PASS_READ_ONLY_FULL196_ACCOUNTING_AND_EXTRACTED_BYTES',
            'completed_at_utc':datetime.now(timezone.utc).isoformat(),
            'command':'python audit_stage02_accounting.py --root . --validated .work/stage02_validated --output .work/review2/full196_independent_audit.json',
            'audit_source_sha256':sha(Path(__file__)), 'validation_summary_sha256':sha(a.validated/'validation_summary.json'),
            'validator_source_sha256':summary['validator_source_sha256'],'approved_panel_sha256':sha(panelpath),
            'exact_approved_assembly_rows':len(qc),'error_rows':len(errors),'review_exception_rows':len(reviews),
            'exception_counts':dict(Counter(r['code'] for r in reviews)),'replicon_rows':len(reps),'member_rows':len(members),
            'verified_extracted_member_bytes':byte_count,'unexpected_extracted_files':0,'exact_unique_locus_keys':len(loci),
            'protein_bearing_loci':protein_count,'computed_translation_states':dict(translations),
            'compact_and_extracted_member_elapsed_seconds':compact_elapsed,
            'locus_accounting_elapsed_seconds':time.monotonic()-locus_started,
            'evidence_limit':'Independent accounting and extracted byte hashes after full sequence validation; no ANI, marker, defense or functional certification.'}
    a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    markdown=(f'Full196 independent Stage2 audit passed. All 196 approved assemblies, {len(reps):,} replicons, '
              f'{len(members):,} extracted members and {len(loci):,} unique assembly|replicon|locus keys were accounted for. '
              f'{byte_count:,} extracted bytes matched their recorded SHA256 and file sets; no extra files or error rows were found. '
              f'{protein_count:,} loci carry primary proteins. The {len(reviews):,} documented exception rows match the sequence-validation summary.\n\n'
              'Checks independently read TSV/JSON accounting and raw extracted member bytes. Locus identity, uniqueness, per-assembly counts, '
              'replicon length sums, panel hash and validator source hash were verified. Translation states are preserved, including documented '
              'exceptions and partial terminal codon handling. This audit does not certify ANI, marker orthology, defense calls or function.\n\n'
              'Command: `'+report['command']+'`\n')
    a.output.with_suffix('.md').write_text(markdown,encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
