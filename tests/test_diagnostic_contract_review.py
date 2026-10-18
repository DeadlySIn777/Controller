"""Independent adapter review: temporary records/packages; no device or API use."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from controller_config import package_archive
from controller_config.diagnostic_explanations import example_fault
from controller_config.diagnostic_recorder import DiagnosticRecorder
from controller_config.diagnostic_service import DiagnosticService
from controller_config.model import ConfigurationError
from controller_config.setup_service import SetupService, example_draft
from controller_config.setup_web import SetupApplication


def envelope(sequence=0, data=None, kind="fault"):
    return {"schema_version": 1, "simulation_only": True, "timestamp_ns": sequence * 1_000_000_000,
            "source": "review-fixture", "sequence": sequence, "kind": kind,
            "data": example_fault() if data is None else data}


class DiagnosticContractReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.service = DiagnosticService(self.directory)

    def files(self):
        return {str(path.relative_to(self.directory)): path.read_bytes()
                for path in self.directory.rglob("*") if path.is_file()}

    def require_codec(self):
        if not package_archive.capabilities()["available"]:
            self.skipTest("Optional Zstandard runtime unavailable")

    def test_absent_readonly_context_report_and_missing_codec_never_initialize(self):
        with patch.object(package_archive, "_zstd", None):
            context = self.service.context()
            report = self.service.report()
            self.assertFalse(context["capabilities"]["available"])
            self.assertFalse(report["initialized"])
            self.assertEqual(self.files(), {})
            with self.assertRaises(ConfigurationError) as caught:
                self.service.append(envelope())
            self.assertEqual(caught.exception.code, "ARCHIVE_UNAVAILABLE")
            self.assertEqual(self.files(), {})

    def test_missing_codec_after_recording_is_unavailable_not_corrupt(self):
        self.require_codec()
        self.service.append(envelope())
        before = self.files()
        with patch.object(package_archive, "_zstd", None):
            context = self.service.context()
            self.assertEqual(context["error"]["code"], "ARCHIVE_UNAVAILABLE")
            with self.assertRaises(ConfigurationError) as caught:
                self.service.report()
            self.assertEqual(caught.exception.code, "ARCHIVE_UNAVAILABLE")
        self.assertEqual(self.files(), before)

    def test_hostile_but_valid_fault_data_is_preserved_without_breaking_report(self):
        self.require_codec()
        variants = [{"unknown_format": "<script>ignored();</script>"}]
        for path, value in (("code", {}), ("source", []), ("resource", []), ("observations", {}),
                            ("machine_response", ["home now"])):
            record = example_fault()
            record[path] = value
            variants.append(record)
        record = example_fault(); record["resource"]["kind"] = []
        variants.append(record)
        record = example_fault(); record["observations"][0]["source"] = {}
        variants.append(record)
        record = example_fault(); record["observations"][0]["valid"] = 1
        variants.append(record)
        for sequence, data in enumerate(variants):
            with self.subTest(sequence=sequence):
                submitted = envelope(sequence, data)
                self.service.append(submitted)
                before = self.files()
                report = self.service.report()
                self.assertEqual(report["fault_record"], submitted)
                self.assertTrue(report["explanation_errors"][-1]["raw_record_retained"])
                self.assertEqual(report["explanations"], [])
                self.assertEqual(report["machine_commands"], [])
                self.assertFalse(report["executed"])
                self.assertEqual(self.files(), before)

    def test_nonfinite_and_oversize_general_records_reject_without_initializing(self):
        for data in ({"value": float("nan")}, {"value": float("inf")},
                     {"value": 2**63}, {"text": "a" * 20_000}):
            with self.subTest(data_type=type(next(iter(data.values()))).__name__):
                with self.assertRaises(ConfigurationError):
                    self.service.append(envelope(data=data, kind="sample"))
                self.assertEqual(self.files(), {})

    def test_read_export_and_restore_preview_preserve_config_and_allowance(self):
        self.require_codec()
        setup = SetupService(self.directory / "setup.json")
        setup.initialize()
        setup.save_draft(example_draft("sim-machine-12motor"), 0)
        setup.commit(setup.preview(), "review-base")
        budget = self.directory / "budget.json"
        budget.write_bytes(b"private existing allowance bytes; intentionally invalid for disclosure test")
        setup_before, budget_before = setup.path.read_bytes(), budget.read_bytes()
        self.service.append(envelope())
        context = SetupApplication(self.directory).context()
        self.assertIsNotNone(context["budget_error"])
        self.assertFalse(context["paid_ai_enabled"])
        self.assertTrue(context["setup"]["initialized"])
        archive = self.directory / "backup.tar.zst"
        self.service.package(archive, "config")
        imported = package_archive.read_archive(archive, expected_kind="config")
        self.assertFalse(any("budget" in name for name in imported["entries"]))
        self.assertNotIn(budget_before, b"".join(imported["entries"].values()))
        plan = self.service.restore_preview(archive)
        self.assertEqual(plan["store_id"], setup.status()["store_id"])
        self.assertFalse(plan["motion_authorized"])
        self.assertEqual(plan["machine_commands"], [])
        self.assertEqual(setup.path.read_bytes(), setup_before)
        self.assertEqual(budget.read_bytes(), budget_before)

    def test_interrupted_authored_example_retries_to_full_reviewable_window(self):
        self.require_codec()
        original_append, count = DiagnosticRecorder.append, 0
        def interrupted(recorder, record):
            nonlocal count
            count += 1
            if count == 3:
                raise OSError("injected process interruption between atomic records")
            return original_append(recorder, record)
        with patch.object(DiagnosticRecorder, "append", interrupted):
            with self.assertRaises((ConfigurationError, OSError)):
                self.service.create_example()
        report = self.service.create_example()
        self.assertEqual(report["record_count"], 331)
        expected = example_fault()
        definition = report["machine_state"]["machine_definition"]["configuration"]
        expected["resource"]["axis"] = definition["motors"][2]["axis"].upper()
        expected["source"]["reference"] = "authored-gantry-diagnostic-example-v2"
        self.assertEqual(report["fault_record"]["data"], expected)
        self.assertTrue(report["window"]["pre_complete"])
        self.assertTrue(report["window"]["post_complete"])
        before = self.files()
        self.service.create_example()
        self.assertEqual(self.files(), before)

    def test_example_does_not_replace_different_retained_records(self):
        self.require_codec()
        recorder = DiagnosticRecorder(self.directory / "diagnostic-example-v2")
        recorder.append(envelope(data={"customer_fact": "retain this"}, kind="sample"))
        before = self.files()
        with self.assertRaises(ConfigurationError) as caught:
            self.service.create_example()
        self.assertEqual(caught.exception.code, "EXAMPLE_CONFLICT")
        self.assertEqual(self.files(), before)


if __name__ == "__main__":
    unittest.main()
