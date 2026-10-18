"""Build the MC hardware permission/latch core from independently sourced pins.

Qualified presence/tamper/filter terms are explicit input boundaries. This does
not invent their upstream circuits, select backplane contacts or qualify timing.
"""
import csv
import hashlib
import json
from pathlib import Path
import uuid

from hardware_build_assembly import parse, dump
from hardware_build_tx_schematic import effects, quote, symbol

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/mc_permission'
NS = uuid.UUID('34366812-426a-407c-8b2f-c4a840316518')

PIN_FUNCTIONS = {
    'LVC1G11': {1: ('A','input'), 2: ('GND','power_in'), 3: ('B','input'),
                4: ('Y','output'), 5: ('VCC','power_in'), 6: ('C','input')},
    'LVC2G08': {1: ('1A','input'), 2: ('1B','input'), 3: ('2Y','output'),
                4: ('GND','power_in'), 5: ('2A','input'), 6: ('2B','input'),
                7: ('1Y','output'), 8: ('VCC','power_in')},
    'LVC2G74': {1: ('CLK','input'), 2: ('D','input'), 3: ('Q_N','output'),
                4: ('GND','power_in'), 5: ('Q','output'), 6: ('CLR_N','input'),
                7: ('PRE_N','input'), 8: ('VCC','power_in')},
    'LVC2G04': {1: ('1A','input'), 2: ('GND','power_in'), 3: ('2A','input'),
                4: ('2Y','output'), 5: ('VCC','power_in'), 6: ('1Y','output')},
    'LVC2G32': {1: ('1A','input'), 2: ('1B','input'), 3: ('2Y','output'),
                4: ('GND','power_in'), 5: ('2A','input'), 6: ('2B','input'),
                7: ('1Y','output'), 8: ('VCC','power_in')},
}
MPNS = {'LVC1G11': ('SN74LVC1G11DBVR','Package_TO_SOT_SMD:SOT-23-6'),
        'LVC2G08': ('SN74LVC2G08DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm'),
        'LVC2G74': ('SN74LVC2G74DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm'),
        'LVC2G04': ('SN74LVC2G04DBVR','Package_TO_SOT_SMD:SOT-23-6'),
        'LVC2G32': ('SN74LVC2G32DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm')}


def description():
    parts = {}
    def ic(ref, kind, pins, role):
        power = {2:'LOGIC_GND',5:'IO_3V3'} if kind in ('LVC1G11','LVC2G04') else {4:'LOGIC_GND',8:'IO_3V3'}
        pins = {**power, **pins}
        mpn, fp = MPNS[kind]
        parts[ref] = {'kind':kind,'mpn':mpn,'value':mpn,'footprint':fp,
                      'pins':{str(k):v for k,v in pins.items()},'role':role,'physical':True}
    def and3(ref, a, b, c, y, role):
        ic(ref,'LVC1G11',{1:a,3:b,6:c,4:y},role)
    def and2x(ref, a,b,y,c,d,z,role):
        ic(ref,'LVC2G08',{1:a,2:b,7:y,5:c,6:d,3:z},role)
    def latch(ref, clk, clear, q, role):
        ic(ref,'LVC2G74',{1:clk,2:'IO_3V3',3:None,5:q,6:clear,7:'IO_3V3'},role)
    and3('U1','MC_RAILS_OK','CDONE_QUALIFIED','DIC_OK_QUALIFIED','BASE_FIRST','base qualification, first stage')
    and3('U2','BASE_FIRST','EXT_PERMIT_3V3','TAMPER_CLEAR_N','BASE_OK','base qualification, second stage')
    and2x('U3','BASE_OK','WD_M_OK','RAW_INHIBIT_N','RAW_INHIBIT_N','FPGA_ENDPOINT_READY','LATCH_CLEAR_M_N','motion raw inhibit and asynchronous clear')
    and3('U4','BASE_OK','WD_O_OK','FPGA_ENDPOINT_READY','LATCH_CLEAR_O_N','output asynchronous clear')
    latch('U5','FPGA_MOTION_REQUEST','LATCH_CLEAR_M_N','ARM_M_Q','motion rising-request arm latch')
    latch('U6','FPGA_OUTPUT_REQUEST','LATCH_CLEAR_O_N','ARM_O_Q','output rising-request arm latch')
    and3('U7','ARM_M_Q','FPGA_MOTION_REQUEST','RAW_INHIBIT_N','TX_PERMIT','final motion permission')
    and3('U8','ARM_O_Q','FPGA_OUTPUT_REQUEST','OUTPUT_RAW_OK','OUT_PERMIT','final output permission')
    and2x('U9','BASE_OK','WD_O_OK','OUTPUT_RAW_OK','TX_PERMIT','PERMIT_OUT_REQ','PERMIT_OUT_DRIVE','output watchdog and safety-output request gate')
    and3('U10','TX_PERMIT','OUT_PERMIT','PROCESS_PERMIT_EXT_3V3','PROC_PERMIT','independent process permission')
    latch('U11','OPI_REARM_TX','TX_PERMIT','OPI_OK_TX','sticky accepted motion-output interruption')
    latch('U12','OPI_REARM_OUT','OUT_PERMIT','OPI_OK_OUT','sticky accepted general-output interruption')
    latch('U13','OPI_REARM_BOE','BANK_B_BUFFER_ENABLE_QUALIFIED','OPI_OK_BOE','sticky qualified bank-B buffer interruption')
    # Exact event semantics: only a WD_OK falling edge samples actual SET1.
    # Q feedback through the OR preserves a captured trip until explicit clear.
    # Request rising while WD_OK is already LOW is not a clock event.
    for index,domain in enumerate(('M','O'),14):
        ic('U'+str(index),'LVC2G74',
           {1:f'WD_{domain}_FALL_CLK',2:f'WD_{domain}_TRIP_D',3:f'WD_{domain}_TRIP_N',
            5:f'WD_{domain}_TRIP_Q',6:f'WD_{domain}_TRIP_CLEAR_N',7:'IO_3V3'},
           f'{domain} sticky actual-SET1-qualified watchdog falling-edge trip')
    ic('U16','LVC2G04',{1:'WD_M_OK',6:'WD_M_FALL_CLK',3:'WD_O_OK',4:'WD_O_FALL_CLK'},
       'invert watchdog health for falling-edge capture')
    ic('U17','LVC2G32',{1:'WD_M_TRIP_Q',2:'WD_M_SET1_BUF',7:'WD_M_TRIP_D',
                       5:'WD_O_TRIP_Q',6:'WD_O_SET1_BUF',3:'WD_O_TRIP_D'},
       'sticky trip feedback OR actual timer SET1')
    ic('U18','LVC2G04',{1:'WD_REARM_M',6:'WD_M_RECORD_CLEAR_N',3:'WD_REARM_O',4:'WD_O_RECORD_CLEAR_N'},
       'invert deliberate active-HIGH trip-record clear strobes')
    and2x('U19','MC_RAILS_OK','WD_M_RECORD_CLEAR_N','WD_M_TRIP_CLEAR_N',
           'MC_RAILS_OK','WD_O_RECORD_CLEAR_N','WD_O_TRIP_CLEAR_N',
           'power-reset and explicit trip-record asynchronous clear')
    for i in range(1,20):
        parts['C'+str(i)] = {'kind':'C','mpn':'GRM188R71E104KA01D','value':'100nF X7R 25V 10%',
                            'footprint':'Capacitor_SMD:C_0603_1608Metric',
                            'pins':{'1':'IO_3V3','2':'LOGIC_GND'},'role':'U'+str(i)+' local decoupling','physical':True}
    # Request/progress pulls live in the separate conditioned watchdog circuit;
    # do not duplicate them here. These GPIO strobes need defined startup LOW.
    pulls = [(net,4700) for net in ('FPGA_ENDPOINT_READY','OPI_REARM_TX','OPI_REARM_OUT',
                                  'OPI_REARM_BOE','WD_REARM_M','WD_REARM_O','PERMIT_OUT_REQ')]
    pulls += [(net,10000) for net in ('MC_RAILS_OK','CDONE_QUALIFIED','DIC_OK_QUALIFIED',
                                    'EXT_PERMIT_3V3','TAMPER_CLEAR_N','PROCESS_PERMIT_EXT_3V3',
                                    'BANK_B_BUFFER_ENABLE_QUALIFIED','TX_PERMIT','OUT_PERMIT',
                                    'PROC_PERMIT','PERMIT_OUT_DRIVE')]
    for i,(net,ohms) in enumerate(pulls,1):
        parts['R'+str(i)] = {'kind':'R','mpn':'CRCW06034K70FKEA' if ohms==4700 else 'CRCW060310K0FKEA',
                             'value':f'{ohms}R 1%','resistance_ohm':ohms,
                             'footprint':'Resistor_SMD:R_0603_1608Metric',
                             'pins':{'1':net,'2':'LOGIC_GND'},'role':'defined-low boundary/output', 'physical':True}
    inputs = ['IO_3V3','LOGIC_GND','MC_RAILS_OK','CDONE_QUALIFIED','DIC_OK_QUALIFIED',
              'EXT_PERMIT_3V3','TAMPER_CLEAR_N','WD_M_OK','WD_O_OK','FPGA_ENDPOINT_READY',
              'FPGA_MOTION_REQUEST','FPGA_OUTPUT_REQUEST','PROCESS_PERMIT_EXT_3V3',
              'PERMIT_OUT_REQ','BANK_B_BUFFER_ENABLE_QUALIFIED','OPI_REARM_TX','OPI_REARM_OUT',
              'OPI_REARM_BOE','WD_REARM_M','WD_REARM_O','WD_M_SET1_BUF','WD_O_SET1_BUF']
    outputs = ['RAW_INHIBIT_N','TX_PERMIT','OUT_PERMIT','PROC_PERMIT','PERMIT_OUT_DRIVE',
               'OPI_OK_TX','OPI_OK_OUT','OPI_OK_BOE','WD_M_TRIP_N','WD_O_TRIP_N']
    for ref,nets in [('B1',inputs),('B2',outputs)]:
        parts[ref]={'kind':ref,'value':'INTERNAL REVIEW BOUNDARY','mpn':'','footprint':'',
                    'pins':{str(i):n for i,n in enumerate(nets,1)},'physical':False,
                    'role':'logical input boundary' if ref=='B1' else 'logical output boundary'}
    return {'schema_version':1,'revision':'mc-permission-r0.2','manufacturing_ready':False,
            'scope':'Physical gate/latch implementation of IS-1 section 6.2 equations; upstream qualification and card output drivers remain separate.',
            'interface_revision':'IS-1 logic with proposed IS-2 GPIO startup-pull conditioning',
            'components':parts,'boundary_inputs':inputs,'boundary_outputs':outputs,
            'operating_supply_v':[3.14,3.465],
            'sources':{f'research/machine-permission/{name}{suffix}':hashlib.sha256((ROOT/'research/machine-permission'/f'{name}{suffix}').read_bytes()).hexdigest()
                       for name in ('sn74lvc1g11','sn74lvc2g08','sn74lvc2g74','sn74lvc2g04','sn74lvc2g32')
                       for suffix in ('.pdf','-permission-pin-source.txt')},
            'watchdog_trip_contract':{'event':'falling_WD_OK_edge_samples_actual_SET1',
                'sticky_feedback':True,'physical_SET1_inputs':['WD_M_SET1_BUF','WD_O_SET1_BUF'],
                'record_clear_strobes_active_high':['WD_REARM_M','WD_REARM_O'],
                'clear_only_after_record_stored_and_while_disarmed':'implementation_requirement_not_verified',
                'power_clear_input':'MC_RAILS_OK','loaded_edge_and_reset_timing_qualified':False},
            'open_gates':['Qualified DIC presence/PGOOD filtering, CDONE qualification and positive tamper-clear generation remain upstream boundaries.',
                          'Bank-B qualified buffer-enable term is an input; actual Ioff buffer gating remains unimplemented.',
                          'PERMIT_OUT_DRIVE is logic only; no photorelay or field contact is implemented in this block.',
                          'Physical reset/clock recovery and removal pulses, full runtime/self-test integration and loaded timing require qualification.',
                          'Trip capture requires actual SET1 setup/hold at inverted WD_OK rising edges; coincident edges remain unqualified.',
                          'WD_REARM_M/O are explicit record-clear strobes; logic owner must issue them only after storage while disarmed, not as healthy-state rearm levels.',
                          'Proposed 4.7k GPIO pulls require versioned interface reconciliation, not an in-place IS-1 edit.']}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    d=description(); uid=lambda key:str(uuid.uuid5(NS,key)); root=uid('root')
    definitions=dict(PIN_FUNCTIONS)
    definitions.update({'R':{1:('','passive'),2:('','passive')},'C':{1:('','passive'),2:('','passive')}})
    for ref in ('B1','B2'):
        definitions[ref]={int(k):(k,'passive') for k in d['components'][ref]['pins']}
    definitions['PWR_FLAG']={1:('pwr','power_out')}
    pins={}; libs=[]
    for kind, functions in definitions.items():
        if kind in ('R','C'):
            p=[(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')]
            body='(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))' if kind=='R' else '(polyline(pts(xy -2.54 .762)(xy 2.54 .762))(stroke(width .3)(type default))(fill(type none)))(polyline(pts(xy -2.54 -.762)(xy 2.54 -.762))(stroke(width .3)(type default))(fill(type none)))'
        elif kind=='PWR_FLAG':
            p=[(1,'pwr',0,0,90,'power_out')];body=''
        else:
            left=[n for n,(_,t) in functions.items() if t!='output'];right=[n for n,(_,t) in functions.items() if t=='output']
            p=[]
            for side,numbers in ((-1,left),(1,right)):
                for i,n in enumerate(numbers):
                    name,typ=functions[n];p.append((n,name,side*20.32,20.32-i*(5.08 if kind.startswith('B') else 7.62),0 if side<0 else 180,typ))
            lower=min(v[3] for v in p)-5.08
            body=f'(rectangle(start -17.78 25.4)(end 17.78 {lower})(stroke(width .254)(type default))(fill(type background)))'
        pins[kind]=p
        libs.append(symbol(kind,p,body,'R' if kind=='R' else 'C' if kind=='C' else 'B' if kind.startswith('B') else '#FLG' if kind=='PWR_FLAG' else 'U'))
    items=[]; bom=[]; netmap={}
    def place(ref,component,x,y):
        kind=component['kind']; p=pins[kind]; physical=component.get('physical',False)
        upper=max(v[3] for v in p); hidden=kind=='PWR_FLAG'
        style=effects(1, 'hide' if hidden else '')
        props=''.join(f'(property {quote(k)} {quote(v)}(at {x} {y-upper-7.62+dy} 0){effects(1,"hide") if hide else style})'
                      for k,v,dy,hide in [('Reference',ref,0,False),('Value',component['value'],2.54,False),('MPN',component.get('mpn',''),0,True),('Footprint',component.get('footprint',''),0,True)])
        items.append(f'(symbol(lib_id "CNC:{kind}")(at {x} {y} 0)(unit 1)(in_bom {"yes" if physical else "no"})(on_board {"yes" if physical else "no"})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "mc_permission"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
        for n,_,px,py,_,_ in p:
            sx,sy=round(x+px,4),round(y-py,4); net=component['pins'].get(str(n))
            if net is None:
                items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(n)+"NC")}"))');continue
            dx=-12.7 if px<0 else 12.7 if px>0 else 0;dy=0 if px else -5.08 if py>=0 else 5.08
            ex,ey=round(sx+dx,4),round(sy+dy,4)
            if dx or dy:items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"W")}"))')
            items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.95,"(justify left bottom)")}(uuid "{uid(ref+str(n)+"L")}"))')
            if not ref.startswith('#'):netmap.setdefault(net,[]).append([ref,str(n)])
        if not ref.startswith('#'):
            bom.append({'Reference':ref,'Value':component['value'],'MPN':component['mpn'],
                        'Footprint':component['footprint'],'Status':'candidate_not_qualified',
                        'Scope':'physical_component_candidate' if physical else 'schematic_boundary_not_orderable'})
    for i,(ref,c) in enumerate((r,c) for r,c in d['components'].items() if r.startswith('U')):
        place(ref,c,76.2+(i%5)*147.32,76.2+(i//5)*116.84)
    for i,(ref,c) in enumerate((r,c) for r,c in d['components'].items() if r[0] in 'RC'):
        place(ref,c,55.88+(i%10)*73.66,541.02+(i//10)*35.56)
    place('B1',d['components']['B1'],76.2,718.82)
    place('B2',d['components']['B2'],406.4,718.82)
    for i,net in enumerate(('IO_3V3','LOGIC_GND')):
        place('#FLG'+str(i),{'kind':'PWR_FLAG','value':'CONDITIONAL SOURCE','pins':{'1':net}},944.88+i*76.2,640.08)
    note='MC PERMISSION / STICKY INTERRUPTION CORE - UPSTREAM QUALIFICATION AND FIELD DRIVERS REMAIN SEPARATE'
    items.append(f'(text {quote(note)}(at 20.32 15.24 0){effects(1.8,"(justify left top)")}(uuid "{uid(note)}"))')
    note='No manufacture/physical timing claim. IS-1 arm/OPI equations; 4.7k GPIO startup pulls need proposed IS-2 reconciliation.\nWD_TRIP_N: a WD_OK FALL captures actual timer SET1; sticky Q feedback, power reset or explicit WD_REARM pulse clears the record.\nB1/B2 are logical boundaries, not connectors. Trip clear protocol, loaded edge timing and upstream qualified terms remain open.'
    items.append(f'(text {quote(note)}(at 20.32 820.42 0){effects(1.2,"(justify left top)")}(uuid "{uid(note)}"))')
    raw=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{root}")(paper "A0")(title_block(title "Motion-card permission core")(date "2026-09-30")(rev "r0.2"))(lib_symbols'+''.join(libs)+')'+''.join(items)+')'
    (OUT/'mc_permission.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf-8')
    library=''.join(s.replace('(symbol "CNC:', '(symbol "',1) for s in libs)
    (OUT/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+library+')'))+'\n',encoding='utf-8')
    table='(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "MC permission core")))'
    (OUT/'sym-lib-table').write_text(dump(parse(table))+'\n',encoding='utf-8')
    (OUT/'mc_permission.kicad_pro').write_text('{"meta":{"filename":"mc_permission.kicad_pro","version":1}}\n',encoding='utf-8')
    (OUT/'design.json').write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
    (OUT/'pin-map.json').write_text(json.dumps(netmap,indent=2)+'\n',encoding='utf-8')
    with (OUT/'bom.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(bom[0]));writer.writeheader();writer.writerows(bom)
    print(json.dumps({'physical_parts':sum(c['physical'] for c in d['components'].values()),
                      'native_schematic':str(OUT/'mc_permission.kicad_sch'),'manufacturing_ready':False}))


if __name__=='__main__':main()
