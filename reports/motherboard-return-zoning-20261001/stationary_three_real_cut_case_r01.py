"""One fresh native process for each actual supply/return/stitch cut."""
from pathlib import Path
import sys,json,shutil,argparse
sys.path[:0]=[str(Path.cwd()/'tools')]
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck

ap=argparse.ArgumentParser()
ap.add_argument('--ref')
ap.add_argument('--case',choices=['VCC_branch','cap_return_branch','nearby_Source_Ground_barrel'])
ap.add_argument('--reload',type=Path)
a=ap.parse_args()
D=Path('reports/motherboard-return-zoning-20261001/ROOT93-stationary-bypass-actual-r01')
B=D/'owned-bypass-loop-candidate.kicad_pcb'
owners=json.loads(Path('reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json').read_text())
owner_by_ref={r['ref']:r for r in owners['capacitors']}
receipt=json.loads((D/'receipt.json').read_text())
if a.reload:
    dest=a.reload
    meta=json.loads(dest.with_suffix('.mutation.json').read_text())
    ref=meta['ref'];case=meta['case'];uid=meta['removed_actual_UUID']
else:
    ref=a.ref;case=a.case
    assert ref in {'C19033','C13017','C15004'}
    dest=D/f'actual-cut-{ref}-{case}.kicad_pcb'
    assert not dest.exists()
b=pcbnew.LoadBoard(str(dest if a.reload else B));b.BuildConnectivity()
tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}
fps={f.GetReference():f for f in b.GetFootprints()}
pin=lambda r,p:next(q for q in fps[r].Pads()if q.GetNumber()==p)
owner=owner_by_ref[ref]
cp=pin(ref,owner['cap_power']);cr=pin(ref,owner['cap_return'])
op=pin(owner['power_nodes'][0]['ref'],owner['power_nodes'][0]['pin'])
ogr=pin(owner['return_nodes'][0]['ref'],owner['return_nodes'][0]['pin'])
group=next(g for g in receipt['owned_loops']if g['ref']==ref and g['retained'])
power_via=next(tracks[u]for u in group['new_UUIDs']if tracks[u].Type()==pcbnew.PCB_VIA_T and tracks[u].GetNetname()==cp.GetNetname())
if not a.reload:
    if case=='VCC_branch':
        target=next(tracks[u]for u in group['new_UUIDs']if tracks[u].Type()==pcbnew.PCB_TRACE_T and tracks[u].GetNetname()==cp.GetNetname()and tracks[u].GetLayer()==op.GetParentFootprint().GetLayer())
    elif case=='cap_return_branch':
        target=next(tracks[u]for u in group['new_UUIDs']if tracks[u].Type()==pcbnew.PCB_TRACE_T and tracks[u].GetNetname()==cr.GetNetname())
    else:
        candidates=[tracks[u]for u in group['new_UUIDs']if tracks[u].Type()==pcbnew.PCB_VIA_T and tracks[u].GetNetname()==cr.GetNetname()]
        target=min(candidates,key=lambda t:(t.GetPosition()-power_via.GetPosition()).EuclideanNorm())
        assert (target.GetPosition()-power_via.GetPosition()).EuclideanNorm()<=pcbnew.FromMM(1.)
    uid=target.m_Uuid.AsString()
    b.Remove(target)
    b.BuildConnectivity()
    for suffix in('.kicad_pro','.kicad_dru'):
        shutil.copy2(B.with_suffix(suffix),dest.with_suffix(suffix))
    pcbnew.SaveBoard(str(dest),b)
    write(dest.with_suffix('.mutation.json'),dict(ref=ref,case=case,removed_actual_UUID=uid,before_board_sha256=sha(B),board_sha256=sha(dest)))
assert uid not in {t.m_Uuid.AsString()for t in b.GetTracks()}
conn=b.GetConnectivity()
connected=lambda p,q:q.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in conn.GetConnectedItems(p)}
if case=='VCC_branch':
    assert not connected(cp,op),'The physical VCC cut did not open actual SOURCE pair'
    reason='Actual capacitor1 / receiving VCC SOURCE pair is physically open'
elif case=='cap_return_branch':
    assert not connected(cr,ogr),'The physical Ground branch cut did not open actual SOURCE pair'
    reason='Actual capacitor2 / receiving Ground SOURCE pair is physically open'
else:
    row=dict(return_net=cr.GetNetname(),reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.10)
    checker=NativeCollectedAnnulusCheck(b,{cp.GetNetname():row})
    reason=None
    try:checker.via(power_via,row)
    except ValueError as e:reason=str(e)
    assert reason,'The physical Source stitch cut passed the frozen guard'
out=dest.with_suffix('.fresh-native-review.json'if a.reload else'.review.json')
assert not out.exists()
write(out,dict(passed=True,ref=ref,case=case,board_sha256=sha(dest),persisted_mutation_verified=a.reload is not None,
  actual_removed_UUID=uid,rejection=reason,no_radius_margin_Source_annulus_or_reference_waiver=True))
print(json.dumps(dict(passed=True,ref=ref,case=case,fresh_reload=a.reload is not None,rejection=reason)))
