#!/usr/bin/env python3
"""Measure a reference image and compare renders with it. Supports judgment; never decides fit.

Run with Pillow available, e.g.:
  uv run --quiet --with pillow python scripts/08-visual-generation/reference_tools.py palette --image ref.png
"""
import argparse
import json
from collections import Counter

from PIL import Image


def palette(path, top=12, step=8):
    """Most common colours, quantized to `step` per channel, ignoring transparent pixels."""
    im = Image.open(path).convert('RGBA')
    im.thumbnail((600, 600))
    counts = Counter()
    raw = im.tobytes()
    for i in range(0, len(raw), 4):
        r, g, b, a = raw[i:i + 4]
        if a < 128:
            continue
        counts[tuple(min(255, round(c / step) * step) for c in (r, g, b))] += 1
    total = sum(counts.values()) or 1
    return [{'hex': '#%02X%02X%02X' % c, 'share': round(n / total, 4)} for c, n in counts.most_common(top)]


def sample(path, points):
    """Exact colours at x,y pixel points."""
    im = Image.open(path).convert('RGBA')
    return [{'point': [x, y], 'hex': '#%02X%02X%02X' % im.getpixel((x, y))[:3]} for x, y in points]


def crop(path, box, out, scale=1.0):
    im = Image.open(path).crop(box)
    if scale != 1.0:
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    im.save(out)
    return {'out': out, 'size': list(im.size)}


def side_by_side(left, right, out, height=1600, gap=24):
    """Scale both images to the same height and place them next to each other on white."""
    ims = []
    for p in (left, right):
        im = Image.open(p).convert('RGB')
        ims.append(im.resize((round(im.width * height / im.height), height), Image.LANCZOS))
    sheet = Image.new('RGB', (ims[0].width + gap + ims[1].width, height), 'white')
    sheet.paste(ims[0], (0, 0))
    sheet.paste(ims[1], (ims[0].width + gap, 0))
    sheet.save(out)
    return {'out': out, 'size': list(sheet.size)}


def info(path):
    im = Image.open(path)
    return {'size': list(im.size), 'aspect_ratio': round(im.width / im.height, 4), 'mode': im.mode}


def _pair(text):
    x, y = text.split(',')
    return int(x), int(y)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('info'); p.add_argument('--image', required=True)
    p = sub.add_parser('palette'); p.add_argument('--image', required=True); p.add_argument('--top', type=int, default=12)
    p = sub.add_parser('sample'); p.add_argument('--image', required=True); p.add_argument('--points', nargs='+', type=_pair, required=True)
    p = sub.add_parser('crop'); p.add_argument('--image', required=True); p.add_argument('--box', required=True)
    p.add_argument('--out', required=True); p.add_argument('--scale', type=float, default=1.0)
    p = sub.add_parser('side-by-side'); p.add_argument('--left', required=True); p.add_argument('--right', required=True)
    p.add_argument('--out', required=True); p.add_argument('--height', type=int, default=1600)
    a = ap.parse_args()
    if a.cmd == 'info':
        r = info(a.image)
    elif a.cmd == 'palette':
        r = palette(a.image, a.top)
    elif a.cmd == 'sample':
        r = sample(a.image, a.points)
    elif a.cmd == 'crop':
        r = crop(a.image, tuple(int(v) for v in a.box.split(',')), a.out, a.scale)
    else:
        r = side_by_side(a.left, a.right, a.out, a.height)
    print(json.dumps(r, indent=2))
