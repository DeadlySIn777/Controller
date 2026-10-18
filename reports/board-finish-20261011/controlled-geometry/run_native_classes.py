"""Root-authorized shared-slot class probe. Separate proposal copy, no save/fill/DRC."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import plan_geometry as pg
import stage_proposal as sp
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"final-bundle/native-open"))
from open_check_shared import sha,inventory,require,no_api_errors

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/"measure/c05-shared/copy"
HELPER=Path("Z:/pcb-runs/claude-finish/tools/heavy.sh")
API_DIR=HERE.parent/"final-bundle/native-open"

def validate(raw,inputs,mapping,geometry):
    require(raw["schema_version"]==1 and raw["native_version"]=="10.0.4","native version/schema differs")
    require(raw["probe_sha256"]==inputs["read_set"][str(HERE/"probe_native_classes.py")],"native producer differs")
    for role in ("baseline","proposal"):
        ctx=raw[role];no_api_errors(ctx)
        require(Path(ctx["board_path"]).resolve()==Path(inputs[role+"_board"]).resolve(),"wrong loaded board")
        require(ctx["directory_before_sha256"]==inputs[role+"_before_sha256"] and ctx["directory_before_sha256"]==ctx["directory_after_sha256"] and ctx["directory_unchanged"] is True,"input directory changed")
        snap=ctx["binding_and_minima"]
        require(snap["project_is_none"] is False and snap["settings_manager_open_not_dummy"] is True and snap["requested_project_present_in_manager"] is True,"project is dummy/unbound")
        require(ctx["project_unloaded_without_save"] is True,"project not unloaded without saving")
    old,new=raw["baseline"],raw["proposal"]
    require(old["binding_and_minima"]["settings_nm"]==new["binding_and_minima"]["settings_nm"],"global minima changed")
    oc,nc=old["declared_classes"],new["declared_classes"]
    require(len(oc)==28 and len(nc)==32 and set(nc)==set(oc)|set(pg.TARGETS),"native declared class set differs")
    for name,values in oc.items():require(nc[name]==values,"native original class changed: "+name)
    oe,ne=old["all_named_net_effective_classes"],new["all_named_net_effective_classes"]
    require(set(oe)==set(ne) and set(mapping)<=set(oe),"named net inventory differs/missing selected nets")
    changed=[]
    for name,previous in oe.items():
        current=ne[name]
        if name not in mapping:
            require(previous==current,"unselected effective class changed: "+name)
            continue
        rec=mapping[name];cls=rec["class"];g=geometry["F.Cu"][cls]
        require(rec["domain"] in current["constituents"],"effective original domain lost: "+name)
        require(cls in current["constituents"],"new class missing from effective constituents")
        require(current["GetTrackWidth"]==round(g["w_mm"]*1e6),"native track geometry differs: "+name)
        exclude={"GetName","GetPriority","constituents","GetTrackWidth"}
        if cls.startswith("DIFF"):
            require(current["GetDiffPairWidth"]==round(g["w_mm"]*1e6) and current["GetDiffPairGap"]==round(g["s_mm"]*1e6),"native pair geometry differs: "+name)
            exclude|={"GetDiffPairWidth","GetDiffPairGap"}
        for field,value in previous.items():
            if field not in exclude:require(current[field]==value,"native inherited property changed: "+name+" "+field)
        changed.append(name)
    for flag in ("refill","DRC","Save","GUI"):require(raw[flag] is False,"probe exceeded scope")
    return {"verdict":"PASS_NATIVE_EFFECTIVE_CLASSES_ONLY","native_version":raw["native_version"],
            "board_sha256":inputs["board_sha256"],"existing_classes_unchanged":28,"total_proposal_classes":32,
            "all_named_nets_checked":len(oe),"selected_controlled_nets_checked":len(changed),
            "all_non_geometry_inherited_values_preserved":True,"real_non_dummy_sibling_project":True,
            "global_minima_unchanged":True,"both_input_directories_unchanged":True,
            "native_custom_rule_full_parse_and_conditions":"UNCONFIRMED_API_NOT_EXPOSED_SILENT_INIT_CATCH",
            "In3_controlled_routing":"HELD_REFERENCE_RETURN","installed":False,"routing_qualified":False,
            "limits":["native LoadBoard/effective netclass observation only; no DRC or router interaction",
                      "current c05 copper unchanged; original raw rules retained as byte prefix in proposal",
                      "no implication of reference continuity, SI, fab geometry or native custom-rule enforcement"]}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",required=True,type=Path);a=ap.parse_args()
    out=a.out.resolve();require(out.is_relative_to(HERE) and not out.exists(),"new isolated output child required")
    records=pg.read_inputs();mapping=json.loads((HERE/"controlled-net-map.json").read_text())
    geometry=json.loads((HERE/"geometry.json").read_text());proposed=HERE/"future-copy-proposal"
    original=json.loads(pg.frozen(records,"project").read_text())
    proposal=json.loads((proposed/"board.kicad_pro.proposed").read_text());sp.verify_project(original,proposal,mapping)
    require((proposed/"board.kicad_dru.proposed").read_bytes().startswith(pg.frozen(records,"rules").read_bytes()),"domain rules changed")
    out.mkdir();clone=out/"proposal-copy";clone.mkdir()
    for target,source in (("board.kicad_pcb",pg.frozen(records,"board")),("board.kicad_pro",proposed/"board.kicad_pro.proposed"),("board.kicad_dru",proposed/"board.kicad_dru.proposed")):
        (clone/target).write_bytes(source.read_bytes())
    sources=[Path(__file__),HERE/"probe_native_classes.py",HERE/"plan_geometry.py",HERE/"stage_proposal.py",HELPER,
             API_DIR/"open_check_shared.py",API_DIR/"probe_native_open.py",HERE/"inputs.json",HERE/"controlled-net-map.json",HERE/"geometry.json",proposed/"board.kicad_pro.proposed",proposed/"board.kicad_dru.proposed"]
    bins=[Path("C:/Program Files/KiCad/10.0/bin")/name for name in ("python.exe","_pcbnew.dll","kicad-cli.exe","Lib/site-packages/pcbnew.py")]
    inputs={"board_sha256":records["board"]["sha256"],"baseline_board":str(BASE/"board.kicad_pcb"),"proposal_board":str(clone/"board.kicad_pcb"),
            "baseline_before_sha256":inventory(BASE),"proposal_before_sha256":inventory(clone),
            "read_set":{str(p):sha(p) for p in sources+bins},"slot":"existing shared heavy.sh","new_slots":0,"new_GPU_jobs":0}
    require(inputs["baseline_before_sha256"]["board.kicad_pcb"]==records["board"]["sha256"],"baseline board differs")
    require(inputs["baseline_before_sha256"]["board.kicad_pro"]==records["project"]["sha256"] and inputs["baseline_before_sha256"]["board.kicad_dru"]==records["rules"]["sha256"],"baseline project/rules differ")
    pg.write(out/"inputs.json",inputs);input_sha=sha(out/"inputs.json")
    command=["C:/Program Files/Git/usr/bin/sh.exe",HELPER.as_posix(),"kicad","C:/Program Files/KiCad/10.0/bin/python.exe",(HERE/"probe_native_classes.py").as_posix(),"--baseline",inputs["baseline_board"],"--proposal",inputs["proposal_board"],"--out",str(out/"native-classes.json")]
    start=time.time();pg.write(out/"invocation.json",{"command":command,"start_unix":start,"inputs_sha256":input_sha})
    env=os.environ.copy();env["PATH"]="C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;"+env["PATH"]
    with (out/"native-classes.log").open("w",encoding="utf-8") as log:
        process=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=False)
    try:
        require(sha(out/"inputs.json")==input_sha,"saved inputs changed")
        require(all(sha(p)==digest for p,digest in inputs["read_set"].items()),"source/runtime changed")
        require(inventory(BASE)==inputs["baseline_before_sha256"] and inventory(clone)==inputs["proposal_before_sha256"],"directory changed")
        require(process.returncode==0,"native probe exit "+str(process.returncode))
        require((out/"native-classes.json").stat().st_mtime>=start-1,"stale native report")
        pg.read_inputs();result=validate(json.loads((out/"native-classes.json").read_text()),inputs,mapping,geometry)
        result.update(elapsed_seconds=round(time.time()-start,3),native_exit=process.returncode,
                      report_sha256=sha(out/"native-classes.json"),inputs_sha256=input_sha)
        code=0
    except (ValueError,KeyError,TypeError,OSError) as exc:
        result={"verdict":"INVALID_OR_FAIL","reason":str(exc),"native_exit":process.returncode,"elapsed_seconds":round(time.time()-start,3),"installed":False};code=1
    pg.write(out/"receipt.json",result);print(json.dumps(result));return code

if __name__=="__main__":raise SystemExit(main())
