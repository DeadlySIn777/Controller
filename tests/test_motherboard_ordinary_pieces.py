"""Real ordinary112 SOURCE inventory and bounded native piece admission."""
from pathlib import Path
import sys,copy,tempfile,json,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
try:
 import pcbnew
 import hardware_route_ordinary_wip_r05 as h
except ModuleNotFoundError:pcbnew=None
@unittest.skipUnless(pcbnew,'KiCad actual native runtime required')
class OrdinaryPieces(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.dir=ROOT/'reports/motherboard-ordinary-routing-20261001/actual-source26-root62-r01'
  cls.boardpath=ROOT/'reports/motherboard-pcb-integration-20261001/source26-orphan-free-adopted-r62/motherboard-source26-WIP.kicad_pcb'
  cls.manifest=h.engine.read(cls.dir/'manifest.json');cls.proof=h.engine.read(cls.dir/'piece-eligibility.json')
  cls.board=pcbnew.LoadBoard(str(cls.boardpath));_,cls.nodes=h.engine.native_source_check(cls.board,h.engine.read(ROOT/'hardware/motherboard/design.json'),ROOT/'hardware/motherboard/netlist.xml')
  cls.nets={str(n)for n in cls.board.GetNetsByName()};cls.layers=[cls.board.GetLayerName(n)for n in cls.board.GetEnabledLayers().CuStack()]
 def test_actual_all_112_keep_original_validator(self):
  h.dependencies();rows=h.engine.manifest_check(self.manifest,self.nets,self.layers,self.nodes);self.assertEqual(112,len(rows))
 def test_exact_scope_retains_all_failures_and_never_whole_net_pass(self):
  proof=h.pieces.verify_receipt(self.dir/'piece-eligibility.json',self.boardpath,self.manifest['nets'])
  self.assertEqual(42,len(proof['eligible_filled_components']));self.assertEqual(15,len(proof['complete_unanchored_components']))
  self.assertFalse(proof['whole_return_net_qualification']);self.assertFalse(proof['whole_board_reference_qualification'])
 def test_fake_whole_net_pass_or_unanchored_admission_rejected(self):
  for mode in ['whole','piece']:
   bad=copy.deepcopy(self.proof)
   if mode=='whole':bad['whole_return_net_qualification']=True
   else:bad['eligible_filled_components'].append(bad['complete_unanchored_components'][0])
   with tempfile.TemporaryDirectory()as t:
    p=Path(t)/'fake.json';p.write_text(json.dumps(bad))
    with self.assertRaises(ValueError):h.pieces.verify_receipt(p,self.boardpath,self.manifest['nets'])
 def test_clock_or_changed_endpoint_cannot_enter(self):
  name=next(iter(self.manifest['nets']))
  for field,v in [('maximum_voltage_v',24),('source_pins',[['U1001','A1'],['U1001','A2']]),('signal_class','IOL1')]:
   bad=copy.deepcopy(self.manifest);bad['nets'][name][field]=v
   with self.assertRaises(ValueError):h.engine.manifest_check(bad,self.nets,self.layers,self.nodes)
if __name__=='__main__':unittest.main()
