"""Continuous additive DI15 transport handoff with exact latest reservations.

Four layer segments, three ordinary signal transitions, no copper rip-up.
Every positive remains a constructor nominee pending separate full audit.
"""
import sys,json,pickle,math,time,uuid,itertools
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
 started=time.monotonic();out=HERE/'di15-hybrid-transport-nomination-r44.json';assert not out.exists();A.read(__file__)
 rpath=HERE/'di15-joint-r11-In3-existing-return-nomination-r38.json';r=json.loads(A.read(rpath));assert C.sha(A.read(rpath))=='19fc476d7016caeb76e4413157754b35a327d03bdcea988950612344c1a5d519';assert r['exact_raw_net']==RAW and r['policy'] is None
 localraw=A.read(r['saved_local_site_checkpoint']);assert C.sha(localraw)=='7f454fd9404c280a61c12eed5be338b41bacd04be58a27223e35baa17645d18c';local=pickle.loads(localraw);free=local['free'];via=local['via'];refs=local['refs'];win=local['window']
 respath=HERE.parent/'logic-return-r18-snapshot-1/proposed-zones.pkl';rr=A.read(respath);assert C.sha(rr)=='943d222e160f478d8cc351f63489b5b07a4ef380a326e81b8e6f2a6d13a05a42';res=pickle.loads(rr);assert len(res)==7 and all(L.norm(z['net'])==GND for z in res);reserve=[];vobs=[]
 for z in res:
  if z['shape'].distance(win)>2:continue
  gap=max(.15,float(z.get('clearance_mm',.15)));mask=z['shape'].buffer(gap+.030+.105,quad_segs=128);free[NET,z['layer']]=free[NET,z['layer']].difference(mask);vobs.append(z['shape'].buffer(.25+gap+.030,quad_segs=128));reserve.append({'UUID':z['uuid'],'layer':z['layer'],'local_mm':float(z.get('clearance_mm',.15)),'shape_WKB_sha256':C.sha(z['shape'].wkb),'hard_only_no_reference_credit':True})
 via[NET]=via[NET].difference(unary_union(vobs));src=local['sourcepad'];dst=local['targetpad'];sp=K.sites(src.buffer(-.075).intersection(free[NET,'F.Cu']),list(src.centroid.coords)[0],4);dp=K.sites(dst.buffer(-.075).intersection(free[NET,'F.Cu']),list(dst.centroid.coords)[0],4);oldret=local['existing_returns'];diagnosis=[];nominees=[];attempts=[]
 def component_for(layer,p):return unary_union([q for q in K.pieces(free[NET,layer]) if q.covers(Point(p))])
 def paired_options(region,preferred):
  choices=[]
  for ret in oldret:
   c=Point(ret['at_mm']);reg=region.intersection(c.buffer(1,quad_segs=128).difference(c.buffer(.825,quad_segs=128)))
   for site in K.sites(reg,preferred,3):choices.append({'signal':site['at_mm'],'return':ret['at_mm'],'return_new':False,'old_return_UUID':ret['UUID'],'score_mm':site['cost_mm'],'old_return_nominee':ret})
  for site in K.sites(region,preferred,6):
   c=Point(site['at_mm']);reg=via[GND].intersection(c.buffer(1,quad_segs=128).difference(c.buffer(.825,quad_segs=128)))
   for ret in K.sites(reg,[site['at_mm'][0]-.9,site['at_mm'][1]],2):choices.append({'signal':site['at_mm'],'return':ret['at_mm'],'return_new':True,'old_return_UUID':None,'score_mm':site['cost_mm']})
  return sorted(choices,key=lambda q:q['score_mm'])[:8]
 for srow in sp[:1]:
  sr=via[NET].intersection(component_for('F.Cu',srow['at_mm'])).intersection(Point(src.centroid).buffer(5,quad_segs=128))
  for drow in dp[:1]:
   dr=via[NET].intersection(component_for('F.Cu',drow['at_mm'])).intersection(Point(dst.centroid).buffer(5,quad_segs=128))
   for l1,l2 in [('B.Cu','In3.Cu'),('In3.Cu','B.Cu')]:
    for i,p1 in enumerate(K.pieces(free[NET,l1])):
     a=sr.intersection(p1)
     if a.is_empty:continue
     for j,p2 in enumerate(K.pieces(free[NET,l2])):
      b=dr.intersection(p2)
      if b.is_empty:continue
      middle=via[NET].intersection(p1).intersection(p2);row={'layers':[l1,l2],'source_component':i,'target_component':j,'source_region_mm2':a.area,'target_region_mm2':b.area,'handoff_region_mm2':middle.area};diagnosis.append(row)
      if middle.is_empty:continue
      aa=paired_options(a,[118.45,90.75]);bb=paired_options(b,[131.25,112.35]);cc=paired_options(middle,[124,104]);row.update(source_paired_options=len(aa),target_paired_options=len(bb),handoff_paired_options=len(cc))
      for qa,qc,qb in itertools.product(aa,cc,bb):
       signals=[qa['signal'],qc['signal'],qb['signal']];returns=[qa['return'],qc['return'],qb['return']];newreturns=[q['return'] for q in(qa,qc,qb) if q['return_new']];allnew=signals+newreturns
       if any(math.dist(x,y)<.81 for x,y in itertools.combinations(allnew,2)):continue
       nominees.append({'layers':['F.Cu',l1,l2,'F.Cu'],'source_attachment':srow['at_mm'],'target_attachment':drow['at_mm'],'signals':signals,'returns':returns,'return_new':[q['return_new'] for q in(qa,qc,qb)],'old_return_UUIDs':[q['old_return_UUID'] for q in(qa,qc,qb)],'score_mm':qa['score_mm']+qc['score_mm']+qb['score_mm']})
 print('DI15_HYBRID_HANDOFF_COMPONENTS',len(diagnosis),'NOMINEES',len(nominees),flush=True)
 for candidate in sorted(nominees,key=lambda q:q['score_mm'])[:20]:
  pathrow={**candidate,'paths':[]};attempts.append(pathrow);cuts=unary_union([Point(p).buffer(.530,quad_segs=128) for p,new in zip(candidate['returns'],candidate['return_new']) if new]);pts=[candidate['source_attachment'],*candidate['signals'],candidate['target_attachment']]
  for l,a,b in zip(candidate['layers'],pts,pts[1:]):
   reg=free[NET,l].difference(cuts);parts=[p for p in K.pieces(reg) if p.covers(Point(a)) and p.covers(Point(b))]
   if not parts:pathrow['failed_layer']=l;break
   path,search=T.route(parts[0],tuple(a),tuple(b))
   if len(path)<2:pathrow['failed_layer']=l;break
   path=[[round(x,6),round(y,6)] for x,y in path];body=unary_union([A.shape({'kind':'segment','a':x,'b':y,'w':.2}) for x,y in zip(path,path[1:])]);gap=body.difference(refs[l]).area;pathrow['paths'].append({'layer':l,'points_mm':path,'length_mm':LineString(path).length,'width_mm':.2,'full_body_prior_actual_source_reference_gap_mm2':gap,'search':search})
   if gap>1e-9:pathrow['failed_reference_layer']=l;break
  if len(pathrow['paths'])==4 and not pathrow.get('failed_reference_layer'):break
 positive=bool(attempts and len(attempts[-1]['paths'])==4 and not attempts[-1].get('failed_reference_layer'));saved=HERE/'di15-r44-hybrid-local-geometry.pkl';assert not saved.exists();saved.write_bytes(pickle.dumps({'free':free,'via':via,'refs':refs,'reservation_shapes':res,'sourcepad':src,'targetpad':dst,'existing_returns':oldret,'current_ROOT_R11_plus_DI6_checkpoint_sha256':r['exact_DI6_delta_only_current_checkpoint_sha256']},protocol=5))
 report={'verdict':'DI15_ADDITIVE_HYBRID_CONCRETE_PATH_NOMINATED_INDEPENDENT_AUDIT_OPEN' if positive else'DI15_HYBRID_HANDOFF_INCOMPLETE','exact_current_ROOT_R11_model_sha256':r['current_joint_R11_model_sha256'],'only_DI6_owned_delta_current_checkpoint_sha256':r['exact_DI6_delta_only_current_checkpoint_sha256'],'R38_local_geometry_sha256':C.sha(localraw),'LG_R18_hard_snapshot_sha256':C.sha(rr),'LG_R18_hard_geometry_ledger':reserve,'LG_R18_reference_credit':False,'raw_net':RAW,'policy':r['policy'],'all_current_Cu_preserved':True,'ordinary_signal_vias_count':3,'every_ordinary_new_via_all6_required':True,'layer_chain_does_not_repeat_transport_layers':True,'all_F_B_SMD_and_old_hole_pitch_masks_preserved':True,'component_handoff_diagnosis':diagnosis,'nomination_count':len(nominees),'attempts':attempts,'saved_local_geometry':str(saved),'saved_local_geometry_sha256':C.sha(saved.read_bytes()),'selected':attempts[-1] if positive else None,'new_and_reused_return_actual_native_annuli_fullcuts_oldcontact_current_r06_r07_source_reference_gates':'OPEN','board_written':False,'native_jobs':0,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'diagnosis':diagnosis,'selected':report['selected']}),flush=True)
if __name__=='__main__':main()
