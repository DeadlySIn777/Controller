"""Run a bounded twelve-instance actual-RTL characterization, without machine I/O.

The production endpoint stays six-channel CNC1. Exploratory timing parameters
do not change production firmware, electrical ratings or drive compatibility.
"""
from __future__ import annotations
import argparse,datetime,hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path,PureWindowsPath

ROOT=Path(__file__).resolve().parents[1]
PROFILES={"historical-default":100,"exploratory-12-tick":12,"exploratory-9-tick":9}

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p:Path,value:object)->None:p.write_text(json.dumps(value,indent=2)+"\n",encoding="utf8")
def linux_path(p:Path)->str:
    if os.name!="nt":return str(p.resolve())
    w=PureWindowsPath(p.resolve())
    if not w.drive or w.drive.startswith("\\"):raise ValueError("WSL characterization requires a local drive path")
    return "/mnt/"+w.drive[0].lower()+"/"+"/".join(w.parts[1:])

def run(out:Path,name:str,cmd:list[str],timeout:int=180)->dict:
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout,encoding="utf8",errors="replace")
        text=r.stdout+r.stderr;code=r.returncode
    except (OSError,subprocess.TimeoutExpired)as error:
        text=str(error);code=-1
    log=out/(name+".log");log.write_text(text,encoding="utf8")
    return dict(command=cmd,started_utc=started,returncode=code,log=str(log),log_sha256=sha(log))

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--cycles",type=int,default=4096)
    ap.add_argument("--wsl-distro",default="GarciaMechBuilder")
    a=ap.parse_args()
    if not 512<=a.cycles<=10000000:ap.error("cycles must be between512 and10000000")
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    rtl=ROOT/"gateware/rtl/cnc_stepgen.v";bench=ROOT/"gateware/tests/tb_stepgen12_characterization.sv"
    frozen={str(p):sha(p)for p in(rtl,bench,Path(__file__))}
    prefix=["wsl.exe","-d",a.wsl_distro,"--"]if os.name=="nt"else[]
    runs=[run(out,"iverilog-version",prefix+["iverilog","-V"]),run(out,"vvp-version",prefix+["vvp","-V"])]
    profiles=[];failed=any(r["returncode"]for r in runs)
    for name,ticks in PROFILES.items():
        if failed:break
        binary=out/(name+".vvp")
        command=prefix+["iverilog","-g2012","-Wall","-s","tb_stepgen12_characterization",
            "-Ptb_stepgen12_characterization.HIGH="+str(ticks),
            "-Ptb_stepgen12_characterization.LOW="+str(ticks),
            "-Ptb_stepgen12_characterization.SETUP="+str(ticks),
            "-Ptb_stepgen12_characterization.HOLD="+str(ticks),
            "-o",linux_path(binary),linux_path(rtl),linux_path(bench)]
        compilation=run(out,name+"-compile",command);runs.append(compilation)
        if compilation["returncode"]:failed=True;break
        simulation=run(out,name+"-simulation",prefix+["vvp",linux_path(binary),"+cycles="+str(a.cycles)],timeout=600);runs.append(simulation)
        lines=Path(simulation["log"]).read_text(encoding="utf8").splitlines()
        rows=[json.loads(s)for s in lines if s.startswith('{"increment"')]
        summary=[s for s in lines if s.startswith("SUMMARY ")]
        passed=simulation["returncode"]==0 and len(rows)==48 and len(summary)==1
        safe=2**32//(ticks+ticks+1)
        # Require independent observed behavior on both sides of the integer
        # boundary, in both signs and every one of the twelve generators.
        edge_rows=[r for r in rows if r["adversarial_reachable_phase"]]
        for increment,expected_mask in [(safe,0),(safe+1,4095)]:
            at=[r for r in edge_rows if r["increment"]==increment]
            passed=passed and {r["reverse"]for r in at}=={0,1} and all(r["fault_mask"]==expected_mask for r in at)
        profiles.append(dict(name=name,status="PASS"if passed else"FAIL",scope="Twelve simultaneous instances of unchanged pulse-generator RTL only",high_cycles=ticks,low_cycles=ticks,setup_cycles=ticks,hold_cycles=ticks,assumed_clock_hz=50000000,analytical_safe_increment=safe,design_pulse_ceiling_hz=50000000*safe/2**32,first_adversarial_failure_increment=safe+1,first_adversarial_failure_hz=50000000*(safe+1)/2**32,boundary_evidence_type="HDL_SIMULATION_AND_DESIGN_ARITHMETIC",finite_sample_cycles=a.cycles,rows=rows,binary_sha256=sha(binary),summary=summary))
        failed=failed or not passed
    unchanged=all(sha(Path(p))==h for p,h in frozen.items());failed=failed or not unchanged
    report=dict(status="FAIL"if failed else"PASS",scope="Isolated pulse-generator characterization; not twelve-channel CNC3/end-to-end controller qualification",input_sha256=frozen,source_hashes_unchanged=unchanged,profiles=profiles,runs=runs,fixture_phase_injection="Zero or reset-reachable DDS subgroup phase; explicitly injected without modifying production RTL",real_machine_interfaces_opened=False,production_endpoint_modified=False,production_default_endpoint_rate_limit_hz=195312.5,production_default_rate_limit_evidence="Existing CNC1 MAX_RATE 0x01000000 at assumed50MHz; endpoint excluded from this sweep",physical_validation_required=True,vendor_timing_performed=False,output_driver_cable_load_timing_performed=False,CNC3_transport_tested=False,simultaneous_full_board_load_tested=False,production_rating_hz=None,manufacturing_ready=False)
    write(out/"receipt.json",report)
    print(json.dumps(dict(status=report["status"],profiles=len(profiles),cases=sum(len(p["rows"])for p in profiles),scope=report["scope"],receipt=str(out/"receipt.json"))))
    return int(failed)

if __name__=="__main__":raise SystemExit(main())
