"""Independent native pin, electrical-observation and hardware-fault truth audit."""
import json,math,itertools,collections
from pathlib import Path
from hardware_validate_motherboard_do import native
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_status'
PAIRS=[(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)]
GOOD=['MC_RAILS_OK_5V','WD_M_TRIP_N','WD_O_TRIP_N','TX_PERMIT','FPGA_USER_RESET_N','MOTOR_TX_GATE_A','MOTOR_TX_GATE_B']
RGB=['SYSTEM','COMPUTE','FPGA','ESP','MOTION','EXPANSION','NETWORK']
PINS=[6,7,8,9,11,12,13,14,15,16,17,18,20,21,22,23]
MPNS={'RGB':('AAA3528RGBS/K11/C8CC','CNC_MB_Status:AAA3528RGBS_Kingbright'),'AHCT04':('SN74AHCT04PWR','CNC_MB_Status:PW14_TI'),'LVC07':('74LVC07APW,118','CNC_MB_Status:SOT402_Nexperia'),'AND4':('SN74AHCT08PWR','CNC_MB_Status:PW14_TI'),'I2C':('TCA9517DGKR','CNC_MB_Status:DGK8_TI'),'LED16':('TLC59116FIPWR','CNC_MB_Status:PW28_TI'),'RGB_SWITCH':('TMUX1121DGKR','CNC_MB_Status:DGK8_TI'),'DIODE':('BAS16,215','Package_TO_SOT_SMD:SOT-23')}

def validate(d,netlist=None,erc=None):
 errors=[]
 def ck(v,m):
  if not v:errors.append(m)
 try:
  p=d['components'];ck(len(p)==d['fitted_component_count']==290 and sum(len(z['pins']) for z in p.values())==d['fitted_pad_count']==861,'290 physical parts861 native numberedpins')
  ck(all(z['physical'] for z in p.values()) and not d['manufacturing_ready'] and not d['physical_qualification'] and not d['target_firmware_implemented'] and not d['software_status_freshness_qualified'],'source evidence not target/physical manufacture')
  ck(d['hardware_good_inputs']==GOOD and d['max_status_i2c_clock_hz']==400000 and d['i2c_addresses']==[0x60,0x61],'exact hardware authorities and separate400k I2C')
  ck(d['i2c_por_allcall_address']==0x68 and d['i2c_software_reset_reserved_address']==0x6B and d['i2c_subcall_default_disabled_addresses']==[0x69,0x6A,0x6C] and len(d['required_firmware_initialization'])==4,'PORALLCALL and reserved reset address are not hidden')
  for ref,z in p.items():
   kind=z['kind']
   ck(z['mpn'] and z['footprint'] and int(ref[1:])>=17001 and int(ref[1:])<18000,'real purchased exact MPN/reference '+ref)
   if kind in MPNS:ck((z['mpn'],z['footprint'])==MPNS[kind],'primary part/footprint '+ref)
   if kind=='R':
    codes={680:'680R',1000:'1K00',6800:'6K80',10000:'10K0',100000:'100K'};ohm=z['resistance_ohm'];ck(ohm in codes and z['mpn']=='CRCW0603'+codes.get(ohm,'?')+'FKEA' and z['tolerance']==.01 and z['tcr_ppm_K']==100 and z['power_rating_w']==.1,'actual rated1%resistor '+ref)
   if kind=='C':ck(z['mpn']=='GRM188R72A104KA35D' and z['capacitance_f']==1e-7 and z['voltage_rating_v']==100 and z['pins']['2']=='LOGIC_GND','real bypass '+ref)
   if kind in ['AHCT04','LVC07','AND4']:ck(z['pins']['7']=='LOGIC_GND' and z['pins']['14']=='CORE_5V','CORE5 restored logic and return '+ref)
   if kind=='DIODE':ck(z['pins']['2'] is None and set(z['pins'])=={'1','2','3'},'BAS16 pin2 trulyNC '+ref)
  ck(len(d['receive_indicators'])==36,'24DI plus12dedicatedALM')
  for i,ch in enumerate(d['receive_indicators']):
   n=f'DI{i}_LOGIC' if i<24 else f'ALM{i-24}_FPGA';pin,out=PAIRS[i%6];label=f'IN{i+1}' if i<24 else f'M{i-23} ALM'
   inv=p[ch['buffer_ref']];sink=p[ch['sink_ref']];led=p[ch['led_ref']];rr=p[ch['current_ref']];br=p[ch['bleed_ref']]
   ck(ch['index']==i and ch['label']==label and ch['observed_net']==n and inv['kind']=='AHCT04' and sink['kind']=='LVC07','actual protected receive endpoints '+str(i))
   ck(inv['pins'][str(pin)]==n and inv['pins'][str(out)]==f'OBS{i}_INVERTED' and sink['pins'][str(pin)]==f'OBS{i}_INVERTED' and sink['pins'][str(out)]==f'OBS{i}_K','HIGH→inverseLOW→sinkON truth '+str(i))
   ck(led['mpn']==('APT1608SGC' if i<24 else 'APT1608SURCK') and led['pins']=={'1':f'OBS{i}_K','2':f'OBS{i}_A'} and led['footprint']=='CNC_MB_Status:APT1608_Kingbright','receiveLEDanode/cathode '+str(i))
   ck(rr['pins']=={'1':'CORE_5V','2':f'OBS{i}_A'} and rr['resistance_ohm']==1000 and br['pins']=={'1':f'OBS{i}_A','2':f'OBS{i}_K'} and br['resistance_ohm']==10000,'bounded current and non-starving OFF bleed '+str(i))
  ck(len(d['output_indicators'])==16 and d['output_observation']=='actual terminal voltage, not command/current/readback validity','actual terminal evidence no cached command')
  for i,ch in enumerate(d['output_indicators']):
   ret='FIELD_A_0V' if i<8 else 'FIELD_B_0V';a=f'OUT{i}_A';mid=f'OUT{i}_R_MID';r1,r2=[p[r] for r in ch['current_refs']];led=p[ch['led_ref']];rv=p[ch['reverse_ref']]
   ck(ch['index']==i and ch['terminal']==f'DO{i:02d}' and ch['return']==ret and ch['observes']=='terminal_voltage_only','actual terminal/domain '+str(i))
   ck(r1['pins']=={'1':f'DO{i:02d}','2':mid} and r2['pins']=={'1':mid,'2':a} and r1['resistance_ohm']==r2['resistance_ohm']==6800,'two actualfield resistors '+str(i))
   ck(led['mpn']=='APT1608SGC' and led['pins']=={'1':ret,'2':a} and rv['pins']=={'1':ret,'2':None,'3':a},'fieldLED and antiparallel diode preserve return '+str(i))
  ops=[('WD_M_TRIP_N','WD_O_TRIP_N','STATUS_NO_WDT_TRIP'),('MC_RAILS_OK_5V','STATUS_NO_WDT_TRIP','STATUS_HW_GOOD'),('TX_PERMIT','FPGA_USER_RESET_N','STATUS_MOTION_REQUEST_GOOD'),('MOTOR_TX_GATE_A','MOTOR_TX_GATE_B','STATUS_MOTION_FEEDS_GOOD'),('STATUS_MOTION_REQUEST_GOOD','STATUS_MOTION_FEEDS_GOOD','STATUS_MOTION_RGB_ENABLE'),('LOGIC_GND','LOGIC_GND',None),('LOGIC_GND','LOGIC_GND',None),('LOGIC_GND','LOGIC_GND',None)]
  ck(d['hardware_gate_operations']==[list(z) for z in ops] or d['hardware_gate_operations']==ops,'exact5activehardwareAND and3NC gates')
  ck(d['global_fault_terms']==['MC_RAILS_OK_5V','WD_M_TRIP_N','WD_O_TRIP_N'] and d['ordinary_disarm_is_fault'] is False,'ordinarydisarm is not a fault')
  actual_ops=[]
  for bank,ref in enumerate(d['hardware_gate_refs']):
   z=p[ref];ck(z['kind']=='AND4','hardwareAND implementation')
   for (a,b,y),op in zip([(1,2,3),(4,5,6),(9,10,8),(12,13,11)],ops[bank*4:bank*4+4]):
    got=tuple(z['pins'][str(k)] for k in [a,b,y]);actual_ops.append(got);ck(got==op,'pin-level globalfault and motion-only tree '+ref+str(y))
  for n in GOOD+['STATUS_HW_GOOD','STATUS_MOTION_RGB_ENABLE']:
   rr=[z for z in p.values() if z['kind']=='R' and z['pins']=={'1':n,'2':'LOGIC_GND'}];ck(len(rr)==1 and rr[0]['resistance_ohm']==(10000 if n.startswith('STATUS_') else 100000),'undriven path LOW '+n)
  fs=p[d['fault_sink_ref']];ck(fs['pins']=={'7':'LOGIC_GND','14':'CORE_5V','1':'STATUS_HW_GOOD','2':'STATUS_RED_BUS0','3':'STATUS_HW_GOOD','4':'STATUS_RED_BUS1','5':'STATUS_NO_WDT_TRIP','6':'STATUS_WDT_K','9':'CORE_5V','8':None,'11':'CORE_5V','10':None,'13':'CORE_5V','12':None},'actualnoninvertingLOWfault sink and separate4/3redcurrent banks')
  ck(p[d['watchdog_indicator_ref']]['pins']=={'1':'STATUS_WDT_K','2':'STATUS_WDT_A'} and p[d['watchdog_current_ref']]['resistance_ohm']==1000,'independent watchdog emitter bounded')
  for bits in itertools.product([0,1],repeat=7):
   state={'LOGIC_GND':0,**dict(zip(GOOD,bits))}
   for a,b,y in actual_ops:
    if y is not None:state[y]=state[a]&state[b]
   ck(state['STATUS_HW_GOOD']==(bits[0]&bits[1]&bits[2]) and state['STATUS_NO_WDT_TRIP']==(bits[1]&bits[2]) and state['STATUS_MOTION_RGB_ENABLE']==int(all(bits[3:])),'128nativegraphfault-versusdisarmtruth states')
  ms=p[d['motion_rgb_switch_ref']];ck(ms['kind']=='RGB_SWITCH' and ms['pins']=={'1':'RGB_MOTION_G_SWITCH_IN','2':'RGB_DRIVER_13','3':'STATUS_MOTION_RGB_ENABLE','4':'LOGIC_GND','5':'RGB_MOTION_B_SWITCH_IN','6':'RGB_DRIVER_14','7':'STATUS_MOTION_RGB_ENABLE','8':'CORE_5V'},'actualactiveHIGHnormallyopenswitch, both G/B paths, sameCORE5 voltage range')
  ir=p[d['i2c_repeater_ref']];ck(ir['pins']=={'1':'IO_3V3','2':'AO_I2C_SCL','3':'AO_I2C_SDA','4':'LOGIC_GND','5':'CORE_5V','6':'STATUS_I2C_SDA5','7':'STATUS_I2C_SCL5','8':'CORE_5V'},'actuallevelshift, no5Vthreshold misuse')
  for chip,ref in enumerate(d['rgb_driver_refs']):
   z=p[ref];expected={1:None,2:'LOGIC_GND' if chip==0 else 'CORE_5V',3:'LOGIC_GND',4:'LOGIC_GND',5:'LOGIC_GND',10:'LOGIC_GND',19:'LOGIC_GND',24:'LOGIC_GND',25:'STATUS_HW_GOOD',26:'STATUS_I2C_SCL5',27:'STATUS_I2C_SDA5',28:'CORE_5V'}
   for j,pin in enumerate(PINS):expected[pin]=f'RGB_DRIVER_{chip*16+j}' if chip*16+j<21 else None
   ck(z['pins']=={str(k):v for k,v in expected.items()} and z['i2c_address']==0x60+chip,'Fvariant pin1NC and physicalreset,21channels '+ref)
  ck([ch['label'] for ch in d['rgb_indicators']]==RGB,'7ordinaryRGB labels')
  for i,ch in enumerate(d['rgb_indicators']):
   led=p[ch['led_ref']];ck(led['pins']=={'4':'CORE_5V',**{str(k):f'RGB_{RGB[i]}_{colour}_K' for k,colour in [(1,'R'),(2,'G'),(3,'B')]}},'Kingbright actual pin colours/commonanode '+str(i))
   for j,z in enumerate(ch['channels']):
    k=f'RGB_{RGB[i]}_{["R","G","B"][j]}_K';idx=i*3+j
    ck(z['colour']==['R','G','B'][j] and z['pin']==j+1 and z['driver_ref']==d['rgb_driver_refs'][idx//16] and z['driver_pin']==PINS[idx%16],'RGB allocation '+str(idx))
    rr=p[z['current_ref']];br=p[z['bleed_ref']];ck(rr['pins']=={'1':k,'2':('RGB_MOTION_'+['R','G','B'][j]+'_SWITCH_IN' if i==4 and j in [1,2] else f'RGB_DRIVER_{idx}')} and rr['resistance_ohm']==680 and br['pins']=={'1':'CORE_5V','2':k} and br['resistance_ohm']==10000,'physical emitter current/leak bound '+str(idx))
   rr=p[ch['hardware_red_ref']];di=p[ch['hardware_diode_ref']];node=f'RGB_{RGB[i]}_HW_RED'
   ck(rr['pins']=={'1':f'RGB_{RGB[i]}_R_K','2':node} and rr['resistance_ohm']==680 and di['pins']=={'1':node,'2':None,'3':'STATUS_RED_BUS0' if i<4 else 'STATUS_RED_BUS1'},'independent hardwareparallelRED '+str(i))
  low_r=.99*.985;led_receive_max=5.05/(1000*low_r);rgb_max=5.05/(680*low_r);field_max=30/(13600*low_r);field_r_power=(30/(13600*low_r))**2*(6800*1.01*1.015)
  ck(4*rgb_max<.032 and 2*rgb_max<.050 and led_receive_max<.020 and field_r_power<.1,'all physical resistor/current ceilings including1%100ppm150K independentofVF')
  ck(3.8>.7*5.05 and .44<.3*4.95,'5V logic restoredHIGH/LOW input threshold screens')
  ck(10e-6*10000*1.01*1.015<.11,'poweredHIGH/unpoweredOD leakage shunt conditional voltage')
  if netlist:
   a=native(netlist);ck(set(a)==set(p)|set(d['boundaries']),'native exact population no missing/extraparts')
   for ref,z in {**p,**d['boundaries']}.items():ck(a.get(ref)=={k:z[k] for k in ['mpn','value','footprint','pins']},'native exact pins/part '+ref)
  if erc:
   e=json.loads(Path(erc).read_text());vs=[v for s in e['sheets'] for v in s['violations']];ck(not e['ignored_checks'] and not vs,'nativeERC0errors0warnings/noignored')
 except (KeyError,ValueError,TypeError,IndexError,OSError) as ex:errors.append('invalidsource '+str(ex))
 return {'ok':not errors,'errors':errors,'physical_qualification':False,'manufacturing_ready':False,'hardware_truth_cases':128,'receive_current_max_a':5.05/(1000*.99*.985),'rgb_path_current_max_a':5.05/(680*.99*.985),'four_red_sink_max_a':4*5.05/(680*.99*.985),'DO_voltage_indicator_max_a':30/(13600*.99*.985),'CORE5_emitter_ceiling_normal_a':37*5.05/(1000*.99*.985)+21*5.05/(680*.99*.985),'CORE5_transition_emitter_ceiling_a':37*5.05/(1000*.99*.985)+28*5.05/(680*.99*.985),'IC_max_current_qualified':False}
if __name__=='__main__':
 r=validate(json.loads((OUT/'design.json').read_text()),OUT/'netlist.xml',OUT/'erc.json');(OUT/'validation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));raise SystemExit(not r['ok'])
