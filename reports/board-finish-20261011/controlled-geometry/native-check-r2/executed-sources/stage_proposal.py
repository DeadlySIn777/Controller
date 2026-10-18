"""Stage reviewable settings for a FUTURE isolated project. Never install them."""
from __future__ import annotations
from collections import Counter
import copy
import json
from pathlib import Path
import re
import plan_geometry as pg

HERE=Path(__file__).resolve().parent

def proposal_project(original, mapping, geometry):
    pro=copy.deepcopy(original); ns=pro["net_settings"]
    if any(c["name"] in pg.TARGETS for c in ns["classes"]):
        raise ValueError("controlled classes already exist; reviewed migration required")
    priority=min(int(c["priority"]) for c in ns["classes"])-1
    for cls in pg.TARGETS:
        rec=geometry["F.Cu"][cls]
        if rec["status"]!="PROVISIONAL_AB": raise ValueError("no valid outer proposal")
        new={"name":cls,"priority":priority,"track_width":rec["w_mm"]}
        # Unset clearance and via properties inherit their original domain/default values.
        # This class supplies only geometry, at higher priority than existing constituents.
        if cls.startswith("DIFF"):
            new.update(diff_pair_width=rec["w_mm"],diff_pair_gap=rec["s_mm"])
        ns["classes"].append(new)
    for exact, rec in mapping.items():
        classes=ns["netclass_assignments"].setdefault(exact,[])
        if not isinstance(classes,list): raise ValueError("list-valued assignments required")
        if rec["class"] in classes: raise ValueError("duplicate proposal assignment")
        classes.append(rec["class"])
    verify_project(original,pro,mapping)
    return pro

def verify_project(original,proposal,mapping):
    old=copy.deepcopy(original); new=copy.deepcopy(proposal)
    oldns,newns=old.pop("net_settings"),new.pop("net_settings")
    if old!=new: raise ValueError("non-netclass settings changed")
    oldc,newc=oldns.pop("classes"),newns.pop("classes")
    if newc[:len(oldc)]!=oldc or len(newc)!=len(oldc)+4: raise ValueError("existing class changed")
    new_add={c["name"]:c for c in newc[len(oldc):]}
    if set(new_add)!=set(pg.TARGETS): raise ValueError("wrong added classes")
    for cls,c in new_add.items():
        allowed={"name","priority","track_width"} | ({"diff_pair_width","diff_pair_gap"} if cls.startswith("DIFF") else set())
        if set(c)!=allowed: raise ValueError("new class overrides original non-geometry fields")
        if c["priority"]>=min(c0["priority"] for c0 in oldc): raise ValueError("geometry class priority is not highest")
    olda,newa=oldns.pop("netclass_assignments"),newns.pop("netclass_assignments")
    if oldns!=newns: raise ValueError("patterns, colors, schema or other net settings changed")
    if set(newa)!=set(olda)|set(mapping): raise ValueError("unexpected class-assignment net")
    for name,classes in newa.items():
        expected=olda.get(name,[]) + ([mapping[name]["class"]] if name in mapping else [])
        if classes!=expected: raise ValueError(f"changed original classes or exact spelling: {name}")

def proposal_rules(original,geometry):
    # Retain the existing narrow-neck eligibility literally; do not enlarge it.
    starts=[m.start() for m in re.finditer(r'\(rule "U1001 exact assigned F signal necks only"',original)]
    if len(starts)!=1: raise ValueError("expected exact frozen BGA exception once")
    neck=pg.balanced(original,starts[0])
    cm=re.search(r'\(condition\s+("(?:\\.|[^"\\])*")\)',neck)
    if not cm: raise ValueError("missing exact BGA neck condition")
    original_condition=json.loads(cm[1])
    rows=["\n# PROPOSED ONLY: ROOT106 c05 35um outer geometry; no native validation or fab release.",
          "# Only outer geometry is staged. All controlled In3 planning remains HELD_REFERENCE_RETURN.",
          "# Original rules remain the exact byte prefix. No isolation or via constraint is changed."]
    for cls in pg.TARGETS:
        rec=geometry["F.Cu"][cls]
        if rec!=geometry["B.Cu"][cls]: raise ValueError("outer models differ; need per-layer proposal")
        if rec["status"]!="PROVISIONAL_AB": raise ValueError("no valid outer proposal")
        ws=[c["w_mm"] for c in rec["corners"]]
        cond=f"(A.Type == 'Track' || A.Type == 'Arc') && A.hasNetclass('{cls}') && !({original_condition})"
        rows.extend([f'(rule "PROVISIONAL {cls} outer width" (layer outer)',
                     f' (condition {json.dumps(cond)})',
                     f' (constraint track_width (min {min(ws):.3f}mm) (opt {rec["w_mm"]:.3f}mm) (max {max(ws):.3f}mm)))'])
        if cls.startswith("DIFF"):
            ss=[c["s_mm"] for c in rec["corners"]]
            cond=f"A.hasNetclass('{cls}') && A.inDiffPair('*')"
            rows.extend([f'(rule "PROVISIONAL {cls} outer coupled gap" (layer outer)',
                         f' (condition {json.dumps(cond)})',
                         f' (constraint diff_pair_gap (min {min(ss):.3f}mm) (opt {rec["s_mm"]:.3f}mm) (max {max(ss):.3f}mm)))'])
    return original+"\n".join(rows)+"\n"

def main():
    records=pg.read_inputs()
    geometry=json.loads((HERE/"geometry.json").read_text(encoding="utf-8"))
    mapping=json.loads((HERE/"controlled-net-map.json").read_text(encoding="utf-8"))
    original=json.loads(pg.frozen(records,"project").read_text(encoding="utf-8"))
    original_rules=pg.frozen(records,"rules").read_bytes()
    rules=proposal_rules(original_rules.decode("utf-8"),geometry).encode("utf-8")
    if not rules.startswith(original_rules): raise ValueError("original rules byte prefix changed")
    pro=proposal_project(original,mapping,geometry)
    out=HERE/"future-copy-proposal"; out.mkdir(exist_ok=True)
    # Deliberately not sibling KiCad settings or a runnable board/project bundle.
    (out/"board.kicad_pro.proposed").write_text(json.dumps(pro,indent=2)+"\n",encoding="utf-8")
    (out/"board.kicad_dru.proposed").write_bytes(rules)
    plan={"scope":"PROVISIONAL_SETTINGS_FOR_FUTURE_ISOLATED_COPY_ONLY", "installed":False,
          "current_board_sha256":records["board"]["sha256"],"original_project_sha256":records["project"]["sha256"],
          "original_rules_sha256":records["rules"]["sha256"], "exact_assignment_count":len(mapping),
          "class_counts":dict(Counter(x["class"] for x in mapping.values())),
          "all_original_domain_memberships_and_patterns_preserved":True,
          "all_original_non_geometry_settings_preserved":True,"original_rule_prefix_byte_exact":True,
          "generic_future_planner_allowed_controlled_layers":["F.Cu","B.Cu"],
          "held_controlled_layers":{"In3.Cu":"HELD_REFERENCE_RETURN: actual In2 zone polygons only /IO_3V3; two equipotential reference planes unproved for every net/domain",
                                    "In1.Cu":"HELD_NOT_MODELLED_REFERENCE_LAYER", "In2.Cu":"HELD_NOT_MODELLED_PLANE_LAYER", "In4.Cu":"HELD_NOT_MODELLED_REFERENCE_LAYER"},
          "migration_is_blocked_until":["review current policy by pad UUID/net/function and actual length/edge/bus budgets",
                 "confirm fabricator finished stackup including masks, copper roughness and effective Dk",
                 "resolve 1.60 nominal versus 1.55 mask-inclusive stackup sum",
                 "verify continuous same-domain reference and return over every planned segment/transition",
                 "native parse and effective composite class/DRC constraints check on an isolated copy",
                 "native router layer-switch/pair-name/band behavior check, preserving literal BGA neck exceptions",
                 "fresh board DRC/partition/SI and preserved connection proof for actual changed settings/copper"],
          "important_limits":["rule gap applies only to recognized coupled pair portions; no uncoupled-length, skew or reference proof is added",
                 "original existing copper has not been resized or requalified; applying these proposals will require migration",
                 "historical policy reuses targets and exact net correspondence only; all historical lengths/reference/settling conclusions remain historical",
                 "width/gap bands are nominal mathematical exploration, not fabricator tolerances or guarantee"]}
    pg.write(out/"proposal.json",plan)
    pg.read_inputs()
    print(json.dumps({"verdict":"PASS_SOURCE_ONLY_PROPOSAL", "exact_assignments":len(mapping),"original_rules_byte_exact":True,
                      "staged_project_sha256":pg.sha((out/"board.kicad_pro.proposed").read_bytes()),
                      "staged_rules_sha256":pg.sha((out/"board.kicad_dru.proposed").read_bytes())}))

if __name__=="__main__":main()
