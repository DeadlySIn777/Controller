"""Report actual failed thin-feature geometry and actual Source contacts, no exception."""
from pathlib import Path
import sys,importlib.util,json,math
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_zone_motherboard_returns import split_polygons
from hardware_route_logic_return import mm
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
F=Path('reports/motherboard-ordinary-routing-20261001/check_io3_backbone_preservation_r07.py');spec=importlib.util.spec_from_file_location('f',F);f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
P=Path('reports/motherboard-critical-routing-20261001/actual-source26-root84-FPGA-CCK-C1022-F-In2-r06');BASE=Path('reports/motherboard-pcb-integration-20261001/source26-FPGA-flash-MISO-r84/motherboard-bounded-merged-candidate.kicad_pcb');OUT=P/'actual-CORE-narrow-review-r02';OUT.mkdir(exist_ok=False)
b=pcbnew.LoadBoard(str(BASE));a=pcbnew.LoadBoard(str(P/'motherboard-FPGA-flash-CCK-candidate.kicad_pcb'));b.BuildConnectivity();a.BuildConnectivity();net='/CORE_1V2'
bp=collect_native_reference_fills(b,{net},[pcbnew.In3_Cu])[net,pcbnew.In3_Cu];ap=collect_native_reference_fills(a,{net},[pcbnew.In3_Cu])[net,pcbnew.In3_Cu]
old=f.duplicate(bp);old.Deflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001));new=f.duplicate(ap);new.Deflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001));opened=f.duplicate(old);opened.Inflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001));opened.BooleanIntersection(bp);opened.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);narrow=f.subtract(bp,opened);precision=f.duplicate(ap);precision.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);lost=f.subtract(narrow,precision)
def bounds(poly):
 box=poly.BBox();return [pcbnew.ToMM(v)for v in(box.GetX(),box.GetY(),box.GetRight(),box.GetBottom())]
padb={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()};pada={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in a.GetPads()};sourceb=padb['L2001','2'];sourcea=pada['L2001','2'];peerb={x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(sourceb)}|{sourceb.m_Uuid.AsString()};peera={x.m_Uuid.AsString()for x in a.GetConnectivity().GetConnectedItems(sourcea)}|{sourcea.m_Uuid.AsString()}
contacts=[dict(reference=k[0],pin=k[1],xy=mm(p.GetPosition()),before_Source_connected=p.m_Uuid.AsString()in peerb,after_Source_connected=pada[k].m_Uuid.AsString()in peera)for k,p in padb.items()if p.GetNetname()==net]
vias=[]
for t in b.GetTracks():
 if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()==net:
  u=t.m_Uuid.AsString();q=next(x for x in a.GetTracks()if x.m_Uuid.AsString()==u)
  vias.append(dict(uuid=u,xy=mm(t.GetPosition()),before_flashing_native_connected_In3=physical_reference_contact(t,pcbnew.In3_Cu,b.GetConnectivity()),after_flashing_native_connected_In3=physical_reference_contact(q,pcbnew.In3_Cu,a.GetConnectivity()),before_Source_connected=u in peerb,after_Source_connected=u in peera))
np=list(split_polygons(new));ownership=[]
for i,p in enumerate(split_polygons(old)):
 owners=[j for j,q in enumerate(np)if f.intersection(p,q).OutlineCount()];ownership.append(dict(before=i,after=owners,passed=len(owners)==1))
fulla=list(split_polygons(ap));full=[]
for i,p in enumerate(split_polygons(bp)):
 owners=[j for j,q in enumerate(fulla)if f.intersection(p,q).OutlineCount()];full.append(dict(before=i,after=owners,passed=len(owners)==1))
removed=f.subtract(bp,ap);rows=[]
for i,p in enumerate(split_polygons(lost)):
 box=bounds(p);rows.append(dict(index=i,area_mm2=p.Area()/1e12,bounds_mm=box,exact_polygon=p.Format(False),nearest_actual_CORE_Source_pad_distance_to_box_mm=min(math.hypot(max(box[0]-r['xy'][0],0,r['xy'][0]-box[2]),max(box[1]-r['xy'][1],0,r['xy'][1]-box[3]))for r in contacts)))
r=dict(actual_native_thin_feature_guard_passed=False,unchanged_frozen_guard_failure_retained=True,actual_removed_CORE_copper_mm2=removed.Area()/1e12,actual_lost_definite_thin_feature_mm2=lost.Area()/1e12,actual_lost_definite_thin_features=rows,actual_unbuffered_topology_ownership=full,actual_1mm_backbone_ownership=ownership,actual_Core_Source_contacts=contacts,actual_Core_via_annuli=vias,actual_old_backbone_component_count=old.OutlineCount(),actual_new_backbone_component_count=new.OutlineCount(),manufacturing_ready=False,no_capacity_exception_applied=True)
(OUT/'review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(removed_CORE_area_mm2=r['actual_removed_CORE_copper_mm2'],lost_thin_features=rows,source_pins=sum(x['before_Source_connected']for x in contacts),old_new_backbones=[old.OutlineCount(),new.OutlineCount()],all_core_ownership=all(x['passed']for x in ownership))))
