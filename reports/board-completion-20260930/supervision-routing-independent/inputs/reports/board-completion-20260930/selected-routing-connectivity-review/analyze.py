"""Independent read-only native connectivity review, using KiCad Python 10.0.4.

Only retained report copies are written. Negative controls mutate unsaved boards
in memory; original PCB, project and engineering source files stay untouched.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from urllib.request import urlopen

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'hardware/board_review/revisions/20260930-05/motion-card-placement.kicad_pcb'
ROUTED = ROOT / 'reports/board-completion-20260930/selected-routing/motion-card-selected-routed.kicad_pcb'
PUBLISHED = ROOT / 'hardware/board_review/revisions/20260930-06/motion-card-route-candidate.kicad_pcb'
CLI = Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
PRIMARY = ['pcbnew/drc/drc_engine.cpp', 'pcbnew/drc/drc_engine.h',
           'pcbnew/drc/drc_test_provider_connectivity.cpp',
           'pcbnew/connectivity/connectivity_data.cpp', 'pcbnew/connectivity/connectivity_data.h',
           'include/advanced_config.h']


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data): path.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')


def key(p): return (p.GetParentFootprint().GetReference(), p.GetNumber())


def all_pads(board): return [p for f in board.GetFootprints() for p in f.Pads()]


def pad_inventory(board):
    result = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            k = key(pad)
            if k in result: raise ValueError('Duplicate physical pad key: '+repr(k))
            result[k] = {'net':pad.GetNetname(), 'position_nm':list(pad.GetPosition()),
                         'size_nm':list(pad.GetSize()), 'drill_nm':list(pad.GetDrillSize()),
                         'orientation_deg':pad.GetOrientationDegrees(),
                         'shape':int(pad.GetShape()), 'attribute':int(pad.GetAttribute()),
                         'layers_hex':pad.GetLayerSet().FmtHex()}
    return result


def describe(item):
    if item.Type() == pcbnew.PCB_VIA_T: item = pcbnew.Cast_to_PCB_VIA(item)
    result = {'uuid':item.m_Uuid.AsString(), 'type':int(item.Type()), 'net':item.GetNetname()}
    if item.Type() == pcbnew.PCB_PAD_T:
        result.update({'reference':key(item)[0], 'pin':key(item)[1], 'position_nm':list(item.GetPosition())})
    else:
        width = item.GetFrontWidth() if item.Type() == pcbnew.PCB_VIA_T else item.GetWidth()
        result.update({'start_nm':list(item.GetStart()), 'end_nm':list(item.GetEnd()),
                       'layer':item.GetLayerName(), 'width_nm':width})
        if item.Type() == pcbnew.PCB_VIA_T:
            result['drill_nm'] = item.GetDrillValue()
            result['layers_hex'] = item.GetLayerSet().FmtHex()
    return result


def inspect(path, selected):
    board = pcbnew.LoadBoard(str(path))
    board.BuildConnectivity()
    connectivity = board.GetConnectivity()
    by_net = {}
    for pad in all_pads(board):
        if pad.GetNetname(): by_net.setdefault(pad.GetNetname(), []).append(pad)
    rows = []
    for name in selected:
        pads = sorted(by_net[name], key=key)
        wanted_ids = {p.m_Uuid.AsString() for p in pads}
        groups = {}
        for pad in pads:
            # Unlike GetNetItems, GetConnectedItems returns the actual copper
            # connectivity cluster containing this pad. It does not return all
            # unrelated pads merely because they share a net assignment.
            physical = list(connectivity.GetConnectedItems(pad))
            physical_ids = {p.m_Uuid.AsString() for p in physical}
            connected_pads = tuple(sorted(key(i) for i in physical if i.Type() == pcbnew.PCB_PAD_T))
            groups.setdefault(connected_pads, physical)
            if not physical_ids or pad.m_Uuid.AsString() not in physical_ids:
                raise ValueError('Invalid native source-pad cluster')
        traces = [t for t in board.GetTracks() if t.GetNetname() == name]
        closest = None
        if len(groups) == 2:
            g = sorted(groups)
            pad_map = {key(p):p for p in pads}
            a,z = min(((a,z) for a in g[0] for z in g[1]),
                      key=lambda pair: (pad_map[pair[0]].GetPosition()-pad_map[pair[1]].GetPosition()).EuclideanNorm())
            closest = {'from_pad':list(a), 'from_mm':[pcbnew.ToMM(v) for v in pad_map[a].GetPosition()],
                       'to_pad':list(z), 'to_mm':[pcbnew.ToMM(v) for v in pad_map[z].GetPosition()],
                       'is_clearance_approved_route':False}
        rows.append({'net':name, 'source_pads':[describe(p) for p in pads],
                     'physical_pad_clusters':[[list(k) for k in g] for g in sorted(groups)],
                     'pad_cluster_count':len(groups), 'missing_pad_cluster_joins':len(groups)-1,
                     'all_source_pads_physically_connected':len(groups)==1,
                     'closest_pad_join_between_clusters':closest,
                     'track_via_items':len(traces),
                     'source_pad_cluster_members':[[describe(i) for i in g] for g in groups.values()],
                     'track_via_geometry':[describe(t) for t in traces]})
    # Detect isolated copper too, rather than treating pad reachability as a
    # complete inspection of every imported trace item.
    orphan_tracks = []
    for track in board.GetTracks():
        cluster = list(connectivity.GetConnectedItems(track))
        if not any(i.Type() == pcbnew.PCB_PAD_T for i in cluster):
            orphan_tracks.append(describe(track))
    return board, {'uncapped_unconnected_ratsnest_edges':connectivity.GetUnconnectedCount(False),
                   'footprints':len(board.GetFootprints()), 'pads':len(all_pads(board)),
                   'track_via_items':len(board.GetTracks()), 'zones':len(board.Zones()),
                   'selected_net_count':len(rows), 'selected_fully_connected':sum(r['pad_cluster_count']==1 for r in rows),
                   'selected_missing_pad_cluster_joins':sum(r['missing_pad_cluster_joins'] for r in rows),
                   'copper_clusters_without_source_pads':orphan_tracks,
                   'pad_geometry_and_net_inventory':{r+'.'+p: v for (r,p),v in pad_inventory(board).items()},
                   'selected_nets':rows}


def physically_reaches(board, source_key, destination_key):
    board.BuildConnectivity()
    pads = {key(p):p for p in all_pads(board)}
    connected = board.GetConnectivity().GetConnectedItems(pads[source_key])
    return pads[destination_key].m_Uuid.AsString() in {i.m_Uuid.AsString() for i in connected}


def main():
    if (OUT/'review.json').exists(): raise SystemExit('Refusing to overwrite a retained review')
    inputs = [BASE, BASE.with_suffix('.kicad_pro'), ROUTED, ROUTED.with_suffix('.kicad_pro'),
              ROOT/'reports/board-completion-20260930/selected-routing/prepare.json',
              ROOT/'reports/board-completion-20260930/selected-routing/import.json',
              ROOT/'reports/board-completion-20260930/selected-routing/native-drc.json',
              Path(__file__).resolve(), PUBLISHED, PUBLISHED.with_suffix('.kicad_pro')]
    before = {str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in inputs}
    for p in inputs:
        destination = OUT/'source'/p.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, destination)
    primary = {}
    for relative in PRIMARY:
        url = 'https://raw.githubusercontent.com/KiCad/kicad-source-mirror/10.0.4/'+relative
        destination = OUT/'primary/kicad-10.0.4'/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(url, timeout=30) as response: destination.write_bytes(response.read())
        primary[relative] = {'url':url, 'sha256':sha(destination)}
    engine = (OUT/'primary/kicad-10.0.4/pcbnew/drc/drc_engine.cpp').read_text()
    assert '#define EXTENDED_ERROR_LIMIT 499' in engine
    assert 'ii == DRCE_CLEARANCE || ii == DRCE_UNCONNECTED_ITEMS' in engine
    selected = json.loads((OUT/'source'/inputs[4].relative_to(ROOT)).read_text())['selected_nets']
    base_copy = OUT/'source'/BASE.relative_to(ROOT)
    routed_copy = OUT/'source'/ROUTED.relative_to(ROOT)
    baseline, base_result = inspect(base_copy, selected)
    routed, route_result = inspect(routed_copy, selected)
    published_copy = OUT/'source'/PUBLISHED.relative_to(ROOT)
    published, published_result = inspect(published_copy, selected)
    assert base_result['pad_geometry_and_net_inventory'] == route_result['pad_geometry_and_net_inventory']
    assert base_result['pad_geometry_and_net_inventory'] == published_result['pad_geometry_and_net_inventory']
    assert base_result['track_via_items'] == 0
    assert route_result['track_via_items'] == 272
    assert published_result['track_via_items'] == 296
    assert base_result['selected_missing_pad_cluster_joins']-route_result['selected_missing_pad_cluster_joins'] == (
        base_result['uncapped_unconnected_ratsnest_edges']-route_result['uncapped_unconnected_ratsnest_edges'])
    assert not route_result['copper_clusters_without_source_pads']
    example = '/mc_permission/BASE_FIRST'
    source, destination = ('U4001','4'), ('U4002','1')
    assert not physically_reaches(baseline, source, destination)
    assert physically_reaches(routed, source, destination)
    # Control 1: retain the pad and trace net labels, but translate all three
    # joining traces 20mm in memory. PCB files are never saved.
    delete_control = pcbnew.LoadBoard(str(routed_copy))
    displaced = []
    for track in list(delete_control.GetTracks()):
        if track.GetNetname() == example:
            displaced.append(describe(track))
            shift = pcbnew.VECTOR2I(pcbnew.FromMM(20),0)
            track.SetStart(track.GetStart()+shift)
            track.SetEnd(track.GetEnd()+shift)
    deleted_reaches = physically_reaches(delete_control, source, destination)
    assert len(displaced) == 3 and not deleted_reaches
    # Control 2: the diagonal trace keeps its assigned net and coordinates,
    # but moves to the wrong copper layer without vias. Same-net membership
    # must not falsely join this path.
    layer_control = pcbnew.LoadBoard(str(routed_copy))
    diagonal = next(t for t in layer_control.GetTracks() if t.GetNetname()==example
                    and t.GetStart().x != t.GetEnd().x and t.GetStart().y != t.GetEnd().y)
    before_geometry = describe(diagonal)
    diagonal.SetLayer(pcbnew.B_Cu)
    wrong_layer_reaches = physically_reaches(layer_control, source, destination)
    assert not wrong_layer_reaches
    controls = {'example_net':example, 'source_pad':source, 'destination_pad':destination,
                'baseline_reachable':False, 'routed_reachable':True,
                'translate_only_three_traces':{'before':displaced, 'translation_mm':[20,0],
                                          'same_pad_and_trace_net_labels':True,
                                          'reachable':deleted_reaches,
                                          'uncapped_unconnected_edges':delete_control.GetConnectivity().GetUnconnectedCount(False)},
                'change_only_diagonal_to_wrong_layer':{'before':before_geometry, 'after':describe(diagonal),
                                                      'same_net_and_coordinates':True,
                                                      'reachable':wrong_layer_reaches,
                                                      'uncapped_unconnected_edges':layer_control.GetConnectivity().GetUnconnectedCount(False)},
                'mutated_boards_saved':False}
    help_result = subprocess.run([str(CLI), 'pcb', 'drc', '--help'], capture_output=True, text=True)
    (OUT/'cli-drc-help.txt').write_text(help_result.stdout+help_result.stderr, encoding='utf-8')
    drc_path = OUT/'fresh-native-drc.json'
    command = [str(CLI), 'pcb', 'drc', '--format', 'json', '--all-track-errors', '--severity-all',
               '--output',str(drc_path),str(published_copy)]
    run = subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (OUT/'fresh-native-drc.txt').write_text(run.stdout+run.stderr,encoding='utf-8')
    assert run.returncode == 0 and drc_path.exists()
    drc = json.loads(drc_path.read_text())
    drc_counts = {name:dict(Counter(r['type'] for r in drc.get(name,[])))
                  for name in ['violations','unconnected_items','schematic_parity']}
    assert len(drc['unconnected_items']) == 499
    after = {str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in inputs}
    assert before == after, 'Read-only original inputs changed during review'
    copied = {name:sha(OUT/'source'/name) for name in before}
    assert copied == before
    write(OUT/'review.json', {'schema_version':1, 'captured_utc':datetime.now(timezone.utc).isoformat(),
                            'scope':'Read-only native geometric connectivity of the selected supervision routing copy',
                            'kicad_version':pcbnew.GetBuildVersion(), 'original_inputs_unchanged':True,
                            'input_sha256':before, 'copied_sha256':copied,
                            'primary_sources':primary, 'baseline':base_result, 'routed':route_result,
                            'published_revision06':published_result,
                            'negative_controls':controls, 'fresh_native_drc_command':command,
                            'fresh_native_drc_counts':drc_counts,
                            'unconnected_report_category_limit':499,
                            'cli_limit_override_found':False,
                            'manufacturing_ready':False, 'full_card_routing_complete':False,
                            'physical_measurement':False})
    print(json.dumps({'baseline_uncapped':base_result['uncapped_unconnected_ratsnest_edges'],
                      'routed_uncapped':route_result['uncapped_unconnected_ratsnest_edges'],
                      'published_revision06_uncapped':published_result['uncapped_unconnected_ratsnest_edges'],
                      'closed_selected_joins':base_result['selected_missing_pad_cluster_joins']-route_result['selected_missing_pad_cluster_joins'],
                      'fully_connected_selected_nets':route_result['selected_fully_connected'],
                      'remaining_selected_joins':route_result['selected_missing_pad_cluster_joins'],
                      'pad_geometry_and_nets_preserved':True, 'negative_controls_pass':True,
                      'native_drc_report_cap':499, 'review':str(OUT/'review.json')}))


if __name__ == '__main__': main()
