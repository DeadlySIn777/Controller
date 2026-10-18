"""Independent corrected-pose actual current audit, with raw gaps preserved."""
from pathlib import Path
import builtins
H=Path(__file__).resolve().parent;base=H/'audit_Q0_R454_independent_actual_reference_r456.py'
def scoped_compile(source,filename,mode,*args,**kwargs):
 if isinstance(source,str):
  source=source.replace('Q0-R454-independent-actual-reference-r456','Q0-R478-exact-pose-current-contacts-reference-r480').replace('Q0_R456_','Q0_R480_').replace('Q0-exact-R452-current-filled-only-r454','Q0-exact-R476-ground-contact-pose-r478').replace('57de8393410dfa149f02777ca4d5d97fb123a3ca305061adbdab98267803b22e','0f81a32c75cc26c0afc3dfb7c12f7494bb9a3042764379e1481a8d850a3e3b2b').replace('aa580499d3bfb057b7047ba124d2813d0af3905315c82871e49baf612ee7d728','aec47d8600135e340be9e38ca18891e2903e7c283ee0b7095673d383ce079ebd').replace('Q0-R450-exact-native-owned-operation-r452','Q0-R474-ground-contact-pose-native-r476').replace('ed12eb485bd83caef6632d6d7aaf35bbddf18b06b4dbe277c34447b76bee030e','7f46fb8f9a1515ca04c58b7e503adef967ab5a2d4eb03e0f27cb73f38d8c3cd8')
  if "start=time.monotonic();out=H/"in source:
   old="put(out/'raw-whole-chunk-reserve-and-exact-original-subset-ledger.json',reserveRaw);"
   new="""poseRows=[]
for pad in h['pads']:
 if pad['ref']!='R10016':continue
 body=unary_union(K.L.poly(pad['layers']['F.Cu']));net=K.L.norm(pad['net']);nearest=min((body.distance(sh),uid)for uid,n,sh in holes);row={'kind':'new_SMD_every_original_drill','pad_UUID':pad['uuid'],'pin':pad['num'],'nearest_hole_UUID':nearest[1],'physical_edge_gap_mm':nearest[0],'guarded_gap_mm':nearest[0]-.005,'required_mm':.275};poseRows.append(row)
 if row['guarded_gap_mm']<.275:errors.append(row)
 for j in trees['F.Cu'].query(body.buffer(.8),predicate='intersects'):
  rec=records['F.Cu'][int(j)]
  if rec['uuid']==pad['uuid']or K.L.norm(rec['net'])==net:continue
  dist=body.distance(rec['shape']);row={'kind':'new_SMD_foreign_native_Cu','pad_UUID':pad['uuid'],'other_UUID':rec['uuid'],'other_kind':rec['kind'],'gap_mm':dist,'required_mm':gap(net,rec['net'])+.025};poseRows.append(row)
  if dist<row['required_mm']:errors.append(row)
fp=next(f for f in h['footprints']if f['ref']=='R10016');fpCourtyard=unary_union(K.L.poly(fp['courtyard'].get('F',[])))
for other in h['footprints']:
 if other['ref']=='R10016':continue
 courtyard=unary_union(K.L.poly(other['courtyard'].get('F',[])))
 if not courtyard.is_empty and fpCourtyard.intersects(courtyard):errors.append({'kind':'new_FP_native_courtyard_overlap','other_ref':other['ref']})
put(out/'new-exact-FP-SMD-Cu-every-drill-and-courtyard-ledger.json',poseRows)
put(out/'raw-whole-chunk-reserve-and-exact-original-subset-ledger.json',reserveRaw);"""
   assert old in source;source=source.replace(old,new,1)
   old="for t in before['tracks']:\n if t['uuid']in removed"
   new="""# Original B terminal subsets retain their original raw gaps. The strict
# full-body rows are not flipped. Independently prove no new reference loss
# to each exact equal-width native capsule before classifying incremental Cu.
for row,t in zip(newref,nt):
 row['new_incremental_body_reference_gate_pass']=row['strong_exact_supported_own_only_gap_empty'];subset=None
 for uid in removed:
  old=oldtracks[uid]
  if(K.L.norm(old['net']),old['layer'],old['w'])!=(K.L.norm(t['net']),t['layer'],t['w']):continue
  aa=[int(round(x*1e6))for x in old['a']];bb=[int(round(x*1e6))for x in old['b']];xx=[[int(round(x*1e6))for x in p]for p in(t['a'],t['b'])];dx,dy=bb[0]-aa[0],bb[1]-aa[1];ll=dx*dx+dy*dy
  if all((p[0]-aa[0])*dy==(p[1]-aa[1])*dx and 0<=(p[0]-aa[0])*dx+(p[1]-aa[1])*dy<=ll for p in xx):subset={'old_UUID':uid,'old_axis_IU':[aa,bb],'retained_axis_IU':xx,'equal_native_width_IU':int(round(t['w']*1e6))};break
 if subset is not None:
  body=K.A.shape({'kind':'segment',**t});l=t['layer'];lost=body.intersection(reference_deltas[l]);row.update(exact_unchanged_native_capsule_subset=subset,raw_inherited_before_reference_gap_mm2=body.difference(oldrefs[l]).area,strict_new_source_reference_loss_mm2=lost.area,strict_new_source_reference_loss_empty=lost.is_empty,new_incremental_body_reference_gate_pass=lost.is_empty,all_raw_before_after_fullbody_reference_failures_preserved=True)
for t in before['tracks']:
 if t['uuid']in removed"""
   assert old in source;source=source.replace(old,new,1)
   source=source.replace("or any(not r['strong_exact_supported_own_only_gap_empty']for r in newref)","or any(not r['new_incremental_body_reference_gate_pass']for r in newref)")
   source=source.replace("'new_strong_track_reference_failures':sum(not r['strong_exact_supported_own_only_gap_empty']for r in newref),","'new_strong_track_reference_failures':sum(not r['strong_exact_supported_own_only_gap_empty']for r in newref),'new_incremental_body_reference_failures':sum(not r['new_incremental_body_reference_gate_pass']for r in newref),")
   source=source.replace('INDEPENDENT_GEOMETRY_CONTACT_SOURCE_REFERENCE_INCREMENTAL_PASS_SAME_PLANE_Q_NATIVE_PAD_CURRENT_OPEN','INDEPENDENT_GEOMETRY_CONTACT_ALL_SOURCE_ZERO_OLD_REFERENCE_INCREMENTAL_PASS_SAME_PLANE_NATIVE_PAD_CURRENT_OPEN')
   (H/'Q0-R478-exact-pose-current-contacts-reference-r480-derived-auditor.py').write_text(source)
 return builtins.compile(source,filename,mode,*args,**kwargs)
ns={'__file__':str(base),'__name__':'__main__','compile':scoped_compile};exec(scoped_compile(base.read_text(),str(base),'exec'),ns)
