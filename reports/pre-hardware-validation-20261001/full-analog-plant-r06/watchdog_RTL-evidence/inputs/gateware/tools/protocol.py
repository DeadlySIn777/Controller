#!/usr/bin/env python3
"""Offline CNC1 ABI codec and independent CRC vectors. Never opens hardware."""
from __future__ import annotations
import argparse
import binascii
import json
from pathlib import Path
import struct

def encode(op: int, mask: int = 0, session: int = 0, sequence: int = 0,
           rates: tuple[int, ...] = (0,) * 6) -> bytes:
    if len(rates) != 6 or not 0 <= mask < 64:
        raise ValueError("six rates and six-bit mask required")
    payload = struct.pack(">4sBBBBII6i22x", b"CNC1", 1, op, mask, 0,
                          session, sequence, *rates)
    assert len(payload) == 62
    return payload + struct.pack(">H", binascii.crc_hqx(payload, 0xFFFF))

def decode_status(frame: bytes) -> dict:
    if len(frame) != 64 or frame[:5] != b"CNS1\x01":
        raise ValueError("invalid frame length, signature, or ABI")
    if binascii.crc_hqx(frame[:62], 0xFFFF) != int.from_bytes(frame[62:], "big"):
        raise ValueError("CRC mismatch")
    if frame[5] & ~3 or frame[6] & ~63 or frame[7] & ~15 or frame[60] & ~0x33 or frame[61]:
        raise ValueError("reserved status bits are nonzero")
    return {"enabled": bool(frame[5] & 1), "endpoint_ready": bool(frame[5] & 2),
            "mask": frame[6], "faults": frame[7],
            "session": int.from_bytes(frame[8:12], "big"),
            "accepted_sequence": int.from_bytes(frame[12:16], "big"),
            "timestamp_ticks": int.from_bytes(frame[16:20], "big"),
            "emitted_step_counts": struct.unpack(">6i", frame[20:44]),
            "encoder_counts": struct.unpack(">2i", frame[44:52]),
            "index_counts": struct.unpack(">2i", frame[52:60]),
            "encoder_flags": frame[60]}

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-vectors", action="store_true")
    parser.add_argument("--check-rtl-status", type=Path,
                        help="check the immutable encoder snapshot emitted by the RTL testbench")
    args = parser.parse_args()
    assert binascii.crc_hqx(b"123456789", 0xFFFF) == 0x29B1
    vectors = [("nop", encode(0)), ("sync", encode(1, session=0x10203041)),
               ("arm", encode(2, 63, 0x10203041, 1))]
    if args.write_vectors:
        out = Path(__file__).resolve().parents[1] / "tests"
        out.mkdir(exist_ok=True)
        # LF on every host: the vectors are hashed byte-for-byte by validation/manifest.json.
        (out / "vectors.hex").write_text("".join(f.hex() + "\n" for _, f in vectors), encoding="ascii", newline="\n")
        (out / "vectors.json").write_text(json.dumps(
            [{"name": name, "frame_hex": f.hex(), "crc_hex": f[-2:].hex()} for name, f in vectors],
            indent=2) + "\n", encoding="ascii", newline="\n")
    print("CRC-16/CCITT-FALSE known-answer and three independent ABI vectors passed")
    if args.check_rtl_status:
        frame = bytes.fromhex(args.check_rtl_status.read_text(encoding="ascii").strip())
        status = decode_status(frame)
        assert not status["enabled"] and status["endpoint_ready"]
        assert status["mask"] == 0 and status["faults"] == 0
        assert status["encoder_counts"] == (0, 0) and status["index_counts"] == (4, 4)
        assert status["encoder_flags"] == 0x33 and status["timestamp_ticks"] > 0
        broken = bytearray(frame)
        broken[20] ^= 1
        try:
            decode_status(bytes(broken))
        except ValueError as exc:
            assert "CRC" in str(exc)
        else:
            raise AssertionError("corrupted RTL status accepted")
        broken = bytearray(frame)
        broken[61] = 1
        broken[62:] = struct.pack(">H", binascii.crc_hqx(broken[:62], 0xFFFF))
        try:
            decode_status(bytes(broken))
        except ValueError as exc:
            assert "reserved" in str(exc)
        else:
            raise AssertionError("reserved RTL status bits accepted")
        print("Python independently decoded RTL status, verified CRC/field layout, and rejected corruption/reserved bits")

if __name__ == "__main__":
    main()
