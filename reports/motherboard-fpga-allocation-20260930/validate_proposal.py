"""Independently check workbook columns, retained pads, direction and scope."""
from __future__ import annotations
import collections
import copy
import hashlib
import json
import pathlib
import re
import xml.etree.ElementTree as ET
import zipfile

REPORT=pathlib.Path(__file__).resolve().parent
ROOT=REPORT.parents[1]
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def archived(n):return json.loads((REPORT/'inputs'/n).read_text(encoding='utf8'))

def package():
    ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(REPORT/'inputs/research/fpga-core/t20-pinout.xlsx') as z:
        strings=[''.join(v.itertext()) for v in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)]
        wb=ET.fromstring(z.read('xl/workbook.xml'))
        sheet=next(v for v in wb.findall('s:sheets/s:sheet',ns) if v.attrib['name']=='T20F256')
        rid=sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
        rel=next(v for v in ET.fromstring(z.read('xl/_rels/workbook.xml.rels')) if v.attrib['Id']==rid)
        target=rel.attrib['Target'];target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
        rows=ET.fromstring(z.read(target));pins={}
        for row in rows.findall('s:sheetData/s:row',ns):
            idx=int(row.attrib['r'])
            if not 4<=idx<=259:continue
            c={}
            for cell in row.findall('s:c',ns):
                v=cell.findtext('s:v','',ns)
                c[re.sub(r'\d','',cell.attrib['r'])]=strings[int(v)] if cell.attrib.get('t')=='s' and v else v
            pins[c['G']]=dict(manufacturer_pin=c.get('B',''),bank=c.get('A',''),
                manufacturer_configuration_function=c.get('C',''),manufacturer_lvds_resource=c.get('D',''),
                worksheet_row=idx,clock_region=c.get('F',''))
    if len(pins)!=256:raise ValueError('Workbook must provide 256 unique physical balls')
    return pins

SUPPORT_OUTPUTS={
 'OPI_REARM_M','OPI_REARM_O','XS_SCLK','XS_MOSI','XS_CS_N','XS_SYNC_STROBE','XS_REFCLK',
 'FPGA_PROGRESS_M','FPGA_PROGRESS_O','FPGA_MOTION_REQUEST','FPGA_OUTPUT_REQUEST','FPGA_ENDPOINT_READY',
 'WATCHDOG_TRIP_CLEAR','FPGA_LINK_FAULT','FPGA_WATCHDOG_FAULT','FPGA_INHIBIT_FAULT','FPGA_TIMING_FAULT','PERMIT_OUT_REQ'}
SUPPORT_INPUTS={
 'MOTION_A_PGOOD','MOTION_B_PGOOD','TAMPER_CLEAR_N','RAILS_OK_FPGA',
 'OPI_OK_TX','OPI_OK_A','OPI_OK_B','OPI_OK_BOE','OPI_OK_OUT','XS_MISO',
 'WD_M_OK','WD_O_OK','TX_PERMIT','OUT_PERMIT','PROC_PERMIT','RAW_INHIBIT_N',
 'WATCHDOG_TRIP_M','WATCHDOG_TRIP_O','FPGA_CLK_50M','FPGA_USER_RESET_N'}
REUSE={'SPARE_FPGA':'HOST_SPI_CS_CMD_N','SPINDLE_FAULT_FPGA':'PERMIT_OUT_REQ',
       'SPINDLE_READY_FPGA':'FPGA_OUTPUT_REQUEST','LUBE_STATUS_FPGA':'FPGA_PROGRESS_O','CYCLE_START_FPGA':'OPI_REARM_O'}

def expected():
    directions={}
    req=archived('hardware/motherboard/requirements.json')
    for r in req['terminal_function_mapping']:
        resource=r['resource'];s=resource.get('signal')
        if resource.get('kind')!='fpga_pin' or not s:continue
        # Exact token matching distinguishes ENn from ENC ABZ inputs.
        output=bool(re.fullmatch(r'(STEP\d+|DIR\d+|EN\d+_N|PWM\d+)_FPGA|PEN\d+_CMD|ARM_LAMP_FPGA',s))
        directions[s]='output' if output else 'input'
    for n in range(4):
        for tail,d in [('SCLK','output'),('MOSI','output'),('MISO','input'),('CS_N','output')]:directions[f'IOL1_L{n}_{tail}']=d
    for stem in ('FAST','EX8','HEALTH'):
        for tail,d in [('SR_CLK','output'),('SR_LOAD_N','output'),('SR_DATA','input')]:directions[f'{stem}_{tail}']=d
    for tail,d in [('SCLK','input'),('MOSI','input'),('MISO','output'),('CS_FB_N','input'),('CS_CMD_N','input')]:directions[f'HOST_SPI_{tail}']=d
    directions.update({n:'output' for n in SUPPORT_OUTPUTS})
    directions.update({n:'input' for n in SUPPORT_INPUTS})
    assert len(directions)==169
    return directions

def validate(p):
    errors=[]
    def need(q,m):
        if not q:errors.append(m)
    pins=package();directions=expected()
    for key in ('manufacturing_ready','vendor_fit','physical_qualification'):need(p.get(key) is False,'Unproved scope flag '+key)
    old=archived('hardware/fpga_core/pin-allocation.json')
    alias=archived('hardware/motion_card/assembly-map.json')['aliases']['fpga_core']
    alias.update({'HOST_SPI_CS_N':'HOST_SPI_CS_FB_N','PROBE_FPGA':'PRB0_FPGA',
        'TOOLSETTER_FPGA':'PRB1_FPGA','PROTECTIVE_STATUS_FPGA':'EXT_PERMIT_FPGA','HW_WATCHDOG_OK_N':'RAW_INHIBIT_N'})
    old_user={alias.get(r['net'],r['net']):r['ball'] for r in old['user_allocations']}
    old_user['FPGA_CLK_50M']='H3'
    gpio={b for b,r in pins.items() if r['manufacturer_pin'].startswith('GPIO')}
    fixed={b for b in gpio if b in old['pin_net'] and b not in set(old_user.values())}
    available=gpio-fixed
    need((len(gpio),len(fixed),len(available))==(195,12,183),'Exact physical GPIO capacity')
    need(set(p['reserved_gpio_balls'])==fixed,'Reserved flash/configuration balls')
    need({r['signal']:r['direction'] for r in p['required_signal_inventory']}==directions,'Normative full signal inventory/directions')
    historical=set(old_user)-set(directions)
    need(len(historical)==19,'Canonical aliases must consume one existing pad each')
    need(sum(r['scope']=='motherboard_standard' and r['resource'].get('kind')=='fpga_pin' for r in archived('hardware/motherboard/requirements.json')['terminal_function_mapping'])>77,'Field terminals include duplicate differential pair positions; must deduplicate function signals')
    summaries={}
    for name,c in p['candidates'].items():
        rows=c['signals'];signals={r['signal'] for r in rows};balls=[r['ball'] for r in rows]
        need(len(signals)==len(rows),name+' duplicate signal')
        need(len(set(balls))==len(balls),name+' duplicate ball')
        need(set(balls)<=available,name+' consumes dedicated/configuration/power/ground pad')
        optional=name!='base_preserve_all_current'
        required=set(directions)
        if not optional:required={n for n in required if not re.fullmatch(r'ENC(?:[4-9]|10|11)_[ABZ]_FPGA|EX8_SR_(?:CLK|LOAD_N|DATA)',n)}
        historical_wanted=historical-set(REUSE) if name=='full_with_five_legacy_repurposes' else historical
        required|=historical_wanted
        need(signals|set(c['unassigned'])==required,name+' required coverage')
        need(not signals&set(c['unassigned']),name+' assigned/unassigned intersection')
        need(len(required)==c['required_with_retained_historical'],name+' required count')
        need(len(rows)==c['assigned'],name+' assigned count')
        need(set(c['unused_gpio_balls'])==available-set(balls),name+' free-pad accounting')
        need(c['source_package_capacity_pass']==(not c['unassigned']),name+' capacity result')
        bysignal={r['signal']:r for r in rows}
        for s,b in old_user.items():
            target=REUSE.get(s,s) if name=='full_with_five_legacy_repurposes' else s
            need(target in bysignal and bysignal[target]['ball']==b,name+' altered retained current pad '+s)
        for r in rows:
            pin=pins.get(r['ball'])
            if pin:
                for k in ('manufacturer_pin','bank','manufacturer_configuration_function','manufacturer_lvds_resource','worksheet_row','clock_region'):
                    need(r[k]==pin[k],name+' worksheet mismatch '+r['signal']+' '+k)
                lvds=bool(pin['manufacturer_lvds_resource'])
                need(r['mode']==('LVDS_as_GPIO' if lvds else 'ordinary_GPIO'),name+' GPIO mode '+r['signal'])
                if lvds:
                    for k in ('ddio','schmitt','internal_pulldown','drive_strength_selectable','slew_selectable'):
                        need(r['gpio_options'][k] is False,name+' unsupported LVDS feature '+k)
            need(r['direction']==directions.get(r['signal'],'input'),name+' wrong direction '+r['signal'])
            need(r['vccio_nominal_v']==3.3 and r['vccio_net']=='IO_3V3' and r['io_standard']=='3.3_V_LVCMOS',name+' bank voltage/standard '+r['signal'])
            need(r['vendor_fit'] is False and r['implemented_in_parent_cad'] is False and r['implemented_full_gateware'] is False,name+' false implementation evidence '+r['signal'])
        for bank in ('BANK4A','BANK4B'):
            outs=sum(r['bank']==bank and r['direction'] in ('output','bidirectional') for r in rows)
            need(outs<=16,name+' exceeds LVDS output recommendation '+bank)
            need(c['summary']['lvds_output_count_by_bank'][bank]==outs,name+' output-bank count '+bank)
        summaries[name]=dict(assigned=len(rows),unassigned=len(c['unassigned']),free=len(c['unused_gpio_balls']))
    need(len(p['candidates']['base_preserve_all_current']['signals'])==161,'Base pin result')
    need(len(p['candidates']['full_preserve_all_current']['unassigned'])==5,'Full preserve shortfall')
    need(len(p['candidates']['full_with_five_legacy_repurposes']['signals'])==183,'Full minimal-reuse pin result')
    need({x['old_logical_signal']:x['new_logical_signal'] for x in p['candidates']['full_with_five_legacy_repurposes']['existing_ball_repurposes']}==REUSE,'Exact five reuse ledger')
    h=p['health_register_candidate'];need(h['implemented'] is False,'Health circuitry is not implemented')
    need(len(h['measured_bits'])==31 and h['length_bits']==40,'Measured health register width')
    need(h['marker_positions']=={'36':0,'37':1,'38':0,'39':1} and h['marker_numeric']==10,'Explicit MSB/LSB health marker packing')
    need(set(h['wires'])=={'HEALTH_SR_CLK','HEALTH_SR_LOAD_N','HEALTH_SR_DATA'},'Measured health bus GPIO')
    need(sum(x['old_pins'] for x in p['semantic_topology_delta'])==175,'Inherited semantic delta tally')
    need(sum(x['new_pins'] for x in p['semantic_topology_delta'])==169,'Onboard semantic delta tally')
    for n,hash_ in p['source_sha256'].items():
        fp=REPORT/'inputs'/n
        need(fp.exists() and hashlib.sha256(fp.read_bytes()).hexdigest()==hash_,'Frozen source mismatch '+n)
    return dict(ok=not errors,errors=errors,source_only=True,native_vendor_fit=False,candidates=summaries)

def mutations(p):
    results=[]
    def run(name,alter):
        q=copy.deepcopy(p);alter(q);v=validate(q)
        results.append(dict(name=name,passed=not v['ok'],detected_errors=v['errors'][:3]))
    candidate='base_preserve_all_current'
    def rows(q):return q['candidates'][candidate]['signals']
    run('duplicate ball',lambda q:rows(q)[1].update(ball=rows(q)[0]['ball']))
    run('wrong manufacturer bank',lambda q:rows(q)[0].update(bank='BANK4B'))
    run('5 V logic-bank claim',lambda q:rows(q)[0].update(vccio_nominal_v=5))
    run('missing required frequency input',lambda q:q['candidates'][candidate].update(signals=[r for r in rows(q) if r['signal']!='FREQ1_FPGA']))
    run('encoder erroneously classified as enable output',lambda q:next(r for r in rows(q) if r['signal']=='ENC0_A_FPGA').update(direction='output'))
    run('dedicated configuration ball reused',lambda q:rows(q)[0].update(ball='P3'))
    run('retained STEP pad moved',lambda q:next(r for r in rows(q) if r['signal']=='STEP0_FPGA').update(ball='M13'))
    run('unsupported LVDS Schmitt option',lambda q:next(r for r in rows(q) if r['mode']=='LVDS_as_GPIO')['gpio_options'].update(schmitt=True))
    run('unsupported vendor-fit claim',lambda q:q.update(vendor_fit=True))
    run('unimplemented health marked complete',lambda q:q['health_register_candidate'].update(implemented=True))
    return results

if __name__=='__main__':
    p=read('hardware/motherboard/fpga-allocation-proposal.json')
    result=validate(p);tests=mutations(p)
    result['mutation_tests']=tests;result['mutation_tests_passed']=sum(x['passed'] for x in tests)
    (REPORT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['ok'] and all(t['passed'] for t in tests) else 1)
