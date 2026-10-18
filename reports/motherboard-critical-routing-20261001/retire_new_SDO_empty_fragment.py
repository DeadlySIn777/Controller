"""Retire one new, independently SOURCE-empty reference fragment only."""
from pathlib import Path
import sys,json,shutil,copy
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_wip_r05 as authority
import hardware_zone_motherboard_returns as z
e=authority.engine
OLD=Path('reports/motherboard-critical-routing-20261001/actual-AO1-SDO-root74-corridor-r02')
SOURCE=OLD/'motherboard-AO1-SDO-corridor-candidate.kicad_pcb'
ROOT=Path('reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb')
MAP=Path('reports/motherboard-domains-20261001/source26-r74-r01/domain-map.json')
OUT=Path(sys.argv[1]);OUT.mkdir(exist_ok=False,parents=True)
uid='401ca06f-4f4f-4ae5-a2c3-863a1df45091'
base=pcbnew.LoadBoard(str(ROOT));b=pcbnew.LoadBoard(str(SOURCE));mapping=e.read(MAP)
if uid in{x.m_Uuid.AsString()for x in base.Zones()}:raise ValueError('An old reference zone cannot be retired by this correction')
zone=next(x for x in b.Zones()if x.m_Uuid.AsString()==uid)
if zone.GetNetname()!='/LOGIC_GND'or zone.GetLayer()!=pcbnew.In1_Cu:raise ValueError('Exact new fragment identity/domain changed')
poly=zone.Outline();conflicts=[]
def check(label,projection,detail):
 hit=z.duplicate(poly);hit.BooleanIntersection(projection)
 if hit.Area():conflicts.append(dict(type=label,detail=detail,actual_intersection_mm2=hit.Area()/1e12))
# Source package projections and individual copper boxes are conservative;
# zero Boolean-intersection proves emptiness without Collide/index inference.
for row in z.reference_envelopes(mapping,'In1.Cu'):check('actual SOURCE package projection',z.rectangle(row['bounds'],.25),row)
for row in mapping['pads']:
 if z.pad_supports_reference(row,'In1.Cu'):check('actual native SOURCE copper envelope',z.rectangle(row['copper_aabb_mm'],.25),dict(reference=row['reference'],pin=row['pin'],net=row['net']))
for t in b.GetTracks():
 if not z.track_supports_reference(b,t,'In1.Cu'):continue
 if t.Type()==pcbnew.PCB_VIA_T:projection=e.corridor_polygon(tuple(t.GetPosition()),tuple(t.GetPosition()),t.GetWidth(pcbnew.F_Cu)/2+pcbnew.FromMM(.25))
 elif t.Type()==pcbnew.PCB_TRACE_T:projection=e.corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()/2+pcbnew.FromMM(.25))
 else:raise ValueError('Unreviewed actual retained arc projection')
 check('actual source-connected/retained copper projection',projection,dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname()))
if conflicts:
 e.write(OUT/'rejected-proof.json',dict(passed=False,conflicts=conflicts));raise ValueError('New fragment contains actual SOURCE/retained projections')
tree=e.parse(SOURCE.read_text());final=[n for n in tree if not(isinstance(n,list)and n and n[0]=='zone'and e.value(e.child(n,'uuid')[1])==uid)]
dest=OUT/'motherboard-AO1-SDO-corridor-candidate.kicad_pcb';dest.write_text(authority.dump_native_board(final)+'\n')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(SOURCE.with_suffix(suffix),dest.with_suffix(suffix))
for f in OLD.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
e.write(OUT/'new-fragment-retirement.json',dict(passed=True,base_sha256=e.sha(ROOT),input_sha256=e.sha(SOURCE),board_sha256=e.sha(dest),map_sha256=e.sha(MAP),removed_only_new_zone_UUID=uid,actual_outline_area_mm2=poly.Area()/1e12,actual_BOOLEAN_Source_package_pad_retained_copper_projection_conflicts=conflicts,no_old_reference_zone_retired=True,no_ignored_check_or_rule_change=True,justification='Only a new SOURCE-empty LOGIC fragment produced by the explicit own-AO1 corridor subtraction is retired. Original source-bearing and unanchored pieces remain retained; no reference eligibility is broadened.',native_revalidation_pending=True,manufacturing_ready=False))
shutil.copyfile(OLD/'proposed-delta.json',OUT/'original-corridor-delta.json')
print(json.dumps(dict(passed=True,removed_new_SOURCE_empty_zone=uid,actual_area_mm2=poly.Area()/1e12)),flush=True)
