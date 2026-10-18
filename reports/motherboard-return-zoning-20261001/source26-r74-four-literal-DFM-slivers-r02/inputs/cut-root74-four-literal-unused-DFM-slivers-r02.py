import sys,json,shutil,collections,subprocess,hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/"tools"))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import identity,pad_identity
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_route_owned_bypass_loops import drc
from hardware_zone_motherboard_returns import rectangle,split_polygons
from hardware_stitch_owned_return_planes import definitions
from hardware_build_assembly import parse,dump
from hardware_merge_bounded_pcb_delta import without_generated_fills,objects,zone_definition
from hardware_validate_motherboard_return_planes_r06 import validate,exact_twice_area
base=Path("reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb")
mp=Path("reports/motherboard-domains-20261001/source26-r74-r01/domain-map.json")
proof=Path("reports/motherboard-return-zoning-20261001/source26-r73-exact-integer-micro-review-r01.json")
out=Path("reports/motherboard-return-zoning-20261001/source26-r74-four-literal-DFM-slivers-r02")
if out.exists():raise ValueError("Fresh immutable evidence required")
out.mkdir();(out/"inputs").mkdir();frozen={str(p):sha(p)for p in(base,mp,proof,Path(__file__))}
for p in(base,mp,proof,Path(__file__)):shutil.copy2(p,out/"inputs"/p.name)
b=pcbnew.LoadBoard(str(base));b.BuildConnectivity();oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldzones=definitions(base);nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};before=native_pad_clusters(b,nets);zones={z.m_Uuid.AsString():z for z in b.Zones()};rows=[];cuts={}
for r in json.loads(proof.read_text())["rows"]:
 witnesses=[v for v in r["literal_intersections"]if v["exact_integer_intersection_twice_area_nm2"]>0]
 if len(witnesses)!=1:raise ValueError("Each exact reviewed DFM sliver needs one positive native literal zone")
 w=witnesses[0];z=zones[w["zone_uuid"]];layer=b.GetLayerID(r["layer"]);literal=list(split_polygons(z.GetFilledPolysList(layer)))[w["literal_filled_piece"]]
 if exact_twice_area(literal)!=r["exact_integer_twice_area_nm2"] or z.GetNetname()!=r["net"]:raise ValueError("Current exact literal sliver differs")
 bounds=[pcbnew.ToMM(v)for v in r["bounds_nm"]];margin=.15 if w["zone_uuid"]=="4272b53f-e8ac-4b85-a9a4-4ed9163f9db1"else .01
 cut=rectangle(bounds,margin)
 # No fitted Source land or native route may be removed or covered by the cut.
 touchedpads=[p.m_Uuid.AsString()for p in b.GetPads()if p.IsOnLayer(layer)and cut.Collide(p.GetEffectiveShape(layer))]
 touchedcu=[t.m_Uuid.AsString()for t in b.GetTracks()if t.IsOnLayer(layer)and cut.Collide(t.GetEffectiveShape(layer))]
 if touchedpads or touchedcu:raise ValueError("Reviewed unused sliver cut reaches actual Source copper")
 cuts.setdefault(w["zone_uuid"],pcbnew.SHAPE_POLY_SET()).BooleanAdd(cut)
 rows.append(dict(net=r["net"],layer=r["layer"],zone_uuid=w["zone_uuid"],literal_filled_piece=w["literal_filled_piece"],literal_exact_twice_area_nm2=exact_twice_area(literal),sliver_bounds_mm=bounds,exact_cut_bounds_mm=[bounds[0]-margin,bounds[1]-margin,bounds[2]+margin,bounds[3]+margin],actual_source_pad_or_track_intersections=[]))
for uid,cut in cuts.items():
 z=zones[uid];poly=pcbnew.SHAPE_POLY_SET();poly.Append(z.Outline());poly.BooleanSubtract(cut)
 if poly.OutlineCount()!=1:raise ValueError("The bounded DFM cut unexpectedly splits a legitimate outline")
 z.Outline().RemoveAllContours();z.Outline().Append(poly)
dest=out/"motherboard-four-literal-slivers-candidate.kicad_pcb";pcbnew.SaveBoard(str(dest),b)
for suffix in(".kicad_pro",".kicad_dru"):shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
for f in base.parent.iterdir():
 if f.is_dir()and(f.suffix==".pretty"or f.name=="3dmodels"):shutil.copytree(f,out/f.name)
 elif f.name=="fp-lib-table":shutil.copy2(f,out/f.name)
write(out/"generation.json",dict(input_sha256=frozen,exact_four_unused_literal_slivers=rows,only_zone_outline_changes=True,no_area_tolerance_or_global_minimum_island_filter=True))
print("Literal unused DFM sliver cuts: native refill starts",flush=True);native=drc(dest,out,"native");b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity()
if oldcu!={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}or oldpads!={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}:raise ValueError("Old Source Cu/pads/poses changed")
after=native_pad_clusters(b,nets);survive=clusters_survive(before,after);write(out/"all-native-SOURCE-cluster-proof.json",dict(passed=survive,before=before,after=after))
if not survive:raise ValueError("Unused sliver correction changed a legitimate Source cluster")
if any(r["severity"]=="error"for r in native["violations"])or native["ignored_checks"]:raise ValueError("Native errors or ignored checks remain")
trees=[parse(without_generated_fills(p.read_text()))for p in(base,dest)];rawzones=[objects(tree,"zone")for tree in trees];ledger=[]
for uid in cuts:
 old,new=[zone_definition(d[uid])for d in rawzones];reason="Remove only the exact positive literal native unconnected DFM sliver, with an exact bounded 10 or 150 micrometre outline collar, after proving it touches no Source pad or track. No area threshold or blanket island suppression; all native Source clusters, old copper and manufacturer lands are preserved."
 ledger.append(dict(uuid=uid,before_definition_sha256=hashlib.sha256(old.encode()).hexdigest(),after_definition_sha256=hashlib.sha256(new.encode()).hexdigest(),electrical_outline_correction_reason=reason))
write(out/"bounded-scope.json",dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[],reviewed_added_zone_UUIDs=[],reviewed_existing_zone_outline_deltas=ledger,reviewed_scope_reason="Four exactly identified unused positive literal native DFM slivers removed by three tightly bounded same-net zone-outline cuts. No functional Source land, route, real Source cluster or manufactured component changes; complete native/refill/reference-loop/independent checks still required."))
full=validate(b,json.loads(mp.read_text()));full.update(board_sha256=sha(dest),source_map_sha256=sha(mp));write(out/"full-exact-literal-resource-review.json",full)
for old in rows:
 layer=b.GetLayerID(old["layer"]);z=next(z for z in b.Zones()if z.m_Uuid.AsString()==old["zone_uuid"]);cut=rectangle(old["sliver_bounds_mm"])
 hit=pcbnew.SHAPE_POLY_SET();hit.Append(z.GetFilledPolysList(layer));hit.BooleanIntersection(cut)
 if exact_twice_area(hit)>0:raise ValueError("Exact unused native sliver persists after refill")
run=subprocess.run([sys.executable,"tools/motion_card_routing_inventory.py","--board",str(dest),"--netlist","hardware/motherboard/netlist.xml","--source-design","hardware/motherboard/design.json","--out",str(out/"independent-connectivity")],capture_output=True,text=True);(out/"independent-command.txt").write_text(run.stdout+run.stderr)
if run.returncode:raise ValueError("Independent complete Source inventory failed")
ind=json.load(open(out/"independent-connectivity/review.json"))
receipt=dict(passed=True,before_board_sha256=sha(base),board_sha256=sha(dest),exact_unused_literal_slivers_removed=4,changed_zone_outlines=len(cuts),native_errors=0,native_DRC_types=dict(collections.Counter(r["type"]for r in native["violations"])),ignored_checks=[],all_old_Source_clusters_Cu_pads_poses_preserved=True,uncapped_unconnected=ind["uncapped_unconnected_ratsnest_edges"],independent_SOURCE_missing_joins=ind["independent_physical_cluster_missing_joins"],orphan_copper=ind["orphan_copper_items"],remaining_physically_unanchored_resources=len(full["unanchored_components"]),actual97bypass_proof_pending=True,manufacturing_ready=False)
write(out/"receipt.json",receipt);print(json.dumps(receipt,indent=2),flush=True)
