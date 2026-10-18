"""Four dedicated ADC ground branches into actual AI_AGND In1 copper.

The original fourteen same-side/no-via capacitor paths are retained exactly.
These supplemental ground vias are parallel branches, never series elements
between a capacitor and AVDD/DVDD/REFCAP. Global plane qualification is separate.
Run with KiCad's bundled Python.
"""
import argparse, collections, json, math, shutil, subprocess
from pathlib import Path
import pcbnew
from hardware_route_owned_bypass_loops import Geometry
from hardware_check_return_corridors import ReturnCheck, circle, covered
from hardware_route_selected_additive import corridor_polygon
from hardware_route_logic_return import xy, mm, identity
from hardware_populate_motherboard_pcb import sha, write
from hardware_layout_ads8684_cell import pad_snapshot, f_only_analysis, f_graph_connected, CAPS
from hardware_apply_adc_capacitor_pcb_delta import source_clusters

CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
NET='/motherboard_analog_input/AI_AGND'
PATHS={'6':[(157.1,261),(158.3,261)],
       '8':[(157.1,262),(158.3,262),(158.3,262.6)],
       '29':[(162.9,263),(161.7,263)],
       '33':[(162.9,261),(164.1,261)]}

def native_drc(board,out,name):
    cmd=[str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(out/(name+'.json')),str(board)]
    p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8');(out/(name+'.log')).write_text(p.stdout+p.stderr,encoding='utf8')
    if p.returncode:raise ValueError('Native DRC did not execute')
    d=json.loads((out/(name+'.json')).read_text());assert not d.get('ignored_checks');return d

def anchor_checks(board,groups):
    b=pcbnew.LoadBoard(str(board));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()};exact={t.m_Uuid.AsString():t for t in b.GetTracks()};check=ReturnCheck(b,{})
    fill=check.reference(NET,b.GetLayerID('In1.Cu'));rows=[]
    for group in groups:
        pin=next(p for p in fps['U14734'].Pads()if p.GetNumber()==group['pin']);ids=group['added_UUIDs']
        if not set(ids)<=set(exact):raise ValueError('Exact dedicated ADC branch item missing')
        items=[exact[u]for u in ids];via=next(t for t in items if isinstance(t,pcbnew.PCB_VIA))
        if any(t.GetNetname()!=NET for t in items)or pin.GetNetname()!=NET:raise ValueError('Quiet ADC branch changed return domain')
        if via.GetWidth(pcbnew.F_Cu)!=pcbnew.FromMM(.5)or via.GetDrillValue()!=pcbnew.FromMM(.2):raise ValueError('Actual ADC ground stitch geometry changed')
        if not covered(circle(tuple(via.GetPosition()),pcbnew.FromMM(.24)),fill):raise ValueError('Quiet ADC stitch lacks actual In1 own fill')
        peers={z.m_Uuid.AsString()for z in b.GetConnectivity().GetConnectedItems(pin)}
        if via.m_Uuid.AsString()not in peers:raise ValueError('Quiet ADC ground branch does not physically reach owner pin')
        if not any(isinstance(z,pcbnew.ZONE)and z.GetNetname()==NET and z.IsOnLayer(b.GetLayerID('In1.Cu')) for z in b.GetConnectivity().GetConnectedItems(via)):
            raise ValueError('Quiet ADC stitch does not physically join actual In1 reference')
        for track in items:
            if isinstance(track,pcbnew.PCB_VIA):continue
            if track.GetLayer()!=pcbnew.F_Cu:raise ValueError('ADC branch uses another signal layer')
        rows.append(dict(owner='U14734',pin=group['pin'],via_uuid=via.m_Uuid.AsString(),return_net=NET,
            actual_native_owner_to_via_connected=True,actual_native_via_to_own_In1_zone_connected=True,
            actual_own_fill_radius_mm=.24,In4_connection_claimed=False,branch_length_mm=group['length_mm']))
    return rows

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('board','adc-receipt','out'):ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();a.out=a.out.resolve();assert not a.out.exists();a.out.mkdir(parents=True)
    adc=json.loads(a.adc_receipt.read_text());assert adc['passed']and len(adc['exact_added_copper_UUIDs'])==183
    inputs={str(p.resolve()):sha(p)for p in [a.board,a.board.with_suffix('.kicad_pro'),a.board.with_suffix('.kicad_dru'),a.adc_receipt,Path(__file__)]}
    dest=a.out/'motherboard-adc-quiet-anchors-candidate.kicad_pcb'
    for p in a.board.parent.iterdir():
        if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,a.out/p.name)
        elif p.name=='fp-lib-table':shutil.copyfile(p,a.out/p.name)
    for ext in ('.kicad_pro','.kicad_dru'):shutil.copyfile(a.board.with_suffix(ext),dest.with_suffix(ext))
    shutil.copyfile(a.board,dest);baseline=native_drc(dest,a.out,'baseline');assert not any(v['severity']=='error'for v in baseline['violations'])
    b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()};old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};lands=pad_snapshot(b)
    if not set(adc['exact_added_copper_UUIDs'])<=set(old):raise ValueError('Actual original183 F ADC paths absent')
    clusters=source_clusters(b,set());g=Geometry(b);check=ReturnCheck(b,{});fill=check.reference(NET,b.GetLayerID('In1.Cu'));groups=[]
    for num,points in PATHS.items():
        pin=next(p for p in fps['U14734'].Pads()if p.GetNumber()==num)
        assert math.dist(mm(pin.GetPosition()),points[0])<1e-6 and pin.GetNetname()==NET
        end=points[-1]
        if not g.via(end,NET)or not g.clear(points,NET,pcbnew.F_Cu):raise ValueError('Frozen full-board ADC branch geometry no longer clear '+num)
        if not covered(circle(tuple(xy(end)),pcbnew.FromMM(.24)),fill):raise ValueError('Frozen own In1 reference absent '+num)
        added=[]
        for start,finish in zip(points,points[1:]):
            t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(NET));t.SetLayer(pcbnew.F_Cu);t.SetStart(xy(start));t.SetEnd(xy(finish));t.SetWidth(pcbnew.FromMM(.20));b.Add(t);g.add(t);added.append(t)
        v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(NET));v.SetPosition(xy(end));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetRemoveUnconnected(True);v.SetIsFree(True);b.Add(v);g.add(v);added.append(v)
        groups.append(dict(pin=num,points_mm=points,length_mm=sum(math.dist(s,e)for s,e in zip(points,points[1:])),added_UUIDs=[t.m_Uuid.AsString()for t in added]))
    pcbnew.SaveBoard(str(dest),b)
    for ext in ('.kicad_pro','.kicad_dru'):shutil.copyfile(a.board.with_suffix(ext),dest.with_suffix(ext))
    final=native_drc(dest,a.out,'drc');fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();actual={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()};errors=[]
    if any(v['severity']=='error'for v in final['violations']):errors.append('New native geometry error')
    if not all(actual.get(k)==v for k,v in old.items()):errors.append('Existing actual copper changed')
    if pad_snapshot(fresh)!=lands:errors.append('Source pad pose/land/net/UUID changed')
    newclusters=source_clusters(fresh,set())
    if not all(set(v)<=set(newclusters.get(k,[]))for k,v in clusters.items()):errors.append('Existing native source pad cluster fragmented')
    beforewarnings=collections.Counter(json.dumps(v,sort_keys=True)for v in baseline['violations']if v['severity']=='warning')
    afterwarnings=collections.Counter(json.dumps(v,sort_keys=True)for v in final['violations']if v['severity']=='warning')
    if afterwarnings-beforewarnings:errors.append('New unsuppressed native warning')
    proof=anchor_checks(dest,groups)
    local=f_only_analysis(dest,a.out/'ADC-F-only-analysis.kicad_pcb');lf={f.GetReference():f for f in local.GetFootprints()};pairs=[]
    for ref,(power,ground)in CAPS.items():
        for cap_pin,owner_pin in [('1',power),('2',ground)]:
            cp=next(p for p in lf[ref].Pads()if p.GetNumber()==cap_pin);op=next(p for p in lf['U14734'].Pads()if p.GetNumber()==owner_pin);passed=f_graph_connected(local,cp,op)
            pairs.append(dict(cap=ref,cap_pin=cap_pin,owner_pin=owner_pin,actual_F_only_connected=passed))
            if not passed:errors.append('Original actual no-via loop lost '+ref+'.'+cap_pin)
    if set(actual)-set(old)!={u for group in groups for u in group['added_UUIDs']}:errors.append('Actual added copper exceeds exact four-branch scope')
    if not all(sha(p)==h for p,h in inputs.items()):errors.append('Frozen input changed')
    write(a.out/'receipt.json',dict(passed=not errors,errors=errors,input_sha256=inputs,board_sha256=sha(dest),
        exact_four_ground_branches=groups,actual_added_copper_items=len(actual)-len(old),actual_added_ground_vias=4,
        actual_native_anchor_proofs=proof,actual_fourteen_F_only_capacitor_pair_proofs=pairs,all_original183F_ADC_items_unchanged=True,
        all_existing_copper_and_source_land_pose_UUID_net_unchanged=True,all_prior_source_pad_clusters_preserved=True,
        native_DRC_errors=sum(v['severity']=='error'for v in final['violations']),native_DRC_warnings=sum(v['severity']=='warning'for v in final['violations']),
        ignored_checks=[],uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),
        global_reference_plane_qualification_pass=False,physical_reference_noise_qualified=False,manufacturing_ready=False))
    if errors:raise ValueError('ADC quiet branch candidate failed '+repr(errors))
    print(json.dumps(dict(passed=True,ground_branches=4,added_copper=len(actual)-len(old),no_via_cap_pairs=14,native_errors=0)))

if __name__=='__main__':main()
