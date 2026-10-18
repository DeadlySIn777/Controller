"""Route only newly found legal pad poses; do not repeat completed pose searches."""
from pathlib import Path
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/nominate_R371_R7035_valid_rigid_poses_routed_actual_network_terminal_reconnect_r384.py'
s=p.read_text(encoding='utf-8').replace('r384','r386').replace('R384','R386')
s=s.replace('nomination-r383','nomination-r385')
s=s.replace("assert sha(N/'receipt.json')=='aef70c55db2f8736825d84135706c8b9385fbc82047aacf5f6d89269f830df8e'", "assert (N/'receipt.json').exists()")
s=s.replace('assert len(poses)==2','assert poses')
s=s.replace('clip=envelope;obs=[]', 'clip=envelope;obs=[]')
s=s.replace("'R383_receipt_sha256':sha(N/'receipt.json')", "'R385_receipt_sha256':sha(N/'receipt.json')")
s=s.replace("'NO_ACTUAL_F_SOURCE_REFERENCE_RECONNECT_IN_TWO_PAD_LEGAL_RIGID_POSES_DECLARED_WINDOW'", "'NO_ACTUAL_F_SOURCE_REFERENCE_RECONNECT_IN_ADDITIONAL_PAD_LEGAL_RIGID_POSES_DECLARED_WINDOW'")
s=s.replace('for pi,pose in enumerate(poses):','fixedNativeCuts={};fixedHoleCuts={}\n for pi,pose in enumerate(poses):')
start=s.index("    for j in trees['F.Cu'].query(clip.buffer(1),predicate='intersects'):")
end=s.index('    for np in moved.values():',start)
block=s[start:end].replace('obs.append','fixed.append')
wrapped="    if net not in fixedNativeCuts:\n     fixed=[]\n"+''.join(' '+line if line.strip()else line for line in block.splitlines(keepends=True))+"     fixedNativeCuts[net]=unary_union(fixed)\n    obs.append(fixedNativeCuts[net])\n"
s=s[:start]+wrapped+s[end:]
start=s.index("    for j in ht.query(clip.buffer(1),predicate='intersects'):")
end=s.index('    obs.append(Z.bounded_buffer(gp,.525))',start)
block=s[start:end].replace('obs.append','fixed.append')
wrapped="    if ownvia not in fixedHoleCuts:\n     fixed=[]\n"+''.join(' '+line if line.strip()else line for line in block.splitlines(keepends=True))+"     fixedHoleCuts[ownvia]=unary_union(fixed)\n    obs.append(fixedHoleCuts[ownvia])\n"
s=s[:start]+wrapped+s[end:]
s=s.replace("p=moved[pin];net=L.norm(p['old']['net']);end=p['xy'];candidates=targets(component,Point(*end));success=None", "p=moved[pin];net=L.norm(p['old']['net']);end=p['xy'];direct_contacts=[{'UUID':rr['uuid'],'kind':rr['kind'],'actual_positive_overlap_mm2':p['shape'].intersection(rr['shape']).area}for rr in component if rr['layer']=='F.Cu'and rr['uuid']not in own and p['shape'].intersects(rr['shape'])]\n   if any(rr['actual_positive_overlap_mm2']>0 for rr in direct_contacts):\n    attempts.append({'pose':pose['host_rigid_pose_deg_dx_dy'],'pin':pin,'actual_old_source_component_request':requestIndex,'already_positive_contact_to_old_actual_component_Cu':direct_contacts,'new_tracks_required':0});put(O/'finite-actual-old-Cu-source-reference-reconnect-attempts.json',attempts);continue\n   candidates=targets(component,Point(*end));success=None")
(H/'sbc-power/exact-expanded-additional-R7035-network-route-with-fixed-mask-cache-r386.py').write_text(s,encoding='utf-8')
exec(compile(s,str(__file__),'exec'))
