#!/usr/bin/env python3
"""Check cache entries against local bytes; never treats a cache as identity proof."""
import json
from pathlib import Path
from verify_assets import verify
def cache_valid(record,run_dir):
 path=Path(run_dir)/record.get('prepared_file_path','')
 checked=verify(path)
 return bool(checked.get('valid') and checked.get('fingerprint')==record.get('fingerprint')),checked
