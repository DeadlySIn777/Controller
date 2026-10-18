"""Source negatives complement real ARM builds and executable C/HDL tests."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_iol1_firmware import validate
class ReadonlySourceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.target=(ROOT/'firmware/motherboard_iol1_readonly/target.c').read_text()
  cls.master=(ROOT/'gateware/motherboard_iol1_target_bringup/cnc_iol1_readonly_target_master.v').read_text()
 def test_actual_source_and_four_native_taps(self):self.assertTrue(validate()['ok'])
 def changed(self,a,b):self.assertFalse(validate(target=self.target.replace(a,b))['ok'])
 def test_no_unconditional_IWDG_runtime_feed(self):self.changed('if(slot_valid&&iol1_accept(&node,rx,transport,now_us()))IWDG','IWDG')
 def test_DMA_bytes_alone_do_not_prove_partial_tail(self):self.changed('(uint16_t)(count-edge_base)','320')
 def test_wrong_timer_AF_is_rejected(self):self.changed('af(GPIOB,5,1)','af(GPIOB,5,0)')
 def test_timer_falling_instead_of_rising_rejected(self):self.changed('TIM3->CCER=TIM_CCER_CC2E;','TIM3->CCER=TIM_CCER_CC2E|TIM_CCER_CC2P;')
 def test_DIC_missing_input_cannot_be_zero_substituted(self):self.changed('13,14,15,0,1,0,1,2,3','13,14,15,0,1,0,1,2,2')
 def test_AO_authority_HIGH_rejected(self):self.changed('output(GPIOA,8,0)','output(GPIOA,8,1)')
 def test_DO_entry_good_not_constant(self):self.changed('node.field_good=do_valid&&input(GPIOB,1)','node.field_good=1')
 def test_SPI_read_never_turns_on_SWnibble(self):self.changed('(address<<5)','((address<<5)|15)')
 def test_missing_address0_driver_not_valid_allzero(self):self.changed('v==0x0a','v==0')
 def test_cleared_fault_evidence_not_discarded(self):self.changed('do_fault_history[i-1]|=batch[i]','do_fault_history[i-1]=batch[i]')
 def test_analog_missing_is_not_valid_zero_age(self):self.changed('p[12]=0xff;p[13]=0xff','p[12]=0;p[13]=0')
 def test_timestamp_IRQ_race_not_reintroduced(self):self.changed('__disable_irq();iol1_timeout(&node,now_us());__enable_irq();','iol1_timeout(&node,now_us());')
 def test_master_doesnot_demand_fake_readback_under_reset(self):self.assertFalse(validate(master=self.master.replace("8'h03","8'h0f"))['ok'])
 def test_guard_cannot_shrink_to_three_FPGA_ticks(self):self.assertFalse(validate(master=self.master.replace('SETUP_CYCLES = 1000','SETUP_CYCLES = 3'))['ok'])
if __name__=='__main__':unittest.main()
