"""Preserve R204 failure; include the discrete-only AUX net and late peer guards."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_R11054_exact_static_and_bleed_repair_r204.py').read_text(encoding='utf-8')
s=s.replace("R11054-static-and-bleed-full-contact-audit-r204","R11054-static-and-bleed-full-contact-audit-r205")
# AUX has no old fill. It still needs every retained discrete relationship checked.
s=s.replace("zoneset=sorted({C.norm(q['net']) for q in before['zones']})","zoneset=sorted({C.norm(q['net']) for q in before['zones']}|{'/motherboard_motors/AUX_5V_B'})")
# Extend only the true-geometry inventory, never the electrical/projected candidate.
geometry_inventory_patch=r'''analytic_h=copy.deepcopy(h)
 monitor=H.parent/'field-monitor-R9026-rotation-source-termination-r66/owned-delta.pkl';assert sha(monitor)=='2669504846249102a6afe479c78f627b7729d0992c48bc64f79a330f431149c5';md=pickle.loads(monitor.read_bytes());analytic_h['tracks']=[q for q in analytic_h['tracks'] if q['uuid']!=md['removed_old_track']['uuid']]+md['tracks'];analytic_h['vias']+=md['vias'];mp={q['uuid']:q for q in md['new_R9026_pads']};analytic_h['pads']=[mp.get(q['uuid'],q) for q in analytic_h['pads']]
 peerplanes=[];peerbindings=[]
 for path,expect in [(H.parent/'SAFE-logic-four-return-restoration-r55/proposed-zones.pkl','b0e3766d17138741ae1f4ab6d2a574e55da6634734b03bec93d6a6abb891e065'),(H.parent/'sbc-power/IO3-group6-wider-existing-port-r193/accepted-zones.pkl','01952e9a9374ac67da080769154bc828cfd6689bff207cb412d9a33d551e4362')]:
  assert sha(path)==expect;peerplanes+=pickle.loads(path.read_bytes());peerbindings.append({'file':str(path.resolve()),'sha256':expect,'hard_only_no_electrical_credit':True})
 analytic_z=z+peerplanes;write(O/'independent-late-peer-hard-bindings.json',{'planes':peerbindings,'R66_monitor_delta_SHA256':sha(monitor),'only_analytic_inventory_extended':True,'native_R66_pad_overlay_qualification_separate':True})
 rec,trees=F.build({**analytic_h,'zones':[]});tm={q['uuid']:q for q in analytic_h['tracks']};vm={q['uuid']:q for q in analytic_h['vias']};checks=[];errors=[]'''
inner_transform="\ns=s.replace("+repr("rec,trees=F.build({**h,'zones':[]});tm={q['uuid']:q for q in h['tracks']};vm={q['uuid']:q for q in h['vias']};checks=[];errors=[]")+","+repr(geometry_inventory_patch)+")\n"
for a,b in [('for q in z:\n   if q[\'layer\']!=l','for q in analytic_z:\n   if q[\'layer\']!=l'),('for pad in h[\'pads\']:', 'for pad in analytic_h[\'pads\']:'),('for other in h[\'vias\']:', 'for other in analytic_h[\'vias\']:'),('for peer in z:', 'for peer in analytic_z:')]:inner_transform+='s=s.replace('+repr(a)+','+repr(b)+')\n'
# R204's insertion point was inside the courtyard loop: remove repeated writes.
s=s.replace(" write(O/'analytic-checks.json',checks)"," write(O/'analytic-checks.json',checks)")
s=s.replace('R204 full candidate projection','R205 full candidate projection')
inner_transform+='s=s.replace('+repr("'board_written':False,'native_jobs':0")+','+repr("'discrete_only_AUX_relationship_scope_added':True,'independent_late_peer_geometry_bound':True,'R204_lookup_failure_preserved':True,'board_written':False,'native_jobs':0")+')\n'
s=s.replace('exec(compile(s,',inner_transform+'exec(compile(s,')
exec(compile(s,str(H/'audit_R11054_exact_static_and_bleed_repair_r204.py'),'exec'))
