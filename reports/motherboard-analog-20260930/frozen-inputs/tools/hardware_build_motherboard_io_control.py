"""Build three actual soldered IOL1 acquisition/control nodes (13xxx).

STM32G031 selections inherit frozen IOL1; no new custom cards. The drawn
controllers close electrical frontend acquisition/reset/control boundaries.
Target firmware, option provisioning, loaded timing and parent monitors remain
explicit requirements, not evidence from a native schematic.
"""
from __future__ import annotations
import csv, hashlib, json, uuid
from pathlib import Path
from hardware_build_assembly import parse,dump
from hardware_build_tx_schematic import symbol,effects,quote

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_io_control'
NS=uuid.UUID('75e097d3-d784-4b92-bc77-dd05dbe0958e')
# DS12992 Rev4 Table12, LQFP columns, not UFQFPN exposed-pad numbering.
P48={1:'PC13',2:'PC14',3:'PC15',4:'VBAT',5:'VREF+',6:'VDD/VDDA',7:'VSS/VSSA',8:'PF0',9:'PF1',10:'PF2-NRST',11:'PA0',12:'PA1',13:'PA2',14:'PA3',15:'PA4',16:'PA5',17:'PA6',18:'PA7',19:'PB0',20:'PB1',21:'PB2',22:'PB10',23:'PB11',24:'PB12',25:'PB13',26:'PB14',27:'PB15',28:'PA8',29:'PA9',30:'PC6',31:'PC7',32:'PA10',33:'PA11',34:'PA12',35:'PA13',36:'PA14-BOOT0',37:'PA15',38:'PD0',39:'PD1',40:'PD2',41:'PD3',42:'PB3',43:'PB4',44:'PB5',45:'PB6',46:'PB7',47:'PB8',48:'PB9'}
P32={1:'PB9',2:'PC14',3:'PC15',4:'VDD/VDDA',5:'VSS/VSSA',6:'PF2-NRST',7:'PA0',8:'PA1',9:'PA2',10:'PA3',11:'PA4',12:'PA5',13:'PA6',14:'PA7',15:'PB0',16:'PB1',17:'PB2',18:'PA8',19:'PA9',20:'PC6',21:'PA10',22:'PA11',23:'PA12',24:'PA13',25:'PA14-BOOT0',26:'PA15',27:'PB3',28:'PB4',29:'PB5',30:'PB6',31:'PB7',32:'PB8'}
KINDS={
 'G031C':{n:(name,'power_in' if n in [4,5,6,7] else 'bidirectional') for n,name in P48.items()},
 'G031K':{n:(name,'power_in' if n in [4,5] else 'bidirectional') for n,name in P32.items()},
 'SUP':{1:('RESET_N','open_collector'),2:('GND','power_in'),3:('MR_N','input'),4:('CT','passive'),5:('SENSE','input'),6:('VDD','power_in')},
 'BUF4':{1:('1OE_N','input'),2:('1A','input'),3:('1Y','output'),4:('2OE_N','input'),5:('2A','input'),6:('2Y','output'),7:('GND','power_in'),8:('3Y','output'),9:('3A','input'),10:('3OE_N','input'),11:('4Y','output'),12:('4A','input'),13:('4OE_N','input'),14:('VCC','power_in')},
 'SCHMITT':{1:('NC','no_connect'),2:('A','input'),3:('GND','power_in'),4:('Y','output'),5:('VCC','power_in')},
 'R':{1:('','passive'),2:('','passive')},'C':{1:('','passive'),2:('','passive')},'TP':{1:('TP','passive')},'PWR_FLAG':{1:('pwr','power_out')}}
MPNS={'G031C':('STM32G031C8T6','Package_QFP:LQFP-48_7x7mm_P0.5mm'),
 'G031K':('STM32G031K8T6','Package_QFP:LQFP-32_7x7mm_P0.8mm'),
 'SUP':('TPS3808G33DBVR','Package_TO_SOT_SMD:SOT-23-6'),
 'BUF4':('74LVC125APW,118','Package_SO:TSSOP-14_4.4x5mm_P0.65mm'),
 'SCHMITT':('SN74LVC1G17DBVR','Package_TO_SOT_SMD:SOT-23-5')}

def description():
 parts={};bounds={};nodes=[];u=r=c=t=13000
 def add(kind,pins,role,**more):
  nonlocal u
  u+=1;ref=f'U{u}';mpn,fp=MPNS[kind];parts[ref]={'kind':kind,'mpn':mpn,'value':mpn,'footprint':fp,'physical':True,'pins':{str(k):v for k,v in pins.items()},'role':role,**more};return ref
 def res(a,b,value,role):
  nonlocal r
  r+=1;ref=f'R{r}';mpn={22:'CRCW060322R0FKEA',10000:'CRCW060310K0FKEA'}[value];parts[ref]={'kind':'R','mpn':mpn,'value':f'{value}R1%','footprint':'Resistor_SMD:R_0603_1608Metric','physical':True,'pins':{'1':a,'2':b},'resistance_ohm':value,'tolerance':.01,'role':role};return ref
 def cap(net,nf,role):
  nonlocal c
  c+=1;ref=f'C{c}';mpn,fp,v={100:('GRM188R72A104KA35D','Capacitor_SMD:C_0603_1608Metric',100),1000:('GRM188R71H105KA12D','Capacitor_SMD:C_0603_1608Metric',50),4700:('GRM21BR71A475KE51K','Capacitor_SMD:C_0805_2012Metric',10)}[nf];parts[ref]={'kind':'C','mpn':mpn,'value':f'{nf}nF{v}V','footprint':fp,'physical':True,'pins':{'1':net,'2':'LOGIC_GND'},'capacitance_f':nf*1e-9,'voltage_rating_v':v,'role':role};return ref
 def tp(net,role):
  nonlocal t
  t+=1;ref=f'TP{t}';parts[ref]={'kind':'TP','mpn':'PCB_COPPER_TEST_PAD_D1.0','value':net,'footprint':'TestPoint:TestPoint_Pad_D1.0mm','physical':True,'pins':{'1':net},'role':role};return ref
 def boundary(ref,nets,role):bounds[ref]={'kind':'Boundary'+str(len(nets)),'mpn':'','value':'PARENT: '+role,'footprint':'','physical':False,'pins':{str(i+1):n for i,n in enumerate(nets)},'role':role,'status':'explicit_unimplemented_parent_boundary'}
 for idx,name in enumerate(['DIC','DOA','DOB']):
  table=P48 if idx==0 else P32;kind='G031C' if idx==0 else 'G031K';pins={p:None for p in table};by={name:n for n,name in table.items()}
  def setpin(port,net):pins[by[port]]=net
  setpin('VDD/VDDA','IO_3V3');setpin('VSS/VSSA','LOGIC_GND');setpin('PF2-NRST',name+'_NRST_N')
  if idx==0:setpin('VBAT','IO_3V3');setpin('VREF+','IO_3V3')
  setpin('PA13',name+'_SWDIO');setpin('PA14-BOOT0',name+'_SWCLK_BOOT0')
  for port,suffix in [('PA4','CS'),('PA5','CLK'),('PA6','RSP'),('PA7','CMD')]:setpin(port,name+'_IOL1_'+suffix+'_MCU')
  di_map={};health={};outputs={};slot_ports=['PB6','PB7','PB8','PB9'] if idx==0 else ['PA9','PA10','PA11','PA12']
  for bit,port in enumerate(slot_ports):
   net=name+f'_SLOT{bit}';setpin(port,net);res(net,'IO_3V3' if idx&(1<<bit) else 'LOGIC_GND',10000,'fixed motherboard logical IOL1 node strap; not card presence')
  if idx==0:
   inputports=['PC13','PC14','PC15','PF0','PF1','PA0','PA1','PA2','PA3','PB0','PB1','PB2','PB10','PB11','PB12','PB13','PB14','PB15','PA8','PA9','PC6','PC7','PA10','PA11']
   for i,port in enumerate(inputports):setpin(port,f'DI{i}_LOGIC');di_map[str(i)]={'gpio':port,'pin':by[port],'net':f'DI{i}_LOGIC'}
   for port,net in [('PA12','DI_SENSOR_G0_FAULT'),('PA15','DI_SENSOR_G1_FAULT'),('PD0','DI_SENSOR_G2_FAULT'),('PD1','DI_SAFETY_SUPPLY_FAULT'),('PD2','DI_SAFETY_SECONDARY_FAULT')]:
    setpin(port,net);res(net,'IO_3V3',10000,'active-HIGH fault; missing parent monitor reads fault, not healthy');health[net]={'pin':by[port],'active_fault':1,'parent_monitor_implemented':False}
  else:
   letter='A' if idx==1 else 'B'
   for port,net in [('PB8',name+'_SCLK_HOST'),('PB7',name+'_SDI_HOST'),('PB6',name+'_SDO_HOST'),('PB9',name+'_CS_N_HOST'),('PA0',name+'_IO_ENABLE_STROBE'),('PA1',name+'_CARD_EN'),('PA2',name+'_OUT_EN_LATCH'),('PA3','OUT_PERMIT_'+letter),('PB0',name+'_FLT_N_HOST'),('PB1',name+'_FIELD_POWER_GOOD'),('PC6',name+'_DO_EN_LOGIC')]:setpin(port,net)
   # Those two10k pull-downs are already physically owned by the10xxx DO
   # frontend. Reserve their old references without fitting duplicates, keeping
   # every later reference stable across the104->100 population repair.
   r+=2
   res(name+'_FIELD_POWER_GOOD','LOGIC_GND',10000,'missing isolated field-supply health monitor is not healthy')
   health[name+'_FIELD_POWER_GOOD']={'pin':by['PB1'],'active_good':1,'parent_monitor_implemented':False}
   outputs={'strobe':{'pin':by['PA0'],'net':name+'_IO_ENABLE_STROBE'},'card_enable':{'pin':by['PA1'],'net':name+'_CARD_EN'},'latch_observation':{'pin':by['PA2'],'net':name+'_OUT_EN_LATCH'},'permission_observation':{'pin':by['PA3'],'net':'OUT_PERMIT_'+letter},'enable_observation':{'pin':by['PC6'],'net':name+'_DO_EN_LOGIC'},'fault_observation':{'pin':by['PB0'],'net':name+'_FLT_N_HOST'}}
  mcu=add(kind,pins,name+' soldered IOL1 acquisition/control MCU; firmware not implemented')
  sup=add('SUP',{1:name+'_NRST_N',2:'LOGIC_GND',3:name+'_MR_N',4:None,5:'IO_3V3',6:'IO_3V3'},'actual3.07V IO rail supervisor; CT open fixed20msnominal reset release')
  res(name+'_NRST_N','IO_3V3',10000,'open-drain rail reset and MCU bidirectional NRST pull-up');res(name+'_MR_N','IO_3V3',10000,'manual reset default released; factory fixture may pull low')
  cap(name+'_NRST_N',100,'recommended NRST RF filter; reset pulse/load qualification remains')
  res(name+'_SWCLK_BOOT0','LOGIC_GND',10000,'physical BOOT0 fallback low; SWD clock may override via factory fixture')
  cap('IO_3V3',100,mcu+' VDD pin bypass');cap('IO_3V3',4700,mcu+' local bulk')
  if idx==0:cap('IO_3V3',100,mcu+' VREF+ bypass');cap('IO_3V3',1000,mcu+' VREF+ recommended local storage')
  cap('IO_3V3',100,sup+' supervisor bypass')
  raw={suffix:name+'_IOL1_'+suffix+'_BUFFER' for suffix in ['CS','CLK','CMD','RSP']}
  buf=add('BUF4',{1:'LOGIC_GND',2:f'IOL1_L{idx}_CS_N',3:raw['CS'],4:'LOGIC_GND',5:f'IOL1_L{idx}_SCLK',6:raw['CLK'],7:'LOGIC_GND',8:raw['CMD'],9:f'IOL1_L{idx}_MOSI',10:'LOGIC_GND',11:raw['RSP'],12:name+'_IOL1_RSP_MCU',13:'LOGIC_GND',14:'IO_3V3'},'point-to-point Ioff isolation;3forward1return')
  cap('IO_3V3',100,buf+' bypass')
  for suffix in ['CS','CLK','CMD']:res(raw[suffix],name+'_IOL1_'+suffix+'_MCU',22,'source series damping; loaded SPI roundtrip unqualified')
  res(raw['RSP'],f'IOL1_L{idx}_MISO',22,'source series damping FPGA response')
  res(f'IOL1_L{idx}_CS_N','IO_3V3',10000,'inactive host link is deselected');res(f'IOL1_L{idx}_SCLK','LOGIC_GND',10000,'inactive host clock LOW');res(f'IOL1_L{idx}_MOSI','LOGIC_GND',10000,'inactive host command LOW');res(name+'_IOL1_RSP_MCU','LOGIC_GND',10000,'unprogrammed/high-Z MCU response LOW; invalid frame remains invalid')
  if idx:
   rb=add('SCHMITT',{1:None,2:name+'_NRST_N',3:'LOGIC_GND',4:name+'_CONTROLLER_RESET_N',5:'IO_3V3'},'actual MCU reset to fail-off frontend; avoids NRST10kUP/RESET10kDOWN divider')
   cap('IO_3V3',100,rb+' bypass')
  else:rb=None
  pads=[tp(net,'factory SWD/power/reset pad; not customer module connector') for net in ['IO_3V3','LOGIC_GND',name+'_SWDIO',name+'_SWCLK_BOOT0',name+'_NRST_N',name+'_MR_N']]
  nodes.append({'name':name,'port':f'L{idx}','class':0x11 if idx==0 else 0x21,'slot':idx,'mcu_ref':mcu,'supervisor_ref':sup,'link_buffer_ref':buf,'reset_buffer_ref':rb,'pin_port_names':{str(k):v for k,v in table.items()},'di_mapping':di_map,'health_inputs':health,'output_boundary':outputs,'factory_pads':pads,'firmware_implemented':False,'programmed_option_bytes_verified':False})
  boundary(f'J{13001+idx}',['IO_3V3','LOGIC_GND',f'IOL1_L{idx}_CS_N',f'IOL1_L{idx}_SCLK',f'IOL1_L{idx}_MOSI',f'IOL1_L{idx}_MISO'],'FPGA host port with final packageball/loaded timing qualification')
 boundary('J13004',[f'DI{i}_LOGIC' for i in range(24)],'native24DI frontend acquisition nets')
 boundary('J13005',['DI_SENSOR_G0_FAULT','DI_SENSOR_G1_FAULT','DI_SENSOR_G2_FAULT','DI_SAFETY_SUPPLY_FAULT','DI_SAFETY_SECONDARY_FAULT','DOA_FIELD_POWER_GOOD','DOB_FIELD_POWER_GOOD'],'actual protected supply monitors remain parent circuitry; missing monitor biases fault/not-good')
 for idx,name in enumerate(['DOA','DOB']):boundary(f'J{13006+idx}',[name+'_SCLK_HOST',name+'_SDI_HOST',name+'_SDO_HOST',name+'_CS_N_HOST',name+'_IO_ENABLE_STROBE',name+'_CARD_EN',name+'_OUT_EN_LATCH','OUT_PERMIT_'+('A' if idx==0 else 'B'),name+'_FLT_N_HOST',name+'_DO_EN_LOGIC',name+'_CONTROLLER_RESET_N'],'existing smart DO frontend control/reset and actual observations')
 obligations=['Keep DIC VREFBUF disabled/high impedance because VREF+ is supplied externally by IO_3V3; verify actual peripheral setup.','Implement/target-compile IOL1 SPI DMA/CRC32C/full-frame class-slot-epoch-sequence/reserved/semantic validation before outputs or watchdog refresh.','Provision/verify hardware-start IWDG option, NRST_MODE=3 and IRHEN=1, BOR and protected bootloader; firmware PR=4/RLR=9 candidate requires register completion and loaded <=2ms measurements.','Implement accepted-frame1ms timer, zero SW_STATE/configuration readback before CARD_EN, same-epoch no-rearm after permission/reset loss and internal-driver CRC/ADC/fault readback.','Actual DI sensor/safety supply monitors and isolated DO field-supply health remain unimplemented parent circuits; missing inputs must remain fault/unavailable.','Integrate native frontend and FPGA nets/ball map, PCB SPI roundtrip/return/reset/decoupling and factory test pads; no final route or manufacturing evidence.','Qualified board-region factory identity/calibration record replaces rack-card identities; MCU96-bitUID alone does not contain electrical ratings/calibration/firmware authenticity.']
 return {'schema_version':1,'revision':'motherboard-io-control-r0.4','parent_reference_index':13,'status':'source_candidate_not_qualified','manufacturing_ready':False,'physical_qualification':False,'firmware_implemented':False,'target_compilation_passed':False,'nodes':nodes,'components':parts,'boundaries':bounds,'fitted_component_count':len(parts),'fitted_pad_count':sum(len(p['pins']) for p in parts.values()),'frontend_owned_biases':{'DOA_CARD_EN':'R10004','DOA_IO_ENABLE_STROBE':'R10003','DOB_CARD_EN':'R10024','DOB_IO_ENABLE_STROBE':'R10023'},'logical_contract':{'protocol':'IOL1','ports':['L0','L1','L2'],'frame_bytes':40,'period_s':100e-6,'spi_hz':8333333.3,'accept_timer_s':.001,'iwdg_max_s':.002,'validate_before_outputs_and_watchdog':True,'no_automatic_resume':True,'no_fake_card_presence':True,'same_board_regions_not_custom_cards':True},'iwdg_candidate':{'independent_clock':'LSI','LSI_min_hz':29500,'LSI_max_hz':34000,'PR_divisor':4,'RLR':9,'counted_period_min_s':4*10/34000,'counted_period_max_s':4*10/29500,'whole_reset_and_inhibit_qualified':False,'option_provisioning_implemented':False,'application_refresh_only_full_accept':True,'bootloader_refresh_allowed_only_outputs_OFF':True,'no_debug_freeze_in_shipping':True},'option_requirements':{'IWDG_SW':0,'NRST_MODE':3,'IRHEN':1,'nBOOT_SEL':1,'nBOOT0':1,'bootloader_write_protected':True,'BOR_enabled':True,'BOR_level_selection_and_provisioning_verified':False,'DIC_VREFBUF_disabled_with_external_VREF':True},'link_poweroff_review':{'manufacturer':'Nexperia','mpn':'74LVC125APW,118','datasheet':'Rev12,2May2025','IOFF_VCC0_VI_or_VO5_5_max_a':20e-6,'IOFF_temperature_c':[-40,125],'tpd_3V_to3_6V_50pF_max_s':6e-9,'powered_brownout_qualified':False,'replaced_TI_no_IOFF_claim':True},'electrical_limits':{'DO_channel_continuous_a':.5,'DO_quad_continuous_a':2,'DI_sensor_group_continuous_a':.2,'driver_commission_ILIM_code':6,'driver_POR_ILIM_a':1.25},'unimplemented_parent_obligations':obligations}

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
  yes='yes' if p['physical'] else 'no';items.append(f'(symbol(lib_id "CNC:{p["kind"]}")(at {x} {y} 0)(unit 1)(in_bom {yes})(on_board {yes})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_io_control"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
  for n,_,px,py,_,_ in layout:
   sx,sy=round(x+px,4),round(y-py,4);net=p['pins'][str(n)]
   if net is None:items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(n)+"nc")}"))');continue
   dx=-5.08 if px<0 else 5.08 if px>0 else 0;dy=0 if px else 5.08;ex,ey=round(sx+dx,4),round(sy+dy,4)
   items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"wire")}"))');items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.65,"(justify right bottom)" if px<0 else "(justify left bottom)")}(uuid "{uid(ref+str(n)+"label")}"))');netmap.setdefault(net,[]).append([ref,str(n)])
 for i,net in enumerate(['IO_3V3','LOGIC_GND']):
  ref=f'#FLG13{i}';x=30.48+i*139.7;y=1262.38;items.append(f'(symbol(lib_id "CNC:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid "{uid(ref)}")(property "Reference" "{ref}"(at {x} {y} 0){effects(1,"hide")})(property "Value" "PARENT SUPPLY"(at {x} {y} 0){effects(1,"hide")})(instances(project "motherboard_io_control"(path "/{root}"(reference "{ref}")(unit 1)))))(label "{net}"(at {x} {y} 0){effects(.8)}(uuid "{uid(ref+"label")}"))')
 note='IOL1 ON-MOTHERBOARD CONTROL / L0:24DI / L1:DOA / L2:DOB\nThree real STM32G031 MCUs, SPI buffers, rail/reset supervisors and factory SWD pads. No custom cards.\nTarget firmware/options/identity/calibration/field monitors and loaded timing remain unimplemented. Outputs default OFF.'
 items.append(f'(text {quote(note)}(at 20.32 17.78 0){effects(1.4,"(justify left top)")}(uuid "{uid(note)}"))')
 raw=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{root}")(paper "User" 1270 1300)(title_block(title "One-motherboard IOL1 control nodes")(date "2026-09-30")(rev "r0.4"))(lib_symbols'+''.join(libs)+')'+''.join(items)+')'
 (out/'motherboard_io_control.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf-8')
 (out/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in libs)+')'))+'\n',encoding='utf-8')
 (out/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "IOL1 motherboard MCU source")))'))+'\n',encoding='utf-8')
 (out/'motherboard_io_control.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_io_control.kicad_pro','version':1},'erc':{'rule_severities':{k:'warning' for k in ['single_global_label','four_way_junction','simulation_model_issue','footprint_filter']}}},indent=2)+'\n')
 (out/'design.json').write_text(json.dumps(d,indent=2)+'\n');(out/'pin-map.json').write_text(json.dumps(netmap,indent=2)+'\n');(out/'boundary-map.json').write_text(json.dumps(d['boundaries'],indent=2)+'\n')
 with (out/'bom.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['Reference','Value','MPN','Footprint','Status']);w.writeheader();w.writerows({'Reference':ref,'Value':p['value'],'MPN':p['mpn'],'Footprint':p['footprint'],'Status':'PCB_copper_test_pad' if p['kind']=='TP' else 'source_candidate_not_qualified'} for ref,p in d['components'].items())
 print(json.dumps({'components':len(d['components']),'pads':d['fitted_pad_count'],'nodes':3,'firmware_implemented':False,'manufacturing_ready':False}));return d

if __name__=='__main__':build()
