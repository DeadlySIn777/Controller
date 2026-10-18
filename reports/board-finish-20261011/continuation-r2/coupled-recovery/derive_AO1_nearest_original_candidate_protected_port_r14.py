"""Refine only-new candidate positions near the preserved R11 point."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;old=H/'search_AO1_MINIMAL_MON3_VREF_old_body_protected_r13.generated.py';text=old.read_text()
text=text.replace('AO1-joint-MON3-VREF-port-all-retained-old-source-bodies-protected-r13','AO1-joint-MON3-VREF-original-nearby-protected-source-port-r14').replace('AO1_R13_','AO1_R14_')
text=text.replace("for desired in([372.8,130.5],[373.7,131.3],[376.6,129]):", "for desired in([376.258442,126.817934],[376.158442,126.917934],[376.008442,126.867934],[376.158442,127.067934],[372.8,130.5],[373.7,131.3],[376.6,129]):")
text=text.replace("for at in sites(sgregion,desired):", "for at in sites(sgregion.buffer(-.000010),desired):")
dest=H/'search_AO1_MINIMAL_MON3_VREF_refined_protected_ports_r14.generated.py';assert not dest.exists();dest.write_text(text)
(H/'AO1-r14-saved-point-refinement-derivation.json').write_text(json.dumps({'source_SHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'generated_SHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'only_new_sg_site_candidates_refined':True,'old_source_no_loss_scope_and_native_antipad_policy_unchanged':True},indent=1)+'\n')
exec(compile(text,str(dest),'exec'),{'__file__':str(dest),'__name__':'__main__'})
