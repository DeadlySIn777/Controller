"""Distinct no-new-power-hole route from two actual original LOAD barrels."""
from pathlib import Path
P=Path(__file__).resolve().parent;H=P.parent
s=(H/'screen_CORE5_scoped_LG_retreat_side_In3_LGIn4_transport_r295.py').read_text(encoding='utf-8')
s=s.replace("OUT=H/'CORE5-current-new-transport-full1p25-In3-real-LGIn4-screen-r295'","OUT=H/'sbc-power/CORE5-existing-LOAD-to-existing-SOURCE-fullwidth-In3-side-annulus-r411'")
s=s.replace('H=Path(__file__).resolve().parent\n','H=Path(__file__).resolve().parent.parent\n')
old='coregroups=K.physical(actual,NET,ctx)[1]';new="cached=H/'CORE5-current-new-transport-full1p25-In3-real-LGIn4-screen-r295';br=json.loads((cached/'source-binding.json').read_bytes());bp=cached/'actual-full-R157-CORE5-middle-withdrawn-all-drilled-groups.pkl';assert sha(bp)==br['CORE5_actual_groups_SHA256'];coregroups=pickle.loads(bp.read_bytes())";assert s.count(old)==1;s=s.replace(old,new)
old="start=next(v for v in h['vias']if v['uuid']=='63677f16-9cb3-5144-a82d-69a2c7fb8b3d');assert(start['d'],start['drill'])==(1.,.5)\n startpoint=(123.560945,206.750243);startcap=Point(start['x'],start['y']).buffer(.775,quad_segs=128)"
new="""rightAnchor=anchors[1];load=next(xs for xs in coregroups if any(r['kind']=='track'and r['uuid']==rightAnchor['uuid']for r in xs));loadids=sorted({r['uuid']for r in load if r['kind']=='via'});assert loadids==['765db048-1685-4652-b04d-5bf817870398','8c0a08eb-cca0-46db-814a-e18d7227c496'];starts=[(next(v for v in actual['vias']if v['uuid']==uid),next(r['shape']for r in load if r['kind']=='via'and r['uuid']==uid and r['layer']=='In3.Cu'))for uid in loadids]""";assert s.count(old)==1;s=s.replace(old,new)
start=s.index(' results=[];accepted=[]');end=s.index(" print('R295_COMPLETE'",start);end=s.index('\n',end)
replacement=''' results=[];accepted=[]
 for start,startann in starts:
  startcap=Point(start['x'],start['y']).buffer(start['d']/2+.275,quad_segs=128)
  for target,ann in targets:
   targetcap=Point(target['x'],target['y']).buffer(target['d']/2+.275,quad_segs=128);allowed=unary_union([reference,startcap,targetcap]);free=allowed.buffer(-.625005,quad_segs=64).intersection(region).intersection(board).difference(hard);startContact=startann.buffer(.624995,quad_segs=128);targetContact=ann.buffer(.624995,quad_segs=128);faces=[face for face in RF.parts(free)if not face.intersection(startContact).is_empty and not face.intersection(targetContact).is_empty];row={'original_LOAD_UUID':start['uuid'],'LOAD_xy':[start['x'],start['y']],'original_SOURCE_UUID':target['uuid'],'SOURCE_xy':[target['x'],target['y']],'exact_own_original_guards_mm':[start['d']/2+.275,target['d']/2+.275],'common_actual_Cu_SOURCE_reference_side_contact_face_count':len(faces),'route':None}
   for face in faces:
    sc=face.intersection(startContact).buffer(-.000005);tc=face.intersection(targetContact).buffer(-.000005)
    if sc.is_empty or tc.is_empty:continue
    a,e=nearest_points(sc,tc);startpoint=list(a.coords[0]);endpoint=list(e.coords[0]);path,method=TR.route(face,startpoint,endpoint);path=[[round(x,6),round(y,6)]for x,y in path];body=unary_union([LineString([a,bb]).buffer(.625,quad_segs=128)for a,bb in zip(path,path[1:])]);missing=body.difference(allowed);sourceOverlap=body.intersection(ann).area;loadOverlap=body.intersection(startann).area;row.update({'side_start_axis':startpoint,'side_target_axis':endpoint,'raw_exact_two_own_guard_reference_gap_EMPTY':missing.is_empty,'raw_gap_area_mm2':missing.area,'actual_SOURCE_annulus_overlap_mm2':sourceOverlap,'actual_LOAD_annulus_overlap_mm2':loadOverlap})
    if not missing.is_empty or sourceOverlap<=0 or loadOverlap<=0:continue
    row.update({'route':path,'length_mm':sum(math.dist(a,bb)for a,bb in zip(path,path[1:])),'method':method,'track_width_mm':1.25,'no_new_power_port_or_hole':True});accepted.append(row);(OUT/(start['uuid']+'-'+target['uuid']+'-only-full1p25-In3-body.wkb')).write_bytes(body.wkb);break
   results.append(row);put('finite-two-existing-LOAD-to-21-actual-SOURCE-side-annulus-attempts.json',results);print('R411_PAIR',start['uuid'],target['uuid'],len(faces),bool(row['route']),flush=True)
   if accepted:break
  if accepted:break
 put('only-existing-LOAD-to-SOURCE-fullwidth-In3-nominations.json',accepted);put('receipt.json',{'status':'EXISTING_ORIGINAL_LOAD_TO_SOURCE_NO_NEW_POWER_HOLE_SCREEN_COMPLETE','actual_R157_SOURCE_cache_SHA256':sha(bp),'actual_R157_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'post_middle_source_keys':len(K.keys(coreroot)),'original_LOAD_keys':len(K.keys(load)),'LOAD_port_count':len(starts),'SOURCE_port_count':len(targets),'attempt_count':len(results),'proposal_count':len(accepted),'width_mm':1.25,'old_anchors_discrete_fieldplanes_all49CM_and_holes_hard':True,'only_original_LG_In3_native_retreat_pending_local_source_oldrefs':True,'actual_existing_barrel_ground_return_finite_transfer_incoming_neck_current_plating_thermal':'OPEN','source_native_jobs_or_board_edits':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R411_COMPLETE',sha(OUT/'receipt.json'),len(accepted),flush=True)
'''
s=s[:start]+replacement+s[end:];E=P/'exact-expanded-existing-LOAD-to-SOURCE-In3-r411.py';assert not E.exists();E.write_text(s,encoding='utf-8');exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
