"""Independent reload/Source/land/physical-cut review of one immutable health cell."""
import argparse, collections, hashlib, json, math, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path('tools').resolve()))
import pcbnew
from hardware_build_assembly import parse, child, value
from hardware_merge_bounded_pcb_delta import dump_board, without_generated_fills, zone_definition
from hardware_route_logic_return import identity, pad_identity, mm
from hardware_populate_motherboard_pcb import pad_template

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def plain(x): return json.loads(json.dumps(x))
def physical_group(board, pad):
    return {pad.m_Uuid.AsString()} | {p.m_Uuid.AsString() for p in board.GetConnectivity().GetConnectedItems(pad) if p.Type()==pcbnew.PCB_PAD_T}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--ref',required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    assert not a.out.exists();a.out.mkdir(parents=True)
    receipt=json.loads((a.candidate.parent/'receipt.json').read_text());before=Path(receipt['before_board'])
    frozen={str(p):sha(p) for p in [before,a.candidate,a.candidate.parent/'receipt.json',Path(__file__)]}
    b0=pcbnew.LoadBoard(str(before));b1=pcbnew.LoadBoard(str(a.candidate));b0.BuildConnectivity();b1.BuildConnectivity()
    f0={f.GetReference():f for f in b0.GetFootprints()};f1={f.GetReference():f for f in b1.GetFootprints()};assert set(f0)==set(f1)
    allowed=set(receipt['old_poses']);assert allowed==set(receipt['new_poses'])
    p0={p.m_Uuid.AsString():p for p in b0.GetPads()};p1={p.m_Uuid.AsString():p for p in b1.GetPads()};assert set(p0)==set(p1)
    for ref in f0:
        x,y=f0[ref],f1[ref]
        assert x.GetFPID().GetLibItemName()==y.GetFPID().GetLibItemName() and x.GetValue()==y.GetValue(),('PART',ref)
        assert collections.Counter(pad_template(p) for p in x.Pads())==collections.Counter(pad_template(p) for p in y.Pads()),('LAND',ref)
        assert {(p.GetNumber(),p.m_Uuid.AsString(),p.GetNetname()) for p in x.Pads()}=={(p.GetNumber(),p.m_Uuid.AsString(),p.GetNetname()) for p in y.Pads()},('PIN',ref)
        if ref not in allowed:
            assert (mm(x.GetPosition()),x.GetOrientationDegrees(),x.GetLayer())==(mm(y.GetPosition()),y.GetOrientationDegrees(),y.GetLayer()),('POSE',ref)
            for p in x.Pads():assert pad_identity(p)==pad_identity(p1[p.m_Uuid.AsString()]),('PAD',ref,p.GetNumber())
    old={t.m_Uuid.AsString():plain(identity(t)) for t in b0.GetTracks()};new={t.m_Uuid.AsString():plain(identity(t)) for t in b1.GetTracks()}
    retired={r['uuid']:r['identity'] for r in receipt['exact_retired_copper']};added={r['uuid']:r['identity'] for r in receipt['exact_added_copper']}
    assert set(old)-set(new)==set(retired);assert set(new)-set(old)==set(added)
    for u in old:
        if u in retired:assert old[u]==retired[u]
        else:assert old[u]==new[u],('RETAINED_CU',u)
    for u in added:assert new[u]==added[u],('NEW_CU',u)
    def zones(board):
        t=parse(without_generated_fills(board.read_text()));return {value(child(z,'uuid')[1]):zone_definition(z) for z in t if isinstance(z,list) and z and z[0]=='zone'}
    assert zones(before)==zones(a.candidate),'ZONE_DEFINITION'
    seen=set();groups=0
    for p in b0.GetPads():
        u=p.m_Uuid.AsString()
        if u in seen:continue
        g=physical_group(b0,p);seen|=g
        if len(g)>1:assert g<=physical_group(b1,p1[u]),('SOURCE_SPLIT',u);groups+=1
    ps={(f.GetReference(),p.GetNumber()):p for f in f1.values() for p in f.Pads() if p.GetNumber()}
    owner=f1[a.ref];cap='C11079' if a.ref=='U11020' else 'C11081';source='C11029' if a.ref=='U11020' else 'C11055'
    endpoint_rows=[]
    for pn,other,opn in [('5',cap,'1'),('2',cap,'2'),('5',source,'1'),('2',source,'2')]:
        p=ps[a.ref,pn];q=ps[other,opn];assert q.m_Uuid.AsString() in physical_group(b1,p),('ACTUAL_OWNER',a.ref,pn,other,opn)
        endpoint_rows.append(dict(owner=[a.ref,pn],endpoint=[other,opn],passed=True))
    private=[]
    for pn in ['1','3','4','6']:
        p=ps[a.ref,pn];other=[q for q in b1.GetPads() if q.GetNetname()==p.GetNetname() and q.m_Uuid.AsString()!=p.m_Uuid.AsString()]
        assert len(other)==1,('PRIVATE_NET_ENDPOINTS',pn,len(other));q=other[0];assert q.m_Uuid.AsString() in physical_group(b1,p),('PRIVATE_SOURCE',pn)
        private.append(dict(pin=pn,net=p.GetNetname(),endpoint=[q.GetParentFootprint().GetReference(),q.GetNumber()],passed=True))
    # A conventional drilled barrel must be outside every fitted SMD land;
    # rounded/oval lands are conservatively bounded by their rotated rectangle.
    drill_rows=[]
    for row in receipt['exact_added_copper']:
        t=next((t for t in b1.GetTracks() if t.m_Uuid.AsString()==row['uuid']),None)
        if not isinstance(t,pcbnew.PCB_VIA):continue
        v=mm(t.GetPosition());r=pcbnew.ToMM(t.GetDrillValue())/2;hits=[];minimum=None
        for pad in b1.GetPads():
            if pad.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD:continue
            c=mm(pad.GetPosition());ang=math.radians(pad.GetOrientationDegrees());dx=v[0]-c[0];dy=v[1]-c[1]
            lx=dx*math.cos(ang)+dy*math.sin(ang);ly=-dx*math.sin(ang)+dy*math.cos(ang);s=mm(pad.GetSize())
            distance=math.hypot(max(abs(lx)-s[0]/2,0),max(abs(ly)-s[1]/2,0))-r
            if minimum is None or distance<minimum['drill_edge_to_conservative_land_mm']:minimum=dict(ref=pad.GetParentFootprint().GetReference(),pin=pad.GetNumber(),drill_edge_to_conservative_land_mm=distance)
            if distance<0:hits.append([pad.GetParentFootprint().GetReference(),pad.GetNumber(),distance])
        assert not hits,('OPEN_VIA_IN_SMD_LAND',row['uuid'],hits)
        drill_rows.append(dict(uuid=row['uuid'],role=row['role'],point_mm=v,nearest_land=minimum,no_open_drill_in_fitted_SMD_land=True))
    # Persist real private-control and receiving-supply breaks, then refill and
    # reload each copy; a net-name-only checker would falsely retain continuity.
    cuts=[];keep=[]
    for pn in ['1','3']:
        p=ps[a.ref,pn];g=physical_group(b1,p)
        q=ps[cap,'1' if pn=='5' else '2'] if pn in ['5','2'] else next(q for q in b1.GetPads() if q.GetNetname()==p.GetNetname() and q.m_Uuid.AsString()!=p.m_Uuid.AsString())
        ids={row['uuid'] for row in receipt['exact_added_copper'] if row['identity'][1]==p.GetNetname()}
        if pn in ['5','2']:ids={row['uuid'] for row in receipt['exact_added_copper'] if row['role'].startswith(a.ref+'_own_') or row['role'] in [a.ref+'_local_positive_transfer',a.ref+'_local_Source_return_stitch',a.ref+'_actual_ground_pin_transfer',a.ref+'_actual_own_Ground_pin']}
        t=parse(without_generated_fills(a.candidate.read_text()));t=[x for x in t if not(isinstance(x,list) and x and x[0] in ['segment','via'] and value(child(x,'uuid')[1]) in ids)]
        cut=a.out/('physical-cut-pin-'+pn+'.kicad_pcb');cut.write_text(dump_board(t))
        for e in ['.kicad_pro','.kicad_dru']:shutil.copyfile(a.candidate.with_suffix(e),cut.with_suffix(e))
        cb=pcbnew.LoadBoard(str(cut));keep.append(cb);pcbnew.ZONE_FILLER(cb).Fill(cb.Zones());pcbnew.SaveBoard(str(cut),cb);reload=pcbnew.LoadBoard(str(cut));keep.append(reload);reload.BuildConnectivity();pm={p.m_Uuid.AsString():p for p in reload.GetPads()}
        connected=q.m_Uuid.AsString() in physical_group(reload,pm[p.m_Uuid.AsString()]);assert not connected,('CUT_NOT_DETECTED',pn)
        cuts.append(dict(pin=pn,retired_actual_copper_UUIDs=sorted(ids),fresh_native_reload_detected_physical_break=True,board_sha256=sha(cut)))
        print('CUT',a.ref,pn,'PASS',flush=True)
    assert all(sha(Path(p))==h for p,h in frozen.items())
    result=dict(passed=True,input_sha256=frozen,allowed_two_component_poses=receipt['new_poses'],all_fitted_parts=len(f1),all_fitted_pad_identities=len(p1),all_old_Source_clusters_preserved=groups,exact_added_Cu=len(added),exact_retired_Cu=len(retired),all_unrelated_Cu_zones_pads_poses_preserved=True,actual_receiving_and_Source_endpoints=endpoint_rows,private_input_and_LED_power_endpoints=private,actual_drill_land_reviews=drill_rows,persisted_physical_negative_controls=cuts,strict_signal_reference_and_loaded_electrical_qualification_separate=True,manufacturing_ready=False)
    (a.out/'receipt.json').write_text(json.dumps(result,indent=2));print('PASS',a.ref,len(added),len(retired),groups,flush=True)
if __name__=='__main__':main()

