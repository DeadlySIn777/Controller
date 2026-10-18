"""Literal AO1 .40 envelopes against SOURCE/native foreign projections."""
from pathlib import Path
import sys,json,collections,math
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_wip_r05 as authority
import hardware_zone_motherboard_returns as z
import hardware_check_return_corridors_r04 as ret
e=authority.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb')
DONOR=Path('reports/motherboard-critical-routing-20261001/actual-AO1-DAC4-geometric-native-r01/motherboard-AO1-four-geometric-candidate.kicad_pcb')
PROOF=DONOR.parent/'native-geometric-proof.json'
MAP=Path('reports/motherboard-domains-20261001/source26-r74-r01/domain-map.json')
OUT=Path(sys.argv[1]);OUT.mkdir(exist_ok=False,parents=True)
b=pcbnew.LoadBoard(str(BASE));d=pcbnew.LoadBoard(str(DONOR));mapping=e.read(MAP);proof=e.read(PROOF)
target='/motherboard_analog_output/AO1_COM';own='AO1'
guard=.25;obstacles=[]
def add(label,poly,detail):
 if poly.Area():obstacles.append((label,poly,detail))
for row in z.reference_envelopes(mapping,'In1.Cu'):
 if row['net']!=target:add('SOURCE package group',z.rectangle(row['bounds'],guard),row)
for row in mapping['barriers']:add('actual isolation barrier',z.functional_barrier(row),row)
for pad in mapping['pads']:
 if z.pad_supports_reference(pad,'In1.Cu')and pad['domain'].startswith(('SUB:','CONTACT:'))or(z.pad_supports_reference(pad,'In1.Cu')and pad['domain']=='CHASSIS'):
  add('ungrounded SOURCE metal',z.rectangle(pad['copper_aabb_mm'],.3),pad)
domains={p['net']:p['domain']for p in mapping['pads']}
for t in b.GetTracks():
 if not z.track_supports_reference(b,t,'In1.Cu'):continue
 domain=domains.get(t.GetNetname());retname=z.return_net(dict(domain=domain,net=t.GetNetname()))
 if retname==target:continue
 if t.Type()==pcbnew.PCB_VIA_T:
  # Exact projected barrel/land diameter remains foreign physical metal.
  poly=e.corridor_polygon(tuple(t.GetPosition()),tuple(t.GetPosition()),t.GetWidth(pcbnew.F_Cu)/2+pcbnew.FromMM(guard))
 elif t.Type()==pcbnew.PCB_TRACE_T:poly=e.corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()/2+pcbnew.FromMM(guard))
 else:raise ValueError('Unreviewed native retained arc')
 add('actual foreign source copper',poly,dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname(),domain=domain,layer=b.GetLayerName(t.GetLayer())))
for zone in b.Zones():
 if zone.GetIsRuleArea()and zone.IsOnLayer(pcbnew.In1_Cu)and zone.GetDoNotAllowZoneFills():add('actual all-Cu/raw/pour exclusion',z.duplicate(zone.Outline()),dict(uuid=zone.m_Uuid.AsString(),name=zone.GetZoneName()))
 if zone.GetZoneName().startswith('FLOATING_SUB_'):add('actual floating SUB region',z.inflation(zone.Outline(),.25),dict(uuid=zone.m_Uuid.AsString(),name=zone.GetZoneName()))
results=[];envelopes=pcbnew.SHAPE_POLY_SET();native_check=ret.NativeCollectedAnnulusCheck(b,{})
rows=e.read('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json')['nets']
tracks={t.m_Uuid.AsString():t for t in d.GetTracks()}
for uid in proof['added_copper_uuids']:
 t=tracks[uid]
 if not t.GetNetname().endswith('/AO1_DAC_SDO'):continue
 row=rows[t.GetNetname()];poly=e.corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()/2+pcbnew.FromMM(.4));envelopes.BooleanAdd(poly)
 intersections=[]
 for label,obs,detail in obstacles:
  # Bounding-box test avoids most native Boolean work on the full board.
  if not poly.BBox().Intersects(obs.BBox()):continue
  hit=z.duplicate(poly);hit.BooleanIntersection(obs)
  if hit.Area()>1:intersections.append(dict(type=label,detail=detail,intersection_area_mm2=hit.Area()/1e12))
 try:native=dict(passed=True,proof=native_check.segment(t,row))
 except ValueError as exc:native=dict(passed=False,reason=str(exc))
 outline=poly.COutline(0);points=[list(pcbnew.ToMM(p))for p in outline.CPoints()]
 results.append(dict(uuid=uid,net=t.GetNetname(),start_mm=list(pcbnew.ToMM(t.GetStart())),end_mm=list(pcbnew.ToMM(t.GetEnd())),width_mm=pcbnew.ToMM(t.GetWidth()),reference_margin_mm=.4,reference_envelope_polygon_mm=points,actual_foreign_intersections=intersections,existing_actual_reference_screen=native))
envelopes.Simplify()
e.write(OUT/'screen.json',dict(root_board_sha256=e.sha(BASE),root_source_map_sha256=e.sha(MAP),actual_donor_sha256=e.sha(DONOR),actual_donor_proof_sha256=e.sha(PROOF),tool_sha256=e.sha(__file__),literal_segments=len(results),union_envelope_area_mm2=envelopes.Area()/1e12,foreign_projection_guard_mm=.25,results=results,segments_with_foreign_projection_conflicts=sum(bool(x['actual_foreign_intersections'])for x in results),segments_missing_existing_fill=sum(not x['existing_actual_reference_screen']['passed']for x in results),actual_reference_extension_adopted=False,passed=False,manufacturing_ready=False))
print(json.dumps(dict(segments=len(results),foreign_conflicts=sum(bool(x['actual_foreign_intersections'])for x in results),missingfill=sum(not x['existing_actual_reference_screen']['passed']for x in results))),flush=True)
