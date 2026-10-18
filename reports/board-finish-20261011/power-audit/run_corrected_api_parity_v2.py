"""Standalone corrected-export API parity; never uses historical SOURCE/sch.net."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
CORRECTED=ROOT/"electrical-correction/c11061-v2"
OUT=CORRECTED/"api-parity-v2"
BOARD=CORRECTED/"native/motherboard.kicad_pcb"
NET=CORRECTED/"corrected.net"
EXPECTED="513becb4b4ccab5626db70b64012812a58f207bfccc168fcc779c3b1a4bb1b2e"
EXTERNAL=Path("Z:/pcb-runs/claude-finish")
KICAD=Path("C:/Program Files/KiCad/10.0/bin")

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def snapshot():
    return {p.relative_to(CORRECTED/"native").as_posix():sha(p) for p in (CORRECTED/"native").rglob("*") if p.is_file()}

def gate(report,host,board_sha,net_sha):
    if report.get("tool")!="netlist_parity" or report["inputs"]["board"]["sha256"]!=board_sha or report["inputs"]["netlist"]["sha256"]!=net_sha:
        raise ValueError("wrong native inputs/tool")
    summary=report["summary"]
    required_zero=("parity_defects","components_missing_on_board","board_extra_unexpected","footprint_id_mismatch","footprint_id_mismatch_case_only","value_mismatch","duplicate_refs","pad_net_mismatch","netlist_nodes_without_board_pad","board_pads_without_netlist_node_with_net","board_pads_unnumbered_with_net","netlist_nets_without_board_pads","board_nets_with_pads_not_in_netlist","net_membership_differences","normalisation_collisions","pads_no_net_touched_by_track_or_via")
    if summary.get("status")!="parity_ok" or any(type(summary.get(key)) is not int or summary[key]!=0 for key in required_zero):
        raise ValueError("native parity defects/missing integer counts")
    if report["pads"].get("netlist_node_conflicts")!=[]:
        raise ValueError("conflicting native nodes")
    for native,portable in (("netlist_components","netlist_components"),("netlist_nets","netlist_nets"),("netlist_nodes","netlist_nodes"),("board_footprints","board_footprints"),("board_pads","board_pads"),("pads_matched","physical_pads_matched")):
        if type(summary.get(native)) is not int or summary[native]!=host[portable]:
            raise ValueError("native/host counts differ "+native)
    if summary["netlist_components"]!=2717 or summary["netlist_nodes"]!=9590:
        raise ValueError("corrected design inventory changed")
    binding=report.get("project_settings_binding",{})
    if binding.get("explicit_settings_manager_load") is not True or binding.get("explicit_board_set_project") is not True or binding.get("load_count")!=1:
        raise ValueError("project context not explicit unique load")
    if any(binding.get(key) is not False for key in ("save_requested","refill_requested","DRC_requested","connectivity_rebuild_requested")):
        raise ValueError("API check scope not read-only")
    cap=report.get("native_corrected_capacitor_fields",{})
    if cap!={"ref":"C11061","value":"4.7uF 25V X7R","MPN":"C2012X7R1E475K125AB","footprint":"Capacitor_SMD:C_0805_2012Metric","uuid":"73b53c88-a7dc-4167-881c-5246eb125d8a"}:
        raise ValueError("corrected cap native fields differ")
    return summary

def main():
    if OUT.exists():
        raise ValueError("choose fresh output; evidence directory exists")
    receipt=json.loads((CORRECTED/"receipt.json").read_text(encoding="utf-8"))
    if receipt["verdict"]!="SOURCE_CORRECTION_AND_NATIVE_EXPORT_PASS" or sha(BOARD)!=EXPECTED or sha(NET)!=receipt["native_export"]["sha256"]:
        raise ValueError("corrected source/export precondition failed")
    before=snapshot()
    for name,digest in receipt["corrected_native_inputs"].items():
        path=(CORRECTED/"native"/name).resolve()
        if not path.is_relative_to((CORRECTED/"native").resolve()) or before.get(name)!=digest:
            raise ValueError("corrected native input changed "+name)
    OUT.mkdir()
    (OUT/"tools").mkdir()
    sources={ROOT/"parity-repair/c05/tools/netlist_parity.py":OUT/"tools/netlist_parity.py",ROOT/"parity-repair/c05/tools/pcbtext.py":OUT/"tools/pcbtext.py",ROOT/"parity-repair/host_parity.py":OUT/"tools/host_parity.py",HERE/"corrected_api_entry_v2.py":OUT/"tools/corrected_api_entry_v2.py"}
    for source,dest in sources.items():
        dest.write_bytes(source.read_bytes())
        if sha(source)!=sha(dest):
            raise ValueError("tool copy mismatch")
    spec=importlib.util.spec_from_file_location("copied_host_parity",OUT/"tools/host_parity.py")
    host_module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(host_module)
    parser=host_module.load_parser(OUT/"tools/netlist_parity.py")
    nl=parser["read_netlist"](NET)
    portable=host_module.read_board_text(BOARD,parser,OUT/"tools/pcbtext.py")
    host=host_module.compare(nl,portable,parser)
    hierarchy=host_module.source_identity(CORRECTED/"native",nl,parser)
    if host["verdict"]!="PASS" or hierarchy["verdict"]!="PASS" or host["netlist_components"]!=2717 or host["netlist_nodes"]!=9590:
        raise ValueError("independent corrected host/hierarchy precondition failed")
    if nl["components"]["C11061"]["value"]!="4.7uF 25V X7R" or nl["components"]["C11061"]["properties"]["MPN"]!="C2012X7R1E475K125AB":
        raise ValueError("corrected export fields failed")
    (OUT/"host-parity.json").write_text(json.dumps(host,indent=2)+"\n",encoding="utf-8")
    (OUT/"source-hierarchy.json").write_text(json.dumps(hierarchy,indent=2)+"\n",encoding="utf-8")
    wrapper=EXTERNAL/"tools/heavyt.sh"
    tools=set(sources)|set(sources.values())|{Path(__file__),CORRECTED/"receipt.json",CORRECTED/"correct_rating.py",CORRECTED/"host-parity.json",NET,wrapper,KICAD/"python.exe",KICAD/"python311.dll",KICAD/"_pcbnew.dll",KICAD/"kicad-cli.exe",KICAD/"Lib/site-packages/pcbnew.py",KICAD/"Lib/site-packages/_pcbnew.pyd",Path("C:/Program Files/Git/usr/bin/sh.exe")}
    bound={str(path.resolve()):sha(path) for path in tools}
    (OUT/"inputs-before.json").write_text(json.dumps({"native_tree":before,"other_inputs_tools_binaries":bound,"corrected_export_sha256":sha(NET),"historical_sch_net":"bound only as immutable historical source; never used by this API invocation"},indent=2)+"\n",encoding="utf-8")
    command=["C:/Program Files/Git/usr/bin/sh.exe",wrapper.as_posix(),"kicad",(KICAD/"python.exe").as_posix(),(OUT/"tools/corrected_api_entry_v2.py").as_posix(),(OUT/"tools/netlist_parity.py").as_posix(),BOARD.as_posix(),NET.as_posix(),(OUT/"native-parity.json").as_posix()]
    started=time.time()
    (OUT/"invocation.json").write_text(json.dumps({"command":command,"started_unix":started,"slot":"existing test KiCad single slot","new_slots":0,"GPU_jobs":0,"native_fill_DRC_save":False},indent=2)+"\n",encoding="utf-8")
    env=os.environ.copy()
    env["PATH"]="C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;"+env["PATH"]
    env.update(OMP_NUM_THREADS="2",MKL_NUM_THREADS="2",OPENBLAS_NUM_THREADS="2")
    with (OUT/"native.log").open("w",encoding="utf-8") as log:
        run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=False)
    after=snapshot()
    result={"verdict":"INVALID_OR_FAIL","native_exit_code":run.returncode,"elapsed_seconds":round(time.time()-started,3),"board_sha256":sha(BOARD),"netlist_sha256":sha(NET),"native_tree_before":before,"native_tree_after":after,"other_inputs_tools_binaries":bound,"implemented":False,"adopted":False}
    try:
        if run.returncode!=0 or after!=before:
            raise ValueError("native failure or corrected design tree mutated")
        for name,digest in bound.items():
            if sha(name)!=digest:
                raise ValueError("bound input/tool/binary mutated "+name)
        output=OUT/"native-parity.json"
        if output.stat().st_mtime<started-1:
            raise ValueError("native output stale")
        report=json.loads(output.read_text(encoding="utf-8"))
        summary=gate(report,host,EXPECTED,bound[str(NET.resolve())])
        result.update(verdict="CORRECTED_SOURCE_NATIVE_API_PARITY_PASS",summary=summary,native_version=report["native_version"],native_report_sha256=sha(output),project_settings_binding=report["project_settings_binding"],native_corrected_capacitor_fields=report["native_corrected_capacitor_fields"],design_inputs_and_tools_unchanged_after=True)
    except (ValueError,KeyError,TypeError,OSError) as exc:
        result["reason"]=str(exc)
    result.update(evidence_class="Explicit project-bound API/source parity using freshly corrected native export",no_fill_no_DRC_no_save=True,
        limits=["No new schematic export in this check; corrected.net is bound to separate native-export receipt","No fresh zone fill, uncapped connectivity, native DRC or circuit/ERC result","Effective CT timing/inrush remains open despite25V-minimum rating correction","Power/current/thermal/SI/field full loads,183c05warnings and unfinished routing remain open","Original c05 and old sch.net remain historical and unchanged"])
    path=OUT/"receipt.json"
    path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"path":str(path),"sha256":sha(path),"verdict":result["verdict"],"reason":result.get("reason"),"native_exit_code":run.returncode}),flush=True)
    return 0 if result["verdict"].endswith("_PASS") else 1

if __name__=="__main__":
    raise SystemExit(main())
