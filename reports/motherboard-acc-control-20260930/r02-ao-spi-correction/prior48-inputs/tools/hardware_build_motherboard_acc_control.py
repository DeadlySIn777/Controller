"""Actual fourth IOL1 controller; native source, not target firmware evidence."""
from __future__ import annotations
import csv,json,uuid
from pathlib import Path
from hardware_build_assembly import parse,dump
from hardware_build_tx_schematic import symbol,effects,quote
from hardware_build_motherboard_io_control import P48,KINDS as CONTROL_KINDS,MPNS as CONTROL_MPNS,description as controls_description
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_acc_control'
NS=uuid.UUID('7d1a80f5-d2d4-4700-850f-bd2b367c8237')
KINDS={k:CONTROL_KINDS[k] for k in ['G031C','SUP','BUF4','SCHMITT','R','C','TP','PWR_FLAG']}
MPNS={k:CONTROL_MPNS[k] for k in ['G031C','SUP','BUF4','SCHMITT']}

def description():
 parts={};bounds={};u=r=c=t=14500
 def add(kind,pins,role):
  nonlocal u
  u+=1;ref=f'U{u}';mpn,fp=MPNS[kind];parts[ref]={'kind':kind,'mpn':mpn,'value':mpn,'footprint':fp,'physical':True,'pins':{str(k):v for k,v in pins.items()},'role':role};return ref
 def res(a,b,value,role):
  nonlocal r
  r+=1;ref=f'R{r}';mpn={22:'CRCW060322R0FKEA',3300:'CRCW06033K30FKEA',10000:'CRCW060310K0FKEA'}[value];parts[ref]={'kind':'R','mpn':mpn,'value':f'{value}R1%','footprint':'Resistor_SMD:R_0603_1608Metric','physical':True,'pins':{'1':a,'2':b},'resistance_ohm':value,'tolerance':.01,'role':role};return ref
 def cap(net,nf,role):
  nonlocal c
  c+=1;ref=f'C{c}';mpn,fp,v={100:('GRM188R72A104KA35D','Capacitor_SMD:C_0603_1608Metric',100),1000:('GRM188R71H105KA12D','Capacitor_SMD:C_0603_1608Metric',50),4700:('GRM21BR71A475KE51K','Capacitor_SMD:C_0805_2012Metric',10)}[nf];parts[ref]={'kind':'C','mpn':mpn,'value':f'{nf}nF{v}V','footprint':fp,'physical':True,'pins':{'1':net,'2':'LOGIC_GND'},'capacitance_f':nf*1e-9,'voltage_rating_v':v,'role':role};return ref
 def tp(net):
  nonlocal t
  t+=1;ref=f'TP{t}';parts[ref]={'kind':'TP','mpn':'PCB_COPPER_TEST_PAD_D1.0','value':net,'footprint':'TestPoint:TestPoint_Pad_D1.0mm','physical':True,'pins':{'1':net},'role':'factory SWD/power/reset PCB copper; no purchased connector'};return ref
 def boundary(ref,nets,role):bounds[ref]={'kind':'Boundary'+str(len(nets)),'mpn':'','value':'PARENT: '+role,'footprint':'','physical':False,'pins':{str(i+1):n for i,n in enumerate(nets)},'role':role,'status':'unimplemented parent connection until native integration'}
 pins={p:None for p in P48};by={name:n for n,name in P48.items()};mapping={}
 def pin(port,net):pins[by[port]]=net;mapping[port]=net
 for port,net in [('VBAT','IO_3V3'),('VREF+','IO_3V3'),('VDD/VDDA','IO_3V3'),('VSS/VSSA','LOGIC_GND'),('PF2-NRST','ACC_NRST_N'),('PA13','ACC_SWDIO'),('PA14-BOOT0','ACC_SWCLK_BOOT0')]:pin(port,net)
 for port,suffix in [('PA4','CS'),('PA5','CLK'),('PA6','RSP'),('PA7','CMD')]:pin(port,'ACC_IOL1_'+suffix+'_MCU')
 for bit,port in enumerate(['PC14','PC15','PF0','PF1']):
  n=f'ACC_SLOT{bit}';pin(port,n);res(n,'IO_3V3' if 3&(1<<bit) else 'LOGIC_GND',10000,'fixed soldered logical node slot3, not removable-card presence')
 for port,net in [('PA0','ACC_IO_ENABLE_STROBE'),('PA1','ACC_CARD_EN'),('PA2','ACC_OUT_EN_LATCH'),('PA3','PEN_OUT_EN_LATCH'),('PB0','OUT_PERMIT_ACC'),('PB1','PROC_PERMIT'),('PB2','PWM_ENABLE_LOGIC'),('PB10','PEN_ENABLE_LOGIC'),('PB11','PWM_AUX_FAULT_N'),('PA8','AO0_ENABLE_REQUEST'),('PA9','AO1_ENABLE_REQUEST'),('PC6','AO0_CLAMP_ACTIVE'),('PC7','AO1_CLAMP_ACTIVE'),('PA10','AI_POWER_GOOD_HOST'),('PA11','AO0_POWER_GOOD_HOST'),('PA12','AO1_POWER_GOOD_HOST'),('PD0','RS485_POWER_GOOD_HOST'),('PD1','CAN_POWER_GOOD_HOST'),('PD2','AI_SENSOR_FAULT_HOST'),('PB12','AI_CS_N_HOST'),('PB13','AI_SCLK_HOST'),('PB14','AI_SDO_HOST'),('PB15','AI_SDI_HOST'),('PB8','AO_I2C_SCL_HOST'),('PB9','AO_I2C_SDA_HOST')]:pin(port,net)
 health={}
 for net in ['AI_POWER_GOOD_HOST','AO0_POWER_GOOD_HOST','AO1_POWER_GOOD_HOST','RS485_POWER_GOOD_HOST','CAN_POWER_GOOD_HOST']:
  res(net,'LOGIC_GND',10000,'missing isolated-domain observation reads not-good; real monitor is separately required');health[net]={'active_good':1,'monitor_implemented':False}
 for net in ['AI_SENSOR_FAULT_HOST','AO0_CLAMP_ACTIVE','AO1_CLAMP_ACTIVE']:
  res(net,'IO_3V3',10000,'missing fault/clamp observation reads fault/clamped');health[net]={'active_fault':1,'monitor_implemented':False}
 for net in ['AO0_ENABLE_REQUEST','AO1_ENABLE_REQUEST']:res(net,'LOGIC_GND',10000,'MCU reset/unprogrammed defaults analog enable requests LOW')
 res('AI_CS_N_HOST','IO_3V3',10000,'unprogrammed MCU deselects isolated AI ADC')
 res('AI_SCLK_HOST','LOGIC_GND',10000,'inactive AI clock LOW');res('AI_SDI_HOST','LOGIC_GND',10000,'inactive AI command LOW')
 for net in ['AO_I2C_SCL_HOST','AO_I2C_SDA_HOST']:res(net,'IO_3V3',3300,'actual open-drain I2C host pull-up; no invented DAC SPI readback')
 mcu=add('G031C',pins,'fourth soldered ACC IOL1 node; actual analog/process monitoring and control pins')
 sup=add('SUP',{1:'ACC_NRST_N',2:'LOGIC_GND',3:'ACC_MR_N',4:None,5:'IO_3V3',6:'IO_3V3'},'3.07V rail reset; fixed open-CT20ms nominal release')
 res('ACC_NRST_N','IO_3V3',10000,'bidirectional internal watchdog/rail reset');res('ACC_MR_N','IO_3V3',10000,'factory manual-reset default released');res('ACC_SWCLK_BOOT0','LOGIC_GND',10000,'physical BOOT fallback LOW')
 cap('ACC_NRST_N',100,'NRST RF filter');cap('IO_3V3',100,'MCU VDD');cap('IO_3V3',4700,'MCU bulk');cap('IO_3V3',100,'MCU VREF');cap('IO_3V3',1000,'MCU VREF storage');cap('IO_3V3',100,'supervisor bypass')
 raw={s:'ACC_IOL1_'+s+'_BUFFER' for s in ['CS','CLK','CMD','RSP']}
 buf=add('BUF4',{1:'LOGIC_GND',2:'IOL1_L3_CS_N',3:raw['CS'],4:'LOGIC_GND',5:'IOL1_L3_SCLK',6:raw['CLK'],7:'LOGIC_GND',8:raw['CMD'],9:'IOL1_L3_MOSI',10:'LOGIC_GND',11:raw['RSP'],12:'ACC_IOL1_RSP_MCU',13:'LOGIC_GND',14:'IO_3V3'},'exact Nexperia powered-off qualified host link,3forward1return')
 cap('IO_3V3',100,'host buffer bypass')
 for s in ['CS','CLK','CMD']:res(raw[s],'ACC_IOL1_'+s+'_MCU',22,'source damping')
 res(raw['RSP'],'IOL1_L3_MISO',22,'response source damping')
 for net,end in [('IOL1_L3_CS_N','IO_3V3'),('IOL1_L3_SCLK','LOGIC_GND'),('IOL1_L3_MOSI','LOGIC_GND'),('ACC_IOL1_RSP_MCU','LOGIC_GND')]:res(net,end,10000,'missing/unprogrammed host link default')
 reset=add('SCHMITT',{1:None,2:'ACC_NRST_N',3:'LOGIC_GND',4:'ACC_CONTROLLER_RESET_N',5:'IO_3V3'},'actual reset buffered to separately pulled-LOW PWM/process frontend')
 cap('IO_3V3',100,'reset buffer bypass')
 pads=[tp(net) for net in ['IO_3V3','LOGIC_GND','ACC_SWDIO','ACC_SWCLK_BOOT0','ACC_NRST_N','ACC_MR_N']]
 boundary('J14501',['IO_3V3','LOGIC_GND','IOL1_L3_CS_N','IOL1_L3_SCLK','IOL1_L3_MOSI','IOL1_L3_MISO'],'allocated fourth host endpoint')
 boundary('J14502',['ACC_CONTROLLER_RESET_N','ACC_IO_ENABLE_STROBE','ACC_CARD_EN','ACC_OUT_EN_LATCH','PEN_OUT_EN_LATCH','OUT_PERMIT_ACC','PROC_PERMIT','PWM_ENABLE_LOGIC','PEN_ENABLE_LOGIC','PWM_AUX_FAULT_N'],'actual frozen144xx process frontend')
 boundary('J14503',['AI_CS_N_HOST','AI_SCLK_HOST','AI_SDI_HOST','AI_SDO_HOST','AO_I2C_SCL_HOST','AO_I2C_SDA_HOST','AO0_ENABLE_REQUEST','AO1_ENABLE_REQUEST','AO0_CLAMP_ACTIVE','AO1_CLAMP_ACTIVE'],'isolated analog frontend still required; no fake ADC/DAC')
 boundary('J14504',list(health),'real isolated supply/clamp/fault monitor sources separately required')
 old=controls_description()
 return {'schema_version':1,'revision':'motherboard-acc-control-r0.1','parent_reference_index':14,'components':parts,'boundaries':bounds,'fitted_component_count':len(parts),'fitted_pad_count':sum(len(p['pins']) for p in parts.values()),'purchased_fitted_parts':len(parts)-6,'PCB_copper_testpads':6,'manufacturing_ready':False,'physical_qualification':False,'firmware_implemented':False,'target_compilation_passed':False,'node':{'name':'ACC','port':'L3','slot':3,'class':0x31,'mcu_ref':mcu,'supervisor_ref':sup,'link_buffer_ref':buf,'reset_buffer_ref':reset,'mapping':mapping,'pin_port_names':{str(k):v for k,v in P48.items()},'health_inputs':health,'factory_pads':pads},'peripheral_mapping':{'hostSPI1':{'PA4':'NSS_AF0','PA5':'SCK_AF0','PA6':'MISO_AF0','PA7':'MOSI_AF0'},'AI_SPI2':{'PB12':'softwareCS','PB13':'SCK_AF0','PB14':'MISO_AF0','PB15':'MOSI_AF0'},'AO_I2C1':{'PB8':'SCL_AF6_open_drain','PB9':'SDA_AF6_open_drain'}},'logical_contract':{'protocol':'IOL1','port':'L3','class':0x31,'slot':3,'frame_bytes':40,'period_s':100e-6,'spi_hz':8333333.3,'accept_timer_s':.001,'no_automatic_rearm':True,'same_board_region_not_card':True,'validate_before_outputs_and_watchdog':True},'iwdg_candidate':old['iwdg_candidate'],'option_requirements':old['option_requirements'],'link_poweroff_review':old['link_poweroff_review'],'frontend_owned_biases':{'ACC_CARD_EN':'R14405','ACC_IO_ENABLE_STROBE':'R14404'},'DAC_readback_plan':{'interface':'I2C','DAC80501_SPI_has_no_SDO':True,'asynchronous_update_required':True,'readback_is_buffer_register_not_measured_VOUT':True,'native_frontend_implemented':False},'unimplemented_parent_obligations':['Target compile/provision protected bootloader, hardware-startIWDG/options, accepted-frame CRC/epoch/age validation and deliberate rearm.','Actual AO/AI isolated circuits and physical supply/clamp/fault observation; boundaries remain fault/not-good while absent.','Parent fourth FPGA package allocation/transport implementation, pin/return/decoupling layout and timed system inhibit.']}

def build(out=OUT):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);d=description();parts={**d['components'],**d['boundaries']};functions=dict(KINDS);uid=lambda n:str(uuid.uuid5(NS,n));root=uid('root');libs=[];layouts={}
 for p in d['boundaries'].values():functions[p['kind']]={int(k):(k,'passive') for k in p['pins']}
 for kind,table in functions.items():
  if kind in ['R','C']:layout=[(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')];body='(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))'
  elif kind in ['TP','PWR_FLAG']:layout=[(1,table[1][0],0,0,90,table[1][1])];body=''
  else:
   keys=list(table);half=(len(keys)+1)//2;layout=[(n,table[n][0],sign*12.7,20.32-i*5.08,0 if sign<0 else 180,table[n][1]) for sign,nums in [(-1,keys[:half]),(1,keys[half:])] for i,n in enumerate(nums)];low=min(p[3] for p in layout)-5.08;body=f'(rectangle(start -10.16 25.4)(end 10.16 {low})(stroke(width .254)(type default))(fill(type background)))'
  layouts[kind]=layout;libs.append(symbol(kind,layout,body,'R' if kind=='R' else 'C' if kind=='C' else 'TP' if kind=='TP' else 'J' if kind.startswith('Boundary') else '#FLG' if kind=='PWR_FLAG' else 'U'))
 items=[];netmap={};ic=pas=bnd=0
 for ref,p in parts.items():
  if ref.startswith('U'):x=63.5+(ic%6)*190.5;y=83.82+(ic//6)*190.5;ic+=1
  elif p['physical']:x=40.64+(pas%15)*76.2;y=708.66+(pas//15)*30.48;pas+=1
  else:x=63.5+(bnd%6)*190.5;y=1016+(bnd//6)*190.5;bnd+=1
  layout=layouts[p['kind']];small=p['kind'] in ['R','C','TP'];rx=x+3.81 if small else x;ry=y-2.54 if small else y-max(z[3] for z in layout)-10.16
  props=''.join(f'(property {quote(k)} {quote(v)}(at {rx} {ry+dy} 0){effects(.8,"hide") if hide else effects(.8,"(justify left)" if small else "")})' for k,v,dy,hide in [('Reference',ref,0,False),('Value',p['value'],2.54,False),('MPN',p['mpn'],0,True),('Footprint',p['footprint'],0,True)])
  yes='yes' if p['physical'] else 'no';items.append(f'(symbol(lib_id "CNC:{p["kind"]}")(at {x} {y} 0)(unit 1)(in_bom {yes})(on_board {yes})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_acc_control"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
  for n,_,px,py,_,_ in layout:
   sx,sy=round(x+px,4),round(y-py,4);net=p['pins'][str(n)]
   if net is None:items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(n)+"nc")}"))');continue
   dx=-5.08 if px<0 else 5.08 if px>0 else 0;dy=0 if px else 5.08;ex,ey=round(sx+dx,4),round(sy+dy,4)
   items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"wire")}"))');items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.65,"(justify right bottom)" if px<0 else "(justify left bottom)")}(uuid "{uid(ref+str(n)+"label")}"))');netmap.setdefault(net,[]).append([ref,str(n)])
 for i,net in enumerate(['IO_3V3','LOGIC_GND']):
  ref=f'#FLG13{i}';x=30.48+i*139.7;y=1262.38;items.append(f'(symbol(lib_id "CNC:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid "{uid(ref)}")(property "Reference" "{ref}"(at {x} {y} 0){effects(1,"hide")})(property "Value" "PARENT SUPPLY"(at {x} {y} 0){effects(1,"hide")})(instances(project "motherboard_acc_control"(path "/{root}"(reference "{ref}")(unit 1)))))(label "{net}"(at {x} {y} 0){effects(.8)}(uuid "{uid(ref+"label")}"))')
 note='IOL1 FOURTH ON-MOTHERBOARD CONTROL / L3:ACC\nOne real STM32G031C MCU, SPI buffers, rail/reset supervisors and factory SWD pads. No custom cards.\nTarget firmware/options/identity/calibration/field monitors and loaded timing remain unimplemented. Outputs default OFF.'
 items.append(f'(text {quote(note)}(at 20.32 17.78 0){effects(1.4,"(justify left top)")}(uuid "{uid(note)}"))')
 raw=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{root}")(paper "User" 1270 1300)(title_block(title "One-motherboard fourth ACC controller")(date "2026-09-30")(rev "r0.1"))(lib_symbols'+''.join(libs)+')'+''.join(items)+')'
 (out/'motherboard_acc_control.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf-8')
 (out/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in libs)+')'))+'\n',encoding='utf-8')
 (out/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "IOL1 motherboard MCU source")))'))+'\n',encoding='utf-8')
 (out/'motherboard_acc_control.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_acc_control.kicad_pro','version':1},'erc':{'rule_severities':{k:'warning' for k in ['single_global_label','four_way_junction','simulation_model_issue','footprint_filter']}}},indent=2)+'\n')
 (out/'design.json').write_text(json.dumps(d,indent=2)+'\n');(out/'pin-map.json').write_text(json.dumps(netmap,indent=2)+'\n');(out/'boundary-map.json').write_text(json.dumps(d['boundaries'],indent=2)+'\n')
 with (out/'bom.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['Reference','Value','MPN','Footprint','Status']);w.writeheader();w.writerows({'Reference':ref,'Value':p['value'],'MPN':p['mpn'],'Footprint':p['footprint'],'Status':'PCB_copper_test_pad' if p['kind']=='TP' else 'source_candidate_not_qualified'} for ref,p in d['components'].items())
 print(json.dumps({'components':len(d['components']),'pads':d['fitted_pad_count'],'nodes':1,'firmware_implemented':False,'manufacturing_ready':False}));return d

if __name__=='__main__':build()
