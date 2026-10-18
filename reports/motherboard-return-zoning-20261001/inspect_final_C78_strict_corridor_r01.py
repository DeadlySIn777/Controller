"""Read-only exact per-object native corridor diagnosis; no acceptance waiver."""
from pathlib import Path
import sys,json
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew as p
from hardware_map_motherboard_domains import write,sha
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
from hardware_check_return_corridors import copy_poly,circle
from hardware_route_selected_additive import corridor_polygon
B=Path(sys.argv[1]);O=Path(sys.argv[2]);assert not O.exists()
b=p.LoadBoard(str(B));b.BuildConnectivity();m=json.loads((B.parent/'current108-final-bypass-manifest.json').read_text());g=next(g for g in m['owned_loops']if g['ref']=='C11078');cu={t.m_Uuid.AsString():t for t in b.GetTracks()};d=dict(return_net='/LOGIC_GND',reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.1);c=NativeCollectedAnnulusCheck(b,{'/mc_local_power/CORE_5V':d});rows=[]
for uid in sorted(g['new_UUIDs']):
 t=cu[uid]
 if t.GetNetname()!='/mc_local_power/CORE_5V':continue
 r=dict(uuid=uid,kind='via'if t.Type()==p.PCB_VIA_T else 'segment')
 try:r['review']=c.via(t,d)if t.Type()==p.PCB_VIA_T else c.segment(t,d);r['passed']=True
 except ValueError as e:
  r.update(passed=False,error=str(e))
  if t.Type()==p.PCB_TRACE_T:
   ly=b.GetLayerID(d['reference_layers'][b.GetLayerName(t.GetLayer())]);f=c.reference('/LOGIC_GND',ly);poly=corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()/2+p.FromMM(.1));allowed=copy_poly(f)
   for endpoint in(tuple(t.GetStart()),tuple(t.GetEnd())):
    for v in c.vias:
     if v.GetNetname()==t.GetNetname()and tuple(v.GetPosition())==endpoint:
      a=c.via(v,d);allowed.BooleanAdd(circle(endpoint,p.FromMM(a['bounded_antipad_radius_mm'][b.GetLayerName(ly)])))
   poly.BooleanSubtract(allowed);r.update(start_nm=list(t.GetStart()),end_nm=list(t.GetEnd()),missing_native_exact=poly.Format(False),missing_area_mm2=poly.Area()/1e12)
 rows.append(r)
write(O,dict(board_sha256=sha(B),rows=rows));print(json.dumps([r for r in rows if not r['passed']]))
