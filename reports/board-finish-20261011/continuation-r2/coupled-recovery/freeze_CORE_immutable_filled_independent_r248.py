"""Independent actual-fill successor audit, exact R112 design geometry."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent
src=H/'audit_CORE_R112_actual_R214_independent_r234.py'
dst=H/'audit_CORE_R246_actual_R214_independent_r248.py'
assert not dst.exists()
t=src.read_text().replace('CORE-R112-vs-actual-R214-independent-r234','CORE-R246-vs-actual-R214-independent-r248').replace('R234_','R248_').replace('CORE_R112_VS_R214','CORE_R246_VS_R214')
anchor=" d=pickle.loads(A.read(candidate/'proposed-discrete.pkl'));"
assert t.count(anchor)==1
extra=""" frozen=H/'CORE-R112-per-polygon-immutable-owned-construction-r246';fr=A.read(frozen/'receipt.json');assert C.sha(fr)=='fd437ea4e5a9139eb4698598ba20f715bf357e841ba257f4f33dd7c1e76b7e82';fc=json.loads(fr);assert not fc['strict_failures'] and fc['adopted'] is False and fc['native_jobs']==0
 changed=A.read(frozen/'model.pkl');assert C.sha(changed)==fc['model_sha256']=='32b60c225aa42347e3739c41d297c0f6047ee87978b42270958678fc6b51e685';fg,fh,fb,fq,fa=pickle.loads(changed);assert fg==ng and fh==h and fb==b;assert len(fq)==len(q)
 for old,new in zip(q,fq):
  assert set(old)==set(new)
  for key in old:assert old[key].wkb==new[key].wkb if hasattr(old[key],'wkb')else old[key]==new[key],(old['uuid'],key)
 qold={z['uuid']for z in q0};origactual={z['uuid']:z for z in after['zones']};factual={z['uuid']:z for z in fa['zones']};assert set(origactual)==set(factual)
 for uid,z in origactual.items():
  if uid not in qold:assert factual[uid]==z,'Every native actual/new CORE fill record exact R112'
  else:assert {k:v for k,v in factual[uid].items()if k!='fills'}=={k:v for k,v in z.items()if k!='fills'}
 for file,pin in fc['output_files_sha256'].items():assert C.sha(A.read(file))==pin
 ledger=json.loads(A.read(frozen/'immutable-owned-record-delta-ledger.json'))
 for row in ledger:
  if row.get('new_CORE_only_filled_records_exact_R112'):continue
  oldz=next(z for z in before['zones']if z['uuid']==row['UUID']);newz=factual[row['UUID']];a=unary_union(L.poly(oldz['fills'][row['layer']]));n=unary_union(L.poly(newz['fills'][row['layer']]));assert C.sha(a.wkb)==row['exact_before_filled_WKB_sha256']and C.sha(n.wkb)==row['exact_after_filled_WKB_sha256'];assert n.difference(a).is_empty,'No gained filled copper independent exact check';assert row['entire_filled_no_reclaimed_Cu']is True
  if row['UUID']=='bde7a0cf-1ad7-5a04-b956-9f8848bb3f2a':assert row['b1ba_exact_local_fill_loss_empty']is True
 put(O/'independent-exact-R112-design-native-newCORE-and-R214-owned-subset.json',{'R246_constructor_receipt_sha256':C.sha(fr),'R246_model_sha256':C.sha(changed),'all_g_h_b_q_WKB_settings_exact_R112':True,'all_actual_native_and_new_CORE_fill_records_exact_R112':True,'literal_independent_existing_owned_fill_no_gain':True,'local_negative_filled_reserves_source_direct_contacts_reference_current_native_requalification':'OPEN; explicitly bound raw gain/cutter/negative data, no threshold or physical role edits'})
 after=fa
"""
t=t.replace(anchor,extra+anchor)
anchor="'R112_model_sha256':C.sha(raw),"
assert t.count(anchor)==1
t=t.replace(anchor,anchor+"'R246_actual_filled_constructor_receipt_sha256':C.sha(fr),'R246_actual_filled_model_sha256':C.sha(changed),")
dst.write_text(t);compile(t,str(dst),'exec')
print(hashlib.sha256(dst.read_bytes()).hexdigest())
