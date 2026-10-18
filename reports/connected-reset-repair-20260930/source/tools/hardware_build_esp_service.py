"""Build an editable ESP service schematic; no PCB or device operations."""
import csv
import json
from pathlib import Path
import uuid
from hardware_build_tx_schematic import effects, quote, symbol
from hardware_build_assembly import parse, dump

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/esp_service'
NS=uuid.UUID('f234c665-dc8e-40a5-b659-bd9e0794db81')
def uid(x):return str(uuid.uuid5(NS,x))

def main():
    d=json.loads((OUT/'design-envelope.json').read_text())
    lib=[];items=[];bom=[];pinmap={};rootid=uid('root')
    two=[(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')]
    rb='(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))'
    cb='(polyline(pts(xy -2.54 .762)(xy 2.54 .762))(stroke(width .3)(type default))(fill(type none)))(polyline(pts(xy -2.54 -.762)(xy 2.54 -.762))(stroke(width .3)(type default))(fill(type none)))(polyline(pts(xy 0 2.54)(xy 0 .762))(stroke(width .254)(type default))(fill(type none)))(polyline(pts(xy 0 -.762)(xy 0 -2.54))(stroke(width .254)(type default))(fill(type none)))'
    lib += [symbol('R',two,rb,'R'),symbol('C',two,cb,'C')]
    def boxpins(mapping):
        result=[];count=len(mapping);split=(count+1)//2
        for i,(n,(name,net,typ)) in enumerate(mapping.items()):
            left=i<split;row=i if left else i-split
            result.append((n,name,-25.4 if left else 25.4,(split-1)*2.54-row*5.08,0 if left else 180,typ))
        height=max(10.16,split*2.54+2.54)
        return result,f'(rectangle(start -22.86 {height})(end 22.86 {-height})(stroke(width .254)(type default))(fill(type background)))'
    def register(name,mapping,refprefix='U'):
        pins,body=boxpins(mapping);lib.append(symbol(name,pins,body,refprefix));return pins
    module={n:(name,d['module_pin_nets'][n],'power_in' if int(n) in(1,2,40,41) else'input' if int(n)==3 else'bidirectional') for n,name in d['module_pin_names'].items()}
    pins={'MODULE':register('ESP32_S3_WROOM_1_N8',module)}
    for ref,p in d['active_parts'].items():pins[ref]=register(ref+'_DEVICE',p['pins'],'D' if ref.startswith('D') else'U')
    usb={n:(n,net,'passive') for n,net in d['usb_receptacle']['pin_map'].items()};pins['JUSB1']=register('USB_C_16P_BOUNDARY',usb,'J')
    for ref,nets in d['boundaries'].items():pins[ref]=register(ref+'_BOUNDARY',{str(i):(str(i),net,'passive') for i,net in enumerate(nets,1)},'J')
    flag=[(1,'pwr',0,0,90,'power_out')];lib.append(symbol('PWR_FLAG',flag,'','#FLG'))
    def place(name,ref,value,x,y,ps,nets,mpn=''):
        x=round(round(x/1.27)*1.27,4);y=round(round(y/1.27)*1.27,4)
        top=y-max(p[3] for p in ps)-9
        props=''.join(f'(property {quote(k)} {quote(v)}(at {x} {top+dy} 0){effects(1,"hide" if hidden else "")})' for k,v,dy,hidden in [('Reference',ref,0,False),('Value',value,2.54,False),('Footprint','',0,True),('MPN',mpn,0,True)])
        items.append(f'(symbol(lib_id "CNC:{name}")(at {x} {y} 0)(unit 1)(in_bom {"no" if ref.startswith("#") else"yes"})(on_board {"no" if ref.startswith("#") else"yes"})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "esp_service"(path "/{rootid}"(reference {quote(ref)})(unit 1)))))')
        pinmap[ref]={str(k):v for k,v in nets.items()}
        for n,_,px,py,_,_ in ps:
            sx,sy=round(x+px,4),round(y-py,4);net=nets.get(str(n))
            if net is None:items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(n)+"NC")}"))');continue
            dx=-35.56 if px<0 else 10.16 if px>0 else 0;dy=0 if px else -5.08 if py>=0 else 5.08
            ex,ey=round(sx+dx,4),round(sy+dy,4)
            items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"W")}"))')
            items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.95,"(justify left bottom)")}(uuid "{uid(ref+str(n)+"L")}"))')
        if not ref.startswith('#'):bom.append({'reference':ref,'value':value,'mpn':mpn,'footprint':'','status':'candidate; exact land and assembly qualification open'})
    place('ESP32_S3_WROOM_1_N8','U1',d['module_mpn'],110,115,pins['MODULE'],d['module_pin_nets'],d['module_mpn'])
    positions={'U2':(310,65),'U3':(485,65),'U4':(660,65),'U5':(310,145),'U6':(485,145),'D1':(660,145),'D2':(310,215),'D3':(485,215),'D4':(660,215)}
    for ref,p in d['active_parts'].items():
        place(ref+'_DEVICE',ref,p['mpn'],*positions[ref],pins[ref],{n:a[1] for n,a in p['pins'].items()},p['mpn'])
    for i,(ref,p) in enumerate(d['passives'].items()):
        place(ref[0],ref,p['value'],round(55+(i%10)*76.2,4),round(290+(i//10)*50.8,4),two,{str(j):net for j,net in enumerate(p['nets'],1)})
    place('USB_C_16P_BOUNDARY','JUSB1','USB-C ELECTRICAL BOUNDARY',110,465,pins['JUSB1'],d['usb_receptacle']['pin_map'])
    for i,(ref,nets) in enumerate(d['boundaries'].items()):
        x=round(310+(i%3)*175,4);y=round(455+(i//3)*80,4)
        place(ref+'_BOUNDARY',ref,ref[1:-1]+' BOUNDARY',x,y,pins[ref],{str(j):net for j,net in enumerate(nets,1)})
    for i,net in enumerate(('ESP_3V3','LOGIC_GND','SERVICE_VREF_3V3')):place('PWR_FLAG','#FLG'+str(i),'CONDITIONAL SOURCE',50+i*75,415,flag,{'1':net})
    def note(y,t,size=1.2):items.append(f'(text {quote(t)}(at 20.32 {y} 0){effects(size,"(justify left top)")}(uuid "{uid(t)}"))')
    note(12.7,'ESP32-S3 SERVICE / RECOVERY CANDIDATE - NO MOTION OR ACCESSORY OUTPUT AUTHORITY',2)
    note(23,'Self-powered USB2 device; USB VBUS never powers controller. USB connector is an electrical boundary pending exact pad mapping.\nU2 is Schmitt AND: module EN = sequencer ESP_CHIP_PU AND manual-reset release. Never ground sequencer output.\nHost RX is GPIO4 via powered-off buffer; default firmware leaves it disabled. UART0 adapter VREF powers only its outgoing buffer.')
    note(565,'All footprints unassigned: no board layout or manufacture claim. USB switch D pins face connector; 1D pins face ESP; port2NC andSground.\nTwo independent5.1k CC resistors. SBU pins NC. NoPD/high-voltage mode. Local USB shield bond toLOGIC_GND is provisional; assess enclosure/EMC.\nJRESET/JBOOT: normally-open dry contacts only. HoldBOOT low, holdRESET>=20ms, releaseRESET, keepBOOTlow>=3ms thenrelease.\nJRES is reserved internal3.3V logic only; current firmware provides no accessory support. No5V/24V/unpowered external drive.\nModule antenna outsidecarrieredge preferred; enclosureclearance>=15mm all directions. Shared2.4GHzWi-Fi/BLE, no5GHzorClassicBT.')
    sch=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{rootid}")(paper "A1")(title_block(title "ESP service and recovery")(date "2026-09-28")(rev "r0.1"))(lib_symbols'+''.join(lib)+')'+''.join(items)+')'
    (OUT/'esp_service.kicad_sch').write_text(dump(parse(sch))+'\n')
    libs=''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in lib)
    (OUT/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+libs+')'))+'\n')
    (OUT/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "ESP service candidate symbols")))'))+'\n')
    (OUT/'esp_service.kicad_pro').write_text('{"meta":{"filename":"esp_service.kicad_pro","version":1}}\n')
    (OUT/'pin-map.json').write_text(json.dumps(pinmap,indent=2)+'\n')
    with (OUT/'bom.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(bom[0]));w.writeheader();w.writerows(bom)
    print(OUT/'esp_service.kicad_sch')

if __name__=='__main__':main()
