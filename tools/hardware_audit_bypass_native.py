"""Measure exact, manufacturer-pin-owned capacitors on the actual native PCB.

Geometric placement targets are screens, not manufacturer maxima or measured
loop impedance. Actual supply/return net parity is mandatory for every row.
"""
import argparse,json,math
from pathlib import Path
import pcbnew
from hardware_populate_motherboard_pcb import sha,write

ROOT=Path(__file__).resolve().parents[1]
MANIFESTS=(ROOT/'reports/motherboard-power-entry-20260930/layout-r07/capacitor-owners.json',
    ROOT/'reports/motherboard-power-entry-20260930/layout-r07/mc-diagnostics-capacitor-owners.json',
    ROOT/'reports/motherboard-bypass-owners-20260930/r03-wide-input-frozen/AI_COMMS_BYPASS_PLACEMENT.json',
    ROOT/'reports/motherboard-status-20260930/bypass-owners-r01.json')

def owners():
    rows=[]
    for path in MANIFESTS[:2]:
        for r in json.loads(path.read_text())['capacitors']:
            rows.append(dict(ref=r['ref'],owner=r['owner_ref'],cap_power='1',cap_return='2',
                power_nodes=r['actual_owner_endpoints']['1'],return_nodes=r['actual_owner_endpoints']['2'],
                target=r['engineering_pad_to_owner_target_mm'],manifest=str(path),category=r['category']))
    path=MANIFESTS[2]
    for r in json.loads(path.read_text())['capacitors']:
        rows.append(dict(ref=r['capacitor_reference'],owner=r['real_owner_reference'],cap_power=r['capacitor_signal_pad'],
            cap_return=r['capacitor_return_pad'],power_nodes=[dict(ref=r['real_owner_reference'],pin=r['real_owner_signal_pin'])],
            return_nodes=[dict(ref=r['real_owner_reference'],pin=k)for k in r['real_owner_matching_return_pins']],
            target=r['placement_target_pad_distance_mm'],manifest=str(path),category=r['category'],
            reviewed_series_path=r['exact_connection_path']))
    path=MANIFESTS[3]
    for r in json.loads(path.read_text())['actual_owner_paths']:
        rows.append(dict(ref=r['capacitor'],owner=r['owner'],cap_power=r['capacitor_power_pin'],cap_return=r['capacitor_return_pin'],
            power_nodes=[dict(ref=r['owner'],pin=r['owner_power_pin'])],return_nodes=[dict(ref=r['owner'],pin=k)for k in r['owner_return_pins']],
            target=3.,manifest=str(path),category='status_local_bypass'))
    if len(rows)!=336 or len({r['ref']for r in rows})!=len(rows):raise ValueError('Exact336 exclusive capacitor owners required')
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--manifest',type=Path,help='Complete exact source capacitor-owner inventory');a=p.parse_args()
    out=a.out.resolve()
    if out.exists():raise ValueError('Fresh report required')
    b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()}
    if a.manifest:
        manifest=json.loads(a.manifest.read_text());rows=manifest['capacitors']
        if manifest['errors']or manifest['pending']or not manifest['all_owner_mappings_verified']:raise ValueError('Unverified whole-source capacitor manifest')
        actual={r for r in fps if r.startswith('C')}
        if len(rows)!=723 or {r['ref']for r in rows}!=actual or len(rows)!=len({r['ref']for r in rows}):raise ValueError('Actual complete723 inventory differs')
        manifests=(a.manifest,)
    else:rows=owners();manifests=MANIFESTS
    def pads(ref,pin):return [p for p in fps[ref].Pads()if p.GetNumber()==pin]
    def dist(a,c):return math.dist(tuple(a.GetPosition()),tuple(c.GetPosition()))/1e6
    for r in rows:
        power=pads(r['ref'],r['cap_power']);gnd=pads(r['ref'],r['cap_return'])
        pp=[p for n in r['power_nodes']for p in pads(n['ref'],n['pin'])];gp=[p for n in r['return_nodes']for p in pads(n['ref'],n['pin'])]
        r['actual_power_pin_match']=bool(pp)and all(p.GetNetname()==power[0].GetNetname()for p in pp)
        path=r.get('reviewed_series_path',[])
        if not r['actual_power_pin_match'] and path:
            # A reference's explicitly reviewed ESR resistor is a real
            # component, not a copper short or a renamed supply pin.
            if len(path)!=3 or path[1]['reference']!=path[2]['reference']or not path[1]['reference'].startswith('R'):
                raise ValueError('Unreviewed series bypass path '+r['ref'])
            first=pads(path[0]['reference'],path[0]['pin']);one=pads(path[1]['reference'],path[1]['pin']);two=pads(path[2]['reference'],path[2]['pin'])
            r['actual_power_pin_match']=all(p.GetNetname()==first[0].GetNetname()for p in one)and all(p.GetNetname()==power[0].GetNetname()for p in two)
            r['series_ESR_not_a_copper_short']=True
        r['actual_return_pin_match']=bool(gp)and all(p.GetNetname()==gnd[0].GetNetname()for p in gp)
        r['actual_supply_pad_distance_mm']=min(dist(a,c)for a in power for c in pp)
        r['actual_return_pad_distance_mm']=min(dist(a,c)for a in gnd for c in gp)
        r['geometric_supply_target_met']=r['actual_supply_pad_distance_mm']<=r['target']if r['target']is not None else None
        r['manufacturer_numeric_maximum']=False
        connected={p.m_Uuid.AsString()for p in b.GetConnectivity().GetConnectedItems(power[0])if p.Type()==pcbnew.PCB_PAD_T}
        r['supply_owner_in_same_actual_copper_cluster']=any(p.m_Uuid.AsString()in connected for p in pp)
        if r.get('series_ESR_not_a_copper_short'):
            from_owner={p.m_Uuid.AsString()for p in b.GetConnectivity().GetConnectedItems(first[0])if p.Type()==pcbnew.PCB_PAD_T}
            r['supply_owner_in_same_actual_copper_cluster']=False
            r['reviewed_supply_path_actual_copper_joins_complete']=any(p.m_Uuid.AsString()in from_owner for p in one)and any(p.m_Uuid.AsString()in connected for p in two)
        else:r['reviewed_supply_path_actual_copper_joins_complete']=r['supply_owner_in_same_actual_copper_cluster']
        connected={p.m_Uuid.AsString()for p in b.GetConnectivity().GetConnectedItems(gnd[0])if p.Type()==pcbnew.PCB_PAD_T}
        r['return_owner_in_same_actual_copper_cluster']=any(p.m_Uuid.AsString()in connected for p in gp)
    out.mkdir(parents=True)
    result=dict(board_sha256=sha(a.board),manifest_hashes={str(p):sha(p)for p in manifests},rows=rows,
        own_pin_match_pass=all(r['actual_power_pin_match']and r['actual_return_pin_match']for r in rows),
        supply_target_misses=sum(r['geometric_supply_target_met']is False for r in rows),
        both_own_pins_in_actual_copper_clusters=sum(r['reviewed_supply_path_actual_copper_joins_complete']and r['return_owner_in_same_actual_copper_cluster']for r in rows),
        local_loop_inductance_or_loaded_effective_capacitance_qualified=False,manufacturing_ready=False)
    write(out/'owner-distances.json',result)
    print({k:v for k,v in result.items()if k not in ('rows','manifest_hashes')})
    for r in sorted(rows,key=lambda r:-r['actual_supply_pad_distance_mm'])[:20]:print(r['ref'],r['owner'],round(r['actual_supply_pad_distance_mm'],3),r['actual_power_pin_match'],r['actual_return_pin_match'])
    if not result['own_pin_match_pass']:raise ValueError('Actual native supply/return owner parity fails')

if __name__=='__main__':main()
