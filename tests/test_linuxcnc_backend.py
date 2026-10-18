"""API-contract tests with a fake LinuxCNC module; these do not prove motion."""
from dataclasses import replace
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from controller_backend import BackendError, LinuxCNCBackend
from controller_backend import fetch_debian_rootfs
from controller_backend.fetch_debian_rootfs import extract_layer, rootfs_member_filter


class Clock:
    def __init__(self):
        self.now = 10.0

    def __call__(self):
        return self.now


class FakeAPI:
    STATE_ESTOP, STATE_ESTOP_RESET, STATE_OFF, STATE_ON = 1, 2, 3, 4
    MODE_MANUAL, MODE_AUTO, MODE_MDI = 1, 2, 3
    INTERP_IDLE, INTERP_READING, INTERP_PAUSED = 1, 2, 3
    AUTO_RUN, AUTO_PAUSE, AUTO_RESUME = 1, 2, 3
    RCS_DONE, RCS_ERROR = 1, 3
    NML_ERROR, OPERATOR_ERROR = 1, 11

    def __init__(self):
        self.created = []
        self.calls = []
        self.error_queue = []
        self.fail_poll = False
        self.wait_result = self.RCS_DONE
        self.s = SimpleNamespace(
            ini_filename=str(LinuxCNCBackend().profile), joints=3, axis_mask=7,
            task_state=self.STATE_ESTOP, task_mode=self.MODE_MANUAL,
            interp_state=self.INTERP_IDLE, enabled=False, estop=True,
            homed=(False, False, False), actual_position=(0.0,) * 9,
            position=(0.0,) * 9, paused=False, inpos=True, current_vel=0.0,
            motion_line=0, file="", poll=self._poll)

    def _poll(self):
        if self.fail_poll:
            raise RuntimeError("NML unavailable")

    def stat(self):
        self.created.append("stat")
        return self.s

    def command(self):
        self.created.append("command")
        return self

    def error_channel(self):
        self.created.append("error_channel")
        return SimpleNamespace(poll=lambda: self.error_queue.pop(0) if self.error_queue else None)

    def wait_complete(self, timeout):
        return self.wait_result

    def state(self, state):
        self.calls.append(("state", state))
        self.s.task_state = self.STATE_OFF if state == self.STATE_ESTOP_RESET else state
        self.s.estop = state == self.STATE_ESTOP
        self.s.enabled = state == self.STATE_ON

    def mode(self, mode):
        self.calls.append(("mode", mode))
        self.s.task_mode = mode

    def teleop_enable(self, value):
        self.calls.append(("teleop_enable", value))

    def home(self, joint):
        self.calls.append(("home", joint))
        self.s.homed = (True, True, True)

    def mdi(self, line):
        self.calls.append(("mdi", line))

    def program_open(self, path):
        self.calls.append(("program_open", path))
        self.s.file = path

    def auto(self, *args):
        self.calls.append(("auto", *args))
        self.s.paused = args[0] == self.AUTO_PAUSE
        self.s.interp_state = self.INTERP_PAUSED if self.s.paused else self.INTERP_READING

    def abort(self):
        self.calls.append(("abort",))
        self.s.interp_state = self.INTERP_IDLE


class LinuxCNCBackendTests(unittest.TestCase):
    def setUp(self):
        self.api, self.clock = FakeAPI(), Clock()
        self.backend = LinuxCNCBackend(api=self.api, clock=self.clock)

    def connect(self):
        return self.backend.connect()

    def send(self, action, **args):
        self.backend.poll()
        return self.backend.execute(self.backend.issue(action, **args))

    def ready(self):
        self.connect()
        self.send("reset_estop")
        self.send("power_on")
        self.send("home_all")

    def load(self):
        path = self.backend.profile.parent / "programs/line_arc.ngc"
        return self.send("open_program", name=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def test_constructor_does_not_connect_or_import(self):
        self.assertFalse(self.backend.connected)
        self.assertEqual(self.api.created, [])
        with self.assertRaises(BackendError):
            self.backend.issue("power_on")

    def test_live_hardware_mode_is_not_implemented(self):
        with self.assertRaises(ValueError):
            LinuxCNCBackend(simulation_only=False)

    def test_configuration_rejects_invalid_freshness(self):
        for value in (0, -1, float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                LinuxCNCBackend(status_max_age=value)

    def test_foreign_profile_rejected_before_command_channel(self):
        self.api.s.ini_filename = "/real-machine/machine.ini"
        with self.assertRaises(BackendError):
            self.connect()
        self.assertEqual(self.api.created, ["stat"])
        self.assertFalse(self.backend.connected)

    def test_uninitialized_status_rejected(self):
        self.api.s.axis_mask = 0
        with self.assertRaises(BackendError):
            self.connect()

    def test_connect_is_read_only(self):
        self.connect()
        self.assertEqual(self.api.calls, [])

    def test_expired_request_is_consumed_without_api_command(self):
        self.connect()
        request = self.backend.issue("reset_estop")
        self.clock.now += 0.5
        with self.assertRaisesRegex(BackendError, "expired"):
            self.backend.execute(request)
        self.assertEqual(self.api.calls, [])
        with self.assertRaisesRegex(BackendError, "replayed"):
            self.backend.execute(request)

    def test_stale_status_rejects_fresh_request(self):
        self.connect()
        self.clock.now += 0.6
        request = self.backend.issue("reset_estop")
        with self.assertRaisesRegex(BackendError, "stale"):
            self.backend.execute(request)
        self.assertEqual(self.api.calls, [])

    def test_reordered_request_cannot_execute(self):
        self.connect()
        older = self.backend.issue("reset_estop")
        newer = self.backend.issue("reset_estop")
        self.backend.execute(newer)
        with self.assertRaisesRegex(BackendError, "reordered"):
            self.backend.execute(older)

    def test_modified_request_cannot_execute(self):
        self.connect()
        request = self.backend.issue("reset_estop")
        with self.assertRaisesRegex(BackendError, "modified"):
            self.backend.execute(replace(request, action="power_on"))
        with self.assertRaises(BackendError):
            self.backend.execute(request)

    def test_state_rejection_cannot_be_replayed_when_ready(self):
        self.connect()
        request = self.backend.issue("mdi", line="G1 X1 F100")
        with self.assertRaisesRegex(BackendError, "not enabled"):
            self.backend.execute(request)
        self.send("reset_estop")
        self.send("power_on")
        self.send("home_all")
        with self.assertRaisesRegex(BackendError, "replayed"):
            self.backend.execute(request)

    def test_reconnect_invalidates_requests(self):
        self.connect()
        request = self.backend.issue("reset_estop")
        old_session = self.backend.session
        self.backend.disconnect()
        self.connect()
        self.assertNotEqual(old_session, self.backend.session)
        with self.assertRaisesRegex(BackendError, "expired connection"):
            self.backend.execute(request)
        self.assertEqual(self.api.calls, [])

    def test_reconnect_does_not_resume_program(self):
        self.ready()
        self.load()
        self.backend.disconnect()
        self.connect()
        with self.assertRaisesRegex(BackendError, "reopened"):
            self.send("run")
        self.assertFalse(any(c[0] == "auto" for c in self.api.calls))

    def test_mdi_requires_homing(self):
        self.connect()
        self.send("reset_estop")
        self.send("power_on")
        with self.assertRaisesRegex(BackendError, "homed"):
            self.send("mdi", line="G1 X1 F100")

    def test_mdi_calls_real_api_shape(self):
        self.ready()
        self.send("mdi", line="G1 X1 F100")
        self.assertEqual(self.api.calls[-2:], [("mode", self.api.MODE_MDI), ("mdi", "G1 X1 F100")])

    def test_mdi_rejects_multiline(self):
        self.ready()
        with self.assertRaisesRegex(BackendError, "one nonempty line"):
            self.send("mdi", line="G1 X1\nM3")

    def test_program_cannot_escape_profile(self):
        self.ready()
        with self.assertRaises(BackendError):
            self.send("open_program", name="../machine.ngc", sha256="0" * 64)

    def test_program_digest_must_match(self):
        self.ready()
        with self.assertRaisesRegex(BackendError, "digest"):
            self.send("open_program", name="line_arc.ngc", sha256="0" * 64)

    def test_run_pause_resume_are_explicit(self):
        self.ready()
        self.load()
        self.send("run")
        self.send("pause")
        self.send("resume")
        self.assertEqual([c for c in self.api.calls if c[0] == "auto"], [("auto", self.api.AUTO_RUN, 0), ("auto", self.api.AUTO_PAUSE), ("auto", self.api.AUTO_RESUME)])

    def test_resume_requires_reported_pause(self):
        self.ready()
        self.load()
        with self.assertRaisesRegex(BackendError, "reported paused"):
            self.send("resume")

    def test_timeout_drops_authority_and_never_retries(self):
        self.connect()
        self.api.wait_result = -1
        with self.assertRaisesRegex(BackendError, "not be retried"):
            self.send("reset_estop")
        self.assertFalse(self.backend.connected)
        self.assertEqual(len(self.api.calls), 1)

    def test_status_failure_drops_authority(self):
        self.connect()
        self.api.fail_poll = True
        with self.assertRaises(BackendError):
            self.backend.poll()
        self.assertFalse(self.backend.connected)

    def test_error_channel_is_read_and_exposed(self):
        self.connect()
        self.api.error_queue.append((self.api.OPERATOR_ERROR, "test error"))
        sample = self.backend.poll()
        self.assertEqual(sample.errors, ((self.api.OPERATOR_ERROR, "test error"),))

    def test_abort_can_be_requested_when_status_age_is_stale(self):
        self.connect()
        self.clock.now += 10
        self.backend.execute(self.backend.issue("abort"))
        self.assertEqual(self.api.calls, [("abort",)])

    def test_preexisting_error_blocks_motion_even_after_error_channel_consumed(self):
        self.ready()
        self.api.error_queue.append((self.api.OPERATOR_ERROR, "unhandled controller fault"))
        self.backend.poll()
        before = list(self.api.calls)
        with self.assertRaisesRegex(BackendError, "error latched"):
            self.send("mdi", line="G1 X1 F100")
        self.assertEqual(before, self.api.calls)
        self.send("abort")

    def test_error_arriving_at_command_precheck_blocks_motion(self):
        self.ready()
        request = self.backend.issue("mdi", line="G1 X1 F100")
        self.api.error_queue.append((self.api.OPERATOR_ERROR, "new controller fault"))
        before = list(self.api.calls)
        with self.assertRaisesRegex(BackendError, "error latched"):
            self.backend.execute(request)
        self.assertEqual(before, self.api.calls)

    def test_expiry_during_status_refresh_sends_nothing(self):
        self.connect()
        request = self.backend.issue("reset_estop")
        self.api.s.poll = lambda: setattr(self.clock, "now", self.clock.now + 0.6)
        with self.assertRaisesRegex(BackendError, "expired during status"):
            self.backend.execute(request)
        self.assertEqual(self.api.calls, [])

    def test_expiry_during_mode_change_cannot_send_mdi(self):
        self.ready()
        original_mode = self.api.mode
        def delayed_mode(mode):
            original_mode(mode)
            self.clock.now += 0.6
        self.api.mode = delayed_mode
        request = self.backend.issue("mdi", line="G1 X1 F100")
        with self.assertRaisesRegex(BackendError, "expired before sending"):
            self.backend.execute(request)
        self.assertFalse(any(call[0] == "mdi" for call in self.api.calls))
        with self.assertRaisesRegex(BackendError, "replayed"):
            self.backend.execute(request)

    def test_nonfinite_velocity_discards_authority(self):
        self.connect()
        self.api.s.current_vel = float("nan")
        with self.assertRaises(BackendError):
            self.backend.poll()
        self.assertFalse(self.backend.connected)

    def test_run_is_asynchronous_to_keep_hold_and_abort_available(self):
        self.ready()
        self.load()
        self.api.wait_result = -1
        self.send("run")
        self.assertTrue(self.backend.connected)


    def test_sample_records_controller_reported_ini_filename(self):
        # The fake reports an equivalent but differently spelled path; the
        # sample must carry the observed string, not the adapter's expectation.
        reported = os.path.join(str(self.backend.profile.parent), ".", "controller.ini")
        self.assertNotEqual(reported, str(self.backend.profile))
        self.api.s.ini_filename = reported
        sample = self.connect()
        self.assertEqual(sample.ini_filename, reported)
        self.assertEqual(self.backend.sample.ini_filename, self.api.s.ini_filename)
        self.assertEqual(Path(sample.ini_filename).resolve(), self.backend.profile)

    def _profile_copy(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        for name in ("controller.ini", "simulation.hal", "display-client", "manifest.json"):
            shutil.copyfile(self.backend.profile.with_name(name), tmp / name)
        return tmp

    def test_profile_copy_positive_control_connects(self):
        tmp = self._profile_copy()
        self.backend.profile = (tmp / "controller.ini").resolve()
        self.api.s.ini_filename = str(self.backend.profile)
        self.assertTrue(self.connect().ini_filename.endswith("controller.ini"))
        self.assertTrue(self.backend.connected)

    def test_profile_file_problems_raise_backend_error_before_any_channel(self):
        def missing_manifest(d): (d / "manifest.json").unlink()
        def malformed_json(d): (d / "manifest.json").write_text("{not json")
        def list_manifest(d): (d / "manifest.json").write_text("[]")
        def sha256_not_object(d):
            (d / "manifest.json").write_text(json.dumps({"schema": 1, "mode": "software-only", "sha256": ["x"]}))
        def wrong_mode(d):
            data = json.loads((d / "manifest.json").read_text())
            data["mode"] = "hardware"
            (d / "manifest.json").write_text(json.dumps(data))
        def missing_profile_file(d): (d / "display-client").unlink()
        def changed_ini(d): (d / "controller.ini").write_text("[EMCMOT]\n")
        for mutate in (missing_manifest, malformed_json, list_manifest, sha256_not_object,
                       wrong_mode, missing_profile_file, changed_ini):
            with self.subTest(case=mutate.__name__):
                api = FakeAPI()
                backend = LinuxCNCBackend(api=api, clock=self.clock)
                tmp = self._profile_copy()
                backend.profile = (tmp / "controller.ini").resolve()
                api.s.ini_filename = str(backend.profile)
                mutate(tmp)
                with self.assertRaises(BackendError):
                    backend.connect()
                self.assertEqual(api.created, [])
                self.assertFalse(backend.connected)

    def test_launchers_start_from_clean_work_copy_and_shared_rootfs_variable(self):
        """Source inspection of the WSL launchers (not an execution test)."""
        package = self.backend.profile.parents[2]
        run = (package / "run_isolated_simulation.sh").read_text()
        self.assertLess(run.index('rm -rf "$task_root/work/controller_backend"\n'),
                        run.index('cp -a "$source_dir" "$task_root/work/"'))
        after_copy = run[run.index('cp -a "$source_dir"'):run.index("timeout 120 unshare")]
        for cleanup in ('profiles/sim/"*.var*', "-name __pycache__", '/work/controller_backend/evidence"'):
            self.assertIn(cleanup, after_copy)
        for script in ("run_isolated_simulation.sh", "provision_isolated_runtime.sh"):
            text = (package / script).read_text()
            self.assertIn("task_root=${CONTROLLER_LAB_ROOTFS:-/root/.cache/controller-lab-linuxcnc/rootfs}", text)
            self.assertEqual(text.count("/root/.cache/controller-lab-linuxcnc/rootfs"), 1, script)
        self.assertIn('os.environ.get("CONTROLLER_LAB_ROOTFS"', (package / "fetch_debian_rootfs.py").read_text())


def _symlinks_supported():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            os.symlink(tmp, os.path.join(tmp, "probe"))
        except (OSError, NotImplementedError, AttributeError):
            return False
    return True


class RootfsLayerFilterTests(unittest.TestCase):
    """Synthetic-archive host tests of the OCI layer extraction filter."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = (self.tmp / "rootfs").resolve()
        self.root.mkdir()
        self.outside = (self.tmp / "outside").resolve()
        self.outside.mkdir()

    def archive(self, *members, name="layer.tar.gz"):
        path = self.tmp / name
        with tarfile.open(path, "w:gz") as tar:
            for info, data in members:
                tar.addfile(info, io.BytesIO(data) if data is not None else None)
        return path

    @staticmethod
    def entry(name, kind=tarfile.REGTYPE, data=b"", linkname="", mode=0o644, uid=0, gid=0):
        info = tarfile.TarInfo(name)
        info.type, info.linkname, info.mode, info.uid, info.gid = kind, linkname, mode, uid, gid
        if kind == tarfile.REGTYPE:
            info.size = len(data)
            return info, data
        return info, None

    def assertRefused(self, *members):
        with self.assertRaises(tarfile.FilterError):
            extract_layer(self.archive(*members), self.root)
        self.assertEqual(list(self.outside.iterdir()), [])

    def test_regular_file_mode_and_ownership_are_preserved(self):
        extract_layer(self.archive(self.entry("usr/bin/su", data=b"su", mode=0o4755, uid=1234, gid=2345),
                                   self.entry("etc", kind=tarfile.DIRTYPE, mode=0o755)), self.root)
        target = self.root / "usr/bin/su"
        self.assertEqual(target.read_bytes(), b"su")
        if os.name == "posix":
            self.assertEqual(target.stat().st_mode & 0o7777, 0o4755)
            if os.geteuid() == 0:
                self.assertEqual((target.stat().st_uid, target.stat().st_gid), (1234, 2345))

    @unittest.skipUnless(_symlinks_supported(), "symlink creation unavailable on this host")
    def test_absolute_and_contained_relative_symlinks_are_kept(self):
        extract_layer(self.archive(self.entry("var", kind=tarfile.DIRTYPE, mode=0o755),
                                   self.entry("var/run", kind=tarfile.SYMTYPE, linkname="/run"),
                                   self.entry("bin", kind=tarfile.SYMTYPE, linkname="usr/bin")), self.root)
        self.assertEqual(os.readlink(self.root / "var/run"), "/run")
        self.assertEqual(os.readlink(self.root / "bin"), "usr/bin")

    def test_escaping_or_absolute_member_names_are_refused(self):
        for name in ("../escape", "/abs", "a/../../escape"):
            with self.subTest(name=name):
                self.assertRefused(self.entry(name, data=b"x"))

    def test_device_nodes_and_fifos_are_refused(self):
        for kind in (tarfile.CHRTYPE, tarfile.BLKTYPE, tarfile.FIFOTYPE):
            with self.subTest(kind=kind):
                info, _ = self.entry("dev/evil", kind=kind)
                info.devmajor, info.devminor = 1, 3
                self.assertRefused((info, None))
                self.assertFalse((self.root / "dev/evil").exists())

    def test_escaping_hardlinks_are_refused(self):
        for linkname in ("../../outside/secret", "/etc/passwd", "a/../../x"):
            with self.subTest(linkname=linkname):
                self.assertRefused(self.entry("h", kind=tarfile.LNKTYPE, linkname=linkname))

    def test_lexically_escaping_relative_symlink_is_refused(self):
        self.assertRefused(self.entry("usr/lib/x", kind=tarfile.SYMTYPE, linkname="../../../outside"))

    @unittest.skipUnless(_symlinks_supported(), "symlink creation unavailable on this host")
    def test_write_through_symlink_extracted_earlier_in_layer_is_refused(self):
        # usr -> <outside> followed by usr/passwd: the second member would be
        # written on the host outside the rootfs, so extraction must stop.
        self.assertRefused(self.entry("usr", kind=tarfile.SYMTYPE, linkname=str(self.outside)),
                           self.entry("usr/passwd", data=b"root::0:0"))

    @unittest.skipUnless(_symlinks_supported(), "symlink creation unavailable on this host")
    def test_members_under_existing_escaping_symlink_are_refused(self):
        os.symlink(self.outside, self.root / "usr")
        mode_before = os.stat(self.outside).st_mode
        cases = {
            "file": self.entry("usr/passwd", data=b"x"),
            "directory": self.entry("usr", kind=tarfile.DIRTYPE, mode=0o777),
            "hardlink": self.entry("h", kind=tarfile.LNKTYPE, linkname="usr/passwd"),
            "symlink_parent": self.entry("usr/evil", kind=tarfile.SYMTYPE, linkname="/run"),
        }
        for case, member in cases.items():
            with self.subTest(case=case):
                self.assertRefused(member)
        self.assertEqual(os.stat(self.outside).st_mode, mode_before)

    def test_contained_hardlink_is_extracted(self):
        extract_layer(self.archive(self.entry("usr/bin/a", data=b"a"),
                                   self.entry("usr/bin/b", kind=tarfile.LNKTYPE, linkname="usr/bin/a")), self.root)
        self.assertEqual((self.root / "usr/bin/b").read_bytes(), b"a")

    def test_filter_callable_matches_tarfile_signature(self):
        member = tarfile.TarInfo("etc/hostname")
        self.assertIs(rootfs_member_filter(self.root)(member, str(self.root)), member)
        with self.assertRaises(tarfile.FilterError):
            rootfs_member_filter(self.root)(tarfile.TarInfo(""), str(self.root))

    def test_symlink_member_whose_last_component_is_dot_or_dotdot_is_refused_by_filter(self):
        # Calls the filter itself, so the result does not depend on whether this
        # Python's tarfile re-filters its link fallback (CVE-2025-4138).
        check = rootfs_member_filter(self.root)
        for name in ("p/..", "p/../", "p/.", "a/b/..", ".", "./"):
            with self.subTest(name=name):
                member = tarfile.TarInfo(name)
                member.type, member.linkname = tarfile.SYMTYPE, "../d"
                with self.assertRaises(tarfile.FilterError):
                    check(member, str(self.root))

    @unittest.skipUnless(_symlinks_supported(), "symlink creation unavailable on this host")
    def test_dotdot_symlink_through_self_link_cannot_touch_directory_above_root(self):
        # p -> . then p/.. -> ../d: the parent p resolves to root, so a
        # parent-only check alone would pass; the link path itself is the
        # directory above root, which an unfiltered link fallback would chmod/chown.
        above = self.root.parent
        mode_before = os.stat(above).st_mode
        self.assertRefused(self.entry("p", kind=tarfile.SYMTYPE, linkname="."),
                           self.entry("d", kind=tarfile.DIRTYPE, mode=0o777, uid=4242, gid=4242),
                           self.entry("p/..", kind=tarfile.SYMTYPE, linkname="../d"))
        self.assertEqual(os.stat(above).st_mode, mode_before)
        self.assertTrue(above.is_dir() and not above.is_symlink())

    @unittest.skipUnless(_symlinks_supported(), "symlink creation unavailable on this host")
    def test_existing_contained_symlink_can_still_be_replaced(self):
        extract_layer(self.archive(self.entry("x", kind=tarfile.SYMTYPE, linkname="/first"),
                                   self.entry("x", kind=tarfile.SYMTYPE, linkname="/second")), self.root)
        self.assertEqual(os.readlink(self.root / "x"), "/second")

    def test_extraction_refused_without_link_fallback_refilter(self):
        archive = self.archive(self.entry("etc/hostname", data=b"x"))
        saved = tarfile.LinkFallbackError
        del tarfile.LinkFallbackError
        try:
            with self.assertRaises(RuntimeError):
                extract_layer(archive, self.root)
            destination = self.tmp / "fresh-rootfs"
            with mock.patch.object(fetch_debian_rootfs, "fetch", side_effect=AssertionError("download attempted")),                     mock.patch("sys.argv", ["fetch_debian_rootfs.py", str(destination)]):
                with self.assertRaises(SystemExit):
                    fetch_debian_rootfs.main()
            self.assertFalse(destination.exists())
        finally:
            tarfile.LinkFallbackError = saved
        self.assertEqual(list(self.root.iterdir()), [])
        extract_layer(archive, self.root)  # positive control with the re-filter present
        self.assertEqual((self.root / "etc/hostname").read_bytes(), b"x")


class RecordedEvidenceConsistencyTests(unittest.TestCase):
    """Read-only cross-check: the report must cite the LinuxCNC run actually on disk."""

    def test_report_cites_current_simulation_evidence(self):
        repo = Path(__file__).resolve().parents[1]
        evidence = repo / "controller_backend/evidence"
        run = json.loads((evidence / "linuxcnc-simulation.json").read_text())
        report = (repo / "reports/LINUXCNC_INTEGRATION.md").read_text(encoding="utf-8")
        self.assertIs(run["success"], True)
        self.assertTrue(all(check["passed"] for check in run["checks"]))
        current = report[report.index("The current evidence is run ID"):]
        current = current[:current.index("Historical runs")]
        self.assertIn("`" + run["run_id"] + "`", current)
        self.assertIn(run["utc"][:19] + "Z", current)
        self.assertIn("**%d passing checks**" % len(run["checks"]), current)
        self.assertIn("**{:,} status samples**".format(run["trace_samples"]), current)
        self.assertEqual(len(json.loads((evidence / "linuxcnc-trace.json").read_text())), run["trace_samples"])
        attach = run["checks"][0]
        self.assertEqual(attach["name"], "attached_exact_simulation_profile")
        self.assertIn("reported_ini_filename", attach)
        log_path = evidence / "linuxcnc-raw.log"
        if not log_path.exists():  # git-ignored; present in the recording workspace
            return
        log = log_path.read_text()
        summary = [line for line in log.splitlines() if line.startswith("task:") and "cycles" in line][-1]
        maximum = summary.split("max=")[1].split(",")[0]
        excursions = summary.split("avg=")[1].split(", ")[1].split(" ")[0]
        self.assertIn("In run `%s`" % run["run_id"][:8], report)
        self.assertIn("logged %s excursions" % excursions, report)
        self.assertIn("maximum was %s s" % maximum, report)


if __name__ == "__main__":
    unittest.main()
