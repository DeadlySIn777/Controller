"""Prepare finite routing of same-side local branches without relaxing guards."""
from pathlib import Path
import json,hashlib
here=Path(__file__).parent;root=here.parents[1]
base=here/'route-typed-local-bypass-r04.py'
target=here/'route-strict-same-side-bypass-r05.py'
assert not target.exists()
s=base.read_text()
s=s.replace('import pcbnew','import pcbnew\nfrom hardware_search_native_local_path import find_local_pad_path\nfrom hardware_index_literal_reference_coverage import LiteralReferenceCoverage',1)
s=s.replace('groups=[];skips=list(dedicated);mapping={};g=Geometry(b);checker=NativeCollectedAnnulusCheck(b,{})','groups=[];skips=list(dedicated);mapping={};g=Geometry(b);checker=NativeCollectedAnnulusCheck(b,{})\n same_side_exclusions=[];path_search_reviews=[]\n indexed=LiteralReferenceCoverage(b,{next(p.GetNetname()for p in fps[r[\'ref\']].Pads()if p.GetNumber()==r[\'cap_return\'])for r in rows},[pcbnew.In1_Cu,pcbnew.In4_Cu])')
old="return all(covered(circle(tuple(xy(pt)),pcbnew.FromMM(.24)),checker.reference(return_net,b.GetLayerID(layer)))for layer in('In1.Cu','In4.Cu'))"
assert old in s
s=s.replace(old,"return all(indexed.candidate_covered(circle(tuple(xy(pt)),pcbnew.FromMM(.24)),return_net,b.GetLayerID(layer))for layer in('In1.Cu','In4.Cu'))")
needle="  if math.dist(mm(owner.GetPosition()),mm(cp.GetPosition()))>8:"
assert s.count(needle)==1
s=s.replace(needle,"  if cp.GetParentFootprint().GetLayer()!=owner.GetParentFootprint().GetLayer():\n   same_side_exclusions.append(dict(ref=row['ref'],reason='Outside this no-supply-transition same-side-only trial; prior proof remains unchanged'));continue\n"+needle)
old="""     path=next((ps for ps in paths(cs,os)if g.clear(ps,cp.GetNetname(),cl)),None)
     if path is None:raise ValueError('No bounded same-side local power branch')
     add_route(path,cp.GetNetname(),cl,items)"""
new="""     layer=pcbnew.In1_Cu if cl==pcbnew.F_Cu else pcbnew.In4_Cu
     search=find_local_pad_path(b,cp,owner,geometry=g,eligible_reference_fill=checker.reference(cr.GetNetname(),layer),layer=cl,width_mm=.20,clearance_mm=.20,reference_margin_mm=.10,maximum_length_mm=8.)
     path_search_reviews.append(dict(ref=row['ref'],**search))
     if not search['passed']:raise ValueError('Strict finite same-side search: '+search['reason'])
     path=search['proposed_points_mm']
     add_route(path,cp.GetNetname(),cl,items)"""
assert old in s
s=s.replace(old,new)
needle="  ids=[t.m_Uuid.AsString()for t in items];index=len(groups);"
assert needle in s
s=s.replace(needle,"  assert all(not isinstance(t,pcbnew.PCB_VIA)for t in items if t.GetNetname()==cp.GetNetname()), 'Same-side trial generated a supply via'\n"+needle)
s=s.replace("write(a.out/'receipt.json',dict(input_sha256=", "write(a.out/'receipt.json',dict(same_side_only=True,new_supply_layer_transitions_permitted=False,original_both_reference_ground_anchoring_retained=True,actual_finite_path_search_reviews=path_search_reviews,explicit_same_side_exclusions=same_side_exclusions,input_sha256=")
s=s.replace("str(Path(__file__)):sha(__file__)","str(Path(__file__)):sha(__file__),str(Path(__file__).resolve().parents[2]/'tools/hardware_search_native_local_path.py'):sha(Path(__file__).resolve().parents[2]/'tools/hardware_search_native_local_path.py'),str(Path(__file__).resolve().parents[2]/'tools/hardware_index_literal_reference_coverage.py'):sha(Path(__file__).resolve().parents[2]/'tools/hardware_index_literal_reference_coverage.py')")
target.write_text(s)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(here/'strict-same-side-search-scope-r05.json').write_text(json.dumps(dict(parent_router_sha256=sha(base),generator_sha256=sha(target),source_scope_77=sha(here/'source26-typed-local-bypass-scope-r04.json'),both_ground_reference_layers_still_required=True,search_only_local_literal_prefilter=True,actual_final_full_native_guard_retained=True,same_side_only=True,no_supply_vias=True,maximum_power_branch_path_mm=8.,width_mm=.20,geometry_search_clearance_mm=.20,reference_corridor_margin_mm=.10),indent=2)+'\n')
print(dict(prepared=True,existing_ground_and_final_reference_guards_unchanged=True))
