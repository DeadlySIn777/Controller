"""Diagnostic only: test whether three retained MON segments form the cage."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;old=H/'construct_AO1_VREF_ONLY_NEW_native_intent_r4.generated.py';text=old.read_text()
text=text.replace('AO1-VREF-ONLY-NEW-native-intent-current-port-constructor-r4','AO1-MON-three-locked-segment-counterfactual-VREF-port-r9').replace('AO1_R4_','AO1_R9_')
target="saved=pickle.loads(cp.read_bytes());c=saved['full_before'];local=saved['current'];refs="
replacement="""saved=pickle.loads(cp.read_bytes());c=saved['full_before'];local=saved['current'];MON_REM={'6b5d7465-3e16-4492-82be-cd9ae2fb2ad5','e0c09d60-50a7-411e-9a56-ce39e23f1bff','16ac4bda-32bd-47a3-8cc4-404758a78d41'};originalmon=[t for t in local['tracks']if t['uuid']in MON_REM];assert len(originalmon)==3 and all(t['net']=='/motherboard_analog_output/AO1_MON_12V'and t['layer']=='F.Cu'and t['w']==.2 for t in originalmon);local={**local,'tracks':[t for t in local['tracks']if t['uuid']not in MON_REM]};put('three-original-MON-segments-diagnostic-removal-NOT_REPAIR.json',originalmon);refs="""
assert target in text;text=text.replace(target,replacement)
text=text.replace("'deleted_original_chunks':{},'selected':selected", "'deleted_original_chunks':{},'selected':selected,'diagnostic_only_original_MON3_omitted_from_guard_context':sorted(MON_REM),'coupled_monitor_replacement_REQUIRED_before_any_candidate_or_adoption':True")
text=text.replace("'deleted_or_moved_original_Cu':0", "'deleted_or_moved_original_Cu':0,'DIAGNOSTIC_ONLY_counterfactual_omitted_original_MON3':sorted(MON_REM),'full_MON_replacement_contact_reference_mandatory':True")
text=text.replace("'ONLY_NEW_VREF_POLICY_PORT_AND_F_B_PATH_CONSTRUCTED_ALL_REQUALIFICATION_OPEN'", "'DIAGNOSTIC_MON3_COUNTERFACTUAL_OPENS_VREF_PORT_MON_CONTINUITY_NOT_REPAIRED'")
dest=H/'construct_AO1_MINIMAL_MON3_counterfactual_r9.generated.py';assert not dest.exists();dest.write_text(text)
(H/'AO1-MON3-counterfactual-r9-derivation.json').write_text(json.dumps({'source_SHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'generated_SHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'guard_context_omits_original_MON3_for_necessity_only':True,'any_candidate_or_adoption':False},indent=1)+'\n')
exec(compile(text,str(dest),'exec'),{'__file__':str(dest),'__name__':'__main__'})
