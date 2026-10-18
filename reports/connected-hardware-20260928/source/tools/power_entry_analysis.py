"""Recompute the bounded TPS26630 study, never declare a power circuit qualified."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class InputError(ValueError):
    pass


def number(value, name, low=0.0, high=1e9, *, low_inclusive=False):
    if type(value) not in (int, float):
        raise InputError(f"{name}: finite number required, not bool/string/null")
    try:
        x = float(value)
    except (OverflowError, ValueError):
        raise InputError(f"{name}: finite representable number required") from None
    if not math.isfinite(x) or x > high or (x < low if low_inclusive else x <= low):
        raise InputError(f"{name}: outside allowed range {low}..{high}")
    return x


def reject_nonfinite(value, path="root"):
    """JSON accepts NaN/Infinity and 1e999 by default; reject them anywhere."""
    if type(value) in (int, float):
        number(value, path, -1e100, 1e100, low_inclusive=True)
    elif isinstance(value, dict):
        for k, v in value.items():
            reject_nonfinite(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            reject_nonfinite(v, f"{path}[{i}]")


def ladder_corners(resistors, tolerance, refs, leak=150e-9, *, node):
    """Positive leakage flows into a pin; enumerate independent endpoints."""
    if node not in ("uv", "ov"):
        raise InputError("ladder node must be uv or ov")
    vals = []
    for factors in itertools.product((1-tolerance, 1+tolerance), repeat=3):
        a, b, c = [r*f for r, f in zip(resistors, factors)]
        for ref, iu, io in itertools.product(refs, (-leak, leak), (-leak, leak)):
            v = (ref*(a+b+c)/(b+c) + iu*a + io*a*c/(b+c) if node == "uv"
                 else ref*(a+b+c)/c + iu*a + io*(a+b))
            vals.append(v)
    return [min(vals), max(vals)]


def divider_corners(top, bottom, tolerance, refs, leak=150e-9):
    vals = [ref*(1+top*a/(bottom*b))+i*top*a
            for a, b, ref, i in itertools.product(
                (1-tolerance, 1+tolerance), (1-tolerance, 1+tolerance), refs, (-leak, leak))]
    return [min(vals), max(vals)]


def analyze(req, ledger):
    result = {"schema_version": 1, "manufacturing_ready": False,
              "evidence": "datasheet-based numerical screening only", "errors": [], "issues": [],
              "not_proved": ["physical fuse clearing/source coordination", "transient voltage survival",
                             "startup sequence and thermal SOA", "board thermal behavior", "EMC immunity",
                             "complete hardware or manufacturing readiness"]}
    try:
        if not isinstance(req, dict) or not isinstance(ledger, dict):
            raise InputError("requirements and ledger must be objects")
        reject_nonfinite(req)
        reject_nonfinite(ledger, "ledger")
        if req.get("manufacturing_ready") is not False:
            raise InputError("requirements must explicitly remain manufacturing_ready=false")
        parts = req["parts"]
        if parts["U1"]["mpn"] != "TPS26630RGER":
            raise InputError("analysis applies only to TPS26630RGER, not other variants")
        q1 = parts["Q1"]
        if q1["mpn"] != "CSD19537Q3" or (q1["source"], q1["drain"], q1["gate"]) != (
                "RAW_FUSED", "EFUSE_IN", "B_GATE"):
            raise InputError("Q1 identity/source/drain/gate differs from reviewed blocking topology")
        if q1["pins"] != {"1": "RAW_FUSED", "2": "RAW_FUSED", "3": "RAW_FUSED", "4": "B_GATE",
                          "5": "EFUSE_IN", "6": "EFUSE_IN", "7": "EFUSE_IN", "8": "EFUSE_IN",
                          "exposed_drain": "EFUSE_IN"}:
            raise InputError("Q1 manufacturer contact map differs from reviewed topology")
        q2 = parts["Q2"]
        if q2["mpn"] != "BSS138P,215" or q2["pins"] != {"1": "DRV", "2": "RAW_FUSED", "3": "B_GATE"}:
            raise InputError("Q2 identity/pin arrangement differs from reviewed fast-pulldown topology")
        if parts["TVS"]["mpn"] != "SMCJ30CA" or parts["TVS"]["bidirectional"] is not True:
            raise InputError("reviewed bidirectional input TVS identity required")
        values = req["support_values"]
        ladder = values["uvov_ladder"]
        r = [number(ladder[k], k, high=1e7) for k in (
            "raw_to_uvlo_ohm", "uvlo_to_ovp_ohm", "ovp_to_gnd_ohm")]
        tolerance = number(ladder["total_error_budget_fraction"], "ladder total tolerance", high=.1)
        initial = number(ladder["initial_resistor_tolerance_fraction"], "ladder initial tolerance", high=.1)
        if tolerance < initial or r[0]*(1-tolerance) < 300000:
            raise InputError("ladder tolerance budget or reverse-input 300k minimum violated")
        pg = values["pgth_divider"]
        pg_top = number(pg["protected_to_pgth_ohm"], "PGTH top", high=1e7)
        pg_bottom = number(pg["pgth_to_gnd_ohm"], "PGTH bottom", high=1e7)
        pg_tol = number(pg["total_error_budget_fraction"], "PGTH tolerance", high=.1)
        if pg_tol < number(pg["initial_resistor_tolerance_fraction"], "PGTH initial tolerance", high=.1):
            raise InputError("PGTH total tolerance smaller than initial tolerance")
        limits = values["rilim"]
        rt = number(limits["total_error_budget_fraction"], "ILIM resistor tolerance", high=.1)
        if rt < number(limits["initial_tolerance_fraction"], "ILIM initial tolerance", high=.1):
            raise InputError("ILIM total tolerance smaller than initial tolerance")
        it = number(limits["current_tolerance_assumption_fraction"], "ILIM transfer allowance", .1, .3, low_inclusive=True)
        if limits["assumption_not_guaranteed_at_selected_r"] is not True:
            raise InputError("selected-R current range must be labeled an assumption")
        env = req["proposed_draft_envelope"]
        vin = env["entry_voltage_v"]
        if not isinstance(vin, list) or len(vin) != 2:
            raise InputError("entry_voltage_v requires exactly two numbers")
        vinlo, vinhi = [number(v, "entry voltage", high=60) for v in vin]
        if vinlo >= vinhi:
            raise InputError("entry voltage interval is reversed or empty")
        if len(req["branches"]) != 2 or {b["id"] for b in req["branches"]} != {"CORE", "FIELD"}:
            raise InputError("exactly one CORE and one FIELD branch required")
        if {b["ground"] for b in req["branches"]} != {"LOGIC_GND", "FIELD_GND"}:
            raise InputError("independent CORE/FIELD ground domains required")
        cim = number(values["imon"]["resistor_ohm"], "IMON resistor", 1000, 100000, low_inclusive=True)
        if values["imon"]["capacitor_allowed"] is not False:
            raise InputError("IMON capacitor is not allowed by this study")
        # Source values below come from SLVSE94G; stored report results are never inputs.
        thresholds = {
            "uvlo_rise_v": ladder_corners(r, tolerance, (1.176, 1.224), node="uv"),
            "uvlo_fall_v": ladder_corners(r, tolerance, (1.09, 1.15), node="uv"),
            "ovp_rise_v": ladder_corners(r, tolerance, (1.176, 1.224), node="ov"),
            "ovp_fall_v": ladder_corners(r, tolerance, (1.09, 1.15), node="ov"),
            "pgth_rise_v": divider_corners(pg_top, pg_bottom, pg_tol, (1.176, 1.224)),
            "pgth_fall_v": divider_corners(pg_top, pg_bottom, pg_tol, (1.09, 1.15)),
        }
        result["thresholds"] = thresholds
        cd = number(values["dvdT"]["capacitance_f"], "dVdT capacitance", 10e-9, 10e-6, low_inclusive=True)
        ct = number(values["dvdT"]["effective_tolerance_fraction"], "dVdT effective tolerance", high=.2)
        cout = number(values["decoupling"]["total_output_capacitance_max_f"], "total COUT", high=.1)
        slo, shi = 1.775e-6*23.5/(cd*(1+ct)), 2.225e-6*26/(cd*(1-ct))
        inrush = cout*shi
        result["startup"] = {"model_slew_v_per_s": [slo, shi], "capacitive_peak_a": inrush,
                             "rise_to_max_input_ms": [vinhi/shi*1000, vinhi/slo*1000],
                             "stored_energy_j": .5*cout*vinhi**2,
                             "fast_model_average_efuse_loss_w": .5*vinhi*inrush,
                             "startup_loads_must_be_held_off": True, "thermal_soa_proved": False}
        if thresholds["uvlo_rise_v"][1] >= vinlo:
            result["issues"].append("UVLO worst-case turn-on is not below minimum entry voltage")
        if thresholds["ovp_rise_v"][0] <= vinhi:
            result["issues"].append("OVP may trip inside normal input range")
        if thresholds["ovp_fall_v"][0] <= vinhi:
            result["issues"].append("OVP recovery is not guaranteed at maximum normal input voltage")
        result["branches"] = {}
        rails = {x["id"]: x for x in ledger["rails"]}
        for b in req["branches"]:
            n, key = b["id"], b["id"].lower()
            expected_ground = "LOGIC_GND" if n == "CORE" else "FIELD_GND"
            if b["ground"] != expected_ground:
                raise InputError(f"{n} ground domain swapped")
            ri = number(b["rilim_ohm"], n+" RILIM", 3000/(1-rt), 30000/(1+rt), low_inclusive=True)
            load = number(b["normal_load_a"], n+" load", high=6)
            rows = [x for x in ledger["power_loads"] if x["rail"] == n+"_24V"]
            ledger_load = math.fsum(number(x["budget_a"], "ledger load", high=100) for x in rows)
            if not rows or not math.isclose(load, ledger_load, rel_tol=0, abs_tol=1e-9):
                raise InputError(f"{n}: normal load no longer matches current ledger")
            nominal = 18000/ri
            ilo, ihi = nominal*(1-it)/(1+rt), nominal*(1+it)/(1-rt)
            path = number(env["total_series_resistance_budget_ohm"][key], key+" total series resistance", high=2)
            supply = number(env[key+"_qualified_source_and_wiring_capacity_target_a"], key+" source target", high=100)
            vout = vinlo-load*path
            # 2x Q1 hot R allowance is intentionally not a guaranteed datasheet maximum.
            efuse_w = load**2*.053+.0017*vinhi
            q1_w = load**2*(2*.0166)
            row = {"load_a": load, "nominal_limit_a": nominal, "assumed_limit_range_a": [ilo, ihi],
                   "assumed_low_limit_margin_a": ilo-load, "minimum_output_model_v": vout,
                   "efuse_loss_model_w": efuse_w, "q1_hot_loss_assumption_w": q1_w,
                   "efuse_reference_rise_c": efuse_w*31.4, "q1_reference_rise_c": q1_w*55,
                   "imon_max_model_v": ihi*30.14e-6*cim*(1+rt),
                   "unsequenced_load_plus_capacitor_a": load+inrush,
                   "source_target_a": supply,
                   "ledger_source_capacity_a": number(rails[n+"_24V"]["capacity_a"], n+" ledger source", high=100)}
            result["branches"][n] = row
            if ilo <= load:
                result["issues"].append(f"{n}: assumed minimum limiter does not exceed normal load")
            if load+inrush >= ilo:
                result["issues"].append(f"{n}: unsequenced startup can enter current limit")
            if ihi > supply:
                result["issues"].append(f"{n}: proposed source/path capacity is below assumed upper limiter")
            if ihi > row["ledger_source_capacity_a"]:
                result["issues"].append(f"{n}: original ledger source capacity is below assumed upper limiter")
            if vout < 18:
                result["issues"].append(f"{n}: calculated protected output below existing18V-min converter requirement")
            if row["imon_max_model_v"] >= 4:
                result["issues"].append(f"{n}: IMON model exceeds4V operating limit")
        result["assumptions"] = ["ILIM transfer +/-10% or greater is an assumption at selectedR",
                                 "Q1 hot resistance2x25C6V-gate max is an assumption",
                                 "source/path targets and0.20ohm budget are not selected hardware",
                                 "thermal metrics are reference-board values",
                                 "dVdT gain/current endpoint product is a model, not waveform qualification"]
    except (InputError, KeyError, TypeError, ValueError, OverflowError, ZeroDivisionError) as exc:
        result["errors"].append(str(exc))
    result["calculation_valid"] = not result["errors"]
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--requirements", type=Path, default=ROOT/"hardware/power_entry/requirements.json")
    p.add_argument("--ledger", type=Path, default=ROOT/"hardware/electrical-design.json")
    p.add_argument("--report", type=Path)
    args = p.parse_args(argv)
    try:
        raw_req, raw_ledger = args.requirements.read_bytes(), args.ledger.read_bytes()
        result = analyze(json.loads(raw_req), json.loads(raw_ledger))
        result["input_sha256"] = {"requirements": hashlib.sha256(raw_req).hexdigest(),
                                  "ledger": hashlib.sha256(raw_ledger).hexdigest()}
    except (OSError, ValueError, UnicodeError) as exc:
        result = {"calculation_valid": False, "manufacturing_ready": False, "errors": [str(exc)]}
    out = json.dumps(result, indent=2, allow_nan=False)+"\n"
    if args.report:
        args.report.write_text(out, encoding="utf-8")
    else:
        print(out, end="")
    return 0 if result["calculation_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
