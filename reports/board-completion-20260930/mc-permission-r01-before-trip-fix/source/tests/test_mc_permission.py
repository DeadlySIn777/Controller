import copy
import importlib.util
from pathlib import Path
import unittest

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


if __name__=='__main__':unittest.main()
