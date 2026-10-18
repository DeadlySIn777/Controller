"""Exact two unused health-collar slivers: native zone-outline correction."""
from pathlib import Path
import sys,json,shutil,hashlib,subprocess
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write,native,classify,positioned
from hardware_zone_motherboard_returns import rectangle,split_polygons
from hardware_route_logic_return import identity,pad_identity
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_route_owned_bypass_loops import drc
from hardware_validate_motherboard_return_planes_r06 import validate,exact_twice_area
from hardware_build_assembly import parse
from hardware_merge_bounded_pcb_delta import without_generated_fills,objects,zone_definition
B=Path('reports/motherboard-return-zoning-20261001/ROOT94-health-U25-field-collars-r02/motherboard-health-U25-field-reference-candidate.kicad_pcb')
D=B.parent;O=D.with_name('ROOT94-health-U25-field-collars-r03');S=Path('hardware/motherboard')
assert not O.exists();O.mkdir();assert sha(B)=='c2d8e8a0ec8ebedcb8f62aa714dfe3bc02f31d9c451b7afa95765ac252cf1907'
inputs={str(p):sha(p)for p in[B,B.with_suffix('.kicad_pro'),B.with_suffix('.kicad_dru'),D/'domain-map.json',D/'actual-one-health-bypass-manifest.json',S/'design.json',S/'netlist.xml',Path(__file__)]}
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};clusters=native_pad_clusters(b,nets)
zs={z.m_Uuid.AsString():z for z in b.Zones()};targets={'c02038df-6166-41a9-bae7-2b140f1340e0':pcbnew.In1_Cu,'631861c5-87d2-433c-b827-22d591425c42':pcbnew.In4_Cu};exact=[(332888690,191404035),(332780690,191466390),(332888698,191404030)];rows=[]
for uid,layer in targets.items():
 z=zs[uid];assert z.GetNetname()=='/motherboard_motors/FIELD_GND'and z.IsOnLayer(layer)
 matches=[p for p in split_polygons(z.GetFilledPolysList(layer))if p.OutlineCount()==1 and p.HoleCount(0)==0 and p.COutline(0).PointCount()==3 and sorted((p.COutline(0).CPoint(i).x,p.COutline(0).CPoint(i).y)for i in range(3))==sorted(exact)]
 assert len(matches)==1 and exact_twice_area(matches[0])==41160
 box=matches[0].BBox();bounds=[pcbnew.ToMM(v)for v in[box.GetX(),box.GetY(),box.GetRight(),box.GetBottom()]];cut=rectangle(bounds,.01)
 assert not any(p.IsOnLayer(layer)and cut.Collide(p.GetEffectiveShape(layer))for p in b.GetPads()),'Unused cut touches actual Source land'
 assert not any(t.IsOnLayer(layer)and cut.Collide(t.GetEffectiveShape(layer))for t in b.GetTracks()),'Unused cut touches native conductor'
 shape=pcbnew.SHAPE_POLY_SET();shape.Append(z.Outline());shape.BooleanSubtract(cut);assert shape.OutlineCount()==1
 z.Outline().RemoveAllContours();z.Outline().Append(shape);rows.append(dict(uuid=uid,layer=b.GetLayerName(layer),literal_vertices_nm=exact,exact_twice_area_nm2=41160,bounds_mm=bounds,cut_bounds_mm=[bounds[0]-.01,bounds[1]-.01,bounds[2]+.01,bounds[3]+.01],Source_or_conductor_intersections=[]))
dest=O/B.name
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(B.with_suffix(suffix),dest.with_suffix(suffix))
for f in D.iterdir():
 if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,O/f.name)
 elif f.name=='fp-lib-table':shutil.copy2(f,O/f.name)
pcbnew.SaveBoard(str(dest),b)
def zonedefs(path):return{u:zone_definition(t)for u,t in objects(parse(without_generated_fills(path.read_text())),'zone').items()}
beforez=zonedefs(B);afterz=zonedefs(dest);ledger=[]
for uid in targets:
 ledger.append(dict(uuid=uid,before_definition_sha256=hashlib.sha256(beforez[uid].encode()).hexdigest(),after_definition_sha256=hashlib.sha256(afterz[uid].encode()).hexdigest(),electrical_outline_correction_reason='Remove one exactly frozen positive unused native triangle using its explicit10micrometre boundary collar, with no physical Source/conductor intersections and unchanged complete Source/receiving-reference proofs; no area exemption.'))
assert set(beforez)==set(afterz)and all(beforez[u]==afterz[u]for u in beforez if u not in targets)
write(O/'generation.json',dict(input_sha256=inputs,before_board=str(B),before_board_sha256=sha(B),board=str(dest),exact_two_literal_unused_slivers=rows,reviewed_existing_zone_outline_deltas=ledger))
print('Native refill after two exact unused health triangles',flush=True);n=drc(dest,O,'native');assert not n['violations']and not n['ignored_checks']
a=pcbnew.LoadBoard(str(dest));a.BuildConnectivity();assert oldcu=={t.m_Uuid.AsString():identity(t)for t in a.GetTracks()};assert oldpads=={p.m_Uuid.AsString():pad_identity(p)for p in a.GetPads()};now=native_pad_clusters(a,nets);assert clusters_survive(clusters,now)
write(O/'all-native-Source-cluster-proof.json',dict(passed=True,before=clusters,after=now))
parts={r:c for r,c in json.loads((S/'design.json').read_text())['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')};nodes,nc,functions=native(S/'netlist.xml');domains,barriers,_,_=classify(parts,nodes,nc);mp=positioned(a,parts,nodes,nc,functions,domains,barriers);assert not mp['errors'];mp.update(actual_board_sha256=sha(dest),input_sha256=inputs);write(O/'domain-map.json',mp)
r=validate(a,mp);r.update(board_sha256=sha(dest),source_map_sha256=sha(O/'domain-map.json'));write(O/'full-native-resource-review.json',r)
manifest=json.loads((D/'actual-one-health-bypass-manifest.json').read_text());manifest['board_sha256']=sha(dest);write(O/'actual-one-health-bypass-manifest.json',manifest)
run=subprocess.run([sys.executable,'tools/hardware_verify_owned_bypass_batch.py','--board',str(dest),'--owners','reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json','--receipt',str(O/'actual-one-health-bypass-manifest.json'),'--out',str(O/'actual-one-health-bypass-proof.json')],capture_output=True,text=True);(O/'actual-one-health-command.txt').write_text(run.stdout+run.stderr);assert run.returncode==0
scope=json.loads((D/'bounded-scope.json').read_text());scope['reviewed_existing_zone_outline_deltas']=ledger;scope['reviewed_scope_reason']+=' Two exact old own-field unused triangle outline corrections, no Cu/source/land/pose changes.';write(O/'bounded-scope.json',scope)
assert all(sha(p)==h for p,h in inputs.items());proof=json.loads((O/'actual-one-health-bypass-proof.json').read_text());write(O/'receipt.json',dict(passed=proof['passed']and r['passed'],board=str(dest),board_sha256=sha(dest),before_board=str(B),before_board_sha256=sha(B),native_errors=0,native_warnings=0,ignored_checks=[],actual_one_health_full_proof=proof['passed'],full_resource_passed=r['passed'],all_old_Cu_lands_poses_Source_clusters_preserved=True,input_sha256=inputs,manufacturing_ready=False));print(json.dumps(dict(passed=proof['passed']and r['passed'],board_sha256=sha(dest))),flush=True)
