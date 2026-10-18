import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import covered
from hardware_route_selected_additive import corridor_polygon
from hardware_route_logic_return import xy,mm
from hardware_map_motherboard_domains import sha,write
base=Path('reports/motherboard-return-zoning-20261001/source26-r56-AO1-secondary-return-r04/motherboard-AO1-secondary-return-candidate.kicad_pcb');b=pcbnew.LoadBoard(str(base));net='/motherboard_analog_output/AO1_COM';fill=collect_native_reference_fills(b,{net},[pcbnew.In1_Cu])[net,pcbnew.In1_Cu];fp=next(f for f in b.GetFootprints()if f.GetReference()=='U14626');pads={p.GetNumber():p for p in fp.Pads()};rows=[]
for pin in ['2','3','6','7','8']:
 p=pads[pin];s=mm(p.GetPosition());side=1 if pin in ['6','7','8']else -1;end=(round(s[0]+side*1.6,6),s[1]);corridor=corridor_polygon(tuple(p.GetPosition()),tuple(xy(end)),pcbnew.FromMM(.25));rows.append(dict(pin=pin,net=p.GetNetname(),actual_source_position_mm=s,proposed_horizontal_escape_end_mm=end,escape_length_mm=1.6,reference_margin_mm=.15,own_AO1_In1_corridor_covered=covered(corridor,fill),actual_full_pad_footprint_size_mm=[pcbnew.ToMM(v)for v in p.GetSize()]))
r=dict(board_sha256=sha(base),own_return_net=net,reference_layer='In1.Cu',unadopted_route_proposals=True,rows=rows,no_source_or_PCB_mutation=True);write(Path('reports/motherboard-return-zoning-20261001/source26-r56-AO1-MSOP-reference-review-r01.json'),r);print(json.dumps(r,indent=2))
