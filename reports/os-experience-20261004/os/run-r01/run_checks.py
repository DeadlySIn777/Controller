"""Source-bound offline overlay, actual nonroot Linux startup/HTTP and unit syntax."""
from datetime import datetime,timezone
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from controller_config.setup_service import SetupService,example_draft
from controller_os.image import APP,application_sources,stage,verify_image

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):
    text=p.resolve().as_posix();return "/mnt/"+text[0].lower()+text[2:]
def main(out):
    out=out.resolve()
    if out.exists() or not out.is_relative_to(HERE):raise ValueError("fresh OS report output required")
    out.mkdir();source={name:hashlib.sha256(body).hexdigest() for name,body in application_sources(ROOT).items()}
    for name in ("tools/controller_os.py","tests/test_controller_os.py"):
        source[name]=sha(ROOT/name)
    helpers=[Path(__file__),HERE/"linux_smoke.py",HERE/"prepare_linux_control.py"]
    helper_sha={p.name:sha(p) for p in helpers};commands=[];failure=None;observations=None
    def run(name,command,expected=0,timeout=120):
        before=time.monotonic();result=subprocess.run(command,capture_output=True,timeout=timeout)
        log=out/(name+".log");log.write_bytes(result.stdout+result.stderr)
        commands.append({"stage":name,"command":command,"exit_code":result.returncode,"seconds":round(time.monotonic()-before,3),"log_sha256":sha(log)})
        print(json.dumps({"stage":name,"exit_code":result.returncode}),flush=True)
        if result.returncode!=expected:raise RuntimeError(name+" unexpected exit")
        return result
    try:
        run("adversarial-tests",[sys.executable,"-m","unittest","discover","-s","tests","-p","test_controller_os.py","-v"])
        first=stage(ROOT,out/"image-a",allow_development=True,release_id="controller-development-r1")
        second=stage(ROOT,out/"image-b",allow_development=True,release_id="controller-development-r1")
        assert first["overlay_sha256"]==second["overlay_sha256"] and first["manifest_sha256"]==second["manifest_sha256"]
        verify_image(out/"image-a/rootfs",allow_development=True,exact_overlay=True)
        fixture=out/"workspace";fixture.mkdir();service=SetupService(fixture/"setup.json")
        service.initialize();service.save_draft(example_draft("sim-machine-12motor"),0);service.commit(service.preview(),str(uuid.uuid4()))
        Path(str(service.path)+".setup.lock").unlink() # Own new fixture only; no existing user lock.
        settings_hash=sha(service.path)
        for helper in helpers:shutil.copyfile(helper,out/helper.name)
        key=uuid.uuid4().hex;work="/work/controller-os-"+key;rootfs="/root/.cache/controller-lab-linuxcnc/rootfs"
        wsl=["wsl","-d","GarciaMechBuilder","-u","root","--"]
        run("create-isolated-work",wsl+["mkdir",rootfs+work])
        run("copy-overlay",wsl+["cp","-r",unix(out/"image-a/rootfs"),rootfs+work+"/rootfs"])
        run("copy-readonly-fixture",wsl+["cp","-r",unix(fixture),rootfs+work+"/workspace"])
        for helper in ("linux_smoke.py","prepare_linux_control.py"):
            run("copy-"+helper,wsl+["cp",unix(out/helper),rootfs+work+"/"+helper])
        run("prepare-readonly-control",wsl+["chroot",rootfs,"python3",work+"/prepare_linux_control.py",work])
        run("systemd-version",wsl+["chroot",rootfs,"systemd-analyze","--version"])
        units=work+"/rootfs/etc/systemd/system/"
        run("systemd-unit-syntax",wsl+["chroot",rootfs,"/usr/bin/env","SYSTEMD_UNIT_PATH="+units+":/usr/lib/systemd/system","systemd-analyze","verify",*[units+name for name in ("controller-preflight.service","controller-shell.service","controller-recovery.service","controller-recovery.target","controller.target")]])
        result=run("nonroot-linux-readonly-http",wsl+["unshare","--net","--", "chroot",rootfs,"/usr/sbin/runuser","-u","cnclab","--","/usr/bin/env","PYTHONDONTWRITEBYTECODE=1","PYTHONPATH="+work+"/rootfs/"+APP,"python3",work+"/linux_smoke.py","--root",work+"/rootfs","--workspace",work+"/workspace"])
        # Only loopback HTTP is exercised. No external route/interface or host
        # desktop is reconfigured; if unshare's loopback starts down, the smoke
        # is rerun in a private net namespace by a separately captured helper.
        observations=json.loads(result.stdout);assert observations["status"]=="PASS"
        (out/"linux-observations.json").write_text(json.dumps(observations,indent=2)+"\n",encoding="utf8")
        assert sha(service.path)==settings_hash
    except Exception as error:failure=repr(error)
    stable=all(sha(ROOT/name)==value for name,value in source.items()) and all(sha(HERE/name)==value for name,value in helper_sha.items())
    receipt={"schema_version":1,"utc":datetime.now(timezone.utc).isoformat(),"status":"PASS_WITHIN_OFFLINE_OVERLAY_SCOPE" if failure is None and stable else "FAIL",
        "error":failure,"source_sha256":source,"source_inputs_unchanged":stable,"runner_sha256":helper_sha,"executions":commands,"linux_observations":observations,
        "deterministic_overlay":first if 'first' in locals() else None,"rootfs_work":work if 'work' in locals() else None,
        "actual_physical_boot":False,"bootable_image_qualified":False,"signed_release":False,"services_installed_or_enabled":False,
        "desktop_or_network_config_modified":False,"paid_api_calls":0,"physical_device_connections":0}
    receipt["artifact_sha256"]={p.relative_to(out).as_posix():sha(p) for p in out.rglob("*") if p.is_file()}
    (out/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"status":receipt["status"],"error":failure,"source_files":len(source)}),flush=True)
    return 0 if receipt["status"]=="PASS_WITHIN_OFFLINE_OVERLAY_SCOPE" else 1
if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--out",type=Path,required=True);raise SystemExit(main(parser.parse_args().out))
