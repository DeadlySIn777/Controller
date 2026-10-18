"""Independent STM32G031 package/pin/interface/default checks; no firmware claim."""
import argparse,collections,json
from pathlib import Path
from hardware_validate_motherboard_do import native

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_io_control'
# Independently transcribed ST DS12992Rev4 Table12 LQFP columns.
CPORTS=['PC13','PC14','PC15','VBAT','VREF+','VDD/VDDA','VSS/VSSA','PF0','PF1','PF2-NRST','PA0','PA1','PA2','PA3','PA4','PA5','PA6','PA7','PB0','PB1','PB2','PB10','PB11','PB12','PB13','PB14','PB15','PA8','PA9','PC6','PC7','PA10','PA11','PA12','PA13','PA14-BOOT0','PA15','PD0','PD1','PD2','PD3','PB3','PB4','PB5','PB6','PB7','PB8','PB9']
KPORTS=['PB9','PC14','PC15','VDD/VDDA','VSS/VSSA','PF2-NRST','PA0','PA1','PA2','PA3','PA4','PA5','PA6','PA7','PB0','PB1','PB2','PA8','PA9','PC6','PA10','PA11','PA12','PA13','PA14-BOOT0','PA15','PB3','PB4','PB5','PB6','PB7','PB8']
DI_PINS=[1,2,3,8,9,11,12,13,14,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33]

def validate(d,netlist=None,erc=None,di=None,do=None):
 errors=[];warnings=[]
 def ck(ok,msg):
  if not ok:errors.append(msg)
 def passive(net,end,val):return [r for r,p in d['components'].items() if p['kind']=='R' and set(p['pins'].values())=={net,end} and p['resistance_ohm']==val]
 try:
  parts=d['components'];ck(len(parts)==d['fitted_component_count']==100,'100 physical footprints after fourduplicate bias removals');ck(sum(len(x['pins']) for x in parts.values())==d['fitted_pad_count']==342,'342 numbered electrical pads')
  ck(collections.Counter(p['kind'] for p in parts.values())=={'G031C':1,'G031K':2,'SUP':3,'BUF4':3,'SCHMITT':2,'R':52,'C':19,'TP':18},'exact region inventory')
  ck(not any(d[k] for k in ['manufacturing_ready','physical_qualification','firmware_implemented','target_compilation_passed']),'source must not claim target or physical qualification')
  ck(d['logical_contract']=={'protocol':'IOL1','ports':['L0','L1','L2'],'frame_bytes':40,'period_s':100e-6,'spi_hz':8333333.3,'accept_timer_s':.001,'iwdg_max_s':.002,'validate_before_outputs_and_watchdog':True,'no_automatic_resume':True,'no_fake_card_presence':True,'same_board_regions_not_custom_cards':True},'frozen IOL1 semantics')
  wd=d['iwdg_candidate'];ck(wd['LSI_min_hz']==29500 and wd['LSI_max_hz']==34000 and wd['PR_divisor']==4 and wd['RLR']==9,'independentLSI watchdog screen uses min/max notnominal')
  ck(wd['counted_period_min_s']==40/34000 and wd['counted_period_max_s']==40/29500 and .001<wd['counted_period_min_s']<wd['counted_period_max_s']<.002,'counted watchdog period supports1ms accept timer, doesnot prove wholepath')
  ck(wd['application_refresh_only_full_accept'] and wd['bootloader_refresh_allowed_only_outputs_OFF'] and wd['no_debug_freeze_in_shipping'] and not wd['whole_reset_and_inhibit_qualified'] and not wd['option_provisioning_implemented'],'watchdog useful-progress and evidence boundary')
  opt=d['option_requirements'];ck(opt['IWDG_SW']==0 and opt['NRST_MODE']==3 and opt['IRHEN']==1 and opt['nBOOT_SEL']==1 and opt['nBOOT0']==1 and opt['bootloader_write_protected'] and opt['DIC_VREFBUF_disabled_with_external_VREF'] and not opt['BOR_level_selection_and_provisioning_verified'],'hardwarestart/bidirectionalreset/protectedflash are provisioningrequirements')
  ck(d['electrical_limits']=={'DO_channel_continuous_a':.5,'DO_quad_continuous_a':2,'DI_sensor_group_continuous_a':.2,'driver_commission_ILIM_code':6,'driver_POR_ILIM_a':1.25},'electrical ratings unchanged')
  bulk=[p for p in parts.values() if p['kind']=='C' and p['capacitance_f']==4700e-9]
  ck(len(bulk)==3 and all(p['mpn']=='GRM21BR71A475KE51K' and p['footprint']=='Capacitor_SMD:C_0805_2012Metric' and p['voltage_rating_v']==10 and p['pins']=={'1':'IO_3V3','2':'LOGIC_GND'} for p in bulk),'three primary-verified active 4.7uF 10V 0805 bulk parts; obsolete MPN rejected')
  ck(len(d['nodes'])==3,'three independent required nodes')
  for idx,node in enumerate(d['nodes']):
   name=['DIC','DOA','DOB'][idx];mc=parts[node['mcu_ref']];ports=CPORTS if idx==0 else KPORTS;pin=lambda gpio:str(ports.index(gpio)+1)
   ck(node['name']==name and node['port']==f'L{idx}' and node['slot']==idx and node['class']==(0x11 if idx==0 else 0x21),'logical lane/class/slot binding')
   ck(node['pin_port_names']=={str(i+1):p for i,p in enumerate(ports)} and set(mc['pins'])==set(node['pin_port_names']),'actualmanufacturer LQFP pinmap, not generic GPIOcount')
   ck(mc['mpn']==('STM32G031C8T6' if idx==0 else 'STM32G031K8T6') and mc['footprint']==('Package_QFP:LQFP-48_7x7mm_P0.5mm' if idx==0 else 'Package_QFP:LQFP-32_7x7mm_P0.8mm'),'MCU exact MPN/package')
   expected={str(i+1):None for i in range(len(ports))}
   def setp(g,n):expected[pin(g)]=n
   setp('VDD/VDDA','IO_3V3');setp('VSS/VSSA','LOGIC_GND');setp('PF2-NRST',name+'_NRST_N');setp('PA13',name+'_SWDIO');setp('PA14-BOOT0',name+'_SWCLK_BOOT0')
   if idx==0:setp('VBAT','IO_3V3');setp('VREF+','IO_3V3')
   for gpio,suffix in [('PA4','CS'),('PA5','CLK'),('PA6','RSP'),('PA7','CMD')]:setp(gpio,name+'_IOL1_'+suffix+'_MCU')
   slots=['PB6','PB7','PB8','PB9'] if idx==0 else ['PA9','PA10','PA11','PA12']
   for bit,gpio in enumerate(slots):
    setp(gpio,name+f'_SLOT{bit}');ck(len(passive(name+f'_SLOT{bit}','IO_3V3' if idx&(1<<bit) else 'LOGIC_GND',10000))==1,'real motherboard node-ID strap')
   if idx==0:
    ck(set(node['di_mapping'])=={str(i) for i in range(24)},'all24generalDI are acquired')
    for i,num in enumerate(DI_PINS):
     expected[str(num)]=f'DI{i}_LOGIC';ck(node['di_mapping'][str(i)]=={'gpio':CPORTS[num-1],'pin':num,'net':f'DI{i}_LOGIC'},'DIC independent24DI pins')
    for gpio,net in [('PA12','DI_SENSOR_G0_FAULT'),('PA15','DI_SENSOR_G1_FAULT'),('PD0','DI_SENSOR_G2_FAULT'),('PD1','DI_SAFETY_SUPPLY_FAULT'),('PD2','DI_SAFETY_SECONDARY_FAULT')]:
     setp(gpio,net);ck(len(passive(net,'IO_3V3',10000))==1 and node['health_inputs'][net]=={'pin':int(pin(gpio)),'active_fault':1,'parent_monitor_implemented':False},'missingDIrailmonitor biasesfault; nofakehealthy')
    ck(not node['output_boundary'] and node['reset_buffer_ref'] is None,'DI doesnot acquire DOpermission')
   else:
    for gpio,net in [('PB8',name+'_SCLK_HOST'),('PB7',name+'_SDI_HOST'),('PB6',name+'_SDO_HOST'),('PB9',name+'_CS_N_HOST'),('PA0',name+'_IO_ENABLE_STROBE'),('PA1',name+'_CARD_EN'),('PA2',name+'_OUT_EN_LATCH'),('PA3','OUT_PERMIT_'+('A' if idx==1 else 'B')),('PB0',name+'_FLT_N_HOST'),('PB1',name+'_FIELD_POWER_GOOD'),('PC6',name+'_DO_EN_LOGIC')]:setp(gpio,net)
    ck(node['health_inputs']=={name+'_FIELD_POWER_GOOD':{'pin':16,'active_good':1,'parent_monitor_implemented':False}} and len(passive(name+'_FIELD_POWER_GOOD','LOGIC_GND',10000))==1,'missingDOrail health defaultsnotgood')
    rb=parts[node['reset_buffer_ref']];ck(rb['mpn']=='SN74LVC1G17DBVR' and rb['pins']=={'1':None,'2':name+'_NRST_N','3':'LOGIC_GND','4':name+'_CONTROLLER_RESET_N','5':'IO_3V3'},'realNRSTSchmitt buffer drives10k frontend load, no1.65Vdivider')
    for net in [name+'_CARD_EN',name+'_IO_ENABLE_STROBE']:ck(not passive(net,'LOGIC_GND',10000),'four frontend-owned pull-downs arenot duplicated')
   ck(mc['pins']==expected,'complete MCU physical pin/allocation agreement '+name)
   sp=parts[node['supervisor_ref']];ck(sp['mpn']=='TPS3808G33DBVR' and sp['pins']=={'1':name+'_NRST_N','2':'LOGIC_GND','3':name+'_MR_N','4':None,'5':'IO_3V3','6':'IO_3V3'},'supervisor actualDBV pinmap/rail/reset; CTopen20msnominal')
   ck(len(passive(name+'_NRST_N','IO_3V3',10000))==1 and len(passive(name+'_MR_N','IO_3V3',10000))==1 and len(passive(name+'_SWCLK_BOOT0','LOGIC_GND',10000))==1,'resetandboot defaults')
   raw=lambda suffix:name+'_IOL1_'+suffix+'_BUFFER';buf=parts[node['link_buffer_ref']]
   ck(buf['mpn']=='SN74LVC125APWR' and buf['pins']=={'1':'LOGIC_GND','2':f'IOL1_L{idx}_CS_N','3':raw('CS'),'4':'LOGIC_GND','5':f'IOL1_L{idx}_SCLK','6':raw('CLK'),'7':'LOGIC_GND','8':raw('CMD'),'9':f'IOL1_L{idx}_MOSI','10':'LOGIC_GND','11':raw('RSP'),'12':name+'_IOL1_RSP_MCU','13':'LOGIC_GND','14':'IO_3V3'},'SPIIoffbuffer physicaldirections')
   for suffix in ['CS','CLK','CMD']:ck(len(passive(raw(suffix),name+'_IOL1_'+suffix+'_MCU',22))==1,'outgoingbuffer damping source')
   ck(len(passive(raw('RSP'),f'IOL1_L{idx}_MISO',22))==1,'FPGAresponse source damping')
   for net,end in [(f'IOL1_L{idx}_CS_N','IO_3V3'),(f'IOL1_L{idx}_SCLK','LOGIC_GND'),(f'IOL1_L{idx}_MOSI','LOGIC_GND'),(name+'_IOL1_RSP_MCU','LOGIC_GND')]:ck(len(passive(net,end,10000))==1,'linkmissing-inputstate')
   ck(not node['firmware_implemented'] and not node['programmed_option_bytes_verified'],'MCUisdrawn, notprogrammed')
   ck(len(node['factory_pads'])==6 and {parts[r]['pins']['1'] for r in node['factory_pads']}=={'IO_3V3','LOGIC_GND',name+'_SWDIO',name+'_SWCLK_BOOT0',name+'_NRST_N',name+'_MR_N'},'actual sixfactorycopperpads pernode')
  if di:
   diparts=di['components'];nets={n for p in diparts.values() for n in p['pins'].values()};ck(all(f'DI{i}_LOGIC' in nets for i in range(24)),'actualDIfrontend netagreement')
  if do:
   ck(d['frontend_owned_biases']=={'DOA_CARD_EN':'R10004','DOA_IO_ENABLE_STROBE':'R10003','DOB_CARD_EN':'R10024','DOB_IO_ENABLE_STROBE':'R10023'},'fourexactfrontend pull-downowners')
   for net,ref in d['frontend_owned_biases'].items():
    p=do['components'][ref];ck(p['pins']=={'1':net,'2':'LOGIC_GND'} and p['resistance_ohm']==10000,'existingphysicalfrontend biasverified')
   for name in ['DOA','DOB']:
    gates=[p for p in do['components'].values() if p['kind']=='AND4' and p['pins']['2']==name+'_CONTROLLER_RESET_N'];ck(len(gates)==1,'actualfrontend resetinputagreement')
    ck(any(p['kind']=='DFF' and p['pins']['5']==name+'_OUT_EN_LATCH' for p in do['components'].values()),'actualfrontend latch observation')
  for p in d['boundaries'].values():ck(p['physical'] is False and not p['mpn'] and not p['footprint'],'noinventedphysicalcardsconnectors')
  if netlist:
   actual=native(netlist);ck(set(actual)==set(parts)|set(d['boundaries']),'nativeXML population')
   for ref,p in {**parts,**d['boundaries']}.items():ck(actual.get(ref)=={k:p[k] for k in ['mpn','footprint','value','pins']},'nativeXML actualpin/value '+ref)
  if erc:
   e=json.loads(Path(erc).read_text());ck(e['ignored_checks']==[] and not any(s['violations'] for s in e['sheets']),'nativeERCzeroerrors/warnings/nosuppression')
 except (KeyError,ValueError,TypeError,OSError,IndexError) as exc:errors.append('invalid source/evidence: '+str(exc))
 warnings=['Firmware/options/protectedbootloader/identity remain unimplemented; cleanERC doesnot establish programmedsafe operation.','FiveDI faults/twoDOgood inputs are explicit parent monitoring gaps, biasedfault/notgood while missing.','LSI arithmetic checks countedperiod only; register synchronization/reset/field inhibition and loadedSPI timings require qualification.']
 return {'ok':not errors,'errors':errors,'warnings':warnings,'physical_footprints':100,'purchased_fitted_parts':82,'PCB_copper_testpads':18,'electrical_pads':342,'manufacturing_ready':False,'firmware_implemented':False,'target_compiled':False}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args();load=lambda p:json.loads(p.read_text());r=validate(load(OUT/'design.json'),OUT/'netlist.xml',OUT/'erc.json',load(ROOT/'hardware/motherboard_di/design.json'),load(ROOT/'hardware/motherboard_do/design.json'))
 if a.write:(OUT/'validation.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r,indent=2));raise SystemExit(not r['ok'])
