"""Independent connectivity and default-state checks of motherboard motors.

No machine interfaces are opened. Native XML/ERC are supplied artifacts; this
validator does not relabel a host check as fresh native KiCad execution.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
import re
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/motherboard_motors'


def validate(model, xml_path=None, erc_path=None, verify_sources=True):
    errors=[];p=model['components'];physical={r:c for r,c in p.items() if c['physical']};counts=Counter(c['kind'] for c in physical.values())
    def check(cond,text):
        if not cond:errors.append(text)
    check(model['motor_count']==12 and len(model['channels'])==12,'All twelve motor interfaces must be fitted')
    check(model['general_di_consumed']==0 and model['general_do_consumed']==0,'Motor enables/alarms must not consume general I/O')
    check(model['architecture']=='one_custom_motherboard_all_12_fitted','Motor interface must not be a custom expansion card')
    for kind,number in [('AM26C31',6),('TLP3640A',12),('TLP4176A',12),('LVC07A',2),('TPS22918',2),('ISO1212',6),('LTC6994',2),('AHCT1G17',2),('LVC14A',2),('LVC00A',3),('LVC2G08',1),('LVC1G74',2)]:check(counts[kind]==number,f'{kind}: expected {number} fitted devices')
    exact_mpns={'AM26C31':'AM26C31IPWR','LVC07A':'74LVC07APW,118','TPS22918':'TPS22918DBVR','ISO1212':'ISO1212DBQR','LTC6994':'LTC6994IS6-2#TRPBF','AHCT1G17':'74AHCT1G17GVH','LVC14A':'74LVC14APW,118','LVC00A':'SN74LVC00APWR','LVC2G08':'SN74LVC2G08DCUR','LVC1G74':'SN74LVC1G74DCUR'}
    for ref,c in physical.items():
        if c['kind'] in exact_mpns:check(c['mpn']==exact_mpns[c['kind']],f'{ref}: MPN does not match reviewed IC truth/pin/leak specification')
    def find(kind,pins):return [(r,c) for r,c in physical.items() if c['kind']==kind and all(c['pins'].get(str(k))==v for k,v in pins.items())]
    def resist(a,b,ohms):return [(r,c) for r,c in physical.items() if c['kind']=='R' and c['resistance_ohm']==ohms and set(c['pins'].values())=={a,b}]
    def capac(a,b,nf):return [(r,c) for r,c in physical.items() if c['kind']=='C' and abs(c['capacitance_f']-nf*1e-9)<1e-15 and set(c['pins'].values())=={a,b}]
    for i,ch in enumerate(model['channels']):
        bank='A' if i<8 else 'B';peer='MIA' if i<8 else 'MX4'
        check(ch['motor']==i and ch['bank']==bank,f'M{i}: identity/bank wrong')
        tx=p.get(ch['tx_ref'],{});pins=tx.get('pins',{});s=i%2;sp=(1,2,3) if s==0 else (9,10,11);dp=(7,6,5) if s==0 else (15,14,13)
        for sig,group in [('STEP',sp),('DIR',dp)]:
            check(pins.get(str(group[0]))==f'{sig}{i}_TO_{peer}' and pins.get(str(group[1]))==f'{sig}{i}_P' and pins.get(str(group[2]))==f'{sig}{i}_N',f'M{i}: {sig} differential pin polarity/input assignment wrong')
            check(len(resist(f'{sig}{i}_TO_{peer}','LOGIC_GND',10000))==1,f'M{i}: receiving {sig} must have own low default')
        check(pins.get('4')==f'MOTOR_TX_GATE_{bank}' and pins.get('12')==f'MOTOR_5V_{bank}' and pins.get('16')==f'MOTOR_5V_{bank}' and pins.get('8')=='LOGIC_GND',f'M{i}: AM26C31 permission/power wrong')
        no=p.get(ch['enable_no_ref'],{});nc=p.get(ch['enable_nc_ref'],{})
        check(no.get('mpn')=='TLP3640A(TPL,E' and no.get('pins')=={'1':f'MOTOR_LED_5V_{bank}','2':f'MOTOR{i}_LED_MID','3':f'EN{i}_NO','4':f'EN{i}_COM'},f'M{i}: normally-open LED/contact pin assignment wrong')
        check(nc.get('mpn')=='TLP4176A(TP,F' and nc.get('pins')=={'1':f'MOTOR{i}_LED_MID','2':f'MOTOR{i}_LED_K','3':f'EN{i}_NC','4':f'EN{i}_COM'},f'M{i}: normally-closed LED/contact pin assignment wrong')
        check(len(resist(f'MOTOR{i}_LED_K',f'MOTOR{i}_LED_SINK',220))==1,f'M{i}: two photorelays must share one series-limited LED current')
        check(len(resist(f'EN{i}_N_TO_{peer}','MOTOR_IO_3V3',10000))==1,f'M{i}: enable default must be a receiver-own-rail pull-up')
        sink=p.get(ch['enable_sink_ref'],{});a,y=ch['enable_sink_input_pin'],ch['enable_sink_output_pin']
        pair=((1,2),(3,4),(5,6),(9,8),(11,10),(13,12))[i%6]
        gatepins=((1,2,3),(4,5,6),(9,10,8),(12,13,11))[i%4]
        check((a,y)==pair and (ch['enable_schmitt_input_pin'],ch['enable_schmitt_output_pin'])==pair and (ch['enable_nand_a_pin'],ch['enable_nand_b_pin'],ch['enable_nand_y_pin'])==gatepins,f'M{i}: reviewed physical gate pin tuple changed')
        check(sink.get('kind')=='LVC07A' and sink['pins'].get(str(a))==f'MOTOR{i}_SINK_OFF' and sink['pins'].get(str(y))==f'MOTOR{i}_LED_SINK' and sink['pins'].get('14')=='MOTOR_IO_3V3' and sink['pins'].get('7')=='LOGIC_GND',f'M{i}: individual open-drain enable sink wrong')
        inv=p.get(ch['enable_schmitt_ref'],{});nand=p.get(ch['enable_nand_ref'],{})
        check(inv.get('kind')=='LVC14A' and inv['pins'].get(str(ch['enable_schmitt_input_pin']))==f'EN{i}_N_TO_{peer}' and inv['pins'].get(str(ch['enable_schmitt_output_pin']))==f'MOTOR{i}_EN_ACTIVE' and inv['pins'].get('7')=='LOGIC_GND' and inv['pins'].get('14')=='MOTOR_IO_3V3',f'M{i}: enable default must enter Schmitt inverter')
        check(nand.get('kind')=='LVC00A' and nand['pins'].get(str(ch['enable_nand_a_pin']))==f'MOTOR{i}_EN_ACTIVE' and nand['pins'].get(str(ch['enable_nand_b_pin']))==f'MOTOR_TX_GATE_{bank}' and nand['pins'].get(str(ch['enable_nand_y_pin']))==f'MOTOR{i}_SINK_OFF' and nand['pins'].get('7')=='LOGIC_GND' and nand['pins'].get('14')=='MOTOR_IO_3V3',f'M{i}: NAND inhibit graph must force sink HIGH/off on GATE LOW')
        for name in ('NO','NC'):
            hits=find('TVS',{1:f'EN{i}_{name}',2:f'EN{i}_COM'})
            check(len(hits)==1 and hits[0][1]['mpn']=='SMBJ33CA-E3/52',f'M{i}: floating enable {name} clamp absent/wrong')
        ar=p[ch['alarm_receiver_ref']];j=i%2;pinset=(16,15,14,13,4) if not j else (11,10,9,12,5)
        expected={pinset[0]:f'ALM{i}_SENSE',pinset[1]:f'ALM{i}_IN',pinset[2]:'FIELD_GND',pinset[3]:f'ALM{i}_SUB_FLOAT',pinset[4]:f'ALM{i}_FPGA'}
        check(all(ar['pins'].get(str(k))==v for k,v in expected.items()),f'M{i}: isolated alarm pins, field return or floating substrate wrong')
        check(ar['pins'].get('2')=='MOTOR_IO_3V3' and ar['pins'].get('3')=='MOTOR_IO_3V3' and ar['pins'].get('1')=='LOGIC_GND' and ar['pins'].get('8')=='LOGIC_GND',f'M{i}: alarm logic rail/enable wrong')
        check(len(resist(f'ALM{i}_FIELD',f'ALM{i}_SENSE',1000))==1 and len(resist(f'ALM{i}_SENSE',f'ALM{i}_IN',562))==1 and len(capac(f'ALM{i}_SENSE','FIELD_GND',10))==1,f'M{i}: alarm threshold/current/filter absent')
    for bank,peer in (('A','MIA'),('B','MX4')):
        sw=find('TPS22918',{1:f'MOTOR_5V_{bank}',2:'LOGIC_GND',3:f'MOTOR_TX_GATE_{bank}',4:None,5:f'MOTOR_LED_5V_{bank}',6:f'MOTOR_LED_5V_{bank}'})
        check(len(sw)==1,f'Bank {bank}: hardware supply cut/QOD pin assignment wrong')
        check(len(resist(f'MOTOR_LED_5V_{bank}','LOGIC_GND',330))==1 and len(capac(f'MOTOR_LED_5V_{bank}','LOGIC_GND',100))==1,f'Bank {bank}: passive supply discharge/output capacitance missing')
        check(len(resist(f'TX_PERMIT_{bank}_TO_{peer}','LOGIC_GND',10000))==1 and len(resist(f'MOTOR_PERMIT_{bank}_SET','LOGIC_GND',60400))==1,f'Bank {bank}: digital permission setting/default missing')
        check(len(find('LTC6994',{1:f'MOTOR_PERMIT_{bank}_TTL_RESTORED',2:'LOGIC_GND',3:f'MOTOR_PERMIT_{bank}_SET',4:'LOGIC_GND',5:f'MOTOR_5V_{bank}',6:f'MOTOR_PERMIT_{bank}_FILTERED'}))==1,f'Bank {bank}: correct both-edge qualifier, code0, 5V rail and output required')
        check(len(find('AHCT1G17',{1:None,2:f'TX_PERMIT_{bank}_TO_{peer}',3:'LOGIC_GND',4:f'MOTOR_PERMIT_{bank}_TTL_RESTORED',5:f'MOTOR_5V_{bank}'}))==1,f'Bank {bank}: TTL Schmitt source restoration on qualifier-own-rail required')
        check(len(resist(f'MOTOR_TX_GATE_{bank}','LOGIC_GND',1000))==1,f'Bank {bank}: strong unpowered Ioff physical gate bias absent')
        check(len(find('LVC1G74',{1:f'OPI_REARM_{bank}',2:'MOTOR_IO_3V3',3:None,4:'LOGIC_GND',5:f'OPI_OK_{bank}',6:f'MOTOR_TX_GATE_{bank}',7:'MOTOR_IO_3V3',8:'MOTOR_IO_3V3'}))==1,f'Bank {bank}: OPI must be asynchronously cleared by exact physical gate')
    check(len(find('LVC2G08',{1:'MOTOR_PERMIT_A_FILTERED',2:'MOTOR_POWER_OK_A_QUALIFIED',7:'MOTOR_TX_GATE_A',5:'MOTOR_PERMIT_B_FILTERED',6:'MOTOR_POWER_OK_B_QUALIFIED',3:'MOTOR_TX_GATE_B'}))==1,'Both TX gates must include independent qualified local power')
    substrate_nets={f'ALM{i}_SUB_FLOAT' for i in range(12)}
    for net in substrate_nets:
        hits=[(ref,pin) for ref,c in p.items() for pin,n in c['pins'].items() if n==net]
        check(len(hits)==1 and p[hits[0][0]]['kind']=='ISO1212' and hits[0][1] in ('12','13'),f'{net}: floating substrate must remain a separate one-pad island')
    check(set(model['source_contract']['iso_substrate_islands'])==substrate_nets,'All twelve substrate islands must have explicit PCB requirements')
    for net,spec in model['source_contract']['iso_substrate_islands'].items():check(spec['minimum_copper_mm']==[2,2] and not spec['ground_connection'] and not spec['mutual_connection'],f'{net}: incorrect floating copper-island requirement')
    for ref,c in physical.items():
        check(c['mpn'] and c['footprint'],f'{ref}: exact MPN/footprint absent')
        check(int(ref[1:])>=6000,f'{ref}: reference collides with preserved MC')
        if c['kind'] not in ('TLP3640A','TLP4176A','TVS','ISO1212'):
            check(not ({'FIELD_GND','LOGIC_GND'}<=set(v for v in c['pins'].values() if v)),f'{ref}: direct cross-domain ground connection')
    xml_stats=None
    if xml_path:
        tree=ET.parse(xml_path);nets={};comps={e.attrib['ref']:e for e in tree.findall('./components/comp')}
        for net in tree.findall('./nets/net'):
            for n in net.findall('node'):nets[(n.attrib['ref'],n.attrib['pin'])]=net.get('name') or net.findtext('name')
        nchecked=0;ncchecked=0
        for ref,c in p.items():
            check(ref in comps,f'{ref}: source component absent from native XML')
            for pin,net in c['pins'].items():
                actual=nets.get((ref,pin));nchecked+=1
                if net is None:
                    ncchecked+=1;check(actual is None or actual.startswith('unconnected-'),f'{ref}.{pin}: declared isolated/NC pin unexpectedly connected')
                else:check(actual=='/'+net,f'{ref}.{pin}: native XML {actual!r} != standalone root name {"/"+net!r}')
        check(not (set(comps)-set(p)),f'Unexpected native XML components: {sorted(set(comps)-set(p))}')
        xml_stats={'source_components_checked':len(p),'source_pin_assignments_checked':nchecked,'native_nc_checked':ncchecked,'physical_components':len(physical)}
    erc_stats=None
    if erc_path:
        erc=json.loads(Path(erc_path).read_text(encoding='utf-8'));viol=[v for s in erc['sheets'] for v in s['violations']]
        # Exactly one label warning for each intentionally separate SUB copper
        # island is documented, not globally disabled or deleted with NC flags.
        labels=[]
        for v in viol:
            if v['type']=='isolated_pin_label' and v['severity']=='warning' and len(v['items'])==1:
                match=re.fullmatch(r"Label '(ALM\d+_SUB_FLOAT)'",v['items'][0]['description'])
                if match and match[1] in substrate_nets:labels.append(match[1])
        approved=labels
        check(set(labels)==substrate_nets,'Native ERC floating substrate labels must match all12 exact island names once')
        check(len(approved)==12 and len(viol)==12,f'Native ERC must contain only12 justified floating SUB label warnings; got {len(viol)} total/{len(approved)} matching')
        check(not erc.get('ignored_checks'),f'Native ERC ignored checks: {erc.get("ignored_checks")}')
        erc_stats={'violations':len(viol),'errors':sum(v['severity']=='error' for v in viol),'justified_floating_substrate_warnings':len(approved),'ignored_checks':erc.get('ignored_checks',[])}
    if verify_sources:
        for path,h in model['sources'].items():check((ROOT/path).exists() and hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h,f'Manufacturer source hash changed: {path}')
    # This screen includes switch drop and additional bleeder load, rather than
    # repeating the old circuit's ideal 5V arithmetic. Vf is only a 25C screen.
    imax=(5.15-1.5-1.0)/(220*.99)
    bankmax=8*imax+5.15/(330*.99);switch_drop=.079*bankmax
    imin=(4.85-switch_drop-1.8-1.3-.55)/(220*1.01)
    check(imin>.005 and imax<.025,'25C LED current screen outside intended 5-25mA')
    # LTC6.2% is the FULL-temperature accuracy, not the25C5.1% headline.
    # Independently add1% R tolerance and100ppm/C worst30C excursion from25C.
    rt=.01+100e-6*max(abs(0-25),abs(55-25));delay_nom=60400/50000*1e-6
    delay_min=delay_nom*(1-rt)*(1-.062);delay_max=delay_nom*(1+rt)*(1+.062)
    check(delay_min>.5e-6 and delay_max+10e-9<2e-6 and delay_min>100e-9,'Digital qualifier programmed intervals fail frozen rejection/acceptance/minimum width')
    check(model['source_contract']['ltc_full_temperature_delay_error']==.062 and model['source_contract']['rset_tcr_per_c']==100e-6,'Qualification used unreviewed timing/TCR bounds')
    check(model['source_contract']['powered_high_ioz_max_a']==10e-6 and model['source_contract']['vcc_zero_ioff_max_a']==10e-6,'Powered HIGH IOZ must be distinct from Ioff-at-zero')
    # Boolean evaluation uses the reviewed IC functions after their exact
    # actual source-pin graph above is checked; NAND and07 polarities differ.
    truth=[{'en_n':en,'gate':gate,'schmitt_en_active':1-en,'sink_input':1-((1-en)&gate),'led_on':bool((1-en)&gate)} for en in (0,1) for gate in (0,1)]
    tau=100e-9*1.1*330*1.01;dark_v=.0001*220*.99
    bleed_screen=tau*math.log(5.15/dark_v)
    # GATE withdrawal ->NAND(4.3ns)->07 LOW-to-Z(3.6ns). Photorelay
    # timing is ONLY25C at5mA/20V/200ohm. No capacitive-charge or thermal
    # measurements are hidden in this conditional timing arithmetic.
    powered_logic_withdraw_ns=4.3+3.6
    calculations={'led_current_screen_min_a':imin,'led_current_screen_max_a':imax,'bank_a_worst_led_and_bleed_a':bankmax,'switch_drop_screen_v':switch_drop,'photorelay_limits_are_25c_only':True,'bleed_worst_steady_power_w':5.15**2/(330*.99),'passive_bleed_tau_s':tau,'ideal_isolated_rail_discharge_to_100ua_s':bleed_screen,'bleed_screen_excludes_switch_delay_leakage_and_board_capacitance':True,'powered_logic_gate_to_sink_highz_max_ns_conditional':powered_logic_withdraw_ns,'relay_withdrawal_no_open_25c_max_s':.0002,'relay_withdrawal_nc_close_25c_max_s':.001,'relay_assertion_nc_open_25c_max_s':.003,'permission_qualifier_nominal_s':delay_nom,'permission_qualifier_min_s':delay_min,'permission_qualifier_max_s':delay_max,'qualifier_input_ttl_high_margin_v':2.38-2.0,'qualifier_input_ttl_low_margin_v':.5-.2,'level_restored_high_margin_v':4.4-.7*5.15,'level_restored_low_margin_v':.3*4.85-.1,'enable_truth_table':truth,'powered_high_output_leakage_guarantee_closed':True,'powered_high_dark_margin_ratio_25c':.0001/10e-6,'qualified_filter_datasheet_bounds_closed_conditionally':True,'fault_to_inhibit_20ms_proven':False,'qualified_filter_proven':False,'native_xml':xml_stats,'native_erc':erc_stats}
    return {'schema_version':1,'revision':model['revision'],'scope':'source connectivity/default-state screen; no hardware operation','errors':errors,'passed':not errors,'physical_components':len(physical),'device_counts':dict(counts),'calculations':calculations,'manufacturing_ready':False,'physical_qualification':False,'remaining_gates':model['open_gates']}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--directory',type=Path,default=OUT);a=ap.parse_args();path=a.directory
    result=validate(json.loads((path/'design.json').read_text(encoding='utf-8')),path/'netlist.xml',path/'erc.json')
    (path/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)


if __name__=='__main__':main()
