"""Reject consequential DO pin/default/qualification errors in new source."""
from pathlib import Path
import copy
import importlib.util
import json
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'hardware/motherboard_do'
spec=importlib.util.spec_from_file_location('motherboard_do_validator',ROOT/'tools/hardware_validate_motherboard_do.py')
HW=importlib.util.module_from_spec(spec)
# Shared syntax parser only; pin/function expectations are independent.
import sys
sys.path.insert(0,str(ROOT/'tools'))
spec.loader.exec_module(HW)

class MotherboardOutputTests(unittest.TestCase):
    def setUp(self):self.d=json.loads((OUT/'design.json').read_text(encoding='utf-8'))
    def reject(self,fragment):
        result=HW.validate(self.d)
        self.assertFalse(result['ok'],result)
        self.assertTrue(any(fragment in e for e in result['errors']),result)
    def test_native_model_erc_and_exact_footprints_match(self):
        r=HW.validate(self.d,OUT/'netlist.xml',OUT/'erc.json',OUT/'CNC_MB_DO.pretty')
        self.assertTrue(r['ok'],r);self.assertFalse(r['manufacturing_ready']);self.assertFalse(r['physical_qualification'])
    def test_sixteenth_channel_is_real(self):
        del self.d['channels'][15];self.reject('capacity')
    def test_channels_do_not_alias(self):
        self.d['channels'][15]['logical_net']='DO14';self.reject('mapping')
    def test_bs_without_adc_cannot_replace_as(self):
        self.d['components']['U10004']['mpn']='TPS274C65BSRHAR';self.reject('TPS AS')
    def test_driver_vs_pin_cannot_float(self):
        self.d['components']['U10004']['pins']['16']=None;self.reject('physical pin/net')
    def test_driver_thermal_pad_is_field_ground(self):
        self.d['components']['U10022']['pins']['41']='LOGIC_GND';self.reject('physical pin/net')
    def test_dnc_is_not_ground_or_led(self):
        self.d['components']['U10009']['pins']['26']='FIELD_A_0V';self.reject('physical pin/net')
    def test_field_ground_does_not_cross_isolation(self):
        self.d['components']['U10016']['pins']['9']='LOGIC_GND';self.reject('physical pin/net')
    def test_default_high_isolator_rejected(self):
        self.d['components']['U10016']['mpn']='ISO7762DBQR';self.reject('default LOW')
    def test_isolator_control_output_cannot_be_fault_pin(self):
        p=self.d['components']['U10003']['pins'];p['12'],p['10']=p['10'],p['12'];self.reject('physical pin/net')
    def test_latch_cannot_skip_permission_drop_clear(self):
        self.d['components']['U10001']['pins']['6']='IO_3V3';self.reject('physical pin/net')
    def test_latch_cannot_auto_set_after_reset(self):
        self.d['components']['U10014']['pins']['1']='IO_3V3';self.reject('physical pin/net')
    def test_local_enable_cannot_bypass_hardwired_permission(self):
        self.d['components']['U10002']['pins']['9']='IO_3V3';self.reject('physical pin/net')
    def test_missing_controller_stays_off(self):
        r=next(ref for ref,p in self.d['components'].items() if p['kind']=='R' and p['pins']=={'1':'DOA_CARD_EN','2':'LOGIC_GND'})
        self.d['components'][r]['pins']['2']='IO_3V3';self.reject('fail-off bias')
    def test_field_do_enable_has_real_pulldown(self):
        r=next(ref for ref,p in self.d['components'].items() if p['kind']=='R' and p['pins']=={'1':'DOB_DO_EN_FIELD','2':'FIELD_B_0V'})
        self.d['components'][r]['resistance_ohm']=1000000;self.reject('field DO_EN')
    def test_rcb_mosfet_source_drain_cannot_reverse(self):
        fr=self.d['channels'][0]['rcb_fet'];p=self.d['components'][fr]['pins'];p['1'],p['5']=p['5'],p['1'];self.reject('physical pin/net')
    def test_rcb_mosfet_gate_is_pin4_after_rendered_topview_review(self):
        fr=self.d['channels'][4]['rcb_fet'];p=self.d['components'][fr]['pins'];p['4'],p['5']=p['5'],p['4'];self.reject('physical pin/net')
    def test_rcb_drain_ep_cannot_be_source(self):
        fr=self.d['channels'][15]['rcb_fet'];self.d['components'][fr]['pins']['9']='DO15_SW';self.reject('physical pin/net')
    def test_sense_filter_does_not_end_at_testpoint_only(self):
        self.d['components']['U10004']['pins']['6']='TEST_ONLY';self.reject('physical pin/net')
    def test_address_resistors_need_strictly_less_than_one_percent(self):
        r=next(ref for ref,p in self.d['components'].items() if p['role']=='addressed SPI identity resistor')
        self.d['components'][r]['tolerance']=.01;self.reject('<1%')
    def test_chip_addresses_are_unique_within_bank(self):
        self.d['components']['U10009']['spi_address']=0;self.reject('address/external')
    def test_tps_internal_regulators_cannot_parallel(self):
        self.d['components']['U10009']['pins']['29']=None;self.reject('physical pin/net')
    def test_por_125a_is_not_advertised_as_072a(self):
        self.d['driver_por_current_limit_a']=.72;self.reject('POR')
    def test_required_software_register_settings_cannot_be_marked_done(self):
        self.d['limits_enforced_by_firmware']=True;self.reject('not represented as qualified')
    def test_controller_and_field_rail_are_explicit_gaps(self):
        self.d['domains'][0]['field_logic_supply_implemented']=True;self.reject('unimplemented parent')
    def test_invented_fitted_connector_rejected(self):
        self.d['boundaries']['J10001']['physical']=True;self.reject('invented fitted')
    def test_adc_only_valid_while_on_and_unimplemented_readout(self):
        self.d['measurement']['host_measurement_implemented']=True;self.reject('ADC/readout')
    def test_ilim_zero_readback_and_crc_not_optional(self):
        self.d['register_requirements']['SW_STATE_zero_readback_before_CARD_EN']=False;self.reject('commissioning')
    def test_unqualified_inrush_and_parallel_tiers_rejected(self):
        for field in ['inrush_boost','parallel']:
            req=[{'continuous_a':.5,'code':6} for _ in range(16)];req[0][field]=True
            with self.subTest(field=field):
                with self.assertRaises(ValueError):HW.request_limits(req)
    def test_independent_pair_limits_not_fake_per_channel_setting(self):
        req=[{'continuous_a':.5,'code':6} for _ in range(16)];req[1]['code']=7
        with self.assertRaises(ValueError):HW.request_limits(req)
    def test_current_limit_nominal1a_exceeds_guaranteed1a_max(self):
        req=[{'continuous_a':.5,'code':8} for _ in range(16)]
        with self.assertRaises(ValueError):HW.request_limits(req)
    def test_actual2a_output_tier_not_qualified(self):
        req=[{'continuous_a':.5,'code':6} for _ in range(16)];req[0]['continuous_a']=2
        with self.assertRaises(ValueError):HW.request_limits(req)
    def test_native_pin_drift_is_caught_independently(self):
        with tempfile.TemporaryDirectory() as tmp:
            import xml.etree.ElementTree as ET
            p=Path(tmp)/'mutated.xml';t=ET.parse(OUT/'netlist.xml')
            target=next(n for n in t.getroot().findall('nets/net') if n.attrib['name']=='/DO00_RCB_GATE')
            target.attrib['name']='/DO00_SW';t.write(p,encoding='utf-8')
            self.assertFalse(HW.validate(self.d,p)['ok'])
    def test_rha_pin1_orientation_not_generic_numbering(self):
        with tempfile.TemporaryDirectory() as tmp:
            import shutil
            folder=Path(tmp);shutil.copytree(OUT/'CNC_MB_DO.pretty',folder,dirs_exist_ok=True)
            p=folder/'TPS274C65_RHA40_TI.kicad_mod';t=p.read_text();t=t.replace('(at -2.9 -2.25)','(at 2.9 -2.25)',1);p.write_text(t)
            self.assertFalse(HW.validate(self.d,fpdir=folder)['ok'])
    def test_dnh_offset_ep_and_source_pin_geometry_not_generic8pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            import shutil
            folder=Path(tmp);shutil.copytree(OUT/'CNC_MB_DO.pretty',folder,dirs_exist_ok=True)
            p=folder/'CSD19538_DNH8_TI.kicad_mod';p.write_text(p.read_text().replace('(at .3275 0)','(at 0 0)',1))
            self.assertFalse(HW.validate(self.d,fpdir=folder)['ok'])
    def test_erc_suppression_or_different_ground_warning_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'erc.json';e=json.loads((OUT/'erc.json').read_text());e['ignored_checks']=['pin_not_connected'];p.write_text(json.dumps(e))
            self.assertFalse(HW.validate(self.d,erc=p)['ok'])

if __name__=='__main__':unittest.main()
