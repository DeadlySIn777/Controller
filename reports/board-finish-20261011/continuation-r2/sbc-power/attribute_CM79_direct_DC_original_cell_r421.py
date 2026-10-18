"""Pin exact DC Cu/hole blockers and saved trial dependency without rerouting."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'exact-expanded-CM79-direct-DC-ground-r420.py').read_text(encoding='utf-8')
s=s.replace('CM79-actual-R157-direct-DC-ground-retained-CORE-r420','CM79-direct-DC-original-Cu-hole-cell-attribution-r421')
a=s.index(' routes=[];winner=None');b=s.index('\nif __name__',a)
tail=''' free=region.intersection(board).difference(hard);point=Point(pad['x'],pad['y']);faces=[p for p in RF.parts(free)if p.covers(point)];boundary=unary_union([p.boundary for p in faces]).buffer(.00001);cmids={r['uuid']for kind in ('tracks','vias')for r in cm[kind]};cuRows=[];holeRows=[]
 for r in rec['F.Cu']:
  if L.norm(r['net'])==NET or not r['shape'].intersects(region):continue
  obstacle=r['shape'].buffer(.1+max(gap(r['net']),float(nativeZones[r['uuid']]['clearance_mm'])if r['kind']=='fill'and r['uuid']in nativeZones else .15)+.025005,quad_segs=64)
  if not obstacle.intersection(boundary).is_empty:cuRows.append({'UUID':r['uuid'],'kind':r['kind'],'net':r['net'],'only_new_CM':r['uuid']in cmids,'bounds_mm':list(r['shape'].bounds),'source':r.get('source',{}).get('uuid')})
 for uid,sh in holes:
  if sh.intersects(roi)and not sh.buffer(.380005,quad_segs=64).intersection(boundary).is_empty:holeRows.append({'UUID':uid,'only_new_CM':uid in cmids,'true_original_drill_bounds_mm':list(sh.bounds)})
 for i,f in enumerate(faces):(OUT/('actual-DC-F-contact-axis-cell-'+str(i)+'.wkb')).write_bytes(f.wkb)
 put('exact-DC-cell-original-Cu-and-hole-boundary.json',{'direct_ground_DC_no_signal_shadow_gate':True,'original_pad':{'UUID':pad['uuid'],'xy_mm':[pad['x'],pad['y']]},'actual_foreign_Cu_hole_rule_free_start_face_count':len(faces),'faces':[{'area_mm2':f.area,'bounds_mm':list(f.bounds)}for f in faces],'boundary_actual_foreign_Cu':cuRows,'boundary_all_true_holes':holeRows})
 trialPath=P/'CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371/model.pkl';_,th,_,_,_=pickle.loads(trialPath.read_bytes());targets=['b7dc346a-8a46-4b4c-ae3d-c5990ddefc96','b1e550d5-047a-447c-a64c-45c2a92c14b0','dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1'];delta=[]
 for uid in targets:
  delta.append({'UUID':uid,'exact_R157_base_items':[x for kind in ('tracks','vias')for x in h[kind]if x['uuid']==uid],'frozen_historical_R371_items':[x for kind in ('tracks','vias')for x in th[kind]if x['uuid']==uid]})
 put('saved-R371-versus-actual-base-exact-wall-dependency.json',{'R371_model_SHA256':sha(trialPath),'actual_BASE_SHA256':sha(BASE),'only_exact_named_wall_barrel_presence_delta':delta,'not_current_source_native_equivalence':True})
 put('receipt.json',{'status':'DC_CONTACT_CELL_BLOCKER_AND_FROZEN_TRIAL_DEPENDENCY_ATTRIBUTION','actual_R157_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'operator_SHA256':sha(policy),'actual_F_Cu_hole_rule_face_count':len(faces),'original_foreign_Cu_boundary_count':len(cuRows),'hole_boundary_count':len(holeRows),'native_jobs_or_edits':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R421_COMPLETE',sha(OUT/'receipt.json'),len(faces),len(cuRows),len(holeRows),flush=True)
'''
s=s[:a]+tail+s[b:]
E=P/'exact-expanded-DC-original-cell-attribution-r421.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8')
exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
