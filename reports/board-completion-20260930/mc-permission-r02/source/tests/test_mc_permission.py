import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('mc_permission_validator',ROOT/'tools/hardware_validate_mc_permission.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


class PermissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import json
        cls.design=json.loads((ROOT/'hardware/mc_permission/design.json').read_text())

    def test_native_source_and_complete_equations(self):
        result=v.validate();self.assertTrue(result['passed'],result['errors'])
        self.assertGreaterEqual(result['host_ideal_digital_checks'],4096)

    def test_async_clear_and_restore_never_rearm_without_edge(self):
        c=v.Circuit(self.design)
        terms=dict(MC_RAILS_OK=1,CDONE_QUALIFIED=1,DIC_OK_QUALIFIED=1,EXT_PERMIT_3V3=1,TAMPER_CLEAR_N=1,
                   WD_M_OK=1,WD_O_OK=1,FPGA_ENDPOINT_READY=1)
        c.drive(**terms);c.drive(FPGA_MOTION_REQUEST=1,FPGA_OUTPUT_REQUEST=1)
        self.assertEqual(c.values['TX_PERMIT'],1)
        c.drive(EXT_PERMIT_3V3=0);c.drive(EXT_PERMIT_3V3=1)
        self.assertEqual((c.values['TX_PERMIT'],c.values['OUT_PERMIT']),(0,0))

    def test_process_interlock_preserves_nonprocess_outputs(self):
        c=v.Circuit(self.design)
        c.drive(MC_RAILS_OK=1,CDONE_QUALIFIED=1,DIC_OK_QUALIFIED=1,EXT_PERMIT_3V3=1,TAMPER_CLEAR_N=1,
                WD_M_OK=1,WD_O_OK=1,FPGA_ENDPOINT_READY=1,PROCESS_PERMIT_EXT_3V3=1)
        c.drive(FPGA_MOTION_REQUEST=1,FPGA_OUTPUT_REQUEST=1)
        self.assertEqual(c.values['PROC_PERMIT'],1)
        c.drive(PROCESS_PERMIT_EXT_3V3=0)
        self.assertEqual((c.values['TX_PERMIT'],c.values['OUT_PERMIT'],c.values['PROC_PERMIT']),(1,1,0))

    def test_mutations_of_every_permission_term_are_detected(self):
        for ref,pin in [('U1','1'),('U1','3'),('U1','6'),('U2','3'),('U2','6'),
                        ('U3','2'),('U3','6'),('U4','3'),('U4','6'),('U7','3'),
                        ('U8','3'),('U9','6'),('U10','6')]:
            with self.subTest(ref=ref,pin=pin):
                d=copy.deepcopy(self.design);d['components'][ref]['pins'][pin]='IO_3V3'
                self.assertFalse(v.validate(d,native=False)['passed'])

    def test_each_latch_clear_and_pin_function_are_checked(self):
        for ref in ('U5','U6','U11','U12','U13','U14','U15'):
            with self.subTest(ref=ref):
                d=copy.deepcopy(self.design);d['components'][ref]['pins']['6']='IO_3V3'
                self.assertFalse(v.validate(d,native=False)['passed'])
        for ref in ('U1','U3','U5'):
            d=copy.deepcopy(self.design);d['components'][ref]['pins']['2']='WRONG_POWER_OR_DATA'
            self.assertFalse(v.validate(d,native=False)['passed'])

    def test_source_and_package_and_scope_guards(self):
        for field,value in [('manufacturing_ready',True),('operating_supply_v',[0,5])]:
            d=copy.deepcopy(self.design);d[field]=value
            self.assertFalse(v.validate(d,native=False)['passed'])
        d=copy.deepcopy(self.design);d['components']['U5']['footprint']='Package_SO:Wrong'
        self.assertFalse(v.validate(d,native=False)['passed'])

    def trip_circuit(self):
        c=v.Circuit(self.design)
        c.drive(MC_RAILS_OK=1,WD_M_OK=1,WD_O_OK=1)
        return c

    def test_startup_and_disarmed_watchdog_health_falls_are_not_trips(self):
        c=self.trip_circuit()
        for domain in ('M','O'):
            c.drive(**{'WD_'+domain+'_OK':0})
            self.assertEqual(c.values['WD_'+domain+'_TRIP_N'],1)
            c.drive(**{'WD_'+domain+'_OK':1})

    def test_first_unrelated_drive_does_not_create_initial_inverse_clock_edge(self):
        c=v.Circuit(self.design)
        c.drive(MC_RAILS_OK=1,WD_M_SET1_BUF=1,WD_O_SET1_BUF=1)
        self.assertEqual((c.values['WD_M_TRIP_N'],c.values['WD_O_TRIP_N']),(1,1))
        c.drive(PERMIT_OUT_REQ=1)
        self.assertEqual((c.values['WD_M_TRIP_N'],c.values['WD_O_TRIP_N']),(1,1))

    def test_set1_rising_with_health_already_low_is_not_a_falling_edge(self):
        c=self.trip_circuit();c.drive(WD_M_OK=0);c.drive(WD_M_SET1_BUF=1)
        self.assertEqual(c.values['WD_M_TRIP_N'],1)
        c.drive(WD_M_OK=1);c.drive(WD_M_OK=0)
        self.assertEqual(c.values['WD_M_TRIP_N'],0)

    def test_trip_samples_actual_set1_instead_of_raw_request(self):
        c=self.trip_circuit();c.drive(FPGA_MOTION_REQUEST=1,WD_M_SET1_BUF=0);c.drive(WD_M_OK=0)
        self.assertEqual(c.values['WD_M_TRIP_N'],1)
        c.drive(FPGA_MOTION_REQUEST=0,WD_M_OK=1,WD_M_SET1_BUF=1);c.drive(WD_M_OK=0)
        self.assertEqual(c.values['WD_M_TRIP_N'],0)

    def test_trip_is_sticky_through_disarmed_health_cycle_then_explicitly_cleared(self):
        c=self.trip_circuit();c.drive(WD_O_SET1_BUF=1);c.drive(WD_O_OK=0)
        c.drive(WD_O_SET1_BUF=0,WD_O_OK=1);c.drive(WD_O_OK=0)
        self.assertEqual(c.values['WD_O_TRIP_N'],0)
        c.drive(WD_REARM_O=1);c.drive(WD_REARM_O=0)
        self.assertEqual(c.values['WD_O_TRIP_N'],1)

    def test_power_clear_defines_trip_state(self):
        c=self.trip_circuit();c.drive(WD_M_SET1_BUF=1,WD_O_SET1_BUF=1);c.drive(WD_M_OK=0,WD_O_OK=0)
        self.assertEqual((c.values['WD_M_TRIP_N'],c.values['WD_O_TRIP_N']),(0,0))
        c.drive(MC_RAILS_OK=0)
        self.assertEqual((c.values['WD_M_TRIP_N'],c.values['WD_O_TRIP_N']),(1,1))

    def test_trip_feedback_and_clock_inversion_mutations_are_rejected(self):
        for ref,pin,net in [('U17','1','LOGIC_GND'),('U17','2','FPGA_MOTION_REQUEST'),
                            ('U16','1','WD_O_OK'),('U18','1','LOGIC_GND'),('U19','1','IO_3V3')]:
            with self.subTest(ref=ref,pin=pin):
                d=copy.deepcopy(self.design);d['components'][ref]['pins'][pin]=net
                self.assertFalse(v.validate(d,native=False)['passed'])

    def native_mutation_result(self, mutate):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            for name in ('netlist.xml','erc.json'):
                shutil.copyfile(ROOT/'hardware/mc_permission'/name,folder/name)
            tree=ET.parse(folder/'netlist.xml');mutate(tree.getroot());tree.write(folder/'netlist.xml',encoding='utf-8')
            return v.validate(self.design,directory=folder)

    def test_native_order_code_and_footprint_mutations_are_rejected(self):
        for tag in ('value','fields/field[@name="MPN"]','footprint'):
            with self.subTest(tag=tag):
                result=self.native_mutation_result(lambda tree: setattr(tree.find('components/comp[@ref="U14"]/'+tag),'text','WRONG'))
                self.assertFalse(result['passed'])
                self.assertTrue(any('Exact native part' in e for e in result['errors']))

    def test_native_fitted_part_dnp_is_rejected(self):
        result=self.native_mutation_result(lambda tree:ET.SubElement(tree.find('components/comp[@ref="U14"]'),'property',{'name':'dnp'}))
        self.assertFalse(result['passed'])

    def test_native_pin_functions_cannot_be_mirrored_wrong(self):
        result=self.native_mutation_result(lambda tree:tree.find('libparts/libpart[@part="LVC2G74"]/pins/pin[@num="3"]').set('name','Q'))
        self.assertFalse(result['passed'])

    def test_native_pin_types_and_duplicate_conductors_are_rejected(self):
        result=self.native_mutation_result(lambda tree:tree.find('libparts/libpart[@part="LVC2G04"]/pins/pin[@num="6"]').set('type','open_collector'))
        self.assertFalse(result['passed'])
        def duplicate(tree):
            net=tree.find('nets/net');net.append(copy.deepcopy(net.find('node')))
        result=self.native_mutation_result(duplicate)
        self.assertFalse(result['passed'])

    def test_missing_decoupler_and_weak_default_pulls_are_rejected(self):
        d=copy.deepcopy(self.design);del d['components']['C19']
        self.assertFalse(v.validate(d,native=False)['passed'])
        d=copy.deepcopy(self.design);d['components']['R1']['resistance_ohm']=100000
        self.assertFalse(v.validate(d,native=False)['passed'])

    def test_primary_pin_extraction_independent_fixtures(self):
        primary=v.primary_pins()
        self.assertEqual(primary['LVC2G04'],{'1':'1A','2':'GND','3':'2A','4':'2Y','5':'VCC','6':'1Y'})
        self.assertEqual(primary['LVC2G32'],{'1':'1A','2':'1B','3':'2Y','4':'GND','5':'2A','6':'2B','7':'1Y','8':'VCC'})
        self.assertEqual(primary['LVC2G74'],{'1':'CLK','2':'D','3':'Q_N','4':'GND','5':'Q','6':'CLR_N','7':'PRE_N','8':'VCC'})


if __name__=='__main__':unittest.main()
