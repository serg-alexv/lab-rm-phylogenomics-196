import argparse, hashlib, json
from pathlib import Path
import pypdfium2 as pdfium
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);p.add_argument('--out',required=True);a=p.parse_args()
pdf=pdfium.PdfDocument(a.pdf)
if len(pdf)<1: raise SystemExit('PDF has no pages')
page=pdf[0]
bitmap=page.render(scale=1.5)
image=bitmap.to_pil(); image.save(a.out,format='PNG',optimize=False)
q=Path(a.out); h=hashlib.sha256(q.read_bytes()).hexdigest()
print(json.dumps({'rendered_page_index':0,'page_count':len(pdf),'render_engine':'pypdfium2','scale':1.5,'png_path':str(q),'png_bytes':q.stat().st_size,'png_sha256':h,'dimensions_px':image.size},indent=2))
