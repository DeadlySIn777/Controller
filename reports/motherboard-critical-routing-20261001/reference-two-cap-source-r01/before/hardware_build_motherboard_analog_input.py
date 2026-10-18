"""Actual isolated differential AI source; target, protection and precision remain qualified separately."""
from __future__ import annotations
import csv,json,uuid,shutil,math
from pathlib import Path
from hardware_build_assembly import parse,dump
from hardware_build_tx_schematic import symbol,effects,quote
from hardware_build_motherboard_analog_output import KINDS as SHARED_KINDS
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_analog_input'
NS=uuid.UUID('d7542d8a-a8e6-4c70-aea6-0caa5127a9d4')
KINDS={k:v.copy() for k,v in SHARED_KINDS.items() if k not in ['DAC','ADC','OPA','LDO']}
KINDS.update({
 'OPA':SHARED_KINDS['OPA'].copy(),
 'ADC':SHARED_KINDS['ADC'].copy(),
 'LIMIT':{1:('SET','passive'),2:('OUT_TAB','power_out'),3:('IN','power_in')},
 'INA':{1:('REFB','input'),2:('-IN','input'),3:('+IN','input'),4:('V-','power_in'),5:('REFA','input'),6:('VOUT','output'),7:('V+','power_in'),8:('NC','no_connect')},
 'OPA4':{1:('OUT_A','output'),2:('-IN_A','input'),3:('+IN_A','input'),4:('V+','power_in'),5:('+IN_B','input'),6:('-IN_B','input'),7:('OUT_B','output'),8:('OUT_C','output'),9:('-IN_C','input'),10:('+IN_C','input'),11:('V-','power_in'),12:('+IN_D','input'),13:('-IN_D','input'),14:('OUT_D','output')},
 'REF':{1:('DNC','no_connect'),2:('VIN','power_in'),3:('TEMP','output'),4:('GND','power_in'),5:('TRIM_NR','passive'),6:('VOUT','output'),7:('NC','no_connect'),8:('DNC','no_connect')},
 'EXP':{1:('A0','input'),2:('A1','input'),3:('A2','input'),4:('P0','bidirectional'),5:('P1','bidirectional'),6:('P2','bidirectional'),7:('P3','bidirectional'),8:('GND','power_in'),9:('P4','bidirectional'),10:('P5','bidirectional'),11:('P6','bidirectional'),12:('P7','bidirectional'),13:('INT_N','open_collector'),14:('SCL','input'),15:('SDA','bidirectional'),16:('VCC','power_in')},
 'ADC38':{1:('SDI','input'),2:('RST_PD_N','input'),3:('DAISY','input'),4:('REFSEL','input'),5:('REFIO','output'),6:('REFGND','power_in'),7:('REFCAP','output'),8:('AGND','power_in'),9:('AVDD','power_in'),10:('AUX_IN','input'),11:('AUX_GND','power_in'),12:('NC','no_connect'),13:('NC','no_connect'),14:('NC','no_connect'),15:('NC','no_connect'),16:('AIN0P','input'),17:('AIN0GND','input'),18:('AIN1P','input'),19:('AIN1GND','input'),20:('AIN2GND','input'),21:('AIN2P','input'),22:('AIN3GND','input'),23:('AIN3P','input'),24:('NC','no_connect'),25:('NC','no_connect'),26:('NC','no_connect'),27:('NC','no_connect'),28:('AGND','power_in'),29:('AGND','power_in'),30:('AVDD','power_in'),31:('AGND','power_in'),32:('AGND','power_in'),33:('DGND','power_in'),34:('DVDD','power_in'),35:('ALARM','output'),36:('SDO','output'),37:('SCLK','input'),38:('CS_N','input')},
 'DCDC24':{2:('-VIN','power_in'),11:('NC','no_connect'),14:('+VOUT','power_out'),16:('-VOUT_SHARED_RETURN','passive'),22:('+VIN','power_in'),23:('+VIN','power_in')},
 'TBU':{1:('LINE','passive'),2:('NU','no_connect'),3:('LINE','passive')},
 'EFUSE':{1:('IN','power_in'),2:('NC','no_connect'),3:('NC','no_connect'),4:('CLMODE','input'),5:('EN','input'),6:('FWD_N','open_collector'),7:('REV_N','open_collector'),8:('SETI','passive'),9:('GND','power_in'),10:('OUT','power_out'),11:('EP_GND','passive')}
})
# These are common passive returns of three separately regulated rails, not three actively driven voltage outputs.
KINDS['DCDC'][7]=('-VOUT_SHARED_RETURN','passive')
KINDS['DCDC24']=KINDS['DCDC'].copy()
KINDS['LDO5']={1:('OUT','power_out'),2:('NC_THERMAL_GND_ALLOWED','passive'),3:('PG','open_collector'),4:('EN','input'),5:('GND','power_in'),6:('IN','power_in'),7:('EP_GND','passive')}
KINDS['WINDOW5']={1:('UV_N','open_collector'),2:('GND','power_in'),3:('SENSE','input'),4:('SET','input'),5:('VDD','power_in'),6:('OV_N','open_collector')}
# This op-amp physically supplies the inline current limiter; OUT is a power source in this circuit.
KINDS['OPA'][1]=('OUT_POWER_DRIVER','power_out')
MPNS={
 'INA':('INA149AIDR','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'),
 'OPA4':('OPA4197IPWR','Package_SO:TSSOP-14_4.4x5mm_P0.65mm'),
 'REF':('REF5025AIDR','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'),
 'EXP':('TCA9534PWR','Package_SO:TSSOP-16_4.4x5mm_P0.65mm'),
 'ADC38':('ADS8684AIDBTR','CNC_MB_AI:ADS8684A_DBT38_TI'),
 'DCDC':('TMR 4-2412WI','CNC_MB_AI:TMR4WI_SIP8_Traco'),
 'DCDC24':('TMR 4-2415WI','CNC_MB_AI:TMR4WI_SIP8_Traco'),
 'TBU':('TBU-CA025-050-WH','CNC_MB_AI:TBU_CA_6.5x4_Bourns'),
 'EFUSE':('MAX17612CATB+T','CNC_MB_AI:MAX17612_T1033_ADI'),
 'OPA':('OPA197IDBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'LIMIT':('LT3092IST#PBF','Package_TO_SOT_SMD:SOT-223-3_TabPin2'),
 'ADC':('ADS1115IDGSR','CNC_MB_AI:ADS1115_DGS10_TI'),
 'WINDOW':('TPS3700DDCR','Package_TO_SOT_SMD:SOT-23-6'),
 'WINDOW5':('TPS3702CX50DDCR','Package_TO_SOT_SMD:SOT-23-6'),
 'LDO5':('TPS7A2650DRVR','CNC_MB_AI:TPS7A26_DRV6_TI'),
 'ISO6':('ISO7761FDWR','CNC_MB_AI:ISO7761_DW16_TI_HV'),
 'ISO2':('ISO7720FDWR','CNC_MB_AI:ISO7720_DW16_TI_HV'),
 'I2CISO':('ISO1540DR','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'),
 'AND':('SN74LVC1G08DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'INV':('SN74LVC1G14DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'ODINV':('SN74LVC1G06DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'BUFFER':('SN74LVC1G125DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'RELAY':('TLP3640A(TPL,E','CNC_MB_AI:TLP3640A_SO4_11-3C1')}


def description():
 parts={};bounds={};u=r=c=14700;channels=[];g='AI_AGND';s5='AI_5V';s15='AI_15V';s24='AI_24V_RAW';raw5='AI_5V_PREREG_12V';pg='AI_POWER_GOOD_FIELD'
 def ic(kind,pins,role,mpn=None,fp=None):
  nonlocal u
  u+=1;ref=f'U{u}';base,foot=MPNS[kind];parts[ref]={'kind':kind,'mpn':mpn or base,'value':mpn or base,'footprint':fp or foot,'physical':True,'pins':{str(k):v for k,v in pins.items()},'role':role};return ref
 def res(a,b,v,role,precision=False,burden=False,minimum_load=False):
  nonlocal r
  r+=1;ref=f'R{r}';codes={1.2:'1R20',47:'47R0',100:'100R',390:'390R',787:'787R',820:'820R',1000:'1K00',4700:'4K70',10000:'10K0',20000:'20K0',30000:'30K0',33200:'33K2',3300:'3K30',3240:'3K24',44200:'44K2',93100:'93K1',120000:'120K',150000:'150K',1000000:'1M00',100000:'100K',111000:'111K',118000:'118K',130000:'130K',274000:'274K',383000:'383K',344000:'344K',562000:'562K',649000:'649K',412000:'412K',549000:'549K',332000:'332K'}
  mpn='PHP01206E1001BST5' if burden else 'PHP02512E7870BST5' if minimum_load else 'TNPW0603'+codes[v]+'BEEA' if precision else 'CRCW0603'+codes[v]+'FKEA'
  fp='CNC_MB_AI:PHP1206_Vishay' if burden else 'CNC_MB_AI:PHP2512_Vishay' if minimum_load else 'Resistor_SMD:R_0603_1608Metric'
  parts[ref]={'kind':'R','mpn':mpn,'value':f'{v}R'+('0.1%' if precision or burden or minimum_load else '1%'),'footprint':fp,'physical':True,'pins':{'1':a,'2':b},'resistance_ohm':v,'tolerance':.001 if precision or burden or minimum_load else .01,'tcr_ppm_K':25 if precision or burden or minimum_load else 100,'power_rating_w':1 if burden else 2.5 if minimum_load else .1,'role':role};return ref
 def cap(a,b,nf,role):
  nonlocal c
  c+=1;ref=f'C{c}';mpn,fp,v={2.2:('GRM1885C1H222JA01D','C_0603_1608Metric',50),10:('GRM1885C2A103JA01D','C_0603_1608Metric',100),100:('GRM188R72A104KA35D','C_0603_1608Metric',100),1000:('GRM188R71H105KA12D','C_0603_1608Metric',50),2200:('CGA5L3X7S2A225K160AB','C_1206_3216Metric',100),10000:('C3216X7R1A106K160AB','C_1206_3216Metric',10),22000:('GCM31CR71A226KE02L','C_1206_3216Metric',10)}[nf]
  parts[ref]={'kind':'C','mpn':mpn,'value':f'{nf}nF{v}V','footprint':'Capacitor_SMD:'+fp,'physical':True,'pins':{'1':a,'2':b},'capacitance_f':nf*1e-9,'voltage_rating_v':v,'role':role};return ref
 def boundary(ref,nets,role):bounds[ref]={'kind':'Boundary'+str(len(nets)),'mpn':'','value':'PARENT: '+role,'footprint':'','physical':False,'pins':{str(i+1):n for i,n in enumerate(nets)},'role':role}
 d5=ic('DCDC',{1:'LOGIC_GND',2:'CORE_24V_PROTECTED',3:None,5:None,6:raw5,7:g,8:None},'actual purchased4W9–36V regulated isolated12V333mA feeds precision5V LDO; field limits unchanged, remoteopen=ON')
 d15=ic('DCDC',{1:'LOGIC_GND',2:'CORE_24V_PROTECTED',3:None,5:None,6:s15,7:g,8:None},'actual purchased4W9–36V regulated isolated15V266mA; remoteopen=ON',mpn='TMR 4-2413WI')
 d24=ic('DCDC24',{1:'LOGIC_GND',2:'CORE_24V_PROTECTED',3:None,5:None,6:s24,7:g,8:None},'actual purchased4W9–36V regulated isolated24V166mA sensorrail; no minimumload, actual<=100mA branch remains')
 for rail in [raw5,s15,s24]:cap('CORE_24V_PROTECTED','LOGIC_GND',2200,'actual module input bypass');cap(rail,g,2200,'actual isolated rail bypass');cap(rail,g,100,'module HF bypass')
 # Retire only R14701: the replacement explicitly requires no minimum load.
 # Keep every subsequent physical reference stable for parent PCB reconciliation.
 r+=1;bleed=None
 # Five independent actual rail observations (24V UV/OV,15V UV/OV,5V UV/OV) share only their open-drain sink.
 windows=[]
 for rail,lo,hi in [(s5,None,None),(s15,332000,412000),(s24,549000,649000)]:
  tag={'AI_5V':'5','AI_15V':'15','AI_24V_RAW':'24'}[rail]
  if rail==s5:
   w=ic('WINDOW5',{1:pg,2:g,3:s5,4:s5,5:s5,6:pg},'factoryUV4.80/OV5.20 SET HIGH, exact .9%trip and .8%max hysteresis; SENSE/return Kelvin at ADC AVDD/AGND, not instantaneous data-valid proof');r+=4
  else:
   rr1='AI_'+tag+'_UV';rr2='AI_'+tag+'_OV';w=ic('WINDOW',{1:pg,2:g,3:rr1,4:rr2,5:s5,6:pg},'coarse dividedrail UV/OV observation, VDD always actual5V not monitored15/24V; all open-drain outputs wireAND')
   res(rail,rr1,lo,'actual window precision upper',True);res(rr1,g,10000,'actual window precision lower',True);res(rail,rr2,hi,'actual window precision upper',True);res(rr2,g,10000,'actual window precision lower',True)
  cap(s5,g,100,'window local actual5V VDD bypass');windows.append(w)
 res(pg,s5,10000,'actual monitored rail good, not always-healthy strap')
 iso=ic('ISO6',{1:'IO_3V3',2:'AI_SCLK_HOST',3:'AI_SDI_HOST',4:'AI_CS_N_HOST',5:'ACC_CLR_N',6:'LOGIC_GND',7:'AI_SDO_ISOLATED',8:'LOGIC_GND',9:g,10:'AI_ADC_SDO',11:None,12:'AI_CLEAR_ISOLATED',13:'AI_ADC_CS_N',14:'AI_ADC_SDI',15:'AI_ADC_SCLK',16:s5},'actual5forward1return ISO7761F; unused input5 heldLOW, unused outputNC; missing host defaults resetLOW')
 cap('IO_3V3','LOGIC_GND',100,'SPI isolation primary bypass');cap(s5,g,100,'SPI isolation secondary bypass')
 reset=ic('AND',{1:'AI_CLEAR_ISOLATED',2:pg,3:g,4:'AI_RESET_N',5:s5},'real actual power+host hardware qualification drives ADCreset and burdenmode gate')
 cap(s5,g,100,'reset gate bypass');res('AI_RESET_N',g,10000,'missing/starting supply resets ADC and opens burdencontacts');res('AI_ADC_CS_N',s5,10000,'inactive powered chip select HIGH')
 ret=ic('BUFFER',{1:'AI_CS_N_HOST',2:'AI_SDO_ISOLATED',3:'LOGIC_GND',4:'AI_SDO_HOST',5:'IO_3V3'},'real chipselect-gated isolated ADC return, not pushpull wired against twoDACreturns')
 cap('IO_3V3','LOGIC_GND',100,'Ioff return buffer bypass')
 i2c=ic('I2CISO',{1:'IO_3V3',2:'AO_I2C_SDA_HOST',3:'AO_I2C_SCL_HOST',4:'LOGIC_GND',5:g,6:'AI_I2C_SCL',7:'AI_I2C_SDA',8:s5},'actual mode/health I2Cbridge, existing sharedhostpullups not duplicated')
 cap('IO_3V3','LOGIC_GND',100,'mode isolation primary bypass');cap(s5,g,100,'mode isolation secondary bypass');res('AI_I2C_SCL',s5,3300,'actual fieldI2C pullup');res('AI_I2C_SDA',s5,3300,'actual fieldI2C pullup')
 exp=ic('EXP',{1:g,2:g,3:g,4:'AI0_CURRENT_MODE',5:'AI1_CURRENT_MODE',6:'AI2_CURRENT_MODE',7:'AI3_CURRENT_MODE',8:g,9:pg,10:'AI_SENSOR_FAULT_N_FIELD',11:'AI_ADC_ALARM',12:None,13:None,14:'AI_I2C_SCL',15:'AI_I2C_SDA',16:s5},'actual address0x20 GPIO expander; powerupallinputs with per-modeLOWbias; firmwaremustwriteoutputLOWbeforeconfiguration')
 cap(s5,g,100,'modeexpander bypass')
 ref=ic('REF',{1:None,2:s5,3:None,4:g,5:'AI_REF_NR',6:'AI_REF_2V5',7:None,8:None},'actual highgrade2.5V lowimpedance reference, allINA REFA/REFB join sameKelvinpoint with no seriesR')
 cap(s5,g,1000,'reference input bypass');cap('AI_REF_NR',g,1000,'noise reduction capacitor');res('AI_REF_2V5','AI_REF_CAP',1.2,'capacitorESR damping only, never in REFA/REFBpath');cap('AI_REF_CAP',g,10000,'nominal10uF capacitor with1.2ohmESR, effective/stability qualification remains')
 amp_pins={4:s15,11:g};amp=ic('OPA4',amp_pins,'actual quad unity-gain ADCdriver avoids silently treating loaded10kdivider as ideal.5')
 cap(s15,g,100,'quadbuffer bypass')
 for i,(outn,minus,plus) in enumerate([(1,2,3),(7,6,5),(8,9,10),(14,13,12)]):
  p=f'AI{i}_P';nn=f'AI{i}_N';prot=f'AI{i}_P_PROTECTED';ao=f'AI{i}_DIFF_SHIFTED';scaled=f'AI{i}_SCALED';buf=f'AI{i}_BUFFERED';adc=f'AI{i}_ADC_IN';bottom=f'AI{i}_BURDEN_BOTTOM';mode=f'AI{i}_CURRENT_MODE';run=f'AI{i}_CURRENT_QUALIFIED';sink=f'AI{i}_LED_K'
  tbu=ic('TBU',{1:p,2:None,3:prot},'actual bidirectional source-only fast50mAprotector; trigger50–100mA guaranteed25C only, fulltemperature/pulse remain sourcegate')
  ina=ic('INA',{1:'AI_REF_2V5',2:nn,3:prot,4:g,5:'AI_REF_2V5',6:ao,7:s15,8:None},'actual differential0–10V plus2.5V offset; common-mode±10V target, not tiedNtoCOM')
  cap(s15,g,100,'differenceamp bypass')
  rs=[]
  for j in range(4):rs.append(res(prot,bottom,1000,'quarterofswitched250ohm burden,1W at70C withspecified mounting; voltagefrontendsenseafterTBU excludesprotectorvoltagefromcurrentreadback',True,burden=True))
  relay=ic('RELAY',{1:s5,2:sink,3:bottom,4:nn},'normallyopen exact60V1Aphotorelay inserts250ohmbank only when configured and hostqualified')
  res(mode,g,10000,'expanderpowerupinputs defaultvoltagemode, actualLOWbias')
  gate=ic('AND',{1:mode,2:'AI_RESET_N',3:g,4:run,5:s5},'currentmode onlywith realhardwarequalifiedhostclear andgoodrails');cap(s5,g,100,'modegate bypass')
  driver=ic('ODINV',{1:None,2:run,3:g,4:f'AI{i}_LED_SINK',5:s5},'actualrelayLED open-drainsink, no burden enables while missinghost');cap(s5,g,100,'LEDsink bypass');res(sink,f'AI{i}_LED_SINK',390,'actualcontactLED limiting')
  res(ao,scaled,10000,'precisionattenuationupper',True);res(scaled,g,10000,'precisionattenuationlower',True)
  parts[amp]['pins'].update({str(outn):buf,str(minus):buf,str(plus):scaled})
  res(buf,adc,47,'ADCdriverisolatescapacitivefilter');cap(adc,g,2.2,'actualADCinputHFfilter')
  channels.append(dict(channel=i,terminal_p=p,terminal_n=nn,protector_ref=tbu,ina_ref=ina,burden_resistors=rs,relay_ref=relay,mode_gate_ref=gate,led_sink_ref=driver,mode_net=mode,qualified_mode_net=run,protected_p=prot,burden_bottom=bottom,shifted=ao,scaled=scaled,buffered=buf,adc_input=adc,buffer_pins=[outn,minus,plus],nominal_burden_ohm=250,differential_v=[0,10],common_mode_target_v=[-10,10],fault_terminal_v=[-30,30],nominal_offset_v=2.5,nominal_scale=.5,mode_defaults_voltage=True,protector_resistance_excluded_from_current_sense=True,wirebreak_threshold_a=.0036,physical_qualified=False))
 adc_pins={1:'AI_ADC_SDI',2:'AI_RESET_N',3:g,4:g,5:'AI_ADC_REFIO',6:g,7:'AI_ADC_REFCAP',8:g,9:s5,10:'AI_REF_2V5',11:g,12:None,13:None,14:None,15:None,16:'AI0_ADC_IN',17:g,18:'AI1_ADC_IN',19:g,20:g,21:'AI2_ADC_IN',22:g,23:'AI3_ADC_IN',24:None,25:None,26:None,27:None,28:g,29:g,30:s5,31:g,32:g,33:g,34:s5,35:'AI_ADC_ALARM',36:'AI_ADC_SDO',37:'AI_ADC_SCLK',38:'AI_ADC_CS_N'}
 adc=ic('ADC38',adc_pins,'actual38pin DBT16bit500kSPSfourmux SAR, configured0–10.24V, AUXreadsactual2.5V reference; noinvalid PWRpackage')
 for rail in ['AI_ADC_REFIO','AI_ADC_REFCAP']:cap(rail,g,22000,'actualreferencechargecap, effective>=10uF mustbequalified');cap(rail,g,1000,'referencecloseHF bypass')
 # TI SBAS680 p70: each AVDD bank1uF; DVDD10uF. These exact already-fitted
 # MPNs replace only three local100nF parts; no shared-rail cap substitutes.
 adc_local_caps={
  9:('885012206052',1000,16,'C_0603_1608Metric'),
  30:('885012206052',1000,16,'C_0603_1608Metric'),
  34:('GRM21BR71A106MA73L',10000,10,'C_0805_2012Metric')}
 for pin,(mpn,nf,voltage,fp) in adc_local_caps.items():
  adc_cap_ref=cap(s5,g,100,'ADC supplypin'+str(pin)+'local bypass')
  parts[adc_cap_ref].update(mpn=mpn,value=f'{nf}nF{voltage}V',capacitance_f=nf*1e-9,
   voltage_rating_v=voltage,footprint='Capacitor_SMD:'+fp,
   role=('ADC '+('DVDD' if pin==34 else 'AVDD')+' pin'+str(pin)+' local'+str(nf//1000)+'uF X7R; direct same-side no-via path'))
 e=ic('EFUSE',{1:s24,2:None,3:None,4:'AI_SENSOR_CLMODE',5:s5,6:'AI_SENSOR_FAULT_N_FIELD',7:'AI_SENSOR_FAULT_N_FIELD',8:'AI_SENSOR_SETI',9:g,10:'AI_SENS_24V',11:g},'actual reverseblocking MAX17612C latched sensorbranch; enabled with real AI5, sensorpower is not actuatorpermission')
 res('AI_SENSOR_CLMODE',g,150000,'actual datasheet latch-off mode, no auto-retry');res('AI_SENSOR_SETI',g,3240,'fullrange precision3.24k yields static max<100mA,87mA usable allocation after bleed',True);res(s5,g,10000,'MAX internally weakly enabled EN defaultsLOW whenAI5 missing');res('AI_SENSOR_FAULT_N_FIELD',s5,10000,'fieldfault realFWD/REV open-drain wireAND');res('AI_SENS_24V',g,100000,'downstream sensorport bleed counted in protected usable allocation');cap('AI_SENS_24V',g,2200,'sensorlocal storage')
 # Actual regulated10V potreference: outer amplifier senses terminal AFTER inline current limiter.
 refamp=ic('OPA',{1:'AI_REF_DRIVE',2:g,3:'AI_REF_2V5',4:'AI_REF_FB',5:s15},'actual regulated10V terminal feedback, composite limiter-loop stability remains physical qualification')
 cap(s15,g,100,'reference driver bypass');res('AI_REF_10V','AI_REF_FB',30000,'precision terminal feedback upper',True);res('AI_REF_FB',g,10000,'precision terminal feedback lower',True)
 reflimit=ic('LIMIT',{1:'AI_REF_SET',2:'AI_REF_LIMIT_OUT',3:'AI_REF_DRIVE'},'actual two-terminal9.31mA nominal limiter, tabOUT must never joinAGND')
 res('AI_REF_SET','AI_REF_10V',93100,'actual floatingSET currentprogram, not referencedGND',True);res('AI_REF_LIMIT_OUT','AI_REF_10V',100,'actual floatingOUT currentprogram, not bypassed',True);res('AI_REF_10V',g,10000,'actual1mA terminal minimumload covers LT3092 max500uA regulation floor')
 mon=ic('ADC',{1:'AI_I2C_SDA',2:None,3:g,4:'AI_MON_REF10',5:'AI_MON_SENS24',6:'AI_SENSOR_SETI',7:'AI_MON_15V',8:s5,9:'AI_I2C_SDA',10:'AI_I2C_SCL'},'real ADS1115 address0x4A measures terminal10V,protected24V,SETIcurrent and15V; slowdiagnostics separatefrom1kSPSfourAI')
 cap(s5,g,100,'actual diagnosticADC bypass')
 for src,dst,up,down in [('AI_REF_10V','AI_MON_REF10',100000,33200),('AI_SENS_24V','AI_MON_SENS24',120000,20000),(s15,'AI_MON_15V',100000,33200)]:res(src,dst,up,'real actualnode observation divider',True);res(dst,g,down,'real actualnode observation divider',True);cap(dst,g,10,'actual diagnosticHFfilter')
 health=ic('ISO2',{1:g,2:None,3:s5,4:pg,5:'AI_SENSOR_FAULT_N_FIELD',6:None,7:g,8:None,9:'LOGIC_GND',10:None,11:None,12:'AI_SENSOR_HEALTH_HOST',13:'AI_POWER_GOOD_HOST',14:'IO_3V3',15:None,16:'LOGIC_GND'},'actual railgood andsensorfault isolation, FdefaultLOW neverhealthywhenfieldpowerabsent')
 cap(s5,g,100,'healthisolation sourcebypass');cap('IO_3V3','LOGIC_GND',100,'healthisolation receivingbypass')
 inv=ic('INV',{1:None,2:'AI_SENSOR_HEALTH_HOST',3:'LOGIC_GND',4:'AI_SENSOR_FAULT_HOST',5:'IO_3V3'},'exactactiveHIGHhostfault, missingfieldpower forcesFAULT');cap('IO_3V3','LOGIC_GND',100,'hostfaultgate bypass')
 boundary('J14701',['IO_3V3','LOGIC_GND','CORE_24V_PROTECTED','ACC_CLR_N'],'actual parent power and independently latchedclear')
 boundary('J14702',['AI_SCLK_HOST','AI_SDI_HOST','AI_SDO_HOST','AI_CS_N_HOST','AO_I2C_SCL_HOST','AO_I2C_SDA_HOST','AI_POWER_GOOD_HOST','AI_SENSOR_FAULT_HOST'],'actual existing ACC2 acquisition/monitoring endpoints')
 boundary('J14703',[x for i in range(4) for x in [f'AI{i}_P',f'AI{i}_N']]+['AI_REF_10V','AI_SENS_24V',g],'fourdifferentialterminals,actual10V<=10mAreference and87mAusablesensorpower; typedterminal/chassisphysicalparent')
 # Append the bounded precision-regulator correction without shifting any retained reference.
 u=14740;c=14755
 ldo=ic('LDO5',{1:s5,2:g,3:pg,4:raw5,5:g,6:raw5,7:g},'fixed5V500mA TPS7A26, actual IN/EN12V; NC2 tiedGND permitted thermal option, EP7GND; PG coarse startup joins strict factorywindow')
 cap(s5,g,2200,'LDO output storage, effective>=1uF overbias/temp/tolerance required');cap(s5,g,100,'LDO output localHF bypass')
 res(s5,g,4700,'actual>=1mA minimumload retains LDO accuracy testconditions even whenADC andallfieldlogic are asleep; alreadyexisting10kENbias separate')
 d={'schema_version':1,'revision':'motherboard-analog-input-r0.2','status':'actual_source_candidate','components':parts,'boundaries':bounds,'channels':channels,'blocks':{'dc5':d5,'dc15':d15,'dc24':d24,'dc24_bleed':bleed,'windows':windows,'spi_isolator':iso,'reset_gate':reset,'return_buffer':ret,'i2c_isolator':i2c,'mode_expander':exp,'reference':ref,'quad_buffer':amp,'adc':adc,'sensor_efuse':e,'health_isolator':health,'fault_inverter':inv},'fitted_component_count':len(parts),'fitted_pad_count':sum(len(q['pins']) for q in parts.values()),'manufacturing_ready':False,'physical_qualification':False,'firmware_implemented':False,'electrical_limits':{'AI_channels':4,'differential_v':[0,10],'common_mode_target_v':[-10,10],'current_a':[.004,.020],'burden_ohm':250,'sensor_rated_a':.100,'input_ohm_min_target':100000,'effective_bits_target':12,'sample_rate_per_channel_target_hz':1000,'isolation':'oneactualAIgroup, threepurchasedregulatorsintentionallysharesecondaryAI_AGND'},'contract_correction':{'prior_invalid_adc_mpn':'ADS8684APWR','exact_adc_mpn':'ADS8684AIDBTR','DBT_38pins':True,'no_compute_family_change':True},'timing':{'spi_hz':4000000,'ai_frame_clocks':32,'ai_wire_seconds':8e-6,'four_channel_roundrobin_target_hz':2500,'two_dac_plus_one_ai_wire_seconds':44e-6,'not_loaded_firmware_latency_proof':True},'power_budget':{'IO_3V3_bypass_nominal_uf':sum(q['capacitance_f'] for q in parts.values() if q['kind']=='C' and q['pins']['1']=='IO_3V3')*1e6,'AI24_minimumload_a':24/820,'AI24_sensor_rated_a':.100,'AI24_module_rated_a':.145,'AI5_module_rated_a':.2,'AI15_module_rated_a':.067,'INA_dualsupply_max_fulltemp_four_a':.0044,'no_dynamic_power_qualification':True},'open_gates':['TBU50–100mA triggering and1usblocking are sourceguaranteed25C only; fulltemperature guaranteedbound, pulse withstand, faultrestart, ESD and cable qualification remain engineering/prototype gates. Do not claim every±30Vfault closed.','Each1k1W burden at100mA bank current25C dissipates.625W;60Vdifferentialfault starts3.6W perpart untilprotector blocks. Highpower mounting copper/stencil and faultthermal require nativePCB/physicalproof.','INA149 nominal15V output2.5–12.5V needs minimumactualrail/outputheadroom fulltemperature, seriesprotectorCMRR/loading, referenceKelvinrouting and systemprecision/calibration qualification.','REC3.5 minimumload29mA includes.70W bleed; 100mAratedsensor plusoverload145–159mA and guaranteedhardshort/supplyfoldback remain explicit source/thermalgates. Publishedpoint is not100mAtrip.','SPI targetfirmware/actualADCconfiguredranges/roundrobinacquisition, modeoutputLOWbeforeDIR and command/readback freshness are nottargetcompiled. Missing/stale readings mustremaininvalid, notzero.','SharedI2C0x20 modeexpander doesnotcollideAOmonitor0x48/49; actualVILoffset/rise/capacitance/addressqualification required.','Actualtypedterminal/chassis/returnplanes/converterheight/creepage/TBUno-underpad-routing and manufacturingDRC notclosed.','Native model receipts are not assembled qualification; noGerbers fabricated from this sourceblock.']}
 d['blocks'].update(reference_amplifier=refamp,reference_limiter=reflimit,diagnostic_adc=mon,precision_ldo=ldo)
 d['electrical_limits'].update(sensor_rated_a=.087,sensor_static_ceiling_a=.1,reference_nominal_v=10,reference_static_ceiling_a=.01)
 d['power_budget']['AI24_minimumload_a']=0.0
 d['power_budget']['AI24_sensor_rated_a']=.087
 d['power_budget']['minimumload_required']=False
 d['power_budget']['AI24_module_rated_a']=.166
 d['power_budget']['AI5_prereg_module_rated_a']=.333
 d['power_budget']['AI5_ldo_rated_a']=.500
 d['power_budget'].pop('AI5_module_rated_a',None)
 d['power_budget']['AI5_accuracy_minimum_load_a']=4.92/(4700*(1+.01+65*.0001))
 d['power_budget']['AI5_ldo_JEDEC_RthetaJA_C_per_W']=73.3
 d['power_budget']['AI5_ldo_55C_ambient_125C_TJ_load_ceiling_screen_a']=(125-55)/(73.3*(12.496-4.92))
 d['power_budget']['AI5_actual_total_load_and_copper_thermal_qualified']=False
 d['power_budget']['AI15_module_rated_a']=.266
 d['power_budget']['sensor_static_limit_min_a']=300/3240*.95/1.0035
 d['power_budget']['sensor_static_limit_max_a']=300/3240*1.05/.9965
 d['power_budget']['sensor_downstream_bleed_max_a']=26.36/(100000*.99)
 d['power_budget']['sensor_usable_a']=.087
 d['power_budget']['sensor_readback_load_max_a']=26.36/(140000*.9965)
 d['power_budget']['AI24_minload_min_a']=0.0
 d['power_budget']['AI24_max_draw_screen_a']=d['power_budget']['sensor_static_limit_max_a']+.00121+.000010
 d['power_budget']['AI5_ADC_500k_internalref_AVDD_max_a']=.0115
 d['power_budget']['AI5_LED_all_four_max_screen_a']=4*5.25/(390*.99)
 d['power_budget']['AI_REF_nominal_limit_a']=10e-6*(1+93100/100)
 d['power_budget']['AI_REF_max_limit_a']=10.2e-6*(1+93100*1.0035/(100*.9965))+.004/(100*.9965)+.000013
 d['power_budget']['AI_REF_min_limit_a']=9.8e-6*(1+93100*.9965/(100*1.0035))-.004/(100*1.0035)-.000025
 d['power_budget']['AI_REF_minimum_load_a']=10/10000+10/40000+10/133200
 d['power_budget']['AI_REF_usable_a']=.0076
 d['diagnostic_i2c_address']='0x4a'
 d['open_gates'][0]='TBU reduces below trigger in1us, not necessarily1mA in1us. Trigger50–100mA is25C only; post-trip leakage1mA max is at50V. Fulltemperature/pulse/reset12–20V/cable fault bounds remain engineering/prototype gates.'
 d['open_gates'][3]='TMR4WI9–36V replaces the known minimum-input mismatch, requires no minimumload; obsolete787ohm bleed removed with no external rating change. Sensor87mA usable after downstream bleed, static ceiling<100mA at resistor/IC corners. MAX17612 overcurrent blank36–44ms is NOT20ms motion inhibit. Converter no-load/load/headroom/hardshort/thermal envelope requires qualification.'
 d['open_gates'].append('Actual10V OPA terminal-feedback/LT3092 inline current limiter includes SET contribution, ±2%source, ±4mVoffset, resistor temperature corners,13uA line and25uA load allowances. <=10mA static source;7.6mA external allocation after realminimum-load/divider. Composite dropout-loop startup/no-load/short/capacitive/faultrecovery must be physically qualified. No±30V reference-terminalfault claim.')
 d['open_gates'].append('DiagnosticADS1115 address0x4A measures actualreference/sensor terminals,SETI/15V. Conversion and actualvoltage/current calibration/freshness firmware remain uncompiled; serialprogrammedvalue is not actualterminal.')
 d['converter_correction']={'reason':'Actual native threeconverterinputs are allCORE24, so old18Vminimum fails after protectedentrydrop. UniformTMR4WI9–36V preserves existing fieldlimits.','primary_pdf_sha256':'37a99e96859378fce90bb56e3339af101f12519802955ee59bed03b1642d0c53','input_range_v':[9,36],'single_output_pins':{'1':'-VIN','2':'+VIN','3':'REMOTE(open=ON)','5':'NC','6':'+VOUT','7':'-VOUT','8':'NC'},'no_minimum_load':True,'retired_reference':'R14701','no_field_rating_increase':True,'isolation_functional_vdc':1600,'input_no_load_a_typ_at24V':.020,'input_full_load_a_typ_at24V':.202,'input_max_not_specified':True,'physical_height_mm':11.2,'assembly_drill_not_vendor_land':True}
 d['ai5_accuracy_correction']={'ldo':'TPS7A2650DRVR','ldo_primary_sha256':'4d0b73c2b191e30fe34fa203e2158d6ae6d92091bac942255427219eb64b4aa9','monitor':'TPS3702CX50DDCR','monitor_primary_sha256':'3f1fb9255cfa9b220938447e903cc6d72eae2abe228393bcb8f1afcb4adb52c8','regulator_static_screen_v':[4.92,5.08],'regulator_screen_test_conditions':'1–500mA;VIN>=5.8V within18V;TJ-40..125C;additiveaccuracy1%+line.1%+load.5%,no transientguarantee','adc_accuracy_supply_v':[4.75,5.25],'UV_falling_min_v':4.8*.991,'UV_release_max_v':4.8*(1.009+.008),'OV_rising_max_v':5.2*1.009,'OV_release_min_v':5.2*(.991-.008),'sense_Kelvin_required':True,'retired_divider_references':['R14702','R14703','R14704','R14705'],'monitor_propagation_not_instantaneous':True,'ldo_output_effective_min_uf':1,'no_external_rating_increase':True}
 d['open_gates'].append('TMR4WI static -40..85C converter screening uses±1%set+.5%line+1%load+65K*.02%/K+40mVhalf-ripple:12V11.504..12.496,15V14.39..15.61,24V23.048..24.952. 15/24 monitors are coarse health, not precision/headroom validity. StrictAI5 fixedLDO+factorywindow admits4.92..5.08 but has only6.8mVUV/3.2mVOV staticaccuracy margins: ADC-local Kelvin sense, returndrop, ripple/startup/propagation/transient freshness must be physicallyqualified. LDO12→5Vactualmaximumload/copperthermal is required, not500mArating. Fulloutputcurrentthrough70C then3.33%/Kderating/case100C; moduleinput202mA and30msstartup aretypical only. No unrelatedtracesunder converter.')
 d['revision']='MB-AI-r03-ADC-local-bypass'
 d['adc_bypass_correction']={'source':'TI SBAS680 p70 §11.1; p9 reference table; p29/31 reference minimums',
  'nominal_avdd_bypass_uf':1,'nominal_dvdd_bypass_uf':10,'source_references':['C14744','C14745','C14746'],
  'capacitor_count_unchanged':True,'all_capacitor_pin_nets_unchanged':True,
  'direct_AVDD_DVDD_REFCAP_no_via_routes_required':True,
  'REFIO_same_side_direct_route_is_engineering_target':True,
  'existing_REFIO_REFCAP_nominal_banks_uf':[22,1],'reference_minimum_effective_uf':10,
  'reference_numeric_ESR_limit_in_primary':False,'reference_nominal_maximum_not_specified':True,
  'reference_effective_bias_age_temp_ESR_qualified':False,'all_seven_local_ADC_caps_generic_router_excluded':True,
  'additional_AI5_nominal_supply_capacitance_uf':11.7,
  'LDO_startup_discharge_transient_new_capacitive_loading_qualified':False}
 return d



def footprints(out):
 lib=out/'CNC_MB_AI.pretty';lib.mkdir(exist_ok=True)
 write_tps7a26_footprint(lib)
 shutil.copyfile(ROOT/'hardware/motherboard_analog_output/CNC_MB_AO.pretty/TMR4WI_SIP8_Traco.kicad_mod',lib/'TMR4WI_SIP8_Traco.kicad_mod')
 for source in ['hardware/motherboard_analog_output/CNC_MB_AO.pretty/ISO7761_DW16_TI_HV.kicad_mod','hardware/motherboard_analog_output/CNC_MB_AO.pretty/ISO7720_DW16_TI_HV.kicad_mod','hardware/motherboard_analog_output/CNC_MB_AO.pretty/TLP3640A_SO4_11-3C1.kicad_mod','hardware/motherboard_analog_output/CNC_MB_AO.pretty/ADS1115_DGS10_TI.kicad_mod','hardware/motherboard_safety_sensor/CNC_MB_Safety.pretty/MAX17612_T1033_ADI.kicad_mod']:
  shutil.copyfile(ROOT/source,lib/Path(source).name)
 def emit(name,body,pads,desc,through=False):
  x,y=body;cx=max(x/2,max(abs(z[1])+z[3]/2 for z in pads))+.6;cy=max(y/2,max(abs(z[2])+z[4]/2 for z in pads))+.6;raw=f'(footprint "{name}"(version 20241229)(generator "controller_hardware")(layer "F.Cu")(descr {quote(desc)})(attr {"through_hole" if through else "smd"})(property "Reference" "REF**"(at 0 {-y/2-1} 0)(layer "F.SilkS"){effects(.7)})(property "Value" "{name}"(at 0 {y/2+1} 0)(layer "F.Fab"){effects(.7)})(fp_rect(start {-x/2} {-y/2})(end {x/2} {y/2})(stroke(width .1)(type default))(layer "F.Fab"))(fp_rect(start {-cx} {-cy})(end {cx} {cy})(stroke(width .05)(type default))(layer "F.CrtYd"))'
  for n,px,py,w,h in pads:
   if through:raw+=f'(pad "{n}" thru_hole circle(at {px} {py})(size {w} {h})(drill 1)(layers "*.Cu" "*.Mask"))'
   elif name.startswith('TBU') and n==1:raw+=f'(pad "1" smd roundrect(at {px} {py})(size {w} {h})(layers "F.Cu" "F.Paste" "F.Mask")(roundrect_rratio 0)(chamfer_ratio { .25/min(w,h)})(chamfer bottom_left)(solder_paste_margin -.0125))'
   else:raw+=f'(pad "{n}" smd rect(at {px} {py})(size {w} {h})(layers "F.Cu" "F.Paste" "F.Mask")'+('(solder_paste_margin -.0125)' if name.startswith('TBU') else '')+')'
  (lib/(name+'.kicad_mod')).write_text(dump(parse(raw+')'))+'\n',encoding='utf-8')
 emit('ADS8684A_DBT38_TI',(4.4,9.7),[(n,-2.9 if n<=19 else 2.9,(n-1)*.5-4.5 if n<=19 else (38-n)*.5-4.5,1.5,.3) for n in range(1,39)],'TI DBT0038A4220221/A05/2020: DBT38 lead1.5x.3 centres+-2.9 pitch.5. Body4.4x9.7, assembly courtyard includes solder land.')
 emit('PHP1206_Vishay',(3.2004,1.6002),[(1,-1.23825,0,1.9177,1.8034),(2,1.23825,0,1.9177,1.8034)],'Vishay60076 Rev19May2026 recommended PHP1206 mounting: gap.022in, pad.0755x.071in, span.173in; high-power copper remains PCB proof.')
 emit('PHP2512_Vishay',(6.5786,3.1496),[(1,-2.54,0,2.3114,3.2004),(2,2.54,0,2.3114,3.2004)],'Vishay60076 recommended PHP2512 mounting: gap.109in, pad.091x.126in, span.291in; thermal copper required.')
 emit('TBU_CA_6.5x4_Bourns',(6.5,4),[(1,-2.025,0,1.85,3.4),(2,0,0,.8,3.4),(3,2.025,0,1.85,3.4)],'BournsTBU-CA p4: TOPview pin1LEFT/backsidechamfer mirrored bottom-left. All3pads soldered; pad2NU remains electricallyNC. Copper6.5x4 keepout under allpads, maskterminalsize and0.025mm-smaller paste; thermal copper and100-120umstencil require PCB proof.')
 emit('REC3.5_R8_A_Single',(32,20.3),[(2,11.43,-7.62,1.8,1.8),(11,-11.43,-7.62,1.8,1.8),(14,-11.43,7.62,1.8,1.8),(16,-6.35,7.62,1.8,1.8),(22,8.89,7.62,1.8,1.8),(23,11.43,7.62,1.8,1.8)],'RECOMREC3.5-RW_R Rev0/2015 /A SINGLE bottomview mirrored for Ftop: pin2-VIN11NC14+OUT16-OUT22/23+VIN; nooptionalCTRLpin1. Body32x20.3x10.2, drill1.0 nominal perprimary1.0+0.15/-0.',True)
 (out/'fp-lib-table').write_text(dump(parse('(fp_lib_table(version 7)(lib(name "CNC_MB_AI")(type "KiCad")(uri "${KIPRJMOD}/CNC_MB_AI.pretty")(options "")(descr "Primarysource AI footprints")))'))+'\n',encoding='utf-8')

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
  yes='yes' if p['physical'] else 'no';items.append(f'(symbol(lib_id "CNC:{p["kind"]}")(at {x} {y} 0)(unit 1)(in_bom {yes})(on_board {yes})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_analog_input"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
  for n,_,px,py,_,_ in layout:
   sx,sy=round(x+px,4),round(y-py,4);net=p['pins'][str(n)]
   if net is None:items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(n)+"nc")}"))');continue
   dx=-5.08 if px<0 else 5.08 if px>0 else 0;dy=0 if px else 5.08;ex,ey=round(sx+dx,4),round(sy+dy,4)
   items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"wire")}"))');items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.65,"(justify right bottom)" if px<0 else "(justify left bottom)")}(uuid "{uid(ref+str(n)+"label")}"))');netmap.setdefault(net,[]).append([ref,str(n)])
 for i,net in enumerate(['IO_3V3','LOGIC_GND','CORE_24V_PROTECTED','AI_AGND']):
  ref=f'#FLG147{i}';x=30.48+i*139.7;y=2080.26;items.append(f'(symbol(lib_id "CNC:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid "{uid(ref)}")(property "Reference" "{ref}"(at {x} {y} 0){effects(1,"hide")})(property "Value" "PARENT SUPPLY"(at {x} {y} 0){effects(1,"hide")})(instances(project "motherboard_analog_input"(path "/{root}"(reference "{ref}")(unit 1)))))(label "{net}"(at {x} {y} 0){effects(.8)}(uuid "{uid(ref+"label")}"))')
 note='ACTUAL FOUR DIFFERENTIAL AI / INA149 protected difference amplifiers, switched250ohm burdens, real ADS8684A SPI acquisition, isolated supplies and sensor branch.\nNative source only. Target firmware, full-temperature protection, precision/calibration, mechanical and loaded acquisition remain qualification.'
 items.append(f'(text {quote(note)}(at 20.32 17.78 0){effects(1.4,"(justify left top)")}(uuid "{uid(note)}"))')
 raw=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{root}")(paper "User" 1270 2200)(title_block(title "Motherboard differential isolated analog inputs")(date "2026-09-30")(rev "r0.2"))(lib_symbols'+''.join(libs)+')'+''.join(items)+')'
 (out/'motherboard_analog_input.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf-8');(out/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in libs)+')'))+'\n',encoding='utf-8');(out/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Analog output source")))'))+'\n',encoding='utf-8');(out/'motherboard_analog_input.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_analog_input.kicad_pro','version':1},'erc':{'rule_severities':{k:'warning' for k in ['single_global_label','four_way_junction','simulation_model_issue','footprint_filter']}}},indent=2)+'\n');footprints(out)
 for name,obj in [('design',d),('pin-map',netmap),('boundary-map',d['boundaries'])]:(out/(name+'.json')).write_text(json.dumps(obj,indent=2)+'\n')
 with (out/'bom.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['Reference','Value','MPN','Footprint','Status']);w.writeheader();w.writerows({'Reference':ref,'Value':p['value'],'MPN':p['mpn'],'Footprint':p['footprint'],'Status':'source_candidate_not_qualified'} for ref,p in d['components'].items())
 print(json.dumps({'components':len(d['components']),'pads':d['fitted_pad_count'],'manufacturing_ready':False}));return d

def write_tps7a26_footprint(lib):
 name='TPS7A26_DRV6_TI'
 raw=f'(footprint "{name}"(version 20241229)(generator "controller_hardware")(layer "F.Cu")(descr "TI DRV0006A4222173/C11/2025; leads0.45x0.30centres+-0.975,pitch0.65,EP7=1.0x1.6. Stencil two1x0.7windowsatY+-0.45 gives87.5%coverage (vendor88%rounded),R0.05leadcorners. Optional thermalvias require filled/capped PCB proof.")(attr smd)(property "Reference" "REF**"(at 0 -1.8 0)(layer "F.SilkS"){effects(.7)})(property "Value" "{name}"(at 0 1.8 0)(layer "F.Fab"){effects(.7)})(fp_rect(start -1 -1)(end 1 1)(stroke(width .1)(type default))(layer "F.Fab"))(fp_rect(start -1.45 -1.25)(end 1.45 1.25)(stroke(width .05)(type default))(layer "F.CrtYd"))'
 for pin,x,y in [(1,-.975,-.65),(2,-.975,0),(3,-.975,.65),(4,.975,.65),(5,.975,0),(6,.975,-.65)]:
  raw+=f'(pad "{pin}" smd roundrect(at {x} {y})(size .45 .30)(layers "F.Cu" "F.Paste" "F.Mask")(roundrect_rratio .166666667))'
 raw+='(pad "7" smd roundrect(at 0 0)(size 1 1.6)(layers "F.Cu" "F.Mask")(roundrect_rratio .05))'
 for y in [-.45,.45]:raw+=f'(pad "" smd roundrect(at 0 {y})(size 1 .7)(layers "F.Paste")(roundrect_rratio .071428571))'
 (lib/(name+'.kicad_mod')).write_text(dump(parse(raw+')'))+'\n',encoding='utf-8')

if __name__=='__main__':build()

