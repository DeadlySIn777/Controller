"""Disconnected native-netlist mutations of the new motion-card assembly."""
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from tools.hardware_validate_motion_card import validate

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/motion_card'


class MotionCardTests(unittest.TestCase):
    def setUp(self):
        self.tree=ET.parse(OUT/'netlist.xml')
        self.model=json.loads((OUT/'design.json').read_text())
        self.mapping=json.loads((OUT/'assembly-map.json').read_text())
    def errors(self):return validate(self.tree,self.model,self.mapping)[0]
    def move(self,ref,pin,destination):
        source=next(n for n in self.tree.findall('.//nets/net') if any(i.attrib['ref']==ref and i.attrib['pin']==pin for i in n.findall('node')))
        item=next(i for i in source.findall('node') if i.attrib['ref']==ref and i.attrib['pin']==pin)
        source.remove(item);next(n for n in self.tree.findall('.//nets/net') if n.attrib['name']==destination).append(item)
    def test_native_export_preserves_all_source_circuit_connections(self):
        errors,e=validate(self.tree,self.model,self.mapping)
        self.assertEqual([],errors);self.assertEqual(327,e['physical_components'])
        self.assertEqual({'fpga_core':70,'mc_local_power':48,'watchdog_conditioning':29,'mc_permission':56,'mc_motor_buffers':124},e['component_groups'])
        self.assertEqual(38,len(e['motor_physical_paths']))
        self.assertEqual(13,e['bank_B_used_OE_pins'])
    def test_bank_B_OE_cannot_bypass_actual_qualified_net(self):
        self.move('U5005','1','/TX_PERMIT');self.assertTrue(self.errors())
    def test_enable_polarity_cannot_be_lost_at_FPGA_boundary(self):
        self.move('U1001','H12','/STEP0_FPGA');self.assertTrue(self.errors())
    def test_expansion_series_path_cannot_cross_motor_channels(self):
        self.move('R5025','2','/mc_motor_buffers/DIR8_TO_MX4');self.assertTrue(self.errors())
    def test_buffer_that_lacks_the_reviewed_Ioff_contract_is_rejected(self):
        self.model['components']['U5005']['mpn']='SN74LVC126APWR';self.assertTrue(self.errors())
    def test_obsolete_decoupling_part_cannot_reenter_current_candidate(self):
        self.model['components']['C5001']['mpn']='GRM188R71E104KA01D';self.assertTrue(self.errors())
    def test_packaging_substitution_cannot_downgrade_temperature_grade(self):
        self.model['components']['U2003']['mpn']='LTC2962CUD#PBF'
        self.tree.find(".//comp[@ref='U2003']/fields/field[@name='MPN']").text='LTC2962CUD#PBF'
        errors=self.errors()
        self.assertIn('H-grade UD16 packaging-only substitution is incomplete or changed',errors)
        self.assertNotIn('MPN/source mismatch U2003',errors)
    def test_packaging_substitution_cannot_change_physical_package(self):
        self.model['components']['U2004']['footprint']='Package_SO:MSOP-16_3x4mm_P0.5mm'
        self.tree.find(".//comp[@ref='U2004']/footprint").text='Package_SO:MSOP-16_3x4mm_P0.5mm'
        errors=self.errors()
        self.assertIn('H-grade UD16 packaging-only substitution is incomplete or changed',errors)
        self.assertNotIn('Footprint/source mismatch U2004',errors)
    def test_packaging_substitution_preserves_inherited_value_and_three_receipts(self):
        packaging={r:c for r,c in self.model['components'].items()
                   if c.get('component_substitution')=='MC-PACK-001-prototype-candidate'}
        self.assertEqual({'U2003','U2004','U2005'},set(packaging))
        for c in packaging.values():
            self.assertEqual('LTC2962HUD#TRPBF',c['value'])
            self.assertEqual('LTC2962HUD#PBF',c['mpn'])
            self.assertEqual('CNC_MC_Power:LTC2962_UD16',c['footprint'])
    def test_permission_cannot_consume_raw5v_rail_qualifier(self):
        self.move('U4001','1','/mc_local_power/MC_RAILS_OK_5V');self.assertTrue(self.errors())
    def test_trip_cannot_sample_unconditioned_request(self):
        self.move('U4017','2','/FPGA_MOTION_REQUEST');self.assertTrue(self.errors())
    def test_motion_and_output_progress_cannot_be_crossed(self):
        self.move('U3004','2','/FPGA_PROGRESS_M');self.assertTrue(self.errors())
    def test_core_and_io_rails_cannot_be_swapped(self):
        self.move('U1001','E9','/IO_3V3');self.assertTrue(self.errors())
    def test_partial_candidate_cannot_assert_manufacturing_ready(self):
        self.model['manufacturing_ready']=True;self.assertTrue(self.errors())
    def test_raw_inhibit_cannot_be_replaced_by_final_arm_permission(self):
        self.move('U1001','A2','/TX_PERMIT');self.assertTrue(self.errors())
    def test_integration_cannot_claim_unallocated_GPIO_endpoints(self):
        errors,e=validate(self.tree,self.model,self.mapping)
        coverage={i['name']:i for i in e['control_endpoint_coverage']}
        self.assertFalse(coverage['FPGA_OUTPUT_REQUEST']['implemented_fpga_endpoint'])
        self.assertFalse(coverage['FPGA_PROGRESS_O']['implemented_fpga_endpoint'])
        self.assertTrue(coverage['FPGA_MOTION_REQUEST']['implemented_fpga_endpoint'])


if __name__=='__main__':unittest.main()
