import copy,json,unittest
import xml.etree.ElementTree as ET
from review import HERE,PINS,reconcile,read,primary_pins
class StatusDeallocation(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  i=HERE/'inputs';cls.m=read(i/'metadata.json');cls.x=ET.parse(i/'netlist.xml').getroot();cls.p=primary_pins(i/'t20-pinout.xlsx');cls.c=read(i/'copper-evidence.json')
 def args(self):return [copy.deepcopy(x) for x in (self.m,self.x,self.p,self.c)]
 def reject(self,f):
  args=self.args();f(*args)
  with self.assertRaises(ValueError):reconcile(*args)
 def test_actual_frozen_source(self):
  m,l,_=reconcile(*self.args());self.assertEqual((135,48,28),(m['assigned_user_pins'],m['free_user_gpio'],m['deallocated_user_pin_count']));self.assertEqual(7,len(l))
  self.assertEqual(self.m['exact_pin_rename_ledger'],m['exact_pin_rename_ledger'][:-7])
  self.assertEqual({'G12','G15','G16'} & {r['pin'] for r in l},set())
 def test_manufacturer_bank_mismatch(self):self.reject(lambda m,x,p,c:p['H13'].update(bank='BANK3E'))
 def test_manufacturer_row_mismatch(self):self.reject(lambda m,x,p,c:p['G14'].update(row=125))
 def test_real_old_net_must_match(self):
  self.reject(lambda m,x,p,c:next(n for n in x.findall('./nets/net') if n.attrib['name']=='/fpga_core/DOOR_STATUS_FPGA').attrib.update(name='/REAL_DI_STATUS'))
 def test_copper_cannot_be_silently_removed(self):self.reject(lambda m,x,p,c:c['rows'][0].update(track_or_via_items=1,zero_existing_copper=False))
 def test_old_direct_input_direction_must_match(self):self.reject(lambda m,x,p,c:m['desired_directions'].update(DOOR_STATUS_FPGA='output'))
 def test_not_generic_GPIO_rename(self):self.reject(lambda m,x,p,c:p['K14'].update(name='GPIOR_140'))
 def test_wrong_resource_baseline(self):self.reject(lambda m,x,p,c:m.update(assigned_user_pins=141))
if __name__=='__main__':unittest.main()
