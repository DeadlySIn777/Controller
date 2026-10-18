"""Actual two-island AO source. No target firmware or assembled qualification."""
from __future__ import annotations
import csv,json,uuid,shutil
from pathlib import Path
from hardware_build_assembly import parse,dump
from hardware_build_tx_schematic import symbol,effects,quote
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_analog_output'
NS=uuid.UUID('798d6c1d-95e4-438b-93d6-e6b0465d1088')
KINDS={
 'DAC':{1:('VDD','power_in'),2:('RESET_N','input'),3:('SDO','output'),4:('LDAC_N','input'),5:('GND','power_in'),6:('SCLK','input'),7:('SYNC_N','input'),8:('SDI','input'),9:('VREF','output'),10:('VOUT','output')},
 'ADC':{1:('ADDR','input'),2:('ALERT_N','open_collector'),3:('GND','power_in'),4:('AIN0','input'),5:('AIN1','input'),6:('AIN2','input'),7:('AIN3','input'),8:('VDD','power_in'),9:('SDA','bidirectional'),10:('SCL','input')},
 'OPA':{1:('OUT','output'),2:('V-','power_in'),3:('IN+','input'),4:('IN-','input'),5:('V+','power_in')},
 'LDO':{1:('OUT','power_out'),2:('DNC','no_connect'),3:('PG','open_collector'),4:('GND','power_in'),5:('EN','input'),6:('NC','no_connect'),7:('DELAY','passive'),8:('IN','power_in'),9:('EP','power_in')},
 'DCDC':{1:('-VIN','power_in'),2:('+VIN','power_in'),4:('+VOUT','power_out'),6:('-VOUT','power_out')},
 'WINDOW':{1:('OUTA','open_collector'),2:('GND','power_in'),3:('INA+','input'),4:('INB-','input'),5:('VDD','power_in'),6:('OUTB','open_collector')},
 'ISO6':{1:('VCC1','power_in'),2:('INA','input'),3:('INB','input'),4:('INC','input'),5:('IND','input'),6:('INE','input'),7:('OUTF','output'),8:('GND1','power_in'),9:('GND2','power_in'),10:('INF','input'),11:('OUTE','output'),12:('OUTD','output'),13:('OUTC','output'),14:('OUTB','output'),15:('OUTA','output'),16:('VCC2','power_in')},
 'ISO2':{1:('GND1','power_in'),2:('NC','no_connect'),3:('VCC1','power_in'),4:('INA','input'),5:('INB','input'),6:('NC','no_connect'),7:('GND1','power_in'),8:('NC','no_connect'),9:('GND2','power_in'),10:('NC','no_connect'),11:('NC','no_connect'),12:('OUTB','output'),13:('OUTA','output'),14:('VCC2','power_in'),15:('NC','no_connect'),16:('GND2','power_in')},
 'I2CISO':{1:('VCC1','power_in'),2:('SDA1','bidirectional'),3:('SCL1','bidirectional'),4:('GND1','power_in'),5:('GND2','power_in'),6:('SCL2','bidirectional'),7:('SDA2','bidirectional'),8:('VCC2','power_in')},
 'AND':{1:('A','input'),2:('B','input'),3:('GND','power_in'),4:('Y','output'),5:('VCC','power_in')},
 'INV':{1:('NC','no_connect'),2:('A','input'),3:('GND','power_in'),4:('Y','output'),5:('VCC','power_in')},
 'ODINV':{1:('NC','no_connect'),2:('A','input'),3:('GND','power_in'),4:('Y','open_collector'),5:('VCC','power_in')},
 'BUFFER':{1:('OE_N','input'),2:('A','input'),3:('GND','power_in'),4:('Y','tri_state'),5:('VCC','power_in')},
 'RELAY':{1:('LED_A','passive'),2:('LED_K','passive'),3:('CONTACT','passive'),4:('CONTACT','passive')},
 'R':{1:('','passive'),2:('','passive')},'C':{1:('','passive'),2:('','passive')},'TVS':{1:('','passive'),2:('','passive')},'PWR_FLAG':{1:('pwr','power_out')}}
MPNS={
 'DAC':('AD5683RBRMZ-3','Package_SO:MSOP-10_3x3mm_P0.5mm'),
 'ADC':('ADS1115IDGSR','CNC_MB_AO:ADS1115_DGS10_TI'),
 'OPA':('OPA197IDBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'LDO':('TPS7A1650DGNR','CNC_MB_AO:TPS7A16_DGN8_TI'),
 'DCDC':('TMR 1-2412','Converter_DCDC:Converter_DCDC_TRACO_TMR-1-xxxx_Single_THT'),
 'WINDOW':('TPS3700DDCR','Package_TO_SOT_SMD:SOT-23-6'),
 'ISO6':('ISO7761FDWR','CNC_MB_AO:ISO7761_DW16_TI_HV'),
 'ISO2':('ISO7720FDWR','CNC_MB_AO:ISO7720_DW16_TI_HV'),
 'I2CISO':('ISO1540DR','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'),
 'AND':('SN74LVC1G08DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'INV':('SN74LVC1G14DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'ODINV':('SN74LVC1G06DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'BUFFER':('SN74LVC1G125DBVR','Package_TO_SOT_SMD:SOT-23-5')}

def description():
 parts={};bounds={};u=r=c=d=14600;channels=[]
 def ic(kind,pins,role,mpn=None,fp=None):
  nonlocal u
  u+=1;ref=f'U{u}';base,foot=MPNS.get(kind,(None,None));parts[ref]={'kind':kind,'mpn':mpn or base,'value':mpn or base,'footprint':fp or foot,'physical':True,'pins':{str(k):v for k,v in pins.items()},'role':role};return ref
 def res(a,b,v,role,precision=False):
  nonlocal r
  r+=1;ref=f'R{r}';codes={4.7:'4R70',390:'390R',1000:'1K00',10000:'10K0',30000:'30K0',33200:'33K2',100000:'100K',274000:'274K',316000:'316K',3300:'3K30'}
  mpn='TNPW0603'+codes[v]+'BEEA' if precision else 'CRCW0603'+codes[v]+'FKEA';parts[ref]={'kind':'R','mpn':mpn,'value':f'{v}R'+('0.1%' if precision else '1%'),'footprint':'Resistor_SMD:R_0603_1608Metric','physical':True,'pins':{'1':a,'2':b},'resistance_ohm':v,'tolerance':.001 if precision else .01,'tcr_ppm_K':25 if precision else 100,'role':role};return ref
 def cap(a,g,nf,role):
  nonlocal c
  c+=1;ref=f'C{c}';mpn,fp,v={10:('GRM1885C2A103JA01D','C_0603_1608Metric',100),100:('GRM188R72A104KA35D','C_0603_1608Metric',100),1000:('GRM188R71H105KA12D','C_0603_1608Metric',50),2200:('CGA5L3X7S2A225K160AB','C_1206_3216Metric',100),22000:('GCM31CR71A226KE02L','C_1206_3216Metric',10)}[nf];parts[ref]={'kind':'C','mpn':mpn,'value':f'{nf}nF{v}V','footprint':'Capacitor_SMD:'+fp,'physical':True,'pins':{'1':a,'2':g},'capacitance_f':nf*1e-9,'voltage_rating_v':v,'role':role};return ref
 def boundary(ref,nets,role):bounds[ref]={'kind':'Boundary'+str(len(nets)),'mpn':'','value':'PARENT: '+role,'footprint':'','physical':False,'pins':{str(i+1):n for i,n in enumerate(nets)},'role':role}
 for i in range(2):
  n=lambda x:f'AO{i}_'+x;g=n('COM');s5=n('5V');s12=n('12V');pg=n('POWER_GOOD_FIELD')
  dc=ic('DCDC',{1:'LOGIC_GND',2:'CORE_24V_PROTECTED',4:s12,6:g},'purchased isolated 1W module, real independent AO island; functional insulation only')
  cap('CORE_24V_PROTECTED','LOGIC_GND',2200,'converter input local bypass');cap(s12,g,2200,'converter output storage');cap(s12,g,100,'converter output HF bypass')
  ld=ic('LDO',{1:s5,2:None,3:pg,4:g,5:s12,6:None,7:n('PG_DELAY'),8:s12,9:g},'fixed5V; DNC2 has NO electrical net; PG joins actual12V UV/OV monitor')
  cap(s12,g,100,'LDO input HF bypass');cap(s5,g,22000,'LDO output nominal22uF, effective>=2.2uF must be qualified');cap(s5,g,100,'LDO output HF bypass');cap(n('PG_DELAY'),g,10,'PG delayed good typical11.93ms, fault release not certified');res(s5,g,100000,'local regulator minimum load/discharge')
  win=ic('WINDOW',{1:pg,2:g,3:n('UV_SENSE'),4:n('OV_SENSE'),5:s12,6:pg},'actual12V UV/OV open-drain outputs wire-AND with LDO5V PG')
  for a,b,v in [(s12,n('UV_SENSE'),274000),(n('UV_SENSE'),g,10000),(s12,n('OV_SENSE'),316000),(n('OV_SENSE'),g,10000)]:res(a,b,v,'real AO12V window divider',True)
  res(pg,s5,10000,'actual good pull-up, not a constant healthy strap');cap(s12,g,100,'window comparator bypass')
  allow=ic('AND',{1:f'AO{i}_ENABLE_REQUEST',2:'PWM_ENABLE_LOGIC',3:'LOGIC_GND',4:n('ENABLE_QUALIFIED'),5:'IO_3V3'},'AO request only becomes permitted after existing independent hardware rearm latch')
  cap('IO_3V3','LOGIC_GND',100,'enable hardware gate bypass')
  iso=ic('ISO6',{1:'IO_3V3',2:'AI_SCLK_HOST',3:'AI_SDI_HOST',4:f'AO{i}_CS_N_HOST',5:n('ENABLE_QUALIFIED'),6:'ACC_CLR_N',7:n('SDO_ISOLATED'),8:'LOGIC_GND',9:g,10:n('DAC_SDO'),11:n('RESET_ISOLATED'),12:n('ENABLE_ISOLATED'),13:n('DAC_CS_N'),14:n('DAC_SDI'),15:n('DAC_SCLK'),16:s5},'5forward1return, exact F defaultLOW; missing primary resets DAC even though chip-select also LOW')
  cap('IO_3V3','LOGIC_GND',100,'SPI/control isolation primary bypass');cap(s5,g,100,'SPI/control isolation secondary bypass')
  run=ic('AND',{1:n('ENABLE_ISOLATED'),2:pg,3:g,4:n('RUN'),5:s5},'real local PG independently withdraws both AO contact LED requests')
  reset=ic('AND',{1:n('RESET_ISOLATED'),2:pg,3:g,4:n('DAC_RESET_N'),5:s5},'power or actual OUT-permit/reset loss hardware resets DAC to zero')
  for ref in [run,reset]:cap(s5,g,100,ref+' local bypass')
  res(n('DAC_RESET_N'),g,10000,'DAC reset asserted until hardware good and host clear released');res(n('RUN'),g,10000,'local relay request defaults OFF');res(n('DAC_CS_N'),s5,10000,'normal powered inactive chip-select HIGH')
  dac=ic('DAC',{1:s5,2:n('DAC_RESET_N'),3:n('DAC_SDO'),4:g,5:g,6:n('DAC_SCLK'),7:n('DAC_CS_N'),8:n('DAC_SDI'),9:n('VREF'),10:n('DAC_VOUT')},'exact -3 SDO variant; hardware reset zero; LDAC tiedLOW updates actual DAC, not cache')
  cap(s5,g,100,'DAC bypass');cap(n('VREF'),g,10,'DAC reference decoupling per primary datasheet')
  buf=ic('BUFFER',{1:f'AO{i}_CS_N_HOST',2:n('SDO_ISOLATED'),3:'LOGIC_GND',4:'AI_SDO_HOST',5:'IO_3V3'},'actual OE-isolated return on shared ADC/DAC SPI2; no wired parallel push-pull SDO')
  cap('IO_3V3','LOGIC_GND',100,'qualified Ioff return buffer bypass')
  sink=ic('ODINV',{1:None,2:n('RUN'),3:g,4:n('LED_SINK'),5:s5},'runHIGH energizes both independent contacts; missing power leaves normally-open output and normally-closed input clamp safe')
  cap(s5,g,100,'contact LED sink bypass')
  clamp=ic('RELAY',{1:s5,2:n('CLAMP_LED_K'),3:n('OPA_IN'),4:g},'normally CLOSED input-to-common clamp; source NO and NC relay types are deliberately distinct','TLP4176A(TP,F','CNC_MB_AO:TLP4176A_2.54SOP4_11-5H1S')
  series=ic('RELAY',{1:s5,2:n('SERIES_LED_K'),3:n('OUTPUT_PROTECTED'),4:f'AO{i}_OUT'},'normally OPEN output disconnect; terminal pulldown holds zero even with island absent','TLP3640A(TPL,E','CNC_MB_AO:TLP3640A_SO4_11-3C1')
  for key in ['CLAMP','SERIES']:res(n(key+'_LED_K'),n('LED_SINK'),390,'separate LED branch; both combined remain below32mA sink screen')
  amp=ic('OPA',{1:n('AMP_OUT'),2:g,3:n('OPA_IN'),4:n('FEEDBACK'),5:s12},'actual precision 12V amplifier gain4; output load>=2kohm, rail accuracy to qualify')
  cap(s12,g,100,'amplifier bypass');res(n('DAC_VOUT'),n('OPA_IN'),1000,'input clamp current limiting');res(n('AMP_OUT'),n('FEEDBACK'),30000,'precision gain4 feedback',True);res(n('FEEDBACK'),g,10000,'precision gain4 bottom',True);res(n('AMP_OUT'),n('OUTPUT_PROTECTED'),4.7,'AO series isolation resistor,6mA nominal totalload drop~28.2mV');res(f'AO{i}_OUT',g,10000,'true terminal zero when NO output relay open')
  d+=1;tv=f'D{d}';parts[tv]={'kind':'TVS','mpn':'SMBJ12CA-E3/52','value':'SMBJ12CA-E3/52','footprint':'Diode_SMD:D_SMB','physical':True,'pins':{'1':f'AO{i}_OUT','2':g},'role':'12Vstandoff bidirectional terminal suppressor; assembled ESD not claimed'}
  obs=ic('INV',{1:None,2:n('LED_SINK'),3:g,4:n('RUN_OBSERVED'),5:s5},'actual contact-drive voltage observation; not proof that mechanical/solid-state contact transitioned')
  cap(s5,g,100,'clamp drive observer bypass')
  health=ic('ISO2',{1:g,2:None,3:s5,4:pg,5:n('RUN_OBSERVED'),6:None,7:g,8:None,9:'LOGIC_GND',10:None,11:None,12:n('RUN_OBSERVED_HOST'),13:f'AO{i}_POWER_GOOD_HOST',14:'IO_3V3',15:None,16:'LOGIC_GND'},'actual PG and drive observations, F defaultsLOW means missing island not healthy')
  cap(s5,g,100,'health isolation primary bypass');cap('IO_3V3','LOGIC_GND',100,'health isolation receiving bypass')
  inv=ic('INV',{1:None,2:n('RUN_OBSERVED_HOST'),3:'LOGIC_GND',4:f'AO{i}_CLAMP_ACTIVE',5:'IO_3V3'},'missing island/defaultLOW observation becomes clamp-active HIGH at MCU')
  cap('IO_3V3','LOGIC_GND',100,'clamp observation inverter bypass')
  i2c=ic('I2CISO',{1:'IO_3V3',2:'AO_I2C_SDA_HOST',3:'AO_I2C_SCL_HOST',4:'LOGIC_GND',5:g,6:n('SCL'),7:n('SDA'),8:s5},'bidirectional isolated terminal-monitoring I2C; host pullups already ownedACC')
  cap('IO_3V3','LOGIC_GND',100,'I2C isolation primary bypass');cap(s5,g,100,'I2C isolation secondary bypass');res(n('SCL'),s5,3300,'actual isolated SCL pullup');res(n('SDA'),s5,3300,'actual isolated SDA pullup')
  for key,src in [('TERMINAL',f'AO{i}_OUT'),('12V',s12),('5V',s5)]:res(src,n('MON_'+key),100000,'read actual voltage, not commanded value',True);res(n('MON_'+key),g,33200,'precision monitoring attenuation',True);cap(n('MON_'+key),g,10,'monitor anti-alias/stability; ADCsourceimpedance error needs calibration')
  adc=ic('ADC',{1:g if i==0 else s5,2:None,3:g,4:n('MON_TERMINAL'),5:n('MON_12V'),6:n('MON_5V'),7:n('VREF'),8:s5,9:n('SDA'),10:n('SCL')},'real 16bit terminal/rails/reference monitor; 860SPS is slow diagnostics, not 1kHz general AI')
  cap(s5,g,100,'readback ADC bypass')
  channels.append({'channel':i,'isolated_return':g,'dac_ref':dac,'readback_adc_ref':adc,'adc_i2c_address':hex(0x48+i),'amplifier_ref':amp,'input_clamp_ref':clamp,'output_disconnect_ref':series,'power_module_ref':dc,'regulator_ref':ld,'window_ref':win,'host_enable_gate_ref':allow,'local_enable_gate_ref':run,'local_reset_gate_ref':reset,'spi_isolator_ref':iso,'spi_return_buffer_ref':buf,'health_isolator_ref':health,'clamp_observer_ref':obs,'clamp_inverter_ref':inv,'i2c_isolator_ref':i2c,'contact_sink_ref':sink,'terminal':f'AO{i}_OUT','voltage_span_v':[0,10],'minimum_receiver_ohm':2000,'nominal_gain':4,'reference_nominal_v':2.5,'clamp_default_closed':True,'disconnect_default_open':True,'actual_terminal_readback':True,'input_register_readback':True,'LDAC_LOW_copies_input_to_DAC':True,'no_independent_internal_DAC_latch_readout':True,'contact_drive_observation_not_contact_proof':True,'effective_precision_bits_target':12,'physical_qualified':False})
 res('AI_SDO_HOST','LOGIC_GND',100000,'shared SPI2 inactive return bias; AI frontend must gate its SDO by separate CS')
 boundary('J14601',['IO_3V3','LOGIC_GND','CORE_24V_PROTECTED','PWM_ENABLE_LOGIC','ACC_CLR_N'],'actual parent rails and independent reset/rearm/permission gates')
 boundary('J14602',['AI_SCLK_HOST','AI_SDI_HOST','AI_SDO_HOST','AO0_CS_N_HOST','AO1_CS_N_HOST','AO_I2C_SCL_HOST','AO_I2C_SDA_HOST','AO0_ENABLE_REQUEST','AO1_ENABLE_REQUEST','AO0_POWER_GOOD_HOST','AO1_POWER_GOOD_HOST','AO0_CLAMP_ACTIVE','AO1_CLAMP_ACTIVE'],'versioned ACC2 SPI2 two CS additions; existing I2C1 also reserved statusLED bus')
 boundary('J14603',['AO0_OUT','AO0_COM','AO1_OUT','AO1_COM'],'two independent isolated0–10V endpoints; typed physical terminals remain parent')
 return {'schema_version':1,'revision':'motherboard-analog-output-r0.1','status':'actual_source_candidate','components':parts,'boundaries':bounds,'channels':channels,'fitted_component_count':len(parts),'fitted_pad_count':sum(len(p['pins']) for p in parts.values()),'manufacturing_ready':False,'physical_qualification':False,'firmware_implemented':False,'contract_correction':{'authorised':True,'prior_dac':'DAC80501ZDQFR','new_dac':'AD5683RBRMZ-3','reason':'DAC80501 has no SPI SDO; its I2C register readback/write cannot meet frozen20us SPI allocation. Exact -3 real SDO preserves readback; no cache/readback substitution.','ACC2_gpio':{'PB3':'AO0_CS_N_HOST','PB4':'AO1_CS_N_HOST'},'wire_time_only':{'spi_hz':4000000,'two_write_clocks':48,'apply_write_seconds':12e-6,'two_readback_clocks':96,'readback_seconds':24e-6,'combined_seconds':36e-6,'readback_is_not_part_of_20us_apply_allocation':True,'not_full_commit_latency_proof':True},'I2C1_preserved':True},'electrical_limits':{'AO_channels':2,'AO_span_v':[0,10],'receiver_min_ohm':2000,'target_effective_bits':12,'independent_islands':True,'no_automatic_rearm':True},'open_gates':['Native target firmware including real DAC register transactions, actual ADS terminal/rail/reference readback freshness, and option-byte hardware watchdog must be implemented.','4MHz twoDACwrites=12us wiretime within20usapply; twoinputreadbacks=24us separate,36uscombined within59.6usprocessing window. Isolation round-trip/CS gaps/MCU scheduling and frozenwhole160.4uscommit require loaded proof.','12Vregulator headroom, effectiveC,LDOthermal,current budget,inputdrop,0–55Cprecision,2kohmload andcalibration remain qualification.','Photorelay worst-case release,total20msinhibit,cablecapacitive/inductive/short/ESD behavior andallpartialpowerstates require prototype measurements.','Actual contact drive voltage is observed but not contact proof; terminal readback must report invalid/stale rather than zero when ADC/bus/power fails.','Typedphysicalterminal/chassis/return routing andmoduleheight/PCBcreepage must be reconciled by parentboard.','Shared I2C addresses0x48/0x49 reserved; qualifiedLEDaddresses andhostVIL/offset/capacitance/clock-stretch conditions remain required.'],'power_budget':{'IO_3V3_bypass_nominal_uf':sum(q['capacitance_f'] for q in parts.values() if q['kind']=='C' and q['pins']['1']=='IO_3V3')*1e6,'AO5_LED_both_max_screen_a':2*5.1/(390*.99),'AO5_LED_single_min_screen_a':(4.9-1.9-.55)/(390*1.01),'AO12_module_rated_a':.083,'no_dynamic_power_qualification':True}}

def footprints(out):
 lib=out/'CNC_MB_AO.pretty';lib.mkdir(exist_ok=True)
 for source in ['hardware/motherboard_motors/CNC_Motors.pretty/TLP3640A_SO4_11-3C1.kicad_mod','hardware/motherboard_motors/CNC_Motors.pretty/TLP4176A_2.54SOP4_11-5H1S.kicad_mod','hardware/motherboard_motor_power/CNC_MotorPower.pretty/ISO7720_DW16_TI_HV.kicad_mod']:shutil.copyfile(ROOT/source,lib/Path(source).name)
 raw=(lib/'ISO7720_DW16_TI_HV.kicad_mod').read_text().replace('ISO7720_DW16_TI_HV','ISO7761_DW16_TI_HV').replace('ISO7720FDWR','ISO7761FDWR').replace('SLLSEP3G','SLLSER1H')
 (lib/'ISO7761_DW16_TI_HV.kicad_mod').write_text(raw,encoding='utf-8')
 raw='(footprint "ADS1115_DGS10_TI"(version 20241229)(generator "controller_hardware")(layer "F.Cu")(descr "TI ADS1115DGS0010A4221984/A05/2015 exactland1.45x.3centres+-2.2,pitch.5")(attr smd)(property "Reference" "REF**"(at 0 -2)(layer "F.SilkS")(effects(font(size .7 .7)(thickness .1))))(property "Value" "ADS1115_DGS10_TI"(at 0 2)(layer "F.Fab")(effects(font(size .7 .7)(thickness .1))))(fp_rect(start -1.55 -1.55)(end 1.55 1.55)(stroke(width .1)(type default))(layer "F.Fab"))(fp_rect(start -3.2 -1.75)(end 3.2 1.75)(stroke(width .05)(type default))(layer "F.CrtYd"))'
 for n in range(1,11):x=-2.2 if n<=5 else 2.2;y=(n-1)*.5-1 if n<=5 else (10-n)*.5-1;raw+=f'(pad "{n}" smd roundrect(at {x} {y})(size 1.45 .3)(layers "F.Cu" "F.Paste" "F.Mask")(roundrect_rratio .1666667))'
 (lib/'ADS1115_DGS10_TI.kicad_mod').write_text(dump(parse(raw+')'))+'\n',encoding='utf-8')
 raw='(footprint "TPS7A16_DGN8_TI"(version 20241229)(generator "controller_hardware")(layer "F.Cu")(descr "TI TPS7A16DGN0008C4218838/A11/2017 exactlandand125umstencil EP1.6x1.92, not TPS1H000differentEP")(attr smd)(property "Reference" "REF**"(at 0 -2.5)(layer "F.SilkS")(effects(font(size .7 .7)(thickness .1))))(property "Value" "TPS7A16_DGN8_TI"(at 0 2.5)(layer "F.Fab")(effects(font(size .7 .7)(thickness .1))))(fp_rect(start -1.5 -1.5)(end 1.5 1.5)(stroke(width .1)(type default))(layer "F.Fab"))(fp_rect(start -3.15 -1.75)(end 3.15 1.75)(stroke(width .05)(type default))(layer "F.CrtYd"))'
 for n in range(1,9):x=-2.2 if n<=4 else 2.2;y=(n-1)*.65-.975 if n<=4 else (8-n)*.65-.975;raw+=f'(pad "{n}" smd roundrect(at {x} {y})(size 1.4 .45)(layers "F.Cu" "F.Paste" "F.Mask")(roundrect_rratio .111111))'
 raw+='(pad "9" smd rect(at 0 0)(size 1.6 1.92)(layers "F.Cu" "F.Paste" "F.Mask")))';(lib/'TPS7A16_DGN8_TI.kicad_mod').write_text(dump(parse(raw))+'\n',encoding='utf-8')
 (out/'fp-lib-table').write_text(dump(parse('(fp_lib_table(version 7)(lib(name "CNC_MB_AO")(type "KiCad")(uri "${KIPRJMOD}/CNC_MB_AO.pretty")(options "")(descr "Primarysource AO footprints")))'))+'\n',encoding='utf-8')

def build(out=OUT):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);d=description();parts={**d['components'],**d['boundaries']};functions=dict(KINDS);uid=lambda n:str(uuid.uuid5(NS,n));root=uid('root');libs=[];layouts={}
 for p in d['boundaries'].values():functions[p['kind']]={int(k):(k,'passive') for k in p['pins']}
 for kind,table in functions.items():
  if kind in ['R','C','TVS']:layout=[(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')];body='(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))'
  elif kind=='PWR_FLAG':layout=[(1,'pwr',0,0,90,'power_out')];body=''
  else:
   keys=sorted(table);half=(len(keys)+1)//2;layout=[(n,table[n][0],sign*12.7,20.32-i*5.08,0 if sign<0 else 180,table[n][1]) for sign,nums in [(-1,keys[:half]),(1,keys[half:])] for i,n in enumerate(nums)];low=min(p[3] for p in layout)-5.08;body=f'(rectangle(start -10.16 25.4)(end 10.16 {low})(stroke(width .254)(type default))(fill(type background)))'
  layouts[kind]=layout;libs.append(symbol(kind,layout,body,'R' if kind=='R' else 'C' if kind=='C' else 'D' if kind=='TVS' else 'J' if kind.startswith('Boundary') else '#FLG' if kind=='PWR_FLAG' else 'U'))
 items=[];netmap={};ic=pas=bnd=0
 for ref,p in parts.items():
  if ref.startswith('U'):x=63.5+(ic%7)*165.1;y=83.82+(ic//7)*160.02;ic+=1
  elif p['physical']:x=40.64+(pas%17)*68.58;y=1201.42+(pas//17)*30.48;pas+=1
  else:x=63.5+(bnd%7)*165.1;y=1691.64+(bnd//7)*190.5;bnd+=1
  layout=layouts[p['kind']];small=p['kind'] in ['R','C','TVS'];rx=x+3.81 if small else x;ry=y-2.54 if small else y-max(z[3] for z in layout)-10.16
  props=''.join(f'(property {quote(k)} {quote(v)}(at {rx} {ry+dy} 0){effects(.8,"hide") if hide else effects(.8,"(justify left)" if small else "")})' for k,v,dy,hide in [('Reference',ref,0,False),('Value',p['value'],2.54,False),('MPN',p['mpn'],0,True),('Footprint',p['footprint'],0,True)])
  yes='yes' if p['physical'] else 'no';items.append(f'(symbol(lib_id "CNC:{p["kind"]}")(at {x} {y} 0)(unit 1)(in_bom {yes})(on_board {yes})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_analog_output"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
  for n,_,px,py,_,_ in layout:
   sx,sy=round(x+px,4),round(y-py,4);net=p['pins'][str(n)]
   if net is None:items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(n)+"nc")}"))');continue
   dx=-5.08 if px<0 else 5.08 if px>0 else 0;dy=0 if px else 5.08;ex,ey=round(sx+dx,4),round(sy+dy,4)
   items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"wire")}"))');items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.65,"(justify right bottom)" if px<0 else "(justify left bottom)")}(uuid "{uid(ref+str(n)+"label")}"))');netmap.setdefault(net,[]).append([ref,str(n)])
 for i,net in enumerate(['IO_3V3','LOGIC_GND','CORE_24V_PROTECTED']):
  ref=f'#FLG146{i}';x=30.48+i*139.7;y=2080.26;items.append(f'(symbol(lib_id "CNC:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid "{uid(ref)}")(property "Reference" "{ref}"(at {x} {y} 0){effects(1,"hide")})(property "Value" "PARENT SUPPLY"(at {x} {y} 0){effects(1,"hide")})(instances(project "motherboard_analog_output"(path "/{root}"(reference "{ref}")(unit 1)))))(label "{net}"(at {x} {y} 0){effects(.8)}(uuid "{uid(ref+"label")}"))')
 note='ACTUAL TWO ISOLATED AO ISLANDS / AD5683R-3 real SDO and hardware RESET, precision amplifier, normally CLOSED input clamp and normally OPEN output disconnect.\nADS1115 reads actual terminal,12V,5V and reference; no cached command readback. Native source only, target/precision/20msqualification remain.'
 items.append(f'(text {quote(note)}(at 20.32 17.78 0){effects(1.4,"(justify left top)")}(uuid "{uid(note)}"))')
 raw=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{root}")(paper "User" 1270 2200)(title_block(title "Motherboard independent isolated analog outputs")(date "2026-09-30")(rev "r0.1"))(lib_symbols'+''.join(libs)+')'+''.join(items)+')'
 (out/'motherboard_analog_output.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf-8');(out/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in libs)+')'))+'\n',encoding='utf-8');(out/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Analog output source")))'))+'\n',encoding='utf-8');(out/'motherboard_analog_output.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_analog_output.kicad_pro','version':1},'erc':{'rule_severities':{k:'warning' for k in ['single_global_label','four_way_junction','simulation_model_issue','footprint_filter']}}},indent=2)+'\n');footprints(out)
 for name,obj in [('design',d),('pin-map',netmap),('boundary-map',d['boundaries'])]:(out/(name+'.json')).write_text(json.dumps(obj,indent=2)+'\n')
 with (out/'bom.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['Reference','Value','MPN','Footprint','Status']);w.writeheader();w.writerows({'Reference':ref,'Value':p['value'],'MPN':p['mpn'],'Footprint':p['footprint'],'Status':'source_candidate_not_qualified'} for ref,p in d['components'].items())
 print(json.dumps({'components':len(d['components']),'pads':d['fitted_pad_count'],'manufacturing_ready':False}));return d

if __name__=='__main__':build()
