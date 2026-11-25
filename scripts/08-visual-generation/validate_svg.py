#!/usr/bin/env python3
import re,xml.etree.ElementTree as ET
from pathlib import Path
def validate(path):
 try:root=ET.fromstring(Path(path).read_bytes())
 except Exception:return ['invalid SVG XML']
 errors=[];ids=[]
 for e in root.iter():
  if 'id' in e.attrib:ids.append(e.attrib['id'])
  if e.tag.lower().endswith('script'):errors.append('script element')
 if len(ids)!=len(set(ids)):errors.append('duplicate IDs')
 if not root.attrib.get('viewBox') or not root.attrib.get('width') or not root.attrib.get('height'):errors.append('missing canvas dimensions')
 return errors
