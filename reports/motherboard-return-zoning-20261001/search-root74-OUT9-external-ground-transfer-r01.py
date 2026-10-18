"""Search a real low-current Ground transfer outside a too-narrow literal piece."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_zone_motherboard_returns import split_polygons,rectangle,return_net
from hardware_route_logic_return import xy,mm
from hardware_route_local_signals import GeometryIndex,paths
from hardware_route_owned_bypass_loops import Geometry
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard,legal_path
from hardware_route_selected_additive import corridor_polygon

bp=Path('reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb')
mp=Path('reports/motherboard-domains-20261001/source26-r74-r01/domain-map.json')
out=Path('reports/motherboard-return-zoning-20261001/source26-r74-OUT9-external-ground-transfer-proposal-r01.json')
b=pcbnew.LoadBoard(str(bp));mapping=json.loads(mp.read_text());g=Geometry(b);guard=ReferenceGuard(b,mapping)
net='/motherboard_do/FIELD_B_0V';z=next(z for z in b.Zones()if z.m_Uuid.AsString()=='70779225-3f58-41c9-9ef5-f15169383fc2')
target=list(split_polygons(z.GetFilledPolysList(pcbnew.In4_Cu)))[0]
ends=[(352.0625,107.85),(347.175,110),(346.175,111)]
metal=GeometryIndex()
for row in mapping['pads']:
    if return_net(row)==net:continue
    poly=rectangle(row['copper_aabb_mm'],.15);bounds=row['copper_aabb_mm']
    metal.add((row['reference'],row['pin'],poly),[bounds[0]-.15,bounds[1]-.15,bounds[2]+.15,bounds[3]+.15])

class PowerOnly:
    def clear(self,path,n,layer,width=.2):
        if n!=net or not g.clear(path,n,layer,width):return False
        for a,c in zip(path,path[1:]):
            shape=corridor_polygon(tuple(xy(a)),tuple(xy(c)),pcbnew.FromMM(width/2))
            for ref,pin,other in metal.candidates(a,c,width/2+.15):
                if shape.Collide(other):return False
        return True

starts=[]
for ix in range(3595,3661,2):
    for iy in range(1055,1101,2):
        p=(ix/10,iy/10)
        if target.Contains(xy(p)) and guard.clear([p,p],net,pcbnew.In4_Cu):starts.append(p)
positions=[(x/10,y/10)for x in range(3570,3681,3)for y in range(1030,1131,3)]
options=[]
for q in positions:
    if not g.via(q,net):continue
    for p in sorted(starts,key=lambda s:math.dist(s,q))[:6]:
        if math.dist(p,q)>3:continue
        contact=legal_path(p,q,net,pcbnew.In4_Cu,guard,4,False)
        if contact:
            options.append((min(math.dist(q,e)for e in ends)+math.dist(p,q),p,q,contact));break
print('Actually clear external barrels/contact proposals',len(options),flush=True)
chosen=[]
for _,p,q,contact in sorted(options)[:60]:
    for e in sorted(ends,key=lambda x:math.dist(q,x)):
        route=legal_path(q,e,net,pcbnew.In3_Cu,PowerOnly(),25,False)
        if route:
            chosen=[dict(new_ground_transfer_via_mm=q,literal_In4_piece_contact_path_mm=contact,
              source_backed_In3_ground_power_path_mm=route,actual_existing_Source_ground_via_mm=e,
              no_signal_transfer_or_signal_reference_claim=True,
              own_source_anchored_annuli_native_DRC_oldclusters_required=True)];break
    if chosen:break
write(out,dict(read_only=True,board_sha256=sha(bp),source_map_sha256=sha(mp),
     actual_clear_external_barrel_contact_candidates=len(options),proposal=chosen))
print(chosen,flush=True)
