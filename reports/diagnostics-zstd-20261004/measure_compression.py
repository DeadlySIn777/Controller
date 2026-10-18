"""Actual synthetic host measurements; no claimed target/flash qualification."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import statistics
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from controller_config.diagnostic_service import DiagnosticService
from controller_config.package_archive import compress_bytes, decompress_bytes, read_archive
from controller_config.service import canonical


def main():
    report_folder = Path(__file__).resolve().parent
    raw = b"".join(canonical({"schema_version": 1, "simulation_only": True,
        "timestamp_ns": i*1_000_000, "source": "authored-benchmark", "sequence": i,
        "kind": "sample", "data": {"motors": [{"id": f"M{m}", "commanded_velocity_mm_s": (i % 100)/10,
            "measured_velocity_mm_s": None, "alarm_valid": False} for m in range(12)],
            "di_valid": False, "do_valid": False, "physical_observation": False}})+b"\n" for i in range(2000))
    levels = []
    for level in (1, 3, 6):
        encode, decode = [], []
        for _ in range(5):
            start = time.perf_counter_ns()
            frame = compress_bytes(raw, level)
            encoded = time.perf_counter_ns()
            restored = decompress_bytes(frame, len(raw))
            end = time.perf_counter_ns()
            assert restored == raw
            encode.append((encoded-start)/1e6)
            decode.append((end-encoded)/1e6)
        levels.append({"level": level, "raw_bytes": len(raw), "compressed_bytes": len(frame),
            "saved_percent": (1-len(frame)/len(raw))*100, "round_trip_sha256": hashlib.sha256(restored).hexdigest(),
            "encode_ms": {"median": statistics.median(encode), "min": min(encode), "max": max(encode)},
            "decode_ms": {"median": statistics.median(decode), "min": min(decode), "max": max(decode)}})
    service = DiagnosticService(report_folder / "ui-preview")
    fixture = service.report(example=True)
    storage = fixture["storage"]
    with tempfile.TemporaryDirectory(prefix="controller-measure-") as folder:
        package_path = Path(folder)/"support.tar.zst"
        export = service.package(package_path, "support", example=True)
        package = read_archive(package_path, "support")
        support = {"payload_bytes": package["manifest"]["payload_bytes"], "archive_bytes": package["archive_bytes"],
                   "sha256": package["sha256"], "verified_members": len(package["entries"])}
    receipt = {"finished_utc": datetime.now(timezone.utc).isoformat(), "runtime": sys.version,
        "platform": platform.platform(), "method": "2,000 authored 12-motor JSON records; five sequential encode/decode trials per level; perf_counter_ns wall timing, no concurrent load characterization",
        "scope": "Synthetic Windows host data only; no realtime, target CPU/load, network, flash wear, powerfail or physical-machine claim",
        "levels": levels, "example": {"record_count": fixture["record_count"], "raw_chunk_bytes": storage["raw_bytes"],
            "compressed_chunk_bytes": storage["compressed_bytes"], "window": fixture["window"], "support_package": support}}
    (report_folder/"compression-measurements.json").write_text(json.dumps(receipt,indent=2),encoding="utf-8")
    print(json.dumps(receipt,indent=2))


if __name__ == "__main__":
    main()
