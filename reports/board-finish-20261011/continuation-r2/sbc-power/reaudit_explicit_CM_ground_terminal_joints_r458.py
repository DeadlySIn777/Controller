"""Fresh full joint replay after explicit ONLY_NEW terminal joints."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'audit_joint_CM_ground_source_before_and_true_guards_r454.py').read_text(encoding='utf-8')
s=s.replace('CM51-fresh-joint-alternate-ground-analytic-guards-and-finite-SOURCE-before-graph-r454','CM51-explicit-terminal-joints-fresh-true-guards-and-SOURCE-before-graph-r458')
s=s.replace("moved=alt['moved_original_barrel'];items=nt+nv+[moved]","repairdir=P/'CM51-explicit-only-NEW-ground-terminal-joints-and-named-R450-path-r457';repairfile=repairdir/'only-NEW-six-terminal-joint-repairs-one-path-ownership.pkl';repair=pickle.loads(repairfile.read_bytes());retired=set(repair['retired_ONLY_NEW_tracks']);assert retired<={t['uuid']for t in nt};nt=[t for t in nt if t['uuid']not in retired]+repair['replacement_ONLY_NEW_tracks'];c['tracks']=[t for t in c['tracks']if t['uuid']not in retired]+repair['replacement_ONLY_NEW_tracks'];moved=alt['moved_original_barrel'];items=nt+nv+[moved]")
old="            if owned:continue\n            d=ax.distance(sh)"
new="""            if not owned and not via:
                for ownpath in repair['exact_whole_terminal_path_ownership']:
                    if uid!=ownpath['via_UUID']or it['uuid']not in ownpath['tracks']:continue
                    pathtracks=[t for t in nt if t['uuid']in ownpath['tracks']];assert len(pathtracks)==len(ownpath['tracks']);pathbody=unary_union([LineString([t['a'],t['b']]).buffer(t['w']/2,quad_segs=128)for t in pathtracks]);op=Point(owner['x'],owner['y']);ann=op.buffer(owner['d']/2,quad_segs=128).difference(sh);outside=pathbody.difference(op.buffer(ownpath['owncap_radius_mm'],quad_segs=128));clear=None if outside.is_empty else outside.distance(sh);assert pathbody.intersection(ann).area>0 and(clear is None or clear>=.28);owned=True;terminal.append({'track_UUID':it['uuid'],'exact_owned_terminal_via_UUID':uid,'cap_radius_mm':ownpath['owncap_radius_mm'],'explicit_named_whole_R450_terminal_path':ownpath['tracks'],'finite_whole_path_own_annulus_contact_mm2':pathbody.intersection(ann).area,'outside_cap_whole_path_drill_gap_mm':clear})
            if owned:continue
            d=ax.distance(sh)"""
assert old in s;s=s.replace(old,new)
s=s.replace("'physical_requirement_mm':req-.025","'physical_requirement_mm':(.275 if kind in {'every_other_physical_drill','new_drill_to_actual_SMD'}else .8 if kind=='ordinary_via_pitch'else req-.025)")
s=s.replace("'retired_only_prospective_track':'65f3a90e-a953-5caa-8493-4623cfc05f2f'","'retired_only_prospective_tracks':['65f3a90e-a953-5caa-8493-4623cfc05f2f']+sorted(retired),'R457_controlled_terminal_packet_SHA256':sha(repairfile),'raw_R454_drill_deficits_preserved':True")
s=s.replace("'R454_ANALYTIC'","'R458_ANALYTIC'").replace("'R454_COMPLETE'","'R458_COMPLETE'")
E=P/'exact-expanded-explicit-CM-terminal-joint-reaudit-r458.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8');exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
