"""Read-only exact local port/free-face authority after frozen IO3 searches."""
import hashlib,json,pickle,sys,time,traceback
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import guarded_power_projection_r44 as Z
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import physical_reference_losses_r3_zero_r208 as RF
import audit_aux_exact_raw as A
O=H/'sbc-power/FIELD5-R393-IO3-no-hole-exact-local-port-obstacles-r297';NET='/IO_3V3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def buf(s,r):x=Z.bounded_buffer(s,r);y=set_precision(x,0);assert y.wkb==x.wkb;return y
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();mp=H/'field-power/FIELD5-R385-minimal-R155-strict-filled-restoration-composition-r393/model.pkl';assert sha(mp)=='df3e75059ea013087ddd8481e1f5bfe79e7915c2c3b4f34e2eaf1de9864acc13';g,h,b,q,c=pickle.loads(mp.read_bytes());bp=H/'field-power/FIELD5-R393-exact-IO3-split-diagnosis-r403';assert sha(bp/'actual-IO3-groups.pkl')=='e50b60d6c2f7c52a3c91b483bb0edc899e5b92759f923673af8d15136da61208';groups=pickle.loads((bp/'actual-IO3-groups.pkl').read_bytes());root=K.root(groups,'R18001','2');target=next(xs for xs in groups if len(K.keys(xs))==383);native=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(native)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';nativeids=set(A.C.inventory(native.read_bytes())[3]);byq={z['uuid']:z for z in q};rec,trees=F.build(c,layers={'In2.Cu','In3.Cu','F.Cu','B.Cu'});dom=h['domains_normalized'];gap=lambda n:.15 if dom.get(L.norm(n))==dom.get(NET)else .6;reserve,exempt=A.reservations();outline=unary_union(L.poly(h['outline'])).buffer(-.525);clip=box(279.08,146.08,329.08,196.08);holes=[(v['uuid'],L.norm(v['net']),Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],L.norm(p['net']),s)for p in h['pads']for s in L.poly(p.get('hole')or[])];ht=STRtree([x[2]for x in holes]);result=[]
 for layer in ('In2.Cu','In3.Cu','F.Cu','B.Cu'):
  aa=unary_union([r['shape']for r in target if r['layer']==layer]).intersection(clip);bb=unary_union([r['shape']for r in root if r['layer']==layer]).intersection(clip);cuts=[];rows=[]
  if aa.is_empty or bb.is_empty:result.append({'layer':layer,'target_local_Cu_empty':aa.is_empty,'source_local_Cu_empty':bb.is_empty});continue
  near=nearest_points(aa,bb)
  for j in trees[layer].query(clip.buffer(2),predicate='intersects'):
   rr=rec[layer][int(j)]
   if L.norm(rr['net'])==NET:continue
   local=rr['shape'].intersection(clip)
   if local.is_empty:continue
   normal_native_retreat=rr['kind']=='fill'and rr['uuid']in nativeids
   req=gap(rr['net'])+.025+.000003
   if rr['kind']=='fill':zz=next(z for z in c['zones']if z['uuid']==rr['uuid']);req=max(float(zz['clearance_mm']),gap(rr['net']))+.025+.000003
   if rr['kind']=='track'and not rr['source'].get('m'):t=rr['source'];cut=buf(LineString([t['a'],t['b']]),t['w']/2+.1+req)
   elif rr['kind']=='via':v=rr['source'];cut=buf(Point(v['x'],v['y']),v['d']/2+.1+req)
   else:cut=buf(rr['shape'],.1+req)
   rows.append({'kind':rr['kind'],'UUID':rr['uuid'],'raw_net':rr['net'],'normalized_net':L.norm(rr['net']),'native_original_UUID':rr['uuid']in nativeids,'generated_owned_peer_UUID':rr['uuid']in byq,'normal_native_fill_may_retreat':normal_native_retreat,'local_actual_Cu_area_mm2':local.area,'hard_cutter_local_area_mm2':cut.intersection(clip).area,'covers_nearest_target_point':cut.covers(near[0]),'covers_nearest_root_point':cut.covers(near[1])})
   if not normal_native_retreat:cuts.append(cut)
  for j in ht.query(clip.buffer(2),predicate='intersects'):
   u,n,sh=holes[int(j)]
   if n!=NET:cuts.append(buf(sh,.380003))
  for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):
   for rule in rules:
    if ex and NET in exempt.get(rule['name'],set()):continue
    if layer not in rule['layers']or(not ex and not rule.get('no_tracks')):continue
    for sh in L.poly(rule['outline']):
     if sh.intersects(clip):cut=buf(sh,.125003);cuts.append(cut);rows.append({'kind':'frozen_reservation'if ex else'native_no_tracks','UUID':rule.get('uuid'),'name':rule.get('name'),'raw_net':NET,'hard_cutter_local_area_mm2':cut.intersection(clip).area,'covers_nearest_target_point':cut.covers(near[0]),'covers_nearest_root_point':cut.covers(near[1])})
  free=clip.intersection(outline.buffer(-.100003)).difference(unary_union(cuts));sources=free.intersection(bb);targets=free.intersection(aa);faces=[{'area_mm2':p.area,'source_port_intersection_mm2':p.intersection(bb).area,'target_port_intersection_mm2':p.intersection(aa).area,'source_port_nonempty':not p.intersection(bb).is_empty,'target_port_nonempty':not p.intersection(aa).is_empty}for p in RF.parts(free)];(O/(layer+'-actual-free.wkb')).write_bytes(free.wkb);(O/(layer+'-source-local.wkb')).write_bytes(bb.wkb);(O/(layer+'-target-local.wkb')).write_bytes(aa.wkb);put(O/(layer+'-exact-obstacles.json'),rows);result.append({'layer':layer,'source_local_Cu_mm2':bb.area,'target_local_Cu_mm2':aa.area,'nearest_target_coord_mm':list(near[0].coords[0]),'nearest_source_coord_mm':list(near[1].coords[0]),'nearest_actual_gap_mm':near[0].distance(near[1]),'raw_free_mm2':free.area,'source_free_port_mm2':sources.area,'target_free_port_mm2':targets.area,'source_free_port_empty':sources.is_empty,'target_free_port_empty':targets.is_empty,'exact_free_faces':faces,'normal_native_fill_retreat_count':sum(bool(x.get('normal_native_fill_may_retreat'))for x in rows),'hard_owned_peer_count':sum(bool(x.get('generated_owned_peer_UUID'))for x in rows),'native_discrete_actual_limits_extra_planner_and_rule_areas_unchanged':True})
  put(O/'four-layer-exact-local-source-constraint-facts.json',result);print('R297_LAYER',layer,free.area,sources.area,targets.area,flush=True)
 put(O/'receipt.json',{'verdict':'READ_ONLY_LOCAL_IO3_PORT_AND_HARD_OBSTACLE_AUTHORITY_NO_GEOMETRY_CHANGE','R393_failed_diagnostic_model_sha256':sha(mp),'R403_actual_IO3_groups_sha256':sha(bp/'actual-IO3-groups.pkl'),'source_native_sha256':sha(native),'layers':result,'board_model_source_native_or_roles_written':False,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R297_COMPLETE',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
