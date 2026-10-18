"""Meaningful isolated host rejection controls; never change frozen inputs."""
import copy, hashlib, importlib.util, json, sys, tempfile, types, unittest
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import measure_combined_r1 as M
class Controls(unittest.TestCase):
 def test_exact_combined_replay(self):
  report=M.validate_construction(M.V.FAG/'staged/construction.json',M.V.FAG/'staged/r07-four-path-fag-repaired.kicad_pcb')
  self.assertEqual(report['total_new_copper_items'],287)
 def test_changed_candidate_refused(self):
  raw=(M.V.FAG/'staged/r07-four-path-fag-repaired.kicad_pcb').read_bytes()
  with tempfile.TemporaryDirectory() as folder:
   candidate=Path(folder)/'bad.pcb';candidate.write_bytes(raw.replace(b'(at 357.05 201.25)',b'(at 357.06 201.25)',1))
   self.assertNotEqual(candidate.read_bytes(),raw)
   with self.assertRaises(ValueError):M.validate_construction(M.V.FAG/'staged/construction.json',candidate)
 def test_edited_construction_refused(self):
  receipt=json.loads((M.V.FAG/'staged/construction.json').read_bytes());receipt['scope_A']=3.6
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'receipt.json';path.write_text(json.dumps(receipt))
   with self.assertRaises(ValueError):M.validate_construction(path,M.V.FAG/'staged/r07-four-path-fag-repaired.kicad_pcb')
 def test_live_loss_fatal(self):self.assertEqual(M.combined_verdict({'verdict':'FAIL'},{'verdict':'PASS'},0),'FAIL')
 def test_r06_loss_fatal(self):self.assertEqual(M.combined_verdict({'verdict':'PASS'},{'verdict':'FAIL'},0),'FAIL')
 def test_one_drc_error_fatal(self):self.assertEqual(M.combined_verdict({'verdict':'PASS'},{'verdict':'PASS'},1),'FAIL')
 def test_equal_inputs_and_bytes_changed(self):
  with tempfile.TemporaryDirectory() as folder:
   out=Path(folder);inputs={'native_binaries':{}};M.write(out/'inputs.json',inputs);digest=M.digest((out/'inputs.json').read_bytes())
   original=M.binary_identities;M.binary_identities=lambda reads:{}
   try:
    M.verify_inputs(out,inputs,digest,M.ReadSet());(out/'inputs.json').write_bytes((out/'inputs.json').read_bytes()+b' ')
    with self.assertRaises(ValueError):M.verify_inputs(out,inputs,digest,M.ReadSet())
   finally:M.binary_identities=original
 def test_changed_helper_and_late_helper(self):
  module=types.ModuleType('isolated_control_helper')
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'helper.py';path.write_text('x=1\n');module.__file__=str(path);sys.modules[module.__name__]=module
   try:
    original=M.helper_identities();M.verify_helpers(original);path.write_text('x=2\n')
    with self.assertRaises(ValueError):M.verify_helpers(original)
    path.write_text('x=1\n');late=types.ModuleType('late_isolated_control_helper');late.__file__=str(path);sys.modules[late.__name__]=late
    try:
     with self.assertRaises(ValueError):M.verify_helpers(original)
    finally:del sys.modules[late.__name__]
   finally:del sys.modules[module.__name__]
 def test_missing_required_helper(self):
  old=sys.modules.pop('project_clone')
  try:
   with self.assertRaises(ValueError):M.helper_identities()
  finally:sys.modules['project_clone']=old
 def test_original_source_precheck(self):
  with tempfile.TemporaryDirectory(dir=HERE) as folder:
   args=types.SimpleNamespace(out=Path(folder),candidate=M.V.FAG/'staged/r07-four-path-fag-repaired.kicad_pcb',before_board=M.V.F.R07)
   result=M.prepare_source(args);M.verify_source(args,result)
   self.assertEqual(result['saved_export_sha256'],M.NETLIST_SHA)
   self.assertEqual(result['host_parity']['verdict'],'PASS')
   (args.out/'source/sch.net').chmod(0o600)
   (args.out/'source/sch.net').write_bytes((args.out/'source/sch.net').read_bytes()+b' ')
   with self.assertRaises(ValueError):M.verify_source(args,result)

if __name__=='__main__':unittest.main(verbosity=2)
