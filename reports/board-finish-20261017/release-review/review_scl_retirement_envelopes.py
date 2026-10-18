"""Independent conservative circle-envelope/contact audit of the SCL packet."""
from pathlib import Path
import hashlib
import json
import math
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = HERE / "overlap-retirement-independent-r1"
R299 = ROOT / "reports/board-finish-20261011/continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299"
PACKET = ROOT / "reports/board-finish-20261017/power-review/overlapping-scl-holes-r1/repair-receipt.json"
DROP = "67c69f6a-075b-465b-96c4-89a8aff35b02"
KEEP = "8f6b8734-8176-4fbf-b83d-1da358cb6d7e"
NET = "/motherboard_acc_control{slash}AO_I2C_SCL_HOST"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
paths = [PACKET, Path(__file__), R299 / "native-full/actual-full-refill-geometry.json", R299 / "native-full/actual-full-refill-via-flashes.json"]
pins = {str(p): sha(p) for p in paths}
g = json.loads(paths[2].read_text()); f = json.loads(paths[3].read_text())["vias"]
v = {v["uuid"]: v for v in g["vias"]}; old = v[DROP]; keep = v[KEEP]
layers = f[DROP]
assert layers == f[KEEP] == ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"]
assert old["net"] == keep["net"] == NET
Q = 1024
factor = 1 / math.cos(math.pi / (4 * Q))
disk = lambda at, radius, outer=False: Point(at).buffer(radius * (factor if outer else 1), quad_segs=Q)
near_holes = []
for row in g["vias"]:
    if math.dist(row["at"], old["at"]) <= row["drill"] / 2 + .31 or math.dist(row["at"], keep["at"]) <= row["drill"] / 2 + .31:
        near_holes.append({"kind": "via", "uuid": row["uuid"], "at": row["at"], "radius": row["drill"] / 2})
for row in g["pads"]:
    drill = row["drill"]
    if drill and (math.dist(row["at"], old["at"]) <= drill / 2 + .31 or math.dist(row["at"], keep["at"]) <= drill / 2 + .31):
        near_holes.append({"kind": "pad", "ref": row["ref"], "pin": row["num"], "at": row["at"], "radius": drill / 2})
assert {p["uuid"] for p in near_holes if p["kind"] == "via"} == {DROP, KEEP}
assert not any(p["kind"] == "pad" for p in near_holes)
holes_lower = unary_union([disk(p["at"], p["radius"]) for p in near_holes])
holes_upper = unary_union([disk(p["at"], p["radius"], True) for p in near_holes])
old_upper = disk(old["at"], .3, True).difference(holes_lower)
kept_lower = disk(keep["at"], .3).difference(holes_upper)
rows = []
assert not any(z.get("net") == NET for z in g["zones"])
for layer in layers:
    entities = []
    for t in g["tracks"]:
        if t["net"] == NET and t["layer"] == layer:
            line = LineString([t["s"], t["e"]])
            entities.append((t["uuid"], "track", line.buffer(t["w"] / 2 * factor, quad_segs=Q).difference(holes_lower), line.buffer(t["w"] / 2, quad_segs=Q).difference(holes_upper)))
    for p in g["pads"]:
        if p["net"] == NET and layer in p["layers"]:
            shape = unary_union([Polygon(r[0], r[1:]) for r in p["poly"]])
            entities.append((p["ref"] + "." + p["num"], "pad", shape.difference(holes_lower), shape.difference(holes_upper)))
    for p in g["vias"]:
        if p["net"] == NET and p["uuid"] not in {DROP, KEEP} and layer in f[p["uuid"]]:
            entities.append((p["uuid"], "via", disk(p["at"], p["w"] / 2, True).difference(holes_lower), disk(p["at"], p["w"] / 2).difference(holes_upper)))
    for uid, kind, upper, lower in entities:
        if upper.intersects(old_upper):
            lower_contact = lower.intersection(kept_lower).area
            assert lower_contact > .004, (uid, layer, lower_contact)
            rows.append({"entity": uid, "kind": kind, "layer": layer, "retained_positive_contact_lower_envelope_mm2": lower_contact})
expected = json.loads(PACKET.read_text())
assert {(r["entity"], r["layer"]) for r in rows} == {(r["entity"], r["layer"]) for r in expected["all_external_old_finite_layer_contacts"]}
assert len(rows) == 3
distance = math.dist(old["at"], keep["at"])
assert distance / 2 + .1 < .3
report = {"verdict": "PASS_INDEPENDENT_UPPER_OLD_INVENTORY_LOWER_RETAINED_CONTACT_ENVELOPES",
          "retire": DROP, "retain": KEEP, "all_six_actual_flashes_preserved_by_survivor": True,
          "nearby_actual_drill_inventory": near_holes,
          "all_existing_external_contacts": rows,
          "circumscribed_old_outer_and_tracks_inscribed_old_holes_inventory": True,
          "inscribed_retained_outer_and_tracks_circumscribed_holes_contact_lower_bound": True,
          "hole_cuts_of_removed_barrel_retained_conservatively_during_contact_proof": True,
          "same_net_zones": 0, "extra_contacts_vs_original_receipt": [],
          "new_Ftie_exact_triangle_disk_containment_upper_radius_mm": distance / 2 + .1,
          "new_Ftie_inside_existing_two_0p3_radius_copper_disks": True,
          "native_AFTER_full_refill_masks_no_loss_DRC_remains_required": True,
          "SI_current_reference_and_physical_qualification": "OPEN",
          "input_sha256": pins, "inputs_unchanged": all(sha(Path(p)) == value for p, value in pins.items()),
          "source_or_PCB_changed": False, "adopted": False, "manufacturing_ready": False}
assert not OUT.exists(); OUT.mkdir()
(OUT / "receipt.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"verdict": report["verdict"], "contacts": rows, "inputs_unchanged": report["inputs_unchanged"]}))
