"""Spatial new-source-port scope, reusing closed R295 source graph; no routes/edits."""
from pathlib import Path
P=Path(__file__).resolve().parent;H=P.parent
base=H/'screen_CORE5_scoped_LG_retreat_side_In3_LGIn4_transport_r295.py'
s=base.read_text(encoding='utf-8')
s=s.replace("OUT=H/'CORE5-current-new-transport-full1p25-In3-real-LGIn4-screen-r295'","OUT=H/'sbc-power/CORE5-actual-new-In2-source-port-reachability-only-new-CM-counterfactual-r406'")
old="coregroups=K.physical(actual,NET,ctx)[1]"
new="saved=H/'CORE5-current-new-transport-full1p25-In3-real-LGIn4-screen-r295'; sr=json.loads((saved/'source-binding.json').read_bytes()); sf=saved/'actual-full-R157-CORE5-middle-withdrawn-all-drilled-groups.pkl'; assert sha(sf)==sr['CORE5_actual_groups_SHA256'];coregroups=pickle.loads(sf.read_bytes())"
assert s.count(old)==1;s=s.replace(old,new)
old="obstacles=[];ledger=[]"
new="""cmfile=H/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/only-new-CM-ordinary-discrete-no-deletes.pkl';cm=pickle.loads(cmfile.read_bytes()); cmids={x['uuid']for kind in('tracks','vias')for x in cm[kind]};obstacles=[];ledger=[];cmObstacles=[];allFixed=[]"""
assert s.count(old)==1;s=s.replace(old,new)
old="obstacles.append(shape.buffer(.625+clear+.025005,quad_segs=64));ledger.append({'UUID':uid,'net':net,'kind':kind,'clearance_mm':clear})"
new="""expanded=shape.buffer(.625+clear+.025005,quad_segs=64);obstacles.append(expanded);(cmObstacles if uid in cmids else allFixed).append(expanded);ledger.append({'UUID':uid,'net':net,'kind':kind,'clearance_mm':clear,'only_new_CM_counterfactual_withdrawable':uid in cmids})"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("if sh.intersects(roi):obstacles.append(sh.buffer(.905005,quad_segs=64))","if sh.intersects(roi):\n    expanded=sh.buffer(.905005,quad_segs=64);obstacles.append(expanded);(cmObstacles if v['uuid']in cmids else allFixed).append(expanded)",1)
old="if sh.intersects(roi):obstacles.append(sh.buffer(.905005,quad_segs=64))"
new="if sh.intersects(roi):\n     expanded=sh.buffer(.905005,quad_segs=64);obstacles.append(expanded);allFixed.append(expanded)"
assert s.count(old)==1;s=s.replace(old,new)
old="if s.intersects(roi):obstacles.append(s.buffer(.650005,quad_segs=64))"
new="if s.intersects(roi):\n     expanded=s.buffer(.650005,quad_segs=64);obstacles.append(expanded);allFixed.append(expanded)"
assert s.count(old)==1;s=s.replace(old,new)
start=s.index(' results=[];accepted=[]')
end=s.index(" print('R295_COMPLETE'",start)
end=s.index('\n',end)
replacement=''' sourceRows=[r for r in coreroot if r['layer']=='In2.Cu']; sourceCu=unary_union([r['shape'].intersection(roi)for r in sourceRows if r['shape'].intersects(roi)]);put('actual-In2-source-spatial-target-authority.json',{'source_selector':['R11022','2'],'after_middle_withdrawal_source_keys':len(K.keys(coreroot)),'source_records':[{'UUID':r['uuid'],'kind':r['kind'],'layer':r['layer'],'area_mm2':r['shape'].area}for r in sourceRows if r['shape'].intersects(roi)],'source_group_cache_SHA256':sha(sf)});(OUT/'actual-CORE5-In2-source-Cu.wkb').write_bytes(sourceCu.wkb)
 results=[]
 for name,obstacle in [('all49CMhard',hard),('ONLY_NEW_CM_counterfactual_not_a_nomination',unary_union(allFixed))]:
  allowed=unary_union([reference,startcap]);free=allowed.buffer(-.625005,quad_segs=64).intersection(region).intersection(board).difference(obstacle);face=next((p for p in RF.parts(free)if p.covers(Point(startpoint))),None);row={'scope':name,'start_has_free_face':face is not None,'power1p25_body_and_native_LGIn4_SOURCE_reference_only':True,'no_unrelated_terminal_caps':True}
  if face is not None:
   (OUT/(name+'-right-port-reachable-axis-face.wkb')).write_bytes(face.wkb);near=sourceCu.intersection(face.buffer(1.024995,quad_segs=128));oldFsource=unary_union([r['shape'].intersection(roi)for r in coreroot if r['layer']=='F.Cu'and r['shape'].intersects(roi)]);nearF=oldFsource.intersection(face.buffer(1.024995,quad_segs=128));(OUT/(name+'-reachable-potential-new-In2-source-port-Cu.wkb')).write_bytes(near.wkb);(OUT/(name+'-reachable-potential-new-F-source-port-Cu.wkb')).write_bytes(nearF.wkb);points=nearest_points(face,sourceCu)if not sourceCu.is_empty else None;row.update({'actual_source_In2_Cu_distance_to_reachable_axis_face_mm':face.distance(sourceCu),'actual_SOURCE_In2_Cu_within_fullwidth625_plus_power400_reach_mm2':near.area,'actual_SOURCE_F_Cu_within_reach_mm2':nearF.area,'nearest_actual_source_and_reachable_axis_points_mm':[list(p.coords[0])for p in points]if points else None,'reachable_axis_face_area_mm2':face.area,'new_source_port_requires_ALL6_native_foreign_mask_court_hole_RETURN_guards':'OPEN'})
  results.append(row);print('R406_SCOPE',name,json.dumps(row),flush=True)
 put('only-finite-source-port-reachability-and-new-CM-counterfactual.json',results);put('receipt.json',{'status':'NEW_SOURCE_PORT_REACHABILITY_GEOGRAPHY_AND_ONLY_NEW_CM_COUNTERFACTUAL_NO_NOMINATION','actual_R295_SOURCE_cache_SHA256':sha(sf),'actual_R157_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'source_key_count':len(K.keys(coreroot)),'all_original_field_native_and_current_owned_planes_remain_hard':True,'only_new_CM_sparse_file_SHA256':sha(cmfile),'only_new_CM_UUID_count':len(cmids),'new_CM_In3_Cu_and_hole_expanded_obstacle_count':len(cmObstacles),'no_current_route_search_repeated':True,'all_original_fullwidth_F_anchor_Cu_before_reference_masks_and_source_contacts':'HARD final new-port/reroute gate','counterfactual_is_not_remove_permission_or_a_proposal':True,'result':results,'native_jobs':0,'source_or_board_edits':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R406_COMPLETE',sha(OUT/'receipt.json'),flush=True)
'''
s=s[:start]+replacement+s[end:]
E=P/'exact-expanded-actual-CORE5-new-source-port-reachability-r406.py';assert not E.exists();E.write_text(s,encoding='utf-8');exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
