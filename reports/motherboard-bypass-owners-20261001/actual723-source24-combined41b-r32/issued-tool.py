"""Read-only full723 source-owned capacitor placement/copper audit on native KiCad.

Pad distances are engineering screens. Native connectivity is not measured
loop impedance, manufacturer effective-capacitance proof or release approval.
"""
import argparse,copy,hashlib,json,math
from pathlib import Path
import pcbnew
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',required=True,type=Path);p.add_argument('--manifest',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();assert not a.out.exists();a.out.mkdir(parents=True)
    hashes={str(f):digest(f)for f in [a.board,a.manifest,Path(__file__)]};manifest=json.loads(a.manifest.read_text());assert manifest['all_owner_mappings_verified']and len(manifest['capacitors'])==723
    b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()};rows=copy.deepcopy(manifest['capacitors'])
    def pads(ref,pin):return [z for z in fps[ref].Pads()if z.GetNumber()==str(pin)]
    def connected(p):return {z.m_Uuid.AsString()for z in b.GetConnectivity().GetConnectedItems(p)if z.Type()==pcbnew.PCB_PAD_T}
    def distance(x,y):return math.dist(tuple(x.GetPosition()),tuple(y.GetPosition()))/1e6
    errors=[]
    for r in rows:
        ref=r['ref'];pp=pads(ref,r['cap_power']);gg=pads(ref,r['cap_return']);sp=[z for n in r['power_nodes']for z in pads(n['ref'],n['pin'])];sg=[z for n in r['return_nodes']for z in pads(n['ref'],n['pin'])]
        assert pp and gg and sp and sg,ref
        r['actual_power_pin_match']=all(z.GetNetname()==pp[0].GetNetname()for z in sp)
        r['actual_return_pin_match']=all(z.GetNetname()==gg[0].GetNetname()for z in sg)
        r['actual_supply_pad_distance_mm']=min(distance(x,y)for x in pp for y in sp)
        r['actual_return_pad_distance_mm']=min(distance(x,y)for x in gg for y in sg)
        r['geometric_supply_target_met']=r['actual_supply_pad_distance_mm']<=r['target']if r['target']is not None else None
        r['geometric_return_target_met']=r['actual_return_pad_distance_mm']<=r['target']if r['target']is not None else None
        cc=connected(pp[0]);r['supply_owner_in_same_actual_copper_cluster']=any(z.m_Uuid.AsString()in cc for z in sp)
        r['reviewed_supply_path_actual_copper_joins_complete']=r['supply_owner_in_same_actual_copper_cluster']
        path=r.get('reviewed_series_path',[])
        if not r['actual_power_pin_match']and len(path)==3:
            one,two,three=path;owner=pads(one['reference'],one['pin']);near=pads(two['reference'],two['pin']);far=pads(three['reference'],three['pin']);assert two['reference']==three['reference']and two['reference'].startswith('R')
            r['actual_power_pin_match']=all(z.GetNetname()==owner[0].GetNetname()for z in near)and all(z.GetNetname()==pp[0].GetNetname()for z in far)
            r['series_ESR_not_a_copper_short']=True
            first=connected(owner[0]);r['reviewed_supply_path_actual_copper_joins_complete']=any(z.m_Uuid.AsString()in first for z in near)and any(z.m_Uuid.AsString()in cc for z in far)
        cc=connected(gg[0]);r['return_owner_in_same_actual_copper_cluster']=any(z.m_Uuid.AsString()in cc for z in sg)
        r['actual_native_cap_pose']=dict(x_mm=fps[ref].GetPosition().x/1e6,y_mm=fps[ref].GetPosition().y/1e6,rotation_deg=fps[ref].GetOrientationDegrees(),layer=fps[ref].GetLayerName())
        if not(r['actual_power_pin_match']and r['actual_return_pin_match']):errors.append('Native pin topology mismatch '+ref)
    assert all(digest(Path(f))==h for f,h in hashes.items())
    result=dict(source_capacitors=723,PCB_footprints=len(fps),input_hashes=hashes,rows=rows,errors=errors,own_pin_match_pass=not errors,supply_target_misses=sum(r['geometric_supply_target_met']is False for r in rows),return_target_misses=sum(r['geometric_return_target_met']is False for r in rows),unassigned_numeric_target_count=sum(r['target']is None for r in rows),both_own_pins_in_actual_copper_clusters=sum(r['reviewed_supply_path_actual_copper_joins_complete']and r['return_owner_in_same_actual_copper_cluster']for r in rows),layout_or_effective_C_qualified=False,source_modified=False,PCB_modified=False,manufacturing_ready=False)
    (a.out/'owner-distances.json').write_text(json.dumps(result,indent=2)+'\n');(a.out/'issued-tool.py').write_bytes(Path(__file__).read_bytes());print(json.dumps({k:v for k,v in result.items()if k not in ['rows','input_hashes']}));assert not errors,errors
if __name__=='__main__':main()
