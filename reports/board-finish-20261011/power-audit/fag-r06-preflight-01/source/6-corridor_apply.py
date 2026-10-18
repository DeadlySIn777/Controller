# Apply corridor_router output to a board: polyline -> PCB_TRACK segments on the named layer/net.
#   python.exe corridor_apply.py in.kicad_pcb routes.json out.kicad_pcb [--lock]
import json
import sys

import pcbnew

src, routes_p, dst = sys.argv[1:4]
lock = "--lock" in sys.argv
b = pcbnew.LoadBoard(src)
R = json.load(open(routes_p, encoding="utf-8"))
F = pcbnew.FromMM
n = 0
nv = 0
for r in R["tracks"]:
    net = b.FindNet(r["net"])
    if net is None:
        raise SystemExit(f"net not on board: {r['net']}")
    if r.get("kind") == "via":
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(F(r["x"]), F(r["y"])))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetWidth(F(r["d"]))
        v.SetDrill(F(r["drill"]))
        v.SetNet(net)
        v.SetLocked(lock)
        b.Add(v)
        nv += 1
        continue
    layer = b.GetLayerID(r["layer"])
    pts = r["points"]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        if abs(ax - bx) < 1e-6 and abs(ay - by) < 1e-6:
            continue
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(F(ax), F(ay)))
        t.SetEnd(pcbnew.VECTOR2I(F(bx), F(by)))
        t.SetWidth(F(r["width"]))
        t.SetLayer(layer)
        t.SetNet(net)
        t.SetLocked(lock)
        b.Add(t)
        n += 1
b.Save(dst)
print(json.dumps({"segments_added": n, "vias_added": nv, "routes": len(R["tracks"]), "failures": len(R.get("failures", []))}))
