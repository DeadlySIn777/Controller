"""Preserve all constituent vertex tokens; integerize only union intersections."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'diagnose_R543_four_clusters_literal_integer_unions_r611.py').read_text(encoding='utf-8')
s=s.replace('R543-four-native-overlap-clusters-literal-integer-union-diagnostic-r611','R543-overlap-only-new-intersection-native-splice-diagnostic-r615')
s=s.replace('from shapely.ops import unary_union','from shapely.ops import unary_union\nfrom shapely.geometry import Polygon,MultiPolygon,GeometryCollection')
old="   after=set_precision(literal,1e-6,mode='valid_output');actual=zero(after)"
new="""   parts=list(literal.geoms)if literal.geom_type=='MultiPolygon'else[literal]
   tokens={tuple(p)for a in before for part in(list(a.geoms)if a.geom_type=='MultiPolygon'else[a])for ring in[part.exterior]+list(part.interiors)for p in ring.coords}
   generated=[];rings=[]
   def native_vertex(p):
    xy=tuple(p)
    if xy in tokens:return xy
    changed=(round(xy[0]*1e6)/1e6,round(xy[1]*1e6)/1e6);generated.append({'literal_intersection_mm':xy,'proposed_new_integer_mm':changed});return changed
   for part in parts:
    exterior=[native_vertex(p)for p in part.exterior.coords];holes=[[native_vertex(p)for p in ring.coords]for ring in part.interiors];rings.append(Polygon(exterior,holes))
   after=rings[0]if len(rings)==1 else MultiPolygon(rings)if rings else GeometryCollection();assert after.is_valid
   actual=zero(after)
   put(OUT/(f'cluster-{i}-{role}-only-new-intersection-integer-replacement-ledger.json'),generated)"""
assert old in s;s=s.replace(old,new)
s=s.replace("'proposed_integer_grid_mm':get_precision(after)","'proposed_integer_grid_mm':get_precision(after),'all_constituent_vertex_tokens_preserved_outside_new_intersections':True,'new_intersection_vertex_count':len(generated)")
s=s.replace("print('R611'","print('R615'")
exec(compile(s,str(Path(__file__)),'exec'))
