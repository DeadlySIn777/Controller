"""Bind the corrected seven-track R656 ground peer, preserving R21 scope."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;old=H/'audit_AO1_R20_R650_R652_joint_new_Cu_r21.py';text=old.read_text()
text=text.replace('AO1-R20-two-ground-peer-packets-joint-new-Cu-r21','AO1-R20-repaired-R656-seven-ground-peer-joint-new-Cu-r25')
start=text.index("sources=[('R650'");end=text.index(';peer=[];metadata=[]',start)
text=text[:start]+"sources=[('R656',H/'AO1-COM-seven-only-NEW-ground-tracks-local-inside-margin-repair-and-widths-r656/only-seven-NEW-COM-ground-tracks-inside-margin-repaired-widths-NOMINEE.pkl','cb36851a') ]"+text[end:]
text=text.replace("t['w']==.2", "t['w']in(.2,.3,.5)").replace('EIGHT_PEER_GROUND_TRACKS','SEVEN_REPAIRED_PEER_GROUND_TRACKS')
dest=H/'audit_AO1_R20_R656_ground_peer_true_new_Cu_r25.generated.py';assert not dest.exists();dest.write_text(text)
(H/'AO1-r25-current-ground-peer-schema-update.json').write_text(json.dumps({'source_SHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'generated_SHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'old_R650_R652_peer_review_preserved':True,'new_peer_full_SHA256':'cb36851a8df37c5e197cea6c8a4de7720ed7e8ec19543ba9a03a5c3b17f1b1b3','native_jobs':0},indent=1)+'\n')
exec(compile(text,str(dest),'exec'),{'__file__':str(dest),'__name__':'__main__'})
