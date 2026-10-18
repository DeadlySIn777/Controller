"""Real Zstd/temp-file recovery, retention, fault coverage and process locking."""
from copy import deepcopy
import base64
import hashlib
import json
import multiprocessing
import os
import random
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from controller_config.diagnostic_explanations import example_fault
from controller_config.diagnostic_recorder import DiagnosticRecorder, RecorderError
from controller_config.package_archive import ArchiveError, capabilities, compress_bytes, decompress_bytes, read_archive
from controller_config.service import atomic_write, canonical, _seal, _verify_seal


def record(index, *, seconds=None, source="fixture", kind="sample", data=None):
    return {"schema_version": 1, "simulation_only": True, "timestamp_ns": (index if seconds is None else seconds)*10**9,
            "source": source, "sequence": index, "kind": kind, "data": deepcopy(data if data is not None else {"observations": []})}


def concurrent_append(directory, source, start, results):
    recorder = DiagnosticRecorder(directory)
    start.wait(10)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            result = recorder.append(record(0, source=source))
            results.put((source, result["accepted"]))
            return
        except RecorderError as error:
            if error.code != "RECORDER_BUSY":
                results.put((source, error.code))
                return
            time.sleep(.01)
    results.put((source, "timeout"))


@unittest.skipUnless(capabilities()["available"], "Optional stdlib Zstd backend unavailable")
class RecorderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / "recorder"
        self.recorder = DiagnosticRecorder(self.directory, pre_fault_seconds=3, post_fault_seconds=2)

    def error(self, code, fn, *args, **kwargs):
        with self.assertRaises(RecorderError) as caught:
            fn(*args, **kwargs)
        self.assertEqual(caught.exception.code, code, str(caught.exception))

    def manifest(self):
        return _verify_seal(json.loads(self.recorder.path.read_text()), "TEST")

    def test_absent_constructor_status_report_close_do_not_write(self):
        self.assertFalse(self.recorder.status()["initialized"])
        self.assertEqual(self.recorder.report()["records"], [])
        self.recorder.close()
        self.assertFalse(self.directory.exists())
        self.directory.mkdir()
        self.recorder.status(); self.recorder.report()
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_real_compressed_chunks_and_exact_fault_observations(self):
        self.recorder.append(record(0))
        fault = record(1, kind="fault", data=example_fault())
        result = self.recorder.capture_fault(fault)
        report = self.recorder.report(result["incident_id"])
        self.assertEqual(report["fault_record"], fault)
        self.assertEqual(report["fault_record"]["data"]["machine_response"], [])
        self.assertEqual(report["machine_commands"], [])
        state = self.manifest()
        chunk = state["chunks"][0]
        frame = (self.directory / chunk["name"]).read_bytes()
        self.assertEqual(frame[:4], b"\x28\xb5\x2f\xfd")
        raw = decompress_bytes(frame, max_output_bytes=65_536)
        self.assertEqual([json.loads(line) for line in raw.splitlines()], [record(0), fault])
        self.assertLess(len(frame), len(raw))

    def test_pre_post_windows_only_complete_after_observed_history_and_restart(self):
        for i in range(3): self.recorder.append(record(i))
        incident = self.recorder.capture_fault(record(3, kind="fault", data=example_fault()))["incident_id"]
        report = self.recorder.report(incident)
        self.assertTrue(report["window"]["pre_complete"])
        self.assertFalse(report["window"]["post_complete"])
        reopened = DiagnosticRecorder(self.directory)  # Retains the stored 3/2 settings.
        reopened.append(record(4)); reopened.append(record(5))
        window = reopened.report()["window"]
        self.assertTrue(window["pre_complete"] and window["post_complete"])
        self.assertEqual(window["post_observed_seconds"], 2)
        before = self.recorder.path.read_bytes()
        reopened.report(); reopened.status(); reopened.flush()
        self.assertEqual(self.recorder.path.read_bytes(), before)

    def test_fault_on_startup_has_no_invented_pre_history(self):
        self.recorder.capture_fault(record(0, kind="fault", data=example_fault()))
        self.assertEqual(self.recorder.report()["window"]["pre_observed_seconds"], 0)
        self.assertFalse(self.recorder.report()["window"]["pre_complete"])

    def test_timestamp_and_sequence_gaps_prevent_complete_coverage(self):
        self.recorder.append(record(0))
        self.recorder.append(record(2))
        self.recorder.capture_fault(record(3, kind="fault", data=example_fault()))
        self.recorder.append(record(4)); self.recorder.append(record(5))
        window = self.recorder.report()["window"]
        self.assertFalse(window["pre_complete"])
        self.assertTrue(window["post_complete"])
        self.assertTrue(any(g["reason"] == "source_sequence_gap" for g in window["gaps"]))

    def test_replay_is_idempotent_and_conflict_time_regression_preserve_state(self):
        value = record(0)
        first = self.recorder.append(value)
        before = self.recorder.path.read_bytes()
        self.assertTrue(self.recorder.append(value)["replayed"])
        self.assertEqual(self.recorder.path.read_bytes(), before)
        self.error("RECORDER_SEQUENCE", self.recorder.append, record(0, data={"changed": True}))
        self.recorder.append(record(1))
        self.error("RECORDER_TIME", self.recorder.append, record(2, seconds=0))
        self.assertEqual(self.recorder.status()["record_count"], 2)

    def test_pinned_fault_quota_drops_explicitly_without_false_post_window(self):
        r = DiagnosticRecorder(self.directory, pre_fault_seconds=3, post_fault_seconds=2, max_chunks=1, chunk_records=1)
        r.capture_fault(record(0, kind="fault", data=example_fault()))
        self.assertFalse(r.append(record(1))["accepted"])
        self.assertFalse(r.append(record(2))["accepted"])
        self.assertEqual(r.status()["dropped_records"], 2)
        self.assertFalse(r.report()["window"]["post_complete"])
        self.assertEqual(r.report()["record_count"], 1)
        self.assertTrue(r.append(record(2))["replayed"])
        self.assertEqual(r.status()["dropped_records"], 2)

    def test_rolling_retention_and_bounded_incidents(self):
        r = DiagnosticRecorder(self.directory, pre_fault_seconds=1, post_fault_seconds=0, max_chunks=3, chunk_records=1, max_incidents=1)
        first = r.capture_fault(record(0, kind="fault", data=example_fault()))["incident_id"]
        for i in range(1, 4): r.append(record(i))
        second = r.capture_fault(record(4, kind="fault", data=example_fault()))["incident_id"]
        self.assertEqual(r.status()["incident_count"], 1)
        self.assertEqual(r.report()["incident_id"], second)
        self.error("RECORDER_INCIDENT", r.report, first)
        self.assertLessEqual(r.status()["chunk_count"], 3)
        self.assertGreater(r.status()["retired_records"], 0)

    def test_compressed_byte_quota_bounds_incompressible_fault_history(self):
        r = DiagnosticRecorder(self.directory, pre_fault_seconds=0, post_fault_seconds=30,
                               max_storage_bytes=131_072, chunk_records=1)
        r.capture_fault(record(0, kind="fault", data=example_fault()))
        random_source = random.Random(147)
        outcomes = []
        for i in range(1, 14):
            text = base64.b64encode(random_source.randbytes(9000)).decode("ascii")
            outcomes.append(r.append(record(i, data={"opaque_fixture_bytes":text}))["accepted"])
            status = r.status()
            self.assertLessEqual(status["compressed_bytes"] + status["manifest_allowance_bytes"], status["quota_bytes"])
            self.assertLessEqual(sum(p.stat().st_size for p in self.directory.iterdir()), status["quota_bytes"])
        self.assertIn(False, outcomes)
        self.assertTrue(any(outcomes))
        self.assertGreater(r.status()["dropped_records"], 0)
        self.assertFalse(r.report()["window"]["post_complete"])

    def test_failed_manifest_commit_leaves_read_only_orphan_then_recovers(self):
        self.recorder.append(record(0))
        with patch("controller_config.diagnostic_recorder.atomic_write", side_effect=OSError("fixture interrupted write")):
            self.error("RECORDER_IO", self.recorder.append, record(1))
        state = self.recorder.status()
        self.assertEqual(state["record_count"], 1)
        self.assertEqual(state["orphan_chunks_pending_recovery"], 1)
        before = sorted(p.name for p in self.directory.iterdir())
        self.recorder.report()
        self.assertEqual(sorted(p.name for p in self.directory.iterdir()), before)
        self.recorder.append(record(1))
        self.assertEqual(self.recorder.status()["recovered_orphan_chunks"], 1)
        self.assertEqual(self.recorder.status()["record_count"], 2)

    def test_first_record_commit_failure_keeps_recoverable_empty_identity(self):
        from controller_config import diagnostic_recorder as module
        original = module.atomic_write
        calls = 0
        def fail_record_commit(path, value):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("first record manifest interrupted")
            return original(path, value)
        with patch.object(module, "atomic_write", side_effect=fail_record_commit):
            self.error("RECORDER_IO", self.recorder.append, record(0))
        status = self.recorder.status()
        self.assertTrue(status["initialized"])
        self.assertEqual(status["record_count"], 0)
        self.assertEqual(status["orphan_chunks_pending_recovery"], 1)
        result = self.recorder.append(record(0))
        self.assertTrue(result["accepted"])
        self.assertEqual(self.recorder.report()["records"], [record(0)])
        self.assertEqual(result["status"]["recovered_orphan_chunks"], 1)

    def test_first_empty_identity_write_failure_can_be_retried(self):
        with patch("controller_config.diagnostic_recorder.atomic_write", side_effect=OSError("initial write interrupted")):
            self.error("RECORDER_IO", self.recorder.append, record(0))
        self.assertFalse(self.recorder.status()["initialized"])
        self.assertTrue(self.recorder.append(record(0))["accepted"])

    def test_process_death_before_manifest_replace_recovers_owned_transaction(self):
        self.recorder.append(record(0))
        code = ("from controller_config import diagnostic_recorder as m; import os,sys; "
                "m._replace=lambda *args: os._exit(19); "
                "m.DiagnosticRecorder(sys.argv[1]).append("
                + repr(record(1)) + ")")
        result = subprocess.run([sys.executable, "-B", "-c", code, str(self.directory)], capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 19, result.stderr)
        before = {p.name: p.read_bytes() for p in self.directory.iterdir()}
        status = self.recorder.status()
        self.assertEqual(status["record_count"], 1)
        self.assertEqual(status["orphan_chunks_pending_recovery"], 1)
        self.assertEqual(status["interrupted_manifests_pending_recovery"], 1)
        self.recorder.report()
        self.assertEqual({p.name: p.read_bytes() for p in self.directory.iterdir()}, before)
        self.assertTrue(self.recorder.append(record(1))["accepted"])
        status = self.recorder.status()
        self.assertEqual(status["record_count"], 2)
        self.assertEqual(status["recovered_orphan_chunks"], 1)
        self.assertEqual(status["interrupted_manifests_pending_recovery"], 0)

    def test_process_death_during_empty_initialization_recovers_only_on_append(self):
        code = ("from controller_config import diagnostic_recorder as m; import os,sys; "
                "m._replace=lambda *args: os._exit(21); "
                "m.DiagnosticRecorder(sys.argv[1]).append(" + repr(record(0)) + ")")
        result = subprocess.run([sys.executable, "-B", "-c", code, str(self.directory)], capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 21, result.stderr)
        before = {p.name: p.read_bytes() for p in self.directory.iterdir()}
        self.assertFalse(self.recorder.path.exists())
        self.error("RECORDER_FOREIGN", self.recorder.status)
        self.assertEqual({p.name: p.read_bytes() for p in self.directory.iterdir()}, before)
        self.assertTrue(self.recorder.append(record(0))["accepted"])
        self.assertEqual(self.recorder.report()["records"], [record(0)])
        self.assertEqual(self.recorder.status()["interrupted_manifests_pending_recovery"], 0)

    def test_partial_initial_transaction_is_preserved_without_inventing_state(self):
        self.directory.mkdir()
        partial = self.directory / ("recorder-txn-" + "0"*32 + "-" + "1"*32 + ".tmp")
        partial.write_bytes(b'{"store_id":')
        self.error("RECORDER_FOREIGN", self.recorder.append, record(0))
        self.assertEqual(partial.read_bytes(), b'{"store_id":')
        self.assertFalse(self.recorder.path.exists())

    def test_pre_fault_gap_ending_at_fault_does_not_contaminate_post_window(self):
        self.recorder.append(record(0))
        self.recorder.capture_fault(record(1, seconds=3, kind="fault", data=example_fault()))
        self.recorder.append(record(2, seconds=4))
        self.recorder.append(record(3, seconds=5))
        window = self.recorder.report()["window"]
        self.assertFalse(window["pre_complete"])
        self.assertTrue(window["post_complete"])

    def test_post_fault_gap_starting_at_fault_does_not_contaminate_pre_window(self):
        for index in range(3):
            self.recorder.append(record(index))
        self.recorder.capture_fault(record(3, kind="fault", data=example_fault()))
        self.recorder.append(record(4, seconds=5))
        window = self.recorder.report()["window"]
        self.assertTrue(window["pre_complete"])
        self.assertFalse(window["post_complete"])

    def test_zero_requested_window_does_not_require_external_history(self):
        recorder = DiagnosticRecorder(self.directory, pre_fault_seconds=0, post_fault_seconds=0)
        recorder.append(record(0))
        recorder.capture_fault(record(2, seconds=3, kind="fault", data=example_fault()))
        window = recorder.report()["window"]
        self.assertTrue(window["pre_complete"])
        self.assertTrue(window["post_complete"])

    def test_last_record_acknowledgment_cannot_disagree_with_retained_bytes(self):
        self.recorder.append(record(0))
        original = self.manifest()
        for changes in ({"record_sha256": "0"*64}, {"timestamp_ns": 1}, {"accepted": False}):
            state = deepcopy(original)
            state["sources"]["fixture"].update(changes)
            atomic_write(self.recorder.path, _seal(state))
            before = self.recorder.path.read_bytes()
            self.error("RECORDER_CORRUPT", self.recorder.status)
            self.assertEqual(self.recorder.path.read_bytes(), before)

    def test_oversized_manifest_and_foreign_lock_are_preserved(self):
        self.recorder.append(record(0))
        self.recorder.path.write_bytes(b"x"*65537)
        self.error("RECORDER_CORRUPT", self.recorder.status)
        self.assertEqual(self.recorder.path.stat().st_size, 65537)
        self.recorder.lock_path.write_bytes(b"user owned lock")
        self.error("RECORDER_CORRUPT", self.recorder.status)
        self.assertEqual(self.recorder.lock_path.read_bytes(), b"user owned lock")

    def test_hardlinked_empty_lock_cannot_modify_a_user_source_file(self):
        self.directory.mkdir()
        source = Path(self.temp.name) / "empty-user-file"
        source.write_bytes(b"")
        os.link(source, self.recorder.lock_path)
        self.error("RECORDER_CORRUPT", self.recorder.append, record(0))
        self.assertEqual(source.read_bytes(), b"")
        self.assertEqual(self.recorder.lock_path.read_bytes(), b"")
        self.assertFalse(self.recorder.path.exists())

    def test_held_empty_lock_is_busy_and_never_initialized_by_competitor(self):
        self.directory.mkdir()
        self.recorder.lock_path.write_bytes(b"")
        descriptor = os.open(self.recorder.lock_path, os.O_RDWR)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.error("RECORDER_BUSY", self.recorder.append, record(0))
            self.assertEqual(self.recorder.lock_path.stat().st_size, 0)
            self.assertFalse(self.recorder.path.exists())
        finally:
            os.close(descriptor)
        self.assertTrue(self.recorder.append(record(0))["accepted"])

    def test_os_unlock_error_never_leaks_host_mutex_or_unstructured_exception(self):
        self.recorder.append(record(0))
        if os.name == "nt":
            import msvcrt
            original = msvcrt.locking
            def unlock_failure(handle, mode, count):
                if mode == msvcrt.LK_UNLCK:
                    raise OSError("interrupted unlock fixture")
                return original(handle, mode, count)
            with patch.object(msvcrt, "locking", side_effect=unlock_failure):
                self.error("RECORDER_IO", self.recorder.status)
        else:
            import fcntl
            original = fcntl.flock
            def unlock_failure(handle, mode):
                if mode == fcntl.LOCK_UN:
                    raise OSError("interrupted unlock fixture")
                return original(handle, mode)
            with patch.object(fcntl, "flock", side_effect=unlock_failure):
                self.error("RECORDER_IO", self.recorder.status)
        self.assertEqual(self.recorder.status()["record_count"], 1)
        self.assertTrue(self.recorder.append(record(1))["accepted"])

    def test_foreign_transaction_identity_is_not_reclaimed(self):
        self.recorder.append(record(0))
        foreign = self.directory / ("recorder-txn-" + "0"*32 + "-" + "1"*32 + ".tmp")
        foreign.write_bytes(b"preserve other store")
        self.error("RECORDER_FOREIGN", self.recorder.append, record(1))
        self.assertEqual(foreign.read_bytes(), b"preserve other store")

    def test_lost_manifest_ack_replay_keeps_one_record_and_reclaims_old_chunk(self):
        self.recorder.append(record(0))
        def write_then_lose_ack(path, value):
            atomic_write(path, value)
            raise OSError("fixture lost acknowledgment")
        with patch("controller_config.diagnostic_recorder.atomic_write", side_effect=write_then_lose_ack):
            self.error("RECORDER_IO", self.recorder.append, record(1))
        self.assertEqual(self.recorder.status()["record_count"], 2)
        result = self.recorder.append(record(1))
        self.assertTrue(result["replayed"])
        self.assertEqual(self.recorder.status()["record_count"], 2)
        self.assertEqual(self.recorder.status()["orphan_chunks_pending_recovery"], 0)
        self.assertEqual(self.recorder.status()["recovered_orphan_chunks"], 1)

    def test_changed_compressed_chunk_fails_closed_and_preserves_bytes(self):
        self.recorder.append(record(0))
        path = self.directory / self.manifest()["chunks"][0]["name"]
        raw = path.read_bytes(); path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
        before = path.read_bytes()
        self.error("RECORDER_CORRUPT", self.recorder.status)
        self.error("RECORDER_CORRUPT", self.recorder.append, record(1))
        self.assertEqual(path.read_bytes(), before)

    def test_missing_and_truncated_records_fail_closed(self):
        self.recorder.append(record(0))
        state = self.manifest(); chunk = state["chunks"][0]
        raw = b'{"schema_version":1\n'; frame = compress_bytes(raw)
        (self.directory / chunk["name"]).write_bytes(frame)
        chunk.update(sha256=hashlib.sha256(frame).hexdigest(), raw_sha256=hashlib.sha256(raw).hexdigest(), raw_bytes=len(raw), compressed_bytes=len(frame))
        atomic_write(self.recorder.path, _seal(state))
        self.error("RECORDER_CORRUPT", self.recorder.report)
        (self.directory / chunk["name"]).unlink()
        self.error("RECORDER_CORRUPT", self.recorder.status)

    def test_sealed_semantic_manifest_corruption_is_not_trusted(self):
        self.recorder.append(record(0))
        original = self.manifest()
        for mutate in (lambda x: x["options"].update(pre_fault_ns=10**1000),
                       lambda x: x.update(schema_version=True),
                       lambda x: x["sources"]["fixture"].update(accepted="yes"),
                       lambda x: x.update(gaps=[{"source":"fixture","start_ns":2,"end_ns":1,"reason":"timestamp_gap"}])):
            state = deepcopy(original); mutate(state)
            atomic_write(self.recorder.path, _seal(state))
            self.error("RECORDER_CORRUPT", self.recorder.status)

    def test_invalid_records_do_not_create_storage(self):
        variants = [dict(record(0), simulation_only=False), dict(record(0), timestamp_ns=True),
                    dict(record(0), kind="command"), dict(record(0), data={"bad": float("nan")}),
                    dict(record(0), data={"bad": 10**1000}), dict(record(0), unexpected=True)]
        for value in variants:
            self.error("RECORDER_RECORD", self.recorder.append, value)
        self.error("RECORDER_RECORD_SIZE", self.recorder.append, record(0, data={"text":"x"*20_000}))
        self.assertFalse(self.directory.exists())

    def test_excessive_record_nesting_is_rejected_before_recursive_copy(self):
        nested = {}
        for _ in range(1000):
            nested = {"nested": nested}
        value = record(0)
        value["data"] = nested
        self.error("RECORDER_RECORD", self.recorder.append, value)
        self.assertFalse(self.directory.exists())

    def test_existing_foreign_files_are_preserved(self):
        self.directory.mkdir()
        foreign = self.directory / "user-data.txt"; foreign.write_text("keep")
        self.error("RECORDER_FOREIGN", self.recorder.status)
        self.error("RECORDER_FOREIGN", self.recorder.append, record(0))
        self.assertEqual(foreign.read_text(), "keep")
        self.assertFalse(self.recorder.path.exists())

    def test_unavailable_codec_is_distinct_from_corrupt_recording(self):
        self.recorder.append(record(0))
        before = {p.name:p.read_bytes() for p in self.directory.iterdir()}
        with patch("controller_config.package_archive._zstd", None):
            with self.assertRaises(ArchiveError) as caught:
                self.recorder.status()
            self.assertEqual(caught.exception.code, "ARCHIVE_UNAVAILABLE")
        self.assertEqual({p.name:p.read_bytes() for p in self.directory.iterdir()}, before)

    def test_export_is_inert_verified_support_and_never_overwrites(self):
        self.recorder.capture_fault(record(0, kind="fault", data=example_fault()))
        target = Path(self.temp.name) / "support.tar.zst"
        config = {"simulation_only": True, "machine_name": "fixture"}
        self.recorder.export(target, configuration=config)
        archive = read_archive(target, expected_kind="support")
        report = json.loads(archive["entries"]["report.json"])
        self.assertEqual(report["records"], self.recorder.report()["records"])
        self.assertEqual(json.loads(archive["entries"]["configuration.json"]), config)
        before = target.read_bytes()
        with self.assertRaises(ArchiveError): self.recorder.export(target)
        self.assertEqual(target.read_bytes(), before)
        self.assertFalse(report["executed"])

    def test_separate_process_writers_do_not_lose_records(self):
        self.recorder.append(record(0, source="initial"))
        context = multiprocessing.get_context("spawn")
        start, results = context.Event(), context.Queue()
        processes = [context.Process(target=concurrent_append, args=(str(self.directory), f"writer{i}", start, results)) for i in range(4)]
        for process in processes: process.start()
        start.set()
        values = [results.get(timeout=15) for _ in processes]
        for process in processes:
            process.join(15)
            self.assertEqual(process.exitcode, 0)
        self.assertTrue(all(value is True for _, value in values), values)
        self.assertEqual(self.recorder.status()["record_count"], 5)
        self.assertEqual(len({r["source"] for r in self.recorder.report()["records"]}), 5)

    def test_process_death_releases_os_lock_without_deleting_lockfile(self):
        self.recorder.append(record(0))
        code = "from controller_config.diagnostic_recorder import DiagnosticRecorder; import os,sys; r=DiagnosticRecorder(sys.argv[1]); c=r._lock(); c.__enter__(); os._exit(0)"
        result = subprocess.run([sys.executable, "-B", "-c", code, str(self.directory)], capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.recorder.lock_path.exists())
        self.assertTrue(self.recorder.append(record(1))["accepted"])


if __name__ == "__main__":
    unittest.main()
