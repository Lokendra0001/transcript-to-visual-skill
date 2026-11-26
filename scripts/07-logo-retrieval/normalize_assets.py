#!/usr/bin/env python3
"""Prepare a verified file without changing its visual content.

SVG, PNG and JPEG are copied as they are. Other verified rasters (AVIF, WebP,
which some logo providers serve) are re-encoded losslessly to PNG so later
steps only meet formats they read; the pixels are not edited.
"""
import argparse,shutil,subprocess
from pathlib import Path
from verify_assets import verify
COPY={'.svg','.png','.jpg','.jpeg'}
def to_png(source,destination):
 """Re-encode with the platform image tool; None when none is available."""
 if not shutil.which('sips'):return None
 p=subprocess.run(['sips','-s','format','png',str(source),'--out',str(destination)],capture_output=True,text=True)
 return destination if p.returncode==0 and destination.is_file() else None
def normalize(source,destination):
 result=verify(source)
 if not result.get('valid'):return result
 source,dst=Path(source),Path(destination);dst.parent.mkdir(parents=True,exist_ok=True)
 if source.suffix.lower() in COPY:
  dst=dst.with_suffix(source.suffix.lower());shutil.copyfile(source,dst);action='copied_verified_original'
 else:
  dst=dst.with_suffix('.png')
  if not to_png(source,dst):return {'valid':False,'reason':'no PNG converter available for '+source.suffix.lower()}
  converted=verify(dst)
  if not converted.get('valid'):return {'valid':False,'reason':'PNG conversion produced an invalid file'}
  result={**converted,'source_format':source.suffix.lower()[1:],'source_fingerprint':result.get('fingerprint')};action='converted_to_png'
 result.update({'prepared_path':str(dst),'normalization_actions':[action]});return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);x=p.parse_args();r=normalize(x.source,x.destination);print(r);raise SystemExit(0 if r.get('valid') else 2)
