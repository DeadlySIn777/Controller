"""Host geometry screen between two new-copper route sets; never a native DRC gate."""
import hashlib
import json
from pathlib import Path

from shapely.geometry import LineString, Point

HERE = Path(__file__).resolve().parent
FAG = HERE / "fag-r06/routes-fag.json"
BRIDGE = Path("Z:/pcb-runs/claude-finish/agent-work/test-bridges3/w/routes.json")


def shapes(records):
    output = []
    for index, record in enumerate(records):
        if record.get("kind") == "via":
            pos = record.get("at", record.get("pos", record.get("point")))
            if pos is None:
                pos = [record["x"], record["y"]]
            output.append((index, record["net"], None, Point(pos), record["d"] / 2))
        else:
            output.append((index, record["net"], record["layer"],
                           LineString(record["points"]), record["width"] / 2))
    return output


def main():
    first, second = [shapes(json.loads(path.read_text())["tracks"]) for path in (FAG, BRIDGE)]
    distances = []
    for ai, an, al, ag, ar in first:
        for bi, bn, bl, bg, br in second:
            if al is None or bl is None or al == bl:
                distances.append({"FAG_record": ai, "bridge_record": bi,
                                  "copper_gap_mm": round(ag.distance(bg) - ar - br, 6)})
    distances.sort(key=lambda item: item["copper_gap_mm"])
    receipt = {"evidence_class": "host new-addition overlap screen only; no full-board/native proof",
               "source_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in (FAG, BRIDGE)},
               "required_cross_domain_gap_mm": 0.6,
               "minimum_observed_copper_gap_mm": distances[0]["copper_gap_mm"],
               "possible_conflicts": [item for item in distances if item["copper_gap_mm"] < 0.6],
               "closest_new_addition_pairs": distances[:8],
               "native_gate": "Composed revision needs exact native refill/DRC and whole-board partition guard"}
    (HERE / "subset-overlay.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"minimum_new_copper_gap_mm": receipt["minimum_observed_copper_gap_mm"],
                      "possible_conflicts": len(receipt["possible_conflicts"])}))


if __name__ == "__main__":
    main()
