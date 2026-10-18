"""Independent bounded old/native continuity and clock-tap negative controls."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_io_control import validate as vi
from hardware_validate_motherboard_acc_control import validate as va
from hardware_validate_motherboard_do import native
class ClockTapTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.io=json.loads((ROOT/'hardware/motherboard_io_control/design.json').read_text())
  cls.acc=json.loads((ROOT/'hardware/motherboard_acc_control/design.json').read_text())
 def test_native_exact_old_pins_except_four_previously_NC(self):
  for directory,changes in [('motherboard_io_control',{'U13001':'44','U13004':'29','U13008':'29'}),('motherboard_acc_control',{'U14501':'44'})]:
   prior=ROOT/'reports/motherboard-iol1-firmware-20260930/clock-taps-r01/prior/hardware'/directory
   current=ROOT/'hardware'/directory
   old=json.loads((prior/'design.json').read_text())['components'];new=json.loads((current/'design.json').read_text())['components']
   new_native=native(current/'netlist.xml');old_native=native(prior/'netlist.xml')
   self.assertEqual(set(new)-set(old),{'R13057','R13058','R13059'} if len(changes)==3 else {'R14533'})
   for ref,part in old.items():
    expected=copy.deepcopy(part);np=copy.deepcopy(old_native[ref])
    if ref in changes:
     pin=changes[ref];self.assertIsNone(part['pins'][pin]);self.assertIsNone(np['pins'][pin])
     expected['pins'][pin]=new[ref]['pins'][pin];np['pins'][pin]=new[ref]['pins'][pin]
    self.assertEqual(new[ref],expected,ref);self.assertEqual(new_native[ref],np,ref)
 def test_every_tap_endpoint_is_exact_native(self):
  rows=[(self.io,'U13001','44','R13057','DIC',0),(self.io,'U13004','29','R13058','DOA',1),(self.io,'U13008','29','R13059','DOB',2),(self.acc,'U14501','44','R14533','ACC',3)]
  for model,mc,pin,r,name,slot in rows:
   self.assertEqual(model['components'][mc]['pins'][pin],f'IOL1_L{slot}_SCLK_COUNT')
   self.assertEqual(model['components'][r]['pins'],{'1':name+'_IOL1_CLK_MCU','2':f'IOL1_L{slot}_SCLK_COUNT'})
 def test_absent_taps_are_not_valid_byte_counter_proof(self):
  for m,ref in [(self.io,'R13057'),(self.io,'R13058'),(self.io,'R13059'),(self.acc,'R14533')]:
   d=copy.deepcopy(m);del d['components'][ref];self.assertFalse((vi if m is self.io else va)(d)['ok'])
 def test_prebuffer_clock_would_be_a_different_electrical_input(self):
  for m,ref in [(self.io,'R13057'),(self.io,'R13058'),(self.io,'R13059'),(self.acc,'R14533')]:
   d=copy.deepcopy(m);d['components'][ref]['pins']['1']='IOL1_L0_SCLK';self.assertFalse((vi if m is self.io else va)(d)['ok'])
 def test_PB5_does_not_steal_sensor_or_AO_GPIO(self):
  for m,ref,pin in [(self.io,'U13001','43'),(self.acc,'U14501','43')]:
   d=copy.deepcopy(m);d['components'][ref]['pins'][pin]='IOL1_L3_SCLK_COUNT';self.assertFalse((vi if m is self.io else va)(d)['ok'])
 def test_nonzero_series_was_not_silently_substituted(self):
  d=copy.deepcopy(self.io);d['components']['R13057']['resistance_ohm']=10000;self.assertFalse(vi(d)['ok'])
if __name__=='__main__':unittest.main()
