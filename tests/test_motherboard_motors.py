import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from hardware_build_motherboard_motors import description
from hardware_validate_motherboard_motors import validate


class MotherboardMotorTests(unittest.TestCase):
    def setUp(self):self.model=description()
    def result(self):return validate(self.model,verify_sources=False)
    def test_complete_source_contract(self):self.assertTrue(self.result()['passed'])
    def test_all12_fitted_no_general_io_consumed(self):
        self.assertEqual(self.result()['device_counts']['TLP3640A'],12)
        self.assertEqual(self.model['general_di_consumed'],0)
        self.assertEqual(self.model['general_do_consumed'],0)
    def test_wrong_load_switch_pinout_rejected(self):
        c=next(p for p in self.model['components'].values() if p['kind']=='TPS22918');c['pins']['1'],c['pins']['6']=c['pins']['6'],c['pins']['1'];self.assertFalse(self.result()['passed'])
    def test_reverse_differential_polarity_rejected(self):
        c=self.model['components'][self.model['channels'][0]['tx_ref']];c['pins']['2'],c['pins']['3']=c['pins']['3'],c['pins']['2'];self.assertFalse(self.result()['passed'])
    def test_enable_pull_on_dead_source_rail_rejected(self):
        c=self.model['components'][self.model['channels'][11]['enable_pullup']];c['pins']['2']='IO_3V3';self.assertFalse(self.result()['passed'])
    def test_enable_per_channel_shortcut_rejected(self):
        ch=self.model['channels'][10];self.model['components'][ch['enable_sink_ref']]['pins'][str(ch['enable_sink_input_pin'])]='EN9_N_TO_MX4';self.assertFalse(self.result()['passed'])
    def test_grounded_alarm_substrate_rejected(self):
        ch=self.model['channels'][0];self.model['components'][ch['alarm_receiver_ref']]['pins']['13']='FIELD_GND';self.assertFalse(self.result()['passed'])
    def test_cross_domain_alarm_return_rejected(self):
        ch=self.model['channels'][0];self.model['components'][ch['alarm_receiver_ref']]['pins']['14']='LOGIC_GND';self.assertFalse(self.result()['passed'])
    def test_removed_bank_power_inhibit_rejected(self):
        c=next(p for p in self.model['components'].values() if p['kind']=='LVC2G08');c['pins']['6']='MOTOR_IO_3V3';self.assertFalse(self.result()['passed'])
    def test_opi_must_see_exact_physical_gate(self):
        c=next(p for p in self.model['components'].values() if p['kind']=='LVC1G74');c['pins']['6']='TX_PERMIT_A_TO_MIA';self.assertFalse(self.result()['passed'])
    def test_relay_drains_and_leds_not_swapped(self):
        c=self.model['components'][self.model['channels'][4]['enable_nc_ref']];c['pins']['2'],c['pins']['3']=c['pins']['3'],c['pins']['2'];self.assertFalse(self.result()['passed'])
    def test_host_check_never_claims_physical_timing(self):
        r=self.result();self.assertFalse(r['manufacturing_ready']);self.assertFalse(r['calculations']['fault_to_inhibit_20ms_proven']);self.assertFalse(r['calculations']['qualified_filter_proven'])
    def test_inverted_sink_polarity_is_not_substituted(self):
        c=next(p for p in self.model['components'].values() if p['kind']=='LVC07A');c['mpn']='74LVC06APW,118';self.assertFalse(self.result()['passed'])
    def test_original_ti_sink_without_powered_high_ioz_rejected(self):
        c=next(p for p in self.model['components'].values() if p['kind']=='LVC07A');c['mpn']='SN74LVC07APWR';self.assertFalse(self.result()['passed'])
    def test_direct_gate_inhibit_cannot_be_bypassed(self):
        ch=self.model['channels'][7];self.model['components'][ch['enable_nand_ref']]['pins'][str(ch['enable_nand_b_pin'])]='MOTOR_IO_3V3';self.assertFalse(self.result()['passed'])
    def test_nand_cannot_be_replaced_by_and(self):
        ch=self.model['channels'][0];self.model['components'][ch['enable_nand_ref']]['kind']='LVC08A';self.assertFalse(self.result()['passed'])
    def test_pin_map_metadata_cannot_hide_a_wrong_hex_pin_tuple(self):
        ch=self.model['channels'][0];ch['enable_sink_input_pin']=2;ch['enable_sink_output_pin']=1;self.assertFalse(self.result()['passed'])
    def test_qualifier_only_one_edge_variant_rejected(self):
        c=next(p for p in self.model['components'].values() if p['kind']=='LTC6994');c['mpn']='LTC6994IS6-1#TRPBF';self.assertFalse(self.result()['passed'])
    def test_qualifier_wrong_div_code_rejected(self):
        c=next(p for p in self.model['components'].values() if p['kind']=='LTC6994');c['pins']['4']='MOTOR_5V_A';self.assertFalse(self.result()['passed'])
    def test_raw_ttl_signal_cannot_directly_drive_qualifier(self):
        c=next(p for p in self.model['components'].values() if p['kind']=='LTC6994');c['pins']['1']='TX_PERMIT_A_TO_MIA';self.assertFalse(self.result()['passed'])
    def test_changed_setting_resistor_is_not_accepted_by_derived_arithmetic(self):
        c=next(p for p in self.model['components'].values() if p['role']=='permission digital qualification RSET');c['resistance_ohm']=500000;self.assertFalse(self.result()['passed'])
    def test_25c_timer_error_not_used_for_full_temperature(self):
        self.model['source_contract']['ltc_full_temperature_delay_error']=.051;self.assertFalse(self.result()['passed'])
    def test_merged_isolated_substrate_islands_rejected(self):
        ch=self.model['channels'][0];self.model['components'][ch['alarm_receiver_ref']]['pins']['13']='ALM1_SUB_FLOAT';self.assertFalse(self.result()['passed'])
    def test_dark_and_armed_truth_table_all_channels(self):
        r=self.result();rows=r['calculations']['enable_truth_table'];self.assertEqual({(v['en_n'],v['gate']):v['led_on'] for v in rows},{(0,0):False,(0,1):True,(1,0):False,(1,1):False})
        self.assertTrue(r['calculations']['powered_high_output_leakage_guarantee_closed']);self.assertEqual(r['calculations']['powered_high_dark_margin_ratio_25c'],10)


if __name__=='__main__':unittest.main()
