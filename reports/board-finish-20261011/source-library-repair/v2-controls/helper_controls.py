"""Tiny isolated at-run helper rejection controls; frozen v2 is read-only."""
import hashlib, importlib.util, json, sys, tempfile, types, unittest
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
V2 = HERE.parent/'v2'
spec = importlib.util.spec_from_file_location('frozen_restore_v2', V2/'restore_libraries.py')
C = importlib.util.module_from_spec(spec); sys.modules[spec.name] = C; spec.loader.exec_module(C)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


class Controls(unittest.TestCase):
    def test_equal_runtime_closure_passes(self):
        before = C.helper_identities(); self.assertEqual(C.verify_helpers(before), before)

    def test_changed_helper_bytes_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            path = Path(directory)/'fixture_helper.py'; path.write_text('VALUE = 1\n')
            module = types.ModuleType('isolated_changed_helper'); module.__file__ = str(path)
            sys.modules[module.__name__] = module
            try:
                expected = C.helper_identities(); path.write_text('VALUE = 2\n')
                with self.assertRaisesRegex(ValueError, 'At-run imported helper identities changed'):
                    C.verify_helpers(expected)
            finally: sys.modules.pop(module.__name__, None)

    def test_new_transitive_helper_after_start_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            expected = C.helper_identities(); path = Path(directory)/'late_helper.py'; path.write_text('VALUE = 1\n')
            module = types.ModuleType('isolated_late_transitive'); module.__file__ = str(path)
            sys.modules[module.__name__] = module
            try:
                with self.assertRaisesRegex(ValueError, 'At-run imported helper identities changed'):
                    C.verify_helpers(expected)
            finally: sys.modules.pop(module.__name__, None)

    def test_required_project_helper_omission_rejected(self):
        module = sys.modules.pop('project_clone')
        try:
            with self.assertRaisesRegex(ValueError, 'Expected imported helper closure incomplete'):
                C.helper_identities()
        finally: sys.modules['project_clone'] = module


def main():
    files = {str(path): sha(path) for path in V2.rglob('*') if path.is_file()}
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
    with (HERE/'controls.log').open('w', encoding='utf-8') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    if not result.wasSuccessful(): raise ValueError('Host helper control failure')
    if any(sha(Path(path)) != digest for path, digest in files.items()): raise ValueError('Frozen v2 changed')
    receipt = {'verdict': 'PASS', 'controls': result.testsRun, 'controls_log_sha256': sha(HERE/'controls.log'),
               'script_sha256': sha(Path(__file__)), 'v2_receipt_sha256': sha(V2/'receipt.json'),
               'frozen_v2_files_unchanged': True, 'native_jobs': 0, 'adopted': False}
    (HERE/'receipt.json').write_text(json.dumps(receipt, indent=1)+'\n', encoding='utf-8')
    print(json.dumps(receipt))


if __name__ == '__main__': main()
