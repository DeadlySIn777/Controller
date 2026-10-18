"""Allow one bounded owned CORE exit with exact source retention gates."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent
s=(H/'construct_major_rail_prioritized_extra_source_r117.py').read_text()
def replace(old,new):
    global s
    assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
replace("OUT=H/'sbc-power/major-rail-prioritized-extra-source-feeds-r117';", "OUT=H/'sbc-power/major-rail-coupled-source-exit-feeds-r121';")
replace(" hole_tree=STRtree([s for raw,s in all_holes]);adds=[];rows=[];attempts=[];bank_proofs=[]", """ hole_tree=STRtree([s for raw,s in all_holes]);adds=[];rows=[];attempts=[];bank_proofs=[];carves=[]
 coupled_uid='c7e36847-4380-503d-80f2-836420105d9e';core_raw='/mc_local_power{slash}CORE_5V';core_net=C.norm(core_raw)
 escape=set_precision(box(233.212,91.61,239.212,97.61),1e-6)
 assert next(q for q in zones if q['uuid']==coupled_uid)['net']==core_raw
 def exact_source(model,net,ref,pin):
  import io3_contact_restore_r2 as Q
  Q.NET=net;gs,parts,assignment=Q.groups(model,return_details=True)
  rr=next(xs for xs in gs if any((r['ref'],r['pad'])==(ref,pin) for r in xs));return {r['uuid'] for r in rr},parts,assignment
 core_selected={**h,'zones':[q for q in h['zones'] if q['net']==core_raw]}
 core_baseline,_=N.projected(old,core_selected,zones)
 core_prior_exact,_,_=exact_source(core_baseline,core_net,'R11022','2')
 core_source_projection=core_baseline
 print('COUPLED_SOURCE_EXIT_BASELINE_CORE_EXACT_CONTACTS',len(core_prior_exact),flush=True)""")
replace("   for q in zones+adds+peer_zones:\n    if q['layer']==layer and q['net']!=raw and search.intersects(q['shape']):obs.append(N.bounded_buffer(q['shape'],max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025+.000020))", """   for q in zones+adds+peer_zones:
    if q['layer']==layer and q['net']!=raw and search.intersects(q['shape']):
     obstruction=q['shape']
     if net=='/CORE_1V2' and layer=='In4.Cu' and q['uuid']==coupled_uid:obstruction=obstruction.difference(escape)
     obs.append(N.bounded_buffer(obstruction,max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025+.000020))""")
replace("     selected={**h,'zones':[q for q in h['zones'] if q['net']==raw]}\n     trial,retreat=N.projected(old,selected,zones+adds+[z]);joined=pads(root(F.graph(trial,net),ref))", """     proposed_base=list(zones);carve=None
     if net=='/CORE_1V2' and layer=='In4.Cu':
      oldq=next(q for q in zones if q['uuid']==coupled_uid)
      distance=max(gap(core_raw),float(oldq.get('clearance_mm',.15)),float(z.get('clearance_mm',.15)))+.025+.000020
      cutter=N.bounded_buffer(z['shape'],distance)
      removed=oldq['shape'].intersection(cutter)
      if not removed.is_empty:
       # A bounded source exit can alter this one NEW owned plane only.
       if not escape.covers(removed):continue
       before=oldq['shape'];before_outline=oldq.get('zone_outline_shape',before)
       after=set_precision(set_precision(before,1e-6).difference(cutter),1e-6);after_outline=set_precision(set_precision(before_outline,1e-6).difference(cutter),1e-6)
       if after.is_empty or not escape.covers(before_outline.difference(after_outline)):continue
       newq={**oldq,'shape':after,'zone_outline_shape':after_outline,'precarve_route_minimum_cross_section_and_current_must_be_requalified':True}
       proposed_base=[newq if q['uuid']==coupled_uid else q for q in zones]
       carve={'zone_UUID':coupled_uid,'raw_net':core_raw,'layer':layer,'physical_before_SHA256':N.digest(before),'physical_after_SHA256':N.digest(after),'outline_before_SHA256':N.digest(before_outline),'outline_after_SHA256':N.digest(after_outline),'physical_removed_mm2':before.difference(after).area,'physical_quantization_added_mm2':after.difference(before).area,'outline_removed_mm2':before_outline.difference(after_outline).area,'outline_quantization_added_mm2':after_outline.difference(before_outline).area,'bounded_exit_scope_WKB_SHA256':N.digest(escape),'exact_outward_cutter_WKB_SHA256':N.digest(cutter),'original_native_zone_definitions_unchanged':True}
     selected={**h,'zones':[q for q in h['zones'] if q['net']==raw]}
     trial,retreat=N.projected(old,selected,proposed_base+adds+[z]);joined=pads(root(F.graph(trial,net),ref))""")
replace("'outward_pad_guards_with_explicit_20nm_construction_reserve':pad_guard};attempts.append(record)", "'outward_pad_guards_with_explicit_20nm_construction_reserve':pad_guard,'bounded_new_owned_CORE_source_exit_carve':carve};attempts.append(record)")
replace("     adds.append(z);source_projection=trial;accepted_targets.append(target);answer=record;print('RETURN_ROOTED',net,vid,layer,line.length,width,flush=True);break", """     exact_joined,_,_=exact_source(trial,net,ref,'2')
     if not target<=exact_joined or not retained<=exact_joined:record['exact_integer_source_gate']='FAIL';continue
     core_trial,_=N.projected(old,core_selected,proposed_base+adds+[z])
     core_exact,core_parts,core_assignment=exact_source(core_trial,core_net,'R11022','2')
     if not core_prior_exact<=core_exact:record['CORE_source_contacts_lost']=sorted(core_prior_exact-core_exact);continue
     # Each component of every retained/new CORE proposal must remain rooted,
     # including pad-free pieces after the owned notch.
     import io3_contact_restore_r2 as Q
     Q.NET=core_net;core_groups,core_parts,core_assignment=Q.groups(core_trial,return_details=True)
     core_root_index=next(i for i,xs in enumerate(core_groups) if any((r['ref'],r['pad'])==('R11022','2') for r in xs))
     floating=[]
     for cq in proposed_base+adds:
      if C.norm(cq['net'])!=core_net:continue
      for part in polys(cq['shape']):
       hits={a for piece,a in zip(core_parts[cq['layer']],core_assignment[cq['layer']]) if piece.intersection(part).area>0}
       if hits!={core_root_index}:floating.append({'UUID':cq['uuid'],'area_mm2':part.area,'groups':list(hits)})
     if floating:record['CORE_detached_new_components']=floating;continue
     record['exact_integer_source_gate']='PASS';record['all_prior_CORE_exact_pad_track_via_contacts_source_retained']=True
     if carve:
      folder=OUT/('accepted-carve-'+str(len(carves)+1));folder.mkdir()
      for label,sh in [('physical-before',before),('physical-after',after),('outline-before',before_outline),('outline-after',after_outline),('cutter',cutter),('bounded-exit-scope',escape)]:
       file=folder/(label+'.wkb');file.write_bytes(sh.wkb)
      write(folder/'ledger.json',carve);carves.append(carve)
     zones=proposed_base;adds.append(z);source_projection=trial;core_source_projection=core_trial;accepted_targets.append(target);answer=record;legal_cache.clear()
     snapshot=OUT/('accepted-positive-snapshot-'+str(len(adds)));snapshot.mkdir();(snapshot/'new-feed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5));(snapshot/'all-owned-zones-with-carves.pkl').write_bytes(pickle.dumps(zones+adds,protocol=5));write(snapshot/'receipt.json',{'verdict':'EXACT_INTEGER_1V2_AND_CORE_SOURCE_CONTACT_CONSTRUCTION_NATIVE_CURRENT_FOREIGN_GATES_OPEN','row':record,'new_feed_zones_sha256':sha(snapshot/'new-feed-zones.pkl'),'all_owned_zones_with_carves_sha256':sha(snapshot/'all-owned-zones-with-carves.pkl'),'prospective_source_extra_flash_requires_native_refill':True,'native_jobs':0,'board_written':False})
     print('COUPLED_MAJOR_RAIL_ROOTED',net,vid,layer,line.length,width,'exact COREcontacts',len(core_exact),flush=True);break""")
replace("  source_zones={q['uuid']:", "  core_source_zones={q['uuid']:(q['net'],q['fills']) for q in core_source_projection['zones'] if q['net']==core_raw};core_full_zones={q['uuid']:(q['net'],q['fills']) for q in current['zones'] if q['net']==core_raw};assert core_source_zones==core_full_zones,'CORE source-only and full projection disagree'\n  source_zones={q['uuid']:")
replace("controller-major-rail-prioritized-extra-source-r117/", "controller-major-rail-coupled-source-exit-r121/")
replace("'label':'Major rail prioritized prospective extra-source-layer feed R117'", "'label':'Major rail coupled bounded owned source exit R121'")
replace("'hard_only_peer_proposals':peer_bindings", "'hard_only_peer_proposals':peer_bindings,'explicit_bounded_new_CORE_carve_ledger':carves")
replace("print('MAJOR_RAIL_PRIORITIZED_EXTRA_SOURCE_R117_FROZEN'", "print('MAJOR_RAIL_COUPLED_SOURCE_R121_FROZEN'")
out=H/'construct_major_rail_coupled_source_exit_r121.py';assert not out.exists();out.write_text(s);compile(s,str(out),'exec')
print('COUPLED_SOURCE_EXIT_DERIVED',hashlib.sha256(out.read_bytes()).hexdigest())
