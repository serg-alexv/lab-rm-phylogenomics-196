#!/usr/bin/env python3
import argparse, csv, hashlib, json, pathlib, re
p=argparse.ArgumentParser()
p.add_argument('--project',type=pathlib.Path,default=pathlib.Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196'))
p.add_argument('--bundle',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parent.parent/'pilot_itol_labels01')
a=p.parse_args(); out=a.project/'pipeline_output/itol_annotations/itol_taxonomic_group_strip.txt'
mapping=a.project/'pipeline_output/itol_annotations/cell_mapping.tsv'; legend=a.bundle/'color_legend.tsv'
ids=[x.strip() for x in (a.project/'config/approved_accessions.txt').read_text(encoding='utf-8-sig').splitlines() if x.strip()]
with mapping.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f,delimiter='\t'))
with legend.open(encoding='utf-8-sig',newline='') as f: legends=list(csv.DictReader(f,delimiter='\t'))
if len(ids)!=196 or len(set(ids))!=196 or len(rows)!=196 or len({r['assembly_accession'] for r in rows})!=196: raise SystemExit('Expected exactly 196 unique approved IDs and mapping rows')
if set(ids)!={r['assembly_accession'] for r in rows}: raise SystemExit('Mapping IDs differ from approved panel')
counts={}; colors={}
for r in rows:
 g=r['operational_group']; c=r['color']; counts[g]=counts.get(g,0)+1
 if not re.fullmatch(r'#[0-9A-Fa-f]{6}',c) or g in colors and colors[g]!=c: raise SystemExit('Invalid or inconsistent operational-group color')
 colors[g]=c
if len(legends)!=10 or {r['operational_group'] for r in legends}!=set(counts): raise SystemExit('Legend must exactly match ten operational groups')
for r in legends:
 g=r['operational_group']
 if r['color']!=colors[g] or int(r['accession_count'])!=counts[g]: raise SystemExit('Legend color/count mismatch')
if out.exists(): raise SystemExit(f'Refusing existing output: {out}')
legend_order=[r['operational_group'] for r in legends]
lines=['DATASET_COLORSTRIP','SEPARATOR TAB','DATASET_LABEL\tOperational taxonomic group','COLOR\t#000000','STRIP_WIDTH\t25','MARGIN\t0','LEGEND_TITLE\tOperational taxonomic group','LEGEND_SHAPES\t'+'\t'.join('1' for _ in legend_order),'LEGEND_COLORS\t'+'\t'.join(colors[g] for g in legend_order),'LEGEND_LABELS\t'+'\t'.join(legend_order),'DATA']
lines += [f"{r['assembly_accession']}\t{r['color']}\t{r['operational_group']}" for r in rows]
data=('\n'.join(lines)+'\n').encode('utf-8')
with out.open('xb') as f: f.write(data)
sha=lambda b:hashlib.sha256(b).hexdigest()
receipt={'status':'PASS','output':str(out),'output_sha256':sha(data),'bytes':len(data),'tips':len(rows),'groups':len(legend_order),'group_counts':counts,'label_semantics':'operational taxonomic group; not host','inputs':{str(x):{'sha256':sha(x.read_bytes()),'bytes':x.stat().st_size} for x in (mapping,legend,a.project/'config/approved_accessions.txt')}}
pathlib.Path(__file__).with_name('taxonomic_group_strip_receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(receipt,indent=2,sort_keys=True))

