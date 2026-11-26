#!/usr/bin/env python3
"""Prepare and check evidence for AI-generated raster visuals; never draw a layout."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

CHECKS = ('design_quality', 'reference_fit', 'readability', 'content_accuracy',
          'relationship_accuracy', 'asset_identity', 'asset_placement', 'unauthorized_content')


def inventory(classification, architecture, writing, selection, assets):
    """Preserve upstream facts for the agent; make no design or completion judgment."""
    return {
        'communication_objective': classification.get('communication_objective', {}),
        'classification': classification.get('classification', {}),
        'information_structures': classification.get('information_structures', []),
        'sections': architecture.get('sections', []),
        'nodes': architecture.get('nodes', []),
        'connections': architecture.get('connections', []),
        'reading_order': architecture.get('reading_order', []),
        'constraints': architecture.get('representation_constraints', []),
        'content_items': writing.get('content_items', []),
        'template_selections': selection.get('template_selections', []),
        'design_direction': selection.get('design_direction', []),
        'asset_mappings': assets.get('asset_mappings', []),
        'assets': assets.get('assets', []),
        'fallback_assets': assets.get('fallback_assets', []),
    }


def generation_brief(source, design_system=None):
    """Organize authored plans for an image prompt; never infer visual correctness."""
    entries = []
    for item in source.get('content_items', []):
        if item.get('status') == 'omitted_optional':
            continue
        rep = item.get('representation')
        if rep is None:
            rep = {'type': 'text', 'meaning': item.get('preferred_text', ''),
                   'visible_text': item.get('preferred_text', ''), 'reason': 'legacy canonical text'}
        if not isinstance(rep, dict):
            raise ValueError('invalid representation')
        if item.get('required') and rep.get('type') == 'context_only':
            raise ValueError('required meaning cannot be context only')
        entries.append({'id': item.get('id'), 'requirement_id': item.get('content_requirement_id'),
                        'target_refs': item.get('target_refs', []), 'required': item.get('required', False),
                        'representation': rep})
    if design_system is not None and not isinstance(design_system, dict):
        raise ValueError('design system must be an object')
    return {'objective': source.get('communication_objective', {}),
            'requirements': entries, 'relationships': source.get('connections', []),
            'reference_direction': source.get('design_direction', []),
            'creative_direction': design_system,
            'asset_mappings': source.get('asset_mappings', []),
            'instruction': 'Treat canonical content and metadata as context; show only approved essential text and unambiguous visual meaning. Verify every requirement in the actual image.',
            'limitation': 'Planning only; no image was generated or inspected.'}


def inspect_png(path):
    """Check PNG signature and IHDR, not full decoding or visual content."""
    raw = Path(path).read_bytes()
    if len(raw) < 33 or raw[:8] != b'\x89PNG\r\n\x1a\n' or raw[12:16] != b'IHDR' or struct.unpack('>I', raw[8:12])[0] != 13:
        raise ValueError('invalid PNG header')
    width, height = struct.unpack('>II', raw[16:24])
    if not width or not height:
        raise ValueError('invalid PNG dimensions')
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'width': width, 'height': height,
            'bytes': len(raw), 'limitation': 'header only; decode and visual review still required'}


def validate_reference_input(reference, record):
    """Check recorded file identity and evidence fields, not remote-tool consumption."""
    try:
        digest = hashlib.sha256(Path(reference).read_bytes()).hexdigest()
    except OSError as exc:
        return {'valid': False, 'errors': [str(exc)]}
    errors = []
    if not isinstance(record, dict):
        return {'valid': False, 'errors': ['invalid reference input record']}
    if record.get('reference_sha256') != digest:
        errors.append('reference fingerprint mismatch')
    if record.get('attached_to_generation') is not True:
        errors.append('reference attachment not recorded')
    for key in ('tool', 'call_evidence'):
        if not isinstance(record.get(key), str) or not record[key].strip():
            errors.append(f'{key}: missing')
    return {'valid': not errors, 'errors': errors, 'reference_sha256': digest,
            'limitation': 'Record and fingerprint check only; does not prove tool consumption or visual reference fit.'}


def validate_review(image_path, review, required_content=(), required_assets=(), required_relationships=()):
    """Check presence and freshness of agent-authored review, not the truth of judgments."""
    errors = []
    try:
        image = inspect_png(image_path)
    except (OSError, ValueError) as exc:
        return {'valid': False, 'errors': [str(exc)], 'method': 'deterministic evidence completeness only'}
    if review.get('image_sha256') != image['sha256']:
        errors.append('review image fingerprint mismatch')
    if review.get('dimensions') != [image['width'], image['height']]:
        errors.append('review dimensions mismatch')
    required_assets = tuple(required_assets)
    required_relationships = tuple(required_relationships)
    not_applicable = set()
    if not required_assets:
        not_applicable.update(('asset_identity', 'asset_placement'))
    if not required_relationships:
        not_applicable.add('relationship_accuracy')
    for key in CHECKS:
        check = review.get('checks', {}).get(key, {})
        valid_status = check.get('status') == 'pass' or (key in not_applicable and check.get('status') == 'not_applicable')
        if not valid_status or not isinstance(check.get('evidence'), str) or not check['evidence'].strip():
            errors.append(f'{key}: missing passing review with evidence')
    for name, expected in (('content', required_content), ('assets', required_assets), ('relationships', required_relationships)):
        rows = review.get(name, [])
        if not isinstance(rows, list):
            errors.append(f'{name}: invalid review entries'); continue
        ids = [r.get('id') for r in rows if isinstance(r, dict)]
        if len(ids) != len(set(ids)):
            errors.append(f'{name}: duplicate review IDs')
        expected_set = set(expected)
        if set(ids) != expected_set:
            errors.append(f'{name}: missing or unexpected review IDs')
        for row in rows:
            if not isinstance(row, dict) or row.get('status') != 'pass' or not isinstance(row.get('evidence'), str) or not row['evidence'].strip():
                errors.append(f'{name}: unverified entry')
    return {'valid': not errors, 'errors': errors, 'image': image,
            'method': 'deterministic evidence completeness only; agent observations are not independently verified'}


def load(path):
    return json.loads(Path(path).read_text())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    inv = sub.add_parser('inventory'); inv.add_argument('--run-dir', type=Path, required=True)
    brief = sub.add_parser('brief'); brief.add_argument('--inventory', type=Path, required=True); brief.add_argument('--design-system', type=Path)
    ref = sub.add_parser('check-reference'); ref.add_argument('--reference', type=Path, required=True); ref.add_argument('--record', type=Path, required=True)
    check = sub.add_parser('check-review'); check.add_argument('--image', type=Path, required=True); check.add_argument('--review', type=Path, required=True); check.add_argument('--inventory', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'inventory':
            files = ['03-content-classification.json','04-workflow-architecture.json','05-content-writing.json','06-template-selection.json','07-logo-retrieval.json']
            result = inventory(*(load(args.run_dir / f) for f in files))
        elif args.command == 'brief':
            result = generation_brief(load(args.inventory), load(args.design_system) if args.design_system else None)
        elif args.command == 'check-reference':
            result = validate_reference_input(args.reference, load(args.record))
        else:
            source = load(args.inventory)
            content = [x['id'] for x in source['content_items'] if x.get('required') and x.get('status') != 'omitted_optional']
            assets = [x['asset_requirement_id'] for x in source['asset_mappings']]
            relationships = [x['id'] for x in source['connections'] if x.get('visual_representation_required')]
            result = validate_review(args.image, load(args.review), content, assets, relationships)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        raise SystemExit(0 if result.get('valid', True) else 2)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'valid': False, 'errors': [str(exc)]})); raise SystemExit(2)
