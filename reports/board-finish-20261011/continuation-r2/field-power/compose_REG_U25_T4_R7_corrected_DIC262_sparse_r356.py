"""Corrected frozen DIC head plus exact sparse SBC and field operations."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'compose_REG312_U25_only_current_R256_r354.py').read_text(encoding='utf-8')
s=s.replace('REG312-U25-sparse-actual-R256-current-composition-r354','REG-U25-T4-R7-corrected-DIC262-sparse-current-composition-r356')
s=s.replace('DIC-C1022-exact-R250-current-construction-r256','DIC-C1022-exact-R250-original-guard-construction-r262')
s=s.replace('7b4c123a051f7b177c928b7a02c479776237c198989f3c1a24d722c29dd25573','64a1f6e1597c9d757b187c3b6db85d79685ee376399bdd4738f915b87b1a0144')
s=s.replace('baseline_R256_model_SHA256','baseline_corrected_DIC_R262_model_SHA256')
s=s.replace('import immutable_local_fill_subtraction_r254 as IM','import immutable_local_fill_subtraction_r254 as IM\nimport construct_T4_R7_sparse_R250_diagnostic_r261 as SB')
needle=' assert len(deleted)==14 and set(deleted)<=set(oldtracks)'
addition="""
 S=H.parent/'sbc-power/T4-R7-exact-sparse-owned-native-and-negative-fill-recipe-r268'
 assert sha(S/'receipt.json')=='a89ae74f70f1798d4fa3b5e831a5140829850b5b7d58abec65fa80a8eba5f467'
 assert sha(S/'only-owned-new-discrete-and-four-exact-deletes.pkl')=='c612d423566e2af6af4a204f8a2afdbfeb049091de337428f598c397777abb40'
 assert sha(S/'only-two-DOB-generated-negative-role-masks.pkl')=='6ef5d8362121ddff8841a48904caa4c716541c526653e5e8a2c2f1a178b10157'
 sd=pickle.loads((S/'only-owned-new-discrete-and-four-exact-deletes.pkl').read_bytes());assert len(sd['tracks'])==10 and len(sd['vias'])==1 and len(sd['removed'])==4
 for row in json.loads((S/'exact-sparse-operation-ledger.json').read_text()):
  path=Path(row['exact_chunk_path']);assert sha(path)==row['exact_chunk_sha256']
  if row['action']!='remove':continue
  uid=row['uuid'];ch=path.read_bytes();assert iv[3][uid]==ch and uid not in deleted;deleted[uid]=ch;delete_rows.append({'owner':'SBC_T4_R7',**row})
 assert len(deleted)==18 and set(deleted)<=set(oldtracks)
 sb_oldbody={}
 for net,layer in {(L.norm(oldtracks[uid]['net']),oldtracks[uid]['layer'])for uid in sd['removed']}:
  sb_oldbody[net,layer]=unary_union([SB.Z.bounded_buffer(LineString([oldtracks[uid]['a'],oldtracks[uid]['b']]),oldtracks[uid]['w']/2)for uid in sd['removed']if(L.norm(oldtracks[uid]['net']),oldtracks[uid]['layer'])==(net,layer)])
"""
assert s.count(needle)==1;s=s.replace(needle,addition)
s=s.replace("nt=rd['tracks']+ud['tracks'];nv=rd['vias']+ud['vias']","nt=rd['tracks']+ud['tracks']+sd['tracks'];nv=rd['vias']+ud['vias']+sd['vias']")
s=s.replace('assert len(newids)==21','assert len(newids)==32')
s=s.replace('def primitives(net,local,layer,physical=True):','def primitives(net,local,layer,physical=True,include_sbc=True):')
s=s.replace('  for v in nv:\n','  for v in rd[\'vias\']+ud[\'vias\']:\n')
s=s.replace('  for t in nt:\n','  for t in rd[\'tracks\']+ud[\'tracks\']:\n')
needle2='  return rows\n # Every owned current role'
addition2="""  if include_sbc:
   for entry in SB.cutters(sd['tracks']+sd['vias'],sb_oldbody,net,layer,local,h,not physical):
    rows.append((entry['new_UUID'],entry['kind'],entry['shape']))
  return rows
 # Every owned current role"""
assert s.count(needle2)==1;s=s.replace(needle2,addition2)
s=s.replace("q['layer'],role=='shape')if r[2].intersects(old)","q['layer'],role=='shape',include_sbc=False)if r[2].intersects(old)")
needle3=' # Frozen local reference/actual-native point cut families'
addition3="""
 # Only two frozen DOB role masks, exact-before checked on this actual
 # corrected head; every other SBC prospective role remains untouched.
 for op in pickle.loads((S/'only-two-DOB-generated-negative-role-masks.pkl').read_bytes()):
  q=zm[op['uuid']];role=op['role'];prior=q[role];assert digest(prior)==op['before_WKB_sha256']
  mask=op['exact_negative_mask'];after=prior.difference(mask);restored=set_precision(after,1e-6,mode='pointwise');assert restored.wkb==after.wkb;assert digest(after)==op['after_WKB_sha256'];q[role]=restored
  role_rows.append({'UUID':q['uuid'],'role':role,'step':'exact_SBC_R268_owned_negative_mask_replay','before_SHA256':digest(prior),'after_SHA256':digest(after),'positive_mm2':set_precision(after,0).difference(set_precision(prior,0)).area,'exact_bound_negative_mask_SHA256':digest(mask)})
 # Frozen local reference/actual-native point cut families"""
assert s.count(needle3)==1;s=s.replace(needle3,addition3)
s=s.replace("'U25_packet_SHA256':sha(U/'receipt.json')","'U25_packet_SHA256':sha(U/'receipt.json'),'SBC_R268_packet_SHA256':sha(S/'receipt.json')")
s=s.replace("'U25_R350_packet_SHA256':sha(U/'receipt.json')","'U25_R350_packet_SHA256':sha(U/'receipt.json'),'SBC_R268_packet_SHA256':sha(S/'receipt.json')")
s=s.replace("'new_vias':5,'new_tracks':16,'exact_before_original_track_deletes':14","'new_vias':6,'new_tracks':26,'exact_before_original_track_deletes':18")
exec(compile(s,str(H/'compose_REG312_U25_only_current_R256_r354.py'),'exec'))
