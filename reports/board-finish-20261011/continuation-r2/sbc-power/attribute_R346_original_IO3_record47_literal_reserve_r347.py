"""Read-only attribution of the rejected native-fill reserve; no head."""
import json,pickle,sys,hashlib,time
from pathlib import Path
from shapely import from_wkb,set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import guarded_power_projection_r44 as Z
O=H/'sbc-power/CM79-R346-original-IO3-record47-exact-raw-gain-controlling-edge-attribution-r347'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def save(n,s):p=O/(n+'.wkb');p.write_bytes(s.wkb);return {'file':str(p.resolve()),'sha256':sha(p),'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds':list(s.bounds)if not s.is_empty else None}
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();base=H/'sbc-power/CM79-exact-R333-larger-power-port-local-q053-sparse-current-diagnostic-original-vertex-splice-r346';mp=H/'sbc-power/CM-sparse-exact-current-R543-TMR-repaired-only-new-role-withdrawal-inherited-fills-FAIL-r333/model.pkl';assert sha(mp)=='f9df66060a0f45959c4234f698500070c1ba2b4837894eee644cec36891dce9b';g,h,b,q,c=pickle.loads(mp.read_bytes());uid='54921f4b-0308-4821-9549-ff9360bf05ca';z=next(z for z in c['zones']if z['uuid']==uid);parent=zero(L.poly(z['fills']['In2.Cu'])[47]);d=pickle.loads((base/'only-CM79-fullwidth-tracks-one-larger-power-via-one-exact-old-delete.pkl').read_bytes());cuts=[];local=float(z['clearance_mm']);dom=h['domains_normalized']
 for x in d['tracks']+d['vias']:
  same=L.norm(x['net'])==L.norm(z['net']);gap=.15 if dom.get(L.norm(x['net']))==dom.get(L.norm(z['net']))else .6
  if 'd'in x:cut=Z.bounded_disk(x,x['drill']/2+.00000002 if same else max(x['drill']/2+.275,x['d']/2+max(local,gap)+.025))
  elif same or x['layer']!='In2.Cu':continue
  else:cut=Z.bounded_buffer(LineString([x['a'],x['b']]),x['w']/2+max(local,gap)+.025)
  if cut.intersects(parent):cuts.append(zero(cut))
 cutter=zero(unary_union(cuts));key=uid+'-In2.Cu-new-CM-local-negative-47';gain=zero(from_wkb((base/(key+'-0-raw-positive-gain.wkb')).read_bytes()));reserve=zero(from_wkb((base/(key+'-0-local-100nm-negative-reserve.wkb')).read_bytes()));final=zero(from_wkb((base/(key+'-actual-final-record.wkb')).read_bytes()));extra=zero(from_wkb((base/(key+'-explicit-extra-negative-delta.wkb')).read_bytes()));edges=[LineString([a,b])for ring in[parent.exterior,*parent.interiors]for a,b in zip(list(ring.coords),list(ring.coords)[1:])];tree=STRtree(edges);gp=list(gain.geoms)if hasattr(gain,'geoms')else[gain];rows=[]
 for p in gp:
  coords=list(p.exterior.coords)if p.geom_type=='Polygon'else list(p.coords)
  for v in coords:
   pt=Point(v);e=edges[int(tree.nearest(pt))];rows.append({'raw_positive_coordinate':list(v),'nearest_original_edge':list(e.coords),'old_edge_length_mm':e.length,'float_distance_mm':pt.distance(e),'original_edge_WKB_sha256':hashlib.sha256(e.wkb).hexdigest(),'native_new_cut_distance_mm':pt.distance(cutter)})
 result={'verdict':'READ_ONLY_REJECTED_RECORD47_RESERVE_ATTRIBUTION_NO_HEAD','R346_failure_sha256':sha(base/'failure.json'),'R333_model_sha256':sha(mp),'zone_UUID':uid,'record':47,'layer':'In2.Cu','actual_native_local_clearance_mm':local,'parent_record':save('exact-original-current-record47',parent),'normal_new_primitive_cut':save('normal-new-primitives-only-cutter',cutter),'literal_raw_gain':save('literal-raw-positive-component',gain),'exact100nm_reserve':save('actual-bound100nm-negative-reserve',reserve),'reserve_outside_normal_plus200nm':save('reserve-outside-normal-plus200nm',reserve.difference(zero(Z.bounded_buffer(cutter,.0002)))),'extra_negative_outside_new_cut':save('actual-additional-negative-outside-new-cut',extra),'after_literal_gain':save('IM-final-literal-gain',final.difference(parent)),'raw_gain_coordinate_old_edge_attribution':rows,'all_contacts_source_references_CURRENT_native':'OPEN','no_area_or_line_waiver':True,'source_model_board_native_changes':0,'elapsed_seconds':time.monotonic()-started}
 put(O/'receipt.json',result);print('R347_COMPLETE',sha(O/'receipt.json'),json.dumps({k:v for k,v in result.items()if k not in('raw_gain_coordinate_old_edge_attribution',)}),flush=True)
if __name__=='__main__':main()
