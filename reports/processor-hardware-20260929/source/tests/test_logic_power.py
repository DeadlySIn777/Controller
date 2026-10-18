"""Independent exported-circuit mutations; no physical device access."""
import copy
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from tools.hardware_validate_logic_power import validate

OUT=Path(__file__).resolve().parents[1]/"hardware/logic_power"


class LogicPowerTests(unittest.TestCase):
    def setUp(self):
        self.tree=ET.parse(OUT/"netlist.xml")
        self.design=json.loads((OUT/"input-electrical-design.json").read_text(encoding="utf-8"))
        self.model=json.loads((OUT/"design-envelope.json").read_text(encoding="utf-8"))
        self.footprints={p.stem:p.read_text(encoding="utf-8") for p in (OUT/"CNC_Power.pretty").glob("*.kicad_mod")}

    def check(self):return validate(self.tree,self.design,self.model,self.footprints)

    def net(self,name):return self.tree.find(f".//nets/net[@name='/{name}']")

    def move(self,source,dest,ref,pin):
        node=self.net(source).find(f"node[@ref='{ref}'][@pin='{pin}']")
        self.net(source).remove(node);self.net(dest).append(node)

    def test_real_exports_match_three_frozen_rail_loads(self):
        self.assertEqual([],self.check())

    def test_independent_esp_and_io_outputs_cannot_be_merged(self):
        self.move("ESP_3V3","IO_3V3","JOUT1","5")
        self.assertTrue(self.check())

    def test_inductor_cannot_be_bypassed(self):
        self.move("CORE_1V2","CORE_1V2_SW","JOUT1","1")
        self.assertTrue(self.check())

    def test_kelvin_sense_cannot_read_switch_node(self):
        self.move("IO_3V3","IO_3V3_SW","U2","3")
        self.assertTrue(self.check())

    def test_uncontrolled_pg_to_enable_cascade_is_rejected(self):
        self.move("IO_3V3_EN","CORE_1V2_PG_OD","U2","5")
        self.assertTrue(self.check())

    def test_enable_cannot_float_or_default_high(self):
        self.move("LOGIC_GND","CORE_5V","R2","2")
        self.assertTrue(self.check())
        self.setUp()
        self.net("CORE_1V2_EN").remove(self.net("CORE_1V2_EN").find("node[@ref='R2']"))
        self.assertTrue(self.check())

    def test_vset_and_mode_population_are_electrical_not_software_choices(self):
        for ref,value in (("R5","49.9k 1%"),("R8","76.8k 1%")):
            with self.subTest(ref=ref):
                self.setUp();self.tree.find(f".//comp[@ref='{ref}']/value").text=value
                self.assertTrue(self.check())
        self.setUp();self.move("LOGIC_GND","CORE_1V2","U1","9")
        self.assertTrue(self.check())

    def test_softstart_cannot_be_omitted_or_misvalued(self):
        self.tree.find(".//comp[@ref='C6']/value").text="680pF 50V C0G"
        self.assertTrue(self.check())
        self.setUp();ET.SubElement(self.tree.find(".//comp[@ref='C6']"),"property",name="dnp")
        self.assertTrue(self.check())

    def test_input_capacitor_package_corrects_reference_table_typo(self):
        self.tree.find(".//comp[@ref='C1']/footprint").text="Capacitor_SMD:C_0805_2012Metric"
        self.assertTrue(self.check())

    def test_tps62160_substitution_does_not_inherit_voltage_and_ramp_evidence(self):
        self.tree.find(".//comp[@ref='U1']/fields/field[@name='MPN']").text="TPS62160DSGR"
        self.assertTrue(self.check())

    def test_pg_open_drain_and_return_paths_are_required(self):
        self.tree.find(".//libpart[@part='TPS62901RPJR']/pins/pin[@num='1']").attrib['type']='output'
        self.assertTrue(self.check())
        self.setUp();self.net("LOGIC_GND").remove(self.net("LOGIC_GND").find("node[@ref='U3'][@pin='4']"))
        self.assertTrue(self.check())

    def test_original_rail_tolerance_or_current_budget_cannot_silently_change(self):
        next(r for r in self.design['rails'] if r['id']=='CORE_1V2')['max_v']=1.3
        self.assertTrue(self.check())
        self.setUp();next(r for r in self.design['power_loads'] if r['id']=='esp_peak')['budget_a']=1.2
        self.assertTrue(self.check())
        self.setUp();next(r for r in self.design['rails'] if r['id']=='CORE_5V')['max_v']=24
        self.assertTrue(self.check())

    def test_analytical_values_must_be_finite_and_exactly_recomputed(self):
        for section,key,value in (("soft_start","model_min_us",float('nan')),("soft_start","nominal_us",55),
                                  ("magnetics","effective_l_model_min_uh",2.2),("capacitors","input_effective_min_required_uf",0)):
            with self.subTest(key=key):
                model=copy.deepcopy(self.model);model[section][key]=value
                self.assertTrue(validate(self.tree,self.design,model,self.footprints))
        self.model['rails'][0]['input_a_at_85pct_efficiency_plus_50ma']=float('inf')
        self.assertTrue(self.check())

    def test_pg_discharge_and_physical_claims_remain_bounded(self):
        for key,value in (("complete_fpga_sequence",True),("pg_is_machine_permission",True),
                          ("pg_valid_below_vin_1v8",True),("discharge_guaranteed_without_input",True),
                          ("thermal_auto_restart",False),("independent_esp_input_isolation",True)):
            with self.subTest(key=key):
                model=copy.deepcopy(self.model);model['boundaries'][key]=value
                self.assertTrue(validate(self.tree,self.design,model,self.footprints))

    def test_rpj9_pad_number_and_vset_pad_geometry_are_not_a_ground_paddle(self):
        self.footprints['TPS62901_RPJ9']=self.footprints['TPS62901_RPJ9'].replace('(pad "9"','(pad "4"')
        self.assertTrue(self.check())

    def test_inductor_land_pattern_uses_center_spacing_not_gap(self):
        self.footprints['XGL4020']=self.footprints['XGL4020'].replace('-1.185','-1.675').replace('1.185','1.675')
        self.assertTrue(self.check())


if __name__=="__main__":unittest.main()
