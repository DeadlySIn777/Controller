"""Actual bounded ordinary 5 V, one-GPIO identity port; no target execution claim."""
from __future__ import annotations
import csv,json,uuid,shutil,math
from pathlib import Path
from hardware_build_assembly import parse,dump
from hardware_build_tx_schematic import symbol,effects,quote
from hardware_build_motherboard_analog_output import KINDS as SHARED
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_identity_io'
NS=uuid.UUID('c6dc398e-6ce1-4f25-a4c7-1394273f36ed')
KINDS={k:SHARED[k].copy() for k in ['WINDOW','R','C','TVS','PWR_FLAG']}
KINDS['REPEATER']={1:('VCCA','power_in'),2:('SCLA_UNUSED','bidirectional'),3:('SDAA','bidirectional'),4:('GND','power_in'),5:('EN','input'),6:('SDAB','bidirectional'),7:('SCLB_UNUSED','bidirectional'),8:('VCCB','power_in')}
MPNS={'REPEATER':('TCA9517ADGKR','CNC_MB_Identity:TCA9517A_DGK8_TI'),'WINDOW':('TPS3700DDCR','Package_TO_SOT_SMD:SOT-23-6'),'TVS':('TPD1E10B06DPYR','CNC_MB_Identity:TPD1E10B06_DPY2_TI')}

def description():
 p={};bounds={};u=r=c=21000;b={}
 def ic(kind,pins,role):
  nonlocal u
  u+=1;ref=('D' if kind=='TVS' else 'U')+str(u);mpn,fp=MPNS[kind];p[ref]={'kind':kind,'mpn':mpn,'value':mpn,'footprint':fp,'physical':True,'pins':{str(k):v for k,v in pins.items()},'role':role};return ref
 def res(a,z,v,role,precision=False):
  nonlocal r
  r+=1;ref=f'R{r}';codes={330:'330R',4700:'4K70',10000:'10K0',107000:'107K',123000:'123K'}
  mpn=('TNPW0603' if precision else 'CRCW0603')+codes[v]+('BEEA' if precision else 'FKEA')
  p[ref]={'kind':'R','mpn':mpn,'value':f'{v}R'+('0.1%' if precision else '1%'),'footprint':'Resistor_SMD:R_0603_1608Metric','physical':True,'pins':{'1':a,'2':z},'resistance_ohm':v,'tolerance':.001 if precision else .01,'tcr_ppm_K':25 if precision else 100,'power_rating_w':.1,'role':role};return ref
 def cap(a,z,role):
  nonlocal c
  c+=1;ref=f'C{c}';p[ref]={'kind':'C','mpn':'GRM188R72A104KA35D','value':'100nF100V','footprint':'Capacitor_SMD:C_0603_1608Metric','physical':True,'pins':{'1':a,'2':z},'capacitance_f':1e-7,'voltage_rating_v':100,'role':role};return ref
 def bd(ref,nets,role):bounds[ref]={'kind':'Boundary'+str(len(nets)),'mpn':'','value':'PARENT: '+role,'footprint':'','physical':False,'pins':{str(i+1):n for i,n in enumerate(nets)},'role':role}
 b['repeater']=ic('REPEATER',{1:'FREQ_5V_LIMITED',2:'LOGIC_GND',3:'FREQ_ID_A_PROTECTED',4:'LOGIC_GND',5:'FREQ_ID_POWER_GOOD_LOCAL',6:'FREQ_1WIRE_DATA_HOST',7:'LOGIC_GND',8:'IO_3V3'},'exact A variant .45V B contention threshold; A is field5V/B is host3.3V; both unused SCL pins grounded per TI Table4-1')
 cap('FREQ_5V_LIMITED','LOGIC_GND','repeater field-reference bypass');cap('IO_3V3','LOGIC_GND','repeater own B logic supply bypass')
 b['host_pullup']=res('FREQ_1WIRE_DATA_HOST','IO_3V3',10000,'actual3.3V open-drain host bias, no added series resistance in narrow .45V VILC path')
 b['field_pullup']=res('FREQ_MOD_ID_TO_FRONTEND','FREQ_5V_LIMITED',4700,'actual5V ordinary ID pull-up; no strong/parasitic write-power function')
 b['field_series']=res('FREQ_MOD_ID_TO_FRONTEND','FREQ_ID_A_PROTECTED',330,'bounded series current/ESD energy resistance; source low/rise screens include actual voltage drop')
 b['tvs']=ic('TVS',{1:'FREQ_MOD_ID_TO_FRONTEND',2:'LOGIC_GND'},'actual5.5V stand-off bidirectional ESD at existing terminal;10Vmax@1A is not arbitrary24V static protection')
 b['window']=ic('WINDOW',{1:'FREQ_ID_POWER_GOOD_LOCAL',2:'LOGIC_GND',3:'FREQ_ID_FIELD_UV',4:'FREQ_ID_FIELD_OV',5:'IO_3V3',6:'FREQ_ID_POWER_GOOD_LOCAL'},'real IO3-powered window sees field5V missing even before field rail rises; actual open-drain outputs wireAND drive repeater EN')
 cap('IO_3V3','LOGIC_GND','actual fieldrail window bypass')
 b['window_pullup']=res('FREQ_ID_POWER_GOOD_LOCAL','IO_3V3',10000,'actual monitored rail good, not synthetic GPIO; TPS3700 sinks actual low on undervoltage/overvoltage')
 for a,z,v in [('FREQ_5V_LIMITED','FREQ_ID_FIELD_UV',107000),('FREQ_ID_FIELD_UV','LOGIC_GND',10000),('FREQ_5V_LIMITED','FREQ_ID_FIELD_OV',123000),('FREQ_ID_FIELD_OV','LOGIC_GND',10000)]:res(a,z,v,'actual .1%25ppm rail-window divider, nominal4.68/5.32V',True)
 bd('J21001',['IO_3V3','LOGIC_GND','FREQ_5V_LIMITED'],'actual parent protectedfrequency supply, sharedlogicreturn and IO3')
 bd('J21002',['FREQ_1WIRE_DATA_HOST','FREQ_MOD_ID_TO_FRONTEND'],'ACC PD3 singleGPIO to existing XF.7 identity terminal; no new external connector')
 delta=.01+100e-6*65;host_i=3.6/(10000*(1-delta))+20e-6;field_i=5.5/(4700*(1-delta))
 limits={'temperature_c':[-40,85],'field_terminal_operating_v':[0,5.5],'IO_3V3_min_for_threshold_screen_v':2.7,'IO_3V3_max_v':3.6,'ordinary_ID_VIL_max_v':.8,'ordinary_ID_VOL_max_v':.4,'TCA_B_VILC_max_v':.45,'TCA_B_VOL_max_v':.6,'TCA_A_VOL_max_at6mA_v':.2,'STM32_PD3_VOL_max_at8mA_v':.4,'host_trace_plus_return_resistance_max_ohm':10,'host_total_capacitance_candidate_pf':50,'field_total_capacitance_candidate_pf':400,'standard_speed_only':True,'parasitic_write_power_supported':False,'arbitrary24V_miswire_claim':False,'numeric_Ioff_guarantee_available':False}
 return {'schema_version':1,'revision':'motherboard-identity-io-r0.1','status':'actual_source_candidate','components':p,'boundaries':bounds,'blocks':b,'fitted_component_count':len(p),'fitted_pad_count':sum(len(q['pins']) for q in p.values()),'manufacturing_ready':False,'physical_qualification':False,'firmware_implemented':False,'target_image_compiled':False,'limits':limits,'power_budget':{'IO_3V3_bypass_nominal_uf':.2,'FREQ_5V_LIMITED_bypass_nominal_uf':.1,'TCA_B_max_quiescent_datasheet5V5_a':.005,'TCA_A_max_quiescent_a':.001,'TPS3700_IDD_max_table_at5V_a':.000013,'TPS3700_IO3_reservation_a':.000018,'host_pullup_max_screen_a':host_i,'field_pullup_max_screen_a':field_i,'field_window_dividers_max_screen_a':5.5/(117000*(1-.002625))+5.5/(133000*(1-.002625)),'no_total_dynamic_qualification':True},'threshold_screens':{'host_LOW_max_v':.4+host_i*10,'host_receiver_LOW_limit_v':.45,'host_receive_LOW_max_v':.6,'host_receive_LOW_limit_v':.3*2.7,'field_receive_LOW_max_v':.2+field_i*330*(1+delta),'field_receive_LOW_limit_v':.8,'host_rise_to70percent_rc_s':-math.log(.3)*10000*(1+delta)*50e-12,'field_rise_to70percent_rc_s':-math.log(.3)*4700*(1+delta)*400e-12,'rise_screens_are_not_loaded_latency_proof':True},'defaults':{'real_field_window_qualifies_EN':True,'field_unpowered_disabled':True,'either_repeater_supply_zero_high_impedance_primary_claim':True,'unused_SCL_channels_grounded':True,'no_strong_pullup':True,'automatic_motion_rearm':False},'open_gates':['ACC PD3 open-drain one-wire firmware, readonly identity/CRC/freshness and disconnect/reconnect handling remain target uncompiled. No supported ordinary ID SKU has been qualified; parasitic write power is absent.','TI specifies highimpedance IO when either supply0 and5.5Vtolerance unpowered; no numeric fulltemperature Ioff limit is provided. Leakage, partial ramps, TPS3700 power-off input injection, its450usmaximumstartup/undefinedPG interval and rail enable/disable transitions require nativeboard/physical proof. No safe health is inferred from a disconnected ID.','Guaranteed .45V VILC uses exact TCA9517A and STM32G031 .4V VOL@8mA/VDD>=2.7, with10ohm total PCB/return allocation and actual low pullupcurrent. MCU aggregate80mAIO/100mAVSS absolute limits are not allowable normal targets; groundnoise, route resistance, clock/OS mode and temperature must be qualified; do not substitute a .4V-contention repeater or extra hostseries resistor.','The existing field terminal is bounded ordinary0..5.5V only. TPD10Vmaxclamp@1A and330ohm do not qualify arbitrary24V miswire, boardESD or allsurge. Fastclamp overshoot, faultenergy and return/chassis geometry require tests.','400pFfield/50pFhost are candidate totalcapacitance ceilings including cable/device/PCB. RC screens exclude loaded repeater delay; actualstandard-speed slot/sample/presence timing and pullup/loading require target+physical proof. EN mustchange only idle for accepted IDs; faults duringtraffic mustinvalidate/restart discovery.','One custom motherboard only: parent owns existing protectedFREQ5 power/currentcap, actualXF.7terminal and shield. This source does not introduce another external terminal, daughterboard or fieldpower converter.']}

def footprints(out):
 lib=out/'CNC_MB_Identity.pretty';lib.mkdir(exist_ok=True)
 shutil.copyfile(ROOT/'hardware/motherboard_operator/CNC_MB_Operator.pretty/TPD1E10B06_DPY2_TI.kicad_mod',lib/'TPD1E10B06_DPY2_TI.kicad_mod')
 raw='(footprint "TCA9517A_DGK8_TI"(version 20241229)(generator "controller_hardware")(layer "F.Cu")(descr "TI DGK0008A4214862/A04/2023 exact land: eight1.4x.45 copper pads atx+-2.2,pitch.65; body3x3. Exact copper/stencil roundedR.05 geometry, assembly tolerances still require PCBWay review.")(attr smd)(property "Reference" "REF**"(at 0 -2.8 0)(layer "F.SilkS")'+effects(.7)+')(property "Value" "TCA9517A_DGK8_TI"(at 0 2.8 0)(layer "F.Fab")'+effects(.7)+')(fp_rect(start -1.5 -1.5)(end 1.5 1.5)(stroke(width .1)(type default))(layer "F.Fab"))(fp_rect(start -3.2 -1.8)(end 3.2 1.8)(stroke(width .05)(type default))(layer "F.CrtYd"))(fp_text user "1"(at -3.15 -2.1 0)(layer "F.SilkS")'+effects(.6)+')'
 for n in range(1,9):
  x=-2.2 if n<=4 else 2.2;y=(n-1)*.65-.975 if n<=4 else (8-n)*.65-.975
  raw+=f'(pad "{n}" smd roundrect(at {x} {y})(size 1.4 .45)(layers "F.Cu" "F.Paste" "F.Mask")(roundrect_rratio .111111111111))'
 (lib/'TCA9517A_DGK8_TI.kicad_mod').write_text(dump(parse(raw+')'))+'\n',encoding='utf-8')
 (out/'fp-lib-table').write_text(dump(parse('(fp_lib_table(version 7)(lib(name "CNC_MB_Identity")(type "KiCad")(uri "${KIPRJMOD}/CNC_MB_Identity.pretty")(options "")(descr "Primary sourced identity footprints")))'))+'\n',encoding='utf-8')

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
  yes='yes' if p['physical'] else 'no';items.append(f'(symbol(lib_id "CNC:{p["kind"]}")(at {x} {y} 0)(unit 1)(in_bom {yes})(on_board {yes})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_identity_io"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
  for n,_,px,py,_,_ in layout:
   sx,sy=round(x+px,4),round(y-py,4);net=p['pins'][str(n)]
   if net is None:items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(n)+"nc")}"))');continue
   dx=-5.08 if px<0 else 5.08 if px>0 else 0;dy=0 if px else 5.08;ex,ey=round(sx+dx,4),round(sy+dy,4)
   items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"wire")}"))');items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.65,"(justify right bottom)" if px<0 else "(justify left bottom)")}(uuid "{uid(ref+str(n)+"label")}"))');netmap.setdefault(net,[]).append([ref,str(n)])
 for i,net in enumerate(['IO_3V3','LOGIC_GND','FREQ_5V_LIMITED']):
  ref=f'#FLG21{i}';x=30.48+i*139.7;y=2080.26;items.append(f'(symbol(lib_id "CNC:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid "{uid(ref)}")(property "Reference" "{ref}"(at {x} {y} 0){effects(1,"hide")})(property "Value" "PARENT SUPPLY"(at {x} {y} 0){effects(1,"hide")})(instances(project "motherboard_identity_io"(path "/{root}"(reference "{ref}")(unit 1)))))(label "{net}"(at {x} {y} 0){effects(.8)}(uuid "{uid(ref+"label")}"))')
 note='ACTUAL PROTECTED ORDINARY 5V IDENTITY / actual one-GPIO 3.3V to5V open-drain path and rail-window enable.\nNative source only; target readonlyidentity, partialpower, noise, cable and loaded timing remain qualification.'
 items.append(f'(text {quote(note)}(at 20.32 17.78 0){effects(1.4,"(justify left top)")}(uuid "{uid(note)}"))')
 raw=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{root}")(paper "User" 1270 2200)(title_block(title "Motherboard protected ordinary 5V identity")(date "2026-09-30")(rev "r0.1"))(lib_symbols'+''.join(libs)+')'+''.join(items)+')'
 (out/'motherboard_identity_io.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf-8');(out/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in libs)+')'))+'\n',encoding='utf-8');(out/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Analog output source")))'))+'\n',encoding='utf-8');(out/'motherboard_identity_io.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_identity_io.kicad_pro','version':1},'erc':{'rule_severities':{k:'warning' for k in ['single_global_label','four_way_junction','simulation_model_issue','footprint_filter']}}},indent=2)+'\n');footprints(out)
 for name,obj in [('design',d),('pin-map',netmap),('boundary-map',d['boundaries'])]:(out/(name+'.json')).write_text(json.dumps(obj,indent=2)+'\n')
 with (out/'bom.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['Reference','Value','MPN','Footprint','Status']);w.writeheader();w.writerows({'Reference':ref,'Value':p['value'],'MPN':p['mpn'],'Footprint':p['footprint'],'Status':'source_candidate_not_qualified'} for ref,p in d['components'].items())
 print(json.dumps({'components':len(d['components']),'pads':d['fitted_pad_count'],'manufacturing_ready':False}));return d

if __name__=='__main__':build()

