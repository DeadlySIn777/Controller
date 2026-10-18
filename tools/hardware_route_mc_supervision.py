"""Join the eleven missing supervision clusters on an immutable rev06 COPY.

Manual 0.2mm signal routes with 0.6/0.3mm through vias. Inner signal-layer
assignment is a six-layer review candidate, not an approved production stackup.
No planes, power routes or fabrication outputs. Two WDI segments are replaced
locally to open a real escape; all other original items remain unchanged.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import pcbnew

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'hardware/board_review/revisions/20260930-06/motion-card-route-candidate.kicad_pcb'
OUT=ROOT/'reports/board-completion-20260930/supervision-routing/manual-v1'
ANALYZER=ROOT/'reports/board-completion-20260930/selected-routing-connectivity-review/analyze.py'
SELECTED=ROOT/'reports/board-completion-20260930/selected-routing/prepare.json'
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,data): path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def xy(point): return pcbnew.VECTOR2I(pcbnew.FromMM(point[0]),pcbnew.FromMM(point[1]))
def mm(point): return [round(pcbnew.ToMM(point.x),6),round(pcbnew.ToMM(point.y),6)]


def analysis_module():
    spec=importlib.util.spec_from_file_location('native_physical_cluster_analysis',ANALYZER)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Endpoint keys come from native physical-cluster analysis, not assigned-net
# membership. Surface escapes are listed independently so nearby fine-pitch
# through vias may be staggered while source pads stay fixed.
JOINS=[
 {'id':'WD_M_OK','net':'/WD_M_OK','from':['U3005','6'],'to':['R3009','1'],'layer':'In1.Cu',
  'a_escape':[[206.1375,21.05],[205.1375,21.05]],'b_escape':[[174.175,34],[173.175,34]],
  'inner':[[205.1375,21.05],[192.1875,34],[173.175,34]]},
 {'id':'WD_M_SET1_BUF','net':'/WD_M_SET1_BUF','from':['R3011','1'],'to':['U4017','2'],'layer':'In3.Cu',
  'a_escape':[[156.175,39],[155.175,39]],'b_escape':[[168.6,70.75],[167.7,70.75],[167.3,70.5]],
  'inner':[[155.175,39],[155.175,70.5],[167.3,70.5]]},
 {'id':'WD_O_OK','net':'/WD_O_OK','from':['U3005','4'],'to':['U4004','3'],'layer':'In2.Cu',
  'a_escape':[[206.1375,22.95],[207.1375,22.95]],'b_escape':[[178.3625,49.95],[177.3625,49.95]],
  'inner':[[207.1375,22.95],[180.1375,49.95],[177.3625,49.95]]},
 {'id':'WD_O_SET1_BUF','net':'/WD_O_SET1_BUF','from':['U3007','4'],'to':['U3002','5'],'layer':'In2.Cu',
  'a_escape':[[183.8375,34.65],[184.8375,34.65]],'b_escape':[[185.4,21.975],[184.534,22.475]],
  'inner':[[184.8375,34.65],[184.8375,22.7785],[184.534,22.475]]},
 {'id':'ARM_O_Q','net':'/mc_permission/ARM_O_Q','from':['U4006','5'],'to':['U4008','1'],'layer':'In1.Cu',
  'a_escape':[[199.9,49.75],[200.9,49.75]],'b_escape':[[149.8625,59.05],[150.3625,58.184]],
  'inner':[[200.9,49.75],[192.466,58.184],[150.3625,58.184]]},
 {'id':'PERMIT_OUT_DRIVE','net':'/mc_permission/PERMIT_OUT_DRIVE','from':['U4009','3'],'to':['R4018','1'],'layer':'In3.Cu',
  'a_escape':[[159.1,60.25],[158.2,60.25],[157.8,60.49]],'b_escape':[[205.175,82],[204.175,82]],
  'inner':[[157.8,60.49],[159.81,62.5],[184.675,62.5],[204.175,82]]},
 {'id':'PERMIT_OUT_REQ','net':'/mc_permission/PERMIT_OUT_REQ','from':['U4009','6'],'to':['R4007','1'],'layer':'In2.Cu',
  'a_escape':[[161.9,60.25],[162.9,60.25]],'b_escape':[[191.175,78],[191.175,79]],
  'inner':[[162.9,60.25],[172.425,60.25],[191.175,79]]},
 {'id':'TAMPER_CLEAR_N','net':'/mc_permission/TAMPER_CLEAR_N','from':['R4012','1'],'to':['U4002','6'],'layer':'In4.Cu',
  'a_escape':[[163.175,82],[162.175,82]],'b_escape':[[161.6375,48.05],[162.8875,48.05]],
  'inner':[[162.175,82],[162.175,48.7625],[162.8875,48.05]]},
 {'id':'WD_M_TRIP_CLEAR_N','net':'/mc_permission/WD_M_TRIP_CLEAR_N','from':['U4019','7'],'to':['U4014','6'],'layer':'In4.Cu',
  'a_escape':[[190.4,70.75],[191.4,70.75]],'b_escape':[[209.4,60.25],[210.4,60.25]],
  'inner':[[191.4,70.75],[199.9,70.75],[210.4,60.25]]},
 {'id':'WD_M_TRIP_Q','net':'/mc_permission/WD_M_TRIP_Q','from':['U4017','1'],'to':['U4014','5'],'layer':'In1.Cu',
  'a_escape':[[168.6,70.25],[168.1,70.25],[168.1,69.55],[167.6,69.55]],
  'b_escape':[[209.4,60.75],[209.9,60.75],[209.9,61.45],[211.2,61.45]],
  'inner':[[167.6,69.55],[203.1,69.55],[211.2,61.45]]},
 {'id':'WD_M_HEALTH_RAW','net':'/watchdog_conditioning/WD_M_HEALTH_RAW','from':['R3001','2'],'to':['U3001','8'],'layer':'In4.Cu',
  'a_escape':[[163,20.175],[163,19.175]],'b_escape':[[159.4,20.35],[160.4,20.35]],
  'b_anchor_on_retained_copper':True,
  'inner':[[163,19.175],[161.575,19.175],[160.4,20.35]]}
]


def native_drc(path,out,stem):
    command=[str(CLI),'pcb','drc','--format','json','--all-track-errors','--severity-all','--output',str(out/(stem+'.json')),str(path)]
    run=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (out/(stem+'.txt')).write_text(run.stdout+run.stderr,encoding='utf-8')
    if run.returncode!=0: raise RuntimeError('Native DRC failed to execute')
    return json.loads((out/(stem+'.json')).read_text())


def route(base,out):
    base=base.resolve();out=out.resolve()
    if out.is_relative_to(ROOT/'hardware') or out.exists(): raise ValueError('Use a fresh report directory, never a hardware/source location')
    inputs=[base,base.with_suffix('.kicad_pro'),SELECTED,ANALYZER,Path(__file__).resolve()]
    before={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in inputs}
    analysis=analysis_module()
    selected=json.loads(SELECTED.read_text())['selected_nets']
    board,baseline=analysis.inspect(base,selected)
    if baseline['track_via_items']!=296 or baseline['selected_missing_pad_cluster_joins']!=11 or baseline['selected_net_count']!=41:
        raise ValueError('Immutable rev06 baseline differs from the reviewed296-item/11-join/41-net scope')
    if board.GetCopperLayerCount()!=6 or len(board.Zones()): raise ValueError('Expected six-layer candidate without planes')
    old_items={t.m_Uuid.AsString():analysis.describe(t) for t in board.GetTracks()}
    original_pads=analysis.pad_inventory(board)
    pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in board.GetPads()}
    for join in JOINS:
        a,b=pads[tuple(join['from'])],pads[tuple(join['to'])]
        if a.GetNetname()!=join['net'] or b.GetNetname()!=join['net']: raise ValueError('Pad/net identity mismatch')
        if mm(a.GetPosition())!=join['a_escape'][0]: raise ValueError('Exact source pad position differs')
        if join.get('b_anchor_on_retained_copper'):
            cluster=board.GetConnectivity().GetConnectedItems(b)
            if not any(i.Type()==pcbnew.PCB_TRACE_T and i.IsOnLayer(pcbnew.F_Cu) and i.GetEffectiveShape(pcbnew.F_Cu).Collide(xy(join['b_escape'][0])) for i in cluster):
                raise ValueError('Proposed anchor is not on retained physically connected copper')
        elif mm(b.GetPosition())!=join['b_escape'][0]: raise ValueError('Exact destination pad position differs')
        if analysis.physically_reaches(board,tuple(join['from']),tuple(join['to'])): raise ValueError('Join already present')
        if join['inner'][0]!=join['a_escape'][-1] or join['inner'][-1]!=join['b_escape'][-1]: raise ValueError('Escape and inner route geometry do not meet')
    out.mkdir(parents=True)
    target=out/'motion-card-supervision-routed.kicad_pcb'
    shutil.copy2(base.with_suffix('.kicad_pro'),target.with_suffix('.kicad_pro'))
    if (base.parent/'fp-lib-table').exists(): shutil.copy2(base.parent/'fp-lib-table',out/'fp-lib-table')
    for directory in base.parent.glob('*.pretty'): shutil.copytree(directory,out/directory.name)
    baseline_drc=native_drc(base,out,'baseline-drc')
    removed_original=[];replacement_items=[];removed_handles=[]
    old_wdi_segments={((159.9541,19.6035),(159.9541,20.9158)),((159.9541,20.9158),(159.5449,21.325))}
    for item in list(board.GetTracks()):
        if item.GetNetname()=='/watchdog_conditioning/WD_M_WDI_BUF' and (tuple(mm(item.GetStart())),tuple(mm(item.GetEnd()))) in old_wdi_segments:
            removed_original.append(analysis.describe(item));board.Remove(item);removed_handles.append(item)
    if len(removed_original)!=2: raise ValueError('Exact two-segment WDI local replacement differs')
    # Rebuild the native container after removal before adding replacements;
    # native connectivity must not retain removed-track graph objects.
    board.BuildConnectivity()
    wdi_pad=pads[('U3001','6')]
    replacement_path=[[159.9541,19.6035],[161.3,19.6035],[161.3,20.9158],[160.8908,21.325],[159.5449,21.325]]
    for start,end in zip(replacement_path,replacement_path[1:]):
        item=pcbnew.PCB_TRACK(board);item.SetStart(xy(start));item.SetEnd(xy(end));item.SetWidth(pcbnew.FromMM(.2))
        item.SetLayer(pcbnew.F_Cu);item.SetNetCode(wdi_pad.GetNetCode());board.Add(item);replacement_items.append(analysis.describe(item))
    routes=[]
    for join in JOINS:
        source_pad=pads[tuple(join['from'])]
        added=[]
        for points,layer in [(join['a_escape'],pcbnew.F_Cu),(join['b_escape'],pcbnew.F_Cu),
                             (join['inner'],board.GetLayerID(join['layer']))]:
            for start,end in zip(points,points[1:]):
                track=pcbnew.PCB_TRACK(board);track.SetStart(xy(start));track.SetEnd(xy(end))
                track.SetWidth(pcbnew.FromMM(.2));track.SetLayer(layer);track.SetNetCode(source_pad.GetNetCode());board.Add(track)
                added.append(analysis.describe(track))
        for position in [join['a_escape'][-1],join['b_escape'][-1]]:
            via=pcbnew.PCB_VIA(board);via.SetPosition(xy(position));via.SetWidth(pcbnew.FromMM(.6));via.SetDrill(pcbnew.FromMM(.3))
            via.SetViaType(pcbnew.VIATYPE_THROUGH);via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
            via.SetNetCode(source_pad.GetNetCode());board.Add(via);added.append(analysis.describe(via))
        routes.append({'id':join['id'],'net':join['net'],'from':join['from'],'to':join['to'],
                       'inner_signal_layer':join['layer'],'surface_escape_layer':'F.Cu','new_items':added})
    pcbnew.SaveBoard(str(target),board)
    loaded,after=analysis.inspect(target,selected)
    loaded_items={t.m_Uuid.AsString():analysis.describe(t) for t in loaded.GetTracks()}
    new_items={i['uuid']:i for route in routes for i in route['new_items']}
    new_items.update({i['uuid']:i for i in replacement_items})
    removed_ids={i['uuid'] for i in removed_original}
    retained_items={uid:item for uid,item in old_items.items() if uid not in removed_ids}
    if original_pads!=analysis.pad_inventory(loaded): raise ValueError('Pad geometry/net inventory changed')
    if any(loaded_items.get(uid)!=item for uid,item in retained_items.items()): raise ValueError('Retained routing item changed')
    if any(loaded_items.get(uid)!=item for uid,item in new_items.items()): raise ValueError('New routing geometry/net changed on roundtrip')
    if set(loaded_items)!=set(retained_items)|set(new_items): raise ValueError('Unexpected routing items after roundtrip')
    drc=native_drc(target,out,'routed-drc')
    # Removing one complete newly-added join must restore the missing cluster
    # without changing any pad's net label. The negative control is not saved.
    control=pcbnew.LoadBoard(str(target));removed=[]
    remove_ids={i['uuid'] for i in routes[4]['new_items']}
    for item in list(control.GetTracks()):
        if item.m_Uuid.AsString() in remove_ids: removed.append(analysis.describe(item));control.Remove(item)
    control_reaches=analysis.physically_reaches(control,tuple(routes[4]['from']),tuple(routes[4]['to']))
    copied_inputs={}
    for path in inputs:
        dest=out/'source'/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
        copied_inputs[str(path.relative_to(ROOT)).replace('\\','/')]=sha(dest)
    unchanged=before=={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in inputs}==copied_inputs
    complete=after['selected_fully_connected']==41 and after['selected_missing_pad_cluster_joins']==0
    passed=unchanged and complete and not drc['violations'] and not control_reaches and not after['copper_clusters_without_source_pads']
    review={'schema_version':1,'status':'PASS' if passed else 'FAIL','native_kicad_version':pcbnew.Version(),
            'input_sha256':before,'source_inputs_unchanged':unchanged,'copied_input_sha256':copied_inputs,
            'baseline':baseline,'routed':after,'original_items_retained_exactly':len(retained_items),
            'exact_original_items_removed':removed_original,'exact_replacement_items':replacement_items,'pad_net_geometry_inventory_preserved_exactly':True,
            'new_items_roundtrip_preserved_exactly':True,'new_items':len(new_items),
            'drc_regular_violations':drc['violations'],'baseline_regular_violations':baseline_drc['violations'],
            'drc_unconnected_reported':len(drc['unconnected_items']),
            'negative_copper_removal':{'net':routes[4]['net'],'removed':removed,'pads_keep_net_labels':True,
                                      'physically_reaches_after_removal':control_reaches,
                                      'uncapped_edges_after_removal':control.GetConnectivity().GetUnconnectedCount(False),'control_saved':False},
            'output_board':str(target.relative_to(ROOT)).replace('\\','/'),'output_board_sha256':sha(target),
            'manufacturing_ready':False,'physical_measurement':False,
            'limitations':['Only41 selected supervision nets are physically complete if review passes; full card remains unconnected.',
                           'Inner layers are provisional signal assignments on existing six-layer candidate. Reference planes, stackup, EMC and timing remain unqualified.',
                           '0.2mm tracks and0.6/0.3mm through vias are geometric candidates, not approved production processes or thermal/current ratings.',
                           'No planes, power routing, fabrication files or published-board changes.']}
    write(out/'route-bundle.json',{'schema_version':1,'base_board_sha256':before[str(base.relative_to(ROOT)).replace('\\','/')],
                                 'preserved_input_items':len(retained_items),'removed_input_items':removed_original,
                                 'replacement_items':replacement_items,'selected_nets':selected,'routes':routes,'new_track_via_items':len(new_items),
                                 'manufacturing_ready':False})
    write(out/'review.json',review)
    print(json.dumps({'status':review['status'],'existing_items_preserved':len(retained_items),'existing_items_replaced':len(removed_original),'new_items':len(new_items),
                      'before_uncapped':baseline['uncapped_unconnected_ratsnest_edges'],'after_uncapped':after['uncapped_unconnected_ratsnest_edges'],
                      'selected_complete':after['selected_fully_connected'],'selected_missing_joins':after['selected_missing_pad_cluster_joins'],
                      'regular_DRC_violations':len(drc['violations']),'control_disconnected':not control_reaches,'source_unchanged':unchanged},indent=2))
    return 0 if passed else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--base',type=Path,default=BASE);parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args();raise SystemExit(route(args.base,args.output))
