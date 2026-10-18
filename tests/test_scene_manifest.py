"""Scene drafts, binding invalidation and rejection tests; no geometry parser."""

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from controller_lab.scene_manifest import load_json, registration_binding_sha256, validate_manifest


ROOT = Path(__file__).resolve().parents[1]
GEOMETRY = b"synthetic test geometry bytes, not an actual CAD file"
PROFILE = {"id": "test-machine", "version": "draft-3", "sha256": hashlib.sha256(b"test profile identity").hexdigest()}


def pose():
    return {"translation_mm": [0, 0, 0], "quaternion_xyzw": [0, 0, 0, 1]}


def scene():
    return {
        "schema_version": 1,
        "machine_profile": copy.deepcopy(PROFILE),
        "frames": [
            {"id": "world", "parent_frame": None, "transform": pose()},
            {"id": "table", "parent_frame": "world", "transform": pose()},
        ],
        "assets": [{
            "id": "vise", "asset_uri": "synthetic://test-vise", "role": "vise",
            "source_units": "mm", "parent_frame": "table", "transform": pose(),
            "trust_level": "registered",
            "provenance": {"source_kind": "synthetic", "sha256": hashlib.sha256(GEOMETRY).hexdigest()},
        }],
    }


def records(manifest):
    return {"vise": {"record_id": "externally-reviewed-test-record", "binding_sha256": registration_binding_sha256(manifest, "vise")}}


def registered_context(manifest):
    return {"active_profile": PROFILE, "registrations": records(manifest), "asset_bytes": {"vise": GEOMETRY}}


class SceneStructureTests(unittest.TestCase):
    def test_synthetic_example_is_a_valid_draft_with_no_motion_authority(self):
        result = validate_manifest(load_json(ROOT / "examples" / "mr1-scene-draft.json"))
        self.assertTrue(result["structurally_valid"], result["errors"])
        self.assertEqual(len(result["assets"]), 3)
        self.assertFalse(result["motion_authorized"])
        for asset in result["assets"]:
            self.assertEqual(asset["effective_trust"], "visual_only")
            self.assertFalse(asset["geometry_digest_verified"])
            self.assertIn("machine_profile_missing", asset["registration_blockers"])

    def test_missing_role_units_and_profile_are_named_blockers(self):
        manifest = scene()
        del manifest["machine_profile"]
        del manifest["assets"][0]["role"]
        del manifest["assets"][0]["source_units"]
        result = validate_manifest(manifest)
        self.assertTrue(result["structurally_valid"])
        blockers = result["assets"][0]["registration_blockers"]
        for code in ("role_missing_or_invalid", "source_units_missing_or_invalid", "machine_profile_missing"):
            self.assertIn(code, blockers)

    def test_ambiguous_and_malformed_units_are_rejected(self):
        for units in ("auto", "mm/in", "inch", "", 25.4, None, ["mm"], {"unit": "mm"}):
            with self.subTest(units=units):
                manifest = scene()
                manifest["assets"][0]["source_units"] = units
                result = validate_manifest(manifest)
                self.assertFalse(result["structurally_valid"])
                self.assertIn("explicit_mm_or_in_required", [error["code"] for error in result["errors"]])

    def test_source_inches_do_not_change_translation_mm_or_mutate_input(self):
        manifest = scene()
        manifest["assets"][0]["source_units"] = "in"
        manifest["assets"][0]["transform"]["translation_mm"] = [25.4, 0, 0]
        before = copy.deepcopy(manifest)
        result = validate_manifest(manifest)
        self.assertTrue(result["structurally_valid"])
        self.assertEqual(result["assets"][0]["source_to_mm_scale"], 25.4)
        self.assertEqual(manifest, before)

    def test_nonfinite_boolean_and_wrong_size_transforms_are_rejected(self):
        bad_vectors = ([float("nan"), 0, 0], [float("inf"), 0, 0], [10**400, 0, 0], [True, 0, 0], [0, 0], "0,0,0")
        for vector in bad_vectors:
            with self.subTest(vector=vector):
                manifest = scene()
                manifest["assets"][0]["transform"]["translation_mm"] = vector
                result = validate_manifest(manifest)
                self.assertFalse(result["structurally_valid"])
                self.assertEqual(result["assets"][0]["effective_trust"], "visual_only")

    def test_quaternion_requires_unit_length_and_accepts_negative_identity(self):
        for quaternion, expected in (([0, 0, 0, 0], False), ([0, 0, 0, 2], False), ([0, 0, 0, -1], True), ([0, 0, 0, float("inf")], False)):
            with self.subTest(quaternion=quaternion):
                manifest = scene()
                manifest["frames"][0]["transform"]["quaternion_xyzw"] = quaternion
                self.assertEqual(validate_manifest(manifest)["structurally_valid"], expected)

    def test_parent_cycle_is_rejected_even_with_a_separate_valid_root(self):
        manifest = scene()
        manifest["frames"].extend([
            {"id": "cycle_a", "parent_frame": "cycle_b", "transform": pose()},
            {"id": "cycle_b", "parent_frame": "cycle_a", "transform": pose()},
        ])
        result = validate_manifest(manifest)
        self.assertFalse(result["structurally_valid"])
        self.assertIn("frame_cycle", [error["code"] for error in result["errors"]])

    def test_missing_parent_and_multiple_roots_are_rejected(self):
        for parent in ("missing", None):
            with self.subTest(parent=parent):
                manifest = scene()
                manifest["frames"][1]["parent_frame"] = parent
                self.assertFalse(validate_manifest(manifest)["structurally_valid"])

    def test_duplicate_asset_ids_and_cross_namespace_ids_are_rejected(self):
        for duplicate in ("asset", "frame"):
            with self.subTest(duplicate=duplicate):
                manifest = scene()
                if duplicate == "asset":
                    manifest["assets"].append(copy.deepcopy(manifest["assets"][0]))
                else:
                    manifest["assets"][0]["id"] = "world"
                result = validate_manifest(manifest)
                self.assertFalse(result["structurally_valid"])
                self.assertIn("duplicate_id", [error["code"] for error in result["errors"]])

    def test_unsupported_motion_authority_field_is_rejected(self):
        manifest = scene()
        manifest["motion_authorized"] = True
        result = validate_manifest(manifest)
        self.assertFalse(result["structurally_valid"])
        self.assertFalse(result["motion_authorized"])


class RegistrationTests(unittest.TestCase):
    def test_raw_cad_with_digest_and_profile_stays_visual_without_commissioning(self):
        manifest = scene()
        manifest["assets"][0]["provenance"]["source_kind"] = "user_import"
        manifest["assets"][0]["asset_uri"] = "unparsed-file.step"
        result = validate_manifest(manifest, active_profile=PROFILE, asset_bytes={"vise": GEOMETRY})
        asset = result["assets"][0]
        self.assertTrue(asset["geometry_digest_verified"])
        self.assertEqual(asset["effective_trust"], "visual_only")
        self.assertIn("external_commissioning_record_missing_or_invalid", asset["registration_blockers"])
        self.assertFalse(asset["motion_authorized"])

    def test_matching_external_record_registers_metadata_without_authorizing_motion(self):
        manifest = scene()
        result = validate_manifest(manifest, **registered_context(manifest))
        self.assertTrue(result["structurally_valid"])
        self.assertEqual(result["assets"][0]["effective_trust"], "registered")
        self.assertEqual(result["registration_blockers"], [])
        self.assertFalse(result["motion_authorized"])

    def test_digest_declaration_alone_is_not_geometry_verification(self):
        manifest = scene()
        context = registered_context(manifest)
        del context["asset_bytes"]
        asset = validate_manifest(manifest, **context)["assets"][0]
        self.assertEqual(asset["effective_trust"], "visual_only")
        self.assertFalse(asset["geometry_digest_verified"])
        self.assertIn("geometry_bytes_not_supplied_for_digest_verification", asset["registration_blockers"])

    def test_changed_geometry_bytes_invalidate_registration(self):
        manifest = scene()
        context = registered_context(manifest)
        context["asset_bytes"] = {"vise": GEOMETRY + b"changed"}
        asset = validate_manifest(manifest, **context)["assets"][0]
        self.assertEqual(asset["effective_trust"], "visual_only")
        self.assertIn("geometry_digest_mismatch", asset["registration_blockers"])

    def test_parent_placement_role_and_units_changes_invalidate_binding(self):
        for change in ("parent_pose", "asset_pose", "role", "units", "parent_frame"):
            with self.subTest(change=change):
                manifest = scene()
                context = registered_context(manifest)
                if change == "parent_pose":
                    manifest["frames"][1]["transform"]["translation_mm"][0] = 1
                elif change == "asset_pose":
                    manifest["assets"][0]["transform"]["translation_mm"][0] = 1
                elif change == "role":
                    manifest["assets"][0]["role"] = "plate"
                elif change == "units":
                    manifest["assets"][0]["source_units"] = "in"
                else:
                    manifest["assets"][0]["parent_frame"] = "world"
                asset = validate_manifest(manifest, **context)["assets"][0]
                self.assertEqual(asset["effective_trust"], "visual_only")
                self.assertIn("commissioning_record_does_not_match_scene_binding", asset["registration_blockers"])

    def test_profile_id_version_and_digest_must_match_external_active_profile(self):
        for key, value in (("id", "different-machine"), ("version", "draft-4"), ("sha256", "0" * 64)):
            with self.subTest(key=key):
                manifest = scene()
                manifest["machine_profile"][key] = value
                context = registered_context(manifest)
                asset = validate_manifest(manifest, **context)["assets"][0]
                self.assertEqual(asset["effective_trust"], "visual_only")
                self.assertIn("machine_profile_identity_version_or_digest_mismatch", asset["registration_blockers"])

    def test_explicit_visual_only_is_never_implicitly_promoted(self):
        manifest = scene()
        context = registered_context(manifest)
        manifest["assets"][0]["trust_level"] = "visual_only"
        asset = validate_manifest(manifest, **context)["assets"][0]
        self.assertEqual(asset["effective_trust"], "visual_only")
        self.assertIn("asset_explicitly_visual_only", asset["registration_blockers"])


class SceneCliTests(unittest.TestCase):
    def test_cli_reports_valid_uncommissioned_draft(self):
        result = subprocess.run([sys.executable, "-m", "controller_lab.scene_manifest", "examples/mr1-scene-draft.json"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["structurally_valid"])
        self.assertFalse(report["motion_authorized"])
        self.assertTrue(report["registration_blockers"])

    def test_loader_rejects_duplicate_json_fields_and_nonfinite_constants(self):
        for content in ('{"id":"a","id":"b"}', '{"value":NaN}', '{"value":Infinity}'):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "invalid.json"
                path.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_json(path)

    def test_schema_is_parseable_and_documents_runtime_checks(self):
        schema = load_json(ROOT / "schemas" / "scene-manifest.schema.json")
        self.assertEqual(schema["$defs"]["asset"]["properties"]["source_units"]["enum"], ["mm", "in"])
        self.assertIn("acyclic", schema["description"])


if __name__ == "__main__":
    unittest.main()
