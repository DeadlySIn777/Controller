"""Independent HTTP fixtures for inherited transport and appliance scopes."""
from datetime import datetime, timezone
import argparse
import hashlib
import http.client
import json
from pathlib import Path
import re
import tempfile
import threading
import uuid

from controller_config import package_archive
from controller_config.setup_service import SetupService
from controller_shell.server import make_server

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"http-r[0-9]{2}", args.run):
        raise ValueError("Exclusive HTTP report run name required")
    OUTPUT = ROOT / "reports/appliance-os-20261004/service" / args.run
    OUTPUT.mkdir(exist_ok=False)
    names = [p.relative_to(ROOT).as_posix() for package in ("controller_appliance", "controller_shell")
             for p in (ROOT / package).rglob("*") if p.is_file() and p.suffix in (".py", ".html", ".css", ".js")]
    names += ["controller_config/setup_web.py", "controller_config/setup_service.py", "controller_config/package_archive.py"]
    names += ["reports/appliance-os-20261004/service/http_controls.py"]
    sources = {name: sha(ROOT / name) for name in sorted(names)}
    observations = []
    with tempfile.TemporaryDirectory(dir=OUTPUT) as task_temp:
        work = Path(task_temp)
        setup = SetupService(work / "setup.json")
        setup.initialize(actor="explicit-http-fixture")
        preserved = {"setup.json": (work / "setup.json").read_bytes()}
        for name in ("budget.json", "entitlements.json", "calibration.json", "machine-backup.json"):
            (work / name).write_bytes(("protected fixture: " + name).encode())
            preserved[name] = (work / name).read_bytes()
        packages = work / "packages"
        packages.mkdir()
        created = package_archive.create_archive(packages / "http-config.tar.zst", {"configuration.json": b'{"inert":true}'}, "config")
        preserved["packages/http-config.tar.zst"] = Path(created["path"]).read_bytes()
        server = make_server(work, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host = f"127.0.0.1:{server.server_port}"
        token, cookie = None, None
        def request(method, route, payload=None, *, selected_token="correct", origin="correct", cookies=None, duplicate_host=False):
            client = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            body = json.dumps(payload).encode() if payload is not None else None
            client.putrequest(method, route, skip_host=True)
            client.putheader("Host", host)
            if duplicate_host:
                client.putheader("Host", host)
            if selected_token is not None:
                client.putheader("X-Setup-Token", token if selected_token == "correct" else selected_token)
            if cookies:
                client.putheader("Cookie", cookies)
            if method == "POST":
                client.putheader("Origin", "http://" + host if origin == "correct" else origin)
                client.putheader("Content-Type", "application/json")
                client.putheader("Content-Length", str(len(body)))
            client.endheaders(body)
            response = client.getresponse()
            data = response.read()
            result = response.status, dict(response.getheaders()), data
            client.close()
            return result
        def check(name, condition):
            observations.append({"name": name, "passed": bool(condition)})
            if not condition:
                raise AssertionError(name)
        try:
            code, headers, body = request("GET", "/", selected_token=None)
            token = re.search(rb'<meta name="setup-token" content="([A-Za-z0-9_-]+)"', body).group(1).decode()
            cookie = headers["Set-Cookie"].split(";", 1)[0]
            read_only_token = cookie.split("=", 1)[1]
            check("shell supplies separate HttpOnly read-only cookie", code == 200 and "HttpOnly" in headers["Set-Cookie"] and read_only_token != token)
            for route in ("/files", "/settings"):
                code, _, body = request("GET", route, selected_token=None)
                check("appliance HTML view " + route, code == 200 and b"__SETUP_TOKEN__" not in body and b"__APPLIANCE_VIEW__" not in body)
            check("status requires header token", request("GET", "/api/appliance/status", selected_token=None)[0] == 403)
            check("cookie alone cannot read preference status", request("GET", "/api/appliance/status", selected_token=None, cookies=cookie)[0] == 403)
            check("duplicate Host rejects", request("GET", "/api/appliance/status", duplicate_host=True)[0] == 403)
            code, _, body = request("GET", "/api/appliance/status")
            check("read-only status does not create appliance store", code == 200 and not (work / "appliance").exists())
            check("cross-origin write refuses", request("POST", "/api/appliance/reset-preview", {"scope":"appliance_preferences"}, origin="http://foreign.invalid")[0] == 403)
            check("read-only cookie token cannot write", request("POST", "/api/appliance/reset-preview", {"scope":"appliance_preferences"}, selected_token=read_only_token)[0] == 403)
            check("unknown mutation fields refuse", request("POST", "/api/appliance/reset-preview", {"scope":"appliance_preferences","motion":True})[0] == 409)
            check("full machine reset refuses", request("POST", "/api/appliance/reset-preview", {"scope":"full_machine"})[0] == 409)
            code, _, body = request("POST", "/api/appliance/preferences-preview", {"patch":{"display_scale":1.5,"startup_page":"files"},"expected_revision":0})
            preview = json.loads(body)
            check("HTTP reviewed preference preview", code == 200 and preview["result"]["scope"] == "appliance_preferences" and type(preview["commit_payload"]) is str)
            request_id = str(uuid.uuid4())
            commit = {"plan":preview["commit_payload"],"request_id":request_id,"confirmation":preview["result"]["confirmation"]}
            code, _, body = request("POST", "/api/appliance/confirm", commit)
            check("HTTP preference confirm changes interface only", code == 200 and json.loads(body)["result"]["preferences"]["display_scale"] == 1.5)
            before = (work / "appliance/preferences.json").read_bytes()
            code, _, body = request("POST", "/api/appliance/confirm", commit)
            check("HTTP retry persisted UUID idempotent", code == 200 and json.loads(body)["result"]["idempotent"] and before == (work / "appliance/preferences.json").read_bytes())
            commit["request_id"] = str(uuid.uuid4())
            check("stale preview cannot create a second change", request("POST", "/api/appliance/confirm", commit)[0] == 409)
            code, _, body = request("GET", "/api/appliance/files")
            row = json.loads(body)["result"]["files"][0]
            route = f'/api/appliance/download?id={row["package_id"]}&sha256={row["sha256"]}'
            code, headers, data = request("GET", route, selected_token=None, cookies=cookie)
            check("native read-only-cookie package download exact bytes", code == 200 and data == preserved["packages/http-config.tar.zst"] and headers["Content-Type"] == "application/zstd")
            check("wrong header overrides valid download cookie", request("GET", route, selected_token="wrong", cookies=cookie)[0] == 403)
            check("duplicate package identity refuses", request("GET", route + "&id=" + row["package_id"])[0] == 409)
            check("package digest is mandatory", request("GET", "/api/appliance/download?id=" + row["package_id"])[0] == 409)
            check("arbitrary path download refuses", request("GET", "/api/appliance/download?id=../setup.json&sha256=" + row["sha256"])[0] == 409)
            code, _, body = request("POST", "/api/appliance/service-mode", {"enabled":True,"confirmation":"ENTER SERVICE VIEW"})
            value = json.loads(body)["result"]
            check("service mode grants no machine or terminal permission", code == 200 and value["service_mode"] and not value["motion_authorized"] and not value["terminal_available"] and not value["physical_authority"])
            code, _, body = request("POST", "/api/appliance/reset-preview", {"scope":"appliance_preferences"})
            preview = json.loads(body)
            request("POST", "/api/appliance/confirm", {"plan":preview["commit_payload"],"request_id":str(uuid.uuid4()),"confirmation":preview["result"]["confirmation"]})
            code, _, body = request("POST", "/api/appliance/undo-preview", {})
            preview = json.loads(body)
            code, _, body = request("POST", "/api/appliance/confirm", {"plan":preview["commit_payload"],"request_id":str(uuid.uuid4()),"confirmation":preview["result"]["confirmation"]})
            check("HTTP reset reversible through same shared service", code == 200 and json.loads(body)["result"]["preferences"]["display_scale"] == 1.5)
            check("all original fixture machine/private/archive bytes preserved", all((work / name).read_bytes() == data for name, data in preserved.items()))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
    stable = all(sha(ROOT / name) == expected for name, expected in sources.items())
    receipt = {"schema_version":1,"status":"SCOPED_PASS" if stable else "FAIL", "utc":datetime.now(timezone.utc).isoformat(),
               "source_sha256":sources,"source_inputs_unchanged":stable,"checks":observations,"check_count":len(observations),
               "api_calls":0,"hardware_connections":0,"machine_commands":[],"physical_authority":False,
               "scope":"Actual local HTTP+shared appliance service+unchanged archive codec, authored temporary fixtures; no browser layout or physical runtime qualification"}
    (OUTPUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status":receipt["status"],"check_count":len(observations),"receipt":str(OUTPUT / "receipt.json")}))


if __name__ == "__main__":
    main()
