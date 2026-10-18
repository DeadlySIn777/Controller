"""Bounded, inert tar+Zstandard packages; no extraction, execution or config apply.

SHA-256 inventories detect corruption, not sender authenticity. One checksummed
frame and strict USTAR regular files are accepted. No dictionary is trained or
loaded. Limits are host safeguards, not target CPU, latency or flash-wear claims.
Format references: docs.python.org/3/library/compression.zstd.html and
github.com/facebook/zstd/blob/dev/doc/zstd_compression_format.md.
"""
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import stat
import tarfile
import tempfile

try:
    from compression import zstd as _zstd
except ImportError:  # Optional in CPython; absent before 3.14.
    _zstd = None

KINDS = ("support", "config", "job")
MAX_ENTRIES = 128
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_PAYLOAD_BYTES = 32 * 1024 * 1024
MAX_MANIFEST_BYTES = 64 * 1024
MAX_METADATA_BYTES = 16 * 1024
MAX_RAW_BYTES = 64 * 1024 * 1024
MAX_COMPRESSED_BYTES = MAX_RAW_BYTES + 1024 * 1024
MAX_WINDOW_BYTES = 8 * 1024 * 1024
MAX_TAR_BYTES = MAX_PAYLOAD_BYTES + MAX_MANIFEST_BYTES + (MAX_ENTRIES + 1) * 1024 + 10240
MANIFEST_NAME = "manifest.json"
FORMAT = "controller-package-tar-zstd"


class ArchiveError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)

    def as_dict(self):
        return {"code": self.code, "message": str(self)}


def _require(condition, code, message):
    if not condition:
        raise ArchiveError(code, message)


def _backend():
    _require(_zstd is not None, "ARCHIVE_UNAVAILABLE", "This Python runtime has no compression.zstd backend; package operations are unavailable")
    return _zstd


def capabilities():
    return {"schema_version": 1, "available": _zstd is not None,
            "backend": "python.compression.zstd" if _zstd is not None else None,
            "format": FORMAT, "kinds": list(KINDS), "default_level": 3,
            "dictionary": None, "checksum_required": True, "single_frame": True,
            "max_entries": MAX_ENTRIES, "max_file_bytes": MAX_FILE_BYTES,
            "max_payload_bytes": MAX_PAYLOAD_BYTES, "max_window_bytes": MAX_WINDOW_BYTES,
            "max_raw_bytes": MAX_RAW_BYTES, "max_compressed_bytes": MAX_COMPRESSED_BYTES,
            "max_manifest_bytes": MAX_MANIFEST_BYTES, "max_metadata_bytes": MAX_METADATA_BYTES,
            "max_path_characters": 100,
            "extracts_files": False, "executes": False, "applies_configuration": False,
            "authenticates_sender": False, "target_performance_qualified": False}


def compress_bytes(data, level=3):
    zstd = _backend()
    _require(type(data) is bytes and len(data) <= MAX_RAW_BYTES, "ARCHIVE_SIZE", "Expected bounded bytes for compression")
    _require(type(level) is int and 1 <= level <= 9, "ARCHIVE_LEVEL", "Compression level must be an integer from 1 to 9")
    try:
        compressor = zstd.ZstdCompressor(options={
            zstd.CompressionParameter.compression_level: level,
            zstd.CompressionParameter.window_log: 23,
            zstd.CompressionParameter.checksum_flag: 1,
            zstd.CompressionParameter.content_size_flag: 1,
            zstd.CompressionParameter.nb_workers: 0})
        compressor.set_pledged_input_size(len(data))
        return compressor.compress(data, zstd.ZstdCompressor.FLUSH_FRAME)
    except zstd.ZstdError as error:
        raise ArchiveError("ARCHIVE_CODEC", "Zstandard compression failed") from error


def decompress_bytes(data, max_output_bytes):
    zstd = _backend()
    _require(type(data) is bytes and len(data) <= MAX_COMPRESSED_BYTES, "ARCHIVE_SIZE", "Expected bounded compressed bytes")
    _require(type(max_output_bytes) is int and 0 <= max_output_bytes <= MAX_RAW_BYTES,
             "ARCHIVE_SIZE", "Invalid decompressed byte limit")
    _require(len(data) >= 6 and data[:4] == b"\x28\xb5\x2f\xfd", "ARCHIVE_FRAME", "Expected one standard Zstandard frame")
    descriptor = data[4]
    _require(descriptor & 4 and not descriptor & 0x1B, "ARCHIVE_FRAME", "A checksummed frame without a dictionary or reserved flags is required")
    try:
        info = zstd.get_frame_info(data)
        _require(info.dictionary_id == 0, "ARCHIVE_FRAME", "Dictionaries are not supported")
        _require(info.decompressed_size is None or info.decompressed_size <= max_output_bytes,
                 "ARCHIVE_SIZE", "Frame exceeds the decompressed byte limit")
        if descriptor & 0x20:
            window = info.decompressed_size
        else:
            base = 1 << (10 + (data[5] >> 3))
            window = base + (base // 8) * (data[5] & 7)
        _require(window is not None and window <= MAX_WINDOW_BYTES,
                 "ARCHIVE_WINDOW", "Frame exceeds the bounded Zstandard window")
        decoder = zstd.ZstdDecompressor(options={zstd.DecompressionParameter.window_log_max: 23})
        result = decoder.decompress(data, max_length=max_output_bytes + 1)
        _require(len(result) <= max_output_bytes, "ARCHIVE_SIZE", "Frame exceeds the decompressed byte limit")
        _require(decoder.eof, "ARCHIVE_FRAME", "Truncated or incomplete Zstandard frame")
        _require(not decoder.unused_data, "ARCHIVE_FRAME", "Trailing bytes or concatenated frames are forbidden")
        return result
    except zstd.ZstdError as error:
        raise ArchiveError("ARCHIVE_CODEC", "Invalid or corrupt Zstandard frame") from error


def _name(name):
    _require(type(name) is str and 0 < len(name) <= 100 and re.fullmatch(r"[A-Za-z0-9._/-]+", name),
             "ARCHIVE_PATH", "Member names must be bounded portable relative paths")
    parts = name.split("/")
    for part in parts:
        stem = part.split(".", 1)[0].upper()
        _require(part not in ("", ".", "..") and not part.endswith(".") and
                 stem not in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))},
                 "ARCHIVE_PATH", "Ambiguous, absolute, traversal or reserved member path")
    return name


def _inventory(names):
    seen = set()
    for name in names:
        folded = _name(name).casefold()
        _require(folded not in seen, "ARCHIVE_DUPLICATE", "Duplicate or case-colliding member path")
        _require(not any(folded.startswith(other + "/") or other.startswith(folded + "/") for other in seen),
                 "ARCHIVE_PATH", "File and parent-directory paths collide")
        seen.add(folded)


def _json(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise ArchiveError("ARCHIVE_MANIFEST", "Expected bounded finite JSON values") from error


def _load_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "ARCHIVE_DUPLICATE", "Duplicate JSON key")
            result[key] = value
        return result

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
    except (UnicodeError, ValueError, RecursionError) as error:
        if isinstance(error, ArchiveError):
            raise
        raise ArchiveError("ARCHIVE_MANIFEST", "Invalid manifest JSON") from error


def _metadata(metadata):
    _require(type(metadata) is dict, "ARCHIVE_MANIFEST", "Metadata must be an object")
    def walk(value, depth=0):
        _require(depth <= 8, "ARCHIVE_MANIFEST", "Metadata is too deeply nested")
        if type(value) is dict:
            for key, child in value.items():
                _require(type(key) is str, "ARCHIVE_MANIFEST", "Metadata keys must be strings")
                walk(child, depth + 1)
        elif type(value) is list:
            for child in value:
                walk(child, depth + 1)
        else:
            _require(value is None or type(value) in (str, int, bool) or
                     (type(value) is float and math.isfinite(value)), "ARCHIVE_MANIFEST", "Metadata must contain finite JSON values")
    walk(metadata)
    encoded = _json(metadata)
    _require(len(encoded) <= MAX_METADATA_BYTES, "ARCHIVE_SIZE", "Metadata exceeds its byte limit")
    return _load_json(encoded)


def _kind(kind):
    _require(type(kind) is str and kind in KINDS, "ARCHIVE_KIND", "Unknown package kind")


def _tar(manifest, entries):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.USTAR_FORMAT, encoding="utf-8", errors="strict") as archive:
        for name, data in [(MANIFEST_NAME, _json(manifest)), *sorted(entries.items())]:
            member = tarfile.TarInfo(name)
            member.size, member.mode, member.mtime = len(data), 0o600, 0
            archive.addfile(member, io.BytesIO(data))
    return buffer.getvalue()


def _sync_directory(parent):
    # POSIX directory fsync makes the exclusive link durable at the host API
    # boundary. Windows file flush remains separate from physical power-loss
    # qualification; no portable directory-flush claim is made there.
    if os.name != "nt":
        descriptor = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _publish(destination, data):
    temporary, target, published = None, None, False
    try:
        requested = Path(destination).absolute()
        parent = requested.parent.resolve(strict=True)
        _require(parent.is_dir(), "ARCHIVE_IO", "Destination parent must be an existing directory")
        target = parent / requested.name
        descriptor, temporary = tempfile.mkstemp(prefix=".controller-package-", suffix=".tmp", dir=parent)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        # Exclusive link is atomic on supported local filesystems. No rename or
        # replacement fallback is permitted if the filesystem cannot do this.
        os.link(temporary, target, follow_symlinks=False)
        published = True
        _sync_directory(parent)
        return target
    except FileExistsError as error:
        raise ArchiveError("ARCHIVE_EXISTS", "Destination exists; no file was replaced") from error
    except (OSError, TypeError, ValueError) as error:
        if isinstance(error, ArchiveError):
            raise
        # An I/O failure can arrive after the link was created. Never delete
        # that published artifact or imply a retry may safely overwrite it.
        if not published and target is not None and temporary is not None:
            try:
                origin, result = os.stat(temporary), target.lstat()
                published = stat.S_ISREG(result.st_mode) and (origin.st_dev, origin.st_ino) == (result.st_dev, result.st_ino)
            except OSError:
                pass
        if published:
            raise ArchiveError("ARCHIVE_PUBLICATION_UNCERTAIN",
                f"Archive was published at {target}, but durable publication was not acknowledged; inspect it before retrying") from error
        raise ArchiveError("ARCHIVE_IO", "Unable to publish a new archive atomically") from error
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except OSError:
                pass


def create_archive(destination, entries, kind, metadata=None):
    _backend()
    _kind(kind)
    _require(type(entries) is dict and 1 <= len(entries) <= MAX_ENTRIES, "ARCHIVE_SIZE", "Expected a nonempty bounded file inventory")
    entries = dict(entries)
    _inventory([MANIFEST_NAME, *entries])
    total = 0
    rows = []
    for name, data in sorted(entries.items()):
        _require(type(data) is bytes and len(data) <= MAX_FILE_BYTES, "ARCHIVE_SIZE", "Member exceeds its byte limit or is not bytes")
        total += len(data)
        _require(total <= MAX_PAYLOAD_BYTES, "ARCHIVE_SIZE", "Package exceeds its payload byte limit")
        rows.append({"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    manifest = {"schema_version": 1, "format": FORMAT, "kind": kind,
                "metadata": _metadata({} if metadata is None else metadata),
                "entries": rows, "payload_bytes": total}
    _require(len(_json(manifest)) <= MAX_MANIFEST_BYTES, "ARCHIVE_SIZE", "Manifest exceeds its byte limit")
    raw = _tar(manifest, entries)
    data = compress_bytes(raw)
    target = _publish(destination, data)
    return {"path": str(target), "kind": kind, "codec": "zstd", "archive_bytes": len(data),
            "uncompressed_bytes": len(raw), "payload_bytes": total,
            "sha256": hashlib.sha256(data).hexdigest(), "manifest": manifest,
            "executed": False, "configuration_applied": False, "publication_acknowledged": True,
            "durability_scope": "file_flush_and_atomic_exclusive_link; target_power_loss_not_qualified",
            "directory_flush": os.name != "nt", "authenticates_sender": False}


def _read_file(path):
    try:
        path = Path(path)
        before = path.lstat()
        _require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_COMPRESSED_BYTES,
                 "ARCHIVE_SIZE", "Archive must be a bounded regular file, not a symlink")
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) |
                             getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(descriptor, "rb") as handle:
            opened = os.fstat(handle.fileno())
            _require(stat.S_ISREG(opened.st_mode) and (before.st_dev, before.st_ino) == (opened.st_dev, opened.st_ino),
                     "ARCHIVE_IO", "Archive changed while opening")
            data = handle.read(MAX_COMPRESSED_BYTES + 1)
        _require(len(data) == before.st_size and len(data) <= MAX_COMPRESSED_BYTES,
                 "ARCHIVE_SIZE", "Archive size changed or exceeds its limit")
        return data
    except (OSError, TypeError, ValueError) as error:
        if isinstance(error, ArchiveError):
            raise
        raise ArchiveError("ARCHIVE_IO", "Unable to read archive") from error


def _members(raw):
    _require(len(raw) % 512 == 0, "ARCHIVE_TAR", "Truncated tar block")
    result, offset, total = {}, 0, 0
    while offset + 512 <= len(raw):
        header = raw[offset:offset + 512]
        if header == bytes(512):
            _require(len(raw) - offset >= 1024 and not any(raw[offset:]), "ARCHIVE_TAR", "Missing end blocks or trailing tar data")
            return result
        _require(len(result) <= MAX_ENTRIES and header[257:265] == b"ustar\x0000",
                 "ARCHIVE_TAR", "Too many members or unsupported tar format")
        try:
            member = tarfile.TarInfo.frombuf(header, encoding="utf-8", errors="strict")
        except (tarfile.HeaderError, UnicodeError, ValueError) as error:
            raise ArchiveError("ARCHIVE_TAR", "Invalid tar header") from error
        _require(member.type in (tarfile.REGTYPE, tarfile.AREGTYPE) and not member.linkname,
                 "ARCHIVE_TAR", "Only regular files are allowed; links and extensions are forbidden")
        _inventory([*result, member.name])
        limit = MAX_MANIFEST_BYTES if member.name == MANIFEST_NAME else MAX_FILE_BYTES
        _require(0 <= member.size <= limit, "ARCHIVE_SIZE", "Member exceeds its byte limit")
        if member.name != MANIFEST_NAME:
            total += member.size
            _require(total <= MAX_PAYLOAD_BYTES, "ARCHIVE_SIZE", "Package exceeds its payload byte limit")
        start, end = offset + 512, offset + 512 + member.size
        padded = ((end + 511) // 512) * 512
        _require(padded <= len(raw) and not any(raw[end:padded]), "ARCHIVE_TAR", "Truncated member or nonzero tar padding")
        result[member.name] = raw[start:end]
        offset = padded
    raise ArchiveError("ARCHIVE_TAR", "Missing tar end blocks")


def read_archive(path, expected_kind=None):
    _backend()
    if expected_kind is not None:
        _kind(expected_kind)
    data = _read_file(path)
    members = _members(decompress_bytes(data, MAX_TAR_BYTES))
    _require(MANIFEST_NAME in members, "ARCHIVE_MANIFEST", "Missing package manifest")
    manifest = _load_json(members.pop(MANIFEST_NAME))
    _require(type(manifest) is dict and set(manifest) == {"schema_version", "format", "kind", "metadata", "entries", "payload_bytes"},
             "ARCHIVE_MANIFEST", "Unknown manifest fields")
    _require(type(manifest["schema_version"]) is int and manifest["schema_version"] == 1 and manifest["format"] == FORMAT,
             "ARCHIVE_SCHEMA", "Unsupported package schema or format")
    _kind(manifest["kind"])
    _require(expected_kind is None or manifest["kind"] == expected_kind, "ARCHIVE_KIND", "Package kind differs from expected kind")
    _metadata(manifest["metadata"])
    rows = manifest["entries"]
    _require(type(rows) is list and 1 <= len(rows) <= MAX_ENTRIES, "ARCHIVE_MANIFEST", "Invalid manifest inventory")
    names, total = [], 0
    for row in rows:
        _require(type(row) is dict and set(row) == {"path", "size", "sha256"}, "ARCHIVE_MANIFEST", "Invalid manifest entry")
        name = _name(row["path"])
        names.append(name)
        _require(type(row["size"]) is int and 0 <= row["size"] <= MAX_FILE_BYTES and
                 type(row["sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]),
                 "ARCHIVE_MANIFEST", "Invalid entry size or SHA-256")
        _require(name in members and len(members[name]) == row["size"] and hashlib.sha256(members[name]).hexdigest() == row["sha256"],
                 "ARCHIVE_INTEGRITY", "Entry is missing or its bytes differ from its manifest")
        total += row["size"]
    _inventory([MANIFEST_NAME, *names])
    _require(set(names) == set(members), "ARCHIVE_INTEGRITY", "Unlisted package members")
    _require(type(manifest["payload_bytes"]) is int and manifest["payload_bytes"] == total <= MAX_PAYLOAD_BYTES,
             "ARCHIVE_INTEGRITY", "Payload total differs from the manifest")
    return {"manifest": manifest, "entries": members, "archive_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(), "executed": False, "configuration_applied": False,
            "authenticates_sender": False, "integrity_verified": True}
