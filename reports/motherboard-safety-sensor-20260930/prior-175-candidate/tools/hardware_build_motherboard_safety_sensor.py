"""Actual FIELD_B sensor supplies and dedicated XS1 hardware frontends.

One motherboard, references19001–19499. Does not edit retained sources/PCB.
"""
from __future__ import annotations
import copy,csv,hashlib,json,shutil,uuid,xml.etree.ElementTree as ET
from pathlib import Path
from hardware_build_assembly import parse,dump
from hardware_build_tx_schematic import effects,quote,symbol
from hardware_build_motherboard_power_entry import PINS as ENTRY_PINS
from hardware_build_motherboard_motor_power import PINS as HEALTH_PINS
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_safety_sensor';REPORT=ROOT/'reports/motherboard-safety-sensor-20260930'
NS=uuid.UUID('d9c0877a-19d9-4b52-af3c-0564a3a2eee9')
KINDS={k:ENTRY_PINS[k] for k in ['R','C','L','AUX24','TLP3640A']}
KINDS.update({'LTC2962':HEALTH_PINS['LTC2962'],'ISO7720F':HEALTH_PINS['ISO7720F'],
 'ISO1212':{1:('GND1','power_in'),2:('VCC1','power_in'),3:('EN','input'),4:('OUT1','output'),5:('OUT2','output'),6:('NC','no_connect'),7:('NC','no_connect'),8:('GND1','power_in'),9:('GND2','power_in'),10:('IN2','input'),11:('SENSE2','input'),12:('SUB2','passive'),13:('SUB1','passive'),14:('GND2','power_in'),15:('IN1','input'),16:('SENSE1','input')},
 'LIMIT':{1:('IN','input'),2:('DIAG_EN','input'),3:('FAULT_N','open_collector'),4:('CL','passive'),5:('DELAY','passive'),6:('GND','power_in'),7:('OUT','power_out'),8:('VS','power_in'),9:('EP_GND','power_in')},
 'ISO7760F':{1:('VCC1','power_in'),2:('INA','input'),3:('INB','input'),4:('INC','input'),5:('IND','input'),6:('INE','input'),7:('INF','input'),8:('GND1','power_in'),9:('GND2','power_in'),10:('OUTF','output'),11:('OUTE','output'),12:('OUTD','output'),13:('OUTC','output'),14:('OUTB','output'),15:('OUTA','output'),16:('VCC2','power_in')},
 'ISO1540':{1:('VCC1','power_in'),2:('SDA1','bidirectional'),3:('SCL1','bidirectional'),4:('GND1','power_in'),5:('GND2','power_in'),6:('SCL2','bidirectional'),7:('SDA2','bidirectional'),8:('VCC2','power_in')},
 'ADC':{1:('ADDR','input'),2:('ALERT_RDY','open_collector'),3:('GND','power_in'),4:('AIN0','input'),5:('AIN1','input'),6:('AIN2','input'),7:('AIN3','input'),8:('VDD','power_in'),9:('SDA','bidirectional'),10:('SCL','input')},
 'MUX':{1:('SEL1','input'),2:('S1','passive'),3:('D1','passive'),4:('SEL2','input'),5:('S2','passive'),6:('D2','passive'),7:('GND','power_in'),8:('D3','passive'),9:('S3','passive'),10:('SEL3','input'),11:('D4','passive'),12:('S4','passive'),13:('SEL4','input'),14:('VDD','power_in')},
 'ODINV':{1:('NC','no_connect'),2:('A','input'),3:('GND','power_in'),4:('Y','open_collector'),5:('VCC','power_in')},
 'AND_TTL':{1:('A','input'),2:('B','input'),3:('GND','power_in'),4:('Y','output'),5:('VCC','power_in')},
 'BUF2':{1:('1A','input'),2:('GND','power_in'),3:('2A','input'),4:('2Y','output'),5:('VCC','power_in'),6:('1Y','output')},
 'TEST':{1:('TEST','passive')},'TVS':{1:('IO','passive'),2:('IO','passive')},'PWR_FLAG':{1:('pwr','power_out')}})
_field_lib=ET.parse(ROOT/'hardware/field_power/netlist.xml').find(".//libparts/libpart[@part='LMR36506R5RPER']")
KINDS['FIELD_LMR36506R5RPER']={int(q.get('num')):(q.get('name'),q.get('type')) for q in _field_lib.findall('pins/pin')}
MPNS={
 'ISO7720F':('ISO7720FDWR','CNC_MB_Safety:ISO7720_DW16_TI_HV'),
 'ISO1212':('ISO1212DBQR','CNC_MB_Safety:ISO1212_DBQ16_TI'),
 'AUX24':('TPS26624DRCR','CNC_MB_Safety:TPS2662_DRC10_TI'),
 'LIMIT':('TPS1H000AQDGNRQ1','CNC_MB_Safety:TPS1H000_DGN8_TI'),
 'LTC2962':('LTC2962HUD#PBF','CNC_MB_Safety:LTC2962_UD16'),
 'ISO7760F':('ISO7760FDWR','CNC_MB_Safety:ISO7760_DW16_TI_HV'),
 'ISO1540':('ISO1540DR','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'),
 'ADC':('ADS1115IDGSR','CNC_MB_Safety:ADS1115_DGS10_TI'),
 'MUX':('TMUX1511PWR','Package_SO:TSSOP-14_4.4x5mm_P0.65mm'),
 'ODINV':('SN74LVC1G06DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'AND_TTL':('SN74AHCT1G08DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'BUF2':('SN74LVC2G34DCKR','Package_TO_SOT_SMD:SOT-363_SC-70-6'),
 'TLP3640A':('TLP3640A(TPL,E','CNC_MB_Safety:TLP3640A_SO4_11-3C1')}

def description():
 parts={};u=r=c=d=19000;inputs=[];groups=[];g='FIELD_B_0V';v='DOB_FIELD_3V3'
 def add(k,pins,role):
  nonlocal u
  u+=1;ref=f'U{u}';m,f=MPNS[k];parts[ref]={'kind':k,'mpn':m,'value':m,'footprint':f,'physical':True,'pins':{str(p):n for p,n in pins.items()},'role':role};return ref
 def res(a,b,ohm,role,mpn=None,tol=.01,tcr=100,fp='Resistor_SMD:R_0603_1608Metric'):
  nonlocal r
  r+=1;ref=f'R{r}';code={243:'243R',562:'562R',1000:'1K00',215:'215R',10000:'10K0',100000:'100K',130000:'130K'}.get(ohm)
  if mpn is None and code is None:raise ValueError('Exact resistor not selected '+str(ohm))
  parts[ref]={'kind':'R','mpn':mpn or 'CRCW0603'+code+'FKEA','value':f'{ohm}R{tol*100:g}%','footprint':fp,'physical':True,'pins':{'1':a,'2':b},'resistance_ohm':ohm,'tolerance':tol,'tcr_ppm_K':tcr,'role':role};return ref
 def cap(a,b,nf,role):
  nonlocal c
  c+=1;ref=f'C{c}';mpn,fp,vr={10:('C2012C0G2A103J125AA','Capacitor_SMD:C_0805_2012Metric',100),100:('GRM188R72A104KA35D','Capacitor_SMD:C_0603_1608Metric',100),1000:('GRM188R71H105KA12D','Capacitor_SMD:C_0603_1608Metric',50)}[nf]
  parts[ref]={'kind':'C','mpn':mpn,'value':f'{nf}nF{vr}V','footprint':fp,'physical':True,'pins':{'1':a,'2':b},'capacitance_f':nf*1e-9,'voltage_rating_v':vr,'role':role};return ref
 def tvs(a,b,role):
  nonlocal d
  d+=1;ref=f'D{d}';parts[ref]={'kind':'TVS','mpn':'SMF36CA','value':'SMF36CA','footprint':'Diode_SMD:D_SOD-123F','physical':True,'pins':{'1':a,'2':b},'role':role};return ref
 names=[('EXT_PERMIT','EXT_PERMIT_RAW'),('PROCESS_PERMIT','PROCESS_PERMIT_RAW'),('SAFETY_STATUS','SAFETY_STATUS_FPGA'),('RESET_ARM','RESET_ARM_FPGA'),('CONTACTOR_FB','CONTACTOR_FB_FPGA'),('STO_FB','STO_FB_FPGA')]
 for pair in range(3):
  pins={1:'LOGIC_GND',2:'IO_3V3',3:'IO_3V3',6:None,7:None,8:'LOGIC_GND',9:g,14:g}
  for j,(name,out) in enumerate(names[pair*2:pair*2+2]):
   pins.update({4+j:out,16-j*5:name+'_SENSE',15-j*5:name+'_ISO_IN',13-j:name+'_SUB_ISLAND'})
   rt=res(name+'_IN',name+'_SENSE',1000,'reviewed sinking threshold/pulse resistor','SMM02040C1001FB300',.01,50,'Resistor_SMD:R_MiniMELF_MMA-0204');rs=res(name+'_SENSE',name+'_ISO_IN',562,'ISO1212 current-setting resistor');cf=cap(name+'_SENSE',g,10,'reviewed safety-input filter; simple R*C is not full delay proof');tvs(name+'_IN',g,'bidirectional 36V field input protection; surge coordination not qualified');res(out,'LOGIC_GND',100000,'powered open-input/zero-VCC bias; partial power not guaranteed')
   inputs.append({'name':name,'output':out,'input':name+'_IN','threshold_ref':rt,'sense_ref':rs,'filter_ref':cf,'substrate_net':name+'_SUB_ISLAND'})
  add('ISO1212',pins,'two dedicated XS1 inputs; no general DI/probe/motor-alarm reuse');cap('IO_3V3','LOGIC_GND',100,'dedicated safety receiver bypass')
 for i in range(3):
  out=f'SENS24_G{i}';rt=f'DI_G{i}_RTN';fl=f'DI_G{i}_FLT_N';lim=f'DI_G{i}_ILIM';uv=f'DI_G{i}_UV';dv=f'DI_G{i}_DVDT'
  ref=add('AUX24',{1:'FIELD_B_24V_PROTECTED',2:uv,3:rt,4:None,5:rt,6:g,7:lim,8:dv,9:fl,10:out,11:rt},'independent FIELD_B sensor group limiter; on at field power, latched overload needs power cycle')
  il=res(lim,rt,26700,'published 26.7k overload testpoint, no interpolation','TNPW060326K7BEEA',.001,25);res('FIELD_B_24V_PROTECTED',uv,130000,'UVLO divider');res(uv,rt,10000,'UVLO divider');res(fl,v,10000,'field fault pullup, not logic-ground alias');res(out,g,100000,'post-limiter discharge/voltage bleed');cap(dv,rt,10,'branch slew control');cap('FIELD_B_24V_PROTECTED',g,100,'limiter input bypass');cap(out,g,1000,'post-limiter bulk')
  groups.append({'group':i,'limiter_ref':ref,'ilim_ref':il,'output':out,'fault_n':fl,'rated_continuous_a':.2,'published_overload_testpoint_a':[.237,.257],'short_max_at_this_resistor_guaranteed':False})
 safe=add('LIMIT',{1:v,2:v,3:'SAFE_SWITCH_FAULT_N',4:'SAFE_ILIM',5:'SAFE_DELAY',6:g,7:'SAFE_24V',8:'FIELD_B_24V_PROTECTED',9:g},'wetting supply limited at >=50mA accuracy range, below150mA cap; open-load flag is diagnostic, not permission')
 safe_il=res('SAFE_ILIM',g,9530,'at least50mA programmed with all fitted resistor corners','TNPW06039K53BEEA',.001,25);cap('SAFE_DELAY',g,10,'latched current-limit delay; manual field power recovery');cap('FIELD_B_24V_PROTECTED',g,100,'safe supply input bypass');cap('SAFE_24V',g,1000,'wetting rail post-limiter');res('SAFE_24V',g,100000,'wetting rail bleed');res('SAFE_SWITCH_FAULT_N',v,10000,'raw switch diagnostic, may report legitimate open dry contacts')
 # Monitor the actual SAFE_24V AND local field-logic rail; actual LTC quad inputs.
 ref='SAFE_MON_REF';p={1:v,2:v,3:g,4:v,5:ref,6:ref,7:g,8:ref,9:g,10:v,11:g,12:'SAFE_DOMAIN_HEALTH',17:g}
 windows=[]
 for rail,up,dn,upcode,dncode,pins in [('SAFE_24V',287000,615000,'TNPW0603287KBEEA','TNPW0603615KBEEA',(16,15)),(v,48700,60400,'TNPW060348K7BEEA','TNPW060360K4BEEA',(14,13))]:
  for j,(kind,top,code) in enumerate([('UV',up,upcode),('OV',dn,dncode)]):
   net=rail+'_SAFE_'+kind;p[pins[j]]=net;tr=res(rail,net,top,'actual post-limiter/local-field-rail '+kind,code,.001,25);br=res(net,g,10000,'Kelvin monitor bottom','TNPW060310K0BEEA',.001,25);windows.append({'rail':rail,'kind':kind,'top_ref':tr,'bottom_ref':br,'top_ohm':top,'bottom_ohm':10000})
 mon=add('LTC2962',p,'200ms qualified release; actual post-limiter SAFE24 + field3.3 window; RST guaranteed low down to VCC1V only');res('SAFE_DOMAIN_HEALTH',v,10000,'monitor output pullup');res('SAFE_DOMAIN_HEALTH',g,100000,'power-loss bias');cap(v,g,100,'monitor bypass')
 # Physical series contacts qualify both non-reconfigurable permission inputs.
 contacts=[]
 for name,out in [('EXT_PERMIT','EXT_PERMIT_3V3'),('PROCESS_PERMIT','PROCESS_PERMIT_EXT_3V3')]:
  led=name+'_HEALTH_LED_A';sink=name+'_HEALTH_LED_K';add('ODINV',{1:None,2:'SAFE_DOMAIN_HEALTH',3:g,4:sink,5:v},'independent HIGH-health LED sink; fault LOW dark');cap(v,g,100,'individual health LED driver bypass');res(v,led,215,'single photorelay LED string, >=3mA conditional trigger screen');q=add('TLP3640A',{1:led,2:sink,3:name+'_RAW',4:out},'dedicated raw-health NO contact in fixed permission path');res(out,'LOGIC_GND',10000,'independent final permission default LOW; existing MC10k also retained');contacts.append(q)
 add('BUF2',{1:'EXT_PERMIT_3V3',2:'LOGIC_GND',3:'PROCESS_PERMIT_EXT_3V3',4:'PROCESS_PERMIT_FPGA',5:'IO_3V3',6:'EXT_PERMIT_FPGA'},'separate TTL status copies; fixed hardware permit itself never serialized');cap('IO_3V3','LOGIC_GND',100,'status-copy buffer bypass')
 # Actual external contact driven from the retained TX_PERMIT AND request gate.
 add('AND_TTL',{1:'PERMIT_OUT_DRIVE',2:'MC_RAILS_OK_5V',3:'LOGIC_GND',4:'XS1_PERMIT_LED_ON',5:'CORE_5V'},'5V TTL restoration + independent actual core-health AND; self-test request LOW keeps contact open');add('ODINV',{1:None,2:'XS1_PERMIT_LED_ON',3:'LOGIC_GND',4:'XS1_PERMIT_LED_K',5:'CORE_5V'},'positive request sinks LED, inputLOW/zero request means dark');res('XS1_PERMIT_LED_ON','LOGIC_GND',10000,'LED driver input default LOW');res('PERMIT_OUT_DRIVE','LOGIC_GND',10000,'fixed permission command receiving default LOW');res('CORE_5V','XS1_PERMIT_LED_A',243,'NO contact LED resistor');po=add('TLP3640A',{1:'XS1_PERMIT_LED_A',2:'XS1_PERMIT_LED_K',3:'PERMIT_OUT_1',4:'PERMIT_OUT_2'},'XS1.10/.11 floating formA contact, userloop<=50mA');tvs('PERMIT_OUT_1','PERMIT_OUT_2','36V bidirectional standoff; clamp below60V only at datasheet pulse point');cap('CORE_5V','LOGIC_GND',100,'TTL permission-gate bypass');cap('CORE_5V','LOGIC_GND',100,'permission LED driver bypass')
 # ARM lamp is a status output, has no motion or process authority.
 add('ISO7720F',{1:'LOGIC_GND',2:None,3:'IO_3V3',4:'ARM_LAMP_FPGA',5:'LOGIC_GND',6:None,7:'LOGIC_GND',8:None,9:g,10:None,11:None,12:None,13:'ARM_LAMP_FIELD_CMD',14:v,15:None,16:g},'default-LOW isolated lamp command; partial-voltage behavior remains bounded separately');cap('IO_3V3','LOGIC_GND',100,'lamp isolation logic bypass');cap(v,g,100,'lamp isolation field bypass');res('ARM_LAMP_FIELD_CMD',g,10000,'lamp command absent-module default LOW')
 lamp=add('LIMIT',{1:'ARM_LAMP_FIELD_CMD',2:v,3:'ARM_LAMP_FAULT_N',4:'ARM_LAMP_ILIM',5:'ARM_LAMP_DELAY',6:g,7:'ARM_LAMP',8:'FIELD_B_24V_PROTECTED',9:g},'50mA rated lamp, >=100mA programmed overload point; OFF at no request');res('ARM_LAMP_ILIM',g,4750,'>=50mA accuracy row at100mA target','TNPW06034K75BEEA',.001,25);cap('ARM_LAMP_DELAY',g,10,'lamp latch-off delay');cap('FIELD_B_24V_PROTECTED',g,100,'lamp switch supply bypass');res('ARM_LAMP_FAULT_N',v,10000,'lamp raw diagnostic');res('ARM_LAMP',g,100000,'lamp output bleed')
 # Only valid powered isolated health drives the fail-default acquisition inputs.
 transfer=['DI_G0_FLT_N','DI_G1_FLT_N','DI_G2_FLT_N','SAFE_DOMAIN_HEALTH','ARM_LAMP_FAULT_N','SAFE_SWITCH_FAULT_N']
 rx=['DI_G0_GOOD_RX','DI_G1_GOOD_RX','DI_G2_GOOD_RX','DI_SAFE_GOOD_RX','DI_LAMP_GOOD_RX','DI_SAFE_SWITCH_GOOD_RX']
 p={1:v,8:g,9:'LOGIC_GND',16:'IO_3V3',**{i+2:n for i,n in enumerate(transfer)},**{15-i:n for i,n in enumerate(rx)}};add('ISO7760F',p,'actual field health/fault transfer, F defaultLOW; no constant healthy metadata');cap(v,g,100,'six-channel field isolation bypass');cap('IO_3V3','LOGIC_GND',100,'six-channel receiving isolation bypass')
 for inn,out in zip(rx[:5],['DI_SENSOR_G0_FAULT','DI_SENSOR_G1_FAULT','DI_SENSOR_G2_FAULT','DI_SAFETY_SUPPLY_FAULT','DI_SAFETY_SECONDARY_FAULT']):
  add('ODINV',{1:None,2:inn,3:'LOGIC_GND',4:out,5:'IO_3V3'},'validHIGH good sinks active-HIGH fault input; receiving MCU10k pullup retained');cap('IO_3V3','LOGIC_GND',100,'fault output bypass');res(inn,'LOGIC_GND',10000,'missing isolated transfer reads bad; no intermediate-power claim')
 parts['TP19001']={'kind':'TEST','mpn':'','value':'SAFE SWITCH DIAGNOSTIC TEST','footprint':'TestPoint:TestPoint_Pad_D1.0mm','physical':True,'purchased':False,'pins':{'1':'DI_SAFE_SWITCH_GOOD_RX'},'role':'bare copper diagnostic only; legitimate open dry contacts can report bad'}
 # Four post-limiter voltages, switch isolation before the unpowered ADC input.
 add('ISO1540',{1:'IO_3V3',2:'DIC_SENSOR_SDA',3:'DIC_SENSOR_SCL',4:'LOGIC_GND',5:g,6:'DI_SENSOR_SCL_FIELD',7:'DI_SENSOR_SDA_FIELD',8:v},'GPIO software-I2C isolation; no unverified MCU alternate-function claim')
 adc=add('ADC',{1:g,2:None,3:g,4:'DI_SENSOR_AIN0',5:'DI_SENSOR_AIN1',6:'DI_SENSOR_AIN2',7:'DI_SENSOR_AIN3',8:v,9:'DI_SENSOR_SDA_FIELD',10:'DI_SENSOR_SCL_FIELD'},'ADS1115 four actual single-ended post-limiter voltages; fixed address0x48')
 p={1:'SAFE_DOMAIN_HEALTH',4:'SAFE_DOMAIN_HEALTH',10:'SAFE_DOMAIN_HEALTH',13:'SAFE_DOMAIN_HEALTH',7:g,14:v}
 for i,(s,dd) in enumerate([(2,3),(5,6),(9,8),(12,11)]):p[s]=f'DI_SENSOR_DIV{i}';p[dd]=f'DI_SENSOR_AIN{i}'
 add('MUX',p,'powered-off protected analog interposition, inputs<=3.6V atVDD0, OFF below qualified domain-health')
 for i,rail in enumerate([f'SENS24_G{j}' for j in range(3)]+['SAFE_24V']):
  res(rail,f'DI_SENSOR_DIV{i}',130000,'voltage divider high leg','TNPW0603130KBEEA',.001,25);res(f'DI_SENSOR_DIV{i}',g,10000,'voltage divider bottom','TNPW060310K0BEEA',.001,25);res(f'DI_SENSOR_AIN{i}',g,100000,'powered-off mux leakage bleed; includeparallel loading in calibrated transfer');cap(f'DI_SENSOR_AIN{i}',g,100,'ADC anti-alias/bleed filter; sample settling qualification')
 for n,power,gg in [('DIC_SENSOR_SDA','IO_3V3','LOGIC_GND'),('DIC_SENSOR_SCL','IO_3V3','LOGIC_GND'),('DI_SENSOR_SDA_FIELD',v,g),('DI_SENSOR_SCL_FIELD',v,g)]:res(n,power,4420,'I2C pullup .5mA minimum isolation testpoint','CRCW06034K42FKEA')
 cap('IO_3V3','LOGIC_GND',100,'I2C isolation primary bypass');cap(v,g,100,'I2C isolation secondary bypass');cap(v,g,100,'ADC bypass');cap(v,g,100,'analog switch bypass')
 # Reuse the exact reviewed FIELD5 converter as a field-B-local preregulator.
 entry=json.loads((ROOT/'hardware/motherboard_power_entry/design.json').read_text())['components'];clones={};nt={'FIELD_A_24V_PROTECTED':'FIELD_B_24V_PROTECTED','FIELD_GND':g,'FIELD_5V':'FIELD_B_5V_PRE','FA_PGOOD':'FIELD_B_PRE_EN'}
 for old,z in entry.items():
  if z.get('source_block')!='field_power':continue
  pref=old[0]
  if pref=='U':u+=1;new=f'U{u}'
  elif pref=='R':r+=1;new=f'R{r}'
  elif pref=='C':c+=1;new=f'C{c}'
  elif pref=='L':new='L19001'
  else:raise ValueError(old)
  zz=copy.deepcopy(z);zz['pins']={k:(nt[n] if n in nt else n.replace('FIELD_FIELD_','FIELD_B_PRE_') if n else None) for k,n in z['pins'].items()};zz['source_ref']=old;zz['source_block']='motherboard_power_entry';zz['role']='FIELD_B local preregulator: exact reviewed '+old;zz['footprint']=zz['footprint'].replace('CNC_MB_Entry:','CNC_MB_Safety:');parts[new]=zz;clones[old]=new
 # Existing receiver slew/default/threshold constraints are recorded, not hidden.
 bounds={}
 for k,nets in [('BoundarySupply',['FIELD_B_24V_PROTECTED',v,g,'IO_3V3','LOGIC_GND','CORE_5V']),('BoundaryXS1',['SAFE_24V','EXT_PERMIT_IN','PROCESS_PERMIT_IN','SAFETY_STATUS_IN','RESET_ARM_IN','ARM_LAMP','CONTACTOR_FB_IN','STO_FB_IN','PERMIT_OUT_1','PERMIT_OUT_2']),('BoundarySignals',['EXT_PERMIT_3V3','PROCESS_PERMIT_EXT_3V3','EXT_PERMIT_FPGA','PROCESS_PERMIT_FPGA','SAFETY_STATUS_FPGA','RESET_ARM_FPGA','CONTACTOR_FB_FPGA','STO_FB_FPGA','PERMIT_OUT_DRIVE','MC_RAILS_OK_5V','ARM_LAMP_FPGA','DIC_SENSOR_SDA','DIC_SENSOR_SCL','DI_SENSOR_G0_FAULT','DI_SENSOR_G1_FAULT','DI_SENSOR_G2_FAULT','DI_SAFETY_SUPPLY_FAULT','DI_SAFETY_SECONDARY_FAULT']),('BoundarySensor',[f'SENS24_G{i}' for i in range(3)]+['FIELD_B_5V_PRE'])]:
  ref=f'B{19001+len(bounds)}';bounds[ref]={'kind':k,'mpn':'','value':'INTERNAL REVIEW INTERFACE','footprint':'','physical':False,'pins':{str(i):n for i,n in enumerate(nets,1)},'role':'No fitted connector/constant power. Parent owns real terminal geometry.'}
 return {'schema_version':1,'revision':'motherboard-safety-sensor-r0.1-candidate','manufacturing_ready':False,'physical_qualification':False,'components':parts,'boundaries':bounds,'fitted_pad_count':sum(len(p['pins']) for p in parts.values()),'general_DI_unchanged':True,'XS1_dedicated_input_count':6,'inputs':inputs,'sensor_groups':groups,'safe_limiter_ref':safe,'safe_ilim_ref':safe_il,'safe_monitor_ref':mon,'safe_health_contacts':contacts,'monitor_windows':windows,'permit_contact_ref':po,'arm_lamp_ref':lamp,'adc_ref':adc,'field_B_preregulator_clone_map':clones,'required_LDO_pin_changes':{'U11018.5':{'old':'FIELD_B_24V_PROTECTED','new':'FIELD_B_5V_PRE'},'U11018.8':{'old':'FIELD_B_24V_PROTECTED','new':'FIELD_B_5V_PRE'}},'required_DIC_pin_changes':{'U13001.42':{'old':None,'new':'DIC_SENSOR_SCL','gpio':'PB3','mode':'software open-drain I2C'},'U13001.43':{'old':None,'new':'DIC_SENSOR_SDA','gpio':'PB4','mode':'software open-drain I2C'}},'open_gates':['Not frozen: exact new component/footprint/native source review in progress.','Existing13 health metadata must be updated only after actual19 endpoints adopted.','All partial rails/ISO7760/ISO7720/TLP LED drivers and power-up trajectories require source reconciliation and physical ramp validation; weak bias is not a proof.','TPS26624 hard-short current max is not published at26.7k; source-backed overload testpoint only.','SAFE switch open-load flag is not used as hardware permission: dry-contact loads can legitimately bebelow8mA.','Sensor-voltage firmware calibration, loaded ADC/source impedance, stale/absent transfer detection and GPIO-I2C are not implemented.','Field3.3 regulator aggregate current/thermal/decoupling/IRdrop including this new circuit must close.','Reset/arm timing, stuck button, contactor/STO mismatch, self-tests and no automaticmotionrestart are FPGA/driver target work, not replaced by these physical frontends.']}

def footprints(out):
 lib=out/'CNC_MB_Safety.pretty';lib.mkdir(exist_ok=True)
 sources=[ROOT/'hardware/motherboard_di/CNC_MB_DI.pretty/ISO1212_DBQ16_TI.kicad_mod',ROOT/'hardware/motherboard_power_entry/CNC_MB_Entry.pretty/TPS2662_DRC10_TI.kicad_mod',ROOT/'hardware/motherboard_motor_power/CNC_MotorPower.pretty/LTC2962_UD16.kicad_mod',ROOT/'hardware/motherboard_motor_power/CNC_MotorPower.pretty/ISO7720_DW16_TI_HV.kicad_mod',ROOT/'hardware/motherboard_motors/CNC_Motors.pretty/TLP3640A_SO4_11-3C1.kicad_mod',ROOT/'hardware/motherboard_process/CNC_MB_Process.pretty/TPS1H000_DGN8_TI.kicad_mod',ROOT/'hardware/motherboard_power_entry/CNC_MB_Entry.pretty/LMR36506_RPE9_TI.kicad_mod',ROOT/'hardware/motherboard_power_entry/CNC_MB_Entry.pretty/LPS6235_Coilcraft.kicad_mod']
 for src in sources:shutil.copyfile(src,lib/src.name)
 iso=(lib/'ISO7720_DW16_TI_HV.kicad_mod').read_text(encoding='utf-8').replace('ISO7720_DW16_TI_HV','ISO7760_DW16_TI_HV').replace('ISO7720','ISO7760')
 (lib/'ISO7760_DW16_TI_HV.kicad_mod').write_text(iso,encoding='utf-8')
 raw='(footprint "ADS1115_DGS10_TI"(version 20241229)(generator "controller_hardware")(layer "F.Cu")(descr "TI DGS0010A 4221984A05/2015:10x1.45x.3 land centres+-2.2, .5pitch; maxbody3.1x3.1;125umstencil")(attr smd)(property "Reference" "REF**"(at 0 -2.3)(layer "F.SilkS")(effects(font(size .7 .7)(thickness .1))))(property "Value" "ADS1115_DGS10_TI"(at 0 2.3)(layer "F.Fab")(effects(font(size .7 .7)(thickness .1))))(fp_rect(start -1.55 -1.55)(end 1.55 1.55)(stroke(width .1)(type default))(layer "F.Fab"))(fp_rect(start -3.175 -1.8)(end 3.175 1.8)(stroke(width .05)(type default))(layer "F.CrtYd"))'
 for n in range(1,11):
  x=-2.2 if n<=5 else 2.2;y=(n-1)*.5-1 if n<=5 else (10-n)*.5-1
  raw+=f'(pad "{n}" smd roundrect(at {x} {y})(size 1.45 .3)(layers "F.Cu" "F.Paste" "F.Mask")(roundrect_rratio .166667))'
 raw+='(fp_circle(center -3.0 -1.55)(end -2.85 -1.55)(stroke(width .12)(type default))(fill solid)(layer "F.SilkS")))'
 (lib/'ADS1115_DGS10_TI.kicad_mod').write_text(dump(parse(raw))+'\n',encoding='utf-8')
 (out/'fp-lib-table').write_text(dump(parse('(fp_lib_table(version 7)(lib(name "CNC_MB_Safety")(type "KiCad")(uri "${KIPRJMOD}/CNC_MB_Safety.pretty")(options "")(descr "Source-backed XS1 and sensor footprints")))'))+'\n',encoding='utf-8')

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
  if ref.startswith('U'):x=63.5+(ic%7)*165.1;y=83.82+(ic//7)*139.7;ic+=1
  elif p['physical']:x=40.64+(pas%17)*68.58;y=800.1+(pas//17)*30.48;pas+=1
  else:x=63.5+(bnd%7)*165.1;y=1905+(bnd//7)*190.5;bnd+=1
  layout=layouts[p['kind']];small=p['kind'] in ['R','C','TVS'];rx=x+3.81 if small else x;ry=y-2.54 if small else y-max(z[3] for z in layout)-10.16
  props=''.join(f'(property {quote(k)} {quote(v)}(at {rx} {ry+dy} 0){effects(.8,"hide") if hide else effects(.8,"(justify left)" if small else "")})' for k,v,dy,hide in [('Reference',ref,0,False),('Value',p['value'],2.54,False),('MPN',p['mpn'],0,True),('Footprint',p['footprint'],0,True)])
  yes='yes' if p['physical'] else 'no';items.append(f'(symbol(lib_id "CNC:{p["kind"]}")(at {x} {y} 0)(unit 1)(in_bom {yes})(on_board {yes})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_safety_sensor"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
  for n,_,px,py,_,_ in layout:
   sx,sy=round(x+px,4),round(y-py,4);net=p['pins'][str(n)]
   if net is None:items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(n)+"nc")}"))');continue
   dx=-5.08 if px<0 else 5.08 if px>0 else 0;dy=0 if px else 5.08;ex,ey=round(sx+dx,4),round(sy+dy,4)
   items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"wire")}"))');items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.65,"(justify right bottom)" if px<0 else "(justify left bottom)")}(uuid "{uid(ref+str(n)+"label")}"))');netmap.setdefault(net,[]).append([ref,str(n)])
 for i,net in enumerate(['IO_3V3','LOGIC_GND','CORE_5V','FIELD_B_24V_PROTECTED','DOB_FIELD_3V3','FIELD_B_0V']):
  ref=f'#FLG190{i}';x=30.48+i*139.7;y=2159;items.append(f'(symbol(lib_id "CNC:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid "{uid(ref)}")(property "Reference" "{ref}"(at {x} {y} 0){effects(1,"hide")})(property "Value" "PARENT SUPPLY"(at {x} {y} 0){effects(1,"hide")})(instances(project "motherboard_safety_sensor"(path "/{root}"(reference "{ref}")(unit 1)))))(label "{net}"(at {x} {y} 0){effects(.8)}(uuid "{uid(ref+"label")}"))')
 note='ACTUAL SENSOR/XS1 FRONTEND / six dedicated wetting inputs, three sensor feeds, safe supply, ARM lamp, physical fixed permission contacts and isolated readback.\nSource candidate: partial rails, loaded timing, surge and GPIO-I2C target qualification remain. No customcards, no automatic rearm.'
 items.append(f'(text {quote(note)}(at 20.32 17.78 0){effects(1.4,"(justify left top)")}(uuid "{uid(note)}"))')
 raw=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{root}")(paper "User" 1270 2210)(title_block(title "Motherboard sensor supplies and dedicated XS1 interface")(date "2026-09-30")(rev "r0.1"))(lib_symbols'+''.join(libs)+')'+''.join(items)+')'
 (out/'motherboard_safety_sensor.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf-8');(out/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in libs)+')'))+'\n',encoding='utf-8');(out/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Sensor and XS1 source")))'))+'\n',encoding='utf-8');(out/'motherboard_safety_sensor.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_safety_sensor.kicad_pro','version':1},'erc':{'rule_severities':{k:'warning' for k in ['single_global_label','four_way_junction','simulation_model_issue','footprint_filter']}}},indent=2)+'\n');footprints(out)
 for name,obj in [('design',d),('pin-map',netmap),('boundary-map',d['boundaries'])]:(out/(name+'.json')).write_text(json.dumps(obj,indent=2)+'\n')
 with (out/'bom.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['Reference','Value','MPN','Footprint','Status']);w.writeheader();w.writerows({'Reference':ref,'Value':p['value'],'MPN':p['mpn'],'Footprint':p['footprint'],'Status':'source_candidate_not_qualified'} for ref,p in d['components'].items())
 print(json.dumps({'components':len(d['components']),'pads':d['fitted_pad_count'],'manufacturing_ready':False}));return d


if __name__=='__main__':build()
