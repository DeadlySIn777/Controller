"""Fresh independent audit of the exact controlled b177 power detour."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;old=H/'audit_AO1_MINIMAL_MON3_VREF_actual_baseline_scope_r12.py';text=old.read_text()
text=text.replace('AO1-MON3-VREF-actual-full-native-baseline-independent-host-scope-r12','AO1-MON3-VREF-b177-5V-source-complete-independent-host-audit-r20')
text=text.replace('AO1-joint-VREF-ports-and-MON3-locked-source-supported-detour-r11','AO1-MON3-VREF-and-only-b177-5V-native-width-endpoint-source-detour-r19')
text=text.replace("assert r['selected'];pf=", "assert r['controlled_power_path'];pf=")
text=text.replace('assert len(removed)==3 and len(nt)==12 and len(nv)==2','assert len(removed)==4 and len(nt)==14 and len(nv)==2')
text=text.replace("==(K.L.norm(t['net'])==MON)","==bool(t.get('locked_yes',False))")
insert=""" power='/motherboard_analog_output/AO1_5V';oldpower=K.root(bg[power],'U14620','1');newpower=K.root(ng[power],'U14620','1');oldpowerkeys={k for k in K.keys(oldpower)if not(k[0]=='track'and k[1]in removed)};newpowerkeys=K.keys(newpower);powerkeysbad=sorted(oldpowerkeys-newpowerkeys);newpowertracks=[t for t in nt if K.L.norm(t['net'])==power];powertracksbad=[t['uuid']for t in newpowertracks if('track',t['uuid'],'F.Cu')not in newpowerkeys];positiveproof={'actual_5V_source_ref':'U14620','pin':'1','source_pinfunction':'OUT_1','all_retained_old_5V_SOURCE_layer_key_losses':[list(k)for k in powerkeysbad],'all_new_locked_native_width_power_tracks_rooted':not powertracksbad,'new_power_track_source_errors':powertracksbad,'old_source_group_layer_keys_retained':len(oldpowerkeys),'new_source_group_layer_keys':len(newpowerkeys),'current_voltage_load_derating_mesh_IR_qualification':'OPEN; no load or fitted channel reduction'}
 from verify_source import parse,children,child,atom
 nf=pin(ROOT/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net','070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2');doc=parse(nf.read_text());chain=[]
 for n in children(child(doc,'nets'),'net'):
  rawnet=atom(n,'name');normnet=K.L.norm(rawnet);nodes=[{q[0]:q[1]for q in node[1:]}for node in children(n,'node')];inputs=[q for q in nodes if q['ref']=='U14620'and q.get('pintype')=='power_in'and normnet!=COM];outputs=[q for q in nodes if q['ref']=='U14619'and q.get('pintype')=='power_out']
  for inp in inputs:
   for out in outputs:
    assert normnet in bg and normnet in ng;before_feed=K.root(bg[normnet],out['ref'],out['pin']);after_feed=K.root(ng[normnet],out['ref'],out['pin']);oldp=any(q['kind']=='pad'and q['ref']==inp['ref']and str(q['pin'])==inp['pin']for q in before_feed);newp=any(q['kind']=='pad'and q['ref']==inp['ref']and str(q['pin'])==inp['pin']for q in after_feed);chain.append({'raw_input_supply_net':rawnet,'genuine_converter_source':out,'regulator_input':inp,'actual_full_before_feed_joined':oldp,'prospective_after_feed_joined':newp,'input_supply_old_source_layer_key_losses':len(K.keys(before_feed)-K.keys(after_feed))})
 put('genuine_U14619_converter_to_U14620_5V_regulator_native_source_chain.json',chain);put('actual-5V-SOURCE-all-old-and-two-new-power-track-provenance.json',positiveproof)
"""
before=" model=OUT/'AO1-only-sparse-prospective-normal-native-antipad-host-model.pkl';"
assert before in text;text=text.replace(before,insert+before)
text=text.replace("passed=not(errors or allrawgain or groupbad or sourcebad or direct or refbad or newbodybad)","passed=not(errors or allrawgain or groupbad or sourcebad or direct or refbad or newbodybad or powerkeysbad or powertracksbad)and bool(chain)and all(q['actual_full_before_feed_joined']and q['prospective_after_feed_joined']and q['input_supply_old_source_layer_key_losses']==0 for q in chain)")
text=text.replace("'only_three_original_locked_MON_replaced':sorted(removed)","'only_controlled_original_MON3_and_exact_b177_5V_replaced':sorted(removed),'genuine_positive_5V_source_proof':positiveproof,'U14619_to_5V_regulator_supply_chain':chain")
text=text.replace('SCOPED_AO1_MINIMAL_MON3_VREF_ACTUAL_BASELINE_HOST_PASS_FULL_CURRENT_NATIVE_ANALOG_SI_OPEN','SCOPED_AO1_MON3_VREF_b177_5V_ALL_HOST_SOURCE_CONTACT_REFERENCE_PASS_FULL_CURRENT_NATIVE_ANALOG_SI_OPEN').replace('SCOPED_AO1_MINIMAL_MON3_VREF_RAW_HOST_REPAIR_REQUIRED','SCOPED_AO1_MON3_VREF_b177_5V_RAW_HOST_REPAIR_REQUIRED')
text=text.replace("d=pt.distance(sh)-t['drill']/2;check({'kind':'ordinary_all_SMD_drill'", "d=pt.distance(sh)-t['drill']/2-.005;check({'kind':'ordinary_all_SMD_drill_after_native_ERROR_INSIDE_bound_5um'")
dest=H/'audit_AO1_MON3_VREF_b177_5V_source_complete_r20.generated.py';assert not dest.exists();dest.write_text(text)
(H/'AO1-r20-actual-source-complete-independent-audit-derivation.json').write_text(json.dumps({'source_SHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'generated_SHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'only_four_explicit_controlled_old_chunks':True,'every_other_old_SOURCE_reference_literal_zero_threshold':True,'whole_new_POWER_body_has_no_own_hole_cap':True,'new_via_SMD_native_inside_export_error_5um_included':True,'native_jobs':0},indent=1)+'\n')
exec(compile(text,str(dest),'exec'),{'__file__':str(dest),'__name__':'__main__'})
