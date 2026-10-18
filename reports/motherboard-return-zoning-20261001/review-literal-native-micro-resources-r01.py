"""Read-only compare Boolean-derived micro pieces with literal native copper."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_zone_motherboard_returns import split_polygons
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact

bp=Path(sys.argv[1]);rp=Path(sys.argv[2]);out=Path(sys.argv[3])
if out.exists():raise ValueError('Fresh evidence required')
b=pcbnew.LoadBoard(str(bp));b.BuildConnectivity();c=b.GetConnectivity();report=json.load(open(rp));nets={r['net']for r in report['unanchored_components']}
fills=collect_native_reference_fills(b,nets,[pcbnew.In1_Cu,pcbnew.In4_Cu]);pieces={k:list(split_polygons(f))for k,f in fills.items()};rows=[]
for r in report['unanchored_components']:
 if r['filled_area_mm2']>=.000001:continue
 layer=b.GetLayerID(r['reference_layer']);micro=pieces[r['net'],layer][r['filled_piece']];bb=micro.BBox();actual=[]
 for z in b.Zones():
  if z.GetIsRuleArea()or z.GetNetname()!=r['net']or not z.IsOnLayer(layer):continue
  for index,p in enumerate(split_polygons(z.GetFilledPolysList(layer))):
   if not p.Collide(micro):continue
   cut=pcbnew.SHAPE_POLY_SET();cut.Append(micro);cut.BooleanIntersection(p)
   if cut.Area()<=0:continue
   anchors=[]
   for t in b.GetTracks():
    if t.GetNetname()!=r['net']or not isinstance(t,pcbnew.PCB_VIA)or not physical_reference_contact(t,layer,c)or not p.Contains(t.GetPosition()):continue
    source=[q for q in c.GetConnectedItems(t)if isinstance(q,pcbnew.PAD)and q.GetNumber()and q.GetNetname()==r['net']]
    if source:anchors.append(dict(via_uuid=t.m_Uuid.AsString(),Source_reference=source[0].GetParentFootprint().GetReference(),Source_pin=source[0].GetNumber()))
    if len(anchors)>=3:break
   direct=[dict(reference=q.GetParentFootprint().GetReference(),pin=q.GetNumber())for q in b.GetPads()if q.GetNumber()and q.GetNetname()==r['net']and physical_reference_contact(q,layer,c)and p.Contains(q.GetPosition())][:3]
   actual.append(dict(zone_uuid=z.m_Uuid.AsString(),literal_native_fill_piece=index,area_mm2=p.Area()/1e12,intersection_area_mm2=cut.Area()/1e12,Source_native_same_literal_piece_via_witnesses=anchors,Source_native_same_literal_piece_direct_pad_witnesses=direct))
 rows.append(dict(derived_resource=r,micro_bounds_mm=[pcbnew.ToMM(v)for v in(bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom())],literal_actual_native_filled_piece_contacts=actual,all_physical_source_qualification_claim=False))
 print(r['net'],r['reference_layer'],r['filled_piece'],'nativePieces',len(actual),flush=True)
write(out,dict(board_sha256=sha(bp),original_unqualified_resource_report_sha256=sha(rp),rows=rows,read_only=True,geometry_or_frozen_checker_changed=False,manufacturing_ready=False))
