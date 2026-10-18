"""Copy-only convex router obstacles with strict conservative coverage proof.

Native fracture bridges are recovered by GEOS linework; the original native
integer obstacle must subtract to EMPTY against every replacement union.
Outward grid enclosures add blockage only. No physical/native source is edited.
"""
from pathlib import Path
import sys,json,copy,math,collections,hashlib,shutil,time
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT/'reports/motherboard-ordinary-routing-20261001/isolated-native-geometry-deps-r01'))
import pcbnew,shapely
from shapely.geometry import Polygon,MultiPoint
from shapely.ops import unary_union
from shapely.validation import explain_validity
import hardware_route_selected_additive_r02 as e
PRE=ROOT/'reports/freerouting-evaluation-20261002/ROOT103-GPIO-config-visual-selected-DSN-r02'
OUT=ROOT/'reports/freerouting-evaluation-20261002/ROOT103-GPIO-config-convex-DSN-r03'
assert not OUT.exists();shutil.copytree(PRE,OUT)
original=e.parse((PRE/'selected.dsn').read_text(encoding='utf8'));tree=copy.deepcopy(original)
structure=e.child(tree,'structure');records=[];replacement=[];started=time.monotonic()
hashtext=lambda s:hashlib.sha256(s.encode()).hexdigest()
def coords(p):return[(round(float(p[i])*1000),round(float(p[i+1])*1000))for i in range(3,len(p),2)]
def area2(p):return sum(x*y1-x1*y for(x,y),(x1,y1)in zip(p,p[1:]+p[:1]))
def edges(p):return list(zip(p,p[1:]+p[:1]))
def hull(points):
 points=sorted(set(points));lo=[];hi=[]
 cross=lambda o,a,b:(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 for p in points:
  while len(lo)>=2 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
  lo.append(p)
 for p in reversed(points):
  while len(hi)>=2 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
  hi.append(p)
 return lo[:-1]+hi[:-1]
def conservative_grid_convex(points):
 # Exact100nm declared DSN grid. Every input vertex lies inside its outward
 # floor/ceil box with a further one-grid-cell collar; convexity then covers
 # the full original triangle/piece. No rounding can shrink an obstacle.
 out=[]
 for x,y in points:
  left=math.floor(x/100)*100-100;right=math.ceil(x/100)*100+100
  bottom=math.floor(y/100)*100-100;top=math.ceil(y/100)*100+100
  out.extend([(left,bottom),(right,bottom),(right,top),(left,top)])
 p=hull(out);assert len(p)>=3 and area2(p)>0 and all(x%100==0 and y%100==0 for x,y in p)
 return p
def parts(g):
 if isinstance(g,Polygon):return[g]
 if hasattr(g,'geoms'):return[p for child in g.geoms for p in parts(child)]
 return[]
def convex_partition(g):
 tris=list(shapely.get_parts(shapely.constrained_delaunay_triangles(g)))
 pieces={};edgeowners=collections.defaultdict(set);queue=[]
 for i,t in enumerate(tris):
  p=[tuple(v)for v in list(t.exterior.coords)[:-1]]
  if area2(p)<0:p.reverse()
  if all(x.is_integer()and y.is_integer()for x,y in p):p=[(int(x),int(y))for x,y in p]
  pieces[i]=p
  for a,b in edges(p):edgeowners[tuple(sorted((a,b)))].add(i)
 for edge,owners in edgeowners.items():
  if len(owners)==2:queue.append((edge,*owners))
 while queue:
  edge,i,j=queue.pop()
  if i not in pieces or j not in pieces or edgeowners.get(edge)!=set((i,j)):continue
  a,b=pieces[i],pieces[j]
  if len(a)+len(b)>32 or not all(isinstance(x,int)and isinstance(y,int)for x,y in a+b):continue
  boundary=set(edges(a))
  for x,y in edges(b):
   if(y,x)in boundary:boundary.remove((y,x))
   else:boundary.add((x,y))
  successors={x:y for x,y in boundary}
  if len(successors)!=len(boundary):continue
  start=next(iter(successors));p=[start];at=successors[start]
  while at!=start and at in successors and len(p)<=len(boundary):p.append(at);at=successors[at]
  if at!=start or len(p)!=len(boundary):continue
  if any((y[0]-x[0])*(z[1]-y[1])-(y[1]-x[1])*(z[0]-y[0])<0 for x,y,z in zip(p,p[1:]+p[:1],p[2:]+p[:2])):continue
  assert area2(p)==area2(a)+area2(b)
  for old in(a,b):
   for x,y in edges(old):edgeowners[tuple(sorted((x,y)))].discard(i);edgeowners[tuple(sorted((x,y)))].discard(j)
  pieces[i]=p;del pieces[j]
  for x,y in edges(p):
   key=tuple(sorted((x,y)));edgeowners[key].add(i)
   if len(edgeowners[key])==2:queue.append((key,*edgeowners[key]))
 return list(pieces.values()),len(tris)
def native_poly(outer,holes=()):
 out=pcbnew.SHAPE_POLY_SET();out.NewOutline()
 for x,y in outer:out.Append(int(x),int(y))
 for hole in holes:
  h=out.NewHole(0)
  for x,y in hole:out.Append(int(x),int(y),0,h)
 return out
def emitted(p,layer,name):
 result=['keepout',e.q(name),['polygon',e.q(layer),'0']]
 for x,y in p:result[2].extend([str(x/1000),str(y/1000)])
 return result
oldlist=e.children(structure,'keepout')
for index,k in enumerate(oldlist):
 raw=e.child(k,'polygon')
 if raw is None:continue
 outer=coords(raw);holes=[coords(e.child(w,'polygon'))for w in e.children(k,'window')]
 before_geom=Polygon(outer,holes);valid=before_geom.is_valid
 recovered=before_geom if valid else shapely.make_valid(before_geom,method='linework')
 polygons=parts(recovered)
 convex=[];tri_count=0;degenerate=not polygons
 for p in polygons:
  assert p.is_valid and p.area>0
  partition,nt=convex_partition(p);tri_count+=nt
  convex.extend(conservative_grid_convex(v)for v in partition)
 if degenerate:convex=[conservative_grid_convex(outer)]
 # Valid zero-area input is never omitted; every serialised vertex is enclosed.
 assert convex
 after_geoms=[Polygon(p)for p in convex];after_union=unary_union(after_geoms)
 positive_before=unary_union(polygons)if polygons else before_geom
 geos_missing=positive_before.difference(after_union)
 assert geos_missing.is_empty,(index,'GEOS obstacle undercoverage',geos_missing.wkt)
 assert all(g.is_valid and g.area>0 and g.equals(g.convex_hull)for g in after_geoms)
 native_before=native_poly(outer,holes);native_after=pcbnew.SHAPE_POLY_SET()
 for p in convex:native_after.Append(native_poly(p))
 native_after.Simplify();missing=pcbnew.SHAPE_POLY_SET(native_before);missing.BooleanSubtract(native_after)
 assert missing.OutlineCount()==0,(index,'Native obstacle undercoverage',missing.Area())
 names=[];new_indices=[];hashes=[]
 for piece,p in enumerate(convex):
  name='LiteralConvex_'+str(index)+'_'+str(piece);obj=emitted(p,e.value(raw[1]),name)
  names.append(name);new_indices.append(len(replacement));hashes.append(hashtext(e.dump(obj)));replacement.append(obj)
 structure.remove(k)
 records.append(dict(original_keepout_index=index,original_definition_sha256=hashtext(e.dump(k)),original_layer=e.value(raw[1]),original_valid=valid,original_reason=explain_validity(before_geom),original_exact_outer_IU=outer,original_exact_holes_IU=holes,native_fractured_outline_recovered=not valid,degenerate_positive_conservative_enclosure=degenerate,original_triangle_count=tri_count,replacement_count=len(convex),replacement_names=names,replacement_definition_sha256=hashes,replacement_sequence_indices=new_indices,GEOS_missing_is_empty=True,native_missing_outline_count=0,source_interpreted_positive_area_IU2=positive_before.area,conservative_added_blockage_area_IU2=after_union.difference(positive_before).area,grid_IU=100,conservative_outward_vertex_bound_IU=200))
 if(index+1)%1000==0:print(json.dumps(dict(processed=index+1,emitted=len(replacement),seconds=time.monotonic()-started)),flush=True)
structure.extend(replacement)
remaining_original=copy.deepcopy(original);remaining_changed=copy.deepcopy(tree)
for x in(remaining_original,remaining_changed):
 s=e.child(x,'structure')
 for k in list(e.children(s,'keepout')):
  if e.child(k,'polygon')is not None:s.remove(k)
assert remaining_original==remaining_changed,'Any non-polygon-obstacle object changed'
dest=OUT/'selected.dsn';dest.write_text(e.dump(tree)+'\n',encoding='utf8')
review=dict(passed=True,copy_only=True,input_DSN_path=str(PRE/'selected.dsn'),input_DSN_sha256=e.sha(PRE/'selected.dsn'),output_DSN_path=str(dest),output_DSN_sha256=e.sha(dest),board_sha256=e.sha(OUT/'base.kicad_pcb'),converter_sha256=e.sha(__file__),shapely_version=shapely.__version__,GEOS_version=shapely.geos_version_string,original_polygon_keepouts=len(records),emitted_valid_convex_polygon_keepouts=len(replacement),original_obstacles_all_conservatively_covered=True,no_positive_or_degenerate_obstacle_skipped=True,original_library_placement_network_rules_protected_wiring_and_nonpolygon_obstacles_unchanged=True,declared_original_DSN_grid_um=.1,exact_native_geometry_or_guard_changed=False,maximum_outward_vertex_grid_expansion_nm=200,records=records,manufacturing_ready=False)
e.write(OUT/'convex-conservative-coverage-review.json',review)
prepare=e.read(OUT/'prepare.json');prepare.update(selected_dsn_sha256=e.sha(dest),copy_only_convex_obstacle_conversion=dict(review_path=str(OUT/'convex-conservative-coverage-review.json'),review_sha256=e.sha(OUT/'convex-conservative-coverage-review.json'),source_DSN_sha256=e.sha(PRE/'selected.dsn'),native_board_unchanged=True))
e.write(OUT/'prepare.json',prepare)
print(json.dumps(dict(passed=True,polygons=len(records),emitted=len(replacement),sha256=e.sha(dest),seconds=time.monotonic()-started)),flush=True)
