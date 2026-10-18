"""Preserve R12 real 5V-reference FAIL and protect all retained old bodies."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;old=H/'search_AO1_coupled_MON3_VREF_joint_ports_r11.py';text=old.read_text()
text=text.replace('AO1-joint-VREF-ports-and-MON3-locked-source-supported-detour-r11','AO1-joint-MON3-VREF-port-all-retained-old-source-bodies-protected-r13').replace('AO1_R11_','AO1_R13_')
before="ep=[375.498,129.0];ats=[]"
insert="""ep=[375.498,129.0];ats=[]
 oldrefprotected=[];protected=[]
 radius=max(float(z['clearance_mm']) for z in c['zones']if K.L.norm(z['net'])==COM)+.25+.000005
 for t in c['tracks']:
  ly=t['layer'];net=K.L.norm(t['net'])
  if t['uuid']in DELS or net==COM or c['domains_normalized'].get(net)!=c['domains_normalized'][COM]or ly not in K.MAP:continue
  body=K.L.body(t)
  if body.envelope.disjoint(win.buffer(1)):continue
  covered=body.intersection(refs[K.MAP[ly]])
  if covered.is_empty:continue
  obstacle=K.Z.bounded_buffer(covered,radius);protected.append(obstacle);oldrefprotected.append({'old_UUID':t['uuid'],'raw_net':t['net'],'body_layer':ly,'SOURCE_reference_layer':K.MAP[ly],'native_normal_new_SG_cut_radius_with_guard_mm':radius,'covered_body_WKB_SHA256':hashlib.sha256(covered.wkb).hexdigest(),'protected_obstacle_WKB_SHA256':hashlib.sha256(obstacle.wkb).hexdigest()})
 beforeports=sgregion;sgregion=sgregion.difference(unary_union(protected));put('all-current-retained-old-SOURCE-body-new-SG-antipad-port-protection.json',oldrefprotected)
 put('old-source-body-protected-port-summary.json',{'protected_body_count':len(oldrefprotected),'before_area_mm2':beforeports.area,'after_area_mm2':sgregion.area,'original_5V_b17752d1_raw_R12_loss_held_mm2':.011436208194387076,'old_SOURCE_contact_or_area_threshold_waivers':0})
"""
assert before in text;text=text.replace(before,insert)
text=text.replace("'all_source_old_contacts_refs_true_caps_native_current_analog_SI_gates':'OPEN'", "'all_source_old_contacts_refs_true_caps_native_current_analog_SI_gates':'OPEN','every_retained_old_source_body_now_protected_from_new_SG_native_antipad':True,'raw_R12_real_5V_loss_preserved':True")
dest=H/'search_AO1_MINIMAL_MON3_VREF_old_body_protected_r13.generated.py';assert not dest.exists();dest.write_text(text)
(H/'AO1-R13-old-body-protection-derivation.json').write_text(json.dumps({'source_SHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'generated_SHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'changes_only_new_VREF_port_search':True,'original_SDI_5V_and_MON3_endpoint_contract_unchanged':True,'raw_R12_FAIL_receipt_preserved':True},indent=1)+'\n')
exec(compile(text,str(dest),'exec'),{'__file__':str(dest),'__name__':'__main__'})
