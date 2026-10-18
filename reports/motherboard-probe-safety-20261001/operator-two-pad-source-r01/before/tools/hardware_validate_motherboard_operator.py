"""Independent exact pins, fault-domain, default, marker and native checks."""
import argparse,collections,json
from pathlib import Path
from hardware_validate_motherboard_do import native
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_operator'
CONTACTS=['MPG_SEL_X','MPG_SEL_Y','MPG_SEL_Z','MPG_SEL_A','MPG_SEL_B','MPG_SEL_C','MPG_MUL_X1','MPG_MUL_X10','MPG_MUL_X100','MPG_PEND_AUX','MPG_ENABLE','MOD_PRESENT']
BITS=[n+'_ACTIVE' for n in CONTACTS]+['XF_SUPPLY_FAULT','MPG_SUPPLY_FAULT','PRB0_SUPPLY_FAULT','PRB1_SUPPLY_FAULT','ENC0_SUPPLY_FAULT','ENC1_SUPPLY_FAULT','ENC2_SUPPLY_FAULT','ENC3_SUPPLY_FAULT','LOGIC_GND','IO_3V3','LOGIC_GND','IO_3V3']

def validate(d,netlist=None,erc=None):
 errors=[]
 def ck(ok,msg):
  if not ok:errors.append(msg)
 try:
  p=d['components'];ck(len(p)==d['fitted_component_count']==194,'194 actual footprints');ck(sum(len(x['pins']) for x in p.values())==d['fitted_pad_count']==579,'579 electrical pads')
  ck(collections.Counter(x['kind'] for x in p.values())=={'R':82,'C':63,'TVS':14,'CLAMP':12,'SW5':6,'SW24':2,'INV6':4,'BUF1':3,'AND1':1,'AND2':1,'ISO2':1,'ISO1212':1,'SR':3,'SHUNT':1},'exact required functional inventory, no custom card/module duplication')
  ck(not d['manufacturing_ready'] and not d['physical_qualification'] and not d['firmware_implemented'] and not d['voltage_adc_implemented'],'source/ERC notphysical/firmware/portvoltage evidence')
  ck(d['one_custom_board'] and not d['external_probes_consume_general_DI'],'dedicated probes separate from24generalDI')
  def pin(ref,mpn,pins):ck(p[ref]['mpn']==mpn and p[ref]['pins']=={str(k):v for k,v in pins.items()},'independent exactmanufacturer pinmap '+ref)
  def resist(a,b,ohm):return [r for r,x in p.items() if x['kind']=='R' and set(x['pins'].values())=={a,b} and x['resistance_ohm']==ohm]
  def caps(a,b,f):return [r for r,x in p.items() if x['kind']=='C' and set(x['pins'].values())=={a,b} and abs(x['capacitance_f']-f)<1e-15]
  def resist_one(a,b,ohm):ck(len(resist(a,b,ohm))==1,'actualsingle resistor '+a+'/'+b+'/'+str(ohm))
  ck(len(d['contacts'])==12 and [x['external'] for x in d['contacts']]==CONTACTS,'tenselectors plusenable pluspresence')
  for i,c in enumerate(d['contacts']):
   name=CONTACTS[i];ck(c['active']==name+'_ACTIVE' and c['conditioned']==name+'_CONDITIONED' and c['active_low_external'] and c['not_a_24V_input'] and c['normal_input_max_v']==5.25,'typed protected5V contact input')
   resist_one(name,name+'_CONDITIONED',1000);resist_one(name,'MOTION_5V_RAW',10000);ck(len(caps(name+'_CONDITIONED','LOGIC_GND',10e-9))==1,'contact filter beforeSchmitt')
   pin(c['clamp_ref'],'BAT54S,215',{1:'LOGIC_GND',2:'MOTION_5V_RAW',3:name+'_CONDITIONED'});t=p[c['tvs_ref']];ck(t['mpn']=='TPD1E10B06DPYR' and t['pins']=={'1':name,'2':'LOGIC_GND'} and t['working_standoff_v']==5.5,'bidirectional5.5VcontactTVS')
  for bank,ref in enumerate(['U14007','U14014']):
   expected={7:'LOGIC_GND',14:'IO_3V3'}
   for j,(a,y) in enumerate([(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)]):expected[a]=CONTACTS[bank*6+j]+'_CONDITIONED';expected[y]=CONTACTS[bank*6+j]+'_ACTIVE'
   pin(ref,'SN74LVC14APWR',expected)
  for ref,incoming,buffered in [('U14015','FAST_PORTS_ENABLE','FAST_PORTS_EN_BUFFER'),('U14016','XF_POWER_ENABLE','XF_REQUEST_BUFFER'),('U14017','FPGA_CDONE','FPGA_CDONE_BUFFER')]:pin(ref,'SN74LVC1G17DBVR',{1:None,2:incoming,3:'LOGIC_GND',4:buffered,5:'IO_3V3'})
  resist_one('FAST_PORTS_ENABLE','LOGIC_GND',4700);resist_one('XF_POWER_ENABLE','LOGIC_GND',4700)
  pin('U14018','SN74LVC1G08DBVR',{1:'FAST_PORTS_EN_BUFFER',2:'FPGA_CDONE_BUFFER',3:'LOGIC_GND',4:'FAST_PORTS_EN_CONFIGURED',5:'IO_3V3'})
  pin('U14019','SN74LVC2G08DCUR',{1:'FAST_PORTS_EN_CONFIGURED',2:'XF_REQUEST_BUFFER',3:'XF_POWER_EN_GATED',4:'LOGIC_GND',5:'XF_POWER_QUALIFIED',6:'MOD_PRESENT_ACTIVE',7:'XF_POWER_QUALIFIED',8:'IO_3V3'})
  # TI SLVS841F10.2.1.1 full-temp bounding equations, resistor tolerance+TCR.
  ck(len(d['ports_5v'])==6,'six independent5Vport switches')
  for idx,(name,ohms,load) in enumerate([('ENC0',110000,.2),('ENC1',110000,.2),('ENC2',110000,.2),('ENC3',110000,.2),('MPG',221000,.1),('FREQ',150000,.15)]):
   rec=d['ports_5v'][idx];ck(rec['name']==name and rec['ilim_ohm']==ohms and rec['normal_load_a']==load,'perport currentlimit selection')
   pin(rec['switch_ref'],'TPS2553DBVR-1',{1:'MOTION_5V_RAW',2:'LOGIC_GND',3:name+'_POWER_EN',4:name+'_POWER_FAULT_N',5:name+'_ILIM',6:name+'_5V'})
   resist_one(name+'_ILIM','LOGIC_GND',ohms);resist_one(name+'_POWER_EN','LOGIC_GND',10000);resist_one('XF_POWER_EN_GATED' if name=='FREQ' else 'FAST_PORTS_EN_CONFIGURED',name+'_POWER_EN',33);resist_one(name+'_POWER_FAULT_N','IO_3V3',10000);resist_one(name+'_5V','LOGIC_GND',100000)
   rlo=ohms/1000*.99*.985;rhi=ohms/1000*1.01*1.015;lo=25.230/rhi**1.016;hi=22.980/rlo**.940
   ck(abs(rec['minimum_calculated_a']-lo)<1e-12 and abs(rec['maximum_calculated_a']-hi)<1e-12,'TI equation bounds incltemp/resistortolerance')
   ck(lo>load+5.25/(100000*.99*.985) and hi<=load*1.5,'normal load plusbleed and1.5xlimittarget screen')
   ck(not rec['guaranteed_point_used'] and rec['equation_screen_only'] and not rec['fault_is_power_good'] and not rec['voltage_adc_implemented'] and rec['validation_requires_motion_rail_and_region_qualification'],'faultflagsnotpowergood; exactpoint/equation distinction')
   for rail in ['MOTION_5V_RAW',name+'_5V']:
    ck(len(caps(rail,'LOGIC_GND',1000e-9))>=1 and len(caps(rail,'LOGIC_GND',100e-9))>=1,'actualport bypass/bulk')
  ck(len(d['ports_24v'])==2,'two protected fieldAprobe supplies')
  for idx,rec in enumerate(d['ports_24v']):
   name=f'PRB{idx}';pin(rec['switch_ref'],'TPS26624DRCR',{1:'FIELD_A_24V_PROTECTED',2:name+'_UVLO',3:'FIELD_GND',4:name+'_SHDN_N',5:'FIELD_GND',6:'FIELD_GND',7:name+'_ILIM',8:name+'_DVDT',9:name+'_FIELD_FAULT_N',10:name+'_24V',11:'FIELD_GND'})
   resist_one(name+'_ILIM','FIELD_GND',49900);resist_one('FIELD_A_24V_PROTECTED',name+'_UVLO',1000000);resist_one('DOA_FIELD_3V3',name+'_SHDN_N',10000);resist_one(name+'_SHDN_N','FIELD_GND',100000);resist_one(name+'_FIELD_FAULT_N','DOA_FIELD_3V3',10000)
   ck(rec['normal_load_a']==.1 and rec['frozen_limit_max_a']==.15 and rec['ilim_ohm']==49900 and not rec['guaranteed_current_bounds_available'] and not rec['hard_short_bound_available'] and rec['engineering_gate'],'unresolved probe guaranteedlimit remains explicit;44.2kmax.159notaccepted')
  pin('U14028','ISO7720FDWR',{1:'FIELD_GND',2:None,3:'DOA_FIELD_3V3',4:'PRB0_FIELD_FAULT_N',5:'PRB1_FIELD_FAULT_N',6:None,7:None,8:'FIELD_GND',9:'LOGIC_GND',10:None,11:None,12:'PRB1_FAULT_GOOD_ISO',13:'PRB0_FAULT_GOOD_ISO',14:'IO_3V3',15:None,16:'LOGIC_GND'})
  good=[n+'_POWER_FAULT_N' for n in ['ENC0','ENC1','ENC2','ENC3','MPG','FREQ']]+['PRB0_FAULT_GOOD_ISO','PRB1_FAULT_GOOD_ISO'];bad=[n+'_SUPPLY_FAULT' for n in ['ENC0','ENC1','ENC2','ENC3','MPG','XF','PRB0','PRB1']]
  for bank,ref in enumerate(['U14029','U14030']):
   expected={7:'LOGIC_GND',14:'IO_3V3'}
   for j,(a,y) in enumerate([(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)]):i=bank*6+j;expected[a]=good[i] if i<8 else 'LOGIC_GND';expected[y]=bad[i] if i<8 else None
   pin(ref,'SN74LVC14APWR',expected)
  pin(d['probe_ref'],'ISO1212DBQR',{1:'LOGIC_GND',2:'IO_3V3',3:'IO_3V3',4:'PROBE_FPGA',5:'TOOLSETTER_FPGA',6:None,7:None,8:'LOGIC_GND',9:'FIELD_GND',10:'PRB1_IN_SENSE',11:'PRB1_SENSE',12:'PRB1_SUB_ISLAND',13:'PRB0_SUB_ISLAND',14:'FIELD_GND',15:'PRB0_IN_SENSE',16:'PRB0_SENSE'})
  for idx,out in enumerate(['PROBE_FPGA','TOOLSETTER_FPGA']):
   resist_one(f'PRB{idx}_IN',f'PRB{idx}_IN_SENSE',1000);resist_one(f'PRB{idx}_IN_SENSE',f'PRB{idx}_SENSE',562);resist_one(out,'LOGIC_GND',100000)
   ck(not any(x['kind']=='C' and any(n and n.startswith(f'PRB{idx}_IN') for n in x['pins'].values()) for x in p.values()),'noordinaryDI RCfilter on dedicated fastprobes')
   ck(len([x for x in p.values() if x['kind']=='TVS' and x['mpn']=='SMBJ33CA-E3/52' and set(x['pins'].values())=={f'PRB{idx}_IN','FIELD_GND'}])==1,'probe bidirectional33VTVS')
  for bank,ref in enumerate(d['sr_refs']):
   expected={1:'FAST_SR_LOAD_BUFFER',2:'FAST_SR_CLK_BUFFER',7:None,8:'LOGIC_GND',9:'FAST_SR_DATA_SOURCE' if bank==0 else f'FAST_SR_CHAIN{bank}',10:'LOGIC_GND' if bank==2 else f'FAST_SR_CHAIN{bank+1}',15:'LOGIC_GND',16:'IO_3V3'}
   for j,num in enumerate([6,5,4,3,14,13,12,11]):expected[num]=BITS[bank*8+j]
   pin(ref,'SN74LV165APWR',expected)
  ck(d['sr_serialized_bits']==BITS and d['marker_word']==10 and d['marker_bits']==[20,21,22,23] and d['shift_first']=='nearestH=bit0','physicalfarendnumeric0xAmarker/bitorder')
  ck(d['double_read_agreement_required'] and d['three_bad_markers_latch_fault'] and d['poll_period_s']==.0001 and d['read_clock_hz']==6250000,'frozenreadonlypolling obligations')
  for a,b,o in [('FAST_SR_CLK','FAST_SR_CLK_BUFFER',33),('FAST_SR_LOAD_N','FAST_SR_LOAD_BUFFER',33),('FAST_SR_DATA_SOURCE','FAST_SR_DATA',33),('FAST_SR_CLK','LOGIC_GND',10000),('FAST_SR_LOAD_N','IO_3V3',10000),('FAST_SR_DATA','LOGIC_GND',100000)]:resist_one(a,b,o)
  pin('U14035','LM4040A25IDBZR',{1:'MPG_VREF_CORE',2:'LOGIC_GND',3:'LOGIC_GND'});resist_one('MOTION_5V_RAW','MPG_VREF_CORE',1800);resist_one('MPG_VREF_CORE','MPG_VREF',22)
  for ref,x in p.items():
   footprints={'CLAMP':'Package_TO_SOT_SMD:SOT-23','INV6':'Package_SO:TSSOP-14_4.4x5mm_P0.65mm','BUF1':'Package_TO_SOT_SMD:SOT-23-5','AND1':'Package_TO_SOT_SMD:SOT-23-5','AND2':'Package_SO:VSSOP-8_2.3x2mm_P0.5mm','SW5':'Package_TO_SOT_SMD:SOT-23-6','SW24':'CNC_MB_Operator:TPS2662_DRC10_TI','ISO2':'Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm','ISO1212':'CNC_MB_Operator:ISO1212_DBQ16_TI','SR':'Package_SO:TSSOP-16_4.4x5mm_P0.65mm','SHUNT':'Package_TO_SOT_SMD:SOT-23'}
   if x['kind'] in footprints:ck(x['footprint']==footprints[x['kind']],'independent exactpackage footprint '+ref)
   if x['kind'] not in ['R','C','TVS','CLAMP','SHUNT']:
    ck(len(caps('IO_3V3','LOGIC_GND',100e-9))>=1,'logic localbypass')
   ck(x['physical'] and x['mpn'] and x['footprint'] and int(ref[1:]) in range(14001,15000),'real14xxx exactparts/footprints')
  for x in d['boundaries'].values():ck(not x['physical'] and not x['mpn'] and not x['footprint'],'parentboundaries are notfittedconnectors')
  if netlist:
   actual=native(netlist);ck(set(actual)==set(p)|set(d['boundaries']),'nativeXML completepopulation')
   for ref,x in {**p,**d['boundaries']}.items():ck(actual.get(ref)=={k:x[k] for k in ['mpn','footprint','value','pins']},'nativeXML fullpin/value/net '+ref)
  if erc:
   e=json.loads(Path(erc).read_text());v=[v for s in e['sheets'] for v in s['violations']];ck(e['ignored_checks']==[] and len(v)==2 and all(x['severity']=='warning' and x['type']=='isolated_pin_label' for x in v),'nativeERC onlytwointentionalfloatingSUB warnings,noignored')
 except (KeyError,TypeError,IndexError,ValueError,OSError) as exc:errors.append('invalid source/evidence: '+str(exc))
 return {'ok':not errors,'errors':errors,'physical_footprints':194,'electrical_pads':579,'manufacturing_ready':False,'warnings':['Probe49.9k guaranteedoverload/hardshort bounds are an unresolved sourcing/engineering gate.','Portfaultflags are not voltage readings and require actual parentrail/region validity.','No firmware/RTL/load/ESD/thermal/physicalconnector qualification from these source checks.']}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args();r=validate(json.loads((OUT/'design.json').read_text()),OUT/'netlist.xml',OUT/'erc.json')
 if a.write:(OUT/'validation.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r,indent=2));raise SystemExit(not r['ok'])
