"""Use exact adjoining MON4 boundary with old SOURCE-body protection."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;old=H/'search_AO1_MINIMAL_MON3_VREF_refined_protected_ports_r14.generated.py';text=old.read_text()
text=text.replace('AO1-joint-MON3-VREF-original-nearby-protected-source-port-r14','AO1-joint-MON4-adjoining-boundary-all-old-source-body-protected-r16').replace('AO1_R14_','AO1_R16_')
text=text.replace('AO1-MON-three-locked-segment-counterfactual-VREF-port-r9','AO1-MON-four-adjoining-locked-segment-counterfactual-current-port-r15')
text=text.replace("'16ac4bda-32bd-47a3-8cc4-404758a78d41'}", "'16ac4bda-32bd-47a3-8cc4-404758a78d41','6a7a6862-5b3a-4764-bead-1acf9ac7b861'}")
text=text.replace('end=[374.55,130.049999]','end=[375.25,130.049999]')
text=text.replace('MON3','MON4').replace('MON3','MON4').replace('MON3','MON4')
dest=H/'search_AO1_MON4_source_body_protected_joint_r16.generated.py';assert not dest.exists();dest.write_text(text)
(H/'AO1-r16-adjoining-MON4-source-preserving-scope-derivation.json').write_text(json.dumps({'source_SHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'generated_SHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'owned_original_MON_segments':4,'next_exact_preserved_terminal_mm':[375.25,130.049999],'native_jobs':0,'adopted':False},indent=1)+'\n')
exec(compile(text,str(dest),'exec'),{'__file__':str(dest),'__name__':'__main__'})
