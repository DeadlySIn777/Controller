"""Source-only geometry exploration for exact c05. No KiCad or board mutations.

All outputs are proposals. No impedance, reference-plane continuity, or fab release
is implied. IPC validity is checked rather than accepting agreeing extrapolations.
"""
from __future__ import annotations
import os
for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import re
import sys
import time

HERE = Path(__file__).resolve().parent
TARGETS = {"IMP_50": 50, "DIFF_90": 90, "DIFF_100": 100, "DIFF_120": 120}
MIN_W, MIN_S, GRID, BAND, TOL, AGREE = .20, .15, .005, .010, .10, .05

def sha(b): return hashlib.sha256(b).hexdigest()
def write(path, value): path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def read_inputs():
    records = json.loads((HERE / "inputs.json").read_text(encoding="utf-8"))
    for role, rec in records.items():
        if sha(Path(rec["path"]).read_bytes()) != rec["sha256"]:
            raise ValueError(f"source changed: {role}")
        if rec["frozen"] and sha(Path(rec["frozen"]).read_bytes()) != rec["sha256"]:
            raise ValueError(f"frozen input changed: {role}")
    return records

def frozen(records, role):
    rec = records[role]
    return Path(rec["frozen"] or rec["path"])

def load_calc(records):
    spec = importlib.util.spec_from_file_location("impedance_calc", frozen(records, "calculator"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def balanced(s, start):
    depth, quote, escape = 0, False, False
    if s[start] != "(": raise ValueError("expression must start with parenthesis")
    for i in range(start, len(s)):
        c = s[i]
        if quote:
            if escape: escape = False
            elif c == "\\": escape = True
            elif c == '"': quote = False
        elif c == '"': quote = True
        elif c == "(": depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0: return s[start:i+1]
    raise ValueError("unclosed expression")

def stackup(board):
    s = board.read_text(encoding="utf-8")
    a = s.index("(stackup")
    block = balanced(s, a)
    layers = []
    for m in re.finditer(r'\(layer\s+"([^"\\]+)"', block):
        item = balanced(block, m.start())
        rec = {"name": m[1]}
        for key in ("type", "material", "thickness", "epsilon_r", "loss_tangent"):
            field = re.search(r'\(' + key + r'\s+("(?:\\.|[^"\\])*"|[^()\s]+)\)', item)
            if field:
                val = field[1]
                rec[key] = json.loads(val) if val.startswith('"') else float(val)
        layers.append(rec)
    names = [x["name"] for x in layers]
    expected = ["F.SilkS", "F.Paste", "F.Mask", "F.Cu", "dielectric 1", "In1.Cu", "dielectric 2", "In2.Cu", "dielectric 3", "In3.Cu", "dielectric 4", "In4.Cu", "dielectric 5", "B.Cu", "B.Mask", "B.Paste", "B.SilkS"]
    if names != expected: raise ValueError("unreviewed layer order")
    general = balanced(s, s.index("(general"))
    nominal = float(re.search(r'\(thickness\s+([^()\s]+)\)', general)[1])
    copper = sum(x.get("thickness", 0) for x in layers if x["type"] == "copper")
    dielectric = sum(x.get("thickness", 0) for x in layers if x["name"].startswith("dielectric "))
    mask = sum(x.get("thickness", 0) for x in layers if x["type"].endswith("Solder Mask"))
    if any(abs(x["thickness"] - .035) > 1e-12 for x in layers if x["type"] == "copper"):
        raise ValueError("current plan requires exact all-layer 35um copper")
    zone_counts = defaultdict(Counter)
    for zone in s.split("\n\t(zone\n")[1:]:
        prefix = zone[:1200]
        lm = re.search(r'\(layer\s+"([^"\\]+)"\)', prefix)
        nm = re.search(r'\(net\s+("(?:\\.|[^"\\])*"|[^()\s]+)\)', prefix)
        if lm and nm: zone_counts[lm[1]][json.loads(nm[1]) if nm[1].startswith('"') else nm[1]] += 1
    return {"layers": layers, "native_nominal_mm": nominal, "copper_mm": copper,
            "dielectrics_mm": dielectric, "copper_plus_dielectric_mm": round(copper + dielectric, 6),
            "including_masks_mm": round(copper + dielectric + mask, 6),
            "nominal_mismatch_mm": round(nominal - copper - dielectric - mask, 6),
            "fabricator_resolution": "OPEN", "source_stackup": block,
            "zone_polygon_counts_not_continuity_evidence": {k: dict(sorted(v.items())) for k, v in sorted(zone_counts.items())}}

def layer_models(ic, stk):
    by = {x["name"]: x for x in stk["layers"]}
    def outer(name, dielectric):
        d = by[dielectric]
        return ic.Layer(name, "microstrip", by[name]["thickness"], h=d["thickness"], er=d["epsilon_r"])
    near, far = by["dielectric 3"], by["dielectric 4"]
    return {
        "F.Cu": outer("F.Cu", "dielectric 1"),
        "B.Cu": outer("B.Cu", "dielectric 5"),
        "In3.Cu": ic.Layer("In3.Cu", "stripline", by["In3.Cu"]["thickness"],
                           h1=near["thickness"], er1=near["epsilon_r"], h2=far["thickness"], er2=far["epsilon_r"]),
    }

def canonical(name): return name.replace("{slash}", "/")

def map_policy(policy, pad_table, project):
    current = defaultdict(set)
    for pad in pad_table["pads"]:
        current[canonical(pad["net"])].add(pad["net"])
    selected = {}
    for old, rec in policy["nets"].items():
        cls = rec["class"]
        if cls == "NONE": continue
        if cls not in TARGETS or rec["target_ohm"] != TARGETS[cls]: raise ValueError("unsupported historical target")
        matches = current.get(canonical(old), set())
        if len(matches) != 1: raise ValueError(f"missing or ambiguous current exact net: {old}")
        exact = next(iter(matches))
        if exact in selected: raise ValueError("two historical nets collapse to one current exact name")
        assignments = project["net_settings"]["netclass_assignments"].get(exact, [])
        if not isinstance(assignments, list) or any(not isinstance(x, str) for x in assignments):
            raise ValueError("expected KiCad 10 list-valued class assignments")
        exact_patterns = [x["netclass"] for x in project["net_settings"]["netclass_patterns"] if x["pattern"] == exact]
        memberships = sorted(set(assignments + exact_patterns))
        dom = [x for x in memberships if x.startswith("DOM_")]
        if len(dom) != 1: raise ValueError(f"controlled net must retain one explicit domain: {exact}")
        selected[exact] = {"class": cls, "target_ohm": TARGETS[cls], "historical_name": old,
                           "historical_group": rec["group"], "historical_rule": rec["rule"],
                           "historical_pair_partner": rec.get("pair_partner"), "existing_classes": memberships,
                           "existing_label_classes": assignments, "existing_exact_pattern_classes": exact_patterns,
                           "domain": dom[0], "policy_requalification": "OPEN_CURRENT_LENGTH_EDGE_BUS_RETURN_AUDIT",
                           "t_r_basis_historical": rec.get("t_r_basis"),
                           "edge_evidence_strongest_historical": rec.get("edge_evidence_strongest")}
    for name, rec in selected.items():
        partner = rec["historical_pair_partner"]
        if rec["class"].startswith("DIFF"):
            matches = current.get(canonical(partner or ""), set())
            if len(matches) != 1: raise ValueError(f"unresolved differential partner: {name}")
            exact_partner = next(iter(matches))
            if exact_partner not in selected or selected[exact_partner]["class"] != rec["class"]:
                raise ValueError("differential partner class mismatch")
            if canonical(selected[exact_partner]["historical_pair_partner"] or "") != canonical(name):
                raise ValueError("nonreciprocal differential pair")
            rec["exact_pair_partner"] = exact_partner
    return dict(sorted(selected.items()))

def methods(ic, layer, cls, w, s=None):
    if cls == "IMP_50":
        a, b, ee = ic.se_methods(layer, w)
    else:
        a, r = ic.diff_methods(layer, w, s)
        b, ee = r["zdiff"], r["ee"]
    ipc_valid = ic.ipc_microstrip_valid(w, layer.h, layer.t, layer.er) if layer.kind == "microstrip" else ic.ipc_stripline_valid(w, layer.h1, layer.h2, layer.t)
    kj_valid = True if cls == "IMP_50" or layer.kind != "microstrip" else ic.kj_valid(w, s, layer.h, layer.er)
    return {"A_ohm": a, "B_ohm": b, "A_valid": ipc_valid, "B_coupled_microstrip_valid": kj_valid,
            "A_B_difference_pct_of_B": 100 * abs(a - b) / b, "effective_er_B": ee,
            "delay_ps_per_mm_B": ic.tpd_ps_per_mm(ee)}

def in_tol(z, target): return abs(z / target - 1) <= TOL + 1e-12

def corners(ic, layer, cls, w, s=None, offcentre=False):
    widths = [max(MIN_W, round(w - BAND, 6)), round(w if offcentre else w + BAND, 6)]
    gaps = [None] if s is None else [max(MIN_S, round(s, 6) if offcentre else round(s - BAND, 6)), round(s + BAND, 6)]
    return [{"w_mm": ww, "s_mm": ss, **methods(ic, layer, cls, ww, ss)} for ww, ss in itertools.product(sorted(set(widths)), sorted(set(gaps), key=lambda x: x or 0))]

def choose(ic, layer, cls):
    target = TARGETS[cls]
    if cls == "IMP_50":
        wb = ic.bisect(lambda w: methods(ic, layer, cls, w)["B_ohm"], .03, 2, target)
        if wb is None: return {"status": "HELD_NO_BRACKET"}
        w = max(MIN_W, round(round(wb / GRID) * GRID, 6))
        rec = methods(ic, layer, cls, w)
        cs = corners(ic, layer, cls, w, offcentre=wb < MIN_W)
        return {"w_mm": w, "s_mm": None, "B_target_width_mm": wb, "offcentre": wb < MIN_W,
                "nominal": rec, "corners": cs, "target_ohm": target,
                "status": "PROVISIONAL_AB" if rec["A_valid"] and in_tol(rec["A_ohm"], target) and in_tol(rec["B_ohm"], target) and rec["A_B_difference_pct_of_B"] <= 100*AGREE and all(c["A_valid"] and in_tol(c["A_ohm"], target) and in_tol(c["B_ohm"], target) for c in cs) else "NEEDS_VALID_SECOND_METHOD"}
    cands = []
    # Microstrip K&J validity covers gap/h <=10; require band corners valid too.
    upper_s = 10 * layer.h - BAND if layer.kind == "microstrip" else 6.0
    upper_w = 2 * layer.h - BAND - 1e-8 if layer.kind == "microstrip" else 1.0
    for iw in range(math.ceil(MIN_W/GRID), math.floor(upper_w/GRID) + 1):
        w = round(iw*GRID, 6)
        sb = ic.bisect(lambda s: methods(ic, layer, cls, w, s)["B_ohm"], MIN_S, upper_s, target)
        if sb is None: continue
        s = round(round(sb/GRID)*GRID, 6)
        if s < MIN_S or s > upper_s: continue
        nominal = methods(ic, layer, cls, w, s)
        cs = corners(ic, layer, cls, w, s)
        if in_tol(nominal["A_ohm"], target) and in_tol(nominal["B_ohm"], target) and nominal["A_B_difference_pct_of_B"] <=100*AGREE and all(c["A_valid"] and c["B_coupled_microstrip_valid"] and in_tol(c["A_ohm"], target) and in_tol(c["B_ohm"], target) for c in cs):
            cands.append({"w_mm": w, "s_mm": s, "nominal": nominal, "corners": cs})
    if cands:
        out = min(cands, key=lambda r: (2*r["w_mm"]+r["s_mm"], r["nominal"]["A_B_difference_pct_of_B"]))
        return {**out, "target_ohm": target, "offcentre": False, "status": "PROVISIONAL_AB", "valid_AB_candidates": len(cands)}
    # Inner layer: IPC is invalid for all legal widths. Keep B/C candidate rather than claiming A.
    if layer.kind == "stripline":
        max_b = 2 * ic.cohn_stripline(MIN_W, layer.h1, layer.h2, layer.t, layer.er1, layer.er2)[0]
        if max_b < target * (1-TOL):
            return {"status": "HELD_INFEASIBLE_B_MODEL", "B_separated_pair_upper_bound_ohm": max_b,
                    "minimum_acceptable_ohm": target*(1-TOL), "target_ohm": target,
                    "A_usable": False, "reason": "legal width >=0.20 mm; increasing gap cannot exceed twice the single-line impedance"}
        # A failed range check cannot supply a valid cross-check. Candidate is chosen by B only for C testing.
        sb = ic.bisect(lambda s: methods(ic, layer, cls, MIN_W, s)["B_ohm"], MIN_S, 6, target)
        off = sb is None
        if off:
            sb = ic.bisect(lambda s: methods(ic, layer, cls, MIN_W, s)["B_ohm"], MIN_S, 6, target*.96)
        if sb is None: return {"status": "HELD_NO_PROVISIONAL_B_CANDIDATE"}
        s = round(round(sb/GRID)*GRID, 6)
        return {"status": "NEEDS_VALID_SECOND_METHOD", "w_mm": MIN_W, "s_mm": s,
                "target_ohm": target, "offcentre": off, "nominal": methods(ic, layer, cls, MIN_W, s),
                "corners": corners(ic, layer, cls, MIN_W, s, offcentre=off)}
    return {"status": "HELD_NO_VALID_AB_CANDIDATE", "target_ohm": target}

def bounded_fd(ic, layer, cls, rec):
    if "w_mm" not in rec: return rec
    w, s = rec["w_mm"], rec["s_mm"]
    def evaluate(ww, ss, refinement=1):
        start = time.perf_counter()
        grids = []
        original = ic.fd_solve
        def measured(*args, **kwargs):
            kwargs["dmin"] /= refinement
            kwargs["dmax"] /= refinement
            # Compute the exact proposed mesh dimensions before the sparse solve.
            conductors, dies = args[:2]
            kx, ky = [0.0], [0.0]
            for r, _ in list(conductors) + list(dies): kx += [r.x0,r.x1]; ky += [r.y0,r.y1]
            top = kwargs.get("top_plane")
            if top is not None: ky.append(top)
            nx = len(ic._graded(kx, kwargs["dmin"],kwargs["dmax"],kwargs.get("ratio",1.25),-kwargs["xspan"],kwargs["xspan"]))
            ny = len(ic._graded(ky, kwargs["dmin"],kwargs["dmax"],kwargs.get("ratio",1.25),0, top or kwargs["ytop"]))
            if nx*ny > 160000: raise ValueError("bounded field mesh exceeds 160000 nodes")
            grids.append({"nx":nx,"ny":ny,"nodes":nx*ny})
            return original(*args, **kwargs)
        ic.fd_solve = measured
        try:
            r = ic.fd_se(layer, ww) if cls == "IMP_50" else ic.fd_diff(layer, ww, ss)
        finally: ic.fd_solve = original
        return {"w_mm": ww, "s_mm": ss, "C_ohm": r["z0" if cls == "IMP_50" else "zdiff"],
                "C_effective_er": r.get("eeff",r.get("ee_o")), "runtime_seconds": time.perf_counter()-start,
                "mesh_refinement_factor":refinement,"meshes":grids}
    out = dict(rec)
    out["field_nominal"] = evaluate(w,s)
    out["field_corners"] = [evaluate(c["w_mm"],c["s_mm"]) for c in rec["corners"]]
    out["field_nominal_refined"] = evaluate(w,s,2)
    out["field_corners_refined"] = [evaluate(c["w_mm"],c["s_mm"],2) for c in rec["corners"]]
    comparisons=[(out["field_nominal"],out["field_nominal_refined"])] + list(zip(out["field_corners"],out["field_corners_refined"]))
    delta=max(100*abs(base["C_ohm"]-fine["C_ohm"])/fine["C_ohm"] for base,fine in comparisons)
    out["mesh_convergence"]={"two_mesh_max_change_pct":delta,"criterion_pct":1,"passes":delta<=1,
                             "limit":"resolution cross-check at two meshes; finite-box and dielectric/geometry model assumptions remain"}
    out["B_C_difference_pct_of_C"] =100*abs(rec["nominal"]["B_ohm"]-out["field_nominal"]["C_ohm"])/out["field_nominal"]["C_ohm"]
    # Keep method A diagnostic, but it is deliberately excluded when invalid.
    valid = out["B_C_difference_pct_of_C"] <=100*AGREE and in_tol(out["field_nominal"]["C_ohm"],rec["target_ohm"]) and all(in_tol(c["C_ohm"],rec["target_ohm"]) for c in out["field_corners"]) and all(in_tol(c["B_ohm"],rec["target_ohm"]) for c in rec["corners"])
    valid=valid and delta<=1 and in_tol(out["field_nominal_refined"]["C_ohm"],rec["target_ohm"]) and all(in_tol(c["C_ohm"],rec["target_ohm"]) for c in out["field_corners_refined"])
    out["status"] = "PROVISIONAL_BC_TWO_MESH_CHECK" if valid else "HELD_BC_MODEL_DISAGREEMENT_BAND_OR_MESH"
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--field-inner",action="store_true");args=ap.parse_args()
    started=time.perf_counter(); records=read_inputs(); ic=load_calc(records)
    stk=stackup(frozen(records,"board")); models=layer_models(ic,stk)
    policy=json.loads(frozen(records,"historical_controlled_nets").read_text(encoding="utf-8"))
    pads=json.loads(frozen(records,"native_matched_pad_table").read_text(encoding="utf-8"))
    pro=json.loads(frozen(records,"project").read_text(encoding="utf-8"))
    mapping=map_policy(policy,pads,pro)
    geometry={}
    for layer, model in models.items():
        geometry[layer]={cls:choose(ic,model,cls) for cls in TARGETS}
    if args.field_inner:
        for cls,rec in geometry["In3.Cu"].items():
            geometry["In3.Cu"][cls]=bounded_fd(ic,models["In3.Cu"],cls,rec)
            print(json.dumps({"layer":"In3.Cu","class":cls,"status":geometry["In3.Cu"][cls]["status"]}),flush=True)
    before={k:r["sha256"] for k,r in records.items()}; after=read_inputs()
    if before != {k:r["sha256"] for k,r in after.items()}: raise ValueError("read set changed")
    write(HERE/"stackup.json",stk); write(HERE/"controlled-net-map.json",mapping); write(HERE/"geometry.json",geometry)
    write(HERE/"source-receipt.json",{"verdict":"PROVISIONAL_SOURCE_ONLY", "board_sha256":records["board"]["sha256"],
        "read_set_unchanged":True,"class_counts":dict(Counter(r["class"] for r in mapping.values())),
        "runtime_seconds":time.perf_counter()-started,"KiCad_invoked":False,"GPU_invoked":False,"numerical_threads":1,
        "field_inner":args.field_inner,"source_inputs":records,
        "open":["FAB_STACKUP_CONFIRMATION", "NOMINAL_STACKUP_THICKNESS_MISMATCH", "MASK_ER_UNKNOWN", "REFERENCE_PLANE_AND_RETURN_CONTINUITY", "FINITE_BOX_AND_MODEL_APPROXIMATION", "COPLANAR_COPPER_EFFECT", "CURRENT_EDGE_LENGTH_BUS_TIMING_POLICY", "NATIVE_CLASS_RULE_ROUTER_VALIDATION", "CURRENT_ROUTING_AND_SI_QUALIFICATION"]})
    print(json.dumps({"verdict":"PROVISIONAL_SOURCE_ONLY","runtime_seconds":time.perf_counter()-started,"controlled_nets":len(mapping),"class_counts":dict(Counter(r["class"] for r in mapping.values()))}),flush=True)

if __name__=="__main__":main()
