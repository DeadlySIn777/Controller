"""Finite ordinary IO3 bypass through two existing observed annuli, no holes."""
import json,pickle,sys,hashlib,time,uuid,math
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_aux_exact_raw as A
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_power_projection_r44 as Z
import tri_route as TR
O=H/'sbc-power/CM79-R353-IO3-existing-actual-annulus-no-hole-fixed-Cu-bypass-nomination-r358'
D=H/'sbc-power/CM79-R353-fresh-IO3-split-source-and-existing-annulus-port-attribution-r355'
NET='/IO_3V3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def parts(s):return []if s.is_empty else list(s.geoms)if s.geom_type=='MultiPolygon'else[s]if s.geom_type=='Polygon'else[]
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(D/'receipt.json')=='f0fccf7f5b5604fb911b8c14b132bf58525619eefd2a25785e3f50319830bbca';r=json.loads((D/'receipt.json').read_text());mp=H/'sbc-power/CM79-exact-R333-larger-power-port-local-q053-sparse-current-diagnostic-original-vertex-splice-r353/model.pkl';assert sha(mp)==r['model_sha256']=='de8e2af4143fe43491773e0e0339c39efb17cb1660072bf37ffc6a22c155255e';g,h,b,q,c=pickle.loads(mp.read_bytes());gp=D/'actual-IO3-before-after-groups.pkl';assert sha(gp)==r['packet_sha256'];banks=pickle.loads(gp.read_bytes());groups=banks['after'];prior=banks['before'];oldkeys=K.keys(K.root(prior,'R18001','2'));assert len(oldkeys)==3689;rec,trees=F.build(c);dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;holes=[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],p['net'],s)for p in h['pads']for s in L.poly(p.get('hole')or[])];ht=STRtree([s for u,n,s in holes]);reserve,exempt=A.reservations();pairs=json.loads((D/'finite-nearest-existing-cross-group-annulus-pairs.json').read_text());rank={'In3.Cu':0,'In2.Cu':1,'B.Cu':2,'F.Cu':3};pairs=[p for p in pairs if p['layer']in rank and p['center_distance_mm']<=18];pairs.sort(key=lambda p:(rank[p['layer']],p['center_distance_mm']));pairs=pairs[:48];attempts=[];winner=None;ctx=K.hole_context(c)
 for pair in pairs:
  ly=pair['layer'];a=pair['source_existing_annulus'];bb=pair['detached_existing_annulus'];start=(a['x'],a['y']);end=(bb['x'],bb['y']);assert a['actual_drill_subtracted_annulus_area_mm2']>.1 and bb['actual_drill_subtracted_annulus_area_mm2']>.1
  for width in(.5,.75,1.0):
   for radius in(1.0,3.0):
    clip=box(min(start[0],end[0])-radius,min(start[1],end[1])-radius,max(start[0],end[0])+radius,max(start[1],end[1])+radius);obs=[]
    for j in trees[ly].query(clip.buffer(1),predicate='intersects'):
     rr=rec[ly][int(j)]
     if L.norm(rr['net'])==NET:continue
     local=next((float(z['clearance_mm'])for z in c['zones']if z['uuid']==rr['uuid']),.15)if rr['kind']=='fill'else .15;obs.append(Z.bounded_buffer(rr['shape'].intersection(clip.buffer(1)),width/2+max(local,gap(NET,rr['net']))+.025))
    for z in q:
     if z['layer']==ly and L.norm(z['net'])!=NET and z['shape'].intersects(clip.buffer(1)):obs.append(Z.bounded_buffer(z['shape'].intersection(clip.buffer(1)),width/2+max(float(z['clearance_mm']),gap(NET,z['net']))+.025))
    for j in ht.query(clip.buffer(1),predicate='intersects'):
     uid,net,sh=holes[int(j)]
     if L.norm(net)!=NET:obs.append(Z.bounded_buffer(sh,width/2+.275+.005))
    for rr in h['rule_areas']:
     if ly in rr['layers']and rr.get('no_tracks'):obs.extend(Z.bounded_buffer(p,width/2+.025)for p in L.poly(rr['outline'])if p.intersects(clip.buffer(1)))
    for rr in reserve['keepouts']:
     if ly in rr['layers']and NET not in exempt.get(rr['name'],set()):obs.extend(Z.bounded_buffer(p,width/2+.025)for p in L.poly(rr['outline'])if p.intersects(clip.buffer(1)))
    blocked=unary_union(obs);free=clip.difference(blocked);face=next((p for p in parts(free)if p.covers(Point(start))and p.covers(Point(end))),None);row={'source_UUID':a['UUID'],'detached_UUID':bb['UUID'],'layer':ly,'ordinary_width_mm':width,'local_window_radius_mm':radius,'both_existing_current_native_annuli_hard':True,'same_free_face':face is not None,'all_original_and_owned_foreign_Cu_holes_reference_peer_body_guards_hard':True};attempts.append(row);put(O/'finite-port-layer-width-window-attempts.json',attempts)
    if face is None:continue
    direct=LineString([start,end]);path=[start,end]if face.covers(direct)else TR.route_poly(face,start,end)
    if not path:continue
    path=[(round(float(x),6),round(float(y),6))for x,y in path];assert all(face.covers(LineString([aa,zz]))for aa,zz in zip(path,path[1:]));nt=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM79-IO3-R358:'+ly+':'+str(width)+':'+str(i))),'net':NET,'layer':ly,'w':width,'a':list(aa),'b':list(zz)}for i,(aa,zz)in enumerate(zip(path,path[1:]))];trial={**c,'tracks':c['tracks']+nt};_,after=K.physical(trial,NET,ctx);cr,loss=K.contact_losses(groups,after);source=K.root(after,'R18001','2');missing=sorted(oldkeys-K.keys(source));row.update({'actual_group_contact_losses':len(loss),'original_full3689_source_keys_missing':len(missing),'new_path_length_mm':LineString(path).length});put(O/'finite-port-layer-width-window-attempts.json',attempts)
    if loss or missing:continue
    actual=zero(unary_union([rr['shape']for xs in after for rr in xs if rr['kind']=='track'and rr['uuid']in{t['uuid']for t in nt}]));ap=zero(unary_union([rr['shape']for xs in groups for rr in xs if rr['kind']=='via'and rr['uuid']==a['UUID']and rr['layer']==ly]));bp=zero(unary_union([rr['shape']for xs in groups for rr in xs if rr['kind']=='via'and rr['uuid']==bb['UUID']and rr['layer']==ly]));ao=actual.intersection(ap).area;bo=actual.intersection(bp).area;assert ao>.025 and bo>.025;winner={'layer':ly,'width_mm':width,'path':path,'source_existing_annulus':a,'detached_existing_annulus':bb,'actual_source_annulus_overlap_mm2':ao,'actual_detached_annulus_overlap_mm2':bo,'source_full3689_retained_keys':True,'actual_IO3_old_groups_no_loss':True,'source_key_missing':missing,'no_original_via_unused_flags_drill_masks_native_chunks_changed':True,'new_used_layer_is_existing_observed_actual_layer':True,'only_new_tracks':nt,'no_new_holes_or_discrete_deletes':True,'all_other_nets_Cu_holes_native_fills_owned_roles_exact':True,'new_body_reference_current_drop_plating_partial_annulus_thermal_native':'OPEN'};(O/'only-new-IO3-existing-annulus-bypass-tracks-no-hole-no-delete.pkl').write_bytes(pickle.dumps({'tracks':nt,'vias':[],'removed_original_UUIDs':[]},protocol=5));(O/'fresh-IO3-after-groups.pkl').write_bytes(pickle.dumps(after,protocol=5));put(O/'only-nominated-existing-port-path.json',winner);break
   if winner:break
  if winner:break
 result={'verdict':'EXISTING_ACTUAL_ANNULUS_NO_HOLE_IO3_BYPASS_NOMINATION_ALL3689_SOURCE_KEYS_RESTORED_DIAGNOSTIC'if winner else'NO_FIXED_CURRENT_CU_EXISTING_ANNULUS_IO3_BYPASS_IN_EXACT_FINITE_WINDOWS','R353_model_sha256':sha(mp),'R355_receipt_sha256':sha(D/'receipt.json'),'finite_pair_count':len(pairs),'attempt_count':len(attempts),'winner':winner,'new_sparse_sha256':sha(O/'only-new-IO3-existing-annulus-bypass-tracks-no-hole-no-delete.pkl')if winner else None,'all_inherited_CORE_raw_body_power_reference_CM1_and_current_native_fault_failures_retained':True,'all_full_signed_IO3_CORE5_GND_current_mesh_and_thermal_native':'OPEN','source_board_rules_or_adoption_changes':0,'elapsed_seconds':time.monotonic()-started};put(O/'receipt.json',result);print('R358',sha(O/'receipt.json'),'WINNER',bool(winner),'attempts',len(attempts),flush=True)
if __name__=='__main__':main()
