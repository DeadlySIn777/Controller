"""Reuse saved GATE detour/ports; keep all old POWER/FLT copper exact.

SENSE existing-barrel In2 transport is a scoped SAME_PLANE engineering
proposal. Inherited blanket paired-return failures remain distinct and open.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'construct_Q0_two_native_walls_downshifted_F_In3_F_r388.py'
prefix=base.read_text().split('from Q0_retained_FLT_source_supported_aperture_r384 import support_FLT')[0]
prefix=prefix.replace('Q0-two-native-walls-downshifted-F-In3-F-r388','Q0-saved-GATE-SENSE-existing-barrels-r450')
old="delete={next(t['uuid']for t in h['tracks']if t['uuid'].startswith('c76c0c67')),'7b8f7e31-baac-4ff2-8b1f-3d210fb85e0d'}"
new="delete={'9963e84b-e2c5-4d1e-9d1e-05e2322e1fca','ff87aa4e-ab2f-45de-95a8-d335e9f4bc58','6faa01ce-84d4-437d-8bcf-165482712afb','7b8f7e31-baac-4ff2-8b1f-3d210fb85e0d'}"
assert old in prefix;prefix=prefix.replace(old,new,1).replace('[229.12,157.72]','[229.15,156.57]')
prefix=prefix.replace("newvias.append({'uuid':'retained-FLT-return','net':GND,'x':227.496314,'y':157.071677,'d':.5,'drill':.2,'flashed':list(K.LAYERS)})",'')
prefix=prefix.replace("refs['In1.Cu'if layer=='F.Cu'else'In4.Cu']","refs['In1.Cu'if layer in('F.Cu','In2.Cu')else'In4.Cu']")
exec(compile(prefix,str(base),'exec'))
POWER='/motherboard_do/DOA_FIELD_3V3';assert not any(K.L.norm(oldtrack[u]['net'])==POWER for u in delete)
ivsrc=source.read_bytes();senseVias=[next(v for v in h['vias']if v['uuid']==u)for u in('1730e9cb-287c-4fd9-9862-57e677846263','5a4b7757-ae7c-470d-81fe-abcec92e0f06')]
assert all(v['flashed']==['F.Cu','B.Cu']and K.L.norm(v['net'])==SENSE for v in senseVias)
supportTemplate=(H/'Q0_retained_FLT_source_supported_aperture_r384.py').read_text();senseOwn=[];senseSupport=[]
for v in senseVias:
 rad=v['drill']/2+.25+.025
 code=supportTemplate.replace('support_FLT','support_SENSE').replace('a01ff36f-ac32-4648-88fe-29a54c58570b',v['uuid']).replace('(228.25,157.65,.6,.3)',repr((v['x'],v['y'],v['d'],v['drill']))).replace('.575',repr(rad));namespace={};exec(compile(code,str(H/'Q0_retained_FLT_source_supported_aperture_r384.py'),'exec'),namespace)
 sh,row=namespace['support_SENSE'](K,current,{**h,'vias':h['vias']+newvias},trueRoot,iv,v,GND,SENSE,'In1.Cu');senseOwn.append(sh);row.update(actual_old_reference_layer_flash=False,actual_reference_width_mm=v['drill'],new_used_signal_layer='In2.Cu',same_plane_proposal='F and In2 share physical source-rooted In1; continuous finite own-aperture-path/source proof OPEN',inherited_blanket_paired_return_checker='FAIL preserved; no old via copper flags changed');senseSupport.append(row)
 for label,shape in [('native-own-support',sh)]: (out/(v['uuid']+'-'+label+'.wkb')).write_bytes(shape.wkb)
put(out/'two-existing-SENSE-same-plane-own-aperture-nominations.json',senseSupport)
# Two exact subsets maintain the real old B contacts and unused-layer flags.
terminals=[[[236.6779,156.3691],[236.8779,156.3691]],[[228.96,160.2],[228.96,160.412]]]
terminalLedger=[]
for axis,uid in zip(terminals,('6faa01ce-84d4-437d-8bcf-165482712afb','7b8f7e31-baac-4ff2-8b1f-3d210fb85e0d')):
 old=oldtrack[uid];aa=[int(round(x*1e6))for x in old['a']];bb=[int(round(x*1e6))for x in old['b']];ends=[[int(round(x*1e6))for x in xy]for xy in axis];dx,dy=bb[0]-aa[0],bb[1]-aa[1];length2=dx*dx+dy*dy
 assert all((xy[0]-aa[0])*dy==(xy[1]-aa[1])*dx and 0<=(xy[0]-aa[0])*dx+(xy[1]-aa[1])*dy<=length2 for xy in ends)
 uidnew,ch=identity.serial_segment(SENSE,'B.Cu',*axis,.2);chunks[uidnew]=ch;tracks.append({'uuid':uidnew,'net':identity.raw(SENSE),'layer':'B.Cu','a':axis[0],'b':axis[1],'w':.2});terminalLedger.append({'old_UUID':uid,'old_chunk_sha256':K.C.sha(iv[3][uid]),'new_UUID':uidnew,'old_native_axis_IU':[aa,bb],'retained_terminal_axis_IU':ends,'equal_signed_native_width_IU':200000,'exact_native_capsule_subset':True,'old_F_B_annuli_and_flags_must_remain_naturally_active':True,'new_actual_In2_annulus_native_proof':'OPEN','inherited_raw_body_reference_failures_not_waived':True})
put(out/'exact-original-B-terminal-subset-and-required-native-masks.json',terminalLedger)
ground_ok=route_attachments('moved-pulldown-real-F-ground',GND,'F.Cu',refs['In1.Cu'],newsh['2'].buffer(-.04,quad_segs=128),groundF.buffer(-.02,quad_segs=128),tracks)
gate_ok=route_attachments('GATE-saved-two-original-chunk-F-detour',GATE,'F.Cu',refs['In1.Cu'],Point(228.85,155.75),Point(229.95,156.25),tracks)
senseAllowed=unary_union(senseOwn);senseRef=refs['In1.Cu'].union(senseAllowed)
sense_ok=route_attachments('SENSE-F-In2-F-existing-native-barrels-same-In1-proposal',SENSE,'In2.Cu',senseRef,Point(senseVias[0]['x'],senseVias[0]['y']),Point(senseVias[1]['x'],senseVias[1]['y']),tracks,qualified_new_own=senseAllowed)
pairRows=[]
for sig,ret in[(newvias[0],next(v for v in h['vias']if v['uuid']=='b88b7a49-a1ea-458a-9195-d0a46a3a7f66')),(newvias[1],newvias[2])]:
 ann=K.Z.bounded_disk(ret,ret['d']/2).difference(K.Z.bounded_disk(ret,ret['drill']/2));spacing=math.dist([sig['x'],sig['y']],[ret['x'],ret['y']]);contact={l:ann.buffer(-.025,quad_segs=128).intersection(refs[l]).area for l in refs};pairRows.append({'signal':sig['uuid'],'return':ret['uuid'],'spacing_mm':spacing,'operator_window_mm':[.90,1.0],'after_finite_nominal_source_reference_contact_mm2':contact,'PASS':.90<=spacing<=1.0 and all(a>.002 for a in contact.values()),'native_full_source_and_mask_gates':'OPEN'})
put(out/'two-Q0-actual-return-nominations.json',pairRows);assert all(r['PASS']for r in pairRows)
def newOwn(v,plane):
 cuts=[K.Z.bounded_disk(o,.1 if K.L.norm(o['net'])==GND else .525)for o in newvias if o['uuid']!=v['uuid']]
 return K.Z.bounded_disk(v,.525).intersection(oldrefs[plane]).difference(unary_union(cuts))
qown={p:unary_union([newOwn(v,p)for v in newvias[:2]])for p in('In1.Cu','In4.Cu')};qref={p:refs[p].union(qown[p])for p in qown}
qsource=route_attachments('Q0-F-saved-upper-port-source',NET,'F.Cu',qref['In1.Cu'],signalF.buffer(-.04,quad_segs=128),Point(sites[0][2]),tracks,qualified_new_own=qown['In1.Cu'])
qtransport=route_attachments('Q0-In3-common-transport',NET,'In3.Cu',qref['In4.Cu'],Point(sites[0][2]),Point(sites[1][2]),tracks,qualified_new_own=qown['In4.Cu'])
qtarget=route_attachments('Q0-F-saved-target-moved-R10016',NET,'F.Cu',qref['In1.Cu'],Point(sites[1][2]),newsh['1'].buffer(-.04,quad_segs=128),tracks,qualified_new_own=qown['In1.Cu'])
identity.assert_chunks(chunks)
for uid,ch in chunks.items():(out/(uid+'.segment-chunk')).write_bytes(ch)
for uid,ch in deleted.items():(out/(uid+'.exact-owned-delete-chunk')).write_bytes(ch)
put(out/'path-nominations.json',pathrows);results={'real_ground':ground_ok,'GATE_F_detour':gate_ok,'SENSE_existing_In2':sense_ok,'Q0_F_source':qsource,'Q0_In3':qtransport,'Q0_F_target':qtarget};packet={'tracks':tracks,'new_vias':newvias,'deleted_tracks':sorted(delete),'R10016_translation_mm':[-.5,-.5],'new_pad_shapes':newsh,'existing_SENSE_vias':senseVias,'existing_SENSE_required_old_masks':['F.Cu','B.Cu'],'existing_SENSE_new_natural_masks':['In2.Cu'],'same_plane_source_and_finite_continuity_proposal':'OPEN','full_gates_OPEN':True};pp=out/'sparse-nomination.pkl';pp.write_bytes(pickle.dumps(packet,protocol=5))
result={'verdict':'CONCRETE_SAVED_Q0_GATE_SENSE_PATH_NOMINATION_ALL_INDEPENDENT_GATES_OPEN'if all(results.values())else'EXACT_SAVED_Q0_GATE_SENSE_CONSTRUCTOR_INCOMPLETE','results':results,'model_file':str(model),'model_sha256':sha(model),'source_file':str(source),'source_sha256':sha(source),'operator_file':str(operator),'operator_sha256':sha(operator),'sparse_packet_file':str(pp),'sparse_packet_sha256':sha(pp),'original_track_deletes':sorted(delete),'old_POWER_FLT_all_native_discrete_Cu_exact_retained':True,'new_track_count':len(tracks),'new_ordinary_via_count':len(newvias),'maximum_signal_legs':3,'inherited_SAME_PLANE_blanket_checker_failures_preserved_and_scoped_proof_OPEN':True,'all_raw_R155_R368_R442_CORE_ROOT42_current_native_failures_preserved':True,'native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'results':results,'tracks':len(tracks)}),flush=True)
