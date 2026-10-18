"""Read-only exact source inspection; small retained output."""
import json
from pathlib import Path
from shapely.geometry import Point
import prepare_sbc_c05_proposal as p

def main():
    g, overlay = p.overlay()
    _, _, _, native, _, _ = p.base.inventory(p.read(p.C05))
    refs = {"U11012", "C11061", "C11062", "C11063", "R11022", "J15001"}
    pads = [pad for pad in g["pads"] if pad["ref"] in refs and (pad["ref"] != "J15001" or pad["num"] in [str(x) for x in (77,79,81,83,85,87)])]
    out = {"board_sha256": p.C05_SHA, "overlay": overlay, "parts": [], "local_tracks": []}
    for ref in sorted(refs):
        foot = next(f for f in g["footprints"] if f["ref"] == ref)
        uid, chunk = next((uid, chunk) for uid, chunk in native.items() if p.base.pcbtext.chunk_kind(chunk) == "footprint" and p.base.ref_of(chunk) == ref)
        out["parts"].append({"ref": ref, "footprint": foot, "uuid": uid, "chunk_sha256": p.hashlib.sha256(chunk).hexdigest(),
            "pose": p.pose(p.base.children(chunk)[1]), "pads": [{k: pad[k] for k in ("uuid", "num", "net", "x", "y", "layers")} for pad in pads if pad["ref"] == ref]})
    window = p.box(216,132,228,146)
    out["local_tracks"] = [t for t in g["tracks"] if p.base.body(t).intersects(window)]
    out["local_vias"] = [v for v in g["vias"] if window.covers(Point(v["x"],v["y"]))]
    out["source_hashes"] = p.READS
    path = p.OUT / "stage-source-inspection.json"
    path.write_text(json.dumps(out, indent=2)+"\n")
    for part in out["parts"]:
        print(part["ref"],part["pose"],[(pad["num"],pad["net"],pad["x"],pad["y"]) for pad in part["pads"]])
    print(path)

if __name__ == "__main__":
    main()
