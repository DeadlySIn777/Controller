"""Independent exact pins, default topology and bounded LOW/current/RC source screens."""
import argparse,json,math
from pathlib import Path
from hardware_validate_motherboard_do import native,footprint_pads
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_identity_io'

def validate(d,netlist=None,erc=None,footprints=None):
 errors=[]
 def ck(v,msg):
  if not v:errors.append(msg)
 try:
  p=d['components'];b=d['blocks'];ck(len(p)==d['fitted_component_count']==14,'14 actual ID parts');ck(sum(len(q['pins']) for q in p.values())==d['fitted_pad_count']==38,'38 exact ID pads')
  def exact(key,mpn,fp,pins):
   q=p[b[key]];ck(q['mpn']==mpn and q['footprint']==fp and q['pins']=={str(k):v for k,v in pins.items()},'independent manufacturer fullpin/MPN/footprint '+key)
  exact('repeater','TCA9517ADGKR','CNC_MB_Identity:TCA9517A_DGK8_TI',{1:'FREQ_5V_LIMITED',2:'LOGIC_GND',3:'FREQ_ID_A_PROTECTED',4:'LOGIC_GND',5:'FREQ_ID_POWER_GOOD_LOCAL',6:'FREQ_1WIRE_DATA_HOST',7:'LOGIC_GND',8:'IO_3V3'})
  exact('window','TPS3700DDCR','Package_TO_SOT_SMD:SOT-23-6',{1:'FREQ_ID_POWER_GOOD_LOCAL',2:'LOGIC_GND',3:'FREQ_ID_FIELD_UV',4:'FREQ_ID_FIELD_OV',5:'IO_3V3',6:'FREQ_ID_POWER_GOOD_LOCAL'})
  exact('tvs','TPD1E10B06DPYR','CNC_MB_Identity:TPD1E10B06_DPY2_TI',{1:'FREQ_MOD_ID_TO_FRONTEND',2:'LOGIC_GND'})
  required=[('host_pullup','FREQ_1WIRE_DATA_HOST','IO_3V3',10000),('field_pullup','FREQ_MOD_ID_TO_FRONTEND','FREQ_5V_LIMITED',4700),('field_series','FREQ_MOD_ID_TO_FRONTEND','FREQ_ID_A_PROTECTED',330),('window_pullup','FREQ_ID_POWER_GOOD_LOCAL','IO_3V3',10000)]
  for key,a,z,v in required:
   q=p[b[key]];code={330:'330R',4700:'4K70',10000:'10K0'}[v];ck(q['kind']=='R' and q['pins']=={'1':a,'2':z} and q['resistance_ohm']==v and q['mpn']=='CRCW0603'+code+'FKEA' and q['tolerance']==.01 and q['tcr_ppm_K']==100,'real low/default/current resistor '+key)
  for a,z,v in [('FREQ_5V_LIMITED','FREQ_ID_FIELD_UV',107000),('FREQ_ID_FIELD_UV','LOGIC_GND',10000),('FREQ_5V_LIMITED','FREQ_ID_FIELD_OV',123000),('FREQ_ID_FIELD_OV','LOGIC_GND',10000)]:
   qs=[q for q in p.values() if q['kind']=='R' and q['pins']=={'1':a,'2':z}];ck(len(qs)==1 and qs[0]['resistance_ohm']==v and qs[0]['tolerance']==.001 and qs[0]['tcr_ppm_K']==25 and qs[0]['mpn']=='TNPW0603'+{10000:'10K0',107000:'107K',123000:'123K'}[v]+'BEEA','exact real monitored UV/OV divider '+a)
  cs=[q for q in p.values() if q['kind']=='C'];ck(len(cs)==3 and all(q['mpn']=='GRM188R72A104KA35D' and q['capacitance_f']==1e-7 and q['pins']['2']=='LOGIC_GND' for q in cs),'actual three100nF bypasses')
  ck(sum(q['pins']['1']=='IO_3V3' for q in cs)==2 and sum(q['pins']['1']=='FREQ_5V_LIMITED' for q in cs)==1,'own rail and actualfieldreference bypass allocation')
  ck(all(q['physical'] and q['mpn'] and q['footprint'] for q in p.values()),'no placeholder fitted sources')
  ck(set(p[b['host_pullup']]['pins'].values())=={'FREQ_1WIRE_DATA_HOST','IO_3V3'},'never expose MCU directly to field5 pullup')
  li=d['limits'];exp={'temperature_c':[-40,85],'field_terminal_operating_v':[0,5.5],'IO_3V3_min_for_threshold_screen_v':2.7,'IO_3V3_max_v':3.6,'ordinary_ID_VIL_max_v':.8,'ordinary_ID_VOL_max_v':.4,'TCA_B_VILC_max_v':.45,'TCA_B_VOL_max_v':.6,'TCA_A_VOL_max_at6mA_v':.2,'STM32_PD3_VOL_max_at8mA_v':.4,'host_trace_plus_return_resistance_max_ohm':10,'host_total_capacitance_candidate_pf':50,'field_total_capacitance_candidate_pf':400,'standard_speed_only':True,'parasitic_write_power_supported':False,'arbitrary24V_miswire_claim':False,'numeric_Ioff_guarantee_available':False}
  ck(li==exp,'bounded exact device/ordinaryID/route limits, no invented generic Ioff/current/voltage')
  delta=.01+100e-6*65;ih=3.6/(10000*(1-delta))+20e-6;ia=5.5/(4700*(1-delta));s=d['threshold_screens']
  facts={'host_LOW_max_v':.4+ih*10,'host_receiver_LOW_limit_v':.45,'host_receive_LOW_max_v':.6,'host_receive_LOW_limit_v':.81,'field_receive_LOW_max_v':.2+ia*330*(1+delta),'field_receive_LOW_limit_v':.8,'host_rise_to70percent_rc_s':-math.log(.3)*10000*(1+delta)*50e-12,'field_rise_to70percent_rc_s':-math.log(.3)*4700*(1+delta)*400e-12}
  ck(all(math.isclose(s[k],v,rel_tol=1e-12,abs_tol=1e-14) for k,v in facts.items()) and s['rise_screens_are_not_loaded_latency_proof'],'independent actual low and RC screens')
  ck(s['host_LOW_max_v']<.45 and ih<.008 and ia<.006 and s['field_receive_LOW_max_v']<.8 and s['host_receive_LOW_max_v']<.81,'guaranteed VOL corner acceptance, not typical RDS')
  pb=d['power_budget'];ck(pb['IO_3V3_bypass_nominal_uf']==.2 and pb['FREQ_5V_LIMITED_bypass_nominal_uf']==.1 and math.isclose(pb['host_pullup_max_screen_a'],ih) and math.isclose(pb['field_pullup_max_screen_a'],ia),'actual cap/current load accounting')
  ck(pb['TCA_B_max_quiescent_datasheet5V5_a']==.005 and pb['TCA_A_max_quiescent_a']==.001 and pb['TPS3700_IDD_max_table_at5V_a']==.000013 and pb['TPS3700_IO3_reservation_a']==.000018 and pb['no_total_dynamic_qualification'],'reserve does not become an unprovided3.3V datasheet max')
  ck(d['defaults']=={'real_field_window_qualifies_EN':True,'field_unpowered_disabled':True,'either_repeater_supply_zero_high_impedance_primary_claim':True,'unused_SCL_channels_grounded':True,'no_strong_pullup':True,'automatic_motion_rearm':False},'bounded hardware defaults without motion auto rearm')
  ck(set(d['boundaries'])=={'J21001','J21002'} and d['boundaries']['J21001']['pins']=={'1':'IO_3V3','2':'LOGIC_GND','3':'FREQ_5V_LIMITED'} and d['boundaries']['J21002']['pins']=={'1':'FREQ_1WIRE_DATA_HOST','2':'FREQ_MOD_ID_TO_FRONTEND'},'exact existing port and PD3 only, no extra terminal')
  ck(all(not q['physical'] and not q['mpn'] and not q['footprint'] for q in d['boundaries'].values()),'boundary is not fictitious physical connector')
  ck(not any(d[k] for k in ['manufacturing_ready','physical_qualification','firmware_implemented','target_image_compiled']),'source checks not target/physical/manufacture')
  if netlist:
   n=native(netlist);ck(set(n)==set(p)|set(d['boundaries']),'native exact population')
   for ref,q in {**p,**d['boundaries']}.items():ck(n.get(ref)=={k:q[k] for k in ['mpn','footprint','value','pins']},'actual native fullpin/MPN/footprint '+ref)
  if erc:
   e=json.loads(Path(erc).read_text());vs=[v for sheet in e['sheets'] for v in sheet['violations']];ck(not e['ignored_checks'] and len(vs)==2 and all(v['type']=='pin_to_pin' and v['severity']=='warning' for v in vs),'ERC0errors2explicitmanufacturerunused-groundwarnings, no ignored')
   ck({v['items'][0]['description'].split('Pin ')[1].split()[0] for v in vs}=={'2','7'},'exact permitted unused SCL pins only')
  if footprints:
   a,_=footprint_pads(Path(footprints)/'TCA9517A_DGK8_TI.kicad_mod');ck(set(a)=={str(n) for n in range(1,9)},'exact8landpads')
   for n in range(1,9):
    vals=a[str(n)];xy=(-2.2,(n-1)*.65-.975) if n<=4 else (2.2,(8-n)*.65-.975)
    ck(all(math.isclose(v,w,abs_tol=1e-12) for v,w in zip(vals['at']+vals['size'],xy+(1.4,.45))),'exact TI DGKland '+str(n))
 except (KeyError,ValueError,TypeError,OSError,IndexError) as e:errors.append('invalid source/evidence '+str(e))
 return {'ok':not errors,'errors':errors,'physical_footprints':14,'electrical_pads':38,'manufacturing_ready':False,'physical_qualification':False,'target_image_compiled':False}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args();r=validate(json.loads((OUT/'design.json').read_text()),OUT/'netlist.xml',OUT/'erc.json',OUT/'CNC_MB_Identity.pretty')
 if a.write:(OUT/'validation.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r,indent=2));raise SystemExit(not r['ok'])
