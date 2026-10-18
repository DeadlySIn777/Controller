"""Check local release evidence; never upload files, purchase or authorize operation."""
import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re

# fabrication_spec: stackup, thickness, copper, finish, impedance and outline notes.
# programming_bundle: revisioned FPGA/NOR, ESP and Linux images plus programmed BOM lines.
# programming_test_scope: agreed PCBWay programming/functional-test scope and acceptance limits.
# link_prototype_measurement: physical measurement of the bounded motion-link cycle and its
#   fault behaviour under representative load on a real host and FPGA evaluation board
#   (docs/BUILD_PLAN.md stage 5). It precedes final layout; host tests and RTL simulation
#   are a different evidence class and cannot satisfy it.
PROTOTYPE = frozenset({
    'full_schematic', 'pcb_layout', 'fabrication_zip', 'fabrication_spec', 'bom',
    'placement', 'assembly_drawing', 'erc', 'drc', 'electrical_review', 'fpga_build',
    'software_validation', 'bringup_procedure', 'programming_bundle',
    'programming_test_scope', 'link_prototype_measurement', 'pcbway_quote',
})
PRODUCTION = PROTOTYPE | frozenset({
    'hardware_test', 'loaded_realtime_test', 'factory_test',
    'system_integration_test', 'final_cost', 'compliance_review',
})

# A PCBWay turnkey quote is computed from these released artifacts. A quote recorded
# before all of them are complete cannot describe the board that would be built.
QUOTE_PREREQUISITES = frozenset({
    'full_schematic', 'pcb_layout', 'fabrication_zip', 'fabrication_spec', 'bom',
    'placement', 'assembly_drawing', 'erc', 'drc', 'programming_bundle',
    'programming_test_scope',
})
# Files actually uploaded to PCBWay; the submission must record their exact hashes.
QUOTE_PACKAGE = ('fabrication_zip', 'bom', 'placement')
SUBMISSION_FIELDS = ('quote_id', 'quoted_at', 'submitted_by', 'board_revision',
                     'quantities', 'package_sha256', 'figures')
# Identity fields follow the same rule as reviewed_by/reviewed_at: non-blank strings.
SUBMISSION_TEXT_FIELDS = ('quote_id', 'quoted_at', 'submitted_by', 'board_revision')
# One entry per quoted quantity, copied from PCBWay's quote: price per assembled board,
# one-time charges (stencil, setup, programming) and the stated lead time.
FIGURE_FIELDS = ('quantity', 'currency', 'unit_price', 'setup_cost', 'lead_time_days')
CURRENCY = re.compile('[A-Z]{3}')
SHA256 = re.compile('[0-9a-f]{64}')
MEANING = 'Evidence manifest consistency only; no order or machine authorization.'


def _positive_quantities(value):
    return (isinstance(value, list) and bool(value) and
            all(type(q) is int and q > 0 for q in value))


def _amount(value):
    return (type(value) in (int, float) and math.isfinite(value) and value >= 0)


def _figure_blockers(figures, quantities):
    """Validate the per-quantity quote figures; values come only from the supplier quote."""
    if not isinstance(figures, list) or not figures:
        return []  # reported as 'submission figures missing'
    blockers = []
    seen = []
    for index, entry in enumerate(figures):
        where = f'pcbway_quote: submission figures[{index}]'
        if not isinstance(entry, dict):
            blockers.append(f'{where} must be an object')
            continue
        missing = [f for f in FIGURE_FIELDS if f not in entry]
        if missing:
            blockers.append(f'{where} missing ' + ', '.join(missing))
            continue
        if type(entry['quantity']) is not int or entry['quantity'] <= 0:
            blockers.append(f'{where} quantity must be a positive whole number')
        else:
            seen.append(entry['quantity'])
        if not isinstance(entry['currency'], str) or not CURRENCY.fullmatch(entry['currency']):
            blockers.append(f'{where} currency must be an ISO 4217 code')
        for field in ('unit_price', 'setup_cost'):
            if not _amount(entry[field]):
                blockers.append(f'{where} {field} must be a non-negative number')
        if type(entry['lead_time_days']) is not int or entry['lead_time_days'] <= 0:
            blockers.append(f'{where} lead_time_days must be a positive whole number')
    if len(seen) != len(set(seen)):
        blockers.append('pcbway_quote: submission figures repeat a quantity')
    if _positive_quantities(quantities) and set(seen) != set(quantities):
        blockers.append('pcbway_quote: submission figures must cover exactly the quoted quantities')
    return blockers


def _quote_blockers(item, items, manifest):
    """Validate the structured PCBWay quote record; never contacts the supplier."""
    if not isinstance(item, dict):
        return []
    blockers = []
    requires = item.get('requires')
    if not isinstance(requires, list) or not all(isinstance(r, str) for r in requires):
        blockers.append('pcbway_quote: structured quote record needs a requires list')
    else:
        missing = sorted(QUOTE_PREREQUISITES - set(requires))
        if missing:
            blockers.append('pcbway_quote: requires omits ' + ', '.join(missing))
    if not _positive_quantities(item.get('quantities')):
        blockers.append('pcbway_quote: quantities must list positive whole-unit quote quantities')
    if 'submission' not in item:
        blockers.append('pcbway_quote: submission must be recorded (null until a real quote exists)')
    submission = item.get('submission')
    if submission is not None:
        if not isinstance(submission, dict):
            blockers.append('pcbway_quote: submission must be an object or null')
            submission = {}
        for field in SUBMISSION_FIELDS:
            value = submission.get(field)
            if field in SUBMISSION_TEXT_FIELDS:
                if not isinstance(value, str) or not value.strip():
                    blockers.append(f'pcbway_quote: submission {field} missing')
            elif value is None or (isinstance(value, (list, dict)) and not value):
                blockers.append(f'pcbway_quote: submission {field} missing')
        quoted_at = submission.get('quoted_at')
        if isinstance(quoted_at, str) and quoted_at.strip():
            try:
                datetime.fromisoformat(quoted_at)
            except ValueError:
                blockers.append('pcbway_quote: submission quoted_at must be an ISO 8601 date')
        if (submission.get('board_revision') is not None and
                submission.get('board_revision') != manifest.get('board_revision')):
            blockers.append('pcbway_quote: submission is for a different board revision')
        if submission.get('quantities') is not None and not _positive_quantities(
                submission.get('quantities')):
            blockers.append('pcbway_quote: submission quantities must be positive whole units')
        package = submission.get('package_sha256')
        if isinstance(package, dict):
            for key in QUOTE_PACKAGE:
                recorded = (items.get(key) or {}).get('sha256')
                if not isinstance(package.get(key), str) or package.get(key) != recorded:
                    blockers.append(f'pcbway_quote: submission package hash for {key} '
                                    'does not match released evidence')
        elif package is not None:
            blockers.append('pcbway_quote: submission package_sha256 must be an object')
        figures = submission.get('figures')
        if figures is not None and not isinstance(figures, list):
            blockers.append('pcbway_quote: submission figures must be a list')
        else:
            blockers.extend(_figure_blockers(figures, submission.get('quantities')))
    if item.get('status') == 'complete':
        if item.get('submission') is None:
            blockers.append('pcbway_quote: complete without a recorded supplier submission')
        for key in sorted(QUOTE_PREREQUISITES):
            status = (items.get(key) or {}).get('status', 'unrecorded')
            if status != 'complete':
                blockers.append(f'pcbway_quote: complete while prerequisite {key} is {status}')
    return blockers


def check_release(manifest, root, stage='prototype'):
    """Check completeness/hash consistency of evidence, not its physical truth."""
    root = Path(root).resolve()
    blockers = []
    if stage not in ('prototype', 'production'):
        raise ValueError('stage must be prototype or production')
    if not isinstance(manifest, dict):
        return {'stage': stage, 'ready': False, 'blockers': ['manifest must be an object'],
                'meaning': MEANING}
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
    seen_paths = {}
    seen_digests = {}
    for key in sorted(required):
        item = items.get(key)
        if item is None:
            blockers.append(f'{key}: required evidence missing')
            continue
        if item.get('status') != 'complete':
            blockers.append(f'{key}: {item.get("status", "unrecorded")}')
            continue
        before = len(blockers)
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
        digest = item.get('sha256')
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            blockers.append(f'{key}: valid SHA-256 missing')
            continue
        data = resolved.read_bytes()
        if not data:
            blockers.append(f'{key}: empty evidence file')
        actual = hashlib.sha256(data).hexdigest()
        if actual != digest:
            blockers.append(f'{key}: file changed after review')
        if len(blockers) != before:
            continue
        # Each artifact id needs its own evidence: one file, or one set of bytes saved
        # under several names, cannot stand for a layout, a DRC report and a quote.
        if resolved in seen_paths:
            blockers.append(f'{key}: shares evidence file with {seen_paths[resolved]}')
        elif actual in seen_digests:
            blockers.append(f'{key}: evidence bytes identical to {seen_digests[actual]} '
                            '(same SHA-256)')
        seen_paths.setdefault(resolved, key)
        seen_digests.setdefault(actual, key)
    if 'pcbway_quote' in required:
        blockers.extend(_quote_blockers(items.get('pcbway_quote'), items, manifest))
    final_cost = items.get('final_cost')
    if ('final_cost' in required and isinstance(final_cost, dict) and
            final_cost.get('status') == 'complete'):
        quote_status = (items.get('pcbway_quote') or {}).get('status', 'unrecorded')
        if quote_status != 'complete':
            blockers.append(f'final_cost: complete while pcbway_quote is {quote_status}')
    return {'stage': stage, 'ready': not blockers, 'blockers': blockers, 'meaning': MEANING}


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
        result = {'stage': args.stage, 'ready': False, 'blockers': [str(exc)], 'meaning': MEANING}
    rendered = json.dumps(result, indent=2) + '\n'
    print(rendered, end='')
    if args.output:
        destination = root / args.output
        destination.parent.mkdir(parents=True, exist_ok=True)
        # LF on every platform: reports are compared and hashed byte-for-byte.
        destination.write_text(rendered, encoding='utf-8', newline='\n')
    return 0 if result['ready'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
