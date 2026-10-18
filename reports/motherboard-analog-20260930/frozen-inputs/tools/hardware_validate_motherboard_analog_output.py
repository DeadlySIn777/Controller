"""Independent exact manufacturer pin/rail/default/readback checks, not physical proof."""
import argparse,collections,json,math
from pathlib import Path
from hardware_validate_motherboard_do import native
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_analog_output'
def validate(d,netlist=None,erc=None):
 errors=[]
 def ck(ok,msg):
  if not ok:errors.append(msg)
 try:
  p=d['components'];ck(len(p)==d['fitted_component_count']==143,'143 actual fitted source components');ck(sum(len(q['pins']) for q in p.values())==d['fitted_pad_count']==468,'468 exact electrical pads')
  ck(collections.Counter(q['kind'] for q in p.values())=={'C':56,'R':49,'AND':6,'RELAY':4,'INV':4,'DCDC':2,'LDO':2,'WINDOW':2,'ISO6':2,'DAC':2,'BUFFER':2,'ODINV':2,'OPA':2,'TVS':2,'ISO2':2,'I2CISO':2,'ADC':2},'two independent islands actual inventory')
  ck(not d['manufacturing_ready'] and not d['physical_qualification'] and not d['firmware_implemented'],'native source not manufactured, measured or target compiled')
  ck(d['electrical_limits']=={'AO_channels':2,'AO_span_v':[0,10],'receiver_min_ohm':2000,'target_effective_bits':12,'independent_islands':True,'no_automatic_rearm':True},'frozen AO scope')
  corr=d['contract_correction'];ck(corr['authorised'] and corr['prior_dac']=='DAC80501ZDQFR' and corr['new_dac']=='AD5683RBRMZ-3' and corr['ACC2_gpio']=={'PB3':'AO0_CS_N_HOST','PB4':'AO1_CS_N_HOST'} and corr['I2C1_preserved'],'bounded source correction and approved GPIO additions')
  t=corr['wire_time_only'];ck(t=={'spi_hz':4000000,'two_write_clocks':48,'apply_write_seconds':12e-6,'two_readback_clocks':96,'readback_seconds':24e-6,'combined_seconds':36e-6,'readback_is_not_part_of_20us_apply_allocation':True,'not_full_commit_latency_proof':True},'apply12us and separate readback24us wiretime, no8MHz/full latency claim')
  def resistor(a,b,v):return [q for q in p.values() if q['kind']=='R' and q['pins']=={'1':a,'2':b} and q['resistance_ohm']==v]
  def cap(a,g,nf):return [q for q in p.values() if q['kind']=='C' and q['pins']=={'1':a,'2':g} and math.isclose(q['capacitance_f'],nf*1e-9)]
  def exact(ref,mpn,fp,pins):
   q=p[ref];ck(q['mpn']==mpn and q['footprint']==fp and q['pins']=={str(k):v for k,v in pins.items()},'exact primary fullpin/part '+ref)
  for i,ch in enumerate(d['channels']):
   n=lambda x:f'AO{i}_'+x;g=n('COM');s5=n('5V');s12=n('12V');pg=n('POWER_GOOD_FIELD')
   ck(ch['channel']==i and ch['isolated_return']==g and ch['terminal']==f'AO{i}_OUT' and ch['voltage_span_v']==[0,10] and ch['minimum_receiver_ohm']==2000 and ch['nominal_gain']==4 and ch['reference_nominal_v']==2.5,'channel rating/gain/island')
   ck(ch['clamp_default_closed'] and ch['disconnect_default_open'] and ch['actual_terminal_readback'] and ch['input_register_readback'] and ch['LDAC_LOW_copies_input_to_DAC'] and ch['no_independent_internal_DAC_latch_readout'] and ch['contact_drive_observation_not_contact_proof'] and not ch['physical_qualified'],'truthful zero/default and exact observation boundary')
   exact(ch['power_module_ref'],'TMR 1-2412','Converter_DCDC:Converter_DCDC_TRACO_TMR-1-xxxx_Single_THT',{1:'LOGIC_GND',2:'CORE_24V_PROTECTED',4:s12,6:g})
   exact(ch['regulator_ref'],'TPS7A1650DGNR','CNC_MB_AO:TPS7A16_DGN8_TI',{1:s5,2:None,3:pg,4:g,5:s12,6:None,7:n('PG_DELAY'),8:s12,9:g})
   exact(ch['window_ref'],'TPS3700DDCR','Package_TO_SOT_SMD:SOT-23-6',{1:pg,2:g,3:n('UV_SENSE'),4:n('OV_SENSE'),5:s12,6:pg})
   for a,b,v in [(s12,n('UV_SENSE'),274000),(n('UV_SENSE'),g,10000),(s12,n('OV_SENSE'),316000),(n('OV_SENSE'),g,10000)]:
    rr=resistor(a,b,v);ck(len(rr)==1 and rr[0]['tolerance']==.001 and rr[0]['tcr_ppm_K']==25,'actual precision window divider')
   ck(len(cap(s5,g,22000))==1 and cap(s5,g,22000)[0]['mpn']=='GCM31CR71A226KE02L','LDO real nominal22uF cap, effectiveC not assumed')
   ck(len(cap(n('PG_DELAY'),g,10))==1 and len(resistor(pg,s5,10000))==1,'actual monitored/delayed power-good')
   exact(ch['host_enable_gate_ref'],'SN74LVC1G08DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:f'AO{i}_ENABLE_REQUEST',2:'PWM_ENABLE_LOGIC',3:'LOGIC_GND',4:n('ENABLE_QUALIFIED'),5:'IO_3V3'})
   exact(ch['spi_isolator_ref'],'ISO7761FDWR','CNC_MB_AO:ISO7761_DW16_TI_HV',{1:'IO_3V3',2:'AI_SCLK_HOST',3:'AI_SDI_HOST',4:f'AO{i}_CS_N_HOST',5:n('ENABLE_QUALIFIED'),6:'ACC_CLR_N',7:n('SDO_ISOLATED'),8:'LOGIC_GND',9:g,10:n('DAC_SDO'),11:n('RESET_ISOLATED'),12:n('ENABLE_ISOLATED'),13:n('DAC_CS_N'),14:n('DAC_SDI'),15:n('DAC_SCLK'),16:s5})
   exact(ch['local_enable_gate_ref'],'SN74LVC1G08DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:n('ENABLE_ISOLATED'),2:pg,3:g,4:n('RUN'),5:s5})
   exact(ch['local_reset_gate_ref'],'SN74LVC1G08DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:n('RESET_ISOLATED'),2:pg,3:g,4:n('DAC_RESET_N'),5:s5})
   ck(len(resistor(n('RUN'),g,10000))==len(resistor(n('DAC_RESET_N'),g,10000))==1,'real local OFF/resetLOW biases')
   exact(ch['dac_ref'],'AD5683RBRMZ-3','Package_SO:MSOP-10_3x3mm_P0.5mm',{1:s5,2:n('DAC_RESET_N'),3:n('DAC_SDO'),4:g,5:g,6:n('DAC_SCLK'),7:n('DAC_CS_N'),8:n('DAC_SDI'),9:n('VREF'),10:n('DAC_VOUT')})
   ck(len(cap(n('VREF'),g,10))==1,'actual reference capacitance')
   exact(ch['spi_return_buffer_ref'],'SN74LVC1G125DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:f'AO{i}_CS_N_HOST',2:n('SDO_ISOLATED'),3:'LOGIC_GND',4:'AI_SDO_HOST',5:'IO_3V3'})
   exact(ch['input_clamp_ref'],'TLP4176A(TP,F','CNC_MB_AO:TLP4176A_2.54SOP4_11-5H1S',{1:s5,2:n('CLAMP_LED_K'),3:n('OPA_IN'),4:g})
   exact(ch['output_disconnect_ref'],'TLP3640A(TPL,E','CNC_MB_AO:TLP3640A_SO4_11-3C1',{1:s5,2:n('SERIES_LED_K'),3:n('OUTPUT_PROTECTED'),4:f'AO{i}_OUT'})
   exact(ch['contact_sink_ref'],'SN74LVC1G06DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:None,2:n('RUN'),3:g,4:n('LED_SINK'),5:s5})
   for key in ['CLAMP','SERIES']:ck(len(resistor(n(key+'_LED_K'),n('LED_SINK'),390))==1,'two separate qualified LED branches')
   exact(ch['amplifier_ref'],'OPA197IDBVR','Package_TO_SOT_SMD:SOT-23-5',{1:n('AMP_OUT'),2:g,3:n('OPA_IN'),4:n('FEEDBACK'),5:s12})
   for a,b,v in [(n('DAC_VOUT'),n('OPA_IN'),1000),(n('AMP_OUT'),n('FEEDBACK'),30000),(n('FEEDBACK'),g,10000),(n('AMP_OUT'),n('OUTPUT_PROTECTED'),4.7),(f'AO{i}_OUT',g,10000)]:ck(len(resistor(a,b,v))==1,'actual gain/clamp/output/default path')
   exact(ch['clamp_observer_ref'],'SN74LVC1G14DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:None,2:n('LED_SINK'),3:g,4:n('RUN_OBSERVED'),5:s5})
   exact(ch['health_isolator_ref'],'ISO7720FDWR','CNC_MB_AO:ISO7720_DW16_TI_HV',{1:g,2:None,3:s5,4:pg,5:n('RUN_OBSERVED'),6:None,7:g,8:None,9:'LOGIC_GND',10:None,11:None,12:n('RUN_OBSERVED_HOST'),13:f'AO{i}_POWER_GOOD_HOST',14:'IO_3V3',15:None,16:'LOGIC_GND'})
   exact(ch['clamp_inverter_ref'],'SN74LVC1G14DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:None,2:n('RUN_OBSERVED_HOST'),3:'LOGIC_GND',4:f'AO{i}_CLAMP_ACTIVE',5:'IO_3V3'})
   exact(ch['i2c_isolator_ref'],'ISO1540DR','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',{1:'IO_3V3',2:'AO_I2C_SDA_HOST',3:'AO_I2C_SCL_HOST',4:'LOGIC_GND',5:g,6:n('SCL'),7:n('SDA'),8:s5})
   exact(ch['readback_adc_ref'],'ADS1115IDGSR','CNC_MB_AO:ADS1115_DGS10_TI',{1:g if i==0 else s5,2:None,3:g,4:n('MON_TERMINAL'),5:n('MON_12V'),6:n('MON_5V'),7:n('VREF'),8:s5,9:n('SDA'),10:n('SCL')})
   ck(ch['adc_i2c_address']==hex(0x48+i),'two actual noncolliding readbackADC addresses')
   for key,src in [('TERMINAL',f'AO{i}_OUT'),('12V',s12),('5V',s5)]:
    ck(len(resistor(src,n('MON_'+key),100000))==len(resistor(n('MON_'+key),g,33200))==len(cap(n('MON_'+key),g,10))==1,'actual terminal/rail readback divider '+key)
   for q in p.values():
    if q['kind'] in ['R','C','TVS']:ck(not {g,'LOGIC_GND'}<=set(q['pins'].values()) and not {'AO0_COM','AO1_COM'}<=set(q['pins'].values()),'no accidental return-domain bond')
  ck(len(d['channels'])==2,'two complete AO channels')
  ck(len(resistor('AI_SDO_HOST','LOGIC_GND',100000))==1,'shared SPI return defined when all CS areinactive')
  ck(not resistor('AO_I2C_SCL_HOST','IO_3V3',3300) and not resistor('AO_I2C_SDA_HOST','IO_3V3',3300),'shared I2C pullups not duplicated from ACC')
  pb=d['power_budget'];ck(math.isclose(pb['IO_3V3_bypass_nominal_uf'],1.2) and math.isclose(pb['AO5_LED_both_max_screen_a'],2*5.1/(390*.99)) and pb['AO5_LED_both_max_screen_a']<.032 and pb['AO5_LED_single_min_screen_a']>.005 and pb['AO12_module_rated_a']==.083 and pb['no_dynamic_power_qualification'],'actual bypass and conditional full-LED sink screen')
  ck(all(q['physical'] and q['mpn'] and q['footprint'] for q in p.values()),'no placeholder fitted parts')
  ck(all(not q['physical'] and not q['mpn'] and not q['footprint'] for q in d['boundaries'].values()),'no fake fitted boundary sockets')
  if netlist:
   a=native(netlist);ck(set(a)==set(p)|set(d['boundaries']),'native exact population')
   for ref,q in {**p,**d['boundaries']}.items():ck(a.get(ref)=={k:q[k] for k in ['mpn','footprint','value','pins']},'native fullpin population '+ref)
  if erc:
   e=json.loads(Path(erc).read_text());v=[v for s in e['sheets'] for v in s['violations']];ck(not e['ignored_checks'],'no ignored ERC checks')
   expected={(r,str(pin)) for r,pins in [('U14605',[9]),('U14615',[1,7]),('U14617',[5]),('U14623',[9]),('U14633',[1,7]),('U14635',[5])] for pin in pins};found=set()
   import re
   for x in v:
    m=re.search(r'Symbol (U\d+) Pin (\d+) ',x['items'][0]['description']);ck(x['severity']=='warning' and x['type']=='ground_pin_not_ground' and m is not None,'only documented isolated-COM naming warnings')
    if m:found.add(m.groups())
   ck(len(v)==8 and found==expected,'exact eight unsuppressed isolated AO_COM ground-name warnings')
 except (KeyError,ValueError,TypeError,OSError,IndexError) as e:errors.append('invalid source/evidence: '+str(e))
 return {'ok':not errors,'errors':errors,'physical_footprints':143,'electrical_pads':468,'manufacturing_ready':False,'warnings':['Eight ERC ground-name warnings are deliberate isolated AO_COM return naming; native electrical/power maps prove no LOGIC_GND bond.','Input-register SDO readback plus tiedLOW LDAC is distinct from measured terminal ADC and independent internal-DAC-latch observation.','Target firmware/options/scheduling, accuracy, rail budget and20ms loaded inhibit remain unqualified.']}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args();r=validate(json.loads((OUT/'design.json').read_text()),OUT/'netlist.xml',OUT/'erc.json')
 if a.write:(OUT/'validation.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r,indent=2));raise SystemExit(not r['ok'])
