"""Independent manufacturer pin/default/rail/current checks; no physical qualification claim."""
import argparse,collections,json,math
from pathlib import Path
from hardware_validate_motherboard_do import native
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_analog_input'

def validate(d,netlist=None,erc=None):
 errors=[]
 def ck(ok,msg):
  if not ok:errors.append(msg)
 try:
  p=d['components'];b=d['blocks'];g='AI_AGND';s5='AI_5V';s15='AI_15V';s24='AI_24V_RAW';pg='AI_POWER_GOOD_FIELD'
  ck(len(p)==d['fitted_component_count']==165,'165 real fitted parts, obsolete minimum-load and four AI5 dividers retired, precision LDO and true minimumload real')
  ck(sum(len(q['pins']) for q in p.values())==d['fitted_pad_count']==554,'554 exact electrical pads including actual seven-pin converters and LDO')
  ck(collections.Counter(q['kind'] for q in p.values())=={'DCDC':2,'DCDC24':1,'C':57,'R':67,'WINDOW':2,'WINDOW5':1,'LDO5':1,'ISO6':1,'AND':5,'BUFFER':1,'I2CISO':1,'EXP':1,'REF':1,'OPA4':1,'TBU':4,'INA':4,'RELAY':4,'ODINV':4,'ADC38':1,'EFUSE':1,'OPA':1,'LIMIT':1,'ADC':1,'ISO2':1,'INV':1},'one actual differential AI group inventory')
  ck(not d['manufacturing_ready'] and not d['physical_qualification'] and not d['firmware_implemented'],'source not manufactured/physical/firmware proof')
  def exact(ref,mpn,fp,pins):
   q=p[ref];ck(q['mpn']==mpn and q['footprint']==fp and q['pins']=={str(k):v for k,v in pins.items()},'exact primary part/footprint/fullpin '+ref)
  def rr(a,z,v):return [q for q in p.values() if q['kind']=='R' and q['pins']=={'1':a,'2':z} and q['resistance_ohm']==v]
  def cc(a,z,nf):return [q for q in p.values() if q['kind']=='C' and q['pins']=={'1':a,'2':z} and math.isclose(q['capacitance_f'],nf*1e-9)]
  for key,mpn,rail in [('dc5','TMR 4-2412WI','AI_5V_PREREG_12V'),('dc15','TMR 4-2413WI',s15),('dc24','TMR 4-2415WI',s24)]:
   exact(b[key],mpn,'CNC_MB_AI:TMR4WI_SIP8_Traco',{1:'LOGIC_GND',2:'CORE_24V_PROTECTED',3:None,5:None,6:rail,7:g,8:None})
  ck(b['dc24_bleed'] is None and 'R14701' not in p and not rr(s24,g,787),'no unnecessary minimum-load bleed; all downstream references preserved')
  exact(b['precision_ldo'],'TPS7A2650DRVR','CNC_MB_AI:TPS7A26_DRV6_TI',{1:s5,2:g,3:pg,4:'AI_5V_PREREG_12V',5:g,6:'AI_5V_PREREG_12V',7:g})
  exact(b['windows'][0],'TPS3702CX50DDCR','Package_TO_SOT_SMD:SOT-23-6',{1:pg,2:g,3:s5,4:s5,5:s5,6:pg})
  ck(all(r not in p for r in ['R14702','R14703','R14704','R14705']),'factory threshold removes only four dividers, stable later references')
  ck(len(cc(s5,g,2200))==1 and len(cc('AI_5V_PREREG_12V',g,2200))==1,'real LDO input and output storage, effective capacitance remains qualified')
  ck(len(rr(s5,g,4700))==1 and 4.92/(4700*(1+.01+65*.0001))>.001,'real>=1mA minimum LDO load including resistor tolerance/TCR')
  for ref,rail,lo,hi,vmin,vmax in zip(b['windows'][1:],[s15,s24],[332000,549000],[412000,649000],[14.39,23.048],[15.61,24.952]):
   tag={s5:'5',s15:'15',s24:'24'}[rail];uv='AI_'+tag+'_UV';ov='AI_'+tag+'_OV'
   exact(ref,'TPS3700DDCR','Package_TO_SOT_SMD:SOT-23-6',{1:pg,2:g,3:uv,4:ov,5:s5,6:pg})
   for a,z,v in [(rail,uv,lo),(uv,g,10000),(rail,ov,hi),(ov,g,10000)]:
    x=rr(a,z,v);ck(len(x)==1 and x[0]['tolerance']==.001 and x[0]['tcr_ppm_K']==25,'actual rail precision divider')
   eps=.001+65*25e-6
   uv_release_max=.404*(1+lo*(1+eps)/(10000*(1-eps)))+25e-9*lo*(1+eps)
   ov_release_min=.387*(1+hi*(1-eps)/(10000*(1+eps)))-15e-9*hi*(1+eps)
   ck(uv_release_max<vmin and ov_release_min>vmax,'coarse health window admits exact new converter static source corners '+rail)
  ck(len(rr(pg,s5,10000))==1,'PG actual open-drain observation')
  exact(b['spi_isolator'],'ISO7761FDWR','CNC_MB_AI:ISO7761_DW16_TI_HV',{1:'IO_3V3',2:'AI_SCLK_HOST',3:'AI_SDI_HOST',4:'AI_CS_N_HOST',5:'ACC_CLR_N',6:'LOGIC_GND',7:'AI_SDO_ISOLATED',8:'LOGIC_GND',9:g,10:'AI_ADC_SDO',11:None,12:'AI_CLEAR_ISOLATED',13:'AI_ADC_CS_N',14:'AI_ADC_SDI',15:'AI_ADC_SCLK',16:s5})
  exact(b['reset_gate'],'SN74LVC1G08DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:'AI_CLEAR_ISOLATED',2:pg,3:g,4:'AI_RESET_N',5:s5})
  ck(len(rr('AI_RESET_N',g,10000))==len(rr('AI_ADC_CS_N',s5,10000))==1,'real resetLOW/selectinactive defaults')
  exact(b['return_buffer'],'SN74LVC1G125DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:'AI_CS_N_HOST',2:'AI_SDO_ISOLATED',3:'LOGIC_GND',4:'AI_SDO_HOST',5:'IO_3V3'})
  exact(b['i2c_isolator'],'ISO1540DR','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',{1:'IO_3V3',2:'AO_I2C_SDA_HOST',3:'AO_I2C_SCL_HOST',4:'LOGIC_GND',5:g,6:'AI_I2C_SCL',7:'AI_I2C_SDA',8:s5})
  exact(b['mode_expander'],'TCA9534PWR','Package_SO:TSSOP-16_4.4x5mm_P0.65mm',{1:g,2:g,3:g,4:'AI0_CURRENT_MODE',5:'AI1_CURRENT_MODE',6:'AI2_CURRENT_MODE',7:'AI3_CURRENT_MODE',8:g,9:pg,10:'AI_SENSOR_FAULT_N_FIELD',11:'AI_ADC_ALARM',12:None,13:None,14:'AI_I2C_SCL',15:'AI_I2C_SDA',16:s5})
  exact(b['reference'],'REF5025AIDR','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',{1:None,2:s5,3:None,4:g,5:'AI_REF_NR',6:'AI_REF_2V5',7:None,8:None})
  ck(len(rr('AI_REF_2V5','AI_REF_CAP',1.2))==len(cc('AI_REF_CAP',g,10000))==1,'actual10uF1.2ohm cap branch notreference series impedance')
  ap={4:s15,11:g};ck(len(d['channels'])==4,'four full AI channels')
  for i,ch in enumerate(d['channels']):
   a=f'AI{i}_';tp=a+'P';tn=a+'N';prot=a+'P_PROTECTED';bottom=a+'BURDEN_BOTTOM';mode=a+'CURRENT_MODE';run=a+'CURRENT_QUALIFIED';sink=a+'LED_K'
   ck(ch['channel']==i and ch['terminal_p']==tp and ch['terminal_n']==tn and ch['differential_v']==[0,10] and ch['nominal_offset_v']==2.5 and ch['nominal_scale']==.5 and ch['nominal_burden_ohm']==250 and ch['mode_defaults_voltage'] and ch['protector_resistance_excluded_from_current_sense'] and not ch['physical_qualified'],'scope/default and actual differential sensing')
   exact(ch['protector_ref'],'TBU-CA025-050-WH','CNC_MB_AI:TBU_CA_6.5x4_Bourns',{1:tp,2:None,3:prot})
   exact(ch['ina_ref'],'INA149AIDR','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',{1:'AI_REF_2V5',2:tn,3:prot,4:g,5:'AI_REF_2V5',6:a+'DIFF_SHIFTED',7:s15,8:None})
   ck(len(ch['burden_resistors'])==4,'four parallel powerburdens')
   for ref in ch['burden_resistors']:
    q=p[ref];ck(q['mpn']=='PHP01206E1001BST5' and q['footprint']=='CNC_MB_AI:PHP1206_Vishay' and q['pins']=={'1':prot,'2':bottom} and q['resistance_ohm']==1000 and q['tolerance']==.001 and q['power_rating_w']==1,'actual switched250ohm1Wbank')
   exact(ch['relay_ref'],'TLP3640A(TPL,E','CNC_MB_AI:TLP3640A_SO4_11-3C1',{1:s5,2:sink,3:bottom,4:tn})
   exact(ch['mode_gate_ref'],'SN74LVC1G08DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:mode,2:'AI_RESET_N',3:g,4:run,5:s5})
   exact(ch['led_sink_ref'],'SN74LVC1G06DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:None,2:run,3:g,4:a+'LED_SINK',5:s5})
   ck(len(rr(mode,g,10000))==len(rr(sink,a+'LED_SINK',390))==1,'real defaultvoltage LEDcontrol')
   for src,dst,v in [(a+'DIFF_SHIFTED',a+'SCALED',10000),(a+'SCALED',g,10000),(a+'BUFFERED',a+'ADC_IN',47)]:ck(len(rr(src,dst,v))==1,'actual attenuation/buffer/filter')
   ck(len(cc(a+'ADC_IN',g,2.2))==1,'real HFfilter')
   op,minus,plus=[(1,2,3),(7,6,5),(8,9,10),(14,13,12)][i];ck(ch['buffer_pins']==[op,minus,plus],'quad exact channel pinassignment');ap.update({op:a+'BUFFERED',minus:a+'BUFFERED',plus:a+'SCALED'})
  exact(b['quad_buffer'],'OPA4197IPWR','Package_SO:TSSOP-14_4.4x5mm_P0.65mm',ap)
  exact(b['adc'],'ADS8684AIDBTR','CNC_MB_AI:ADS8684A_DBT38_TI',{1:'AI_ADC_SDI',2:'AI_RESET_N',3:g,4:g,5:'AI_ADC_REFIO',6:g,7:'AI_ADC_REFCAP',8:g,9:s5,10:'AI_REF_2V5',11:g,12:None,13:None,14:None,15:None,16:'AI0_ADC_IN',17:g,18:'AI1_ADC_IN',19:g,20:g,21:'AI2_ADC_IN',22:g,23:'AI3_ADC_IN',24:None,25:None,26:None,27:None,28:g,29:g,30:s5,31:g,32:g,33:g,34:s5,35:'AI_ADC_ALARM',36:'AI_ADC_SDO',37:'AI_ADC_SCLK',38:'AI_ADC_CS_N'})
  for node in ['AI_ADC_REFIO','AI_ADC_REFCAP']:ck(len(cc(node,g,22000))==len(cc(node,g,1000))==1,'actual SAR reference capacitance')
  exact(b['sensor_efuse'],'MAX17612CATB+T','CNC_MB_AI:MAX17612_T1033_ADI',{1:s24,2:None,3:None,4:'AI_SENSOR_CLMODE',5:s5,6:'AI_SENSOR_FAULT_N_FIELD',7:'AI_SENSOR_FAULT_N_FIELD',8:'AI_SENSOR_SETI',9:g,10:'AI_SENS_24V',11:g})
  for a,z,v in [('AI_SENSOR_CLMODE',g,150000),('AI_SENSOR_SETI',g,3240),(s5,g,10000),('AI_SENSOR_FAULT_N_FIELD',s5,10000),('AI_SENS_24V',g,100000)]:ck(len(rr(a,z,v))==1,'actual sensor mode/current/EN/fault/bleed')
  exact(b['reference_amplifier'],'OPA197IDBVR','Package_TO_SOT_SMD:SOT-23-5',{1:'AI_REF_DRIVE',2:g,3:'AI_REF_2V5',4:'AI_REF_FB',5:s15})
  exact(b['reference_limiter'],'LT3092IST#PBF','Package_TO_SOT_SMD:SOT-223-3_TabPin2',{1:'AI_REF_SET',2:'AI_REF_LIMIT_OUT',3:'AI_REF_DRIVE'})
  for a,z,v in [('AI_REF_10V','AI_REF_FB',30000),('AI_REF_FB',g,10000),('AI_REF_SET','AI_REF_10V',93100),('AI_REF_LIMIT_OUT','AI_REF_10V',100),('AI_REF_10V',g,10000)]:ck(len(rr(a,z,v))==1,'actual regulated10V terminal-after-limiter and minimumload')
  exact(b['diagnostic_adc'],'ADS1115IDGSR','CNC_MB_AI:ADS1115_DGS10_TI',{1:'AI_I2C_SDA',2:None,3:g,4:'AI_MON_REF10',5:'AI_MON_SENS24',6:'AI_SENSOR_SETI',7:'AI_MON_15V',8:s5,9:'AI_I2C_SDA',10:'AI_I2C_SCL'})
  ck(d['diagnostic_i2c_address']=='0x4a','ADS1115address0x4AactualSDAstrap')
  for src,dst,up,down in [('AI_REF_10V','AI_MON_REF10',100000,33200),('AI_SENS_24V','AI_MON_SENS24',120000,20000),(s15,'AI_MON_15V',100000,33200)]:ck(len(rr(src,dst,up))==len(rr(dst,g,down))==len(cc(dst,g,10))==1,'actualnode diagnostic readback '+src)
  exact(b['health_isolator'],'ISO7720FDWR','CNC_MB_AI:ISO7720_DW16_TI_HV',{1:g,2:None,3:s5,4:pg,5:'AI_SENSOR_FAULT_N_FIELD',6:None,7:g,8:None,9:'LOGIC_GND',10:None,11:None,12:'AI_SENSOR_HEALTH_HOST',13:'AI_POWER_GOOD_HOST',14:'IO_3V3',15:None,16:'LOGIC_GND'})
  exact(b['fault_inverter'],'SN74LVC1G14DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:None,2:'AI_SENSOR_HEALTH_HOST',3:'LOGIC_GND',4:'AI_SENSOR_FAULT_HOST',5:'IO_3V3'})
  pb=d['power_budget'];smin=300/3240*.95/1.0035;smax=300/3240*1.05/.9965
  ck(math.isclose(pb['sensor_static_limit_min_a'],smin) and math.isclose(pb['sensor_static_limit_max_a'],smax) and smax<.1,'full-corner sensor limit with correct kOhm/Ohm units')
  ck(pb['sensor_usable_a']==.087 and .087+pb['sensor_downstream_bleed_max_a']+pb['sensor_readback_load_max_a']<smin,'87mAexternalafter actual bleed/readback allocation')
  ck(pb['AI24_minload_min_a']==0 and pb['AI24_minimumload_a']==0 and not pb['minimumload_required'] and pb['AI24_max_draw_screen_a']<pb['AI24_module_rated_a']==.166,'no minimum load, actual protected-sensor draw below166mA converter rating')
  fix=d['converter_correction'];ck(fix['input_range_v']==[9,36] and fix['no_minimum_load'] and fix['no_field_rating_increase'] and fix['retired_reference']=='R14701' and fix['input_max_not_specified'] and fix['primary_pdf_sha256']=='37a99e96859378fce90bb56e3339af101f12519802955ee59bed03b1642d0c53','bounded primary-backed18V input correction, not typical-to-maximum assertion')
  ac=d['ai5_accuracy_correction'];ck(ac['regulator_static_screen_v']==[4.92,5.08] and ac['adc_accuracy_supply_v']==[4.75,5.25] and ac['sense_Kelvin_required'] and ac['monitor_propagation_not_instantaneous'],'bounded static AI5 source correction with real Kelvin/transient gates')
  ck(math.isclose(ac['UV_falling_min_v'],4.8*.991) and ac['UV_falling_min_v']>4.75 and math.isclose(ac['UV_release_max_v'],4.8*(1.009+.008)) and ac['UV_release_max_v']<4.92,'factory UV guaranteed bound and hysteresis admit regulator')
  ck(math.isclose(ac['OV_rising_max_v'],5.2*1.009) and ac['OV_rising_max_v']<5.25 and math.isclose(ac['OV_release_min_v'],5.2*(.991-.008)) and ac['OV_release_min_v']>5.08,'factory OV guaranteed bound and hysteresis admit regulator')
  ck(.009<pb['AI_REF_max_limit_a']<.01 and pb['AI_REF_min_limit_a']-.0014>=pb['AI_REF_usable_a']==.0076 and pb['AI_REF_minimum_load_a']>.0005,'<=10mAcap and7.6mAexternalafterrealminimumload')
  ck(math.isclose(pb['IO_3V3_bypass_nominal_uf'],.5),'actual IO3 .5uFbypass')
  ck(d['electrical_limits']['sensor_rated_a']==.087 and d['electrical_limits']['sensor_static_ceiling_a']==.1 and d['electrical_limits']['reference_static_ceiling_a']==.01,'actualcaps not nominalmarketing')
  for q in p.values():
   ck(q['physical'] and q['mpn'] and q['footprint'],'no placeholder fitted parts')
   if q['kind'] in ['R','C']:ck(not {g,'LOGIC_GND'}<=set(q['pins'].values()),'no return-domain bond')
  ck(all(not q['physical'] and not q['footprint'] and not q['mpn'] for q in d['boundaries'].values()),'boundary symbols notfakephysicalconnectors')
  ck(not rr('AO_I2C_SDA_HOST','IO_3V3',3300) and not rr('AO_I2C_SCL_HOST','IO_3V3',3300),'no duplicate hostpullups')
  if netlist:
   n=native(netlist);ck(set(n)==set(p)|set(d['boundaries']),'native exact population')
   for ref,q in {**p,**d['boundaries']}.items():ck(n.get(ref)=={k:q[k] for k in ['mpn','footprint','value','pins']},'native fullpin/model agreement '+ref)
  if erc:
   e=json.loads(Path(erc).read_text());v=[v for s in e['sheets'] for v in s['violations']];ck(not v and not e['ignored_checks'],'nativeERCzeroerrors/zero warnings/noignored')
 except (KeyError,ValueError,TypeError,OSError,IndexError) as e:errors.append('invalid source/evidence: '+str(e))
 return {'ok':not errors,'errors':errors,'physical_footprints':165,'electrical_pads':554,'manufacturing_ready':False,'physical_qualification':False}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args();r=validate(json.loads((OUT/'design.json').read_text()),OUT/'netlist.xml',OUT/'erc.json')
 if a.write:(OUT/'validation.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r,indent=2));raise SystemExit(not r['ok'])
