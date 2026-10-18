"""Proposal only: original IO3 record tokens exact, only new intersections move."""
import json,hashlib,time,math
from pathlib import Path
from shapely import from_wkb,set_precision
from shapely.geometry import Point,LineString,Polygon,MultiPolygon,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
D=H/'sbc-power/CM79-R346-original-IO3-record47-exact-raw-gain-controlling-edge-attribution-r347'
O=H/'sbc-power/CM79-original-IO3-record47-only-new-intersection-native-inward-splice-proposal-r348'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def save(n,s):p=O/(n+'.wkb');p.write_bytes(s.wkb);return {'file':str(p.resolve()),'sha256':sha(p),'type':s.geom_type,'empty':s.is_empty,'area_mm2':s.area,'length_mm':s.length,'bounds':list(s.bounds)if not s.is_empty else None}
def polys(s):return list(s.geoms)if s.geom_type=='MultiPolygon'else[s]
def rings(s):return[list(r.coords)for p in polys(s)for r in[p.exterior,*p.interiors]]
def vertices(s):return{tuple(x)for r in rings(s)for x in r[:-1]}
def edges(s):return{tuple(sorted((tuple(a),tuple(z))))for r in rings(s)for a,z in zip(r,r[1:])}
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(D/'receipt.json')=='dac555ad0ffb7b47b5ef7095ea75c29d1c5bf001ac34f8fd130491ceb5743f72';before=zero(from_wkb((D/'exact-original-current-record47.wkb').read_bytes()));cut=zero(from_wkb((D/'normal-new-primitives-only-cutter.wkb').read_bytes()));raw=before.difference(cut);save('literal-before-serialization-after',raw);oldv=vertices(before);oldedges=[LineString(e)for e in edges(before)];tree=STRtree(oldedges);newv=vertices(raw)-oldv-vertices(cut);moves={};rows=[]
 for v in sorted(newv):
  e=oldedges[int(tree.nearest(Point(v)))];assert e.distance(Point(v))<.00000001;choices=[]
  for rad in(.0001,.0002,.0005):
   for i in range(256):
    angle=2*math.pi*i/256;pt=(round((v[0]+rad*math.cos(angle))*1e6)/1e6,round((v[1]+rad*math.sin(angle))*1e6)/1e6);s=Point(pt)
    if raw.covers(s)and before.covers(s)and s.distance(raw.boundary)>=.000000001:choices.append((s.distance(Point(v)),pt))
   if choices:break
  assert choices,('no legal inward intersection',v);m=min(choices)[1];moves[v]=m
  incident=[]
  for r in rings(raw):
   for k,x in enumerate(r[:-1]):
    if tuple(x)!=v:continue
    aa=tuple(r[k-1]if k else r[-2]);bb=tuple(r[k+1]);incident=[Polygon([v,m,aa,v]),Polygon([v,m,bb,v])]
  assert len(incident)==2
  rows.append({'new_raw_cut_intersection':v,'new_native_inward_intersection':m,'displacement_mm':Point(v).distance(Point(m)),'exact_original_controlling_edge':save('intersection-'+str(len(rows))+'-before-controlling-edge',e),'exact_two_incident_wedges':[save('intersection-'+str(len(rows))+'-wedge-'+str(j),p)for j,p in enumerate(incident)],'old_coordinate_tokens_changed':0})
 def rc(r):return[moves.get(tuple(x),tuple(x))for x in r.coords]
 ps=[Polygon(rc(p.exterior),[rc(r)for r in p.interiors])for p in polys(raw)];after=MultiPolygon(ps)if len(ps)>1 else ps[0];assert after.is_valid;actual=unary_union([Polygon(p.exterior.coords,[r.coords for r in p.interiors])for p in polys(after)]);gain=zero(actual).difference(before);removed=before.difference(zero(actual));extra=removed.difference(cut);local=box(116,169,139,212);remotev={v for v in oldv if Point(v).disjoint(local)};remotee={e for e in edges(before)if LineString(e).disjoint(local)}
 put(O/'receipt.json',{'verdict':'ORIGINAL_RECORD_ONLY_NEW_INTERSECTION_INWARD_SPLICE_PROPOSAL_NO_MODEL','R347_receipt_sha256':sha(D/'receipt.json'),'before_WKB_sha256':hashlib.sha256(before.wkb).hexdigest(),'rows':rows,'new_intersections':len(moves),'after':save('only-proposed-current-record47-after',actual),'literal_no_gain':save('literal-after-gain',gain),'actual_removed':save('actual-removed',removed),'additional_negative_beyond_normalcut':save('actual-named-negative-wedges',extra),'outside_original_declared_corridor':save('extra-negative-outside-original-corridor',extra.difference(box(116,169,139,208))),'all_untouched_original_vertex_tokens_exact':remotev<=vertices(actual),'all_complete_disjoint_original_edges_exact':remotee<=edges(actual),'all_contacts_source_reference_native_CURRENT':'OPEN','accepted':False,'model_changes':0,'elapsed_seconds':time.monotonic()-started});print('R348_PROPOSAL',sha(O/'receipt.json'),'new-intersections',len(moves),'gainEMPTY',gain.is_empty,'extra',extra.area,flush=True)
if __name__=='__main__':main()
