"""Editable independent watchdog/permission candidate; no manufacturing release."""
import hashlib
import json
from pathlib import Path
import re
import uuid
from hardware_build_tx_schematic import effects, quote, symbol
from hardware_build_logic_power import footprint

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/machine_permission'
NS=uuid.UUID('23cfeefb-8715-4e9c-ae8d-e4580042392c')


def main():
    OUT.mkdir(exist_ok=True); uid=lambda text:str(uuid.uuid5(NS,text));root=uid('root')
    # Physical package pin tables; every named pin is represented once.
    defs={
        'TPS3431':{1:('VDD','power_in'),2:('CWD','input'),3:('EN','input'),4:('GND','power_in'),
                   5:('SET1','input'),6:('WDI','input'),7:('WDO_N','open_collector'),8:('ENOUT','open_collector'),9:('EP','power_in')},
        'LVC2G17':{1:('1A','input'),2:('GND','power_in'),3:('2A','input'),4:('2Y','output'),5:('VCC','power_in'),6:('1Y','output')},
        'LVC1G34':{1:('NC','no_connect'),2:('A','input'),3:('GND','power_in'),4:('Y','output'),5:('VCC','power_in')},
        'LVC1G11':{1:('A','input'),2:('GND','power_in'),3:('B','input'),4:('Y','output'),5:('VCC','power_in'),6:('C','input')},
        'LVC2G08':{1:('1A','input'),2:('1B','input'),3:('2Y','output'),4:('GND','power_in'),5:('2A','input'),6:('2B','input'),7:('1Y','output'),8:('VCC','power_in')},
        'LVC2G74':{1:('CLK','input'),2:('D','input'),3:('Q_N','output'),4:('GND','power_in'),5:('Q','output'),6:('CLR_N','input'),7:('PRE_N','input'),8:('VCC','power_in')}}
    pinsets={};lib=[]
    for name,pmap in defs.items():
        left=[p for p,(_,t) in pmap.items() if t not in ('output','open_collector')]
        right=[p for p,(_,t) in pmap.items() if t in ('output','open_collector')]
        pins=[]
        for side,plist in ((-1,left),(1,right)):
            for j,p in enumerate(plist):
                nm,typ=pmap[p];pins.append((p,nm,side*20.32,25.4-j*10.16,0 if side==-1 else 180,typ))
        pinsets[name]=pins
        lib.append(symbol(name,pins,'(rectangle(start -17.78 30.48)(end 17.78 -50.8)(stroke(width .254)(type default))(fill(type background)))'))
    pp=[(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')]
    for name,shape,prefix in [('R','(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))','R'),
                              ('C','(polyline(pts(xy -2.54 .762)(xy 2.54 .762))(stroke(width .3)(type default))(fill(type none))) (polyline(pts(xy -2.54 -.762)(xy 2.54 -.762))(stroke(width .3)(type default))(fill(type none))) (polyline(pts(xy 0 2.54)(xy 0 .762))(stroke(width .254)(type default))(fill(type none))) (polyline(pts(xy 0 -.762)(xy 0 -2.54))(stroke(width .254)(type default))(fill(type none)))','C')]:
        lib.append(symbol(name,pp,shape,prefix));pinsets[name]=pp
    fp=[(1,'pwr',0,0,90,'power_out')];pinsets['PWR_FLAG']=fp;lib.append(symbol('PWR_FLAG',fp,'','#FLG'))
    boundary={'JCTRL1':['IO_3V3','LOGIC_GND','FPGA_LOCAL_RESET_N','FPGA_CDONE','EXT_PERMIT_3V3','FPGA_ENDPOINT_READY','FPGA_MOTION_REQUEST','FPGA_PROGRESS_WDI'],
              'JOUT1':['TX_PERMIT','HW_WATCHDOG_OK_N','HW_PERMISSION_LATCHED','WD_HEALTH_RAW_N','LOGIC_GND']}
    for n in (5,8):
        pins=[(i,str(i),-5.08,-(i-1)*5.08,0,'passive') for i in range(1,n+1)]
        pinsets['Conn'+str(n)]=pins
        lib.append(symbol('Conn'+str(n),pins,f'(rectangle(start -2.54 2.54)(end 2.54 {-n*5.08})(stroke(width .254)(type default))(fill(type background)))','J'))
    items=[];positions={};parts={};nodes={}
    def place(name,ref,val,x,y,mpn='',foot=''):
        pins=pinsets[name];positions[ref]={str(n):(round(x+px,4),round(y-py,4)) for n,_,px,py,_,_ in pins}
        passive=name in ('R','C');px=x+3.81 if passive else x;ry=y-2.54 if passive else y-7.62;vy=y+1.27 if passive else y-5.08
        ef=effects(.95,'(justify left)') if passive else effects(1)
        props=f'(property "Reference" {quote(ref)}(at {px} {ry} 0){ef})(property "Value" {quote(val)}(at {px} {vy} 0){ef})(property "Footprint" {quote(foot)}(at {x} {y} 0){effects(extra="hide")})(property "MPN" {quote(mpn)}(at {x} {y} 0){effects(extra="hide")})'
        items.append(f'(symbol(lib_id "CNC:{name}")(at {x} {y} 0)(unit 1)(in_bom {"no" if ref.startswith("#") else "yes"})(on_board {"no" if ref.startswith("#") else "yes"})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "machine_permission"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
        if not ref.startswith('#'):parts[ref]={'value':val,'mpn':mpn,'footprint':foot}
    def label(ref,pin,net,dx=0,dy=0):
        x,y=positions[ref][str(pin)];xx,yy=round(x+dx,4),round(y+dy,4)
        if dx or dy:items.append(f'(wire(pts(xy {x} {y})(xy {xx} {yy}))(stroke(width 0)(type default))(uuid "{uid(ref+str(pin)+"w")}"))')
        items.append(f'(label {quote(net)}(at {xx} {yy} 0){effects(.95,"(justify left bottom)")}(uuid "{uid(ref+str(pin)+"l")}"))')
        if not ref.startswith('#'):nodes.setdefault(net,[]).append([ref,str(pin)])
    def nc(ref,pin):
        x,y=positions[ref][str(pin)];items.append(f'(no_connect(at {x} {y})(uuid "{uid(ref+str(pin)+"nc")}"))')
    def note(x,y,s,size=1.15):items.append(f'(text {quote(s)}(at {x} {y} 0){effects(size,"(justify left top)")}(uuid "{uid(s)}"))')
    chips=[
        ('U1','TPS3431','TPS3431SDRBR',139.7,96.52,'CNC_Permit:TPS3431_DRB8', {1:'IO_3V3',2:'WD_CWD',3:'IO_3V3',4:'LOGIC_GND',5:'IO_3V3',6:'WD_INPUT_BUF',7:'WD_HEALTH_RAW_N',8:'WD_HEALTH_RAW_N',9:'LOGIC_GND'}),
        ('U2','LVC2G17','SN74LVC2G17DBVR',353.06,96.52,'Package_TO_SOT_SMD:SOT-23-6',{1:'WD_HEALTH_RAW_N',2:'LOGIC_GND',3:'FPGA_CDONE',4:'CDONE_BUF',5:'IO_3V3',6:'WD_HEALTH_BUF'}),
        ('U3','LVC1G34','SN74LVC1G34DBVR',556.26,96.52,'Package_TO_SOT_SMD:SOT-23-5',{1:None,2:'FPGA_PROGRESS_WDI',3:'LOGIC_GND',4:'WD_INPUT_BUF',5:'IO_3V3'}),
        ('U4','LVC1G11','SN74LVC1G11DBVR',139.7,292.1,'Package_TO_SOT_SMD:SOT-23-6',{1:'FPGA_LOCAL_RESET_N',2:'LOGIC_GND',3:'CDONE_BUF',4:'BASE_INTERLOCK_OK',5:'IO_3V3',6:'EXT_PERMIT_3V3'}),
        ('U5','LVC2G08','SN74LVC2G08DCUR',353.06,292.1,'Package_SO:VSSOP-8_2.3x2mm_P0.5mm',{1:'BASE_INTERLOCK_OK',2:'WD_HEALTH_BUF',3:'LATCH_CLEAR_N',4:'LOGIC_GND',5:'HW_WATCHDOG_OK_N',6:'FPGA_ENDPOINT_READY',7:'HW_WATCHDOG_OK_N',8:'IO_3V3'}),
        ('U6','LVC2G74','SN74LVC2G74DCUR',556.26,292.1,'Package_SO:VSSOP-8_2.3x2mm_P0.5mm',{1:'FPGA_MOTION_REQUEST',2:'IO_3V3',3:None,4:'LOGIC_GND',5:'HW_PERMISSION_LATCHED',6:'LATCH_CLEAR_N',7:'IO_3V3',8:'IO_3V3'}),
        ('U7','LVC1G11','SN74LVC1G11DBVR',759.46,292.1,'Package_TO_SOT_SMD:SOT-23-6',{1:'HW_PERMISSION_LATCHED',2:'LOGIC_GND',3:'FPGA_MOTION_REQUEST',4:'TX_PERMIT',5:'IO_3V3',6:'HW_WATCHDOG_OK_N'})]
    for ref,name,mpn,x,y,foot,pmap in chips:
        place(name,ref,mpn,x,y,mpn,foot)
        for pin,net in pmap.items():
            if net is None:nc(ref,pin)
            else:label(ref,pin,net,dx=-63.5 if defs[name][pin][1] not in ('output','open_collector') else 7.62)
    def passive(name,ref,val,top,bottom,x,y,mpn=''):
        place(name,ref,val,x,y,mpn,('Resistor_SMD:R_0603_1608Metric' if name=='R' else 'Capacitor_SMD:C_0603_1608Metric'))
        label(ref,1,top,dy=-5.08);label(ref,2,bottom,dy=5.08)
    passive('C','C1','120pF C0G 50V 5%','WD_CWD','LOGIC_GND',55.88,170.18,'GRM1885C1H121JA01D')
    for i in range(7):passive('C',f'C{i+2}','100nF X7R 25V 20%','IO_3V3','LOGIC_GND',50.8+i*101.6,398.78)
    rrows=[('R1','10k','10K0','IO_3V3','WD_HEALTH_RAW_N',241.3,66.04),
           ('R2','100k','100K','WD_INPUT_BUF','LOGIC_GND',655.32,116.84),
           ('R3','10k','10K0','FPGA_PROGRESS_WDI','LOGIC_GND',454.66,180.34),
           ('R4','10k','10K0','FPGA_LOCAL_RESET_N','LOGIC_GND',55.88,210.82),
           ('R5','10k','10K0','EXT_PERMIT_3V3','LOGIC_GND',160.02,210.82),
           ('R6','10k','10K0','FPGA_ENDPOINT_READY','LOGIC_GND',261.62,210.82),
           ('R7','10k','10K0','FPGA_MOTION_REQUEST','LOGIC_GND',469.9,210.82),
           ('R8','10k','10K0','LATCH_CLEAR_N','LOGIC_GND',660.4,210.82),
           ('R9','10k','10K0','HW_PERMISSION_LATCHED','LOGIC_GND',660.4,335.28),
           ('R10','10k','10K0','TX_PERMIT','LOGIC_GND',792.48,398.78),
           ('R11','10k','10K0','HW_WATCHDOG_OK_N','LOGIC_GND',365.76,363.22)]
    for ref,val,code,top,bottom,x,y in rrows:passive('R',ref,val+' 1%',top,bottom,x,y,'CRCW0603'+code+'FKEA')
    for ref,x,y in [('JCTRL1',144.78,472.44),('JOUT1',398.78,472.44)]:
        nets=boundary[ref];place('Conn'+str(len(nets)),ref,'INTERNAL BOUNDARY',x,y)
        for pin,net in enumerate(nets,1):label(ref,pin,net,dx=-63.5)
    for i,net in enumerate(('IO_3V3','LOGIC_GND')):
        ref=f'#FLG{i+1}';place('PWR_FLAG',ref,'EXTERNAL',241.3+i*76.2,556.26);label(ref,1,net,dy=5.08)
    note(20.32,12.7,'INDEPENDENT WATCHDOG AND EDGE-ARMED GLOBAL PERMISSION - ENGINEERING CANDIDATE',2.2)
    note(20.32,27.94,'Seven ICs; no firmware timer owns the external watchdog. IO_3V3=3.2-3.4V, common LOGIC_GND. Eight motors minimum / twelve expansion requirement.',1.2)
    note(20.32,48.26,'1. Always-enabled watchdog; WDO + ENOUT wired together',1.5)
    note(264.16,48.26,'2. Schmitt inputs for open-drain watchdog and CDONE',1.5)
    note(477.52,48.26,'3. Rail-to-rail WDI buffer; FALLING edges feed timer',1.5)
    note(20.32,246.38,'4. Raw interlock',1.5);note(264.16,246.38,'5. Raw return and latch clear',1.5)
    note(477.52,246.38,'6. Accepted ARM edge; async clear',1.5);note(685.8,246.38,'7. Final physical permit',1.5)
    note(695.96,60.96,'120pF:64.288ms nominal watchdog. NOT20ms.\n100pF nominal would violate tested minimum at -tolerance.\nFalling progress edge occurs every TWO accepted UPDATEs.\nWDO auto-releases after170-230ms; heartbeat alone\ncannot set the arm latch. SYNC + deliberate ARM required.\nCDONE pullup belongs to FPGA block: no local pulldown.',1.15)
    note(477.52,462.28,'HW_WATCHDOG_OK_N -> RTL inhibit_n. Never return TX_PERMIT there.\nRaw interlock has no endpoint_ready / motion_request / latch dependency.\nD is permanently HIGH; clock is FPGA_MOTION_REQUEST rising edge.\nAsynchronous clear is raw interlock AND endpoint_ready.\nTX_PERMIT = latched_arm AND motion_request AND raw_interlock.',1.2)
    note(477.52,500.38,'TX_PERMIT drives six AM26C31 G inputs + six10k pulldowns; /G fixedHIGH.\nDefaultLOW disables transmitters. Per-drive active-low enables are separate.\nEXT_PERMIT_3V3 is protected internal logic, never raw24V or certified E-stop.\nSingle-channel candidate: no safety certification, fault tolerance or controlled stop.\nBrownout slew, partial power, metastability, wiring and physical timing remain open.\nClearing output permission can truncate a pulse; reconcile position before recovery.',1.15)
    sch=f'(kicad_sch(version 20250114)(generator "eeschema")(uuid "{root}")(paper "A1")(title_block(title "Independent watchdog / global permission")(date "2026-09-28")(rev "r0.1"))(lib_symbols {"".join(lib)})'+''.join(items)+')'
    (OUT/'machine_permission.kicad_sch').write_text(sch,encoding='utf-8')
    (OUT/'CNC.kicad_sym').write_text('(kicad_symbol_lib(version 20241209)(generator "kicad_symbol_editor")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in lib)+')',encoding='utf-8')
    (OUT/'sym-lib-table').write_text('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Permission candidate")))')
    (OUT/'machine_permission.kicad_pro').write_text('{"meta":{"filename":"machine_permission.kicad_pro","version":1}}\n')
    (OUT/'CNC_Permit.pretty').mkdir(exist_ok=True)
    pads=[(i+1,-1.4,-.975+i*.65,.6,.31) for i in range(4)]
    pads += [(i+5,1.4,.975-i*.65,.6,.31) for i in range(4)]
    pads += [(9,0,0,1.5,1.75)]
    (OUT/'CNC_Permit.pretty/TPS3431_DRB8.kicad_mod').write_text(footprint('TPS3431_DRB8',(3,3),pads))
    (OUT/'fp-lib-table').write_text('(fp_lib_table(version 7)(lib(name "CNC_Permit")(type "KiCad")(uri "${KIPRJMOD}/CNC_Permit.pretty")(options "")(descr "DRB copper pad candidate; thermal fanout/paste unresolved")))')
    data={'schema_version':1,'manufacturing_ready':False,'minimum_motor_requirement':8,'expansion_motor_requirement':12,
          'historical_ledger_used_only_for_rail_reference':True,'boundary':boundary,'parts':parts,
          'watchdog':{'mpn':'TPS3431SDRBR','capacitor_pf':120,'cap_initial_tolerance':.05,'cap_temperature_allowance':.006,
                      'cap_parasitic_allowance_pf':10,'timer_relative_error':.095,'reset_pulse_ms':[170,230],
                      'falling_edge_only':True,'enabled_permanently':True,'nominal_timeout_ms':64.288},
          'source_ledger_sha256':hashlib.sha256((OUT/'input-electrical-design.json').read_bytes()).hexdigest(),
          'unproven':['physical_edge_timing','power_transition_behavior','watchdog_pin_leakage','actual_cap_parasitic_and_leakage',
                     'full_temperature_schmitt_interpolation','async_clear_recovery_metastability','external_permit_frontend',
                     'single_component_fault_coverage','machine_stop_response','production_cost']}
    (OUT/'design-envelope.json').write_text(json.dumps(data,indent=2)+'\n')
    (OUT/'pin-map.json').write_text(json.dumps({k:sorted(v) for k,v in sorted(nodes.items())},indent=2)+'\n')
    for path in (OUT/'machine_permission.kicad_sch',OUT/'CNC.kicad_sym',OUT/'sym-lib-table',OUT/'fp-lib-table'):
        tokens=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',path.read_text());stack=[];tree=None
        for token in tokens:
            if token=='(':
                n=[]
                if stack:stack[-1].append(n)
                else:tree=n
                stack.append(n)
            elif token==')':stack.pop()
            else:stack[-1].append(token)
        def dump(n):return '('+' '.join(dump(x) if isinstance(x,list) else x for x in n)+')'
        path.write_text(dump(tree)+'\n')
    print(OUT/'machine_permission.kicad_sch')


if __name__=='__main__':main()
