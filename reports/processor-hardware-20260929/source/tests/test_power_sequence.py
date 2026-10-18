"""Mutate actual KiCad export; simulation only and no physical interface access."""
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from tools.hardware_validate_power_sequence import validate, windows, enable_corners, reset_bounds

OUT=Path(__file__).resolve().parents[1]/'hardware/power_sequence'


class PowerSequenceTests(unittest.TestCase):
    def setUp(self):
        self.tree=ET.parse(OUT/'netlist.xml')
        self.design=json.loads((OUT/'input-electrical-design.json').read_text(encoding='utf-8'))
        self.model=json.loads((OUT/'design-envelope.json').read_text(encoding='utf-8'))
        self.footprint=(OUT/'CNC_Power.pretty/LTC2962_UD16.kicad_mod').read_text(encoding='utf-8')

    def errors(self):return validate(self.tree,self.design,self.model,self.footprint)
    def net(self,name):return self.tree.find(f".//nets/net[@name='/{name}']")
    def move(self,source,dest,ref,pin):
        node=self.net(source).find(f"node[@ref='{ref}'][@pin='{pin}']")
        self.net(source).remove(node);self.net(dest).append(node)

    def test_real_export_exact_maps_and_fresh_corners_pass(self):
        self.assertEqual([],self.errors())
        self.assertTrue(all(r['static_acceptance_and_detection'] for r in windows()))

    def test_uv_cannot_silently_become_ov(self):
        self.move('SEQ_REF2','LOGIC_GND','U2','6')
        self.assertTrue(self.errors())

    def test_manual_reset_cannot_bypass_preceding_core_qualifier(self):
        self.move('IO_3V3_EN','CORE_5V','U3','2')
        self.assertTrue(self.errors())

    def test_enable_cannot_connect_directly_to_five_volts(self):
        self.move('CORE_1V2_EN','CORE_5V','JCTRL1','1')
        self.assertTrue(self.errors())

    def test_standalone_enable_and_reset_pulldowns_are_required(self):
        for ref in ('R103','R105','R107','R110','R113'):
            with self.subTest(ref=ref):
                self.setUp();node=self.net('LOGIC_GND').find(f"node[@ref='{ref}']")
                self.net('LOGIC_GND').remove(node)
                self.assertTrue(self.errors())

    def test_reset_buffer_must_use_destination_rail(self):
        self.move('IO_3V3','CORE_5V','U5','5')
        self.assertTrue(self.errors())

    def test_esp_fault_cannot_be_inserted_in_fpga_reset_chain(self):
        self.move('SEQ_FPGA_RESET_GOOD','SEQ_ESP_RESET_GOOD','U5','2')
        self.assertTrue(self.errors())

    def test_buffer_input_output_swap_is_detected(self):
        self.move('SEQ_FPGA_RESET_GOOD','FPGA_CRESET_N','U5','2')
        self.move('FPGA_CRESET_N','SEQ_FPGA_RESET_GOOD','U5','4')
        self.assertTrue(self.errors())

    def test_internal_pullup_mode_cannot_replace_open_drain(self):
        self.move('LOGIC_GND','CORE_5V','U1','3')
        self.assertTrue(self.errors())

    def test_unused_channels_cannot_float_or_monitor_ground(self):
        self.move('CORE_5V','LOGIC_GND','U4','13')
        self.assertTrue(self.errors())

    def test_margin_disable_and_release_delay_cannot_be_shortened(self):
        for pin in ('1','10'):
            with self.subTest(pin=pin):
                self.setUp();self.move('CORE_5V','LOGIC_GND','U2',pin)
                self.assertTrue(self.errors())

    def test_precision_and_nominal_resistors_cannot_silently_change(self):
        for ref,val in (('R21','1.10k 1%'),('R31','10 1% 100ppm'),('R107','100k 1%')):
            with self.subTest(ref=ref):
                self.setUp();self.tree.find(f".//comp[@ref='{ref}']/value").text=val
                self.assertTrue(self.errors())

    def test_generic_non_schmitt_buffer_not_equivalent(self):
        self.tree.find(".//comp[@ref='U5']/fields/field[@name='MPN']").text='SN74LVC1G126DBVR'
        self.assertTrue(self.errors())

    def test_pin_function_and_unused_pin_mutation_fail(self):
        self.tree.find(".//libpart[@part='LVC1G17']/pins/pin[@num='4']").attrib['type']='open_collector'
        self.assertTrue(self.errors())
        self.setUp()
        net=next(n for n in self.tree.findall('.//nets/net') if 'unconnected-(U5-NC' in n.attrib['name'])
        node=net.find('node');net.remove(node);self.net('IO_3V3').append(node)
        self.assertTrue(self.errors())

    def test_package_pad_map_cannot_rotate_or_drop_exposed_pad(self):
        self.footprint=self.footprint.replace('(pad "1"','(pad "16"',1)
        self.assertTrue(self.errors())

    def test_fresh_static_pass_must_not_hide_lifetime_failure(self):
        # Vishay gives a 10kh/70C aging figure of0.04%; independent extrema exceed
        # this core window. This sensitivity case is not a lifetime qualification.
        aged=windows(.0004)
        self.assertFalse(aged[1]['static_acceptance_and_detection'])
        self.assertLess(min(windows()[1]['static_margins_v']),.0005)

    def test_coupled_network_includes_both_pulldowns_and_disconnects(self):
        data=enable_corners();self.assertEqual(4,len(data['coupled_core_esp']))
        fitted=next(c for c in data['coupled_core_esp'] if c['core_carrier_pulldown'] and c['esp_carrier_pulldown'])
        self.assertGreater(fitted['seq5_v'][0],1.6)
        self.assertGreater(fitted['core_en_v'][0],1.03)
        self.assertLess(fitted['core_en_v'][1],2)
        for row in data['coupled_core_esp']:
            self.assertLess(row['core_en_v'][1],3.6)
            self.assertLess(row['esp_en_v'][1],3.6)
        self.assertFalse(data['arbitrary_partial_power_proven'])

    def test_no_fabricated_manufacturing_or_transient_approval(self):
        self.model['manufacturing_ready']=True
        self.assertTrue(self.errors())
        self.setUp();self.model['unproven'].remove('brownout_slew_and_filter_delay')
        self.assertTrue(self.errors())

    def test_esp_reset_high_proof_uses_light_load_voh_not_fpga_threshold(self):
        reset=reset_bounds()
        self.assertLess(reset['esp_reset_high_load_a_including_20ua_allowance'],100e-6)
        self.assertGreater(reset['esp_reset_min_high_margin_v'],.69)
        self.assertFalse(reset['partial_power_or_external_injection_qualified'])
        self.tree.find(".//comp[@ref='R113']/value").text='4.7k 1%'
        self.assertTrue(self.errors())

    def test_required_bypass_cannot_be_dnp(self):
        ET.SubElement(self.tree.find(".//comp[@ref='C5']"),'property',name='dnp')
        self.assertTrue(self.errors())


if __name__=='__main__':unittest.main()
