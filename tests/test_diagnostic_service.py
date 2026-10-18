"""Shared service/CLI/HTTP integration, entirely temporary and disconnected."""
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

from controller_config.diagnostic_service import DiagnosticService
from controller_config.model import ConfigurationError
from controller_config.package_archive import capabilities, create_archive, read_archive
from controller_config.setup_service import SetupService, example_draft
from controller_config.setup_web import make_server


@unittest.skipUnless(capabilities()["available"], "Optional stdlib Zstd backend unavailable")
class DiagnosticIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.service = DiagnosticService(self.folder)

    def setup_generation(self):
        setup = SetupService(self.folder / "setup.json")
        state = setup.initialize()
        setup.save_draft(example_draft("sim-mill-3axis"), state["revision"])
        setup.commit(setup.preview(), "first")
        return setup

    def cli(self, *args):
        result = subprocess.run([sys.executable, "-B", "-m", "controller_config", "setup",
                                 "--directory", str(self.folder), *args],
                                capture_output=True, text=True, timeout=15)
        self.assertNotIn("Traceback", result.stderr)
        return result.returncode, json.loads(result.stdout)

    def test_status_is_read_only_and_no_provider_calls(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("No network")):
            result = self.service.context()
        self.assertFalse(result["live_source_connected"])
        self.assertEqual(result["api_calls"], 0)
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_typed_state_binds_setup_and_keeps_commands_separate(self):
        from controller_config.machine_state import example_machine_observation
        setup = self.setup_generation()
        observation = example_machine_observation(setup.status())
        self.service.append(observation)
        state = self.service.report()["machine_state"]
        self.assertEqual(state["configuration_binding"], observation["data"]["configuration_binding"])
        self.assertEqual(state["domains"]["motion"]["counts"]["commanded"], 1)
        self.assertEqual(state["domains"]["motion"]["counts"]["measured"], 0)
        self.assertEqual(state["machine_commands"], [])
        draft = example_draft("sim-mill-3axis")
        draft["machine_name"] = "New revision"
        setup.save_draft(draft, setup.status()["revision"])
        stale = self.service.report()["machine_state"]
        self.assertEqual(stale["counts"]["accepted_records"], 0)
        self.assertEqual(stale["domains"]["motion"]["status"], "unknown")

    def test_support_package_uses_one_config_snapshot_when_store_changes(self):
        setup = self.setup_generation()
        original = self.service.setup.backup_snapshot
        def snapshot_then_change():
            value = original()
            draft = example_draft("sim-mill-3axis")
            draft["machine_name"] = "Concurrent edit"
            setup.save_draft(draft, setup.status()["revision"])
            return value
        path = self.folder / "support.tar.zst"
        with patch.object(self.service.setup, "backup_snapshot", side_effect=snapshot_then_change):
            self.service.package(path, "support")
        entries = read_archive(path, "support")["entries"]
        snapshot = json.loads(entries["setup/snapshot.json"])
        report = json.loads(entries["diagnostics/report.json"])
        self.assertEqual(report["machine_state"]["configuration_binding"]["revision"], snapshot["revision"])
        self.assertNotEqual(setup.status()["revision"], snapshot["revision"])

    def test_cli_state_example_and_state_share_service_contract(self):
        self.setup_generation()
        file = self.folder / "observation.json"
        code, result = self.cli("diagnostics", "observation-example", "--output", str(file))
        self.assertEqual(code, 0, result)
        self.assertFalse(result["result"]["physical_observation"])
        code, result = self.cli("diagnostics", "append", str(file))
        self.assertEqual(code, 0, result)
        code, result = self.cli("diagnostics", "state")
        self.assertEqual(code, 0, result)
        self.assertEqual(result["result"], self.service.report()["machine_state"])

    def test_example_is_complete_separate_and_idempotent(self):
        legacy = self.folder / "diagnostic-example" / "retained-record.json"
        legacy.parent.mkdir()
        legacy.write_bytes(b"earlier authored example preserved")
        report = self.service.create_example()
        self.assertTrue(report["window"]["pre_complete"])
        self.assertTrue(report["window"]["post_complete"])
        self.assertEqual(report["window"]["gaps"], [])
        self.assertEqual(report["explanations"][-1]["machine_response"]["position_retained"], "unverified")
        self.assertFalse(self.service.report()["initialized"])
        self.assertEqual(report, self.service.create_example())
        self.assertFalse((self.folder / "setup.json").exists())
        self.assertFalse((self.folder / "budget.json").exists())
        self.assertEqual(legacy.read_bytes(), b"earlier authored example preserved")
        self.assertEqual(report["machine_state"]["machine_definition"]["configuration"]["profile_id"], "sim-gantry-4motor")

    def test_example_package_binds_its_gantry_and_excludes_workspace_setup(self):
        self.setup_generation()
        self.service.create_example()
        path = self.folder / "example.tar.zst"
        self.service.package(path, "support", example=True)
        entries = read_archive(path, "support")["entries"]
        snapshot = json.loads(entries["setup/snapshot.json"])
        report = json.loads(entries["diagnostics/report.json"])
        self.assertEqual(snapshot["active"]["draft"]["profile_id"], "sim-gantry-4motor")
        self.assertEqual(snapshot["active"]["draft"]["motors"][2]["axis"].upper(), "Y")
        self.assertEqual(report["fault_record"]["data"]["resource"]["axis"], "Y")
        self.assertEqual(report["explanations"][0]["resource"]["axis"], "Y")
        self.assertEqual(report["machine_state"]["configuration_binding"]["store_id"], snapshot["store_id"])
        self.assertNotEqual(snapshot["store_id"], self.service.setup.status()["store_id"])
        self.assertNotIn(b"Simulation 3-axis", entries["setup/snapshot.json"])

    def test_backup_includes_history_but_excludes_api_ledger(self):
        setup = self.setup_generation()
        draft = example_draft("sim-mill-3axis")
        draft["machine_name"] = "Second configuration"
        setup.save_draft(draft, setup.status()["revision"])
        setup.commit(setup.preview(), "second")
        (self.folder / "budget.json").write_text('private ledger content')
        path = self.folder / "backup.tar.zst"
        self.service.package(path, "config")
        archive = read_archive(path, "config")
        self.assertEqual(set(archive["entries"]), {"setup/snapshot.json"})
        snapshot = json.loads(archive["entries"]["setup/snapshot.json"])
        self.assertEqual(snapshot["generation"], 2)
        self.assertEqual(snapshot["history"][0]["generation"], 1)
        self.assertNotIn("requests", snapshot)
        self.assertNotIn(b"private ledger content", archive["entries"]["setup/snapshot.json"])

    def test_package_restore_requires_preview_commit_and_keeps_guards(self):
        setup = self.setup_generation()
        backup = self.folder / "backup.tar.zst"
        self.service.package(backup, "config")
        draft = example_draft("sim-mill-3axis")
        draft["machine_name"] = "Changed configuration"
        setup.save_draft(draft, setup.status()["revision"])
        setup.commit(setup.preview(), "changed")
        before = setup.path.read_bytes()
        plan = self.service.restore_preview(backup)
        self.assertEqual(setup.path.read_bytes(), before)
        result = setup.commit(plan, "restore-package")
        self.assertEqual(result["generation"], 3)
        self.assertFalse(result["motion_authorized"])
        self.assertTrue(result["outputs_inhibited"])
        self.assertFalse(result["homed"])
        self.assertEqual(result["machine_commands"], [])

    def test_malicious_backup_cannot_extend_simulation_limits(self):
        setup = self.setup_generation()
        snapshot = setup.backup_snapshot()
        snapshot["active"]["draft"]["outputs"] = [{"resource": "SIM.DO0", "role": "load",
            "equipment_profile": "sim-smart-output-v1", "voltage_v": 24, "current_a": .6}]
        path = self.folder / "invalid.tar.zst"
        create_archive(path, {"setup/snapshot.json": json.dumps(snapshot).encode()}, "config")
        before = setup.path.read_bytes()
        with self.assertRaises(ConfigurationError):
            self.service.restore_preview(path)
        self.assertEqual(setup.path.read_bytes(), before)

    def test_existing_export_is_never_overwritten(self):
        self.setup_generation()
        output = self.folder / "customer-config.txt"
        output.write_bytes(b"retain customer source")
        with self.assertRaises(ConfigurationError):
            self.service.package(output, "config")
        self.assertEqual(output.read_bytes(), b"retain customer source")

    def test_uninterpretable_fault_preserves_raw_report(self):
        record = {"schema_version": 1, "simulation_only": True, "timestamp_ns": 0,
                  "source": "test-fixture", "sequence": 0, "kind": "fault", "data": {"unknown_format": 1}}
        self.service.append(record)
        report = self.service.report()
        self.assertEqual(report["records"][0], record)
        self.assertEqual(report["explanations"], [])
        self.assertTrue(report["explanation_errors"][0]["raw_record_retained"])

    def test_cli_job_packages_are_inert_and_reject_unsafe_members(self):
        program = self.folder / "program.ngc"
        program.write_bytes(b"G0 X1\nM2\n")
        original = program.read_bytes()
        package = self.folder / "test.cncjob"
        code, value = self.cli("package", "job", str(package), "--entry", "program/main.ngc=" + str(program))
        self.assertEqual(code, 0, value)
        code, value = self.cli("package", "inspect", str(package))
        self.assertEqual(code, 0, value)
        self.assertFalse(value["result"]["executed"])
        self.assertFalse(value["result"]["extracted"])
        code, value = self.cli("package", "job", str(self.folder / "unsafe.cncjob"), "--entry", "../outside=" + str(program))
        self.assertEqual(code, 2)
        self.assertFalse(value["ok"])
        self.assertEqual(program.read_bytes(), original)

    def test_cli_malformed_record_and_backup_return_structured_errors(self):
        malformed = self.folder / "record.json"
        malformed.write_text('[1,2]')
        code, result = self.cli("diagnostics", "append", str(malformed))
        self.assertEqual(code, 2)
        self.assertFalse(result["ok"])
        bad = self.folder / "bad.tar.zst"
        create_archive(bad, {"setup/snapshot.json": b'{"broken":'}, "config")
        code, result = self.cli("package", "restore-preview", str(bad), "--output", str(self.folder / "plan.json"))
        self.assertEqual(code, 2)
        self.assertFalse(result["ok"])

    def test_http_example_and_real_compressed_download_use_same_service(self):
        server = make_server(self.folder, port=0)
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": .01}, daemon=True)
        thread.start()
        try:
            host = f"127.0.0.1:{server.server_port}"
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            connection.request("GET", "/", headers={"Host": host})
            html = connection.getresponse().read().decode()
            token = re.search(r'name="setup-token" content="([^"]+)"', html).group(1)
            connection.request("POST", "/api/diagnostic_example", body=b'{}', headers={
                "Host": host, "Origin": "http://" + host, "Content-Type": "application/json", "X-Setup-Token": token})
            response = connection.getresponse()
            value = json.loads(response.read())
            self.assertEqual(response.status, 200, value)
            self.assertTrue(value["result"]["window"]["post_complete"])
            connection.request("GET", "/api/example-package", headers={"Host": host, "X-Setup-Token": token})
            response = connection.getresponse()
            data = response.read()
            self.assertEqual(response.status, 200, data[:100])
            self.assertEqual(response.getheader("Content-Type"), "application/zstd")
            path = self.folder / "download.tar.zst"
            path.write_bytes(data)
            archive = read_archive(path, "support")
            self.assertTrue(archive["manifest"]["metadata"]["authored_example"])
            self.assertIn("diagnostics/report.json", archive["entries"])
            connection.request("GET", "/api/example-package", headers={"Host": host})
            response = connection.getresponse()
            response.read()
            self.assertEqual(response.status, 403)
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
