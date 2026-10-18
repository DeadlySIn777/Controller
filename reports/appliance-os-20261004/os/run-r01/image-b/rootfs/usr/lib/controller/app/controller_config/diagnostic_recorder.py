"""Bounded synchronous host recorder for disconnected simulation observations.

Compression and file I/O are not real-time safe and must not run in a motion loop.
Producer timestamps describe a simulation timeline, never measured physical time.
Immutable checksummed Zstd chunks precede an atomic manifest commit. No transport,
machine action, inferred stop state, or automatic external upload exists here.
"""
from contextlib import contextmanager
from copy import deepcopy
import errno
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import threading
import uuid

from .model import ConfigurationError
from .service import canonical, digest, _replace, _seal, _verify_seal, _unique_pairs


MAX_RECORD_BYTES = 16_384
MANIFEST_ALLOWANCE = 65_536
MAX_COUNTER = 2**63 - 1
GUARDS = {"simulation_only": True, "executed": False, "machine_commands": [],
          "physical_evidence": False, "real_time_safe": False}
_HOST_LOCK = threading.Lock()


class RecorderError(ConfigurationError):
    pass


def _require(condition, code, message):
    if not condition:
        raise RecorderError(code, message)


def _integer(value, low=0, high=MAX_COUNTER):
    return type(value) is int and low <= value <= high


def _hash(raw):
    return hashlib.sha256(raw).hexdigest()


def _read_regular(path, limit):
    """Bound allocation and reject symlinks/replacement while opening evidence."""
    before = path.lstat()
    _require(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= limit,
             "RECORDER_CORRUPT", "Recorder entry is not a bounded regular file")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) |
                         getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        _require(stat.S_ISREG(opened.st_mode) and
                 (before.st_dev, before.st_ino, before.st_size) == (opened.st_dev, opened.st_ino, opened.st_size),
                 "RECORDER_CORRUPT", "Recorder entry changed while opening")
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    _require(len(raw) == before.st_size and len(raw) <= limit and after.st_size == before.st_size,
             "RECORDER_CORRUPT", "Recorder entry changed size while reading")
    return raw


def atomic_write(path, value):
    """Recorder-owned transaction names allow recovery after process death.

    Windows file flush/atomic replacement remains host evidence only; actual
    target filesystem/media power-loss behavior requires physical qualification.
    """
    path = Path(path)
    raw = canonical(value) + b"\n"
    _require(len(raw) <= MANIFEST_ALLOWANCE, "RECORDER_METADATA_LIMIT", "Recorder metadata allowance exhausted")
    temporary = path.parent / f"recorder-txn-{value['store_id']}-{uuid.uuid4().hex}.tmp"
    try:
        with temporary.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        _replace(temporary, path)
        if os.name != "nt":
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def _json_tree(value, depth=0):
    _require(depth <= 12, "RECORDER_RECORD", "Record nesting is too deep")
    if type(value) is str:
        _require(len(value) <= MAX_RECORD_BYTES, "RECORDER_RECORD_SIZE", "Observation text exceeds the record byte budget")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        _require(-MAX_COUNTER <= value <= MAX_COUNTER, "RECORDER_RECORD", "Integer observation exceeds the bounded JSON range")
    elif type(value) is float:
        _require(math.isfinite(value), "RECORDER_RECORD", "Observation must be finite")
    elif type(value) is list:
        _require(len(value) <= 256, "RECORDER_RECORD", "Observation list is too long")
        for item in value:
            _json_tree(item, depth + 1)
    elif type(value) is dict:
        _require(len(value) <= 128 and all(type(k) is str and 0 < len(k) <= 128 for k in value), "RECORDER_RECORD", "Observation object keys are invalid")
        for item in value.values():
            _json_tree(item, depth + 1)
    else:
        raise RecorderError("RECORDER_RECORD", "Only bounded finite JSON observations are supported")


def _record(value):
    _require(type(value) is dict and set(value) == {"schema_version", "simulation_only", "timestamp_ns", "source", "sequence", "kind", "data"}, "RECORDER_RECORD", "Expected the exact simulation record envelope")
    _require(type(value["schema_version"]) is int and value["schema_version"] == 1 and value["simulation_only"] is True, "RECORDER_RECORD", "Explicit simulation schema version 1 is required")
    _require(_integer(value["timestamp_ns"]) and _integer(value["sequence"]), "RECORDER_RECORD", "Timestamp and sequence must be bounded nonnegative integers")
    _require(type(value["source"]) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}", value["source"]), "RECORDER_RECORD", "Source needs a stable bounded identifier")
    _require(value["kind"] in ("sample", "event", "fault") and type(value["data"]) is dict, "RECORDER_RECORD", "Record kind or data object is invalid")
    _json_tree(value["data"])
    try:
        raw = canonical(value) + b"\n"
    except (ValueError, TypeError, UnicodeError, RecursionError) as error:
        raise RecorderError("RECORDER_RECORD", "Record cannot be represented as bounded UTF-8 JSON") from error
    _require(len(raw) <= MAX_RECORD_BYTES, "RECORDER_RECORD_SIZE", "Record exceeds 16 KiB")
    return raw


class DiagnosticRecorder:
    """Explicit append initializes; construction and absent status/report do not write.

    Stored settings are authoritative when reopening. Quota includes a reserved
    64 KiB manifest allowance. Atomic updates may transiently add one chunk;
    recognized abandoned chunks are reported and reclaimed by the next writer.
    Locks coordinate processes on one host, not synchronized multi-host copies.
    """
    def __init__(self, directory, *, pre_fault_seconds=300, post_fault_seconds=30,
                 max_gap_seconds=1, max_storage_bytes=8*1024*1024,
                 max_chunks=96, chunk_records=128, chunk_bytes=65_536,
                 max_incidents=8):
        self.directory = Path(directory).expanduser().resolve()
        self.path = self.directory / "recorder.json"
        self.lock_path = self.directory / "recorder.lock"
        values = (pre_fault_seconds, post_fault_seconds, max_gap_seconds)
        _require(all(type(v) in (int, float) and 0 <= v <= 3600 and (type(v) is int or math.isfinite(v)) for v in values) and max_gap_seconds > 0, "RECORDER_OPTIONS", "Time windows must be finite, bounded seconds with a positive gap limit")
        _require(_integer(max_storage_bytes, 131_072, 64*1024*1024) and _integer(max_chunks, 1, 96) and _integer(chunk_records, 1, 1024) and _integer(chunk_bytes, MAX_RECORD_BYTES, 65_536) and _integer(max_incidents, 1, 8), "RECORDER_OPTIONS", "Storage/chunk limits exceed supported bounds")
        self.options = {"pre_fault_ns": round(pre_fault_seconds*1e9), "post_fault_ns": round(post_fault_seconds*1e9), "max_gap_ns": max(1, round(max_gap_seconds*1e9)), "max_storage_bytes": max_storage_bytes, "max_chunks": max_chunks, "chunk_records": chunk_records, "chunk_bytes": chunk_bytes, "max_incidents": max_incidents}

    @staticmethod
    def schema():
        return {"schema_version": 1, "required": ["schema_version", "simulation_only", "timestamp_ns", "source", "sequence", "kind", "data"], "additional_fields": False,
                "timestamp_ns": "nonnegative caller-declared simulation monotonic nanoseconds; not wall-clock evidence",
                "source": "stable ASCII identifier, maximum 64 characters", "sequence": "monotonic per source; exact last-record retries are idempotent",
                "kind": ["sample", "event", "fault"], "data": "finite bounded JSON object; fault explanation record may be embedded verbatim",
                "maximum_record_bytes": MAX_RECORD_BYTES, "freshness": "never inferred; retain explicit validity/freshness/age in observations", **deepcopy(GUARDS)}

    @contextmanager
    def _lock(self, write=False):
        _require(_HOST_LOCK.acquire(blocking=False), "RECORDER_BUSY", "Another host recorder operation is in progress; retry deliberately")
        handle, acquired = None, False
        try:
            if write:
                self.directory.mkdir(parents=True, exist_ok=True)
            try:
                before = self.lock_path.lstat()
                _require(stat.S_ISREG(before.st_mode) and before.st_size <= 1 and before.st_nlink == 1,
                         "RECORDER_CORRUPT", "Recorder lock must be its own singly linked bounded regular file")
            except FileNotFoundError:
                before = None
            flags = os.O_RDWR | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0) | (os.O_CREAT if write else 0)
            handle = os.open(self.lock_path, flags, 0o600)
            opened = os.fstat(handle)
            current = self.lock_path.lstat()
            _require(stat.S_ISREG(current.st_mode) and stat.S_ISREG(opened.st_mode) and
                     (current.st_dev, current.st_ino) == (opened.st_dev, opened.st_ino) and opened.st_size <= 1 and
                     current.st_nlink == opened.st_nlink == 1 and
                     (before is None or (before.st_dev, before.st_ino) == (opened.st_dev, opened.st_ino)),
                     "RECORDER_CORRUPT", "Recorder lock changed while opening")
            os.lseek(handle, 0, os.SEEK_SET)
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except OSError as error:
                if error.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                    raise RecorderError("RECORDER_BUSY", "Another process owns recorder state") from error
                raise
            # Ownership precedes byte initialization: a competing process can
            # hold an empty native lock, which must remain untouched on BUSY.
            if os.fstat(handle).st_size == 0:
                _require(write, "RECORDER_CORRUPT", "Recorder lock file is incomplete")
                os.write(handle, b"\0")
                os.fsync(handle)
            yield
        except RecorderError:
            raise
        except OSError as error:
            raise RecorderError("RECORDER_IO", "Recorder I/O failed; do not assume the last write was acknowledged") from error
        finally:
            try:
                if handle is not None:
                    try:
                        if acquired:
                            os.lseek(handle, 0, os.SEEK_SET)
                            if os.name == "nt":
                                import msvcrt
                                msvcrt.locking(handle, msvcrt.LK_UNLCK, 1)
                            else:
                                import fcntl
                                fcntl.flock(handle, fcntl.LOCK_UN)
                    finally:
                        os.close(handle)
            except OSError as error:
                raise RecorderError("RECORDER_IO", "Recorder lock release failed; verify the committed state before retrying") from error
            finally:
                _HOST_LOCK.release()

    def _empty(self):
        return {"schema_version": 1, "kind": "disconnected-diagnostic-recorder", "store_id": uuid.uuid4().hex,
                "revision": 0, "options": deepcopy(self.options), "chunks": [], "incidents": [], "sources": {},
                "last_timestamp_ns": None, "dropped_records": 0, "retired_records": 0, "expired_incidents": 0,
                "gaps": [], "gap_count": 0, "recovered_orphan_chunks": 0}

    def _absent(self):
        if self.path.exists():
            return False
        if self.directory.exists():
            _require(not any(p.name != "recorder.lock" for p in self.directory.iterdir()), "RECORDER_FOREIGN", "No recorder manifest exists; existing files were preserved")
        return True

    def _read(self, manifest_path=None):
        from .package_archive import ArchiveError, decompress_bytes
        try:
            raw_manifest = _read_regular(self.path if manifest_path is None else manifest_path, MANIFEST_ALLOWANCE)
            state = _verify_seal(json.loads(raw_manifest.decode("utf-8-sig"), object_pairs_hook=_unique_pairs,
                parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite recorder metadata"))), "RECORDER_CORRUPT")
            required = set(self._empty())
            _require(type(state) is dict and set(state) == required and type(state["schema_version"]) is int and state["schema_version"] == 1 and state["kind"] == "disconnected-diagnostic-recorder", "RECORDER_CORRUPT", "Invalid recorder manifest")
            _require(type(state["store_id"]) is str and re.fullmatch(r"[0-9a-f]{32}", state["store_id"]), "RECORDER_CORRUPT", "Invalid recorder identity")
            options = state["options"]
            _require(type(options) is dict and set(options) == set(self.options), "RECORDER_CORRUPT", "Invalid stored recorder options")
            _require(all(_integer(options[k], 0 if k != "max_gap_ns" else 1, 3600*10**9) for k in ("pre_fault_ns", "post_fault_ns", "max_gap_ns")), "RECORDER_CORRUPT", "Invalid stored time windows")
            checked = DiagnosticRecorder(self.directory, pre_fault_seconds=options["pre_fault_ns"]/1e9, post_fault_seconds=options["post_fault_ns"]/1e9, max_gap_seconds=options["max_gap_ns"]/1e9, **{k: options[k] for k in ("max_storage_bytes", "max_chunks", "chunk_records", "chunk_bytes", "max_incidents")})
            _require(checked.options == options, "RECORDER_CORRUPT", "Invalid stored time precision")
            for key in ("revision", "dropped_records", "retired_records", "expired_incidents", "gap_count", "recovered_orphan_chunks"):
                _require(_integer(state[key]), "RECORDER_CORRUPT", "Invalid recorder counter")
            _require(state["last_timestamp_ns"] is None or _integer(state["last_timestamp_ns"]), "RECORDER_CORRUPT", "Invalid recorder timeline")
            _require(type(state["chunks"]) is list and len(state["chunks"]) <= options["max_chunks"] and type(state["incidents"]) is list and len(state["incidents"]) <= options["max_incidents"] and type(state["sources"]) is dict and len(state["sources"]) <= 32 and type(state["gaps"]) is list and len(state["gaps"]) <= 64, "RECORDER_CORRUPT", "Recorder inventory exceeds limits")
            for source, row in state["sources"].items():
                _require(type(source) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}", source) and type(row) is dict and set(row) == {"sequence", "timestamp_ns", "record_sha256", "accepted", "incident_id"}, "RECORDER_CORRUPT", "Invalid source progress record")
                _require(_integer(row["sequence"]) and _integer(row["timestamp_ns"]) and row["timestamp_ns"] <= state["last_timestamp_ns"] and type(row["accepted"]) is bool and type(row["record_sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", row["record_sha256"]) and (row["incident_id"] is None or type(row["incident_id"]) is str and re.fullmatch(r"[0-9a-f]{32}", row["incident_id"])), "RECORDER_CORRUPT", "Invalid source progress bounds")
            for gap in state["gaps"]:
                _require(type(gap) is dict and set(gap) == {"source", "start_ns", "end_ns", "reason"} and gap["source"] in state["sources"] and _integer(gap["start_ns"]) and _integer(gap["end_ns"]) and gap["start_ns"] <= gap["end_ns"] <= state["last_timestamp_ns"] and gap["reason"] in ("source_sequence_gap", "timestamp_gap", "storage_quota_drop"), "RECORDER_CORRUPT", "Invalid retained gap")
            _require(state["gap_count"] >= len(state["gaps"]), "RECORDER_CORRUPT", "Gap accounting disagrees")
            records, decoded, names, previous, source_sequences = [], {}, set(), -1, {}
            for chunk in state["chunks"]:
                _require(type(chunk) is dict and set(chunk) == {"name", "sha256", "raw_sha256", "raw_bytes", "compressed_bytes", "record_count", "first_ns", "last_ns"}, "RECORDER_CORRUPT", "Invalid chunk descriptor")
                name = chunk["name"]
                _require(type(name) is str and re.fullmatch(r"chunk-" + state["store_id"] + r"-[0-9a-f]{32}\.zst", name) and name not in names, "RECORDER_CORRUPT", "Invalid or repeated chunk path")
                names.add(name)
                _require(all(_integer(chunk[k]) for k in ("raw_bytes", "compressed_bytes", "record_count", "first_ns", "last_ns")) and 0 < chunk["raw_bytes"] <= options["chunk_bytes"] and 0 < chunk["record_count"] <= options["chunk_records"] and chunk["compressed_bytes"] <= options["chunk_bytes"] + 1024, "RECORDER_CORRUPT", "Invalid chunk bounds")
                path = self.directory / name
                _require(path.is_file() and not path.is_symlink() and path.stat().st_size == chunk["compressed_bytes"], "RECORDER_CORRUPT", "Chunk missing or changed size")
                raw_frame = _read_regular(path, options["chunk_bytes"] + 1024)
                _require(_hash(raw_frame) == chunk["sha256"], "RECORDER_CORRUPT", "Compressed chunk checksum changed")
                raw = decompress_bytes(raw_frame, max_output_bytes=options["chunk_bytes"])
                _require(len(raw) == chunk["raw_bytes"] and _hash(raw) == chunk["raw_sha256"] and raw.endswith(b"\n"), "RECORDER_CORRUPT", "Chunk payload is truncated or changed")
                rows = [json.loads(line.decode("utf-8"), object_pairs_hook=_unique_pairs) for line in raw.splitlines()]
                _require(len(rows) == chunk["record_count"], "RECORDER_CORRUPT", "Chunk record count changed")
                for record in rows:
                    _record(record)
                    _require(previous <= record["timestamp_ns"] <= state["last_timestamp_ns"], "RECORDER_CORRUPT", "Stored record timeline regressed")
                    _require(record["source"] in state["sources"] and source_sequences.get(record["source"], -1) < record["sequence"] <= state["sources"][record["source"]]["sequence"], "RECORDER_CORRUPT", "Stored source sequence disagrees")
                    source_sequences[record["source"]] = record["sequence"]
                    progress = state["sources"][record["source"]]
                    if record["sequence"] == progress["sequence"]:
                        _require(progress["accepted"] and record["timestamp_ns"] == progress["timestamp_ns"] and
                                 _hash(_record(record)) == progress["record_sha256"],
                                 "RECORDER_CORRUPT", "Last-record acknowledgment disagrees with retained evidence")
                    previous = record["timestamp_ns"]
                _require(rows[0]["timestamp_ns"] == chunk["first_ns"] and rows[-1]["timestamp_ns"] == chunk["last_ns"], "RECORDER_CORRUPT", "Chunk timeline metadata changed")
                decoded[name] = rows
                records.extend(rows)
            incident_ids = set()
            for incident in state["incidents"]:
                _require(type(incident) is dict and set(incident) == {"id", "timestamp_ns", "source", "sequence"} and type(incident["id"]) is str and re.fullmatch(r"[0-9a-f]{32}", incident["id"]) and _integer(incident["timestamp_ns"]) and _integer(incident["sequence"]) and type(incident["source"]) is str, "RECORDER_CORRUPT", "Invalid incident reference")
                _require(any(r["kind"] == "fault" and all(r[k] == incident[k] for k in ("timestamp_ns", "source", "sequence")) for r in records), "RECORDER_CORRUPT", "Incident fault record is absent")
                _require(incident["id"] not in incident_ids, "RECORDER_CORRUPT", "Duplicate incident identity")
                incident_ids.add(incident["id"])
            _require(sum(c["compressed_bytes"] for c in state["chunks"]) + MANIFEST_ALLOWANCE <= options["max_storage_bytes"], "RECORDER_CORRUPT", "Stored chunks exceed quota")
            orphan_paths = []
            for path in self.directory.iterdir():
                if path.name in names or path.name in ("recorder.json", "recorder.lock"):
                    continue
                if re.fullmatch(r"chunk-" + state["store_id"] + r"-[0-9a-f]{32}\.zst", path.name) and path.is_file() and not path.is_symlink():
                    orphan_paths.append(path)
                elif (re.fullmatch(r"recorder-txn-" + state["store_id"] + r"-[0-9a-f]{32}\.tmp", path.name) and
                      path.is_file() and not path.is_symlink() and path.stat().st_size <= MANIFEST_ALLOWANCE):
                    orphan_paths.append(path)
                else:
                    raise RecorderError("RECORDER_FOREIGN", "Unrecognized recorder-directory entry was preserved")
            return state, records, decoded, orphan_paths
        except RecorderError:
            raise
        except ArchiveError as error:
            if error.code == "ARCHIVE_UNAVAILABLE":
                raise
            raise RecorderError("RECORDER_CORRUPT", "Compressed recorder data is invalid; files were preserved") from error
        except (ConfigurationError, KeyError, TypeError, ValueError, UnicodeError, RecursionError, OSError) as error:
            raise RecorderError("RECORDER_CORRUPT", "Recorder manifest/chunk validation failed; data was preserved") from error

    @staticmethod
    def _gap(state, source, start, end, reason):
        state["gap_count"] += 1
        state["gaps"] = (state["gaps"] + [{"source": source, "start_ns": start, "end_ns": end, "reason": reason}])[-64:]

    @staticmethod
    def _pinned(chunk, state):
        o = state["options"]
        return any(chunk["last_ns"] >= i["timestamp_ns"]-o["pre_fault_ns"] and chunk["first_ns"] <= i["timestamp_ns"]+o["post_fault_ns"] for i in state["incidents"])

    def _write(self, state):
        _require(all(_integer(state[k]) for k in ("revision", "dropped_records", "retired_records", "expired_incidents", "gap_count", "recovered_orphan_chunks")), "RECORDER_COUNTER_LIMIT", "Recorder counter exhausted; no wrapping is permitted")
        _require(len(canonical(_seal(state))) + 1 <= MANIFEST_ALLOWANCE, "RECORDER_METADATA_LIMIT", "Recorder metadata allowance exhausted")
        atomic_write(self.path, _seal(state))

    @staticmethod
    def _pending_counts(paths):
        return (sum(path.name.startswith("chunk-") for path in paths),
                sum(path.name.startswith("recorder-txn-") for path in paths))

    def _recover_empty_initialization(self):
        """Adopt only a fully validated empty initial transaction on retry.

        Partial/foreign metadata and transactions containing observations are
        preserved. Read-only operations never perform this adoption.
        """
        if self.path.exists():
            return
        for path in self.directory.iterdir():
            if not re.fullmatch(r"recorder-txn-[0-9a-f]{32}-[0-9a-f]{32}\.tmp", path.name):
                continue
            try:
                state, records, _, _ = self._read(manifest_path=path)
                empty = (not records and not state["sources"] and not state["incidents"] and
                         not state["gaps"] and state["last_timestamp_ns"] is None and
                         all(state[key] == 0 for key in ("revision", "dropped_records", "retired_records",
                             "expired_incidents", "gap_count", "recovered_orphan_chunks")))
                if empty:
                    self._write(state)
                    return
            except RecorderError:
                continue

    def append(self, record):
        from .package_archive import compress_bytes
        # Validate structure before deepcopy: excessively nested JSON must fail
        # with a structured error rather than exhausting deepcopy recursion.
        raw_record = _record(record)
        record = deepcopy(record)
        # Prove the codec is available before creating or changing storage.
        frame_probe = compress_bytes(raw_record, level=3)
        with self._lock(write=True):
            self._recover_empty_initialization()
            absent = self._absent()
            state, records, decoded, orphans = (self._empty(), [], {}, []) if absent else self._read()
            # Establish a recoverable empty identity before publishing a chunk.
            # A failed first record commit must not strand an unowned chunk.
            if absent:
                self._write(state)
            orphan_chunks, interrupted_manifests = self._pending_counts(orphans)
            for orphan in orphans:
                orphan.unlink()
            state["recovered_orphan_chunks"] += orphan_chunks
            options, source, timestamp = state["options"], record["source"], record["timestamp_ns"]
            prior = state["sources"].get(source)
            if prior and record["sequence"] == prior["sequence"]:
                _require(prior["record_sha256"] == _hash(raw_record), "RECORDER_SEQUENCE", "Sequence was already used by different data")
                if orphans:
                    state["revision"] += 1
                    self._write(state)
                return {"accepted": prior["accepted"], "replayed": True, "incident_id": prior["incident_id"], "status": self._status(state), **deepcopy(GUARDS)}
            _require(prior is None or record["sequence"] > prior["sequence"], "RECORDER_SEQUENCE", "Source sequence regressed")
            _require(state["last_timestamp_ns"] is None or timestamp >= state["last_timestamp_ns"], "RECORDER_TIME", "Simulation timestamp regressed; use a separate recorder timeline")
            _require(prior is not None or len(state["sources"]) < 32, "RECORDER_SOURCE_LIMIT", "Recorder source inventory is full")
            if prior:
                if record["sequence"] != prior["sequence"] + 1:
                    self._gap(state, source, prior["timestamp_ns"], timestamp, "source_sequence_gap")
                if timestamp-prior["timestamp_ns"] > options["max_gap_ns"]:
                    self._gap(state, source, prior["timestamp_ns"], timestamp, "timestamp_gap")
            original = deepcopy(state["chunks"])
            chunk_rows = [record]
            if state["chunks"]:
                last = state["chunks"][-1]
                if last["record_count"] < options["chunk_records"] and last["raw_bytes"] + len(raw_record) <= options["chunk_bytes"]:
                    chunk_rows = decoded[last["name"]] + [record]
                    state["chunks"].pop()
            raw = b"".join(_record(r) for r in chunk_rows)
            frame = frame_probe if len(chunk_rows) == 1 else compress_bytes(raw, level=3)
            name = f"chunk-{state['store_id']}-{uuid.uuid4().hex}.zst"
            chunk = {"name": name, "sha256": _hash(frame), "raw_sha256": _hash(raw), "raw_bytes": len(raw), "compressed_bytes": len(frame), "record_count": len(chunk_rows), "first_ns": chunk_rows[0]["timestamp_ns"], "last_ns": timestamp}
            state["chunks"].append(chunk)
            original_incidents = deepcopy(state["incidents"])
            incident_id = uuid.uuid4().hex if record["kind"] == "fault" else None
            if incident_id:
                state["incidents"] = (state["incidents"] + [{"id": incident_id, "timestamp_ns": timestamp, "source": source, "sequence": record["sequence"]}])[-options["max_incidents"]:]
            cutoff = timestamp-options["pre_fault_ns"]
            state["chunks"] = [c for c in state["chunks"] if c["name"] == name or c["last_ns"] >= cutoff or self._pinned(c, state)]
            def over_quota():
                return len(state["chunks"]) > options["max_chunks"] or sum(c["compressed_bytes"] for c in state["chunks"]) + MANIFEST_ALLOWANCE > options["max_storage_bytes"]
            while over_quota():
                victim = next((c for c in state["chunks"] if c["name"] != name and not self._pinned(c, state)), None)
                if victim is None:
                    break
                state["chunks"].remove(victim)
            accepted = not over_quota()
            if not accepted:
                state["chunks"], state["incidents"], incident_id = original, original_incidents, None
                state["dropped_records"] += 1
                self._gap(state, source, timestamp, timestamp, "storage_quota_drop")
            else:
                state["expired_incidents"] += max(0, len(original_incidents) + int(incident_id is not None) - len(state["incidents"]))
            keep = {c["name"] for c in state["chunks"]}
            replaced = {c["name"] for c in original if c["name"] not in keep}
            # Replacing a partially filled chunk does not retire its copied rows.
            copied = len(chunk_rows)-1 if accepted else 0
            state["retired_records"] += max(0, sum(c["record_count"] for c in original if c["name"] in replaced) - copied)
            state["last_timestamp_ns"] = timestamp
            state["sources"][source] = {"sequence": record["sequence"], "timestamp_ns": timestamp, "record_sha256": _hash(raw_record), "accepted": accepted, "incident_id": incident_id}
            state["revision"] += 1
            if accepted:
                target = self.directory / name
                with target.open("xb") as stream:
                    stream.write(frame)
                    stream.flush()
                    os.fsync(stream.fileno())
            self._write(state)
            for old in replaced:
                (self.directory / old).unlink()
            return {"accepted": accepted, "replayed": False, "incident_id": incident_id, "dropped_reason": None if accepted else "storage_quota", "status": self._status(state), **deepcopy(GUARDS)}

    def capture_fault(self, record):
        _require(type(record) is dict and record.get("kind") == "fault", "RECORDER_FAULT", "capture_fault requires an explicit fault envelope")
        return self.append(record)

    @staticmethod
    def _status(state, orphan_count=0, interrupted_count=0):
        chunks = state["chunks"]
        return {"initialized": True, "store_id": state["store_id"], "revision": state["revision"],
                "chunk_count": len(chunks), "record_count": sum(c["record_count"] for c in chunks), "stored_records": sum(c["record_count"] for c in chunks),
                "raw_bytes": sum(c["raw_bytes"] for c in chunks), "compressed_bytes": sum(c["compressed_bytes"] for c in chunks),
                "quota_bytes": state["options"]["max_storage_bytes"], "manifest_allowance_bytes": MANIFEST_ALLOWANCE,
                "transient_extra_chunk_bytes": state["options"]["chunk_bytes"]+1024,
                "incident_count": len(state["incidents"]), "incidents": deepcopy(state["incidents"]), "options": deepcopy(state["options"]),
                "last_timestamp_ns": state["last_timestamp_ns"], "dropped_records": state["dropped_records"], "retired_records": state["retired_records"],
                "gaps": deepcopy(state["gaps"]), "gap_count": state["gap_count"], "older_gap_details_unavailable": state["gap_count"] > len(state["gaps"]),
                "orphan_chunks_pending_recovery": orphan_count, "recovered_orphan_chunks": state["recovered_orphan_chunks"],
                "interrupted_manifests_pending_recovery": interrupted_count,
                "durability_scope": "file_flush_and_atomic_host_commit; target_power_loss_not_qualified",
                "time_basis": "caller_declared_simulation_monotonic_ns", "freshness": "not_inferred; inspect explicit observation validity/freshness/age", **deepcopy(GUARDS)}

    def status(self):
        if self._absent():
            return {"initialized": False, "chunk_count": 0, "record_count": 0, "raw_bytes": 0, "compressed_bytes": 0, "incident_count": 0, "incidents": [], "dropped_records": 0, "gaps": [], "quota_bytes": self.options["max_storage_bytes"], **deepcopy(GUARDS)}
        with self._lock():
            state, _, _, orphans = self._read()
            return self._status(state, *self._pending_counts(orphans))

    @staticmethod
    def _report(state, records, incident_id=None, orphan_count=0, interrupted_count=0):
        incident = None
        if incident_id is not None:
            incident = next((i for i in state["incidents"] if i["id"] == incident_id), None)
            _require(incident is not None, "RECORDER_INCIDENT", "Requested incident is not retained")
        elif state["incidents"]:
            incident = state["incidents"][-1]
        window, fault = None, None
        selected = records
        if incident:
            o, t = state["options"], incident["timestamp_ns"]
            start, end = t-o["pre_fault_ns"], t+o["post_fault_ns"]
            selected = [r for r in records if start <= r["timestamp_ns"] <= end]
            source_rows = [r for r in selected if r["source"] == incident["source"]]
            fault = next(r for r in source_rows if r["kind"] == "fault" and r["sequence"] == incident["sequence"])
            pre = max(0, t-min(r["timestamp_ns"] for r in source_rows))
            post = max(0, max(r["timestamp_ns"] for r in source_rows)-t)
            gaps = [g for g in state["gaps"] if g["source"] == incident["source"] and g["end_ns"] >= start and g["start_ns"] <= end]
            # Reconstruct sample gaps too: old bounded gap history can never hide
            # missing records when declaring this retained window complete.
            for a, b in zip(source_rows, source_rows[1:]):
                if b["timestamp_ns"]-a["timestamp_ns"] > o["max_gap_ns"] or b["sequence"] != a["sequence"]+1:
                    gaps.append({"source": incident["source"], "start_ns": a["timestamp_ns"], "end_ns": b["timestamp_ns"], "reason": "retained_record_gap"})
            unknown_gaps = state["gap_count"] > len(state["gaps"])
            window = {"requested_pre_seconds": o["pre_fault_ns"]/1e9, "requested_post_seconds": o["post_fault_ns"]/1e9,
                      "pre_observed_seconds": min(pre, o["pre_fault_ns"])/1e9, "post_observed_seconds": min(post, o["post_fault_ns"])/1e9,
                      "pre_complete": o["pre_fault_ns"] == 0 or (pre >= o["pre_fault_ns"] and not unknown_gaps and
                          not any(g["start_ns"] < t or g["start_ns"] == g["end_ns"] == t for g in gaps)),
                      "post_complete": o["post_fault_ns"] == 0 or (post >= o["post_fault_ns"] and not unknown_gaps and
                          not any(g["end_ns"] > t or g["start_ns"] == g["end_ns"] == t for g in gaps)),
                      "gaps": gaps, "older_gap_details_unavailable": unknown_gaps,
                      "claim": "retained simulated sample coverage only; no physical clock, sampling deadline or machine response qualification"}
        return {"schema_version": 1, "initialized": True, "incident_id": incident["id"] if incident else None,
                "incidents": deepcopy(state["incidents"]), "fault_record": deepcopy(fault), "records": deepcopy(selected), "record_count": len(selected),
                "window": window, "storage": DiagnosticRecorder._status(state, orphan_count, interrupted_count), **deepcopy(GUARDS)}

    def report(self, incident_id=None):
        if self._absent():
            _require(incident_id is None, "RECORDER_INCIDENT", "No incident exists in an uninitialized recorder")
            return {"schema_version": 1, "initialized": False, "incident_id": None, "incidents": [], "fault_record": None, "records": [], "record_count": 0, "window": None, "storage": self.status(), **deepcopy(GUARDS)}
        with self._lock():
            state, records, _, orphans = self._read()
            return self._report(state, records, incident_id, *self._pending_counts(orphans))

    def export(self, destination, configuration=None, incident_id=None):
        from .package_archive import create_archive
        _require(not self._absent(), "RECORDER_EMPTY", "No recorded observations exist to export")
        if configuration is not None:
            _require(type(configuration) is dict, "RECORDER_CONFIGURATION", "Configuration snapshot must be an explicit JSON object")
            _json_tree(configuration)
        with self._lock():
            state, records, _, orphans = self._read()
            report = self._report(state, records, incident_id, *self._pending_counts(orphans))
            entries = {"report.json": canonical(report), "recorder-manifest.json": canonical(_seal(state))}
            if configuration is not None:
                entries["configuration.json"] = canonical(configuration)
            for chunk in state["chunks"]:
                entries["chunks/" + chunk["name"]] = _read_regular(self.directory / chunk["name"], state["options"]["chunk_bytes"] + 1024)
            receipt = create_archive(destination, entries, kind="support", metadata={"source": "disconnected-diagnostic-recorder", "simulation_only": True})
            return {"archive": receipt, "incident_id": report["incident_id"], "record_count": report["record_count"], **deepcopy(GUARDS)}

    def flush(self):
        """Every acknowledged append is already persisted; this verifies it."""
        return self.status()

    def close(self):
        return self.flush()
