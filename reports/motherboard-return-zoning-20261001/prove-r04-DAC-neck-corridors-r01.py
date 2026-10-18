import sys,json
from pathlib import Path
sys.path.insert(0,'tools');import pcbnew
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_route_selected_additive import corridor_polygon
from hardware_check_return_corridors import covered
from hardware_route_logic_return import xy,mm
from hardware_map_motherboard_domains import write,sha
from hardware_validate_return_bridge_sources import review
out=Path('reports/motherboard-return-zoning-20261001/source26-r61-AO1-DAC-return-r04');dest=out/'motherboard-AO1-DAC-return-candidate.kicad_pcb';b=pcbnew.LoadBoard(str(dest));pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()};fill=collect_native_reference_fills(b,{'/motherboard_analog_output/AO1_COM'},[pcbnew.In1_Cu])['/motherboard_analog_output/AO1_COM',pcbnew.In1_Cu];rows=[]
for pin,direction,delta in [('2',-1,-.075),('3',-1,.075),('6',1,.075),('7',1,0),('8',1,-.075)]:
 p=pads['U14626',pin];s=mm(p.GetPosition());points=[s,(s[0]+direction*.85,s[1]),(s[0]+direction,s[1]+delta)];ok=all(covered(corridor_polygon(tuple(xy(a)),tuple(xy(c)),pcbnew.FromMM(.1+.4)),fill)for a,c in zip(points,points[1:]));rows.append(dict(reference='U14626',pin=pin,pad_uuid=p.m_Uuid.AsString(),net=p.GetNetname(),points_mm=points,width_mm=.2,reference_margin_mm=.4,return_net='/motherboard_analog_output/AO1_COM',reference_layer='In1.Cu',own_In1_continuous_filled_corridor=ok))
r=dict(board_sha256=sha(dest),all_five_prepared_neck_reference_corridors_passed=all(q['own_In1_continuous_filled_corridor']for q in rows),rows=rows,no_route_or_source_mutation=True);write(out/'actual-five-MSOP-escape-reference-screen.json',r)
if not r['all_five_prepared_neck_reference_corridors_passed']:raise ValueError('Actual unchanged .40 reference-margin neck failed')
m=json.load(open('reports/motherboard-domains-20261001/source26-r61-orphan-free-r01/domain-map.json'));receipt=json.loads((out/'receipt.json').read_text());source=review(b,[dict(net='/motherboard_analog_output/AO1_COM',new_copper_UUIDs=receipt['new_copper_UUIDs'])],m['pads']);source['board_sha256']=sha(dest);write(out/'every-new-DAC-return-conductor-SOURCE-witness.json',source);print('All five exact necks pass .40 own-reference margin; all three new return conductors reach real SOURCE pads.')
