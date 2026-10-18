"""Fresh CM49 sparse replay on R543; no older whole-role or fill overlay."""
from pathlib import Path
P=Path(__file__).resolve().parent
t=(P/'construct_CM_sparse_only_new_role_withdrawal_r283.py').read_text(encoding='utf-8')
t=t.replace('CM-sparse-exact-current-R364-only-new-role-withdrawal-inherited-fills-FAIL-r283','CM-sparse-exact-current-R543-TMR-repaired-only-new-role-withdrawal-inherited-fills-FAIL-r333')
t=t.replace("s=s.replace('R279','R283')", "s=s.replace('R279','R333')")
needle="exec(compile(s,str(__file__),'exec'))"
assert t.count(needle)==1
replacement="""s=s.replace('field-power/REG-U25-DIC-SBC273-two-new-REG-actual-fill-margin-repair-r364/model.pkl','field-power/FIELD5-source-plane-exact-owned-edge-negative-redesign-current-r543/model.pkl')
s=s.replace('a39e7784abf8969b7f68176555b2c37b5227981cbc615c4bd542205e410373ad','474949d472a1870320b95cd494d4c96f79735b43632076d237d432d10c006416')
s=s.replace('d2d09cda7df82496860d7089cf0acb551e622596c9686f8d40b93181c0fd7a36','e049f4b72291cba52dab6c14f892c80ae38042919542969483efdc250627b214')
s=s.replace("oldq={z['uuid']:z for z in q};", "tmrAuthority=H/'field-power/FA-IO3-native-TMR-exact-two-zone-sparse-rebase-contract-r519/receipt.json';assert sha(tmrAuthority)=='bf494afa1699ce52e1812b79efe3676d31cb9d25f4a9c6d0f79b55b65bf8440e';tmrQ=next(z for z in q if z['uuid']=='4f297f78-8d11-5be4-910e-9245f73fa249');assert dig(tmrQ['shape'])=='06ef5939f3625df48164f01042bd0f0bdd62ec2c55bab7e86cb766706ed6e04b';assert dig(tmrQ['zone_outline_shape'])=='54d90e0bba440e852b8efe2cc09fa5ba8162c2269aeae75964a83ab1846072ac';put(O/'exact-field-TMR-repaired-q4f-before-role-authority.json',{'R519_contract_sha256':sha(tmrAuthority),'current_R543_model_sha256':sha(mp),'q4f_physical_before_sha256':dig(tmrQ['shape']),'q4f_intended_before_sha256':dig(tmrQ['zone_outline_shape']),'field_TMR_triangle_and_corridor_scope_hard_mm':[324,119,348,134],'only_new_CM_ground_primitives_normal_negative_replay':True,'no_R289_snapshot_overlay':True});oldq={z['uuid']:z for z in q};")
s=s.replace("(O/'only-new-CM-ordinary-discrete-no-deletes.pkl').write_bytes(pickle.dumps(d,protocol=5));", "(O/'only-new-CM-ordinary-discrete-no-deletes.pkl').write_bytes(pickle.dumps(d,protocol=5));assert sha(O/'only-new-CM-ordinary-discrete-no-deletes.pkl')=='72321f8b75794e2cf2bd5d4ba6788da7bbdb8eaa4ba692cf9a121d4c3bde3207';")
s=s.replace("started=time.monotonic();assert not O.exists();O.mkdir();", "started=time.monotonic();assert not O.exists();O.mkdir();(O/'exact-expanded-sparse-constructor.py').write_text(s,encoding='utf-8');")
exec(compile(s,str(__file__),'exec'))"""
t=t.replace(needle,replacement)
exec(compile(t,str(__file__),'exec'))
