"""Construct an isolated, source-only current patch without importing the raster planner."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ORIGINAL=Path('Z:/pcb-runs/claude-finish/tools/field_pdn_design.py')
BASE=HERE.parent.parent
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=ORIGINAL.read_bytes();source=raw.decode();nl='\r\n' if '\r\n' in source else '\n';source=source.replace('\r\n','\n')
 (HERE/'original-field_pdn_design.py').write_bytes(raw)
 changes=[]
 def replace(old,new,count=1):
  nonlocal source
  if source.count(old)!=count:raise ValueError('Unexpected patch boundary: '+old[:80])
  source=source.replace(old,new);changes.append({'original':old,'replacement':new,'occurrences':count})
 replace('Segment current = sum of the cluster currents downstream, capped at the rail design current.',
         'Segment current = explicit downstream sum; inconsistent documented loads/design/source limits reject before routing.')
 replace('from collections import defaultdict\n','from collections import defaultdict\nfrom field_current_guard import CurrentModelError, validate_spec, required_vias, array_status, modeled_route_status, route_output\n')
 replace('        self.G, self.PART, self.spec, self.a = G, PART, spec, args',
         '        self.current_preflight = validate_spec(spec, args.only)\n        self.G, self.PART, self.spec, self.a = G, PART, spec, args')
 replace('"clusters_sum_a": round(sum(c["amps"] for c in clusters), 3),',
         '"clusters_sum_a": math.fsum(c["amps"] for c in clusters),')
 replace('"share_rule": "cluster current = documented maximum (basis/cite); segment current = downstream sum capped at "\n                            "the rail design current", "islands": []}',
         '"share_rule": "cluster current = documented maximum (basis/cite); segment current = explicit downstream sum without caps", "islands": []}')
 replace('        self.design["nets"][rid] = des',
         '        des["current_model"] = {"preflight": self.current_preflight["rails"][rid],\n            "source_and_positive_load_pads_resolved": bool(src_pads) and all(self.resolve(r, [selector]) for selector in r["source"]["pads"])\n                and all(all(self.resolve(r, [selector]) for selector in c["pads"]) for c in clusters if c["amps"] > 0),\n            "pad_selector_policy": "Each explicit ref/pad selector resolves; wildcard retains original any-matching-role semantics",\n            "source_local_load_a": 0.0, "full_rail_qualified": False}\n        self.design["nets"][rid] = des')
 replace('            I_C = min(sum(down[J] for J in tg), r["design_a"])','            I_C = math.fsum(down[J] for J in tg)')
 replace('max(1, math.ceil(I_C / self.amps_per_via - 1e-9))','required_vias(I_C, self.amps_per_via)')
 replace('max(1, math.ceil(down[J] / self.amps_per_via - 1e-9))','required_vias(down[J], self.amps_per_via)')
 replace('ipc_width_mm(min(down[J], r["design_a"]))','ipc_width_mm(down[J])',2)
 replace('ipc_width_mm(min(u["amps"], r["design_a"]))','ipc_width_mm(u["amps"])')
 replace('round(min(down_eff.get(vg["island"], 0.0), r["design_a"]), 3)','down_eff.get(vg["island"], 0.0)')
 replace('max(1, math.ceil(vg["amps"] / self.amps_per_via - 1e-9))','required_vias(vg["amps"], self.amps_per_via)')
 replace('round(min(sum(p["amps"] for p in ct["paths"]), r["design_a"]), 3)','math.fsum(p["amps"] for p in ct["paths"])')
 replace('max(1, math.ceil(ct["root"]["amps"] / self.amps_per_via - 1e-9))','required_vias(ct["root"]["amps"], self.amps_per_via)')
 replace('round(min(down_eff.get(src_gi, 0.0) - g_amps.get(src_gi, 0.0), r["design_a"]), 3)',
         'down_eff.get(src_gi, 0.0) - g_amps.get(src_gi, 0.0)')
 replace('        self.finalize(r, des, cts, hw, down_eff, reached, src_gi)',
         '        des["current_model"]["source_local_load_a"] = g_amps.get(src_gi, 0.0)\n        self.finalize(r, des, cts, hw, down_eff, reached, src_gi)')
 replace('s["amps"] = min(s.get("amps_raw", 0.0), r["design_a"])','s["amps"] = s.get("amps_raw", 0.0)')
 replace('"width_mm": w, "amps": round(s["amps"], 3),','"width_mm": w, "amps": s["amps"],')
 replace('"w_ipc10C_mm": round(s["w_ipc"], 2), "w_available_mm": round(s["w_avail"], 2),',
         '"w_ipc10C_mm": round(s["w_ipc"], 2), "w_ipc10C_mm_raw": s["w_ipc"], "w_available_mm": round(s["w_avail"], 2),')
 replace('"drop_v": round(base + v + vv, 4)})',
         '"drop_v": round(base + v + vv, 4), "drop_v_raw": base + v + vv})')
 replace('        des["worst_drop_v"] = max([d["drop_v"] for d in drops] or [0])',
         '        des["worst_drop_v"] = max([d["drop_v"] for d in drops] or [0])\n        des["worst_drop_v_raw"] = max([d["drop_v_raw"] for d in drops] or [0])')
 replace('        n = len(vg.get("vias", []))\n        return',
         '        n = len(vg.get("vias", []))\n        qualification = array_status(vg.get("amps"), n, self.amps_per_via, vg.get("n_req"))\n        return')
 replace('"n": n, "ok": n >= (vg.get("n_req") or 0), "vias": vg.get("vias", []),',
         '"n": n, "ok": qualification["qualified_for_modeled_current"], "current_qualification": qualification, "full_rail_qualified": False, "vias": vg.get("vias", []),')
 replace('        routes_name = "routes.json"',
         '        qualifications = {rid: modeled_route_status(self.rail[rid], d, self.spec) for rid, d in self.design["nets"].items()}\n        self.design["current_qualification"] = qualifications\n        self.design["full_rail_qualified"] = False\n        route_failures = [{"net": rid, "reason": reason} for rid, q in qualifications.items() for reason in q["reasons"]]\n        routes_name = route_output(qualifications, bool(self.pool))\n        self.design["applicable_routes_emitted"] = routes_name == "routes.json"')
 replace('        w = self.a.work\n        for rid, d in self.design["nets"].items():',
         '        w = self.a.work\n        if os.path.exists(os.path.join(w, "routes.json")):\n            raise SystemExit("Existing applicable routes.json: use a fresh work directory to avoid stale route reuse")\n        for rid, d in self.design["nets"].items():')
 replace('json.dump({"tracks": self.out_tracks + self.out_vias, "failures": []},',
         'json.dump({"tracks": self.out_tracks + self.out_vias, "failures": route_failures,\n                   "current_qualification": qualifications, "full_rail_qualified": False},')
 replace('    spec = json.load(open(a.spec, encoding="utf-8"))',
         '    if os.path.exists(os.path.join(a.work, "routes.json")):\n        raise SystemExit("Existing applicable routes.json: use a fresh work directory to avoid stale route reuse")\n    spec = json.load(open(a.spec, encoding="utf-8"))\n    try:\n        preflight = validate_spec(spec, a.only)\n    except CurrentModelError as error:\n        json.dump(error.report, open(os.path.join(a.work, "field-current-preflight.json"), "w", encoding="utf-8"), indent=1)\n        log(str(error))\n        raise SystemExit(3)\n    json.dump(preflight, open(os.path.join(a.work, "field-current-preflight.json"), "w", encoding="utf-8"), indent=1)')
 replace('    os.makedirs(a.work, exist_ok=True)',
         '    if os.path.isdir(a.work) and os.listdir(a.work):\n        raise SystemExit("Nonempty field work directory: use a fresh work directory; historical outputs preserved")\n    os.makedirs(a.work, exist_ok=True)')
 compile(source,str(HERE/'field_pdn_design.py'),'exec')
 (HERE/'field_pdn_design.py').write_bytes(source.replace('\n',nl).encode())
 (HERE/'source.patch').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),source.replace('\n',nl).splitlines(True),fromfile=str(ORIGINAL),tofile='field_pdn_design.py')),encoding='utf-8')
 ready=BASE/'recovery-composite/c06/four-fag/ready-r1.json';closure=json.loads(ready.read_bytes())['files']
 bound=[p for p in closure if Path(p).resolve() in (ORIGINAL.resolve(),(ORIGINAL.parent/'field_current_guard.py').resolve())]
 identities={str(ORIGINAL.resolve()):digest(ORIGINAL),str(ready.resolve()):digest(ready)}
 snapshots=json.loads((HERE.parent/'donor-screening.json').read_bytes())['constraint_snapshots']
 for original,record in snapshots.items():
  if digest(record['snapshot'])!=record['sha256'] or digest(original)!=record['sha256']:raise ValueError('Field model source/snapshot changed')
  identities[original]=record['sha256'];identities[record['snapshot']]=record['sha256']
 design=Path('Z:/pcb-runs/claude-finish/agent-work/field-pdn/testA3/w/design/design.json')
 identities[str(design.resolve())]=digest(design)
 result={'verdict':'STAGED_FIELD_CURRENT_SOURCE_PATCH','input_sha256':identities,
  'original_source_sha256':digest(ORIGINAL),'patched_source_sha256':digest(HERE/'field_pdn_design.py'),
  'current_guard_sha256':digest(HERE/'field_current_guard.py'),'changes':changes,
  'active_combined_source_binding':bound,'shared_source_modified':False,'installed':False,
  'heavy_planner_execution':False,'gpu_jobs':0,'native_jobs':0,'capacity_constants_changed':False,'geometry_masks_changed':False}
 (HERE/'construction.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({k:result[k] for k in ('verdict','original_source_sha256','patched_source_sha256','current_guard_sha256','active_combined_source_binding','installed')}))
if __name__=='__main__':main()
