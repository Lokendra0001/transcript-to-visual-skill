#!/usr/bin/env python3
"""Prepare a verified file without changing its visual content."""
import argparse,shutil
from pathlib import Path
from verify_assets import verify
def normalize(source,destination):
 result=verify(source)
 if not result.get('valid'):return result
 dst=Path(destination);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dst)
 result.update({'prepared_path':str(dst),'normalization_actions':['copied_verified_original']});return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);x=p.parse_args();r=normalize(x.source,x.destination);print(r);raise SystemExit(0 if r.get('valid') else 2)
