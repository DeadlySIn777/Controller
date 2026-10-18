"""Source-bound compiled-C / actual-SPI / disconnected-provider qualification."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from controller_config.service import read_json
from controller_config.setup_service import SetupService
from controller_lab.cnc3_configuration import prepare_configuration,verify_configuration
from tools.create_cnc3_qualification_fixture import runtime_sources

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def unix(path):
    value=path.resolve().as_posix()
    return "/mnt/"+value[0].lower()+value[2:]
def main(out,motors):
    if out.exists():raise ValueError("qualification output must be new")
    out.mkdir(parents=True)
    fixture=ROOT/f"reports/deeper-runtime-20261004/host/fixtures-{motors}"
    store=fixture/"setup.json";store_before=sha(store)
    inventory=runtime_sources();source_before={p:sha(ROOT/p) for p in inventory}
    manifest=prepare_configuration(SetupService(store),read_json(fixture/"binding.json"),run_id=str(uuid.uuid4()),source_root=ROOT,source_files=inventory,encoder_mapping=read_json(fixture/"encoder-mapping.json"))
    verify_configuration(manifest,SetupService(store),source_root=ROOT,expected_source_files=inventory)
    (out/"configuration").mkdir()
    (out/"configuration/runtime.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    shutil.copyfile(store,out/"configuration/setup.json")
    for p in inventory:
        destination=out/"source"/p;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,destination)
    key=uuid.uuid4().hex;work="/work/deeper-cnc3-"+key
    wsl=["wsl","-d","GarciaMechBuilder","-u","root","--"]
    executions=[];error=None
    def run(stage,args,timeout=900):
        started=time.monotonic();result=subprocess.run(args,capture_output=True,timeout=timeout)
        log=out/(stage+".log");log.write_bytes(result.stdout+result.stderr)
        executions.append({"stage":stage,"command":args,"exit_code":result.returncode,"seconds":round(time.monotonic()-started,3),"log_sha256":sha(log)})
        print(json.dumps({"stage":stage,"exit_code":result.returncode}),flush=True)
        if result.returncode:raise RuntimeError(stage+" failed")
        return result
    try:
        run("build",wsl+["sh",unix(out/"source/cnc3_runtime/tools/build.sh"),unix(out),key])
        rootfs="/root/.cache/controller-lab-linuxcnc/rootfs"
        run("verify-copy",wsl+["chroot",rootfs,"python3",work+"/source/tools/prepare_cnc3_sim2.py","--store",work+"/configuration/setup.json","--verify",work+"/configuration/runtime.json"])
        run("driver-spi",wsl+["chroot",rootfs,work+"/build/driver-spi",work+"/configuration/runtime.json"],timeout=180)
    except Exception as exc:error=repr(exc)
    unchanged=all(sha(ROOT/p)==s for p,s in source_before.items())
    receipt={"status":"PASS" if not error and unchanged and sha(store)==store_before else "FAIL","error":error,"source_sha256":source_before,"source_inputs_unchanged":unchanged,"settings_preserved":sha(store)==store_before,"settings_sha256":store_before,"configuration_manifest_sha256":manifest["manifest_sha256"],"rootfs_work":work,"run_key":key,"executions":executions,"scope":{"actual_CNC3_C_driver":True,"actual_serial_SPI":True,"compiled_RTL":True,"independent_disconnected_provider":True,"actual_LinuxCNC_task_trajectory":False,"physical_qualification":False,"hardware_connections":0,"paid_API_calls":0},"full_requested_milestone_complete":False}
    (out/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":receipt["status"],"error":error}),flush=True)
    return 0 if receipt["status"]=="PASS" else 1
if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--out",type=Path,required=True);parser.add_argument("--motors",type=int,choices=[8,12],required=True);args=parser.parse_args()
    raise SystemExit(main(args.out.resolve(),args.motors))
