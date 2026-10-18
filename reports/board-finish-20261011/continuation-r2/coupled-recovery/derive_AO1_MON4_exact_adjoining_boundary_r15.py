"""Counterfactual through the next real original locked MON segment only."""
from pathlib import Path
import json,hashlib,pickle,math
H=Path(__file__).resolve().parent;old=H/'construct_AO1_MINIMAL_MON3_counterfactual_r9.generated.py';text=old.read_text()
text=text.replace('AO1-MON-three-locked-segment-counterfactual-VREF-port-r9','AO1-MON-four-adjoining-locked-segment-counterfactual-current-port-r15').replace('AO1_R9_','AO1_R15_')
text=text.replace("'16ac4bda-32bd-47a3-8cc4-404758a78d41'};originalmon", "'16ac4bda-32bd-47a3-8cc4-404758a78d41','6a7a6862-5b3a-4764-bead-1acf9ac7b861'};originalmon")
text=text.replace('assert len(originalmon)==3','assert len(originalmon)==4').replace('three-original-MON-segments-diagnostic-removal-NOT_REPAIR.json','four-adjoining-original-MON-segments-diagnostic-removal-NOT_REPAIR.json')
dest=H/'construct_AO1_MON4_adjoining_native_boundary_r15.generated.py';assert not dest.exists();dest.write_text(text)
context=pickle.loads((H/'AO1-saved-four-add-exact-current-native-screen-r1/pinned-current-local-Cu-native-before-source-only-screen.pkl').read_bytes());terminal=[375.25,130.049999]
near=[v for v in context['current_vias']if math.dist([v['x'],v['y']],terminal)<.000005]
oldseg=next(t for t in context['current']['tracks']if t['uuid']=='6a7a6862-5b3a-4764-bead-1acf9ac7b861');assert oldseg['net']=='/motherboard_analog_output/AO1_MON_12V'and oldseg['layer']=='F.Cu'and oldseg['w']==.2
(H/'AO1-MON4-adjoining-controlled-boundary-r15-derivation.json').write_text(json.dumps({'source_SHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'generated_SHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'fourth_exact_current_segment':oldseg,'next_real_native_terminal_mm':terminal,'actual_native_vias_at_next_terminal':near,'guard_context_change_only_for_owned_controlled_MON4_replacement':True,'native_jobs':0,'adopted':False},indent=1)+'\n')
exec(compile(text,str(dest),'exec'),{'__file__':str(dest),'__name__':'__main__'})
