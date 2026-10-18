"""Read-only true full-cap/native-hole constraints of original/local power axes."""
import hashlib,json,pickle,sys,time,traceback
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_aux_exact_raw as A
O=H/'sbc-power/CM79-fullwidth-exact-native-and-owned-axis-obstacles-r304'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();mp=H/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/model.pkl';assert sha(mp)=='a5340075975ddad925b57663d475978eba7f346c3709e93fa6b67064cbf4ccec';g,h,b,q,c=pickle.loads(mp.read_bytes());src=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(src)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';iv=A.C.inventory(src.read_bytes());net='/mc_local_power/CORE_5V';uid='dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1';old=next(t for t in h['tracks']if t['uuid']==uid);rec,trees=F.build({**c,'zones':[]},layers={'F.Cu'});domain=h['domains_normalized'];gap=lambda n:.15 if domain.get(L.norm(n))==domain.get(net)else .6;holes=[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],p['net'],sh)for p in h['pads']for sh in L.poly(p.get('hole')or[])];ht=STRtree([x[2]for x in holes]);result=[]
 for label,axis in [('exact-original-before-full-axis',LineString([old['a'],old['b']]))]+[('local-balanced-'+str(y),LineString([(116,y),(120,y)]))for y in(202.705,202.715,202.725)]:
  rows=[]
  for j in trees['F.Cu'].query(axis.buffer(1.5),predicate='intersects'):
   rr=rec['F.Cu'][int(j)]
   if L.norm(rr['net'])==net:continue
   if rr['kind']=='track'and not rr['source'].get('m'):t=rr['source'];d=axis.distance(LineString([t['a'],t['b']]))-.625-t['w']/2
   elif rr['kind']=='via':v=rr['source'];d=axis.distance(Point(v['x'],v['y']))-.625-v['d']/2
   else:d=axis.distance(rr['shape'])-.625
   req=gap(rr['net']);plan=req+.025
   if d<plan:rows.append({'kind':rr['kind'],'UUID':rr['uuid'],'raw_net':rr['net'],'normalized_net':L.norm(rr['net']),'ref':rr.get('ref'),'pin':rr.get('pin'),'layer':'F.Cu','native_original_UUID':rr['uuid']in iv[3],'native_pad_UUID':rr['kind']=='pad','actual_native_item':rr['uuid']in iv[3]or rr['kind']=='pad','actual_full_cap_gap_mm':d,'native_required_mm':req,'extra_planner_required_mm':plan,'native_PASS':d>=req,'planner_PASS':d>=plan,'shape_bounds_mm':rr['shape'].bounds,'exact_source_track':rr.get('source')})
  for j in ht.query(axis.buffer(1.2),predicate='intersects'):
   u,n,sh=holes[int(j)]
   if L.norm(n)==net:continue
   d=axis.distance(sh)-.625-.005
   if d<.275:rows.append({'kind':'every_foreign_drill','UUID':u,'raw_net':n,'actual_guarded_drill_edge_gap_mm':d,'required_mm':.275,'native_or_ordinary_hole_rule_PASS':False,'hole_bounds_mm':sh.bounds})
  result.append({'axis':label,'exact_centreline_coords_mm':list(axis.coords),'fullwidth_mm':1.25,'all_native_and_owned_copper_planner_deficits_and_every_foreign_drill_failures':rows});put(O/'exact-axis-obstacle-rows.json',result)
 put(O/'receipt.json',{'verdict':'READ_ONLY_EXACT_NATIVE_AND_OWNED_POWER_AXIS_OBSTACLE_DIAGNOSIS','R289_failed_diagnostic_model_sha256':sha(mp),'source_native_sha256':sha(src),'rows':result,'board_model_source_rules_or_annuli_changed':False,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R304_COMPLETE',sha(O/'receipt.json'),[(r['axis'],len(r['all_native_and_owned_copper_planner_deficits_and_every_foreign_drill_failures']))for r in result],flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
