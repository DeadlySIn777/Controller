"""Complete, source-owned capacitor function ledger; no hardware mutation.

An owner is selected from the frozen generator/function declaration, then its
actual native pins are checked. Sharing a supply rail never selects an owner.
Timing, reference, field-filter and AC coupling rows are not VDD bypass rows.
"""
import argparse,collections,json,re,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);args=ap.parse_args();out=args.out.resolve();assert not out.exists();out.mkdir(parents=True)
source=ROOT/'reports/motherboard-integration-20260930/r23-2688-reset-bypass-staged'
model_path=source/'design.json';xml_path=source/'netlist.xml';model=json.loads(model_path.read_text())['components'];tree=ET.parse(xml_path)
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
inputs={str(f):sha(f)for f in [model_path,xml_path,Path(__file__)]}
nodes={(z.attrib['ref'],z.attrib['pin']):n.attrib['name']for n in tree.findall('.//nets/net')for z in n.findall('node')}
libs={(x.attrib['lib'],x.attrib['part']):{z.attrib['num']:dict(z.attrib)for z in x.findall('./pins/pin')}for x in tree.findall('.//libparts/libpart')}
functions={x.attrib['ref']:libs[x.find('libsource').attrib['lib'],x.find('libsource').attrib['part']]for x in tree.findall('.//components/comp')}
caps={r:c for r,c in model.items()if r.startswith('C')};assert len(caps)==723
rows={};pending={}
def own(ref,owner,pins,returns,category,evidence,target=2.,return_ref=None,path=None):
    assert ref not in rows,ref
    if isinstance(pins,str):pins=[pins]
    if isinstance(returns,str):returns=[returns]
    pnodes=[dict(ref=owner,pin=str(k))for k in pins]
    rnodes=[dict(ref=return_ref or owner,pin=str(k))for k in returns]
    row=dict(ref=ref,owner=owner,cap_power='1',cap_return='2',power_nodes=pnodes,return_nodes=rnodes,target=target,category=category,evidence=evidence,reviewed_series_path=path or [])
    rows[ref]=row;pending.pop(ref,None)
def pins_same(ref,net,types=None):
    return [pin for pin,f in functions[ref].items()if nodes.get((ref,pin))==net and (types is None or f['type']in types)]
def return_pins(owner,ref):
    n=nodes[(ref,'2')];return [k for k,v in functions[owner].items()if nodes.get((owner,k))==n and (v['type'].startswith('power')or re.search(r'GND|VSS|V-|EP|RETURN|COM',v['name']))]
def named_supply(ref,owner,role=None):
    role=role if role is not None else caps[ref].get('role','');n=nodes[(ref,'1')]
    candidates=[k for k,v in functions[owner].items()if nodes.get((owner,k))==n and v['type'].startswith('power')and not re.search(r'GND|VSS|V-|EP',v['name'])]
    if re.search(r'VREF|reference',role,re.I):candidates=[k for k in candidates if 'VREF'in functions[owner][k]['name']]
    elif 'VDD'in role or 'MCU'in role:candidates=[k for k in candidates if 'VDD'in functions[owner][k]['name']]
    elif 'output'in role.lower():
        a=[k for k in candidates if functions[owner][k]['type']=='power_out'];candidates=a or candidates
    elif 'input'in role.lower():
        a=[k for k in candidates if functions[owner][k]['type']=='power_in'];candidates=a or candidates
    # Multi-lead same physical VS/power pin is one functional owner. Different
    # names (e.g MCU VBAT/VREF/VDD) must be explicitly distinguished.
    names={functions[owner][k]['name']for k in candidates}
    if len(names)!=1:pending[ref]=dict(reason='Named functional owner has ambiguous/non-power signal pin',owner=owner,candidates=candidates,role=role);return
    ret=return_pins(owner,ref)
    if not ret:pending[ref]=dict(reason='Named owner has no matching own-domain native return',owner=owner);return
    category='reference_bypass'if re.search('VREF|reference',role,re.I)else 'local_reservoir'if re.search('bulk|storage|reservoir|stabilizer',role,re.I)else 'output_bypass'if 'output'in role.lower()else 'supply_bypass'
    own(ref,owner,candidates,ret,category,'Frozen source component role/decouples declaration names this owner; exact native function and own return checked.',target=5. if category=='local_reservoir'else 2.)

# Existing exact336 source-reviewed rows, preserving reference ESR paths.
old_path=ROOT/'reports/motherboard-bypass-owners-20260930/actual-r24f-r03/owner-distances.json';inputs[str(old_path)]=sha(old_path)
for r in json.loads(old_path.read_text())['rows']:
    rows[r['ref']]={k:r[k]for k in ['ref','owner','cap_power','cap_return','power_nodes','return_nodes','target','category']}
    rows[r['ref']]['evidence']=r['manifest'];rows[r['ref']]['reviewed_series_path']=r.get('reviewed_series_path',[])

# FPGA caps: exact placement ball/bank from reviewed Efinix-derived source.
cols='ABCDEFGHJKLMNRT'
def ball_xy(ball):return cols.index(ball[0]),int(ball[1:])
fpga_ground=[k for k,v in functions['U1001'].items()if v['name']=='GND']
def adjacent_ground(power):
    result=set()
    for ball in power:
        x,y=ball_xy(ball);scores={g:abs(ball_xy(g)[0]-x)+abs(ball_xy(g)[1]-y)for g in fpga_ground};minimum=min(scores.values());result.update(g for g,v in scores.items()if v==minimum)
    return sorted(result)
for ref,c in caps.items():
    if c.get('source_block')!='fpga_core':continue
    target=c['placement_target']
    if target in functions['U1001']:
        own(ref,'U1001',[target],adjacent_ground([target]),'FPGA_ball_bypass','Frozen placement_target identifies the actual powered package ball; matching native name and physically adjacent package GND balls checked.')
    elif target=='VCC cluster':
        pp=[k for k,v in functions['U1001'].items()if v['name']=='VCC'];own(ref,'U1001',pp,adjacent_ground(pp),'FPGA_core_reservoir','Frozen generator CORE VCC-cluster reservoir, not a VCCIO bank.',target=5.)
    elif 'VCCIO'+target in {v['name']for v in functions['U1001'].values()}:
        pp=[k for k,v in functions['U1001'].items()if v['name']=='VCCIO'+target];own(ref,'U1001',pp,adjacent_ground(pp),'FPGA_bank_reservoir','Frozen placement_target names exact Efinix VCCIO bank; actual powered balls checked.',target=5.)
    elif target=='U2':named_supply(ref,'U1002','flash VCC bypass'if c['capacitance_f']<1e-6 else 'flash VCC reservoir')
    elif target=='Y1':named_supply(ref,'Y1001','oscillator VDD bypass')
    elif target=='U3':named_supply(ref,'U1003','reset gate VCC bypass')
    elif target=='post-CDONE reset delay':own(ref,'U1004','2','3','reset_timing_filter','Frozen post-CDONE RC generator: Schmitt A input, not VDD bypass.')
    else:pending[ref]=dict(reason='Unresolved exact FPGA placement target',target=target)

# Legacy renamed blocks retain source_reference/decouples identities explicitly.
for ref,c in caps.items():
    if ref in rows:continue
    block=c.get('source_block');role=c.get('role','');name=c.get('decouples')
    if name:
        owner=[r for r,d in model.items()if d.get('source_block')==block and d.get('source_reference')==name];assert len(owner)==1,(ref,name,owner);named_supply(ref,owner[0]);continue
    names=re.findall(r'\bU\d+\b',role)
    if len(set(names))==1:
        name=names[0]
        if name not in model:
            possible=[r for r,d in model.items()if d.get('source_block')==block and d.get('source_reference')==name];assert len(possible)==1,(ref,name,possible);name=possible[0]
        named_supply(ref,name)

for ref,owner in [('C3001','U3001'),('C3002','U3002')]:own(ref,owner,'2',['4','9'],'watchdog_timing','Frozen independent TPS3851 CWD timing-cap generator; timing is not a measured20ms qualification.')
for i in range(4):
    for j in range(2):named_supply(f'C{7001+2*i+j}',f'U{7001+i}','AM26LV32 VCC bypass'if j==0 else'AM26LV32 VCC reservoir')

# DI: native SENSE16/11, never upstream IN15/10; NC7 is excluded.
for i in range(12):
    own(f'C{8101+i}',f'U{8001+i}','2',['1','8'],'logic_bypass','Frozen ISO1212 VCC2 and own logic GND1/8; NC6/7 remain NC.')
    own(f'C{8001+2*i}',f'U{8001+i}','16','14','field_input_filter','Frozen DI even SENSE16/own field GND14; actual RSENSE/RTHR frontend, RTHR placement>=4mm separate requirement.')
    own(f'C{8002+2*i}',f'U{8001+i}','11','9','field_input_filter','Frozen DI odd SENSE11/own field GND9; actual RSENSE/RTHR frontend, RTHR placement>=4mm separate requirement.')

motor_path=ROOT/'reports/motherboard-motors-20260930/capacitor-owners-r01.json';inputs[str(motor_path)]=sha(motor_path)
motor=json.loads(motor_path.read_text());motor_rows=motor.get('capacitors',motor.get('rows',[]))
for r in motor_rows:
    ref=r['ref']
    rows[ref]=dict(ref=ref,owner=r['owner_ref'],cap_power='1',cap_return='2',power_nodes=r['actual_owner_endpoints']['1'],return_nodes=r['actual_owner_endpoints']['2'],target=r['placement_target_mm'],category=r['category'],evidence=str(motor_path),related_external_parts=r['related_external_parts'],reviewed_series_path=[])
    pending.pop(ref,None)

# Exact motor-health source construction order, not rail-based owner inference.
for i in range(4):named_supply(f'C{9001+i}',f'U{9001+i}','window supervisor VCC bypass')
for i in range(2):named_supply(f'C{9005+i}',f'U{9005+i}','health VCC bypass')
named_supply('C9007','U9007','isolator primary supply bypass');named_supply('C9008','U9007','isolator secondary supply bypass');named_supply('C9009','U9008','health VCC bypass')

ao_path=ROOT/'hardware/motherboard_analog_output/design.json';inputs[str(ao_path)]=sha(ao_path);ao=json.loads(ao_path.read_text())
for ch in ao['channels']:
    base=14601+28*ch['channel']
    spec=[('power_module_ref','2','1','converter_input_bypass'),('power_module_ref','6','7','isolated_output_reservoir'),('power_module_ref','6','7','isolated_output_bypass'),('regulator_ref','8',['4','9'],'LDO_input_bypass'),('regulator_ref','1',['4','9'],'LDO_output_reservoir'),('regulator_ref','1',['4','9'],'LDO_output_bypass'),('regulator_ref','7',['4','9'],'PG_release_timing'),('window_ref','5','2','window_supply_bypass'),('host_enable_gate_ref','5','3','logic_bypass'),('spi_isolator_ref','1','8','isolation_primary_bypass'),('spi_isolator_ref','16','9','isolation_secondary_bypass'),('local_enable_gate_ref','5','3','logic_bypass'),('local_reset_gate_ref','5','3','logic_bypass'),('dac_ref','1','5','DAC_supply_bypass'),('dac_ref','9','5','DAC_reference_bypass'),('spi_return_buffer_ref','5','3','logic_bypass'),('contact_sink_ref','5','3','logic_bypass'),('amplifier_ref','5','2','amplifier_supply_bypass'),('clamp_observer_ref','5','3','logic_bypass'),('health_isolator_ref','3',['1','7'],'isolation_primary_bypass'),('health_isolator_ref','14',['9','16'],'isolation_secondary_bypass'),('clamp_inverter_ref','5','3','logic_bypass'),('i2c_isolator_ref','1','4','isolation_primary_bypass'),('i2c_isolator_ref','8','5','isolation_secondary_bypass'),('readback_adc_ref','4','3','ADC_input_filter'),('readback_adc_ref','5','3','ADC_input_filter'),('readback_adc_ref','6','3','ADC_input_filter'),('readback_adc_ref','8','3','ADC_supply_bypass')]
    for i,(key,pp,gg,category)in enumerate(spec):
        ref=f'C{base+i}'
        if ref not in rows:own(ref,ch[key],pp,gg,category,'Frozen AO channel metadata and exact28-cap generator sequence/function; native node/return checked.',target=5. if 'reservoir'in category else 2.)

# MCU references are tied to source-specified VREF5 versus actual VDD6.
for ref,owner in [('C13001','U13001'),('C13008','U13004'),('C13014','U13008'),('C14501','U14501')]:own(ref,owner,'10','7','MCU_reset_RF_filter','Frozen NRST RF capacitor belongs to actual PF2-NRST10, not VDD.')
for base,owner in [(13002,'U13001'),(13009,'U13004'),(13015,'U13008'),(14502,'U14501')]:
    for offset,cat in [(0,'MCU_VDD_bypass'),(1,'MCU_VDD_bulk')]:
        ref=f'C{base+offset}'
        if ref in rows:rows.pop(ref)
        own(ref,owner,'6','7',cat,'Frozen STM32G031 source VDD/VDDA6 versus VREF5 and VSS7 explicitly distinguished.',target=5. if offset else 2.)
for ref,owner in [('C13004','U13001'),('C13005','U13001'),('C14504','U14501'),('C14505','U14501')]:
    if ref in rows:rows.pop(ref)
    own(ref,owner,'5','7','MCU_VREF_bypass','Frozen STM32G031 VREF+5 explicitly distinguished from same-rail VDD6; no same-rail arbitrary selection.')
for ref,owner in [('C14506','U14502'),('C14507','U14503'),('C14508','U14504')]:named_supply(ref,owner,'supply bypass')

# Purchased compute/service/storage port power and reference owners.
def connector(ref,owner,signal_pins,return_pins,category,reason,return_ref=None,target=3.):
    own(ref,owner,signal_pins,return_pins,category,reason,target=target,return_ref=return_ref)
for ref in ['C15001','C15002']:connector(ref,'J15001',['77','79','81','83','85','87'],['71','74','98'],'compute_bay_reservoir'if ref=='C15001'else'compute_bay_bypass','Frozen CM connector current-carrying5V contacts, not supervisor pin on the same rail.',target=5. if ref=='C15001'else 3.)
connector('C15003','J15001',['78','84','86'],['71','74','98'],'module_AUX3V3_reservoir','Frozen module-owned auxiliary3V3 contacts; cannot source from carrier IO3.',target=5.)
for ref in ['C15016','C15017']:connector(ref,'J15003','4','6','microSD_local_reservoir'if ref=='C15016'else'microSD_local_bypass','Exact Molex SD VDD4/VSS6 socket; supplied downstream of actual port switch.',target=5. if ref=='C15016'else 3.)
own('C15019','U15013','4','2','supervisor_timing','Frozen exact TPS3808 CT4 capacitor; not VDD bypass.')
connector('C15024','J15004','18','17','HDMI_local5V_bypass','Actual HDMI5V18/localground17, not cable shield.')
for ref in ['C15034','C15035']:connector(ref,'J15005','1','4','USB_local_reservoir'if ref=='C15034'else'USB_local_bypass','Actual USB-A VBUS1/GND4 load reservoir and HF bypass; shield is separate CHASSIS.',target=5. if ref=='C15034'else 3.)
connector('C15047','J15007','1',['7','8'],'Ethernet_PHY_CT_AC_coupling','Exact MagJack CT_PHY1 ac-coupled to PHY module digital-return plane, using actual CM connector GND7/8; never direct3V3.',return_ref='J15002')
connector('C16006','J16001',pins_same('J16001',nodes[('C16006','1')]),pins_same('J16001',nodes[('C16006','2')]),'ESP_module_local_bulk','Frozen purchased ESP module own5V socket contacts; no arbitrary IC supply assignment.',target=5.)
own('C14417','U14417','5','2','protection_latchoff_timing','Frozen TPS2662 CT/FLT timing capacitor belongs to exact device timing pin; native pin name checked.')
for ref,owner in [('C21001','U21001'),('C21002','U21001'),('C21003','U21003')]:named_supply(ref,owner,'repeater supply bypass')

# Actual nine AC-only chassis coupling locations and both physical domain pins.
couplings={'C19501':('J15004',['17'],['SH1','SH2','SH3','SH4']),'C19502':('J19513',['2','9'],['10']),'C19503':('J19501',['13'],['6']),'C19504':('J19534',['9'],['12']),'C19505':('J19529',['2'],['3']),'C19506':('J19530',['2'],['3']),'C19507':('J19531',['11'],['12']),'C19508':('J19532',['3','6'],['5']),'C19509':('J19533',['3','6'],['5'])}
for ref,(owner,pp,rr)in couplings.items():connector(ref,owner,pp,rr,'AC_only_Y2_chassis_coupling','Frozen source domain role plus actual same connector domain/CHASSIS pins; no DC bond or VDD bypass claim.',target=5.)

# Validate exact source pin nets/functions after all declaration-based mappings.
errors=[]
for ref,r in rows.items():
    if ref not in caps:errors.append('Noncapacitor or absent row '+str(ref));continue
    if not all(k in r for k in ['owner','power_nodes','return_nodes','cap_power','cap_return']):pending[ref]=dict(reason='External owner schema needs explicit normalization',row=r);continue
    pn=nodes[(ref,r['cap_power'])];gn=nodes[(ref,r['cap_return'])]
    r['actual_cap_signal_net']=pn;r['actual_cap_return_net']=gn;r['actual_MPN']=caps[ref]['mpn'];r['source_block']=caps[ref]['source_block'];r['source_role']=caps[ref].get('role');r['actual_native_function_nodes']={'signal':[{**n,'function':functions[n['ref']][str(n['pin'])]['name'],'net':nodes.get((n['ref'],str(n['pin'])))}for n in r['power_nodes']],'return':[{**n,'function':functions[n['ref']][str(n['pin'])]['name'],'net':nodes.get((n['ref'],str(n['pin'])))}for n in r['return_nodes']]}
    direct=all(nodes.get((n['ref'],str(n['pin'])))==pn for n in r['power_nodes'])
    path=r.get('reviewed_series_path',[])
    if not direct and path:
        assert len(path)==3 and path[1]['reference']==path[2]['reference'];direct=nodes[(path[0]['reference'],str(path[0]['pin']))]==nodes[(path[1]['reference'],str(path[1]['pin']))]and nodes[(path[2]['reference'],str(path[2]['pin']))]==pn
    r['actual_native_signal_pin_match']=direct;r['actual_native_return_pin_match']=bool(r['return_nodes'])and all(nodes.get((n['ref'],str(n['pin'])))==gn for n in r['return_nodes']);r['owner_mapping_verified']=r['actual_native_signal_pin_match']and r['actual_native_return_pin_match'];r['manufacturer_numeric_maximum']=False;r['physical_loop_or_effective_capacitance_qualified']=False
    if not r['owner_mapping_verified']:errors.append('Native function/return mismatch '+ref)
for ref,c in caps.items():
    if ref not in rows:pending.setdefault(ref,dict(reason='Generator/function owner still requires explicit review',role=c.get('role'),block=c.get('source_block'),native_nodes={k:nodes[(ref,k)]for k in ['1','2']}))
assert all(sha(Path(f))==h for f,h in inputs.items())
report={'source_physical_parts':2688,'source_capacitor_count':723,'input_hashes':inputs,'capacitors':list(rows.values()),'owner_mapping_count':sum(r.get('owner_mapping_verified',False)for r in rows.values()),'pending':pending,'errors':errors,'exclusive_full_population_accounted':set(rows)|set(pending)==set(caps),'all_owner_mappings_verified':not errors and not pending and len(rows)==723,'categories':dict(collections.Counter(r.get('category','external')for r in rows.values())),'source_or_PCB_mutated':False,'manufacturing_ready':False,'scope':'Exact source generator/function and native physical pin ownership. This is not PCB placement, complete connectivity, measured loop impedance, effective-C, loaded thermal or hardware qualification.'}
(out/'capacitor-owners.json').write_text(json.dumps(report,indent=2)+'\n');(out/'issued-tool.py').write_bytes(Path(__file__).read_bytes());print(json.dumps({k:v for k,v in report.items()if k not in ['capacitors','input_hashes']}))
