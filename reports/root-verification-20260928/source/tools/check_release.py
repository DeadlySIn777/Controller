"""Check local release evidence; never upload files, purchase or authorize operation."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

# fabrication_spec: stackup, thickness, copper, finish, impedance and outline notes.
# programming_bundle: revisioned FPGA/NOR, ESP and Linux images plus programmed BOM lines.
# programming_test_scope: agreed PCBWay programming/functional-test scope and acceptance limits.
PROTOTYPE = frozenset({
    'full_schematic', 'pcb_layout', 'fabrication_zip', 'fabrication_spec', 'bom',
    'placement', 'assembly_drawing', 'erc', 'drc', 'electrical_review', 'fpga_build',
    'software_validation', 'bringup_procedure', 'programming_bundle',
    'programming_test_scope', 'pcbway_quote',
})
PRODUCTION = PROTOTYPE | frozenset({
    'hardware_test', 'loaded_realtime_test', 'factory_test',
    'system_integration_test', 'final_cost', 'compliance_review',
})


def check_release(manifest, root, stage='prototype'):
    """Check completeness/hash consistency of evidence, not its physical truth."""
    root = Path(root).resolve()
    blockers = []
    if stage not in ('prototype', 'production'):
        raise ValueError('stage must be prototype or production')
    if not isinstance(manifest, dict):
        return {'stage': stage, 'ready': False, 'blockers': ['manifest must be an object']}
    if manifest.get('schema_version') != 1 or type(manifest.get('schema_version')) is not int:
        blockers.append('schema_version must be integer 1')
    for field in ('product_revision', 'board_revision'):
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            blockers.append(f'{field} must be assigned')
    if manifest.get('manufacturer') != 'PCBWay':
        blockers.append('manufacturer must match PCBWay release plan')
    artifacts = manifest.get('artifacts')
    if not isinstance(artifacts, list):
        artifacts = []
        blockers.append('artifacts must be an array')
    items = {}
    for index, item in enumerate(artifacts):
        if not isinstance(item, dict) or not isinstance(item.get('id'), str):
            blockers.append(f'artifacts[{index}] has no valid id')
            continue
        key = item['id']
        if key in items:
            blockers.append(f'{key}: duplicate evidence id')
        items[key] = item
    required = PROTOTYPE if stage == 'prototype' else PRODUCTION
    seen_files = {}
    for key in sorted(required):
        item = items.get(key)
        if item is None:
            blockers.append(f'{key}: required evidence missing')
            continue
        if item.get('status') != 'complete':
            blockers.append(f'{key}: {item.get("status", "unrecorded")}')
            continue
        if item.get('board_revision') != manifest.get('board_revision'):
            blockers.append(f'{key}: evidence is for a different board revision')
        for field in ('reviewed_by', 'reviewed_at'):
            if not isinstance(item.get(field), str) or not item[field].strip():
                blockers.append(f'{key}: {field} missing')
        relative = item.get('path')
        if (not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative or
                PurePosixPath(relative).is_absolute() or '..' in PurePosixPath(relative).parts):
            blockers.append(f'{key}: path must be relative and remain inside project')
            continue
        resolved = (root / relative).resolve()
        if not resolved.is_relative_to(root) or not resolved.is_file():
            blockers.append(f'{key}: file missing or outside project')
            continue
        if resolved in seen_files:
            blockers.append(f'{key}: shares evidence file with {seen_files[resolved]}')
        seen_files.setdefault(resolved, key)
        digest = item.get('sha256')
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
            blockers.append(f'{key}: valid SHA-256 missing')
            continue
        if resolved.stat().st_size == 0:
            blockers.append(f'{key}: empty evidence file')
        if hashlib.sha256(resolved.read_bytes()).hexdigest() != digest:
            blockers.append(f'{key}: file changed after review')
    return {'stage': stage, 'ready': not blockers, 'blockers': blockers,
            'meaning': 'Evidence manifest consistency only; no order or machine authorization.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('prototype', 'production'), default='prototype')
    parser.add_argument('--manifest', default='manufacturing/release-manifest.json')
    parser.add_argument('--output')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        manifest = json.loads((root / args.manifest).read_text(encoding='utf-8'))
        result = check_release(manifest, root, args.stage)
    except (OSError, ValueError) as exc:
        result = {'stage': args.stage, 'ready': False, 'blockers': [str(exc)]}
    rendered = json.dumps(result, indent=2) + '\n'
    print(rendered, end='')
    if args.output:
        destination = root / args.output
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding='utf-8')
    return 0 if result['ready'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
