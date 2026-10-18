"""Editable autonomous rail-window/reset candidate. Never a release-to-manufacture gate."""
import hashlib
import json
import re
from pathlib import Path
import uuid
from hardware_build_tx_schematic import effects, quote, symbol
from hardware_build_logic_power import footprint

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/power_sequence'
NS = uuid.UUID('2a5c0753-f749-4f1b-a734-8c0df65bc0a3')


def main():
    OUT.mkdir(exist_ok=True)
    uid = lambda s: str(uuid.uuid5(NS, s))
    root_id = uid('root')
    # ADI UD16 top view, p2. Pin17 is exposed ground, not a signal.
    pin_names = {1:'RDIS',2:'MR',3:'DVCC',4:'VCC',5:'REF',6:'PG1',7:'PG2',8:'PG3',
                 9:'PG4',10:'RT',11:'GND',12:'RST',13:'V4',14:'V3',15:'V2',16:'V1',17:'EP'}
    left = [4,16,15,14,13,2,1,3]
    right = [12,5,6,7,8,9,10]
    pins=[]
    for side, numbers in ((-1,left),(1,right)):
        for j,n in enumerate(numbers):
            typ = 'power_in' if n in (3,4) else 'open_collector' if n==12 else 'output' if n==5 else 'input'
            pins.append((n,pin_names[n],side*20.32,30.48-j*10.16,0 if side<0 else 180,typ))
    pins += [(11,'GND',-5.08,-55.88,90,'power_in'),(17,'EP',5.08,-55.88,90,'power_in')]
    bp=[(1,'NC',-5.08,15.24,270,'no_connect'),(2,'A',-10.16,0,0,'input'),
        (3,'GND',0,-10.16,90,'power_in'),(4,'Y',10.16,0,180,'output'),(5,'VCC',0,10.16,270,'power_in')]
    pp=[(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')]
    fp=[(1,'pwr',0,0,90,'power_out')]
    lib=[symbol('LTC2962HUD',pins,'(rectangle (start -17.78 38.1) (end 17.78 -50.8) (stroke (width 0.254) (type default)) (fill (type background)))'),
         symbol('LVC1G17',bp,'(polyline (pts (xy -7.62 5.08) (xy -7.62 -5.08) (xy 7.62 0) (xy -7.62 5.08)) (stroke (width 0.254) (type default)) (fill (type none)))'),
         symbol('R',pp,'(rectangle (start -1.016 2.54) (end 1.016 -2.54) (stroke (width 0.254) (type default)) (fill (type none)))','R'),
         symbol('C',pp,'(polyline (pts (xy -2.54 0.762) (xy 2.54 0.762)) (stroke (width 0.3) (type default)) (fill (type none))) (polyline (pts (xy -2.54 -0.762) (xy 2.54 -0.762)) (stroke (width 0.3) (type default)) (fill (type none))) (polyline (pts (xy 0 2.54) (xy 0 0.762)) (stroke (width 0.254) (type default)) (fill (type none))) (polyline (pts (xy 0 -0.762) (xy 0 -2.54)) (stroke (width 0.254) (type default)) (fill (type none)))','C'),
         symbol('PWR_FLAG',fp,'','#FLG')]
    cp={}
    for count in (5,7):
        cp[count]=[(n,str(n),-5.08,-(n-1)*5.08,0,'passive') for n in range(1,count+1)]
        lib.append(symbol('Conn'+str(count),cp[count],f'(rectangle (start -2.54 2.54) (end 2.54 {-count*5.08}) (stroke (width 0.254) (type default)) (fill (type background)))','J'))
    items=[]; positions={}; parts={}; netmap={}

    def place(name,ref,value,x,y,pinlist,foot='',mpn=''):
        positions[ref]={str(n):(round(x+px,4),round(y-py,4)) for n,_,px,py,_,_ in pinlist}
        rx,ry,vy=(x+3.81,y-2.54,y+1.27) if name in ('R','C') else (x,y-5.08,y-2.54)
        e=effects(.95,'(justify left)') if name in ('R','C') else effects(1)
        if name=='LVC1G17':rx,ry,vy,e=x+15.24,y-7.62,y-5.08,effects(.95,'(justify left)')
        props=f'(property "Reference" {quote(ref)} (at {rx} {ry} 0) {e})(property "Value" {quote(value)} (at {rx} {vy} 0) {e})(property "Footprint" {quote(foot)} (at {x} {y} 0) {effects(extra="hide")})(property "MPN" {quote(mpn)} (at {x} {y} 0) {effects(extra="hide")})'
        items.append(f'(symbol(lib_id "CNC:{name}")(at {x} {y} 0)(unit 1)(in_bom {"no" if ref.startswith("#") else "yes"})(on_board {"no" if ref.startswith("#") else "yes"})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "power_sequence"(path "/{root_id}"(reference {quote(ref)})(unit 1)))))')
        if not ref.startswith('#'):parts[ref]={'value':value,'mpn':mpn,'footprint':foot}

    def label(ref,pin,net,dx=0,dy=0):
        x,y=positions[ref][str(pin)];ex,ey=round(x+dx,4),round(y+dy,4)
        if dx or dy:items.append(f'(wire(pts(xy {x} {y})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(pin)+"w")}"))')
        items.append(f'(label {quote(net)} (at {ex} {ey} 0) {effects(.9,"(justify left bottom)")}(uuid "{uid(ref+str(pin)+"l")}"))')
        if not ref.startswith('#'):netmap.setdefault(net,[]).append([ref,str(pin)])

    def note(x,y,text,size=1.1):items.append(f'(text {quote(text)}(at {x} {y} 0){effects(size,"(justify left top)")}(uuid "{uid(text)}"))')

    def res(ref,value,top,bottom,x,y,mpn):
        place('R',ref,value,x,y,pp,'Resistor_SMD:R_0603_1608Metric',mpn)
        label(ref,1,top,dy=-5.08);label(ref,2,bottom,dy=5.08)

    def cap(ref,rail,x,y):
        place('C',ref,'100nF 25V X7R 20%',x,y,pp,'Capacitor_SMD:C_0603_1608Metric')
        label(ref,1,rail,dy=-5.08);label(ref,2,'LOGIC_GND',dy=5.08)

    rails=['CORE_5V','CORE_1V2','IO_3V3','ESP_3V3']
    mr=['CORE_5V','SEQ_5V_OK','IO_3V3_EN','SEQ_5V_OK']
    rst=['SEQ_5V_OK','IO_3V3_EN','SEQ_FPGA_RESET_GOOD','SEQ_ESP_RESET_GOOD']
    ladders=[([('87.9k',87900,'8792')],[('92.1k',92100,'9212')],10000,'1002'),
             ([('1.10k',1100,'1101'),('255',255,'2550')],[('1.15k',1150,'1151'),('294',294,'2940'),('1',1,None)],1000,'1001'),
             ([('54.5k',54500,'5452')],[('57.5k',57500,'5752')],10000,'1002'),
             ([('54.5k',54500,'5452')],[('57.5k',57500,'5752')],10000,'1002')]
    models=[]
    for i,rail in enumerate(rails):
        ox=(i%2)*406.4;oy=(i//2)*218.44;u=f'U{i+1}';x=ox+241.3;y=oy+114.3
        place('LTC2962HUD',u,'LTC2962HUD#TRPBF',x,y,pins,'CNC_Power:LTC2962_UD16','LTC2962HUD#TRPBF')
        pnet={1:'CORE_5V',2:mr[i],3:'LOGIC_GND',4:'CORE_5V',5:f'SEQ_REF{i+1}',6:f'SEQ_REF{i+1}',7:'LOGIC_GND',8:f'SEQ_REF{i+1}',9:f'SEQ_REF{i+1}',10:'CORE_5V',11:'LOGIC_GND',12:rst[i],13:'CORE_5V',14:'CORE_5V',15:f'{rail}_OV_SENSE',16:f'{rail}_UV_SENSE',17:'LOGIC_GND'}
        for pin,net in pnet.items():label(u,pin,net,dx=-55.88 if pin in left else 7.62 if pin in right else 0,dy=5.08 if pin in (11,17) else 0)
        # Separate dividers avoid correlated sense-bias assumptions.
        lows,highs,rb,code=ladders[i]
        row={'rail':rail,'uv_top_ohm':sum(v for _,v,_ in lows),'ov_top_ohm':sum(v for _,v,_ in highs),'bottom_ohm':rb,'uv_series':[],'ov_series':[]}
        for j,chain in enumerate((lows,highs)):
            prefix='UV' if j==0 else 'OV';sense=f'{rail}_{prefix}_SENSE';xx=ox+35.56+j*60.96
            for k,(val,ohm,c) in enumerate(chain):
                rr=f'R{i*20+j*8+k+1}';top=rail if k==0 else f'SEQ_{prefix}{i+1}_{k}'
                bottom=sense if k==len(chain)-1 else f'SEQ_{prefix}{i+1}_{k+1}'
                mpn='PLT0603Z'+c+'LST1' if c else 'CRCW06031R00FKEA'
                res(rr,val+(' 0.01% 5ppm' if c else ' 1% 100ppm'),top,bottom,xx,oy+58.42+k*30.48,mpn)
                row[prefix.lower()+'_series'].append({'reference':rr,'ohm':ohm,'initial_fraction':.0001 if c else .01,'tcr_ppm':5 if c else 100})
            rr=f'R{i*20+j*8+7}';res(rr,f'{rb/1000:g}k 0.01% 5ppm',sense,'LOGIC_GND',xx,oy+180.34,'PLT0603Z'+code+'LST1')
        models.append(row)
        cap(f'C{i+1}','CORE_5V',ox+157.48,oy+50.8)
        note(ox+20.32,oy+30.48,f'{i+1}. {rail} window / autonomous release',1.8)
        note(ox+157.48,oy+194.31,'PG1=REF: UV; PG2=GND: OV. Unused V3/V4=VCC, PG3/4=REF.\nRT=VCC: 160-240ms release. RDIS=VCC: margin override disabled.',1.0)
    # First qualifier fans out through resistors; each output has an on-sheet pulldown.
    res('R101','3.3k 1%','CORE_5V','SEQ_5V_OK',345.44,58.42,'CRCW06033K30FKEA')
    for rr,net,xx in ((102,'CORE_1V2_EN',320.04),(104,'ESP_3V3_EN',370.84)):
        res(f'R{rr}','3.3k 1%','SEQ_5V_OK',net,xx,101.6,'CRCW06033K30FKEA')
        res(f'R{rr+1}','10k 1%',net,'LOGIC_GND',xx,137.16,'CRCW060310K0FKEA')
    res('R106','6.8k 1%','CORE_5V','IO_3V3_EN',746.76,58.42,'CRCW06036K80FKEA')
    res('R107','10k 1%','IO_3V3_EN','LOGIC_GND',746.76,104.14,'CRCW060310K0FKEA')
    for i,(rail,qual,out) in enumerate((('IO_3V3','SEQ_FPGA_RESET_GOOD','FPGA_CRESET_N'),('ESP_3V3','SEQ_ESP_RESET_GOOD','ESP_CHIP_PU'))):
        xx=320.04+i*406.4;yy=284.48
        res(f'R{108+i*3}','47k 1%','CORE_5V',qual,xx,yy,'CRCW060347K0FKEA')
        res(f'R{109+i*3}','470k 1%',qual,'LOGIC_GND',xx,yy+35.56,'CRCW0603470KFKEA')
        u=f'U{i+5}';place('LVC1G17',u,'SN74LVC1G17DBVR',xx+38.1,yy+73.66,bp,'Package_TO_SOT_SMD:SOT-23-5','SN74LVC1G17DBVR')
        for p,n in {2:qual,3:'LOGIC_GND',4:out,5:rail}.items():label(u,p,n,dx=-45.72 if p==2 else 5.08 if p==4 else 0,dy=-7.62 if p==5 else 5.08 if p==3 else 0)
        px,py=positions[u]['1'];items.append(f'(no_connect(at {px} {py})(uuid "{uid(u+"nc")}"))')
        # ESP VIH is0.75*VDD; <100uA load uses the buffer VCC-0.1V VOH guarantee.
        res(f'R{110+i*3}','4.7k 1%' if not i else '47k 1%',out,'LOGIC_GND',xx+43.18,yy+119.38,
            'CRCW06034K70FKEA' if not i else 'CRCW060347K0FKEA')
        cap(f'C{i+5}',rail,xx-10.16,yy+119.38)
    boundary={'JRAIL1':['CORE_5V','CORE_1V2','IO_3V3','ESP_3V3','LOGIC_GND'],
              'JCTRL1':['CORE_1V2_EN','IO_3V3_EN','ESP_3V3_EN','FPGA_CRESET_N','ESP_CHIP_PU','SEQ_5V_OK','LOGIC_GND']}
    for ref,xx,yy in [('JRAIL1',132.08,482.6),('JCTRL1',299.72,482.6)]:
        nets=boundary[ref];place('Conn'+str(len(nets)),ref,'INTEGRATION BOUNDARY',xx,yy,cp[len(nets)])
        for n,net in enumerate(nets,1):label(ref,n,net,dx=-58.42)
    for i,net in enumerate(('CORE_5V','LOGIC_GND','IO_3V3','ESP_3V3')):
        ref=f'#FLG{i+1}';place('PWR_FLAG',ref,'EXTERNAL',45.72+i*63.5,551.18,fp);label(ref,1,net,dy=5.08)
    note(20.32,12.7,'AUTONOMOUS POWER WINDOW / RESET CANDIDATE - NOT MACHINE PERMISSION',2.3)
    note(370.84,477.52,'CORE5 -> core + ESP enables; valid core -> IO enable. IO qualifier -> FPGA reset.\nESP qualifier -> ESP reset only: ESP fault does not reset FPGA through this circuit.\nEvery EN also has the existing regulator10k pulldown. No active-high external driver allowed.\n5V/internal pullups never directly drive destination reset pins. Schmitt buffers use destination rails.',1.15)
    note(370.84,510.54,'Core threshold static margins are sub-mV at some corners. Aging, stress, ripple and transient\nresponse remain release blockers. Comparator40us maximum applies only at10% overdrive.\nNo guaranteed brownout slew, powered-off regulator discharge, shutdown order or restart latch.\nFPGA package/PLL filters, configuration, CDONE/user-mode guard and machine inhibit remain external.\nFour precision supervisors are a COST-RISK CANDIDATE, not a production BOM choice.',1.15)
    sch=f'(kicad_sch(version 20250114)(generator "eeschema")(uuid "{root_id}")(paper "A1")(title_block(title "Autonomous rail qualification and reset")(date "2026-09-28")(rev "r0.1")(comment 1 "Engineering candidate; no PCB or physical validation"))(lib_symbols {"".join(lib)})'+''.join(items)+')\n'
    (OUT/'power_sequence.kicad_sch').write_text(sch,encoding='utf-8')
    libtext='\n'.join(s.replace('(symbol "CNC:', '(symbol "',1) for s in lib)
    (OUT/'CNC.kicad_sym').write_text('(kicad_symbol_lib(version 20241209)(generator "kicad_symbol_editor")'+libtext+')\n',encoding='utf-8')
    (OUT/'power_sequence.kicad_pro').write_text('{"meta":{"filename":"power_sequence.kicad_pro","version":1}}\n')
    (OUT/'sym-lib-table').write_text('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Autonomous power candidate")))\n')
    pads=[]
    for i in range(4):pads.append((i+1,-1.4,-.75+i*.5,.7,.25))
    for i in range(4):pads.append((i+5,-.75+i*.5,1.4,.25,.7))
    for i in range(4):pads.append((i+9,1.4,.75-i*.5,.7,.25))
    for i in range(4):pads.append((i+13,.75-i*.5,-1.4,.25,.7))
    pads.append((17,0,0,1.45,1.45))
    (OUT/'CNC_Power.pretty').mkdir(exist_ok=True)
    (OUT/'CNC_Power.pretty/LTC2962_UD16.kicad_mod').write_text(footprint('LTC2962_UD16',(3,3),pads))
    (OUT/'fp-lib-table').write_text('(fp_lib_table(version 7)(lib(name "CNC_Power")(type "KiCad")(uri "${KIPRJMOD}/CNC_Power.pretty")(options "")(descr "ADI UD16 land pattern candidate")))\n')
    envelope={'schema_version':1,'manufacturing_ready':False,'candidate_not_production_selection':True,
              'parts':parts,'pin_map':{str(k):v for k,v in pin_names.items()},'boundary':boundary,
              'windows':models,'monitor_reference_v':[.4975,.5025],'monitor_input_bias_a':15e-9,
              'resistor_temperature_excursion_c':100,'fixed_delay_ms':[160,240],
              'additional_core5_reservation_a':.010,'additional_core5_cap_max_uf':.552,
              'source_ledger_sha256':hashlib.sha256((OUT/'input-electrical-design.json').read_bytes()).hexdigest(),
              'unproven':['aging_and_assembly_stress','ripple_and_load_transients','brownout_slew_and_filter_delay','arbitrary_partial_power','shutdown_order','FPGA_package_supply_mapping','machine_permission','physical_qualification','production_cost']}
    (OUT/'design-envelope.json').write_text(json.dumps(envelope,indent=2)+'\n')
    (OUT/'pin-map.json').write_text(json.dumps({k:sorted(v) for k,v in sorted(netmap.items())},indent=2)+'\n')
    # Canonical expression formatting also allows KiCad to identify library-table types.
    for path in (OUT/'power_sequence.kicad_sch',OUT/'CNC.kicad_sym',OUT/'sym-lib-table',OUT/'fp-lib-table'):
        tokens=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',path.read_text(encoding='utf-8'))
        stack=[];tree=None
        for token in tokens:
            if token=='(':
                node=[]
                if stack:stack[-1].append(node)
                else:tree=node
                stack.append(node)
            elif token==')':stack.pop()
            else:stack[-1].append(token)
        def dump(n):return '('+' '.join(dump(x) if isinstance(x,list) else x for x in n)+')'
        path.write_text(dump(tree)+'\n',encoding='utf-8')
    print(OUT/'power_sequence.kicad_sch')


if __name__=='__main__':main()
