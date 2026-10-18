"""Actual native destructive-copy controls; immutable real PCB never edited."""
import copy,json,hashlib
from pathlib import Path
import pcbnew
from check_same_side_bypass_r01 import check_group
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/motherboard-pcb-integration-20261001/source26-FPGA38-rule-r76/motherboard-literal38-neck-rule-candidate.kicad_pcb'
MP=ROOT/'reports/motherboard-domains-20261001/source26-r76-r01/domain-map.json'
OWNERS=ROOT/'reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json'
HERE=Path(__file__).parent
DEST=HERE/'same-side-native-controls-r01.json'
assert not DEST.exists()
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[BASE,MP,OWNERS,HERE/'same-side-real-circuit-proof-r01.json',HERE/'check_same_side_bypass_r01.py',Path(__file__)]
frozen={str(p):sha(p)for p in files}
positive=read(files[3]);assert positive['passed']
original=next(v for v in positive['actual_circuit_checks']if v['ref']=='C13013')
row=next(v for v in read(OWNERS)['capacitors']if v['ref']=='C13013')
results=[]
for mode in ['missing_supply_trace','real_supply_via','opposite_layer_supply','NC_source_endpoint','wrong_source_net','missing_adjacent_reference','cut_actual_surface_return','remove_unused_far_reference']:
    b=pcbnew.LoadBoard(str(BASE));m=read(MP);g=copy.deepcopy(original['group']);removed=[]
    exact={t.m_Uuid.AsString():t for t in b.GetTracks()}
    t=exact[g['complete_supply_branch_UUIDs'][0]]
    if mode=='missing_supply_trace':
        removed.append(t);b.Remove(t)
    elif mode=='real_supply_via':
        v=pcbnew.PCB_VIA(b);v.SetNet(t.GetNet());v.SetPosition(t.GetStart());v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v);g['complete_supply_branch_UUIDs'].append(v.m_Uuid.AsString())
    elif mode=='opposite_layer_supply':
        t.SetLayer(pcbnew.B_Cu)
    elif mode in ['NC_source_endpoint','wrong_source_net']:
        source=next(p for p in m['pads']if p['reference']=='C13013'and p['pin']==row['cap_power'])
        if mode=='NC_source_endpoint':source['native_nc']=True
        else:source['net']='/DELIBERATELY_WRONG'
    elif mode in ['missing_adjacent_reference','remove_unused_far_reference']:
        layer=pcbnew.In1_Cu if mode=='missing_adjacent_reference'else pcbnew.In4_Cu
        for z in b.Zones():
            if z.GetNetname()==original['review']['return_net']and z.IsOnLayer(layer):z.UnFill()
    elif mode=='cut_actual_surface_return':
        ids={u for ep in original['review']['actual_return_endpoint_reviews']for a in ep['anchors']for u in a['actual_surface_ground_path']['actual_surface_trace_UUIDs']}
        for ident in ids:removed.append(exact[ident]);b.Remove(exact[ident])
    expected=mode=='remove_unused_far_reference'
    try:
        r=check_group(b,g,row,m);accepted=True;reason=None
    except ValueError as error:
        accepted=False;reason=str(error)
    result=dict(mode=mode,expected_acceptance=expected,actual_acceptance=accepted,passed=accepted==expected,rejection=reason,actual_native_copy_only=True)
    results.append(result);print(result,flush=True)
assert frozen=={p:sha(Path(p))for p in frozen}
DEST.write_text(json.dumps(dict(passed=all(r['passed']for r in results),inputs=frozen,cases=results,no_actual_board_or_old_guard_changes=True,new_router_authorized=False),indent=2)+'\n')
assert all(r['passed']for r in results)
