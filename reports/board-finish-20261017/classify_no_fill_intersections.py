"""Classify the496 raw no-fill intersections without discarding any witness.

Intended zone envelopes and real filled copper are distinct. Positive actual
intersections get exact rational point tests against native integral-nm rings.
This is a diagnostic classification, not a tolerance, refill or DRC waiver.
"""
import os
import sys
sys.dont_write_bytecode = True
for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[key] = "2"
import collections
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import time
from shapely import from_wkb

H = Path(__file__).resolve().parent
OUT = H / "no-fill-intersection-review-r1"
RAW = H / "actual-full-audit-repaired-r1/r763/actual-native-no-fill-area-closed-set-both-role-intersections.json"
GEOMETRY = H.parent / "board-finish-20261011/continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299/native-full/actual-full-refill-geometry.json"
HELPER = H / "routing/parent-audit-review/verify_positive_points_native_IU_true_drills_r1.py"


def sha(p):
    with Path(p).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def polygons(shape):
    if shape.geom_type == "Polygon":
        yield shape
    elif hasattr(shape, "geoms"):
        for child in shape.geoms:
            yield from polygons(child)


def main():
    start = time.monotonic()
    assert not OUT.exists()
    assert sha(GEOMETRY) == "9567a5c5a3c4e055a7ae989e0832a152fa21c09b8df6250fbb495b2c07c42b3f"
    spec = importlib.util.spec_from_file_location("exact_native_ring_predicates", HELPER)
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    raw = json.loads(RAW.read_bytes())
    native = json.loads(GEOMETRY.read_bytes())
    areas = {r["uuid"]: r for r in native["rule_areas"]}
    zones = {z["uuid"]: z for z in native["zones"]}
    prepared = {}
    def prepare(label, contours):
        if label not in prepared:
            prepared[label] = [[A.ring(ring) for ring in rings] for rings in contours]
        return prepared[label]
    def location(point, rows):
        locs = [A.polyloc(point, r) for r in rows if A.inbounds(point, r[0][1])]
        return "INTERIOR" if "INTERIOR" in locs else "BOUNDARY" if "BOUNDARY" in locs else "EXTERIOR"
    pins = {str(p): sha(p) for p in (Path(__file__), RAW, GEOMETRY, HELPER)}
    result, counts, certcounts = [], collections.Counter(), collections.Counter()
    for i, row in enumerate(raw):
        witness = Path(row["overlap"]["file"])
        assert sha(witness) == row["overlap"]["WKB_SHA256"]
        pins[str(witness)] = sha(witness)
        shape = from_wkb(witness.read_bytes())
        assert shape.area == row["overlap"]["area_mm2"] and not shape.is_empty
        area, zone = areas[row["area_UUID"]], zones[row["zone_UUID"]]
        assert area["no_fill"]
        dimension = "POSITIVE_AREA" if shape.area > 0 else "BOUNDARY_ONLY_RAW"
        counts[row["role"], dimension] += 1
        entry = {**row, "area_name": area.get("name"), "rule_no_fill_flag": area["no_fill"],
                 "raw_class": dimension, "raw_failure_retained": True}
        if row["role"] == "INTENDED_OUTLINE":
            entry["engineering_scope"] = "ZONE_ENVELOPE_DIAGNOSTIC_NOT_ETCHED_COPPER; actual fill independently classified"
        elif dimension == "POSITIVE_AREA":
            layer = row["layer"]
            rules = prepare(("rule", area["uuid"]), area["outline"])
            fills = prepare(("fill", zone["uuid"], layer), zone["fills"][layer])
            certificates = []
            for j, component in enumerate(polygons(shape)):
                if not component.area > 0:
                    continue
                candidate = component.representative_point()
                point_mm = (Fraction(str(candidate.x)), Fraction(str(candidate.y)))
                point = tuple(p * 10**6 for p in point_mm)
                rl, fl = location(point, rules), location(point, fills)
                status = "EXACT_NATIVE_IU_POINT_INTERIOR_TO_RULE_AND_FILL" if (rl, fl) == ("INTERIOR", "INTERIOR") else "RAW_COMPONENT_EXACT_INTERIOR_CERTIFICATE_OPEN"
                certcounts[status] += 1
                certificates.append({"component": j, "classification": status,
                                     "point_exact_mm": [str(p) for p in point_mm],
                                     "native_IU_rule_location": rl, "native_IU_fill_location": fl,
                                     "native_rounding_DRC_process_implication": "OPEN_NO_TOLERANCE_WAIVER"})
            entry["exact_positive_point_checks"] = certificates
        else:
            entry["engineering_scope"] = "RAW_CLOSED_SET_CONTACT_RETAINED; no positive physical overlap certified here"
        result.append(entry)
    OUT.mkdir()
    assert all(sha(Path(path)) == digest for path, digest in pins.items())
    (OUT / "all-496-classifications.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    report = {"status": "ALL_RAW_WITNESSES_RETAINED_ROLE_DIMENSION_AND_EXACT_POINT_CLASSIFICATION_ONLY",
              "counts": {"/".join(k): v for k, v in counts.items()}, "exact_actual_positive_point_checks": dict(certcounts),
              "actual_raw_positive_area_sum_mm2": sum(r["overlap"]["area_mm2"] for r in raw if r["role"] == "ACTUAL_CPP_FILL"),
              "zone_envelope_is_not_etched_fill": True, "native_rule_flag_and_IU_outline_independent_read": "SEPARATE_PENDING",
              "unresolved_native_rounding_boundary_and_manufacturing_implications": True,
              "official_format_reference": "https://dev-docs.kicad.org/en/file-formats/sexpr-intro/",
              "official_zone_and_rule_area_manual": "https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html",
              "input_SHA256": pins, "elapsed_seconds": time.monotonic() - start,
              "native_Fill_calls": 0, "native_Save_calls": 0, "no_ignored_checks_added": True,
              "adopted": False, "manufacturing_ready": False}
    (OUT / "receipt.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "counts", "exact_actual_positive_point_checks", "actual_raw_positive_area_sum_mm2")}))


if __name__ == "__main__":
    main()
