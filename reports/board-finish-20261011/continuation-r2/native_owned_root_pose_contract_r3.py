"""Allow only the legacy R17031 translation and two exact independently attested root-at rotations."""
import hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'))
import native_translation_owned_contract_r2 as LEGACY
from verify_source import parse,child,atom
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def authority():
 folder=H/'two-rotated-native-FP-masks-r85';rp=folder/'receipt.json';mp=folder/'native-metadata.json';assert sha(rp)=='67617abf125ea761eb157e57d9ff2690e423d1ed213bb46e8309cd094ff3cbd8';r=json.loads(rp.read_bytes());assert r['verdict']=='PASS_READ_ONLY_TWO_ROTATED_NATIVE_FP_COLLECTOR_METADATA'and sha(mp)==r['native_metadata_sha256']=='58f4df4ac61f5f63f487ea745f376f1058e65af39f47a0657409c1b4115f7f3e';metadata=json.loads(mp.read_bytes());assert metadata['verdict']=='PASS_TWO_EXACT_NATIVE_ROTATED_FP_MASKS_ANGLES_AND_FIELDS'
 specs=json.loads((folder/'spec.json').read_bytes());assert sha(folder/'spec.json')==r['spec_sha256'];by={q['ref']:q for q in metadata['rows']};assert set(by)=={'R9026','R11054'};return by,specs,{str(p.resolve()):sha(p)for p in(rp,mp,folder/'spec.json')}
def frozen_rows():
 metadata,specs,pins=authority();rows=[]
 for spec in specs['footprints']:
  ps=json.loads(Path(spec['pose_spec_file']).read_bytes());ref=ps['ref'];folder=Path(spec['board_file']).parent.parent
  if ref=='R9026':old=folder/'R9026.original-footprint-chunk';author=folder/'receipt.json'
  else:old=H/'field-power/R11054-static-and-AUX-bleed-native-owned-recipe-r208/R11054.original-exact-footprint-chunk';author=old.parent/'FP-authorization.json'
  new=Path(spec['replacement_FP_chunk_file']);rows.append({'uuid':ps['native_footprint_uuid'],'ref':ref,'original_chunk_file':str(old.resolve()),'original_chunk_sha256':sha(old),'replacement_chunk_file':str(new.resolve()),'replacement_chunk_sha256':sha(new),'authorizing_recipe_file':str(author.resolve()),'authorizing_recipe_sha256':sha(author),'original_root_pose_mm_deg':ps['prior_pose'],'replacement_root_pose_mm_deg':ps['target_pose'],'native_pose_row':metadata[ref]['native_pose_row'],'native_mask_and_text_row':metadata[ref]['native_mask_and_text_row'],'native_FP_pose_attestation_file':spec['native_rotation_receipt_file'],'native_FP_pose_attestation_sha256':spec['native_rotation_receipt_sha256'],'exact_rotated_FP_metadata_file':str((H/'two-rotated-native-FP-masks-r85/native-metadata.json').resolve()),'exact_rotated_FP_metadata_sha256':'58f4df4ac61f5f63f487ea745f376f1058e65af39f47a0657409c1b4115f7f3e'})
 return rows
def collect(rows,inventory):
 assert len(rows)<=3 and len({q['ref']for q in rows})==len(rows)and all(q['ref']in{'R17031','R9026','R11054'}for q in rows)
 legacy=[q for q in rows if q['ref']=='R17031'];result,pins,poses,masks=LEGACY.collect(legacy,inventory);pins[str(Path(LEGACY.__file__).resolve())]=sha(LEGACY.__file__);expected={q['ref']:q for q in frozen_rows()};_,_,metadata_pins=authority();pins.update(metadata_pins)
 for r in rows:
  if r['ref']=='R17031':continue
  ref=r['ref'];f=expected[ref];assert r==f,'Every row field must equal frozen actual-native authority; caller supplied poses/masks cannot replace it'
  old,new,author=map(Path,(r['original_chunk_file'],r['replacement_chunk_file'],r['authorizing_recipe_file']));assert sha(old)==r['original_chunk_sha256']and sha(new)==r['replacement_chunk_sha256']and sha(author)==r['authorizing_recipe_sha256'];uid=r['uuid'];ob=old.read_bytes();nb=new.read_bytes();assert inventory[3][uid]==ob and uid not in result
  a,b=parse(ob.decode()),parse(nb.decode());assert a[0]==b[0]=='footprint'and atom(a,'uuid')==atom(b,'uuid')==uid and atom(a,'layer')==atom(b,'layer')=='F.Cu'
  assert [q for q in a if not(isinstance(q,list)and q and q[0]=='at')]==[q for q in b if not(isinstance(q,list)and q and q[0]=='at')],'All local pads/nets/properties/courtyard/angles/source atoms must remain exact'
  prior=[float(x)for x in child(a,'at')[1:]];later=[float(x)for x in child(b,'at')[1:]]
  if len(prior)==2:prior.append(0.)
  if len(later)==2:later.append(0.)
  assert prior==r['original_root_pose_mm_deg']and later==r['replacement_root_pose_mm_deg']and next(q for q in a if isinstance(q,list)and q[:2]==['property','Reference'])[2]==ref
  attest=Path(r['native_FP_pose_attestation_file']);assert sha(attest)==r['native_FP_pose_attestation_sha256'];actual=json.loads(attest.read_bytes())['native_attestation'];assert actual['FP_pose_mm_deg']==later and actual['footprint_UUID']==uid
  pose=r['native_pose_row'];mask=r['native_mask_and_text_row'];assert pose['ref']==mask['ref']==ref and pose['native_footprint_uuid']==mask['footprint_UUID']==uid and pose['root_pose_mm_deg']==mask['target_pose_mm_deg']==later and pose['chunk_sha256']==mask['exact_chunk_sha256']==sha(new)
  assert {q['pad_uuid']for q in pose['pads']}=={q['physical_pad_UUID']for q in mask['pads']}=={q['UUID']for q in actual['native_pads']};assert all(q['actual_original_clone_native_flashes']==['F.Cu']for q in pose['pads'])
  result[uid]=nb;poses.append(pose);masks.append(mask)
  for path in(old,new,author,attest):pins[str(path.resolve())]=sha(path)
 return result,pins,poses,masks
