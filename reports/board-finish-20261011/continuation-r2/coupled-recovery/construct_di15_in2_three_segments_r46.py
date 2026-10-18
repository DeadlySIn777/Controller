"""Ordinary F/In2/F, preserving strict single dive/return and all current Cu.

Adjacent source-rooted In1 is the sole reference used for this ordinary net.
No proposed R18 ground shape receives reference credit or SI qualification.
"""
import sys,json,pickle,math,time,itertools
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import construct_di6_direct_source_escape_r5 as K
import tri_route as T
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
C=A.C;NET='/motherboard_di/DI15_LOGIC';GND='/LOGIC_GND';RAW='/motherboard_di{slash}DI15_LOGIC'
def main():
 started=time.monotonic();out=HERE/'di15-In2-three-segment-nomination-r46.json';assert not out.exists();A.read(__file__);rp=HERE/'di15-hybrid-transport-nomination-r44.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='1f957becfd819b46b14075aff7aa62e676302cb27db62cfa2b2c2004d4101d09';assert r['policy'] is None and r['raw_net']==RAW
 lr=A.read(r['saved_local_geometry']);assert C.sha(lr)==r['saved_local_geometry_sha256'];loc=pickle.loads(lr);free=loc['free'];via=loc['via'];refs=loc['refs'];src=loc['sourcepad'];dst=loc['targetpad'];oldret=loc['existing_returns'];refs['In2.Cu']=refs['F.Cu'];free[NET,'In2.Cu']=free[NET,'In2.Cu'].intersection(refs['In2.Cu'].buffer(-.105))
 r38=json.loads(A.read(HERE/'di15-joint-r11-In3-existing-return-nomination-r38.json'));l38raw=A.read(r38['saved_local_site_checkpoint']);assert C.sha(l38raw)=='7f454fd9404c280a61c12eed5be338b41bacd04be58a27223e35baa17645d18c';l38=pickle.loads(l38raw);currentraw=A.read(HERE/'di15-current-joint-r11-projection-r34.pkl');assert C.sha(currentraw)==r['only_DI6_owned_delta_current_checkpoint_sha256'];cur=pickle.loads(currentraw);domain=cur['h']['domains_normalized'];prior=[]
 for q in l38['records']['In2.Cu']:
  n=L.norm(q['net'])
  if q['kind']=='track' and n!=GND and domain.get(n)==domain.get(GND):
   covered=q['shape'].intersection(refs['In2.Cu'])
   if not covered.is_empty:prior.append(covered)
 prior=unary_union(prior);via[NET]=via[NET].difference(prior.buffer(.530,quad_segs=128));via[GND]=via[GND].difference(prior.buffer(.105,quad_segs=128));del cur
 sp=K.sites(src.buffer(-.075).intersection(free[NET,'F.Cu']),list(src.centroid.coords)[0],4);dp=K.sites(dst.buffer(-.075).intersection(free[NET,'F.Cu']),list(dst.centroid.coords)[0],4);diagnosis=[];nominees=[];attempts=[]
 def component_for(layer,p):return unary_union([q for q in K.pieces(free[NET,layer]) if q.covers(Point(p))])
 def pairs_for(region,preferred):
  choices=[]
  for ret in oldret:
   c=Point(ret['at_mm']);reg=region.intersection(c.buffer(1,quad_segs=128).difference(c.buffer(.825,quad_segs=128)))
   for site in K.sites(reg,preferred,4):choices.append({'signal':site['at_mm'],'return':ret['at_mm'],'return_new':False,'old_return_UUID':ret['UUID'],'score_mm':site['cost_mm'],'old_return':ret})
  for site in K.sites(region,preferred,12):
   c=Point(site['at_mm']);reg=via[GND].intersection(c.buffer(1,quad_segs=128).difference(c.buffer(.825,quad_segs=128)))
   for ret in K.sites(reg,[site['at_mm'][0]-.9,site['at_mm'][1]],4):choices.append({'signal':site['at_mm'],'return':ret['at_mm'],'return_new':True,'old_return_UUID':None,'score_mm':site['cost_mm']})
  return sorted(choices,key=lambda q:q['score_mm'])[:16]
 for srow in sp[:1]:
  sr=via[NET].intersection(component_for('F.Cu',srow['at_mm'])).intersection(Point(src.centroid).buffer(5,quad_segs=128))
  for drow in dp[:1]:
   dr=via[NET].intersection(component_for('F.Cu',drow['at_mm'])).intersection(Point(dst.centroid).buffer(5,quad_segs=128))
   for i,p in enumerate(K.pieces(free[NET,'In2.Cu'])):
    a=sr.intersection(p);b=dr.intersection(p)
    if a.is_empty and b.is_empty:continue
    row={'component':i,'source_via_area_mm2':a.area,'target_via_area_mm2':b.area,'common_transport':not a.is_empty and not b.is_empty};diagnosis.append(row)
    if a.is_empty or b.is_empty:continue
    so=pairs_for(a,[118.45,90.75]);do=pairs_for(b,[131.25,112.35]);row.update(source_pair_options=len(so),target_pair_options=len(do))
    for qa,qb in itertools.product(so,do):
     news=[qa['signal'],qb['signal']]+[q['return'] for q in(qa,qb) if q['return_new']]
     if any(math.dist(x,y)<.81 for x,y in itertools.combinations(news,2)):continue
     nominees.append({'source_attachment':srow['at_mm'],'target_attachment':drow['at_mm'],'signals':[qa['signal'],qb['signal']],'returns':[qa['return'],qb['return']],'return_new':[qa['return_new'],qb['return_new']],'old_return_UUIDs':[qa['old_return_UUID'],qb['old_return_UUID']],'score_mm':qa['score_mm']+qb['score_mm']})
 print('DI15_STRICT_IN2_COMMON_COMPONENTS',diagnosis,'NOMINEES',len(nominees),flush=True)
 for candidate in sorted(nominees,key=lambda q:q['score_mm'])[:24]:
  pathrow={**candidate,'paths':[]};attempts.append(pathrow);cuts=unary_union([Point(p).buffer(.530,quad_segs=128) for p,new in zip(candidate['returns'],candidate['return_new']) if new]);pts=[candidate['source_attachment'],*candidate['signals'],candidate['target_attachment']]
  for l,a,b in zip(['F.Cu','In2.Cu','F.Cu'],pts,pts[1:]):
   ff=free[NET,l].difference(cuts);parts=[p for p in K.pieces(ff) if p.covers(Point(a)) and p.covers(Point(b))]
   if not parts:pathrow['failed_layer']=l;break
   path,search=T.route(parts[0],tuple(a),tuple(b))
   if len(path)<2:pathrow['failed_layer']=l;break
   path=[[round(x,6),round(y,6)] for x,y in path];body=unary_union([A.shape({'kind':'segment','a':x,'b':y,'w':.2}) for x,y in zip(path,path[1:])]);gap=body.difference(refs[l]).area;pathrow['paths'].append({'layer':l,'points_mm':path,'length_mm':LineString(path).length,'width_mm':.2,'full_body_prior_actual_source_reference_gap_mm2':gap,'search':search})
   if gap>1e-9:pathrow['failed_reference_layer']=l;break
  if len(pathrow['paths'])==3 and not pathrow.get('failed_reference_layer'):break
 positive=bool(attempts and len(attempts[-1]['paths'])==3 and not attempts[-1].get('failed_reference_layer'));saved=HERE/'di15-r46-In2-local-geometry.pkl';assert not saved.exists();saved.write_bytes(pickle.dumps({'free':free,'via':via,'refs':refs,'sourcepad':src,'targetpad':dst,'existing_returns':oldret,'reservation_shapes':loc['reservation_shapes'],'old_In2_body_protection':prior},protocol=5))
 report={'verdict':'DI15_STRICT_ORDINARY_F_IN2_F_CONCRETE_PATH_NOMINATED_INDEPENDENT_AUDIT_OPEN' if positive else'DI15_STRICT_IN2_TRANSPORT_INCOMPLETE','exact_current_ROOT_R11_model_sha256':r['exact_current_ROOT_R11_model_sha256'],'only_DI6_owned_delta_current_checkpoint_sha256':r['only_DI6_owned_delta_current_checkpoint_sha256'],'R18_hard_snapshot_sha256':r['LG_R18_hard_snapshot_sha256'],'R18_hard_only_no_source_reference_credit':True,'preserved_four_segment_R44_incomplete_alternative_sha256':C.sha(A.read(rp)),'raw_net':RAW,'policy':None,'ordinary_only_no_controlled_In2_or_SI_qualification':True,'adjacent_used_reference':'actual source-rooted In1 LOGIC_GND for both F and In2 bodies','strict_max_three_layer_segments_retained':True,'ordinary_signal_vias_count':2,'all_current_Cu_FAULT9_and_DI6_exact_preserved':True,'old_In2_bodies_also_protected_from_new_holes':True,'old_In2_body_protection_WKB_sha256':C.sha(prior.wkb),'all_F_B_SMD_old_hole_pitch_masks_preserved':True,'component_diagnosis':diagnosis,'nomination_count':len(nominees),'attempts':attempts,'selected':attempts[-1] if positive else None,'saved_local_geometry':str(saved),'saved_local_geometry_sha256':C.sha(saved.read_bytes()),'full_new_cut_and_oldcontact_current_r06_r07_source_return_native_DRC_and_SI_gates':'OPEN','every_new_or_reused_ordinary_via_actual_native_all6_attestation_required':True,'board_written':False,'native_jobs':0,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'diagnosis':diagnosis,'selected':report['selected']}),flush=True)
if __name__=='__main__':main()
