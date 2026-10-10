import argparse, hashlib, json, re, xml.etree.ElementTree as ET
from pathlib import Path
from pypdf import PdfReader

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--svg',required=True); ap.add_argument('--pdf',required=True)
    ap.add_argument('--labels',required=True); ap.add_argument('--tree',required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    svg=Path(a.svg); pdf=Path(a.pdf); lab=Path(a.labels); tree=Path(a.tree)
    root=ET.parse(svg).getroot()
    svg_text=' '.join(' '.join(x.itertext()) for x in root.iter() if x.tag.rsplit('}',1)[-1]=='text')
    mappings=[]
    for line in lab.read_text(encoding='utf-8-sig').splitlines():
        if not line or line in ('LABELS','SEPARATOR TAB','DATA'): continue
        cols=line.split('\t',1)
        if len(cols)==2: mappings.append((cols[0],cols[1]))
    accessions=[x[0] for x in mappings]
    tree_text=tree.read_text(encoding='utf-8')
    tree_ids=set(re.findall(r'GCF_[0-9]+\.[0-9]+',tree_text))
    svg_present=[acc for acc,label in mappings if label in svg_text]
    reader=PdfReader(str(pdf),strict=True)
    pdf_text=' '.join((p.extract_text() or '') for p in reader.pages)
    pdf_present=[acc for acc,label in mappings if label in pdf_text]
    out={
      'schema':'itol-export-visual-inspection-v1',
      'inputs':{str(p):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in (svg,pdf,lab,tree)},
      'svg':{'xml_parse':'PASS','root_tag':root.tag,'text_element_count':sum(1 for x in root.iter() if x.tag.rsplit('}',1)[-1]=='text'),'mapped_label_count':len(mappings),'mapped_labels_found':len(svg_present),'missing_label_count':len(set(accessions)-set(svg_present)),'unique_label_ids':len(set(accessions))},
      'pdf':{'strict_parse':'PASS','page_count':len(reader.pages),'mapped_label_count':len(mappings),'mapped_labels_found_in_extracted_text':len(pdf_present),'missing_label_count':len(set(accessions)-set(pdf_present)),'unique_label_ids':len(set(accessions)),'header_magic':pdf.read_bytes()[:8].decode('ascii','replace')},
      'tree':{'accession_tip_count':len(tree_ids),'label_accession_count':len(set(accessions)),'accession_sets_equal':tree_ids==set(accessions)},
      'limitations':['PDF raster preview not generated: PyMuPDF/fitz unavailable in the active Python runtimes.','Label checks use exact display-label substring presence in SVG text and pypdf-extracted PDF text; they do not independently reconstruct geometry or infer scientific validity.']
    }
    Path(a.out).write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(out,indent=2,ensure_ascii=False))
if __name__=='__main__': main()
