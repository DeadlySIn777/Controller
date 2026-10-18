"""Read-only exact ADC source/PCB audit; a shared rail is not a local bypass."""
from __future__ import annotations
import argparse, hashlib, json, math, shutil
from pathlib import Path
import pcbnew
from hardware_build_ordinary_route_manifest import native

ROOT=Path(__file__).resolve().parents[1]
CAPS={'C14740':('5','6'),'C14741':('5','6'),'C14742':('7','6'),
      'C14743':('7','6'),'C14744':('9','8'),'C14745':('30','29'),
      'C14746':('34','33')}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mm(v):return [pcbnew.ToMM(v.x),pcbnew.ToMM(v.y)]
def audit(source,board):
    source=Path(source);board=Path(board)
    model=json.loads((source/'design.json').read_text(encoding='utf8'))
    nodes,nets,functions=native(model,source/'netlist.xml')
    b=pcbnew.LoadBoard(str(board.resolve()));b.BuildConnectivity()
    footprints={f.GetReference():f for f in b.GetFootprints()}
    adc=footprints['U14734'];adcp={p.GetNumber():p for p in adc.Pads()}
    conn=b.GetConnectivity();rows=[]
    for ref,(sp,rp) in CAPS.items():
        c=model['components'][ref];fp=footprints[ref]
        cp={p.GetNumber():p for p in fp.Pads()}
        actual_power=nodes[ref,'1'];actual_return=nodes[ref,'2']
        if actual_power!=nodes['U14734',sp] or actual_return!=nodes['U14734',rp]:
            raise ValueError('Exact ADC owner topology differs: '+ref)
        ends={i.m_Uuid.AsString()for i in conn.GetConnectedItems(cp['1'])}
        returns={i.m_Uuid.AsString()for i in conn.GetConnectedItems(cp['2'])}
        rows.append(dict(reference=ref,MPN=c['mpn'],value=c['value'],footprint=c['footprint'],
            actual_signal_net=actual_power,actual_return_net=actual_return,
            actual_owner_signal_pin=sp,actual_owner_signal_function=functions['U14734'][sp]['name'],
            actual_owner_return_pin=rp,actual_owner_return_function=functions['U14734'][rp]['name'],
            capacitor_pose_mm=mm(fp.GetPosition()),capacitor_layer=fp.GetLayerName(),
            owner_layer=adc.GetLayerName(),same_side=fp.GetLayer()==adc.GetLayer(),
            signal_pad_centre_distance_mm=math.dist(mm(cp['1'].GetPosition()),mm(adcp[sp].GetPosition())),
            return_pad_centre_distance_mm=math.dist(mm(cp['2'].GetPosition()),mm(adcp[rp].GetPosition())),
            physical_signal_cluster_joined=adcp[sp].m_Uuid.AsString()in ends,
            physical_return_cluster_joined=adcp[rp].m_Uuid.AsString()in returns,
            no_via_direct_routed_loop_proved=False,
            manufacturer_recommendation='TI SBAS680 p70: no vias between AVDD/DVDD or REFCAP pins and capacitor; REFIO close. Same-side required for a direct SMD route.',
            generic_cap_router_permitted=False))
    other=[]
    for ref,c in model['components'].items():
        if ref in CAPS or not ref.startswith('C'):continue
        if nodes.get((ref,'1'))==nodes['U14734','9'] and nodes.get((ref,'2'))==nodes['U14734','8']:
            fp=footprints[ref]
            other.append(dict(reference=ref,value=c['value'],MPN=c['mpn'],role=c.get('role'),
                source_block=c.get('source_block'),pose_mm=mm(fp.GetPosition()),layer=fp.GetLayerName(),
                centre_distance_to_ADC_mm=math.dist(mm(fp.GetPosition()),mm(adc.GetPosition())),
                may_count_as_ADC_local_supply_bank=False))
    return dict(schema_version=1,board_sha256=sha(board),
        source_hashes={str((source/f).resolve()):sha(source/f)for f in ['design.json','netlist.xml']},
        actual_ADC=dict(reference='U14734',MPN=model['components']['U14734']['mpn'],pose_mm=mm(adc.GetPosition()),
            actual_supplies=[dict(pin=p,function=functions['U14734'][p]['name'],net=nodes['U14734',p])for p in ['9','30','34']],
            actual_returns=[dict(pin=p,function=functions['U14734'][p]['name'],net=nodes['U14734',p])for p in ['6','8','29','31','33']]),
        capacitors=rows,other_same_rail_capacitors=other,
        discrepancy=dict(local_AVDD_nominal_existing_uf=[.1,.1],local_DVDD_nominal_existing_uf=.1,
            manufacturer_AVDD_recommended_uf=1,manufacturer_DVDD_recommended_uf=10,
            wrong_side_reference_or_supply_capacitors=[r['reference']for r in rows if not r['same_side']],
            actual_same_rail_remote_storage_is_not_local_bank=True),
        source_or_PCB_mutated=False,manufacturing_ready=False,physical_qualified=False)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,default=ROOT/'hardware/motherboard')
    ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();hashes={str(p.resolve()):sha(p)for p in [a.board,a.source/'design.json',a.source/'netlist.xml']}
    result=audit(a.source,a.board);a.out.mkdir(parents=True,exist_ok=False)
    inp=a.out/'inputs';inp.mkdir()
    for p in [a.source/'design.json',a.source/'netlist.xml']:
        shutil.copyfile(p,inp/p.name)
    for key,expected in hashes.items():
        if sha(key)!=expected:raise ValueError('Read-only audit input changed: '+key)
    result['tool_sha256']=sha(__file__)
    (a.out/'review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(board_sha256=result['board_sha256'],actual_caps=len(result['capacitors']),
        wrong_side=result['discrepancy']['wrong_side_reference_or_supply_capacitors'],source_or_PCB_mutated=False)))
if __name__=='__main__':main()
