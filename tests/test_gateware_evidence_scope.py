"""Historical verifier checks in temporary copies, never execute an HDL tool."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[1]
FIXES = Path('reports/readiness-fixes-20261004')
SEPARATE = Path('reports/pre-hardware-characterization-20261001/stepgen12-sweep-r02/receipt.json')


class GatewareEvidenceScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        manifest = json.loads((PROJECT / 'gateware/validation/manifest.json').read_text())
        paths = [Path('gateware') / name for name in manifest['source_sha256']]
        paths += [Path('gateware/validation/manifest.json')]
        paths += [Path('gateware/validation') / name for name in manifest['evidence_sha256']]
        paths += [Path('gateware/tests/tb_stepgen12_characterization.sv'), SEPARATE,
                  FIXES / 'rtl-verifier-transition.json',
                  FIXES / 'before/gateware/tools/record_evidence.py']
        for relative in paths:
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT / relative, destination)

    def run_check(self):
        return subprocess.run([sys.executable, '-B', 'gateware/tools/record_evidence.py', '--check'],
                              cwd=self.root, capture_output=True, text=True, timeout=15)

    def mutate(self, relative, content=b'\n// changed test-only input\n'):
        path = self.root / relative
        path.write_bytes(path.read_bytes() + content)

    def test_historical_baseline_passes_with_explicit_separate_bench(self):
        before = {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.root.rglob('*') if p.is_file()}
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('252 v1 + 27 v2', result.stdout)
        self.assertIn('Historical recorder bytes verified', result.stdout)
        self.assertIn('Excluded independent characterization', result.stdout)
        after = {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_unknown_new_inventory_is_rejected(self):
        for relative in ('gateware/tests/new_baseline.sv', 'gateware/rtl/new_logic.v',
                         'gateware/tools/new_decoder.py'):
            with self.subTest(path=relative):
                path = self.root / relative
                path.write_text('test-only new file')
                result = self.run_check()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('unrecorded baseline-scope inventory', result.stderr)
                path.unlink()

    def test_new_runner_dependency_cannot_hide_behind_existing_pin(self):
        self.mutate('gateware/tools/run_tests.sh', b'\niverilog tests/new_baseline.sv\n')
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('baseline runner changed', result.stderr)

    def test_changed_pinned_rtl_or_bench_is_rejected(self):
        for relative in ('gateware/rtl/cnc_encoder.v', 'gateware/tests/tb_cnc_endpoint.sv',
                         'gateware/tests/vectors.hex', 'gateware/tools/protocol.py'):
            with self.subTest(path=relative):
                path = self.root / relative
                original = path.read_bytes()
                self.mutate(relative)
                result = self.run_check()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('changed ' + relative.removeprefix('gateware/'), result.stderr)
                path.write_bytes(original)

    def test_missing_pinned_dependency_is_rejected(self):
        (self.root / 'gateware/tests/vectors.hex').unlink()
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('missing baseline dependency tests/vectors.hex', result.stderr)

    def test_characterization_is_not_a_name_only_exclusion(self):
        self.mutate('gateware/tests/tb_stepgen12_characterization.sv')
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('independent characterization identity/evidence changed', result.stderr)

    def test_missing_or_changed_independent_receipt_is_rejected(self):
        path = self.root / SEPARATE
        self.mutate(SEPARATE)
        self.assertNotEqual(self.run_check().returncode, 0)
        path.unlink()
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_changed_historical_archive_is_rejected(self):
        self.mutate(FIXES / 'before/gateware/tools/record_evidence.py')
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('changed tools/record_evidence.py', result.stderr)

    def test_changed_current_verifier_is_rejected(self):
        self.mutate('gateware/tools/record_evidence.py', b'\n# test-only verifier edit\n')
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('changed tools/record_evidence.py', result.stderr)

    def test_missing_transition_is_rejected(self):
        (self.root / FIXES / 'rtl-verifier-transition.json').unlink()
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_removed_manifest_dependency_and_evidence_cannot_bypass(self):
        path = self.root / 'gateware/validation/manifest.json'
        manifest = json.loads(path.read_text())
        del manifest['source_sha256']['rtl/cnc_encoder.v']
        del manifest['evidence_sha256']['status_encoder.hex']
        path.write_text(json.dumps(manifest))
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('complete reviewed baseline dependency scope', result.stderr)
        self.assertIn('both required baseline evidence hashes', result.stderr)

    def test_changed_historical_evidence_is_rejected(self):
        self.mutate('gateware/validation/status_encoder.hex', b'00')
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('evidence changed or missing', result.stderr)


if __name__ == '__main__':
    unittest.main()
