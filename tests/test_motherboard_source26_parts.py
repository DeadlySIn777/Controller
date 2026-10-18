"""Native source26 identity and honest conditional-model boundaries."""
import copy, importlib.util, json, os, unittest
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('source26_checks',ROOT/'tools/hardware_check_source26_parts.py')
check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check)

class Source26Tests(unittest.TestCase):
    def setUp(self):
        folder=Path(os.environ.get('CONTROLLER_SOURCE26_STAGE',ROOT/'reports/motherboard-integration-20261001/source26-reference-fuse-staged-r01/candidate/hardware/motherboard'))
        self.model=json.loads((folder/'design.json').read_text());self.mapping=json.loads((folder/'assembly-map.json').read_text())
        self.nodes={(n.attrib['ref'],n.attrib['pin']):net.attrib['name'] for net in ET.parse(folder/'netlist.xml').findall('.//nets/net') for n in net.findall('node')}
    def errors(self):return check.check_source26(self.model['components'],self.nodes,self.model,self.mapping)
    def test_exact_five_parts_native_pass(self):self.assertEqual([],self.errors())
    def test_historical_revision_is_readable(self):
        self.model.pop('adc_reference_component_qualification');self.mapping.pop('reviewed_source26_qualification_delta');self.assertEqual([],self.errors())
    def test_reference_old_alias_rejected(self):
        self.model['components']['C14741']['mpn']='GRM188R71H105KA12D';self.assertTrue(self.errors())
    def test_unproven_aging_margin_rejected(self):
        self.model['adc_reference_component_qualification']['reference_effective_capacitance_full_corner_qualified']=True;self.assertTrue(self.errors())
    def test_no_expanded_product_temperature(self):
        self.model['adc_reference_component_qualification']['product_internal_ambient_c']=[-40,55];self.assertTrue(self.errors())
    def test_fuse_stock_geometry_rejected(self):
        self.model['components']['F11002']['footprint']='Fuse:Fuseholder_Blade_Mini_Keystone_3568';self.assertTrue(self.errors())
    def test_no_changed_fuse_mpn(self):
        self.model['components']['F11003']['mpn']='3569';self.assertTrue(self.errors())
    def test_reference_logic_return_rejected(self):
        self.nodes['C14743','2']='/LOGIC_GND';self.assertTrue(self.errors())
    def test_missing_ledger_rejected(self):
        self.mapping.pop('reviewed_source26_qualification_delta');self.assertTrue(self.errors())

if __name__=='__main__':unittest.main()
