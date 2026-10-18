"""Choose only new integer intersection vertices inward of exact old edges."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'diagnose_R543_four_clusters_literal_integer_unions_r611.py').read_text(encoding='utf-8')
s=s.replace('R543-four-native-overlap-clusters-literal-integer-union-diagnostic-r611','R543-overlap-exact-inward-intersection-native-splice-diagnostic-r617')
s=s.replace('from shapely.ops import unary_union','from shapely.ops import unary_union\nfrom shapely.geometry import Polygon,MultiPolygon,GeometryCollection\nfrom fractions import Fraction\nimport math')
anchor='def main():\n'
helper='''def F(p):return tuple(Fraction.from_float(float(v))for v in p)
def orient(a,b,p):return(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
def inward_union(literal,before):
 parts=list(literal.geoms)if literal.geom_type=='MultiPolygon'else[literal]
 tokens={tuple(p)for a in before for part in(list(a.geoms)if a.geom_type=='MultiPolygon'else[a])for ring in[part.exterior]+list(part.interiors)for p in ring.coords}
 generated=[];polys=[]
 for part in parts:
  rings=[]
  for hole,ring in enumerate([part.exterior]+list(part.interiors)):
   pp=list(ring.coords)[:-1];out=[];inside=(1 if ring.is_ccw else-1)*(-1 if hole else 1)
   for j,p in enumerate(pp):
    vertex=tuple(p)
    if vertex in tokens:out.append(vertex);continue
    prev=tuple(pp[j-1]);nxt=tuple(pp[(j+1)%len(pp)]);vf=F(vertex);pf=F(prev);nf=F(nxt);kx=(vf[0]*1000000).__floor__();ky=(vf[1]*1000000).__floor__();found=[]
    for radius in (2,4,8,16,32):
     for x in range(kx-radius,kx+radius+2):
      for y in range(ky-radius,ky+radius+2):
       candidate=(x/1e6,y/1e6);cf=F(candidate);o1=inside*orient(pf,vf,cf);o2=inside*orient(vf,nf,cf)
       if o1>=0 and o2>=0:found.append(((cf[0]-vf[0])**2+(cf[1]-vf[1])**2,candidate,o1,o2))
     if found:break
    assert found,('no inward integer point',vertex,prev,nxt,inside)
    _,candidate,o1,o2=min(found,key=lambda r:r[0]);out.append(candidate)
    generated.append({'literal_intersection_mm':vertex,'new_integer_mm':candidate,'incoming_exact_old_edge_mm':[prev,vertex],'outgoing_exact_old_edge_mm':[vertex,nxt],'copper_inside_orientation_sign':inside,'exact_Fraction_incoming_inside_cross':str(o1),'exact_Fraction_outgoing_inside_cross':str(o2),'both_exact_halfplane_nonnegative':True,'displacement_mm':math.dist(vertex,candidate),'search_grid_radius_nm':radius,'only_new_intersection_vertex_changes':True})
   rings.append(out)
  poly=Polygon(rings[0],rings[1:]);assert poly.is_valid;polys.append(poly)
 after=polys[0]if len(polys)==1 else MultiPolygon(polys)if polys else GeometryCollection();assert after.is_valid
 return after,generated
'''
assert anchor in s;s=s.replace(anchor,helper+anchor)
old="   after=set_precision(literal,1e-6,mode='valid_output');actual=zero(after)"
new="   after,generated=inward_union(literal,before);actual=zero(after);put(OUT/(f'cluster-{i}-{role}-exact-new-intersection-inward-ledger.json'),generated)"
assert old in s;s=s.replace(old,new)
s=s.replace("'proposed_integer_grid_mm':get_precision(after)","'proposed_integer_grid_mm':get_precision(after),'old_vertex_tokens_retained':True,'new_intersection_vertices_exact_inward_halfplanes':len(generated)")
s=s.replace("print('R611'","print('R617'")
exec(compile(s,str(Path(__file__)),'exec'))
