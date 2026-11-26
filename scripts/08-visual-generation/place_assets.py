#!/usr/bin/env python3
"""Place approved raster assets into agent-selected image regions, not a layout engine.

Requires Pillow. Input plan is authored after visually inspecting the AI image.
Every placement: occurrence_id, source (run-relative path), sha256, and bounds
[x,y,width,height] in pixels. This utility cannot establish brand identity or
whether a box is semantically correct; those require upstream and visual review.
"""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def place(base, run_dir, placements, output):
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise RuntimeError('Pillow is required for lossless raster asset placement') from exc
    run = Path(run_dir).resolve(); base = Path(base).resolve(); output = Path(output).resolve()
    if output == base or output.exists():
        raise ValueError('output must be a new file; source and existing files are preserved')
    if not placements:
        raise ValueError('no placements')
    with Image.open(base) as image:
        image.load(); canvas = image.convert('RGBA')
    width, height = canvas.size
    seen = set(); rectangles = []; records = []
    for entry in placements:
        occurrence = entry.get('occurrence_id')
        if not occurrence or occurrence in seen:
            raise ValueError('missing or duplicate occurrence ID')
        seen.add(occurrence)
        asset = (run / entry['source']).resolve()
        if not asset.is_relative_to(run) or not asset.is_file():
            raise ValueError('asset path outside run or missing')
        if asset.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp'):
            raise ValueError('unsupported asset format: use a verified raster derivative')
        if sha(asset) != entry.get('sha256'):
            raise ValueError('source asset fingerprint mismatch')
        bounds = entry.get('bounds')
        if not isinstance(bounds, list) or len(bounds) != 4 or any(type(v) is not int for v in bounds):
            raise ValueError('bounds must be four integer pixels')
        x, y, w, h = bounds
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > width or y + h > height:
            raise ValueError('asset bounds outside image')
        if any(x < rx+rw and x+w > rx and y < ry+rh and y+h > ry for rx,ry,rw,rh in rectangles):
            raise ValueError('asset placement rectangles overlap')
        rectangles.append(bounds)
        with Image.open(asset) as img:
            img.load(); mark = ImageOps.contain(img.convert('RGBA'), (w, h), Image.Resampling.LANCZOS)
        px, py = x + (w-mark.width)//2, y + (h-mark.height)//2
        canvas.alpha_composite(mark, (px, py))
        records.append({'occurrence_id':occurrence, 'source':entry['source'], 'source_sha256':entry['sha256'], 'bounds':bounds, 'actual_bounds':[px,py,mark.width,mark.height]})
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format='PNG')
    return {'output':str(output), 'sha256':sha(output), 'width':width, 'height':height, 'placements':records,
            'limitations':['Geometry and hashes do not verify brand identity, semantic target, or visual quality.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, required=True); p.add_argument('--run-dir', type=Path, required=True)
    p.add_argument('--plan', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    try:
        print(json.dumps(place(args.base,args.run_dir,json.loads(args.plan.read_text())['placements'],args.output),indent=2))
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        print(json.dumps({'error':str(exc)})); raise SystemExit(2)
