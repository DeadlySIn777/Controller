"""Report-only exact-owner placement manifest; never edit frozen circuits or PCB."""
from pathlib import Path
import hashlib,json,copy

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/motherboard-bypass-owners-20260930'
MODELS={n:json.loads((ROOT/'hardware'/n/'design.json').read_text()) for n in ['motherboard_analog_input','motherboard_comms']}
rows=[]

def add(block,cap,owner,signal,returns,category='HF_supply_bypass',via=None,notes=None,exact_distance=None,pair=None):
    m=MODELS[block];p=m['components'];signal=str(signal);returns=list(map(str,returns))
    c=p[cap];o=p[owner]
    assert all(x in o['pins'] for x in [signal,*returns])
    chain=[dict(reference=owner,pin=signal,net=o['pins'][signal])]
    if via:
        cur=o['pins'][signal]
        for rr in via:
            vals=p[rr]['pins'];start=next(k for k,v in vals.items() if v==cur);end=next(k for k in vals if k!=start);cur=vals[end]
            chain.extend([dict(reference=rr,pin=start,net=vals[start]),dict(reference=rr,pin=end,net=cur)])
        assert cur==c['pins']['1']
    else:assert o['pins'][signal]==c['pins']['1'],(cap,owner,signal)
    assert all(o['pins'][r]==c['pins']['2'] for r in returns),(cap,owner,returns)
    assert not any(r['capacitor_reference']==cap for r in rows)
    rows.append(dict(source_block=block,capacitor_reference=cap,capacitor_mpn=c['mpn'],capacitor_value=c['value'],
        capacitor_signal_pad='1',capacitor_return_pad='2',signal_net=c['pins']['1'],return_net=c['pins']['2'],
        real_owner_reference=owner,real_owner_mpn=o['mpn'],real_owner_signal_pin=signal,real_owner_matching_return_pins=returns,
        exact_connection_path=chain,category=category,generator_role=c['role'],
        placement_target_pad_distance_mm=exact_distance if exact_distance is not None else 3.0,
        distance_basis='TI ISOW layout maximum, measured from bypass copper pad to actual supply pin' if exact_distance==1.0 else 'Engineering placement target, not a device electrical guarantee; route the exact owner loop locally',
        bulk_to_HF_pair_reference=pair,bulk_to_HF_pad_distance_mm=[2.0,4.0] if pair else None,
        effective_capacitance_proven=False,placement_measured=False,routed_loop_measured=False,
        notes=notes or []))

ai='motherboard_analog_input';m=MODELS[ai];b=m['blocks'];ch=m['channels']
for k,base in [('dc5',1),('dc15',4),('dc24',7)]:
    owner=b[k]
    add(ai,f'C147{base:02}',owner,22 if k=='dc24' else 2,[2] if k=='dc24' else [1],'converter_input_bulk',notes=['REC input pins22/23 share the local VIN loop.'] if k=='dc24' else [])
    add(ai,f'C147{base+1:02}',owner,14 if k=='dc24' else 4,[16] if k=='dc24' else [6],'converter_secondary_bulk')
    add(ai,f'C147{base+2:02}',owner,14 if k=='dc24' else 4,[16] if k=='dc24' else [6],'converter_secondary_HF')
for i,w in enumerate(b['windows']):add(ai,f'C147{10+i}',w,5,[2])
for cap,key,power,ret in [(13,'spi_isolator',1,[6,8]),(14,'spi_isolator',16,[9]),(15,'reset_gate',5,[3]),(16,'return_buffer',5,[3]),(17,'i2c_isolator',1,[4]),(18,'i2c_isolator',8,[5]),(19,'mode_expander',16,[8]),(20,'reference',2,[4]),(21,'reference',5,[4]),(22,'reference',6,[4]),(23,'quad_buffer',4,[11])]:
    add(ai,f'C147{cap}',b[key],power,ret,category='reference_noise_filter' if cap==21 else 'reference_output_storage_with_real_ESR' if cap==22 else 'HF_supply_bypass',via=['R14719'] if cap==22 else None,
        notes=['Keep R14719 (1.2ohm) in the capacitor branch only; reference VOUT has a Kelvin path directly to all INA REFA/REFB pins.'] if cap==22 else None)
for i,c in enumerate(ch):
    base=24+4*i
    for offset,key in [(0,'ina_ref'),(1,'mode_gate_ref'),(2,'led_sink_ref')]:
        add(ai,f'C147{base+offset}',c[key],7 if offset==0 else 5,[4] if offset==0 else [3])
    add(ai,f'C147{base+3}',b['adc'],[16,18,21,23][i],[[17],[19],[20],[22]][i],'ADC_input_HF_filter',notes=['Keep filter next to actual ADC input; source47ohm isolation resistor remains in the buffer-to-ADC path.'])
for cap,pin in [(40,5),(41,5),(42,7),(43,7)]:add(ai,f'C147{cap}',b['adc'],pin,[6],'ADC_reference_charge_storage',notes=['Nominal22uF bulk requires >=10uF effective over actual bias, temperature and tolerance; 1uF is a separate close HF capacitor.'])
for cap,pin,ret in [(44,9,[8]),(45,30,[29,31]),(46,34,[33])]:add(ai,f'C147{cap}',b['adc'],pin,ret)
add(ai,'C14747',b['sensor_efuse'],10,[9,11],'protected_sensor_output_storage')
add(ai,'C14748',b['reference_amplifier'],5,[2])
add(ai,'C14749',b['diagnostic_adc'],8,[3])
for cap,pin in [(50,4),(51,5),(52,7)]:add(ai,f'C147{cap}',b['diagnostic_adc'],pin,[3],'diagnostic_ADC_input_filter')
add(ai,'C14753',b['health_isolator'],3,[1,7]);add(ai,'C14754',b['health_isolator'],14,[9,16]);add(ai,'C14755',b['fault_inverter'],5,[3])

com='motherboard_comms';b=MODELS[com]['blocks']
for cap,key,power,ret,cat in [(1,'load_switch',1,[2],'switch_input_storage'),(2,'load_switch',4,[2],'load_switch_slew_capacitor'),(3,'load_switch',6,[2],'switched_controller_output_bulk'),(4,'controller_supervisor',3,[1],'HF_supply_bypass'),(5,'link_ready_gate',5,[3],'HF_supply_bypass'),(6,'ready_inverter',5,[3],'HF_supply_bypass'),(7,'spi_buffer',14,[7],'HF_supply_bypass'),(8,'controller',14,[7],'HF_supply_bypass'),(9,'clock',4,[2],'HF_supply_bypass'),(10,'can_tx_buffer',5,[3],'HF_supply_bypass'),(11,'can_rx_buffer',5,[3],'HF_supply_bypass'),(12,'standby_gate',5,[3],'HF_supply_bypass'),(13,'rs_de_gate',5,[3],'HF_supply_bypass')]:add(com,f'C148{cap:02}',b[key],power,ret,cat)
for base,key,fieldret in [(14,'rs_transceiver',[15]),(25,'can_transceiver',[15,16,17])]:
    owner=b[key]
    for offset,power,ret in [(0,9,[10]),(4,12,[11])]:
        hf=f'C148{base+offset:02}'
        add(com,hf,owner,power,ret,'ISOW_0402_converter_HF',exact_distance=1.0)
        add(com,f'C148{base+offset+1:02}',owner,power,ret,'ISOW_local_1uF')
        for cidx in [base+offset+2,base+offset+3]:add(com,f'C148{cidx:02}',owner,power,ret,'ISOW_converter_bulk',pair=hf,notes=['Two22uF nominal bulk parts provide44uF nominal; aggregate actual effective capacitance must remain >=10uF over operating corners. Symmetric power/return loop, not a remote same-rail capacitor.'])
    add(com,f'C148{base+8:02}',owner,1,[6],'ISOW_VIO_logic_bypass')
    add(com,f'C148{base+9:02}',owner,16 if key=='rs_transceiver' else 20,fieldret,'ISOW_filtered_field_bypass',notes=['After real power/return ferrites; do not merge raw isolated converter return with filtered field COM, LOGIC_GND or CHASSIS.'])
add(com,'C14824',b['RS485_window'],5,[2]);add(com,'C14835',b['CAN_window'],5,[2])
add(com,'C14836',b['can_health_isolator'],3,[1,7]);add(com,'C14837',b['can_health_isolator'],14,[9,16]);add(com,'C14838',b['RS485_health_gate'],5,[3]);add(com,'C14839',b['CAN_health_gate'],5,[3])

expected={r for m in MODELS.values() for r,p in m['components'].items() if p['kind']=='C'}
assert {r['capacitor_reference'] for r in rows}==expected and len(rows)==94
negative=[]
for name,mut in [('wrong local IC owner',lambda x:x.update(real_owner_reference='U14701')),('wrong return domain',lambda x:x.update(return_net='LOGIC_GND')),('wrong physical pin',lambda x:x.update(real_owner_signal_pin='4'))]:
    row=copy.deepcopy(next(x for x in rows if x['capacitor_reference']=='C14724'));mut(row)
    try:
        cp=MODELS[row['source_block']]['components'][row['capacitor_reference']];op=MODELS[row['source_block']]['components'][row['real_owner_reference']]
        assert op['pins'][row['real_owner_signal_pin']]==cp['pins']['1'];assert row['return_net']==cp['pins']['2'];assert all(op['pins'][p]==cp['pins']['2'] for p in row['real_owner_matching_return_pins'])
    except (AssertionError,KeyError):negative.append(dict(name=name,rejected=True))
    else:raise AssertionError(name)
files=[ROOT/'hardware'/n/'design.json' for n in MODELS]+[ROOT/'tools'/('hardware_build_'+n+'.py') for n in MODELS]+[ROOT/'reports/motherboard-comms-20260930/sources/isow1044.txt',ROOT/'reports/motherboard-comms-20260930/sources/isow1432.txt']
hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
data=dict(schema_version=1,scope='Exact source-generated capacitor ownership and source pin/net checks; report-only, no placement or routing modification.',
    physical_source_parts={'motherboard_analog_input':166,'motherboard_comms':95},capacitor_count=94,source_hashes=hashes,capacitors=rows,
    generator_relationships_verified=True,pad_geometry_measured=False,PCB_placement_pass=False,PCB_routing_pass=False,manufacturing_ready=False,
    converter_layout_rules=['TI ISOW1432/1044 converter10nF0402 within1mm of actual VDD9/GND10 or VISOOUT12/GND11 pair; bulk after that cap,2–4mm from it.','Symmetric power/return loops. Both power and return ferrites are actual components, with raw and filtered isolated nets kept distinct.','TI section9.4.1 also requires converter-output routing/pour exclusions within4mm of pins11/12; reconcile exact allowed own-power/capacitor paths with vendor layout drawing, preserve required creepage. This report does not measure or waive that native PCB gate.'],
    negative_controls=negative,all_caps_exactly_owned=True)
OUT.mkdir(exist_ok=True)
path=OUT/'AI_COMMS_BYPASS_PLACEMENT.json';assert not path.exists(),'Do not overwrite issued report'
path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
text=['# Exact AI / communications capacitor ownership','', '94 source capacitors: 55 in AI166 and 39 in COMMS95. Each has the actual generated IC owner, physical supply/signal pin, matching local return pins and exact series path when applicable. No nearest-same-rail inference or circuit mutation.','', '1mm ISOW HF and 2–4mm bulk-to-HF limits are manufacturer requirements. The other 3mm distances are conservative placement targets; actual route loops, converter output exclusions, creepage, effective capacitance and clearances remain native PCB/physical gates.','', '| Capacitor | Owner pin | Return pins | Role |','|---|---|---|---|']
for r in rows:text.append(f"| {r['capacitor_reference']} | {r['real_owner_reference']}.{r['real_owner_signal_pin']} | {','.join(r['real_owner_matching_return_pins'])} | {r['category']} |")
(OUT/'README.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
print('PASS 94 exact capacitor owners / 3 adversarial owner-return-pin controls:',path)
