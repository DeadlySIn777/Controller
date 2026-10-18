import hashlib
import http.client
import json
from pathlib import Path
import re
import tempfile
import threading
import unittest

from controller_config.setup_service import SetupService
from controller_config.setup_budget import BudgetLedger
from controller_shell.server import make_server


class ShellContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.server = make_server(self.directory, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.host = f"127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        self.temp.cleanup()

    def request(self, method, path, payload=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            data = json.dumps(payload).encode() if payload is not None else None
            connection.request(method, path, body=data, headers={"Host": self.host, **(headers or {})})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def token(self, path="/"):
        status, headers, html = self.request("GET", path)
        self.assertEqual(status, 200)
        return re.search(rb'<meta name="setup-token" content="([A-Za-z0-9_-]+)">', html).group(1).decode(), headers, html

    def test_home_and_status_do_not_initialize_or_spend(self):
        token, headers, html = self.token()
        self.assertIn(b"Motion X12", html)
        self.assertIn("HttpOnly; SameSite=Strict", headers["Set-Cookie"])
        for endpoint in ("context", "readiness"):
            with self.subTest(endpoint=endpoint):
                status, _, body = self.request("GET", "/api/" + endpoint, headers={"X-Setup-Token": token})
                self.assertEqual(status, 200)
                result = json.loads(body)["result"]
                self.assertTrue(result["simulation_only"])
                if endpoint == "readiness":
                    self.assertFalse(result["motion_authorized"])
                    self.assertFalse(result["physical_commissioning_complete"])
                    self.assertEqual(result["api_calls"], 0)
        self.assertFalse((self.directory / "setup.json").exists())
        self.assertFalse((self.directory / "budget.json").exists())

    def test_shell_and_workbench_share_one_security_session(self):
        shell_token, _, _ = self.token()
        for view in ("setup", "readiness", "diagnostics"):
            with self.subTest(view=view):
                token, headers, html = self.token("/workbench?view=" + view)
                self.assertEqual(token, shell_token)
                self.assertIn(b"/workbench-shell.js", html)
                self.assertIn(b"/setup.js", html)
                self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
                self.assertIn("script-src 'self'", headers["Content-Security-Policy"])

    def test_wrong_host_assets_traversal_and_foreign_origin_rejected(self):
        token, _, _ = self.token()
        for route in ("/", "/workbench", "/shell.js", "/api/context"):
            with self.subTest(route=route):
                status, _, _ = self.request("GET", route, headers={"Host": "foreign.invalid"})
                self.assertEqual(status, 403)
        status, _, _ = self.request("GET", "/../controller_config/setup_service.py")
        self.assertEqual(status, 404)
        for origin in (None, "http://foreign.invalid"):
            with self.subTest(origin=origin):
                headers = {"X-Setup-Token": token, "Content-Type": "application/json"}
                if origin: headers["Origin"] = origin
                status, _, _ = self.request("POST", "/api/initialize", {}, headers)
                self.assertEqual(status, 403)
        self.assertFalse((self.directory / "setup.json").exists())

    def test_authorized_operations_use_original_service_and_remain_inhibited(self):
        token, _, _ = self.token()
        status, _, body = self.request("POST", "/api/initialize", {},
            {"X-Setup-Token": token, "Content-Type": "application/json", "Origin": "http://" + self.host})
        self.assertEqual(status, 200)
        result = json.loads(body)["result"]
        original = SetupService(self.directory / "setup.json").status()
        self.assertEqual(result, original)
        self.assertTrue(original["outputs_inhibited"])
        self.assertFalse(original["homed"])
        self.assertFalse(original["motion_authorized"])
        self.assertEqual(original["machine_commands"], [])
        budget = BudgetLedger(self.directory / "budget.json").status()
        self.assertEqual(budget["spent_microdollars"], 0)

    def test_home_preserves_existing_setup_and_private_allowance(self):
        token, _, _ = self.token()
        self.request("POST", "/api/initialize", {},
            {"X-Setup-Token": token, "Content-Type": "application/json", "Origin": "http://" + self.host})
        paths = [self.directory / name for name in ("setup.json", "budget.json")]
        before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
        for route in ("/", "/shell.css", "/shell.js", "/api/context", "/api/readiness"):
            self.assertEqual(self.request("GET", route, headers={"X-Setup-Token": token})[0], 200)
        self.assertEqual(before, {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths})


if __name__ == "__main__":
    unittest.main()
