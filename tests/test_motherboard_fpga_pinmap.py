"""Cross-source rejection checks for the native T20 package electrical contract."""
import copy,json,sys,unittest
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_reconcile_fpga_pinmap import reconcile
from hardware_validate_fpga_core import primary_pins

class PinContract(unittest.TestCase):
    def setUp(self):
        self.xml=ET.parse(ROOT/'hardware/motherboard/netlist.xml').getroot()
        self.meta=json.loads((ROOT/'hardware/motherboard/fpga-allocation-parent.json').read_text())
        self.official=primary_pins()
        self.plan=json.loads((ROOT/'reports/motherboard-fpga-source-20260930/status-deallocation-r01/interface-constraint-plan.json').read_text())
        self.reserved=json.loads((ROOT/'hardware/motherboard/fpga-allocation-proposal.json').read_text())['reserved_gpio_balls']
    def check(self):return reconcile(self.xml,self.meta,self.official,self.plan,self.reserved)
    def test_actual_inventory_and_unproved_boundaries(self):
        r=self.check();self.assertEqual((r['assigned'],r['free'],len(r['resources'])),(135,48,183));self.assertEqual(len(r['bank_power_pins']),14)
        self.assertFalse(r['vendor_package_fit']);self.assertFalse(r['manufacturing_ready'])
    def test_ball_function(self):
        self.official['P2']['name']='GPIOL_WRONG'
        with self.assertRaisesRegex(ValueError,'Manufacturer function'):self.check()
    def test_wrong_bank(self):
        self.plan['constraints'][0]['bank']='BANK3D'
        with self.assertRaisesRegex(ValueError,'ball/net/bank'):self.check()
    def test_wrong_connected_net(self):
        self.plan['constraints'][0]['native_net']='/DIR0_FPGA'
        with self.assertRaisesRegex(ValueError,'ball/net/bank'):self.check()
    def test_wrong_direction(self):
        self.plan['constraints'][0]['direction']='input'
        with self.assertRaisesRegex(ValueError,'direction'):self.check()
    def test_missing_reviewed_direction(self):
        self.meta['desired_directions'].pop('STEP0_FPGA')
        with self.assertRaisesRegex(ValueError,'direction'):self.check()
    def test_duplicate_ball(self):
        self.plan['constraints'].append(copy.deepcopy(self.plan['constraints'][0]))
        with self.assertRaisesRegex(ValueError,'Duplicate constrained'):self.check()
    def test_driven_documented_NC(self):
        self.plan['constraints'].append(dict(ball='H13',native_net='unconnected-(U1001-GPIOR_125_CLK10-PadH13)',manufacturer_pin='GPIOR_125_CLK10',bank='BANK3D',logical_signal='DOOR_STATUS_FPGA',direction='input',io_standard='3.3_V_LVCMOS'))
        with self.assertRaisesRegex(ValueError,'drives nativeNC'):self.check()
    def test_wrong_VCCIO_rail(self):
        ball=next(k for k,v in self.official.items()if v['name'].startswith('VCCIO'))
        node=next(p for p in self.xml.findall('nets/net/node')if p.attrib['ref']=='U1001'and p.attrib['pin']==ball)
        parent=next(n for n in self.xml.findall('nets/net')if node in list(n));parent.remove(node)
        dest=next(n for n in self.xml.findall('nets/net')if n.attrib['name']=='/CORE_1V2');dest.append(node)
        with self.assertRaisesRegex(ValueError,'VCCIO bank rail'):self.check()
    def test_false_metadata_total(self):
        self.meta['assigned_user_pins']=142
        with self.assertRaisesRegex(ValueError,'metadata count'):self.check()
if __name__=='__main__':unittest.main()
