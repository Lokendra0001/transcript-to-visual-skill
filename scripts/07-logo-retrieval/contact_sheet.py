#!/usr/bin/env python3
"""Create a neutral PNG contact sheet from real prepared assets."""
import base64,html,shutil,subprocess,tempfile
from pathlib import Path
MIME={'.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp'}
def embedded_image(run,relative_path):
 path=Path(run)/relative_path
 try:
  mime=MIME.get(path.suffix.lower())
  if not mime:return None
  return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode('ascii')
 except OSError:return None
def generate(run,assets,requests):
 columns=5;rows=max(1,(len(requests)+columns-1)//columns);width,height=900,rows*156+40;svg=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="%s"><rect width="100%%" height="100%%" fill="#f8fafc"/>'%height]
 by_id={a['id']:a for a in assets}
 for i,r in enumerate(requests):
  column,row=i%columns,i//columns;x=20+column*172;y=20+row*156;a=by_id.get(r['id']);label=html.escape(str(r.get('canonical_entity_name') or r['id']))
  svg.append(f'<g><rect x="{x}" y="{y}" width="160" height="136" rx="12" fill="white" stroke="#dbe3ea"/><text x="{x+80}" y="{y+106}" text-anchor="middle" font-family="sans-serif" font-size="13" font-weight="600">{label}</text>')
  if a:
   href=embedded_image(run,a['prepared_file_path'])
   if href:svg.append(f'<image href="{href}" x="{x+48}" y="{y+16}" width="64" height="64" preserveAspectRatio="xMidYMid meet"/><text x="{x+80}" y="{y+124}" text-anchor="middle" font-family="sans-serif" font-size="9" fill="#475569">{html.escape(a.get("representation_type","exact_logo"))}</text>')
   else:svg.append(f'<text x="{x+80}" y="{y+82}" text-anchor="middle" font-family="sans-serif" font-size="10" fill="#b45309">Asset cannot render</text>')
  else:svg.append(f'<text x="{x+80}" y="{y+72}" text-anchor="middle" font-family="sans-serif" font-size="10" fill="#b45309">Unresolved</text>')
  svg.append('</g>')
 svg.append('</svg>');step=Path(run)/'step-07';step.mkdir(exist_ok=True);source=step/'asset-contact-sheet.svg';png=step/'asset-contact-sheet.png';source.write_text(''.join(svg))
 if shutil.which('sips'):
  p=subprocess.run(['sips','-s','format','png',str(source),'--out',str(png)],capture_output=True,text=True)
  if p.returncode==0 and png.is_file():return {'svg':str(source),'png':str(png),'rendered':True,'renderer':'sips'}
 if shutil.which('qlmanage'):
  with tempfile.TemporaryDirectory() as temp:
   p=subprocess.run(['qlmanage','-t','-s','1000','-o',temp,str(source)],capture_output=True,text=True)
   rendered=Path(temp)/(source.name+'.png')
   if p.returncode==0 and rendered.is_file():shutil.copyfile(rendered,png);return {'svg':str(source),'png':str(png),'rendered':True,'renderer':'qlmanage'}
 return {'svg':str(source),'png':str(png),'rendered':False,'reason':'no usable renderer'}
