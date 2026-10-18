"""Build sixteen sourcing DO frontends, with real isolated SPI and inhibit gates.

One motherboard source region, not an output daughtercard or fabrication release.
Unimplemented parent power, local controller and field connector boundaries are
explicitly excluded from the PCB/BOM. Reference index 10 is reserved here.
"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import shutil
import uuid
from hardware_build_assembly import parse, dump
from hardware_build_tx_schematic import symbol, effects, quote

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/motherboard_do'
SOURCES = ROOT / 'reports/motherboard-do-20260930/sources'
NS = uuid.UUID('04b645d1-c086-40f7-b737-eb0d2a2a6828')
PIN_FUNCTIONS = {
 'TPS': {1:('READY','output'),2:('FLT_N','open_collector'),3:('DO_EN','input'),4:('VDD','power_in'),5:('GND','power_in'),6:('ISNS','passive'),7:('SDO','tri_state'),8:('SDI','input'),9:('SCLK','input'),10:('CS_N','input'),11:('RCB3','output'),12:('OUT3','passive'),13:('OUT3','passive'),14:('VS','power_in'),15:('VS','power_in'),16:('VS','power_in'),17:('VS','power_in'),18:('OUT4','passive'),19:('OUT4','passive'),20:('RCB4','output'),21:('GND','power_in'),22:('LEDOUT1','output'),23:('LEDOUT2','output'),24:('LEDOUT3','output'),25:('LEDOUT4','output'),26:('DNC','no_connect'),27:('DNC','no_connect'),28:('DSPI','input'),29:('REG_EN','input'),30:('ADDCFG','passive'),31:('RCB2','output'),32:('OUT2','passive'),33:('OUT2','passive'),34:('VS','power_in'),35:('VS','power_in'),36:('VS','power_in'),37:('VS','power_in'),38:('OUT1','passive'),39:('OUT1','passive'),40:('RCB1','output'),41:('EP_GND','power_in')},
 'ISO': {1:('VCC1','power_in'),2:('INA','input'),3:('INB','input'),4:('INC','input'),5:('IND','input'),6:('OUTE','output'),7:('OUTF','output'),8:('GND1','power_in'),9:('GND2','power_in'),10:('INF','input'),11:('INE','input'),12:('OUTD','output'),13:('OUTC','output'),14:('OUTB','output'),15:('OUTA','output'),16:('VCC2','power_in')},
 'DFF': {1:('CLK','input'),2:('D','input'),3:('Q_N','output'),4:('GND','power_in'),5:('Q','output'),6:('CLR_N','input'),7:('PRE_N','input'),8:('VCC','power_in')},
 'AND4': {1:('1A','input'),2:('1B','input'),3:('1Y','output'),4:('2A','input'),5:('2B','input'),6:('2Y','output'),7:('GND','power_in'),8:('3Y','output'),9:('3A','input'),10:('3B','input'),11:('4Y','output'),12:('4A','input'),13:('4B','input'),14:('VCC','power_in')},
 'NMOS': {1:('S','passive'),2:('S','passive'),3:('S','passive'),4:('G','input'),5:('D','passive'),6:('D','passive'),7:('D','passive'),8:('D','passive'),9:('EP_D','passive')},
 'R':{1:('','passive'),2:('','passive')},'C':{1:('','passive'),2:('','passive')}
}
MPNS = {'TPS':('TPS274C65ASRHAR','CNC_MB_DO:TPS274C65_RHA40_TI'), 'ISO':('ISO7762FDBQR','CNC_MB_DO:ISO7762_DBQ16_TI'), 'DFF':('SN74LVC1G74DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm'), 'AND4':('SN74LVC08APWR','Package_SO:TSSOP-14_4.4x5mm_P0.65mm'), 'NMOS':('CSD19538Q3AT','CNC_MB_DO:CSD19538_DNH8_TI')}

def description():
    parts={}; boundaries={}; channels=[]; domains=[]; u=r=c=10000
    def add(kind,pins,role,ref=None,**more):
        nonlocal u
        if ref is None: u+=1; ref=f'U{u}'
        mpn,fp=MPNS[kind]
        parts[ref]={'kind':kind,'mpn':mpn,'value':mpn,'footprint':fp,'physical':True,'pins':{str(k):v for k,v in pins.items()},'role':role,**more}
        return ref
    def resistor(a,b,value,role,tolerance=.01):
        nonlocal r
        r+=1; ref=f'R{r}'
        mpn={1000:'CRCW06031K00FKEA',10000:'CRCW060310K0FKEA',13300:'TNPW060313K3BEEA',17800:'TNPW060317K8BEEA'}[value]
        parts[ref]={'kind':'R','mpn':mpn,'value':f'{value}R {100*tolerance:g}%','footprint':'Resistor_SMD:R_0603_1608Metric','physical':True,'pins':{'1':a,'2':b},'role':role,'resistance_ohm':value,'tolerance':tolerance}
        return ref
    def capacitor(a,b,nf,role):
        nonlocal c
        c+=1; ref=f'C{c}'
        mpn,fp,rating={.1:('GRM1885C1H101JA01D','Capacitor_SMD:C_0603_1608Metric',50),22:('C0805C223K1RACTU','Capacitor_SMD:C_0805_2012Metric',100),100:('GRM188R72A104KA35D','Capacitor_SMD:C_0603_1608Metric',100),1000:('GRM188R71H105KA12D','Capacitor_SMD:C_0603_1608Metric',50),2200:('GRM21BR71C225KA12L','Capacitor_SMD:C_0805_2012Metric',16)}[nf]
        parts[ref]={'kind':'C','mpn':mpn,'value':f'{nf:g}nF {rating}V','footprint':fp,'physical':True,'pins':{'1':a,'2':b},'role':role,'capacitance_f':nf*1e-9,'voltage_rating_v':rating,'tolerance':.05 if nf==.1 else .1}
        return ref
    def boundary(ref,nets,role):
        boundaries[ref]={'kind':'Boundary'+str(len(nets)),'physical':False,'mpn':'','footprint':'','value':'UNIMPLEMENTED PARENT: '+role,'pins':{str(i+1):net for i,net in enumerate(nets)},'role':role,'status':'unimplemented_parent_boundary_excluded_from_PCB'}
    for bank,letter in enumerate(('A','B')):
        dom=f'DO{letter}'; gnd=f'FIELD_{letter}_0V'; vs=f'FIELD_{letter}_24V'; vdd=f'{dom}_FIELD_3V3'
        latch=add('DFF',{1:f'{dom}_IO_ENABLE_STROBE',2:'IO_3V3',3:None,4:'LOGIC_GND',5:f'{dom}_OUT_EN_LATCH',6:f'{dom}_CLR_N',7:'IO_3V3',8:'IO_3V3'},'permission drop/reset requires a new enable edge')
        gate=add('AND4',{1:f'OUT_PERMIT_{letter}',2:f'{dom}_CONTROLLER_RESET_N',3:f'{dom}_CLR_N',4:f'OUT_PERMIT_{letter}',5:f'{dom}_OUT_EN_LATCH',6:f'{dom}_PERMIT_LATCHED',7:'LOGIC_GND',8:f'{dom}_DO_EN_LOGIC',9:f'{dom}_PERMIT_LATCHED',10:f'{dom}_CARD_EN',11:None,12:'LOGIC_GND',13:'LOGIC_GND',14:'IO_3V3'},'hardwired permit/latch/local-controller AND; unused gate grounded')
        iso=add('ISO',{1:'IO_3V3',2:f'{dom}_SCLK_HOST',3:f'{dom}_SDI_HOST',4:f'{dom}_CS_N_HOST',5:f'{dom}_DO_EN_LOGIC',6:f'{dom}_SDO_HOST',7:f'{dom}_FLT_N_HOST',8:'LOGIC_GND',9:gnd,10:f'{dom}_FLT_N_FIELD',11:f'{dom}_SDO_FIELD',12:f'{dom}_DO_EN_FIELD',13:f'{dom}_CS_N_FIELD',14:f'{dom}_SDI_FIELD',15:f'{dom}_SCLK_FIELD',16:vdd},'F variant: all missing-input outputs default LOW')
        for ref in (latch,gate): capacitor('IO_3V3','LOGIC_GND',100,ref+' logic decoupling')
        capacitor('IO_3V3','LOGIC_GND',100,iso+' logic-side decoupling'); capacitor(vdd,gnd,100,iso+' field-side decoupling')
        for net in (f'OUT_PERMIT_{letter}',f'{dom}_CONTROLLER_RESET_N',f'{dom}_IO_ENABLE_STROBE',f'{dom}_CARD_EN',f'{dom}_DO_EN_LOGIC',f'{dom}_SCLK_HOST',f'{dom}_SDI_HOST'):
            resistor(net,'LOGIC_GND',10000,'logic fail-off/default bias')
        resistor(f'{dom}_CS_N_HOST','IO_3V3',10000,'host SPI default deselected')
        resistor(f'{dom}_DO_EN_FIELD',gnd,10000,'local DO_EN external pull-off')
        resistor(f'{dom}_SCLK_FIELD',gnd,10000,'field SPI idle LOW'); resistor(f'{dom}_SDI_FIELD',gnd,10000,'field SPI idle LOW')
        resistor(f'{dom}_CS_N_FIELD',vdd,10000,'field SPI pull-up; F isolator overrides LOW with missing host')
        resistor(f'{dom}_SDO_FIELD',gnd,10000,'inactive SDO has bounded local state'); resistor(f'{dom}_FLT_N_FIELD',vdd,10000,'wired OR fault pull-up')
        drivers=[]
        for quad in range(2):
            base=bank*8+quad*4; tag=f'{dom}_Q{quad}'
            pins={1:tag+'_READY_N',2:f'{dom}_FLT_N_FIELD',3:f'{dom}_DO_EN_FIELD',4:vdd,5:gnd,6:tag+'_ISNS',7:f'{dom}_SDO_FIELD',8:f'{dom}_SDI_FIELD',9:f'{dom}_SCLK_FIELD',10:f'{dom}_CS_N_FIELD',11:f'DO{base+2:02}_RCB_GATE',12:f'DO{base+2:02}_SW',13:f'DO{base+2:02}_SW',18:f'DO{base+3:02}_SW',19:f'DO{base+3:02}_SW',20:f'DO{base+3:02}_RCB_GATE',21:gnd,22:None,23:None,24:None,25:None,26:None,27:None,28:gnd,29:gnd,30:tag+'_ADDRESS',31:f'DO{base+1:02}_RCB_GATE',32:f'DO{base+1:02}_SW',33:f'DO{base+1:02}_SW',38:f'DO{base:02}_SW',39:f'DO{base:02}_SW',40:f'DO{base:02}_RCB_GATE',41:gnd}
            pins.update({pin:vs for pin in (*range(14,18),*range(34,38))})
            driver=add('TPS',pins,'quad sourcing output / internal ADC / RCB gate driver',spi_address=quad,channel_ids=list(range(base,base+4)),internal_regulator_enabled=False)
            drivers.append(driver)
            resistor(tag+'_ADDRESS',gnd,13300 if quad==0 else 17800,'addressed SPI identity resistor',.001)
            resistor(tag+'_READY_N',gnd,10000,'datasheet READY pin resistor to GND')
            resistor(tag+'_ISNS',gnd,1000,'sense current to internal ADC voltage')
            capacitor(tag+'_ISNS',gnd,.1,'SNS ADC low-pass filter')
            capacitor(vdd,gnd,2200,'TI recommended VDD stabilizer'); capacitor(vdd,gnd,100,'local VDD HF bypass')
            capacitor(vs,gnd,100,'local VS HF bypass'); capacitor(vs,gnd,1000,'local VS MLCC; external bank bulk remains required')
            for ch in range(4):
                i=base+ch
                fet=add('NMOS',{1:f'DO{i:02}_SW',2:f'DO{i:02}_SW',3:f'DO{i:02}_SW',4:f'DO{i:02}_RCB_GATE',5:f'DO{i:02}',6:f'DO{i:02}',7:f'DO{i:02}',8:f'DO{i:02}',9:f'DO{i:02}'},'reverse blocking: body diode from switch output/source toward terminal/drain')
                outputcap=capacitor(f'DO{i:02}',gnd,22,'TI output RF/transient filter after RCB FET')
                channels.append({'id':f'DO{i}','logical_net':f'DO{i:02}','bank':letter,'driver':driver,'chip_channel':ch+1,'rcb_fet':fet,'output_filter':outputcap,'continuous_limit_a':.5,'group_continuous_limit_a':2.0,'group':base,'paired_ilim_resource':f'{driver}_ILIM_'+('12' if ch<2 else '34'),'default_current_limit_code':6})
        boundary(f'J{10001+bank}',[f'DO{i:02}' for i in range(bank*8,bank*8+8)]+[gnd]*4,'XDO'+str(bank)+' field connector not selected')
        boundary(f'J{10003+bank}',[vs,gnd,vdd],'protected field entry and same-VS-derived 3V3 supply not drawn')
        boundary(f'J{10005+bank}',['IO_3V3','LOGIC_GND',f'OUT_PERMIT_{letter}',f'{dom}_CONTROLLER_RESET_N',f'{dom}_IO_ENABLE_STROBE',f'{dom}_CARD_EN',f'{dom}_SCLK_HOST',f'{dom}_SDI_HOST',f'{dom}_CS_N_HOST',f'{dom}_SDO_HOST',f'{dom}_FLT_N_HOST'],'local IOL1 controller/watchdog/reset/readout not drawn')
        domains.append({'id':dom,'bank':letter,'channels':list(range(bank*8,bank*8+8)),'driver_refs':drivers,'isolator_ref':iso,'latch_ref':latch,'gate_ref':gate,'field_supply':vs,'field_logic_supply':vdd,'field_return':gnd,'logic_return':'LOGIC_GND','field_logic_supply_implemented':False,'controller_implemented':False,'serial_watchdog_implemented':False,'physical_connector_implemented':False})
    return {'schema_version':1,'revision':'motherboard-do-r0.1','parent_reference_index':10,'manufacturing_ready':False,'physical_qualification':False,'status':'source_candidate_not_qualified','channel_count':16,'banks':2,'quad_count':4,'source_driver_mpn':'TPS274C65ASRHAR','continuous_limit_a_per_channel':.5,'continuous_limit_a_per_quad':2.0,'paired_current_limits':True,'limits_enforced_by_firmware':False,'driver_por_current_limit_a':1.25,'driver_commission_current_limit_a':[.62,.72,.82],'driver_commission_current_limit_code':6,'hardware_disable_equation':'OUT_PERMIT_k AND OUT_EN_LATCH_Q AND CARD_EN; latch CLR_N = OUT_PERMIT_k AND CONTROLLER_RESET_N','no_automatic_reenable':True,'hardware_gate_is_complete':True,'whole_permission_path_complete':False,'measurement':{'path':'ISNS RC -> internal TPS 10-bit ADC -> addressed CRC SPI -> ISO7762F -> local IOL1 controller boundary','host_measurement_implemented':False,'adc_reference_v':[2.72,2.85],'conversion_s':128e-6,'sample_current_valid_only_while_on':True,'calibration_implemented':False},'register_requirements':{'SW_STATE':0,'FS_SW_STATE':0,'DEV_CONFIG1':6,'DEV_CONFIG2':6,'DEV_CONFIG3':64,'CRC_EN':True,'ADC_EN':True,'WD_EN':True,'WD_TO':0,'watchdog_nominal_s':400e-6,'AUTO_RETRY_DIS':True,'SW_STATE_zero_readback_before_CARD_EN':True,'per_chip_configuration_readback_before_enable':True,'IOL1_crc_epoch_sequence_freshness_validate_before_commit':True,'inrush_boost_allowed':False,'parallel_channels_allowed':False,'off_state_open_load_excitation_default_allowed':False},'unimplemented_parent_obligations':['Two field-derived VDD supplies, power-good and safe sequencing; never parallel TPS internal VDD regulators.','Local IOL1 controllers, 1ms accepted-frame timeout / <=2ms independent IWDG, reset, epoch enable and physical qualification; no constant CARD_EN/identity.','SPI/ADC CRC driver, configuration/readback limits/calibration, fault latching, bank current/thermal/load qualification and CLI/UI integration.','Protected field entry/bank bulk/surge clamp and output cable inductive-energy/EMC protection; TVS placeholder is deliberately not fitted.','Final connectors, return current/copper/thermal vias, clearance/isolation/stencil and PCB layout.','Actual output observations/status LEDs; unused LEDOUT pins do not prove observed output state.'], 'domains':domains,'channels':channels,'components':parts,'boundaries':boundaries,'fitted_component_count':len(parts),'fitted_pad_count':sum(len(x['pins']) for x in parts.values())}

def footprints(out):
    fpdir=out/'CNC_MB_DO.pretty'; fpdir.mkdir(exist_ok=True)
    def wrap(name,pads,body,court,desc):
        x,y=body; cx,cy=court
        return f'(footprint "{name}"(version 20250108)(generator "controller_hardware")(layer "F.Cu")(descr {quote(desc)})(attr smd)(property "Reference" "REF**"(at 0 {-cy-1})(layer "F.SilkS"){effects()})(property "Value" "{name}"(at 0 {cy+1})(layer "F.Fab"){effects()})(fp_rect(start {-x} {-y})(end {x} {y})(stroke(width .1)(type default))(fill none)(layer "F.Fab"))(fp_rect(start {-cx} {-cy})(end {cx} {cy})(stroke(width .05)(type default))(fill none)(layer "F.CrtYd"))(fp_circle(center {-x+.3} {-y+.3})(end {-x+.4} {-y+.3})(stroke(width .1)(type default))(fill none)(layer "F.Fab"))'+''.join(pads)+')'
    pads=[]
    for n in range(1,41):
        if n<=10:x,y,w,h=-2.9,-2.25+(n-1)*.5,.6,.25
        elif n<=20:x,y,w,h=-2.25+(n-11)*.5,2.9,.25,.6
        elif n<=30:x,y,w,h=2.9,2.25-(n-21)*.5,.6,.25
        else:x,y,w,h=2.25-(n-31)*.5,-2.9,.25,.6
        pads.append(f'(pad "{n}" smd rect(at {x:g} {y:g})(size {w:g} {h:g})(layers "F.Cu" "F.Paste" "F.Mask"))')
    pads.append('(pad "41" smd rect(at 0 0)(size 4.15 4.15)(layers "F.Cu" "F.Mask"))')
    for x in (-1.37,0,1.37):
        for y in (-1.37,0,1.37): pads.append(f'(pad "" smd rect(at {x} {y})(size 1.17 1.17)(layers "F.Paste"))')
    name='TPS274C65_RHA40_TI'; (fpdir/(name+'.kicad_mod')).write_text(dump(parse(wrap(name,pads,(3.05,3.05),(3.45,3.45),'TI RHA0040M drawing4226110/A example; thermal vias belong to PCB; not stencil-qualified')))+'\n',encoding='utf-8')
    iso=ROOT/'hardware/motherboard_di/CNC_MB_DI.pretty/ISO1212_DBQ16_TI.kicad_mod'
    text=iso.read_text(encoding='utf-8').replace('ISO1212_DBQ16_TI','ISO7762_DBQ16_TI').replace('TI ISO1212','TI ISO7762')
    (fpdir/'ISO7762_DBQ16_TI.kicad_mod').write_text(text,encoding='utf-8')
    pads=[]
    for n in range(1,5):
        y=-.975+(n-1)*.65
        pads.append(f'(pad "{n}" smd rect(at -1.55 {y:g})(size .7 .4)(layers "F.Cu" "F.Mask")(solder_mask_margin -.05))')
        pads.append(f'(pad "" smd rect(at -1.55 {y:g})(size .6 .3)(layers "F.Paste"))')
    # DNH mask-defined comb is represented by same-net numbered fingers and
    # central drain pad. Adjacent overlaps are intentional inside one footprint.
    for n in range(5,9):
        y=.975-(n-5)*.65
        pads.append(f'(pad "{n}" smd rect(at 1.55 {y:g})(size .7 .4)(layers "F.Cu" "F.Mask")(solder_mask_margin -.05))')
        pads.append(f'(pad "" smd rect(at 1.55 {y:g})(size .6 .3)(layers "F.Paste"))')
    pads.append('(pad "9" smd rect(at .3275 0)(size 1.875 2.55)(layers "F.Cu" "F.Mask")(solder_mask_margin -.05))')
    for x in (-.208,.697):
        for y in (-.6625,.6625): pads.append(f'(pad "" smd rect(at {x} {y})(size .705 1.125)(layers "F.Paste"))')
    name='CSD19538_DNH8_TI'; (fpdir/(name+'.kicad_mod')).write_text(dump(parse(wrap(name,pads,(1.75,1.75),(2.15,2),'TI DNH0008A4222499/C02/2025 mask-defined lands; 1-3S4G5-8/9D; rounding omitted prototype candidate')))+'\n',encoding='utf-8')
    review={'TPS274C65_RHA40_TI':{'source':'tps274c65.pdf pp90-92 RHA0040M4226110/A07/2020','pads':41,'pitch_mm':.5,'perimeter_lands_mm':[.6,.25],'centres_mm':2.9,'EP_mm':[4.15,4.15],'paste_apertures':9,'paste_aperture_mm':[1.17,1.17],'thermal_vias':'actual PCB mandatory; filled/plugged/capped beneath paste, >=85% assembled solder coverage; 72% stencil printed area is different','RHA0040B_also_in_datasheet':'same package/pin numbering, alternative example0.22mm lands; M example chosen, vendor lot/stencil review remains'},'ISO7762_DBQ16_TI':{'source':'iso7760.pdf pp49-51 DBQ0016A4214846/A03/2014','shared_geometry_source':str(iso.relative_to(ROOT)).replace('\\','/'),'source_sha256':hashlib.sha256(iso.read_bytes()).hexdigest(),'pads':16,'pad_mm':[1.6,.41],'x_mm':2.7,'pitch_mm':.635},'CSD19538_DNH8_TI':{'source':'csd19538q3a.pdf pp1,10-12 DNH0008A4222499/C02/2025','pads':9,'pin_functions':'1-3 SOURCE,4 GATE,5-8+9 DRAIN; verified rendered TOP VIEW, not extraction order','left_centres_x_mm':-1.55,'right_centres_x_mm':1.55,'pitch_mm':.65,'central_copper_mm':[1.875,2.55],'central_mask_mm':[1.775,2.45],'central_x_mm':.3275,'finger_copper_mm':[.7,.4],'finger_mask_mm':[.6,.3],'paste_apertures':4,'paste_aperture_mm':[.705,1.125],'square_corner_allowance':'TI example R0.05 corners omitted; bounding lands/paste dimensions preserved; board/stencil assembly review remains'},'manufacturing_ready':False,'stencil_approved':False,'PCB_thermal_isolation_approved':False}
    (out/'footprint-review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
    (out/'fp-lib-table').write_text(dump(parse('(fp_lib_table(version 7)(lib(name "CNC_MB_DO")(type "KiCad")(uri "${KIPRJMOD}/CNC_MB_DO.pretty")(options "")(descr "Reviewed motherboard DO prototype lands")))'))+'\n',encoding='utf-8')

def build(out=OUT):
    out=Path(out);out.mkdir(parents=True,exist_ok=True); model=description(); parts={**model['components'],**model['boundaries']}; uid=lambda n:str(uuid.uuid5(NS,n)); root=uid('root'); functions=dict(PIN_FUNCTIONS)
    for p in model['boundaries'].values(): functions[p['kind']]={int(k):(k,'passive') for k in p['pins']}
    functions['PWR_FLAG']={1:('pwr','power_out')}; layouts={}; libs=[]
    for kind,table in functions.items():
        if kind in ('R','C'): layout=[(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')]; body='(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))'
        elif kind=='PWR_FLAG': layout=[(1,'pwr',0,0,90,'power_out')]; body=''
        else:
            right=[n for n,(_,t) in table.items() if t in ('output','tri_state','open_collector')]; left=[n for n in table if n not in right]
            if kind=='NMOS':left=[1,2,3,4];right=[5,6,7,8,9]
            if kind=='TPS':left=[1,2,3,4,5,6,7,8,9,10,21,22,23,24,25,26,27,28,29,30,41];right=[n for n in table if n not in left]
            layout=[(n,table[n][0],sign*12.7,20.32-i*5.08,0 if sign<0 else 180,table[n][1]) for sign,keys in [(-1,left),(1,right)] for i,n in enumerate(keys)]
            low=min(x[3] for x in layout)-5.08; body=f'(rectangle(start -10.16 25.4)(end 10.16 {low})(stroke(width .254)(type default))(fill(type background)))'
        layouts[kind]=layout;libs.append(symbol(kind,layout,body,kind if kind in ('R','C') else 'J' if kind.startswith('Boundary') else '#FLG' if kind=='PWR_FLAG' else 'U'))
    items=[];netmap={}; ic=pas=bnd=0
    for ref,p in parts.items():
        if ref.startswith('U'): x=63.5+(ic%6)*190.5;y=83.82+(ic//6)*190.5;ic+=1
        elif p['physical']: x=40.64+(pas%15)*76.2;y=899.16+(pas//15)*30.48;pas+=1
        else: x=63.5+(bnd%6)*190.5;y=1122.68;bnd+=1
        layout=layouts[p['kind']]; upper=max(x[3] for x in layout); small=p['kind'] in ('R','C'); rx=x+3.81 if small else x; ry=y-2.54 if small else y-upper-10.16
        props=''.join(f'(property {quote(k)} {quote(v)}(at {rx} {ry+dy} 0){effects(.8,"hide") if hide else effects(.8,"(justify left)" if small else "")})' for k,v,dy,hide in [('Reference',ref,0,False),('Value',p['value'],2.54,False),('MPN',p['mpn'],0,True),('Footprint',p['footprint'],0,True)])
        yes='yes' if p['physical'] else 'no'
        items.append(f'(symbol(lib_id "CNC:{p["kind"]}")(at {x} {y} 0)(unit 1)(in_bom {yes})(on_board {yes})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_do"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
        for n,_,px,py,_,_ in layout:
            sx,sy=round(x+px,4),round(y-py,4);net=p['pins'][str(n)]
            if net is None:items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(n)+"nc")}"))');continue
            dx=-5.08 if px<0 else 5.08 if px>0 else 0; dy=0 if px else -5.08 if py>0 else 5.08; ex,ey=round(sx+dx,4),round(sy+dy,4)
            items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"wire")}"))')
            items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.65,"(justify right bottom)" if px<0 else "(justify left bottom)")}(uuid "{uid(ref+str(n)+"label")}"))')
            netmap.setdefault(net,[]).append([ref,str(n)])
    for i,net in enumerate(('IO_3V3','LOGIC_GND','DOA_FIELD_3V3','FIELD_A_0V','FIELD_A_24V','DOB_FIELD_3V3','FIELD_B_0V','FIELD_B_24V')):
        ref=f'#FLG10{i}'; x=30.48+i*139.7;y=1262.38
        items.append(f'(symbol(lib_id "CNC:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid "{uid(ref)}")(property "Reference" "{ref}"(at {x} {y} 0){effects(1,"hide")})(property "Value" "CONDITIONAL PARENT SUPPLY"(at {x} {y} 0){effects(1,"hide")})(instances(project "motherboard_do"(path "/{root}"(reference "{ref}")(unit 1)))))(label "{net}"(at {x} {y} 0){effects(.8)}(uuid "{uid(ref+"label")}"))')
    note='16 SOURCING DO / FOUR TPS274C65AS / TWO ISOLATED SPI DOMAINS / HARDWIRED DROP + REARM LATCH\n0.5A/channel,2A/quad. POR ILIM=1.25A is NOT the 0.72A commissioning setting: verified configuration is required before CARD_EN.\nField VDD must derive from same VS; parent supplies/controllers/terminals and surge/bulk/thermal/PCB qualification remain open. Not fabrication data.'
    items.append(f'(text {quote(note)}(at 20.32 17.78 0){effects(1.4,"(justify left top)")}(uuid "{uid(note)}"))')
    raw=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{root}")(paper "User" 1270 1300)(title_block(title "One-motherboard sixteen smart output frontends")(date "2026-09-30")(rev "r0.1"))(lib_symbols'+''.join(libs)+')'+''.join(items)+')'
    (out/'motherboard_do.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf-8')
    (out/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in libs)+')'))+'\n',encoding='utf-8')
    (out/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Motherboard DO prototype source")))'))+'\n',encoding='utf-8')
    (out/'motherboard_do.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_do.kicad_pro','version':1},'erc':{'rule_severities':{k:'warning' for k in ('single_global_label','four_way_junction','simulation_model_issue','footprint_filter')}}},indent=2)+'\n',encoding='utf-8')
    footprints(out)
    model['sources']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES.glob('*.pdf')}
    (out/'design.json').write_text(json.dumps(model,indent=2)+'\n',encoding='utf-8');(out/'pin-map.json').write_text(json.dumps(netmap,indent=2)+'\n',encoding='utf-8')
    with (out/'bom.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['Reference','Value','MPN','Footprint','Status']);w.writeheader();w.writerows({'Reference':ref,'Value':p['value'],'MPN':p['mpn'],'Footprint':p['footprint'],'Status':'source_candidate_not_qualified'} for ref,p in model['components'].items())
    (out/'boundary-map.json').write_text(json.dumps({'fitted':False,'excluded_from_PCB_and_BOM':True,'boundaries':model['boundaries'],'domains':model['domains']},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'physical_parts':model['fitted_component_count'],'pads':model['fitted_pad_count'],'output_count':16,'source':str(out/'motherboard_do.kicad_sch'),'manufacturing_ready':False}))
    return model

if __name__=='__main__':build()
