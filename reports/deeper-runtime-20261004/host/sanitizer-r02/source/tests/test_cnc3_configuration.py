"""Adversarial shared-setup to actual CNC3 runtime contract checks."""
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch
import uuid

from controller_config.model import ConfigurationError
from controller_config.service import digest
from controller_config.setup_service import SetupService, example_draft, validate_draft
from controller_lab.cnc3_configuration import (prepare_configuration, verify_configuration,
                                             configuration_binding, FITTED_MASK)


class CNC3ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "runtime.cpp"
        self.source.write_text("// explicit disconnected runtime source\n")
        self.service = SetupService(self.root / "setup.json")
        self.run_id = str(uuid.uuid4())

    def commit(self, draft=None, profile="sim-machine-12motor"):
        self.service.initialize()
        self.service.save_draft(draft or example_draft(profile), self.service.status()["revision"])
        self.service.commit(self.service.preview(), str(uuid.uuid4()))
        return configuration_binding(self.service.backup_snapshot())

    def prepare(self, binding=None):
        encoders = self.service.backup_snapshot()["draft"]["encoders"]
        mapping = [{"encoder_channel": int(item["resource"].removeprefix("SIM.ABZ")),
                    "motor_channel": int(item["resource"].removeprefix("SIM.ABZ")), "edges_per_step": 1} for item in encoders]
        return prepare_configuration(self.service, binding or configuration_binding(self.service.backup_snapshot()),
            run_id=self.run_id, source_root=self.root, source_files=["runtime.cpp"], encoder_mapping=mapping)

    def code(self, code, callback):
        with self.assertRaises(ConfigurationError) as caught:
            callback()
        self.assertEqual(caught.exception.code, code)

    @staticmethod
    def full_io(draft):
        draft["inputs"] = [{"resource": f"SIM.DI{i}", "role": f"input{i}", "equipment_profile": "sim-24v-switch-v1", "voltage_v": 24} for i in range(24)]
        draft["outputs"] = [{"resource": f"SIM.DO{i}", "role": f"output{i}", "equipment_profile": "sim-smart-output-v1", "voltage_v": 24, "current_a": .25} for i in range(16)]
        draft["encoders"] = [{"resource": f"SIM.ABZ{i}", "role": f"feedback{i}", "equipment_profile": "sim-abz-5v-v1", "counts_per_revolution": 3200} for i in range(4)]
        return draft

    def test_full_reviewed_manifest_is_read_only_exact_and_numeric(self):
        draft = self.full_io(example_draft("sim-machine-12motor"))
        # A valid user assignment is numeric, never lexical or list-index based.
        draft["motors"][9]["resource"], draft["motors"][10]["resource"] = "SIM.M10", "SIM.M9"
        draft["motors"][9]["travel_per_load_revolution"] = 10
        self.commit(draft)
        before = self.service.path.read_bytes()
        manifest = self.prepare()
        self.assertEqual(before, self.service.path.read_bytes())
        host = manifest["cnc3_host"]
        self.assertEqual(host["active_mask"], FITTED_MASK)
        self.assertEqual(host["scale"][10], 320)
        self.assertEqual(host["scale"][9], 640)
        self.assertEqual([motor["channel"] for motor in manifest["motors"]], list(range(12)))
        self.assertEqual(host["timing_ticks"], [[250] * 4] * 12)
        self.assertEqual(host["required_encoder_mask"], 15)
        self.assertEqual(host["dout_enable_mask"], 65535)
        self.assertEqual([len(manifest["configured_io"][name]) for name in ("inputs", "outputs", "encoders")], [24, 16, 4])
        self.assertTrue(all(group["selected_current_a"] == 1 for group in manifest["output_groups"]))
        self.assertEqual(manifest, verify_configuration(manifest, self.service, source_root=self.root, expected_source_files=["runtime.cpp"]))
        self.assertFalse(manifest["physical_backend_allowed"])
        self.assertFalse(manifest["motion_authorized"])
        self.assertTrue(manifest["outputs_inhibited"])
        self.assertFalse(manifest["physical_commissioning_complete"])
        self.assertEqual(manifest["physical_measurements"], 0)
        self.assertEqual(manifest["api_calls"], 0)

    def test_eight_active_still_has_twelve_fitted_and_no_invented_encoders(self):
        self.commit(profile="sim-machine-8motor")
        manifest = self.prepare()
        host = manifest["cnc3_host"]
        self.assertEqual((host["active_mask"], host["fitted_mask"]), (255, 4095))
        self.assertEqual(host["scale"][8:], [0] * 4)
        self.assertEqual(host["max_velocity"][8:], [0] * 4)
        self.assertEqual(host["required_encoder_mask"], 0)
        self.assertEqual(manifest["configured_io"]["encoders"], [])

    def test_mm_and_inch_preserve_selected_mechanics(self):
        draft = example_draft("sim-mill-3axis")
        draft["motors"][1].update(unit="in", travel_per_load_revolution=1, max_velocity_units_per_second=.25)
        self.commit(draft)
        host = self.prepare()["cnc3_host"]
        self.assertEqual(host["scale"][0], 640)
        self.assertAlmostEqual(host["scale"][1], 3200 / 25.4)
        self.assertEqual(host["max_velocity"][1], 6.35)
        self.assertEqual(host["active_mask"], 7)

    def test_timing_rounds_up_and_refuses_endpoint_overflow(self):
        draft = example_draft("sim-machine-12motor")
        draft["motors"][0]["step_high_ns"] = 5001
        self.commit(draft)
        self.assertEqual(self.prepare()["cnc3_host"]["timing_ticks"][0][0], 251)
        draft["motors"][0]["step_high_ns"] = 20461
        self.assertTrue(validate_draft(draft, require_complete=True)["valid"])
        self.commit(draft)
        self.code("SIM2_TIMING", self.prepare)

    def test_dds_guard_rejects_nominal_frontend_ceiling_without_clamping(self):
        draft = example_draft("sim-machine-12motor")
        draft["motors"][0]["max_velocity_units_per_second"] = 156.25
        self.assertEqual(validate_draft(draft, True)["calculations"][0]["required_step_rate_hz"], 100000)
        self.commit(draft)
        self.code("SIM2_RATE", self.prepare)
        draft["motors"][0]["max_velocity_units_per_second"] = 99700 / 640
        self.commit(draft)
        motor = self.prepare()["motors"][0]
        self.assertLessEqual(motor["maximum_rate_word"] * motor["timing_guard_period_ticks"], 1 << 32)

    def test_unsupported_polarity_is_explicit_not_silently_reinterpreted(self):
        for field, value in (("step_active_high", False), ("dir_inverted", True)):
            with self.subTest(field=field):
                draft = example_draft("sim-machine-12motor")
                draft["motors"][0][field] = value
                self.commit(draft)
                self.code("SIM2_POLARITY", self.prepare)

    def test_each_stale_binding_component_is_rejected(self):
        binding = self.commit()
        for key in binding:
            changed = deepcopy(binding)
            changed[key] = changed[key] + 1 if type(changed[key]) is int else "0" + changed[key][1:]
            if changed[key] == binding[key]:
                changed[key] = "f" + binding[key][1:]
            with self.subTest(key=key):
                self.code("SIM2_STALE", lambda: self.prepare(changed))
        bad = deepcopy(binding)
        bad["revision"] = True
        self.code("SIM2_BINDING", lambda: self.prepare(bad))

    def test_unreviewed_draft_cannot_feed_runtime(self):
        self.commit()
        draft = self.service.status()["draft"]
        draft["machine_name"] = "Unreviewed change"
        self.service.save_draft(draft, self.service.status()["revision"])
        self.code("SIM2_REVIEW", self.prepare)

    def test_recomputed_derived_values_and_guards_are_checked_independently(self):
        self.commit()
        original = self.service.backup_snapshot()
        tampered = deepcopy(original)
        tampered["active"]["calculations"][0]["steps_per_mm"] += 1
        with patch.object(self.service, "backup_snapshot", return_value=tampered):
            self.code("SIM2_DERIVED", self.prepare)
        for key, value in (("motion_authorized", True), ("physical_commissioning_complete", True), ("homed", True), ("outputs_inhibited", False)):
            tampered = deepcopy(original)
            tampered[key] = value
            with self.subTest(key=key), patch.object(self.service, "backup_snapshot", return_value=tampered):
                self.code("SIM2_AUTHORITY", self.prepare)

    def test_changed_sources_or_resealed_manifest_cannot_bypass_recomputation(self):
        self.commit()
        manifest = self.prepare()
        self.source.write_text("// changed implementation\n")
        self.code("SIM2_MANIFEST", lambda: verify_configuration(manifest, self.service, source_root=self.root, expected_source_files=["runtime.cpp"]))
        manifest = self.prepare()
        manifest["cnc3_host"]["max_velocity"][0] *= 2
        manifest["manifest_sha256"] = digest({key: value for key, value in manifest.items() if key != "manifest_sha256"})
        self.code("SIM2_MANIFEST", lambda: verify_configuration(manifest, self.service, source_root=self.root, expected_source_files=["runtime.cpp"]))

    def test_stale_manifest_refused_after_atomic_snapshot(self):
        self.commit()
        binding = configuration_binding(self.service.backup_snapshot())
        original = self.service.backup_snapshot

        def interleave():
            snapshot = original()
            draft = deepcopy(snapshot["draft"])
            draft["machine_name"] = "Intervening writer"
            self.service.save_draft(draft, snapshot["revision"])
            return snapshot

        with patch.object(self.service, "backup_snapshot", side_effect=interleave):
            manifest = prepare_configuration(self.service, binding, run_id=self.run_id,
                source_root=self.root, source_files=["runtime.cpp"], encoder_mapping=[])
        self.code("SIM2_STALE", lambda: verify_configuration(manifest, self.service, source_root=self.root, expected_source_files=["runtime.cpp"]))

    def test_source_scope_and_run_context_strictly_explicit(self):
        binding = self.commit()
        for paths in ([], ["runtime.cpp", "runtime.cpp"], ["../runtime.cpp"], [str(self.source)], ["missing.cpp"], ["./runtime.cpp"]):
            with self.subTest(paths=paths):
                self.code("SIM2_SOURCE", lambda: prepare_configuration(self.service, binding, run_id=self.run_id,
                    source_root=self.root, source_files=paths))
        for run_id in (None, "", "session1", str(uuid.uuid4()).upper(), True):
            with self.subTest(run_id=run_id):
                self.code("SIM2_CONTEXT", lambda: prepare_configuration(self.service, binding, run_id=run_id,
                    source_root=self.root, source_files=["runtime.cpp"]))
        first = self.prepare()
        self.run_id = str(uuid.uuid4())
        second = self.prepare()
        self.assertNotEqual(first["simulation_context"]["context_sha256"], second["simulation_context"]["context_sha256"])
        self.assertEqual(first["simulation_context"]["config_digest"], second["simulation_context"]["config_digest"])

    def test_encoder_mapping_is_explicit_and_matching_not_inferred(self):
        self.commit(self.full_io(example_draft("sim-machine-12motor")))
        binding = configuration_binding(self.service.backup_snapshot())
        self.code("SIM2_ENCODER_MAPPING", lambda: prepare_configuration(self.service, binding,
            run_id=self.run_id, source_root=self.root, source_files=["runtime.cpp"]))
        draft = self.service.status()["draft"]
        draft["encoders"][0]["counts_per_revolution"] = 4000
        self.commit(draft)
        self.code("SIM2_ENCODER_MAPPING", self.prepare)

    def test_cli_verification_requires_complete_source_closure_and_never_overwrites(self):
        from tools import prepare_cnc3_sim2 as cli
        binding = self.commit()
        binding_file = self.root / "binding.json"
        binding_file.write_text(json.dumps(binding))
        target = self.root / "reports/runtime.json"
        store_bytes = self.service.path.read_bytes()
        args = ["prepare_cnc3_sim2", "--store", str(self.service.path), "--binding", str(binding_file),
                "--run-id", self.run_id, "--source", "runtime.cpp", "--output", str(target)]
        with patch.object(cli, "ROOT", self.root), patch.object(cli, "runtime_sources", return_value=["runtime.cpp"]):
            with patch.object(sys, "argv", args), patch("sys.stdout", new_callable=io.StringIO) as stream:
                self.assertEqual(cli.main(), 0)
                self.assertEqual(json.loads(stream.getvalue())["status"], "PASS")
            original_manifest = target.read_bytes()
            with patch.object(sys, "argv", args), patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(cli.main(), 1)
            self.assertEqual(original_manifest, target.read_bytes())
            verify_args = ["prepare_cnc3_sim2", "--store", str(self.service.path), "--verify", str(target)]
            with patch.object(sys, "argv", verify_args), patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(cli.main(), 0)
            with patch.object(cli, "runtime_sources", return_value=["runtime.cpp", "new_dependency.hpp"]):
                with patch.object(sys, "argv", verify_args), patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(cli.main(), 1)
                    self.assertEqual(json.loads(stream.getvalue())["code"], "SIM2_SOURCE_CLOSURE")
        self.assertEqual(store_bytes, self.service.path.read_bytes())

    def test_recreated_manifest_cannot_omit_a_trusted_dependency(self):
        binding = self.commit()
        dependency = self.root / "dependency.hpp"
        dependency.write_text("// critical dependency\n")
        omitted = prepare_configuration(self.service, binding, run_id=self.run_id,
            source_root=self.root, source_files=["runtime.cpp"])
        # This is a fully valid/resealed smaller manifest, not a failed checksum.
        self.code("SIM2_SOURCE_CLOSURE", lambda: verify_configuration(omitted, self.service,
            source_root=self.root, expected_source_files=["runtime.cpp", "dependency.hpp"]))


if __name__ == "__main__":
    unittest.main()
