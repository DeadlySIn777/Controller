# Per-net pad partitions (which pads are connected to which) for EVERY net, uncapped, optionally after a zone
# refill on the in-memory copy (the input file is never written). Used to count, between two revisions, the
# connections COMPLETED and the connections LOST, not just the net change.
#   python.exe net_partitions.py board.kicad_pcb out.json [--refill]
# A pad is named "REF.NUMBER#k" (k = 0,1,... for repeated pad numbers in one footprint, in pad order).
# Output: {"board", "sha256", "refilled", "api_unconnected_count", "pad_island_joins", "tracks", "vias",
#          "nets": {name: [[pad, pad, ...], [pad, ...], ...]}}   (every net with >= 2 pads)
import collections
import hashlib
import json
import sys

import pcbnew

board, out_p = sys.argv[1], sys.argv[2]
refill = "--refill" in sys.argv[3:]
sha = hashlib.sha256(open(board, "rb").read()).hexdigest()
b = pcbnew.LoadBoard(board)
if refill:
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.BuildConnectivity()
conn = b.GetConnectivity()
pads_by_net = collections.defaultdict(list)
pad_name = {}
for f in b.GetFootprints():
    seen_num = collections.Counter()
    for p in f.Pads():
        num = str(p.GetNumber())
        pad_name[p.m_Uuid.AsString()] = f"{f.GetReference()}.{num}#{seen_num[num]}"
        seen_num[num] += 1
        if p.GetNetCode() > 0:
            pads_by_net[p.GetNetCode()].append(p)
names = {c: str(n.GetNetname()) for c, n in b.GetNetsByNetcode().items()}
nets, joins_missing = {}, 0
for code, pads in pads_by_net.items():
    if len(pads) < 2:
        continue
    seen, groups = set(), []
    for p in pads:
        k = p.m_Uuid.AsString()
        if k in seen:
            continue
        seen.add(k)
        grp, q = [pad_name[k]], [p]
        while q:
            cur = q.pop()
            for o in conn.GetConnectedItems(cur):
                if o.GetClass() != "PAD" or o.GetNetCode() != code:
                    continue
                ok = o.m_Uuid.AsString()
                if ok not in seen:
                    seen.add(ok)
                    grp.append(pad_name[ok])
                    q.append(o)
        groups.append(sorted(grp))
    nets[names[code]] = sorted(groups)
    joins_missing += len(groups) - 1
tracks = sum(1 for t in b.GetTracks() if t.GetClass() != "PCB_VIA")
vias = sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_VIA")
json.dump({"board": board, "sha256": sha, "refilled": refill, "api_unconnected_count": conn.GetUnconnectedCount(False),
           "pad_island_joins": joins_missing, "tracks": tracks, "vias": vias, "nets": nets},
          open(out_p, "w", encoding="utf-8"))
print(json.dumps({"sha256": sha[:16], "refilled": refill, "api_unconnected_count": conn.GetUnconnectedCount(False),
                  "pad_island_joins": joins_missing, "tracks": tracks, "vias": vias}))
