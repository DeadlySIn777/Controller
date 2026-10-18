"""Read-only native MC motor placement inspection, independent of its generator."""
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import pcbnew as K

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
BOARD=ROOT/'hardware/board_review/revisions/20260930-07/motion-card-placement.kicad_pcb'
PREVIOUS=ROOT/'hardware/board_review/revisions/20260930-06/motion-card-route-candidate.kicad_pcb'
SOURCE=ROOT/'hardware/motion_card'
STANDALONE=ROOT/'hardware/mc_motor_buffers'
LIB=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
INPUTS=[BOARD,PREVIOUS,SOURCE/'design.json',SOURCE/'assembly-map.json',SOURCE/'netlist.xml',
        SOURCE/'bom.csv',SOURCE/'motor-placement.json',SOURCE/'motion_card.pdf',
        SOURCE/'motion_card.kicad_sch',SOURCE/'erc.json',
        ROOT/'hardware/board_review/revisions/20260930-07/native-drc.json',
        STANDALONE/'design.json',ROOT/'research/mc-motor-buffers/sn74lvc244a.pdf',
        ROOT/'research/mc-motor-buffers/sn74lvc2g126.pdf',
        LIB/'Package_SO.pretty/TSSOP-20_4.4x6.5mm_P0.65mm.kicad_mod',
        LIB/'Package_SO.pretty/VSSOP-8_2.3x2mm_P0.5mm.kicad_mod',Path(__file__)]


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mm(v):return round(K.ToMM(v),6)
def xy(p):return [mm(p.x),mm(p.y)]
def distance(a,b):return math.dist(xy(a.GetPosition()),xy(b.GetPosition()))
def fp_record(f):
    return {'ref':f.GetReference(),'position_mm':xy(f.GetPosition()),'orientation_deg':f.GetOrientationDegrees(),
            'footprint':f.GetFPIDAsString(),'value':f.GetValue(),'layer':f.GetLayerName(),
            'pads':{p.GetNumber():{'position_mm':xy(p.GetPosition()),
              'local_mm':xy(p.GetPosition()-f.GetPosition()),'size_mm':xy(p.GetSize()),
              'net':p.GetNetname(),'pad_angle_deg':p.GetOrientationDegrees()} for p in f.Pads()}}


def main():
    before={str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p):digest(p) for p in INPUTS}
    board=K.LoadBoard(str(BOARD));prior=K.LoadBoard(str(PREVIOUS))
    footprints={f.GetReference():f for f in board.GetFootprints()}
    old={f.GetReference():f for f in prior.GetFootprints()}
    standalone=json.loads((STANDALONE/'design.json').read_text());parent=json.loads((SOURCE/'design.json').read_text())
    block=json.loads((SOURCE/'assembly-map.json').read_text())['blocks']['mc_motor_buffers'];mapping=block['references']
    global_nets=set(block['interfaces'])
    net_xml=ET.parse(SOURCE/'netlist.xml').getroot();native={}
    for net in net_xml.findall('./nets/net'):
        for node in net.findall('node'):native[node.attrib['ref'],node.attrib['pin']]=net.attrib['name']
    bom=list(csv.DictReader((SOURCE/'bom.csv').open(encoding='utf-8')))
    physical_bom={r['Reference']:r for r in bom if r['Scope']=='physical_component_candidate'}
    mismatches=[];pad_count=0;new={};ic_geometry=[]
    for ref,c in standalone['components'].items():
        target=mapping[ref]
        if not c['physical']:
            if target in footprints:mismatches.append('Logical boundary acquired a footprint: '+target)
            continue
        if target not in footprints:mismatches.append('Missing motor footprint: '+target);continue
        f=footprints[target];record=fp_record(f);new[target]=record
        if record['footprint']!=c['footprint']:mismatches.append('Footprint differs: '+target)
        if target not in physical_bom or physical_bom[target]['MPN']!=c['mpn']:mismatches.append('BOM differs: '+target)
        expected=parent['components'][target]['pins']
        if set(record['pads'])!=set(c['pins']):mismatches.append('Pad count/name differs: '+target)
        for pin,pad in record['pads'].items():
            pad_count+=1
            if pad['net']!=native.get((target,pin)):mismatches.append('Native conductor differs: '+target+'/'+pin)
            if expected.get(pin) is not None:
                expected_net='/'+expected[pin] if expected[pin] in global_nets else '/mc_motor_buffers/'+expected[pin]
                if pad['net']!=expected_net:mismatches.append('Source conductor differs: '+target+'/'+pin)
        if c['kind'] in ('LVC244A','LVC2G126'):
            p=record['pads'];count=20 if c['kind']=='LVC244A' else 8;left=list(range(1,count//2+1));right=list(range(count,count//2,-1))
            y_pitch=abs(p['2']['local_mm'][1]-p['1']['local_mm'][1]);row_separation=abs(p[str(count)]['local_mm'][0]-p['1']['local_mm'][0])
            correct=(record['orientation_deg']==0 and record['layer']=='F.Cu' and
                all(p[str(i)]['local_mm'][0]<0 for i in left) and all(p[str(i)]['local_mm'][0]>0 for i in right) and
                all(p[str(left[i])]['local_mm'][1]<p[str(left[i+1])]['local_mm'][1] for i in range(len(left)-1)) and
                all(p[str(right[i])]['local_mm'][1]<p[str(right[i+1])]['local_mm'][1] for i in range(len(right)-1)) and
                abs(y_pitch-(.65 if count==20 else .5))<1e-6)
            if not correct:mismatches.append('Physical orientation/spacing differs: '+target)
            ic_geometry.append({'ref':target,'kind':c['kind'],'physical_pad_numbering_and_pitch_match_package':correct,
                'pin1_local_mm':p['1']['local_mm'],'pitch_mm':y_pitch,'row_separation_mm':row_separation,
                'pad_size_mm':p['1']['size_mm'],'same_column_copper_gap_mm':round(y_pitch-p['1']['size_mm'][1],6),
                'VCC_pin':'20' if count==20 else '8','GND_pin':'10' if count==20 else '4',
                'exact_TI_example_landpattern':False,'alternate_IPC_landpattern_assembly_approval':False})
    capacitors=[];series=[]
    for i in range(1,12):
        ur=mapping[f'U{i}'];cr=mapping[f'C{i}'];u=footprints[ur];c=footprints[cr]
        kind=standalone['components'][f'U{i}']['kind'];vcc='20' if kind=='LVC244A' else '8';gnd='10' if kind=='LVC244A' else '4'
        up={p.GetNumber():p for p in u.Pads()};cp={p.GetNumber():p for p in c.Pads()}
        capacitors.append({'buffer':ur,'capacitor':cr,'VCC_to_cap1_straight_line_mm':round(distance(up[vcc],cp['1']),6),
            'GND_pin_to_cap2_straight_line_mm':round(distance(up[gnd],cp['2']),6),
            'VCC_net_correct':up[vcc].GetNetname()==cp['1'].GetNetname()=='/IO_3V3',
            'GND_net_correct':up[gnd].GetNetname()==cp['2'].GetNetname()=='/LOGIC_GND',
            'route_loop_inductance_qualified':False})
    for path in standalone['paths']:
        u=footprints[mapping[path['buffer_ref']]];r=footprints[mapping[path['series_ref']]]
        up={p.GetNumber():p for p in u.Pads()};rp={p.GetNumber():p for p in r.Pads()};y=up[path['output_pin']]
        series.append({'output':path['output'],'buffer':u.GetReference(),'Y_pin':path['output_pin'],
            'source_resistor':r.GetReference(),'Y_to_R1_straight_line_mm':round(distance(y,rp['1']),6),
            'raw_net_correct':y.GetNetname()==rp['1'].GetNetname(),
            'Y_local_side':'left' if y.GetPosition().x<u.GetPosition().x else 'right',
            'resistor_center_relative_x_mm':mm(r.GetPosition().x-u.GetPosition().x),'route_qualified':False})
    series.sort(key=lambda row:row['Y_to_R1_straight_line_mm'],reverse=True)
    retained_changed=[];retained_net_changes={}
    for ref,f in old.items():
        if ref not in footprints:retained_changed.append('Missing '+ref);continue
        current=fp_record(footprints[ref]);previous=fp_record(f)
        if current['position_mm']!=previous['position_mm'] or current['orientation_deg']!=previous['orientation_deg'] or current['footprint']!=previous['footprint'] or set(current['pads'])!=set(previous['pads']):retained_changed.append(ref)
        net_changes=[]
        for pin,pad in previous['pads'].items():
            now=current['pads'].get(pin,{})
            if any(now.get(k)!=pad[k] for k in ('position_mm','local_mm','size_mm','pad_angle_deg')):retained_changed.append(ref+'/'+pin)
            if now.get('net')!=pad['net']:net_changes.append({'pin':pin,'previous':pad['net'],'current':now.get('net')})
        if net_changes:retained_net_changes[ref]=net_changes
    drc=json.loads((ROOT/'hardware/board_review/revisions/20260930-07/native-drc.json').read_text())
    after={str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p):digest(p) for p in INPUTS}
    result={'scope':'Read-only actual native pad/BOM/source-net and placement review; no routing or manufacture approval',
        'inputs_sha256':before,'inputs_unchanged_during_review':before==after,'native_footprints':len(footprints),
        'physical_BOM_rows':len(physical_bom),'native_motor_footprints':len(new),'motor_physical_pads_checked':pad_count,
        'motor_pad_BOM_source_net_mismatches':mismatches,'retained_footprints':len(old),'retained_footprint_geometry_changes':retained_changed,
        'retained_footprint_net_changes':retained_net_changes,
        'native_DRC_non_unconnected_violations':len(drc.get('violations',[])),
        'native_DRC_unconnected_items':len(drc.get('unconnected_items',[])),
        'IC_package_geometry':ic_geometry,'decoupling_pad_distances':capacitors,
        'source_series_pad_distances':series,'motor_native_footprint_detail':new,
        'placement_priorities':['Move source series resistors to their actual physical Y pads; current generic right-side anchoring creates long unterminated source traces.',
          'Reduce seven VSSOP bypass VCC connections and place immediate ground-return vias once the ground-plane design is reviewed.',
          'Qualify the two stock IPC footprint landpatterns; they are not exact TI example landpatterns.',
          'No source-series value, routed loop/return path, solder process or signal integrity has been qualified.'],
        'complete_MC':False,'manufacturing_ready':False}
    (HERE/'native-inspection.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    with (HERE/'series-pad-distances.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(series[0]));w.writeheader();w.writerows(series)
    print(json.dumps({k:result[k] for k in ('inputs_unchanged_during_review','native_footprints','physical_BOM_rows',
        'native_motor_footprints','motor_physical_pads_checked','motor_pad_BOM_source_net_mismatches','retained_footprints',
        'retained_footprint_geometry_changes','native_DRC_non_unconnected_violations','native_DRC_unconnected_items')},indent=2))
    print('worst_series',json.dumps(series[:6]));print('capacitors',json.dumps(capacitors))


if __name__=='__main__':main()
