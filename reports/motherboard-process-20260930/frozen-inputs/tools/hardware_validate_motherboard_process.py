"""Independent primary-pin/default/current checks, not a target or PCB test."""
import argparse,collections,json,math
from pathlib import Path
from hardware_validate_motherboard_do import native
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_process'

def validate(d,netlist=None,erc=None):
 errors=[]
 def ck(ok,msg):
  if not ok:errors.append(msg)
 try:
  p=d['components'];ck(len(p)==d['fitted_component_count']==68,'68 fitted source parts, no placeholders');ck(sum(len(x['pins']) for x in p.values())==d['fitted_pad_count']==216,'216 unique electrical pads')
  ck(collections.Counter(x['kind'] for x in p.values())=={'DFF':2,'AND4':2,'AND1':2,'DIODEPOWER':1,'T45':1,'ODINV':3,'NMOS':2,'CLAMP':2,'LOAD':1,'RELAY':2,'LIMIT':1,'TVS':5,'R':23,'C':21},'exact source inventory')
  ck(not d['manufacturing_ready'] and not d['physical_qualification'] and not d['firmware_implemented'],'source must not claim manufacture/physical/firmware')
  ck(d['electrical_limits']=={'PWM_channels':2,'PWM_source_sink_a':.02,'process_channels':2,'process_contact_v':30,'process_contact_a':.05,'no_automatic_rearm':True},'frozen twoPWM/twofloatingprocess ratings')
  def resistor(a,b,v):return [x for x in p.values() if x['kind']=='R' and x['pins']=={'1':a,'2':b} and x['resistance_ohm']==v]
  def exact(ref,mpn,fp,pins):
   q=p[ref];ck(q['mpn']==mpn and q['footprint']==fp and q['pins']=={str(k):v for k,v in pins.items()},'primary exactpin/part '+ref)
  exact(d['latch_ref'],'SN74LVC1G74DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm',{1:'ACC_IO_ENABLE_STROBE',2:'IO_3V3',3:None,4:'LOGIC_GND',5:'ACC_OUT_EN_LATCH',6:'ACC_CLR_N',7:'IO_3V3',8:'IO_3V3'})
  exact(d['permission_gate_ref'],'SN74LVC08APWR','Package_SO:TSSOP-14_4.4x5mm_P0.65mm',{1:'OUT_PERMIT_ACC',2:'ACC_CONTROLLER_RESET_N',3:'ACC_CLR_N',4:'ACC_OUT_EN_LATCH',5:'ACC_CARD_EN',6:'ACC_READY',7:'LOGIC_GND',8:'PWM_ENABLE_LOGIC',9:'ACC_READY',10:'OUT_PERMIT_ACC',11:'PEN_PERMIT_READY',12:'ACC_READY',13:'PROC_PERMIT',14:'IO_3V3'})
  exact(d['command_gate_ref'],'SN74LVC08APWR','Package_SO:TSSOP-14_4.4x5mm_P0.65mm',{1:'PWM_ENABLE_LOGIC',2:'PWM0_FPGA',3:'PWM0_GATED',4:'PWM_ENABLE_LOGIC',5:'PWM1_FPGA',6:'PWM1_GATED',7:'LOGIC_GND',8:'PEN0_LED_REQUEST',9:'PEN_ENABLE_LOGIC',10:'PEN0_CMD',11:'PEN1_LED_REQUEST',12:'PEN_ENABLE_LOGIC',13:'PEN1_CMD',14:'IO_3V3'})
  exact(d['process_clear_ref'],'SN74LVC1G08DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:'ACC_CLR_N',2:'PROC_PERMIT',3:'LOGIC_GND',4:'PEN_CLR_N',5:'IO_3V3'})
  exact(d['process_latch_ref'],'SN74LVC1G74DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm',{1:'ACC_IO_ENABLE_STROBE',2:'IO_3V3',3:None,4:'LOGIC_GND',5:'PEN_OUT_EN_LATCH',6:'PEN_CLR_N',7:'IO_3V3',8:'IO_3V3'})
  exact(d['process_permission_ref'],'SN74LVC1G08DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:'PEN_OUT_EN_LATCH',2:'PEN_PERMIT_READY',3:'LOGIC_GND',4:'PEN_ENABLE_LOGIC',5:'IO_3V3'})
  exact(d['reverse_feed_ref'],'LM66100DCKR','Package_TO_SOT_SMD:SOT-363_SC-70-6',{1:'MOTION_5V_RAW',2:'LOGIC_GND',3:'PWM_5V_INTERNAL',4:None,5:None,6:'PWM_5V_INTERNAL'})
  exact(d['clamp_gate_ref'],'SN74LVC1G06DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:None,2:'PWM_ENABLE_LOGIC',3:'LOGIC_GND',4:'PWM_CLAMP_GATE',5:'IO_3V3'})
  exact(d['relay_supply_ref'],'TPS22918DBVR','Package_TO_SOT_SMD:SOT-23-6',{1:'PWM_5V_INTERNAL',2:'LOGIC_GND',3:'PEN_ENABLE_LOGIC',4:None,5:'PEN_LED_5V',6:'PEN_LED_5V'})
  for net in ['OUT_PERMIT_ACC','PROC_PERMIT','ACC_CONTROLLER_RESET_N','ACC_IO_ENABLE_STROBE','ACC_CARD_EN','PWM_ENABLE_LOGIC','PEN_ENABLE_LOGIC']:ck(len(resistor(net,'LOGIC_GND',10000))==1,'realOFF bias '+net)
  for net in ['PWM0_FPGA','PWM1_FPGA','PEN0_CMD','PEN1_CMD']:ck(len(resistor(net,'LOGIC_GND',4700))==1,'FPGA unused-user weakpull LOW bias '+net)
  ck(len(resistor('PWM_CLAMP_GATE','PWM_5V_INTERNAL',56000))==1,'hardware clamp defaults ON whenIO3missing')
  ck(len(d['PWM_channels'])==len(d['process_channels'])==2,'bothfrozenpairs populated')
  for i,ch in enumerate(d['PWM_channels']):
   ck(ch['channel']==i and ch['net']==f'PWM{i}' and ch['continuous_source_sink_a']==.02 and ch['noIO3_clamp_ON'] and not ch['physical_response_qualified'],'PWM fieldlimits/evidence')
   exact(ch['driver_ref'],'SN74LVC2T45DCTR','Package_SO:SSOP-8_2.95x2.8mm_P0.65mm',{1:'IO_3V3',2:'PWM0_GATED',3:'PWM1_GATED',4:'LOGIC_GND',5:'IO_3V3',6:'PWM1_DRIVER',7:'PWM0_DRIVER',8:'PWM_5V_INTERNAL'})
   exact(ch['clamp_ref'],'PMV20XNEAR','CNC_MB_Process:PMV20XNEA_SOT23_NXP',{1:'PWM_CLAMP_GATE',2:'LOGIC_GND',3:f'PWM{i}_DRIVER'})
   exact(ch['rail_clamp_ref'],'BAT54S,215','Package_TO_SOT_SMD:SOT-23',{1:'LOGIC_GND',2:'PWM_5V_INTERNAL',3:f'PWM{i}'})
   ck(p[ch['series_ref']]['pins']=={'1':f'PWM{i}_DRIVER','2':f'PWM{i}'} and p[ch['series_ref']]['resistance_ohm']==4.7 and p[ch['series_ref']]['mpn']=='CRCW06034R70FKEA','20mA terminal dropbounded')
   ck(p[ch['pulldown_ref']]['pins']=={'1':f'PWM{i}','2':'LOGIC_GND'} and p[ch['pulldown_ref']]['resistance_ohm']==10000,'PWM terminal defaultLOW')
   ck(p[ch['tvs_ref']]['mpn']=='TPD1E10B06DPYR' and p[ch['tvs_ref']]['bidirectional'] and p[ch['tvs_ref']]['pins']=={'1':f'PWM{i}','2':'LOGIC_GND'},'typed5V primarysuppressor')
   ck(abs(ch['loaded_VOH_min_screen_v']-(3.8-.02*4.7*1.01))<1e-12 and abs(ch['loaded_VOL_max_screen_v']-(.55+.02*4.7*1.01))<1e-12,'loadedlevel screen not ideal5V claim')
   ck(ch['gate_specs_temperature_c']==25 and ch['clamp_gate_pullup_ohm']==56000 and math.isclose(ch['clamp_gate_noIO3_min_screen_v'],4.5-20e-6*56560) and ch['clamp_gate_noIO3_min_screen_v']>2.5 and ch['enabled_sink_max_load_a']<=100e-6,'gatevoltage/offload screenwithactualprimaryconditions')
  for i,ch in enumerate(d['process_channels']):
   ck(ch['channel']==i and ch['contact_v_max']==30 and ch['contact_continuous_a']==.05 and ch['normally_open'] and ch['floating'] and not ch['physical_response_qualified'],'floatingNO processratings')
   exact(ch['relay_ref'],'TLP3640A(TPL,E','CNC_MB_Process:TLP3640A_SO4_11-3C1',{1:'PEN_LED_5V',2:f'PEN{i}_LED_K',3:f'PEN{i}_1',4:f'PEN{i}_2'})
   exact(ch['sink_ref'],'SN74LVC1G06DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:None,2:f'PEN{i}_LED_REQUEST',3:'LOGIC_GND',4:f'PEN{i}_LED_SINK',5:'IO_3V3'})
   ck(p[ch['LED_resistor_ref']]['pins']=={'1':f'PEN{i}_LED_K','2':f'PEN{i}_LED_SINK'} and p[ch['LED_resistor_ref']]['resistance_ohm']==330,'actualLED resistor')
   ck(p[ch['tvs_ref']]['mpn']=='SMBJ33CA-E3/52' and p[ch['tvs_ref']]['pins']=={'1':f'PEN{i}_1','2':f'PEN{i}_2'} and p[ch['tvs_ref']]['bidirectional'],'contactsprotection staysfloating')
   ck(math.isclose(ch['LED_min_screen_a'],(4.5-1.9-.55)/(330*1.01)) and .003<ch['LED_min_screen_a']<ch['LED_max_conservative_a']<.02,'LEDprimary3mA trigger/20mAmax conditional screen')
  a=d['aux_supply'];exact(a['limiter_ref'],'TPS1H000AQDGNRQ1','CNC_MB_Process:TPS1H000_DGN8_TI',{1:'IO_3V3',2:'IO_3V3',3:'PWM_AUX_FAULT_N',4:'PWM_AUX_ILIM',5:'PWM_AUX_DELAY',6:'LOGIC_GND',7:'PWM_5V_AUX',8:'PWM_5V_INTERNAL',9:'LOGIC_GND'})
  q=p[a['ilim_ref']];ck(q['mpn']=='TNPW06039K53BEEA' and q['pins']=={'1':'PWM_AUX_ILIM','2':'LOGIC_GND'} and q['resistance_ohm']==9530 and q['tolerance']==.001 and q['tcr_ppm_K']==25,'exactprecision50mA candidate resistor')
  lo=9530*.999*.99625;hi=9530*1.001*1.00375
  ck(a['current_limit_target_a']==.05 and math.isclose(a['programmed_nominal_a'],480/9530) and a['programmed_low_resistor_allowance_a']>.05 and math.isclose(a['overload_min_screen_a'],.8*480/hi) and math.isclose(a['overload_max_screen_a'],1.2*480/lo),'published50mA accuracypoint conditions/tolerance budget')
  ck(a['not_a_guaranteed_50mA_maximum'] and a['latchoff'] and not a['delay_physical_qualified'] and '1.5x' in a['accuracy_condition'],'currentlimitbounds andtypicaldelayevidence mustnotbehidden')
  ck(any(x['kind']=='C' and x['pins']=={'1':'PWM_AUX_DELAY','2':'LOGIC_GND'} and math.isclose(x['capacitance_f'],10e-9) for x in p.values()),'actual latchoff C notholding/auto retry')
  ck(len(resistor('PWM_AUX_FAULT_N','IO_3V3',10000))==1,'actual fault telemetry pullup')
  for q in d['boundaries'].values():ck(not q['physical'] and not q['footprint'] and not q['mpn'],'no invented connectors/cards')
  for q in p.values():
   if q['kind']=='C':ck(q['pins']['2']=='LOGIC_GND' and q['voltage_rating_v']>=50,'capacitorratedforactualrail')
   ck(q['physical'] and bool(q['mpn']) and bool(q['footprint']),'real fittedsourcepart')
  if netlist:
   actual=native(netlist);ck(set(actual)==set(p)|set(d['boundaries']),'nativeXML population')
   for ref,q in {**p,**d['boundaries']}.items():ck(actual.get(ref)=={k:q[k] for k in ['mpn','footprint','value','pins']},'nativeXML exactpin/value '+ref)
  if erc:
   e=json.loads(Path(erc).read_text());ck(not e['ignored_checks'] and not any(s['violations'] for s in e['sheets']),'ERCzeroerrors/warnings, noignoredchecks')
 except (KeyError,ValueError,TypeError,OSError,IndexError) as e:errors.append('invalid source/evidence: '+str(e))
 return {'ok':not errors,'errors':errors,'warnings':['Primary current limits are conditional bounds, not a guaranteed50mAmaximum or assembledmeasurement.','PWMloadedlevels/partial-power/clampcontention/ESD andwhole20msresponse remainphysicalqualification.','FourthACC/IOL1MCU/firmware/reset/qualified parentrails andterminalintegration remain.'],'physical_footprints':68,'electrical_pads':216,'manufacturing_ready':False}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args();r=validate(json.loads((OUT/'design.json').read_text()),OUT/'netlist.xml',OUT/'erc.json')
 if a.write:(OUT/'validation.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r,indent=2));raise SystemExit(not r['ok'])
