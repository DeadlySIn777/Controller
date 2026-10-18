"""Host tests for record_evidence.py guards (no build, WSL or device needed).

    python -m pytest -q firmware/esp32_service/tests/test_record_evidence.py
"""
import importlib.util
import os
import pathlib
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('record_evidence', HERE.parent / 'record_evidence.py')
record_evidence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(record_evidence)


def touch(path, mtime):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'x')
    os.utime(path, (mtime, mtime))


class StaleImageGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_image_newer_than_inputs_is_accepted(self):
        touch(self.root / 'src.c', 1000)
        touch(self.root / 'cnc_service.bin', 2000)
        self.assertEqual(record_evidence.stale_inputs(
            self.root / 'cnc_service.bin', [self.root / 'src.c']), [])

    def test_input_newer_than_image_is_reported(self):
        touch(self.root / 'cnc_service.bin', 1000)
        touch(self.root / 'src.c', 2000)
        stale = record_evidence.stale_inputs(self.root / 'cnc_service.bin', [self.root / 'src.c'])
        self.assertEqual(stale, [str(self.root / 'src.c')])

    def test_missing_image_is_reported(self):
        touch(self.root / 'src.c', 1000)
        self.assertEqual(len(record_evidence.stale_inputs(
            self.root / 'missing.bin', [self.root / 'src.c'])), 1)

    def test_refuse_stale_images_exits_for_newer_sdkconfig(self):
        build_dir = self.root / 'build'
        touch(build_dir / 'cnc_service.bin', 10 ** 10)  # newer than every real input
        sdkconfig = self.root / 'uart-sdkconfig'
        touch(sdkconfig, 10 ** 10 + 5)                    # generated config changed later
        variants = [('uart-compile-check', build_dir, sdkconfig, [], 'log', 'img')]
        with self.assertRaises(SystemExit) as raised:
            record_evidence.refuse_stale_images(variants)
        self.assertIn('uart-sdkconfig', str(raised.exception))
        os.utime(sdkconfig, (10 ** 10 - 5, 10 ** 10 - 5))
        record_evidence.refuse_stale_images(variants)     # no exit once the image is newer

    def test_real_firmware_inputs_exist(self):
        for name in record_evidence.FIRMWARE_INPUTS:
            self.assertTrue((record_evidence.HERE / name).is_file(), name)
        self.assertIn('firmware/esp32_service/sdkconfig', record_evidence.SOURCES)

    def test_unrun_host_log_is_not_carried_forward(self):
        touch(self.root / record_evidence.HOST_LOG, 1000)
        self.assertTrue(record_evidence.drop_unrun_host_log(self.root))
        self.assertFalse((self.root / record_evidence.HOST_LOG).exists())
        self.assertFalse(record_evidence.drop_unrun_host_log(self.root))


if __name__ == '__main__':
    unittest.main()
