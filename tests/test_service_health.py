import struct
import unittest
import zlib
from controller_lab.service_health import encode_health


class ServiceFrameTests(unittest.TestCase):
    def setUp(self):
        self.args = dict(boot_id=0x0102030405060708, sequence=9,
                        completed_cycle_counter=12, uptime_ms=1000,
                        reported_disarmed=True, reported_fault=False)

    def test_wire_format_and_independent_crc(self):
        frame = encode_health(**self.args)
        self.assertEqual(len(frame), 40)
        self.assertEqual(frame[:8], b'ESV1\x01\x01\x1c\x00')
        self.assertEqual(frame[8:16], b'\x08\x07\x06\x05\x04\x03\x02\x01')
        self.assertEqual(struct.unpack('<IIQI', frame[16:36]), (9,12,1000,1))
        self.assertEqual(struct.unpack('<I',frame[36:])[0], zlib.crc32(frame[:36]))

    def test_zero_progress_is_permitted_without_claiming_progress(self):
        self.args['completed_cycle_counter'] = 0
        self.assertEqual(encode_health(**self.args)[20:24], b'\x00'*4)

    def test_all_advisory_flag_combinations(self):
        for disarmed in [False,True]:
            for fault in [False,True]:
                self.args.update(reported_disarmed=disarmed, reported_fault=fault)
                self.assertEqual(encode_health(**self.args)[32], int(disarmed)+2*int(fault))

    def test_integer_ranges_and_boolean_confusion(self):
        for field, bad in [('boot_id',0),('boot_id',2**64),('sequence',-1),
                           ('sequence',2**32),('sequence',True),('uptime_ms',-1),
                           ('uptime_ms',1.0),('completed_cycle_counter',2**32)]:
            with self.subTest(field=field, bad=bad):
                args = dict(self.args); args[field]=bad
                with self.assertRaises(ValueError): encode_health(**args)

    def test_flags_require_boolean(self):
        for field in ['reported_disarmed','reported_fault']:
            args=dict(self.args); args[field]=1
            with self.assertRaises(ValueError): encode_health(**args)


if __name__ == '__main__':
    unittest.main()
