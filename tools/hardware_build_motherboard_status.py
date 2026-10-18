"""Actual ordinary LED status circuits, independent of the motion transport.

New 17xxx source only. All receive/output observations are physical electrical
nodes, never cached requests. Native/source evidence is not physical validation.
"""
from __future__ import annotations
import csv,json,uuid
from pathlib import Path
from hardware_build_assembly import parse,dump
from hardware_build_tx_schematic import effects,quote,symbol
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/motherboard_status'
REPORT=ROOT/'reports/motherboard-status-20260930'
NS=uuid.UUID('b9fa2272-e985-4a1b-85b2-164f65ef2836')
PAIRS=[(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)]
RGB_NAMES=['SYSTEM','COMPUTE','FPGA','ESP','MOTION','EXPANSION','NETWORK']
GOOD_INPUTS=['MC_RAILS_OK_5V','WD_M_TRIP_N','WD_O_TRIP_N','TX_PERMIT','FPGA_USER_RESET_N','MOTOR_TX_GATE_A','MOTOR_TX_GATE_B']
KINDS={'R':{1:('','passive'),2:('','passive')},'C':{1:('','passive'),2:('','passive')},
 'LED':{1:('K','passive'),2:('A','passive')},
 'RGB':{1:('R_K','passive'),2:('G_K','passive'),3:('B_K','passive'),4:('A_COMMON','passive')},
 'DIODE':{1:('A','passive'),2:('NC','no_connect'),3:('K','passive')},
 'AHCT04':{7:('GND','power_in'),14:('VCC','power_in'),**{p:(f'{i+1}A','input') for i,(p,q) in enumerate(PAIRS)},**{q:(f'{i+1}Y','output') for i,(p,q) in enumerate(PAIRS)}},
 'LVC07':{7:('GND','power_in'),14:('VCC','power_in'),**{p:(f'{i+1}A','input') for i,(p,q) in enumerate(PAIRS)},**{q:(f'{i+1}Y','open_collector') for i,(p,q) in enumerate(PAIRS)}},
 'AND4':{1:('1A','input'),2:('1B','input'),3:('1Y','output'),4:('2A','input'),5:('2B','input'),6:('2Y','output'),7:('GND','power_in'),8:('3Y','output'),9:('3A','input'),10:('3B','input'),11:('4Y','output'),12:('4A','input'),13:('4B','input'),14:('VCC','power_in')},
 'I2C':{1:('VCCA','power_in'),2:('SCLA','bidirectional'),3:('SDAA','bidirectional'),4:('GND','power_in'),5:('EN','input'),6:('SDAB','bidirectional'),7:('SCLB','bidirectional'),8:('VCCB','power_in')},
 'LED16':{1:('NC','no_connect'),2:('A0','input'),3:('A1','input'),4:('A2','input'),5:('A3','input'),10:('GND','power_in'),19:('GND','power_in'),24:('GND','power_in'),25:('RESET_N','input'),26:('SCL','input'),27:('SDA','bidirectional'),28:('VCC','power_in'),**{p:(f'OUT{i}','open_collector') for i,p in enumerate([6,7,8,9,11,12,13,14,15,16,17,18,20,21,22,23])}},
 'RGB_SWITCH':{1:('S1','passive'),2:('D1','passive'),3:('SEL2','input'),4:('GND','power_in'),5:('S2','passive'),6:('D2','passive'),7:('SEL1','input'),8:('VDD','power_in')},
 'PWR_FLAG':{1:('pwr','power_out')}}
MPNS={'RGB':('AAA3528RGBS/K11/C8CC','CNC_MB_Status:AAA3528RGBS_Kingbright'),
 'AHCT04':('SN74AHCT04PWR','CNC_MB_Status:PW14_TI'),
 'LVC07':('74LVC07APW,118','CNC_MB_Status:SOT402_Nexperia'),
 'AND4':('SN74AHCT08PWR','CNC_MB_Status:PW14_TI'),
 'I2C':('TCA9517DGKR','CNC_MB_Status:DGK8_TI'),
 'LED16':('TLC59116FIPWR','CNC_MB_Status:PW28_TI'),
 'RGB_SWITCH':('TMUX1121DGKR','CNC_MB_Status:DGK8_TI'),
 'DIODE':('BAS16,215','Package_TO_SOT_SMD:SOT-23')}

def description():
 p={};u=r=c=d=17000;receivers=[];outputs=[];rgb=[];g='LOGIC_GND';v='CORE_5V'
 def add(k,pins,role,mpn=None,fp=None,value=None,**extra):
  nonlocal u,d
  if k in ['RGB','LED','DIODE']:d+=1;ref=f'D{d}'
  else:u+=1;ref=f'U{u}'
  m,f=MPNS[k] if k!='LED' else (mpn,'CNC_MB_Status:APT1608_Kingbright')
  p[ref]={'kind':k,'mpn':mpn or m,'footprint':fp or f,'value':value or mpn or m,'physical':True,'pins':{str(n):q for n,q in pins.items()},'role':role,**extra};return ref
 def res(a,b,ohm,role):
  nonlocal r
  r+=1;ref=f'R{r}';code={680:'680R',1000:'1K00',6800:'6K80',10000:'10K0',100000:'100K'}[ohm]
  p[ref]={'kind':'R','mpn':'CRCW0603'+code+'FKEA','value':f'{ohm}R1%','footprint':'Resistor_SMD:R_0603_1608Metric','physical':True,'pins':{'1':a,'2':b},'resistance_ohm':ohm,'tolerance':.01,'tcr_ppm_K':100,'power_rating_w':.1,'role':role};return ref
 def cap(rail):
  nonlocal c
  c+=1;ref=f'C{c}';p[ref]={'kind':'C','mpn':'GRM188R72A104KA35D','value':'100nF100V','footprint':'Capacitor_SMD:C_0603_1608Metric','physical':True,'pins':{'1':rail,'2':g},'capacitance_f':1e-7,'voltage_rating_v':100,'role':'local supply bypass'}
 # Physical receive observation. TTL receivers on CORE5 accept actual 3.3V
 # outputs, followed by separately specified powered-HIGH/off-leak OD sinks.
 nets=[f'DI{i}_LOGIC' for i in range(24)]+[f'ALM{i}_FPGA' for i in range(12)]
 for bank in range(6):
  inv={7:g,14:v};od={7:g,14:v}
  for j,(pin,outpin) in enumerate(PAIRS):
   i=bank*6+j;n=nets[i];label=f'IN{i+1}' if i<24 else f'M{i-23} ALM';inv[pin]=n;inv[outpin]=f'OBS{i}_INVERTED';od[pin]=f'OBS{i}_INVERTED';od[outpin]=f'OBS{i}_K'
   rr=res(v,f'OBS{i}_A',1000,'bounded receive LED current, even a shorted LED');bleed=res(f'OBS{i}_A',f'OBS{i}_K',10000,'off-leak shunt prevents an LED path becoming a leakage display')
   led=add('LED',{1:f'OBS{i}_K',2:f'OBS{i}_A'},'actual protected receive HIGH observation',mpn='APT1608SGC' if i<24 else 'APT1608SURCK',label=label)
   receivers.append({'index':i,'label':label,'observed_net':n,'led_ref':led,'current_ref':rr,'bleed_ref':bleed,'inv_pin':pin,'od_pin':pin,'output_pin':outpin})
  ir=add('AHCT04',inv,'TTL receive buffer, no motion/DI authority');sr=add('LVC07',od,'5V open-drain sink with explicit powered-HIGH and unpowered leakage bounds');cap(v);cap(v)
  for z in receivers[-6:]:z.update({'buffer_ref':ir,'sink_ref':sr})
 # DO observation stays on the actual terminal and its original field return.
 for i in range(16):
  n=f'DO{i:02d}';ret='FIELD_A_0V' if i<8 else 'FIELD_B_0V';a=f'OUT{i}_A';mid=f'OUT{i}_R_MID'
  r1=res(n,mid,6800,'actual terminal voltage indicator resistor1');r2=res(mid,a,6800,'series resistor2 shares worst-case30V dissipation')
  led=add('LED',{1:ret,2:a},'terminal-voltage indication; no claim of load current or command acceptance',mpn='APT1608SGC',label=f'OUT{i+1}')
  reverse=add('DIODE',{1:ret,2:None,3:a},'anti-parallel LED reverse clamp; not a field surge protector')
  outputs.append({'index':i,'label':f'OUT{i+1}','terminal':n,'return':ret,'led_ref':led,'current_refs':[r1,r2],'reverse_ref':reverse,'observes':'terminal_voltage_only'})
 # Real hardware GOOD tree; no constant/software cached GOOD.
 gate_ops=[('WD_M_TRIP_N','WD_O_TRIP_N','STATUS_NO_WDT_TRIP'),('MC_RAILS_OK_5V','STATUS_NO_WDT_TRIP','STATUS_HW_GOOD'),('TX_PERMIT','FPGA_USER_RESET_N','STATUS_MOTION_REQUEST_GOOD'),('MOTOR_TX_GATE_A','MOTOR_TX_GATE_B','STATUS_MOTION_FEEDS_GOOD'),('STATUS_MOTION_REQUEST_GOOD','STATUS_MOTION_FEEDS_GOOD','STATUS_MOTION_RGB_ENABLE'),(g,g,None),(g,g,None),(g,g,None)]
 gate_refs=[]
 for bank in range(2):
  pins={7:g,14:v}
  for (aa,bb,yy),(a,b,y) in zip([(1,2,3),(4,5,6),(9,10,8),(12,13,11)],gate_ops[bank*4:bank*4+4]):pins.update({aa:a,bb:b,yy:y})
  gate_refs.append(add('AND4',pins,'actual sticky trips/rail fault priority; disabled permission only removes MOTIONgreenblue'));cap(v)
 for n in GOOD_INPUTS:res(n,g,100000,'absent qualification defaults unavailable/inhibited, not a cached healthy state')
 res('STATUS_HW_GOOD',g,10000,'both driver resets LOW for actual rail/trip fault')
 res('STATUS_MOTION_RGB_ENABLE',g,10000,'missing motion qualification physically opens greenblue paths')
 # Explicit separate 4-red/3-red sinks; each stays below32mA at5V.
 faultpins={7:g,14:v,1:'STATUS_HW_GOOD',2:'STATUS_RED_BUS0',3:'STATUS_HW_GOOD',4:'STATUS_RED_BUS1',5:'STATUS_NO_WDT_TRIP',6:'STATUS_WDT_K',9:v,8:None,11:v,10:None,13:v,12:None}
 fault_ref=add('LVC07',faultpins,'hardware RED override and independent WDT fault sink; LOW GOOD -> fault ON');cap(v)
 wrr=res(v,'STATUS_WDT_A',1000,'independent watchdog LED current');res('STATUS_WDT_A','STATUS_WDT_K',10000,'watchdog OFF leakage shunt');wdt=add('LED',{1:'STATUS_WDT_K',2:'STATUS_WDT_A'},'actual sticky watchdog-trip indication; before logic rail qualification it is unavailable/red, not a measured trip',mpn='APT1608SURCK',label='WDT')
 # I2C status traffic remains separate from precision motion transport.
 i2c_ref=add('I2C',{1:'IO_3V3',2:'AO_I2C_SCL',3:'AO_I2C_SDA',4:g,5:v,6:'STATUS_I2C_SDA5',7:'STATUS_I2C_SCL5',8:v},'3.3V-to-5V I2C repeater; physical powered-off tolerance, no slave at forbidden addresses');cap('IO_3V3');cap(v)
 for a,b in [('IO_3V3','AO_I2C_SCL'),('IO_3V3','AO_I2C_SDA'),(v,'STATUS_I2C_SCL5'),(v,'STATUS_I2C_SDA5')]:res(a,b,10000,'local I2C pullup; total shared pullup/capacitance must be reconciled')
 driver_refs=[];ledpins=[6,7,8,9,11,12,13,14,15,16,17,18,20,21,22,23]
 for chip in range(2):
  pins={1:None,2:g if chip==0 else v,3:g,4:g,5:g,10:g,19:g,24:g,25:'STATUS_HW_GOOD',26:'STATUS_I2C_SCL5',27:'STATUS_I2C_SDA5',28:v}
  for j,pin in enumerate(ledpins):pins[pin]=f'RGB_DRIVER_{chip*16+j}' if chip*16+j<21 else None
  driver_refs.append(add('LED16',pins,'ordinary RGB PWM paths; hardware RESET takes priority and POR is all OFF',i2c_address=0x60+chip));cap(v)
 for i,name in enumerate(RGB_NAMES):
  pins={4:v};channels=[]
  for colour,pin in [('R',1),('G',2),('B',3)]:
   k=f'RGB_{name}_{colour}_K';pins[pin]=k;idx=i*3+len(channels);sink=f'RGB_DRIVER_{idx}'
   rr=res(k,sink,680,'physical RGB current ceiling independent of PWM register values');bleed=res(v,k,10000,'RGB emitter off-leak shunt')
   channels.append({'colour':colour,'pin':pin,'driver_ref':driver_refs[idx//16],'driver_pin':ledpins[idx%16],'current_ref':rr,'bleed_ref':bleed})
  if name=='MOTION':
   switch_ref=add('RGB_SWITCH',{1:'RGB_MOTION_G_SWITCH_IN',2:'RGB_DRIVER_13',3:'STATUS_MOTION_RGB_ENABLE',4:g,5:'RGB_MOTION_B_SWITCH_IN',6:'RGB_DRIVER_14',7:'STATUS_MOTION_RGB_ENABLE',8:v},'two actual series SPST paths physically remove MOTION G/B when disarmed, leave red control and other RGBs available');cap(v)
   for colour in ['G','B']:
    rr=p[next(z['current_ref'] for z in channels if z['colour']==colour)];rr['pins']['2']='RGB_MOTION_'+colour+'_SWITCH_IN'
  led=add('RGB',pins,'ordinary common-anode RGB with independent R/G/B',label=name)
  # Parallel hardware red path has its own resistor, preventing RGB driver
  # channel shorts from imposing unbounded shared current.
  hnode=f'RGB_{name}_HW_RED';hrr=res(pins[1],hnode,680,'hardware fault red has separate bounded resistor')
  diode=add('DIODE',{1:hnode,2:None,3:'STATUS_RED_BUS0' if i<4 else 'STATUS_RED_BUS1'},'parallel RED sink isolation prevents software red channel coupling')
  rgb.append({'label':name,'led_ref':led,'channels':channels,'hardware_red_ref':hrr,'hardware_diode_ref':diode,'hardware_red_bus':0 if i<4 else 1})
 boundaries={};b=17000
 def boundary(nets,role):
  nonlocal b
  b+=1;kind='Boundary'+str(len(nets));ref=f'J{b}';boundaries[ref]={'kind':kind,'physical':False,'mpn':'','footprint':'','value':'PARENT INTERFACE '+role,'pins':{str(i+1):n for i,n in enumerate(nets)},'role':role}
 boundary([v,g,'IO_3V3'],'existing protected rails/return; not an invented supply')
 for start in range(0,36,12):boundary(nets[start:start+12],'actual receive observation')
 boundary([f'DO{i:02d}' for i in range(8)]+['FIELD_A_0V'],'bankA actual terminals; isolation retained')
 boundary([f'DO{i:02d}' for i in range(8,16)]+['FIELD_B_0V'],'bankB actual terminals; isolation retained')
 boundary(GOOD_INPUTS,'actual hardware qualification nodes')
 boundary(['AO_I2C_SCL','AO_I2C_SDA'],'ACC existing shared I2C; no new MCU pins')
 return {'schema_version':1,'revision':'motherboard-status-r0.1','parent_reference_index':17,'manufacturing_ready':False,'physical_qualification':False,'status':'source_candidate_not_qualified','components':p,'boundaries':boundaries,'fitted_component_count':len(p),'fitted_pad_count':sum(len(q['pins']) for q in p.values()),'receive_indicators':receivers,'output_indicators':outputs,'rgb_indicators':rgb,'watchdog_indicator_ref':wdt,'watchdog_current_ref':wrr,'fault_sink_ref':fault_ref,'i2c_repeater_ref':i2c_ref,'rgb_driver_refs':driver_refs,'hardware_good_inputs':GOOD_INPUTS,'motion_rgb_switch_ref':switch_ref,'global_fault_terms':['MC_RAILS_OK_5V','WD_M_TRIP_N','WD_O_TRIP_N'],'ordinary_disarm_is_fault':False,'hardware_gate_refs':gate_refs,'hardware_gate_operations':gate_ops,'max_status_i2c_clock_hz':400000,'i2c_addresses':[0x60,0x61],'i2c_por_allcall_address':0x68,'i2c_software_reset_reserved_address':0x6B,'i2c_subcall_default_disabled_addresses':[0x69,0x6A,0x6C],'required_firmware_initialization':['Keep all LEDOUT registers OFF until measured fresh status qualifies','Disable MODE1 ALLCALL; keep SUB1/SUB2/SUB3 disabled','Read back MODE1, LEDOUT and PWM configuration after any hardware reset','Expire stale subsystem indications; watchdog remains independent'],'hardware_override':'actual rail qualification LOW or sticky watchdog trip holds both drivers reset and independently illuminates red; ordinary disarm opens MOTIONgreenblue only; CORE5 missing means dark/unavailable','receive_observation':'actual protected receive HIGH, not interpreted configured polarity','output_observation':'actual terminal voltage, not command/current/readback validity','target_firmware_implemented':False,'software_status_freshness_qualified':False,'open_gates':['Loaded I2C timing/shared pullup/rise and ACK-low noise margin','Full-temperature RGB optical/current/VF and driver OFF leakage; driver ICC is typical only','All rail ramp/partial-power/default and fault indication transitions','Source receive loading/capacitance and digital input transition-rate qualification','Firmware owner, stale software state reset policy and register readback','Field surge/reverse-transient and sunlight/light-pipe/label/mechanical qualification','Whole-board load, current, routing and thermal qualification']}



def footprints(out):
 lib=out/'CNC_MB_Status.pretty';lib.mkdir(exist_ok=True)
 def write(name,pads,body,court,descr):
  raw=f'(footprint "{name}"(version 20241229)(generator "controller_hardware")(layer "F.Cu")(descr {quote(descr)})(attr smd)(property "Reference" "REF**"(at 0 {-court[1]-.5})(layer "F.SilkS")(effects(font(size .7 .7)(thickness .1))))(property "Value" "{name}"(at 0 {court[1]+.5})(layer "F.Fab")(effects(font(size .7 .7)(thickness .1))))(fp_rect(start {-body[0]/2} {-body[1]/2})(end {body[0]/2} {body[1]/2})(stroke(width .1)(type default))(layer "F.Fab"))(fp_rect(start {-court[0]} {-court[1]})(end {court[0]} {court[1]})(stroke(width .05)(type default))(layer "F.CrtYd"))'
  for n,x,y,w,h in pads:raw+=f'(pad "{n}" smd rect(at {x} {y})(size {w} {h})(layers "F.Cu" "F.Paste" "F.Mask"))'
  raw+=f'(fp_circle(center {-court[0]} {-court[1]-.3})(end {-court[0]+.12} {-court[1]-.3})(stroke(width .1)(type default))(fill solid)(layer "F.SilkS")))'
  (lib/(name+'.kicad_mod')).write_text(dump(parse(raw))+'\n',encoding='utf-8')
 def dual(n,x,pitch,w,h):return [(i,-x if i<=n/2 else x,round((i-1)*pitch-(n/2-1)*pitch/2 if i<=n/2 else (n-i)*pitch-(n/2-1)*pitch/2,5),w,h) for i in range(1,n+1)]
 write('PW14_TI',dual(14,2.9,.65,1.5,.45),(4.5,5.1),(3.9,2.8),'TI PW0014A example 4220202/B12/2023, AHCT04/08:14 lands1.5x.45 at x+-2.9,pitch.65; body max4.5x5.1; courtyard .25 allowance.')
 write('SOT402_Nexperia',dual(14,2.9,.65,1.5,.45),(4.5,5.1),(3.9,2.8),'Nexperia74LVC07A SOT402-1 package outline Rev10 2025:bodymax4.5x5.1,leadspan6.2-6.6,pitch.65,width.19-.30,length.45-.75. Lands derived from matching TI PW14 example1.5x.45; lead-toe/heel coverage .35/.20minimum; not an NXP published solderland. Assembly approval required.')
 write('PW28_TI',dual(28,2.9,.65,1.5,.45),(4.5,9.8),(3.9,5.15),'TI PW R-PDSO-G28 outline4040064-7/G02/2011 retained DIR9001 p37; TLC59116F PW28. Matching TI PW14 land width/pitch extended28 pins:1.5x.45 x+-2.9 .65pitch. Derived land,not claimed manufacturer PW28 example; max lead toe3.3 vsland3.65 and minheel2.35 vsland2.15. Assembly qualification required.')
 write('DGK8_TI',dual(8,2.2,.65,1.4,.45),(3.1,3.1),(3.15,1.8),'TI TCA9517 DGK0008A official example:8 lands1.4x.45 x+-2.2,pitch.65; maxbody3.1square, .25courtyard.')
 write('AAA3528RGBS_Kingbright',[(1,1.4,.725,1.2,.9),(2,-1.4,.725,1.2,.9),(3,-1.4,-.725,1.2,.9),(4,1.4,-.725,1.2,.9)],(3.7,3.0),(2.25,1.75),'KingbrightAAA3528RGBS/K11/C8CC Rev5B recommendedlands1.2x.9 at x+-1.4,y+-.725; pin1RED2GREEN3BLUE4COMMONANODE; bodymax3.7x3.0; MSL3.')
 write('APT1608_Kingbright',[(1,-.825,0,.8,.8),(2,.825,0,.8,.8)],(1.7,.9),(1.475,.7),'KingbrightAPT1608SGC/SURCK Rev22:recommended .8x.8 lands,.85gap,centres+-.825;pin1K,pin2A;bodymax1.7x.9;MSL3.')
 (out/'fp-lib-table').write_text(dump(parse('(fp_lib_table(version 7)(lib(name "CNC_MB_Status")(type "KiCad")(uri "${KIPRJMOD}/CNC_MB_Status.pretty")(options "")(descr "Actual ordinary status LEDs, reviewed manufacturer maps")))'))+'\n',encoding='utf-8')
def build(out=OUT):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);d=description();parts={**d['components'],**d['boundaries']};functions=dict(KINDS);uid=lambda n:str(uuid.uuid5(NS,n));root=uid('root');libs=[];layouts={}
 for p in d['boundaries'].values():functions[p['kind']]={int(k):(k,'passive') for k in p['pins']}
 for kind,table in functions.items():
  if kind in ['R','C']:layout=[(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')];body='(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))'
  elif kind=='PWR_FLAG':layout=[(1,'pwr',0,0,90,'power_out')];body=''
  else:
   keys=sorted(table);half=(len(keys)+1)//2;layout=[(n,table[n][0],sign*12.7,20.32-i*5.08,0 if sign<0 else 180,table[n][1]) for sign,nums in [(-1,keys[:half]),(1,keys[half:])] for i,n in enumerate(nums)];low=min(p[3] for p in layout)-5.08;body=f'(rectangle(start -10.16 25.4)(end 10.16 {low})(stroke(width .254)(type default))(fill(type background)))'
  layouts[kind]=layout;libs.append(symbol(kind,layout,body,'R' if kind=='R' else 'C' if kind=='C' else 'D' if kind in ['RGB','LED','DIODE'] else 'J' if kind.startswith('Boundary') else '#FLG' if kind=='PWR_FLAG' else 'U'))
 items=[];netmap={};ic=pas=bnd=0
 for ref,p in parts.items():
  if ref.startswith('U'):x=63.5+(ic%7)*165.1;y=83.82+(ic//7)*139.7;ic+=1
  elif p['physical']:x=40.64+(pas%17)*68.58;y=800.1+(pas//17)*30.48;pas+=1
  else:x=63.5+(bnd%7)*165.1;y=1905+(bnd//7)*190.5;bnd+=1
  layout=layouts[p['kind']];small=p['kind'] in ['R','C'];rx=x+3.81 if small else x;ry=y-2.54 if small else y-max(z[3] for z in layout)-10.16
  props=''.join(f'(property {quote(k)} {quote(v)}(at {rx} {ry+dy} 0){effects(.8,"hide") if hide else effects(.8,"(justify left)" if small else "")})' for k,v,dy,hide in [('Reference',ref,0,False),('Value',p['value'],2.54,False),('MPN',p['mpn'],0,True),('Footprint',p['footprint'],0,True)])
  yes='yes' if p['physical'] else 'no';items.append(f'(symbol(lib_id "CNC:{p["kind"]}")(at {x} {y} 0)(unit 1)(in_bom {yes})(on_board {yes})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_status"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
  for n,_,px,py,_,_ in layout:
   sx,sy=round(x+px,4),round(y-py,4);net=p['pins'][str(n)]
   if net is None:items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(n)+"nc")}"))');continue
   dx=-5.08 if px<0 else 5.08 if px>0 else 0;dy=0 if px else 5.08;ex,ey=round(sx+dx,4),round(sy+dy,4)
   items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"wire")}"))');items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.65,"(justify right bottom)" if px<0 else "(justify left bottom)")}(uuid "{uid(ref+str(n)+"label")}"))');netmap.setdefault(net,[]).append([ref,str(n)])
 for i,net in enumerate(['IO_3V3','LOGIC_GND','CORE_5V','FIELD_A_0V','FIELD_B_0V']):
  ref=f'#FLG170{i}';x=30.48+i*139.7;y=2159;items.append(f'(symbol(lib_id "CNC:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid "{uid(ref)}")(property "Reference" "{ref}"(at {x} {y} 0){effects(1,"hide")})(property "Value" "PARENT SUPPLY"(at {x} {y} 0){effects(1,"hide")})(instances(project "motherboard_status"(path "/{root}"(reference "{ref}")(unit 1)))))(label "{net}"(at {x} {y} 0){effects(.8)}(uuid "{uid(ref+"label")}"))')
 note='ACTUAL STATUS LED SOURCE / 7ordinary RGB,24DI,12motoralarms,16terminal-voltage indicators and independent WDT. Hardware reset/red priority uses actual rail/sticky-watchdog faults; motionpermissionLOW opens onlyMOTIONgreenblue.\nSource candidate: partial rails, loaded I2C/current/optical/thermal and target status freshness remain. No motion authority.'
 items.append(f'(text {quote(note)}(at 20.32 17.78 0){effects(1.4,"(justify left top)")}(uuid "{uid(note)}"))')
 raw=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{root}")(paper "User" 1270 2210)(title_block(title "Motherboard ordinary status indicators")(date "2026-09-30")(rev "r0.1"))(lib_symbols'+''.join(libs)+')'+''.join(items)+')'
 (out/'motherboard_status.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf-8');(out/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in libs)+')'))+'\n',encoding='utf-8');(out/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Ordinary status LED source")))'))+'\n',encoding='utf-8');(out/'motherboard_status.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_status.kicad_pro','version':1},'erc':{'rule_severities':{k:'warning' for k in ['single_global_label','four_way_junction','simulation_model_issue','footprint_filter']}}},indent=2)+'\n');footprints(out)
 for name,obj in [('design',d),('pin-map',netmap),('boundary-map',d['boundaries'])]:(out/(name+'.json')).write_text(json.dumps(obj,indent=2)+'\n')
 with (out/'bom.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['Reference','Value','MPN','Footprint','Status']);w.writeheader();w.writerows({'Reference':ref,'Value':p['value'],'MPN':p['mpn'],'Footprint':p['footprint'],'Status':'source_candidate_not_qualified'} for ref,p in d['components'].items())
 print(json.dumps({'components':len(d['components']),'pads':d['fitted_pad_count'],'manufacturing_ready':False}));return d


if __name__=='__main__':build()
