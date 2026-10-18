"""Compact copy-only DSN obstacles with explicit legal window holes.

Original obstacle material must subtract to EMPTY in independent GEOS and
native integer operations. Conservative grid construction adds blockage only;
it does not change any PCB conductor, reference requirement or routing rule.
"""
from pathlib import Path
import sys,json,copy,hashlib,shutil,time
ROOT=Path.cwd();sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'reports/motherboard-ordinary-routing-20261001/isolated-native-geometry-deps-r01')]
import pcbnew,shapely
from shapely.geometry import Polygon,MultiPoint
from shapely.ops import unary_union
from shapely.validation import explain_validity
import hardware_route_selected_additive_r02 as e
PRE=ROOT/'reports/freerouting-evaluation-20261002/ROOT103-GPIO-config-visual-selected-DSN-r02'
OUT=ROOT/'reports/freerouting-evaluation-20261002/ROOT103-GPIO-config-window-DSN-r04'
assert not OUT.exists();shutil.copytree(PRE,OUT)
original=e.parse((PRE/'selected.dsn').read_text(encoding='utf8'));tree=copy.deepcopy(original)
structure=e.child(tree,'structure');records=[];replacement=[];started=time.monotonic()
hashtext=lambda s:hashlib.sha256(s.encode()).hexdigest()
def coords(raw):return[(round(float(raw[i])*1000),round(float(raw[i+1])*1000))for i in range(3,len(raw),2)]
def parts(g):
 if isinstance(g,Polygon):return[g]
 if hasattr(g,'geoms'):return[p for c in g.geoms for p in parts(c)]
 return[]
def native_poly(outer,holes=()):
 out=pcbnew.SHAPE_POLY_SET();out.NewOutline()
 for x,y in outer:out.Append(int(x),int(y))
 for hole in holes:
  h=out.NewHole(0)
  for x,y in hole:out.Append(int(x),int(y),0,h)
 return out
def emit(p,layer,name):
 def ring(v):
  result=['polygon',e.q(layer),'0']
  for x,y in v:result.extend([str(x/1000),str(y/1000)])
  return result
 outer=[(round(x),round(y))for x,y in list(p.exterior.coords)[:-1]]
 holes=[[(round(x),round(y))for x,y in list(h.coords)[:-1]]for h in p.interiors]
 assert all(x%100==0 and y%100==0 for r in[outer,*holes]for x,y in r)
 assert Polygon(outer,holes).is_valid and all(Polygon(r).is_valid for r in[outer,*holes])
 return ['keepout',e.q(name),ring(outer),*(['window',ring(h)]for h in holes)],outer,holes
for index,k in enumerate(e.children(structure,'keepout')):
 raw=e.child(k,'polygon')
 if raw is None:continue
 outer=coords(raw);holes=[coords(e.child(w,'polygon'))for w in e.children(k,'window')]
 g=Polygon(outer,holes);valid=g.is_valid;recovered=g if valid else shapely.make_valid(g,method='linework')
 polygon_parts=parts(recovered);positive=unary_union(polygon_parts)if polygon_parts else g
 degenerate=not polygon_parts
 # The DSN declares a100nm grid. The200nm circular outward collar exceeds
 # the70.711nm maximum point displacement when snapping to that grid. Round
 # joins use64 chords/circle; their radial undershoot is<0.241nm. Final exact
 # GEOS/native coverage, rather than this construction estimate, is the gate.
 source=positive if polygon_parts else MultiPoint(outer).convex_hull
 expanded=source.buffer(200,quad_segs=16,join_style='round',cap_style='round')
 snapped=shapely.set_precision(expanded,100,mode='valid_output')
 emitted_parts=parts(snapped);assert emitted_parts,(index,'No obstacle may be skipped')
 after=unary_union(emitted_parts);assert after.is_valid
 missing=positive.difference(after)
 assert missing.is_empty,(index,'GEOS obstacle undercoverage',missing.wkt)
 if degenerate:assert all(after.covers(MultiPoint([v]))for v in outer)
 native_before=native_poly(outer,holes);native_after=pcbnew.SHAPE_POLY_SET()
 names=[];hashes=[];indices=[];ring_counts=[];objects=[]
 for piece,p in enumerate(emitted_parts):
  assert p.is_valid and p.area>0
  obj,oo,hh=emit(p,e.value(raw[1]),'LiteralWindow_'+str(index)+'_'+str(piece))
  native_after.Append(native_poly(oo,hh));objects.append(obj)
  names.append(e.value(obj[1]));hashes.append(hashtext(e.dump(obj)));indices.append(len(replacement));replacement.append(obj);ring_counts.append(dict(outer_vertices=len(oo),window_holes=len(hh),hole_vertices=sum(map(len,hh))))
 native_after.Simplify();native_missing=pcbnew.SHAPE_POLY_SET(native_before);native_missing.BooleanSubtract(native_after)
 assert native_missing.OutlineCount()==0,(index,'Native obstacle undercoverage',native_missing.Area())
 structure.remove(k)
 records.append(dict(original_keepout_index=index,original_definition_sha256=hashtext(e.dump(k)),original_layer=e.value(raw[1]),original_valid=valid,original_reason=explain_validity(g),original_exact_outer_IU=outer,original_exact_holes_IU=holes,native_fractured_outline_recovered=not valid,degenerate_positive_conservative_enclosure=degenerate,replacement_count=len(objects),replacement_names=names,replacement_definition_sha256=hashes,replacement_sequence_indices=indices,replacement_ring_counts=ring_counts,GEOS_missing_is_empty=True,native_missing_outline_count=0,source_interpreted_positive_area_IU2=positive.area,conservative_added_blockage_area_IU2=after.difference(positive).area,grid_IU=100,outward_buffer_IU=200,maximum_round_join_radial_undershoot_IU=.241,maximum_grid_point_snap_displacement_IU=70.711,conservative_copy_only_boundary_displacement_bound_IU=300))
 if(index+1)%1000==0:print(json.dumps(dict(processed=index+1,emitted=len(replacement),seconds=time.monotonic()-started)),flush=True)
unchanged_nonpolygon_count=len(e.children(structure,'keepout'));structure.extend(replacement)
for row in records:row['replacement_final_keepout_indices']=[unchanged_nonpolygon_count+i for i in row['replacement_sequence_indices']]
a=copy.deepcopy(original);b=copy.deepcopy(tree)
for v in(a,b):
 s=e.child(v,'structure')
 for k in list(e.children(s,'keepout')):
  if e.child(k,'polygon')is not None:s.remove(k)
assert a==b,'Non-polygon obstacle or any library/placement/network/rule/wiring changed'
dest=OUT/'selected.dsn';dest.write_text(e.dump(tree)+'\n',encoding='utf8')
report=OUT/'window-conservative-coverage-review.json'
e.write(report,dict(passed=True,copy_only=True,input_DSN_path=str(PRE/'selected.dsn'),input_DSN_sha256=e.sha(PRE/'selected.dsn'),output_DSN_path=str(dest),output_DSN_sha256=e.sha(dest),board_sha256=e.sha(OUT/'base.kicad_pcb'),converter_sha256=e.sha(__file__),shapely_version=shapely.__version__,GEOS_version=shapely.geos_version_string,original_polygon_keepouts=len(records),emitted_valid_simple_polygon_window_keepouts=len(replacement),emitted_windows=sum(v['window_holes']for r in records for v in r['replacement_ring_counts']),original_obstacles_all_conservatively_covered=True,no_positive_or_degenerate_obstacle_skipped=True,all_nonpolygon_obstacles_and_library_placement_network_rules_protected_wiring_unchanged=True,original_DSN_resolution_um=.1,constructed_copy_only_maximum_boundary_displacement_nm=300,native_source_board_geometry_or_guards_changed=False,records=records,manufacturing_ready=False))
receipt=e.read(OUT/'prepare.json');receipt.update(selected_dsn_sha256=e.sha(dest),copy_only_polygon_window_conversion=dict(review_path=str(report),review_sha256=e.sha(report),source_DSN_sha256=e.sha(PRE/'selected.dsn'),native_board_unchanged=True));e.write(OUT/'prepare.json',receipt)
print(json.dumps(dict(passed=True,polygons=len(records),emitted=len(replacement),windows=sum(v['window_holes']for r in records for v in r['replacement_ring_counts']),sha256=e.sha(dest),seconds=time.monotonic()-started)),flush=True)
