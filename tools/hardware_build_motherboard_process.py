"""Actual hardware-latched PWM and floating process frontend, region144xx.

Native source only: target ACC firmware and assembled protection/timing remain.
"""
from __future__ import annotations
import csv,hashlib,json,shutil,uuid
from pathlib import Path
from hardware_build_assembly import parse,dump
from hardware_build_tx_schematic import symbol,effects,quote
from hardware_build_motherboard_do import PIN_FUNCTIONS as DO_PINS
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_process'
NS=uuid.UUID('d72441c2-6dc7-477d-bf80-c6c1d5b92722')
KINDS={k:DO_PINS[k] for k in ['DFF','AND4','NMOS','R','C']}
KINDS.update({
 'NMOS':{1:('G','input'),2:('S','passive'),3:('D','passive')},
 'T45':{1:('VCCA','power_in'),2:('A1','input'),3:('A2','input'),4:('GND','power_in'),5:('DIR','input'),6:('B2','output'),7:('B1','output'),8:('VCCB','power_in')},
 'ODINV':{1:('NC','no_connect'),2:('A','input'),3:('GND','power_in'),4:('Y','open_collector'),5:('VCC','power_in')},
 'LOAD':{1:('VIN','power_in'),2:('GND','power_in'),3:('ON','input'),4:('CT','passive'),5:('QOD','passive'),6:('VOUT','power_out')},
 'LIMIT':{1:('IN','input'),2:('DIAG_EN','input'),3:('FAULT_N','open_collector'),4:('CL','passive'),5:('DELAY','passive'),6:('GND','power_in'),7:('OUT','power_out'),8:('VS','power_in'),9:('EP_GND','power_in')},
 'DIODEPOWER':{1:('VIN','power_in'),2:('GND','power_in'),3:('CE','input'),4:('NC','no_connect'),5:('ST','open_collector'),6:('VOUT','power_out')},
 'RELAY':{1:('LED_A','passive'),2:('LED_K','passive'),3:('CONTACT','passive'),4:('CONTACT','passive')},
 'CLAMP':{1:('A1','passive'),2:('K2','passive'),3:('K1_A2','passive')},
 'AND1':{1:('A','input'),2:('B','input'),3:('GND','power_in'),4:('Y','output'),5:('VCC','power_in')},
 'TVS':{1:('IO','passive'),2:('IO','passive')},'PWR_FLAG':{1:('pwr','power_out')}})
MPNS={
 'DFF':('SN74LVC1G74DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm'),
 'AND4':('SN74LVC08APWR','Package_SO:TSSOP-14_4.4x5mm_P0.65mm'),
 'AND1':('SN74LVC1G08DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'T45':('SN74LVC2T45DCTR','Package_SO:SSOP-8_2.95x2.8mm_P0.65mm'),
 'ODINV':('SN74LVC1G06DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'LOAD':('TPS22918DBVR','Package_TO_SOT_SMD:SOT-23-6'),
 'LIMIT':('TPS1H000AQDGNRQ1','CNC_MB_Process:TPS1H000_DGN8_TI'),
 'DIODEPOWER':('LM66100DCKR','Package_TO_SOT_SMD:SOT-363_SC-70-6'),
 'NMOS':('PMV20XNEAR','CNC_MB_Process:PMV20XNEA_SOT23_NXP'),
 'RELAY':('TLP3640A(TPL,E','CNC_MB_Process:TLP3640A_SO4_11-3C1'),
 'CLAMP':('BAT54S,215','Package_TO_SOT_SMD:SOT-23')}

def description():
 parts={};bounds={};u=r=c=d=14400
 def add(kind,pins,role):
  nonlocal u
  u+=1;ref=f'U{u}';mpn,fp=MPNS[kind];parts[ref]={'kind':kind,'mpn':mpn,'value':mpn,'footprint':fp,'physical':True,'pins':{str(k):v for k,v in pins.items()},'role':role};return ref
 def res(a,b,ohms,role,mpn=None,tol=.01,tcr=100):
  nonlocal r
  r+=1;ref=f'R{r}';code={4.7:'4R70',330:'330R',4700:'4K70',10000:'10K0',56000:'56K0',100000:'100K'}
  parts[ref]={'kind':'R','mpn':mpn or 'CRCW0603'+code[ohms]+'FKEA','value':f'{ohms}R{tol*100:g}%','footprint':'Resistor_SMD:R_0603_1608Metric','physical':True,'pins':{'1':a,'2':b},'resistance_ohm':ohms,'tolerance':tol,'tcr_ppm_K':tcr,'role':role};return ref
 def cap(a,nf,role):
  nonlocal c
  c+=1;ref=f'C{c}';mpn,v={10:('GRM1885C2A103JA01D',100),100:('GRM188R72A104KA35D',100),1000:('GRM188R71H105KA12D',50)}[nf]
  parts[ref]={'kind':'C','mpn':mpn,'value':f'{nf}nF{v}V','footprint':'Capacitor_SMD:C_0603_1608Metric','physical':True,'pins':{'1':a,'2':'LOGIC_GND'},'capacitance_f':nf*1e-9,'voltage_rating_v':v,'role':role};return ref
 def tvs(a,b,process=False):
  nonlocal d
  d+=1;ref=f'D{d}';mpn,fp=('SMBJ33CA-E3/52','Diode_SMD:D_SMB') if process else ('TPD1E10B06DPYR','CNC_MB_Process:TPD1E10B06_DPY2_TI')
  parts[ref]={'kind':'TVS','mpn':mpn,'value':mpn,'footprint':fp,'physical':True,'pins':{'1':a,'2':b},'bidirectional':True,'role':'primary bidirectional suppressor; assembled protection not claimed'};return ref
 def boundary(ref,nets,role):bounds[ref]={'kind':'Boundary'+str(len(nets)),'mpn':'','value':'PARENT: '+role,'footprint':'','physical':False,'pins':{str(i+1):n for i,n in enumerate(nets)},'role':role}
 latch=add('DFF',{1:'ACC_IO_ENABLE_STROBE',2:'IO_3V3',3:None,4:'LOGIC_GND',5:'ACC_OUT_EN_LATCH',6:'ACC_CLR_N',7:'IO_3V3',8:'IO_3V3'},'permission/reset drop clears latch; next enable needs fresh valid-frame-controlled edge')
 gate=add('AND4',{1:'OUT_PERMIT_ACC',2:'ACC_CONTROLLER_RESET_N',3:'ACC_CLR_N',4:'ACC_OUT_EN_LATCH',5:'ACC_CARD_EN',6:'ACC_READY',7:'LOGIC_GND',8:'PWM_ENABLE_LOGIC',9:'ACC_READY',10:'OUT_PERMIT_ACC',11:'PEN_PERMIT_READY',12:'ACC_READY',13:'PROC_PERMIT',14:'IO_3V3'},'independent OUT/PROC permissions; MCU cannot override hardware inhibit')
 cmds=add('AND4',{1:'PWM_ENABLE_LOGIC',2:'PWM0_FPGA',3:'PWM0_GATED',4:'PWM_ENABLE_LOGIC',5:'PWM1_FPGA',6:'PWM1_GATED',7:'LOGIC_GND',8:'PEN0_LED_REQUEST',9:'PEN_ENABLE_LOGIC',10:'PEN0_CMD',11:'PEN1_LED_REQUEST',12:'PEN_ENABLE_LOGIC',13:'PEN1_CMD',14:'IO_3V3'},'commands physically gated; no constant permit')
 for ref in [latch,gate,cmds]:cap('IO_3V3',100,ref+' local bypass')
 procclr=add('AND1',{1:'ACC_CLR_N',2:'PROC_PERMIT',3:'LOGIC_GND',4:'PEN_CLR_N',5:'IO_3V3'},'process permission/reset loss independently clears process rearm latch')
 proclatch=add('DFF',{1:'ACC_IO_ENABLE_STROBE',2:'IO_3V3',3:None,4:'LOGIC_GND',5:'PEN_OUT_EN_LATCH',6:'PEN_CLR_N',7:'IO_3V3',8:'IO_3V3'},'process cannot automatically resume when PROC permission returns; new accepted rearm edge required')
 procgate=add('AND1',{1:'PEN_OUT_EN_LATCH',2:'PEN_PERMIT_READY',3:'LOGIC_GND',4:'PEN_ENABLE_LOGIC',5:'IO_3V3'},'process latch plus live permission; PWM lane remains independently armed')
 for ref in [procclr,proclatch,procgate]:cap('IO_3V3',100,ref+' local bypass')
 for net in ['OUT_PERMIT_ACC','PROC_PERMIT','ACC_CONTROLLER_RESET_N','ACC_IO_ENABLE_STROBE','ACC_CARD_EN','PWM_ENABLE_LOGIC','PEN_ENABLE_LOGIC']:res(net,'LOGIC_GND',10000,'missing controller/permission defaults OFF')
 for net in ['PWM0_FPGA','PWM1_FPGA','PEN0_CMD','PEN1_CMD']:res(net,'LOGIC_GND',4700,'LOW default includes unused-user FPGA weak pull-up; receiving leakage to qualify')
 reverse=add('DIODEPOWER',{1:'MOTION_5V_RAW',2:'LOGIC_GND',3:'PWM_5V_INTERNAL',4:None,5:None,6:'PWM_5V_INTERNAL'},'real ideal diode CE senses VOUT; prevents steady-state receiver/clamp backfeed into motion rail; switching energy remains qualification')
 cap('MOTION_5V_RAW',100,reverse+' input bypass');cap('PWM_5V_INTERNAL',100,reverse+' local bypass');cap('PWM_5V_INTERNAL',1000,reverse+' storage');res('PWM_5V_INTERNAL','LOGIC_GND',100000,'isolated PWM section bleed')
 trans=add('T45',{1:'IO_3V3',2:'PWM0_GATED',3:'PWM1_GATED',4:'LOGIC_GND',5:'IO_3V3',6:'PWM1_DRIVER',7:'PWM0_DRIVER',8:'PWM_5V_INTERNAL'},'dual supply noninverting A-to-B translator; 5V ±32mA device drive supports ±20mA port rating')
 cap('IO_3V3',100,trans+' A-side bypass');cap('PWM_5V_INTERNAL',100,trans+' B-side bypass')
 clampgate=add('ODINV',{1:None,2:'PWM_ENABLE_LOGIC',3:'LOGIC_GND',4:'PWM_CLAMP_GATE',5:'IO_3V3'},'HIGH enable sinks common clamp gate; missingIO3 Ioff leaves gate pulled5V and clamps ON')
 cap('IO_3V3',100,clampgate+' bypass');res('PWM_CLAMP_GATE','PWM_5V_INTERNAL',56000,'enabled OD load<100uA givesmaxVOL0.1V;missingIO3 clamp gate remainsabove2.5V screen;transitiontiming unqualified')
 pwm=[]
 for i in range(2):
  nmos=add('NMOS',{1:'PWM_CLAMP_GATE',2:'LOGIC_GND',3:f'PWM{i}_DRIVER'},'independent fail-LOW shunt before terminal resistor; maxRDS34mohm at2.5V/25C,20mohm4.5V/25C and30mohm4.5V/150C')
  series=res(f'PWM{i}_DRIVER',f'PWM{i}',4.7,'bounded20mA drop94mV; cable/protection qualification required');bias=res(f'PWM{i}','LOGIC_GND',10000,'terminal LOW bias ifallrails absent');tv=tvs(f'PWM{i}','LOGIC_GND');cl=add('CLAMP',{1:'LOGIC_GND',2:'PWM_5V_INTERNAL',3:f'PWM{i}'},'secondary Schottky rail clamp onto reverse-blocked local rail; not24V tolerant')
  pwm.append({'channel':i,'driver_ref':trans,'clamp_ref':nmos,'series_ref':series,'pulldown_ref':bias,'tvs_ref':tv,'rail_clamp_ref':cl,'net':f'PWM{i}','supply_v_nominal':5,'continuous_source_sink_a':.020,'loaded_VOH_min_screen_v':3.8-.020*4.7*1.01,'loaded_VOL_max_screen_v':.55+.020*4.7*1.01,'noIO3_clamp_ON':True,'clamp_gate_pullup_ohm':56000,'clamp_gate_noIO3_min_screen_v':4.5-20e-6*56000*1.01,'enabled_sink_max_load_a':5.25/(56000*.99),'gate_specs_temperature_c':25,'physical_response_qualified':False})
 load=add('LOAD',{1:'PWM_5V_INTERNAL',2:'LOGIC_GND',3:'PEN_ENABLE_LOGIC',4:None,5:'PEN_LED_5V',6:'PEN_LED_5V'},'shared permitted LED power; QOD engaged independently of command buffers')
 cap('PWM_5V_INTERNAL',100,load+' VIN bypass');cap('PEN_LED_5V',100,load+' output bypass');res('PEN_LED_5V','LOGIC_GND',330,'LED supply discharge worstcase conservative bleed')
 pens=[]
 for i in range(2):
  sink=add('ODINV',{1:None,2:f'PEN{i}_LED_REQUEST',3:'LOGIC_GND',4:f'PEN{i}_LED_SINK',5:'IO_3V3'},'realLED sink defaults highZ withmissingpower/LOWrequest');cap('IO_3V3',100,sink+' bypass')
  relay=add('RELAY',{1:'PEN_LED_5V',2:f'PEN{i}_LED_K',3:f'PEN{i}_1',4:f'PEN{i}_2'},'floatingNO process contact0–30VAC/DC50mA; hardware cuts LED power and sink')
  led=res(f'PEN{i}_LED_K',f'PEN{i}_LED_SINK',330,'LEDcurrent screen meetsIFTmax3mA, preserves20mA LED maximum');tv=tvs(f'PEN{i}_1',f'PEN{i}_2',True)
  pens.append({'channel':i,'relay_ref':relay,'sink_ref':sink,'LED_resistor_ref':led,'tvs_ref':tv,'contact_v_max':30,'contact_continuous_a':.05,'normally_open':True,'floating':True,'LED_min_screen_a':(4.5-1.9-.55)/(330*1.01),'LED_max_conservative_a':5.25/(330*.99),'physical_response_qualified':False})
 aux=add('LIMIT',{1:'IO_3V3',2:'IO_3V3',3:'PWM_AUX_FAULT_N',4:'PWM_AUX_ILIM',5:'PWM_AUX_DELAY',6:'LOGIC_GND',7:'PWM_5V_AUX',8:'PWM_5V_INTERNAL',9:'LOGIC_GND'},'actual latch-off auxiliary supply; on withlogic, fault telemetry, noauto retry')
 ilim=res('PWM_AUX_ILIM','LOGIC_GND',9530,'exactprecision resistor keeps programmedsetting above50mA forpublished±20%bound','TNPW06039K53BEEA',.001,25);cap('PWM_AUX_DELAY',10,'latchoff capacitor; delay source 4.5uA/1.45V is typical only');res('PWM_AUX_FAULT_N','IO_3V3',10000,'actual open-drain diagnostic; validity requires parentMOTIONrailgood');res('PWM_5V_AUX','LOGIC_GND',100000,'passive auxiliary discharge');cap('PWM_5V_INTERNAL',100,aux+' input bypass');cap('PWM_5V_INTERNAL',1000,aux+' input storage');cap('PWM_5V_AUX',100,aux+' output bypass');cap('PWM_5V_AUX',1000,aux+' output storage');tvs('PWM_5V_AUX','LOGIC_GND')
 rlo=9530*.999*(1-.00375);rhi=9530*1.001*(1+.00375)
 boundary('J14401',['IO_3V3','LOGIC_GND','MOTION_5V_RAW','OUT_PERMIT_ACC','PROC_PERMIT','PWM0_FPGA','PWM1_FPGA','PEN0_CMD','PEN1_CMD'],'parentrails,actualhardwarepermissions andallocatedFPGAcommands')
 boundary('J14402',['ACC_CONTROLLER_RESET_N','ACC_IO_ENABLE_STROBE','ACC_CARD_EN','ACC_OUT_EN_LATCH','PEN_OUT_EN_LATCH','PWM_ENABLE_LOGIC','PEN_ENABLE_LOGIC','PWM_AUX_FAULT_N'],'actualfourthIOL1ACCcontroller/observations required, notconstanthealthy')
 boundary('J14403',['PWM0','PWM1','PWM_5V_AUX','LOGIC_GND','PEN0_1','PEN0_2','PEN1_1','PEN1_2'],'typedfieldterminalsmating/shielding remainparent')
 return {'schema_version':1,'revision':'motherboard-process-r0.1','parent_reference_index':14,'status':'source_candidate_not_qualified','manufacturing_ready':False,'physical_qualification':False,'firmware_implemented':False,'components':parts,'boundaries':bounds,'fitted_component_count':len(parts),'fitted_pad_count':sum(len(p['pins']) for p in parts.values()),'latch_ref':latch,'process_latch_ref':proclatch,'process_clear_ref':procclr,'process_permission_ref':procgate,'permission_gate_ref':gate,'command_gate_ref':cmds,'clamp_gate_ref':clampgate,'relay_supply_ref':load,'reverse_feed_ref':reverse,'PWM_channels':pwm,'process_channels':pens,'aux_supply':{'limiter_ref':aux,'ilim_ref':ilim,'current_limit_target_a':.05,'programmed_nominal_a':480/9530,'programmed_low_resistor_allowance_a':480/rhi,'overload_min_screen_a':.8*480/rhi,'overload_max_screen_a':1.2*480/rlo,'accuracy_condition':'programmedlimit>=50mA,VS–VOUT>=2.5V,overload>1.5xsetting;TI5.5note2','not_a_guaranteed_50mA_maximum':True,'latchoff':True,'delay_physical_qualified':False},'unimplemented_parent_obligations':['ActualACC/IOL1L3 MCU,supervisor/rearmfirmware,hardware-startIWDG andidentity/readback.','Actual parentMOTIONrailqualification andpermissionfanout loading.','Final typedterminal/chassis/return routing andportorientation.','LoadedPWMlevels/short/clampcontention/EMC/processcontactturnoffwhole20msfaultpath.'],'electrical_limits':{'PWM_channels':2,'PWM_source_sink_a':.02,'process_channels':2,'process_contact_v':30,'process_contact_a':.05,'no_automatic_rearm':True}}

def footprints(out):
 lib=out/'CNC_MB_Process.pretty';lib.mkdir(exist_ok=True)
 for p in [ROOT/'hardware/motherboard_motors/CNC_Motors.pretty/TLP3640A_SO4_11-3C1.kicad_mod',ROOT/'hardware/motherboard_operator/CNC_MB_Operator.pretty/TPD1E10B06_DPY2_TI.kicad_mod']:shutil.copyfile(p,lib/p.name)
 mos='(footprint "PMV20XNEA_SOT23_NXP"(version 20241229)(generator "controller_hardware")(layer "F.Cu")(descr "Nexperia PMV20XNEA9Mar2016 Fig19,sot023_fr .6x.7copper,.5x.6paste;rotated90deg1G2S3D")(attr smd)(property "Reference" "REF**"(at 0 -2)(layer "F.SilkS")(effects(font(size .7 .7)(thickness .1))))(property "Value" "PMV20XNEA_SOT23_NXP"(at 0 2)(layer "F.Fab")(effects(font(size .7 .7)(thickness .1))))(fp_rect(start -.7 -1.5)(end .7 1.5)(stroke(width .1)(type default))(layer "F.Fab"))(fp_rect(start -1.5 -1.65)(end 1.5 1.65)(stroke(width .05)(type default))(layer "F.CrtYd"))'
 for n,x,y in [(1,-1,-.95),(2,-1,.95),(3,1,0)]:mos+=f'(pad "{n}" smd rect(at {x} {y})(size .7 .6)(layers "F.Cu" "F.Mask")(solder_mask_margin .05))(pad "" smd rect(at {x} {y})(size .6 .5)(layers "F.Paste"))'
 (lib/'PMV20XNEA_SOT23_NXP.kicad_mod').write_text(dump(parse(mos+')'))+'\n',encoding='utf-8')
 raw='(footprint "TPS1H000_DGN8_TI"(version 20241229)(generator "controller_hardware")(layer "F.Cu")(descr "TI DGN0008K-C01 4232899A04/2026land:1.4x.45outercentres+-2.2,.65pitch;EP1.57x1.89;125umstencil100pct;R.05")(attr smd)(property "Reference" "REF**"(at 0 -2.5)(layer "F.SilkS")(effects(font(size .7 .7)(thickness .1))))(property "Value" "TPS1H000_DGN8_TI"(at 0 2.5)(layer "F.Fab")(effects(font(size .7 .7)(thickness .1))))(fp_rect(start -1.5 -1.5)(end 1.5 1.5)(stroke(width .1)(type default))(layer "F.Fab"))(fp_rect(start -3.15 -1.75)(end 3.15 1.75)(stroke(width .05)(type default))(layer "F.CrtYd"))'
 for n in range(1,9):x=-2.2 if n<=4 else 2.2;y=(n-1)*.65-.975 if n<=4 else (8-n)*.65-.975;raw+=f'(pad "{n}" smd roundrect(at {x} {y})(size 1.4 .45)(layers "F.Cu" "F.Paste" "F.Mask")(roundrect_rratio .111111))'
 raw+='(pad "9" smd rect(at 0 0)(size 1.57 1.89)(layers "F.Cu" "F.Paste" "F.Mask")))';(lib/'TPS1H000_DGN8_TI.kicad_mod').write_text(dump(parse(raw))+'\n',encoding='utf-8');(out/'fp-lib-table').write_text(dump(parse('(fp_lib_table(version 7)(lib(name "CNC_MB_Process")(type "KiCad")(uri "${KIPRJMOD}/CNC_MB_Process.pretty")(options "")(descr "Primarysource process footprints")))'))+'\n',encoding='utf-8')
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
  else:x=63.5+(bnd%7)*165.1;y=1371.6+(bnd//7)*190.5;bnd+=1
  layout=layouts[p['kind']];small=p['kind'] in ['R','C','TVS'];rx=x+3.81 if small else x;ry=y-2.54 if small else y-max(z[3] for z in layout)-10.16
  props=''.join(f'(property {quote(k)} {quote(v)}(at {rx} {ry+dy} 0){effects(.8,"hide") if hide else effects(.8,"(justify left)" if small else "")})' for k,v,dy,hide in [('Reference',ref,0,False),('Value',p['value'],2.54,False),('MPN',p['mpn'],0,True),('Footprint',p['footprint'],0,True)])
  yes='yes' if p['physical'] else 'no';items.append(f'(symbol(lib_id "CNC:{p["kind"]}")(at {x} {y} 0)(unit 1)(in_bom {yes})(on_board {yes})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_process"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
  for n,_,px,py,_,_ in layout:
   sx,sy=round(x+px,4),round(y-py,4);net=p['pins'][str(n)]
   if net is None:items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(n)+"nc")}"))');continue
   dx=-5.08 if px<0 else 5.08 if px>0 else 0;dy=0 if px else 5.08;ex,ey=round(sx+dx,4),round(sy+dy,4)
   items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"wire")}"))');items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.65,"(justify right bottom)" if px<0 else "(justify left bottom)")}(uuid "{uid(ref+str(n)+"label")}"))');netmap.setdefault(net,[]).append([ref,str(n)])
 for i,net in enumerate(['IO_3V3','LOGIC_GND','MOTION_5V_RAW']):
  ref=f'#FLG144{i}';x=30.48+i*139.7;y=1600.2;items.append(f'(symbol(lib_id "CNC:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid "{uid(ref)}")(property "Reference" "{ref}"(at {x} {y} 0){effects(1,"hide")})(property "Value" "PARENT SUPPLY"(at {x} {y} 0){effects(1,"hide")})(instances(project "motherboard_process"(path "/{root}"(reference "{ref}")(unit 1)))))(label "{net}"(at {x} {y} 0){effects(.8)}(uuid "{uid(ref+"label")}"))')
 note='ACTUAL PWM/PROCESS FRONTEND / hardware rearm latch, permission gates, dual5Vpushpull PWM, independent fail-low clamps,2floatingprocess contacts.\nSource candidate only:4thACCnode,parentpermission,loadedtiming/ESD andphysicalconnectorsremain. No customcards,noautomatic rearm.'
 items.append(f'(text {quote(note)}(at 20.32 17.78 0){effects(1.4,"(justify left top)")}(uuid "{uid(note)}"))')
 raw=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{root}")(paper "User" 1270 1650)(title_block(title "Motherboard PWM and floating process control")(date "2026-09-30")(rev "r0.1"))(lib_symbols'+''.join(libs)+')'+''.join(items)+')'
 (out/'motherboard_process.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf-8');(out/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in libs)+')'))+'\n',encoding='utf-8');(out/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Process source")))'))+'\n',encoding='utf-8');(out/'motherboard_process.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_process.kicad_pro','version':1},'erc':{'rule_severities':{k:'warning' for k in ['single_global_label','four_way_junction','simulation_model_issue','footprint_filter']}}},indent=2)+'\n');footprints(out)
 for name,obj in [('design',d),('pin-map',netmap),('boundary-map',d['boundaries'])]:(out/(name+'.json')).write_text(json.dumps(obj,indent=2)+'\n')
 with (out/'bom.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['Reference','Value','MPN','Footprint','Status']);w.writeheader();w.writerows({'Reference':ref,'Value':p['value'],'MPN':p['mpn'],'Footprint':p['footprint'],'Status':'source_candidate_not_qualified'} for ref,p in d['components'].items())
 print(json.dumps({'components':len(d['components']),'pads':d['fitted_pad_count'],'manufacturing_ready':False}));return d

if __name__=='__main__':build()
