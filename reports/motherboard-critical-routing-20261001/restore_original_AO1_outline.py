"""Retain the exact old same-net outline; remove overlap from its extension."""
from pathlib import Path
import sys,copy,shutil,json
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_wip_r05 as authority
import hardware_zone_motherboard_returns as z
e=authority.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb')
OLD=Path('reports/motherboard-critical-routing-20261001/actual-AO1-SDO-root74-corridor-r03/motherboard-AO1-SDO-corridor-candidate.kicad_pcb')
OUT=Path(sys.argv[1]);OUT.mkdir(exist_ok=False,parents=True)
olduid='14802936-d0f8-465a-93cb-871f2ea664d9';mainuid='ed959e66-2592-4d75-8c2f-3bca0ccac426'
base=pcbnew.LoadBoard(str(BASE));current=pcbnew.LoadBoard(str(OLD))
original=next(q for q in base.Zones()if q.m_Uuid.AsString()==olduid)
main=next(q for q in current.Zones()if q.m_Uuid.AsString()==mainuid)
if original.GetNetname()!=main.GetNetname()or original.GetLayer()!=main.GetLayer()or original.GetAssignedPriority()!=main.GetAssignedPriority():raise ValueError('Exact old/new AO1 layer/net/priority differ')
union_before=z.duplicate(main.Outline());newpoly=z.duplicate(main.Outline());newpoly.BooleanSubtract(original.Outline());newpoly.Simplify()
if newpoly.OutlineCount()!=1:raise ValueError('Exact original subtraction splits the owning extension')
union_after=z.duplicate(newpoly);union_after.BooleanAdd(original.Outline());union_after.Simplify()
forward=z.duplicate(union_before);forward.BooleanSubtract(union_after)
reverse=z.duplicate(union_after);reverse.BooleanSubtract(union_before)
if forward.Area()or reverse.Area():raise ValueError('Native original+extension union physical outline differs')
minimal=pcbnew.BOARD();net=pcbnew.NETINFO_ITEM(minimal,'/POLYGON_ONLY');minimal.Add(net)
z.add_zone(minimal,'/POLYGON_ONLY',newpoly,pcbnew.In1_Cu,20,'OWN_POLYGON_ONLY')
temp=OUT/'polygon-serialization-donor.kicad_pcb';pcbnew.SaveBoard(str(temp),minimal)
polygons=e.children(e.children(e.parse(temp.read_text()),'zone')[0],'polygon')
tree=e.parse(OLD.read_text());base_tree=e.parse(BASE.read_text())
oldnode=next(q for q in e.children(base_tree,'zone')if e.value(e.child(q,'uuid')[1])==olduid)
mainnode=next(q for q in e.children(tree,'zone')if e.value(e.child(q,'uuid')[1])==mainuid)
for q in list(e.children(mainnode,'polygon')):mainnode.remove(q)
mainnode.extend(copy.deepcopy(polygons));tree.append(copy.deepcopy(oldnode))
dest=OUT/'motherboard-AO1-SDO-corridor-candidate.kicad_pcb';dest.write_text(authority.dump_native_board(tree)+'\n')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(OLD.with_suffix(suffix),dest.with_suffix(suffix))
for f in OLD.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
e.write(OUT/'original-outline-restoration.json',dict(passed=True,base_sha256=e.sha(BASE),input_sha256=e.sha(OLD),board_sha256=e.sha(dest),exact_original_zone_UUID=olduid,extension_zone_UUID=mainuid,original_net=original.GetNetname(),original_layer=base.GetLayerName(original.GetLayer()),original_priority=original.GetAssignedPriority(),native_own_union_Boolean_difference_mm2=[forward.Area()/1e12,reverse.Area()/1e12],exact_original_zone_definition_retained=True,old_zone_retirements=0,changed_other_source_copper_or_rules=False,native_refill_and_full_return_validation_pending=True,manufacturing_ready=False))
print(json.dumps(dict(passed=True,old_zones_retired=0,native_physical_own_union_exact=True)),flush=True)
