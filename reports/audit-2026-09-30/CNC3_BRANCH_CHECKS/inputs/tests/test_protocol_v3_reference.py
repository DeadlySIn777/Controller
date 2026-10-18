# SPDX-License-Identifier: LicenseRef-Proprietary
"""Host tests for the IS-1 CNC3/IOL1 reference codec (gateware/v3/tools/protocol_v3.py)."""
import importlib.util
import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("protocol_v3", os.path.join(ROOT, "gateware", "v3", "tools", "protocol_v3.py"))
p3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p3)

R8 = [1000, -2000, 3000, -4000, 5000, -6000, 7000, -8000]
R12 = R8 + [9000, -10000, 11000, -12000]


def reseal(layout, data):
    return p3.seal(layout, bytearray(data))


class CrcTests(unittest.TestCase):
    def test_check_values_match_spec(self):
        crc = p3.spec().raw["crc"]
        self.assertEqual(p3.crc16_ccitt_false(b"123456789"), 0x29B1)
        self.assertEqual(p3.crc32c(b"123456789"), 0xE3069283)
        self.assertEqual(f"0x{p3.crc16_ccitt_false(b'123456789'):04X}", crc["host_frames"]["check_123456789"])
        self.assertEqual(f"0x{p3.crc32c(b'123456789'):08X}", crc["io_link"]["check_123456789"])

    def test_empty_input(self):
        self.assertEqual(p3.crc16_ccitt_false(b""), 0xFFFF)
        self.assertEqual(p3.crc32c(b""), 0)


class SpecModelTests(unittest.TestCase):
    def test_layouts_are_contiguous_and_sized(self):
        s = p3.spec()
        expected = {"fb_command": 176, "fb_response_CNF3": 176, "cmd_command": 96, "cmd_response_CNS3": 96,
                    "cap3_page0": 176, "cap3_page1": 176, "flt3_page2": 176, "idp3_page3": 176,
                    "iol1_command": 40, "iol1_response": 40}
        for name, length in expected.items():
            self.assertEqual(s.layout(name).length, length, name)
        for name in ("fb_read_payload_at_16", "configure_payload_at_16", "configure_io_page0_at_16",
                     "configure_io_page1_at_16", "configure_io_card_pages_at_16"):
            self.assertLessEqual(s.layout(name).length, s.payload_size, name)

    def test_chip_select_opcode_partition(self):
        s = p3.spec()
        self.assertEqual(s.cs_frame_bytes, {"CS_FB": 176, "CS_CMD": 96})
        self.assertFalse(s.cs_opcodes["CS_FB"] & s.cs_opcodes["CS_CMD"])
        self.assertEqual(s.cs_opcodes["CS_FB"] | s.cs_opcodes["CS_CMD"], set(s.opcodes))
        for name, cs in (("FB_READ", "CS_FB"), ("READ_PAGE", "CS_FB"), ("CONFIGURE", "CS_FB"), ("MAINT", "CS_FB"),
                         ("UPDATE", "CS_CMD"), ("SYNC", "CS_CMD"), ("ARM", "CS_CMD"), ("NOP", "CS_CMD")):
            self.assertEqual(s.cs_for_opcode(s.opcode_by_name[name]), cs, name)


class VectorTests(unittest.TestCase):
    def test_every_spec_vector_validates_and_round_trips(self):
        for name, ok in p3.self_check():
            with self.subTest(name):
                self.assertTrue(ok)

    def test_update_8ch_vector_fields(self):
        data = p3.spec().vectors["update_8ch_do5"]
        d = p3.validate_command("CS_CMD", data)
        self.assertEqual(d["opcode_name"], "UPDATE")
        self.assertEqual(d["channel_mask"], 0x00FF)
        for ch in range(8, 12):
            self.assertEqual(d[f"rate_{ch}"], 0)

    def test_iol1_vector(self):
        d = p3.validate_iol1("iol1_command", p3.spec().vectors["iol1_sync_doa"])
        self.assertEqual(d["sequence"], 0)
        self.assertTrue(d["control"] & 1)


class ChannelConfigurationTests(unittest.TestCase):
    def test_eight_motor_update(self):
        frame = p3.encode_update(session=0x01020304, sequence=9, rates=R8, channel_mask=0x00FF, dout_image=0x8001)
        self.assertEqual(len(frame), 96)
        d = p3.validate_command("CS_CMD", frame)
        self.assertEqual([d[f"rate_{i}"] for i in range(12)], R8 + [0, 0, 0, 0])
        self.assertEqual((d["session"], d["sequence"], d["dout_image"]), (0x01020304, 9, 0x8001))

    def test_twelve_motor_update(self):
        frame = p3.encode_update(session=5, sequence=10, rates=R12, channel_mask=0x0FFF)
        d = p3.validate_command("CS_CMD", frame)
        self.assertEqual([d[f"rate_{i}"] for i in range(12)], R12)
        self.assertEqual(d["channel_mask"], 0x0FFF)

    def test_rate_limits(self):
        top = p3.encode_update(session=1, sequence=1, rates=[0x01000000, -0x01000000], channel_mask=0x0003)
        d = p3.validate_command("CS_CMD", top)
        self.assertEqual((d["rate_0"], d["rate_1"]), (0x01000000, -0x01000000))
        with self.assertRaises(p3.ProtocolError) as ctx:
            p3.encode_update(session=1, sequence=1, rates=[0x01000001], channel_mask=0x0001)
        self.assertEqual(ctx.exception.code, "RATE_CLAMP")

    def test_mask_above_twelve_rejected_on_encode(self):
        with self.assertRaises(p3.ProtocolError) as ctx:
            p3.encode_update(session=1, sequence=1, rates=R12, channel_mask=0x1FFF)
        self.assertEqual(ctx.exception.code, "MASK_WIDTH")

    def test_rate_outside_mask_rejected_on_encode(self):
        with self.assertRaises(p3.ProtocolError) as ctx:
            p3.encode_update(session=1, sequence=1, rates=R12, channel_mask=0x00FF)
        self.assertEqual(ctx.exception.code, "UNMASKED_RATE")


class MalformedFrameTests(unittest.TestCase):
    def setUp(self):
        self.good = p3.encode_update(session=7, sequence=3, rates=R8, channel_mask=0x00FF)

    def expect(self, code, cs, data):
        with self.assertRaises(p3.ProtocolError) as ctx:
            p3.validate_command(cs, data)
        self.assertEqual(ctx.exception.code, code)

    def test_lengths(self):
        self.expect("LENGTH", "CS_CMD", self.good[:-1])
        self.expect("LENGTH", "CS_CMD", self.good + b"\x00")
        self.expect("LENGTH", "CS_CMD", b"")
        self.expect("LENGTH", "CS_FB", self.good)
        self.expect("LENGTH", "CS_CMD", p3.spec().vectors["fb_read_session0"])

    def test_every_single_bit_flip_fails_crc(self):
        for bit in range(len(self.good) * 8):
            bad = bytearray(self.good)
            bad[bit // 8] ^= 1 << (bit % 8)
            with self.assertRaises(p3.ProtocolError, msg=f"bit {bit}") as ctx:
                p3.validate_command("CS_CMD", bytes(bad))
            self.assertEqual(ctx.exception.code, "CRC")

    def test_magic_abi_opcode(self):
        bad = bytearray(self.good); bad[0:4] = b"CNC2"
        self.expect("MAGIC", "CS_CMD", reseal("cmd_command", bad))
        for abi in (0, 1, 2, 4, 255):
            bad = bytearray(self.good); bad[4] = abi
            self.expect("ABI", "CS_CMD", reseal("cmd_command", bad))
        bad = bytearray(self.good); bad[5] = 0x7F
        self.expect("UNKNOWN_OPCODE", "CS_CMD", reseal("cmd_command", bad))

    def test_opcode_on_wrong_chip_select(self):
        s = p3.spec()
        for name in ("FB_READ", "READ_PAGE", "CONFIGURE", "CONFIGURE_IO", "MAINT"):
            bad = bytearray(96); bad[0:4] = b"CNC3"; bad[4] = 3; bad[5] = s.opcode_by_name[name]
            self.expect("WRONG_CS", "CS_CMD", reseal("cmd_command", bad))
        for name in ("UPDATE", "SYNC", "ARM", "DISARM", "NOP"):
            bad = bytearray(176); bad[0:4] = b"CNC3"; bad[4] = 3; bad[5] = s.opcode_by_name[name]
            self.expect("WRONG_CS", "CS_FB", reseal("fb_command", bad))

    def test_mask_bits_12_to_15(self):
        for bit in range(12, 16):
            bad = bytearray(self.good)
            mask = int.from_bytes(bad[6:8], "big") | (1 << bit)
            bad[6:8] = mask.to_bytes(2, "big")
            self.expect("MASK_WIDTH", "CS_CMD", reseal("cmd_command", bad))

    def test_rate_on_unmasked_channel(self):
        for ch in range(8, 12):
            bad = bytearray(self.good)
            off = 16 + 4 * ch
            bad[off:off + 4] = (1).to_bytes(4, "big")
            self.expect("UNMASKED_RATE", "CS_CMD", reseal("cmd_command", bad))

    def test_reserved_and_zero_fields(self):
        layout = p3.spec().layout("cmd_command")
        zero_fields = [f for f in layout.fields if f.must_be_zero]
        self.assertTrue(zero_fields)
        for f in zero_fields:
            for i in range(f.size):
                bad = bytearray(self.good); bad[f.offset + i] = 0x80
                self.expect("RESERVED_NONZERO", "CS_CMD", reseal("cmd_command", bad))

    def test_rates_on_non_update_opcode(self):
        sync = p3.spec().vectors["sync_session1"]
        bad = bytearray(sync)
        bad[6:8] = (1).to_bytes(2, "big")
        bad[16:20] = (1).to_bytes(4, "big")
        with self.assertRaises(p3.ProtocolError) as ctx:
            p3.validate_command("CS_CMD", reseal("cmd_command", bad))
        self.assertEqual(ctx.exception.code, "RATE_ON_NON_UPDATE")

    def test_unknown_chip_select(self):
        self.expect("UNKNOWN_CS", "CS_X", self.good)


class ResponseTests(unittest.TestCase):
    def test_cns3_round_trip_and_crc(self):
        frame = p3.encode_response("CS_CMD", {"session": 9, "last_sequence": 4})
        self.assertEqual(len(frame), 96)
        d = p3.decode_response("CS_CMD", frame)
        self.assertEqual((d["session"], d["last_sequence"]), (9, 4))
        bad = bytearray(frame); bad[20] ^= 1
        with self.assertRaises(p3.ProtocolError) as ctx:
            p3.decode_response("CS_CMD", bytes(bad))
        self.assertEqual(ctx.exception.code, "CRC")

    def test_cnf3_magic_checked(self):
        frame = p3.encode_response("CS_FB", {})
        self.assertEqual(len(frame), 176)
        p3.decode_response("CS_FB", frame)
        with self.assertRaises(p3.ProtocolError) as ctx:
            p3.decode_response("CS_CMD", frame)
        self.assertEqual(ctx.exception.code, "LENGTH")
        bad = bytearray(frame); bad[3] = ord("2")
        with self.assertRaises(p3.ProtocolError) as ctx:
            p3.decode_response("CS_FB", reseal("fb_response_CNF3", bad))
        self.assertEqual(ctx.exception.code, "MAGIC")


class Iol1Tests(unittest.TestCase):
    def base(self, **kw):
        values = {"expected_class": 1, "expected_slot": 2, "epoch": 0x1234, "sequence": 5, "control": 0}
        values.update(kw)
        return p3.encode_iol1(values)

    def expect(self, code, data, **kw):
        with self.assertRaises(p3.ProtocolError) as ctx:
            p3.validate_iol1("iol1_command", data, **kw)
        self.assertEqual(ctx.exception.code, code)

    def test_valid_and_addressing(self):
        frame = self.base()
        self.assertEqual(len(frame), 40)
        p3.validate_iol1("iol1_command", frame, expected_class=1, expected_slot=2)
        self.expect("CLASS", frame, expected_class=2)
        self.expect("SLOT", frame, expected_slot=3)

    def test_rules(self):
        self.expect("EPOCH", self.base(epoch=0))
        self.expect("SEQUENCE", self.base(sequence=0, control=0))
        self.expect("SEQUENCE", self.base(sequence=3, control=1))
        self.expect("CONTROL", self.base(control=0x40))
        self.expect("SLOT", self.base(expected_slot=0x12))
        frame = bytearray(self.base()); frame[0] = 0xA6
        self.expect("SOF", reseal("iol1_command", frame))
        frame = bytearray(self.base()); frame[1] = 2
        self.expect("VERSION", reseal("iol1_command", frame))
        frame = bytearray(self.base()); frame[15] ^= 0x10
        self.expect("CRC", bytes(frame))
        self.expect("LENGTH", self.base()[:39])

    def test_sequence_wrap_skips_zero(self):
        self.assertEqual(p3.iol1_next_sequence(0xFFFF), 1)
        self.assertEqual(p3.iol1_next_sequence(1), 2)


class CounterTests(unittest.TestCase):
    def test_u24_unwrap(self):
        self.assertEqual(p3.unwrap_u24(0, 5), 5)
        self.assertEqual(p3.unwrap_u24(0xFFFFFE, 1), 0x1000001)
        self.assertEqual(p3.unwrap_u24(0x1000001, 0xFFFFFF), 0xFFFFFF)
        self.assertEqual(p3.unwrap_u24(-3, 0xFFFFFE), -2)
        self.assertEqual(p3.unwrap_u24(10, 10), 10)
        with self.assertRaises(p3.ProtocolError):
            p3.unwrap_u24(0, 1 << 24)


class GoldenVectorTests(unittest.TestCase):
    def test_golden_vectors_self_consistent(self):
        vectors = p3.golden_vectors()
        names = [v["name"] for v in vectors["vectors"]]
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("update_8ch", names)
        self.assertIn("update_12ch_limits", names)
        for entry in vectors["vectors"]:
            with self.subTest(entry["name"]):
                self.assertEqual(p3._check_vector(entry), entry["expect"])

    def test_committed_vectors_current(self):
        path = os.path.join(ROOT, "gateware", "v3", "vectors", "protocol_v3_vectors.json")
        if not os.path.exists(path):
            self.skipTest("vectors not generated")
        with open(path, encoding="utf-8") as handle:
            self.assertEqual(json.load(handle), p3.golden_vectors())

    def test_generated_c_headers_current(self):
        _gen = importlib.util.spec_from_file_location("gen_c_layout", os.path.join(ROOT, "gateware", "v3", "tools", "gen_c_layout.py"))
        gen = importlib.util.module_from_spec(_gen)
        _gen.loader.exec_module(gen)
        self.assertEqual(gen.main(["--check"]), 0)


class DerivedRuleTests(unittest.TestCase):
    """Pins what the codec derives from the IS-1 rule phrases; a reworded phrase fails here."""

    def rules(self, name):
        s = p3.spec()
        return {k: v for k, v in s.opcode_rules[s.opcode_by_name[name]].items() if v}

    def test_opcode_rules(self):
        self.assertEqual(self.rules("NOP"), {"sequence": "zero", "zero_ranges": [(6, 7), (16, 93)]})
        self.assertEqual(self.rules("SYNC"), {"sequence": "zero", "session_nonzero": True, "zero_ranges": [(16, 93)]})
        self.assertEqual(self.rules("ARM"), {"sequence": "nonzero", "session_nonzero": True, "mask_nonzero": True})
        self.assertEqual(self.rules("UPDATE"), {"sequence": "nonzero", "session_nonzero": True})
        self.assertEqual(self.rules("DISARM"), {"sequence": "nonzero", "session_nonzero": True, "mask_zero": True})
        self.assertEqual(self.rules("READ_PAGE"), {"sequence": "zero", "zero_ranges": [(17, 173)], "byte16": [(0, 3)]})
        self.assertEqual(self.rules("CONFIGURE"), {"paired": True, "payload_layout": "configure_payload_at_16"})
        self.assertEqual(self.rules("CONFIGURE_IO")["payload_pages"],
                         ["configure_io_card_pages_at_16", "configure_io_page0_at_16", "configure_io_page1_at_16"])
        self.assertEqual(self.rules("MAINT"), {"sequence": "zero", "byte16": [(0, 3)], "embedded_iol1": (17, 56, 5),
                                               "rest_zero": True})
        self.assertEqual(self.rules("SELFTEST"), {"sequence": "nonzero", "session_nonzero": True,
                                                  "byte16": [(1, 1), (2, 2)], "rest_zero": True})
        self.assertEqual(self.rules("FB_READ"), {"sequence": "zero", "payload_layout": "fb_read_payload_at_16"})
        for name in ("IO_CLEAR_FAULTS", "IO_WRITE"):
            self.assertTrue(self.rules(name)["mask_zero"], name)
        for name in ("IO_ENABLE", "IO_DISABLE"):
            self.assertEqual(self.rules(name)["zero_ranges"], [(16, 93)], name)

    def test_field_rules(self):
        s = p3.spec()
        cmd = s.layout("cmd_command")
        for ch in range(12):
            self.assertEqual(cmd.field(f"rate_{ch}").rules, {"only_opcodes": {"UPDATE"}})
        self.assertEqual(cmd.field("dout_image").rules["only_opcodes"], {"UPDATE", "IO_WRITE", "IO_CLEAR_FAULTS"})
        self.assertEqual(cmd.field("dout_fault_clear").rules["disjoint_with"], "dout_image")
        self.assertEqual(cmd.field("probe_arm").rules["zero_bits"], 0xFC)
        conf = s.layout("configure_payload_at_16")
        self.assertEqual(conf.field("format").rules, {"allowed": [(2, 2)]})
        self.assertEqual(conf.field("required_mask").rules,
                         {"nonzero": True, "bits_require": (0x0F00, "expected_module_class", "nonzero")})
        self.assertEqual(conf.field("required_encoder_mask").rules["bits_require"],
                         (0x0FF0, "expected_encoder_expansion_class", 1))
        self.assertEqual(conf.field("timing_11").rules, {"allowed": [(100, 1023)]})
        self.assertEqual(conf.field("servo_period_us").rules, {"allowed": [(250, 2500)]})
        page1 = s.layout("configure_io_page1_at_16")
        self.assertEqual(page1.field("probe1_capture_sources").rules,
                         {"allowed": [(0x00, 0x0B), (0x10, 0x1B), (0x20, 0x20), (0xFF, 0xFF)]})
        self.assertEqual(page1.field("pwm1_flags").rules, {"zero": True})


if __name__ == "__main__":
    unittest.main()
