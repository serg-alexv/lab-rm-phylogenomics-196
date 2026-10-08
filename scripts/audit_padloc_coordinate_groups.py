"""Audit all196 actual source geometries; no detector search or system call."""
from pathlib import Path
from collections import defaultdict
import csv, hashlib, json, os, time
import stage04_controller as C
import production_resume as w
from workflow_publication import commit

ROOT=Path(__file__).resolve().parents[1]
HISTORY=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
OUT=ROOT/'reports/stage05/preparation_coordinate_audit'
w.LOG=OUT/'commands.jsonl'

def main():
    with C.WorkflowLock(HISTORY/'.work/workflow.lock'):
        C.reconcile(ROOT);start=time.monotonic();cpu=time.process_time()
        panel=(ROOT/'config/approved_accessions.txt').read_text().split()
        C.check(len(panel)==len(set(panel))==196 and C.digest(ROOT/'config/approved_accessions.txt')=='85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6','Exact196 required')
        source=ROOT/'.work/source_locus_inputs_v1/assemblies'
        total_context=total_targets=0;collisions=[];by_assembly=[]
        for accession in panel:
            directory=source/accession;path=directory/'locus_crosswalk.tsv'
            receipt=C.load(directory/'build_receipt.json')
            expected=[r for r in receipt['output_files'] if r['path']=='locus_crosswalk.tsv']
            C.check(len(expected)==1 and C.digest(path)==expected[0]['sha256'] and path.stat().st_size==expected[0]['bytes'],
                    'Frozen source crosswalk changed: '+accession)
            groups=defaultdict(list);keys=set();count=targets=0
            with path.open(encoding='utf-8',newline='') as stream:
                for row in csv.DictReader(stream,delimiter='\t'):
                    key=row['locus_key'];C.check(row['assembly_accession']==accession and key not in keys,
                                                'Actual source locus duplicate or assembly mismatch')
                    keys.add(key);count+=1
                    C.check(key=='|'.join([accession,row['replicon'],row['locus_tag']]),'Locus key changed')
                    C.check(row['protein_target_present'] in ('True','False'),'Nonliteral source target flag')
                    if row['protein_target_present']=='False':continue
                    targets+=1;start_pos=int(row['derived_linear_order_start_one_based']);end_pos=int(row['derived_linear_order_end_one_based'])
                    C.check(1<=start_pos<=end_pos,'Invalid actual derived PADLOC geometry')
                    groups[(row['replicon'],start_pos,end_pos)].append(row)
            C.check(count==receipt['metrics']['source_context_loci'] and targets==receipt['metrics']['protein_bearing_loci'],
                    'Actual source counts differ from frozen construction')
            collision_count=0
            for (replicon,lo,hi),rows in groups.items():
                if len(rows)<2:continue
                collision_count+=1
                for row in rows:
                    collisions.append({'assembly_accession':accession,'replicon':replicon,'padloc_start':lo,'padloc_end':hi,
                        'coincident_loci':len(rows),'locus_key':row['locus_key'],'protein_accession':row['protein_accession'],
                        'strand':row['gbff_strand'],'protein_aa_length':row['protein_aa_length'],
                        'source_pseudo_any':row['source_pseudo_any'],'partial_or_fuzzy':row['partial_or_fuzzy'],
                        'origin_spanning':row['origin_spanning'],'source_aa_sha256':row['primary_faa_sequence_sha256'],
                        'interpretation':'NATIVE_COORDINATE_GROUP_COLLISION_REVIEW_REQUIRED; locus IDs retained, no RM state inferred'})
            by_assembly.append({'assembly_accession':accession,'source_context_loci':count,'protein_targets':targets,
                                'native_coordinate_groups':len(groups),'coincident_coordinate_groups':collision_count,
                                'source_crosswalk_sha256':C.digest(path)})
            total_context+=count;total_targets+=targets
        C.check(total_context==411523 and total_targets==398537,'Full production source totals differ')
        OUT.mkdir(parents=True,exist_ok=True)
        for name,rows,columns in [
            ('assembly_geometry_audit.tsv',by_assembly,list(by_assembly[0])),
            ('coincident_locus_coordinates.tsv',collisions,['assembly_accession','replicon','padloc_start','padloc_end','coincident_loci',
                'locus_key','protein_accession','strand','protein_aa_length','source_pseudo_any','partial_or_fuzzy','origin_spanning',
                'source_aa_sha256','interpretation'])]:
            import io
            buffer=io.StringIO();writer=csv.DictWriter(buffer,columns,delimiter='\t',lineterminator='\n')
            writer.writeheader();writer.writerows(rows);w.atomic(OUT/name,buffer.getvalue().encode())
        summary={'status':'PASS_ACTUAL_FULL196_SOURCE_GEOMETRY_AUDIT_ONLY','utc':w.now(),'actual_pid':os.getpid(),
                 'approved_assemblies':196,'source_context_loci':total_context,'protein_targets':total_targets,
                 'coincident_coordinate_groups':sum(r['coincident_coordinate_groups'] for r in by_assembly),
                 'affected_loci':len(collisions),'elapsed_seconds':time.monotonic()-start,'process_cpu_seconds':time.process_time()-cpu,
                 'peak_rss_bytes':None,'measurement_limit':'Windows process peak RSS not sampled for this serial TSV/hash audit',
                 'source_audit_script_sha256':C.digest(__file__),'stage05_native_searches':'NOT_RUN','curated_rm_states':'NOT_RUN',
                 'validation_scope':'Source geometry/count/hash evidence for curation implementation; not detector or biological completion',
                 'source_geometry_basis':'Exact source-derived PADLOC GFF start/end fields; native grouping ignores strand and locus key'}
        w.js(OUT/'summary.json',summary)
        w.atomic(OUT/'REPORT.md',
                 ('# Executed full196 PADLOC geometry review input\n\n'
                  'The serial reader checked every frozen source crosswalk hash and all411523 locus keys/context rows, including398537 protein targets. Native PADLOC2 selection groups by sequence/start/end within a model; locus IDs remain distinct evidence keys. The tables report actual coincident coordinates for review, without changing inputs or claiming any R-M system.\n\n'
                  'Coincident groups: '+str(summary['coincident_coordinate_groups'])+'; affected loci: '+str(len(collisions))+'. No PADLOC or DefenseFinder biological job was run. This preparation audit cannot establish detection, nondetection, completeness or function. Subsequent native equivalence/curated review and independent784-cell validation remain required.\n').encode())
        paths=['scripts/audit_padloc_coordinate_groups.py']+[p.relative_to(ROOT).as_posix() for p in OUT.iterdir() if p.is_file()]
        head=commit(paths,'Audit actual full196 source coordinate groups while preserving separate locus keys')
        print(json.dumps({**summary,'publication_commit':head}),flush=True)

if __name__=='__main__':main()
