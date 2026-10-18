import copy,importlib.util,json,unittest,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('esp_socket_validation',ROOT/'tools/hardware_validate_motherboard_esp_socket.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class EspSocketTests(unittest.TestCase):
 def setUp(self):
  self.tree=ET.parse(ROOT/'hardware/motherboard_esp_socket/netlist.xml');self.model=json.loads((ROOT/'hardware/motherboard_esp_socket/design.json').read_text())
 def check(self):return v.validate(self.tree,self.model)
 def mutate(self,ref,pin,name):
  nets=self.tree.getroot().find('nets')
  for net in list(nets):
   for node in list(net):
    if node.attrib.get('ref')==ref and node.attrib.get('pin')==pin:
     net.remove(node);target=next((n for n in nets if n.attrib['name']==name),None)
     if target is None:target=ET.SubElement(nets,'net',{'name':name,'code':'998877'})
     target.append(node);return
  self.fail('Missing mutation pin')
 def test_native_contract(self):self.assertEqual([],self.check())
 def test_reverse_blocker_ce_ground_is_rejected(self):
  self.mutate('U16002','3','/LOGIC_GND');self.assertTrue(any('CE must observe' in e for e in self.check()))
 def test_reverse_blocker_input_output_bypass_rejected(self):
  self.mutate('U16002','1','/ESP_HEADER_5V');self.assertTrue(any('input/output bypassed' in e for e in self.check()))
 def test_uart_power_may_not_use_motherboard_io3(self):
  self.mutate('U16003','5','/IO_3V3');self.assertTrue(any('actual module LDO' in e for e in self.check()))
 def test_uart0_collision_rejected(self):
  self.mutate('J16002','3','/ESP_SERVICE_RX');self.assertTrue(any('CP2102' in e for e in self.check()))
 def test_no_esp_tx_authority(self):
  self.mutate('J16002','2','/MACHINE_REQUEST');self.assertTrue(any('TX must have no' in e for e in self.check()))
 def test_module_gpio18_exact_header_contact(self):
  self.assertEqual('18',self.model['components']['J16001']['module_manufacturer_pin_names']['11'])
  self.assertEqual(18,self.model['selected_connections']['RX_GPIO'])
 def test_two_actual_socket_rows_and_purchased_board_separate(self):
  self.assertEqual('61302211821',self.model['components']['J16001']['mpn']);self.assertEqual('61302211821',self.model['components']['J16002']['mpn'])
  self.assertEqual(22,len(self.model['components']['J16001']['pins']));self.assertFalse(self.model['purchased_module']['included_in_PCB_BOM'])
  self.assertFalse(any(p['mpn'].startswith('ESP32') for p in self.model['components'].values()))
 def test_not_ready_by_erc(self):
  self.model['manufacturing_ready']=True;self.assertTrue(any('cannot claim' in e for e in self.check()))
 def test_simultaneous_usb_power_not_claimed(self):
  self.model['branch_power']['simultaneous_USB_and_header_power_qualified']=True;self.assertTrue(any('mutually exclusive' in e for e in self.check()))
if __name__=='__main__':unittest.main()
