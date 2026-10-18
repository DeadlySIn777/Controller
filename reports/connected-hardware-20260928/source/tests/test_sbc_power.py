import copy
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from tools.hardware_validate_sbc_power import validate,analyze

ROOT=Path(__file__).resolve().parents[1]
class SBCPowerTests(unittest.TestCase):
    def setUp(self):
        self.tree=ET.parse(ROOT/'hardware/sbc_power/netlist.xml')
        self.design=json.loads((ROOT/'hardware/sbc_power/design-envelope.json').read_text())
    def move(self,ref,pin,to):
        target=next(n for n in self.tree.findall('.//nets/net') if n.attrib['name'].lstrip('/')==to)
        for n in self.tree.findall('.//nets/net'):
            for p in n.findall('node'):
                if (p.attrib['ref'],p.attrib['pin'])==(ref,str(pin)):n.remove(p);target.append(p);return
        self.fail('pin missing')
    def reject(self):self.assertTrue(validate(self.tree,self.design))
    def test_actual_topology_and_bounds(self):
        self.assertEqual([],validate(self.tree,self.design))
        result=analyze(self.design)
        self.assertTrue(result['host_min_v_ge4p75'])
        self.assertTrue(result['rising_max_below_regulated4p95v'])
        self.assertTrue(result['qod_discharge_pass_if_powered'])
        self.assertFalse(result['short_current_limit_implemented'])
        self.assertFalse(result['production_qualified'])
    def test_switch_thermal_pad_is_vin_never_ground(self):self.move('U1',11,'LOGIC_GND');self.reject()
    def test_one_output_pin_cannot_bypass_switch(self):self.move('U1',9,'CORE_5V');self.reject()
    def test_supervisor_must_not_power_from_host_rail(self):self.move('U2',4,'SBC_5V');self.reject()
    def test_supervisor_must_sense_unswitched_rail(self):self.move('RHI1',1,'SBC_5V');self.reject()
    def test_hardware_enable_cannot_be_permanently_high(self):self.move('U1',5,'CORE_5V');self.reject()
    def test_ct_cannot_be_removed(self):
        ET.SubElement(self.tree.find(".//components/comp[@ref='CTSW1']"),'property',{'name':'dnp'});self.reject()
    def test_ct_rating_cannot_silently_drop_below_internal_voltage(self):
        self.tree.find(".//components/comp[@ref='CTSW1']/value").text='1uF6.3V X7R';self.reject()
    def test_default_enable_pulldown_cannot_float(self):self.move('RPD1',2,'SBC_5V');self.reject()
    def test_pg_is_not_a_push_pull_source(self):
        self.tree.find(".//libpart[@part='TPS22990DMLR']/pins/pin[@num='7']").attrib['type']='output';self.reject()
    def test_wrong_supervisor_threshold_variant_rejected(self):
        self.tree.find(".//components/comp[@ref='U2']/fields/field[@name='MPN']").text='TPS389033DSET';self.reject()
    def test_unsafe_numeric_parameters_rejected(self):
        for bad in (True,float('nan'),float('inf'),-1,'1mF',10**10000):
            d=copy.deepcopy(self.design);d['bounds']['sbc_charge_cap_max_f']=bad
            with self.subTest(kind=type(bad).__name__),self.assertRaises(ValueError):analyze(d)
    def test_host_cap_increase_changes_charge_and_discharge(self):
        base=analyze(self.design);self.design['bounds']['sbc_charge_cap_max_f']*=3
        revised=analyze(self.design)
        self.assertGreater(revised['host_charge_current_a_assumed'],base['host_charge_current_a_assumed'])
        self.assertFalse(revised['qod_discharge_pass_if_powered'])
    def test_output_drop_is_not_ignored(self):
        self.design['bounds']['trace_contact_resistance_max_ohm']=.1
        self.assertFalse(analyze(self.design)['host_min_v_ge4p75'])
    def test_retained_delay_cap_cannot_claim_full_reset_delay_or_discharge(self):
        self.design['bounds']['supervisor_delay_cap_initial_v_assumed']=[1.17,1.17]
        result=analyze(self.design)
        self.assertEqual(result['supervisor_delay_min_s'],0)
        self.assertFalse(result['qod_discharge_pass_if_powered'])
        self.assertFalse(result['arbitrary_warm_reset_minimum_delay_proven'])

if __name__=='__main__':unittest.main()
