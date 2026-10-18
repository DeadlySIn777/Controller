"""Independent physical-pin, isolation, default-state and native DO checks.

Expected pins are transcribed from TI datasheet pin tables/top-view drawings.
This does not import the source generator. Tests distinguish a drawn front-end
from the missing controller/firmware, supply and final-board qualification.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import uuid
import xml.etree.ElementTree as ET
from hardware_build_assembly import parse

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/motherboard_do'
NS=uuid.UUID('04b645d1-c086-40f7-b737-eb0d2a2a6828')

def native(path):
    tree=ET.parse(path).getroot(); parts={}
    for node in tree.findall('components/comp'):
        ref=node.attrib['ref']
        if ref.startswith('#'):continue
        fields={f.attrib['name']:f.text or '' for f in node.findall('fields/field')}
        if ref in parts:raise ValueError('duplicate native reference')
        parts[ref]={'mpn':fields.get('MPN',''),'footprint':node.findtext('footprint',''),'value':node.findtext('value',''),'pins':{}}
    for net in tree.findall('nets/net'):
        name=net.attrib['name'].removeprefix('/')
        for pin in net.findall('node'):
            ref,num=pin.attrib['ref'],pin.attrib['pin']
            if ref.startswith('#'):continue
            if num in parts[ref]['pins']:raise ValueError('duplicate native pin')
            parts[ref]['pins'][num]=None if name.startswith('unconnected-') else name
    return parts

def expected_driver(letter,quad):
    # SLVSFZ2C Table5-1 AS; B/SH pin functions must not be inherited here.
    dom='DO'+letter; g=f'FIELD_{letter}_0V'; vs=f'FIELD_{letter}_24V'; n=(0 if letter=='A' else 8)+quad*4; tag=f'{dom}_Q{quad}'
    out={1:tag+'_READY_N',2:dom+'_FLT_N_FIELD',3:dom+'_DO_EN_FIELD',4:dom+'_FIELD_3V3',5:g,6:tag+'_ISNS',7:dom+'_SDO_FIELD',8:dom+'_SDI_FIELD',9:dom+'_SCLK_FIELD',10:dom+'_CS_N_FIELD',11:f'DO{n+2:02}_RCB_GATE',12:f'DO{n+2:02}_SW',13:f'DO{n+2:02}_SW',18:f'DO{n+3:02}_SW',19:f'DO{n+3:02}_SW',20:f'DO{n+3:02}_RCB_GATE',21:g,28:g,29:g,30:tag+'_ADDRESS',31:f'DO{n+1:02}_RCB_GATE',32:f'DO{n+1:02}_SW',33:f'DO{n+1:02}_SW',38:f'DO{n:02}_SW',39:f'DO{n:02}_SW',40:f'DO{n:02}_RCB_GATE',41:g}
    out.update({i:vs for i in [14,15,16,17,34,35,36,37]});out.update({i:None for i in [22,23,24,25,26,27]})
    return {str(k):v for k,v in out.items()}

def expected_iso(letter):
    dom='DO'+letter
    return {str(k):v for k,v in {1:'IO_3V3',2:dom+'_SCLK_HOST',3:dom+'_SDI_HOST',4:dom+'_CS_N_HOST',5:dom+'_DO_EN_LOGIC',6:dom+'_SDO_HOST',7:dom+'_FLT_N_HOST',8:'LOGIC_GND',9:f'FIELD_{letter}_0V',10:dom+'_FLT_N_FIELD',11:dom+'_SDO_FIELD',12:dom+'_DO_EN_FIELD',13:dom+'_CS_N_FIELD',14:dom+'_SDI_FIELD',15:dom+'_SCLK_FIELD',16:dom+'_FIELD_3V3'}.items()}

def footprint_pads(path):
    tree=parse(Path(path).read_text(encoding='utf-8')); pads={};paste=[]
    for el in tree:
        if not isinstance(el,list) or not el or el[0]!='pad':continue
        info={x[0]:x[1:] for x in el[4:] if isinstance(x,list)}
        n=json.loads(el[1]) if el[1].startswith('"') else el[1]; at=tuple(float(x) for x in info['at'][:2]);size=tuple(float(x) for x in info['size']);layers=[json.loads(x) if x.startswith('"') else x for x in info['layers']]
        if n:
            if n in pads:raise ValueError('duplicate numbered physical pad')
            pads[n]={'at':at,'size':size,'layers':layers,'mask':float(info.get('solder_mask_margin',[0])[0])}
        elif layers==['F.Paste']:paste.append({'at':at,'size':size})
        else:raise ValueError('unidentified non-paste physical land')
    return pads,paste

def request_limits(channels):
    """Validation screen only; this is not a deployed configuration API."""
    if len(channels)!=16:raise ValueError('16 output limit declarations required')
    allowed={0:.33,1:.39,2:.47,3:.55,4:.63,5:.78,6:.82,7:1.0}
    for start in range(0,16,4):
        group=channels[start:start+4]
        if any(not 0<=x['continuous_a']<=.5 or x['code'] not in allowed for x in group):raise ValueError('unqualified continuous/current-limit rating')
        if sum(x['continuous_a'] for x in group)>2:raise ValueError('quad continuous rating')
        if group[0]['code']!=group[1]['code'] or group[2]['code']!=group[3]['code']:raise ValueError('shared paired ILIM mismatch')
        if any(x.get('inrush_boost',False) or x.get('parallel',False) for x in group):raise ValueError('unqualified inrush/paralleled outputs')
    return True

def validate(d,netlist=None,erc=None,fpdir=None):
    errors=[]
    def check(ok,msg):
        if not ok:errors.append(msg)
    def pin(ref,expected):check(d['components'][ref]['pins']=={str(k):v for k,v in expected.items()},ref+' physical pin/net contract')
    def passive_between(a,b,kind,value=None):
        return [ref for ref,p in d['components'].items() if p['kind']==kind and set(p['pins'].values())=={a,b} and (value is None or p.get('resistance_ohm')==value if kind=='R' else value is None or abs(p.get('capacitance_f',0)-value)<1e-18)]
    try:
        p=d['components'];count={k:sum(x['kind']==k for x in p.values()) for k in ['TPS','ISO','DFF','AND4','NMOS','R','C']}
        check(count=={'TPS':4,'ISO':2,'DFF':2,'AND4':2,'NMOS':16,'R':40,'C':44},'fitted component population')
        check(d['channel_count']==16 and d['banks']==2 and d['quad_count']==4 and len(d['channels'])==16,'sixteen output capacity')
        check(d['fitted_component_count']==110==len(p) and d['fitted_pad_count']==552==sum(len(x['pins']) for x in p.values()),'part/pad inventory')
        check(d['continuous_limit_a_per_channel']==.5 and d['continuous_limit_a_per_quad']==2 and d['paired_current_limits'] is True,'frozen electrical limits')
        check(d['driver_por_current_limit_a']==1.25 and d['driver_commission_current_limit_a']==[.62,.72,.82] and d['driver_commission_current_limit_code']==6,'POR differs from qualified 0.72A setting')
        check([x['id'] for x in d['channels']]==[f'DO{i}' for i in range(16)],'channel IDs')
        check(not any(d[k] for k in ['manufacturing_ready','physical_qualification','whole_permission_path_complete','limits_enforced_by_firmware']),'incomplete controller/source not represented as qualified')
        check(d['hardware_gate_is_complete'] and d['no_automatic_reenable'],'rearm latch required')
        regs=d['register_requirements']
        check(regs=={'SW_STATE':0,'FS_SW_STATE':0,'DEV_CONFIG1':6,'DEV_CONFIG2':6,'DEV_CONFIG3':64,'CRC_EN':True,'ADC_EN':True,'WD_EN':True,'WD_TO':0,'watchdog_nominal_s':400e-6,'AUTO_RETRY_DIS':True,'SW_STATE_zero_readback_before_CARD_EN':True,'per_chip_configuration_readback_before_enable':True,'IOL1_crc_epoch_sequence_freshness_validate_before_commit':True,'inrush_boost_allowed':False,'parallel_channels_allowed':False,'off_state_open_load_excitation_default_allowed':False},'required safe commissioning register contract')
        check(d['measurement']['host_measurement_implemented'] is False and d['measurement']['calibration_implemented'] is False and d['measurement']['conversion_s']==128e-6 and d['measurement']['adc_reference_v']==[2.72,2.85],'ADC/readout evidence boundary')
        for bank,letter in enumerate(('A','B')):
            dom='DO'+letter; g=f'FIELD_{letter}_0V'; v=dom+'_FIELD_3V3'; domrec=d['domains'][bank]; lr,gr,ir=('U10001','U10002','U10003') if bank==0 else ('U10014','U10015','U10016')
            check(domrec['id']==dom and domrec['latch_ref']==lr and domrec['gate_ref']==gr and domrec['isolator_ref']==ir,'domain/reference assignment')
            check(all(domrec[k] is False for k in ['field_logic_supply_implemented','controller_implemented','serial_watchdog_implemented','physical_connector_implemented']),'unimplemented parent boundary')
            check(p[ir]['mpn']=='ISO7762FDBQR','default LOW F isolator exact part')
            pin(ir,expected_iso(letter))
            check(p[lr]['mpn']=='SN74LVC1G74DCUR' and p[gr]['mpn']=='SN74LVC08APWR','latch/gate exact IC')
            pin(lr,{1:dom+'_IO_ENABLE_STROBE',2:'IO_3V3',3:None,4:'LOGIC_GND',5:dom+'_OUT_EN_LATCH',6:dom+'_CLR_N',7:'IO_3V3',8:'IO_3V3'})
            pin(gr,{1:'OUT_PERMIT_'+letter,2:dom+'_CONTROLLER_RESET_N',3:dom+'_CLR_N',4:'OUT_PERMIT_'+letter,5:dom+'_OUT_EN_LATCH',6:dom+'_PERMIT_LATCHED',7:'LOGIC_GND',8:dom+'_DO_EN_LOGIC',9:dom+'_PERMIT_LATCHED',10:dom+'_CARD_EN',11:None,12:'LOGIC_GND',13:'LOGIC_GND',14:'IO_3V3'})
            for name in ['OUT_PERMIT_'+letter,dom+'_CONTROLLER_RESET_N',dom+'_IO_ENABLE_STROBE',dom+'_CARD_EN',dom+'_DO_EN_LOGIC',dom+'_SCLK_HOST',dom+'_SDI_HOST']:
                check(len(passive_between(name,'LOGIC_GND','R',10000))==1,'logic fail-off bias '+name)
            check(len(passive_between(dom+'_DO_EN_FIELD',g,'R',10000))==1,'field DO_EN pull-off')
            check(len(passive_between(dom+'_FLT_N_FIELD',v,'R',10000))==1,'wired-OR FLT pull-up')
            drivers=['U10004','U10009'] if bank==0 else ['U10017','U10022']
            check(domrec['driver_refs']==drivers,'two chips per output domain')
            for q,dr in enumerate(drivers):
                check(p[dr]['mpn']=='TPS274C65ASRHAR' and p[dr]['footprint']=='CNC_MB_DO:TPS274C65_RHA40_TI','TPS AS part/package')
                pin(dr,expected_driver(letter,q))
                check(p[dr]['spi_address']==q and p[dr]['internal_regulator_enabled'] is False,'address/external field VDD')
                addr=passive_between(f'{dom}_Q{q}_ADDRESS',g,'R',13300 if q==0 else 17800)
                check(len(addr)==1 and p[addr[0]]['tolerance']<.01,'<1% address resistor identity')
                check(len(passive_between(f'{dom}_Q{q}_ISNS',g,'R',1000))==1 and len(passive_between(f'{dom}_Q{q}_ISNS',g,'C',100e-12))==1,'ISNS RC to internal ADC')
            for i in range(bank*8,bank*8+8):
                ch=d['channels'][i]; q=(i%8)//4; dr=drivers[q]
                check(ch['logical_net']==f'DO{i:02}' and ch['driver']==dr and ch['chip_channel']==i%4+1 and ch['bank']==letter,'channel/driver/pad mapping')
                check(ch['continuous_limit_a']==.5 and ch['group_continuous_limit_a']==2 and ch['group']==bank*8+q*4 and ch['default_current_limit_code']==6 and ch['paired_ilim_resource']==dr+'_ILIM_'+('12' if i%4<2 else '34'),'channel paired-current resource')
                fr=ch['rcb_fet'];check(p[fr]['mpn']=='CSD19538Q3AT' and p[fr]['footprint']=='CNC_MB_DO:CSD19538_DNH8_TI','RCB MOSFET exact part/package')
                pin(fr,{1:f'DO{i:02}_SW',2:f'DO{i:02}_SW',3:f'DO{i:02}_SW',4:f'DO{i:02}_RCB_GATE',5:f'DO{i:02}',6:f'DO{i:02}',7:f'DO{i:02}',8:f'DO{i:02}',9:f'DO{i:02}'})
                cap=p[ch['output_filter']];check(cap['pins']=={'1':f'DO{i:02}','2':g} and abs(cap['capacitance_f']-22e-9)<1e-18 and cap['voltage_rating_v']==100,'output cap after reverse blocking FET')
        for ref,x in p.items():
            check(x['physical'] is True and x['mpn'] and x['footprint'],'fitted part has exact identity '+ref)
            domains=set(x['pins'].values());check(not ({'LOGIC_GND','FIELD_A_0V'}<=domains or {'LOGIC_GND','FIELD_B_0V'}<=domains) or x['kind']=='ISO','no direct isolation bridge '+ref)
        check(len(d['boundaries'])==6,'six explicit integration boundaries')
        for b in d['boundaries'].values():check(b['physical'] is False and b['mpn']==b['footprint']=='','boundary cannot become invented fitted connector')
        if netlist:
            actual=native(netlist);check(set(actual)==set(p)|set(d['boundaries']),'native/reference population')
            for ref,x in {**p,**d['boundaries']}.items():
                check(actual.get(ref)=={k:x[k] for k in ['mpn','footprint','value','pins']},ref+' native symbol/pin/export mismatch')
        if erc:
            e=json.loads(Path(erc).read_text(encoding='utf-8'));check(e['ignored_checks']==[],'no ERC suppression')
            vs=[v for s in e['sheets'] for v in s['violations']];check(len(vs)==2,'only two documented native ground-name warnings')
            seen=set()
            for v in vs:
                item=v.get('items',[{}])[0]; key=item.get('uuid');seen.add(key)
                check(v.get('severity')=='warning' and v.get('type')=='ground_pin_not_ground' and item.get('description') in ['Symbol U10003 Pin 9 [GND2, Power input, Line]','Symbol U10016 Pin 9 [GND2, Power input, Line]'],'unexpected ERC warning/error')
            check(len(seen)==2 and len({v['items'][0]['description'] for v in vs})==2,'unique exact field-return ERC references')
        if fpdir:
            fpdir=Path(fpdir); pads,paste=footprint_pads(fpdir/'TPS274C65_RHA40_TI.kicad_mod')
            check(set(pads)=={str(i) for i in range(1,42)} and len(paste)==9,'RHA numbered/thermal/paste lands')
            for i in range(1,41):
                if i<=10: at=(-2.9,-2.25+(i-1)*.5);size=(.6,.25)
                elif i<=20:at=(-2.25+(i-11)*.5,2.9);size=(.25,.6)
                elif i<=30:at=(2.9,2.25-(i-21)*.5);size=(.6,.25)
                else:at=(2.25-(i-31)*.5,-2.9);size=(.25,.6)
                check(pads[str(i)]['at']==at and pads[str(i)]['size']==size,'RHA physical pad orientation/geometry')
            check(pads['41']['at']==(0,0) and pads['41']['size']==(4.15,4.15) and pads['41']['layers']==['F.Cu','F.Mask'],'RHA ground EP no full-size paste')
            check({x['at'] for x in paste}=={(x,y) for x in [-1.37,0,1.37] for y in [-1.37,0,1.37]} and all(x['size']==(1.17,1.17) for x in paste),'RHA 72% printed stencil example')
            pads,paste=footprint_pads(fpdir/'ISO7762_DBQ16_TI.kicad_mod');check(set(pads)=={str(i) for i in range(1,17)} and not paste,'DBQ physical population')
            for i in range(1,17):check(pads[str(i)]['at']==(-2.7 if i<=8 else 2.7,round(-2.2225+(i-1)*.635 if i<=8 else 2.2225-(i-9)*.635,4)) and pads[str(i)]['size']==(1.6,.41),'DBQ manufacturer pad geometry')
            pads,paste=footprint_pads(fpdir/'CSD19538_DNH8_TI.kicad_mod');check(set(pads)=={str(i) for i in range(1,10)} and len(paste)==12,'DNH physical numbered/paste population')
            for i in range(1,9):check(pads[str(i)]['at']==(-1.55 if i<=4 else 1.55,round(-.975+(i-1)*.65 if i<=4 else .975-(i-5)*.65,4)) and pads[str(i)]['size']==(.7,.4) and pads[str(i)]['mask']==-.05,'DNH source/gate/drain finger geometry')
            check(pads['9']['at']==(.3275,0) and pads['9']['size']==(1.875,2.55) and pads['9']['mask']==-.05,'DNH offset drain EP/mask-defined land')
        check(request_limits([{'continuous_a':.5,'code':6} for _ in range(16)]),'qualified limit screen')
    except (KeyError,ValueError,TypeError,OSError,ET.ParseError,IndexError) as exc:errors.append('invalid design/evidence: '+str(exc))
    return {'ok':not errors,'errors':errors,'manufacturing_ready':False,'physical_qualification':False,'component_count':len(d.get('components',{})),'fitted_pad_count':d.get('fitted_pad_count'),'warnings':['Two native ground_pin_not_ground warnings are exact ISO7762 pin9 FIELD_A/B_0V power returns; distinct isolated grounds are required, and the independent pin/domain check proves their connection. No native warning is suppressed.','Required commissioning ILIM=0.72A is a register requirement, not the POR default1.25A or implemented firmware. Missing controller/reset/enable stays inhibited; controller and verified register driver remain parent work.','Gate/default structure is checked; loaded 20ms end-to-end inhibit, IOL1 watchdog timing, analogue accuracy, surge/inductive energy, thermal/current paths and final PCB remain unmeasured.']}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    result=validate(json.loads((OUT/'design.json').read_text(encoding='utf-8')),OUT/'netlist.xml',OUT/'erc.json',OUT/'CNC_MB_DO.pretty')
    if args.write:(OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['ok'] else 1)
