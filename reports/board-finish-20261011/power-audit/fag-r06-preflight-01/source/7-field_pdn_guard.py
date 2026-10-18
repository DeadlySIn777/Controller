# Guard for tools/producer_field_pdn.sh (KiCad 10 python.exe): the applied board may differ from the input ONLY by
# added, locked In3 tracks and through vias of the four field nets listed in routes.json.
#   python.exe field_pdn_guard.py in.kicad_pcb applied.kicad_pcb routes.json out.json   (exit 1 on any other change)
import json
import sys

import pcbnew

src, dst, routes_p, out_p = sys.argv[1:5]
R = json.load(open(routes_p, encoding="utf-8"))
nets = {r["net"] for r in R["tracks"]}
# corridor_apply.py writes one track per non-degenerate polyline piece (pieces shorter than 1e-6 mm are skipped)
n_tr = sum(1 for r in R["tracks"] if r.get("kind") != "via" for (ax, ay), (bx, by) in zip(r["points"], r["points"][1:])
           if abs(ax - bx) >= 1e-6 or abs(ay - by) >= 1e-6)
n_v = sum(1 for r in R["tracks"] if r.get("kind") == "via")


def snap(path):
    b = pcbnew.LoadBoard(path)
    tr = {}
    for t in b.GetTracks():
        k = t.m_Uuid.AsString()
        if t.GetClass() == "PCB_VIA":
            tr[k] = ("via", t.GetNetname(), t.GetPosition().x, t.GetPosition().y, t.GetWidth(pcbnew.F_Cu), t.GetDrillValue(), t.IsLocked())
        else:
            tr[k] = (t.GetClass(), t.GetNetname(), b.GetLayerName(t.GetLayer()), t.GetStart().x, t.GetStart().y, t.GetEnd().x,
                     t.GetEnd().y, t.GetWidth(), t.IsLocked())
    zs = {}
    for z in b.Zones():
        o = z.Outline()
        zs[z.m_Uuid.AsString()] = (z.GetNetname(), tuple(b.GetLayerName(l) for l in z.GetLayerSet().Seq()), o.FullPointCount(),
                                   round(o.Area()), z.GetAssignedPriority())
    fp = {f.m_Uuid.AsString(): (f.GetReference(), f.GetPosition().x, f.GetPosition().y, f.GetOrientationDegrees(), f.IsFlipped(),
                                tuple((p.GetNumber(), p.GetNetname()) for p in f.Pads())) for f in b.GetFootprints()}
    dr = {d.m_Uuid.AsString(): (d.GetClass(), b.GetLayerName(d.GetLayer())) for d in b.GetDrawings()}
    return tr, zs, fp, dr


a_tr, a_z, a_fp, a_dr = snap(src)
b_tr, b_z, b_fp, b_dr = snap(dst)
bad = []
removed = [k for k in a_tr if k not in b_tr]
changed = [k for k in a_tr if k in b_tr and a_tr[k] != b_tr[k]]
added = [k for k in b_tr if k not in a_tr]
if removed:
    bad.append(f"{len(removed)} tracks/vias removed")
if changed:
    bad.append(f"{len(changed)} tracks/vias changed")
add_tr = [b_tr[k] for k in added if b_tr[k][0] != "via"]
add_v = [b_tr[k] for k in added if b_tr[k][0] == "via"]
for t in add_tr:
    if t[2] != "In3.Cu" or t[1] not in nets or not t[-1]:
        bad.append(f"added track not a locked In3 track of a field net: {t[:3]}")
        break
for v in add_v:
    if v[1] not in nets or not v[-1]:
        bad.append(f"added via not a locked via of a field net: {v[:2]}")
        break
if len(add_tr) != n_tr or len(add_v) != n_v:
    bad.append(f"added {len(add_tr)} tracks / {len(add_v)} vias, routes.json has {n_tr} / {n_v}")
if a_z != b_z:
    bad.append("zones differ (outline, net, layers or priority)")
if a_fp != b_fp:
    bad.append("footprints differ")
if set(a_dr) != set(b_dr):
    bad.append("board drawings differ")
res = {"ok": not bad, "problems": bad, "added_tracks": len(add_tr), "added_vias": len(add_v), "removed": len(removed),
       "changed": len(changed), "nets": sorted(nets), "zones": len(b_z), "footprints": len(b_fp)}
json.dump(res, open(out_p, "w"), indent=1)
print(json.dumps(res))
sys.exit(0 if not bad else 1)
