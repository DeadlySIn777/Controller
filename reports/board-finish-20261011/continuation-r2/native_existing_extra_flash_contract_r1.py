"""Bind unchanged existing barrels to explicit post-fill layer obligations."""
import hashlib,json
from pathlib import Path
STACK=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def collect(rows,original,after,copper,removed,replaced):
 result=[];pins={};seen=set()
 for row in rows:
  uid=row['uuid'];assert uid not in seen and uid not in removed and uid not in replaced;seen.add(uid)
  assert uid in original and original[uid]==after[uid] and copper[uid]['kind']=='via'
  path=Path(row['explicit_ledger_file']);assert sha(path)==row['explicit_ledger_sha256'];pins[str(path.resolve())]=sha(path);r=json.loads(path.read_bytes())
  if 'via_uuid'in r:
   assert uid==r['via_uuid'] and r['parent_native_board_sha256']=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
   chunk=Path(r['original_native_via_chunk_file']);assert sha(chunk)==r['original_native_via_chunk_sha256'] and chunk.read_bytes()==original[uid];pins[str(chunk.resolve())]=sha(chunk)
   old=r['original_actual_native_flash_mask'];required=r['required_native_postfill_flash_mask'];net=r['net_raw'];extra=r['prospective_additional_flash_layer']
   assert r['same_serialized_existing_via_UUID_net_position_diameter_drill'] and r['no_new_drill_and_no_native_layer_span_change']
   expected=r['expected_original_host_geometry'];c=copper[uid]
   assert c['at_IU']==[round(expected['x']*1e6),round(expected['y']*1e6)] and c['drill_IU']==round(expected['drill']*1e6)
   assert all(v==round(expected['d']*1e6)for v in c['diameters_IU'].values())
  else:
   assert sha(path)=='d7d9fc1ba8bdbd40d2de8c13d80089e58a40949e7e8761302372838b04696950' and uid==r['existing_via_UUID']=='18701851-0390-4dc4-b03d-f8e1cd66c395'
   old=r['existing_native_flash_mask'];extra=r['prospective_additional_flash_layer'];required=[l for l in STACK if l in set(old)|{extra}];net=r['repair']['raw_net']
   assert r['old_discrete_Cu_unchanged'] and r['native_fill_must_attest_added_flash_and_all_four_retained_flashes']
  assert row['same_existing_serialized_via'] is True and row['original_native_flashes']==old and set(row['required_after_refill'])==set(required)
  assert len(required)==len(set(required)) and set(required)<=set(STACK) and extra not in old and set(required)==set(old)|{extra}
  assert copper[uid]['raw_net']==net
  flags=row['exact_consumed_prospective_metadata'];assert set(flags)<= {'prospective_new_flash_requires_native_refill','prospective_extra_flash_native_required'} and flags
  if 'prospective_new_flash_requires_native_refill'in flags:assert flags['prospective_new_flash_requires_native_refill']==extra
  if 'prospective_extra_flash_native_required'in flags:assert flags['prospective_extra_flash_native_required'] is True and uid=='18701851-0390-4dc4-b03d-f8e1cd66c395'
  result.append({'uuid':uid,'original_actual_native_flashes':old,'required_actual_fresh_refill_flashes':[l for l in STACK if l in required],'extra_layer':extra,'raw_net':net,'same_existing_serialized_via':True,'exact_original_native_chunk_sha256':hashlib.sha256(original[uid]).hexdigest(),'explicit_ledger_file':str(path.resolve()),'explicit_ledger_sha256':sha(path)})
 return result,pins
