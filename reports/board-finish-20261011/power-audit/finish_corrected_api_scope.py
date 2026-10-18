"""Read-only final path/hash/source-scope check over completed API evidence."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import run_corrected_api_parity_v2 as runner

def main():
    output=runner.OUT/"qualification-scope.json"
    if output.exists():raise ValueError("new immutable output required")
    receipt=json.loads((runner.OUT/"receipt.json").read_text())
    report=json.loads((runner.OUT/"native-parity.json").read_text())
    host=json.loads((runner.OUT/"host-parity.json").read_text())
    if receipt["verdict"]!="CORRECTED_SOURCE_NATIVE_API_PARITY_PASS" or receipt["native_report_sha256"]!=runner.sha(runner.OUT/"native-parity.json"):
        raise ValueError("completed native receipt/hash mismatch")
    runner.gate(report,host,runner.EXPECTED,runner.sha(runner.NET))
    if Path(report["inputs"]["board"]["path"]).resolve()!=runner.BOARD.resolve() or Path(report["inputs"]["netlist"]["path"]).resolve()!=runner.NET.resolve():
        raise ValueError("native input paths are not corrected exact targets")
    if Path(report["project_settings_binding"]["project"]).resolve()!=runner.BOARD.with_suffix(".kicad_pro").resolve():
        raise ValueError("project path is not exact corrected sibling")
    if Path(report["native_pcbnew_module"]).resolve()!=(runner.KICAD/"Lib/site-packages/pcbnew.py").resolve():
        raise ValueError("native API module path not bound")
    if receipt["native_tree_before"]!=receipt["native_tree_after"] or runner.snapshot()!=receipt["native_tree_before"]:
        raise ValueError("corrected native design tree changed")
    for path,sha in receipt["other_inputs_tools_binaries"].items():
        if runner.sha(path)!=sha:raise ValueError("bound input/tool/binary changed "+path)
    test=Path(__file__).with_name("test_corrected_api_guard.py")
    run=subprocess.run([sys.executable,str(test)],capture_output=True,text=True,check=False)
    (runner.OUT/"guard-test.log").write_text(run.stdout+run.stderr,encoding="utf-8")
    if run.returncode!=0:raise ValueError("API guard fixtures failed")
    envelope=Path("hardware/sbc_power/design-envelope.json").resolve()
    historical=json.loads(envelope.read_text())
    refs={str(path.resolve()):runner.sha(path) for path in (Path(__file__),Path(runner.__file__),test,envelope,runner.CORRECTED/"receipt.json",runner.OUT/"receipt.json",runner.OUT/"native-parity.json",runner.OUT/"host-parity.json",runner.OUT/"source-hierarchy.json",runner.OUT/"guard-test.log")}
    result={"verdict":"CORRECTED_SOURCE_NATIVE_API_PARITY_AND_SCOPE_PASS","evidence_class":"Source/explicit-project native API parity, no fill/DRC/connectivity/timing proof","board_sha256":runner.EXPECTED,"corrected_export_sha256":runner.sha(runner.NET),"native_version":report["native_version"],"native_summary":report["summary"],"C11061":report["native_corrected_capacitor_fields"],
        "native_input_tools_binaries_unchanged":True,"guard_fixtures_pass":11,"checks_single_read_only_api_load":True,
        "historical_source_distinction":{"historical_file":str(envelope),"standalone_CT_part":"CTSW1","historical_value":"1uF50V X7R","historical_net":"SBC_SLEW_CT","historical_effective_CT_f":historical["bounds"]["switch_ct_effective_f"],"ROOT106_CT_part":"C11061","ROOT106_corrected_value":"4.7uF25V X7R","ROOT106_net":"SBC_RAMP_CT","historical_timing_qualification_inherited":False,"current_ramp_inrush_timing_status":"OPEN_REQUIRES_CURRENT_PART_AND_CURRENT_CIRCUIT_ANALYSIS"},
        "limits":["Rating-only correction and source/API parity are proven here; circuit behavior is not","Current4.7uF nominal is distinct from historical1uF nominal/effective envelope; neither DC-bias nor timing bounds transfer automatically","No full-board native DRC/refill/unconnected partition remeasure, circuit ERC, transient, thermal, current/SI or fabrication proof","All3switches retain CT/control pin intent; no motor CT caps invented","Oldsch.net is historical and never the corrected API input"],"read_set_sha256":refs,"native_jobs":1,"new_slots":0,"GPU_jobs":0,"adopted":False,"manufacturing_ready":False}
    output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"path":str(output),"sha256":runner.sha(output),"verdict":result["verdict"],"guard_fixtures":11}))

if __name__=="__main__":main()
