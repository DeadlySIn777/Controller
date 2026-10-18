from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
p=H/'audit_AO1_two_ground_additions_joint_R20_current_r654.py';s=p.read_text()
old="[('AO1-COM-actual-SOURCE-to-U14623-9-B-Cu-finite-ground-bridge-r650/only-NEW-COM-B-Cu-ground-tracks-NOMINEE.pkl','148e8734780eb501c45711b971c785a2a054b2924f6f9c1ee378f0bc931d1f9e'),('AO1-COM-actual-SOURCE-to-U14636-3-F-Cu-finite-ground-bridge-r652/only-NEW-COM-F-Cu-ground-tracks-NOMINEE.pkl','95661ff14556f9c45f93231e6c10c34ae9e500e6ea269d90e2b07e0ecbeab5f0')]"
new="[('AO1-COM-seven-only-NEW-ground-tracks-local-inside-margin-repair-and-widths-r656/only-seven-NEW-COM-ground-tracks-inside-margin-repaired-widths-NOMINEE.pkl','cb36851a8df37c5e197cea6c8a4de7720ed7e8ec19543ba9a03a5c3b17f1b1b3')]"
replacements=[(old,new),('AO1-R650-R652-eight-GROUND-additions-joint-R20-independent-source-geometry-r654','AO1-R656-seven-GROUND-additions-joint-R20-independent-source-geometry-r658'),('len(tracks)==len(chunks)==8','len(tracks)==len(chunks)==7'),("assert t['w']==.20","assert t['w']in(.20,.30,.50)"),("'new_ground_tracks':8","'new_ground_tracks':7"),("'candidate_widening_is_not_applied':True","'widening_applied_only_on_individually_guarded_NEW_tracks':True"),('EIGHT_ADDITIVE','SEVEN_ADDITIVE'),('R654_COMPLETE','R658_COMPLETE'),('R20-plus-only-eight-ground','R20-plus-only-seven-ground')]
for a,b in replacements:
 assert s.count(a)==(2 if a=='EIGHT_ADDITIVE'else 1),(a,s.count(a));s=s.replace(a,b)
s=s.replace('eight additive GROUND','seven additive GROUND').replace('the eight named tracks','the seven named tracks')
out=H/'audit_AO1_repaired_seven_ground_additions_joint_R20_current_r658.generated.py';assert not out.exists();out.write_text(s)
(H/'derive-AO1-ground-independent-r658.json').write_text(json.dumps({'source':str(p.resolve()),'source_SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'generated':str(out.resolve()),'generated_SHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'exact_changes':replacements},indent=1)+'\n')
