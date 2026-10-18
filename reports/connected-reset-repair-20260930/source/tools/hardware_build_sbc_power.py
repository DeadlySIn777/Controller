"""Create the standalone hardware-supervised SBC power branch; no board files."""
import csv
import json
from pathlib import Path
import uuid
from hardware_build_tx_schematic import effects, quote, symbol
from hardware_build_assembly import parse, dump

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/sbc_power'
NS=uuid.UUID('eb568241-cc55-4f15-954e-18d062f738bb')
def uid(value):return str(uuid.uuid5(NS,value))

def main():
    d=json.loads((OUT/'design-envelope.json').read_text())
    two=[(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')]
    rbody='(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width 0.254)(type default))(fill(type none)))'
    cbody='(polyline(pts(xy -2.54 .762)(xy 2.54 .762))(stroke(width .3)(type default))(fill(type none)))(polyline(pts(xy -2.54 -.762)(xy 2.54 -.762))(stroke(width .3)(type default))(fill(type none)))(polyline(pts(xy 0 2.54)(xy 0 .762))(stroke(width .254)(type default))(fill(type none)))(polyline(pts(xy 0 -.762)(xy 0 -2.54))(stroke(width .254)(type default))(fill(type none)))'
    switch=[]
    for n,name in d['switch_pin_map'].items():
        n=int(n);left=n<=6;row=n-1 if left else n-7
        typ='power_in' if n in(3,4,6,11) else 'power_out' if n==8 else 'passive' if n in(1,9,10) else 'open_collector' if n==7 else 'no_connect' if n==2 else 'input'
        switch.append((n,name,-20.32 if left else 20.32,25.4-row*10.16,0 if left else 180,typ))
    supervisor=[]
    for n,name in d['supervisor_pin_map'].items():
        n=int(n);left=n<=3;row=n-1 if left else n-4
        supervisor.append((n,name,-20.32 if left else 20.32,10.16-row*10.16,0 if left else 180,'power_in' if n in(2,4) else 'open_collector' if n==6 else 'passive' if n==5 else 'input'))
    body=lambda h:f'(rectangle(start -17.78 {h})(end 17.78 {-h})(stroke(width .254)(type default))(fill(type background)))'
    lib=[symbol('TPS22990DMLR',switch,body(30.48)),symbol('TPS389001DSET',supervisor,body(15.24)),symbol('R',two,rbody,'R'),symbol('C',two,cbody,'C')]
    conns={}
    for count in (2,3):
        ps=[(i,str(i),-5.08,-(i-1)*5.08,0,'passive') for i in range(1,count+1)];conns[count]=ps
        lib.append(symbol('Conn'+str(count),ps,f'(rectangle(start -2.54 2.54)(end 2.54 {-count*5.08})(stroke(width .254)(type default))(fill(type background)))','J'))
    lib.append(symbol('PWR_FLAG',[(1,'pwr',0,0,90,'power_out')],'','#FLG'))
    items=[];bom=[];pinmap={};rootid=uid('sbc-power')
    def place(name,ref,value,x,y,pins,nets,mpn=''):
        top=y-max(p[3] for p in pins)-10.16
        props=''.join(f'(property {quote(k)} {quote(v)}(at {x+5.08} {top+dy} 0){effects(.95,"hide" if hide else "")})' for k,v,dy,hide in [('Reference',ref,0,False),('Value',value,2.54,False),('Footprint','',0,True),('MPN',mpn,0,True)])
        items.append(f'(symbol(lib_id "CNC:{name}")(at {x} {y} 0)(unit 1)(in_bom {"no" if ref.startswith("#") else "yes"})(on_board {"no" if ref.startswith("#") else "yes"})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "sbc_power"(path "/{rootid}"(reference {quote(ref)})(unit 1)))))')
        pinmap[ref]={str(k):v for k,v in nets.items()}
        for n,_,px,py,_,_ in pins:
            sx,sy=round(x+px,4),round(y-py,4);net=nets.get(n)
            if net is None:items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(n)+"NC")}"))');continue
            dx=-25.4 if px<0 else 10.16 if px>0 else 0;dy=0 if px else-5.08 if py>=0 else 5.08
            ex,ey=round(sx+dx,4),round(sy+dy,4)
            items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"W")}"))')
            items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.95,"(justify left bottom)")}(uuid "{uid(ref+str(n)+"L")}"))')
        if not ref.startswith('#'):bom.append({'reference':ref,'value':value,'mpn':mpn,'footprint':'','status':'candidate; footprint and assembly qualification open'})
    place('TPS22990DMLR','U1','TPS22990DMLR',106.68,96.52,switch,{1:'SBC_SLEW_CT',2:None,3:'CORE_5V',4:'CORE_5V',5:'SBC_ENABLE',6:'LOGIC_GND',7:'SBC_SWITCH_PG',8:'SBC_5V',9:'SBC_5V',10:'SBC_5V',11:'CORE_5V'},d['switch_mpn'])
    place('TPS389001DSET','U2','TPS389001DSET',106.68,200.66,supervisor,{1:'SBC_SENSE',2:'LOGIC_GND',3:'SBC_RESET_N',4:'CORE_5V',5:'SBC_DELAY_CT',6:'SBC_ENABLE'},d['supervisor_mpn'])
    for i,(ref,p) in enumerate(d['parts'].items()):
        place(ref[0],ref,p['value'],round(269.24+(i%4)*81.28,4),round(71.12+(i//4)*66.04,4),two,dict(enumerate(p['nets'],1)))
    for i,(ref,nets) in enumerate(d['boundary'].items()):
        place('Conn'+str(len(nets)),ref,ref[1:-1]+' BOUNDARY',round(76.2+i*137.16,4),279.4,conns[len(nets)],dict(enumerate(nets,1)))
    for i,net in enumerate(('CORE_5V','LOGIC_GND')):place('PWR_FLAG','#FLG'+str(i),'NORMAL SOURCE',50.8+i*76.2,350.52,[(1,'pwr',0,0,90,'power_out')],{1:net})
    def note(y,txt,size=1.2):items.append(f'(text {quote(txt)}(at 20.32 {y} 0){effects(size,"(justify left top)")}(uuid "{uid(txt)}"))')
    note(15.24,'HARDWARE-SUPERVISED SBC POWER - 3 A BRANCH CANDIDATE',2)
    note(27.94,'CORE_5V charges first. Supervisor release and controlled switch slew start SBC_5V without host software.\nU1 pad11 is VIN, never GND. U2 has six terminals and no exposed thermal pad. All footprints remain unassigned.')
    note(322.58,'JMR1 accepts an optional normally-open dry contact to ground. No external power or active-high driver.\nJSTATUS1 is a 5 V-domain diagnostic boundary, not direct 3.3 V GPIO. Switch PG means enhanced FET, not valid output voltage.')
    note(375.92,'No branch current limiting, reverse blocking or arbitrary-brownout hold-up is supplied by this block.\nCTSW1 requires >=470 nF effective; CTSUP1 >=1.2 uF effective. Values and timing require qualified parts/tests.\nSBC total charge capacitance <=1 mF; host current <=3 A. No alternative USB/SBC power source until backfeed is reviewed.\nNo machine permission follows from power return. Circuit ERC is not PCB or physical qualification.')
    sch=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{rootid}")(paper "A2")(title_block(title "Sequenced SBC supply")(date "2026-09-28")(rev "r0.1"))(lib_symbols'+''.join(lib)+')'+''.join(items)+')'
    (OUT/'sbc_power.kicad_sch').write_text(dump(parse(sch))+'\n')
    libs=''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in lib)
    (OUT/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+libs+')'))+'\n')
    (OUT/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "SBC power candidate symbols")))'))+'\n')
    (OUT/'sbc_power.kicad_pro').write_text('{"meta":{"filename":"sbc_power.kicad_pro","version":1}}\n')
    (OUT/'pin-map.json').write_text(json.dumps(pinmap,indent=2)+'\n')
    with (OUT/'bom.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(bom[0]));w.writeheader();w.writerows(bom)
    print(OUT/'sbc_power.kicad_sch')

if __name__=='__main__':main()
