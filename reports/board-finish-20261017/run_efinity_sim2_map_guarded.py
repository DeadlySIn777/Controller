"""Native vendor resource diagnostic of the existing full functional SIM2 top.

Never substitutes the tiny inhibited entry point. This maps the simulation core,
not a complete physical135-pin motherboard wrapper; no PNR or bitstream/program.
"""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
import psutil

H = Path(__file__).resolve().parent
ROOT = H.parent.parent
OUT = H / "efinity-functional-SIM2-map-r1"
INSTALL = Path("C:/Efinity/2026.1")


def sha(p):
    with Path(p).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def put(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    assert not OUT.exists()
    me = psutil.Process()
    me.cpu_affinity([16, 17])
    me.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    OUT.mkdir()
    inputs = OUT / "inputs"
    inputs.mkdir()
    canonical = ROOT / "gateware/v3/runtime"
    old = json.loads((ROOT / "reports/deeper-runtime-20261004/rtl/receipt.json").read_bytes())
    expected = {row["path"]: row["sha256"] for row in old["source_inventory"]}
    inventory = []
    for path in sorted(canonical.glob("*.v")):
        relative = path.relative_to(ROOT).as_posix()
        assert sha(path) == expected[relative], "Current RTL differs from the recorded functional SIM2 source"
        copied = inputs / path.name
        shutil.copyfile(path, copied)
        inventory.append({"source": str(path), "copy": str(copied), "SHA256": sha(path)})
    assert inventory and any(Path(r["copy"]).name == "cnc3_runtime_sim.v" for r in inventory)
    ns = "http://www.efinixinc.com/enf_proj"
    ET.register_namespace("efx", ns)
    tag = lambda name: "{" + ns + "}" + name
    project = ET.Element(tag("project"), name="cnc3_runtime_sim", description="Native resource diagnostic of frozen functional SIM2; physical wrapper absent", sw_version="2026.1.132")
    device = ET.SubElement(project, tag("device_info"))
    for name, value in (("family", "Trion"), ("device", "T20F256"), ("timing_model", "I4")):
        ET.SubElement(device, tag(name), name=value)
    design = ET.SubElement(project, tag("design_info"), def_veri_version="verilog_2k", def_vhdl_version="vhdl_2008", unified_flow="false")
    ET.SubElement(design, tag("top_module"), name="cnc3_runtime_sim")
    for row in inventory:
        ET.SubElement(design, tag("design_file"), name="inputs/" + Path(row["copy"]).name, version="default", library="default")
    ET.SubElement(design, tag("top_vhdl_arch"), name="")
    for name in ("constraint_info", "sim_info", "misc_info", "ip_info"):
        ET.SubElement(project, tag(name))
    synth = ET.SubElement(project, tag("synthesis"), tool_name="efx_map")
    for name, value, kind in (("work_dir", "work_syn", "e_string"), ("write_efx_verilog", "on", "e_bool"),
                              ("max_threads", "2", "e_integer"), ("blackbox-error", "1", "e_option")):
        ET.SubElement(synth, tag("param"), name=name, value=value, value_type=kind)
    xml = OUT / "cnc3_runtime_sim.xml"
    ET.indent(project)
    ET.ElementTree(project).write(xml, encoding="UTF-8", xml_declaration=True)
    pins = {str(p): sha(p) for p in (Path(__file__), xml, INSTALL / "bin/efx_run.bat")}
    args = ["cmd.exe", "/d", "/c", str(INSTALL / "bin/efx_run.bat"), "cnc3_runtime_sim", "--prj", "-f", "map", "--timeout", "900"]
    put("plan.json", {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "args": args, "cwd": str(OUT),
        "explicit_profile": "DISCONNECTED_FUNCTIONAL_SIM2_CORE_NATIVE_VENDOR_RESOURCE_DIAGNOSTIC",
        "top": "cnc3_runtime_sim", "family": "Trion", "device": "T20F256", "timing_model": "I4",
        "physical_top_wrapper_absent": True, "native_physical_IO_legality_different_check": "efinity-native-pincheck-r1",
        "affinity": [16, 17], "maximum_numeric_threads": 2, "CPU_pause": 70, "CPU_resume": 62,
        "source_inventory": inventory, "input_SHA256": pins, "PNR_bitstream_or_hardware_programming": False})
    env = dict(os.environ)
    env.update({key: "2" for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")})
    started = time.monotonic()
    peak, breaches, paused = 0.0, 0, set()
    with (OUT / "vendor-map.log").open("w", encoding="utf-8") as log:
        run = subprocess.Popen(args, cwd=OUT, env=env, stdout=log, stderr=subprocess.STDOUT)
        worker = psutil.Process(run.pid)
        print(f"Native Efinity functional-SIM2 resource diagnostic running, PID {run.pid}; two logical CPUs.", flush=True)
        try:
            while run.poll() is None:
                cpu = psutil.cpu_percent(interval=1)
                peak = max(peak, cpu)
                breaches += cpu >= 80
                try:
                    family = [worker, *worker.children(recursive=True)]
                except psutil.NoSuchProcess:
                    break
                if cpu >= 70:
                    for p in reversed(family):
                        if p.pid not in paused:
                            try:
                                p.suspend()
                                paused.add(p.pid)
                            except psutil.Error:
                                pass
                elif cpu < 62:
                    for p in family:
                        if p.pid in paused:
                            try:
                                p.resume()
                                paused.remove(p.pid)
                            except psutil.Error:
                                pass
                row = {"phase": "NATIVE_FUNCTIONAL_SIM2_MAP_RUNNING", "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                       "pid": run.pid, "CPU_percent": cpu, "paused_pids": sorted(paused)}
                with (OUT / "resource-samples.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(row) + "\n")
                put("status.json", row)
        finally:
            for pid in paused:
                try:
                    psutil.Process(pid).resume()
                except psutil.Error:
                    pass
        rc = run.wait()
    assert all(sha(Path(r["source"])) == sha(Path(r["copy"])) == r["SHA256"] for r in inventory)
    assert all(sha(Path(p)) == digest for p, digest in pins.items())
    put("receipt.json", {"status": "VENDOR_FUNCTIONAL_SIM2_MAPPING_PROCESS_COMPLETE_RESULT_REVIEW_REQUIRED", "exit_code": rc,
                         "source_inventory": inventory, "sources_unchanged": True, "input_SHA256": pins,
                         "elapsed_seconds": time.monotonic() - started, "peak_CPU_percent": peak, "samples_at_or_above_80_percent": breaches,
                         "full_physical_motherboard_RTL_fit_timing": "UNEXECUTED_OPEN", "physical_measurements": 0,
                         "PNR_bitstream_or_programming_requested": False, "adopted": False, "manufacturing_ready": False})
    put("status.json", {"phase": "MAPPING_PROCESS_COMPLETE_REVIEW_REQUIRED", "exit_code": rc})
    print(f"Functional SIM2 vendor mapping process exited {rc}; full physical design fit remains open.", flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
