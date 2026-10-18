"""Source22: actual separate-return field-entry PG receivers and fault pads.

One integrated motherboard region. No card, additional processor or permission
authority. FA's existing converter-EN divider is sensed without rebiasing it.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
import shutil
import uuid
from hardware_build_assembly import parse, dump
from hardware_build_tx_schematic import symbol, effects, quote

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/motherboard_diagnostics'
NS = uuid.UUID('292c8fdf-3d4b-4b7a-b1b6-0e2517626f72')
KINDS = {
 'ISO': {1:('GND1','power_in'),2:('NC','no_connect'),3:('VCC1','power_in'),4:('INA','input'),5:('INB','input'),6:('NC','no_connect'),7:('NC','no_connect'),8:('GND1','power_in'),9:('GND2','power_in'),10:('NC','no_connect'),11:('NC','no_connect'),12:('OUTB','output'),13:('OUTA','output'),14:('VCC2','power_in'),15:('NC','no_connect'),16:('GND2','power_in')},
 'MON': {1:('OUTA','open_collector'),2:('GND','power_in'),3:('INA+','input'),4:('INB-','input'),5:('VDD','power_in'),6:('OUTB','open_collector')},
 'R': {1:('','passive'),2:('','passive')},
 'C': {1:('','passive'),2:('','passive')},
 'TP': {1:('TP','passive')},
 'MOUNT': {},
 'PWR_FLAG': {1:('pwr','power_out')},
}


def description():
 parts = {}
 def component(ref,kind,mpn,fp,pins,role,**extra):
  parts[ref]={'kind':kind,'mpn':mpn,'value':mpn or role,'footprint':fp,'physical':True,'pins':{str(k):v for k,v in pins.items()},'role':role,**extra}
 def resistor(ref,a,b):
  component(ref,'R','CRCW060310K0FKEA','Resistor_SMD:R_0603_1608Metric',{1:a,2:b},'actual own-field3.3 pullup; no cross-return bond',resistance_ohm=10000,tolerance=.01,tcr_ppm_K=100)
 def cap(ref,rail,ground):
  component(ref,'C','GRM188R72A104KA35D','Capacitor_SMD:C_0603_1608Metric',{1:rail,2:ground},'local100nF bypass in actual IC supply-return domain',capacitance_f=100e-9,voltage_rating_v=100)
 component('U22001','MON','TPS3700DDCR','Package_TO_SOT_SMD:SOT-23-6',
  {1:'FA_PGOOD_LEVEL_3V3',2:'FIELD_GND',3:'FA_PGOOD',4:'FIELD_GND',5:'DOA_FIELD_3V3',6:None},
  'INA+ senses existing1.6–2.7V FA eFuse/EN divider; unused INB grounded/OUTBNC; no added pullup on original divider')
 resistor('R22001','FA_PGOOD_LEVEL_3V3','DOA_FIELD_3V3')
 resistor('R22002','FB_PGOOD','DOB_FIELD_3V3')
 cap('C22001','DOA_FIELD_3V3','FIELD_GND')
 for i,bank,ground,rail,raw in [(2,'DOA','FIELD_GND','DOA_FIELD_3V3','FA_PGOOD_LEVEL_3V3'),(3,'DOB','FIELD_B_0V','DOB_FIELD_3V3','FB_PGOOD')]:
  component(f'U2200{i}','ISO','ISO7720FDWR','CNC_MB_Diagnostics:ISO7720_DW16_TI_HV',
   {1:ground,2:None,3:rail,4:raw,5:ground,6:None,7:None,8:ground,9:'LOGIC_GND',10:None,11:None,12:None,13:bank+'_FIELD_POWER_GOOD',14:'IO_3V3',15:None,16:'LOGIC_GND'},
   'field→logic own-return defaultLOW F-variant isolated entryPG; unused second inputGND/outputNC')
  cap(f'C2200{2*i-2}',rail,ground)
  cap(f'C2200{2*i-1}','IO_3V3','LOGIC_GND')
 for i,net in enumerate(['FPGA_LINK_FAULT','FPGA_WATCHDOG_FAULT','FPGA_INHIBIT_FAULT','FPGA_TIMING_FAULT'],1):
  component(f'TP2200{i}','TP','PCB_COPPER_TEST_PAD_D1.0','TestPoint:TestPoint_Pad_D1.0mm',{1:net},'bare PCB diagnostic test-only; no field-output or motion authority',purchased=False,exclude_from_position=True)
 for i in range(1,7):
  component(f'H2200{i}','MOUNT','','MountingHole:MountingHole_3.2mm_M3',{},'bare3.2mm NPTH M3 mechanical mount; no electrical pin/net',purchased=False,exclude_from_bom=True,exclude_from_position=True,drill_mm=3.2,conductive_pad=False)
 nets=['IO_3V3','LOGIC_GND','DOA_FIELD_3V3','FIELD_GND','DOB_FIELD_3V3','FIELD_B_0V','FA_PGOOD','FB_PGOOD','DOA_FIELD_POWER_GOOD','DOB_FIELD_POWER_GOOD','FPGA_LINK_FAULT','FPGA_WATCHDOG_FAULT','FPGA_INHIBIT_FAULT','FPGA_TIMING_FAULT']
 bounds={'B22001':{'kind':'Boundary14','mpn':'','value':'PARENT electrical connections only','footprint':'','physical':False,'pins':{str(i+1):n for i,n in enumerate(nets)},'role':'nonphysical interface declaration, not a module/header'}}
 return {'schema_version':1,'revision':'motherboard-diagnostics-r0.1','parent_reference_index':22,'components':parts,'boundaries':bounds,
  'physical_footprints':len(parts),'purchased_fitted_components':len(parts)-10,'bare_testpads':4,'bare_NPTH_mounts':6,'native_pad_count':sum(len(c['pins']) for c in parts.values()),
  'entry_good_semantics':'Real upstream entryPG received in each own field ground and qualified through actual own-field3.3-powered circuitry; it is not a calibrated local3.3 window or a readable eFuseFLT flag.',
  'preserved_parent_defaults':{'DOA_FIELD_POWER_GOOD':'R13027 existing10kLOW; U13004.PB1/pin16 readonly','DOB_FIELD_POWER_GOOD':'R13045 existing10kLOW; U13008.PB1/pin16 readonly'},
  'existing_FA_PGOOD_divider':'R11038=100k from FIELD_A_24V_PROTECTED, R11039=10k to FIELD_GND; U11009.3 converterEN. No divider/pullup substitution.',
  'isolation_returns_must_remain_distinct':['FIELD_GND','FIELD_B_0V','LOGIC_GND'],
  'gateware_pin_changes':False,'new_MCU_GPIO':False,'new_permission_authority':False,'manufacturing_ready':False,'physical_qualification':False,
  'unqualified_gates':['Native parent alias/pin reconciliation, PCB local bypass/return/isolation routing and faultpad access.','Assembled partial-power/ramp/monitor450usstartup/current/leakage/EMC qualification; entries remain unarmable while records invalid.','Target image reads real PB1 plus actual driver diagnostics; simulator fixtures are not hardware evidence.']}


def build(out=OUT):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);d=description();parts={**d['components'],**d['boundaries']};kinds={**KINDS,'Boundary14':{i:(str(i),'passive') for i in range(1,15)}}
 uid=lambda key:str(uuid.uuid5(NS,key));root=uid('root');layouts={};libs=[]
 for kind,table in kinds.items():
  if kind in ('R','C'):layout=[(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')];body='(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))'
  elif kind in ('TP','PWR_FLAG'):layout=[(1,table[1][0],0,0,90,table[1][1])];body=''
  elif kind=='MOUNT':layout=[];body='(circle(center 0 0)(radius 1.6)(stroke(width .254)(type default))(fill(type none)))'
  else:
   keys=list(table);half=(len(keys)+1)//2;layout=[(n,table[n][0],side*12.7,20.32-i*5.08,0 if side<0 else 180,table[n][1]) for side,ks in [(-1,keys[:half]),(1,keys[half:])] for i,n in enumerate(ks)]
   body=f'(rectangle(start -10.16 25.4)(end 10.16 {min(p[3] for p in layout)-5.08})(stroke(width .254)(type default))(fill(type background)))'
  layouts[kind]=layout;libs.append(symbol(kind,layout,body,'R' if kind=='R' else 'C' if kind=='C' else 'TP' if kind=='TP' else 'H' if kind=='MOUNT' else '#FLG' if kind=='PWR_FLAG' else 'B' if kind.startswith('Boundary') else 'U'))
 items=[];netmap={};ic=pas=bnd=0
 for ref,c in parts.items():
  if ref.startswith('U'):x=63.5+ic*190.5;y=83.82;ic+=1
  elif c['physical']:x=40.64+(pas%8)*76.2;y=233.68+(pas//8)*35.56;pas+=1
  else:x=63.5;y=340.36;bnd+=1
  layout=layouts[c['kind']];small=c['kind'] in ('R','C','TP','MOUNT');rx=x+3.81 if small else x;ry=y-2.54 if small else y-max(z[3] for z in layout)-10.16
  props=''.join(f'(property {quote(k)} {quote(v)}(at {rx} {ry+dy} 0){effects(.8,"hide") if hide else effects(.8,"(justify left)" if small else "")})' for k,v,dy,hide in [('Reference',ref,0,False),('Value',c['value'],2.54,False),('MPN',c['mpn'],0,True),('Footprint',c['footprint'],0,True)])
  yes='yes' if c['physical'] else 'no';purchased='no' if c.get('purchased') is False else yes
  items.append(f'(symbol(lib_id "CNC:{c["kind"]}")(at {x} {y} 0)(unit 1)(in_bom {purchased})(on_board {yes})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_diagnostics"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
  for pin,_,px,py,_,_ in layout:
   sx,sy=round(x+px,4),round(y-py,4);net=c['pins'][str(pin)]
   if net is None:items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(pin)+"nc")}"))');continue
   dx=-5.08 if px<0 else 5.08 if px>0 else 0;dy=0 if px else 5.08;ex,ey=round(sx+dx,4),round(sy+dy,4)
   items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(pin)+"wire")}"))')
   items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.65,"(justify right bottom)" if px<0 else "(justify left bottom)")}(uuid "{uid(ref+str(pin)+"label")}"))');netmap.setdefault(net,[]).append([ref,str(pin)])
 for i,net in enumerate(['IO_3V3','LOGIC_GND','DOA_FIELD_3V3','FIELD_GND','DOB_FIELD_3V3','FIELD_B_0V']):
  ref=f'#FLG22{i}';x=30.48+i*76.2;y=440.69;items.append(f'(symbol(lib_id "CNC:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid "{uid(ref)}")(property "Reference" "{ref}"(at {x} {y} 0){effects(1,"hide")})(property "Value" "ACTUAL PARENT SUPPLY"(at {x} {y} 0){effects(1,"hide")})(instances(project "motherboard_diagnostics"(path "/{root}"(reference "{ref}")(unit 1)))))(label "{net}"(at {x} {y} 0){effects(.8)}(uuid "{uid(ref+"label")}"))')
 note='SOURCE22 / REAL FIELD ENTRY PGOOD + FOUR TEST-ONLY FAULT PADS\nSeparate fieldA/fieldB returns; defaultLOW isolation. FA divider preserved.\nEntryPG is not calibrated local3.3 health. Target/partial-power/PCB qualification remains.'
 items.append(f'(text {quote(note)}(at 20.32 17.78 0){effects(1.2,"(justify left top)")}(uuid "{uid(note)}"))')
 raw=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{root}")(paper "User" 650 500)(title_block(title "Integrated motherboard diagnostic/entryPG region")(date "2026-09-30")(rev "r0.1"))(lib_symbols'+''.join(libs)+')'+''.join(items)+')'
 (out/'motherboard_diagnostics.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf-8')
 (out/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in libs)+')'))+'\n',encoding='utf-8')
 (out/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Actual diagnostic/entryPG source22")))'))+'\n',encoding='utf-8')
 (out/'motherboard_diagnostics.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_diagnostics.kicad_pro','version':1},'erc':{'rule_severities':{k:'warning' for k in ['single_global_label','four_way_junction','simulation_model_issue','footprint_filter']}}},indent=2)+'\n',encoding='utf-8')
 lib=out/'CNC_MB_Diagnostics.pretty';lib.mkdir(exist_ok=True);shutil.copy2(ROOT/'hardware/motherboard_motor_power/CNC_MotorPower.pretty/ISO7720_DW16_TI_HV.kicad_mod',lib/'ISO7720_DW16_TI_HV.kicad_mod')
 (out/'fp-lib-table').write_text(dump(parse('(fp_lib_table(version 7)(lib(name "CNC_MB_Diagnostics")(type "KiCad")(uri "${KIPRJMOD}/CNC_MB_Diagnostics.pretty")(options "")(descr "Reviewed TI DW16 HV land reused")))'))+'\n',encoding='utf-8')
 (out/'design.json').write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8');(out/'pin-map.json').write_text(json.dumps(netmap,indent=2)+'\n',encoding='utf-8')
 with (out/'bom.csv').open('w',encoding='utf-8',newline='') as stream:
  w=csv.DictWriter(stream,fieldnames=['Reference','Value','MPN','Footprint','Purchased','Status']);w.writeheader();w.writerows({'Reference':r,'Value':c['value'],'MPN':c['mpn'],'Footprint':c['footprint'],'Purchased':c.get('purchased') is not False,'Status':'bare_test_only_pad' if c['kind']=='TP' else 'source_candidate_not_qualified'} for r,c in d['components'].items())
 print(json.dumps({'physical_footprints':d['physical_footprints'],'purchased':d['purchased_fitted_components'],'bare_testpads':4,'bare_NPTH_mounts':6,'physical_qualification':False}));return d


if __name__=='__main__':build()
