"""Independent fourth-node pin/AF/default/frontend/native evidence checks."""
import argparse,collections,json
from pathlib import Path
from hardware_validate_motherboard_do import native
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_acc_control'
PORTS=['PC13','PC14','PC15','VBAT','VREF+','VDD/VDDA','VSS/VSSA','PF0','PF1','PF2-NRST','PA0','PA1','PA2','PA3','PA4','PA5','PA6','PA7','PB0','PB1','PB2','PB10','PB11','PB12','PB13','PB14','PB15','PA8','PA9','PC6','PC7','PA10','PA11','PA12','PA13','PA14-BOOT0','PA15','PD0','PD1','PD2','PD3','PB3','PB4','PB5','PB6','PB7','PB8','PB9']
REQUIRED={'VBAT':'IO_3V3','VREF+':'IO_3V3','VDD/VDDA':'IO_3V3','VSS/VSSA':'LOGIC_GND','PF2-NRST':'ACC_NRST_N','PA13':'ACC_SWDIO','PA14-BOOT0':'ACC_SWCLK_BOOT0','PA4':'ACC_IOL1_CS_MCU','PA5':'ACC_IOL1_CLK_MCU','PA6':'ACC_IOL1_RSP_MCU','PA7':'ACC_IOL1_CMD_MCU','PC14':'ACC_SLOT0','PC15':'ACC_SLOT1','PF0':'ACC_SLOT2','PF1':'ACC_SLOT3','PA0':'ACC_IO_ENABLE_STROBE','PA1':'ACC_CARD_EN','PA2':'ACC_OUT_EN_LATCH','PA3':'PEN_OUT_EN_LATCH','PB0':'OUT_PERMIT_ACC','PB1':'PROC_PERMIT','PB2':'PWM_ENABLE_LOGIC','PB10':'PEN_ENABLE_LOGIC','PB11':'PWM_AUX_FAULT_N','PA8':'AO0_ENABLE_REQUEST','PA9':'AO1_ENABLE_REQUEST','PC6':'AO0_CLAMP_ACTIVE','PC7':'AO1_CLAMP_ACTIVE','PA10':'AI_POWER_GOOD_HOST','PA11':'AO0_POWER_GOOD_HOST','PA12':'AO1_POWER_GOOD_HOST','PD0':'RS485_POWER_GOOD_HOST','PD1':'CAN_POWER_GOOD_HOST','PD2':'AI_SENSOR_FAULT_HOST','PB12':'AI_CS_N_HOST','PB13':'AI_SCLK_HOST','PB14':'AI_SDO_HOST','PB15':'AI_SDI_HOST','PB8':'AO_I2C_SCL_HOST','PB9':'AO_I2C_SDA_HOST','PB3':'AO0_CS_N_HOST','PB4':'AO1_CS_N_HOST','PD3':'FREQ_1WIRE_DATA_HOST','PB5':'IOL1_L3_SCLK_COUNT'}
def validate(d,netlist=None,erc=None,process=None):
 errors=[]
 def ck(ok,msg):
  if not ok:errors.append(msg)
 try:
  parts=d['components'];node=d['node'];ck(len(parts)==d['fitted_component_count']==51 and d['purchased_fitted_parts']==45 and d['PCB_copper_testpads']==6,'51 physical/45 purchased/6 bare pads')
  ck(sum(len(q['pins']) for q in parts.values())==d['fitted_pad_count']==161,'161 exact electrical pads')
  ck(collections.Counter(q['kind'] for q in parts.values())=={'G031C':1,'SUP':1,'BUF4':1,'SCHMITT':1,'R':33,'C':8,'TP':6},'single fourth node actual inventory')
  ck(node['name']=='ACC' and node['port']=='L3' and node['slot']==3 and node['class']==0x31,'actual fourth protocol class/lane/slot')
  ck(not any(d[k] for k in ['manufacturing_ready','physical_qualification','firmware_implemented','target_compilation_passed']),'native source cannot prove target/physical/manufacture')
  mc=parts[node['mcu_ref']];expected={str(i+1):REQUIRED.get(port) for i,port in enumerate(PORTS)}
  ck(mc['mpn']=='STM32G031C8T6' and mc['footprint']=='Package_QFP:LQFP-48_7x7mm_P0.5mm' and mc['pins']==expected,'complete ST LQFP48 allocation, not absentK32 GPIO')
  ck(node['mapping']==REQUIRED and node['pin_port_names']=={str(i+1):port for i,port in enumerate(PORTS)},'independent physical GPIO table')
  ck(d['peripheral_mapping']=={'hostSPI1':{'PA4':'NSS_AF0','PA5':'SCK_AF0','PA6':'MISO_AF0','PA7':'MOSI_AF0'},'AI_AO_SPI2':{'PB12':'AI_softwareCS','PB3':'AO0_softwareCS','PB4':'AO1_softwareCS','PB13':'SCK_AF0','PB14':'MISO_AF0','PB15':'MOSI_AF0'},'AO_I2C1':{'PB8':'SCL_AF6_open_drain','PB9':'SDA_AF6_open_drain'},'FREQ_identity_GPIO':{'PD3':'bidirectional_open_drain_3V3_host'}},'ST DS12992 tables13/14 separate hardware peripherals')
  def resistor(a,b,v):return [q for q in parts.values() if q['kind']=='R' and set(q['pins'].values())=={a,b} and q['resistance_ohm']==v]
  ck(parts['R14533']['mpn']=='CRCW06030000Z0EA' and parts['R14533']['resistance_ohm']==0 and parts['R14533']['pins']=={'1':'ACC_IOL1_CLK_MCU','2':'IOL1_L3_SCLK_COUNT'},'actual post22ohm PB5 timer tap')
  for bit in range(4):ck(len(resistor(f'ACC_SLOT{bit}','IO_3V3' if 3&(1<<bit) else 'LOGIC_GND',10000))==1,'four real slot3 region straps')
  for net in ['AI_POWER_GOOD_HOST','AO0_POWER_GOOD_HOST','AO1_POWER_GOOD_HOST','RS485_POWER_GOOD_HOST','CAN_POWER_GOOD_HOST']:
   ck(node['health_inputs'][net]=={'active_good':1,'monitor_implemented':False} and len(resistor(net,'LOGIC_GND',10000))==1,'absent real monitor defaultsnotgood '+net)
  for net in ['AI_SENSOR_FAULT_HOST','AO0_CLAMP_ACTIVE','AO1_CLAMP_ACTIVE']:
   ck(node['health_inputs'][net]=={'active_fault':1,'monitor_implemented':False} and len(resistor(net,'IO_3V3',10000))==1,'missing fault/clamp observation failclosed '+net)
  for net in ['AO0_ENABLE_REQUEST','AO1_ENABLE_REQUEST']:ck(len(resistor(net,'LOGIC_GND',10000))==1,'analog enable requests resetOFF')
  for net in ['AO_I2C_SCL_HOST','AO_I2C_SDA_HOST']:ck(len(resistor(net,'IO_3V3',3300))==1,'real open-drain I2C pullups')
  sup=parts[node['supervisor_ref']];ck(sup['mpn']=='TPS3808G33DBVR' and sup['pins']=={'1':'ACC_NRST_N','2':'LOGIC_GND','3':'ACC_MR_N','4':None,'5':'IO_3V3','6':'IO_3V3'},'actual supervisor sense/reset/CT pinmap')
  reset=parts[node['reset_buffer_ref']];ck(reset['mpn']=='SN74LVC1G17DBVR' and reset['pins']=={'1':None,'2':'ACC_NRST_N','3':'LOGIC_GND','4':'ACC_CONTROLLER_RESET_N','5':'IO_3V3'},'buffered bidirectional internal-reset fanout')
  raw=lambda s:'ACC_IOL1_'+s+'_BUFFER';buf=parts[node['link_buffer_ref']]
  ck(buf['mpn']=='74LVC125APW,118' and buf['pins']=={'1':'LOGIC_GND','2':'IOL1_L3_CS_N','3':raw('CS'),'4':'LOGIC_GND','5':'IOL1_L3_SCLK','6':raw('CLK'),'7':'LOGIC_GND','8':raw('CMD'),'9':'IOL1_L3_MOSI','10':'LOGIC_GND','11':raw('RSP'),'12':'ACC_IOL1_RSP_MCU','13':'LOGIC_GND','14':'IO_3V3'},'actual exact Ioff buffer directions')
  for s in ['CS','CLK','CMD']:ck(len(resistor(raw(s),'ACC_IOL1_'+s+'_MCU',22))==1,'three source damping resistors')
  ck(len(resistor(raw('RSP'),'IOL1_L3_MISO',22))==1,'response source damping')
  for net,end in [('IOL1_L3_CS_N','IO_3V3'),('IOL1_L3_SCLK','LOGIC_GND'),('IOL1_L3_MOSI','LOGIC_GND'),('ACC_IOL1_RSP_MCU','LOGIC_GND'),('ACC_NRST_N','IO_3V3'),('ACC_MR_N','IO_3V3'),('ACC_SWCLK_BOOT0','LOGIC_GND'),('AI_CS_N_HOST','IO_3V3'),('AO0_CS_N_HOST','IO_3V3'),('AO1_CS_N_HOST','IO_3V3'),('AI_SCLK_HOST','LOGIC_GND'),('AI_SDI_HOST','LOGIC_GND')]:ck(len(resistor(net,end,10000))==1,'actual safe link/reset/boot default '+net)
  ck(d['frontend_owned_biases']=={'ACC_CARD_EN':'R14405','ACC_IO_ENABLE_STROBE':'R14404'},'process frontend ownership references')
  for net in d['frontend_owned_biases']:ck(not resistor(net,'LOGIC_GND',10000),'no duplicate frontend bias '+net)
  if process:
   for net,ref in d['frontend_owned_biases'].items():ck(process['components'][ref]['pins']=={'1':net,'2':'LOGIC_GND'} and process['components'][ref]['resistance_ohm']==10000,'actual process sourceOFF resistor '+net)
   pn={n for q in process['components'].values() for n in q['pins'].values() if n}
   ck(set(d['boundaries']['J14502']['pins'].values())<=pn,'all process controller observations connect real source')
  ck(d['DAC_readback_plan']=={'interface':'SPI2','selected_DAC':'AD5683RBRMZ-3','DAC80501_SPI_has_no_SDO':True,'asynchronous_update_required':True,'LDAC_tied_LOW':True,'readback_is_buffer_register_not_measured_VOUT':True,'independent_internal_DAC_latch_readout':False,'actual_terminal_monitor':'ADS1115IDGSR on isolated I2C1','native_frontend_implemented':True,'target_firmware_implemented':False},'real DAC interface/readback limitation')
  wd=d['iwdg_candidate'];ck(wd['LSI_min_hz']==29500 and wd['LSI_max_hz']==34000 and wd['PR_divisor']==4 and wd['RLR']==9 and wd['counted_period_max_s']==40/29500 and not wd['whole_reset_and_inhibit_qualified'] and not wd['option_provisioning_implemented'],'independent counted watchdog screen, not measuredwholepath')
  opt=d['option_requirements'];ck(opt['IWDG_SW']==0 and opt['NRST_MODE']==3 and opt['IRHEN']==1 and opt['bootloader_write_protected'] and opt['DIC_VREFBUF_disabled_with_external_VREF'] and not opt['BOR_level_selection_and_provisioning_verified'],'unprogrammed mandatory options remainactualrequirements')
  ck(d['logical_contract']=={'protocol':'IOL1','port':'L3','class':0x31,'slot':3,'frame_bytes':40,'period_s':100e-6,'spi_hz':8333333.3,'accept_timer_s':.001,'no_automatic_rearm':True,'same_board_region_not_card':True,'validate_before_outputs_and_watchdog':True},'complete frozen IOL1 semantics')
  ck(d['boundaries']['J14505']['pins']=={'1':'FREQ_1WIRE_DATA_HOST'} and mc['pins']['41']=='FREQ_1WIRE_DATA_HOST','bounded PD3 pin41 actual identityGPIO boundary, not pullup or fictitious peripheral')
  ck(len(node['factory_pads'])==6 and all(parts[r]['kind']=='TP' and len(parts[r]['pins'])==1 for r in node['factory_pads']),'factory copper pads not purchasedconnectors')
  ck(all(not q['physical'] and not q['mpn'] and not q['footprint'] for q in d['boundaries'].values()),'no fake fitted boundary connectors')
  if netlist:
   actual=native(netlist);ck(set(actual)==set(parts)|set(d['boundaries']),'native exact population')
   for ref,q in {**parts,**d['boundaries']}.items():ck(actual.get(ref)=={k:q[k] for k in ['mpn','value','footprint','pins']},'native exact pins '+ref)
  if erc:
   e=json.loads(Path(erc).read_text());ck(not e['ignored_checks'] and not any(s['violations'] for s in e['sheets']),'nativeERC0/0 noignoredchecks')
 except (KeyError,ValueError,TypeError,OSError) as exc:errors.append('invalid source '+str(exc))
 return {'ok':not errors,'errors':errors,'physical_footprints':51,'purchased_fitted_parts':45,'PCB_copper_testpads':6,'electrical_pads':161,'manufacturing_ready':False,'target_compiled':False,'warnings':['Analog/comms circuits and real monitors are separately unfinished; disconnected defaults are fault/not-good.','Source/watchdog arithmetic does not prove target firmware/options/whole20ms physical inhibit.']}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args();r=validate(json.loads((OUT/'design.json').read_text()),OUT/'netlist.xml',OUT/'erc.json',json.loads((ROOT/'hardware/motherboard_process/design.json').read_text()))
 if a.write:(OUT/'validation.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r,indent=2));raise SystemExit(not r['ok'])
