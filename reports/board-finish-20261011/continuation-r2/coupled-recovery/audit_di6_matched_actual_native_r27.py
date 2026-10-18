"""Independent matched fresh-before/after DI6 reference/contact comparison.

Consumes native exports only; never invokes native tools, saves a board, or
attributes old stored-cache differences to the eleven-item repair.
"""
import sys,json,pickle,copy,math,time,collections
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import audit_c10036_r24_full_independent_r30 as Q
import audit_di6_actual_scoped_native_r19 as R19
import physical_reference_losses_r2 as RF
C,N=A.C,A.N
GROUND=R19.GROUND;NET=R19.NET

def rows_by_uuid(xs):
 d={q['uuid']:q for q in xs};assert len(d)==len(xs);return d
def contact_obligations(beforegroups,aftergroups):
 mapping=collections.defaultdict(set)
 for i,xs in enumerate(aftergroups):
  for k in Q.discrete_keys(xs):mapping[k].add(i)
 rows=[];losses=[]
 for i,xs in enumerate(beforegroups):
  keys=Q.discrete_keys(xs)
  parts=set().union(*(mapping.get(k,{'MISSING'}) for k in keys)) if keys else set()
  row={'before_group':i,'unchanged_discrete_keys':[list(k) for k in sorted(keys)],'after_components':sorted(str(p) for p in parts)};rows.append(row)
  if len(parts)>1 or 'MISSING' in parts:losses.append(row)
 return rows,losses
def main():
 started=time.monotonic();out=HERE/'di6-matched-actual-native-independent-r27.json';assert not out.exists()
 for p in(__file__,Q.__file__,R19.__file__,RF.__file__):A.read(p)
 r19p=HERE/'di6-actual-native-reference-independent-r19.json';r=json.loads(A.read(r19p));assert C.sha(A.read(r19p))=='db2452f3192ad4d7d0054144e44e03ce44ddf04279022ddb177b0e2480f3985d'
 r22p=HERE/'di6-native-existing-target-return-r22.json';r22=json.loads(A.read(r22p));assert C.sha(A.read(r22p))=='6bb5403004b11d997e867092c4362c78e7033230485d4e9d48409a770fc38ad1'
 assert r22['entire_gap_in_one_exact_current_same_net_attachment_void'] and r22['radius_expansion_mm']==0 and r22['all_other_eight_new_segment_native_reference_checks_pass']
 mr=A.read(r['saved_actual_model']);assert C.sha(mr)=='a70eee0497ea68a5673e49ec15ed5c6e6b184079f8fa761a34d7c80824daf26f';m=pickle.loads(mr);after=m['actual']
 bd=HERE.parent/'di6-matched-native-baseline-r1';ad=HERE.parent/'di6-native-diagnostic-r1'
 closed=json.loads(A.read(bd/'receipt-r2.json'));br=json.loads(A.read(bd/'scoped-native-fill/receipt.json'));ar=json.loads(A.read(ad/'scoped-native-fill/receipt.json'))
 assert closed['exact_same_source_pose_project_rules_and_fill_helper_as_after'] and closed['only_exact_DI6_11additions_absent'] and closed['same_selected_native_zone_UUIDs']
 assert C.sha(A.read(bd/'scoped-native-fill/receipt.json'))==closed['native_export_receipt_sha256']
 assert C.sha(A.read(ad/'scoped-native-fill/receipt.json'))==closed['after_native_export_receipt_sha256']
 for p,pin in closed['frozen_input_pins'].items():assert C.sha(A.read(p))==pin,p
 for receipt in(br,ar):
  assert receipt['verdict']=='PASS_SCOPED_LOGIC_GND_NATIVE_REFILL_EXPORT_RAW_COPPER' and receipt['filler_ok'] and receipt['all_discrete_post_fill_errors']==[] and receipt['selected_raw_net']==GROUND
  for p,pin in receipt['input_sha256'].items():assert C.sha(A.read(p))==pin,p
 bgraw=A.read(bd/'scoped-native-fill/geometry.json');agraw=A.read(ad/'scoped-native-fill/geometry.json');bfraw=A.read(bd/'scoped-native-fill/actual-via-flashes.json');afraw=A.read(ad/'scoped-native-fill/actual-via-flashes.json')
 assert C.sha(bgraw)==br['geometry_sha256']==closed['geometry_sha256']=='6a3fe096794534c5d1dd1c4802d8fd600dbc073c01a14754e723ff482469a8bd'
 assert C.sha(bfraw)==br['actual_via_flashes_sha256']==closed['actual_via_flashes_sha256']=='b81d50e210eca304ed0b9879f2c000fe3e49b8c00134ce3d1c787dfe1cf48a62'
 assert C.sha(agraw)==ar['geometry_sha256']==r['fresh_native_geometry_sha256'];assert C.sha(afraw)==ar['actual_via_flashes_sha256']==r['fresh_native_flashes_sha256']
 bg=json.loads(bgraw);ag=json.loads(agraw);bf=json.loads(bfraw)['vias'];af=json.loads(afraw)['vias']
 parent=A.read(bd/'copy/board.kicad_pcb');candidate=A.read(ad/'copy/board.kicad_pcb');assert C.sha(parent)==br['candidate_sha256']=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';assert C.sha(candidate)==ar['candidate_sha256']==r['native_candidate_sha256']
 ident=N.SourceNets(parent);ident.assert_no_collisions(candidate);bi=C.inventory(parent);ai=C.inventory(candidate);new={q['UUID'] for q in r['exact_new_native_discrete']};assert len(new)==11 and ai[0]==bi[0] and ai[2]==bi[2] and set(ai[3])==set(bi[3])|new and all(ai[3][u]==ch for u,ch in bi[3].items())
 for stem in('board.kicad_pro','board.kicad_dru'):assert A.read(bd/'copy'/stem)==A.read(ad/'copy'/stem)
 bt=rows_by_uuid(bg['tracks']);at=rows_by_uuid(ag['tracks']);bv=rows_by_uuid(bg['vias']);av=rows_by_uuid(ag['vias']);assert set(at)==set(bt)|(new&set(at));assert set(av)==set(bv)|(new&set(av));assert len(at)-len(bt)==9 and len(av)-len(bv)==2
 assert all(at[u]==t for u,t in bt.items());assert all(av[u]==v for u,v in bv.items());assert bg['pads']==ag['pads'];assert all(bf[u]==af[u] for u in bv),'Actual old via flash mask changed; explicit additional contact proof required'
 bz=rows_by_uuid(bg['zones']);az=rows_by_uuid(ag['zones']);assert set(bz)==set(az);selected=set(br['selected_zone_UUIDs']);assert selected==set(ar['selected_zone_UUIDs'])=={u for u,z in bz.items() if L.norm(z['net'])==GROUND}
 assert all(z==az[u] for u,z in bz.items() if u not in selected),'An unrefilled other-domain fill differs'
 before=copy.deepcopy(after);before['tracks']=[t for t in before['tracks'] if t['uuid'] not in new];before['vias']=[v for v in before['vias'] if v['uuid'] not in new]
 assert set(t['uuid'] for t in before['tracks'])==set(bt) and set(v['uuid'] for v in before['vias'])==set(bv)
 for t in before['tracks']:
  n=bt[t['uuid']];assert(t['net'],t['a'],t['b'],t['w'],t['layer'])==(n['net'],n['s'],n['e'],n['w'],n['layer'])
 for v in before['vias']:
  n=bv[v['uuid']];assert(v['net'],v['x'],v['y'],v['d'],v['drill'],v['flashed'])==(n['net'],n['at'][0],n['at'][1],n['w'],n['drill'],bf[v['uuid']])
 oldsettings={z['uuid']:z for z in before['zones'] if L.norm(z['net'])==GROUND};assert set(oldsettings)==selected
 before['zones']=[z for z in before['zones'] if L.norm(z['net'])!=GROUND]
 for u in sorted(selected):
  z=bz[u];s=oldsettings[u];before['zones'].append({'uuid':u,'net':z['net'],'fills':{l:A.polys(rs) for l,rs in z['fills'].items()},'clearance_mm':s['clearance_mm'],'priority':s['priority'],'native_actual_selected_refill':True})
 print('MATCHED_NATIVE_FRESH_BEFORE_PHYSICAL_ROOT',flush=True);bu,bgroups,broot,brefs=R19.root_refs(before);agroups=m['groups'];aroot=m['root'];arefs=m['root_reference']
 groundobligations,groundlosses=contact_obligations(bgroups,agroups)
 rootkeys=Q.discrete_keys(aroot);oldrootkeys=Q.discrete_keys(broot);oldrootloss=sorted(oldrootkeys-rootkeys)
 print('MATCHED_NATIVE_DI6_CONTACT_OBLIGATIONS',flush=True);su,sg=Q.physical(before,NET);sigobligations,siglosses=contact_obligations(sg,m['DI6_groups'])
 checkpoint=HERE/'di6-matched-native-r27-pre-reference-checkpoint.pkl';assert not checkpoint.exists();checkpoint.write_bytes(pickle.dumps({'before':before,'after':after,'before_groups':bgroups,'before_root':broot,'before_refs':brefs,'after_groups':agroups,'after_root':aroot,'after_refs':arefs,'ground_obligations':groundobligations,'ground_losses':groundlosses,'DI6_obligations':sigobligations,'DI6_losses':siglosses,'old_root_key_losses':oldrootloss},protocol=5))
 print('MATCHED_NATIVE_PRE_REFERENCE_CHECKPOINT',C.sha(checkpoint.read_bytes()),flush=True)
 losses,proof=RF.audit(before,brefs,arefs,GROUND)
 passed=not(groundlosses or siglosses or oldrootloss or losses) and r['actual_DI6_source_target_same_group'] and r22['entire_gap_in_one_exact_current_same_net_attachment_void']
 saved=HERE/'di6-matched-native-r27-model.pkl';assert not saved.exists();saved.write_bytes(pickle.dumps({'before':before,'after':after,'before_groups':bgroups,'before_root':broot,'before_refs':brefs,'after_groups':agroups,'after_root':aroot,'after_refs':arefs},protocol=5))
 report={'verdict':'MATCHED_FRESH_NATIVE_DI6_REFERENCE_CONTACT_RETURN_PASS_FINAL_PDN_OPEN' if passed else'MATCHED_FRESH_NATIVE_DI6_REFERENCE_OR_CONTACT_OPEN','scope':'Exact eedf before vs exact eedf+11 DI6 items after; identical source footprint chunks/project/rules/filler, LOGIC_GND fills freshly computed separately; other fills unchanged and unvalidated','native_before_board_sha256':C.sha(parent),'native_after_board_sha256':C.sha(candidate),'before_geometry_sha256':C.sha(bgraw),'after_geometry_sha256':C.sha(agraw),'before_flash_sha256':C.sha(bfraw),'after_flash_sha256':C.sha(afraw),'exact_11_adds_0_deletes_no_FP_rule_source_change':True,'all_old_native_tracks_vias_IU_raw_net_and_actual_flash_masks_unchanged':True,'all_native_pad_poses_nets_layers_polygons_unchanged':True,'all_non_LOGIC_GND_exported_fills_identical_unvalidated':True,'unchanged_other_net_contact_proof':'No removed/changed discrete bodies, holes or actual via flashes; no other-net fill delta. Every non-DI6/non-GND contact geometry is identical. DI6/GND physical groups separately audited.','actual_before_GND_pad_groups':sum(any(q['kind']=='pad' for q in xs) for xs in bgroups),'actual_after_GND_pad_groups':r['actual_GND_pad_groups'],'actual_before_source_rooted_pad_count':len({q['uuid'] for q in broot if q['kind']=='pad'}),'actual_after_source_rooted_pad_count':r['actual_source_rooted_pad_count'],'every_old_GND_contact_obligation':groundobligations,'GND_contact_losses':groundlosses,'every_old_DI6_contact_obligation':sigobligations,'DI6_contact_losses':siglosses,'old_source_root_discrete_key_losses':[list(k) for k in oldrootloss],'all_retained_neighbor_reference_losses':losses,'exact_reference_delta_proof':proof,'new_nine_body_reference_and_source_target_pair_authority_R19_sha256':C.sha(A.read(r19p)),'exact_existing_same_net_target_575000_IU_qualification_R22_sha256':C.sha(A.read(r22p)),'target_new_transition_added':False,'no_In1_target_credit_claimed':True,'old_cache_comparison_separately_preserved':'R19 2748 old198b-cache to actual-after reference differences remain historical diagnostic evidence, not attributed to DI6 and not waived by this matched comparison','immutable_pre_reference_checkpoint_sha256':C.sha(checkpoint.read_bytes()),'saved_matched_actual_model':str(saved),'saved_matched_actual_model_sha256':C.sha(saved.read_bytes()),'allboard_source_current_r06_r07_fullDRC_SI_latest_R78_field_FG_C_AO_composition':'OPEN','board_written':False,'native_jobs':0,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started}
 for p,pin in A.READS.items():assert C.sha(Path(p).read_bytes())==pin,p
 out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'receipt':str(out),'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'GND_contact_losses':len(groundlosses),'DI6_contact_losses':len(siglosses),'source_root_losses':len(oldrootloss),'reference_losses':len(losses),'delta_proof':proof}),flush=True)
if __name__=='__main__':main()
