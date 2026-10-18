"""Fault-focused mutations of native 16-path receiver connectivity/defaults."""
import copy
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from tools.hardware_validate_motherboard_fast_inputs import validate

ROOT=Path(__file__).resolve().parents[1]


class MotherboardFastInputTests(unittest.TestCase):
    def setUp(self):
        self.tree=ET.parse(ROOT/'hardware/motherboard_fast_inputs/netlist.xml')
        self.model=json.loads((ROOT/'hardware/motherboard_fast_inputs/design.json').read_text())

    def net(self,name):return self.tree.find(f"./nets/net[@name='/{name}']")
    def check(self):return validate(self.tree,self.model)

    def test_all_four_ABZ_and_frequency_MPG_paths_match_native_mapping(self):self.assertEqual([],self.check())

    def test_differential_pair_polarity_swap_is_rejected(self):
        p=self.net('ENC3_Z_P').find("node[@ref='U3']")
        n=self.net('ENC3_Z_N').find("node[@ref='U3']")
        p.attrib['pin'],n.attrib['pin']=n.attrib['pin'],p.attrib['pin']
        self.assertTrue(self.check())

    def test_frequency_and_MPG_feedback_swap_is_rejected(self):
        a=self.net('FREQ1_FPGA').find("node[@ref='B8']")
        b=self.net('MPG_A_FPGA').find("node[@ref='B8']")
        a.attrib['pin'],b.attrib['pin']=b.attrib['pin'],a.attrib['pin']
        self.assertTrue(self.check())

    def test_enables_must_be_always_on_without_floating_logic(self):
        for ref in ('U1','U2','U3','U4'):
            with self.subTest(ref=ref):
                t=copy.deepcopy(self.tree);n=t.find("./nets/net[@name='/IO_3V3']")
                n.remove(n.find(f"node[@ref='{ref}'][@pin='4']"))
                self.assertTrue(validate(t,self.model))

    def test_missing_local_bypass_is_rejected(self):
        n=self.net('LOGIC_GND');n.remove(n.find("node[@ref='C7']"));self.assertTrue(self.check())

    def test_5V_port_rails_cannot_be_unprotected_or_cross_connected(self):
        n=self.net('ENC3_5V_LIMITED');x=n.find("node[@ref='B7']");n.remove(x)
        self.net('ENC0_5V_LIMITED').append(x);self.assertTrue(self.check())

    def test_chassis_cannot_be_shortened_to_logic_ground_by_annotation(self):
        n=self.net('CHASSIS');x=n.find("node[@ref='B1']");n.remove(x)
        self.net('LOGIC_GND').append(x);self.assertTrue(self.check())

    def test_TTL_MPG_cannot_silently_gain_120ohm_reference_loading(self):
        r=self.tree.find("./components/comp[@ref='R15']")
        r.remove(r.find("property[@name='dnp']"));self.assertTrue(self.check())

    def test_termination_cannot_be_shortened_or_underpowered(self):
        self.tree.find("./components/comp[@ref='R1']/value").text='0R / FIT';self.assertTrue(self.check())

    def test_unknown_connector_cannot_become_fitted_by_clearing_boundary_flags(self):
        b=self.tree.find("./components/comp[@ref='B5']")
        b.remove(b.find("property[@name='exclude_from_board']"));self.assertTrue(self.check())

    def test_package_and_pin_count_cannot_be_silently_substituted(self):
        self.tree.find("./components/comp[@ref='U4']/footprint").text='Package_SO:SOIC-16_3.9x9.9mm_P1.27mm';self.assertTrue(self.check())

    def test_source_model_pin_and_physical_flag_must_match_native_XML(self):
        self.model['components']['U1']['pins']['4']='LOGIC_GND';self.assertTrue(self.check())

    def test_physical_qualification_and_arithmetic_must_not_be_invented(self):
        for key,val in [('physical_thermal_qualified',True),('worst_w_per_fitted_channel',float('nan')),('maximum_applied_differential_v',14)]:
            with self.subTest(key=key):
                m=copy.deepcopy(self.model);m['termination'][key]=val;self.assertTrue(validate(self.tree,m))


if __name__=='__main__':unittest.main()
