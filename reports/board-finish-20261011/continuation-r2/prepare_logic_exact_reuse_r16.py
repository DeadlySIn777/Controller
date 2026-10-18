"""Reuse unchanged source fills/graphs within a return bank; compare full GP58.

No h Cu, pad, hole or foreign plane changes during this constructor. Adding
same-raw-net return shapes cannot change the source-zone cutter set. The final
fresh full GP58 bank equality and source retention assertions remain mandatory.
"""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=H/'repair_logic_lazy_existing_returns_r12.py';o=H/'repair_logic_exact_reuse_returns_r16.py';assert not o.exists()
s=p.read_text()
changes={"OUT=H/'logic-lazy-existing-return-restoration-r12'":"OUT=H/'logic-exact-reuse-return-restoration-r16'","'controller-logic-existing-return-r12/'":"'controller-logic-exact-reuse-return-r16/'",'Logic existing-annulus return continuation R12':'Logic unchanged-source graph/fill reuse return R16','LOGIC_RETURN_R12_FROZEN':'LOGIC_RETURN_R16_FROZEN',"accepted_targets=[];source_projection=current":"accepted_targets=[];source_projection=current;groups_cache=initial", "   gs=F.graph(source_projection,net);rr=root(gs,ref);retained=pads(rr)":"   gs=groups_cache;rr=root(gs,ref);retained=pads(rr)"}
for a,b in changes.items():assert s.count(a)==1,a;s=s.replace(a,b)
a="     selected={**h,'zones':[q for q in h['zones'] if q['net']==raw]}\n     trial,retreat=N.projected(old,selected,zones+adds+[z]);joined=pads(root(F.graph(trial,net),ref))"
b="""     # No foreign cutter or h geometry changed. Original source-zone fills
     # from the current full GP58 projection are immutable within this bank.
     # Append exactly GP58's owned-source-row representation; prove equality
     # to a fresh ALL-net full GP58 projection again at bank completion.
     newrow=N.projected(old,{**h,'zones':[]},[z])[0]['zones']
     trial={**h,'zones':[q for q in source_projection['zones']if q['net']==raw]+newrow}
     trial_groups=F.graph(trial,net);joined=pads(root(trial_groups,ref))"""
assert s.count(a)==1;s=s.replace(a,b)
a="adds.append(z);source_projection=trial;accepted_targets.append(target)";b="adds.append(z);source_projection=trial;groups_cache=trial_groups;accepted_targets.append(target)";assert s.count(a)==1;s=s.replace(a,b)
compile(s,str(o),'exec');o.write_text(s)
(H/'logic-exact-reuse-returns-r16-derivation.json').write_text(json.dumps({'source_file':str(p),'source_sha256':sha(p),'derived_file':str(o),'derived_sha256':sha(o),'only_unchanged_graph_and_source_fill_reuse_with_same_raw_source_owned_row_appends':True,'h_Cu_pad_hole_foreign_plane_geometry_immutable_within_bank':True,'literal_fresh_all_net_GP58_source_zone_fill_equality_and_actual_all_prior_target_source_contacts_still_mandatory':True,'no_buffer_operator_grid_clearance_rule_or_reference_tolerance_changes':True,'all_mutual_current_native_reference_gates':'OPEN','native_jobs':0,'board_written':False},indent=1)+'\n')
print(json.dumps({'script':str(o),'sha256':sha(o)}))
