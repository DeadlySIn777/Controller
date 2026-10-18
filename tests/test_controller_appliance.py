"""Explicit temporary appliance fixtures; no existing store or device changes."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid

from controller_appliance.service import (ApplianceError, ApplianceService, DEFAULTS, MAX_SCAN,
                                          PLAN_SECONDS, canonical, digest)
from controller_config import package_archive


class ApplianceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.now = 10000
        self.app = ApplianceService(self.root, clock=lambda: self.now)
        self.protected = {}
        for name in ("setup.json", "budget.json", "calibration.json", "entitlements.json", "machine-backup.json", "job.nc"):
            path = self.root / name
            path.write_bytes(("PROTECTED FIXTURE " + name).encode())
            self.protected[name] = path.read_bytes()

    def tearDown(self):
        for name, expected in self.protected.items():
            self.assertEqual((self.root / name).read_bytes(), expected, name)
        self.temp.cleanup()

    def code(self, code, function, *args, **kwargs):
        with self.assertRaises(ApplianceError) as caught:
            function(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)

    def commit(self, plan, request_id=None):
        return self.app.confirm(plan, request_id or str(uuid.uuid4()), plan["confirmation"])

    def set_preferences(self):
        return self.commit(self.app.preview_preferences({"display_scale": 1.5, "reduced_motion": True, "startup_page": "files"}, 0))

    def archive(self, name="config.tar.zst", kind="config"):
        if not package_archive.capabilities()["available"]:
            self.skipTest("compression.zstd unavailable on this Python")
        folder = self.root / "packages"
        folder.mkdir(exist_ok=True)
        return package_archive.create_archive(folder / name, {"machine/config.json": b'{"inert":true}'}, kind)

    def test_read_only_first_use_and_nested_new_workspace(self):
        selected = self.root / "new"
        app = ApplianceService(selected)
        self.assertFalse(app.status()["initialized"])
        self.assertEqual(app.files()["files"], [])
        self.assertFalse(selected.exists())
        plan = app.preview_reset()
        self.assertFalse(selected.exists())
        app.confirm(plan, str(uuid.uuid4()), plan["confirmation"])
        self.assertTrue((selected / "appliance" / "preferences.json").is_file())
        self.assertEqual(set(p.name for p in selected.iterdir()), {"appliance"})

    def test_preferences_reset_and_undo_preserve_all_machine_files(self):
        self.set_preferences()
        plan = self.app.preview_reset()
        self.assertEqual(len(plan["diff"]), 3)
        self.assertEqual(plan["scope"], "appliance_preferences")
        result = self.commit(plan)
        self.assertEqual(result["preferences"], DEFAULTS)
        fresh = ApplianceService(self.root, clock=lambda: self.now)
        self.assertTrue(fresh.status()["undo_available"])
        undo = fresh.preview_undo()
        fresh.confirm(undo, str(uuid.uuid4()), undo["confirmation"])
        self.assertEqual(fresh.status()["preferences"]["display_scale"], 1.5)
        self.assertFalse(fresh.status()["undo_available"])

    def test_full_machine_reset_blocked_without_writes(self):
        self.code("MACHINE_RESET_BLOCKED", self.app.preview_reset, "full_machine")
        self.assertFalse((self.root / "appliance").exists())
        self.assertFalse(self.app.status()["full_machine_reset"]["available"])

    def test_service_view_deliberate_volatile_and_has_no_authority(self):
        self.code("APPLIANCE_CONFIRMATION", self.app.service_mode, True, "yes")
        result = self.app.service_mode(True, "ENTER SERVICE VIEW")
        self.assertTrue(result["service_mode"])
        self.assertFalse(result["motion_authorized"])
        self.assertFalse(result["physical_authority"])
        self.assertEqual(result["machine_commands"], [])
        self.assertFalse(ApplianceService(self.root).status()["service_mode"])
        self.assertFalse((self.root / "appliance").exists())

    def test_browser_numeric_roundtrip_and_unknown_preferences(self):
        plan = self.app.preview_preferences({"display_scale": 1.0}, 0)
        self.assertIs(type(plan["preferences"]["display_scale"]), int)
        self.commit(json.loads(json.dumps(plan)))
        for patch_value in ({"display_scale": True}, {"display_scale": float("nan")}, {"display_scale": 2},
                            {"reduced_motion": 1}, {"startup_page": "terminal"}, {"motion_authorized": True}):
            self.code("APPLIANCE_PREFERENCES", self.app.preview_preferences, patch_value, 1)

    def test_stale_revision_and_plan_binding(self):
        old = self.app.preview_reset()
        self.set_preferences()
        self.code("APPLIANCE_STALE", self.commit, old)
        self.code("APPLIANCE_STALE", self.app.preview_preferences, {"display_scale": 1}, 0)
        self.code("APPLIANCE_STALE", self.app.preview_preferences, {"display_scale": 1}, True)

    def test_first_use_plan_is_bound_to_selected_workspace(self):
        other = self.root / "other-empty-workspace"
        plan = self.app.preview_preferences({"display_scale": 1.5}, 0)
        app = ApplianceService(other, clock=lambda: self.now)
        self.code("APPLIANCE_STALE", app.confirm, plan, str(uuid.uuid4()), plan["confirmation"])
        self.assertFalse(app.path.exists())
        self.assertFalse((other / "setup.json").exists())
        self.assertNotEqual(plan["binding"]["workspace_id"], app.status()["binding"]["workspace_id"])
        alias = ApplianceService(self.root / ".." / self.root.name, clock=lambda: self.now)
        self.assertEqual(plan["binding"]["workspace_id"], alias.status()["binding"]["workspace_id"])
        self.assertEqual(alias.confirm(plan, str(uuid.uuid4()), plan["confirmation"])["preferences"]["display_scale"], 1.5)

    def test_undo_invalidated_by_new_preferences(self):
        self.set_preferences()
        self.commit(self.app.preview_reset())
        old = self.app.preview_undo()
        self.commit(self.app.preview_preferences({"display_scale": 1.25}, 2))
        self.code("APPLIANCE_UNDO", self.app.preview_undo)
        self.code("APPLIANCE_STALE", self.commit, old)

    def test_exact_confirmation_and_expiry(self):
        plan = self.app.preview_reset()
        self.code("APPLIANCE_CONFIRMATION", self.app.confirm, plan, str(uuid.uuid4()), "RESET EVERYTHING")
        self.now += PLAN_SECONDS
        self.code("APPLIANCE_EXPIRED", self.commit, plan)
        plan = self.app.preview_reset()
        self.now -= 1
        self.code("APPLIANCE_EXPIRED", self.commit, plan)

    def test_retry_is_idempotent_even_after_expiry_and_rejects_conflicting_uuid(self):
        plan = self.app.preview_reset()
        request_id = str(uuid.uuid4())
        self.commit(plan, request_id)
        before = self.app.path.read_bytes()
        self.now += PLAN_SECONDS + 1
        result = self.commit(plan, request_id)
        self.assertTrue(result["idempotent"])
        self.assertEqual(self.app.path.read_bytes(), before)
        self.code("APPLIANCE_REQUEST_CONFLICT", self.commit, self.app.preview_reset(), request_id)

    def test_resealed_forged_reset_target_and_scope_are_rejected(self):
        plan = self.app.preview_reset()
        for changes in ({"preferences": {**DEFAULTS, "display_scale": 1.5}}, {"scope": "machine"},
                        {"preserved": []}, {"terminal_available": True}, {"unknown": 1}):
            bad = {**deepcopy(plan), **changes}
            bad["plan_sha256"] = digest({k: v for k, v in bad.items() if k != "plan_sha256"})
            self.code("APPLIANCE_PLAN", self.commit, bad)
        self.assertFalse(self.app.path.exists())

    def test_corrupt_and_duplicate_preference_store_fails_without_overwrite(self):
        self.set_preferences()
        good = self.app.path.read_bytes()
        self.app.path.write_bytes(good.replace(b'"display_scale":1.5', b'"display_scale":1.25'))
        before = self.app.path.read_bytes()
        self.code("APPLIANCE_INTEGRITY", self.app.status)
        self.assertEqual(self.app.path.read_bytes(), before)
        self.app.path.write_bytes(b'{"schema_version":1,"schema_version":1}')
        self.code("APPLIANCE_FORMAT", self.app.status)

    def test_actual_process_owned_lock_blocks_second_writer_and_recovers(self):
        plan = self.app.preview_reset()
        with self.app._lock():
            another = ApplianceService(self.root, clock=lambda: self.now)
            self.code("APPLIANCE_BUSY", another.confirm, plan, str(uuid.uuid4()), plan["confirmation"])
        self.commit(plan)
        self.assertEqual(self.app.status()["revision"], 1)

    def test_lost_publication_ack_is_uncertain_then_exact_retry_recovers(self):
        plan = self.app.preview_reset()
        request_id = str(uuid.uuid4())
        actual_replace = os.replace
        def lost(*args, **kwargs):
            actual_replace(*args, **kwargs)
            raise OSError("injected acknowledgement loss")
        with patch("controller_appliance.service.os.replace", side_effect=lost):
            self.code("APPLIANCE_PUBLICATION_UNCERTAIN", self.app.confirm, plan, request_id, plan["confirmation"])
        self.assertEqual(self.app.status()["revision"], 1)
        self.assertTrue(self.commit(plan, request_id)["idempotent"])
        self.assertEqual(list(self.app.directory.glob("*.pending")), [])

    def test_failed_write_preserves_previous_preferences(self):
        self.set_preferences()
        before = self.app.path.read_bytes()
        plan = self.app.preview_reset()
        with patch("controller_appliance.service.os.replace", side_effect=OSError("injected prepublication failure")):
            self.code("APPLIANCE_IO", self.commit, plan)
        self.assertEqual(self.app.path.read_bytes(), before)
        self.assertEqual(list(self.app.directory.glob("*.pending")), [])

    def test_preference_hardlink_is_rejected_without_modifying_original(self):
        self.app.directory.mkdir()
        os.link(self.root / "calibration.json", self.app.path)
        self.code("APPLIANCE_FILE", self.app.status)

    def test_symlink_preferences_and_package_are_rejected(self):
        self.app.directory.mkdir()
        try:
            self.app.path.symlink_to(self.root / "calibration.json")
        except OSError:
            self.skipTest("Windows symlink permission unavailable")
        self.code("APPLIANCE_FILE", self.app.status)
        (self.root / "packages").mkdir()
        (self.root / "packages" / "bad.tar.zst").symlink_to(self.root / "calibration.json")
        self.assertEqual(self.app.files()["files"], [])
        self.assertEqual(len(self.app.files()["unavailable"]), 1)

    def test_linked_parent_is_rejected_without_traversal(self):
        original = self.root / "original"
        original.mkdir()
        link = self.root / "link"
        try:
            link.symlink_to(original, target_is_directory=True)
        except OSError:
            self.skipTest("Windows symlink permission unavailable")
        self.code("APPLIANCE_PATH", ApplianceService(link).status)
        self.assertEqual(list(original.iterdir()), [])

    def test_fifo_package_is_not_opened_or_blocking(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO test runs on Linux")
        folder = self.root / "packages"
        folder.mkdir()
        os.mkfifo(folder / "fifo.tar.zst")
        result = self.app.files()
        self.assertEqual(result["files"], [])
        self.assertEqual(result["unavailable"][0]["error"]["code"], "APPLIANCE_FILE")

    def test_fifo_swap_during_unchanged_archive_validator_is_nonblocking(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO test runs on Linux")
        folder = self.root / "packages"
        folder.mkdir()
        path = folder / "swap.tar.zst"
        path.write_bytes(b"inert negative file fixture")
        actual_reader = package_archive.read_archive
        def swapped(target):
            path.unlink()
            os.mkfifo(path)
            return actual_reader(target)
        # The inert backend sentinel reaches the unchanged regular-file guard;
        # it never decompresses bytes or marks a package valid.
        with patch.object(package_archive, "_zstd", object()), patch.object(package_archive, "read_archive", side_effect=swapped):
            result = self.app.files()
        self.assertEqual(result["files"], [])
        self.assertEqual(result["unavailable"][0]["error"]["code"], "ARCHIVE_SIZE")

    def test_oversized_sparse_package_refused_before_archive_decode(self):
        from controller_appliance.service import MAX_PACKAGE
        folder = self.root / "packages"
        folder.mkdir()
        with (folder / "large.tar.zst").open("wb") as handle:
            handle.truncate(MAX_PACKAGE + 1)
        with patch.object(package_archive, "read_archive", side_effect=AssertionError("must not decode")):
            result = self.app.files()
        self.assertEqual(result["files"], [])
        self.assertEqual(result["unavailable"][0]["error"]["code"], "APPLIANCE_FILE")

    def test_inventory_io_errors_do_not_reveal_absolute_paths(self):
        folder = self.root / "packages"
        folder.mkdir()
        (folder / "private.tar.zst").write_bytes(b"inert")
        with patch.object(self.app, "_package", side_effect=OSError(f"private path: {self.root}")):
            result = self.app.files()
        self.assertNotIn(str(self.root), json.dumps(result))

    def test_real_package_inventory_and_sha_bound_download(self):
        receipt = self.archive()
        self.archive("support.tar.zst", "support")
        result = self.app.files()
        self.assertEqual({r["kind"] for r in result["files"]}, {"config", "support"})
        row = next(r for r in result["files"] if r["kind"] == "config")
        downloaded = self.app.download(row["package_id"], row["sha256"])
        self.assertEqual(hashlib.sha256(downloaded["data"]).hexdigest(), receipt["sha256"])
        self.assertTrue(row["integrity_verified"])
        self.assertFalse(row["authenticates_sender"])
        self.code("APPLIANCE_STALE", self.app.download, row["package_id"], "f" * 64)
        for package_id in ("../setup.json", str(self.root / "setup.json"), True):
            self.code("APPLIANCE_DOWNLOAD", self.app.download, package_id, row["sha256"])

    def test_unsupported_and_corrupt_packages_never_download(self):
        self.archive("job.tar.zst", "job")
        receipt = self.archive()
        path = Path(receipt["path"])
        body = bytearray(path.read_bytes())
        body[-1] ^= 0x80
        path.write_bytes(body)
        result = self.app.files()
        self.assertEqual(result["files"], [])
        self.assertEqual(len(result["unavailable"]), 2)
        self.code("APPLIANCE_PACKAGE_KIND", self.app.download, hashlib.sha256(b"job.tar.zst").hexdigest(), "f" * 64)

    def test_absent_zstd_backend_is_visible_and_never_fake_verified(self):
        self.archive()
        with patch.object(package_archive, "_zstd", None):
            result = self.app.files()
        self.assertEqual(result["files"], [])
        self.assertFalse(result["archive_capabilities"]["available"])
        self.assertEqual(result["unavailable"][0]["error"]["code"], "ARCHIVE_UNAVAILABLE")

    def test_package_changed_between_raw_read_and_archive_validation_is_refused(self):
        receipt = self.archive()
        row = self.app.files()["files"][0]
        actual_read = package_archive.read_archive
        def changed(path):
            Path(path).unlink()
            package_archive.create_archive(path, {"other.json": b'{}'}, "config")
            return actual_read(path)
        with patch.object(package_archive, "read_archive", side_effect=changed):
            self.code("APPLIANCE_FILE_CHANGED", self.app.download, row["package_id"], receipt["sha256"])

    def test_bounded_scan_has_no_partial_success(self):
        folder = self.root / "packages"
        folder.mkdir()
        for i in range(MAX_SCAN + 1):
            (folder / f"unapproved-{i}.txt").write_bytes(b"")
        self.code("APPLIANCE_INVENTORY_LIMIT", self.app.files)

    def test_non_regular_workspace_is_refused(self):
        path = self.root / "not-a-directory"
        path.write_bytes(b"inert")
        self.code("APPLIANCE_PATH", ApplianceService(path).status)

    def test_cli_status_preview_confirm_and_exclusive_download(self):
        command = [sys.executable, "-m", "controller_appliance", "--directory", str(self.root)]
        def invoke(*args):
            done = subprocess.run([*command, *args], capture_output=True, text=True, timeout=15)
            self.assertEqual(done.stderr, "")
            return done.returncode, json.loads(done.stdout)
        code, status = invoke("status")
        self.assertEqual(code, 0)
        self.assertFalse(status["result"]["initialized"])
        code, preview = invoke("preview-preferences", "--patch", '{"display_scale":1.25}', "--expected-revision", "0")
        self.assertEqual(code, 0)
        plan = preview["result"]
        path = self.root / "reviewed-plan.json"
        path.write_bytes(canonical(plan))
        code, result = invoke("confirm", "--plan", str(path), "--request-id", str(uuid.uuid4()), "--confirmation", plan["confirmation"])
        self.assertEqual(code, 0)
        self.assertEqual(result["result"]["preferences"]["display_scale"], 1.25)
        self.archive()
        row = self.app.files()["files"][0]
        target = self.root / "download.tar.zst"
        args = ("download", "--package-id", row["package_id"], "--expected-sha256", row["sha256"], "--output", str(target))
        code, _ = invoke(*args)
        self.assertEqual(code, 0)
        before = target.read_bytes()
        code, failed = invoke(*args)
        self.assertEqual(code, 1)
        self.assertEqual(failed["error"]["code"], "ARCHIVE_EXISTS")
        self.assertEqual(target.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
