"""Actual own-field reference collars for one native health receiving loop."""
from pathlib import Path
import sys,json,shutil,subprocess
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import native,classify,positioned,sha,write
from hardware_zone_motherboard_returns import split_polygons,functional_barrier
from hardware_route_selected_additive import corridor_polygon
from hardware_route_logic_return import identity,pad_identity,mm
from hardware_stitch_owned_return_planes import definitions
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_route_owned_bypass_loops import drc
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard
from hardware_validate_motherboard_return_planes_r06 import validate

B=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U25-return-r173/motor-health-U25-return-candidate.kicad_pcb')
M=Path('reports/motherboard-power-entry-20261001/health-supply-r99/health-four-local-owner-manifest-r02.json')
OWN=Path('reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json')
O=Path('reports/motherboard-return-zoning-20261001/ROOT94-health-U25-field-collars-r01')
S=Path('hardware/motherboard')
if O.exists():raise ValueError('Fresh immutable health collar output required')
O.mkdir();assert sha(B)=='7d7f70d08196f5643362168ae5864f9883ba82a54019a8cff60eeae794bfb43c'
frozen={str(p):sha(p)for p in[B,B.with_suffix('.kicad_pro'),B.with_suffix('.kicad_dru'),M,OWN,S/'design.json',S/'netlist.xml',Path(__file__)]}
assert sha(S/'design.json')=='6ec697f7ab420648de187b963b35825a695c3af00d25a9efd5844a8c908a8cb8'
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity()
parts={r:c for r,c in json.loads((S/'design.json').read_text())['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')}
nodes,nc,functions=native(S/'netlist.xml');domains,barriers,_,_=classify(parts,nodes,nc)
mapping=positioned(b,parts,nodes,nc,functions,domains,barriers);assert not mapping['errors']
mapping.update(actual_board_sha256=sha(B),input_sha256=frozen)
write(O/'before-domain-map.json',mapping)
guard=ReferenceGuard(b,mapping);cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
fps={f.GetReference():f for f in b.GetFootprints()}
row=next(r for r in json.loads(M.read_text())['actual_local_loops']if r['owner']=='U11025')
owner=next(p for p in fps['U11025'].Pads()if p.GetNumber()=='5')
ret=next(p for p in fps['U11025'].Pads()if p.GetNumber()=='2')
capret=next(p for p in fps['C11080'].Pads()if p.GetNumber()=='2')
assert ret.GetNetname()==capret.GetNetname()=='/motherboard_motors/FIELD_GND'
assert owner.GetNetname()=='/motherboard_power_entry/FIELD_5V'
groundvias=[t for t in cu.values()if t.Type()==pcbnew.PCB_VIA_T and mm(t.GetPosition())==(333.4375,191.)]
assert len(groundvias)==1 and groundvias[0].GetNetname()==ret.GetNetname()
g=groundvias[0];co=b.GetConnectivity();assert g.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in co.GetConnectedItems(ret)}
oldcu={u:identity(t)for u,t in cu.items()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldz=definitions(B)
nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};oldclusters=native_pad_clusters(b,nets)
shapes={};screen=[]
for uid in row['local_positive_copper']:
 t=cu[uid];assert t.GetNetname()==owner.GetNetname()
 specs=[(pcbnew.In1_Cu,corridor_polygon(tuple(t.GetPosition()),tuple(t.GetPosition()),pcbnew.FromMM(1.1))),
        (pcbnew.In4_Cu,corridor_polygon(tuple(t.GetPosition()),tuple(t.GetPosition()),pcbnew.FromMM(1.1)))]if t.Type()==pcbnew.PCB_VIA_T else[(pcbnew.In1_Cu if t.GetLayer()==pcbnew.F_Cu else pcbnew.In4_Cu,corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()//2+pcbnew.FromMM(.20)))]
 for layer,shape in specs:
  rows=[]
  for foreign,project in guard.indices[layer].candidates(mm(t.GetStart()),mm(t.GetEnd()),1.2):
   if foreign==ret.GetNetname():continue
   hit=pcbnew.SHAPE_POLY_SET(shape);hit.BooleanIntersection(project)
   if hit.OutlineCount():rows.append(dict(foreign=foreign,exact_intersection=hit.Format(False)))
  for barrier in mapping['barriers']:
   hit=pcbnew.SHAPE_POLY_SET(shape);hit.BooleanIntersection(functional_barrier(barrier))
   if hit.OutlineCount():rows.append(dict(package_barrier=barrier['reference'],exact_intersection=hit.Format(False)))
  screen.append(dict(uuid=uid,reference_layer=b.GetLayerName(layer),native_collar=shape.Format(False),conflicts=rows))
  shapes.setdefault(layer,pcbnew.SHAPE_POLY_SET()).BooleanAdd(shape)
for layer in(pcbnew.In1_Cu,pcbnew.In4_Cu):
 shapes[layer].BooleanAdd(corridor_polygon(tuple(g.GetPosition()),tuple(g.GetPosition()),pcbnew.FromMM(.35)))
write(O/'literal-foreign-source-screen.json',dict(passed=not any(r['conflicts']for r in screen),rows=screen))
assert not any(r['conflicts']for r in screen),'Actual foreign Source or package barrier prevents the field collar'
new=[]
for layer,shape in shapes.items():
 blocked=pcbnew.SHAPE_POLY_SET()
 for barrier in mapping['barriers']:blocked.Append(functional_barrier(barrier))
 for z in b.Zones():
  if z.GetIsRuleArea()and z.IsOnLayer(layer)and z.GetDoNotAllowZoneFills():blocked.Append(z.Outline())
 blocked.Simplify();shape.BooleanSubtract(blocked);shape.Simplify()
 template=next(z for z in b.Zones()if not z.GetIsRuleArea()and z.GetNetname()==ret.GetNetname()and z.IsOnLayer(layer))
 priority=max(z.GetAssignedPriority()for z in b.Zones()if not z.GetIsRuleArea()and z.IsOnLayer(layer))+1
 for i,piece in enumerate(split_polygons(shape)):
  z=template.Duplicate();z.Outline().RemoveAllContours();z.Outline().Append(piece);z.SetAssignedPriority(priority);z.SetZoneName('U11025_ACTUAL_FIELD_LOCAL_REFERENCE_'+b.GetLayerName(layer)+'_'+str(i));b.Add(z);new.append(z.m_Uuid.AsString())
dest=O/'motherboard-health-U25-field-reference-candidate.kicad_pcb'
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(B.with_suffix(suffix),dest.with_suffix(suffix))
for f in B.parent.iterdir():
 if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,O/f.name)
 elif f.name=='fp-lib-table':shutil.copy2(f,O/f.name)
pcbnew.SaveBoard(str(dest),b)
write(O/'generation.json',dict(input_sha256=frozen,new_zone_UUIDs=new,actual_ground_via_uuid=g.m_Uuid.AsString(),actual_ground_via_xy_mm=mm(g.GetPosition()),exact_local_supply_UUIDs=row['local_positive_copper']))
print('Native refill of actual U11025 field reference',flush=True)
n=drc(dest,O,'native');after=pcbnew.LoadBoard(str(dest));after.BuildConnectivity()
assert not n['violations']and not n['ignored_checks'],'Actual collar produces a native DRC defect'
assert oldcu=={t.m_Uuid.AsString():identity(t)for t in after.GetTracks()}
assert oldpads=={p.m_Uuid.AsString():pad_identity(p)for p in after.GetPads()}
az=definitions(dest);assert set(az)==set(oldz)|set(new)and all(az[u]==d for u,d in oldz.items())
nowclusters=native_pad_clusters(after,nets);assert clusters_survive(oldclusters,nowclusters)
write(O/'native-Source-cluster-proof.json',dict(passed=True,before=oldclusters,after=nowclusters))
afps={f.GetReference():f for f in after.GetFootprints()}
currentmap=positioned(after,parts,nodes,nc,functions,domains,barriers);assert not currentmap['errors']
currentmap.update(actual_board_sha256=sha(dest),input_sha256=frozen);write(O/'domain-map.json',currentmap)
resource=validate(after,currentmap);resource.update(board_sha256=sha(dest),source_map_sha256=sha(O/'domain-map.json'));write(O/'full-native-resource-review.json',resource)
ownerrow=next(r for r in json.loads(OWN.read_text())['capacitors']if r['ref']=='C11080')
manifest=dict(owned_loops=[dict(ref='C11080',category=ownerrow['category'],owner='U11025',retained=True,new_UUIDs=row['local_positive_copper']+row['local_return_copper']+[g.m_Uuid.AsString()])],actual_filled_supply_branch_return_reviews=[],board_sha256=sha(dest),manufacturing_ready=False)
write(O/'actual-one-health-bypass-manifest.json',manifest)
run=subprocess.run([sys.executable,'tools/hardware_verify_owned_bypass_batch.py','--board',str(dest),'--owners',str(OWN),'--receipt',str(O/'actual-one-health-bypass-manifest.json'),'--out',str(O/'actual-one-health-bypass-proof.json')],capture_output=True,text=True)
(O/'actual-one-health-bypass-command.txt').write_text(run.stdout+run.stderr)
if run.returncode:raise ValueError('Actual one-health full return/annulus/receiving proof failed')
proof=json.loads((O/'actual-one-health-bypass-proof.json').read_text())
write(O/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[],reviewed_added_zone_UUIDs=new,reviewed_scope_reason='Exact U11025 own-field In1/In4 local receiving supply/reference collar around real Source-ground pair; no source/land/Cu/pose/old-zone change, no generic field alias or all-current/20ms qualification.'))
for path,h in frozen.items():assert sha(path)==h,'Frozen input changed'
write(O/'receipt.json',dict(passed=proof['passed']and resource['passed'],input_sha256=frozen,before_board=str(B),before_board_sha256=sha(B),board=str(dest),board_sha256=sha(dest),native_errors=0,native_warnings=0,ignored_checks=[],actual_one_loop_full_reference_proved=proof['passed'],new_zone_UUIDs=new,all_old_Cu_lands_pads_poses_zones_Source_clusters_preserved=True,current_full_resource_passed=resource['passed'],manufacturing_ready=False))
print(json.dumps(dict(passed=proof['passed']and resource['passed'],new_zones=len(new),board_sha256=sha(dest))))
