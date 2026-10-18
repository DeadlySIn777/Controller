"""Independently inspect the actual C14012 filter, including native cut probes.

Source-ground reachability, an adjacent flashed annulus and projected real
return copper are distinct checks. These do not qualify EMC or whole-board
manufacturing. The source and input PCB remain unchanged.
"""
import argparse,collections,json,math,shutil,sys
from pathlib import Path
import pcbnew
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import circle,covered
from hardware_route_selected_additive import corridor_polygon
from hardware_populate_motherboard_pcb import sha,write
from hardware_route_logic_return import mm

def inspect(board,signal_ids,via_id):
    board.BuildConnectivity();conn=board.GetConnectivity()
    fps={fp.GetReference():fp for fp in board.GetFootprints()}
    pad=lambda r,n:next(p for p in fps[r].Pads()if p.GetNumber()==n)
    cp,cr,op,og=pad('C14012','1'),pad('C14012','2'),pad('U14014','11'),pad('U14014','7')
    if cp.GetNetname()!=op.GetNetname()or cr.GetNetname()!=og.GetNetname()or cr.GetNetname()!='/LOGIC_GND':
        raise ValueError('Exact actual source filter/ground pin identity differs')
    connected=lambda p,q:q.m_Uuid.AsString()in {i.m_Uuid.AsString()for i in conn.GetConnectedItems(p)}
    if not connected(cp,op):raise ValueError('Actual signal capacitor/input pair is open')
    if not connected(cr,og):raise ValueError('Actual capacitor/receiver source-ground pair is open')
    if fps['C14012'].GetLayer()!=pcbnew.F_Cu or fps['U14014'].GetLayer()!=pcbnew.F_Cu:
        raise ValueError('Actual sameF filter source layout differs')
    items={i.m_Uuid.AsString():i for i in board.GetTracks()}
    via=items.get(via_id)
    if not isinstance(via,pcbnew.PCB_VIA)or via.GetNetname()!=cr.GetNetname():raise ValueError('Actual own ground via is missing/wrong')
    if math.dist(mm(cr.GetPosition()),mm(via.GetPosition()))>2.:raise ValueError('Local receiving ground transition exceeds2mm layout screen')
    if not via.FlashLayer(pcbnew.In1_Cu)or not conn.IsConnectedOnLayer(via,pcbnew.In1_Cu):
        raise ValueError('Ground drill lacks actual flashed/native-connected adjacent reference annulus')
    own=collect_native_reference_fills(board,{cr.GetNetname()},[pcbnew.In1_Cu]).get((cr.GetNetname(),pcbnew.In1_Cu))
    if own is None or not covered(circle(tuple(via.GetPosition()),pcbnew.FromMM(.24)),own):
        raise ValueError('Actual adjacent own reference does not cover the ground annulus')
    length=0.
    for ident in signal_ids:
        track=items.get(ident)
        if track is None or isinstance(track,pcbnew.PCB_VIA)or track.GetLayer()!=pcbnew.F_Cu or track.GetNetname()!=cp.GetNetname():
            raise ValueError('Exact actual F signal copper missing/wrong')
        if not covered(corridor_polygon(tuple(track.GetStart()),tuple(track.GetEnd()),pcbnew.FromMM(.2)),own):
            raise ValueError('Actual signal corridor crosses a missing own-reference boundary')
        length+=math.dist(mm(track.GetStart()),mm(track.GetEnd()))
    if not signal_ids or length>8.:raise ValueError('Declared actual signal exceeds8mm layout screen')
    return dict(actual_signal_and_source_ground_pairs_connected=True,
        actual_ground_annulus_flashed_and_native_connected_on_In1=True,
        actual_projected_F_signal_corridor_covered_by_own_In1=True,
        actual_signal_mm=length,actual_ground_transition_mm=math.dist(mm(cr.GetPosition()),mm(via.GetPosition())),
        measured_filter_or_EMC_qualified=False,whole_board_manufacturing_qualified=False)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in('before','board','source','out'):ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Fresh immutable output required')
    source=json.loads((a.source/'design.json').read_text())['components']
    if source['C14012']['mpn']!='GRM1885C2A103JA01D'or source['C14012']['pins']!={'1':'MPG_ENABLE_CONDITIONED','2':'LOGIC_GND'}or source['U14014']['mpn']!='SN74LVC14APWR':
        raise ValueError('Actual source-owned filter identity differs')
    paths=[a.before,a.board,a.source/'design.json',Path(__file__)]
    # Bind the actual native geometry implementations used by this review.
    paths.extend(Path(sys.modules[name].__file__) for name in (
        'hardware_collect_native_reference_fills','hardware_check_return_corridors',
        'hardware_route_selected_additive','hardware_populate_motherboard_pcb',
        'hardware_route_logic_return'))
    frozen={str(p.resolve()):sha(p)for p in paths}
    before=pcbnew.LoadBoard(str(a.before));board=pcbnew.LoadBoard(str(a.board))
    old={i.m_Uuid.AsString()for i in before.GetTracks()};added=[i for i in board.GetTracks()if i.m_Uuid.AsString()not in old]
    vias=[i for i in added if isinstance(i,pcbnew.PCB_VIA)and i.GetNetname()=='/LOGIC_GND']
    signal=[i.m_Uuid.AsString()for i in added if not isinstance(i,pcbnew.PCB_VIA)and i.GetNetname()=='/motherboard_operator/MPG_ENABLE_CONDITIONED']
    if len(vias)!=1:raise ValueError('Exactly one actual new local ground transition required')
    positive=inspect(board,signal,vias[0].m_Uuid.AsString());a.out.mkdir(parents=True)
    cases=[]
    cap=next(fp for fp in board.GetFootprints()if fp.GetReference()=='C14012')
    cp=next(p for p in cap.Pads()if p.GetNumber()=='1')
    near=next(i.m_Uuid.AsString()for i in added if i.m_Uuid.AsString()in signal and i.HitTest(cp.GetPosition()))
    for name,cut in [('missing-real-signal-branch',near),('missing-real-ground-transition',vias[0].m_Uuid.AsString())]:
        probe=pcbnew.LoadBoard(str(a.board));removed=next(i for i in probe.GetTracks()if i.m_Uuid.AsString()==cut);probe.Remove(removed)
        candidate=a.out/(name+'.kicad_pcb');pcbnew.SaveBoard(str(candidate),probe)
        reloaded=pcbnew.LoadBoard(str(candidate));reloaded.BuildConnectivity()
        probe_fps={f.GetReference():f for f in reloaded.GetFootprints()}
        probe_pin=lambda ref,num:next(p for p in probe_fps[ref].Pads() if p.GetNumber()==num)
        first,second=(('C14012','1'),('U14014','11')) if name=='missing-real-signal-branch' else (('C14012','2'),('U14014','7'))
        source,target=probe_pin(*first),probe_pin(*second)
        physically_joined=target.m_Uuid.AsString() in {i.m_Uuid.AsString() for i in reloaded.GetConnectivity().GetConnectedItems(source)}
        if physically_joined:raise ValueError('Serialized cut did not physically open the actual source-pin pair: '+name)
        try:inspect(reloaded,signal,vias[0].m_Uuid.AsString())
        except ValueError as error:cases.append(dict(case=name,rejected=True,actual_source_pin_pair_physically_open=True,reason=str(error),board_sha256=sha(candidate)))
        else:raise ValueError('Actual serialized native cut was incorrectly accepted: '+name)
    if any(sha(Path(p))!=h for p,h in frozen.items()):raise ValueError('Frozen source/input changed during independent review')
    result=dict(passed=True,input_sha256=frozen,positive=positive,persisted_native_cut_cases=cases,
        source_pin_nets_and_input_PCB_unchanged=True,manufacturing_ready=False)
    write(a.out/'review.json',result);print(json.dumps(result['positive']))

if __name__=='__main__':main()
