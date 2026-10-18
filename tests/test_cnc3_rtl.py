"""Guarded frozen-input/reproducibility checks; functional cases run compiled RTL."""
from pathlib import Path
import hashlib, importlib.util, json, shutil, subprocess, tempfile, unittest

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'gateware/v3'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load_generator(path):
    spec=importlib.util.spec_from_file_location('cnc3_rtl_generator_for_test',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

class CNC3FrozenInputs(unittest.TestCase):
    def test_exact_original_reference_hashes(self):
        manifest=json.loads((PACKAGE/'frozen/manifest.json').read_text())
        self.assertFalse(manifest['stateful_endpoint_implemented'])
        self.assertFalse(manifest['HAL_implemented'])
        for relative,sha in manifest['files'].items():
            self.assertEqual(digest(PACKAGE/'frozen'/relative),sha,relative)

    def test_generator_readonly_reproduction(self):
        before={str(p):digest(p) for p in PACKAGE.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        module=load_generator(PACKAGE/'tools/generate_protocol_rtl.py');module.build()
        self.assertEqual(before,{path:digest(Path(path)) for path in before})

    def test_changed_spec_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            dest=Path(folder)/'v3';shutil.copytree(PACKAGE,dest,ignore=shutil.ignore_patterns('__pycache__'))
            path=dest/'frozen/spec/protocol.json';path.write_bytes(path.read_bytes()+b'\n')
            module=load_generator(dest/'tools/generate_protocol_rtl.py')
            with self.assertRaisesRegex(ValueError,'Frozen input hash mismatch'):
                module.build()

    def test_stale_generated_validator_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            dest=Path(folder)/'v3';shutil.copytree(PACKAGE,dest,ignore=shutil.ignore_patterns('__pycache__'))
            path=dest/'rtl/cnc3_command_validate.v';path.write_text(path.read_text().replace("(mask & 16'hf000) != 0","1'b0"))
            module=load_generator(dest/'tools/generate_protocol_rtl.py')
            with self.assertRaisesRegex(ValueError,'Generated RTL is stale'):
                module.build()

    def test_actual_compiler_receipt_matches_five_rtl_sources(self):
        receipt=json.loads((ROOT/'reports/cnc3-rtl-implementation-20261001/shared-package-final-r02/receipt.json').read_text())
        self.assertEqual(receipt['status'],'PASS')
        self.assertTrue(receipt['source_hashes_unchanged'])
        self.assertFalse(receipt['stateful_CNC3_endpoint'])
        self.assertFalse(receipt['CNC3_HAL'])
        for path in (PACKAGE/'rtl').glob('*.v'):
            key='rtl/'+path.name
            self.assertEqual(digest(path),receipt['source_stage_hashes'][key],key)

    def test_actual_family_mapping_remains_distinct_from_fit_timing(self):
        receipt=json.loads((ROOT/'reports/cnc3-rtl-implementation-20261001/shared-package-final-r02/family-synthesis/receipt.json').read_text())
        self.assertEqual(receipt['status'],'PASS')
        self.assertTrue(receipt['source_unchanged'])
        self.assertTrue(receipt['required_outputs_present'])
        self.assertTrue(receipt['family_synthesis_only'])
        self.assertFalse(receipt['Efinity_fit_timing'])
        self.assertFalse(receipt['clock_frequency_qualified'])
        for path in (PACKAGE/'rtl').glob('*.v'):
            self.assertEqual(digest(path),receipt['source_hashes']['rtl/'+path.name])

if __name__=='__main__':unittest.main()
