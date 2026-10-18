"""Distinct local source-only screen; Cu-radius hole envelope, no native writes.

Earlier hole screens used prospective drill radius and are unqualified.
This wrapper only changes its in-memory imported helper bindings.
"""
import json
from pathlib import Path

from shapely.geometry import Point
from shapely.ops import unary_union

import prepare_sbc_local_v5 as five

p, v = five.p, five.v
_old_via_region = five.via_region
_old_landing = p.landing


def copper_hole_obstructions(g, window, diameter):
    """Existing hole edge to prospective copper edge >= .25 + .025 mm."""
    radius = diameter / 2
    blockers = []
    for pad in g["pads"]:
        for hole in p.base.polygons(pad.get("hole") or []):
            if hole.intersects(window.buffer(2)):
                blockers.append(hole.buffer(radius + .25 + p.MARGIN))
    for via in g["vias"]:
        point = Point(via["x"], via["y"])
        if point.intersects(window.buffer(2)):
            blockers.append(point.buffer(via["drill"] / 2 + radius + .25 + p.MARGIN))
    return unary_union(blockers)


def via_region(g, areas, net, diameter, drill):
    # The old hole-hole screen remains; the stronger hole-copper screen is added.
    region = _old_via_region(g, areas, net, diameter, drill).difference(
        copper_hole_obstructions(g, v.VIA_WINDOW, diameter))
    blockers = []
    domain = g["domains_normalized"].get(p.norm(net))
    for graphic in g["shapes"]:
        if p.norm(graphic["net"]) != p.norm(net):
            gap = .15 if g["domains_normalized"].get(p.norm(graphic["net"])) == domain else .6
            blockers.extend(poly.buffer(diameter / 2 + gap + p.MARGIN)
                for poly in p.base.polygons(graphic["poly"]) if poly.intersects(v.VIA_WINDOW.buffer(2)))
    return region.difference(unary_union(blockers))


def landing(g, areas, terminal, window):
    # Every power array site remains .6/.3, regardless of OPI signal-via case.
    # Recheck all source copper against the same full .025 margin as signal vias;
    # old source_screen supplied front connectivity but had no copper margin.
    old_window = v.VIA_WINDOW
    try:
        v.VIA_WINDOW = window
        all_layer_legal = via_region(g, areas, p.NET, .6, .3)
    finally:
        v.VIA_WINDOW = old_window
    return _old_landing(g, areas, terminal, window).intersection(all_layer_legal)


def main():
    # Frozen producers remain unchanged. Invoke a distinct compiled copy of the
    # bounded driver, with current helper globals and distinct result filename.
    five.via_region = via_region
    p.landing = landing
    source = Path(five.__file__).read_text(encoding="utf-8")
    source = source[source.index("def main():"):source.index('\n\nif __name__ == "__main__":')]
    source = source.replace('"local-cap-opi-v5.json"', '"local-cap-opi-v6.json"')
    source = source.replace('"Source-only exact-endpoint local re-layout and conservative return/source-array coexistence screen"',
        '"Source-only exact-endpoint local screen with prospective copper-radius hole exclusion"')
    source = source.replace('"earlier_v2_v3_v4_detour_negatives_superseded": True,',
        '"earlier_v2_v3_v4_detour_negatives_superseded": True, "earlier_v5_hole_screen_unqualified": True, '
        '"prospective_hole_to_copper_mm": .25, "hole_planner_margin_mm": .025, '
        '"prospective_copper_radius_used_for_hole_obstruction": True,')
    source = source.replace('Path(__file__), Path(four.__file__)',
        'Path(__file__), Path(five.__file__), Path(__file__).with_name("test_sbc_hole_envelope.py"), Path(four.__file__)')
    scope = dict(five.__dict__)
    scope.update({"__file__": __file__, "five": five, "via_region": via_region})
    exec(compile(source, str(Path(__file__).resolve()) + ":bounded-driver", "exec"), scope)
    scope["main"]()


if __name__ == "__main__":
    main()
