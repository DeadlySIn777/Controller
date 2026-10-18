"""Report-only actual native placement and all-layer escape screen; no refill/adoption."""
from pathlib import Path
import sys,json,math,copy
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_owned_bypass_loops_wip_r03 as w
from hardware_route_logic_return import xy,mm,segment_distance
from hardware_populate_motherboard_pcb import write,sha
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-FPGA-flash-MISO-r84/motherboard-bounded-merged-candidate.kicad_pcb')
OUT=Path(sys.argv[1]);OUT.mkdir(parents=True,exist_ok=False)
b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity();parts={f.GetReference():f for f in b.GetFootprints()};cap=parts['C1022'];original=(mm(cap.GetPosition()),cap.GetOrientationDegrees())
for f in b.GetFootprints():f.BuildCourtyardCaches()
results=[]
for centre,angle in [((94.5,48.0),90),((94.25,48.0),90)]:
 cap.SetOrientationDegrees(angle);cap.SetPosition(xy(centre));cap.BuildCourtyardCaches();g=w.Geometry(b);issues=[];cy=cap.GetCourtyard(pcbnew.B_CrtYd)
 for other in b.GetFootprints():
  if other.GetReference()=='C1022':continue
  ocy=other.GetCourtyard(pcbnew.B_CrtYd)
  if cy.OutlineCount() and ocy.OutlineCount():
   hit=pcbnew.SHAPE_POLY_SET();hit.Append(cy);hit.BooleanIntersection(ocy)
   if hit.Area():issues.append(dict(kind='actual_backside_courtyard',other=other.GetReference(),area_mm2=hit.Area()/1e12))
 for pad in cap.Pads():
  layer=pcbnew.B_Cu;shape=pad.GetEffectiveShape(layer)
  for other in b.GetFootprints():
   if other.GetReference()=='C1022':continue
   for q in other.Pads():
    if q.IsOnLayer(layer) and q.GetNetname()!=pad.GetNetname() and shape.Collide(q.GetEffectiveShape(layer),pcbnew.FromMM(.20-1e-6)):
     issues.append(dict(kind='actual_cap_foreign_pad',cap_pin=pad.GetNumber(),other=other.GetReference(),other_pin=q.GetNumber()))
  for t in b.GetTracks():
   if t.GetNetname()==pad.GetNetname():continue
   if t.Type()==pcbnew.PCB_VIA_T:
    if t.IsOnLayer(layer) and shape.Collide(pcbnew.SHAPE_CIRCLE(t.GetPosition(),t.GetWidth(layer)//2),pcbnew.FromMM(.20-1e-6)):
     issues.append(dict(kind='actual_cap_foreign_via',cap_pin=pad.GetNumber(),uuid=t.m_Uuid.AsString(),net=t.GetNetname()))
   elif t.GetLayer()==layer and shape.Collide(pcbnew.SEG(t.GetStart(),t.GetEnd()),t.GetWidth()//2+pcbnew.FromMM(.20-1e-6)):
    issues.append(dict(kind='actual_cap_foreign_track',cap_pin=pad.GetNumber(),uuid=t.m_Uuid.AsString(),net=t.GetNetname()))
 def via(net,at,d=.5,dr=.2):
  found=[];shape=pcbnew.SHAPE_CIRCLE(xy(at),pcbnew.FromMM(d/2))
  for f in b.GetFootprints():
   for p in f.Pads():
    if p.GetNetname()==net:continue
    clearance=.125 if f.GetReference()=='U1001'else .20
    for layer in b.GetEnabledLayers().CuStack():
     if p.IsOnLayer(layer) and p.GetEffectiveShape(layer).Collide(shape,pcbnew.FromMM(clearance-1e-6)):
      found.append(dict(kind='actual_via_foreign_pad',ref=f.GetReference(),pin=p.GetNumber(),layer=b.GetLayerName(layer),clearance_mm=clearance))
  for layer,index in g.tracks.items():
   for other,a,z,width in index.candidates(at,at,d/2+.7):
    if other!=net and segment_distance(at,at,a,z)<d/2+width/2+.20-1e-6:found.append(dict(kind='actual_via_foreign_Cu',net=other,layer=b.GetLayerName(layer),start=a,end=z))
  for pos,hole in g.holes:
   if math.dist(at,pos)<dr/2+hole/2+.25-1e-6:found.append(dict(kind='actual_hole_spacing',other=pos))
  for zone in g.keepouts:
   if zone.GetDoNotAllowVias() and zone.Outline().Collide(shape):found.append(dict(kind='actual_no_via_keepout',uuid=zone.m_Uuid.AsString()))
  protected=[]
  for zone in b.Zones():
   if zone.GetNetname() in ('/CORE_1V2','/IO_3V3'):
    for layer in zone.GetLayerSet().CuStack():
     fill=zone.GetFilledPolysList(layer)
     if fill.Contains(xy(at)):protected.append(dict(net=zone.GetNetname(),layer=b.GetLayerName(layer),zone=zone.m_Uuid.AsString()))
  return dict(net=net,xy=at,passed=not found,issues=found,actual_existing_protected_power_fill_at_centre=protected)
 pads={p.GetNumber():p for p in cap.Pads()}
 sites=[via('/fpga_core/FPGA_FLASH_CCK_SOURCE',(95.2,46.4)),via('/LOGIC_GND',(94.4,46.4)),via('/LOGIC_GND',(94.4,47.2)),via('/IO_3V3',(93.6,48.8))]
 results.append(dict(cap_centre=centre,cap_angle=angle,cap_pads={n:dict(net=p.GetNetname(),xy=mm(p.GetPosition()))for n,p in pads.items()},power_pad_to_actual_owner_pin_centre_mm=math.dist(mm(pads['1'].GetPosition()),mm(next(p for p in parts['U1001'].Pads()if p.GetNumber()=='L6').GetPosition())),placement_passed=not issues,placement_issues=issues,via_screens=sites,actual_geometry_passed=not issues and all(r['passed']for r in sites)))
cap.SetPosition(xy(original[0]));cap.SetOrientationDegrees(original[1])
write(OUT/'review.json',dict(base_sha256=sha(BASE),actual_C1022_original_pose=original,recipes=results,no_source_or_board_file_changed=True,native_DRC_not_run=True,local_cap_power_return_loops_pending=True,CORE_relative_power_review_pending=True,manufacturing_ready=False))
print(json.dumps(results))
