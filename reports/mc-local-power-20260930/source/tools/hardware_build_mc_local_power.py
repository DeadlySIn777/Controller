"""Source-backed MC local power candidate; not a manufacturing release.

Preserves the old central-power source. Exact schematic boundaries are review
symbols, never fabricated connectors. IS-1 TPS386000 deviation is an IS-2 proposal.
"""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import uuid

from hardware_build_tx_schematic import effects, quote, symbol
from hardware_build_assembly import parse, dump

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/mc_local_power'
NS = uuid.UUID('89c52a4d-c6b6-4492-9731-a770a4d8acb5')


def build(out=OUT):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    uid = lambda name: str(uuid.uuid5(NS, name))
    root = uid('root')
    two = [(1, '', 0, 5.08, 270, 'passive'), (2, '', 0, -5.08, 90, 'passive')]
    reg = [(1, 'PG', 20.32, 15.24, 180, 'open_collector'), (2, 'SW', 20.32, 25.4, 180, 'power_out'),
           (3, 'VOS', 20.32, 5.08, 180, 'input'), (4, 'GND', 0, -40.64, 90, 'power_in'),
           (5, 'EN', -20.32, 15.24, 0, 'input'), (6, 'VIN', -20.32, 25.4, 0, 'power_in'),
           (7, 'MODE/S-CONF', -20.32, 0, 0, 'input'), (8, 'SS/TR', -20.32, -15.24, 0, 'input'),
           (9, 'FB/VSET', 20.32, -15.24, 180, 'input')]
    names = {1:'RDIS',2:'MR',3:'DVCC',4:'VCC',5:'REF',6:'PG1',7:'PG2',8:'PG3',9:'PG4',
             10:'RT',11:'GND',12:'RST',13:'V4',14:'V3',15:'V2',16:'V1',17:'EP'}
    left, right = [4,16,15,14,13,2,1,3], [12,5,6,7,8,9,10]
    sup=[]
    for side, nums in ((-1,left),(1,right)):
        for index,n in enumerate(nums):
            typ='power_in' if n in (3,4) else 'open_collector' if n==12 else 'output' if n==5 else 'input'
            sup.append((n,names[n],side*20.32,30.48-index*10.16,0 if side<0 else 180,typ))
    sup += [(11,'GND',-5.08,-55.88,90,'power_in'),(17,'EP',5.08,-55.88,90,'power_in')]
    buf=[(1,'NC',-5.08,15.24,270,'no_connect'),(2,'A',-10.16,0,0,'input'),
         (3,'GND',0,-10.16,90,'power_in'),(4,'Y',10.16,0,180,'output'),(5,'VCC',0,10.16,270,'power_in')]
    pins={'TPS62901RPJR':reg,'LTC2962HUD':sup,'LVC1G17':buf,'R':two,'C':two,
          'L':[(1,'',-5.08,0,0,'passive'),(2,'',5.08,0,180,'passive')],
          'INTERNAL_REVIEW_BOUNDARY':[(i,str(i),-5.08,-(i-1)*5.08,0,'passive') for i in range(1,10)],
          'PWR_FLAG':[(1,'pwr',0,0,90,'power_out')]}
    rect=lambda y1,y2:f'(rectangle(start -17.78 {y1})(end 17.78 {y2})(stroke(width .254)(type default))(fill(type background)))'
    shape={'TPS62901RPJR':rect(30.48,-35.56),'LTC2962HUD':rect(38.1,-50.8),
           'LVC1G17':'(polyline(pts(xy -7.62 5.08)(xy -7.62 -5.08)(xy 7.62 0)(xy -7.62 5.08))(stroke(width .254)(type default))(fill(type none)))',
           'R':'(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))',
           'C':'(polyline(pts(xy -2.54 .762)(xy 2.54 .762))(stroke(width .3)(type default))(fill(type none))) (polyline(pts(xy -2.54 -.762)(xy 2.54 -.762))(stroke(width .3)(type default))(fill(type none))) (polyline(pts(xy 0 2.54)(xy 0 .762))(stroke(width .254)(type default))(fill(type none))) (polyline(pts(xy 0 -.762)(xy 0 -2.54))(stroke(width .254)(type default))(fill(type none)))',
           'L':'(rectangle(start -2.54 1.27)(end 2.54 -1.27)(stroke(width .254)(type default))(fill(type none)))',
           'INTERNAL_REVIEW_BOUNDARY':'(rectangle(start -2.54 2.54)(end 2.54 -45.72)(stroke(width .254)(type default))(fill(type background)))','PWR_FLAG':''}
    library=[symbol(n,p,shape[n],'R' if n=='R' else 'C' if n=='C' else 'L' if n=='L' else 'B' if n=='INTERNAL_REVIEW_BOUNDARY' else '#FLG' if n=='PWR_FLAG' else 'U') for n,p in pins.items()]
    items=[]; positions={}; components={}; nets={}
    def place(name,ref,value,x,y,mpn='',fp='',physical=True):
        positions[ref]={str(n):(round(x+px,4),round(y-py,4)) for n,_,px,py,_,_ in pins[name]}
        passive=name in ('R','C','L'); rx,ry,vy=(x+3.81,y-2.54,y+1.27) if passive else (x,y-48.26,y-44.45)
        style=effects(.95,'(justify left)') if passive else effects(1.1,'hide' if ref.startswith('#') else '')
        if name=='LVC1G17':rx,ry,vy,style=x+15.24,y-7.62,y-3.81,effects(.95,'(justify left)')
        if name=='INTERNAL_REVIEW_BOUNDARY':rx,ry,vy,style=x+10.16,y-7.62,y-3.81,effects(.95,'(justify left)')
        props=f'(property "Reference" {quote(ref)}(at {rx} {ry} 0){style})(property "Value" {quote(value)}(at {rx} {vy} 0){style})'
        props+=f'(property "MPN" {quote(mpn)}(at {x} {y} 0){effects(extra="hide")})(property "Footprint" {quote(fp)}(at {x} {y} 0){effects(extra="hide")})'
        items.append(f'(symbol(lib_id "CNC:{name}")(at {x} {y} 0)(unit 1)(in_bom {"yes" if physical else "no"})(on_board {"yes" if physical else "no"})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "mc_local_power"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
        if not ref.startswith('#'):components[ref]={'value':value,'mpn':mpn,'footprint':fp,'physical':physical,'pins':{},'no_connect':[],'status':'candidate_not_qualified'}
    def label(ref,pin,net,dx=0,dy=0):
        x,y=positions[ref][str(pin)];ex,ey=round(x+dx,4),round(y+dy,4)
        if dx or dy:items.append(f'(wire(pts(xy {x} {y})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(pin)+"w")}"))')
        items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.85,"(justify left bottom)")}(uuid "{uid(ref+str(pin)+"l")}"))')
        if ref in components:components[ref]['pins'][str(pin)]=net;nets.setdefault(net,[]).append([ref,str(pin)])
    def resistor(ref,value,mpn,a,b,x,y):
        place('R',ref,value,x,y,mpn,'Resistor_SMD:R_0603_1608Metric');label(ref,1,a,dy=-5.08);label(ref,2,b,dy=5.08)
    def capacitor(ref,value,mpn,a,x,y,fp='Capacitor_SMD:C_0603_1608Metric'):
        place('C',ref,value,x,y,mpn,fp);label(ref,1,a,dy=-5.08);label(ref,2,'LOGIC_GND',dy=5.08)
    def note(x,y,text,size=1.1):items.append(f'(text {quote(text)}(at {x} {y} 0){effects(size,"(justify left top)")}(uuid "{uid(text)}"))')
    rails=[('CORE_1V2',1.2,.8,76800,'76.8k','76K8','2.2uH','XGL4020-222MEC'),
           ('IO_3V3',3.3,.15,32400,'32.4k','32K4','1uH','XGL4020-102MEC')]
    for i,(rail,voltage,load,mode,value,code,ind,indmpn) in enumerate(rails):
        ox=i*406.4;u=f'U{i+1}';place('TPS62901RPJR',u,'TPS62901RPJR',ox+147.32,104.14,'TPS62901RPJR','CNC_MC_Power:TPS62901_RPJ9')
        pnet={1:rail+'_PG_OD',2:rail+'_SW',3:rail,4:'LOGIC_GND',5:rail+'_EN',6:'CORE_5V',7:rail+'_MODE',8:rail+'_SS',9:'LOGIC_GND' if not i else rail+'_VSET'}
        for pin,net in pnet.items():label(u,pin,net,dx=-40.64 if pin in (5,6,7,8) else 10.16 if pin!=4 else 0,dy=5.08 if pin==4 else 0)
        l=f'L{i+1}';place('L',l,ind,ox+218.44,60.96,indmpn,'CNC_MC_Power:XGL4020');label(l,1,rail+'_SW',dx=-20.32);label(l,2,rail,dx=5.08)
        r=i*4
        resistor(f'R{r+1}',value+' 1%','CRCW0603'+code+'FKEA',rail+'_MODE','LOGIC_GND',ox+38.1,154.94)
        resistor(f'R{r+2}','10k 1%','CRCW060310K0FKEA',rail+'_EN','LOGIC_GND',ox+101.6,154.94)
        resistor(f'R{r+3}','100k 1%','CRCW0603100KFKEA',rail,'LOGIC_GND',ox+162.56,203.2)
        if i:resistor('R8','301k 1%','CRCW0603301KFKEA',rail+'_VSET','LOGIC_GND',ox+223.52,203.2)
        capacitor(f'C{i*3+1}','10uF 25V X7R 10%','C3216X7R1E106K160AB','CORE_5V',ox+38.1,63.5,'Capacitor_SMD:C_1206_3216Metric')
        capacitor(f'C{i*3+2}','22uF 10V X7S 20%','C2012X7S1A226M125AC',rail,ox+287.02,63.5,'Capacitor_SMD:C_0805_2012Metric')
        capacitor(f'C{i*3+3}','6.8nF 50V C0G 5%','GRM1885C1H682JA01D',rail+'_SS',ox+38.1,203.2)
        note(ox+20.32,22.86,f'{rail}: {voltage} V / {load} A reservation; {"1" if not i else "2.5"} MHz forced PWM',1.6)
    # Three precision window supervisors: 5 V -> core -> I/O -> reset.
    lows=((('87.9k',87900,'8792'),),(('1.07k',1070,'1071'),('261',261,'2610')),(('54.5k',54500,'5452'),))
    highs=((('92.1k',92100,'9212'),),(('1.15k',1150,'1151'),('316',316,'3160'),('4.02',4.02,None)),(('57.5k',57500,'5752'),))
    models=[]
    for i,rail in enumerate(('CORE_5V','CORE_1V2','IO_3V3')):
        ox=i*266.7;u=f'U{i+3}';place('LTC2962HUD',u,'LTC2962HUD#TRPBF',ox+177.8,335.28,'LTC2962HUD#TRPBF','CNC_MC_Power:LTC2962_UD16')
        mr=('CORE_5V','MC_SEQ_5V_OK','IO_3V3_EN')[i];rst=('MC_SEQ_5V_OK','IO_3V3_EN','MC_RAILS_OK_5V')[i];rn=f'MC_SEQ_REF{i+1}'
        pnet={1:'CORE_5V',2:mr,3:'LOGIC_GND',4:'CORE_5V',5:rn,6:rn,7:'LOGIC_GND',8:rn,9:rn,10:'CORE_5V',11:'LOGIC_GND',12:rst,13:'CORE_5V',14:'CORE_5V',15:rail+'_OV_SENSE',16:rail+'_UV_SENSE',17:'LOGIC_GND'}
        for pin,net in pnet.items():label(u,pin,net,dx=-40.64 if pin in left else 7.62 if pin in right else 0,dy=5.08 if pin in (11,17) else 0)
        rb,rbcode=(1000,'1001') if i==1 else (10000,'1002')
        row={'rail':rail,'uv_top_ohm':sum(r[1] for r in lows[i]),'ov_top_ohm':sum(r[1] for r in highs[i]),'bottom_ohm':rb,'uv_series':[],'ov_series':[]}
        for j,chain in enumerate((lows[i],highs[i])):
            prefix='UV' if j==0 else 'OV';sense=rail+'_'+prefix+'_SENSE';xx=ox+25.4+j*60.96
            for k,(value,ohm,code) in enumerate(chain):
                ref=f'R{i*20+21+j*8+k}';a=rail if not k else f'MC_SEQ_{prefix}{i+1}_{k}';b=sense if k==len(chain)-1 else f'MC_SEQ_{prefix}{i+1}_{k+1}'
                resistor(ref,value+(' 0.01% 5ppm' if code else ' 1% 100ppm'),'PLT0603Z'+code+'LST1' if code else 'CRCW06034R02FKEA',a,b,xx,259.08+k*30.48)
                row[prefix.lower()+'_series'].append({'reference':ref,'ohm':ohm,'initial_fraction':.0001 if code else .01,'tcr_ppm':5 if code else 100})
            resistor(f'R{i*20+27+j*8}',f'{rb/1000:g}k 0.01% 5ppm','PLT0603Z'+rbcode+'LST1',sense,'LOGIC_GND',xx,386.08)
        capacitor(f'C{i+7}','100nF 25V X7R 10%','GRM188R71E104KA01D','CORE_5V',ox+119.38,259.08)
        models.append(row)
    for ref,value,code,a,b,x,y in (
        ('R101','3.3k','3K30','CORE_5V','MC_SEQ_5V_OK',38.1,436.88),
        ('R102','3.3k','3K30','MC_SEQ_5V_OK','CORE_1V2_EN',101.6,436.88),
        ('R103','10k','10K0','CORE_1V2_EN','LOGIC_GND',162.56,436.88),
        ('R104','6.8k','6K80','CORE_5V','IO_3V3_EN',223.52,436.88),
        ('R105','10k','10K0','IO_3V3_EN','LOGIC_GND',284.48,436.88),
        ('R106','47k','47K0','CORE_5V','MC_RAILS_OK_5V',345.44,436.88),
        ('R107','470k','470K','MC_RAILS_OK_5V','LOGIC_GND',406.4,436.88),
        ('R108','4.7k','4K70','FPGA_CRESET_N','LOGIC_GND',579.12,436.88)):
        resistor(ref,value+' 1%','CRCW0603'+code+'FKEA',a,b,x,y)
    place('LVC1G17','U6','SN74LVC1G17DBVR',508,434.34,'SN74LVC1G17DBVR','Package_TO_SOT_SMD:SOT-23-5')
    for pin,net in {2:'MC_RAILS_OK_5V',3:'LOGIC_GND',4:'FPGA_CRESET_N',5:'IO_3V3'}.items():label('U6',pin,net,dx=-20.32 if pin==2 else 5.08 if pin==4 else 0,dy=-7.62 if pin==5 else 5.08 if pin==3 else 0)
    nx,ny=positions['U6']['1'];items.append(f'(no_connect(at {nx} {ny})(uuid "{uid("U6NC")}"))');components['U6']['no_connect']=['1']
    capacitor('C10','100nF 25V X7R 10%','GRM188R71E104KA01D','IO_3V3',660.4,436.88)
    boundary=['CORE_5V','LOGIC_GND','CORE_1V2','IO_3V3','FPGA_CRESET_N','MC_RAILS_OK_5V','CORE_1V2_PG_OD','IO_3V3_PG_OD','LOGIC_GND']
    place('INTERNAL_REVIEW_BOUNDARY','B1','MC POWER REVIEW BOUNDARY',152.4,492.76,physical=False)
    for pin,net in enumerate(boundary,1):label('B1',pin,net,dx=-66.04)
    for i,net in enumerate(('CORE_5V','LOGIC_GND','CORE_1V2','IO_3V3')):
        ref=f'#FLG{i+1}';place('PWR_FLAG',ref,'EXTERNAL' if i<2 else 'REGULATED OUTPUT AFTER L',45.72+i*63.5,566.42,physical=False);label(ref,1,net,dy=5.08)
    note(20.32,12.7,'MC LOCAL POWER - IS-2 HARDWARE PROPOSAL / NOT MANUFACTURING READY',2)
    note(223.52,497.84,'5 V window releases core; core window releases IO; IO window releases FPGA reset.\nEach supervisor release: 160-240 ms. Raw MC_RAILS_OK_5V is not a 3.3 V signal.\nFPGA_CRESET_N is the buffered rails-good term; combine other reset requests upstream.\nRegulator PG pins are diagnostic only; no PG-to-EN cascade. Physical connector is external.',1.2)
    note(223.52,533.4,'Actual rail limits retained: 5 V 4.85-5.15; T20 core 1.15-1.25; IO 3.20-3.40 V.\nCore thresholds include initial/temp plus 400ppm drift; historical tight ledger is distinct.\nIO uses 2.5 MHz because existing FPGA decoupling exceeds the 1 MHz capacitance limit.\nProposed MC slot: 0.50 A steady / 0.80 A downstream startup; input charging separate.\nArbitrary partial power, assembled stress, brownout slew, shutdown and timing unproved.',1.15)
    text=f'(kicad_sch(version 20250114)(generator "eeschema")(uuid "{root}")(paper "A1")(title_block(title "MC local regulators and independent window sequencing")(date "2026-09-30")(rev "r0.1 / IS-2 proposal"))(lib_symbols {"".join(library)})'+''.join(items)+')\n'
    (out/'mc_local_power.kicad_sch').write_text(dump(parse(text))+'\n',encoding='utf-8')
    (out/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "kicad_symbol_editor")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in library)+')'))+'\n',encoding='utf-8')
    (out/'mc_local_power.kicad_pro').write_text('{"meta":{"filename":"mc_local_power.kicad_pro","version":1}}\n',encoding='utf-8')
    (out/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "MC local source review")))'))+'\n',encoding='utf-8')
    pretty=out/'CNC_MC_Power.pretty';pretty.mkdir(exist_ok=True)
    for source,name in (('logic_power','TPS62901_RPJ9'),('logic_power','XGL4020'),('power_sequence','LTC2962_UD16')):
        shutil.copyfile(ROOT/f'hardware/{source}/CNC_Power.pretty/{name}.kicad_mod',pretty/(name+'.kicad_mod'))
    (out/'fp-lib-table').write_text(dump(parse('(fp_lib_table(version 7)(lib(name "CNC_MC_Power")(type "KiCad")(uri "${KIPRJMOD}/CNC_MC_Power.pretty")(options "")(descr "Sourced copper land-pattern candidates")))'))+'\n',encoding='utf-8')
    source_paths=['hardware/logic_power/design-envelope.json','hardware/logic_power/input-electrical-design.json','hardware/power_sequence/design-envelope.json','hardware/fpga_core/design.json',
                  'research/logic-power/tps62901.pdf','research/logic-power/xgl4020.pdf','research/logic-power/softstart-cap.pdf','research/power-sequence/SOURCES.md',
                  'research/mc-local-power/sn74lvc1g17.pdf','research/mc-local-power/vishay-plt.pdf','research/mc-local-power/SOURCES.md']
    source_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_paths}
    design={'schema_version':1,'revision':'mc-local-power-r0.1','status':'review_candidate','manufacturing_ready':False,'specification':'IS-2 hardware proposal; frozen IS-1 unchanged',
            'component_deviation':{'IS-1':'TPS386000','proposed':'LTC2962HUD#TRPBF x3','reason':'Preserve narrow guaranteed rail windows; TPS386000 full corners do not close them.'},
            'components':components,'nets':{n:sorted(v) for n,v in sorted(nets.items())},'boundary':{'B1':boundary},
            'windows':models,'rail_limits_v':{'CORE_5V':[4.85,5.15],'CORE_1V2':[1.15,1.25],'IO_3V3':[3.2,3.4]},
            'threshold_deviation':{'historical_tight_ledger_core_v':[1.17,1.23],'actual_T20_core_v':[1.15,1.25],'core_UV_top_ohm':1331,'core_OV_top_ohm':1470.02,'bottom_ohm':1000,'additional_drift_fraction':.0004,'reason':'Inset thresholds within actual Efinix operating limits while avoiding historical sub-mV false-trip and aging margins.'},
            'regulation_only_v':{'CORE_5V':[4.95,5.05],'CORE_1V2':[1.185,1.215],'IO_3V3':[3.25875,3.34125]},
            'load_reservations_a':{'CORE_1V2':.8,'IO_3V3':.15,'CORE_5V_steady_slot':.5,'IS1_steady_slot':.45,'additional_supervision_input':.01},
            'slot_power_deviation':{'IS-1_steady_a':.45,'IS-2_proposed_steady_a':.5,'IS-2_proposed_startup_allowance_a':.8,'reason':'Count both converter reservations, overhead and complete decoupling; input-cap charging separately.'},
            'rail_capacitor_limits':{'CORE_1V2':{'effective_max_uf':50,'additional_nominal_load_budget_uf':2},'IO_3V3':{'effective_max_uf':100,'additional_nominal_load_budget_uf':10}},
            'release_delay_ms':[160,240],'source_sha256':source_hashes,'physical_qualification':False,
            'reset_boundary_contract':{'destination':'3.3 V logic inputs; existing FPGA core reset-AND input','external_high_load_max_a':.001,'external_low_load_max_a':.0001,'external_pushpull_driver_allowed':False,'raw_5v_qualifier_may_drive_FPGA':False},
            'unproven':['FPGA_load_reservations','dynamic_regulation_and_thermal','minimum_effective_capacitance_DC_bias','arbitrary_partial_power','shutdown_order_and_discharge','brownout_detection_delay_and_slew','precision_resistor_lifetime_drift','connector_and_slot_limiter','machine_permission','logic_owner_IS2_agreement','physical_qualification','production_cost']}
    (out/'design.json').write_text(json.dumps(design,indent=2)+'\n',encoding='utf-8')
    (out/'pin-map.json').write_text(json.dumps(design['nets'],indent=2)+'\n',encoding='utf-8')
    with (out/'bom.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f);writer.writerow(['Reference','Value','MPN','Footprint','Status'])
        for ref,c in components.items():
            if c['physical']:writer.writerow([ref,c['value'],c['mpn'],c['footprint'],c['status']])
    print(out/'mc_local_power.kicad_sch')


if __name__=='__main__':build()
