"""Derive guarded existing-annulus repairs for the current composed head."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;p=H/'repair_protected_field_returns_r2.py';out=H/'repair_protected_field_returns_r3.py';assert not out.exists()
s=p.read_text().replace('import zone_projection_r1 as N','import guarded_declared_settings_projection_r58 as N\nfrom guarded_declared_settings_projection_r58 import bounded_buffer,bounded_disk')
s=s.replace("OUT=H/'protected-field-return-restoration-r2'","OUT=H/'protected-field-return-restoration-r3'")
begin=s.index('    precise=');end=s.index('    rec,_=F.build',begin)
s=s[:begin]+"    zones,initial_guards=N.normalize_owned_via_guards(h,zones);current,initial_fill_retreats=N.projected(old,h,zones)\n"+s[end:]
s=s.replace("q['shape'].buffer(gap(q['net'])+.025)","bounded_buffer(q['shape'],max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025)")
s=s.replace("s.buffer(.275)","bounded_buffer(s,.275)")
s=s.replace("Point(v['x'],v['y']).buffer(v['drill']/2+.275,quad_segs=32)","bounded_disk(v,v['drill']/2+.275)")
s=s.replace("s.buffer(.025)","bounded_buffer(s,.025)")
s=s.replace("sorted(options,key=lambda q:(-q[2],q[0]))","sorted(options,key=lambda q:(q[0],-q[2]))")
needle="                try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))\n                except (AssertionError,ValueError):continue"
assert s.count(needle)==1
s=s.replace(needle,"                chord=LineString([start,end])\n                if part.covers(chord):points=list(chord.coords);search={'method':'exact_covered_nearest_chord'}\n                else:\n                    try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))\n                    except (AssertionError,ValueError):continue")
needle="                trial,cuts=N.projected(old,h,zones+adds+[z]);gs=F.graph(trial,net);"
assert s.count(needle)==1
s=s.replace(needle,"                guarded,via_guards=N.normalize_owned_via_guards(h,zones+adds+[z]);z=next(q for q in guarded if q['uuid']==uid);trial,cuts=N.projected(old,h,guarded);gs=F.graph(trial,net);")
s=s.replace("'search':search};attempted.append(record)","'search':search,'new_outward_via_guards':via_guards};attempted.append(record)")
s=s.replace("'board_written':False,'native_jobs':0,'adopted':False}","'initial_outward_owned_via_guards':initial_guards,'initial_old_fill_retreats':initial_fill_retreats,'script_sha256':sha(Path(__file__)),'finite_construction_search_not_no_path_proof':True,'current_width_barrel_thermal_mesh_qualification':'OPEN','board_written':False,'native_jobs':0,'adopted':False}")
compile(s,str(out),'exec');out.write_text(s)
r=H/'protected-field-return-r3-derivation.json';assert not r.exists();r.write_text(json.dumps({'prior_script_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'derived_script_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'latest_input_is_explicit_argument_and_adjacent_receipt_model_pin':True,'existing_actual_annuli_only':True,'declared_settings_outward_guarded_projection':True,'all_target_and_prior_root_contacts_required_after_each_full_projection':True,'global_or_simplified_finite_search_failure_is_not_proof_of_no_path':True,'old_native_outlines_and_all_discrete_preserved':True,'all_native_current_and_final_mutual_gates':'OPEN'},indent=1)+'\n')
print(json.dumps({'script':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
