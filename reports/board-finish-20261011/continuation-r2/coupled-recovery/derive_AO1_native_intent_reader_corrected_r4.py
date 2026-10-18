"""Correct a local profile variable collision; exact geometry unchanged."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent
old=H/'construct_AO1_VREF_ONLY_NEW_native_intent_r3.generated.py';text=old.read_text()
out=H/'AO1-VREF-ONLY-NEW-native-intent-current-port-constructor-r3';assert out.exists()and not(out/'receipt.json').exists()
(out/'reader-failure.json').write_text(json.dumps({'status':'VARIABLE_NAME_READER_FAILURE_BEFORE_CANDIDATE_EMISSION','reason':'Parsed native clearance local float shadowed the current local geometry dictionary','native_jobs':0,'adopted':False},indent=1)+'\n')
text=text.replace('AO1-VREF-ONLY-NEW-native-intent-current-port-constructor-r3','AO1-VREF-ONLY-NEW-native-intent-current-port-constructor-r4').replace('AO1_R3_','AO1_R4_')
text=text.replace("local=float(atom(child(a,'connect_pads'),'clearance'));row=", "zoneclear=float(atom(child(a,'connect_pads'),'clearance'));row=").replace("'clearance_mm':local,'shape':shape,'native_chunk_SHA256'", "'clearance_mm':zoneclear,'shape':shape,'native_chunk_SHA256'")
dest=H/'construct_AO1_VREF_ONLY_NEW_native_intent_r4.generated.py';assert not dest.exists();dest.write_text(text)
(H/'AO1-constructor-r4-reader-correction.json').write_text(json.dumps({'source_SHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'generated_SHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'failure_preserved':str(out/'reader-failure.json'),'geometry_or_policy_changes':0},indent=1)+'\n')
exec(compile(text,str(dest),'exec'),{'__file__':str(dest),'__name__':'__main__'})
