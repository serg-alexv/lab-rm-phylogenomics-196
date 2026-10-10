#!/usr/bin/env python3
import csv, hashlib, json, pathlib, re
BUNDLE=pathlib.Path('/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/pilot_itol_labels01')
PROJECT=pathlib.Path('/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196')
OUT=pathlib.Path('/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/full100_labels_audit86')
sha=lambda b:hashlib.sha256(b).hexdigest()
def read_bytes(p): return p.read_bytes()
def read_text(p): return p.read_text(encoding='utf-8-sig')
def data_rows(name,header):
    lines=read_text(BUNDLE/name).splitlines()
    if lines[:3] != header: raise ValueError(f'{name}: unexpected header: {lines[:3]}')
    rows=[line.split('\t') for line in lines[3:] if line]
    return rows
manifest=json.loads(read_text(BUNDLE/'manifest.json'))
panel_path=PROJECT/'config/approved_panel.tsv'; approved_path=PROJECT/'config/approved_accessions.txt'
panel_bytes=read_bytes(panel_path); approved_bytes=read_bytes(approved_path)
panel=list(csv.DictReader(panel_bytes.decode('utf-8-sig').splitlines(),delimiter='\t'))
approved=[x.strip() for x in approved_bytes.decode('utf-8-sig').splitlines() if x.strip()]
raw=read_bytes(PROJECT/'pilot_output/species_tree.newick'); flat=read_bytes(PROJECT/'pilot_output/species_tree.itol_quartet_frequency.newick')
pat=re.compile(r'\bGCF_\d{9}\.\d+\b')
tree_ids={}
for name,data in [('raw',raw),('flat',flat)]:
    found=pat.findall(data.decode('utf-8'))
    tree_ids[name]={'count':len(found),'unique':len(set(found)),'sha256':sha(data)}
    if len(found)!=196 or len(set(found))!=196: raise ValueError(f'{name} tree does not contain 196 unique accession-like tips')
    if set(found)!=set(approved): raise ValueError(f'{name} tree tips differ from approved_accessions')
if sha(panel_bytes)!=manifest['source_files']['config/approved_panel.tsv']['sha256'] or len(panel_bytes)!=manifest['source_files']['config/approved_panel.tsv']['bytes']:
    raise ValueError('approved_panel provenance mismatch')
if sha(approved_bytes)!=manifest['source_files']['config/approved_accessions.txt']['sha256'] or len(approved_bytes)!=manifest['source_files']['config/approved_accessions.txt']['bytes']:
    raise ValueError('approved_accessions provenance mismatch')
if len(panel)!=196 or len(approved)!=196 or len(set(approved))!=196: raise ValueError('canonical panel/accession counts invalid')
if set(r['assembly_accession'] for r in panel)!=set(approved): raise ValueError('panel accession membership mismatch')
labels=data_rows('itol_labels.txt',['LABELS','SEPARATOR TAB','DATA'])
colors=data_rows('itol_group_colors.txt',['TREE_COLORS','SEPARATOR TAB','DATA'])
mapping_lines=read_text(BUNDLE/'cell_mapping.tsv').splitlines()
if not mapping_lines or mapping_lines[0].split('\t')!=['assembly_accession','display_label','operational_group','color']:
    raise ValueError('cell_mapping.tsv header mismatch')
mapping=[line.split('\t') for line in mapping_lines[1:] if line]
legend_lines=read_text(BUNDLE/'color_legend.tsv').splitlines()
if not legend_lines or legend_lines[0].split('\t')!=['operational_group','color','accession_count']:
    raise ValueError('color_legend.tsv header mismatch')
legend=[line.split('\t') for line in legend_lines[1:] if line]
if not (len(labels)==len(colors)==len(mapping)==196): raise ValueError('bundle row counts do not equal 196')
if any(len(row)!=2 for row in labels) or any(len(row)!=3 for row in colors) or any(len(row)!=4 for row in mapping) or any(len(row)!=3 for row in legend):
    raise ValueError('bundle row width mismatch')
label_map={a:l for a,l in labels}; color_map={a:(style,color) for a,style,color in colors}; map_map={r[0]:r[1:] for r in mapping}
if len(label_map)!=196 or len(color_map)!=196 or len(map_map)!=196: raise ValueError('duplicate IDs in bundle')
panel_map={r['assembly_accession']:(r['display_label'],r['operational_group']) for r in panel}
if set(label_map)!=set(approved) or set(color_map)!=set(approved) or set(map_map)!=set(approved): raise ValueError('bundle IDs differ from approved panel')
for a,(display,group) in panel_map.items():
    label=display.strip()+f' [{a}]'
    if label_map[a]!=label: raise ValueError(f'label mismatch for {a}')
    if map_map[a][0]!=label or map_map[a][1]!=group: raise ValueError(f'mapping provenance mismatch for {a}')
    style,color=color_map[a]
    if style!='label' or color!=map_map[a][2] or not re.fullmatch(r'#[0-9A-Fa-f]{6}',color): raise ValueError(f'color directive mismatch for {a}')
group_counts={}
for a,(_,group) in panel_map.items(): group_counts[group]=group_counts.get(group,0)+1
legend_map={r[0]:(r[1],int(r[2])) for r in legend}
if set(legend_map)!=set(group_counts): raise ValueError('legend group set mismatch')
for group,count in group_counts.items():
    if legend_map[group][1]!=count: raise ValueError(f'legend count mismatch for {group}')
    assigned={map_map[a][2] for a,(_,g) in panel_map.items() if g==group}
    if assigned!={legend_map[group][0]}: raise ValueError(f'group color not consistent for {group}')
source_manifest={k:{'bytes':len(read_bytes(BUNDLE/k)),'sha256':sha(read_bytes(BUNDLE/k))} for k in ['itol_labels.txt','itol_group_colors.txt','cell_mapping.tsv','color_legend.tsv']}
receipt={'status':'PASS','audit_scope':'label/color bundle vs canonical approved panel/accessions and pilot raw/flat tree tips',
 'source_bundle_manifest_sha256':sha(read_bytes(BUNDLE/'manifest.json')),'manifest_provenance_matches_canonical':True,
 'approved_panel_sha256':sha(panel_bytes),'approved_accessions_sha256':sha(approved_bytes),'approved_count':196,
 'pilot_trees':tree_ids,'bundle_files':source_manifest,'bundle_row_counts':{'labels':len(labels),'tree_colors':len(colors),'cell_mapping':len(mapping),'color_legend_groups':len(legend)},
 'unique_label_count':len(set(label_map.values()),),'unique_group_count':len(group_counts),'group_counts':group_counts,
 'semantics':'display labels + operational taxonomic group colors from approved_panel.tsv; no host or defense-system annotations.',
 'copy_candidates':['itol_labels.txt','itol_group_colors.txt','cell_mapping.tsv'],
 'limitations':['Tree tip membership checked by accession-token extraction; no phylogenetic recomputation or iTOL upload performed.','Bundle can support labels and operational-group coloring only; it does not establish host metadata or defense-system presence/absence.']}
(OUT/'audit_receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(receipt,indent=2,sort_keys=True))
