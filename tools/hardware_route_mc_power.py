"""Route ten pad-backed MC buck connections on a review COPY only.

Run with KiCad's bundled Python. No planes, fabrication exports or live-board
changes. Widths are provisional geometry choices, not ampacity/thermal approval.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
KICAD_CLI = Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
DEFAULT_BASE = ROOT / 'hardware/board_review/revisions/20260930-05/motion-card-placement.kicad_pcb'
DEFAULT_OUTPUT = ROOT / 'reports/board-completion-20260930/power-routing'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')


def mmxy(position):
    return [round(pcbnew.ToMM(position.x), 6), round(pcbnew.ToMM(position.y), 6)]


def vector(point):
    return pcbnew.VECTOR2I(pcbnew.FromMM(point[0]), pcbnew.FromMM(point[1]))


def same_xy(a, b):
    # Native coordinates are integer nanometres. Decimal-to-integer conversion
    # can differ by one nanometre; this tolerance remains far below PCB rules.
    return all(abs(x-y) <= .000002 for x,y in zip(a,b))


def native_drc(board_path, output_dir, stem):
    report_path = output_dir / (stem+'.json')
    command = [str(KICAD_CLI), 'pcb', 'drc', '--format', 'json',
               '--all-track-errors', '--severity-all', '--output', str(report_path), str(board_path)]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
    (output_dir / (stem+'.txt')).write_text(result.stdout+result.stderr, encoding='utf-8')
    if result.returncode != 0 or not report_path.exists():
        raise RuntimeError(f'Native DRC failed to execute: {result.returncode}')
    return read_json(report_path)


def drc_counts(report):
    return {key:dict(Counter((row.get('severity','')+':'+row.get('type','')) for row in report.get(key, [])))
            for key in ['violations', 'unconnected_items', 'schematic_parity']}


def item_ids(row):
    return {str(item.get('uuid', '')) for item in row.get('items', [])}


def signature(row):
    return json.dumps({'type':row.get('type'), 'severity':row.get('severity'),
                       'description':row.get('description'),
                       'items':sorted((str(i.get('uuid','')),str(i.get('description',''))) for i in row.get('items',[]))}, sort_keys=True)


def route_plan(connection):
    """Use short 0.2mm RPJ escapes; wider power paths outside the package."""
    points = connection['suggested_centerline_mm']
    source_pad = connection['from'][1]
    if connection['net'].endswith('_SW'):
        a, b = points
        escape = [round(a[0]-.425,6), a[1]]
        return [(a,escape,.2), (escape,b,.4)]
    if connection['from'][0].startswith('L'):
        return [(a,b,.6) for a,b in zip(points,points[1:])]
    if source_pad in {'4','6'}:
        a = points[0]
        escape = [round(a[0]+.6,6),a[1]]
        return [(a,escape,.2), (escape,points[1],.4), (points[1],points[2],.4)]
    return [(a,b,.2) for a,b in zip(points,points[1:])]


def native_reachable(board, start_pad, goal):
    """Follow native geometric connectivity, not just the assigned net."""
    connectivity=board.GetConnectivity()
    seen=set()
    pending=[start_pad]
    connected_pad_keys=set()
    while pending:
        item=pending.pop()
        uid=item.m_Uuid.AsString()
        if uid in seen:
            continue
        seen.add(uid)
        for pad in connectivity.GetConnectedPads(item):
            connected_pad_keys.add((pad.GetParentFootprint().GetReference(),pad.GetNumber()))
            pending.append(pad)
        pending.extend(connectivity.GetConnectedTracks(item))
    return goal in connected_pad_keys


def route(base_path, output_dir):
    base_path = base_path.resolve()
    output_dir = output_dir.resolve()
    if not base_path.is_file():
        raise FileNotFoundError(base_path)
    if output_dir == base_path.parent or output_dir.is_relative_to(ROOT/'hardware'):
        raise ValueError('Route output must be a separate report directory, never a live or revision PCB directory')
    if output_dir.exists():
        raise FileExistsError('Preserve existing routing evidence; choose another output directory')
    placement_path = ROOT/'hardware/motion_card/local-power-placement.json'
    design_path = ROOT/'hardware/mc_local_power/design.json'
    mapping_path = ROOT/'hardware/motion_card/assembly-map.json'
    netlist_path = ROOT/'hardware/motion_card/netlist.xml'
    source_paths = [base_path, base_path.with_suffix('.kicad_pro'), placement_path, design_path, mapping_path, netlist_path,
                    Path(__file__).resolve()]
    before = {str(path.relative_to(ROOT)):sha(path) for path in source_paths}
    placement = read_json(placement_path)
    design = read_json(design_path)
    mapping = read_json(mapping_path)['blocks']['mc_local_power']['references']
    native_net_for_pad={(node.attrib['ref'],node.attrib['pin']):net.attrib['name']
                        for net in ET.parse(netlist_path).getroot().findall('./nets/net') for node in net.findall('node')}
    board = pcbnew.LoadBoard(str(base_path))
    if len(board.Zones()) != 0:
        raise ValueError('Selected route review expects no planes/zones; refuses to modify filled planes')
    original_track_ids = {track.m_Uuid.AsString() for track in board.GetTracks()}
    footprints = {fp.GetReference():fp for fp in board.GetFootprints()}
    pads = {(ref,pad.GetNumber()):pad for ref,fp in footprints.items() for pad in fp.Pads()}
    physical_refs = {ref for ref,row in design['components'].items() if row['physical']}
    if set(placement['positions']) != physical_refs:
        raise ValueError('Incomplete or extra local-power placement references')
    for ref,position in placement['positions'].items():
        fp = footprints[mapping[ref]]
        angle_error=(fp.GetOrientationDegrees()-position[2]+180)%360-180
        if not same_xy(mmxy(fp.GetPosition()),position[:2]) or abs(angle_error) > .000001:
            raise ValueError(f'Source placement has changed for {ref}')
    if len(placement['critical_connections']) != 10:
        raise ValueError('Only the ten reviewed connections may be routed')
    board.BuildConnectivity()
    negative_controls={}
    for index,connection in enumerate(placement['critical_connections'],1):
        start=(mapping[connection['from'][0]],connection['from'][1])
        goal=(mapping[connection['to'][0]],connection['to'][1])
        negative_controls[f'MC_POWER_{index:02d}']=native_reachable(board,pads[start],goal)
    if any(negative_controls.values()):
        raise ValueError('An intended connection is already routed on the base; do not duplicate it')

    output_dir.mkdir(parents=True)
    target = output_dir/'motion-card-power-routed.kicad_pcb'
    # The native project rules and footprint library context are copied alongside
    # the candidate; no source project, footprint or revision file is edited.
    project = read_json(base_path.with_suffix('.kicad_pro'))
    project.setdefault('meta', {})['filename'] = target.with_suffix('.kicad_pro').name
    write_json(target.with_suffix('.kicad_pro'), project)
    for directory in base_path.parent.glob('*.pretty'):
        shutil.copytree(directory, output_dir/directory.name)
    if (base_path.parent/'fp-lib-table').exists():
        shutil.copy2(base_path.parent/'fp-lib-table', output_dir/'fp-lib-table')
    baseline_drc = native_drc(base_path, output_dir, 'baseline-drc')
    connections = []
    new_ids = set()
    for index,connection in enumerate(placement['critical_connections'],1):
        a_original, b_original = connection['from'], connection['to']
        a_key = (mapping[a_original[0]],a_original[1])
        b_key = (mapping[b_original[0]],b_original[1])
        a_pad,b_pad = pads[a_key],pads[b_key]
        intended_net = connection['net']
        if design['components'][a_original[0]]['pins'][a_original[1]] != intended_net or design['components'][b_original[0]]['pins'][b_original[1]] != intended_net:
            raise ValueError(f'Circuit pad/net mismatch in connection {index}')
        native_net=native_net_for_pad[a_key]
        if native_net_for_pad[b_key] != native_net or a_pad.GetNetname() != native_net or b_pad.GetNetname() != native_net:
            raise ValueError(f'Native board net differs from circuit in connection {index}')
        if not same_xy(mmxy(a_pad.GetPosition()),connection['suggested_centerline_mm'][0]) or not same_xy(mmxy(b_pad.GetPosition()),connection['suggested_centerline_mm'][-1]):
            raise ValueError(f'Native pad coordinates differ in connection {index}')
        segments=[]
        for start,end,width in route_plan(connection):
            if start == end or not all(7 <= point[0] <= 58 and 10 <= point[1] <= 78 for point in [start,end]):
                raise ValueError('Invalid route geometry or route outside region')
            track=pcbnew.PCB_TRACK(board)
            track.SetStart(vector(start))
            track.SetEnd(vector(end))
            track.SetWidth(pcbnew.FromMM(width))
            track.SetLayer(pcbnew.F_Cu)
            track.SetNetCode(a_pad.GetNetCode())
            board.Add(track)
            identifier=track.m_Uuid.AsString()
            new_ids.add(identifier)
            segments.append({'uuid':identifier, 'start_mm':start, 'end_mm':end,
                             'width_mm':width, 'layer':'F.Cu', 'net':native_net})
        connections.append({'id':f'MC_POWER_{index:02d}', 'from_original':a_original,'to_original':b_original,
                            'from':list(a_key),'to':list(b_key),'net':native_net,'logical_net':intended_net,'segments':segments})
    pcbnew.SaveBoard(str(target),board)
    reloaded=pcbnew.LoadBoard(str(target))
    reloaded.BuildConnectivity()
    loaded_pads={(fp.GetReference(),pad.GetNumber()):pad for fp in reloaded.GetFootprints() for pad in fp.Pads()}
    loaded_tracks={track.m_Uuid.AsString():track for track in reloaded.GetTracks()}
    if set(loaded_tracks) != original_track_ids | new_ids:
        raise ValueError('Track identity changed after save/reload')
    endpoint_checks=[]
    for connection in connections:
        start_pad=loaded_pads[tuple(connection['from'])]
        goal=tuple(connection['to'])
        reached=native_reachable(reloaded,start_pad,goal)
        if not reached:
            raise ValueError(f'Native connectivity did not join {connection["id"]}')
        for segment in connection['segments']:
            track=loaded_tracks[segment['uuid']]
            if (not same_xy(mmxy(track.GetStart()),segment['start_mm']) or not same_xy(mmxy(track.GetEnd()),segment['end_mm']) or
                abs(pcbnew.ToMM(track.GetWidth())-segment['width_mm']) > .000001 or
                track.GetNetname() != connection['net'] or track.GetLayer() != pcbnew.F_Cu):
                raise ValueError('Native segment geometry or net changed after reload')
        endpoint_checks.append({'id':connection['id'],'from':connection['from'],'to':connection['to'],
                                'unrouted_negative_control_reached':negative_controls[connection['id']],
                                'native_connectivity_reached':reached,'native_segment_geometry_preserved':True})
    routed_drc=native_drc(target,output_dir,'routed-drc')
    base_signatures={signature(row) for row in baseline_drc.get('violations',[])}
    added_violations=[row for row in routed_drc.get('violations',[]) if signature(row) not in base_signatures]
    route_violations=[row for row in routed_drc.get('violations',[]) if item_ids(row)&new_ids]
    after={str(path.relative_to(ROOT)):sha(path) for path in source_paths}
    source_unchanged=before==after
    for path in source_paths:
        copied=output_dir/'source'/path.relative_to(ROOT)
        copied.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,copied)
        if sha(copied) != before[str(path.relative_to(ROOT))]:
            raise ValueError('A recorded source snapshot changed during the copy')
    passed=source_unchanged and not added_violations and not route_violations
    bundle={'schema_version':1,'status':'review_candidate','base_board_sha256':before[str(base_path.relative_to(ROOT))],
            'original_reference_mapping':mapping,'selected_connections':connections,'track_segments':len(new_ids),
            'layer':'F.Cu','manufacturing_ready':False,
            'width_status':'Provisional geometry: 0.2mm RPJ pad escapes/VOS, 0.4mm outside-package SW/VIN/GND, 0.6mm L-COUT; no ampacity/thermal approval',
            'no_planes_or_vias_added':True}
    write_json(output_dir/'route-bundle.json',bundle)
    review={'schema_version':1,'status':'PASS' if passed else 'FAIL','native_kicad_version':pcbnew.Version(),
            'evidence_level':'native PCB DRC and saved/reloaded copper connectivity/geometry; no physical electrical or thermal measurements',
            'source_inputs_sha256':before,'source_inputs_unchanged':source_unchanged,
            'source_board':str(base_path.relative_to(ROOT)),'routed_copy':str(target.relative_to(ROOT)),
            'routed_copy_sha256':sha(target),'selected_connections':len(connections),'added_track_segments':len(new_ids),
            'planes_added':0,'vias_added':0,'native_endpoint_checks':endpoint_checks,
            'baseline_drc_counts':drc_counts(baseline_drc),'routed_drc_counts':drc_counts(routed_drc),
            'new_drc_violations':added_violations,'violations_involving_added_routes':route_violations,
            'manufacturing_ready':False,'limitations':[
                'Only ten connections were routed. Output-capacitor return loops, complete rail distribution and precision load Kelvin routing remain open.',
                'Unconnected items are expected on this partial board and are reported without exclusion.',
                'Widths and six-layer geometry are provisional; copper weight, thermal behavior and current capacity remain unqualified.',
                'No zones, vias, fabrication files, production approval or physical measurements were generated.']}
    write_json(output_dir/'review.json',review)
    print(json.dumps({key:review[key] for key in ['status','selected_connections','added_track_segments','source_inputs_unchanged',
           'baseline_drc_counts','routed_drc_counts','manufacturing_ready']},indent=2))
    return 0 if passed else 2


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=DEFAULT_BASE)
    parser.add_argument('--output',type=Path,default=DEFAULT_OUTPUT)
    args=parser.parse_args()
    return route(args.base,args.output)


if __name__=='__main__':
    raise SystemExit(main())
