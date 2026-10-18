from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from tools.hardware_validate_core_converter import validate

ROOT=Path(__file__).resolve().parents[1]
class CoreConverterTests(unittest.TestCase):
    def setUp(self):self.tree=ET.parse(ROOT/'hardware/core_converter/netlist.xml')
    def net(self,name):return next(n for n in self.tree.findall('.//nets/net') if n.attrib['name'].lstrip('/')==name)
    def move(self,ref,pin,to):
        for n in self.tree.findall('.//nets/net'):
            for p in n.findall('node'):
                if (p.attrib['ref'],p.attrib['pin'])==(ref,str(pin)):
                    n.remove(p);self.net(to).append(p);return
        self.fail('Missing pin')
    def reject(self):self.assertTrue(validate(self.tree))
    def test_actual_connection_contract(self):self.assertEqual([],validate(self.tree))
    def test_vin_thermal_power_land_cannot_be_grounded(self):self.move('U1',29,'LOGIC_GND');self.reject()
    def test_controller_ground_pad_cannot_be_switch_node(self):self.move('U1',30,'CORE_SW');self.reject()
    def test_current_sense_cannot_bypass_shunt(self):self.move('U1',11,'CORE_5V');self.reject()
    def test_fixed_voltage_selector_cannot_be_output_divider(self):self.move('RFBSEL1',2,'CORE_5V');self.reject()
    def test_enable_bias_cannot_depend_on_downstream_logic(self):self.move('RENHI1',1,'IO_3V3');self.reject()
    def test_bootstrap_cannot_return_to_ground(self):self.move('CBST1',2,'LOGIC_GND');self.reject()
    def test_compensation_zero_cannot_be_shorted_to_ground(self):self.move('RCOMP1',2,'LOGIC_GND');self.reject()
    def test_output_capacitance_cannot_silently_change(self):
        self.tree.find(".//components/comp[@ref='COUT1']/value").text='4.7uF';self.reject()
    def test_current_sense_resistor_cannot_be_omitted(self):
        ET.SubElement(self.tree.find(".//components/comp[@ref='RS1']"),'property',{'name':'dnp'});self.reject()
    def test_bulk_capacitor_polarity_cannot_reverse(self):
        self.move('CBULK1',1,'LOGIC_GND');self.reject()
    def test_bulk_capacitor_cannot_be_omitted(self):
        ET.SubElement(self.tree.find(".//components/comp[@ref='CBULK2']"),'property',{'name':'dnp'});self.reject()
    def test_old_compensation_rejected_after_bulk_change(self):
        self.tree.find(".//components/comp[@ref='CHF1']/value").text='47pF5% C0G';self.reject()
    def test_part_current_variant_cannot_change(self):
        self.tree.find(".//components/comp[@ref='U1']/fields/field[@name='MPN']").text='LM706A0RRXR';self.reject()
    def test_unknown_assembly_part_rejected(self):
        ET.SubElement(self.tree.find('.//components'),'comp',{'ref':'R99'});self.reject()
    def test_long_side_shunt_cannot_use_ordinary_1206_footprint(self):
        c=self.tree.find(".//components/comp[@ref='RS1']")
        f=c.find('footprint')
        if f is None:f=ET.SubElement(c,'footprint')
        f.text='Resistor_SMD:R_1206_3216Metric';self.reject()

if __name__=='__main__':unittest.main()
