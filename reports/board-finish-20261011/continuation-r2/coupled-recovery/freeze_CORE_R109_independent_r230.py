"""Freeze a separate full independent audit of the immutable-fill successor."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent
src=H/'audit_CORE_R100_actual_R214_independent_r224.py'
dst=H/'audit_CORE_R109_actual_R214_independent_r230.py'
assert not dst.exists()
t=src.read_text()
replacements={
 'CORE R100 scope':'CORE R109 immutable-native-fill scope',
 'CORE-R100-vs-actual-R214-independent-r224':'CORE-R109-vs-actual-R214-independent-r230',
 'CORE-In2-owned-notch-materialized-source-proposal-r100':'CORE-narrow-immutable-R214-materialized-source-proposal-r109',
 'cdb3c648f30dfd0ec60d921169637c180b90769d70ef141fc19d143fb0b18258':'ee3ac6173b2ee41e48ad330686c46054994b299c34835b68ba971b0929d9d7c5',
 'db01ba8f89c614c72b19688ec6479c96e8524259f1968eaa2dd3f2caeef49635':'fcd5182a7f2d415195508bda0297b9da9eed8cf118b0d78d1d52f942c844a773',
 'R224_':'R230_',
 'CORE_R100_VS_R214':'CORE_R109_VS_R214',
 'R100_constructor_receipt_sha256':'R109_constructor_receipt_sha256',
 'R100_model_sha256':'R109_model_sha256',
 'exact-R83-R100-owned-role-authority-replay.json':'exact-R83-R109-owned-role-authority-replay.json',
}
for a,b in replacements.items():
 assert a in t,a
 t=t.replace(a,b)
# Bind unchanged native/discrete definitions and every generated role to the
# independently audited rejected R100.  This is byte/WKB identity evidence,
# not a reuse of its reference failure or old native-fill recomputation.
anchor=" put(O/'exact-R83-R109-owned-role-authority-replay.json',replay);"
assert t.count(anchor)==1
extra=""" exact100=H.parent/'CORE-In2-owned-notch-materialized-source-proposal-r100';raw100=A.read(exact100/'model.pkl');assert C.sha(raw100)=='db01ba8f89c614c72b19688ec6479c96e8524259f1968eaa2dd3f2caeef49635';g100,h100,b100,q100,after100=pickle.loads(raw100);assert g100==g and h100==h and b100==b;qm100={z['uuid']:z for z in q100};assert set(qm100)==set(by);same_roles=[]
 for uid,z in by.items():
  old=qm100[uid];assert {k:v for k,v in z.items()if k not in('shape','zone_outline_shape')}=={k:v for k,v in old.items()if k not in('shape','zone_outline_shape')}
  for role in('shape','zone_outline_shape'):
   assert z[role].wkb==old[role].wkb,(uid,role)
   same_roles.append({'UUID':uid,'role':role,'R100_R109_identical_WKB_sha256':C.sha(z[role].wkb)})
 assert r['actual_native_fill_immutable_R214_baseline_sha256']==C.sha(br) and r['only_owned_remove_only_masks_are_applied_NO_reclaimed_old_fill_credit'] is True
 put(O/'exact-R100-R109-native-discrete-generated-role-identity.json',same_roles)
 del raw100,g100,h100,b100,q100,after100,qm100
"""
t=t.replace(anchor,extra+anchor)
# Record any alleged native reclaimed copper explicitly, never suppress it
# from source/reference/contact testing.  Those exact deltas are facts.
anchor=" put(O/'all-derived-native-and-owned-fill-deltas-vs-R214.json',filldelta);"
assert t.count(anchor)==1
t=t.replace(anchor," put(O/'native-derived-fill-gain-claim-ledger.json',[row for row in filldelta if row['new_actual_projection_credit_mm2']>0]);"+anchor)
dst.write_text(t)
compile(t,str(dst),'exec')
print(str(dst))
print(hashlib.sha256(dst.read_bytes()).hexdigest())
