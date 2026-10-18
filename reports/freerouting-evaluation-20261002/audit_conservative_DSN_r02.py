"""Read-only independent whole-layer obstacle coverage + exact record audit."""
from pathlib import Path
import argparse,collections,hashlib,json,sys,time
ROOT=Path.cwd();sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
import hardware_route_selected_additive_r02 as parser
from independent_obstacle_geometry import reconstruct,Polygon,unary_union
from shapely.prepared import prep

ap=argparse.ArgumentParser()
for name in ('before','after','out'):ap.add_argument('--'+name,type=Path,required=True)
ap.add_argument('--expect-format',choices=['convex','simple-with-windows'],default='convex')
a=ap.parse_args();assert not a.out.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs={str(p.resolve()):sha(p)for p in(a.before,a.after,Path(__file__),Path(__file__).with_name('independent_obstacle_geometry.py'))}
trees=[parser.parse(p.read_text(encoding='utf8'))for p in(a.before,a.after)]
structures=[parser.child(t,'structure')for t in trees]
assert [[parser.dump(x)if isinstance(x,list)else x for x in t if x is not s]for t,s in zip(trees,structures)][0]==[[parser.dump(x)if isinstance(x,list)else x for x in t if x is not s]for t,s in zip(trees,structures)][1]
def non_obstacles(s):return [parser.dump(x)if isinstance(x,list)else x for x in s if not(isinstance(x,list)and x[0]=='keepout')]
assert non_obstacles(structures[0])==non_obstacles(structures[1])
def coordinates(p):return[(float(p[i]),float(p[i+1]))for i in range(3,len(p),2)]
def extract(s):
 rows=[]
 for n,k in enumerate(parser.children(s,'keepout')):
  p=parser.child(k,'polygon')
  if p is None:raise ValueError('Unreviewed non-polygon keepout')
  outer=coordinates(p);holes=[coordinates(parser.child(w,'polygon'))for w in parser.children(k,'window')]
  rows.append((n,parser.value(p[1]),outer,holes,sha_text(parser.dump(k))))
 return rows
def sha_text(t):return hashlib.sha256(t.encode()).hexdigest()
before,after=map(extract,structures)
olddefs={r[4]for r in before};by_layer=collections.defaultdict(list);new_convex=0
for n,layer,outer,holes,digest in after:
 g=Polygon(outer,holes)
 if not g.is_valid or g.area<=0:raise ValueError('Invalid/empty emitted obstacle '+str(n))
 if digest not in olddefs:
  if a.expect_format=='convex' and (holes or not g.symmetric_difference(g.convex_hull).is_empty):raise ValueError('New obstacle is not convex '+str(n))
  if not g.exterior.is_simple or any(not ring.is_simple for ring in g.interiors):raise ValueError('New obstacle has nonsimple ring '+str(n))
  if any(abs(v*10-round(v*10))>1e-7 for ring in [outer,*holes] for pair in ring for v in pair):raise ValueError('Off0.1um integer-grid output '+str(n))
  new_convex+=1
 by_layer[layer].append(g)
unions={layer:unary_union(shapes)for layer,shapes in by_layer.items()}
prepared={layer:prep(g)for layer,g in unions.items()}
rows=[];failures=[];reconstructed=0
for n,layer,outer,holes,digest in before:
 g,lines,rebuilt=reconstruct(outer,holes);reconstructed+=int(rebuilt)
 target=g if not g.is_empty else lines
 good=layer in prepared and prepared[layer].covers(target)
 missing=target.difference(unions[layer]) if layer in unions and not good else None
 if missing is not None and not missing.is_empty:
  failures.append(dict(index=n,layer=layer,area_um2=missing.area,length_um=missing.length,wkt=missing.wkt[:1000]))
 elif not good:good=missing is not None and missing.is_empty
 rows.append(dict(index=n,layer=layer,original_sha256=digest,reconstructed_by_independent_parity=rebuilt,passed=good))
 assert sha(a.before)==inputs[str(a.before.resolve())] if n==0 else True
 if n and n%1000==0:print(json.dumps(dict(checked=n,failures=len(failures))),flush=True)
assert all(sha(Path(p))==h for p,h in inputs.items())
r=dict(passed=not failures and all(x['passed']for x in rows),input_sha256=inputs,
 exact_all_non_obstacle_records_preserved=True,original_obstacles=len(before),output_obstacles=len(after),
 required_output_format=a.expect_format,new_valid_grid_obstacles=new_convex,independently_reconstructed_originals=reconstructed,
 every_original_obstacle_covered_without_area_tolerance=not failures,failures=failures,rows=rows,
 original_native_board_mutated=False,router_or_native_import_pass_claim=False,manufacturing_ready=False)
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items()if k not in('rows','input_sha256','failures')}),flush=True)
raise SystemExit(0 if r['passed']else 1)
