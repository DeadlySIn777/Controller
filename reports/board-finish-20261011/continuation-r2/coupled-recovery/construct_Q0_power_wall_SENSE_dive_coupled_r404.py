"""Concrete bounded Q0/FLT/power/SENSE nomination, no board/native jobs."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'construct_Q0_two_native_walls_downshifted_F_In3_F_r388.py'
prefix=base.read_text(encoding='utf-8').split('from Q0_retained_FLT_source_supported_aperture_r384 import support_FLT')[0]
prefix=prefix.replace('Q0-two-native-walls-downshifted-F-In3-F-r388','Q0-power-wall-SENSE-dive-coupled-r404')
prefix=prefix.replace("delete={next(t['uuid']for t in h['tracks']if t['uuid'].startswith('c76c0c67')),'7b8f7e31-baac-4ff2-8b1f-3d210fb85e0d'}", "delete={next(t['uuid']for t in h['tracks']if t['uuid'].startswith('c76c0c67')),'7b8f7e31-baac-4ff2-8b1f-3d210fb85e0d','7bb3c794-cbe6-40a7-abfb-5a3ab7df28ff'}")
prefix=prefix.replace("FLT='/motherboard_do/DOA_FLT_N_FIELD'", "FLT='/motherboard_do/DOA_FLT_N_FIELD'\nnewvias += [{'uuid':'SENSE-source','net':SENSE,'x':229.03,'y':156.8,'d':.5,'drill':.2,'flashed':list(K.LAYERS)},{'uuid':'retained-SENSE-return','net':GND,'x':228.754382,'y':159.484519,'d':.5,'drill':.2,'flashed':list(K.LAYERS)}]")
exec(compile(prefix,str(base),'exec'))
POWER='/motherboard_do/DOA_FIELD_3V3'
from Q0_retained_FLT_source_supported_aperture_r384 import support_FLT
oldFLTvia=next(v for v in h['vias']if v['uuid'].startswith('a01ff36f'))
fltOwn,fltOwnLedger=support_FLT(K,current,{**h,'vias':h['vias']+newvias},trueRoot,iv,oldFLTvia,GND,FLT,'In1.Cu')
put(out/'retained-FLT-exact-own-support.json',fltOwnLedger);(out/'retained-FLT-exact-own-support.wkb').write_bytes(fltOwn.wkb)
oldSense=next(v for v in h['vias']if v['uuid']=='5a4b7757-ae7c-470d-81fe-abcec92e0f06')
assert oldSense['flashed']==['F.Cu','B.Cu']
supportCode=(H/'Q0_retained_FLT_source_supported_aperture_r384.py').read_text().replace('support_FLT','support_SENSE').replace('a01ff36f-ac32-4648-88fe-29a54c58570b','5a4b7757-ae7c-470d-81fe-abcec92e0f06').replace('(228.25,157.65,.6,.3)','(228.96,160.412,.5,.2)').replace('.575','.525').replace('RETAINED_FLT','RETAINED_SENSE')
namespace={};exec(compile(supportCode,str(H/'Q0_retained_FLT_source_supported_aperture_r384.py'),'exec'),namespace)
oldSenseOwn,oldSenseLedger=namespace['support_SENSE'](K,current,{**h,'vias':h['vias']+newvias},trueRoot,iv,oldSense,GND,SENSE,'In4.Cu')
put(out/'retained-SENSE-identity-bound-own-support.json',oldSenseLedger);(out/'retained-SENSE-identity-bound-own-support.wkb').write_bytes(oldSenseOwn.wkb)
def newOwn(v,plane):
 own=K.Z.bounded_disk(v,.525).intersection(oldrefs[plane])
 cuts=[K.Z.bounded_disk(o,.1 if K.L.norm(o['net'])==GND else .525)for o in newvias if o['uuid']!=v['uuid']]
 return own.difference(unary_union(cuts))
pairRows=[]
for sid,rid in [('Q0-source','b88b7a49-a1ea-458a-9195-d0a46a3a7f66'),('Q0-target','Q0-target-return'),('SENSE-source','b88b7a49-a1ea-458a-9195-d0a46a3a7f66'),('5a4b7757-ae7c-470d-81fe-abcec92e0f06','retained-SENSE-return'),('a01ff36f-ac32-4648-88fe-29a54c58570b','retained-FLT-return')]:
 sv=next(v for v in h['vias']+newvias if v['uuid']==sid);rv=next(v for v in h['vias']+newvias if v['uuid']==rid);ann=K.Z.bounded_disk(rv,rv['d']/2).difference(K.Z.bounded_disk(rv,rv['drill']/2));spacing=math.dist([sv['x'],sv['y']],[rv['x'],rv['y']]);layers={l:{'actual_before_annular_contact_mm2':ann.intersection(oldrefs[l]).area,'actual_after_annular_contact_mm2':ann.intersection(refs[l]).area,'after_finite_interior_contact_mm2':ann.buffer(-.025,quad_segs=128).intersection(refs[l]).area}for l in refs};ok=.90<=spacing<=1.0 and all(x['after_finite_interior_contact_mm2']>.002 for x in layers.values());pairRows.append({'signal':sid,'return':rid,'spacing_mm':spacing,'operator_window_mm':[.90,1.0],'after_local_source_contact_nomination_pass':ok,'layers':layers,'actual_global_after_graph_native_all_flashes_SI':'OPEN'})
put(out/'all-five-paired-source-return-nominations.json',pairRows);assert all(x['after_local_source_contact_nomination_pass']for x in pairRows)
power_ok=route_attachments('POWER-only-7bb-two-endpoints-fullwidth-F',POWER,'F.Cu',refs['In1.Cu'],Point(228.45,158.35),Point(229.45,159.35),tracks)
flt_ok=route_attachments('FLT-single-F-wall-detour-retained-barrel',FLT,'F.Cu',refs['In1.Cu'].union(fltOwn),Point(229.35,158.45),Point(228.5,157.6),tracks,qualified_new_own=fltOwn)
if flt_ok:
 uid,ch=identity.serial_segment(FLT,'F.Cu',[228.45,157.55],[228.5,157.6],.2);chunks[uid]=ch;tracks.append({'uuid':uid,'net':identity.raw(FLT),'layer':'F.Cu','a':[228.45,157.55],'b':[228.5,157.6],'w':.2})
ground_ok=route_attachments('moved-pulldown-real-F-ground',GND,'F.Cu',refs['In1.Cu'],newsh['2'].buffer(-.04,quad_segs=128),groundF.buffer(-.02,quad_segs=128),tracks)
senseSrc=next(v for v in newvias if v['uuid']=='SENSE-source');senseOwn=newOwn(senseSrc,'In4.Cu');senseRef=refs['In4.Cu'].union(senseOwn).union(oldSenseOwn)
senseB=route_attachments('SENSE-B-local-source-to-new-dive',SENSE,'B.Cu',senseRef,Point(228.96,156.45),Point(senseSrc['x'],senseSrc['y']),tracks,qualified_new_own=senseOwn)
if senseB:
 uid,ch=identity.serial_segment(SENSE,'B.Cu',[228.96,156.3691],[228.96,156.45],.2);chunks[uid]=ch;tracks.append({'uuid':uid,'net':identity.raw(SENSE),'layer':'B.Cu','a':[228.96,156.3691],'b':[228.96,156.45],'w':.2})
senseIn3=route_attachments('SENSE-In3-transport-to-retained-barrel-new-natural-In3-annulus',SENSE,'In3.Cu',senseRef,Point(senseSrc['x'],senseSrc['y']),Point(oldSense['x'],oldSense['y']),tracks,qualified_new_own=senseOwn.union(oldSenseOwn))
qref={l:refs[p].union(unary_union([newOwn(v,p)for v in newvias[:2]]))for l,p in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]}
qsource=route_attachments('Q0-F-source',NET,'F.Cu',qref['F.Cu'],signalF.buffer(-.04,quad_segs=128),Point(sites[0][2]),tracks,qualified_new_own=qref['F.Cu'].difference(refs['In1.Cu']))
qtransport=route_attachments('Q0-In3-common-transport',NET,'In3.Cu',qref['B.Cu'],Point(sites[0][2]),Point(sites[1][2]),tracks,qualified_new_own=qref['B.Cu'].difference(refs['In4.Cu']))
qtarget=route_attachments('Q0-F-target-moved-R10016',NET,'F.Cu',qref['F.Cu'],Point(sites[1][2]),newsh['1'].buffer(-.04,quad_segs=128),tracks,qualified_new_own=qref['F.Cu'].difference(refs['In1.Cu']))
identity.assert_chunks(chunks)
for uid,ch in chunks.items():(out/(uid+'.segment-chunk')).write_bytes(ch)
for uid,ch in deleted.items():(out/(uid+'.exact-owned-delete-chunk')).write_bytes(ch)
put(out/'path-nominations.json',pathrows)
pickle.dump({'tracks':tracks,'new_vias':newvias,'deleted_tracks':sorted(delete),'R10016_translation_mm':[-.5,-.5],'new_pad_shapes':newsh,'retained_SENSE_existing_mask':['F.Cu','B.Cu'],'retained_SENSE_prospective_additional_mask':['In3.Cu'],'all_required_old_flags_retained':True},(out/'sparse-nomination.pkl').open('wb'))
results={'POWER':power_ok,'FLT':flt_ok,'moved_ground':ground_ok,'SENSE_B':senseB,'SENSE_In3':senseIn3,'Q0_F_source':qsource,'Q0_In3':qtransport,'Q0_F_target':qtarget}
result={'verdict':'CONCRETE_BOUNDED_COUPLED_PATH_NOMINATION_ALL_FULL_GATES_OPEN'if all(results.values())else'BOUNDED_COUPLED_CONSTRUCTOR_INCOMPLETE','results':results,'model_sha256':sha(model),'source_sha256':sha(source),'operator_sha256':sha(operator),'actual_current_source_groups_sha256':sha(groupsfile),'exact_original_deletes':sorted(delete),'new_track_count':len(tracks),'new_via_count':len(newvias),'native_barrel_annulus_obligation':{'UUID':oldSense['uuid'],'unchanged_actual_required':['F.Cu','B.Cu'],'new_natural_flash_to_attest':['In3.Cu'],'unused_layer_flags_retained':True},'power_endpoint_and_interior_contact_authority':{'file':str(H/'Q0-adjacent-power-SENSE-barrel-contact-obligations-r402/receipt.json'),'sha256':sha(H/'Q0-adjacent-power-SENSE-barrel-contact-obligations-r402/receipt.json')},'same_net_new_own_hole_old_body_reference_scope':'OPEN; exact before-rooted own scope only, all other holes subtracted; full old strict failure ledger mandatory','full_source_contact_current_r06_r07_native_refill_DRC_and_new_SMD_DCloop_SI':'OPEN','maximum_signal_layer_legs':3,'all_inherited_R155_R368_28_CORE_R7_ROOT42_planner_native_failures_preserved':True,'board_written':False,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'results':results,'tracks':len(tracks)}),flush=True)
