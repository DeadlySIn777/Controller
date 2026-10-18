"""Reuse the saved bounded existing-port constructor for an explicit extra-In2 hypothesis."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
parent=H/'CORE-source-existing-barrel-In2-hypothesis-r77';rp=parent/'receipt.json';r=json.loads(rp.read_bytes());assert r['verdict']=='EXPLICIT_In2_HOST_HYPOTHESIS_SOURCE4_FAIL_PRESERVED_FEED_CONSTRUCTION_REQUIRED'and r['source_rooted_named_pads']==4 and r['old_source_pad_loss_still_unresolved']==21
mp=parent/'model.pkl';assert sha(mp)==r['model_sha256'];src=H/'repair_CORE_reference_safe_feeds_r65.py';dst=H/'repair_CORE_In2_existing_port_feed_r79.py';assert not dst.exists();s=src.read_text().replace('SAFE-CORE1V2-reference-safe-feed-restoration-r65','CORE-In2-existing-port-feed-r79').replace('r65/','r79/').replace(' R65',' R79')
a="assert sha(mp)==r['model_sha256']=='05c4fa70e4472c7f684e9ada8f72a48a7422dbc6af115c75f3b581be07dd9fc1' and sha(mr)=='423119130f248520dc10477141032e1504a14e403d144bc8e9e6cdd357205c39'";assert s.count(a)==1;s=s.replace(a,"assert sha(mp)==r['model_sha256']=='"+sha(mp)+"' and sha(mr)=='"+sha(rp)+"'")
a="LAYERS=('In4.Cu','In2.Cu','In3.Cu','In1.Cu')";assert s.count(a)==1;s=s.replace(a,"LAYERS=('In2.Cu',)")
a="logic_reference={l:unary_union([q['shape']for q in logic_root if q['kind']=='fill'and q['layer']==l])for l in ('In1.Cu','In4.Cu')}";assert s.count(a)==1
# Reference masks already repaired in R74 remain fully hard; the feed is only on In2.
s=s.replace(a,"logic_reference={l:unary_union([q['shape']for q in logic_root if q['kind']=='fill'and q['layer']==l])for l in ('In1.Cu','In4.Cu')}")
a="for width in (2.,1.,.5,.35,.25):";assert s.count(a)==1;s=s.replace(a,"for width in (4.,3.,2.,1.,.5,.35,.25):")
a="iohard=pickle.loads(iofile.read_bytes())";assert s.count(a)==1;s=s.replace(a,"""iohard=pickle.loads(iofile.read_bytes())
 fieldpacket=H/'field-power/SAFE-U10017-wider-native-owned-recipe-r183';assert sha(fieldpacket/'receipt.json')=='00c4e035dc2f95f6a4e5560ec00d1393763b4386cfead6e1a104af1bdbaf123d';fr=json.loads((fieldpacket/'receipt.json').read_bytes());fpq=fieldpacket/'new-owned-zones.pkl';fpd=fieldpacket/'proposed-discrete.pkl';assert sha(fpq)==fr['new_owned_zones_sha256']and sha(fpd)==fr['proposed_discrete_sha256'];peerq=pickle.loads(fpq.read_bytes());peerd=pickle.loads(fpd.read_bytes());assert len(peerq)==1 and peerq[0]['uuid']=='e8ec0287-e6d1-597d-8ad8-c4ab74280f6c';iohard+=peerq
 hard_h={**h,'tracks':h['tracks']+peerd['tracks'],'vias':h['vias']+peerd['vias']};write(OUT/'positive-U10017-peer-hard-binding.json',{'receipt_sha256':sha(fieldpacket/'receipt.json'),'prospective_plane_and_all_discretes_hard_only_not_appended_to_source_model':True})""")
a="rec,trees=F.build({**h,'zones':[]})";assert s.count(a)==1;s=s.replace(a,"rec,trees=F.build({**hard_h,'zones':[]})")
a="all_holes += [(v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64)) for v in h['vias']]";assert s.count(a)==1;s=s.replace(a,"all_holes += [(v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64)) for v in hard_h['vias']]")
compile(s,str(dst),'exec');dst.write_text(s)
(H/'CORE-In2-existing-port-feed-r79-derivation.json').write_text(json.dumps({'prior_constructor_sha256':sha(src),'derived_constructor_sha256':sha(dst),'exact_hypothesis_model_sha256':sha(mp),'exact_hypothesis_receipt_sha256':sha(rp),'only_changed_scope':'Pinned explicitR77prospectiveexistingf6In2 hypothesis; feedconstructor restrictedIn2 and begins4/3/2mm before smaller source-compatible widths. All actual original foreignCu/drills/keepouts/newIO3/fieldreturns hard. ExistingR65 zero-feed result preserved.','full_CORE1V2_load_A':.8,'native_actual_extra_flash_current_drop_return_thermal_stability_source_and_all77gates':'OPEN','no_old_native_layer_unsuppression_or_serialized_barrel_edit':True,'native_jobs':0,'adopted':False},indent=1)+'\n')
print(dst)
