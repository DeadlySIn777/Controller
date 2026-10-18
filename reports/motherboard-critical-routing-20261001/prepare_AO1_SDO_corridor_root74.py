"""Bounded actual SDO route and empty-space own-In1 reference correction."""
from pathlib import Path
import sys, copy, json, shutil, uuid
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_wip_r05 as authority
import hardware_zone_motherboard_returns as z
e=authority.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb')
MAP=Path('reports/motherboard-domains-20261001/source26-r74-r01/domain-map.json')
DONOR=Path('reports/motherboard-critical-routing-20261001/actual-AO1-DAC4-geometric-native-r01/motherboard-AO1-four-geometric-candidate.kicad_pcb')
SCREEN=Path('reports/motherboard-critical-routing-20261001/actual-AO1-SDO-root74-corridor-screen-r01/screen.json')
OUT=Path(sys.argv[1]);OUT.mkdir(exist_ok=False,parents=True)
screen=e.read(SCREEN)
if screen['root_board_sha256']!=e.sha(BASE)or screen['root_source_map_sha256']!=e.sha(MAP)or screen['foreign_projection_guard_mm']!=.25 or screen['foreign_projection_guard_mm']!=.25 or screen['segments_with_foreign_projection_conflicts']:
 raise ValueError('Literal actual SDO foreign SOURCE screen is not accepted')
b=pcbnew.LoadBoard(str(BASE)); d=pcbnew.LoadBoard(str(DONOR));mapping=e.read(MAP)
target='/motherboard_analog_output/AO1_COM';layer=pcbnew.In1_Cu
ids={r['uuid']for r in screen['results']};tracks={t.m_Uuid.AsString():t for t in d.GetTracks()}
if len(ids)!=4 or any(not tracks[u].GetNetname().endswith('/AO1_DAC_SDO')for u in ids):raise ValueError('Only the literal four SDO segments are accepted')
corridor=pcbnew.SHAPE_POLY_SET()
for u in ids:
 t=tracks[u];corridor.BooleanAdd(e.corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()/2+pcbnew.FromMM(.70)))
# Clearance reserve outside the unchanged .40 required reference envelope is
# .30 mm. Clip only this addition against real Source/barrel/raw projections.
obstacles=pcbnew.SHAPE_POLY_SET()
for row in z.reference_envelopes(mapping,'In1.Cu'):
 if row['net']!=target:obstacles.BooleanAdd(z.rectangle(row['bounds'],.25))
for row in mapping['barriers']:obstacles.BooleanAdd(z.functional_barrier(row))
for pad in mapping['pads']:
 if z.pad_supports_reference(pad,'In1.Cu')and(pad['domain'].startswith(('SUB:','CONTACT:'))or pad['domain']=='CHASSIS'):
  obstacles.BooleanAdd(z.rectangle(pad['copper_aabb_mm'],.3))
domains={p['net']:p['domain']for p in mapping['pads']}
for t in b.GetTracks():
 if not z.track_supports_reference(b,t,'In1.Cu')or z.return_net(dict(domain=domains.get(t.GetNetname()),net=t.GetNetname()))==target:continue
 if t.Type()==pcbnew.PCB_VIA_T:poly=e.corridor_polygon(tuple(t.GetPosition()),tuple(t.GetPosition()),t.GetWidth(pcbnew.F_Cu)/2+pcbnew.FromMM(.25))
 elif t.Type()==pcbnew.PCB_TRACE_T:poly=e.corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()/2+pcbnew.FromMM(.25))
 else:raise ValueError('Unreviewed retained arc projection')
 obstacles.BooleanAdd(poly)
for zone in b.Zones():
 if zone.GetIsRuleArea()and zone.IsOnLayer(layer)and zone.GetDoNotAllowZoneFills():obstacles.BooleanAdd(z.duplicate(zone.Outline()))
 if zone.GetZoneName().startswith('FLOATING_SUB_'):obstacles.BooleanAdd(z.inflation(zone.Outline(),.25))
obstacles.Simplify();corridor.BooleanSubtract(obstacles);corridor.Simplify()
touch=[]
for zone in b.Zones():
 if zone.GetNetname()!=target or zone.GetLayer()!=layer:continue
 hit=z.duplicate(corridor);hit.BooleanIntersection(zone.Outline())
 if hit.Area():touch.append(zone)
if not touch:raise ValueError('Own corridor lacks actual Source-own outline connection')
poly=z.duplicate(corridor)
for zone in touch:poly.BooleanAdd(zone.Outline())
poly.Simplify()
if poly.OutlineCount()!=1:raise ValueError('Literal touched own outlines did not join as one native outline')
main=next((zone for zone in touch if zone.m_Uuid.AsString()=='ed959e66-2592-4d75-8c2f-3bca0ccac426'),touch[0])
replacements={main.m_Uuid.AsString():[poly]};retired={zone.m_Uuid.AsString()for zone in touch if zone!=main}
logic_cut=z.inflation(corridor,.25)
for zone in b.Zones():
 if zone.GetNetname()!='/LOGIC_GND'or zone.GetLayer()!=layer:continue
 hit=z.duplicate(logic_cut);hit.BooleanIntersection(zone.Outline())
 if not hit.Area():continue
 revised=z.duplicate(zone.Outline());revised.BooleanSubtract(logic_cut);revised.Simplify()
 sections=sorted(z.split_polygons(revised),key=lambda p:p.Area(),reverse=True)
 if not sections:raise ValueError('Bounded corridor subtraction would retire an entire LOGIC outline')
 replacements[zone.m_Uuid.AsString()]=sections
original=e.parse(BASE.read_text());final=copy.deepcopy(original)
minimal=pcbnew.BOARD();mini_net=pcbnew.NETINFO_ITEM(minimal,'/POLYGON_ONLY');minimal.Add(mini_net)
for uid,sections in replacements.items():
 for index,outline in enumerate(sections):z.add_zone(minimal,'/POLYGON_ONLY',outline,layer,20,uid+'#'+str(index))
temp=OUT/'polygon-serialization-donor.kicad_pcb';pcbnew.SaveBoard(str(temp),minimal)
zones_by_name={e.value(e.child(n,'name')[1]):n for n in e.children(e.parse(temp.read_text()),'zone')}
ledger=[]
for n in list(e.children(final,'zone')):
 uid=e.value(e.child(n,'uuid')[1])
 if uid in retired:
  final.remove(n);ledger.append(dict(uuid=uid,action='retire_touched_same_net_outline_after_exact_union',before=e.dump(n)));continue
 if uid not in replacements:continue
 old=e.dump(n);sections=replacements[uid]
 # Native KiCad stores one outline per zone. Every disconnected section is
 # retained as an explicit same-net/rules clone; no tiny-piece deletion.
 for index in range(1,len(sections)):
  added_zone=copy.deepcopy(n);newuid=str(uuid.uuid4())
  e.child(added_zone,'uuid')[1]=e.q(newuid)
  name=e.child(added_zone,'name')
  if name:name[1]=e.q(e.value(name[1])+'_SDO_BOUNDED_SPLIT_'+str(index))
  for p in list(e.children(added_zone,'polygon')):added_zone.remove(p)
  added_zone.extend(copy.deepcopy(e.children(zones_by_name[uid+'#'+str(index)],'polygon')))
  final.append(added_zone)
  ledger.append(dict(uuid=newuid,action='exact_empty_space_same_net_polygon_split',parent_uuid=uid,after=e.dump(added_zone),area_mm2=sections[index].Area()/1e12))
 for p in list(e.children(n,'polygon')):n.remove(p)
 n.extend(copy.deepcopy(e.children(zones_by_name[uid+'#0'],'polygon')))
 ledger.append(dict(uuid=uid,action='polygon_only',before=old,after=e.dump(n)))
donor_tree=e.parse(DONOR.read_text());additions=[n for k in('segment','via','arc')for n in e.children(donor_tree,k)if e.value(e.child(n,'uuid')[1])in ids]
final.extend(copy.deepcopy(additions))
dest=OUT/'motherboard-AO1-SDO-corridor-candidate.kicad_pcb';dest.write_text(authority.dump_native_board(final)+'\n')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(BASE.with_suffix(suffix),dest.with_suffix(suffix))
for f in BASE.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
e.write(OUT/'proposed-delta.json',dict(base_sha256=e.sha(BASE),board_sha256=e.sha(dest),map_sha256=e.sha(MAP),literal_source_net='/motherboard_analog_output/AO1_DAC_SDO',actual_added_copper_UUIDs=sorted(ids),changed_zone_polygon_ledger=ledger,own_target_return=target,unchanged_reference_margin_mm=.40,foreign_projection_guard_mm=.25,only_added_empty_space_reference_clipped_against_actual_SOURCE=True,native_validation_pending=True,manufacturing_ready=False))
print(json.dumps(dict(newCu=len(ids),touched_own_zones=len(touch),changed_polygons=len(replacements),retired_same_net_outline_UUIDs=sorted(retired))),flush=True)
