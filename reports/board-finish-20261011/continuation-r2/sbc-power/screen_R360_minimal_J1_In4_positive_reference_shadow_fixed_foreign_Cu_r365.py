"""Read-only minimal LG support shadow; every existing foreign Cu stays hard."""
import pickle,json,hashlib,sys,time,traceback
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_aux_exact_raw as A
import guarded_power_projection_r44 as Z
O=H/'sbc-power/CM79-R360-minimal-J1-In4-positive-reference-shadow-fixed-foreign-Cu-read-only-r365'
D=H/'sbc-power/CM79-R353-plus-no-hole-IO3-existing-annulus-current-independent-byte-source-native-proof-r360'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(D/'receipt.json')=='63399c63f8222501bad737e59f39eb46a1e13d2aa1da7a2af5c4d856202c8ddf';mp=D/'model.pkl';assert sha(mp)=='69fe1c947f564c2e13a5ca7beac2f3dc1d344cdc3a55c51d7e1da53171ec3899';g,h,b,q,c=pickle.loads(mp.read_bytes());io=pickle.loads((D/'fresh-actual-IO3-after-groups.pkl').read_bytes());tracks=pickle.loads((D/'only-seven-IO3-tracks-no-hole-no-delete.pkl').read_bytes())['tracks'];ids={t['uuid']for t in tracks};body=zero(unary_union([r['shape']for xs in io for r in xs if r['kind']=='track'and r['uuid']in ids and r['layer']=='In3.Cu']));caps=zero(unary_union([Point(*p['xy']).buffer(p['named_original_terminal_own_guard_radius_mm'],quad_segs=128)for p in json.loads((H/'sbc-power/CM79-R360-IO3-actual-J1-In4-exact-two-original-terminal-fullbody-reference-r361/exact-two-original-terminal-reference-guard-authority.json').read_text())]));required=zero(body.difference(caps));shadow=zero(Z.bounded_buffer(required,.005));cache=H/'sbc-power/CM79-R353-fresh-all-current-source-native-reference-audit-r354/actual-drilled-after-groups.pkl';assert sha(cache)=='339dbe2c2173388fa7384c697e6364dcf5b9c507e552e64836b08c55203ed4eb';lg=K.root(pickle.loads(cache.read_bytes())['/LOGIC_GND'],'J11001','2');ref=zero(unary_union([r['shape']for r in lg if r['kind']=='fill'and r['layer']=='In4.Cu']));(O/'only-prospective-minimal-fullbody5um-LG-reference-shadow.wkb').write_bytes(shadow.wkb);(O/'exact-IO3-body-outside-two-original-terminal-caps.wkb').write_bytes(required.wkb);rec,trees=F.build(c,layers={'In4.Cu'});dom=h['domains_normalized'];gap=lambda n:.15 if dom.get(L.norm(n))==dom.get('/LOGIC_GND')else .6;rows=[];bad=[]
 targets=[rec['In4.Cu'][int(i)]for i in trees['In4.Cu'].query(shadow.buffer(1),predicate='intersects')]+[{'uuid':z['uuid'],'net':z['net'],'kind':'owned_physical_zone','shape':z['shape'],'local':float(z['clearance_mm'])}for z in q if z['layer']=='In4.Cu'and z['shape'].intersects(shadow.buffer(1))]
 for rr in targets:
  if L.norm(rr['net'])=='/LOGIC_GND':continue
  local=rr.get('local',next((float(z['clearance_mm'])for z in c['zones']if z['uuid']==rr['uuid']),.15));req=max(gap(rr['net']),local);distance=shadow.distance(rr['shape']);row={'other_UUID':rr['uuid'],'other_net':rr['net'],'kind':rr['kind'],'actual_gap_mm':distance,'actual_native_required_mm':req,'planner_required_mm':req+.025,'exact_foreign_shape_unchanged':True};rows.append(row)
  if distance<req+.025:bad.append(row)
 holes=[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],p['net'],s)for p in h['pads']for s in L.poly(p.get('hole')or[])];ht=STRtree([s for u,n,s in holes])
 for i in ht.query(shadow.buffer(.285),predicate='intersects'):
  uid,n,s=holes[int(i)]
  if L.norm(n)=='/LOGIC_GND':continue
  row={'other_UUID':uid,'other_net':n,'kind':'every_real_foreign_hole','actual_gap_mm':shadow.distance(s),'planner_required_mm':.28};rows.append(row)
  if row['actual_gap_mm']<.28:bad.append(row)
 reserve,exempt=A.reservations()
 for rr in [*h['rule_areas'],*reserve['keepouts']]:
  if 'In4.Cu'not in rr['layers']or not rr.get('no_copperpour',rr.get('no_copper_pour',True)):continue
  if rr.get('name')in exempt and '/LOGIC_GND'in exempt[rr['name']]:continue
  for s in L.poly(rr['outline']):
   if shadow.distance(s)<.025:bad.append({'kind':'native_or_reserved_area','UUID':rr.get('uuid'),'name':rr.get('name'),'actual_gap_mm':shadow.distance(s)})
 put(O/'every-fixed-foreign-Cu-and-hole-shadow-guard-ledger.json',rows);put(O/'all-fixed-foreign-shadow-conflicts.json',bad);parts=list(shadow.geoms)if shadow.geom_type=='MultiPolygon'else[shadow];components=[{'component':i,'area_mm2':p.area,'actual_source_overlap_mm2':p.intersection(ref).area,'actual_source_positive_overlap':p.intersection(ref).area>0}for i,p in enumerate(parts)];put(O/'actual-J1-source-overlap-every-shadow-component.json',components);result={'verdict':'READ_ONLY_MINIMAL_SOURCE_REFERENCE_SHADOW_CONFLICT_ATTRIBUTION_NO_MODEL_OR_NATIVE_EMISSION','R360_receipt_sha256':sha(D/'receipt.json'),'model_sha256':sha(mp),'required_body_area_mm2':required.area,'minimal_shadow_area_mm2':shadow.area,'source_overlap_mm2':shadow.intersection(ref).area,'all_shadow_components_positively_source_contacted':all(x['actual_source_positive_overlap']for x in components),'fixed_foreign_Cu_hole_reserved_conflict_count':len(bad),'no_foreign_cut_original_hole_via_mask_pose_or_source_change':True,'no_own_ground_annulus_signal_aperture_borrow':True,'literal_fullbody_reference_source_current_native_thermal':'FAIL_OR_OPEN_RETAINED','elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)};put(O/'receipt.json',result);print('R365',sha(O/'receipt.json'),json.dumps(result),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
