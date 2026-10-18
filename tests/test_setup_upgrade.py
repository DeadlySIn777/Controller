"""Actual disconnected setup workflows, corruption and stale-input regressions."""
import hashlib
import http.client
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from controller_config.diagnostic_service import DiagnosticService, MAX_BACKUP_UPLOAD
from controller_config.model import ConfigurationError
from controller_config.package_archive import ArchiveError, capabilities
from controller_config.setup_readiness import ReadinessService
from controller_config.setup_service import SetupService, example_draft, draft_template
from controller_config.setup_web import make_server


def inventory(folder):
    return {str(path.relative_to(folder)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in folder.rglob("*") if path.is_file()}


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.setup = SetupService(self.folder / "setup.json")
        self.readiness = ReadinessService(self.folder)

    def commit(self, profile="sim-machine-12motor"):
        self.setup.initialize()
        self.setup.save_draft(example_draft(profile), 0)
        self.setup.commit(self.setup.preview(), "first")

    def test_readiness_is_read_only_without_fake_hardware_passes(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("No network")):
            report = self.readiness.status()
        self.assertEqual(inventory(self.folder), {})
        self.assertFalse(report["simulation_configuration_ready"])
        self.assertEqual(report["next_step"]["id"], "store")
        self.assertEqual(report["checks"][-1]["status"], "unavailable")
        self.assertFalse(report["physical_commissioning_complete"])
        self.assertEqual(report["machine_commands"], [])

    def test_twelve_motor_progress_uses_actual_missing_facts_and_review(self):
        self.setup.initialize()
        self.setup.save_draft(draft_template("sim-machine-12motor"), 0)
        report = self.readiness.status()
        self.assertEqual(report["next_step"]["id"], "facts")
        self.assertEqual(report["checks"][1]["evidence"]["missing_count"], 72)
        self.setup.save_draft(example_draft("sim-machine-12motor"), 1)
        report = self.readiness.status()
        self.assertEqual(report["next_step"]["id"], "review")
        self.setup.commit(self.setup.preview(), "complete")
        report = self.readiness.status()
        self.assertTrue(report["simulation_configuration_ready"])
        self.assertIsNone(report["next_step"])
        self.assertEqual(report["configuration_binding"]["configuration_sha256"], self.setup.status()["active"]["configuration_sha256"])

    def test_bound_save_rejects_replaced_store_at_same_revision(self):
        state = self.setup.initialize()
        before_binding = state["draft_binding"]
        other = SetupService(self.folder / "replacement.json")
        replacement = other.initialize()
        self.assertEqual(replacement["revision"], state["revision"])
        self.setup.path.write_bytes(other.path.read_bytes())
        before = inventory(self.folder)
        with self.assertRaises(ConfigurationError) as caught:
            self.setup.save_draft(example_draft("sim-machine-12motor"), 0, expected_binding=before_binding)
        self.assertEqual(caught.exception.code, "SETUP_STALE")
        self.assertEqual(inventory(self.folder), before)
        result = self.setup.save_draft(example_draft("sim-machine-12motor"), 0, expected_binding=replacement["draft_binding"])
        self.assertEqual(result["draft_binding"]["store_id"], replacement["store_id"])

    def test_bound_save_rejects_same_revision_draft_substitution(self):
        from controller_config.service import _seal, read_json
        self.setup.initialize()
        self.setup.save_draft(draft_template("sim-mill-3axis"), 0)
        before_binding = self.setup.status()["draft_binding"]
        state = read_json(self.setup.path)
        state.pop("integrity_sha256")
        state["draft"]["machine_name"] = "Externally replaced valid draft"
        self.setup.path.write_bytes(json.dumps(_seal(state)).encode())
        before = inventory(self.folder)
        with self.assertRaises(ConfigurationError) as caught:
            self.setup.save_draft(example_draft("sim-mill-3axis"), 1, expected_binding=before_binding)
        self.assertEqual(caught.exception.code, "SETUP_STALE")
        self.assertEqual(inventory(self.folder), before)

    def test_unreviewed_edits_and_limit_failure_invalidate_readiness(self):
        self.commit()
        draft = self.setup.status()["draft"]
        draft["motors"][7]["dir_setup_ns"] = 1
        self.setup.save_draft(draft, self.setup.status()["revision"])
        report = self.readiness.status()
        self.assertFalse(report["simulation_configuration_ready"])
        self.assertEqual(report["next_step"]["id"], "limits")
        self.assertEqual(report["checks"][2]["status"], "blocked")
        with self.assertRaises(ConfigurationError) as caught:
            self.readiness.rehearse(self.setup.status()["revision"])
        self.assertEqual(caught.exception.code, "READINESS_REVIEW")

    def test_corrupt_settings_preserved_and_readiness_blocks(self):
        self.commit()
        self.setup.path.write_bytes(b'{"broken":')
        before = inventory(self.folder)
        report = self.readiness.status()
        self.assertFalse(report["simulation_configuration_ready"])
        self.assertEqual(report["next_step"]["status"], "blocked")
        self.assertEqual(inventory(self.folder), before)

    @unittest.skipUnless(capabilities()["available"], "Optional Zstd unavailable")
    def test_self_check_runs_all_twelve_motor_negative_cases_and_real_backup(self):
        self.commit()
        (self.folder / "budget.json").write_bytes(b"broken optional ledger remains untouched")
        before = inventory(self.folder)
        with patch("urllib.request.urlopen", side_effect=AssertionError("No network")):
            result = self.readiness.rehearse(self.setup.status()["revision"])
        self.assertTrue(result["passed"])
        self.assertEqual(result["motor_count"], 12)
        self.assertEqual(len(result["checks"]), 15)
        self.assertEqual(result["checks"][-1]["id"], "backup_roundtrip")
        self.assertFalse(result["motion_loop_tested"])
        self.assertFalse(result["motion_authorized"])
        self.assertEqual(result["api_calls"], 0)
        self.assertEqual(inventory(self.folder), before)

    def test_self_check_rejects_stale_revision_and_unavailable_codec_is_explicit(self):
        self.commit()
        with self.assertRaises(ConfigurationError) as caught:
            self.readiness.rehearse(0)
        self.assertEqual(caught.exception.code, "SETUP_STALE")
        with patch("controller_config.package_archive.create_archive", side_effect=ArchiveError("ARCHIVE_UNAVAILABLE", "Test codec missing")):
            result = self.readiness.rehearse(self.setup.status()["revision"])
        self.assertFalse(result["passed"])
        self.assertEqual(result["checks"][-1]["status"], "unavailable")

    @unittest.skipUnless(capabilities()["available"], "Optional Zstd unavailable")
    def test_revision_change_during_roundtrip_cannot_publish_current_receipt(self):
        from controller_config.package_archive import create_archive
        self.commit()
        def archive_then_edit(*args, **kwargs):
            value = create_archive(*args, **kwargs)
            draft = self.setup.status()["draft"]
            draft["machine_name"] = "Concurrent edit"
            self.setup.save_draft(draft, self.setup.status()["revision"])
            return value
        with patch("controller_config.package_archive.create_archive", side_effect=archive_then_edit):
            with self.assertRaises(ConfigurationError) as caught:
                self.readiness.rehearse(2)
        self.assertEqual(caught.exception.code, "SETUP_STALE")

    def test_cli_readiness_matches_service_and_never_initializes(self):
        result = subprocess.run([sys.executable, "-B", "-m", "controller_config", "setup", "--directory", str(self.folder), "readiness"], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["result"], self.readiness.status())
        self.assertEqual(inventory(self.folder), {})


class UpgradeHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.server = make_server(self.folder, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": .01}, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)
        self.host = f"127.0.0.1:{self.server.server_port}"
        html = self.request("/")[1].decode()
        self.token = re.search(r'name="setup-token" content="([^"]+)"', html).group(1)
        self.download_cookie = self.last_headers["Set-Cookie"].split(";", 1)[0]

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, path, raw=None, *, headers=None, extra=()):
        method = "POST" if raw is not None else "GET"
        fields = {"Host": self.host}
        if hasattr(self, "token"):
            fields["X-Setup-Token"] = self.token
        if raw is not None:
            fields.update({"Origin": "http://" + self.host, "Content-Type": "application/json", "Content-Length": str(len(raw))})
        fields.update(headers or {})
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            connection.putrequest(method, path, skip_host=True)
            for key, value in list(fields.items()) + list(extra):
                if value is not None:
                    connection.putheader(key, value)
            connection.endheaders(raw or b"")
            response = connection.getresponse()
            self.last_headers = dict(response.getheaders())
            return response.status, response.read()
        finally:
            connection.close()

    def api(self, path, payload):
        status, body = self.request("/api/" + path, json.dumps(payload).encode())
        value = json.loads(body)
        self.assertEqual(status, 200, value)
        return value

    def test_http_intake_requires_binding_and_returns_only_a_local_review_candidate(self):
        self.api("initialize", {})
        self.api("save", {"draft": draft_template("sim-mill-3axis"), "expected_revision": 0})
        before = inventory(self.folder)
        result = self.api("local_intake", {"facts": "Motor m0 has 200 full steps per revolution", "expected_revision": 1})["result"]
        self.assertEqual(result["proposed_draft"]["motors"][0]["motor_steps_per_revolution"], 200)
        self.assertEqual(result["paid_calls"], 0)
        self.assertEqual(inventory(self.folder), before)
        self.assertEqual(self.request("/api/local_intake", json.dumps({"facts": "Motor m0 has 200 full steps per revolution", "expected_revision": 0}).encode())[0], 409)

    def test_http_bound_save_rejects_foreign_identity_without_changing_it(self):
        state = self.api("initialize", {})["result"]
        wrong = {**state["draft_binding"], "store_id": "00000000-0000-0000-0000-000000000000"}
        before = inventory(self.folder)
        status, body = self.request("/api/save", json.dumps({"draft": example_draft("sim-mill-3axis"), "expected_revision": 0, "expected_binding": wrong}).encode())
        self.assertEqual(status, 409, body)
        self.assertEqual(json.loads(body)["error"]["code"], "SETUP_STALE")
        self.assertEqual(inventory(self.folder), before)

    def test_authenticated_readiness_does_not_write_settings(self):
        self.assertEqual(self.request("/api/readiness", headers={"X-Setup-Token": None})[0], 403)
        status, body = self.request("/api/readiness")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["result"]["checks"][-1]["status"], "unavailable")
        self.assertEqual(inventory(self.folder), {})

    @unittest.skipUnless(capabilities()["available"], "Optional Zstd unavailable")
    def test_download_cookie_is_port_scoped_read_only_and_never_masks_bad_header(self):
        self.api("initialize", {})
        self.api("save", {"draft": example_draft("sim-mill-3axis"), "expected_revision": 0})
        cookie = self.download_cookie
        download_token = cookie.split("=", 1)[1]
        self.assertNotEqual(download_token, self.token)
        fields = {"X-Setup-Token": None, "Cookie": cookie}
        self.assertEqual(self.request("/api/config-package", headers=fields)[0], 200)
        self.assertEqual(self.request("/api/setup-download", headers=fields)[0], 200)
        self.assertEqual(self.request("/api/context", headers=fields)[0], 403)
        self.assertEqual(self.request("/api/readiness", headers=fields)[0], 403)
        before = inventory(self.folder)
        self.assertEqual(self.request("/api/initialize", b"{}", headers=fields)[0], 403)
        self.assertEqual(self.request("/api/initialize", b"{}", headers={"X-Setup-Token": download_token})[0], 403)
        self.assertEqual(self.request("/api/config-package", headers={**fields, "X-Setup-Token": "wrong"})[0], 403)
        self.assertEqual(self.request("/api/config-package", headers={**fields, "Cookie": cookie + "; " + cookie})[0], 403)
        self.assertEqual(self.request("/api/config-package", headers={**fields, "Cookie": f"setup-download-{self.server.server_port + 1}={self.token}"})[0], 403)
        self.assertEqual(inventory(self.folder), before)

    @unittest.skipUnless(capabilities()["available"], "Optional Zstd unavailable")
    def test_binary_backup_review_exact_payload_commit_and_guards(self):
        self.api("initialize", {})
        self.api("save", {"draft": example_draft("sim-machine-12motor"), "expected_revision": 0})
        envelope = self.api("preview", {})
        self.api("commit", {"plan": envelope["commit_payload"], "request_id": "saved"})
        data = DiagnosticService(self.folder).package_bytes("config")
        draft = example_draft("sim-mill-3axis")
        self.api("save", {"draft": draft, "expected_revision": 2})
        before = inventory(self.folder)
        status, body = self.request("/api/backup-preview", data, headers={"Content-Type": "application/zstd"})
        value = json.loads(body)
        self.assertEqual(status, 200, value)
        self.assertEqual(inventory(self.folder), before)
        self.assertIn('640.0', value["commit_payload"])
        result = self.api("commit", {"plan": value["commit_payload"], "request_id": "import"})["result"]
        self.assertTrue(result["outputs_inhibited"])
        self.assertFalse(result["motion_authorized"])
        self.assertFalse(result["homed"])
        self.assertEqual(result["machine_commands"], [])
        self.assertEqual(len(self.server.application.service.status()["draft"]["motors"]), 12)

    def test_binary_import_corruption_bad_framing_and_origin_are_rejected(self):
        cases = [{"Content-Type": "application/json"}, {"Content-Type": "application/zstd", "Content-Length": str(MAX_BACKUP_UPLOAD + 1)}, {"Content-Type": "application/zstd", "Transfer-Encoding": "chunked"}, {"Content-Type": "application/zstd", "Origin": "https://evil.example"}]
        for headers in cases:
            with self.subTest(headers=headers):
                self.assertIn(self.request("/api/backup-preview", b"junk", headers=headers)[0], (403, 409))
        for extra in (("Content-Length", "4"), ("Content-Type", "application/zstd")):
            self.assertEqual(self.request("/api/backup-preview", b"junk", headers={"Content-Type": "application/zstd"}, extra=[extra])[0], 409)
        self.assertEqual(self.request("/api/backup-preview", b"junk", headers={"Content-Type": "application/zstd"})[0], 409)
        self.assertEqual(inventory(self.folder), {})
