"""Independent fault mutations of actual supply/inhibit connectivity."""
import copy
from itertools import product
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_power_entry import validate, inhibit_screen, evaluate_graph, parent_interposition_rules
from hardware_build_assembly import parse,children,child,value


def polygon_record(pad):
    at=[float(v) for v in child(pad,'at')[1:3]]
    pts=child(child(child(pad,'primitives'),'gr_poly'),'pts')
    return at,[[float(p[1])+at[0],float(p[2])+at[1]] for p in children(pts,'xy')]


def inside_winding(poly,p):
    # Independently implemented winding-number anchor test, not builder raycast.
    winding=0
    for a,b in zip(poly,poly[1:]+poly[:1]):
        cross=(b[0]-a[0])*(p[1]-a[1])-(p[0]-a[0])*(b[1]-a[1])
        if a[1]<=p[1]<b[1] and cross>0:winding+=1
        if b[1]<=p[1]<a[1] and cross<0:winding-=1
    return winding!=0


class MotherboardPowerEntryTests(unittest.TestCase):
    def setUp(self):
        self.model=json.loads((ROOT/'hardware/motherboard_power_entry/design.json').read_text(encoding='utf8'))
        self.tree=ET.parse(ROOT/'hardware/motherboard_power_entry/netlist.xml')
    def find(self,kind,predicate=lambda p:True):
        return next((r,p) for r,p in self.model['components'].items() if p['kind']==kind and predicate(p))
    def errors(self):return validate(self.model,self.tree)
    def test_actual_native_contract_and_purchasing_population(self):
        self.assertEqual(self.errors(),[])
        self.assertEqual(sum(p['physical'] for p in self.model['components'].values()),220)
        self.assertTrue(all(p['mpn'] and p['footprint'] and not p.get('selection_required') for p in self.model['components'].values() if p['physical']))
    def test_32_actual_pin_graph_truth_cases(self):
        for bits in product((False,True),repeat=5):
            result=evaluate_graph(self.model,*bits);core,fa,fb,ga,gb=bits
            self.assertEqual(result['MOTOR_TX_GATE_A'],core and fa and ga)
            self.assertEqual(result['MOTOR_TX_GATE_B'],core and fb and gb)
    def test_fault_on_either_bank_does_not_cross_other_bank(self):
        result=evaluate_graph(self.model,True,False,True,True,True)
        self.assertEqual(result,{'MOTOR_TX_GATE_A':False,'MOTOR_TX_GATE_B':True})
    def test_driver_polarity_swap_rejected_and_truth_changes(self):
        _,p=self.find('LVC2G07',lambda p:p['pins']['5']=='FIELD_5V');p['pins']['1']='MOTOR_FIELD_HEALTH_A_RAW'
        self.assertTrue(self.errors())
        self.assertFalse(evaluate_graph(self.model,True,True,True,True,True)['MOTOR_TX_GATE_A'])
    def test_direct_inhibit_cannot_be_replaced_by_iso_output(self):
        _,p=self.find('LVC2G04',lambda p:p['pins']['5']=='FIELD_5V');p['pins']['1']='MOTOR_POWER_OK_A_QUALIFIED'
        self.assertTrue(self.errors())
    def test_gate_contact_bypass_rejected(self):
        _,p=self.find('TLP3640A',lambda p:p['pins']['4']=='MOTOR_TX_GATE_A');p['pins']['3']='MOTOR_TX_GATE_SOURCE_A'
        self.assertTrue(self.errors())
    def test_nc_contact_substitution_rejected(self):
        _,p=self.find('TLP3640A');p['mpn']='TLP4176A(TP,F';self.assertTrue(self.errors())
    def test_wrong_powered_leakage_driver_rejected(self):
        _,p=self.find('LVC2G07');p['mpn']='BSS138P,215';self.assertTrue(self.errors())
    def test_open_final_gate_pulldown_rejected(self):
        r,_=self.find('R',lambda p:set(p['pins'].values())=={'MOTOR_TX_GATE_A','LOGIC_GND'});del self.model['components'][r]
        self.assertTrue(self.errors())
    def test_feed_latch_requires_actual_five_volt_domain(self):
        _,p=self.find('LVC1G74');p['pins']['8']='IO_3V3';self.assertTrue(self.errors())
    def test_active_low_clear_and_rearm_are_not_tied_high(self):
        _,p=self.find('LVC1G74');p['pins']['6']='MOTION_5V_RAW';self.assertTrue(self.errors())
    def test_tps22990_ep_is_input_not_ground(self):
        _,p=self.find('FEED',lambda p:p['pins']['8']=='MOTOR_5V_A');p['pins']['11']='LOGIC_GND';self.assertTrue(self.errors())
    def test_actual_buck_inductor_cannot_be_omitted(self):
        r,_=self.find('L',lambda p:p['pins']['1']=='MOTION_CORE_SW');del self.model['components'][r];self.assertTrue(self.errors())
    def test_actual_six_milliohm_shunt_cannot_be_omitted(self):
        r,_=self.find('R',lambda p:p.get('resistance_ohm')==.006 and p['pins']['2']=='CORE_5V');del self.model['components'][r];self.assertTrue(self.errors())
    def test_reverse_fet_orientation_is_not_assumed_from_erc(self):
        _,p=self.find('QREV');p['pins']['1'],p['pins']['5']=p['pins']['5'],p['pins']['1'];self.assertTrue(self.errors())
    def test_field_returns_not_bridged_to_logic(self):
        _,p=self.find('FIELD_LDO',lambda p:p['pins']['1']=='DOB_FIELD_3V3');p['pins']['4']='LOGIC_GND';self.assertTrue(self.errors())
    def test_tps2662_rtn_must_remain_separate_from_ground(self):
        _,p=self.find('AUX24');p['pins']['5']='FIELD_GND';self.assertTrue(self.errors())
    def test_aux_limit_not_unpublished_interpolation(self):
        _,p=self.find('R',lambda p:p['pins'].get('1')=='AUX24_A_ILIM');p['resistance_ohm']=60400;self.assertTrue(self.errors())
    def test_limited_field_envelope_cannot_replace_requirement(self):
        self.model['inherited_requirements']['field24_requirement_v']=[19,29];self.assertTrue(self.errors())
    def test_clean_erc_never_confers_readiness(self):
        self.model['manufacturing_ready']=True;self.assertTrue(self.errors())
    def test_unselected_part_is_a_source_error(self):
        _,p=self.find('R');p['mpn']='';self.assertTrue(self.errors())
    def test_native_switch_ep_function_must_be_input(self):
        self.tree.find(".//libpart[@part='FEED']/pins/pin[@num='11']").set('name','EP_GND')
        self.assertTrue(self.errors())
    def test_native_lvc_dff_clock_pin_must_not_swap_data(self):
        self.tree.find(".//libpart[@part='LVC1G74']/pins/pin[@num='1']").set('name','D')
        self.assertTrue(self.errors())
    def test_tcr_is_in_conditional_current_and_leakage_screen(self):
        s=inhibit_screen();self.assertAlmostEqual(s['ordinary_resistor_corner_including_initial_and_0_to55c_tcr'],.013)
        self.assertGreater(s['series_led_current_a'][0],.005)
        self.assertLess(s['series_led_current_a'][1],.020)
        self.assertLess(s['gate_off_v_with_two_contact_leaks'],.8)
        self.assertGreater(s['final_gate_high_min_v_at_2p4v_source_testpoint'],2)
        self.assertFalse(s['opening_at_actual5p36_to18p94ma_or_alltemperatures_guaranteed'])
        self.assertFalse(s['whole20ms_watchdog_physical_or_allcondition_proof'])
    def test_parent_change_is_exactly_two_driver_pins(self):
        rules=parent_interposition_rules()['exactly_two_output_pin_changes_permitted']
        self.assertEqual(rules['A']['old_driver'],['U6042','7'])
        self.assertEqual(rules['B']['old_driver'],['U6042','3'])
        for bank in ('A','B'):
            self.assertTrue(rules[bank]['final_consumers_must_remain_exact'])
            self.assertNotIn(rules[bank]['old_driver'],rules[bank]['final_consumers_must_remain_exact'])
    def test_every_custom_copper_anchor_is_inside_its_manufacturer_polygon(self):
        for path in (ROOT/'hardware/motherboard_power_entry/CNC_MB_Entry.pretty').glob('*.kicad_mod'):
            for pad in children(parse(path.read_text()),'pad'):
                if child(pad,'primitives') is None:continue
                anchor,poly=polygon_record(pad)
                for dx in (-.0005,.0005):
                    for dy in (-.0005,.0005):self.assertTrue(inside_winding(poly,[anchor[0]+dx,anchor[1]+dy]),(path.name,pad[1]))
    def test_old_concave_anchor_is_a_real_negative_case(self):
        prior=ROOT/'reports/motherboard-power-entry-20260930/prior-r02-before-native-pad-repair/hardware/motherboard_power_entry/CNC_MB_Entry.pretty'
        for name,n in [('LMR36506_RPE9_TI','4'),('TPS22990_DML10_TI','8')]:
            pad=next(p for p in children(parse((prior/(name+'.kicad_mod')).read_text()),'pad') if value(p[1])==n)
            anchor,poly=polygon_record(pad);self.assertFalse(inside_winding(poly,anchor))
    def test_converter_vector_normalization_matches_six_annotated_bounds(self):
        pads=children(parse((ROOT/'hardware/motherboard_power_entry/CNC_MB_Entry.pretty/LM70660_RRX29_TI.kicad_mod').read_text()),'pad')
        for n,want in [('1',[-3.2,-.625,-3.2,-.484]),('20',[-.125,3.2,-2.1,-.14])]:
            pad=next(p for p in pads if value(p[1])==n);_,poly=polygon_record(pad)
            actual=[min(x for x,y in poly),max(x for x,y in poly),min(y for x,y in poly),max(y for x,y in poly)]
            for a,b in zip(actual,want):self.assertAlmostEqual(a,b,delta=.00003)
    def test_nexfet_exact_pitch_copper_and_stencil_not_stock_rounding(self):
        self.assertTrue(all(p['footprint']=='CNC_MB_Entry:CSD19537Q3_TI' for _,p in self.model['components'].items() if p['kind']=='QREV'))
        pads=children(parse((ROOT/'hardware/motherboard_power_entry/CNC_MB_Entry.pretty/CSD19537Q3_TI.kicad_mod').read_text()),'pad')
        for n,x in enumerate([-.975,-.325,.325,.975],1):
            pad=next(p for p in pads if value(p[1])==str(n));self.assertEqual(list(map(float,child(pad,'at')[1:3])),[x,1.435]);self.assertEqual(list(map(float,child(pad,'size')[1:3])),[.5,.63])
        paste=[p for p in pads if value(p[1])=='']
        self.assertEqual(len(paste),10)
        sizes=sorted(tuple(map(float,child(p,'size')[1:3])) for p in paste)
        self.assertEqual(sizes,[(.34,.45)]*8+[(1.02,1.445)]*2)


if __name__=='__main__':unittest.main()
