import copy
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from tools.hardware_validate_assembly import validate, validate_erc

ROOT=Path(__file__).resolve().parents[1]
class AssemblyTests(unittest.TestCase):
    def setUp(self):
        self.tree=ET.parse(ROOT/'hardware/controller_assembly/netlist.xml')
        self.mapping=json.loads((ROOT/'hardware/controller_assembly/assembly-map.json').read_text())
    def net(self,name):return next(n for n in self.tree.findall('.//nets/net') if n.attrib['name']==name)
    def reject(self):self.assertTrue(validate(self.tree,self.mapping))
    def test_all_actual_source_connections_preserved(self):self.assertEqual([],validate(self.tree,self.mapping))
    def test_domain_return_cannot_be_merged(self):
        source=self.net('/FIELD_GND');p=source.find('node');source.remove(p);self.net('/LOGIC_GND').append(p);self.reject()
    def test_encoder_supplies_cannot_be_merged(self):
        source=self.net('/ENC0_5V_LIMITED');p=source.find('node');source.remove(p);self.net('/ENC1_5V_LIMITED').append(p);self.reject()
    def test_missing_power_connection_detected(self):
        n=self.net('/CORE_5V');n.remove(n.find('node'));self.reject()
    def test_duplicate_node_cannot_hide_in_set(self):
        n=self.net('/CORE_5V');n.append(copy.deepcopy(n.find('node')));self.reject()
    def test_missing_real_component_detected(self):
        cs=self.tree.find('.//components');cs.remove(cs.find('comp'));self.reject()
    def test_new_hidden_alias_is_rejected(self):
        self.mapping['aliases']['power_entry']={'FIELD_GND':'LOGIC_GND'};self.reject()
    def test_wrong_source_identity_invalidates_review(self):
        key=next(iter(self.mapping['input_sha256']));self.mapping['input_sha256'][key]='0'*64;self.reject()
    def test_source_inventory_cannot_be_removed(self):
        self.mapping['input_sha256']={};self.reject()
    def test_builder_identity_cannot_be_faked(self):
        self.mapping['builder_sha256']='not-a-hash';self.reject()
    def test_missing_block_cannot_be_accepted_as_complete_scope(self):
        self.mapping['blocks'].pop('digital_inputs');self.reject()
    def test_component_cannot_become_dnp_in_assembly(self):
        ET.SubElement(self.tree.find('.//components/comp'),'property',{'name':'dnp'});self.reject()
    def test_actual_erc_has_only_specific_expected_warnings(self):
        erc=json.loads((ROOT/'hardware/controller_assembly/erc.json').read_text())
        self.assertEqual([],validate_erc(erc,self.mapping['blocks']))
    def test_arbitrary_warning_cannot_pass_as_substrate_island(self):
        erc={'sheets':[{'path':'/digital_inputs/','violations':[{'severity':'warning','type':'isolated_pin_label',
              'description':'Label connected to only one pin','items':[{'description':"Label 'CORE_5V'"}]}]}]}
        self.assertTrue(validate_erc(erc,{'digital_inputs':{}}))
    def test_erc_error_on_expected_label_is_still_rejected(self):
        erc={'sheets':[{'path':'/digital_inputs/','violations':[{'severity':'error','type':'isolated_pin_label',
              'description':'Fault','items':[{'description':"Label 'DI00_SUB_ISLAND'"}]}]}]}
        self.assertTrue(validate_erc(erc,{'digital_inputs':{}}))

    def test_protective_status_is_reserved_for_hardwired_permission(self):
        self.assertEqual({'EXT_PERMIT_3V3':'PROTECTIVE_STATUS_FPGA'},self.mapping['aliases']['machine_permission'])
        refs=self.mapping['blocks']['machine_permission']['references']
        net=self.net('/PROTECTIVE_STATUS_FPGA')
        self.assertTrue(any(n.get('ref') in refs.values() for n in net.findall('node')))
        self.mapping['aliases']['machine_permission']['EXT_PERMIT_3V3']='SPARE_FPGA'
        self.reject()
    def test_all_twelve_step_dir_signals_reach_fpga_and_transmitters(self):
        fpga=set(self.mapping['blocks']['fpga_core']['references'].values())
        tx=set(self.mapping['blocks']['tx_twelve']['references'].values())
        for joint in range(12):
            for kind in ('STEP','DIR'):
                refs={n.get('ref') for n in self.net(f'/{kind}{joint}_FPGA').findall('node')}
                self.assertTrue(refs & fpga)
                self.assertTrue(refs & tx)
    def test_programming_reset_is_in_the_hardware_permission_chain(self):
        refs={n.get('ref') for n in self.net('/FPGA_LOCAL_RESET_N').findall('node')}
        for block in ('fpga_core','machine_permission'):
            self.assertTrue(refs & set(self.mapping['blocks'][block]['references'].values()))

if __name__=='__main__':unittest.main()
