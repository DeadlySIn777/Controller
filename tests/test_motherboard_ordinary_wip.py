"""Actual ordinary inventory and bounded admission; no invented global plane pass."""
from pathlib import Path
import copy,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
try:
 import pcbnew
 import hardware_route_ordinary_wip_r04 as h
except ModuleNotFoundError:pcbnew=None
@unittest.skipUnless(pcbnew,'Actual KiCad native runtime required')
class OrdinaryWIP(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.review=h.engine.read(ROOT/h.SOURCE)
  cls.board=pcbnew.LoadBoard(str(ROOT/'reports/motherboard-pcb-integration-20261001/source26-entry-return-r56/motherboard-bounded-merged-candidate.kicad_pcb'))
  _,cls.nodes=h.engine.native_source_check(cls.board,h.engine.read(ROOT/'hardware/motherboard/design.json'),ROOT/'hardware/motherboard/netlist.xml')
  cls.nets={str(n)for n in cls.board.GetNetsByName()}
  cls.layers=[cls.board.GetLayerName(layer)for layer in cls.board.GetEnabledLayers().CuStack()]
 def test_all_actual_112_rows_keep_original_validator_and_source_inventory(self):
  h.dependencies()
  rows=h.engine.manifest_check(self.review,self.nets,self.layers,self.nodes)
  self.assertEqual(112,len(rows));self.assertEqual({'/LOGIC_GND'},{r['return_net']for r in rows.values()})
 def test_changed_class_voltage_or_endpoint_is_rejected(self):
  name=next(iter(self.review['nets']))
  for field,value in [('signal_class','isolated_ADC_DAC_SPI'),('maximum_voltage_v',24),('source_pins',[['U1001','A1'],['U1001','A2']])]:
   bad=copy.deepcopy(self.review);bad['nets'][name][field]=value
   with self.assertRaises(ValueError):h.engine.manifest_check(bad,self.nets,self.layers,self.nodes)
 def test_clock_name_cannot_be_promoted_into_ordinary(self):
  bad=copy.deepcopy(self.review);row=bad['nets'].pop(next(iter(bad['nets'])))
  bad['nets']['/IOL1_L0_SCLK']=row
  with self.assertRaises(ValueError):h.engine.manifest_check(bad,self.nets|{'/IOL1_L0_SCLK'},self.layers,self.nodes)
 def test_actual_unanchored_logic_resources_are_not_silently_qualified(self):
  d=ROOT/'reports/motherboard-return-zoning-20261001/source26-r56-AO1-secondary-return-r04'
  with self.assertRaisesRegex(ValueError,'unanchored'):
   h.scope.qualify(d/'board-bound-native-resource-review.json',ROOT/'reports/motherboard-domains-20261001/source26-r56-AO1-closed-r01/domain-map.json',['/LOGIC_GND'])
if __name__=='__main__':unittest.main()
