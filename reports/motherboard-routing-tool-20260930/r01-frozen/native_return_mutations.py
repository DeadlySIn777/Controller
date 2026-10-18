"""Native polygon/return mutation checks; no board is saved or adopted."""
import copy,json,sys
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from hardware_route_selected_additive import return_corridor_check,read,corridor_polygon,write
HERE=Path(__file__).resolve().parent;P=HERE/'native-fixture-r05/actual-router-import'
receipt=read(P/'receipt.json');rows=read(P/'manifest.json')['nets'];ids=set(receipt['added_copper_uuids'])
def load():return pcbnew.LoadBoard(str(P/'additive-route-candidate.kicad_pcb'))
results=[]
def reject(name,change):
 b=load();r=copy.deepcopy(rows);change(b,r)
 try:return_corridor_check(b,ids,r)
 except ValueError as error:results.append(dict(name=name,rejected=True,error=str(error)));return
 raise AssertionError('Unsafe return mutation was accepted: '+name)
valid=return_corridor_check(load(),ids,rows);assert valid['passed'];results.append(dict(name='actual_filled_adjacent_reference',passed=True))
def slot(b,r):
 z=next(z for z in b.Zones() if z.GetLayer()==pcbnew.In1_Cu)
 p=pcbnew.SHAPE_POLY_SET();p.BooleanAdd(z.GetFilledPolysList(pcbnew.In1_Cu))
 # Narrow slot crosses the entire projected track corridor. Polygon
 # subtraction must detect it; a sample of endpoints would miss it.
 t=next(t for t in b.GetTracks() if t.m_Uuid.AsString() in ids and abs(t.GetEnd().x-t.GetStart().x)>pcbnew.FromMM(5))
 x=(t.GetStart().x+t.GetEnd().x)//2;y=(t.GetStart().y+t.GetEnd().y)//2
 cut=corridor_polygon((x,y-pcbnew.FromMM(.4)),(x,y+pcbnew.FromMM(.4)),pcbnew.FromMM(.005))
 p.BooleanSubtract(cut);z.SetFilledPolysList(pcbnew.In1_Cu,p)
reject('10um_reference_slot_rejected',slot)
reject('wrong_field_return_rejected',lambda b,r:r['/SIGNAL'].update(return_net='/FIELD_B_0V'))
reject('absent_reference_layer_rejected',lambda b,r:r['/SIGNAL']['reference_layers'].update({'F.Cu':'In2.Cu'}))
write(HERE/'native-return-mutations.json',dict(passed=True,cases=len(results),results=results,native_boards_saved=False,physical_measurement=False))
print(json.dumps(results))
