"""Actual one-motherboard supply source candidate, namespace 11xxx.

Reuses reviewed converter circuits, the existing MC sequence/reset and the
9xxx receiving-rail monitors. Does not export fabrication data or edit copper.
"""
import csv
import hashlib
import json
import math
import re
from pathlib import Path
import shutil
import uuid
import xml.etree.ElementTree as ET

from hardware_build_assembly import parse, dump
from hardware_build_tx_schematic import effects, quote, symbol

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'hardware/motherboard_power_entry'
REPORT = ROOT/'reports/motherboard-power-entry-20260930'
NS = uuid.UUID('3e455f1f-b613-4ae3-8f04-15803c3882c1')
PINS = {
 'R':{1:('', 'passive'),2:('', 'passive')},
 'C':{1:('', 'passive'),2:('', 'passive')},
 'L':{1:('', 'passive'),2:('', 'passive')},
 'F':{1:('', 'passive'),2:('', 'passive')},
 'D':{1:('K','passive'),2:('A','passive')},
 'QREV':{1:('S1','passive'),2:('S2','passive'),3:('S3','passive'),4:('G','input'),5:('D5_8_AND_LAND','passive')},
 'Q':{1:('G','input'),2:('S','passive'),3:('D','passive')},
 'MAIN':{1:('IN','power_in'),2:('IN','power_in'),3:('BGATE','output'),4:('DRV','output'),5:('IN_SYS','power_in'),6:('UVLO','input'),7:('OVP','input'),8:('GND','power_in'),9:('DVDT','passive'),10:('ILIM','passive'),11:('MODE','input'),12:('SHDN','input'),13:('IMON','output'),14:('FLT_N','open_collector'),15:('PGTH','input'),16:('PGOOD','open_collector'),17:('OUT','passive'),18:('OUT','power_out'),19:('NC','no_connect'),20:('NC','no_connect'),21:('NC','no_connect'),22:('NC','no_connect'),23:('NC','no_connect'),24:('NC','no_connect'),25:('EP_GND','power_in')},
 'AUX24':{1:('IN','power_in'),2:('UVLO','input'),3:('OVP','input'),4:('SHDN','input'),5:('RTN','power_out'),6:('GND','power_in'),7:('ILIM','passive'),8:('DVDT','passive'),9:('FLT_N','open_collector'),10:('OUT','power_out'),11:('EP_RTN','passive')},
 'AUX5':{1:('IN','power_in'),2:('GND','power_in'),3:('EN','input'),4:('FAULT_N','open_collector'),5:('ILIM','passive'),6:('OUT','power_out')},
 'FEED':{1:('CT','passive'),2:('NC','no_connect'),3:('VIN','power_in'),4:('VBIAS','power_in'),5:('ON','input'),6:('GND','power_in'),7:('PG','open_collector'),8:('OUT','power_out'),9:('OUT','passive'),10:('OUT','passive'),11:('EP_VIN','power_in')},
 'FIELD_LDO':{1:('OUT','power_out'),2:('DNC','no_connect'),3:('PG','open_collector'),4:('GND','power_in'),5:('EN','input'),6:('NC','no_connect'),7:('DELAY','passive'),8:('IN','power_in'),9:('EP_GND','power_in')},
 'LVC2G04':{1:('1A','input'),2:('GND','power_in'),3:('2A','input'),4:('2Y','output'),5:('VCC','power_in'),6:('1Y','output')},
 'LVC2G07':{1:('1A','input'),2:('GND','power_in'),3:('2A','input'),4:('2Y','open_collector'),5:('VCC','power_in'),6:('1Y','open_collector')},
 'TLP3640A':{1:('A','passive'),2:('K','passive'),3:('D','passive'),4:('D','passive')},
 'AHCT1G17':{1:('NC','no_connect'),2:('A','input'),3:('GND','power_in'),4:('Y','output'),5:('VCC','power_in')},
 'LVC1G74':{1:('CLK','input'),2:('D','input'),3:('Q_N','output'),4:('GND','power_in'),5:('Q','output'),6:('CLR_N','input'),7:('PRE_N','input'),8:('VCC','power_in')},
}
BOUNDARY_POWER = ['CORE_24V_INPUT','FIELD_A_24V_INPUT','FIELD_B_24V_INPUT','LOGIC_GND','FIELD_GND','FIELD_B_0V','IO_3V3']
BOUNDARY_INPUTS = ['MC_RAILS_OK_5V','MOTOR_FIELD_HEALTH_A_RAW','MOTOR_FIELD_HEALTH_B_RAW','OPI_REARM_A','OPI_REARM_B','MOTOR_TX_GATE_SOURCE_A','MOTOR_TX_GATE_SOURCE_B']
BOUNDARY_OUTPUTS = ['CORE_24V_PROTECTED','FIELD_A_24V_PROTECTED','FIELD_B_24V_PROTECTED','CORE_5V','MOTION_5V_RAW','MOTOR_5V_A','MOTOR_5V_B','SBC_5V','FIELD_5V','AUX_5V_A','AUX_5V_B','AUX_24V_A','AUX_24V_B','DOA_FIELD_3V3','DOB_FIELD_3V3','MOTOR_FEED_PG_A','MOTOR_FEED_PG_B','C_FAULT_N','FA_FAULT_N','FB_FAULT_N','FB_PGOOD','MOTOR_TX_GATE_A','MOTOR_TX_GATE_B']


def select_passives(parts):
    """Close purchasing strings without replacing reviewed selected parts.

    Vishay 20035/28758 ordering tables and exact TDK/Murata product records
    are the source. Initial tolerance is not an all-temperature tolerance.
    """
    codes={120:'120R',330:'330R',1000:'1K00',3000:'3K00',4020:'4K02',9530:'9K53',10000:'10K0',24900:'24K9',26700:'26K7',29400:'29K4',34000:'34K0',44200:'44K2',49900:'49K9',100000:'100K',110000:'110K',140000:'140K',887000:'887K',1000000:'1M00'}
    caps={
      '100nF5%C0G':('C3216C0G2A104J160AC','C_1206_3216Metric',.05,100,'C0G'),
      '1uF100VX7R':('GRM31CR72A105KA01L','C_1206_3216Metric',.10,100,'X7R'),
      '10nF100VX7R':('GRM188R72A103KA01D','C_0603_1608Metric',.10,100,'X7R'),
      '47nF25VX7R':('C1608X7R1H473K080AA','C_0603_1608Metric',.10,50,'X7R'),
      '4.7uF16VX7R':('C2012X7R1C475K125AB','C_0805_2012Metric',.10,16,'X7R'),
      '100nF16VX7R':('GRM188R72A104KA35D','C_0603_1608Metric',.10,100,'X7R'),
      '22nF5%C0G':('C2012C0G1H223J125AA','C_0805_2012Metric',.05,50,'C0G'),
      '330pF5%C0G':('GRM1885C1H331JA01D','C_0603_1608Metric',.05,50,'C0G'),
      '10nF100VC0G':('C2012C0G2A103J125AA','C_0805_2012Metric',.05,100,'C0G'),
    }
    for ref,p in parts.items():
        if not p['physical']:continue
        if p['kind']=='R':
            if 'resistance_ohm' not in p:
                m=re.match(r'([\d.]+)(mOhm|k|R)',p['value'])
                if m:p['resistance_ohm']=float(m[1])*{'mOhm':.001,'k':1000,'R':1}[m[2]]
            if not p['mpn']:
                precision='0.1%' in p['value'];code=codes[p['resistance_ohm']]
                size='0805' if precision and p['resistance_ohm']>332000 else '0603'
                p.update(mpn=('TNPW'+size+code+'BEEA') if precision else ('CRCW0603'+code+'FKEA'),initial_tolerance=.001 if precision else .01,tcr_ppm=25 if precision else 100,rated_power_w=.1,working_voltage_v=75,selection_required=False)
                if size=='0805':p['footprint']='Resistor_SMD:R_0805_2012Metric'
                p['purchasing_source']='Vishay 28758 Rev10Apr2026' if precision else 'Vishay20035 Rev14Apr2026'
        elif p['kind']=='C' and not p['mpn']:
            key=p['value'].replace(' ','');mpn,fp,tol,v,dielectric=caps[key]
            p.update(mpn=mpn,footprint='Capacitor_SMD:'+fp,initial_tolerance=tol,rated_voltage_v=v,dielectric=dielectric,selection_required=False,purchasing_source='Exact primary TDK/Murata product record; see procurement-source-record.json')
            if key=='47nF25VX7R':p['value']='47nF50V X7R'
            if key=='100nF16VX7R':p['value']='100nF100V X7R'


def description():
    parts={}; counters={k:11000 for k in ['U','R','C','L','D','Q','F','J']}; groups=[]
    def add(kind,mpn,fp,pins,role,value=None,**details):
        letter=kind if kind in counters else 'U';counters[letter]+=1;ref=letter+str(counters[letter])
        parts[ref]={'kind':kind,'mpn':mpn,'footprint':fp,'value':value or mpn,'physical':True,'pins':{str(k):v for k,v in pins.items()},'role':role,**details};return ref
    def r(a,b,ohm,role,precision=False):
        # Exact purchasing string is filled by select_passives after population.
        code=f'{ohm:g}'; return add('R','', 'Resistor_SMD:R_0603_1608Metric',{1:a,2:b},role,code+'R '+('0.1%' if precision else '1%'),resistance_ohm=ohm,initial_tolerance=.001 if precision else .01,selection_required=True)
    def c(a,b,value,role,mpn='',fp='Capacitor_SMD:C_0603_1608Metric'):
        return add('C',mpn,fp,{1:a,2:b},role,value,selection_required=not bool(mpn))
    # Three independently fused entries. FIELD_A supplies BOTH AUX banks.
    for prefix,gnd,out,current,fuse in [('C','LOGIC_GND','CORE_24V_PROTECTED',4020,'0997005.WXN'),('FA','FIELD_GND','FIELD_A_24V_PROTECTED',3000,'099707.5WXN'),('FB','FIELD_B_0V','FIELD_B_24V_PROTECTED',3000,'099707.5WXN')]:
        inp={'C':'CORE_24V_INPUT','FA':'FIELD_A_24V_INPUT','FB':'FIELD_B_24V_INPUT'}[prefix]
        PINS['J']={1:('+24V','passive'),2:('0V','passive')}
        add('J','1757242','Connector_Phoenix_MSTB:PhoenixContact_MSTBA_2,5_2-G-5,08_1x02_P5.08mm_Horizontal',{1:inp,2:gnd},prefix+' input; mating plug/customer wiring separate')
        add('F','3568','Fuse:Fuseholder_Blade_Mini_Keystone_3568',{1:inp,2:prefix+'_RAW'},prefix+' physical fuseholder; fitted fuse is separate BOM item','Keystone3568 / '+fuse,fuse_mpn=fuse,fuse_selection_qualified=False)
        add('D','SMCJ30CA','Diode_SMD:D_SMC',{1:prefix+'_RAW',2:gnd},prefix+' bidirectional surge TVS; whole surge coordination remains open')
        c(prefix+'_RAW',gnd,'2.2uF 100V X7S',prefix+' raw bypass','CGA5L3X7S2A225K160AB','Capacitor_SMD:C_1206_3216Metric')
        add('QREV','CSD19537Q3T','CNC_MB_Entry:CSD19537Q3_TI',{1:prefix+'_RAW',2:prefix+'_RAW',3:prefix+'_RAW',4:prefix+'_BGATE',5:prefix+'_IN'},prefix+' source faces input; TI pins1–3S,4G,5–8D combinedpad5')
        add('Q','BSS138P,215','Package_TO_SOT_SMD:SOT-23',{1:prefix+'_DRV',2:prefix+'_RAW',3:prefix+'_BGATE'},prefix+' reverse blocking driver; source refers to RAW')
        pins={1:prefix+'_IN',2:prefix+'_IN',3:prefix+'_BGATE',4:prefix+'_DRV',5:prefix+'_RAW',6:prefix+'_UV',7:prefix+'_OV',8:gnd,9:prefix+'_DVDT',10:prefix+'_ILIM',11:None,12:prefix+'_SHDN',13:prefix+'_IMON',14:prefix+'_FAULT_N',15:prefix+'_PGTH',16:prefix+'_PGOOD',17:out,18:out,25:gnd,**{n:None for n in range(19,25)}}
        u=add('MAIN','TPS26630RGER','Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm',pins,prefix+' protected entry; MODE open selects latch-off overload')
        for a,b,ohm in [(prefix+'_RAW',prefix+'_UV',887000),(prefix+'_UV',prefix+'_OV',29400),(prefix+'_OV',gnd,34000),(prefix+'_ILIM',gnd,current),(out,prefix+'_PGTH',140000),(prefix+'_PGTH',gnd,10000),(prefix+'_IMON',gnd,10000)]:r(a,b,ohm,prefix+' entry setting',True)
        c(prefix+'_DVDT',gnd,'100nF 5% C0G',prefix+' inrush ramp capacitor',fp='Capacitor_SMD:C_1206_3216Metric')
        for net in [prefix+'_IN',out]:c(net,gnd,'1uF 100V X7R',prefix+' entry local bypass',fp='Capacitor_SMD:C_1206_3216Metric')
        add('J','1757242','Connector_Phoenix_MSTB:PhoenixContact_MSTBA_2,5_2-G-5,08_1x02_P5.08mm_Horizontal',{1:prefix+'_SHDN',2:gnd},prefix+' dry-contact shutdown/reset; never machine rearm')
        groups.append({'entry':prefix,'efuse':u,'ground':gnd,'output':out,'ilim_r_ohm':current,'nominal_input_requirement_v':[18,30],'guaranteed_ilim_testpoint_a':[4.185,4.815] if prefix=='C' else [5.58,6.42]})
    # Preserve reviewed native converter topology, replace ONLY internal labels.
    for block,name,newin,newout,gnd in [('core_converter','CORE','CORE_24V_PROTECTED','CORE_5V','LOGIC_GND'),('core_converter','MOTION','CORE_24V_PROTECTED','MOTION_5V_RAW','LOGIC_GND'),('field_power','FIELD','FIELD_A_24V_PROTECTED','FIELD_5V','FIELD_GND')]:
        folder=ROOT/'hardware'/block; xml=ET.parse(folder/'netlist.xml')
        pinmap={}
        for net in xml.findall('.//nets/net'):
            n=net.get('name').lstrip('/')
            for node in net.findall('node'):pinmap.setdefault(node.get('ref'),{})[int(node.get('pin'))]=n
        libs={p.get('part'):{int(q.get('num')):(q.get('name'),q.get('type')) for q in p.findall('pins/pin')} for p in xml.findall('.//libparts/libpart')}
        rows=list(csv.DictReader((folder/'bom.csv').open(encoding='utf-8-sig')))
        for row in rows:
            old=row.get('reference');
            if old.startswith('J'):continue
            comp=xml.find(".//components/comp[@ref='"+old+"']");part=comp.find('libsource').get('part');kind=name+'_'+part if old.startswith('U') else old[0]
            if name=='CORE' and old=='U1':kind='CORE_LM706A0RRXR'
            if old.startswith('U'):PINS[kind]=libs[part]
            nets={}
            for num in (libs[part] if old.startswith('U') else [1,2]):
                n=pinmap.get(old,{}).get(num)
                if old.startswith('U') and libs[part][num][1]=='no_connect':n=None
                if n is not None:
                    if n in ['CORE_24V_PROTECTED','FIELD_24V_PROTECTED']:n=newin
                    elif n in ['CORE_5V','FIELD_5V']:n=newout
                    elif n in ['LOGIC_GND','FIELD_GND']:n=gnd
                    elif n=='IO_3V3':n='IO_3V3'
                    elif n in ['C_PGOOD','F_PGOOD']:n=('C' if name!='FIELD' else 'FA')+'_PGOOD'
                    else:n=name+'_'+n
                nets[num]=n
            fp=row.get('footprint','');mpn=row.get('mpn','');value=row.get('value','')
            if old.startswith('U'):fp='CNC_MB_Entry:'+('LM70660_RRX29_TI' if name!='FIELD' else 'LMR36506_RPE9_TI')
            if old.startswith('RS'):fp='CNC_MB_Entry:KRL3216_LongSide_Susumu'
            if mpn=='16SVPG330M':fp='CNC_MB_Entry:OSCON_C10L_Panasonic'
            if mpn=='LPS6235-223MRC':fp='CNC_MB_Entry:LPS6235_Coilcraft'
            if name=='CORE' and old=='U1':mpn=value='LM706A0RRXR'
            if name=='CORE' and old=='RS1':mpn='KRL3216D-C-R005-F-T1';value='5mOhm 1% 1.5W'
            if name=='CORE' and old=='L1':mpn='XAL1010-472MED';fp='CNC_MB_Entry:XAL1010_Coilcraft'
            add(kind,mpn,fp,nets,name+' reused reviewed '+old,value,source_block=block,source_ref=old,selection_required=not bool(mpn))
    # Receiving5V switches: low RON is needed for the inset supervisor windows.
    feeds=[]
    for bank in ['A','B']:
        out='MOTOR_5V_'+bank;on='MOTOR_FEED_ON_'+bank
        u=add('FEED','TPS22990DMLR','CNC_MB_Entry:TPS22990_DML10_TI',{1:None,2:None,3:'MOTION_5V_RAW',4:'MOTION_5V_RAW',5:on,6:'LOGIC_GND',7:'MOTOR_FEED_PG_'+bank,8:out,9:out,10:out,11:'MOTION_5V_RAW'},bank+' actual receiving rail feed; latch authority is separate')
        r(on,'LOGIC_GND',10000,'receiving feed defaultsOFF; does not supply software authority')
        r('IO_3V3','MOTOR_FEED_PG_'+bank,10000,'actual switchPG pullup')
        r(out,'LOGIC_GND',330,'receiving rail passive discharge; direct gate inhibit is separate')
        c('MOTION_5V_RAW','LOGIC_GND','1uF 16V X7R','feed input bypass','885012206052')
        c(out,'LOGIC_GND','100nF 100V X7R','receiving switch output bypass','GRM188R72A104KA35D')
        feeds.append({'bank':bank,'switch':u,'on':on,'normal_load_a':.8976 if bank=='A' else .4488,'input_fixed_v':[4.95,5.05],'receiving_static_arming_min_v':4.9296376,'total_switch_and_distribution_loss_max_v':.0203624})
    # Staged commoditycompute feed; currentprofile<=3A, totalcorebuck<=6A.
    add('FEED','TPS22990DMLR','CNC_MB_Entry:TPS22990_DML10_TI',{1:'SBC_RAMP_CT',2:None,3:'CORE_5V',4:'CORE_5V',5:'MC_RAILS_OK_5V',6:'LOGIC_GND',7:'SBC_SWITCH_PG',8:'SBC_5V',9:'SBC_5V',10:'SBC_5V',11:'CORE_5V'},'commodity compute supply delayed until retainedMCrailsqualified')
    c('SBC_RAMP_CT','LOGIC_GND','4.7uF 16V X7R','slow host inrush; effectiveC/rise bounds unqualified',fp='Capacitor_SMD:C_0805_2012Metric')
    c('CORE_5V','LOGIC_GND','1uF 16V X7R','host feed input bypass','885012206052')
    c('SBC_5V','LOGIC_GND','100nF 100V X7R','host feed output bypass','GRM188R72A104KA35D')
    r('MC_RAILS_OK_5V','LOGIC_GND',100000,'host gate zero-source bias');r('IO_3V3','SBC_SWITCH_PG',10000,'host actualPG')
    # Field5V branches stay supplied when LOGIC loses power.
    for bank,ohm in [('A',110000),('B',110000)]:
        ilim='AUX5_'+bank+'_ILIM';out='AUX_5V_'+bank
        add('AUX5','TPS2553DBVR-1','Package_TO_SOT_SMD:SOT-23-6',{1:'FIELD_5V',2:'FIELD_GND',3:'FIELD_5V',4:'AUX5_'+bank+'_FAULT_N',5:ilim,6:out},bank+' independent latched-short AUX5 feed, EN tied actualFIELD5')
        r(ilim,'FIELD_GND',ohm,'AUX5 actualILIM 110k1%');r('FIELD_5V','AUX5_'+bank+'_FAULT_N',10000,'field-local fault pullup');r(out,'FIELD_GND',100000,'AUX5 output bleed')
        c('FIELD_5V','FIELD_GND','100nF 100V X7R','limiter input bypass','GRM188R72A104KA35D');c(out,'FIELD_GND','1uF 16V X7R','AUX5 output bypass','885012206052')
    # Single latch-off AUX24 device per bank, exact published ILIM testpoints.
    # Keep RTN distinct from GND: TI explicitly forbids bonding them together.
    aux24=[]
    for bank,ohm,bounds in [('A',26700,[.237,.257]),('B',44200,[.145,.159])]:
        out='AUX_24V_'+bank;lim='AUX24_'+bank+'_ILIM';rtn='AUX24_'+bank+'_RTN'
        u=add('AUX24','TPS26624DRCR','CNC_MB_Entry:TPS2662_DRC10_TI',{1:'FIELD_A_24V_PROTECTED',2:'AUX24_'+bank+'_UVLO',3:rtn,4:None,5:rtn,6:'FIELD_GND',7:lim,8:'AUX24_'+bank+'_DVDT',9:'AUX24_'+bank+'_FAULT_N',10:out,11:rtn},bank+' independent input/output reverse-blocking latch-off AUX24; RTN only support circuits/EP')
        r(lim,rtn,ohm,'AUX24 exact published ILIM testpoint',True);r('FIELD_A_24V_PROTECTED','AUX24_'+bank+'_UVLO',1000000,'minimal TI UVLO feed limits pin current');r('FIELD_5V','AUX24_'+bank+'_FAULT_N',10000,'field-local fault pullup');r(out,'FIELD_GND',100000,'AUX24 output bleed')
        c('AUX24_'+bank+'_DVDT',rtn,'10nF 100V C0G','AUX24 ramp',fp='Capacitor_SMD:C_0603_1608Metric')
        for net in ['FIELD_A_24V_PROTECTED',out]:c(net,'FIELD_GND','1uF 100V X7R','AUX24 bypass',fp='Capacitor_SMD:C_1206_3216Metric')
        aux24.append({'bank':bank,'efuse':u,'rtn':rtn,'ilim_r_ohm':ohm,'datasheet_testpoint_bounds_a':bounds,'test_conditions':'TI SLVSDT4F Table7.5 -40..125C, VIN24V, VIN-VOUT1V; no interpolation','resistor_tolerance_model_bounds_a':[bounds[0]/1.001,bounds[1]/.999],'sustained_short_exact_resistance_max_guaranteed':False})
    # Actual3.3V fieldlogic supplies required by existing DO bank interfaces.
    for bank,gnd,inp,out in [('A','FIELD_GND','FIELD_A_24V_PROTECTED','DOA_FIELD_3V3'),('B','FIELD_B_0V','FIELD_B_24V_PROTECTED','DOB_FIELD_3V3')]:
        add('FIELD_LDO','TPS7A1633DGNR','CNC_MB_Entry:TPS7A16_DGN8_TI',{1:out,2:None,3:None,4:gnd,5:inp,6:None,7:None,8:inp,9:gnd},bank+' independent fieldlogic3.3V LDO; fixedFBpin2 must remainDNC')
        c(inp,gnd,'2.2uF 100V X7S','fieldLDO input bypass','CGA5L3X7S2A225K160AB','Capacitor_SMD:C_1206_3216Metric')
        c(out,gnd,'22uF 10V X7R','LDO output effectiveC>=2.2uF','GCM31CR71A226KE02L','Capacitor_SMD:C_1206_3216Metric')
        r(out,gnd,10000,'fieldlogic rail bleed')
    # Independent partial-domain blanking uses the actual PRE-isolation field
    # health, never the ISO7720 output that is undefined at 1.7--2.25V VCC2.
    # The two local LED drivers have specified powered IOZ and VCC0 IOFF,
    # instead of inferring MOSFET off-current from a threshold voltage curve.
    contact_refs={};gate_contact_refs={};driver_refs=[]
    for domain,rail,gnd,signals in [('CORE','CORE_5V','LOGIC_GND',['MC_RAILS_OK_5V']*2),('FIELD','FIELD_5V','FIELD_GND',['MOTOR_FIELD_HEALTH_A_RAW','MOTOR_FIELD_HEALTH_B_RAW'])]:
        inv=add('LVC2G04','74LVC2G04GW,125','Package_TO_SOT_SMD:SOT-363_SC-70-6',{1:signals[0],2:gnd,3:signals[1],4:domain+'_HEALTH_B_N',5:rail,6:domain+'_HEALTH_A_N'},domain+' raw-health inversion for fail-open photocontacts')
        sink=add('LVC2G07','74LVC2G07GW,125','Package_TO_SOT_SMD:SOT-363_SC-70-6',{1:domain+'_HEALTH_A_N',2:gnd,3:domain+'_HEALTH_B_N',4:domain+'_HEALTH_B_LED_K',5:rail,6:domain+'_HEALTH_A_LED_K'},domain+' independent LED sinks; IOZ2uA/IOFF2uA at datasheet testconditions')
        driver_refs.append({'domain':domain,'rail':rail,'inverter':inv,'sink':sink,'raw_health':signals})
        c(rail,gnd,'100nF 100V X7R','health LED-driver bypass','GRM188R72A104KA35D');c(rail,gnd,'100nF 100V X7R','health LED-sink bypass','GRM188R72A104KA35D')
        for bank,signal in zip(['A','B'],signals):
            r(signal,gnd,100000,domain+' raw-health bias; does not override hardware reset')
            r(rail,domain+'_HEALTH_'+bank+'_LED_A',120,domain+' two-series NO relay LED resistor')
            contact_in='MOTOR_FEED_CLEAR_SOURCE_'+bank if domain=='CORE' else 'MOTOR_FEED_CLEAR_MID_'+bank
            contact_out='MOTOR_FEED_CLEAR_MID_'+bank if domain=='CORE' else 'MOTOR_FEED_CLEAR_N_'+bank
            contact_refs[(domain,bank)]=add('TLP3640A','TLP3640A(TPL,E','CNC_MB_Entry:TLP3640A_SO4_11-3C1',{1:domain+'_HEALTH_'+bank+'_LED_A',2:domain+'_HEALTH_'+bank+'_LED_MID',3:contact_in,4:contact_out},domain+' actual-health isolated NO contact; must open on invalid source rail',bank=bank)
            gate_in='MOTOR_TX_GATE_SOURCE_'+bank if domain=='CORE' else 'MOTOR_TX_GATE_CONTACT_MID_'+bank
            gate_out='MOTOR_TX_GATE_CONTACT_MID_'+bank if domain=='CORE' else 'MOTOR_TX_GATE_'+bank
            gate_contact_refs[(domain,bank)]=add('TLP3640A','TLP3640A(TPL,E','CNC_MB_Entry:TLP3640A_SO4_11-3C1',{1:domain+'_HEALTH_'+bank+'_LED_MID',2:domain+'_HEALTH_'+bank+'_LED_K',3:gate_in,4:gate_out},domain+' direct gate-authority NO contact; separate receiving-rail cutting',bank=bank)
    latches=[]
    for bank in ['A','B']:
        clear='MOTOR_FEED_CLEAR_N_'+bank;clock='MOTOR_FEED_REARM_'+bank;on='MOTOR_FEED_ON_'+bank
        r('MOTION_5V_RAW','MOTOR_FEED_CLEAR_SOURCE_'+bank,1000,'feed clear source limits fault current')
        r(clear,'LOGIC_GND',100000,'asynchronous activeLOW clear default; contact IOFF bound')
        c(clear,'LOGIC_GND','1nF 5% C0G','clear contact RC; not a new rail supervisor','C0603C102J5GACTU')
        rearm=add('AHCT1G17','74AHCT1G17GVH','Package_TO_SOT_SMD:SOT-23-5',{1:None,2:'OPI_REARM_'+bank,3:'LOGIC_GND',4:clock,5:'MOTION_5V_RAW'},bank+' TTL-compatible existing3.3V rearm restoration to5V DFF')
        r('OPI_REARM_'+bank,'LOGIC_GND',10000,'rearm input idleLOW')
        latch=add('LVC1G74','SN74LVC1G74DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm',{1:clock,2:'MOTION_5V_RAW',3:None,4:'LOGIC_GND',5:on,6:clear,7:'MOTION_5V_RAW',8:'MOTION_5V_RAW'},bank+' actual bankfeed sticky latch; fault asynchronousclear and deliberate freshrearm',bank=bank)
        c('MOTION_5V_RAW','LOGIC_GND','100nF 100V X7R','feed latch bypass','GRM188R72A104KA35D');c('MOTION_5V_RAW','LOGIC_GND','100nF 100V X7R','rearm restorer bypass','GRM188R72A104KA35D')
        r('MOTOR_TX_GATE_'+bank,'LOGIC_GND',1000,'direct final-gate receiving pulldown independent of source MCU/FPGA/ISO outputs')
        latches.append({'bank':bank,'clear':clear,'latch':latch,'clock_restorer':rearm,'on':on,'series_contacts':[contact_refs[('CORE',bank)],contact_refs[('FIELD',bank)]],'direct_gate_contacts':[gate_contact_refs[('CORE',bank)],gate_contact_refs[('FIELD',bank)]],'direct_gate_input':'MOTOR_TX_GATE_SOURCE_'+bank,'direct_gate_output':'MOTOR_TX_GATE_'+bank,'gate_pulldown_ohm':1000})
    # Bounded CORE-only 7 A source correction. Add last to preserve every
    # existing reference and pin/net identity; MOTION remains the reviewed6A.
    extra=c('CORE_5V','LOGIC_GND','330uF16V 20% polymer','CORE fourth output bulk for reviewed7A envelope','16SVPG330M','CNC_MB_Entry:OSCON_C10L_Panasonic')
    assert extra=='C11088'
    select_passives(parts)
    parts['R11022'].update(initial_tolerance=.01,tcr_ppm=50,rated_power_w=1.5,temperature_rating_c=[-55,175],total_R_corner_screen_fraction=.02,aging_allowance_fraction=.0025,aging_allowance_qualified=False,purchasing_source='Susumu exact primary product_detail pdid559 and KRL3216 catalogue')
    boundary=BOUNDARY_POWER+BOUNDARY_INPUTS
    for ref,nets in [('B11001',boundary),('B11002',BOUNDARY_OUTPUTS)]:parts[ref]={'kind':ref,'mpn':'','value':'INTERNAL SOURCE BOUNDARY','footprint':'','physical':False,'pins':{str(i):n for i,n in enumerate(nets,1)},'role':'internalinterface; no generatedpower or fictitiousqualification'}
    return {'schema_version':1,'revision':'motherboard-power-entry-r0.4','one_custom_board':True,'manufacturing_ready':False,'physical_qualification':False,'components':parts,'boundary_power':BOUNDARY_POWER,'boundary_inputs':BOUNDARY_INPUTS,'boundary_outputs':BOUNDARY_OUTPUTS,'entries':groups,'motor_feeds':feeds,'aux24_limiters':aux24,'independent_feed_latches':latches,'health_led_drivers':driver_refs,'source_hashes':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'hardware/core_converter/requirements.json',ROOT/'hardware/field_power/design.json',ROOT/'hardware/mc_local_power/design.json',ROOT/'hardware/motherboard_motor_power/design.json']},'inherited_requirements':{'motor_channels':12,'core5_capacity_a':7,'core5_capacity_qualified':False,'core5_silicon_rating_a':10,'motion5_min_capacity_a':3,'actual_motion5_capacity_a':6,'host_profile_planning_reserve_a':3.6,'host_profile_delivery_qualified':False,'field5_min_capacity_a':.3,'actual_field5_capacity_a':.6,'aux5_load_a':{'A':.128,'B':.064},'aux24_load_a':{'A':.148,'B':.074},'aux24_limit_max_a':{'A':.30,'B':.20},'field24_requirement_v':[18,30],'field24_guaranteed_static_arming_v':[19,29],'field_logic_returns_joined_to_logic':False,'new_fpga_regulators':0,'new_voltage_monitors':0},'engineering_gates':[
      'Series pre-isolation health contacts independently clear each MOTION5-powered feed latch AND physically open the final TX/LED/enable authority path. ISO7720F1.7–2.25V receiver outputs cannot defeat these contacts when raw field/corehealth is LOW and their LED drivers have valid power. Arbitrary CORE/FIELD/MOTION ramps, healthy-at-powerup CLR/CLK sequencing and partial VCC LED-driver behavior remain electrical qualification gates.',
      'AUX24 exact overload testpoint ranges fit normal/cap budgets. Resistor tolerance uses an inverse-law engineering model; the published shortcircuit max at7.5k does not guarantee hardshort bounds at26.7k/44.2k. Vendor confirmation or a source-backed hardshort bound remains required.',
      '18–30V fullfieldinput requirement remains narrower than9xxx19–29V guaranteedstaticarming screen.',
      'Field5 fixedregulation/tolerance+AUX5 limiter/distribution losses must meet4.86919887V worstUVarmingthreshold; circuitfitted, lossqualification open.',
      'Motorfeed switch/distribution loss must stayunder20.3624mV. TPS22990 RON guarantees are atlistedbiasvoltage; thermal/noise/transient/IRdrop need reconciliation.',
      'Separatefield3.3LDO normal/dynamicICC/thermal/railcurrent budget must be completed; .1A rating isnotloadestimate.',
      'All fittedpassiveMPNs and three fittedfuseaccessoryMPNs are selected. Outputnegativeclamp/surgecoordination, fusefault/thermalcoordination, connector matingorientation andstencilprocess remain engineering/procurement gates.',
      'Nexperia74LVC2G04 raw-health inputs retain a10ns/V recommendedrise/fall constraint despite advertisedSchmittaction. ExactLTC RST loading/slew at the fitted10k pullups andadded100k biases must be reconciled; no arbitraryslowramp guarantee is claimed.',
      'CORE-only bounded7A candidate uses LM706A0RRXR,5mohm KRL3216,XAL1010-472MED and four330uF outputbulks. The10A silicon rating does not qualify8A/10A board operation. Reviewed conditional normal6.637A screen, compensation/effectivecap/current-limit/inrush andhotinductor/thermal corners require qualification; allfaults may inhibit/trip rather than sustain simultaneousshort loads.',
      'Displaypower andoptionalAI loads remain qualifiedpermodule; no fixedCM5 or21inch assumption.',
      'Two-step bank bootstrap: freshOPI rearm powers healthybankfeed, waitreceiving5Vqualification, then freshOPI rearm setsOPIstatus. Circuitfitted, softwaresequence notimplemented here.'
    ]}

def polygon_contains(points, point):
    """Independent ray-cast; custom-pad anchors must stay inside copper."""
    x,y=point;inside=False
    for (ax,ay),(bx,by) in zip(points,points[1:]+points[:1]):
        if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:inside=not inside
    return inside


def polygon_anchor(points, preferred=None):
    """Keep a valid anchor or choose the most interior deterministic grid point.

    KiCad unions its 1 um anchor rectangle into the custom copper. A vertex
    average may lie outside a concave land and create a disconnected island.
    This changes the coordinate origin only, never the absolute polygon.
    """
    def valid(p):
        return all(polygon_contains(points,[p[0]+dx,p[1]+dy]) for dx in (-.0005,.0005) for dy in (-.0005,.0005))
    if preferred is not None and valid(preferred):return list(preferred)
    lo=[min(p[i] for p in points) for i in (0,1)];hi=[max(p[i] for p in points) for i in (0,1)]
    def distance(p):
        result=math.inf
        for a,b in zip(points,points[1:]+points[:1]):
            dx=b[0]-a[0];dy=b[1]-a[1];den=dx*dx+dy*dy
            t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den)) if den else 0
            result=min(result,math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy))
        return result
    candidates=[[lo[0]+(hi[0]-lo[0])*(i+.5)/32,lo[1]+(hi[1]-lo[1])*(j+.5)/32] for i in range(32) for j in range(32)]
    candidates=[p for p in candidates if valid(p)]
    if not candidates:raise ValueError('Manufacturer copper has no valid 1 um anchor')
    return max(candidates,key=distance)


def footprints(out):
    """Primary drawing copper; solder-paste process remains a review gate."""
    pretty=out/'CNC_MB_Entry.pretty';pretty.mkdir(exist_ok=True);review={}
    tlp_source=ROOT/'hardware/motherboard_motors/CNC_Motors.pretty/TLP3640A_SO4_11-3C1.kicad_mod'
    shutil.copyfile(tlp_source,pretty/tlp_source.name)
    review['TLP3640A_SO4_11-3C1']={'source':str(tlp_source.relative_to(ROOT)),'sha256':hashlib.sha256(tlp_source.read_bytes()).hexdigest(),'reused_frozen_manufacturer_land':True,'physical_stencil_or_thermal_qualified':False}
    def make(name,pads,body,courtyard,source,pin1_marker=None):
        raw=f'(footprint "{name}"(version 20250108)(generator "pcbnew")(layer "F.Cu")(attr smd)(descr {quote(source)})(property "Reference" "REF**"(at 0 {-courtyard[1]-1} 0)(layer "F.SilkS")(effects(font(size 1 1)(thickness .15))))(property "Value" {quote(name)}(at 0 {courtyard[1]+1} 0)(layer "F.Fab")(effects(font(size 1 1)(thickness .15))))(fp_rect(start {-body[0]/2} {-body[1]/2})(end {body[0]/2} {body[1]/2})(stroke(width .1)(type default))(fill none)(layer "F.Fab"))(fp_rect(start {-courtyard[0]} {-courtyard[1]})(end {courtyard[0]} {courtyard[1]})(stroke(width .05)(type default))(fill none)(layer "F.CrtYd"))'+''.join(pads)+')'
        tree=parse(raw)
        if pin1_marker is not None:
            x,y=pin1_marker
            tree.append(parse(f'(fp_circle(center {x} {y})(end {x+.1} {y})(stroke(width .1)(type default))(fill none)(layer "F.SilkS"))'))
        (pretty/(name+'.kicad_mod')).write_text(dump(tree)+'\n',encoding='utf8')
        review[name]={'source':source,'body_mm':body,'courtyard_half_mm':courtyard,'physical_stencil_or_thermal_qualified':False,'three_d_model':None}
    def rect(n,x,y,w,h,layers='"F.Cu" "F.Paste" "F.Mask"'):
        return f'(pad "{n}" smd rect(at {x} {y})(size {w} {h})(layers {layers}))'
    def poly(n,points,anchor=None,layers='"F.Cu" "F.Paste" "F.Mask"'):
        if anchor is None:anchor=[sum(p[0] for p in points)/len(points),sum(p[1] for p in points)/len(points)]
        anchor=polygon_anchor(points,anchor)
        pts=''.join(f'(xy {x-anchor[0]:.6f} {y-anchor[1]:.6f})' for x,y in points)
        return f'(pad "{n}" smd custom(at {anchor[0]} {anchor[1]})(size .001 .001)(layers {layers})(options(clearance outline)(anchor rect))(primitives(gr_poly(pts {pts})(width 0)(fill yes))))'
    # TI copper polygons extracted from vector paths, cubic curves sampled8x.
    # VIN/SW common lead+die lands are not separate electrically: all logical
    # same-rail pads lie on the manufacturer common copper, no hiddenNC pads.
    dat=json.loads((REPORT/'sources/lm70660-pad-polygons.json').read_text())
    # Reconcile extracted vectors against SIX drawing dimensions: VIN bounds
    # [-3.2,-.625] x [-3.2,-.484]; SW [-.125,3.2] x [-2.1,-.14].
    # Earlier extraction used 45.80875 pt/mm instead of this drawing's 15X.
    scale_correction=dat['scale_pt_per_mm']/(15*72/25.4)
    corrected=[[[x*scale_correction,y*scale_correction] for x,y in ps] for ps in dat['loops']]
    vin,sw=sorted(corrected,key=lambda ps:sum(x for x,y in ps)/len(ps))
    pads=[poly(1,vin,[-1.5,-1.5]),poly(20,sw,[1,-1])]
    for n,x,y,w,h in [(2,-2.9,-1.75,.6,.25),(3,-1.5,-1,.1,.1),(4,-2.9,-1.25,.6,.25),(5,-2.9,-.25,.6,.25),(6,-2.9,1.25,.6,.25),(7,-2.9,1.75,.6,.25),(8,-2.9,2.25,.6,.25),(17,2.9,1.75,.6,.25),(18,2.9,1.25,.6,.25),(19,2.9,.75,.6,.25),(21,2.9,-1.25,.6,.25),(22,2.9,-1.75,.6,.25),(30,-.037,1.308,3.125,1.584)]:pads.append(rect(n,x,y,w,h))
    for n,x in [(9,-2),(10,-1.5),(11,-1),(12,-.037),(13,.5),(14,1),(15,1.5),(16,2)]:pads.append(rect(n,x,2.9,.25,.6))
    for n,x in [(23,2),(24,1.5),(25,1),(26,.5),(27,-1),(28,-1.5),(29,-2)]:pads.append(rect(n,x,-2.9,.25,.6))
    make('LM70660_RRX29_TI',pads,[6,6],[3.5,3.5],'TI SNVSCD4 RRX0029B4228757/D04/2024 p54; 15X vector normalization verified against annotated bounds; same-rail shared power copper; stencil/thermal review required')
    review['LM70660_RRX29_TI']['vector_scale_correction']=scale_correction
    review['LM70660_RRX29_TI']['annotated_copper_bounds_mm']={'VIN':[-3.2,-.625,-3.2,-.484],'SW':[-.125,3.2,-2.1,-.14]}
    # DML regular lead metal=.45x.24; green outline of these in TI drawing is
    # MASK opening, whereas the green thermal/common8–10 outline is COPPER.
    ds=json.loads((REPORT/'sources/dml-raw-loops.json').read_text());loops=ds['loops'];cx=294.0833435;cy=271.333328;scale=70.86614
    def convert(ps):return [[round((x-cx)/scale,6),round((y-cy)/scale,6)] for x,y in ps]
    pads=[rect(n,-.975,-1+(n-1)*.5,.45,.24) for n in range(1,6)]+[rect(6,.975,1,.45,.24),rect(7,.975,.5,.45,.24),poly(8,convert(loops[8]),[.975,-.8]),rect(9,.975,-.5,.1,.1),rect(10,.975,-1,.1,.1),rect(11,0,0,1.1,2.6)]
    make('TPS22990_DML10_TI',pads,[2,3],[1.45,1.8],'TI SLVSDK1C DML0010A4222524/A11/2015 p32; thermalpad11VIN; output8–10 common copper')
    ds=json.loads((REPORT/'sources/rpe-raw-loops.json').read_text());cx=306.110565;cy=306.020752;scale=66.9638
    ordered=[ds['loops'][i] for i in [3,2,1,0,4,5,7,8,6]]
    pads=[]
    for n,ps in enumerate(ordered,1):pads.append(poly(n,[[round((x-cx)/scale,6),round((y-cy)/scale,6)] for x,y in ps]))
    make('LMR36506_RPE9_TI',pads,[2,2],[1.5,1.5],'TI SNVSBB6C RPE0009B4227033/B09/2023 p45; groundpad9; vector copper curves flattened8x, joins<=.05PDFpoint')
    # Q3T differs only in reel quantity, per SLPS549B ordering table. Use the
    # actual .650 pitch/.500 width instead of stock .640 end-pair pitch.
    # Pins5..8 share the one drain land numbered5, consistent with our symbol.
    drain=[[-1.225,.560],[-1.225,-1.750],[-.725,-1.750],[-.725,-1.340],[-.575,-1.340],[-.575,-1.750],[-.075,-1.750],[-.075,-1.340],[.075,-1.340],[.075,-1.750],[.575,-1.750],[.575,-1.340],[.725,-1.340],[.725,-1.750],[1.225,-1.750],[1.225,.560]]
    pads=[rect(n,x,1.435,.500,.630,'"F.Cu" "F.Mask"') for n,x in enumerate([-.975,-.325,.325,.975],1)]
    pads += [poly(5,drain,[0,0],'"F.Cu" "F.Mask"')]
    pads += [rect('',x,-.2625,1.020,1.445,'"F.Paste"') for x in [-.635,.635]]
    pads += [rect('',x,y,.340,.450,'"F.Paste"') for x in [-.975,-.325,.325,.975] for y in [-1.435,1.435]]
    make('CSD19537Q3_TI',pads,[3.3,3.3],[2,2],'TI SLPS549B p9 recommended PCB pattern/stencil: .650 pitch,.500x.630 source/gate; .560 gap; 2.450x1.900 drain+.410 tabs; paste two1.020x1.445 islands+.340x.450 leads; Q3T reel variant per p1; sharedD5–8 representedpad5',[-1.65,1.435])
    pads=[rect(n,-1.4,-1+(n-1)*.5,.6,.24) for n in range(1,6)] +[rect(n,1.4,1-(n-6)*.5,.6,.24) for n in range(6,11)]
    # DRC0010J copper1.65x2.4 with four .25x.5 solder wick tabs,
    # outertabspan3.4. Orthogonal corners approximate drawingR.05 locally.
    ep=[[-.825,-1.2],[-.375,-1.2],[-.375,-1.7],[-.125,-1.7],[-.125,-1.2],[.125,-1.2],[.125,-1.7],[.375,-1.7],[.375,-1.2],[.825,-1.2],[.825,1.2],[.375,1.2],[.375,1.7],[.125,1.7],[.125,1.2],[-.125,1.2],[-.125,1.7],[-.375,1.7],[-.375,1.2],[-.825,1.2]]
    pads += [poly(11,ep,[0,0],'"F.Cu" "F.Mask"')]
    pads += [rect('',0,y,1.5,1.06,'"F.Paste"') for y in [-.63,.63]]
    pads += [rect('',x,y,.25,.34,'"F.Paste"') for x in [-.25,.25] for y in [-1.53,1.53]]
    make('TPS2662_DRC10_TI',pads,[3.1,3.1],[2,2],'TI SLVSDT4F DRC0010J4218878/B07/2018 land/stencil;EP11RTN;0.125mm stencilexample80percent; drawingR.05 replacedorthogonalcornerrequiresstencilreview')
    pads=[rect(n,-2.2,-.975+(n-1)*.65,1.4,.45) for n in range(1,5)]+[rect(n,2.2,.975-(n-5)*.65,1.4,.45) for n in range(5,9)]
    pads += [rect(9,0,0,2,3,'"F.Cu"'),rect('',0,0,1.6,1.92,'"F.Mask"'),rect('',0,0,1.2,1.52,'"F.Paste"')]
    make('TPS7A16_DGN8_TI',pads,[3,3],[3.15,1.85],'TI SBVS171F DGN0008C4218838/A11/2017 p35; pad9GND; copper2x3/mask1.6x1.92; stencil requires vendorreview')
    make('KRL3216_LongSide_Susumu',[rect(1,-.75,0,.9,3.4),rect(2,.75,0,.9,3.4)],[1.6,3.2],[1.45,1.95],'Susumu n_e_all.pdf p148(printed147), KRL3216D/E>=2mΩ on35µm copper: gap.60/span2.40/width3.40mm')
    make('OSCON_C10L_Panasonic',[rect(1,-2.8,0,3.5,2.5),rect(2,2.8,0,3.5,2.5)],[6.6,6.6],[4.85,3.55],'Panasonic AAB8000COL10 31Oct2025 C10L: gap2.1/span9.1/width2.5mm;16SVPG330M diameter6.3mm,height10.4mm; polarpositivepad1')
    make('XAL1010_Coilcraft',[rect(1,3.325,0,2.38,9.0),rect(2,-3.325,0,2.38,9.0)],[10.5,11.8],[5.5,6.15],'Coilcraft Doc804-4 Rev25Feb2026 official recommended land: centres+-3.325mm,2.38x9.0mm rectangular lands. Bodymax10.5x11.8mm,height10.0max; pad1 right-hand markedshortlead is high-dv/dt CORE_CORE_SW. Courtyard .25mm beyondmaxbody, not manufacturer courtyard.',pin1_marker=[5.25,0])
    # The annotated drawing has4.20mm upper and4.25mm lower bevel spans,
    # plus4.25mm outer straight-side height. Preserve its small asymmetry;
    # PDF vector artwork is not a dimensioned scale substitute.
    left=[[-3.3,-2.125],[-2.1,-3.3],[-1,-3.3],[-1,-2.1],[-2.1,-.9],[-2.1,.9],[-1,2.1],[-1,3.3],[-2.125,3.3],[-3.3,2.125]]
    make('LPS6235_Coilcraft',[poly(1,left,[-2.7,0]),poly(2,[[-x,y] for x,y in reversed(left)],[2.7,0])],[6.13,6.13],[3.55,3.55],'Coilcraft Document587-2 p2:6.60landspan,4.20upper/4.25lower bevelspan,4.25straightheight,2.00innergap,1.80innerverticalgap; annotated dimensions, not vector scale')
    (out/'footprint-review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf8')


def build(out=OUT):
    out = Path(out); out.mkdir(parents=True,exist_ok=True)
    model = description(); parts = model['components']; uid = lambda name:str(uuid.uuid5(NS,name)); root = uid('root')
    funcs = dict(PINS)
    for p in parts.values():
        if not p['physical']:funcs[p['kind']] = {int(k):(k,'passive') for k in p['pins']}
    funcs['PWR_FLAG'] = {1:('pwr','power_out')}
    library = []; geometry = {}
    for kind,pinmap in funcs.items():
        if kind in ('R','C','L','F','D'):
            coords = [(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')]
            shape = '(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))' if kind=='R' else '(polyline(pts(xy -2.54 .762)(xy 2.54 .762))(stroke(width .3)(type default))(fill(type none)))(polyline(pts(xy -2.54 -.762)(xy 2.54 -.762))(stroke(width .3)(type default))(fill(type none)))(polyline(pts(xy 0 2.54)(xy 0 .762))(stroke(width .254)(type default))(fill(type none)))(polyline(pts(xy 0 -.762)(xy 0 -2.54))(stroke(width .254)(type default))(fill(type none)))'
        elif kind=='PWR_FLAG':coords=[(1,'pwr',0,0,90,'power_out')];shape=''
        else:
            keys=list(pinmap);left=keys[:(len(keys)+1)//2];right=keys[len(left):];half=max(len(left),len(right))*5.08
            coords=[]
            for side,keys in ((-1,left),(1,right)):
                for i,n in enumerate(keys):coords.append((n,pinmap[n][0],side*20.32,half-i*10.16,0 if side<0 else 180,pinmap[n][1]))
            shape=f'(rectangle(start -17.78 {half+5.08})(end 17.78 {-half+5.08})(stroke(width .254)(type default))(fill(type background)))'
        geometry[kind]=coords
        library.append(symbol(kind,coords,shape,'R' if kind=='R' else 'C' if kind=='C' else '#FLG' if kind=='PWR_FLAG' else 'B' if kind.startswith('B') else 'U'))
    items=[];nets={};ic_count=passive_count=boundary_count=0
    for ref,p in parts.items():
        kind=p['kind']; passive=kind in ('R','C','L','F','D')
        if passive:x=50.8+(passive_count%10)*101.6;y=2202.18+(passive_count//10)*38.1;passive_count+=1
        elif p['physical']:x=177.8+(ic_count%4)*266.7;y=114.3+(ic_count//4)*167.64;ic_count+=1
        else:x=177.8+boundary_count*508;y=3101.34;boundary_count+=1
        py=y-10.16 if passive else y-max(abs(row[3]) for row in geometry[kind])-15.24
        props=f'(property "Reference" {quote(ref)}(at {x+5.08 if passive else x} {py} 0){effects(.95)})(property "Value" {quote(p["value"])}(at {x+7.62 if passive else x} {py+5.08} 0){effects(.8)})'
        props+=f'(property "MPN" {quote(p["mpn"])}(at {x} {y} 0){effects(extra="hide")})(property "Footprint" {quote(p["footprint"])}(at {x} {y} 0){effects(extra="hide")})'
        items.append(f'(symbol(lib_id "CNC:{kind}")(at {x} {y} 0)(unit 1)(in_bom {"yes" if p["physical"] else "no"})(on_board {"yes" if p["physical"] else "no"})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_power_entry"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
        for n,_,px,py,_,_ in geometry[kind]:
            xx,yy=round(x+px,4),round(y-py,4);net=p['pins'][str(n)]
            if net is None:items.append(f'(no_connect(at {xx} {yy})(uuid "{uid(ref+str(n)+"nc")}"))');continue
            ex=xx if passive else round(xx+(-30.48 if px<0 else 10.16),4);ey=round(yy+(-5.08 if n==1 else 5.08),4) if passive else yy
            if (ex,ey)!=(xx,yy):items.append(f'(wire(pts(xy {xx} {yy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"w")}"))')
            items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.7,"(justify left bottom)")}(uuid "{uid(ref+str(n)+"l")}"))')
            nets.setdefault(net,[]).append([ref,str(n)])
    flag_rails=BOUNDARY_POWER+[p+'_RAW' for p in ['C','FA','FB']]+[p+'_IN' for p in ['C','FA','FB']]+['CORE_5V','MOTION_5V_RAW','FIELD_5V']
    for i,net in enumerate(flag_rails):
        x,y=50.8+(i%12)*88.9,3342.64+(i//12)*25.4;ref='#FLG'+str(11001+i)
        items.append(f'(symbol(lib_id "CNC:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid "{uid(ref)}")(property "Reference" {quote(ref)}(at {x} {y-5.08} 0){effects(extra="hide")})(property "Value" "Actual fitted fuse/FET/buck path; flags are ERC declarations only"(at {x} {y-2.54} 0){effects(extra="hide")})(instances(project "motherboard_power_entry"(path "/{root}"(reference {quote(ref)})(unit 1)))))(label {quote(net)}(at {x} {y} 0){effects(.7,"(justify left bottom)")}(uuid "{uid(ref+"l")}"))')
    for i,line in enumerate(['PROTECTED ENTRY / ACTUAL RAIL GENERATION / ONE MOTHERBOARD / SOURCE CANDIDATE r0.4','CORE/FIELD_A/FIELD_B entries; preserve existingFPGA1V2 andIO3 regulators, sequence and9xxx window monitors.','CORE5 bounded7A +MOTION5 6A converters; two switchedmotorfeeds; FIELD5 .6A +independentAUX limiters.','Published AUX24 overload testpoints; series raw-health photocontacts and bank-feed asynchronousclear/rearm latches.','No fabrication release; exact package/peripheral load/IRdrop andfield surge coordination require reconciliation.']):
        items.append(f'(text {quote(line)}(at 25.4 {20.32+i*7.62} 0){effects(1.2,"(justify left top)")}(uuid "{uid("note"+str(i))}"))')
    raw=f'(kicad_sch(version 20250114)(generator "eeschema")(uuid "{root}")(paper "User" 1189 3440)(title_block(title "One-board protected power entry and supply")(date "2026-09-30")(rev "r0.3 / source candidate"))(lib_symbols {"".join(library)})'+''.join(items)+')'
    (out/'motherboard_power_entry.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf-8')
    lib='(kicad_symbol_lib(version 20241209)(generator "kicad_symbol_editor")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in library)+')'
    (out/'CNC.kicad_sym').write_text(dump(parse(lib))+'\n',encoding='utf-8')
    (out/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Actual motor health source candidate")))'))+'\n',encoding='utf-8')
    (out/'fp-lib-table').write_text(dump(parse('(fp_lib_table(version 7)(lib(name "CNC_MB_Entry")(type "KiCad")(uri "${KIPRJMOD}/CNC_MB_Entry.pretty")(options "")(descr "Source-backed power monitor lands")))'))+'\n',encoding='utf-8')
    (out/'motherboard_power_entry.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_power_entry.kicad_pro','version':1},'erc':{'rule_severities':{k:'warning' for k in ('single_global_label','four_way_junction','simulation_model_issue','footprint_filter')}}},indent=2)+'\n',encoding='utf-8')
    model['nets']={n:sorted(v) for n,v in sorted(nets.items())}
    (out/'design.json').write_text(json.dumps(model,indent=2)+'\n',encoding='utf-8')
    (out/'pin-map.json').write_text(json.dumps(model['nets'],indent=2)+'\n',encoding='utf-8')
    with (out/'bom.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(['Reference','Value','MPN','Footprint','Status'])
        for ref,p in parts.items():
            if p['physical']:writer.writerow([ref,p['value'],p['mpn'],p['footprint'],'source candidate / not qualified'])
    with (out/'fitted-accessories-bom.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(['AssemblyReference','MPN','Description','PCB_Footprint','Status'])
        for ref,p in parts.items():
            if p['kind']=='F':writer.writerow([ref+'-FUSE',p['fuse_mpn'],'Fitted Littelfuse MINI997 58V blade fuse','none; installs in '+ref,'Exact fitted accessory; fault coordination not qualified'])
    footprints(out)
    print(out/'motherboard_power_entry.kicad_sch')


if __name__=='__main__':build()
