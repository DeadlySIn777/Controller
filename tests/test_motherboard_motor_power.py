import copy
import hashlib
from itertools import product
import json
from pathlib import Path
import re
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_motor_power import validate, analytical_screen, evaluate_actual_health


class MotorPowerTests(unittest.TestCase):
    def setUp(self):
        self.model=json.loads((ROOT/'hardware/motherboard_motor_power/design.json').read_text(encoding='utf-8'))
        self.tree=ET.parse(ROOT/'hardware/motherboard_motor_power/netlist.xml')
        self.fps={p.stem:p.read_text(encoding='utf-8') for p in (ROOT/'hardware/motherboard_motor_power/CNC_MotorPower.pretty').glob('*.kicad_mod')}
    def errors(self):return validate(self.tree,self.model,self.fps)
    def test_complete_native_contract(self):self.assertEqual(self.errors(),[])
    def test_frozen_motor_source_unchanged(self):
        receipt=json.loads((ROOT/'reports/motherboard-motors-20260930/receipt-r02.json').read_text(encoding='utf-8'))
        for path,want in receipt['hashes'].items():
            if path.startswith('hardware/') or path.startswith('tools/') or path.startswith('tests/'):
                self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),want,path)
    def test_all_256_valid_supply_truth_cases(self):
        names=('IO_3V3','MOTOR_5V_A','MOTOR_5V_B','AUX_5V_A','AUX_24V_A','AUX_5V_B','AUX_24V_B','FIELD_5V')
        for bits in product((False,True),repeat=8):
            s=dict(zip(names,bits));result=evaluate_actual_health(self.model,s)
            for bank in ('A','B'):
                self.assertEqual(result[f'MOTOR_POWER_OK_{bank}_QUALIFIED'],s['IO_3V3'] and s[f'MOTOR_5V_{bank}'] and s[f'AUX_5V_{bank}'] and s[f'AUX_24V_{bank}'] and s['FIELD_5V'])
    def test_no_physical_or_full_range_claim(self):
        screen=analytical_screen()
        self.assertFalse(screen['arbitrary_partial_power_proven'])
        self.assertFalse(screen['full_18_to30v_aux24_acceptance_proven'])
        self.assertFalse(screen['supplies_or_limiters_fitted'])
        self.assertTrue(screen['iso7720_supply_1p7_to2p25_undetermined'])
    def test_static_threshold_bounds_include_bias_temp_and_drift(self):
        screen=analytical_screen();self.assertEqual(screen['precision_r_corner_fraction_including_drift'],.001)
        for window in screen['windows']:self.assertTrue(window['static_bounds_pass'],window['rail'])
        self.assertGreater(screen['windows'][4]['uv_v'][0],4.8)
        self.assertLess(screen['windows'][4]['uv_v'][1],4.875)
        self.assertGreater(screen['windows'][5]['uv_v'][0],18)
        self.assertLess(screen['windows'][5]['ov_v'][1],30)
    def test_default_high_isolator_substitution_rejected(self):
        self.model['components']['U9007']['mpn']='ISO7720DWR';self.assertTrue(self.errors())
    def test_isolator_ground_bridge_rejected(self):
        self.model['components']['U9007']['pins']['1']='LOGIC_GND';self.assertTrue(self.errors())
    def test_isolator_wrong_package_pin_rejected(self):
        self.model['components']['U9007']['pins']['3']='MOTOR_FIELD_HEALTH_A_RAW';self.assertTrue(self.errors())
    def test_ov_comparator_wrong_config_rejected(self):
        self.model['components']['U9003']['pins']['7']='MOTOR_PWR_REF_FIELD_A';self.assertTrue(self.errors())
    def test_rst_disable_bypass_rejected(self):
        self.model['components']['U9001']['pins']['1']='LOGIC_GND';self.assertTrue(self.errors())
    def test_mr_disabled_or_grounded_rejected(self):
        self.model['components']['U9001']['pins']['2']='LOGIC_GND';self.assertTrue(self.errors())
    def test_missing_receiving5_monitor_rejected(self):
        self.model['components']['U9002']['pins']['16']='CORE_5V';self.assertTrue(self.errors())
    def test_qualified_high_constant_rejected(self):
        self.model['components']['U9008']['pins']['2']='IO_3V3';self.assertTrue(self.errors())
    def test_weak_1pct_precision_substitution_rejected(self):
        self.model['components']['R9021']['initial_tolerance']=.01;self.assertTrue(self.errors())
    def test_removal_of_raw_health_pulldown_rejected(self):
        del self.model['components']['R9010'];self.assertTrue(self.errors())
    def test_aux5_monitor_not_upstream_fictitious_rail(self):
        self.model['components']['R9021']['pins']['1']='FIELD_5V';self.assertTrue(self.errors())
    def test_full18_to30_acceptance_not_silently_substituted(self):
        self.model['contract']['aux24_static_acceptance_limit_v']=[18,30];self.assertTrue(self.errors())
    def test_partial_power_not_promoted_by_passed_erc(self):
        self.model['arbitrary_partial_power_qualified']=True;self.assertTrue(self.errors())
    def test_changed_native_pin_function_rejected(self):
        pin=self.tree.find(".//libpart[@part='ISO7720F']/pins/pin[@num='3']");pin.attrib['name']='INA';self.assertTrue(self.errors())
    def test_iso_land_width_substitution_rejected(self):
        self.fps['ISO7720_DW16_TI_HV'],changed=re.subn(r'\(size 1\.65 (?:0)?\.6\)','(size 2 0.6)',self.fps['ISO7720_DW16_TI_HV'])
        self.assertEqual(changed,16);self.assertTrue(self.errors())
    def test_ltc_thermal_pad_type_must_stay_smd(self):
        self.fps['LTC2962_UD16']=self.fps['LTC2962_UD16'].replace('(pad "17" smd','(pad "17" thru_hole');self.assertTrue(self.errors())


if __name__=='__main__':unittest.main()
