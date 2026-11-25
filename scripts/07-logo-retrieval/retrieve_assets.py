#!/usr/bin/env python3
"""Bounded public HTTP(S) downloader. Call only after identity/source review."""
import ipaddress,socket,urllib.error,urllib.parse,urllib.request
from pathlib import Path
MIME_EXTENSIONS={'image/svg+xml':'.svg','image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp','image/gif':'.gif','image/x-icon':'.ico','image/vnd.microsoft.icon':'.ico','image/avif':'.avif'}
def safe_url(url):
 p=urllib.parse.urlparse(url)
 if p.scheme not in {'http','https'} or not p.hostname:return False
 try:
  ip=ipaddress.ip_address(p.hostname)
  return not ip.is_private and not ip.is_loopback and not ip.is_link_local
 except ValueError:return p.hostname.lower()!='localhost'
def image_extension(data,content_type=''):
 """Determine a safe image extension from bytes first, MIME second."""
 probe=data.lstrip()[:512].lower()
 if probe.startswith(b'<svg') or (probe.startswith(b'<?xml') and b'<svg' in probe):return '.svg'
 if data.startswith(b'\x89PNG\r\n\x1a\n'):return '.png'
 if data.startswith(b'\xff\xd8'):return '.jpg'
 if data.startswith(b'RIFF') and data[8:12]==b'WEBP':return '.webp'
 if data.startswith((b'GIF87a',b'GIF89a')):return '.gif'
 if data.startswith(b'\x00\x00\x01\x00'):return '.ico'
 return MIME_EXTENSIONS.get(content_type.split(';',1)[0].strip().lower(),'.bin')
def retrieve(url,destination,timeout=15,max_bytes=5_000_000):
 if not safe_url(url):return {'ok':False,'reason':'unsafe network destination'}
 try:
  with urllib.request.urlopen(url,timeout=timeout) as r:
   data=r.read(max_bytes+1)
   content_type=r.headers.get_content_type() if r.headers else ''
  if len(data)>max_bytes:return {'ok':False,'reason':'download too large'}
  extension=image_extension(data,content_type);d=Path(destination).with_suffix(extension);d.parent.mkdir(parents=True,exist_ok=True);tmp=d.with_suffix(d.suffix+'.tmp');tmp.write_bytes(data);tmp.replace(d);return {'ok':True,'path':str(d),'content_type':content_type,'detected_extension':extension,'byte_size':len(data)}
 except urllib.error.HTTPError as e:
  category='http_404' if e.code==404 else 'http_403' if e.code==403 else 'rate_limited' if e.code==429 else 'http_error'
  return {'ok':False,'failure_category':category,'http_status':e.code}
 except (urllib.error.URLError,socket.timeout,TimeoutError) as e:return {'ok':False,'failure_category':'network_failure','reason':e.__class__.__name__}
 except Exception as e:return {'ok':False,'failure_category':'download_failure','reason':e.__class__.__name__}
