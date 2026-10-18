"""Freeze the exact native eight-channel ISO1212 topology review."""
from pathlib import Path
import hashlib,json,shutil,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=ROOT/'reports/motherboard-integration-20260930/r23-2688-reset-bypass-staged'
tree=ET.parse(old/'netlist.xml')
nodes={(n.attrib['ref'],n.attrib['pin']):net.attrib['name']
       for net in tree.findall('.//nets/net') for n in net.findall('node')}
rows=[]
for i,(r,thr,rsense,name,sense,inp) in enumerate([
    ('U14031','R14069','R14070','PRB0',16,15),
    ('U14031','R14072','R14073','PRB1',11,10),
    ('U19001','R19001','R19002','EXT_PERMIT',16,15),
    ('U19001','R19004','R19005','PROCESS_PERMIT',11,10),
    ('U19002','R19007','R19008','SAFETY_STATUS',16,15),
    ('U19002','R19010','R19011','RESET_ARM',11,10),
    ('U19003','R19013','R19014','CONTACTOR_FB',16,15),
    ('U19003','R19016','R19017','STO_FB',11,10)]):
    ns=nodes[r,str(sense)];ni=nodes[r,str(inp)]
    assert {nodes[rsense,'1'],nodes[rsense,'2']}=={ns,ni}
    correct=nodes[thr,'2']==ns
    assert correct==(i>=2)
    rows.append(dict(channel=name,IC=r,RTHR=thr,RSENSE=rsense,
        native_SENSE_pin=str(sense),native_IN_pin=str(inp),
        old_RTHR_protected_pin_net=nodes[thr,'2'],required_RTHR_protected_pin_net=ns,
        exact_RSENSE_bridge=[nodes[rsense,'1'],nodes[rsense,'2']],
        old_source_topology_correct=correct,
        field_return=nodes[r,'14' if sense==16 else '9'],
        logic_VCC=nodes[r,'2'],logic_GND=[nodes[r,'1'],nodes[r,'8']],
        SUB_pin='13' if sense==16 else '12',SUB_native_net=nodes[r,'13' if sense==16 else '12']))
inputs=OUT/'inputs';inputs.mkdir(exist_ok=True)
for p in [old/'netlist.xml',old/'design.json',old/'assembly-map.json',
          ROOT/'research/digital-inputs/iso1212.pdf',ROOT/'research/digital-inputs/iso1212.txt',
          ROOT/'reports/motherboard-return-zoning-20260930/di-capacitor-owner-r01/iso1212-layout-p31.png']:
    shutil.copyfile(p,inputs/p.name)
review=dict(scope='Independent exact native topology inspection; no board routing or physical qualification.',
    source_stage=str(old.relative_to(ROOT)),source_SHA256=sha(old/'design.json'),
    native_XML_SHA256=sha(old/'netlist.xml'),
    manufacturer=dict(name='Texas Instruments',part='ISO1212DBQR',
        URL='https://www.ti.com/lit/ds/symlink/iso1212.pdf',
        retained_document='SLLSEY7G, revised February2025; native downloaded document retained unchanged',
        primary_pages=[31],primary_figures=['8-17','8-18'],
        topology='External input -> RTHR -> SENSE; RSENSE bridges SENSE and IN; optional CIN goes from SENSE to own field return.',
        geometric_requirements=dict(RTHR_external_pad_to_protected_device_CIN_RSENSE_minimum_mm=4.0,
            logic_bypass_positive_to_VCC_maximum_mm=2.0),
        voltage_rating_scope='Retain frozen SELV field input envelopes; this does not grant full package insulation certification.'),
    channels=rows,exact_required_parent_native_pin_delta=[dict(ref='R14069',pin='2',old=rows[0]['old_RTHR_protected_pin_net'],new=rows[0]['required_RTHR_protected_pin_net']),
        dict(ref='R14072',pin='2',old=rows[1]['old_RTHR_protected_pin_net'],new=rows[1]['required_RTHR_protected_pin_net'])],
    all_six_safety_RTHR_topologies_correct=True,old_two_probe_topologies_invalid=True,
    SUB_islands_distinct=len({r['SUB_native_net'] for r in rows})==8,
    footprint_MPN_parts_unchanged_by_proposed_source_correction=True,
    PCB_pose_spacing_return_route_and_EMC_not_passed_by_this_review=True,
    frozen_input_hashes={p.name:sha(p) for p in inputs.iterdir()},manufacturing_ready=False)
assert review['SUB_islands_distinct']
(OUT/'review.json').write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps(dict(channels=len(rows),invalid_probe_topologies=2,correct_safety_topologies=6,
    exact_source_pad_corrections=2,review_SHA256=sha(OUT/'review.json'))))
