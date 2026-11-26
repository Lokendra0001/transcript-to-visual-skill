#!/usr/bin/env python3
"""Verify bytes and reject active SVG; semantic authenticity is Claude-reviewed."""
import hashlib,re,xml.etree.ElementTree as ET
from pathlib import Path
def verify(path):
 try:data=Path(path).read_bytes()
 except OSError:return {'valid':False,'reason':'unreadable'}
 ext=Path(path).suffix.lower(); sig={'.png':b'\x89PNG\r\n\x1a\n','.jpg':b'\xff\xd8','.jpeg':b'\xff\xd8','.webp':b'RIFF'}
 if not data:return {'valid':False,'reason':'empty'}
 if ext=='.svg':
  text=data.decode('utf-8','ignore')
  if re.search(r'<!doctype|<!entity|<\?xml-stylesheet',text,re.I):return {'valid':False,'reason':'unsafe SVG declaration'}
  try: root=ET.fromstring(data)
  except ET.ParseError:return {'valid':False,'reason':'invalid SVG XML'}
  if not root.tag.lower().endswith('svg'):return {'valid':False,'reason':'missing SVG root'}
  view_box=root.attrib.get('viewBox') or root.attrib.get('viewbox')
  for element in root.iter():
   tag=element.tag.lower()
   if tag.endswith('script') or tag.endswith('foreignobject'):return {'valid':False,'reason':'unsafe SVG element'}
   for key,value in element.attrib.items():
    low=str(value).strip().lower(); name=key.lower()
    if name.startswith('on') or low.startswith('javascript:'):return {'valid':False,'reason':'unsafe SVG attribute'}
    if name.endswith('href') and low and not low.startswith('#') and not low.startswith('data:image/'):return {'valid':False,'reason':'external SVG reference'}
 elif ext=='.avif':
  if data[4:8]!=b'ftyp' or data[8:12] not in {b'avif',b'avis'}:return {'valid':False,'reason':'unsupported or invalid signature'}
 elif ext not in sig or not data.startswith(sig[ext]):return {'valid':False,'reason':'unsupported or invalid signature'}
 result={'valid':True,'format':ext[1:],'byte_size':len(data),'fingerprint':hashlib.sha256(data).hexdigest()}
 if ext=='.png' and len(data)>=24 and data[12:16]==b'IHDR':
  width,height=int.from_bytes(data[16:20],'big'),int.from_bytes(data[20:24],'big')
  if width and height:result.update({'width':width,'height':height,'aspect_ratio':width/height})
 if ext=='.svg' and view_box:
  try:
   _,_,width,height=map(float,re.split(r'[ ,]+',view_box.strip()))
   if width<=0 or height<=0:return {'valid':False,'reason':'invalid SVG viewBox'}
   result.update({'viewBox':view_box,'aspect_ratio':width/height})
  except ValueError:return {'valid':False,'reason':'invalid SVG viewBox'}
 return result
