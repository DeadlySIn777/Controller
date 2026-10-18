"""Build the bounded MC motor/TX Ioff circuitry, not a complete motion card.

Internal B1-B4 symbols are non-orderable logical boundaries. Source termination
is an engineering candidate; loaded edges and receiver defaults require tests.
"""
import csv
import hashlib
import json
from pathlib import Path
import uuid

from hardware_build_assembly import parse, dump
from hardware_build_tx_schematic import effects, quote, symbol

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/mc_motor_buffers'
NS = uuid.UUID('eb95e3fd-e053-44da-bf8c-4c82a4a2b9ea')
PIN_FUNCTIONS = {
    'LVC244A': {1:('1OE_N','input'),2:('1A1','input'),3:('2Y4','tri_state'),
        4:('1A2','input'),5:('2Y3','tri_state'),6:('1A3','input'),7:('2Y2','tri_state'),
        8:('1A4','input'),9:('2Y1','tri_state'),10:('GND','power_in'),11:('2A1','input'),
        12:('1Y4','tri_state'),13:('2A2','input'),14:('1Y3','tri_state'),15:('2A3','input'),
        16:('1Y2','tri_state'),17:('2A4','input'),18:('1Y1','tri_state'),
        19:('2OE_N','input'),20:('VCC','power_in')},
    'LVC2G126': {1:('1OE','input'),2:('1A','input'),3:('2Y','tri_state'),
        4:('GND','power_in'),5:('2A','input'),6:('1Y','tri_state'),7:('2OE','input'),8:('VCC','power_in')},
}
MPNS = {'LVC244A': ('SN74LVC244APWR','Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm'),
        'LVC2G126': ('SN74LVC2G126DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm')}


def description():
    components = {}
    paths = []
    for i in range(12):
        peer = 'MIA' if i < 8 else 'MX4'
        for signal in ('STEP','DIR','EN_N'):
            base = f'EN{i}_N' if signal == 'EN_N' else f'{signal}{i}'
            paths.append({'input':base+'_FPGA','raw':base+'_BUFFER_OUT',
                          'output':base+'_TO_'+peer,'bank':'A' if i<8 else 'B',
                          'signal':signal,'channel':i,'receiver':peer})
    for bank,peer in [('A','MIA'),('B','MX4')]:
        paths.append({'input':'TX_PERMIT','raw':'TX_PERMIT_'+bank+'_BUFFER_OUT',
                      'output':'TX_PERMIT_'+bank+'_TO_'+peer,'bank':bank,
                      'signal':'TX_PERMIT','channel':None,'receiver':peer})
    for bank,count,kind in [('A',4,'LVC244A'),('B',7,'LVC2G126')]:
        bank_paths = [p for p in paths if p['bank']==bank]
        channels = [(2,18),(4,16),(6,14),(8,12),(11,9),(13,7),(15,5),(17,3)] if bank=='A' else [(2,6),(5,3)]
        for index in range(count):
            ref = 'U'+str(index+1 if bank=='A' else index+5)
            pins = {10:'LOGIC_GND',20:'IO_3V3',1:'LOGIC_GND',19:'LOGIC_GND'} if bank=='A' else {4:'LOGIC_GND',8:'IO_3V3'}
            for k,(a,y) in enumerate(channels):
                path_index = index*len(channels)+k
                used = path_index < len(bank_paths)
                if used:
                    path=bank_paths[path_index]; pins[a]=path['input'];pins[y]=path['raw']
                    path.update({'buffer_ref':ref,'input_pin':str(a),'output_pin':str(y)})
                else:pins[a]='LOGIC_GND';pins[y]=None
                if bank=='B':pins[1 if k==0 else 7]='BANK_B_BUFFER_ENABLE_QUALIFIED' if used else 'LOGIC_GND'
            mpn,footprint=MPNS[kind]
            components[ref]={'kind':kind,'mpn':mpn,'value':mpn,'footprint':footprint,
                'pins':{str(k):v for k,v in pins.items()},'physical':True,
                'role':'bankA always-active Ioff' if bank=='A' else 'bankB physical positive-OE Ioff'}
    def resistor(ref,net,other,ohms,role):
        mpn={33:'CRCW060333R0FKEA',4700:'CRCW06034K70FKEA',10000:'CRCW060310K0FKEA'}[ohms]
        components[ref]={'kind':'R','mpn':mpn,'value':str(ohms)+'R 1%',
            'resistance_ohm':ohms,'tolerance':0.01,'footprint':'Resistor_SMD:R_0603_1608Metric',
            'pins':{'1':net,'2':other},'physical':True,'role':role}
    n=0
    for path in paths:
        n+=1;resistor('R'+str(n),path['raw'],path['output'],33,'source series candidate; SI not qualified')
        path['series_ref']='R'+str(n)
    input_defaults = [(f'{s}{i}_FPGA','LOGIC_GND') for i in range(12) for s in ('STEP','DIR')]
    input_defaults += [(f'EN{i}_N_FPGA','IO_3V3') for i in range(12)]
    input_defaults += [('TX_PERMIT','LOGIC_GND'),('BANK_B_BUFFER_ENABLE_QUALIFIED','LOGIC_GND')]
    for net,other in input_defaults:
        n+=1;resistor('R'+str(n),net,other,4700,'FPGA/qualified-gate defined idle; overrides weak pull')
    for path in paths:
        if path['signal']=='EN_N':continue
        n+=1;resistor('R'+str(n),path['output'],'LOGIC_GND',10000,'outgoing STEP/DIR/TX idle-low')
    for i in range(1,12):
        components['C'+str(i)]={'kind':'C','value':'100nF X7R 25V 10%','mpn':'GRM188R71E104KA01D',
            'footprint':'Capacitor_SMD:C_0603_1608Metric','pins':{'1':'IO_3V3','2':'LOGIC_GND'},
            'physical':True,'role':'U'+str(i)+' local decoupling'}
    inputs=['IO_3V3','LOGIC_GND']+list(dict.fromkeys(p['input'] for p in paths))+['BANK_B_BUFFER_ENABLE_QUALIFIED']
    outputs=[p['output'] for p in paths]
    boundaries={
        'B1':['IO_3V3','LOGIC_GND']+[p['input'] for p in paths if p['bank']=='A'],
        'B2':[p['input'] for p in paths if p['bank']=='B' and p['input']!='TX_PERMIT']+['BANK_B_BUFFER_ENABLE_QUALIFIED'],
        'B3':[p['output'] for p in paths if p['bank']=='A'],
        'B4':[p['output'] for p in paths if p['bank']=='B'],
    }
    for ref,nets in boundaries.items():
        components[ref]={'kind':ref,'mpn':'','value':'INTERNAL LOGICAL BOUNDARY','footprint':'',
            'pins':{str(i):net for i,net in enumerate(nets,1)},'physical':False,'role':'review boundary, not connector'}
    names=['sn74lvc244a','sn74lvc2g126','sn74lvc07a','am26c31']
    sources={f'research/mc-motor-buffers/{name}{suffix}':hashlib.sha256((ROOT/'research/mc-motor-buffers'/f'{name}{suffix}').read_bytes()).hexdigest()
             for name in names for suffix in ('.pdf','.txt')}
    sources.update({f'research/mc-motor-buffers/{name}-pin-source.txt':hashlib.sha256((ROOT/'research/mc-motor-buffers'/f'{name}-pin-source.txt').read_bytes()).hexdigest()
                    for name in names[:2]})
    sources['research/fpga-core/trion20-ds-v6.0.pdf']=hashlib.sha256((ROOT/'research/fpga-core/trion20-ds-v6.0.pdf').read_bytes()).hexdigest()
    return {'schema_version':1,'revision':'mc-motor-buffers-r0.1','manufacturing_ready':False,
        'scope':'38 motor/TX paths only; not full MC isolation, qualification, receiver circuits or backplane mapping',
        'interface_revision':'IS-1 motor/Ioff requirements; proposedIS-2 strong startup pulls and source-series implementation',
        'operating_supply_v':[3.14,3.465],'logic_interface_nominal_v':3.3,'components':components,
        'boundary_inputs':inputs,'boundary_outputs':outputs,'paths':paths,'sources':sources,
        'boe_contract':{'physical_net':'BANK_B_BUFFER_ENABLE_QUALIFIED','used_buffer_OE_pins':13,
            'same_net_required_for_OPI_BOE_CLR_N':True,'upstream_qualification_drawn_here':False,'OPI_latch_drawn_here':False},
        'receiver_contract':{'STEP_DIR':{'pull_ohm':10000,'to':'LOGIC_GND','receiver':'AM26C31IPWR'},
            'EN_N':{'pull_ohm':10000,'to':'receiver_own_powered_3V3','receiver':'SN74LVC07APWR',
                'pull_fitted_on_MC_output':False},'TX_PERMIT':{'pull_ohm':10000,'to':'LOGIC_GND',
                'receiver':'card-qualified Schmitt gate; exact aggregate fanout unqualified'},
            'receiving_circuits_drawn_here':False,'high_Z_EN_disabled_only_if_receiver_contract_satisfied':True},
        'open_gates':['No complete MC or connector contact/net map.',
            'DIC/OPI/MIA/MX4 qualification, receiver pull-ups/drive enable and differential drivers remain separate.',
            '33ohm source-series values need routing, IBIS and loaded-edge qualification.',
            'Static divider/leakage screening is not dynamic power sequencing, TTL transition or thermal qualification.',
            '4.7k startup defaults and extra physical buffering loads need integrated power/BOM review.',
            'The same qualifiedOE copper net must clear OPI_BOE in parent integration; the latch is not in this block.',
            'All other card-bound MC outputs need separate Ioff completion.']}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    d=description();uid=lambda key:str(uuid.uuid5(NS,key)); root_id=uid('root')
    functions=dict(PIN_FUNCTIONS)
    functions.update({'R':{1:('','passive'),2:('','passive')},'C':{1:('','passive'),2:('','passive')},'PWR_FLAG':{1:('pwr','power_out')}})
    for ref in ('B1','B2','B3','B4'):functions[ref]={int(k):(k,'passive') for k in d['components'][ref]['pins']}
    lib=[];pin_layout={}
    for kind,table in functions.items():
        if kind in ('R','C'):
            pp=[(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')]
            body='(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))' if kind=='R' else '(polyline(pts(xy -2.54 .762)(xy 2.54 .762))(stroke(width .3)(type default))(fill(type none)))(polyline(pts(xy -2.54 -.762)(xy 2.54 -.762))(stroke(width .3)(type default))(fill(type none)))'
        elif kind=='PWR_FLAG':pp=[(1,'pwr',0,0,90,'power_out')];body=''
        else:
            pp=[]
            for side,numbers in [(-1,[k for k,(_,t) in table.items() if t!='tri_state']), (1,[k for k,(_,t) in table.items() if t=='tri_state'])]:
                for i,k in enumerate(numbers):
                    name,typ=table[k];pp.append((k,name,side*20.32,20.32-i*(5.08 if kind.startswith('B') else 7.62),0 if side<0 else 180,typ))
            lower=min(p[3] for p in pp)-5.08
            body=f'(rectangle(start -17.78 25.4)(end 17.78 {lower})(stroke(width .254)(type default))(fill(type background)))'
        pin_layout[kind]=pp
        lib.append(symbol(kind,pp,body,'R' if kind=='R' else 'C' if kind=='C' else 'B' if kind.startswith('B') else '#FLG' if kind=='PWR_FLAG' else 'U'))
    items=[];bom=[];netmap={}
    def place(ref,c,x,y):
        kind=c['kind'];pp=pin_layout[kind];physical=c.get('physical',False);upper=max(v[3] for v in pp);hidden=kind=='PWR_FLAG'
        property_x=x+2.54 if kind in ('R','C') else x
        property_y=y-2.54 if kind in ('R','C') else y-upper-12.7
        property_justify='(justify left)' if kind in ('R','C') else ''
        props=''.join(f'(property {quote(k)} {quote(v)}(at {property_x} {property_y+dy} 0){effects(1,"hide") if hide or hidden else effects(1,property_justify)})'
            for k,v,dy,hide in [('Reference',ref,0,False),('Value',c['value'],2.54,False),('MPN',c.get('mpn',''),0,True),('Footprint',c.get('footprint',''),0,True)])
        items.append(f'(symbol(lib_id "CNC:{kind}")(at {x} {y} 0)(unit 1)(in_bom {"yes" if physical else "no"})(on_board {"yes" if physical else "no"})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "mc_motor_buffers"(path "/{root_id}"(reference {quote(ref)})(unit 1)))))')
        for number,_,px,py,_,_ in pp:
            sx,sy=round(x+px,4),round(y-py,4);net=c['pins'].get(str(number))
            if net is None:items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(number)+"NC")}"))');continue
            dx=-12.7 if px<0 else 12.7 if px>0 else 0;dy=0 if px else -5.08 if py>=0 else 5.08
            ex,ey=round(sx+dx,4),round(sy+dy,4)
            items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(number)+"W")}"))')
            justify='(justify right bottom)' if px<0 else '(justify left bottom)'
            items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.9,justify)}(uuid "{uid(ref+str(number)+"L")}"))')
            if not ref.startswith('#'):netmap.setdefault(net,[]).append([ref,str(number)])
        if not ref.startswith('#'):bom.append({'Reference':ref,'Value':c['value'],'MPN':c['mpn'],'Footprint':c['footprint'],'Status':'candidate_not_qualified','Scope':'physical_component_candidate' if physical else 'logical_boundary_not_orderable'})
    for i in range(1,5):place('U'+str(i),d['components']['U'+str(i)],91.44+(i-1)*213.36,78.74)
    for i in range(5,12):place('U'+str(i),d['components']['U'+str(i)],76.2+(i-5)*147.32,246.38)
    for i,(ref,c) in enumerate((r,c) for r,c in d['components'].items() if r[0] in 'RC'):
        place(ref,c,55.88+(i%12)*91.44,340.36+(i//12)*27.94)
    for ref,x in [('B1',101.6),('B2',355.6),('B3',609.6),('B4',914.4)]:place(ref,d['components'][ref],x,665.48)
    for i,net in enumerate(('IO_3V3','LOGIC_GND')):place('#FLG'+str(i),{'kind':'PWR_FLAG','value':'CONDITIONAL RAIL BOUNDARY','pins':{'1':net}},1005.84+i*76.2,772.16)
    notes=[(20.32,17.78,'MC MOTOR / TX Ioff: 8 STANDARD +4 EXPANSION; B1-B4 ARE LOGICAL BOUNDARIES, NOT CONNECTORS',1.8),
        (20.32,812.8,'BankA244A OEs tiedLOW(active). BankB2G126 used OEs share BANK_B_BUFFER_ENABLE_QUALIFIED with parentOPI_BOE clear.\nEN_N outgoing pull-ups belong on poweredMIA/MX4 receiver rails; NEVER on deadMC rail. 33R series are unqualified SI candidates.\nNot completeMC; no routing, targetfit, loadedtiming or manufacture claim.',1.2)]
    for x,y,n,size in notes:items.append(f'(text {quote(n)}(at {x} {y} 0){effects(size,"(justify left top)")}(uuid "{uid(n)}"))')
    raw=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{root_id}")(paper "A0")(title_block(title "Motion-card motor Ioff boundaries")(date "2026-09-30")(rev "r0.1"))(lib_symbols'+''.join(lib)+')'+''.join(items)+')'
    (OUT/'mc_motor_buffers.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf-8')
    library=''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in lib)
    (OUT/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+library+')'))+'\n',encoding='utf-8')
    (OUT/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "MC motor buffers")))'))+'\n',encoding='utf-8')
    (OUT/'mc_motor_buffers.kicad_pro').write_text('{"meta":{"filename":"mc_motor_buffers.kicad_pro","version":1}}\n',encoding='utf-8')
    (OUT/'design.json').write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
    (OUT/'pin-map.json').write_text(json.dumps(netmap,indent=2)+'\n',encoding='utf-8')
    with (OUT/'bom.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(bom[0]));writer.writeheader();writer.writerows(bom)
    print(json.dumps({'physical_parts':sum(c['physical'] for c in d['components'].values()),'motor_paths':36,'TX_paths':2,'manufacturing_ready':False}))


if __name__=='__main__':main()
