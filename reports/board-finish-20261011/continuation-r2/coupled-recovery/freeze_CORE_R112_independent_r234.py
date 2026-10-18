"""Freeze full wider-CORE audit with its own exact constructor authorities."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent
src=H/'audit_CORE_R100_actual_R214_independent_r224.py'
dst=H/'audit_CORE_R112_actual_R214_independent_r234.py'
assert not dst.exists()
t=src.read_text()
for a,b in {
 'CORE R100 scope':'CORE R112 wider reserved-IO3 scope',
 'CORE-R100-vs-actual-R214-independent-r224':'CORE-R112-vs-actual-R214-independent-r234',
 'CORE-In2-owned-notch-materialized-source-proposal-r100':'CORE-wide-reserved-IO3-immutable-R214-materialized-r112',
 'cdb3c648f30dfd0ec60d921169637c180b90769d70ef141fc19d143fb0b18258':'94a8a335edcda606c0c64f94ae77597815b6206f80dfef13fe5e2422ca460680',
 'db01ba8f89c614c72b19688ec6479c96e8524259f1968eaa2dd3f2caeef49635':'6312b10a88b2d3614e21760d1709866d2417b419d418e20e09055eb13b8e3b7e',
 'R224_':'R234_',
 'CORE_R100_VS_R214':'CORE_R112_VS_R214',
 'R100_constructor_receipt_sha256':'R112_constructor_receipt_sha256',
 'R100_model_sha256':'R112_model_sha256',
 'exact-R83-R100-owned-role-authority-replay.json':'exact-R83-R112-owned-role-authority-replay.json',
}.items():
 assert a in t,a
 t=t.replace(a,b)
anchor=" put(O/'exact-R83-R112-owned-role-authority-replay.json',replay);"
assert t.count(anchor)==1
extra=""" packet=H.parent/'CORE-wide-local-IO3-branch-reservation-proposal-r111';pr=A.read(packet/'receipt.json');assert C.sha(pr)==r['route_receipt_sha256']=='7ee4c5126cdaeb45db8f26524ec34d459cdcfe5baf54ec20d9c8b67230ebc24c';rpbytes=A.read(packet/'proposed-route-and-zone.pkl');assert C.sha(rpbytes)=='a4fd1aa2ac6199858b569750e1f8440171f524174d74335a5411950771a8691f';route=pickle.loads(rpbytes);assert len(route)==1;routecore=route[0]['zone'];assert routecore['uuid']==core['uuid'] and C.sha(routecore['shape'].wkb)=='d7e6b486a7bc3410a82b432cf541acc713eb6f5de15f8adf814427bcc438c8d9';pd=A.read(packet/'proposed-discrete.pkl');assert C.sha(pd)=='14b3cf21c009b254ae29f96662a35eea1d567f7486169dae4a6b36b60f0e6fa9' and pickle.loads(pd)==d
 assert {k:v for k,v in core.items()if k not in('shape','zone_outline_shape')}=={k:v for k,v in routecore.items()if k not in('shape','zone_outline_shape')}
 assert core['zone_outline_shape'].wkb==routecore['zone_outline_shape'].wkb
 rr=rolemap[core['uuid'],'shape'];assert C.sha(routecore['shape'].wkb)==rr['before_WKB_sha256'] and C.sha(core['shape'].wkb)==rr['after_WKB_sha256'];assert core['shape'].difference(routecore['shape']).is_empty
 meta='CORE_R112_only_added_ordinary_native_actual_fill_projection';expected={'baseline_model_sha256':C.sha(praw),'route_receipt_sha256':C.sha(pr),'old_native_zone_definitions_unchanged':True,'new_ordinary_vias':[v['uuid']for v in nv],'new_owned_CORE_In2_UUID':core['uuid'],'strict_original104_PDN_and_all_raw_failed_reference_ledgers_unchanged':True,'all_full_current_return_source_native_qualification':'OPEN'};assert b[meta]==expected
 assert b['generated_precision_state_ledger']==json.loads(A.read(candidate/'generated-precision-state-ledger.json'))
 assert {k:v for k,v in b.items()if k not in(meta,'generated_precision_state_ledger','restored_generated_grid_UUIDs')}=={k:v for k,v in pb.items()if k not in('generated_precision_state_ledger','restored_generated_grid_UUIDs')}
 assert r['actual_native_fill_immutable_R214_baseline_sha256']==C.sha(br) and r['only_owned_remove_only_masks_are_applied_NO_reclaimed_old_fill_credit'] is True
 put(O/'exact-wider-R111-role-discrete-metadata-authority.json',{'route_receipt_sha256':C.sha(pr),'route_geometry_sha256':C.sha(rpbytes),'discrete_sha256':C.sha(pd),'new_core_intended_outline_exact':True,'new_core_physical_role_bound_remove_only':rr,'every_other_binding_metadata_exact_to_R83':True,'exact_current_projection_provenance':expected})
"""
t=t.replace(anchor,extra+anchor)
anchor=" put(O/'all-derived-native-and-owned-fill-deltas-vs-R214.json',filldelta);"
assert t.count(anchor)==1
t=t.replace(anchor," put(O/'complete-native-and-owned-fill-gain-facts.json',[row for row in filldelta if row['new_actual_projection_credit_mm2']>0]);"+anchor)
dst.write_text(t);compile(t,str(dst),'exec')
print(hashlib.sha256(dst.read_bytes()).hexdigest())
