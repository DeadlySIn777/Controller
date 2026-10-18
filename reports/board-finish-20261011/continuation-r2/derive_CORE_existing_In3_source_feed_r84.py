"""Investigate the original actual In3 source port on the latest exact positive joint head."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
folder=H/'joint-positive-head-signal-reference-mask-proposal-r83';rp=folder/'receipt.json';r=json.loads(rp.read_bytes());assert r['verdict']=='EXACT_REMOVE_ONLY_MASKS_REBASED_SOURCE_REPAIR_REQUIRED_NOT_ACCEPTED'and r['new_In2_flash_hypothesis_EXCLUDED']and not r['host_retention_and_adoption_flags'];mp=folder/'model.pkl';assert sha(mp)==r['model_sha256']
src=H/'repair_CORE_In2_owned_ground_feed_r80.py';dst=H/'repair_CORE_existing_In3_source_feed_r84.py';assert not dst.exists();s=src.read_text().replace('CORE-In2-owned-ground-feed-r80','CORE-existing-In3-source-feed-r84').replace('r80/','r84/').replace('R80_','R84_')
def sub(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
sub("assert sha(mp)==r['model_sha256']=='f8c15f8501c5ef15b7257b88cfd33ac1f275e225e69dac49b38cac9d4fb61394' and sha(mr)=='b459e4240bdcf6c518f9b4fb165645ff93c04cf6b80cd784541483d5ba7bbc51'", "assert sha(mp)==r['model_sha256']=='"+sha(mp)+"' and sha(mr)=='"+sha(rp)+"'")
s=s.replace("LAYERS=('In2.Cu',)","LAYERS=('In3.Cu',)").replace("layer=='In2.Cu'and q['uuid']=='6b1d4fb8-c0e5-531b-acf4-26ef99b34597'","layer=='In3.Cu'and q['uuid']=='47888e35-9a96-5393-b579-7c0b4a64ec93'")
s=s.replace("q['layer']=='In2.Cu'","q['layer']=='In3.Cu'").replace("q['uuid']!='6b1d4fb8-c0e5-531b-acf4-26ef99b34597'","q['uuid']!='47888e35-9a96-5393-b579-7c0b4a64ec93'").replace('bounded-new-owned-In2-ground-remove-only-ledger','bounded-new-owned-In3-ground-remove-only-ledger').replace('only_one_new_owned_LG_In2','only_one_new_owned_LG_In3')
sub("hard_h={**h,'tracks':h['tracks']+peerd['tracks'],'vias':h['vias']+peerd['vias']}", """assert {q['uuid']for q in peerd['tracks']}<={q['uuid']for q in h['tracks']}and {q['uuid']for q in peerd['vias']}<={q['uuid']for q in h['vias']};hard_h=h
 # Exact current R214/R201 canonical IO3 groups in zones are authoritative. Do not re-harden superseded R172 thin previews.
 assert any(q['uuid']=='ba9d5c62-8882-505e-a190-2a1ba940719b'and q['layer']=='In3.Cu'and q['net']=='/IO_3V3'for q in zones);iohard=[]""")
sub("[('/LOGIC_GND','J11001'),('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005')]:", "[('/LOGIC_GND','J11001'),('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005'),('/IO_3V3','R18001'),('/mc_local_power/CORE_5V','R11022')]:")
compile(s,str(dst),'exec');dst.write_text(s)
(H/'CORE-existing-In3-source-feed-r84-derivation.json').write_text(json.dumps({'prior_constructor_sha256':sha(src),'derived_constructor_sha256':sha(dst),'current_exact_joint_mask_model_sha256':sha(mp),'scope':'Actual original f6In3 source Cu to actual21pad/main COREgroup, exactR214current h and latestR201canonicalIO3 hard. Only NEWLGIn3 group47888 may receive bounded remove-only notch. Existing native barrels/hole/poses/masks unchanged; no newIn2 hypothesis. All5prior ground/power sources, full77contact/reference/geometry/PDN/native required.','full_fitted_CORE1V2_load_A':.8,'R80_In2_failure_preserved':True,'native_jobs':0,'adopted':False},indent=1)+'\n');print(dst)
