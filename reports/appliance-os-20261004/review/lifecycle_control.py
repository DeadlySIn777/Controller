"""Disconnected Linux process-separation control; never starts a motion runtime.

Uses a staged application and cloned setup exclusively below a new evidence
directory. A counter sentinel is deliberately NOT LinuxCNC, HAL, or an RT task.
No service installation/activation, hardware, external network, or paid calls.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}


def wait_for(callback, timeout=12):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = callback()
        if result:
            return result
        time.sleep(0.025)
    raise AssertionError("Bounded wait expired")


def get(url, token=None):
    headers = {"X-Setup-Token": token} if token else {}
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=3) as response:
        return response.status, response.read().decode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rootfs", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert sys.platform == "linux", "Linux process control only"
    rootfs = args.rootfs.resolve(strict=True)
    app = rootfs / "usr/lib/controller/app"
    out = args.output.absolute()
    out.mkdir(parents=True, exist_ok=False)
    workspace = out / "workspace"
    workspace.mkdir()
    shutil.copyfile(args.fixture, workspace / "setup.json")
    settings_before = files(workspace)
    image_before = files(rootfs)
    env = {**os.environ, "PYTHONPATH": str(app), "PYTHONDONTWRITEBYTECODE": "1"}
    for key in ("OPENAI_API_KEY", "CNC3_ALLOW_DISCONNECTED_RTL_SIMULATION"):
        env.pop(key, None)
    children = []
    logs = []
    checks = []
    observations = {}

    def check(name, condition):
        checks.append({"name": name, "passed": bool(condition)})
        assert condition, name

    def spawn(name, command):
        log = (out / (name + ".log")).open("wb")
        logs.append(log)
        child = subprocess.Popen(command, cwd=app, env=env, stdout=log,
                                 stderr=subprocess.STDOUT, start_new_session=True)
        children.append(child)
        return child

    def inspect(name, root=rootfs, store=workspace, recovery=False):
        command = [sys.executable, "-B", "-m", "controller_os",
                   "recovery" if recovery else "preflight", "--root", str(root),
                   "--workspace", str(store), "--allow-development"]
        result = subprocess.run(command, cwd=app, env=env, text=True, capture_output=True, timeout=20)
        (out / (name + ".stdout.json")).write_text(result.stdout)
        (out / (name + ".stderr.txt")).write_text(result.stderr)
        body = json.loads(result.stdout)
        observations[name] = {"exit_code": result.returncode, "body": body}
        return result.returncode, body

    def start_shell(name):
        code, body = inspect(name + "-preflight")
        check(name + " fresh preflight admitted disconnected shell", code == 0 and body["ok"])
        child = spawn(name, [sys.executable, "-B", "-m", "controller_shell", "--directory", str(workspace), "--port", "0"])
        def address():
            assert child.poll() is None, "shell exited during startup"
            match = re.search(r"http://127\.0\.0\.1:(\d+)", (out / (name + ".log")).read_text())
            return "http://127.0.0.1:" + match[1] if match else None
        url = wait_for(address)
        status, page = get(url + "/")
        token = re.search(r'<meta name="setup-token" content="([A-Za-z0-9_-]+)">', page)[1]
        context = json.loads(get(url + "/api/context", token)[1])
        readiness = json.loads(get(url + "/api/readiness", token)[1])
        appliance = json.loads(get(url + "/api/appliance/status", token)[1])
        check(name + " actual HTTP context and readiness remain inhibited", status == 200 and context["ok"] and
              context["result"]["simulation_only"] is True and readiness["ok"] and
              readiness["result"]["motion_authorized"] is False and
              readiness["result"]["physical_commissioning_complete"] is False and
              readiness["result"]["outputs_inhibited"] is True)
        check(name + " appliance status has no runtime or terminal authority",
              appliance["ok"] and appliance["result"]["physical_authority"] is False and
              appliance["result"]["motion_authorized"] is False and
              appliance["result"]["terminal_available"] is False and
              appliance["result"]["machine_commands"] == [] and
              appliance["result"]["service_mode"] is False)
        return child, url, token

    sentinel_file = out / "sentinel.json"
    sentinel_code = """import json,os,pathlib,time,sys
p=pathlib.Path(sys.argv[1]); counter=0
identity=pathlib.Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19]
while True:
 counter+=1
 body={'pid':os.getpid(),'start_ticks':identity,'counter':counter,'monotonic_ns':time.monotonic_ns()}
 temp=p.with_suffix('.pending');temp.write_text(json.dumps(body));os.replace(temp,p)
 time.sleep(.01)
"""

    def sample():
        try:
            return json.loads(sentinel_file.read_text())
        except FileNotFoundError:
            return None

    def continuity(name, previous):
        def progressed():
            value = sample()
            return value if value and value["counter"] > previous["counter"] + 3 else None
        observed = wait_for(progressed)
        check(name, sentinel.poll() is None and observed["pid"] == previous["pid"] and
              observed["start_ticks"] == previous["start_ticks"] and
              observed["counter"] > previous["counter"] and observed["monotonic_ns"] > previous["monotonic_ns"])
        observations[name] = {"before": previous, "after": observed}
        return observed

    try:
        units = {p.relative_to(rootfs).as_posix(): p.read_text() for p in
                 (rootfs / "etc/systemd").rglob("*") if p.is_file()}
        application_unit = units["etc/systemd/system/controller-shell.service"]
        kiosk_unit = units["etc/systemd/user/controller-kiosk.service"]
        check("staged shell invokes fresh read-only preflight on every launch",
              "ExecStartPre=/usr/bin/python3 -m controller_os preflight " in application_unit)
        check("staged shell and kiosk have bounded nonzero retry budgets",
              all("StartLimitIntervalSec=infinity" in value and "StartLimitBurst=3" in value and
                  "RestartSec=3" in value for value in (application_unit, kiosk_unit)))
        user_units = "\n".join(value for path, value in units.items() if "/user/" in path)
        check("staged user kiosk graph has no application or runtime coupling",
              "controller-shell.service" not in user_units and "controller-runtime" not in user_units and
              all(key not in user_units for key in ("PartOf=", "BindsTo=", "PropagatesStopTo=", "Upholds=")))
        observations["staged_units"] = {"sha256": {name: sha(rootfs / name) for name in units},
                                        "activated": False, "actual_runtime_unit_present": False}
        sentinel = spawn("independent-counter-sentinel", [sys.executable, "-B", "-c", sentinel_code, str(sentinel_file)])
        initial = wait_for(sample)
        shell, url, token = start_shell("shell-first")
        kiosk_code = "import sys,time,urllib.request\nwhile True:\n urllib.request.urlopen(sys.argv[1],timeout=2).read()\n time.sleep(.05)\n"
        kiosk = spawn("get-only-client-first", [sys.executable, "-B", "-c", kiosk_code, url + "/"])
        first = continuity("sentinel progressed during shell and client startup", initial)
        check("client is separate from shell and sentinel sessions", len({os.getsid(p.pid) for p in (sentinel, shell, kiosk)}) == 3)
        kiosk.kill(); kiosk.wait(timeout=5)
        check("GET-only client crash leaves shell serving", shell.poll() is None and get(url + "/")[0] == 200)
        second = continuity("sentinel survived client SIGKILL", first)
        kiosk2 = spawn("get-only-client-second", [sys.executable, "-B", "-c", kiosk_code, url + "/"])
        third = continuity("sentinel survived client restart", second)
        check("client restart retains original shell PID", shell.poll() is None and kiosk2.poll() is None)
        kiosk2.kill(); kiosk2.wait(timeout=5)
        shell.kill(); shell.wait(timeout=5)
        fourth = continuity("sentinel survived shell SIGKILL", third)
        shell2, url2, token2 = start_shell("shell-second")
        fifth = continuity("sentinel survived fresh-preflight shell restart", fourth)
        check("shell restart uses a new PID and new API token", shell2.pid != shell.pid and token2 != token)
        try:
            get(url2 + "/api/context", token)
            old_token_rejected = False
        except urllib.error.HTTPError as error:
            old_token_rejected = error.code == 403
        check("old process API token cannot read restarted API", old_token_rejected)
        check("cloned settings and workspace bytes unchanged after read-only HTTP", files(workspace) == settings_before)
        shell2.terminate(); shell2.wait(timeout=5)
        corrupt_workspace = out / "corrupt-workspace"; corrupt_workspace.mkdir()
        (corrupt_workspace / "setup.json").write_bytes(b'{"corrupt":')
        corrupt_before = files(corrupt_workspace)
        code, body = inspect("corrupt-settings-preflight", store=corrupt_workspace)
        check("corrupt settings refuse a fresh launch check", code != 0 and body["ok"] is False)
        code, body = inspect("corrupt-settings-recovery", store=corrupt_workspace, recovery=True)
        check("recovery reports blocked settings and no authority", code == 0 and body["result"]["checks"]["settings"]["status"] == "BLOCKED" and
              body["result"]["physical_authority"] is False and body["result"]["automatic_restore"] is False)
        check("recovery preserves corrupt bytes and creates no settings artifact", files(corrupt_workspace) == corrupt_before)
        copied_image = out / "tampered-image"
        shutil.copytree(rootfs, copied_image)
        modified = copied_image / "usr/lib/controller/app/controller_shell/server.py"
        modified.write_bytes(modified.read_bytes() + b"\n# deliberate report-only integrity control\n")
        code, body = inspect("changed-image-preflight", root=copied_image)
        check("changed installed source refuses a fresh launch check", code != 0 and body["ok"] is False)
        continuity("sentinel survives all refusal and recovery checks", fifth)
        check("original staged image bytes unchanged", files(rootfs) == image_before)
        check("original cloned workspace remains unchanged", files(workspace) == settings_before)
        status = "SCOPED_PASS"
    except Exception as error:
        observations["error"] = repr(error)
        status = "FAIL"
    finally:
        for child in reversed(children):
            if child.poll() is None:
                child.terminate()
                try: child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait(timeout=5)
        for log in logs:
            log.close()
    receipt = {"schema_version": 1, "status": status, "checks": checks,
               "observations": observations, "source_manifest_sha256": sha(rootfs / "usr/share/controller/image-manifest.json"),
               "harness_sha256": sha(Path(__file__)), "fixture_sha256": sha(args.fixture),
               "limits": ["Ordinary Linux subprocess separation; sentinel is a counter, NOT motion, LinuxCNC, HAL, or an RT task.",
                          "Client is a GET-only Python HTTP process, not a rendered browser/kiosk.",
                          "Systemd units are not installed or enabled; restart policies require separate static/syntax checks.",
                          "Fresh launch preflight is invoked by this harness explicitly; successful shell launch grants no authority.",
                          "No physical measurements, loaded real-time continuity, hardware, vendor fit or complete appliance boot qualification."],
               "physical_authority": False, "runtime_started": False, "hardware_connections": 0,
               "systemd_units_activated": False, "paid_calls": 0}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": status, "checks": len(checks), "error": observations.get("error")}))
    return 0 if status == "SCOPED_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
