"""Complete current discrete diff; authorizers are identity and byte bound."""
import json,pickle,hashlib,sys
from pathlib import Path
H=Path(__file__).resolve().parent
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_aux_exact_raw as A
C=A.C
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(kind,r):
 fields={'tracks':('uuid','net','layer','a','b','m','w'),'vias':('uuid','net','x','y','d','drill','span','flashed'),'pads':tuple(sorted(r))}[kind]
 return {k:r[k]for k in fields if k in r}
def freeze(current_h,legacy,fp_rows,sparse_delete_rows,out,extra_delete_packages=()):
 base=H.parent/'field-power/native-bound-field-base-r5';raw=A.read(base/'model.pkl');assert C.sha(raw)=='fe49e79fcf9429af97e8ed0f520466e1188f7ba53f02998f08d464a6ce505d2e';old=pickle.loads(raw)['discrete'];sourcefile=H.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';source=A.read(sourcefile);assert C.sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';deletes={};replacements={};bindings=[]
 def bind_delete(row,packet,psha):
  row=dict(row);uid=row['uuid'];file=row.get('chunk_file')or row.get('chunk_path');want=row.get('exact_original_chunk_sha256')or row.get('chunk_sha256');ch=A.read(file);assert C.sha(ch)==want and source.count(ch)==1;assert uid.encode()in ch
  auth=row.get('authorizing_recipe_file')or row.get('authorizing_packet_file')or str(packet);ah=row.get('authorizing_recipe_sha256')or row.get('authorizing_packet_sha256')or psha;assert sha(auth)==ah
  if uid in deletes:assert deletes[uid]['exact_original_chunk_sha256']==want
  deletes[uid]={'uuid':uid,'kind':row['kind'],'chunk_path':str(file),'exact_original_chunk_sha256':want,'authorizing_recipe_file':auth,'authorizing_recipe_sha256':ah,'inventory_carrier_file':str(packet),'inventory_carrier_sha256':psha,'original_expected_geometry':row.get('expected_geometry'),'source_chunk_occurs_exactly_once':True}
 legacyfile=H.parent/'sbc-power/exploratory-SAFE-power-native-recipe-r169/receipt.json';assert sha(legacyfile)=='cbc2252a73de52c5a5b3290aa10384bde88762cdb5d5bc6e826e184d627d4e40'
 for row in legacy['native_existing_owned_Cu_delete_rows']:bind_delete(row,legacyfile,sha(legacyfile))
 for row in legacy['native_existing_owned_Cu_replacement_rows']:
  uid=row['uuid'];assert uid not in replacements
  for kind in('original_chunk','replacement_chunk','authorizing_recipe'):assert sha(row[kind+'_file'])==row[kind+'_sha256']
  assert source.count(Path(row['original_chunk_file']).read_bytes())==1;replacements[uid]=row
 extra=[(H.parent/'field-power/R11054-static-and-AUX-bleed-native-owned-recipe-r208/receipt.json','1e768077e1be6ca94c5da4d48e724f911679bb3b4454b2325aa748b343e8aa70'),(H.parent/'field-power/SAFE-U10017-wider-native-owned-recipe-r183/receipt.json','00c4e035dc2f95f6a4e5560ec00d1393763b4386cfead6e1a104af1bdbaf123d')]
 for packet,want in extra:
  data=A.read(packet)
  # A declared pin must match before its rows can authorize an operation.
  assert C.sha(data)==want,(str(packet),C.sha(data),want)
  for row in json.loads(data)['delete_rows']:bind_delete(row,packet,want)
 monitor=H/'R66-monitor-exact-native-delete-authorizer-r268/receipt.json';monraw=A.read(monitor);assert C.sha(monraw)=='8a6917f823ccb2ed8758e3c278c4014599ebc28b6a920a8a1bedbaf4f0c41daf'
 for row in json.loads(monraw)['delete_rows']:bind_delete(row,monitor,C.sha(monraw))
 for packet,want in extra_delete_packages:
  data=A.read(packet);assert C.sha(data)==want
  for row in json.loads(data)['delete_rows']:bind_delete(row,packet,want)
 for row in sparse_delete_rows:bind_delete(row,H/'DIC-C1022-one-R214-joint-native-integration-delta-r222/receipt.json','bbf14c6887829a93d50fbf285aad61353dbc60eb30eaad1485036d410c89be0f')
 flash={r['uuid']:r for r in legacy['existing_via_prospective_new_flashes']};assert set(flash)=={'18701851-0390-4dc4-b03d-f8e1cd66c395','f6ad6a15-3a41-4605-9ad5-72f4ba7d5d92'}
 pad_authority={p['pad_uuid']:r for r in fp_rows for p in r['native_pose_row']['pads']};rows=[];unbound=[];counts={};sameuuid=[];missing=[]
 for kind in('tracks','vias','pads'):
  oldmap={r['uuid']:r for r in old[kind]};newmap={r['uuid']:r for r in current_h[kind]};assert len(oldmap)==len(old[kind])and len(newmap)==len(current_h[kind]);added=sorted(newmap.keys()-oldmap.keys());unchanged=sorted(u for u in oldmap.keys()&newmap.keys()if oldmap[u]==newmap[u]);lost=sorted(oldmap.keys()-newmap.keys());changed=[];metadata=[]
  for uid in sorted(oldmap):
   a=oldmap[uid];b=newmap.get(uid)
   if b is None:
    auth=deletes.get(uid);row={'action':'MISSING_ORIGINAL','kind':kind,'UUID':uid,'complete_original_record':a,'matched_exact_delete_authorizer':auth,'bound':bool(auth)};missing.append(row)
   elif a==b:continue
   else:
    native_delta=canonical(kind,a)!=canonical(kind,b);auth=replacements.get(uid)if kind!='pads'else pad_authority.get(uid);row={'action':'SAME_UUID_NATIVE_RECORD_CHANGE'if native_delta else'HOST_METADATA_ONLY_CHANGE','kind':kind,'UUID':uid,'complete_original_record':a,'complete_current_record':b,'exact_changed_fields':sorted(k for k in set(a)|set(b)if a.get(k)!=b.get(k)),'matched_exact_native_authorizer':auth,'bound':bool(auth)}
    if auth and kind!='pads':
     for expected,key in((auth['expected_original_geometry'],'complete_original_record'),(auth['expected_replacement_geometry'],'complete_current_record')):
      actual=row[key];assert all(actual.get(k)==v for k,v in expected.items()if k in actual),(uid,key,expected,actual)
    if auth and kind=='pads':
     want=next(p for p in auth['native_pose_row']['pads']if p['pad_uuid']==uid);assert b['net']==want['raw_net']and [b['x'],b['y']]==want['absolute_center_mm'];assert sha(auth['replacement_chunk_file'])==auth['replacement_chunk_sha256']
    if kind=='vias'and uid in flash and not auth:
     fr=flash[uid];assert fr['same_existing_serialized_via']and a['flashed']==fr['original_native_flashes']and b['flashed']==fr['required_after_refill'];assert {k:v for k,v in a.items()if k!='flashed'}=={k:v for k,v in b.items()if k not in('flashed','prospective_new_flash_requires_native_refill')};assert fr['exact_consumed_prospective_metadata']=={'prospective_new_flash_requires_native_refill':b['prospective_new_flash_requires_native_refill']};assert sha(fr['explicit_ledger_file'])==fr['explicit_ledger_sha256'];row['matched_exact_postfill_additional_layer_obligation']=fr;row['native_operation']='NO_VIA_BYTES_OR_GEOMETRY_OR_MASK_FLAG_OVERRIDE_REQUIRED_POSTFILL_ANNULUS_PROOF_OPEN';row['bound']=True
     if uid=='f6ad6a15-3a41-4605-9ad5-72f4ba7d5d92':
      er=json.loads(Path(fr['explicit_ledger_file']).read_bytes());assert er['expected_original_host_geometry']==a and er['expected_prospective_host_geometry']==b;assert er['original_actual_native_flash_mask']==a['flashed']and er['required_native_postfill_flash_mask']==b['flashed'];assert sha(er['original_native_via_chunk_file'])==er['original_native_via_chunk_sha256'];assert source.count(Path(er['original_native_via_chunk_file']).read_bytes())==1
     else:
      lr=json.loads(Path(fr['explicit_ledger_file']).read_bytes());assert lr['existing_via_UUID']==uid and lr['existing_native_flash_mask']==a['flashed']and lr['prospective_additional_flash_layer']==b['prospective_new_flash_requires_native_refill']
    if native_delta:changed.append(uid);sameuuid.append(row)
    else:metadata.append(uid)
   rows.append(row)
   if not row['bound']:unbound.append(row)
  counts[kind]={'original':len(oldmap),'current':len(newmap),'new_UUIDs':added,'new_complete_native_rows':[newmap[u]for u in added],'unchanged_original_UUIDs':unchanged,'unchanged_original_complete_record_pairs_sha256':C.sha(json.dumps([(u,oldmap[u],newmap[u])for u in unchanged],sort_keys=True,separators=(',',':')).encode()),'missing_original_UUIDs':lost,'changed_native_record_UUIDs':changed,'metadata_only_change_UUIDs':metadata}
 summary={'base_native_bound_model_file':str(base/'model.pkl'),'base_native_bound_model_sha256':C.sha(raw),'base_native_board_sha256':C.sha(source),'complete_every_original_track_via_pad_compared':True,'no_original_difference_hidden_by_net_normalization_or_rounding':True,'counts':counts,'all_missing_original_rows':missing,'all_same_UUID_native_change_rows':sameuuid,'all_difference_rows':rows,'unbound_original_difference_rows':unbound,'all_original_inventory_differences_bound':not unbound,'native_existing_owned_Cu_delete_rows':[deletes[u]for u in sorted(deletes)if any(r['UUID']==u and r['action']=='MISSING_ORIGINAL'for r in rows)],'native_existing_owned_Cu_replacement_rows':[replacements[u]for u in sorted(replacements)if any(r['UUID']==u and r['action']=='SAME_UUID_NATIVE_RECORD_CHANGE'for r in rows)],'native_existing_owned_footprint_replacement_rows':fp_rows,'existing_via_prospective_new_flashes':list(flash.values()),'all_current_owned_geometry_must_come_from_current_model_not_legacy_recipe':True,'native_all_annuli_IU_pose_full_source_parity_and_full_fill':'OPEN','adopted':False,'native_jobs':0}
 file=out/'complete-native-bound-original-discrete-inventory-diff.json';file.write_text(json.dumps(summary,indent=1,allow_nan=False)+'\n');return file,summary
