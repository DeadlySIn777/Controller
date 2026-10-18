"""Full .90-1.0 window overbound and exact own-new DIC blocker diagnosis."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'nominate_DIC_second_return_continuous_saved_window_r396.py'
code=base.read_text().replace('DIC-second-return-continuous-saved-window-r396','DIC-second-return-full-window-owned-blockers-r412')
old="ring=Point(sig['x'],sig['y']).buffer(.997,quad_segs=256).difference(Point(sig['x'],sig['y']).buffer(.903,quad_segs=256))"
new="ring=K.Z.bounded_disk(sig,1.0).difference(Point(sig['x'],sig['y']).buffer(.90,quad_segs=256))"
assert old in code;code=code.replace(old,new)
old="physical=ring.difference(unary_union(obs));final=physical.difference(unary_union(refObstacles));"
new="""physical=ring.difference(unary_union(obs));final=physical.difference(unary_union(refObstacles));
DIC='/motherboard_io_control/DIC_IOL1_CS_MCU';newDIC={t['uuid']for t in h['tracks']+h['vias']if K.L.norm(t['net'])==DIC and t['uuid']not in iv[3]};assert len(ledger)<=len(obs)
ownedIndices={i for i,row in enumerate(ledger)if row['uuid']in newDIC};withoutOwned=ring.difference(unary_union([sh for i,sh in enumerate(obs)if i not in ownedIndices]));(out/'full-window-with-only-own-new-DIC-copper-withdrawn.wkb').write_bytes(withoutOwned.wkb)
ownrows=[]
for i in sorted(ownedIndices):
 other=ring.difference(unary_union([sh for j,sh in enumerate(obs)if j!=i]));ownrows.append({**ledger[i],'actual_current_only_this_own_new_cutter_withdrawn_legal_mm2':other.area,'actual_current_only_this_own_new_cutter_withdrawn_legal_empty':other.is_empty})
sites=[]
for part in K.RF.parts(withoutOwned.buffer(-.002,quad_segs=128)):
 for pt in [part.representative_point(),nearest_points(Point(old['x'],old['y']),part)[1]]:
  at=[round(x,6)for x in pt.coords[0]];pp=Point(at)
  if not withoutOwned.covers(pp)or not .90<=pp.distance(Point(sig['x'],sig['y']))<=1:continue
  ann=pp.buffer(.25,quad_segs=128).difference(pp.buffer(.1,quad_segs=128));witness={l:ann.buffer(-.025,quad_segs=128).intersection(ref).area for l,ref in sourceRefs.items()};blockers=[ledger[i]for i in sorted(ownedIndices)if obs[i].covers(pp)];sites.append({'xy_mm':at,'spacing_mm':pp.distance(Point(sig['x'],sig['y'])),'actual_before_J1_source_annular_interior_mm2':witness,'new_DIC_copper_blockers':blockers,'new_ground_drill_retained_current_reference_conflict':any(sh.covers(pp)for sh in refObstacles),'source_local_nomination_pass':all(x>.005 for x in witness.values())})
put(out/'full-window-own-new-copper-diagnosis.json',{'full_saved_window_outer_bounded_circle_inner_inscribed_circle_overbound':True,'full_window_raw_legal_area_mm2':physical.area,'full_window_raw_legal_empty':physical.is_empty,'only_own_unadopted_new_DIC_discrete_UUIDs':sorted(newDIC),'only_own_unadopted_new_DIC_foreign_Cu_cutters_withdrawn_legal_area_mm2':withoutOwned.area,'only_own_unadopted_new_DIC_foreign_Cu_cutters_withdrawn_legal_empty':withoutOwned.is_empty,'own_cutter_single_withdrawal_rows':ownrows,'possible_return_sites_for_bounded_new_DIC_reroute':sites,'all_original_and_power_Cu_remain_hard':True,'raw_designated_pair_FAILURE_and_native_jobs_unchanged':True})
"""
assert old in code;code=code.replace(old,new).replace("'window_mm':[.903,.997]","'window_mm':[.90,1.0]");exec(compile(code,str(base),'exec'))
