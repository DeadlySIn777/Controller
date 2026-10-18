"""Bounded ADC promotion must not permit an undersized or wrong-domain bypass."""
import copy,importlib.util,json,os,unittest
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('adc_parent_validation',ROOT/'tools/hardware_validate_motherboard.py')
validation=importlib.util.module_from_spec(spec);spec.loader.exec_module(validation)
class ADCSourceAdoptionTests(unittest.TestCase):
    def setUp(self):
        p=Path(os.environ.get('CONTROLLER_MOTHERBOARD_TEST_SOURCE',ROOT/'hardware/motherboard'))
        self.model=json.loads((p/'design.json').read_text());self.mapping=json.loads((p/'assembly-map.json').read_text());self.tree=ET.parse(p/'netlist.xml')
    def errors(self):return validation.validate(self.tree,self.model,self.mapping,False)
    def test_healthy_complete_parent(self):
        self.assertEqual([],self.errors());self.assertEqual(2688,len(self.model['components']))
    def test_small_AVDD_and_DVDD_rejected(self):
        for ref in ['C14744','C14745','C14746']:
            with self.subTest(ref=ref):
                old=copy.deepcopy(self.model);self.model['components'][ref]['capacitance_f']=1e-7
                self.assertTrue(any('Exact local ADC bypass' in e for e in self.errors()));self.model=old
    def test_old_DVDD_0603_not_accepted(self):
        self.model['components']['C14746']['footprint']='Capacitor_SMD:C_0603_1608Metric'
        self.assertTrue(any('Exact local ADC bypass' in e for e in self.errors()))
    def test_uncorroborated_MPN_not_accepted(self):
        self.model['components']['C14744']['mpn']='GRM188R71H105KA12D'
        self.assertTrue(any('Exact local ADC bypass' in e for e in self.errors()))
    def test_ledger_cannot_disappear(self):
        self.mapping.pop('reviewed_adc_bypass_delta')
        self.assertTrue(any('three-cap ADC source ledger' in e for e in self.errors()))
    def test_generic_via_router_cannot_claim_precision_cell(self):
        self.model['adc_bypass_correction']['all_seven_local_ADC_caps_generic_router_excluded']=False
        self.assertTrue(any('direct-loop' in e for e in self.errors()))
    def test_unmeasured_startup_cannot_be_claimed(self):
        self.model['adc_bypass_correction']['LDO_startup_discharge_transient_new_capacitive_loading_qualified']=True
        self.assertTrue(any('qualification gates' in e for e in self.errors()))
    def test_unmeasured_effective_reference_not_claimed(self):
        self.model['adc_bypass_correction']['reference_effective_bias_age_temp_ESR_qualified']=True
        self.assertTrue(any('qualification gates' in e for e in self.errors()))
    def test_return_cannot_be_logic_ground(self):
        for net in self.tree.findall('.//nets/net'):
            for node in list(net):
                if node.attrib=={'ref':'C14744','pin':'2','pinfunction':'2','pintype':'passive'} or(node.attrib.get('ref')=='C14744'and node.attrib.get('pin')=='2'):
                    net.remove(node);new=ET.SubElement(self.tree.getroot().find('nets'),'net',{'code':'900000','name':'/LOGIC_GND'});new.append(node)
                    self.assertTrue(any('exact supply/return' in e for e in self.errors()));return
        self.fail('Real capacitor return missing')
if __name__=='__main__':unittest.main()
