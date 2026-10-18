"""Sequential read-only In1/In4 screens in one confined host budget."""
from pathlib import Path
p=Path(__file__).with_name('nominate_CM79_external_larger_port_actual_In2_source_route_r326.py')
base=p.read_text(encoding='utf-8')
for layer in ('In1','In4'):
 s=base.replace('In2',layer).replace('r326','r330').replace('R326','R330')
 s=s.replace('region=box(104,158,144,214)','region=box(10,145,215,228)').replace('[104,158,144,214]','[10,145,215,228]')
 marker=" board=zero(unary_union(L.poly(h['outline'])))"
 assert marker in s
 mask=''' audit=H/'sbc-power/CM79-R315-fresh-sparse-current-source-native-reference-audit-r316';assert sha(audit/'receipt.json')=='bb93a32c96d7aab3f624152ae916eb52b128b4c899b4bc97e41cf2c2b230c249';beforeGroups=pickle.loads((audit/'actual-drilled-before-groups.pkl').read_bytes());beforeLG=K.root(beforeGroups['/LOGIC_GND'],'J11001','2');mappedLayers=MAPPEDLAYERS;ref=zero(K.source_refs(beforeLG)[REFKEY]);supported=[]
 for t in c['tracks']:
  if t['layer']not in mappedLayers or dom.get(L.norm(t['net']))!=dom['/LOGIC_GND']:continue
  bodies=[zero(L.body({**t,'a':aa,'b':bb}))for aa,bb in((old['a'],[116.2,202.35]),([120.1,202.35],old['b']))]if t['uuid']==old['uuid']else[zero(L.body(t))]
  for body in bodies:
   if not body.envelope.intersects(wide):continue
   support=body.intersection(ref)
   if support.is_empty:continue
   obstacles.append(buf(support,.900003));supported.append({'old_UUID':t['uuid'],'layer':t['layer'],'kind':'exact_BEFORE_supported_whole_old_track_body_all_dimensions_hard','supported_WKB_sha256':hashlib.sha256(support.wkb).hexdigest(),'actual_native_LG_track_antipad_mm':.900})
 for z in q:
  if z['layer']not in mappedLayers or dom.get(L.norm(z['net']))!=dom['/LOGIC_GND']or not z['shape'].intersects(wide):continue
  support=zero(z['shape']).intersection(ref)
  if support.is_empty:continue
  obstacles.append(buf(support,.900003));supported.append({'old_UUID':z['uuid'],'layer':z['layer'],'kind':'exact_BEFORE_supported_DC_body_no_shadow_over_missing_before','supported_WKB_sha256':hashlib.sha256(support.wkb).hexdigest(),'actual_native_LG_track_antipad_mm':.900})
 put(O/'exact-source-bank-old-reference-hard-mask-ledger.json',{'before_actual_source_audit_receipt_sha256':sha(audit/'receipt.json'),'mapped_old_layers':mappedLayers,'actual_native_LG_local_clearance_mm':.25,'new_fullwidth_track_antipad_radius_mm':.9,'every_old_supported_track_or_DC_body_no_ownhole_or_dimension_waiver':supported})
'''.replace('MAPPEDLAYERS',"('F.Cu','In2.Cu')"if layer=='In1'else"('B.Cu','In3.Cu')").replace('REFKEY',"'F.Cu'"if layer=='In1'else"'B.Cu'")
 s=s.replace(marker,mask+marker)
 s=s.replace("started=time.monotonic();assert not O.exists();O.mkdir()", "started=time.monotonic();assert not O.exists();O.mkdir();(O/'exact-expanded-read-only-layer-screen.py').write_text(EXPANDED,encoding='utf-8')")
 namespace={'__name__':'_read_only_source_layer_screen','__file__':str(__file__),'EXPANDED':s};exec(compile(s,str(__file__),'exec'),namespace)
 try:namespace['main']()
 except Exception:
  namespace['put'](namespace['O']/'failure.json',{'traceback':namespace['traceback'].format_exc(),'script_sha256':namespace['sha'](__file__)})
  raise
