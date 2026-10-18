"""Source-pin/connectivity fault injection for the T20 candidate, not physical tests."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('fpga_core_validation',ROOT/'tools/hardware_validate_fpga_core.py')
HW=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(HW)
OUT=ROOT/'hardware/fpga_core'


class FpgaCoreTests(unittest.TestCase):
    def setUp(self):
        self.d=json.loads((OUT/'design.json').read_text(encoding='utf-8'))
        self.a=json.loads((OUT/'pin-allocation.json').read_text(encoding='utf-8'))

    def reject(self,fragment):
        r=HW.validate(self.d,self.a)
        self.assertFalse(r['ok'],r)
        self.assertTrue(any(fragment in e for e in r['errors']),r)

    def test_actual_netlist_and_erc_match_reviewed_candidate(self):
        r=HW.validate(self.d,self.a,OUT/'netlist.xml',OUT/'erc.json')
        self.assertTrue(r['ok'],r);self.assertFalse(r['manufacturing_ready'])

    def test_independent_xlsx_extract_has_all_balls(self):
        p=HW.primary_pins();self.assertEqual(len(p),256)
        self.assertEqual(p['R1']['name'],'CDONE');self.assertEqual(p['P1']['name'],'CRESET_N')
        self.assertEqual(p['H3']['name'],'GPIOL_24_CLK0');self.assertEqual(p['K6']['name'],'VCCIO1A')

    def test_twelve_motor_and_four_encoder_unique_pin_capacity(self):
        u=self.a['user_allocations'];self.assertEqual(len(u),96)
        self.assertEqual(len({x['ball'] for x in u}),96)
        for i in range(12):
            for prefix in ('STEP','DIR','HOME','ALM'):
                self.assertEqual(sum(x['net']==f'{prefix}{i}_FPGA' for x in u),1)
        self.assertFalse(any(x['config'] for x in u))

    def test_core_pin_cannot_receive_3v3(self):
        self.d['components']['U1']['pins']['E9']='IO_3V3';self.a['pin_net']['E9']='IO_3V3'
        self.reject('supply/ground pin E9')

    def test_bank_supply_cannot_be_left_unconnected(self):
        del self.a['pin_net']['L6'];del self.d['components']['U1']['pins']['L6']
        self.reject('supply/ground pin L6')

    def test_missing_ground_ball(self):
        self.a['pin_net']['G8']='CORE_1V2';self.d['components']['U1']['pins']['G8']='CORE_1V2'
        self.reject('supply/ground pin G8')

    def test_cdones_pullup_may_not_be_5v(self):
        self.d['components']['R3']['pins']['1']='SIGNAL_5V';self.reject('R3 pull')

    def test_pushpull_service_reset_cannot_short_sequencer(self):
        self.d['components']['U3']['pins']['4']='FPGA_CRESET_N';self.reject('U3 exact')

    def test_user_reset_must_follow_local_service_reset(self):
        self.a['pin_net']['D5']='FPGA_CRESET_N';self.d['components']['U1']['pins']['D5']='FPGA_CRESET_N'
        self.reject('critical configuration')

    def test_clock_ordinary_pin_swap_is_detected(self):
        self.a['pin_net']['H3']='HOST_SPI_SCLK';self.d['components']['U1']['pins']['H3']='HOST_SPI_SCLK'
        self.reject('critical configuration')

    def test_dual_assignment_collision_is_detected(self):
        self.a['user_allocations'][1]['ball']=self.a['user_allocations'][0]['ball'];self.reject('unique user')

    def test_logic_net_collision_is_detected(self):
        self.a['user_allocations'][1]['net']=self.a['user_allocations'][0]['net'];self.reject('logical user signal collision')

    def test_configuration_pin_reuse_is_detected(self):
        self.a['user_allocations'][0].update({'ball':'L3','name':'GPIOL_08_CDI0','config':'CDI0','bank':'BANK1B','row':14})
        self.reject('configuration/native LVDS')

    def test_missing_configuration_strap(self):
        del self.d['components']['R5'];self.reject('component set')

    def test_flash_mosi_miso_swap(self):
        p=self.d['components']['U2']['pins'];p['2'],p['5']=p['5'],p['2'];self.reject('U2 exact')

    def test_native_lvds_reference_not_arbitrarily_grounded(self):
        self.a['pin_net']['R2']='LOGIC_GND';self.d['components']['U1']['pins']['R2']='LOGIC_GND'
        self.reject('REF_RES/native LVDS')

    def test_bypass_must_be_at_its_named_supply_ball(self):
        self.d['components']['C1']['pins']['1']='IO_3V3';self.reject('per-ball bypass')

    def test_bad_capacitor_voltage(self):
        self.d['components']['C30']['voltage_v']=2.5;self.reject('rating/return')

    def test_nonfinite_capacitance(self):
        self.d['components']['C30']['capacitance_f']=float('nan');self.reject('capacitance')

    def test_insufficient_support_budget(self):
        self.d['rails']['IO_3V3']['additional_support_reservation_a']=.04;self.reject('current reservation')

    def test_manufacturing_claim_refused(self):
        self.d['manufacturing_ready']=True;self.reject('unearned')

    def test_erasing_pin_source_hash_is_detected(self):
        self.d['source_sha256']['t20-pinout.xlsx']='0'*64;self.reject('source hash changed')

    def test_support_current_and_capacitance_screen(self):
        c=HW.calculations(self.d)
        self.assertLess(c['support_static_current_screen_a'],.06)
        self.assertLess(c['reset_high_z_screen_max_v'],.8)
        self.assertAlmostEqual(c['nominal_bypass_f']['CORE_1V2'],8.6e-6)
        self.assertAlmostEqual(c['nominal_bypass_f']['IO_3V3'],35.51e-6)
        self.assertEqual(c['single_image_bytes'],680700)

    def test_stale_or_modified_native_netlist_is_detected(self):
        tree=ET.parse(OUT/'netlist.xml');node=tree.find("components/comp[@ref='U2']/value");node.text='different_flash'
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'bad.xml';tree.write(path,encoding='utf-8')
            r=HW.validate(self.d,self.a,path);self.assertFalse(r['ok']);self.assertTrue(any('native export value' in e for e in r['errors']))

    def test_exported_package_pin_name_mutation_detected(self):
        tree=ET.parse(OUT/'netlist.xml');node=tree.find("libparts/libpart[@part='T20F256I4']/pins/pin[@num='K6']");node.set('name','VCC')
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'bad.xml';tree.write(path,encoding='utf-8')
            r=HW.validate(self.d,self.a,path);self.assertFalse(r['ok']);self.assertTrue(any('native symbol pin table' in e for e in r['errors']))

    def test_suppressed_erc_check_is_detected(self):
        j=json.loads((OUT/'erc.json').read_text());j['ignored_checks'].append({'key':'pin_to_pin','description':'bad'})
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'erc.json';path.write_text(json.dumps(j))
            r=HW.validate(self.d,self.a,erc=path);self.assertFalse(r['ok']);self.assertTrue(any('suppression' in e for e in r['errors']))


if __name__=='__main__':unittest.main()
