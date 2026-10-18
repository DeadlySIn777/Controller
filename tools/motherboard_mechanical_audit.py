"""Read-only native PCB/module/mate mechanical screening. Run with KiCad Python.

No PCB/schematic mutations. Manufacturer module envelopes are distinguished from
conservative engineering cable/extraction reservations. Native filled copper is
screened as well as component bodies; this is not a 3D assembly qualification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
from datetime import datetime, timezone

import pcbnew as p

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = [
    "reports/board-completion-20260930/compute-bay-pin-audit/sources/cm5-datasheet.pdf",
    "reports/board-completion-20260930/compute-bay-pin-audit/sources/cm4-datasheet.pdf",
    "reports/motherboard-esp-socket-20260930/espressif-s3-devkit-dimensions.dxf",
    "reports/motherboard-esp-socket-20260930/espressif-s3-devkit-dimensions.pdf",
    "reports/motherboard-compute-20260930/sources/wurth-usba-614004134726.pdf",
    "reports/motherboard-compute-20260930/sources/gct-usb4105.pdf",
    "reports/motherboard-compute-20260930/sources/wurth-7499111446.pdf",
    "reports/motherboard-compute-20260930/sources/edac-690-019-298-412-mfr-drawing.pdf",
    "reports/motherboard-compute-20260930/sources/molex-5033981892-manufacturer-drawing-mirror.pdf",
    "reports/motherboard-cost-20260930/power-mates/power-mates-review.json",
    "reports/motherboard-cost-20260930/power-mates/1757019-manufacturer.pdf",
    "hardware/motherboard_compute/design.json",
    "hardware/motherboard_esp_socket/design.json",
    "reports/motherboard-mechanical-20260930/primary-drawing-review/espressif-module-layout.html",
    "reports/motherboard-mechanical-20260930/primary-drawing-review/pcbway-manufacturing-tolerances.html",
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def xy(v):
    return [round(p.ToMM(v.x), 6), round(p.ToMM(v.y), 6)]


def rect(bb):
    return [p.ToMM(bb.GetLeft()), p.ToMM(bb.GetTop()),
            p.ToMM(bb.GetRight()), p.ToMM(bb.GetBottom())]


def overlap(a, b, tol=1e-6):
    return min(a[2], b[2])-max(a[0], b[0]) > tol and min(a[3], b[3])-max(a[1], b[1]) > tol


def merge(rs):
    return [min(r[0] for r in rs), min(r[1] for r in rs),
            max(r[2] for r in rs), max(r[3] for r in rs)] if rs else None


def transform(fp, pt):
    a = math.radians(fp.GetOrientationDegrees())
    q = xy(fp.GetPosition())
    return [round(q[0]+pt[0]*math.cos(a)+pt[1]*math.sin(a), 6),
            round(q[1]-pt[0]*math.sin(a)+pt[1]*math.cos(a), 6)]


def transformed_box(fp, r):
    q = [transform(fp, x) for x in [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]]
    return [min(x[0] for x in q), min(x[1] for x in q), max(x[0] for x in q), max(x[1] for x in q)]


def grown(r, x):
    return [r[0]-x, r[1]-x, r[2]+x, r[3]+x]


def graphic_box(fp, layer):
    # Reference/value text must never enlarge the native body proxy.
    return merge([rect(g.GetBoundingBox()) for g in fp.GraphicalItems()
                  if g.GetLayer() == layer and isinstance(g, p.PCB_SHAPE)])


def body_box(fp):
    r = graphic_box(fp, p.F_Fab)
    if r is not None:
        return r, "native F.Fab graphics bounding rectangle (includes stroke)"
    r = graphic_box(fp, p.F_CrtYd)
    if r is not None:
        return r, "native F.CrtYd fallback; conservative body proxy"
    return merge([rect(x.GetBoundingBox()) for x in fp.Pads()]), "native pad bbox fallback; body not established"


def inside(pt, r):
    return r[0] <= pt[0] <= r[2] and r[1] <= pt[1] <= r[3]


def segment_hit(a, b, r):
    # Liang-Barsky, inclusive. Used after expanding by copper half width.
    lo, hi = 0.0, 1.0
    dx, dy = b[0]-a[0], b[1]-a[1]
    for den, num in [(-dx, a[0]-r[0]), (dx, r[2]-a[0]), (-dy, a[1]-r[1]), (dy, r[3]-a[1])]:
        if abs(den) < 1e-12:
            if num < 0:
                return False
        elif den < 0:
            lo = max(lo, num/den)
        else:
            hi = min(hi, num/den)
        if lo > hi:
            return False
    return True


def filled_zone_hit(zone, layer, r):
    poly = zone.GetFilledPolysList(layer)
    if poly.OutlineCount() == 0:
        return False
    pts = [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3]),
           ((r[0]+r[2])/2, (r[1]+r[3])/2)]
    if any(poly.Contains(p.VECTOR2I(p.FromMM(x), p.FromMM(y))) for x, y in pts):
        return True
    for n in range(poly.OutlineCount()):
        line = poly.COutline(n)
        q = [xy(line.CPoint(k)) for k in range(line.PointCount())]
        for a, b in zip(q, q[1:]+q[:1]):
            if segment_hit(a, b, r):
                return True
    return False


def copper_hits(board, r):
    tracks, pads, zones = [], [], []
    for t in board.GetTracks():
        if not overlap(rect(t.GetBoundingBox()), r):
            continue
        hit = True if isinstance(t, p.PCB_VIA) else segment_hit(xy(t.GetStart()), xy(t.GetEnd()), grown(r, p.ToMM(t.GetWidth())/2))
        if hit:
            tracks.append({"uuid": t.m_Uuid.AsString(), "type": t.GetClass(), "net": t.GetNetname(), "layer": board.GetLayerName(t.GetLayer())})
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if overlap(rect(pad.GetBoundingBox()), r):
                pads.append({"ref": fp.GetReference(), "pad": pad.GetNumber(), "net": pad.GetNetname(), "bbox_mm": rect(pad.GetBoundingBox())})
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        for layer in z.GetLayerSet().Seq():
            if board.IsLayerEnabled(layer) and p.IsCopperLayer(layer) and filled_zone_hit(z, layer, r):
                zones.append({"uuid": z.m_Uuid.AsString(), "net": z.GetNetname(), "layer": board.GetLayerName(layer)})
    return {"tracks_vias": tracks, "pads": pads, "filled_zones": zones,
            "counts": {"tracks_vias": len(tracks), "pads": len(pads), "filled_zones": len(zones)},
            "method": "segment/width+via and pad bounding screens; actual native filled-zone Contains/outline intersection. Curved copper and body/pad rectangular proxies remain conservative."}


def self_tests():
    assert overlap([0,0,1,1], [.5,.5,2,2])
    assert not overlap([0,0,1,1], [1,1,2,2])
    assert segment_hit([-1,.5],[2,.5],[0,0,1,1])
    assert not segment_hit([-1,2],[2,2],[0,0,1,1])
    assert segment_hit([.5,-1],[.5,2],[0,0,1,1])
    assert not segment_hit([-1,-1],[-2,-2],[0,0,1,1])
    assert not inside([2,2], [0,0,1,1])
    return 7


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, required=True)
    ap.add_argument("--source", type=Path, default=ROOT/"reports/motherboard-integration-20260930/r20b-2663-electrical-corrections-staged/design.json")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    out = args.output.resolve()
    if out.exists() and (out/"review.json").exists():
        raise SystemExit("Immutable mechanical report already exists; use a new output directory")
    out.mkdir(parents=True, exist_ok=True)
    before = sha(args.board)
    shutil.copyfile(args.board, out/"input-board.kicad_pcb")
    shutil.copyfile(args.source, out/"input-source-design.json")
    shutil.copyfile(__file__, out/"issued-audit-tool.py")
    board = p.LoadBoard(str(out/"input-board.kicad_pcb"))
    source = json.loads((out/"input-source-design.json").read_text(encoding="utf-8"))
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    edges = [s for s in board.GetDrawings() if isinstance(s,p.PCB_SHAPE) and s.GetLayer()==p.Edge_Cuts]
    if len(edges)==4 and all(int(s.GetShape())==0 for s in edges):
        edge_pts = [xy(v) for s in edges for v in [s.GetStart(),s.GetEnd()]]
        bb = [min(v[0] for v in edge_pts),min(v[1] for v in edge_pts),max(v[0] for v in edge_pts),max(v[1] for v in edge_pts)]
        edge_method = "Exact four native Edge.Cuts segment centre-lines; graphic stroke excluded"
    elif len(edges)==10 and sum(s.GetShape()==p.SHAPE_T_ARC for s in edges)==2 and all(s.GetShape()in (p.SHAPE_T_SEGMENT,p.SHAPE_T_ARC)for s in edges):
        edge_pts=[xy(v)for s in edges for v in [s.GetStart(),s.GetEnd()]]
        bb=[min(v[0]for v in edge_pts),min(v[1]for v in edge_pts),max(v[0]for v in edge_pts),max(v[1]for v in edge_pts)]
        required=[(424.8,340),(424.8,339.3),(425.3,338.8),(443.8,338.8),(444.3,339.3),(444.3,340)]
        if bb!=[0,0,460,340]or any(not any(math.dist(q,w)<.001 for q in edge_pts)for w in required):
            raise SystemExit('Unknown ten-element outline; exact approved RF-notch profile required')
        if any(abs(p.ToMM(s.GetRadius())-.5)>.001 for s in edges if s.GetShape()==p.SHAPE_T_ARC):
            raise SystemExit('RF-notch corner radius differs from reviewed0.5mm profile')
        edge_method='Exact native460x340 outer edges plus source-reviewed1.2mm ESP RF notch x424.8..444.3 with0.5mm inside arcs; stroke excluded. Bbox is not used as a copper/fit proof of notch material.'
    else:
        raise SystemExit("Audit requires independently reviewed rectangular or exact RF-notch outline; do not approximate unknown shapes by bbox")
    component_boxes = {ref: body_box(f) for ref, f in fps.items()}

    def components_hit(r, exclude=()):
        found = []
        for ref, (b, method) in component_boxes.items():
            if ref in exclude or b is None:
                continue
            if overlap(b, r):
                found.append({"ref": ref, "body_proxy_mm": b, "method": method,
                              "MPN": source["components"].get(ref, {}).get("mpn"),
                              "side": board.GetLayerName(fps[ref].GetLayer())})
        return sorted(found, key=lambda d: d["ref"])

    data = {"date_utc": datetime.now(timezone.utc).isoformat(), "board_path": str(args.board.resolve()),
            "board_sha256": before, "source_path": str(args.source.resolve()), "source_sha256": sha(args.source),
            "native_footprints": len(fps), "source_physical_parts": len(source["components"]),
            "source_missing_from_board": sorted(set(source["components"])-set(fps)),
            "board_extra_refs": sorted(set(fps)-set(source["components"])),
            "board_edges_bbox_mm": bb, "board_outline_method":edge_method,
            "native_edge_graphic_stroke_bbox_mm":rect(board.GetBoardEdgesBoundingBox()),
            "layer_count": board.GetCopperLayerCount(),
            "physical_qualification": False, "manufacturing_ready": False,
            "native_geometry_is_read_only": True, "self_tests_passed": self_tests(),
            "strict_3D_interference_check": False,
            "limitations": ["Body proxies are 2D and many installed component heights are not source qualified.",
                            "No enclosure, heatsink, display frame, cable SKU or fastener assembly is qualified.",
                            "Service/extraction reservation sizes are engineering screens, not manufacturer cable dimensions.",
                            "Any footprint absent from this exact board cannot receive a mechanical pass."]}
    if "J15001" in fps and "J15002" in fps:
        a, b = fps["J15001"], fps["J15002"]
        expected_b = transform(a, [34,0])
        holes = sorted([xy(z.GetPosition()) for f in [a,b] for z in f.Pads() if z.GetAttribute() == p.PAD_ATTRIB_NPTH])
        cm = transformed_box(a, [-3,-30,37,25])
        antenna = transformed_box(a, [6,18.5,17,25])
        clear = grown(antenna, 10)
        pose_ok = math.dist(expected_b, xy(b.GetPosition())) < .001 and abs(a.GetOrientationDegrees()-b.GetOrientationDegrees()) < .001
        assert math.dist(xy(next(z for z in a.Pads() if z.GetNumber()=="1").GetPosition()), transform(a,[-1.54,-9.8])) < .001
        data["compute"] = {"socket_A_pose": [*xy(a.GetPosition()), a.GetOrientationDegrees()],
                           "socket_B_pose": [*xy(b.GetPosition()), b.GetOrientationDegrees()],
                           "socket_pair_34mm_same_rotation_pass": pose_ok,
                           "mount_holes_mm": holes, "expected_mount_grid_mm": [33,48],
                           "hole_diameters_mm": [xy(z.GetDrillSize()) for f in [a,b] for z in f.Pads() if z.GetAttribute()==p.PAD_ATTRIB_NPTH],
                           "module_40x55_envelope_mm": cm, "manufacturer_mated_height_mm": 1.5,
                           "manufacturer_CM5_under_clearance_mm": 0,
                           "under_module_body_conflicts": components_hit(cm, ["J15001","J15002"]),
                           "antenna_6p5x11_cutout_mm": antenna,
                           "antenna_min_10mm_clearance_bbox_mm": clear,
                           "antenna_under_copper": copper_hits(board, antenna),
                           "antenna_10mm_component_conflicts": components_hit(clear,["J15001","J15002"]),
                           "heatsink_SKU": None, "heatsink_assembly_clearance_pass": None,
                           "CM5_mounted_top_height_mm": 4.94,
                           "reference": "Raspberry Pi CM5 datasheet printed pp16-17/Figure4, official CM5IO source socket origins"}
    if "J16001" in fps and "J16002" in fps:
        a, b = fps["J16001"], fps["J16002"]
        esp = transformed_box(a, [-1.27,-1.565,24.13,61.3])
        antenna = transformed_box(a, [2.48,-7.85,20.48,-1.54])
        clear = grown(antenna,15)
        # Axis aligned native current candidate, this screen rejects ambiguous other angles.
        angle_ok = abs(a.GetOrientationDegrees()/90-round(a.GetOrientationDegrees()/90)) < .001
        data["ESP"] = {"socket_A_pose": [*xy(a.GetPosition()),a.GetOrientationDegrees()],
                       "socket_B_pose": [*xy(b.GetPosition()),b.GetOrientationDegrees()],
                       "22p86mm_pair_same_rotation_pass": math.dist(transform(a,[22.86,0]),xy(b.GetPosition()))<.001 and abs(a.GetOrientationDegrees()-b.GetOrientationDegrees())<.001,
                       "native_pin22_53p34mm_offset_pass": math.dist(transform(a,[0,53.34]),xy(next(z for z in a.Pads() if z.GetNumber()=="22").GetPosition()))<.001,
                       "PCB_body_25p4x62p865_mm": esp,
                       "body_overlap_2D_requires_installed_height_review": components_hit(esp,["J16001","J16002"]),
                       "antenna_DXF18x6p31_mm": antenna,
                       "antenna_entirely_outside_motherboard_pass": angle_ok and not overlap(antenna,bb),
                       "antenna_over_board_intersection_mm": [max(bb[0],antenna[0]),max(bb[1],antenna[1]),min(bb[2],antenna[2]),min(bb[3],antenna[3])],
                       "antenna_15mm_RF_reservation_mm": clear,
                       "antenna_under_copper": copper_hits(board,antenna),
                       "RF_15mm_copper_screen": copper_hits(board,clear),
                       "RF_15mm_component_conflicts": components_hit(clear,["J16001","J16002"]),
                       "RF_15mm_screen_is_not_blanket_rejection_of_the_modules_own_purchased_headers": True,
                       "RF_guideline_scope": "Espressif prefers antenna outside baseboard. End-product housing/nearby-metal clearance of at least15mm is recommended in all directions. This screen identifies extrinsic metallic component/body/copper candidates; purchased module/socket geometry is separately identified, not labelled a violated mandatory15mm no-copper rule behind the antenna feed.",
                       "USB_access_end": transformed_box(a, [-1.27,53.34,24.13,81.3]),
                       "USB_access_reservation_extra_mm": 20,
                       "USB_access_conflicts": components_hit(transformed_box(a,[-1.27,61.3,24.13,81.3])),
                       "socket_standoff_or_under_module_height_pass": None,
                       "reference": "Official Espressif v1.1 DXF: header J1 pin1 (1.27,61.3); board 0..25.4/0..62.865; TOP antenna x3.75..21.75/y62.84..69.15. 15mm engineering RF screen follows official hardware guideline recommendation."}
    ports = []
    # Native/local body landmarks independently tied to retained manufacturer drawing.
    # These reservations are intentionally named engineering screening envelopes.
    specs = {"J15003": {"axis": "horizontal -localY", "height_mm": 1.28, "service": [-6.8,-29.33,6.8,-7.025], "detail": "Molex push-push: locked protrusion1.9, eject/dashing2.8, reverse-insertion6.2; 0.5mm minimum forbidden protrusion strip; engineering20mm hand/card extraction."},
             "J15004": {"axis": "horizontal +localY", "height_mm": 6.17, "service": [-10,10.55,10,45.55], "detail": "EDAC body12.14deep,14.55facewidth,6.17high; manufacturer PCB edge at localY10.55. Engineering20mm wide/35mm cable/plug reservation; cable SKU unselected."},
             "J15005": {"axis": "horizontal -localX, upright face", "height_mm": None, "provisional_top_clearance_mm": 14.7, "service": [-52.33,-10,-12.33,10], "detail": "Würth Up Right describes narrow upright face, NOT a vertical mating axis. Native body19.3deep alongX/7.1wide alongY; mouth atlocalX−12.33.17.6±.30 includes3.5±.15 lead protrusion: simple seated-height subtraction gives14.1nominal/14.55conservative. Drawing13.1 and14.5 reference other body/flange datums; reserveatleast14.7mm provisionally pending exact assembly datum. Engineer20mm wide/40mm extraction/cable screen."},
             "J15006": {"axis": "horizontal +localY", "height_mm": 3.3, "service": [-7,3.675,7,33.675], "detail": "GCT body8.94x7.35,3.3height; exact nativePCBedge andmouth localY3.675; mating drawing calls1.85mm minimum plug clearance; engineer14mm wide/30mm extraction/cable screen."},
             "J15007": {"axis": "horizontal +localY", "height_mm": 13.5, "provisional_all_metal_top_clearance_mm": 15.4, "service": [-5.285,19.78,16.715,59.78], "detail": "Exact manufacturerrev1STEP registered byall10 reallead-tail centres proves localmouth+19.780 andfullmetalXY[-3.64145,-1.470,15.06145,19.780]. Body16x21.25/13.5height; EMIspringswidth18.703/topapproximately14.852aboveprovisionalseatingdatum; reserve15.4mm allmetal. NativeFab15.88x21.84 isnotexactmanufacturerbody; courtyardneeds.25mm springassemblymargin. Engineer22mm wide/40mm latch/extraction screen; exactcable/enclosure fit remains qualification."}}
    for ref, spec in specs.items():
        item = {"ref": ref, "MPN": source["components"].get(ref,{}).get("mpn"), "present": ref in fps, **spec}
        if ref in fps:
            f = fps[ref]
            reservation = transformed_box(f,spec["service"])
            item.update({"pose": [*xy(f.GetPosition()),f.GetOrientationDegrees()], "body_proxy_mm": component_boxes[ref][0],
                         "service_reservation_mm": reservation, "service_conflicts_2D": components_hit(reservation,[ref]),
                         "board_edge_access_or_enclosure_cutout_qualified": False,
                         "vertical_access_qualified": None})
        ports.append(item)
    data["compute_ports"] = ports
    power = []
    for n in range(11001,11007):
        ref = f"J{n}"
        item = {"ref": ref, "header_MPN": "1757242", "mate_MPN": "1757019", "present": ref in fps,
                "manufacturer_mate_mm": [10.16,18.3,15], "manufacturer_header_mm": [12.16,12,8.57],
                "full_depth_body_outside_mouth_is_conservative": True,
                "exact_mated_overlap_and_lower_body_height_qualified": False,
                "unmating_extra_engineering_mm": 20, "wire_tool_and_bend_SKU_qualified": False}
        if ref in fps:
            f = fps[ref]
            plug = transformed_box(f,[-2.54,10,7.62,28.3])
            service = transformed_box(f,[-4.04,10,9.12,48.3])
            item.update({"pose": [*xy(f.GetPosition()),f.GetOrientationDegrees()],
                         "pitch_5p08_pass": abs(math.dist(*[xy(z.GetPosition()) for z in sorted(f.Pads(),key=lambda z:z.GetNumber())[:2]])-5.08)<.001,
                         "drill_1p4_pass": all(abs(p.ToMM(z.GetDrillSize().x)-1.4)<.001 and abs(p.ToMM(z.GetDrillSize().y)-1.4)<.001 for z in f.Pads()),
                         "header_body_proxy_mm": component_boxes[ref][0], "conservative_mate_projection_mm": plug,
                         "mate_projection_conflicts_2D": components_hit(plug,[ref]),
                         "service_reservation_mm": service, "service_conflicts_2D": components_hit(service,[ref]),
                         "actual_header_pins": source["components"].get(ref,{}).get("pins")})
        power.append(item)
    data["power_headers_and_mates"] = power
    mount_holes = []
    for ref, f in fps.items():
        for z in f.Pads():
            if z.GetAttribute()==p.PAD_ATTRIB_NPTH:
                mount_holes.append({"ref": ref, "location_mm": xy(z.GetPosition()), "drill_mm": xy(z.GetDrillSize()), "pad": z.GetNumber(),
                                    "not_automatically_a_board_retention_mount": True})
    data["chassis_and_mounting"] = {"H19501_present": "H19501" in fps,
                                    "H19501_body_and_pad_provenance": source["components"].get("H19501"),
                                    "native_NPTH_holes": mount_holes,
                                    "dedicated_board_retention_fastener_system_qualified": False,
                                    "CHASSIS_bond_lug_washer_torque_and_enclosure_qualified": False,
                                    "Y2_HF_capacitors_are_not_DC_domain_bonds_or_proof_of_PE_rating": True}
    data["input_file_unchanged_pass"] = sha(args.board)==before
    assert data["input_file_unchanged_pass"]
    data["primary_local_evidence"] = {path:sha(ROOT/path) for path in PRIMARY if (ROOT/path).exists()}
    (out/"review.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    (out/"component-body-proxies.json").write_text(json.dumps(component_boxes,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"report":str(out),"native_parts":len(fps),"source_parts":len(source["components"]),
                      "CM_underbody_conflicts":len(data.get("compute",{}).get("under_module_body_conflicts",[])),
                      "ESP_RF_entirely_beyond_edge":data.get("ESP",{}).get("antenna_entirely_outside_motherboard_pass"),
                      "missing_ports":[x["ref"] for x in ports if not x["present"]],"input_unchanged":True}))


if __name__ == "__main__":
    main()
