"""Host check that the recorded CNC1 and spidev manifests match the bytes on disk.

Run from the workspace root: python -m unittest discover -s cnc1/tests -p test_evidence_manifests.py
The CNC1 check is skipped (not failed) when the ignored build output
cnc1/build/cnc1_sim.so is absent, as in a fresh checkout.
"""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]


def run(script):
    return subprocess.run([sys.executable, str(ROOT / 'cnc1/tools' / script), '--check'],
                          capture_output=True, text=True, cwd=ROOT)


class EvidenceManifestTests(unittest.TestCase):
    def test_cnc1_manifest_matches_current_bytes(self):
        if not (ROOT / 'cnc1/build/cnc1_sim.so').is_file():
            self.skipTest('cnc1/build/cnc1_sim.so is ignored build output and is absent')
        result = run('record_evidence.py')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_spidev_manifest_matches_current_bytes(self):
        result = run('record_spidev_evidence.py')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
