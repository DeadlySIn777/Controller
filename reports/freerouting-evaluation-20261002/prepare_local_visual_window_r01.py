"""Copy-only restricted-search DSN; every original obstacle remains covered.

Only the two previously reviewed and actually unjoined general-DI visual nets
remain eligible. Opaque outside blockers restrict router search; no native
board, placement, conductor, manufacturing or return rule is changed.
"""
from pathlib import Path
import sys,json,copy,hashlib,shutil,time,collections
ROOT=Path.cwd()
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'reports/motherboard-ordinary-routing-20261001/isolated-native-geometry-deps-r01')]
import pcbnew,shapely
from shapely.geometry import Polygon,box,MultiPoint
from shapely.ops import unary_union
import hardware_route_selected_additive_r02 as e
PRE=ROOT/'reports/freerouting-evaluation-20261002/ROOT103-visual-selected-DSN-r01'
OUT=ROOT/'reports/freerouting-evaluation-20261002/ROOT103-visual-local-window-DSN-r05'
WINDOW=(300_000_000,120_000_000,330_000_000,150_000_000)
NETS=['/motherboard_status/OBS8_INVERTED','/motherboard_status/OBS9_INVERTED']
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
assert not OUT.exists();shutil.copytree(PRE,OUT)
hashtext=lambda s:hashlib.sha256(s.encode()).hexdigest()
started=time.monotonic()
def coords(raw):return[(round(float(raw[i])*1000),round(float(raw[i+1])*1000))for i in range(3,len(raw),2)]
def parts(g):
 if isinstance(g,Polygon):return[g]
 if hasattr(g,'geoms'):return[p for c in g.geoms for p in parts(c)]
 return[]
def native(outer,holes=()):
 out=pcbnew.SHAPE_POLY_SET();out.NewOutline()
 for x,y in outer:out.Append(int(x),int(y))
 for hole in holes:
  h=out.NewHole(0)
  for x,y in hole:out.Append(int(x),int(y),0,h)
 return out
def area2(p):return sum(x*y1-x1*y for(x,y),(x1,y1)in zip(p,p[1:]+p[:1]))
def edges(p):return list(zip(p,p[1:]+p[:1]))
def strip_collinear(p):
 while len(p)>3:
  r=[b for a,b,c in zip(p[-1:]+p[:-1],p,p[1:]+p[:1]) if (b[0]-a[0])*(c[1]-b[1])!=(b[1]-a[1])*(c[0]-b[0])]
  if len(r)==len(p):return p
  p=r
 return p
def partition(g):
 tris=list(shapely.get_parts(shapely.constrained_delaunay_triangles(g)))
 pieces={};owners=collections.defaultdict(set);queue=[]
 for i,t in enumerate(tris):
  p=[tuple(v)for v in list(t.exterior.coords)[:-1]]
  assert all(x.is_integer()and y.is_integer()for x,y in p)
  p=[(int(x),int(y))for x,y in p]
  if area2(p)<0:p.reverse()
  pieces[i]=p
  for a,b in edges(p):owners[tuple(sorted((a,b)))].add(i)
 for edge,ids in owners.items():
  if len(ids)==2:queue.append((edge,*ids))
 queue.sort(key=lambda v:(v[0][0][0]-v[0][1][0])**2+(v[0][0][1]-v[0][1][1])**2)
 while queue:
  edge,i,j=queue.pop()
  if i not in pieces or j not in pieces or owners.get(edge)!=set((i,j)):continue
  a,b=pieces[i],pieces[j];boundary=set(edges(a))
  for x,y in edges(b):
   if(y,x)in boundary:boundary.remove((y,x))
   else:boundary.add((x,y))
  successor={x:y for x,y in boundary}
  if len(successor)!=len(boundary):continue
  start=next(iter(successor));p=[start];at=successor[start]
  while at!=start and at in successor and len(p)<=len(boundary):p.append(at);at=successor[at]
  if at!=start or len(p)!=len(boundary):continue
  if any((y[0]-x[0])*(z[1]-y[1])-(y[1]-x[1])*(z[0]-y[0])<0 for x,y,z in zip(p,p[1:]+p[:1],p[2:]+p[:2])):continue
  assert area2(p)==area2(a)+area2(b)
  for old in(a,b):
   for x,y in edges(old):owners[tuple(sorted((x,y)))].discard(i);owners[tuple(sorted((x,y)))].discard(j)
  pieces[i]=p;del pieces[j]
  for x,y in edges(p):
   key=tuple(sorted((x,y)));owners[key].add(i)
   if len(owners[key])==2:queue.append((key,*owners[key]))
 result=[strip_collinear(p)for p in pieces.values()]
 # Integer shoelace, not rounded floating-point polygon area, accounts for
 # large coordinate offsets and native-IU slivers exactly.
 ring=lambda r:[(round(x),round(y))for x,y in list(r.coords)[:-1]]
 exact=abs(area2(ring(g.exterior)))-sum(abs(area2(ring(h)))for h in g.interiors)
 assert sum(area2(p)for p in result)==exact
 return result,len(tris)
def emit(p,layer,name):
 raw=['polygon',e.q(layer),'0']
 for x,y in p:raw.extend([str(x/1000),str(y/1000)])
 return ['keepout',e.q(name),raw]
original=e.parse((PRE/'selected.dsn').read_text());tree=copy.deepcopy(original);structure=e.child(tree,'structure')
prepare=e.read(PRE/'prepare.json');manifest=e.read(PRE/'manifest.json')
assert prepare['selection']['selected_nets']==NETS and set(manifest['nets'])==set(NETS)
b=pcbnew.LoadBoard(str(PRE/'base.kicad_pcb'))
assert e.sha(PRE/'base.kicad_pcb')=='639e1b7803bfaa24480d824d97d0d487e545b658a0e3e343435e8297083ef053'
pads={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()}
endpoints=[]
for net in NETS:
 for ref,pin in manifest['nets'][net]['source_pins']:
  p=pads[(ref,pin)];pt=p.GetPosition();assert WINDOW[0]<pt.x<WINDOW[2]and WINDOW[1]<pt.y<WINDOW[3]
  assert p.GetNetname()==net
  endpoints.append(dict(net=net,reference=ref,pin=pin,pad_uuid=str(p.m_Uuid),xy_IU=[pt.x,pt.y]))
window=box(*WINDOW);local=collections.defaultdict(list);records=[];geometries={};maxbox=[WINDOW[0]-1_000_000,WINDOW[1]-1_000_000,WINDOW[2]+1_000_000,WINDOW[3]+1_000_000]
for index,k in enumerate(e.children(structure,'keepout')):
 raw=e.child(k,'polygon')
 if raw is None:continue
 layer=e.value(raw[1]);assert layer in LAYERS
 outer=coords(raw);holes=[coords(e.child(w,'polygon'))for w in e.children(k,'window')]
 g=Polygon(outer,holes);recovered=g if g.is_valid else shapely.make_valid(g,method='linework');positive=unary_union(parts(recovered))
 if positive.is_empty:
  # Retain zero-area records conservatively rather than omitting them.
  positive=MultiPoint(outer).convex_hull.buffer(200,quad_segs=16)
 geometries[index]=positive
 minx,miny,maxx,maxy=positive.bounds
 maxbox=[min(maxbox[0],int(minx)-1_000_000),min(maxbox[1],int(miny)-1_000_000),max(maxbox[2],int(maxx)+1_000_000),max(maxbox[3],int(maxy)+1_000_000)]
 clipped=positive.intersection(window)
 if not clipped.is_empty:local[layer].extend(parts(clipped))
 records.append(dict(original_keepout_index=index,original_definition_sha256=hashtext(e.dump(k)),layer=layer,exact_outer_IU=outer,exact_holes_IU=holes,has_positive_local_intersection=not clipped.is_empty,replacement_layer_group=layer))
 structure.remove(k)
extent=(maxbox[0]//100*100,maxbox[1]//100*100,(maxbox[2]+99)//100*100,(maxbox[3]+99)//100*100);x0,y0,x1,y1=extent;wx0,wy0,wx1,wy1=WINDOW
outside=[box(x0,y0,wx0,y1),box(wx1,y0,x1,y1),box(wx0,y0,wx1,wy0),box(wx0,wy1,wx1,y1)]
groups={};replacement=[]
for layer in LAYERS:
 source=unary_union(local[layer]);expanded=source.buffer(200,quad_segs=16,join_style='round')
 snapped=shapely.set_precision(expanded,100,mode='valid_output')
 assert source.difference(snapped).is_empty
 convex=[];triangles=0
 for g in parts(snapped):
  pp,nt=partition(g);convex.extend(pp);triangles+=nt
 convex=[[(round(x),round(y))for x,y in list(g.exterior.coords)[:-1]]for g in outside]+convex
 outgeom=unary_union([Polygon(p)for p in convex]);native_group=pcbnew.SHAPE_POLY_SET();names=[];hashes=[];indices=[]
 for i,p in enumerate(convex):
  assert all(x%100==0 and y%100==0 for x,y in p)
  g=Polygon(p);assert g.is_valid and g.area>0 and g.equals(g.convex_hull)
  native_group.Append(native(p));obj=emit(p,layer,'LocalVisual_'+layer.replace('.','_')+'_'+str(i))
  names.append(e.value(obj[1]));hashes.append(hashtext(e.dump(obj)));indices.append(len(replacement));replacement.append(obj)
 native_group.Simplify()
 for row in records:
  if row['layer']!=layer:continue
  assert geometries[row['original_keepout_index']].difference(outgeom).is_empty
  missing=native(row['exact_outer_IU'],row['exact_holes_IU']);missing.BooleanSubtract(native_group)
  assert missing.OutlineCount()==0,(row['original_keepout_index'],'Native obstacle undercoverage')
  row.update(GEOS_missing_is_empty=True,native_missing_outline_count=0)
 groups[layer]=dict(replacement_names=names,replacement_definition_sha256=hashes,replacement_sequence_indices=indices,opaque_outside_polygons=4,local_convex_polygons=len(convex)-4,local_source_triangles=triangles,max_vertices=max(map(len,convex)),all_original_positive_geometry_covered=True)
 print(json.dumps(dict(layer=layer,pieces=len(convex),triangles=triangles,seconds=time.monotonic()-started)),flush=True)
remaining_count=len(e.children(structure,'keepout'));structure.extend(replacement)
for row in groups.values():row['replacement_final_keepout_indices']=[remaining_count+i for i in row['replacement_sequence_indices']]
a=copy.deepcopy(original);c=copy.deepcopy(tree)
for v in(a,c):
 s=e.child(v,'structure')
 for k in list(e.children(s,'keepout')):
  if e.child(k,'polygon')is not None:s.remove(k)
assert a==c,'Non-obstacle/source eligibility/protected wiring changed'
dest=OUT/'selected.dsn';dest.write_text(e.dump(tree)+'\n',encoding='utf8')
report=OUT/'local-window-conservative-review.json'
e.write(report,dict(passed=True,copy_only=True,restricted_search_only=True,source_board_sha256=e.sha(PRE/'base.kicad_pcb'),source_DSN_path=str(PRE/'selected.dsn'),source_DSN_sha256=e.sha(PRE/'selected.dsn'),output_DSN_path=str(dest),output_DSN_sha256=e.sha(dest),converter_sha256=e.sha(__file__),selected_nets=NETS,required_joins_before=2,required_native_endpoints=endpoints,window_IU=WINDOW,opaque_outside_blocker_extent_IU=extent,original_polygon_obstacles=len(records),replacement_convex_polygon_obstacles=len(replacement),maximum_output_vertices=max(g['max_vertices']for g in groups.values()),all_non_polygon_obstacles_and_non_obstacle_records_exact=True,native_board_or_rules_changed=False,source_manifest_and_existing_source_anchored_reference_piece_receipt_unchanged=True,local_outward_grid_bound_nm=300,opaque_outside_blockage_is_explicit_search_restriction_not_reference_or_physical_copper=True,groups=groups,records=records,manufacturing_ready=False))
prepare.update(selected_dsn_sha256=e.sha(dest),copy_only_local_window_conversion=dict(review_path=str(report),review_sha256=e.sha(report),source_DSN_sha256=e.sha(PRE/'selected.dsn'),window_IU=WINDOW,native_board_unchanged=True))
e.write(OUT/'prepare.json',prepare)
print(json.dumps(dict(passed=True,pieces=len(replacement),max_vertices=max(g['max_vertices']for g in groups.values()),DSN_bytes=dest.stat().st_size,DSN_sha256=e.sha(dest),seconds=time.monotonic()-started)),flush=True)
