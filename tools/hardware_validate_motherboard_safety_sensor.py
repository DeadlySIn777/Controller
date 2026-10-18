"""Independent native/source pin, circuit, domain and conditional-bound review."""
import argparse,collections,json,math,xml.etree.ElementTree as ET
from pathlib import Path
from itertools import product
from hardware_validate_motherboard_do import native
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_safety_sensor'

def validate(d,netlist=None,erc=None):
 errors=[]
 def ck(x,msg):
  if not x:errors.append(msg)
 try:
  p=d['components'];ck(len(p)==176 and sum(len(c['pins']) for c in p.values())==547,'176 real footprint/547 pin source inventory')
  ck(not d['manufacturing_ready'] and not d['physical_qualification'],'no source/native to manufacture assertion')
  ck(d['general_DI_unchanged'] and d['XS1_dedicated_input_count']==6,'six independent safety inputs preserve 24 DI')
  ck(all(19001<=int(r.lstrip('UCDRLTP'))<19500 for r in p),'bounded 19xxx source namespace')
  def find(kind):return [(r,c) for r,c in p.items() if c['kind']==kind]
  def rs(a,b,v):return [c for c in p.values() if c['kind']=='R' and c['pins']=={'1':a,'2':b} and c['resistance_ohm']==v]
  def exact(ref,mpn,pins):
   c=p[ref];ck(c['mpn']==mpn and c['pins']=={str(k):v for k,v in pins.items()},'exact manufacturer part/pin '+ref)
  ck(len(find('ISO1212'))==3,'three actual two-channel safety receivers')
  names=[('EXT_PERMIT','EXT_PERMIT_RAW'),('PROCESS_PERMIT','PROCESS_PERMIT_RAW'),('SAFETY_STATUS','SAFETY_STATUS_FPGA'),('RESET_ARM','RESET_ARM_FPGA'),('CONTACTOR_FB','CONTACTOR_FB_FPGA'),('STO_FB','STO_FB_FPGA')]
  for pair,(ref,c) in enumerate(find('ISO1212')):
   pins={1:'LOGIC_GND',2:'IO_3V3',3:'IO_3V3',6:None,7:None,8:'LOGIC_GND',9:'FIELD_B_0V',14:'FIELD_B_0V'}
   for j,(name,out) in enumerate(names[pair*2:pair*2+2]):
    pins.update({4+j:out,16-j*5:name+'_SENSE',15-j*5:name+'_ISO_IN',13-j:name+'_SUB_ISLAND'})
    ck(len(rs(name+'_IN',name+'_SENSE',1000))==1 and len(rs(name+'_SENSE',name+'_ISO_IN',562))==1,'reviewed sinking threshold/current network '+name)
    ck(len(rs(out,'LOGIC_GND',100000))==1,'physical receiver bias '+name)
   exact(ref,'ISO1212DBQR',pins);ck(c['footprint']=='CNC_MB_Safety:ISO1212_DBQ16_TI','TI DBQ16 source geometry')
  for ch in d['sensor_groups']:
   i=ch['group'];r=ch['limiter_ref'];g='FIELD_B_0V';fl=f'DI_G{i}_FLT_N'
   exact(r,'MAX17612AATB+T',{1:'FIELD_B_24V_PROTECTED',2:f'DI_G{i}_UV',3:g,4:f'DI_G{i}_CLMODE',5:'DOB_FIELD_3V3',6:fl,7:fl,8:f'DI_G{i}_SETI',9:g,10:f'SENS24_G{i}',11:g})
   q=p[ch['ilim_ref']];ck(q['mpn']=='TNPW06031K37BEEA' and q['resistance_ohm']==1370 and q['tolerance']==.001 and q['tcr_ppm_K']==25,'actual full-range current adjustment')
   rhi=1370*1.001*1.00375;rlo=1370*.999*.99625
   ck(.95*300/rhi>.2+30/99000+30/130000 and 1.05*300/rlo<.3,'normal200mA plus actual bleeds and300mA cap')
   ck(ch['rated_continuous_a']==.2 and ch['guaranteed_limit_accuracy_fraction']==.05 and ch['static_short_limit_uses_same_accuracy_range'] and not ch['transient_short_overshoot_qualified'],'sourced static limit, no transient energy certification')
   ck(len(rs(f'DI_G{i}_CLMODE',g,150000))==1,'manufacturer latch-off resistor')
  g='FIELD_B_0V';v='DOB_FIELD_3V3'
  exact(d['safe_limiter_ref'],'TPS1H000AQDGNRQ1',{1:v,2:v,3:'SAFE_SWITCH_FAULT_N',4:'SAFE_ILIM',5:'SAFE_DELAY',6:g,7:'SAFE_24V',8:'FIELD_B_24V_PROTECTED',9:g})
  q=p[d['safe_ilim_ref']];ck(q['mpn']=='TNPW06039K53BEEA' and q['resistance_ohm']==9530 and q['tolerance']==.001 and q['tcr_ppm_K']==25,'atleast50mA accuracy range exact resistor')
  # Fitted initial tolerance plus full150K datasheet range screen.
  rrlo=9530*.999*(1-150*25e-6);rrhi=9530*1.001*(1+150*25e-6);imin=.8*480/rrhi;imax=1.2*480/rrlo
  ck(480/rrhi>=.05 and 6*.00275+30/99000<imin and imax<.15,'six wetting loads below minimum limit and150mA cap')
  mon=p[d['safe_monitor_ref']];ck(mon['mpn']=='LTC2962HUD#PBF' and mon['pins']['12']=='SAFE_DOMAIN_HEALTH' and mon['pins']['1']==v and mon['pins']['10']==v,'actual200ms post-rail monitor not idealmetadata')
  ck(len(rs('SAFE_DOMAIN_HEALTH',v,10000))==1 and len(rs('SAFE_DOMAIN_HEALTH',g,100000))==1 and not rs('SAFE_DOMAIN_HEALTH',g,10000),'loaded monitor HIGH must not be half-rail')
  for name,out,qref in [('EXT_PERMIT','EXT_PERMIT_3V3',d['safe_health_contacts'][0]),('PROCESS_PERMIT','PROCESS_PERMIT_EXT_3V3',d['safe_health_contacts'][1])]:
   led=name+'_HEALTH_LED_A';k=name+'_HEALTH_LED_K';exact(qref,'TLP3640A(TPL,E',{1:led,2:k,3:name+'_RAW',4:out})
   ck(len(rs(v,led,215))==1 and len(rs(out,'LOGIC_GND',10000))==1,'real LED trigger/output bias '+name)
   drivers=[(r,c) for r,c in find('ODINV') if c['pins']['4']==k];ck(len(drivers)==1,'independent single-string load '+name)
   if drivers:exact(drivers[0][0],'SN74LVC1G06DBVR',{1:None,2:'SAFE_DOMAIN_HEALTH',3:g,4:k,5:v})
  ledmin=(3.234-1.9-.55)/(215*1.01);ledmax=3.366/(215*.99);ck(ledmin>.003 and ledmax<.02,'conditional minimum/maximum single-string current')
  for ref,c in find('BUF2'):exact(ref,'SN74LVC2G34DCKR',{1:'EXT_PERMIT_3V3',2:'LOGIC_GND',3:'PROCESS_PERMIT_EXT_3V3',4:'PROCESS_PERMIT_FPGA',5:'IO_3V3',6:'EXT_PERMIT_FPGA'})
  for ref,c in find('AND_TTL'):exact(ref,'SN74AHCT1G08DBVR',{1:'PERMIT_OUT_DRIVE',2:'MC_RAILS_OK_5V',3:'LOGIC_GND',4:'XS1_PERMIT_LED_ON',5:'CORE_5V'})
  exact(d['permit_contact_ref'],'TLP3640A(TPL,E',{1:'XS1_PERMIT_LED_A',2:'XS1_PERMIT_LED_K',3:'PERMIT_OUT_1',4:'PERMIT_OUT_2'})
  ck(len(rs('CORE_5V','XS1_PERMIT_LED_A',270))==1 and (4.95-1.9-.55)/(270*1.01)>.005 and 5.05/(270*.99)<.02,'external contact bounded LED min/max')
  ck(len(rs('PERMIT_OUT_DRIVE','LOGIC_GND',10000))==1 and len(rs('XS1_PERMIT_LED_ON','LOGIC_GND',10000))==1,'external NO permission off defaults')
  exact(d['arm_lamp_ref'],'TPS1H000AQDGNRQ1',{1:'ARM_LAMP_FIELD_CMD',2:v,3:'ARM_LAMP_FAULT_N',4:'ARM_LAMP_ILIM',5:'ARM_LAMP_DELAY',6:g,7:'ARM_LAMP',8:'FIELD_B_24V_PROTECTED',9:g})
  rx=['DI_G0_GOOD_RX','DI_G1_GOOD_RX','DI_G2_GOOD_RX','DI_SAFE_GOOD_RX','DI_LAMP_GOOD_RX','DI_SAFE_SWITCH_GOOD_RX'];tx=['DI_G0_FLT_N','DI_G1_FLT_N','DI_G2_FLT_N','SAFE_DOMAIN_HEALTH','ARM_LAMP_FAULT_N','SAFE_SWITCH_FAULT_N']
  for ref,c in find('ISO7760F'):exact(ref,'ISO7760FDWR',{1:v,8:g,9:'LOGIC_GND',16:'IO_3V3',**{i+2:n for i,n in enumerate(tx)},**{15-i:n for i,n in enumerate(rx)}})
  outs=['DI_SENSOR_G0_FAULT','DI_SENSOR_G1_FAULT','DI_SENSOR_G2_FAULT','DI_SAFETY_SUPPLY_FAULT','DI_SAFETY_SECONDARY_FAULT']
  for inn,out in zip(rx[:5],outs):
   z=[(r,c) for r,c in find('ODINV') if c['pins']['4']==out];ck(len(z)==1,'five actual fault endpoints '+out)
   if z:exact(z[0][0],'SN74LVC1G06DBVR',{1:None,2:inn,3:'LOGIC_GND',4:out,5:'IO_3V3'})
  for ref,c in find('ISO1540'):exact(ref,'ISO1540DR',{1:'IO_3V3',2:'DIC_SENSOR_SDA',3:'DIC_SENSOR_SCL',4:'LOGIC_GND',5:g,6:'DI_SENSOR_SCL_FIELD',7:'DI_SENSOR_SDA_FIELD',8:v})
  exact(d['adc_ref'],'ADS1115IDGSR',{1:g,2:None,3:g,4:'DI_SENSOR_AIN0',5:'DI_SENSOR_AIN1',6:'DI_SENSOR_AIN2',7:'DI_SENSOR_AIN3',8:v,9:'DI_SENSOR_SDA_FIELD',10:'DI_SENSOR_SCL_FIELD'})
  expected={1:'SAFE_DOMAIN_HEALTH',4:'SAFE_DOMAIN_HEALTH',10:'SAFE_DOMAIN_HEALTH',13:'SAFE_DOMAIN_HEALTH',7:g,14:v}
  for i,(s,dd) in enumerate([(2,3),(5,6),(9,8),(12,11)]):expected[s]=f'DI_SENSOR_DIV{i}';expected[dd]=f'DI_SENSOR_AIN{i}'
  for ref,c in find('MUX'):exact(ref,'TMUX1511PWR',expected)
  ck(d['required_DIC_pin_changes']=={'U13001.42':{'old':None,'new':'DIC_SENSOR_SCL','gpio':'PB3','mode':'software open-drain I2C'},'U13001.43':{'old':None,'new':'DIC_SENSOR_SDA','gpio':'PB4','mode':'software open-drain I2C'}},'bounded two GPIOs, no fake hardwareI2C')
  ck(d['required_LDO_pin_changes']=={'U11018.5':{'old':'FIELD_B_24V_PROTECTED','new':'FIELD_B_5V_PRE'},'U11018.8':{'old':'FIELD_B_24V_PROTECTED','new':'FIELD_B_5V_PRE'}},'exact two-pin B-LDO preregulation')
  entry=json.loads((ROOT/'hardware/motherboard_power_entry/design.json').read_text())['components'];mapping=d['field_B_preregulator_clone_map'];ck(len(mapping)==16,'complete converter loop clone')
  nt={'FIELD_A_24V_PROTECTED':'FIELD_B_24V_PROTECTED','FIELD_GND':g,'FIELD_5V':'FIELD_B_5V_PRE','FA_PGOOD':'FIELD_B_PRE_EN'}
  for old,new in mapping.items():
   z=entry[old];c=p[new];pins={k:nt[n] if n in nt else n.replace('FIELD_FIELD_','FIELD_B_PRE_') if n else None for k,n in z['pins'].items()}
   ck(c['mpn']==z['mpn'] and c['value']==z['value'] and c['footprint']==z['footprint'].replace('CNC_MB_Entry:','CNC_MB_Safety:') and c['pins']==pins,'exact copied converter loop '+old)
  fixed_footprints={'MAX17612A':('MAX17612AATB+T','CNC_MB_Safety:MAX17612_T1033_ADI'),'ISO7720F':('ISO7720FDWR','CNC_MB_Safety:ISO7720_DW16_TI_HV'),'ISO7760F':('ISO7760FDWR','CNC_MB_Safety:ISO7760_DW16_TI_HV'),'ISO1540':('ISO1540DR','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'),'ADC':('ADS1115IDGSR','CNC_MB_Safety:ADS1115_DGS10_TI'),'MUX':('TMUX1511PWR','Package_SO:TSSOP-14_4.4x5mm_P0.65mm'),'ODINV':('SN74LVC1G06DBVR','Package_TO_SOT_SMD:SOT-23-5'),'AND_TTL':('SN74AHCT1G08DBVR','Package_TO_SOT_SMD:SOT-23-5'),'BUF2':('SN74LVC2G34DCKR','Package_TO_SOT_SMD:SOT-363_SC-70-6'),'TLP3640A':('TLP3640A(TPL,E','CNC_MB_Safety:TLP3640A_SO4_11-3C1'),'LIMIT':('TPS1H000AQDGNRQ1','CNC_MB_Safety:TPS1H000_DGN8_TI'),'LTC2962':('LTC2962HUD#PBF','CNC_MB_Safety:LTC2962_UD16')}
  for ref,c in p.items():
   if c['kind'] in fixed_footprints:ck((c['mpn'],c['footprint'])==fixed_footprints[c['kind']],'reviewed exact package '+ref)
  for i,rail in enumerate(['SENS24_G0','SENS24_G1','SENS24_G2','SAFE_24V']):
   ck(len(rs(rail,f'DI_SENSOR_DIV{i}',130000))==1 and len(rs(f'DI_SENSOR_DIV{i}',g,10000))==1 and len(rs(f'DI_SENSOR_AIN{i}',g,100000))==1,'actual post-limiter ADC divider/loading '+rail)
  for ref,c in find('ISO7720F'):exact(ref,'ISO7720FDWR',{1:'LOGIC_GND',2:None,3:'IO_3V3',4:'ARM_LAMP_FPGA',5:'LOGIC_GND',6:None,7:'LOGIC_GND',8:None,9:g,10:None,11:None,12:None,13:'ARM_LAMP_FIELD_CMD',14:v,15:None,16:g})
  for ref,c in p.items():
   ck(c['physical'] and bool(c['footprint']) and (bool(c['mpn']) or c.get('purchased')==False),'real exact fitted part '+ref)
   ck(not any(n=='FIELD_GND' for n in c['pins'].values()),'B return never silently joins A')
  if netlist:
   a=native(netlist);ck(set(a)==set(p)|set(d['boundaries']),'native complete population')
   for r,c in {**p,**d['boundaries']}.items():ck(a.get(r)=={k:c[k] for k in ['mpn','value','footprint','pins']},'native exact pin/part '+r)
  if erc:
   e=json.loads(Path(erc).read_text());vs=[v for s in e['sheets'] for v in s['violations']];ck(not e['ignored_checks'] and all(v['severity']=='warning' and v['type'] in ['isolated_pin_label','ground_pin_not_ground'] for v in vs),'ERC only technical floatingSUB/fieldground warnings, no suppressed checks');ck(collections.Counter(v['type'] for v in vs)=={'isolated_pin_label':6,'ground_pin_not_ground':10},'exact reviewed unsuppressed warning inventory')
 except (KeyError,ValueError,TypeError,OSError,IndexError) as e:errors.append('invalid evidence '+str(e))
 return {'ok':not errors,'errors':errors,'physical_qualification':False,'manufacturing_ready':False,'conditional_safe_current_a':[imin,imax] if 'imin' in locals() else [],'conditional_field_LED_a':[ledmin,ledmax] if 'ledmin' in locals() else []}

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--write',action='store_true');args=a.parse_args();r=validate(json.loads((OUT/'design.json').read_text()),OUT/'netlist.xml',OUT/'erc.json')
 if args.write:(OUT/'validation.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r,indent=2));raise SystemExit(not r['ok'])
