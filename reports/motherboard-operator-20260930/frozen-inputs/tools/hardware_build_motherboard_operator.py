"""Actual on-motherboard operator, probe and eight protected port branches.

The source closes electrical paths; current/ESD/timing qualification and loaded
FPGA code remain separate. Frozen source originals and parent CAD are untouched.
"""
from __future__ import annotations
import csv,hashlib,json,shutil,uuid
from pathlib import Path
from hardware_build_assembly import parse,dump
from hardware_build_tx_schematic import symbol,effects,quote
from hardware_build_motherboard_di import iso_footprint

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_operator'
NS=uuid.UUID('a918a370-aa8b-499d-a8a9-6c689f939147')
KINDS={
 'SR':{1:('SH_LD_N','input'),2:('CLK','input'),3:('E','input'),4:('F','input'),5:('G','input'),6:('H','input'),7:('QH_N','output'),8:('GND','power_in'),9:('QH','output'),10:('SER','input'),11:('A','input'),12:('B','input'),13:('C','input'),14:('D','input'),15:('CLK_INH','input'),16:('VCC','power_in')},
 'INV6':{1:('1A','input'),2:('1Y','output'),3:('2A','input'),4:('2Y','output'),5:('3A','input'),6:('3Y','output'),7:('GND','power_in'),8:('4Y','output'),9:('4A','input'),10:('5Y','output'),11:('5A','input'),12:('6Y','output'),13:('6A','input'),14:('VCC','power_in')},
 'BUF1':{1:('NC','no_connect'),2:('A','input'),3:('GND','power_in'),4:('Y','output'),5:('VCC','power_in')},
 'AND1':{1:('A','input'),2:('B','input'),3:('GND','power_in'),4:('Y','output'),5:('VCC','power_in')},
 'AND2':{1:('1A','input'),2:('1B','input'),3:('2Y','output'),4:('GND','power_in'),5:('2A','input'),6:('2B','input'),7:('1Y','output'),8:('VCC','power_in')},
 'ISO1212':{1:('GND1','power_in'),2:('VCC1','power_in'),3:('EN','input'),4:('OUT1','output'),5:('OUT2','output'),6:('NC','no_connect'),7:('NC','no_connect'),8:('GND1','power_in'),9:('FGND2','passive'),10:('IN2','input'),11:('SENSE2','input'),12:('SUB2','passive'),13:('SUB1','passive'),14:('FGND1','passive'),15:('IN1','input'),16:('SENSE1','input')},
 'SW5':{1:('IN','power_in'),2:('GND','power_in'),3:('EN','input'),4:('FAULT_N','open_collector'),5:('ILIM','passive'),6:('OUT','power_out')},
 'SW24':{1:('IN','power_in'),2:('UVLO','input'),3:('OVP','input'),4:('SHDN_N','input'),5:('RTN','power_in'),6:('GND','power_in'),7:('ILIM','passive'),8:('dVdT','passive'),9:('FLT_N','open_collector'),10:('OUT','power_out'),11:('EP_RTN','power_in')},
 'ISO2':{1:('GND1','power_in'),2:('NC','no_connect'),3:('VCC1','power_in'),4:('INA','input'),5:('INB','input'),6:('NC','no_connect'),7:('NC','no_connect'),8:('GND1','power_in'),9:('GND2','power_in'),10:('NC','no_connect'),11:('NC','no_connect'),12:('OUTB','output'),13:('OUTA','output'),14:('VCC2','power_in'),15:('NC','no_connect'),16:('GND2','power_in')},
 'SHUNT':{1:('CATHODE','passive'),2:('ANODE','passive'),3:('NC_ANODE','passive')},
 'CLAMP':{1:('A1','passive'),2:('K2','passive'),3:('K1_A2','passive')},
 'R':{1:('','passive'),2:('','passive')},'C':{1:('','passive'),2:('','passive')},'TVS':{1:('IO','passive'),2:('IO','passive')},'PWR_FLAG':{1:('pwr','power_out')}}
MPNS={
 'SR':('SN74LV165APWR','Package_SO:TSSOP-16_4.4x5mm_P0.65mm'),
 'INV6':('SN74LVC14APWR','Package_SO:TSSOP-14_4.4x5mm_P0.65mm'),
 'BUF1':('SN74LVC1G17DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'AND1':('SN74LVC1G08DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'AND2':('SN74LVC2G08DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm'),
 'ISO1212':('ISO1212DBQR','CNC_MB_Operator:ISO1212_DBQ16_TI'),
 'SW5':('TPS2553DBVR-1','Package_TO_SOT_SMD:SOT-23-6'),
 'SW24':('TPS26624DRCR','CNC_MB_Operator:TPS2662_DRC10_TI'),
 'ISO2':('ISO7720FDWR','Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm'),
 'SHUNT':('LM4040A25IDBZR','Package_TO_SOT_SMD:SOT-23'),
 'CLAMP':('BAT54S,215','Package_TO_SOT_SMD:SOT-23')}

def description():
 parts={};bounds={};u=r=c=d=14000
 def add(kind,pins,role):
  nonlocal u
  u+=1;ref=f'U{u}';mpn,fp=MPNS[kind];parts[ref]={'kind':kind,'mpn':mpn,'value':mpn,'footprint':fp,'physical':True,'pins':{str(k):v for k,v in pins.items()},'role':role};return ref
 def res(a,b,ohms,role,mpn=None,fp='Resistor_SMD:R_0603_1608Metric'):
  nonlocal r
  r+=1;ref=f'R{r}';code={22:'22R0',33:'33R0',1000:'1K00',1800:'1K80',4700:'4K70',10000:'10K0',49900:'49K9',100000:'100K',110000:'110K',150000:'150K',221000:'221K',1000000:'1M00'}
  parts[ref]={'kind':'R','mpn':mpn or 'CRCW0603'+code[ohms]+'FKEA','value':f'{ohms}R1%','footprint':fp,'physical':True,'pins':{'1':a,'2':b},'resistance_ohm':ohms,'tolerance':.01,'role':role};return ref
 def cap(a,b,nf,role):
  nonlocal c
  c+=1;ref=f'C{c}';mpn,v={10:('GRM1885C2A103JA01D',100),100:('GRM188R72A104KA35D',100),1000:('GRM188R71H105KA12D',50)}[nf]
  parts[ref]={'kind':'C','mpn':mpn,'value':f'{nf}nF{v}V','footprint':'Capacitor_SMD:C_0603_1608Metric','physical':True,'pins':{'1':a,'2':b},'capacitance_f':nf*1e-9,'voltage_rating_v':v,'role':role};return ref
 def tvs(a,b,probe=False):
  nonlocal d
  d+=1;ref=f'D{d}';mpn,fp=('SMBJ33CA-E3/52','Diode_SMD:D_SMB') if probe else ('TPD1E10B06DPYR','CNC_MB_Operator:TPD1E10B06_DPY2_TI')
  parts[ref]={'kind':'TVS','mpn':mpn,'value':mpn,'footprint':fp,'physical':True,'pins':{'1':a,'2':b},'working_standoff_v':33 if probe else 5.5,'role':'bidirectional primary transient suppressor; assembled ESD/surge qualification required'};return ref
 def boundary(ref,nets,role):bounds[ref]={'kind':'Boundary'+str(len(nets)),'mpn':'','value':'PARENT: '+role,'footprint':'','physical':False,'pins':{str(i+1):n for i,n in enumerate(nets)},'role':role}
 contacts=['MPG_SEL_X','MPG_SEL_Y','MPG_SEL_Z','MPG_SEL_A','MPG_SEL_B','MPG_SEL_C','MPG_MUL_X1','MPG_MUL_X10','MPG_MUL_X100','MPG_PEND_AUX','MPG_ENABLE','MOD_PRESENT']
 active=[];contactrecords=[]
 # Real Schmitt inputs tolerate normal5V; slow cable/contact transitions never
 # drive a non-Schmitt shift-register input directly.
 for bank in range(2):
  pins={7:'LOGIC_GND',14:'IO_3V3'}
  for j,(ip,op) in enumerate([(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)]):
   net=contacts[bank*6+j];conditioned=net+'_CONDITIONED';state=net+'_ACTIVE';pins[ip]=conditioned;pins[op]=state;active.append(state)
   series=res(net,conditioned,1000,'contact series current limiting before clamp and Schmitt input');pull=res(net,'MOTION_5V_RAW',10000,'open contact inactive;5V pull-up, not24V fieldinput');filt=cap(conditioned,'LOGIC_GND',10,'operator/contact RF filter; never used on fast probes')
   protection=tvs(net,'LOGIC_GND');clamp=add('CLAMP',{1:'LOGIC_GND',2:'MOTION_5V_RAW',3:conditioned},'secondary rail clamp after1k;5V input only, EMC/partialpower remains to measure')
   contactrecords.append({'external':net,'conditioned':conditioned,'active':state,'series_ref':series,'pullup_ref':pull,'filter_ref':filt,'tvs_ref':protection,'clamp_ref':clamp,'active_low_external':True,'normal_input_max_v':5.25,'not_a_24V_input':True})
  inv=add('INV6',pins,'six protected active-LOW contacts translated to active-HIGH status');cap('IO_3V3','LOGIC_GND',100,inv+' bypass')
 # Common enable is a real LOW-default prerequisite, not hardcoded qualified.
 res('FAST_PORTS_ENABLE','LOGIC_GND',4700,'4.7k LOW default: no internalpull duringreset/config;27k weakpullup only unuseduser mode;actualleakagebudgetreview');res('XF_POWER_ENABLE','LOGIC_GND',4700,'4.7k LOW default including unuseduser weakpullup andleakage;accessory OFF untilconfigured')
 buf=add('BUF1',{1:None,2:'FAST_PORTS_ENABLE',3:'LOGIC_GND',4:'FAST_PORTS_EN_BUFFER',5:'IO_3V3'},'buffer shared five-port enable;Ioff whenlogicpowerabsent');cap('IO_3V3','LOGIC_GND',100,buf+' bypass')
 for incoming,buffered in [('XF_POWER_ENABLE','XF_REQUEST_BUFFER'),('FPGA_CDONE','FPGA_CDONE_BUFFER')]:
  b=add('BUF1',{1:None,2:incoming,3:'LOGIC_GND',4:buffered,5:'IO_3V3'},'Schmitt restore slow request/configuration input before non-Schmitt AND');cap('IO_3V3','LOGIC_GND',100,b+' bypass')
 config=add('AND1',{1:'FAST_PORTS_EN_BUFFER',2:'FPGA_CDONE_BUFFER',3:'LOGIC_GND',4:'FAST_PORTS_EN_CONFIGURED',5:'IO_3V3'},'real configurationdone AND regionqualification;notconstanthealthy');cap('IO_3V3','LOGIC_GND',100,config+' bypass')
 gate=add('AND2',{1:'FAST_PORTS_EN_CONFIGURED',2:'XF_REQUEST_BUFFER',3:'XF_POWER_EN_GATED',4:'LOGIC_GND',5:'XF_POWER_QUALIFIED',6:active[11],7:'XF_POWER_QUALIFIED',8:'IO_3V3'},'XF enable=configurationdone AND qualifiedregion AND configuredrequest AND actual modulepresence');cap('IO_3V3','LOGIC_GND',100,gate+' bypass')
 # Four base encoders, oneMPG and oneXF supply, independent current limiters.
 portrecords=[];faultgood=[]
 for name,rval,load in [('ENC0',110000,.2),('ENC1',110000,.2),('ENC2',110000,.2),('ENC3',110000,.2),('MPG',221000,.1),('FREQ',150000,.15)]:
  supply=name+'_5V';en=name+'_POWER_EN';fault=name+'_POWER_FAULT_N';ilim=name+'_ILIM'
  sw=add('SW5',{1:'MOTION_5V_RAW',2:'LOGIC_GND',3:en,4:fault,5:ilim,6:supply},'independent latch-off '+name+' supply;FAULT is not voltage measurement')
  resistor=res(ilim,'LOGIC_GND',rval,'TI full-temp equation screen incl1%100ppm150K;not physicalqualification');res(en,'LOGIC_GND',10000,'local EN defaults OFF');res('XF_POWER_EN_GATED' if name=='FREQ' else 'FAST_PORTS_EN_CONFIGURED',en,33,'buffered enable source damping');res(fault,'IO_3V3',10000,'open-drain FAULT readback;valid only withqualifiedparentrails');res(supply,'LOGIC_GND',100000,'passive bleed;no active discharge timing guarantee')
  for net in ['MOTION_5V_RAW',supply]:cap(net,'LOGIC_GND',100,sw+' local HF bypass');cap(net,'LOGIC_GND',1000,sw+' local storage;DCbiascharacterization required')
  rmin=rval/1000*.99*.985;rmax=rval/1000*1.01*1.015;lo=25230/rmax**1.016/1000;hi=22980/rmin**.94/1000
  portrecords.append({'name':name,'switch_ref':sw,'ilim_ref':resistor,'ilim_ohm':rval,'normal_load_a':load,'minimum_calculated_a':lo,'maximum_calculated_a':hi,'guaranteed_point_used':False,'equation_source':'TI SLVS841F sections10.2.1.1/10.2.1.2','equation_screen_only':True,'fault_is_power_good':False,'voltage_adc_implemented':False,'validation_requires_motion_rail_and_region_qualification':True});faultgood.append(fault)
 # Independent24V probe branches preserve fieldA isolation. Exact49.9k
 # source candidate is drawn, but a published44.2k limit is NOT passed off as
 # a guaranteed150mA point. Hard-short/threshold bounds remain sourcing gates.
 probe_powers=[]
 for i in range(2):
  name=f'PRB{i}';pins={1:'FIELD_A_24V_PROTECTED',2:name+'_UVLO',3:'FIELD_GND',4:name+'_SHDN_N',5:'FIELD_GND',6:'FIELD_GND',7:name+'_ILIM',8:name+'_DVDT',9:name+'_FIELD_FAULT_N',10:name+'_24V',11:'FIELD_GND'}
  sw=add('SW24',pins,'independent probe latch-off eFuse;current/short bound remains source gate');ilim=res(name+'_ILIM','FIELD_GND',49900,'unqualified49.9k limit candidate, no invented guaranteedpoint');res('FIELD_A_24V_PROTECTED',name+'_UVLO',1000000,'TI disableexternalUVLOvia>=1M;parententry enforces19–30V');res('DOA_FIELD_3V3',name+'_SHDN_N',10000,'probe on withfieldrail ready;no software automaticclear');res(name+'_SHDN_N','FIELD_GND',100000,'field3V3 absent defaults shutdown');res(name+'_FIELD_FAULT_N','DOA_FIELD_3V3',10000,'fieldlocal fault pull-up;never bridge toLOGIC');res(name+'_24V','FIELD_GND',100000,'passive supplybleed')
  cap(name+'_DVDT','FIELD_GND',10,'inrush slew setting;startup tolerance unqualified')
  for net in ['FIELD_A_24V_PROTECTED',name+'_24V']:cap(net,'FIELD_GND',100,sw+' bypass');cap(net,'FIELD_GND',1000,sw+' storage;effectivecapmustmeasure')
  probe_powers.append({'name':name,'switch_ref':sw,'ilim_ref':ilim,'normal_load_a':.1,'frozen_limit_max_a':.15,'ilim_ohm':49900,'guaranteed_current_bounds_available':False,'hard_short_bound_available':False,'engineering_gate':'TI exact49.9k overload/hardshort bound or qualified alternative required;44.2k .159A maximum violates .150A contract'})
 iso=add('ISO2',{1:'FIELD_GND',2:None,3:'DOA_FIELD_3V3',4:'PRB0_FIELD_FAULT_N',5:'PRB1_FIELD_FAULT_N',6:None,7:None,8:'FIELD_GND',9:'LOGIC_GND',10:None,11:None,12:'PRB1_FAULT_GOOD_ISO',13:'PRB0_FAULT_GOOD_ISO',14:'IO_3V3',15:None,16:'LOGIC_GND'},'two real field fault observations;Fvariant defaultLOW on missinginputpower')
 cap('DOA_FIELD_3V3','FIELD_GND',100,iso+' field bypass');cap('IO_3V3','LOGIC_GND',100,iso+' logic bypass');faultgood+=['PRB0_FAULT_GOOD_ISO','PRB1_FAULT_GOOD_ISO']
 faultnets=['ENC0_SUPPLY_FAULT','ENC1_SUPPLY_FAULT','ENC2_SUPPLY_FAULT','ENC3_SUPPLY_FAULT','MPG_SUPPLY_FAULT','XF_SUPPLY_FAULT','PRB0_SUPPLY_FAULT','PRB1_SUPPLY_FAULT']
 for bank in range(2):
  pins={7:'LOGIC_GND',14:'IO_3V3'}
  for j,(ip,op) in enumerate([(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)]):
   i=bank*6+j;pins[ip]=faultgood[i] if i<8 else 'LOGIC_GND';pins[op]=faultnets[i] if i<8 else None
  inv=add('INV6',pins,'active-LOW fault/isolatedgood converted to active-HIGH status;unusedinputs grounded');cap('IO_3V3','LOGIC_GND',100,inv+' bypass')
 # Dedicatedunfiltered2probe channels;no ordinaryDI used/no10nF inputs.
 probe=add('ISO1212',{1:'LOGIC_GND',2:'IO_3V3',3:'IO_3V3',4:'PROBE_FPGA',5:'TOOLSETTER_FPGA',6:None,7:None,8:'LOGIC_GND',9:'FIELD_GND',10:'PRB1_IN_SENSE',11:'PRB1_SENSE',12:'PRB1_SUB_ISLAND',13:'PRB0_SUB_ISLAND',14:'FIELD_GND',15:'PRB0_IN_SENSE',16:'PRB0_SENSE'},'dedicated isolated unfiltered fast probes;SUB separate copperislands')
 cap('IO_3V3','LOGIC_GND',100,probe+' bypass');cap('IO_3V3','LOGIC_GND',1000,probe+' localstorage')
 for i,out in enumerate(['PROBE_FPGA','TOOLSETTER_FPGA']):
  res(f'PRB{i}_IN',f'PRB{i}_IN_SENSE',1000,'unfiltered Type3 threshold resistance',mpn='SMM02040C1001FB300',fp='Resistor_SMD:R_MiniMELF_MMA-0204');res(f'PRB{i}_IN_SENSE',f'PRB{i}_SENSE',562,'Type3 current-settingresistor',mpn='CRCW0603562RFKEA');res(out,'LOGIC_GND',100000,'probe LOW when frontend unpowered/highZ');tvs(f'PRB{i}_IN','FIELD_GND',True)
 # Physical far-end marker and24bit chain, nearestH shiftedfirst=bit0.
 bits=active[:12]+['XF_SUPPLY_FAULT','MPG_SUPPLY_FAULT','PRB0_SUPPLY_FAULT','PRB1_SUPPLY_FAULT']+faultnets[:4]+['LOGIC_GND','IO_3V3','LOGIC_GND','IO_3V3']
 srrefs=[]
 for bank in range(3):
  pins={1:'FAST_SR_LOAD_BUFFER',2:'FAST_SR_CLK_BUFFER',7:None,8:'LOGIC_GND',9:'FAST_SR_DATA_SOURCE' if bank==0 else f'FAST_SR_CHAIN{bank}',10:'LOGIC_GND' if bank==2 else f'FAST_SR_CHAIN{bank+1}',15:'LOGIC_GND',16:'IO_3V3'}
  for j,pin in enumerate([6,5,4,3,14,13,12,11]):pins[pin]=bits[bank*8+j]
  sr=add('SR',pins,'read-only parallel-in register;bank'+str(bank)+' Hfirst');cap('IO_3V3','LOGIC_GND',100,sr+' bypass');srrefs.append(sr)
 res('FAST_SR_CLK','FAST_SR_CLK_BUFFER',33,'source damping;loaded6.25MHz timingrequiresPCBproof');res('FAST_SR_LOAD_N','FAST_SR_LOAD_BUFFER',33,'load-line damping');res('FAST_SR_CLK','LOGIC_GND',10000,'idleclockLOW');res('FAST_SR_LOAD_N','IO_3V3',10000,'idleloadreleasedHIGH');res('FAST_SR_DATA_SOURCE','FAST_SR_DATA',33,'shiftdata source damping');res('FAST_SR_DATA','LOGIC_GND',100000,'missing chain reads invalid marker')
 # Actual2.5V single-ended MPG bias,1mAexternalloadscreen—not expandableRAM.
 ref=add('SHUNT',{1:'MPG_VREF_CORE',2:'LOGIC_GND',3:'LOGIC_GND'},'2.5V shunt reference;TI recommendsNCpinconnectedtoanode inEMIenvironment');res('MOTION_5V_RAW','MPG_VREF_CORE',1800,'feed reference plus1mAexternalload atminimumrail');res('MPG_VREF_CORE','MPG_VREF',22,'resistor-fedexternalbias rated1mA');cap('MPG_VREF_CORE','LOGIC_GND',100,ref+' referenceRFbypass')
 boundary('J14001',['IO_3V3','LOGIC_GND','MOTION_5V_RAW','DOA_FIELD_3V3','FIELD_A_24V_PROTECTED','FIELD_GND'],'realparent powerdomains')
 boundary('J14002',['FAST_SR_CLK','FAST_SR_LOAD_N','FAST_SR_DATA','PROBE_FPGA','TOOLSETTER_FPGA','FAST_PORTS_ENABLE','XF_POWER_ENABLE','FPGA_CDONE'],'FPGA status/probe,actualconfigurationdone andtwoexplicitnewqualificationcontrolpins')
 boundary('J14003',contacts+['MPG_VREF'],'operator terminals;exactphysicalplugs ownedparent')
 boundary('J14004',['PRB0_IN','PRB0_24V','FIELD_GND','PRB1_IN','PRB1_24V','FIELD_GND'],'two fastprobeports')
 boundary('J14005',[n+'_5V' for n in ['ENC0','ENC1','ENC2','ENC3','MPG','FREQ']]+['LOGIC_GND'],'sixlogicportpowerfeeds')
 return {'schema_version':1,'revision':'motherboard-operator-r0.1','parent_reference_index':14,'one_custom_board':True,'manufacturing_ready':False,'physical_qualification':False,'firmware_implemented':False,'components':parts,'boundaries':bounds,'fitted_component_count':len(parts),'fitted_pad_count':sum(len(p['pins']) for p in parts.values()),'contacts':contactrecords,'ports_5v':portrecords,'ports_24v':probe_powers,'probe_ref':probe,'sr_refs':srrefs,'sr_serialized_bits':bits,'marker_word':10,'marker_bits':[20,21,22,23],'shift_first':'nearestH=bit0','poll_period_s':.0001,'read_clock_hz':6250000,'double_read_agreement_required':True,'three_bad_markers_latch_fault':True,'external_probes_consume_general_DI':False,'voltage_adc_implemented':False,'unimplemented_obligations':['Source-bound guaranteed49.9k probe current/short limits; no44.2k .159A guarantee meets .150A cap.','FPGA two newenablepinallocation, RTL marker/polarity/qualification/age validity; noconstanthealthy.','Six5V FAULT flags do not prove rail voltage; onlyvalid withactualMOTION railmonitor andqualifiedregion;unpowered frontend validity mustfall.','Unfilteredprobe threshold/timing/TVS,contact EMC/partialpower/cable qualification;neverattach24V to5V selector ports.','Exactport ENrestart/faultpolicy,capacitancedCbias,shortenergy,thermal andassemblyverification.','PWM/process,analog/comms/fourthIOL1node/accessory1-Wire andphysicalconnectors remain separate sourcework.']}

def footprints(out):
 lib=out/'CNC_MB_Operator.pretty';lib.mkdir(exist_ok=True)
 (lib/'ISO1212_DBQ16_TI.kicad_mod').write_text(iso_footprint(),encoding='utf-8')
 source=ROOT/'hardware/motherboard_power_entry/CNC_MB_Entry.pretty/TPS2662_DRC10_TI.kicad_mod'
 shutil.copyfile(source,lib/source.name)
 text='(footprint "TPD1E10B06_DPY2_TI"(version 20241229)(generator "controller_hardware")(layer "F.Cu")(descr "TI DPY0002A4224561/C07/2024 .5x.3 pads .7pitch;bidirectional2pin")(attr smd)(property "Reference" "REF**"(at 0 -1)(layer "F.SilkS")(effects(font(size .7 .7)(thickness .1))))(property "Value" "TPD1E10B06_DPY2_TI"(at 0 1)(layer "F.Fab")(effects(font(size .7 .7)(thickness .1))))(fp_rect(start -.525 -.325)(end .525 .325)(stroke(width .1)(type default))(layer "F.Fab"))(fp_rect(start -.85 -.6)(end .85 .6)(stroke(width .05)(type default))(layer "F.CrtYd"))'
 for n,x in [(1,-.35),(2,.35)]:text+=f'(pad "{n}" smd roundrect(at {x} 0)(size .3 .5)(layers "F.Cu" "F.Paste" "F.Mask")(roundrect_rratio .166667))'
 (lib/'TPD1E10B06_DPY2_TI.kicad_mod').write_text(dump(parse(text+')'))+'\n',encoding='utf-8')
 (out/'fp-lib-table').write_text(dump(parse('(fp_lib_table(version 7)(lib(name "CNC_MB_Operator")(type "KiCad")(uri "${KIPRJMOD}/CNC_MB_Operator.pretty")(options "")(descr "Primarysource reviewed operator/probe footprints")))'))+'\n',encoding='utf-8')

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
  yes='yes' if p['physical'] else 'no';items.append(f'(symbol(lib_id "CNC:{p["kind"]}")(at {x} {y} 0)(unit 1)(in_bom {yes})(on_board {yes})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_operator"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
  for n,_,px,py,_,_ in layout:
   sx,sy=round(x+px,4),round(y-py,4);net=p['pins'][str(n)]
   if net is None:items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(n)+"nc")}"))');continue
   dx=-5.08 if px<0 else 5.08 if px>0 else 0;dy=0 if px else 5.08;ex,ey=round(sx+dx,4),round(sy+dy,4)
   items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"wire")}"))');items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.65,"(justify right bottom)" if px<0 else "(justify left bottom)")}(uuid "{uid(ref+str(n)+"label")}"))');netmap.setdefault(net,[]).append([ref,str(n)])
 for i,net in enumerate(['IO_3V3','LOGIC_GND','MOTION_5V_RAW','DOA_FIELD_3V3','FIELD_A_24V_PROTECTED','FIELD_GND']):
  ref=f'#FLG14{i}';x=30.48+i*139.7;y=1600.2;items.append(f'(symbol(lib_id "CNC:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid "{uid(ref)}")(property "Reference" "{ref}"(at {x} {y} 0){effects(1,"hide")})(property "Value" "PARENT SUPPLY"(at {x} {y} 0){effects(1,"hide")})(instances(project "motherboard_operator"(path "/{root}"(reference "{ref}")(unit 1)))))(label "{net}"(at {x} {y} 0){effects(.8)}(uuid "{uid(ref+"label")}"))')
 note='ACTUAL OPERATOR/FAST-PROBE/PORT SOURCE / 12contactinputs,2dedicatedprobes,8independentportlimiters,24bitreadonlystatus.\nSourcecandidate only: 49.9k probe guaranteedcurrent/shortbound notestablished;loadedRTL,EMC,thermal,capbias andphysicalconnectorsremain.\nNo generalDI consumed,nofakehealthy,noextra customcards. Fault flags are not portvoltage measurements.'
 items.append(f'(text {quote(note)}(at 20.32 17.78 0){effects(1.4,"(justify left top)")}(uuid "{uid(note)}"))')
 raw=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{root}")(paper "User" 1270 1650)(title_block(title "Motherboard operator/probes/protected ports")(date "2026-09-30")(rev "r0.1"))(lib_symbols'+''.join(libs)+')'+''.join(items)+')'
 (out/'motherboard_operator.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf-8');(out/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in libs)+')'))+'\n',encoding='utf-8');(out/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Operator source")))'))+'\n',encoding='utf-8');(out/'motherboard_operator.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_operator.kicad_pro','version':1},'erc':{'rule_severities':{k:'warning' for k in ['single_global_label','four_way_junction','simulation_model_issue','footprint_filter']}}},indent=2)+'\n');footprints(out)
 for name,obj in [('design',d),('pin-map',netmap),('boundary-map',d['boundaries'])]:(out/(name+'.json')).write_text(json.dumps(obj,indent=2)+'\n')
 with (out/'bom.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['Reference','Value','MPN','Footprint','Status']);w.writeheader();w.writerows({'Reference':ref,'Value':p['value'],'MPN':p['mpn'],'Footprint':p['footprint'],'Status':'source_candidate_not_qualified'} for ref,p in d['components'].items())
 print(json.dumps({'components':len(d['components']),'pads':d['fitted_pad_count'],'manufacturing_ready':False}));return d

if __name__=='__main__':build()
