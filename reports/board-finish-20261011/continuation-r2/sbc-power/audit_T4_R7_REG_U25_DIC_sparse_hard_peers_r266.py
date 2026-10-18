"""R265 joint diagnostic local safeguard scope, all hard peer packets."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'audit_T4_R7_peer_holes_raw_native_scope_r263.py').read_text()
s=s.replace('T4-R7-sparse-exact-R250-diagnostic-r262','T4-R7-sparse-exact-R250-diagnostic-r265')
s=s.replace('T4-R7-R262-independent-peer-hole-native-rule-source-scope-r263','T4-R7-R265-independent-all-hard-peers-native-scope-r266')
needle="assert len(pt)==21 and len(pv)==5"
addition="""assert len(pt)==21 and len(pv)==5
 regbase=H/'field-power/REG7-native-support-minimal-current-delta-r312'; manifest=regbase/'owned-file-manifest.json';assert sha(manifest)=='309209204292c448ccf50dd18d346d76466067ed138ac8a11f37438c7339a9e6';mf=json.loads(manifest.read_text());assert all(sha(regbase/name)==pin for name,pin in mf.items());reg=pickle.loads((regbase/'new-REG-discrete.pkl').read_bytes());rz=pickle.loads((regbase/'new-REG7-zones.pkl').read_bytes());up=H/'field-power/U11025-exact-health-ground-native-owned-recipe-r350/proposed-discrete.pkl';assert sha(up)=='438d1f9b5adc8b8255870a531107d96cbc55faa11bfca1d2500bae8202871fa5';u=pickle.loads(up.read_bytes());fieldt=reg['tracks']+u['tracks'];fieldv=reg['vias']+u['vias'];assert len(reg['tracks'])==10 and len(reg['vias'])==4 and len(rz)==7 and len(u['tracks'])==6 and len(u['vias'])==1;put(O/'hard-field-packet-binding.json',{'REG_owned_manifest_sha256':sha(manifest),'REG_discrete_sha256':sha(regbase/'new-REG-discrete.pkl'),'REG_only_new_zones_sha256':sha(regbase/'new-REG7-zones.pkl'),'U25_discrete_sha256':sha(up),'field_source_and_native_parity_authority_remains_field_R346_R350_NOT_replaced_by_SBC_contract':True,'whole_stale_models_used':False})"""
assert s.count(needle)==1;s=s.replace(needle,addition)
needle2="dru=H/'sbc-native-contract-r1/copy/board.kicad_dru';assert sha(dru)=='159c4614968368a7d88946cc71cc341f886fd22b356ced1d0738252dbeb65fe4'"
replace2=needle2+";pt+=fieldt;pv+=fieldv"
assert s.count(needle2)==1;s=s.replace(needle2,replace2)
needle3="for y in pt+pv:"
addition3="""for z in rz:
   if L.norm(z['net'])==L.norm(x['net'])or z['layer']not in layers:continue
   d=axis.distance(z['shape'])-r;req=max(float(z['clearance_mm']),gap(x['net'],z['net']))+.025;row={'kind':'hard_only_new_REG7_zone','UUID':x['uuid'],'REG_zone_UUID':z['uuid'],'layer':z['layer'],'true_gap_mm':d,'required_mm':req};checks.append(row)
   if d<req:errors.append(row)
  for y in pt+pv:"""
assert s.count(needle3)==1;s=s.replace(needle3,addition3)
s=s.replace('R263','R266')
exec(compile(s,str(__file__),'exec'))
