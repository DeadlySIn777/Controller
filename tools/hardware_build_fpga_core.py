"""Build a sourced T20F256 candidate schematic. Does not fit HDL or emit fabrication files."""
from pathlib import Path
import csv
import hashlib
import json
import uuid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/fpga_core'
NS = uuid.UUID('df6f5618-2d9f-4be4-bcb0-4ee705bfc0a9')


def uid(key):
    return str(uuid.uuid5(NS, key))


def q(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


def ef(n=1, extra=''):
    return f'(effects (font (size {n} {n})) {extra})'


def symbol(name, pins, body, ref='U'):
    props = ''.join(f'(property {q(k)} {q(v)} (at 0 0 0) {ef(extra="hide")})' for k, v in [('Reference', ref), ('Value', name)])
    ps = ''.join(f'(pin {kind} line (at {x} {y} {angle}) (length 2.54) (name {q(label)} {ef()}) (number {q(number)} {ef()}))' for number, label, x, y, angle, kind in pins)
    return f'(symbol "FPGA:{name}" (pin_names (offset 0.5)) (in_bom yes) (on_board yes) {props} (symbol "{name}_0_1" {body}) (symbol "{name}_1_1" {ps}))'


def rect(x, y):
    return f'(rectangle (start {-x} {y}) (end {x} {-y}) (stroke (width 0.254) (type default)) (fill (type background)))'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    research = ROOT / 'research/fpga-core'
    official = json.loads((research/'pins-official.json').read_text(encoding='utf-8'))
    allocation = json.loads((OUT/'pin-allocation.json').read_text(encoding='utf-8'))
    nets = allocation['pin_net']
    fpga = []
    for index, p in enumerate(official):
        side, row = divmod(index, 128)
        kind = 'power_in' if p['name'].startswith('VCC') or p['name'] == 'GND' else 'bidirectional'
        if p['name'] in ('CRESET_N', 'TCK', 'TDI', 'TMS'): kind = 'input'
        if p['name'] == 'TDO': kind = 'tri_state'
        if p['name'] == 'CDONE': kind = 'open_collector'
        if p['name'] == 'REF_RES': kind = 'passive'
        fpga.append((p['ball'],p['name'],-88.9 if side==0 else 88.9,round(322.58-row*5.08,3),0 if side==0 else 180,kind))
    two = [(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')]
    flash = [(1,'CS_N',-20.32,15.24,0,'input'),(2,'DO / IO1',20.32,10.16,180,'tri_state'),(3,'WP_N / IO2',-20.32,-5.08,0,'bidirectional'),(4,'GND',0,-25.4,90,'power_in'),(5,'DI / IO0',-20.32,5.08,0,'input'),(6,'CLK',-20.32,10.16,0,'input'),(7,'HOLD_N / IO3',-20.32,-10.16,0,'bidirectional'),(8,'VCC',0,25.4,270,'power_in')]
    osc = [(1,'STBY_N',-20.32,5.08,0,'input'),(2,'GND',0,-20.32,90,'power_in'),(3,'OUT',20.32,0,180,'output'),(4,'VDD',0,20.32,270,'power_in')]
    gate = [(1,'A',-15.24,5.08,0,'input'),(2,'B',-15.24,-5.08,0,'input'),(3,'GND',0,-20.32,90,'power_in'),(4,'Y',15.24,0,180,'output'),(5,'VCC',0,20.32,270,'power_in')]
    # Nexperia 74LVC1G17 Rev.16.1, Table3: GW/TSSOP5 is NC1/A2/GND3/Y4/VCC5.
    # Do not reuse a different vendor's functionally equivalent package pin order.
    buffer = [(1,'N.C.',-15.24,-5.08,0,'no_connect'),(2,'A',-15.24,5.08,0,'input'),(3,'GND',0,-20.32,90,'power_in'),(4,'Y',15.24,0,180,'output'),(5,'VCC',0,20.32,270,'power_in')]
    capbody = '(polyline (pts (xy -2.54 0.762) (xy 2.54 0.762)) (stroke (width 0.3) (type default)) (fill (type none))) (polyline (pts (xy -2.54 -0.762) (xy 2.54 -0.762)) (stroke (width 0.3) (type default)) (fill (type none))) (polyline (pts (xy 0 2.54) (xy 0 0.762)) (stroke (width 0.254) (type default)) (fill (type none))) (polyline (pts (xy 0 -0.762) (xy 0 -2.54)) (stroke (width 0.254) (type default)) (fill (type none)))'
    lib=[symbol('T20F256I4',fpga,rect(86.36,327.66)),symbol('W25Q32JVSSIQ',flash,rect(17.78,22.86)),symbol('ASE_50MHz',osc,rect(17.78,17.78),'Y'),symbol('SN74LVC1G08DCKR',gate,rect(12.7,17.78)),symbol('74LVC1G17GW',buffer,rect(12.7,17.78)),symbol('R',two,rect(1.016,2.54),'R'),symbol('C',two,capbody,'C')]
    flag=[(1,'pwr',0,0,90,'power_out')]; lib.append(symbol('PWR_FLAG',flag,'','#FLG'))
    conns={}
    for n in (8,12,14,24):
        conns[n]=[(i,str(i),-5.08,-(i-1)*2.54,0,'passive') for i in range(1,n+1)]
        body=f'(rectangle (start -2.54 2.54) (end 2.54 {-n*2.54}) (stroke (width 0.254) (type default)) (fill (type background)))'
        lib.append(symbol(f'Conn{n}',conns[n],body,'J'))
    rootid=uid('root'); items=[]; pos={}; parts={}

    def place(name,ref,value,x,y,pins,mpn='',footprint='',**detail):
        pos[ref]={str(n):(round(x+px,3),round(y-py,3)) for n,_,px,py,_,_ in pins}
        xx,ry,vy=x+4,y-2.54,y+1.27
        if name not in ('R','C'):xx,ry,vy=x,y-32,y-29
        if ref=='U1':xx,ry,vy=x,y-338,y-333
        props=f'(property "Reference" {q(ref)} (at {xx} {ry} 0) {ef()}) (property "Value" {q(value)} (at {xx} {vy} 0) {ef()})'
        props+=f'(property "MPN" {q(mpn)} (at {x} {y} 0) {ef(extra="hide")}) (property "Footprint" {q(footprint)} (at {x} {y} 0) {ef(extra="hide")})'
        items.append(f'(symbol (lib_id "FPGA:{name}") (at {x} {y} 0) (unit 1) (in_bom {"no" if ref.startswith("#") else "yes"}) (on_board {"no" if ref.startswith("#") else "yes"}) (dnp no) (uuid "{uid(ref)}") {props} (instances (project "fpga_core" (path "/{rootid}" (reference {q(ref)}) (unit 1)))))')
        if not ref.startswith('#'):parts[ref]={'value':value,'mpn':mpn,'footprint':footprint,'pins':{},'status':'candidate_not_qualified',**detail}

    def label(ref,pin,net,dx=0,dy=0):
        x,y=pos[ref][str(pin)];ex,ey=round(x+dx,3),round(y+dy,3)
        if dx or dy:items.append(f'(wire (pts (xy {x} {y}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid "{uid(ref+str(pin)+"wire")}"))')
        items.append(f'(label {q(net)} (at {ex} {ey} 0) {ef(.95,"(justify left bottom)")} (uuid "{uid(ref+str(pin)+"label")}"))')
        if ref in parts:parts[ref]['pins'][str(pin)]=net

    def nc(ref,pin):
        x,y=pos[ref][str(pin)]
        items.append(f'(no_connect (at {x} {y}) (uuid "{uid(ref+str(pin)+"nc")}"))')

    def note(x,y,text,size=1.4):
        items.append(f'(text {q(text)} (at {x} {y} 0) {ef(size,"(justify left top)")} (uuid "{uid(text)}"))')

    def passive(ref,value,x,y,n1,n2,mpn='',**detail):
        name=ref[0];footprint=detail.pop('footprint',f'{"Resistor" if name=="R" else "Capacitor"}_SMD:{name}_0603_1608Metric');place(name,ref,value,x,y,two,mpn,footprint,**detail)
        label(ref,1,n1,dy=-5.08);label(ref,2,n2,dy=5.08)

    place('T20F256I4','U1','T20F256I4 / CANDIDATE PIN ALLOCATION',325.12,398.78,fpga,'T20F256I4',package='FBGA256 13x13mm 0.8mm pitch',footprint_status='requires_manufacturer_land_pattern_review')
    for pin,_,x,_,_,_ in fpga:
        if pin in nets:label('U1',pin,nets[pin],dx=-101.6 if x<0 else 10.16)
        else:
            px,py=pos['U1'][pin];items.append(f'(no_connect (at {px} {py}) (uuid "{uid("NC"+pin)}"))')
    place('W25Q32JVSSIQ','U2','W25Q32JVSSIQ / x1 SPI',693.42,99.06,flash,'W25Q32JVSSIQ','Package_SO:SOIC-8_5.3x5.3mm_P1.27mm',package='SOIC8 208mil',capacity_bits=33554432)
    for pin,net in {1:'FPGA_FLASH_CS_N',2:'FPGA_FLASH_MISO',3:'FPGA_FLASH_IO2',4:'LOGIC_GND',5:'FPGA_FLASH_MOSI',6:'FPGA_FLASH_CCK',7:'FPGA_FLASH_IO3',8:'IO_3V3'}.items():label('U2',pin,net,dx=-63.5 if pin in (1,3,5,6,7) else 10.16 if pin==2 else 0,dy=-5.08 if pin==8 else 5.08 if pin==4 else 0)
    place('ASE_50MHz','Y1','ASE-50.000MHZ-L-C-T',922.02,99.06,osc,'ASE-50.000MHZ-L-C-T',package='3.2x2.5mm 4pad',footprint_status='manufacturer_land_pattern_pending',frequency_hz=50000000,frequency_stability_ppm=50,supply_v=[3.135,3.465],supply_current_max_a=.019,startup_max_s=.002)
    for pin,net in {1:'IO_3V3',2:'LOGIC_GND',3:'FPGA_CLK_SOURCE',4:'IO_3V3'}.items():label('Y1',pin,net,dx=-20.32 if pin==1 else 10.16 if pin==3 else 0,dy=-5.08 if pin==4 else 5.08 if pin==2 else 0)
    place('SN74LVC1G08DCKR','U3','SN74LVC1G08DCKR / RESET AND',1069.34,99.06,gate,'SN74LVC1G08DCKR','Package_TO_SOT_SMD:SOT-353_SC-70-5',package='DCK5 SC70')
    for pin,net in {1:'FPGA_CRESET_N',2:'FPGA_SERVICE_RUN_N',3:'LOGIC_GND',4:'FPGA_LOCAL_RESET_N',5:'IO_3V3'}.items():label('U3',pin,net,dx=-48.26 if pin in (1,2) else 7.62 if pin==4 else 0,dy=-5.08 if pin==5 else 5.08 if pin==3 else 0)
    place('74LVC1G17GW','U4','74LVC1G17GW / CDONE DELAY SCHMITT',1069.34,175.26,buffer,'74LVC1G17GW','Package_TO_SOT_SMD:SOT-353_SC-70-5',package='SOT353-1',role='post_configuration_reset_delay')
    for pin,net in {2:'FPGA_USER_RESET_RC',3:'LOGIC_GND',4:'FPGA_USER_RESET_DELAYED',5:'IO_3V3'}.items():label('U4',pin,net,dx=-48.26 if pin==2 else 7.62 if pin==4 else 0,dy=-5.08 if pin==5 else 5.08 if pin==3 else 0)
    nc('U4',1)
    place('SN74LVC1G08DCKR','U5','SN74LVC1G08DCKR / USER RESET AND',1069.34,251.46,gate,'SN74LVC1G08DCKR','Package_TO_SOT_SMD:SOT-353_SC-70-5',package='DCK5 SC70',role='post_configuration_reset_gate')
    for pin,net in {1:'FPGA_USER_RESET_DELAYED',2:'FPGA_SERVICE_RUN_N',3:'LOGIC_GND',4:'FPGA_USER_RESET_N',5:'IO_3V3'}.items():label('U5',pin,net,dx=-48.26 if pin in (1,2) else 7.62 if pin==4 else 0,dy=-5.08 if pin==5 else 5.08 if pin==3 else 0)
    rlist=[('FPGA_CLK_SOURCE','FPGA_CLK_50M',33),('FPGA_FLASH_CCK_SOURCE','FPGA_FLASH_CCK',33)]
    for net in ('FPGA_CDONE','FPGA_CFG_CSI','FPGA_CFG_TEST_N','FPGA_FLASH_CS_N','FPGA_CFG_CBUS2','FPGA_CFG_CBUS1','FPGA_CFG_CBUS0','FPGA_JTAG_TCK','FPGA_JTAG_TDI','FPGA_JTAG_TMS','FPGA_JTAG_TDO','FPGA_FLASH_IO2','FPGA_FLASH_IO3','FPGA_SERVICE_RUN_N','FPGA_CFG_NSTATUS'):
        rlist.append(('IO_3V3',net,10000))
    rlist += [('FPGA_CFG_CBSEL0','LOGIC_GND',10000),('FPGA_CFG_CBSEL1','LOGIC_GND',10000)]
    rlist += [('IO_3V3','FPGA_LOCAL_RESET_N',47000),('FPGA_LOCAL_RESET_N','LOGIC_GND',1000),('FPGA_CDONE','FPGA_USER_RESET_RC',10000)]
    # These defaults bound unconfigured/high-Z FPGA states; external permission still independently gates drivers.
    for net in ('FPGA_ENDPOINT_READY','FPGA_MOTION_REQUEST','FPGA_PROGRESS_WDI'):rlist.append((net,'LOGIC_GND',10000))
    for i,(a,b,r) in enumerate(rlist,1):
        x=584.2+((i-1)%7)*81.28;y=175.26+((i-1)//7)*48.26
        # Keep the new U4/U5 reset symbols clear of the former last resistor column.
        # These unused final-row positions change drawing geometry, not connectivity.
        if i in (7,14,21):x=909.32+((i//7)-1)*81.28;y=320.04
        mpn={33:'CRCW060333R0FKEA',10000:'CRCW060310K0FKEA',47000:'CRCW060347K0FKEA',1000:'CRCW06031K00FKEA'}[r]
        passive(f'R{i}',f'{r:g}R 1%',x,y,a,b,mpn,resistance_ohm=r,tolerance=.01,power_70c_w=.1)
    supplypins=[p for p in official if p['name'].startswith('VCC')]
    capspec=[(.1e-6,nets[p['ball']],p['ball']) for p in supplypins]
    capspec += [(4.7e-6,'CORE_1V2','VCC cluster')]+[(1e-6,'CORE_1V2',ball) for ball in ('K11','F7','G11')]
    capspec += [(4.7e-6,'IO_3V3',bank) for bank in ('1A','1B_1C','1D_1E','3A_3B_3C','3D_3E','4A','4B')]
    capspec += [(.1e-6,'IO_3V3','U2'),(1e-6,'IO_3V3','U2'),(.01e-6,'IO_3V3','Y1'),(.1e-6,'IO_3V3','U3')]
    capspec += [(1e-6,'FPGA_USER_RESET_RC','post-CDONE reset delay')]
    for i,(c,net,target) in enumerate(capspec,1):
        x=584.2+((i-1)%8)*71.12;y=383.54+((i-1)//8)*43.18
        value=f'{c*1e6:g}uF 16V X7R';mpn={.1e-6:'885012206046',1e-6:'885012206052',4.7e-6:'885012207053',.01e-6:'885012206040'}[c]
        passive(f'C{i}',value,x,y,net,'LOGIC_GND',mpn,capacitance_f=c,footprint='Capacitor_SMD:C_0805_2012Metric' if c==4.7e-6 else 'Capacitor_SMD:C_0603_1608Metric',voltage_v=16,tolerance=.1,temperature_change=.15,placement_target=target,mpn_status='primary_datasheet_verified_dc_bias_and_lifecycle_review_pending')
    groups=[('J1','POWER / QUALIFIED SEQUENCER',['CORE_1V2','IO_3V3','LOGIC_GND','FPGA_CRESET_N','FPGA_LOCAL_RESET_N','FPGA_CDONE','FPGA_CFG_NSTATUS','LOGIC_GND']),('J2','JTAG SERVICE / NO POWER INJECTION',['IO_3V3','LOGIC_GND','FPGA_JTAG_TCK','FPGA_JTAG_TMS','FPGA_JTAG_TDI','FPGA_JTAG_TDO','FPGA_SERVICE_RUN_N','FPGA_CDONE']),('J3','HOST SPI / 3V3 ONLY',['HOST_SPI_CS_N','HOST_SPI_SCLK','HOST_SPI_MOSI','HOST_SPI_MISO','LOGIC_GND','FPGA_LINK_FAULT','FPGA_WATCHDOG_FAULT','FPGA_TIMING_FAULT']),('J4','HW PERMISSION / NO ESP MOTION AUTHORITY',['HW_WATCHDOG_OK_N','FPGA_ENDPOINT_READY','FPGA_MOTION_REQUEST','FPGA_PROGRESS_WDI','TX_PERMIT','FPGA_INHIBIT_FAULT','FPGA_LOCAL_RESET_N','LOGIC_GND'])]
    groups += [('J5','TWELVE MOTOR STEP / DIR',[n for i in range(12) for n in (f'STEP{i}_FPGA',f'DIR{i}_FPGA')]),('J6','ENABLE RESERVES / CIRCUITS ABSENT',[f'DRIVE_ENABLE{i}_FPGA_RESERVED' for i in range(12)]),('J7','HOME / 0-5 PRESENT; 6-11 RESERVED',[f'HOME{i}_FPGA' for i in range(12)]),('J8','ALARM / 0-5 PRESENT; 6-11 RESERVED',[f'ALM{i}_FPGA' for i in range(12)]),('J9','ENCODERS / 0-1 PRESENT; 2-3 RESERVED',[f'ENC{i}_{s}_FPGA' for i in range(4) for s in 'ABZ']),('J10','AUX / EXISTING ISOLATED INPUTS',['PROBE_FPGA','TOOLSETTER_FPGA','DOOR_STATUS_FPGA','PROTECTIVE_STATUS_FPGA','SPINDLE_FAULT_FPGA','SPINDLE_READY_FPGA','FEED_HOLD_FPGA','CYCLE_START_FPGA','LUBE_STATUS_FPGA','SPARE_FPGA','IO_3V3','LOGIC_GND'])]
    for i,(ref,title,nn) in enumerate(groups):
        x=638.81+(i%5)*116.84;y=635+(i//5)*104.14
        place(f'Conn{len(nn)}',ref,title,x,y,conns[len(nn)],role='schematic_boundary_not_orderable')
        for j,net in enumerate(nn,1):label(ref,j,net,dx=-96.52)
    for i,net in enumerate(('CORE_1V2','IO_3V3','LOGIC_GND'),1):
        place('PWR_FLAG',f'#FLG0{i}','SUPPLIED BY UPSTREAM',71.12,746.76+i*15.24,flag);label(f'#FLG0{i}',1,net,dx=7.62)
    note(20.32,15.24,'T20F256 FPGA CORE / MINIMUM 8 MOTOR CHANNELS, 12-CHANNEL PIN CAPACITY CANDIDATE',2.4)
    note(20.32,28,'Exact 256 balls: Efinix T20-PINOUT worksheet T20F256. Pin allocation is a board candidate, NOT vendor fit or routed timing.\nAll VCCIO=3.3V. All VCC/VCCA=1.2V. No 5V-tolerant FPGA connection. No native LVDS: REF_RES intentionally NC.',1.5)
    note(560,28,'One 100nF per supply ball; bulk per physical supply group. Decoupling is a layout-study allowance, not a PDN proof.\nActive SPI x1 straps111; CSI/TEST high. Flash bus reserved from user RTL. CCK damping33R is provisional.\nCDONE is open-drain with10k pullup; status does not grant motion permission. Configuration clock is internal, not Y1.',1.5)
    note(20.32,740,'RESET: U3 combines qualified upstream reset with service RUN for configuration reset only. U4/U5 make a separate CDONE-qualified user-logic reset; R22/C39 provide a candidate post-CDONE delay and service RUN can hold it low through a JTAG handoff. No programmer output fights the sequencer.\nUser-logic reset release threshold, RC tolerance, discharge time, tUSER handoff and startup/release synchronizers remain bench/HDL qualification gates.\nJ2 is a logical service boundary: actual keyed connector, adapter, cable loading and ESD are unresolved.\nJTAG programming requires a deliberate reset cycle, valid rails and machine outputs inhibited. No hot-plug or phantom powering.',1.5)
    note(165.1,785,'NC crosses are genuine unused GPIO/config outputs and REF_RES only; every supply/GND ball is connected.\nBoundary symbols are not released connectors. No footprint approval, PCB, DRC, bitstream, qualification or fabrication files.',1.4)
    note(560,586,'J1-J10 ARE INTERNAL LOGIC BOUNDARIES, NOT FIELD TERMINALS. Enables and extra home/alarm/encoder channels are reserves only.\nCRESET47k/1k plus two internal pullups screened. The separate 10k/1uF CDONE reset delay is a candidate, not a guaranteed time or safety function; threshold/partial-power confirmation required.',1.4)
    sch=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{rootid}") (paper "A0") (lib_symbols {"".join(lib)})\n'+ '\n'.join(items)+')\n'
    (OUT/'fpga_core.kicad_sch').write_text(sch,encoding='utf-8')
    (OUT/'FPGA.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") '+''.join(s.replace('(symbol "FPGA:','(symbol "',1) for s in lib)+')\n',encoding='utf-8')
    (OUT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "FPGA")(type "KiCad")(uri "${KIPRJMOD}/FPGA.kicad_sym")(options "")(descr "Sourced T20 candidate symbols")))\n',encoding='utf-8')
    (OUT/'fpga_core.kicad_pro').write_text('{"meta":{"filename":"fpga_core.kicad_pro","version":1}}\n',encoding='utf-8')
    model={'schema_version':1,'revision':'fpga-core-r0.2','status':'review_candidate_not_qualified','manufacturing_ready':False,'fpga_package_fit_proved':False,'physical_qualification':False,'motor_capacity':{'minimum_required':8,'candidate_physical_step_dir':12,'individual_enable_circuits_present':0,'alarm_circuits_present':6,'historical_six_scope_preserved':True},'rails':{'CORE_1V2':{'nominal_v':1.2,'permitted_v':[1.15,1.25],'existing_reservation_a':.8},'IO_3V3':{'nominal_v':3.3,'permitted_v':[3.14,3.465],'existing_fpga_reservation_a':.4,'additional_support_reservation_a':.06}},'clock_hz':50000000,'bitstream_max_bits':5445600,'flash_bits':33554432,'configuration_mode':'active_SPI_x1_CBUS111','root_uuid':rootid,'source_sha256':{n:hashlib.sha256((research/n).read_bytes()).hexdigest() for n in ('t20-pinout.xlsx','pins-official.json','trion20-ds-v6.0.pdf','an006.pdf','t20-board.pdf','ase.pdf','w25q32jv.pdf','sn74lvc1g08.pdf','74lvc1g17.pdf','885012206046.pdf','885012206052.pdf','885012207053.pdf','885012206040.pdf')},'components':parts}
    model['revision']='fpga-core-r0.3'
    model['source_sha256']['74LVC1G17.txt']=hashlib.sha256((research/'74LVC1G17.txt').read_bytes()).hexdigest()
    (OUT/'design.json').write_text(json.dumps(model,indent=2)+'\n',encoding='utf-8')
    with (OUT/'bom.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['Reference','Value','MPN','Footprint','Status','Scope'])
        for ref,v in parts.items():w.writerow([ref,v['value'],v['mpn'],v['footprint'],v['status'],v.get('role','physical_component_candidate')])
    print(OUT/'fpga_core.kicad_sch')


if __name__=='__main__':main()
