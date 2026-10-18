"""Actual purchased ESP32-S3 DevKitC-1 v1.1 sockets and isolated service power.

This is source CAD, not an ESP SoC recreation or manufacturing release.
"""
from __future__ import annotations
import csv,json,uuid
from pathlib import Path
from hardware_build_assembly import parse,dump
from hardware_build_tx_schematic import symbol,quote,effects

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_esp_socket'
NS=uuid.UUID('05a9b71c-9c35-48c3-8d4b-435ceae6b46e')
J1=['3V3','3V3','RST','4','5','6','7','15','16','17','18','8','3','46','9','10','11','12','13','14','5V','GND']
J3=['GND','43','44','1','2','42','41','40','39','38','37','36','35','0','45','48','47','21','20','19','GND','GND']
KINDS={
 'SOCKET22':{i:(str(i),'passive') for i in range(1,23)},
 'LIMIT':{1:('IN','power_in'),2:('GND','power_in'),3:('EN','input'),4:('FAULT_N','open_collector'),5:('ILIM','passive'),6:('OUT','power_out')},
 'IDEAL':{1:('VIN','power_in'),2:('GND','power_in'),3:('CE','input'),4:('NC','no_connect'),5:('ST','open_collector'),6:('VOUT','power_out')},
 'SCHMITT':{1:('NC','no_connect'),2:('A','input'),3:('GND','power_in'),4:('Y','output'),5:('VCC','power_in')},
 'R':{1:('','passive'),2:('','passive')},'C':{1:('','passive'),2:('','passive')},
 'Boundary3':{i:(str(i),'passive') for i in range(1,4)},'PWR_FLAG':{1:('pwr','power_out')}}

def description():
 parts={};bounds={};ri=ci=16000
 def add(ref,kind,mpn,fp,pins,role,**data):
  parts[ref]=dict(kind=kind,mpn=mpn,value=mpn,footprint=fp,physical=True,pins={str(k):v for k,v in pins.items()},role=role,**data)
 def res(a,b,ohms,role,mpn=None):
  nonlocal ri
  ri+=1;ref=f'R{ri}';codes={33:'33R0',10000:'10K0',100000:'100K'}
  add(ref,'R',mpn or 'CRCW0603'+codes[ohms]+'FKEA','Resistor_SMD:R_0603_1608Metric',{1:a,2:b},role,resistance_ohm=ohms,tolerance=.001 if mpn else .01)
  parts[ref]['value']=f'{ohms}R';return ref
 def cap(a,b,nf,role):
  nonlocal ci
  ci+=1;ref=f'C{ci}';mpn={100:'GRM188R72A104KA35D',1000:'GRM188R71H105KA12D',10000:'GRM21BR71A106MA73L'}[nf]
  add(ref,'C',mpn,'Capacitor_SMD:C_0805_2012Metric' if nf==10000 else 'Capacitor_SMD:C_0603_1608Metric',{1:a,2:b},role,capacitance_f=nf*1e-9,tolerance=.2 if nf==10000 else .1)
  parts[ref]['value']=f'{nf}nF';return ref
 p1={i:None for i in range(1,23)};p1.update({1:'ESP_MODULE_3V3',2:'ESP_MODULE_3V3',4:'ESP_LIMIT_FAULT_N',5:'ESP_REVERSE_GATE_STATUS',11:'ESP_SERVICE_RX',21:'ESP_HEADER_5V',22:'LOGIC_GND'})
 p3={i:None for i in range(1,23)};p3.update({1:'LOGIC_GND',21:'LOGIC_GND',22:'LOGIC_GND'})
 for ref,pins,header in [('J16001',p1,'J1'),('J16002',p3,'J3')]:
  add(ref,'SOCKET22','61302211821','CNC_MB_ESP:Wurth_61302211821_1x22_P2.54',pins,
      'Actual female socket for purchased ESP32-S3-DevKitC-1-N8R8 v1.1 '+header,
      module_header=header,module_manufacturer_pin_names={str(i):n for i,n in enumerate(J1 if header=='J1' else J3,1)})
 add('U16001','LIMIT','TPS2553DBVR-1','Package_TO_SOT_SMD:SOT-23-6',
     {1:'CORE_5V',2:'LOGIC_GND',3:'ESP_SUPPLY_EN',4:'ESP_LIMIT_FAULT_N',5:'ESP_ILIM',6:'ESP_LIMITED_5V'},
     'Independent latch-off purchased-module branch; fault observation is not voltage measurement')
 res('CORE_5V','ESP_SUPPLY_EN',10000,'Service branch starts with core5; no machine output authority')
 res('ESP_SUPPLY_EN','LOGIC_GND',100000,'Service branch disabled when core input absent')
 ilim=res('ESP_ILIM','LOGIC_GND',20000,'Published20k design point1.200..1.375A; resistor/timing/thermal corners retained',mpn='TNPW060320K0BEEA')
 cap('CORE_5V','LOGIC_GND',100,'U16001 input HF bypass');cap('CORE_5V','LOGIC_GND',1000,'U16001 input reservoir')
 cap('ESP_LIMITED_5V','LOGIC_GND',100,'U16001 output bypass');cap('ESP_LIMITED_5V','LOGIC_GND',1000,'U16001 output reservoir')
 res('ESP_LIMITED_5V','LOGIC_GND',10000,'Bleed limits reverse-blocker leakage from USB-powered module')
 # CE MUST observe VOUT: tying CE to ground does not implement reverse blocking.
 add('U16002','IDEAL','LM66100DCKR','Package_TO_SOT_SMD:SOT-363_SC-70-6',
     {1:'ESP_LIMITED_5V',2:'LOGIC_GND',3:'ESP_HEADER_5V',4:None,5:'ESP_REVERSE_GATE_STATUS',6:'ESP_HEADER_5V'},
     'CE=VOUT real reverse-current protection;1.5A device; no claim that simultaneous devkit power modes are qualified')
 cap('ESP_HEADER_5V','LOGIC_GND',100,'U16002 output HF bypass');cap('ESP_HEADER_5V','LOGIC_GND',10000,'Purchased-module local bulk; effective bias and inrush remain to verify')
 res('ESP_HEADER_5V','LOGIC_GND',10000,'Defined disconnected-module output bleed')
 res('ESP_LIMIT_FAULT_N','ESP_MODULE_3V3',10000,'Observation pulled only to purchased module LDO output')
 res('ESP_REVERSE_GATE_STATUS','ESP_MODULE_3V3',10000,'Reverse-switch status uses module domain; not power-good')
 res('ESP_MODULE_3V3','LOGIC_GND',10000,'Discharge/Ioff leakage return with module absent; never powered from motherboard IO3')
 add('U16003','SCHMITT','SN74LVC1G17DBVR','Package_TO_SOT_SMD:SOT-23-5',
     {1:None,2:'ESP_SERVICE_TX_BUFFER',3:'LOGIC_GND',4:'ESP_SERVICE_RX_SOURCE',5:'ESP_MODULE_3V3'},
     'Ioff-rated read-only UART receiver crossing powered from actual purchased module3V3; no TX/reset/actuator path')
 res('COMPUTE_SERVICE_TX','ESP_SERVICE_TX_BUFFER',33,'UART source damping before module-domain input')
 res('ESP_SERVICE_TX_BUFFER','LOGIC_GND',100000,'Absent compute defined LOW; frame freshness decides availability')
 res('ESP_SERVICE_RX_SOURCE','ESP_SERVICE_RX',33,'UART receive output damping')
 cap('ESP_MODULE_3V3','LOGIC_GND',100,'U16003 local HF bypass')
 bounds['B16001']=dict(kind='Boundary3',mpn='',value='PARENT CORE5/GND/READONLY TX',footprint='',physical=False,pins={'1':'CORE_5V','2':'LOGIC_GND','3':'COMPUTE_SERVICE_TX'})
 return dict(schema_version=1,revision='motherboard-esp-socket-r0.1',manufacturing_ready=False,physical_qualification=False,
  components=parts,boundaries=bounds,purchased_module=dict(mpn='ESP32-S3-DevKitC-1-N8R8',revision='v1.1',not_a_custom_PCB=True,quantity=1,included_in_PCB_BOM=False),
  socket_geometry=dict(pitch_mm=2.54,pins_per_row=22,row_spacing_mm=22.86,origin='J1pin1 antenna end;J3pin1 at+22.86X',pin22_offset_mm=53.34,
   body_mm=[25.4,62.865],pdf_outline_length_mm=62.74,dxf_length_mm=62.865,measured_housing_height_qualified=False,
   rf_keepout_mm=15,antenna_beyond_motherboard_edge_required=True,usb_access_end='opposite pin1/antenna'),
  selected_connections=dict(uart_peripheral='UART1',RX_GPIO=18,TX_GPIO=None,status_GPIOs=[4,5],GPIO44_not_used='CP2102 onboard drives UART0RX',
   reserved_or_strap_GPIOs=[0,3,35,36,37,45,46],native_USB_GPIOs=[19,20],RGB_v11_GPIO=38,no_motion_authority=True),
  branch_power=dict(normal_reservation_a=.7,hardware_limit_design_point_a=[1.2,1.375],ilim_ref=ilim,ilim_ohm=20000,
   absolute_continuous_reverse_device_a=1.5,CE_connected_to_output=True,simultaneous_USB_and_header_power_qualified=False,
   qualification_gates=['Actual purchased LDO/dropout and revision','Series loss, copper, startup/inrush and thermal','Exact20k resistor corners/fullfault range','USB reverse leakage/ramp and Ioff behavior','RF/USB mechanics and retention'],
   manufacturer_power_modes_mutually_exclusive=True),
  references=['https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html',
   'https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf',
   'https://dl.espressif.com/dl/schematics/esp_idf/DXF_ESP32-S3-DevKitC-1_V1.1_20220429.dxf',
   'https://www.we-online.com/components/products/datasheet/61302211821.pdf',
   'https://www.ti.com/lit/ds/symlink/tps2553-1.pdf','https://www.ti.com/lit/ds/symlink/lm66100.pdf',
   'https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf'])

def footprint(out):
 folder=out/'CNC_MB_ESP.pretty';folder.mkdir(exist_ok=True)
 name='Wurth_61302211821_1x22_P2.54';items=[]
 for i in range(22):
  items.append(f'(pad "{i+1}" thru_hole {"rect" if i==0 else "circle"}(at 0 {i*2.54:.4f})(size 1.8 1.8)(drill 1.02)(layers "*.Cu" "*.Mask"))')
 for layer,x0,y0,x1,y1,width in [('F.Fab',-1.25,-1.52,1.25,54.86,.1),('F.CrtYd',-1.6,-1.895,1.6,55.235,.05),('F.SilkS',-1.45,-1.72,1.45,55.06,.12)]:
  items.append(f'(fp_rect(start {x0} {y0})(end {x1} {y1})(stroke(width {width})(type default))(fill none)(layer "{layer}"))')
 raw=f'(footprint "{name}"(version 20241229)(generator "controller_hardware")(layer "F.Cu")(attr through_hole)(descr "Wurth61302211821;manufacturer1.02mmholes;56.38mmhousing;2.54mmpitch")'+''.join(items)+')'
 (folder/(name+'.kicad_mod')).write_text(dump(parse(raw))+'\n')
 (out/'fp-lib-table').write_text(dump(parse(f'(fp_lib_table(version 7)(lib(name "CNC_MB_ESP")(type "KiCad")(uri "${{KIPRJMOD}}/CNC_MB_ESP.pretty")(options "")(descr "Actual purchased ESP sockets")))'))+'\n')

def build():
 OUT.mkdir(parents=True,exist_ok=True);d=description();parts={**d['components'],**d['boundaries']};uid=lambda s:str(uuid.uuid5(NS,s));root=uid('root');libs=[];layouts={}
 for kind in sorted({p['kind'] for p in parts.values()}|{'PWR_FLAG'}):
  rows=list(KINDS[kind].items());layout=[(n,nm,-20.32,round(30.48-i*5.08,4),0,typ) for i,(n,(nm,typ)) in enumerate(rows)]
  if kind in ('R','C'):layout=[(1,'',-5.08,0,0,'passive'),(2,'',5.08,0,180,'passive')]
  if kind=='PWR_FLAG':layout=[(1,'pwr',0,0,90,'power_out')]
  body='' if kind=='PWR_FLAG' else f'(rectangle(start -17.78 35.56)(end 17.78 {min(p[3] for p in layout)-5.08})(stroke(width .254)(type default))(fill(type background)))'
  if kind in ('R','C'):body='(rectangle(start -2.54 1.27)(end 2.54 -1.27)(stroke(width .254)(type default))(fill(type none)))'
  layouts[kind]=layout;libs.append(symbol(kind,layout,body,'J' if kind=='SOCKET22' else 'R' if kind=='R' else 'C' if kind=='C' else 'B' if kind.startswith('Boundary') else '#FLG' if kind=='PWR_FLAG' else 'U'))
 items=[]
 for i,(ref,p) in enumerate(parts.items()):
  x=50.8+(i%6)*127;y=76.2+(i//6)*167.64;layout=layouts[p['kind']]
  props=''.join(f'(property {quote(k)} {quote(v)}(at {x+25.4} {y-38.1+z*3.81} 0){effects(.9,extra="hide" if z>=2 else "")})' for z,(k,v) in enumerate([('Reference',ref),('Value',p['value']),('MPN',p['mpn']),('Footprint',p['footprint'])]))
  yes='yes' if p['physical'] else 'no';items.append(f'(symbol(lib_id "CNC:{p["kind"]}")(at {x} {y} 0)(unit 1)(in_bom {yes})(on_board {yes})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_esp_socket"(path "/{root}"(reference "{ref}")(unit 1)))))')
  for pin,nm,px,py,angle,typ in layout:
   a,b=round(x+px,4),round(y-py,4);net=p['pins'][str(pin)]
   if net is None:items.append(f'(no_connect(at {a} {b})(uuid "{uid(ref+str(pin)+"nc")}"))');continue
   end=round(a-5.08 if px<0 else a+5.08,4)
   items.append(f'(wire(pts(xy {a} {b})(xy {end} {b}))(stroke(width 0)(type default))(uuid "{uid(ref+str(pin)+"wire")}"))')
   items.append(f'(label {quote(net)}(at {end} {b} 0){effects(.8,"(justify left bottom)")}(uuid "{uid(ref+str(pin)+"label")}"))')
 for i,net in enumerate(('CORE_5V','LOGIC_GND','ESP_MODULE_3V3')):
  ref=f'#FLG16{i}';x=50.8+i*127;y=1016
  items.append(f'(symbol(lib_id "CNC:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid "{uid(ref)}")(property "Reference" "{ref}"(at {x} {y} 0){effects(1,"hide")})(property "Value" "EXTERNAL"(at {x} {y} 0){effects(1,"hide")})(instances(project "motherboard_esp_socket"(path "/{root}"(reference "{ref}")(unit 1)))))(label "{net}"(at {x} {y} 0){effects(.8)}(uuid "{uid(ref+"label")}"))')
 note='PURCHASED ESP32-S3 DEVKITC-1 N8R8 V1.1; TWO ACTUAL SOCKETS; READONLY UART1 GPIO18.\nNo machine-output, reset or motion authority. CE=VOUT reverse blocking; ESP3V3 comes only from purchased board.\nManufacturer USB/header/3V3 power modes mutually exclusive. Power/RF/mechanical/target validation remains open.'
 items.append(f'(text {quote(note)}(at 20.32 12.7 0){effects(1.3,"(justify left top)")}(uuid "{uid("notes")}"))')
 raw=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{root}")(paper "User" 850 1100)(title_block(title "Purchased ESP service sockets")(date "2026-09-30")(rev "r0.1"))(lib_symbols'+''.join(libs)+')'+''.join(items)+')'
 (OUT/'motherboard_esp_socket.kicad_sch').write_text(dump(parse(raw))+'\n')
 (OUT/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in libs)+')'))+'\n')
 (OUT/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Purchased ESP socket source")))'))+'\n')
 (OUT/'motherboard_esp_socket.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_esp_socket.kicad_pro','version':1}},indent=2)+'\n')
 (OUT/'design.json').write_text(json.dumps(d,indent=2)+'\n');footprint(OUT)
 with (OUT/'bom.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['Reference','Value','MPN','Footprint','Status'])
  for ref,p in d['components'].items():w.writerow([ref,p['value'],p['mpn'],p['footprint'],'candidate_not_qualified'])
 print(json.dumps({'physical_parts':len(d['components']),'purchased_modules_separate':1,'manufacturing_ready':False}))

if __name__=='__main__':build()
