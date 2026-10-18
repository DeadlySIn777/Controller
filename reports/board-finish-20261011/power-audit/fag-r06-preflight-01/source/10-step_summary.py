# Summary of one revision measurement directory (drc.json + partitions.json) -> summary.json.
#   python step_summary.py <dir>
import collections
import json
import sys

o = sys.argv[1]
d = json.load(open(o + "/drc.json", encoding="utf-8"))
p = json.load(open(o + "/partitions.json", encoding="utf-8"))
c = collections.Counter((v["type"], v["severity"]) for v in d["violations"])
err = sum(n for (t, s), n in c.items() if s == "error")
war = sum(n for (t, s), n in c.items() if s == "warning")
s = {"board_sha256": p["sha256"], "kicad": d.get("kicad_version"),
     "drc_flags": "--refill-zones --severity-all --all-track-errors --schematic-parity",
     "drc_by_category": {f"{t} [{sv}]": n for (t, sv), n in sorted(c.items())},
     "drc_errors": err, "drc_warnings": war, "drc_violations_total_excluding_unconnected": err + war,
     "unconnected_items_in_drc_report_capped": len(d.get("unconnected_items", [])),
     "unconnected_api_uncapped": p["api_unconnected_count"], "missing_pad_joins": p["pad_island_joins"],
     "schematic_parity_items": len(d.get("schematic_parity", [])), "tracks": p["tracks"], "vias": p["vias"],
     "possibly_capped_categories": [f"{t} [{sv}]" for (t, sv), n in c.items() if n in (199, 200, 499, 500)]}
json.dump(s, open(o + "/summary.json", "w"), indent=1)
print(json.dumps(s))
