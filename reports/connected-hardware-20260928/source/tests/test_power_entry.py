"""Mutate real exported entry connectivity; no electrical qualification implied."""
from pathlib import Path
import copy
import unittest
import xml.etree.ElementTree as ET
from tools.hardware_validate_power_entry import validate

ROOT=Path(__file__).resolve().parents[1]


class PowerEntryTests(unittest.TestCase):
    def setUp(self):self.tree=ET.parse(ROOT/'hardware/power_entry/netlist.xml')
    def net(self,name):return next(n for n in self.tree.findall('.//nets/net') if n.attrib['name'].lstrip('/')==name)
    def move(self,ref,pin,to):
        source=next(n for n in self.tree.findall('.//nets/net') if any(x.attrib.get('ref')==ref and x.attrib.get('pin')==str(pin) for x in n.findall('node')))
        node=next(x for x in source.findall('node') if (x.attrib['ref'],x.attrib['pin'])==(ref,str(pin)))
        source.remove(node);self.net(to).append(node)
    def reject(self):self.assertTrue(validate(self.tree))
    def test_actual_export_matches_independent_contract(self):self.assertEqual([],validate(self.tree))
    def test_reverse_blocking_fet_source_cannot_face_output(self):self.move('Q1',1,'C_IN');self.reject()
    def test_fast_gate_pulldown_source_is_raw_not_ground(self):self.move('Q2',2,'LOGIC_GND');self.reject()
    def test_fuse_cannot_be_bypassed_by_input_terminal(self):self.move('JIN1',1,'C_RAW');self.reject()
    def test_field_and_logic_returns_cannot_join(self):self.move('JIN2',2,'LOGIC_GND');self.reject()
    def test_field_fault_pullup_cannot_reach_logic_rail(self):self.move('R28',1,'IO_3V3');self.reject()
    def test_reset_contact_cannot_short_raw_supply(self):self.move('JRESET1',1,'C_RAW');self.reject()
    def test_exposed_ground_pad_cannot_float(self):self.move('U1',25,'C_IN');self.reject()
    def test_mode_cannot_silently_enable_auto_retry(self):self.move('U1',11,'LOGIC_GND');self.reject()
    def test_output_negative_clamp_cannot_be_reversed(self):self.move('D2',1,'LOGIC_GND');self.move('D2',2,'CORE_24V_PROTECTED');self.reject()
    def test_uvlo_ladder_cannot_be_rewired_as_ovp(self):self.move('U1',6,'C_OV');self.reject()
    def test_current_limit_value_change_requires_review(self):
        self.tree.find(".//components/comp[@ref='R4']/value").text='3.00k 0.1%';self.reject()
    def test_pulse_current_variant_cannot_replace_26630(self):
        self.tree.find(".//components/comp[@ref='U1']/fields/field[@name='MPN']").text='TPS26631RGER';self.reject()
    def test_unexpected_imon_capacitor_node_is_rejected(self):
        ET.SubElement(self.net('C_IMON'),'node',{'ref':'C99','pin':'1'});self.reject()
    def test_duplicate_pin_cannot_be_hidden_by_set_comparison(self):
        net=self.net('C_IN');net.append(copy.deepcopy(net.find('node')));self.reject()
    def test_duplicate_component_identity_is_rejected(self):
        comps=self.tree.find('.//components');comps.append(copy.deepcopy(comps.find('comp')));self.reject()
    def test_fuse_cannot_be_omitted_from_assembly(self):
        ET.SubElement(self.tree.find(".//components/comp[@ref='F1']"),'property',{'name':'dnp'});self.reject()
    def test_fault_pin_cannot_lose_open_drain_erc_type(self):
        self.tree.find(".//libpart[@part='TPS26630RGER']/pins/pin[@num='14']").set('type','passive');self.reject()
    def test_downstream_pgood_pullup_cannot_backfeed_unpowered_logic(self):
        ET.SubElement(self.net('C_PGOOD'),'node',{'ref':'R9','pin':'2'});self.reject()


if __name__=='__main__':unittest.main()
