"""ONLY-NEW CM hole counterfactual and exact original reference attribution."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'exact-expanded-CM79-retained-CORE-named-handoffs-r418.py').read_text(encoding='utf-8')
s=s.replace('CM79-actual-R157-retained-CORE-named-ground-handoffs-r418','CM79-actual-R157-only-new-CM-hole-counterfactual-r419')
a=s.index(' cmids={r[');b=s.index(' ports.sort(',a)
new=''' cmids={r['uuid']for kind in ('tracks','vias')for r in cm[kind]};ports=[]
 saved=json.loads((P/'CM79-actual-R157-retained-CORE-ground-port-census-r417/only-eligible-new-LG-source-ports.json').read_bytes())
 for i,row in enumerate(saved):
  xy=row['xy_mm'];point=Point(*xy);ann=point.buffer(.25,quad_segs=128).difference(point.buffer(.1,quad_segs=128));ports.append({'via':{'uuid':'R419-CANDIDATE-'+str(i),'x':xy[0],'y':xy[1],'d':.5,'drill':.2},'ann':ann,'source_class':'NEW_PORT_COUNTERFACTUAL_NOT_A_NOMINATION','both_plane_actual_SOURCE_keys':False,'actual_before_SOURCE_annulus_overlap_mm2':row['actual_SOURCE_LG_annulus_overlap_mm2']})
'''
s=s[:a]+new+s[b:]
s=s.replace("holeShapes={uid:sh.buffer(.380005,quad_segs=64)for uid,sh in holes if sh.intersects(roi)}","holeShapes={uid:sh.buffer(.380005,quad_segs=64)for uid,sh in holes if uid not in cmids and sh.intersects(roi)}")
s=s.replace("'both_plane_actual_SOURCE_keys':port['both_plane_actual_SOURCE_keys'],","'both_plane_actual_SOURCE_keys':port['both_plane_actual_SOURCE_keys'],'ONLY_NEW_CM_holes_counterfactually_withdrawn':True,")
s=s.replace("'status':'ACTUAL_R157_CM79_RETAINED_CORE_NAMED_HANDOFF_AND_BLOCKER_SCREEN'","'status':'ONLY_NEW_CM_HOLE_WITHDRAWAL_COUNTERFACTUAL_NOT_A_PROPOSAL'")
s=s.replace("'no_unrelated_caps_no_newholes_no_NEW_CM_source_credit':True","'no_unrelated_caps_no_actual_newholes_no_NEW_CM_source_credit':True,'ONLY_NEW_CM_holes_withdrawal_is_not_authority_to_adopt':True")
s=s.replace('R418_COMPLETE','R419_COMPLETE')
needle=" put('exact-CM79-retained-CORE-F-start-contact-face-and-blockers.json',"
a=s.index(needle)
extra=''' originalHoleRows=[];referenceRows=[]
 for uid,sh in holeShapes.items():
  if not sh.intersects(faceBoundary):continue
  originalHoleRows.append({'UUID':uid,'original_drill_expanded_F_axis_guard_bounds_mm':list(sh.bounds),'contacts_current_start_axis_boundary':True})
 for z in native['zones']:
  if L.norm(z['net'])==NET:continue
  for sh in L.poly(N.O.polys(z['fills'].get('In1.Cu',[]))):
   if sh.distance(faceBoundary)<1:referenceRows.append({'UUID':z['uuid'],'raw_net':z['net'],'layer':'In1.Cu','actual_native_foreign_fill_distance_to_F_face_boundary_mm':sh.distance(faceBoundary),'bounds_mm':list(sh.bounds)})
 for z in q:
  if z['layer']=='In1.Cu'and L.norm(z['net'])!=NET and z['shape'].distance(faceBoundary)<1:referenceRows.append({'UUID':z['uuid'],'raw_net':z['net'],'layer':'In1.Cu','held_current_owned_role_distance_to_F_face_boundary_mm':z['shape'].distance(faceBoundary),'bounds_mm':list(z['shape'].bounds)})
 put('exact-original-hole-and-In1-reference-boundary-attribution.json',{'start_axis_face_bounds_mm':[list(f.bounds)for f in startFaces],'original_hole_axis_obstacles':originalHoleRows,'actual_native_or_owned_foreign_reference_plane_neighbors':referenceRows,'source_LGIn1_reference_boundary_distance_mm':reference.boundary.distance(faceBoundary),'counterfactual_new_CM_holes_removed_count':sum(uid in cmids for uid,sh in holes),'every_original_hole_and_foreign_plane_held':True})
'''
s=s[:a]+extra+s[a:]
E=P/'exact-expanded-only-new-CM-hole-counterfactual-r419.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8')
exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
