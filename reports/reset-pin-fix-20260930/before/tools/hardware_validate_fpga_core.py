"""Independent physical-pin and support-circuit checks. No timing/board certification."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/fpga_core'
RESEARCH=ROOT/'research/fpga-core'
FIXED={'R1':'FPGA_CDONE','P1':'FPGA_LOCAL_RESET_N','H3':'FPGA_CLK_50M','D5':'FPGA_USER_RESET_N',
       'M2':'FPGA_JTAG_TCK','K5':'FPGA_JTAG_TDI','L5':'FPGA_JTAG_TDO','M1':'FPGA_JTAG_TMS',
       'P3':'FPGA_FLASH_CS_N','M3':'FPGA_FLASH_CCK_SOURCE','L3':'FPGA_FLASH_MOSI','N1':'FPGA_FLASH_MISO',
       'N3':'FPGA_CFG_CSI','L12':'FPGA_CFG_TEST_N','R16':'FPGA_CFG_CBUS2','L14':'FPGA_CFG_CBUS1','K13':'FPGA_CFG_CBUS0',
       'D7':'FPGA_CFG_CBSEL1','C7':'FPGA_CFG_CBSEL0','B8':'FPGA_CFG_NSTATUS'}
SUPPORT={'U2':{'1':'FPGA_FLASH_CS_N','2':'FPGA_FLASH_MISO','3':'FPGA_FLASH_IO2','4':'LOGIC_GND','5':'FPGA_FLASH_MOSI','6':'FPGA_FLASH_CCK','7':'FPGA_FLASH_IO3','8':'IO_3V3'},
         'U3':{'1':'FPGA_CRESET_N','2':'FPGA_SERVICE_RUN_N','3':'LOGIC_GND','4':'FPGA_LOCAL_RESET_N','5':'IO_3V3'},
         'U4':{'1':'FPGA_USER_RESET_RC','2':'LOGIC_GND','4':'FPGA_USER_RESET_DELAYED','5':'IO_3V3'},
         'U5':{'1':'FPGA_USER_RESET_DELAYED','2':'FPGA_SERVICE_RUN_N','3':'LOGIC_GND','4':'FPGA_USER_RESET_N','5':'IO_3V3'},
         'Y1':{'1':'IO_3V3','2':'LOGIC_GND','3':'FPGA_CLK_SOURCE','4':'IO_3V3'}}
PULLUPS=['FPGA_CDONE','FPGA_CFG_CSI','FPGA_CFG_TEST_N','FPGA_FLASH_CS_N','FPGA_CFG_CBUS2','FPGA_CFG_CBUS1','FPGA_CFG_CBUS0','FPGA_JTAG_TCK','FPGA_JTAG_TDI','FPGA_JTAG_TMS','FPGA_JTAG_TDO','FPGA_FLASH_IO2','FPGA_FLASH_IO3','FPGA_SERVICE_RUN_N','FPGA_CFG_NSTATUS']


def primary_pins(path=RESEARCH/'t20-pinout.xlsx'):
    """Read workbook independently, not the generator's JSON extraction."""
    ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(path) as z:
        strings=[''.join(v.itertext()) for v in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)]
        wb=ET.fromstring(z.read('xl/workbook.xml'))
        sheet=next(v for v in wb.findall('s:sheets/s:sheet',ns) if v.attrib['name']=='T20F256')
        rid=sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
        rel=next(v for v in ET.fromstring(z.read('xl/_rels/workbook.xml.rels')) if v.attrib['Id']==rid)
        target=rel.attrib['Target'];target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
        root=ET.fromstring(z.read(target));result={}
        for row in root.findall('s:sheetData/s:row',ns):
            cells={}
            for c in row.findall('s:c',ns):
                v=c.findtext('s:v','',ns)
                cells[''.join(k for k in c.attrib['r'] if k.isalpha())]=strings[int(v)] if c.attrib.get('t')=='s' and v else v
            if 4<=int(row.attrib['r'])<=259:
                ball=cells.get('G','');result[ball]={'name':cells.get('B',''),'bank':cells.get('A',''),'config':cells.get('C',''),'row':int(row.attrib['r'])}
    if len(result)!=256:raise ValueError('primary XLSX did not yield 256 unique balls')
    return result


def exported(path):
    xml=ET.parse(path).getroot();parts={}
    for c in xml.findall('components/comp'):
        ref=c.attrib['ref']
        if ref in parts:raise ValueError('duplicate reference in export')
        fields={v.attrib['name']:v.text or '' for v in c.findall('fields/field')}
        parts[ref]={'value':c.findtext('value',''),'mpn':fields.get('MPN',''),'pins':{}}
    for n in xml.findall('nets/net'):
        for node in n.findall('node'):
            ref,pin=node.attrib['ref'],node.attrib['pin']
            if ref.startswith('#'):continue
            if pin in parts[ref]['pins']:raise ValueError('duplicate connected pin in export')
            net=n.attrib['name'].removeprefix('/')
            if not net.startswith('unconnected-'):parts[ref]['pins'][pin]=net
    sym=next(v for v in xml.findall('libparts/libpart') if v.attrib['part']=='T20F256I4')
    pins={v.attrib['num']:v.attrib['name'] for v in sym.findall('pins/pin')}
    return parts,pins


def calculations(d):
    p=d['components'];vmax=d['rails']['IO_3V3']['permitted_v'][1]
    cap={rail:sum(v['capacitance_f'] for ref,v in p.items() if ref.startswith('C') and v['pins']['1']==rail) for rail in ('CORE_1V2','IO_3V3')}
    capmax={rail:sum(v['capacitance_f']*(1+v['tolerance'])*(1+v['temperature_change']) for ref,v in p.items() if ref.startswith('C') and v['pins']['1']==rail) for rail in cap}
    # Table75: CRESET AND user GPIO D5 can each pull up through27k in configuration.
    # Screen includes10uA gate Ioff,10uA each FPGA input,5uA permission input.
    gpu=1/(47000*.99)+2/27000
    highzmax=(vmax*gpu+35e-6)/(gpu+1/(1000*1.01))
    integrated=(vmax*gpu+35e-6)/(gpu+1/(1000*1.01)+1/(10000*1.01))
    static=.019+.025+.000010+len(PULLUPS)*vmax/9900+3*vmax/9900+vmax/(1000*.99)
    return {'nominal_bypass_f':cap,'max_bypass_before_dc_bias_f':capmax,'reset_high_z_screen_max_v':highzmax,
            'reset_with_permission_10k_pulldown_screen_max_v':integrated,
            'reset_output_high_load_max_a':vmax/(1000*.99)+vmax/(10000*.99)+25e-6,
            'cdone_asserted_pullup_sink_max_a':vmax/9900+vmax/27000+15e-6,
            'cdone_released_screen_min_v':3.14-15e-6/(1/10100+1/65000),
            'support_static_current_screen_a':static,'support_reservation_a':d['rails']['IO_3V3']['additional_support_reservation_a'],
            'single_image_bytes':d['bitstream_max_bits']//8,'flash_capacity_bytes':d['flash_bits']//8,
            'flash_image_size_fraction':d['bitstream_max_bits']/d['flash_bits'],
            'clock_50ppm_rate_error_hz':d['clock_hz']*50e-6,
            'limitations':['Static screen excludes unbounded GPIO/trace switching loads;60mA is an allocation, not a proved worst case.',
                          'Capacitor DC-bias/aging minima, mounting inductance, rail ramps and transient stability are not proved.',
                          'Reset screen includes both internal pullups; .8V is only a generic GPIO comparison. Dedicated CRESET Schmitt table lists thresholds without min/max; no guaranteed reset threshold is claimed.',
                          'Gate VOH>=2.4V at3V/16mA is a component limit; dedicated reset compatibility, partial-power transfer and shutdown still need confirmation.',
                          'Flash single-image fit does not implement atomic recovery, field-update security or a multiboot loader.']}


def validate(d=None,a=None,netlist=None,erc=None,check_sources=True):
    if d is None:d=json.loads((OUT/'design.json').read_text(encoding='utf-8'))
    if a is None:a=json.loads((OUT/'pin-allocation.json').read_text(encoding='utf-8'))
    errors=[];calc={}
    def need(ok,msg):
        if not ok:errors.append(msg)
    try:
        p=d['components'];official=primary_pins();wired=a['pin_net']
        need(not any(d[k] for k in ('manufacturing_ready','fpga_package_fit_proved','physical_qualification')),'unearned qualification claim')
        need(set(p)=={'U1','U2','U3','U4','U5','Y1'}|{f'R{i}' for i in range(1,26)}|{f'C{i}' for i in range(1,40)}|{f'J{i}' for i in range(1,11)},'component set differs from70 physical candidates+10 boundaries')
        need(p['U1']['mpn']=='T20F256I4','wrong FPGA grade/package')
        need(p['U2']['mpn']=='W25Q32JVSSIQ' and p['U3']['mpn']=='SN74LVC1G08DCKR' and p['U4']['mpn']=='74LVC1G17GW' and p['U5']['mpn']=='SN74LVC1G08DCKR' and p['Y1']['mpn']=='ASE-50.000MHZ-L-C-T','wrong support device')
        need(p['U1']['pins']==wired,'U1 allocation differs from actual modeled pins')
        need(all(wired.get(ball)==net for ball,net in FIXED.items()),'critical configuration/clock/reset pin assignment')
        need(set(wired)<=set(official),'unknown package ball')
        for ball,info in official.items():
            n=info['name'];expected='LOGIC_GND' if n=='GND' else 'IO_3V3' if n.startswith('VCCIO') else 'CORE_1V2' if n.startswith('VCC') else None
            if expected:need(wired.get(ball)==expected,'supply/ground pin '+ball+' must connect '+expected)
        need(set(x['ball'] for x in a['unconnected'])==set(official)-set(wired),'NC inventory incomplete or required pin hidden')
        need('R2' not in wired and not any(official[x]['name'].startswith('GPIOB') for x in wired),'REF_RES/native LVDS policy changed')
        user=a['user_allocations'];need(len(user)==96 and len({x['ball'] for x in user})==96,'96 unique user allocations required')
        need(len({x['net'] for x in user})==96,'logical user signal collision')
        for x in user:
            source=official[x['ball']]
            need(all(x[k]==source[k] for k in ('name','bank','config','row')),'user ball source trace mismatch')
            need(not source['config'] and source['name'].startswith(('GPIOL','GPIOR')),'user allocation collides with configuration/native LVDS')
            need(wired.get(x['ball'])==x['net'],'user allocation net differs')
        required={f'{kind}{i}_FPGA' for kind in ('STEP','DIR','HOME','ALM') for i in range(12)}|{f'DRIVE_ENABLE{i}_FPGA_RESERVED' for i in range(12)}|{f'ENC{i}_{s}_FPGA' for i in range(4) for s in 'ABZ'}
        need(required<={x['net'] for x in user},'12-motor/four-encoder capacity contract')
        for ref,expected in SUPPORT.items():need(p[ref]['pins']==expected,ref+' exact support pin mapping')
        rpairs=[('FPGA_CLK_SOURCE','FPGA_CLK_50M',33),('FPGA_FLASH_CCK_SOURCE','FPGA_FLASH_CCK',33)]+[('IO_3V3',n,10000) for n in PULLUPS]+[('FPGA_CFG_CBSEL0','LOGIC_GND',10000),('FPGA_CFG_CBSEL1','LOGIC_GND',10000),('IO_3V3','FPGA_LOCAL_RESET_N',47000),('FPGA_LOCAL_RESET_N','LOGIC_GND',1000),('FPGA_CDONE','FPGA_USER_RESET_RC',10000)]+[(n,'LOGIC_GND',10000) for n in ('FPGA_ENDPOINT_READY','FPGA_MOTION_REQUEST','FPGA_PROGRESS_WDI')]
        for i,(n1,n2,r) in enumerate(rpairs,1):
            v=p[f'R{i}'];need(v['pins']=={'1':n1,'2':n2} and v['resistance_ohm']==r,f'R{i} pull/termination connection or value')
        supply=[(ball,info) for ball,info in official.items() if info['name'].startswith('VCC')]
        for i,(ball,info) in enumerate(supply,1):need(p[f'C{i}']['pins']=={'1':wired[ball],'2':'LOGIC_GND'} and p[f'C{i}']['capacitance_f']==.1e-6 and p[f'C{i}']['placement_target']==ball,'per-ball bypass '+ball)
        need(p['C39']['pins']=={'1':'FPGA_USER_RESET_RC','2':'LOGIC_GND'} and p['C39']['capacitance_f']==1e-6,'post-CDONE reset delay capacitor')
        for ref,v in p.items():
            need(not any('FIELD' in n or 'SIGNAL_5V' in n for n in v['pins'].values()),'forbidden voltage/domain on '+ref)
            if ref.startswith('C'):
                need(v['voltage_v']>=6.3 and v['pins']['2']=='LOGIC_GND',ref+' capacitor rating/return')
                need(type(v['capacitance_f']) in (int,float) and math.isfinite(v['capacitance_f']) and v['capacitance_f']>0,ref+' capacitance')
            if ref.startswith('J'):need(v['role']=='schematic_boundary_not_orderable',ref+' must remain explicit boundary')
        need(d['rails']['CORE_1V2']['permitted_v']==[1.15,1.25] and d['rails']['IO_3V3']['permitted_v']==[3.14,3.465],'supply rating intersection changed')
        need(d['clock_hz']==50000000 and d['bitstream_max_bits']==5445600 and d['flash_bits']==33554432,'clock/flash capacity source facts')
        need(d['configuration_mode']=='active_SPI_x1_CBUS111','configuration mode changed')
        calc=calculations(d)
        need(calc['reset_high_z_screen_max_v']<.4,'reset default divider exceeds conservative screening target')
        need(calc['support_static_current_screen_a']<calc['support_reservation_a'],'support current reservation below static screen')
        if check_sources:
            for name,sha in d['source_sha256'].items():need(hashlib.sha256((RESEARCH/name).read_bytes()).hexdigest()==sha,'source hash changed: '+name)
            need(a['source_sha256']==hashlib.sha256((RESEARCH/'t20-pinout.xlsx').read_bytes()).hexdigest(),'allocation source hash')
        if netlist:
            actual,symbol=exported(netlist);need(set(actual)==set(p),'native export component set')
            need(symbol=={ball:v['name'] for ball,v in official.items()},'native symbol pin table differs from manufacturer')
            for ref,v in actual.items():
                for k in ('value','mpn','pins'):need(v[k]==p[ref][k],ref+' native export '+k+' mismatch')
        if erc:
            j=json.loads(Path(erc).read_text(encoding='utf-8'))
            need(set(j.get('included_severities',[]))>={'error','warning'},'ERC severity coverage incomplete')
            need(len(j.get('sheets',[]))==1 and all(not s.get('violations') for s in j['sheets']),'ERC contains violations or missing sheet')
            need({x['key'] for x in j['ignored_checks']}=={'single_global_label','four_way_junction','simulation_model_issue','footprint_filter'},'unexpected ERC suppression')
    except (KeyError,TypeError,ValueError,OverflowError,OSError,ET.ParseError) as e:errors.append('malformed or incomplete evidence: '+str(e))
    return {'ok':not errors,'manufacturing_ready':False,'errors':errors,'calculations':calc,'warnings':['Package pins are sourced; this allocation has not passed Efinity interface placement/routed timing/bitstream generation.','Enable stages and extra alarm/home/ABZ circuits remain incomplete;12STEP/DIR pins are not12 complete machine channels.','All interfaces are unisolated internal3.3V logic. Field interfaces require the separate protected circuits.','GPIO startup pulls are not a safety function; independent permission must inhibit unconfigured outputs.','No PCB,PDN simulation,DRC,programmer qualification,physical measurements or industrial qualification exists.']}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=OUT/'validation.json');args=ap.parse_args()
    r=validate(netlist=OUT/'netlist.xml',erc=OUT/'erc.json');args.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps({'ok':r['ok'],'errors':r['errors'],'manufacturing_ready':False}));return 0 if r['ok'] else 1


if __name__=='__main__':raise SystemExit(main())
