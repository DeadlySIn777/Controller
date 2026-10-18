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
def main(out,motors,linuxcnc):
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
    wsl=["wsl","-d","GarciaMechBuilder","-u","root","--","taskset","-c","16,17"]
    executions=[];error=None;install_attempted=False;observation=None
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
        run("verify-copy",wsl+["chroot",rootfs,"/usr/sbin/runuser","-u","cnclab","--","python3",work+"/source/tools/prepare_cnc3_sim2.py","--store",work+"/configuration/setup.json","--verify",work+"/configuration/runtime.json"])
        run("driver-spi",wsl+["timeout","-k","5","240","chroot",rootfs,work+"/build/driver-spi",work+"/configuration/runtime.json"],timeout=260)
        run("manifest-controls",wsl+["chroot",rootfs,"python3",work+"/source/cnc3_runtime/tests/manifest_controls.py",work+"/build/manifest-probe",work+"/configuration/runtime.json"])
        if linuxcnc:
            install_attempted=True
            run("install-temporary-module",wsl+["python3",unix(out/"source/cnc3_runtime/tools/module_guard.py"),"install",work,unix(out)])
            result=run("LinuxCNC-task",wsl+["timeout","-s","KILL","420","unshare","--mount","--pid","--ipc","--net","--fork","--kill-child","sh",unix(out/"source/cnc3_runtime/tools/run_linuxcnc.sh"),work,"c3rt_"+key[:20],unix(out)],timeout=450)
            if (out/"linuxcnc.json").exists():observation=read_json(out/"linuxcnc.json")
            else:
                for line in result.stdout.decode(errors="replace").splitlines():
                    if line.startswith("CNC3_RUNTIME_RECEIPT_JSON="):observation=json.loads(line.split("=",1)[1])
                if observation is None:
                    result=run("collect-LinuxCNC",wsl+["cat",rootfs+work+"/linuxcnc.json"]);observation=json.loads(result.stdout)
                (out/"linuxcnc.json").write_text(json.dumps(observation,indent=2)+"\n",encoding="utf-8")
            if observation["status"]!="PASS":raise RuntimeError("NML trajectory observations failed")
    except Exception as exc:error=repr(exc)
    finally:
        if linuxcnc:
            transcript=out/"LinuxCNC-task.log"
            if not (out/"linuxcnc.json").exists() and transcript.exists():
                for line in transcript.read_text(errors="replace").splitlines():
                    if line.startswith("CNC3_RUNTIME_RECEIPT_JSON="):
                        observation=json.loads(line.split("=",1)[1]);(out/"linuxcnc.json").write_text(json.dumps(observation,indent=2)+"\n",encoding="utf-8")
            try:
                # Collect failure evidence too; never replace an earlier result.
                if not (out/"linuxcnc.json").exists():
                    result=run("collect-LinuxCNC-failure",wsl+["cat","/root/.cache/controller-lab-linuxcnc/rootfs"+work+"/linuxcnc.json"])
                    observation=json.loads(result.stdout);(out/"linuxcnc.json").write_text(json.dumps(observation,indent=2)+"\n",encoding="utf-8")
            except Exception:pass
        if install_attempted and (out/"installed-modules-before.json").exists():
            try:run("restore-installed-module",wsl+["python3",unix(out/"source/cnc3_runtime/tools/module_guard.py"),"restore",work,unix(out)])
            except Exception as exc:error=(error or "")+"; restoration: "+repr(exc)
    unchanged=all(sha(ROOT/p)==s for p,s in source_before.items())
    preserved=not linuxcnc or ((out/"installed-modules-after.json").exists() and read_json(out/"installed-modules-before.json")==read_json(out/"installed-modules-after.json"))
    receipt={"status":"PASS" if not error and unchanged and sha(store)==store_before and preserved else "FAIL","error":error,"source_sha256":source_before,"source_inputs_unchanged":unchanged,"settings_preserved":sha(store)==store_before,"settings_sha256":store_before,"installed_existing_rootfs_modules_preserved":preserved,"configuration_manifest_sha256":manifest["manifest_sha256"],"rootfs_work":work,"run_key":key,"executions":executions,"observations":observation,"scope":{"actual_CNC3_C_driver":True,"actual_serial_SPI":True,"compiled_RTL":True,"independent_disconnected_provider":True,"actual_LinuxCNC_task_trajectory":bool(observation and observation["status"]=="PASS"),"physical_qualification":False,"hardware_connections":0,"paid_API_calls":0},"full_requested_milestone_complete":False}
    (out/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":receipt["status"],"error":error}),flush=True)
    return 0 if receipt["status"]=="PASS" else 1
if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--out",type=Path,required=True);parser.add_argument("--motors",type=int,choices=[8,12],required=True);parser.add_argument("--linuxcnc",action="store_true");args=parser.parse_args()
    raise SystemExit(main(args.out.resolve(),args.motors,args.linuxcnc))
