"""Opt-in MC package envelopes; historical child footprint sources stay intact.

Only adds a courtyard to the four specifically sourced custom footprints.
The existing nominal F.Fab outlines and every electrical pad expression remain
unchanged. 0.25 mm beyond maximum body/actual copper is a project placement
allowance, not assembly-process qualification or a manufacturer land pattern.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import hashlib
from pathlib import Path

try:
    from hardware_build_assembly import parse, child, children, value
except ModuleNotFoundError:
    from tools.hardware_build_assembly import parse, child, children, value

ROOT = Path(__file__).resolve().parents[1]
ALLOWANCE_MM = Decimal('0.25')
GRID_MM = Decimal('0.05')
ENVELOPES = {
    'TPS62901_RPJ9': {
        'body_nominal_xy_mm': [1.5, 2.0], 'body_maximum_xy_mm': [1.6, 2.1],
        'drawing': 'TI RPJ0009A 4224505/A 10/2018; TPS62901 Rev A p45',
        'source_url': 'https://www.ti.com/lit/ds/symlink/tps62901.pdf',
        'source_path': 'research/logic-power/tps62901.pdf',
    },
    'XGL4020': {
        'body_nominal_xy_mm': [4.0, 4.0], 'body_maximum_xy_mm': [4.3, 4.3],
        'drawing': 'Coilcraft 1529-3 Rev 02/19/26 p3; 4.0 +/-0.3 mm',
        'source_url': 'https://www.coilcraft.com/getmedia/76c9c081-4945-4c85-9129-9356e1ad6734/xgl4020.pdf',
        'source_path': 'research/logic-power/xgl4020.pdf',
    },
    'LTC2962_UD16': {
        'body_nominal_xy_mm': [3.0, 3.0], 'body_maximum_xy_mm': [3.1, 3.1],
        'drawing': 'ADI LTC2962/2963/2964 Rev 0 p18; UD16 DWG 05-08-1691',
        'source_url': 'https://www.analog.com/media/en/technical-documentation/data-sheets/LTC2962-2963-2964.pdf',
        'source_path': 'research/mc-courtyards/ltc2962-ud16-dimensions.json',
        'source_is_dimension_transcription_not_full_pdf': True,
    },
    'TPS3851_DRB8': {
        'body_nominal_xy_mm': [3.0, 3.0], 'body_maximum_xy_mm': [3.1, 3.1],
        'drawing': 'TI DRB0008A 4218875/A 01/2018; TPS3851 Rev B p33',
        'source_url': 'https://www.ti.com/lit/ds/symlink/tps3851.pdf',
        'source_path': 'research/is1-watchdogs/tps3851-revb.pdf',
    },
}


def _d(v):
    result = Decimal(str(v))
    if not result.is_finite():
        raise ValueError('Nonfinite footprint geometry')
    return result


def geometry(text):
    """Return reviewed maximum body plus actual, unchanged pad extents in mm."""
    tree = parse(text)
    name = value(tree[1])
    if name not in ENVELOPES:
        return None
    body_x, body_y = map(_d, ENVELOPES[name]['body_maximum_xy_mm'])
    bounds = [-body_x / 2, -body_y / 2, body_x / 2, body_y / 2]
    pads = children(tree, 'pad')
    if not pads:
        raise ValueError('Sourced custom footprint has no pads')
    for pad in pads:
        at, size = child(pad, 'at'), child(pad, 'size')
        if at is None or size is None:
            raise ValueError('Incomplete pad geometry')
        # Reviewed footprints have axis-aligned roundrect pads. Refuse a new
        # rotation/shape instead of silently understating its physical extent.
        if value(pad[3]) != 'roundrect' or (len(at) > 3 and _d(at[3]) % 180):
            raise ValueError('Unreviewed pad shape or rotation')
        x, y, width, height = map(_d, [at[1], at[2], size[1], size[2]])
        if width <= 0 or height <= 0:
            raise ValueError('Nonpositive pad size')
        bounds = [min(bounds[0], x-width/2), min(bounds[1], y-height/2),
                  max(bounds[2], x+width/2), max(bounds[3], y+height/2)]
    courtyard = [
        ((bounds[i]+(-ALLOWANCE_MM if i < 2 else ALLOWANCE_MM))/GRID_MM)
        .to_integral_value(rounding=ROUND_FLOOR if i < 2 else ROUND_CEILING)*GRID_MM
        for i in range(4)]
    return {
        'name': name, **ENVELOPES[name], 'pad_count': len(pads),
        'body_and_copper_bounds_mm': [float(v) for v in bounds],
        'courtyard_bounds_mm': [float(v) for v in courtyard],
        'courtyard_allowance_mm': float(ALLOWANCE_MM),
        'courtyard_outward_rounding_grid_mm': float(GRID_MM),
        'manufacturing_ready': False,
    }


def add_courtyard(text):
    """Append only sourced F.CrtYd geometry; unknown footprints pass unchanged."""
    g = geometry(text)
    if g is None:
        return text
    tree = parse(text)
    existing = [item for item in tree if isinstance(item, list) and
                item and item[0].startswith('fp_') and
                child(item, 'layer') is not None and
                value(child(item, 'layer')[1]) == 'F.CrtYd']
    if existing:
        if len(existing) != 1 or existing[0][0] != 'fp_rect':
            raise ValueError('Unreviewed existing courtyard')
        start, end = child(existing[0], 'start'), child(existing[0], 'end')
        actual = [float(start[1]), float(start[2]), float(end[1]), float(end[2])]
        if actual != g['courtyard_bounds_mm']:
            raise ValueError('Existing courtyard differs from sourced envelope')
        return text
    x1, y1, x2, y2 = g['courtyard_bounds_mm']
    rectangle = (f'\n(fp_rect (start {x1:g} {y1:g}) (end {x2:g} {y2:g}) '
                 '(stroke (width 0.05) (type default)) (fill none) '
                 '(layer "F.CrtYd"))\n')
    pos = text.rfind(')')
    if pos < 0:
        raise ValueError('Incomplete footprint expression')
    return text[:pos]+rectangle+text[pos:]


def source_paths():
    return sorted({c['source_path'] for c in ENVELOPES.values()})


def sourced_receipt(text):
    result = geometry(text)
    if result is not None:
        result['source_sha256'] = hashlib.sha256(
            (ROOT/result['source_path']).read_bytes()).hexdigest()
    return result
