"""Source-bound no-hole IO3 bridge nomination on the failed R393 diagnostic.

No parent model is emitted. A candidate must retain literal current foreign Cu,
all existing holes, native/frozen rules, and strict actual fill-only reference.
"""
import hashlib,json,pickle,sys,uuid,time,traceback,math
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import guarded_power_projection_r44 as Z
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import physical_reference_losses_r3_zero_r208 as RF
import audit_aux_exact_raw as A
import tri_route as TR
O=H/'sbc-power/FIELD5-R393-IO3-no-hole-actual-source-strict-reference-bridge-r293'
NET='/IO_3V3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def buf(s,r):x=Z.bounded_buffer(s,r);y=set_precision(x,0);assert y.wkb==x.wkb;return y
def main():
 started=time.monotonic();assert not O.exists();O.mkdir()
 mp=H/'field-power/FIELD5-R385-minimal-R155-strict-filled-restoration-composition-r393/model.pkl';assert sha(mp)=='df3e75059ea013087ddd8481e1f5bfe79e7915c2c3b4f34e2eaf1de9864acc13';g,h,b,q,c=pickle.loads(mp.read_bytes())
 bp=H/'field-power/FIELD5-R393-exact-IO3-split-diagnosis-r403';assert sha(bp/'receipt.json')=='26d8d23143d9f84d11340fab5b8afc572741639c9abe321fbc1a7e671d06333f';assert sha(bp/'actual-IO3-groups.pkl')=='e50b60d6c2f7c52a3c91b483bb0edc899e5b92759f923673af8d15136da61208';groups=pickle.loads((bp/'actual-IO3-groups.pkl').read_bytes());root=K.root(groups,'R18001','2');target=next(xs for xs in groups if len(K.keys(xs)&{tuple(k)for r in json.loads((bp/'exact-detached-key-membership.json').read_text())if not r['source_rooted']for k in r['all_retained_keys']})==383)
 fp=H/'field-power/FIELD5-R393-current-independent-all-contact-source-reference-audit-r395';r=json.loads((fp/'receipt.json').read_text());assert r['current_model_SHA256']==sha(mp);allgroups=pickle.loads((fp/'actual-drilled-current-groups.pkl').read_bytes());lg=K.root(allgroups['/LOGIC_GND'],'J11001','2');refs=K.source_refs(lg);del allgroups
 cm=H/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/only-new-CM-ordinary-discrete-no-deletes.pkl';assert sha(cm)=='72321f8b75794e2cf2bd5d4ba6788da7bbdb8eaa4ba692cf9a121d4c3bde3207';cd=pickle.loads(cm.read_bytes());hard={**c,'tracks':c['tracks']+cd['tracks'],'vias':c['vias']+cd['vias']}
 rec,trees=F.build(hard);dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6
 holes=[(v['uuid'],L.norm(v['net']),Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in hard['vias']]+[(p['uuid'],L.norm(p['net']),s)for p in h['pads']for s in L.poly(p.get('hole')or[])];ht=STRtree([x[2]for x in holes]);outline=unary_union(L.poly(h['outline'])).buffer(-.525);reserve,exempt=A.reservations()
 def free(layer,width,clip):
  rad=width/2;cuts=[]
  for j in trees[layer].query(clip.buffer(2),predicate='intersects'):
   rr=rec[layer][int(j)]
   if L.norm(rr['net'])==NET:continue
   req=gap(NET,rr['net'])+.025+.000003
   if rr['kind']=='fill':
    z=next(z for z in hard['zones']if z['uuid']==rr['uuid']);req=max(float(z['clearance_mm']),gap(NET,rr['net']))+.025+.000003
   if rr['kind']=='track'and not rr['source'].get('m'):t=rr['source'];cut=buf(LineString([t['a'],t['b']]),t['w']/2+rad+req)
   elif rr['kind']=='via':v=rr['source'];cut=buf(Point(v['x'],v['y']),v['d']/2+rad+req)
   else:cut=buf(rr['shape'],rad+req)
   cuts.append(cut)
  for j in ht.query(clip.buffer(2),predicate='intersects'):
   u,n,s=holes[int(j)]
   if n!=NET:cuts.append(buf(s,rad+.275+.005003))
  for rules,ex in ((h['rule_areas'],False),(reserve['keepouts'],True)):
   for rule in rules:
    if ex and NET in exempt.get(rule['name'],set()):continue
    if layer in rule['layers']and(ex or rule.get('no_tracks')):cuts.extend(buf(s,rad+.025003)for s in L.poly(rule['outline'])if s.intersects(clip))
  return clip.intersection(outline.buffer(-rad-.000003)).difference(unary_union(cuts))
 attempts=[];winner=None
 for radius in (6.,12.,25.):
  clip=box(304.08-radius,171.08-radius,304.08+radius,171.08+radius)
  for width in (.5,.3,.2):
   for layer in ('In2.Cu','In3.Cu','F.Cu','B.Cu'):
    a=unary_union([r['shape']for r in target if r['layer']==layer]);bb=unary_union([r['shape']for r in root if r['layer']==layer]);row={'radius_mm':radius,'width_mm':width,'layer':layer,'target_real_Cu_present':not a.is_empty,'root_real_Cu_present':not bb.is_empty};attempts.append(row)
    if a.is_empty or bb.is_empty:continue
    rawfree=free(layer,width,clip);f=rawfree.intersection(refs[layer].buffer(-width/2-.000004,quad_segs=128));faces=[]
    row['actual_foreign_Cu_holes_rules_only_faces']=sum(not(ff.intersection(a).is_empty or ff.intersection(bb).is_empty)for ff in RF.parts(rawfree))
    for ff in RF.parts(f):
     aa=ff.intersection(a);zz=ff.intersection(bb)
     if aa.is_empty or zz.is_empty:continue
     faces.append((ff,aa,zz))
    row['strict_actual_fill_reference_same_face_count']=len(faces)
    if not faces:continue
    faces.sort(key=lambda v:v[1].distance(v[2]))
    for ff,aa,zz in faces[:3]:
     s,e=nearest_points(aa,zz);path,method=TR.route(ff,list(s.coords[0]),list(e.coords[0]));path=[[round(x,6),round(y,6)]for x,y in path]
     if not ff.covers(LineString(path)):continue
     nt=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'FIELD5-IO3-R293:'+layer+':'+str(width)+':'+str(i))),'net':NET,'layer':layer,'w':width,'a':x,'b':y}for i,(x,y)in enumerate(zip(path,path[1:]))if x!=y];body=unary_union([buf(LineString([t['a'],t['b']]),width/2)for t in nt]);actual=body.difference(unary_union([holes[int(j)][2]for j in ht.query(body,predicate='intersects')]));missing=actual.difference(refs[layer]);row['fresh_drilled_actual_fullbody_ref_gap_mm2']=missing.area
     if not missing.is_empty:continue
     trial={**c,'tracks':c['tracks']+nt};_,new=K.physical(trial,NET,K.hole_context(trial));rows,loss=K.contact_losses(groups,new);nr=K.root(new,'R18001','2');allkeys=K.keys(root)|K.keys(target);lost=sorted(allkeys-K.keys(nr));row['all_old_IO3_contact_losses']=len(loss);row['expected_source_root_layer_keys_missing']=len(lost)
     if loss or lost:continue
     checks=[];errors=[]
     for t in nt:
      axis=LineString([t['a'],t['b']]);bod=buf(axis,width/2)
      for j in trees[layer].query(bod.buffer(.8),predicate='intersects'):
       rr=rec[layer][int(j)]
       if L.norm(rr['net'])==NET:continue
       req=gap(NET,rr['net'])+.025
       if rr['kind']=='fill':z=next(z for z in hard['zones']if z['uuid']==rr['uuid']);req=max(float(z['clearance_mm']),gap(NET,rr['net']))+.025
       if rr['kind']=='track'and not rr['source'].get('m'):d=axis.distance(LineString([rr['source']['a'],rr['source']['b']]))-width/2-rr['source']['w']/2
       elif rr['kind']=='via':d=axis.distance(Point(rr['source']['x'],rr['source']['y']))-width/2-rr['source']['d']/2
       else:d=axis.distance(rr['shape'])-width/2
       cr={'new_UUID':t['uuid'],'other_UUID':rr['uuid'],'kind':rr['kind'],'layer':layer,'actual_analytic_gap_mm':d,'required_mm':req};checks.append(cr)
       if d<req:errors.append(cr)
      for j in ht.query(bod.buffer(.285),predicate='intersects'):
       u,n,sh=holes[int(j)]
       if n==NET:continue
       d=axis.distance(sh)-width/2-.005;cr={'new_UUID':t['uuid'],'other_UUID':u,'kind':'all_foreign_real_drill','actual_analytic_gap_mm':d,'required_mm':.275};checks.append(cr)
       if d<.275:errors.append(cr)
     if errors:row['actual_geometry_errors']=errors;continue
     winner={'tracks':nt,'vias':[],'removed_original_UUIDs':[],'path':path,'route':method,'width_mm':width,'layer':layer,'length_mm':sum(math.dist(t['a'],t['b'])for t in nt),'old_IO3_drilled_contacts_lost':0,'383_detached_old_keys_now_R18001_2_rooted':True,'fullbody_drill_subtracted_fill_reference_gap_empty':True,'strict_REFERENCE_shadow_expansion_mm':0,'new_holes':0,'all_foreign_current_fill_Cu_preserved':True,'actual_analytic_geometry_checks':checks};break
    if winner:break
   put(O/'finite-current-reference-route-matrix.json',attempts)
   if winner:break
  if winner:break
 if winner:(O/'only-new-IO3-tracks-no-holes-no-deletes.pkl').write_bytes(pickle.dumps({k:winner[k]for k in('tracks','vias','removed_original_UUIDs')},protocol=5))
 put(O/'receipt.json',{'verdict':'NO_HOLE_EXISTING_SOURCE_IO3_BRIDGE_NOMINATION_PENDING_INDEPENDENT_FULL_CURRENT_AUDIT'if winner else'NO_NO_HOLE_STRICT_CURRENT_REFERENCE_IO3_BRIDGE_IN_DECLARED_WINDOWS','R393_failed_diagnostic_model_sha256':sha(mp),'R403_exact_split_receipt_sha256':sha(bp/'receipt.json'),'R395_failed_current_reference_receipt_sha256':sha(fp/'receipt.json'),'remote_CM49_hard_sparse_sha256':sha(cm),'winner':winner,'nomination_file_sha256':sha(O/'only-new-IO3-tracks-no-holes-no-deletes.pkl')if winner else None,'inherited_29_old_reference_and_other_CORE_current_native_failures':'FAIL_OR_OPEN_RETAINED','every_other_current_native_owned_body_fill_hole_exact':True,'new_generated_or_native_fill_role_operations':0,'board_written':False,'whole_model_emitted':False,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R293_COMPLETE',bool(winner),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
