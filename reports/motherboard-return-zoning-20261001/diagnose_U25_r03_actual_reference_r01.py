"""Read-only exact native U25 bypass and U26 unchanged control diagnostics."""
from pathlib import Path
import sys,json,math
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path.cwd()/'reports/motherboard-return-zoning-20261001')]
import pcbnew
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
from check_exact_endpoint_antipad_union_r01 import ExactEndpointUnionCheck
from hardware_check_return_corridors import circle
from hardware_route_selected_additive import corridor_polygon
from hardware_map_motherboard_domains import write,sha
from hardware_route_logic_return import mm
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-two-local-barrel-correction-r03/motherboard-U25-two-local-barrels-candidate.kicad_pcb');O=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-r03-actual-reference-diagnostic-r01');assert not O.exists();O.mkdir()
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()};pads={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()if p.GetNumber()};ret=pads['U11025','2'].GetNetname();supply=pads['U11025','5'].GetNetname()
group=next(g for g in json.loads(Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-pair-current-native-proof-r03/current106-C80-rebound-manifest.json').read_text())['owned_loops']if g['ref']=='C11080');decl=dict(return_net=ret,reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.1)
original=NativeCollectedAnnulusCheck(b,{supply:decl});equiv=ExactEndpointUnionCheck(b,{supply:decl});rows=[]
for u in group['new_UUIDs']:
 t=cu[u]
 if t.GetNetname()!=supply:continue
 row=dict(uuid=u,net=t.GetNetname(),type=t.Type(),start_mm=mm(t.GetStart()),end_mm=mm(t.GetEnd()))
 for name,ch in [('frozen_sequential',original),('equivalent_union',equiv)]:
  try:row[name]=dict(passed=True,review=ch.via(t,decl)if t.Type()==pcbnew.PCB_VIA_T else ch.segment(t,decl))
  except ValueError as e:row[name]=dict(passed=False,error=str(e))
 if t.Type()==pcbnew.PCB_TRACE_T and not row['equivalent_union']['passed']:
  layer=b.GetLayerID(decl['reference_layers'][b.GetLayerName(t.GetLayer())]);aug=pcbnew.SHAPE_POLY_SET(equiv.reference(ret,layer));exceptions=[]
  for endpoint in(tuple(t.GetStart()),tuple(t.GetEnd())):
   for v in equiv.vias:
    if v.GetNetname()==supply and tuple(v.GetPosition())==endpoint:
     try:a=equiv.via(v,decl);aug.BooleanAdd(circle(endpoint,pcbnew.FromMM(a['bounded_antipad_radius_mm'][b.GetLayerName(layer)])));exceptions.append(v.m_Uuid.AsString())
     except ValueError:pass
  miss=corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()/2+pcbnew.FromMM(.1));miss.BooleanSubtract(aug);bb=miss.BBox();row.update(exact_missing_shape=miss.Format(False),missing_area_mm2=miss.Area()/1e12,missing_bounds_mm=[pcbnew.ToMM(v)for v in(bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom())],exact_endpoint_exceptions=exceptions)
 rows.append(row)
private={pads['U11026',n].GetNetname()for n in('1','3')};d=dict(decl,reference_corridor_margin_mm=.4);eq=ExactEndpointUnionCheck(b,{n:d for n in private});controls=[]
for t in cu.values():
 if t.GetNetname()not in private:continue
 try:controls.append(dict(uuid=t.m_Uuid.AsString(),passed=True,review=eq.via(t,d)if t.Type()==pcbnew.PCB_VIA_T else eq.segment(t,d)))
 except ValueError as e:controls.append(dict(uuid=t.m_Uuid.AsString(),passed=False,error=str(e)))
write(O/'diagnostic.json',dict(board_sha256=sha(B),C80=rows,U26_controls=controls,passed=all(r['equivalent_union']['passed']for r in rows)and all(r['passed']for r in controls),native_B_sliver_warning_remains=True,no_mutation=True));print(json.dumps(dict(C80=rows,U26_failed=[r for r in controls if not r['passed']]),default=str),flush=True)
