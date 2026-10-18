"""Actual KiCad export mutations and bounded digital scenarios; no live outputs."""
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from tools.hardware_validate_machine_permission import validate, PermissionModel, electrical_bounds

OUT=Path(__file__).resolve().parents[1]/'hardware/machine_permission'


class PermissionCircuitTests(unittest.TestCase):
    def setUp(self):
        self.tree=ET.parse(OUT/'netlist.xml');self.model=json.loads((OUT/'design-envelope.json').read_text())
        self.fp=(OUT/'CNC_Permit.pretty/TPS3431_DRB8.kicad_mod').read_text()
    def errors(self):return validate(self.tree,self.model,self.fp)
    def net(self,name):return self.tree.find(f".//nets/net[@name='/{name}']")
    def move(self,source,dest,ref,pin):
        node=self.net(source).find(f"node[@ref='{ref}'][@pin='{pin}']")
        self.net(source).remove(node);self.net(dest).append(node)
    def test_actual_circuit_matches_independent_contract(self):self.assertEqual([],self.errors())
    def test_watchdog_cannot_be_disabled_from_fpga_arm(self):
        self.move('IO_3V3','FPGA_MOTION_REQUEST','U1','3');self.assertTrue(self.errors())
    def test_watchdog_enable_output_is_required_for_powerup(self):
        self.net('WD_HEALTH_RAW_N').remove(self.net('WD_HEALTH_RAW_N').find("node[@ref='U1'][@pin='8']"))
        self.assertTrue(self.errors())
    def test_timing_cap_cannot_inherit_a_false_20ms_claim(self):
        self.model['watchdog']['nominal_timeout_ms']=20;self.assertTrue(self.errors())
        self.setUp();self.tree.find(".//comp[@ref='C1']/value").text='100pF C0G 50V 5%';self.assertTrue(self.errors())
    def test_final_permit_cannot_create_inhibit_feedback_deadlock(self):
        self.move('HW_WATCHDOG_OK_N','TX_PERMIT','JOUT1','2');self.assertTrue(self.errors())
    def test_heartbeat_cannot_be_used_as_arm_clock(self):
        self.move('FPGA_MOTION_REQUEST','FPGA_PROGRESS_WDI','U6','1');self.assertTrue(self.errors())
    def test_arm_latch_async_clear_cannot_be_bypassed(self):
        self.move('LATCH_CLEAR_N','IO_3V3','U6','6');self.assertTrue(self.errors())
    def test_q_and_qbar_pin_identity_is_not_interchangeable(self):
        self.tree.find(".//libpart[@part='LVC2G74']/pins/pin[@num='5']").attrib['name']='Q_N'
        self.assertTrue(self.errors())
    def test_final_gate_requires_live_request_and_raw_interlock(self):
        for pin,net in (('3','FPGA_MOTION_REQUEST'),('6','HW_WATCHDOG_OK_N')):
            with self.subTest(pin=pin):
                self.setUp();self.move(net,'IO_3V3','U7',pin);self.assertTrue(self.errors())
    def test_programming_reset_must_clear_permission(self):
        self.move('FPGA_LOCAL_RESET_N','IO_3V3','U4','1');self.assertTrue(self.errors())
    def test_cdone_must_not_be_pulled_down_by_this_block(self):
        self.move('EXT_PERMIT_3V3','FPGA_CDONE','R5','1');self.assertTrue(self.errors())
    def test_external_permit_cannot_be_bypassed(self):
        self.move('EXT_PERMIT_3V3','IO_3V3','U4','6');self.assertTrue(self.errors())
    def test_wdi_buffer_and_light_load_are_required(self):
        self.move('WD_INPUT_BUF','FPGA_PROGRESS_WDI','U1','6');self.assertTrue(self.errors())
        self.setUp();self.tree.find(".//comp[@ref='R2']/value").text='10k 1%';self.assertTrue(self.errors())
    def test_tx_default_pulldown_and_bypass_cannot_be_dnp(self):
        for ref in ('R10','C8'):
            with self.subTest(ref=ref):
                self.setUp();ET.SubElement(self.tree.find(f".//comp[@ref='{ref}']"),'property',name='dnp')
                self.assertTrue(self.errors())
    def test_support_package_pad_map_is_checked(self):
        self.fp=self.fp.replace('(pad "1"','(pad "8"',1);self.assertTrue(self.errors())
    def test_historical_six_channel_ledger_does_not_set_new_product_size(self):
        self.model['minimum_motor_requirement']=6;self.assertTrue(self.errors())
    def test_consistency_cannot_be_relabelled_manufacturing_approval(self):
        self.model['manufacturing_ready']=True;self.assertTrue(self.errors())
    def test_load_and_timer_bounds_are_conservative_declared_models(self):
        b=electrical_bounds();self.assertGreater(b['timing_cap_min_pf'],100)
        self.assertGreater(b['timeout_fresh_ms'][0],55);self.assertLess(b['timeout_fresh_ms'][1],72)
        self.assertLess(b['tx_load_a_at3v4_seven_10k_min_and_six_1ua_inputs'],.003)
        self.assertGreater(b['tx_voh_bound_v_at_vcc_ge3v_load_le16ma'],2)
        self.assertLess(b['wdi_load_a_100k_pd_and_20ua_allowance'],100e-6)
        self.assertFalse(b['parasitic_and_leakage_physically_verified'])


class PermissionBehaviorTests(unittest.TestCase):
    def armed(self,timeout=None,reset=200):
        m=PermissionModel(timeout_ms=timeout,reset_ms=reset)
        m.set(1,reset=True,cdone=True,external=True,ready=True);m.set(2,request=True)
        self.assertTrue(m.tx);return m
    def test_boot_requires_valid_configuration_ready_and_new_edge(self):
        m=PermissionModel();m.set(.1,request=True)
        m.set(1,reset=True,cdone=True,external=True,ready=True)
        self.assertTrue(m.raw);self.assertFalse(m.tx)
        m.set(2,request=False);m.set(3,request=True);self.assertTrue(m.tx)
    def test_falling_edge_only_means_two_accepted_updates_per_feed(self):
        m=self.armed();deadline=m.event;m.set(3,wdi=True);self.assertEqual(deadline,m.event)
        m.set(4,wdi=False);self.assertAlmostEqual(4+64.288,m.event)
    def test_clock_stall_removes_permission_without_any_more_fpga_edges(self):
        for timeout in electrical_bounds()['timeout_fresh_ms']:
            with self.subTest(timeout=timeout):
                m=self.armed(timeout);m.advance(m.event);self.assertFalse(m.raw);self.assertFalse(m.tx)
                self.assertTrue(m.inputs['request']);self.assertFalse(m.q)
    def test_reset_pulse_ignores_progress_and_auto_release_never_rearms(self):
        for reset in (170,230):
            with self.subTest(reset=reset):
                m=self.armed(reset=reset);m.advance(m.event);deadline=m.event
                m.set(m.now+1,wdi=True);m.set(m.now+1,wdi=False);self.assertEqual(deadline,m.event)
                m.advance(deadline);self.assertTrue(m.raw);self.assertFalse(m.tx)
                m.set(m.now+1,wdi=True);m.set(m.now+1,wdi=False);self.assertFalse(m.tx)
    def test_deliberate_arm_after_ready_recovery_sets_latch(self):
        m=self.armed();m.advance(m.event);m.set(m.now+1,ready=False,request=False)
        m.advance(m.event);m.set(m.now+1,ready=True);m.set(m.now+1,request=True);self.assertTrue(m.tx)
    def test_external_permit_reset_and_cdone_losses_require_new_arm(self):
        for signal in ('reset','cdone','external','ready'):
            with self.subTest(signal=signal):
                m=self.armed();m.set(3,**{signal:False});self.assertFalse(m.tx)
                m.set(4,**{signal:True});self.assertFalse(m.tx)
                m.set(5,request=False);m.set(6,request=True);self.assertTrue(m.tx)
    def test_disarm_removes_final_permit_even_if_latch_was_set(self):
        m=self.armed();m.set(3,request=False);self.assertFalse(m.tx);self.assertTrue(m.q)
        m.set(4,request=True);self.assertTrue(m.tx)
    def test_held_arm_during_fault_cannot_resume_on_healthy_status(self):
        m=self.armed();m.set(3,external=False);m.set(4,request=False);m.set(5,request=True)
        m.set(6,external=True);self.assertFalse(m.q);self.assertFalse(m.tx)
    def test_events_on_timeout_do_not_retroactively_feed(self):
        m=self.armed();m.set(3,wdi=True);deadline=m.event
        m.set(deadline,wdi=False);self.assertEqual('reset_pulse',m.state);self.assertFalse(m.tx)


if __name__=='__main__':unittest.main()
