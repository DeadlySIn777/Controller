"""Freeze R291 successor with source graph rebuilt after exact middle removal."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
source=H/'screen_CORE5_current_In3_LGIn4_transport_r291.py'; target=H/'screen_CORE5_middle_withdrawn_In3_LGIn4_transport_r292.py'
assert not target.exists(); s=source.read_text(encoding='utf-8')
s=s.replace('r291','r292').replace('R291','R292')
old="coregroups=K.physical(actual,NET,ctx)[1];(OUT/'actual-full-R157-CORE5-all-drilled-groups.pkl').write_bytes(pickle.dumps(coregroups,protocol=5));coreroot=K.root(coregroups,'R11022','2')"
new="""original=next(t for t in actual['tracks']if t['uuid']=='dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1')
 assert(original['a'],original['b'],original['w'],original['layer'])==([112.95,202.35],[133.549999,202.35],1.25,'F.Cu')
 import copy,uuid
 anchors=[]
 for a,bp in (([112.95,202.35],[116.2,202.35]),([120.1,202.35],[133.549999,202.35])):
  anchor={**original,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CORE5-R292-source-test-anchor-'+str(a))), 'a':a,'b':bp};anchors.append(anchor)
 actual={**actual,'tracks':[t for t in actual['tracks']if t['uuid']!=original['uuid']]+anchors}
 # Only the original middle is withdrawn in this independent physical
 # source graph. Every native fill, pad, barrel, hole and mask is unchanged.
 coregroups=K.physical(actual,NET,ctx)[1];(OUT/'actual-full-R157-CORE5-middle-withdrawn-all-drilled-groups.pkl').write_bytes(pickle.dumps(coregroups,protocol=5));coreroot=K.root(coregroups,'R11022','2')
 put('exact-original-middle-withdrawal-physical-source-ledger.json',{'old_track':original,'two_full_width_source_test_anchors':anchors,'withdrawn_middle_only_mm':[[116.2,202.35],[120.1,202.35]],'native_fills_pads_holes_masks_unchanged':True,'actual_post_withdrawal_root_keys':len(K.keys(coreroot))})"""
assert s.count(old)==1; s=s.replace(old,new).replace("sha(OUT/'actual-full-R157-CORE5-all-drilled-groups.pkl')","sha(OUT/'actual-full-R157-CORE5-middle-withdrawn-all-drilled-groups.pkl')")
s=s.replace("'only_NEW_CORE5_transport_withdrawable':sorted(withdrawn)","'only_NEW_CORE5_transport_withdrawable':sorted(withdrawn),'source_is_actual_R157_AFTER_exact_original_middle_withdrawal':True")
compile(s,str(target),'exec');target.write_text(s,encoding='utf-8')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
receipt=H/'CORE5-actual-source-middle-withdrawn-In3-screen-derivation-r292.json';assert not receipt.exists();receipt.write_text(json.dumps({'source_file':str(source),'source_sha256':sha(source),'derived_file':str(target),'derived_sha256':sha(target),'only_source_graph_middle_withdrawal_and_revision_paths_changed':True,'native_jobs':0,'adopted':False},indent=1)+'\n',encoding='utf-8')
print('R292_SCRIPT_FROZEN',sha(target),flush=True)
