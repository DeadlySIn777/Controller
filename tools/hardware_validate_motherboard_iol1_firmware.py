"""Independent source/interface checks, separate from target execution."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
def validate(target=None,master=None,models=None):
 target=target if target is not None else (ROOT/'firmware/motherboard_iol1_readonly/target.c').read_text()
 master=master if master is not None else (ROOT/'gateware/motherboard_iol1_target_bringup/cnc_iol1_readonly_target_master.v').read_text()
 if models is None:models=[json.loads((ROOT/'hardware/motherboard_io_control/design.json').read_text()),json.loads((ROOT/'hardware/motherboard_acc_control/design.json').read_text())]
 errors=[]
 def ck(ok,msg):
  if not ok:errors.append(msg)
 ck('af(GPIOB,5,1)' in target and 'TIM3->CCMR1=TIM_CCMR1_CC2S_0' in target and 'TIM3->CCER=TIM_CCER_CC2E;' in target,'actual PB5 AF1 rising TIM3 CH2')
 ck('TIM3->SMCR=(7u<<TIM_SMCR_SMS_Pos)|(6u<<TIM_SMCR_TS_Pos)' in target,'actual external clockmode1 TI2FP2')
 ck('(uint16_t)(count-edge_base)' in target and '40u-DMA1_Channel1->CNDTR' in target and '40u-DMA1_Channel2->CNDTR' in target,'independent exact edge and two DMA completion checks')
 ck('if(slot_valid&&iol1_accept(&node,rx,transport,now_us()))IWDG->KR=0xaaaa;' in target,'only physical-slot/full-frame acceptance reloads runtime IWDG')
 ck(target.count('IWDG->KR=0xaaaa')==2,'one initial watchdog load, one accepted-frame reload; no peripheral/timer feed')
 ck('DBG->APBFZ1&=~DBG_APB_FZ1_DBG_IWDG_STOP' in target and 'IWDG->PR=0;IWDG->RLR=9' in target,'no firmware debug watchdog freeze and exact counted timing')
 ck('__disable_irq();iol1_timeout(&node,now_us());__enable_irq();' in target,'timestamp/state tuple protected from IRQ underflow race')
 outputs=re.findall(r'output\((GPIO[A-F]),(\d+),(\d+)\)',target)
 ck(set(outputs)=={('GPIOA','0','0'),('GPIOA','1','0'),('GPIOA','8','0'),('GPIOA','9','0'),('GPIOB','9','1'),('GPIOB','12','1'),('GPIOB','3','1'),('GPIOB','4','1')},'GPIO authority alwaysLOW; only peripheral chip selects HIGH')
 ck('p[12]=0xff;p[13]=0xff' in target and 'p[14]=0;' in target and 'p[15]=(uint8_t)(input(GPIOC,6)|(input(GPIOC,7)<<1))' in target,'actual ACC clamp controls and unavailableADC/readback')
 ck('v==0x0a' in target and 'spi2_byte((uint8_t)(address<<5))' in target and 'spi2_byte(reg&0x7fu)' in target,'real nonzero TPS POR read plus no SWnibble request')
 ck('static const uint8_t regs[5]={6,7,5,4,3}' in target and 'do_fault_history[i-1]|=batch[i]' in target,'actual fault registerorder and RC history preservation')
 ck('parameter integer SETUP_CYCLES = 1000' in master and 'parameter integer HOLD_CYCLES = 250' in master,'50MHz 20ussetup/5ushold')
 ck("response_age == 16'hffff" in master and 'octet(rx_shift,24) == 0' in master and "octet(rx_shift,25) == 8'h03" in master,'diagnostic heldreset cannot masquerade as live ADC/readback')
 ck("8'h0f" not in master,'historical syntheticDACvalid response not accepted here')
 ports=list(map(int,re.search(r'port\[24\]=\{([^}]+)',target).group(1).split(',')))
 bits=list(map(int,re.search(r'bit\[24\]=\{([^}]+)',target).group(1).split(',')))
 dic=models[0]['nodes'][0];decode={0:'PA',1:'PB',2:'PC',3:'PD',5:'PF'}
 ck(len(ports)==len(bits)==24 and all(dic['di_mapping'][str(i)]['gpio']==decode[ports[i]]+str(bits[i]) for i in range(24)),'actual24native DI GPIOs match acquisition code')
 rows=[(models[0],'U13001','44','R13057','DIC',0),(models[0],'U13004','29','R13058','DOA',1),(models[0],'U13008','29','R13059','DOB',2),(models[1],'U14501','44','R14533','ACC',3)]
 for m,ref,pin,r,name,slot in rows:
  c=m['components'];ck(c[ref]['pins'][pin]==f'IOL1_L{slot}_SCLK_COUNT' and c[r]['pins']=={'1':name+'_IOL1_CLK_MCU','2':f'IOL1_L{slot}_SCLK_COUNT'},'actual native count tap '+ref)
 ck('node.field_good=do_valid&&input(GPIOB,1)' in target,'real independent DO entry-good PB1 is read, never fixedhealthy')
 ck('p->OSPEEDR=(p->OSPEEDR&~(3u<<(2u*b)))|(3u<<(2u*b));' in target,'actual SPI output two-bit OSPEEDR11 assignment')
 ck(set(re.findall(r'spi_output_speed\((GPIO[A-F]),(\d+)\)',target))=={('GPIOA','6'),('GPIOB','8'),('GPIOB','7')},'only actual SPI1MISO and DO SPI2SCLK/MOSI get speed11')
 ck(0<=target.find('spi_output_speed(GPIOA,6)')<target.find('for(unsigned b=4;b<=7;b++)af(GPIOA,b,0)') and 0<=target.find('spi_output_speed(GPIOB,8)')<target.find('af(GPIOB,8,1)'), 'output speed set before actual alternate-function enable')
 return {'ok':not errors,'errors':errors,'source_inspection':True,'target_execution':False,'physical_qualified':False}
if __name__=='__main__':
 r=validate();print(json.dumps(r,indent=2));raise SystemExit(not r['ok'])
