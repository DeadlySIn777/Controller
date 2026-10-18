"""Independent fresh geometry/source/ref audit of the exact R350 diagnostic."""
from pathlib import Path
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/audit_CM79_R315_fresh_sparse_source_native_reference_r316.py'
s=p.read_text(encoding='utf-8').replace('CM79-R315-fresh-sparse-current-source-native-reference-audit-r316','CM79-R350-fresh-all-current-source-native-reference-audit-r351').replace('R316','R351')
s=s.replace("p=H/'sbc-power/CM79-exact-R289-existing-return-fullwidth-sparse-diagnostic-r315'", "p=H/'sbc-power/CM79-exact-R333-larger-power-port-local-q053-sparse-current-diagnostic-original-vertex-splice-r350'")
s=s.replace("assert sha(p/'receipt.json')=='2c86eed57b368e0470cfaa0540899b2c446e758b6e359fae234e82d977227106';", "boundReceipt=sha(p/'receipt.json');assert r['native_IO3_record47_only_two_bound_new_intersection_replay_R349']and r['all_generated_and_current_filled_literal_remove_only'];")
s=s.replace("sha(mp)==r['model_sha256']=='df44ef8d66cc4bea0b2dd1bf1e8ab9d9c54e4c88e41c92fefd0301f5555391bf'", "sha(mp)==r['model_sha256']")
s=s.replace("sha(bp)=='a5340075975ddad925b57663d475978eba7f346c3709e93fa6b67064cbf4ccec'", "sha(bp)=='f9df66060a0f45959c4234f698500070c1ba2b4837894eee644cec36891dce9b'")
s=s.replace('only-CM79-six-tracks-two-power-vias-one-exact-old-delete.pkl','only-CM79-fullwidth-tracks-one-larger-power-via-one-exact-old-delete.pkl').replace('len(nt)==6 and len(nv)==2','len(nt)==19 and len(nv)==1').replace('len(native)==8 and len(parsed)==8','len(native)==20 and len(parsed)==20')
needle="assert all(a['uuid']==z['uuid']and all(a[role].wkb==z[role].wkb for role in('shape','zone_outline_shape'))for a,z in zip(q,bq));"
assert needle in s
s=s.replace(needle,"assert all(a['uuid']==z['uuid']and{k:v for k,v in a.items()if k not in('shape','zone_outline_shape')}=={k:v for k,v in z.items()if k not in('shape','zone_outline_shape')}and all(zero(a[role]).difference(zero(z[role])).is_empty for role in('shape','zone_outline_shape'))for a,z in zip(q,bq));")
s=s.replace("'all_q_roles_WKB_exact':True", "'all_q_native_settings_exact_and_roles_literal_no_gain':True")
s=s.replace("assert bh['vias']==ch['vias']and bh['pads']==ch['pads'];", '')
s=s.replace("pairs=json.loads((p/'bound-existing-return-port-and-fullwidth-proposal.json').read_text());conditional=[]", "pairs=json.loads((p/'bound-current-existing-return-fullwidth-source-embed-proposal.json').read_text());assert .9<=pairs['screen']['actual_ordinary_ground_pair_distance_mm']<=1.0;conditional=[]")
s=s.replace("((.0001+plating*.000001)**2-.0001**2)","((.00025+plating*.000001)**2-.00025**2)")
s=s.replace("'conditional_two_F_to_In2_used_barrels_length_each_mm':.620,'series_two_barrel_R_ohm':2*barrel,'series_two_barrel_drop_mV':current*2*barrel*1000,'series_two_barrel_power_W':current*current*2*barrel", "'conditional_single_1p0_0p5_F_to_In2_barrel_length_mm':.620,'conditional_single_barrel_R_ohm':barrel,'conditional_single_barrel_drop_mV':current*barrel*1000,'conditional_single_barrel_power_W':current*current*barrel")
s=s.replace('conditional-signed-current-two-single-barrel-bottleneck.json','conditional-signed-current-one-larger-barrel-bottleneck.json')
needle="lg=K.root(groups['/LOGIC_GND'],'J11001','2');"
assert needle in s
extra="""retainedAnchors=[];ownedDCrefs=[]
 for bank,rootref,pin in ROOTS:
  if rootref not in('J11001','J11003','J11005'):continue
  ab=K.root(oldgroups[bank],rootref,pin);an=K.root(groups[bank],rootref,pin);ar={ly:zero(sh)for ly,sh in K.source_refs(ab).items()};nr={ly:zero(sh)for ly,sh in K.source_refs(an).items()}
  if bank=='/LOGIC_GND':
   for t in nt:
    if t['net']=='/LOGIC_GND'or t['layer']!='F.Cu':continue
    actual=zero(unary_union([rr['shape']for xs in groups[L.norm(t['net'])]for rr in xs if rr['kind']=='track'and rr['uuid']==t['uuid']and rr['layer']=='F.Cu']));prior=actual.intersection(ar['F.Cu']);supported=actual.intersection(nr['F.Cu']);lost=prior.difference(supported);fn=O/(t['uuid']+'-retained-fullwidth-F-before-supported-anchor-loss.wkb');fn.write_bytes(lost.wkb);retainedAnchors.append({'UUID':t['uuid'],'before_supported_Cu_mm2':prior.area,'literal_before_supported_loss_EMPTY':lost.is_empty,'loss_type':lost.geom_type,'loss_area_mm2':lost.area,'loss_WKB_sha256':sha(fn),'deleted_dc1a_UUID_exclusion_not_applied':True})
  for z in bq:
   ly=z['layer'];net=L.norm(z['net'])
   if ly not in ar or net==bank or before['domains_normalized'].get(net)!=before['domains_normalized'][bank]:continue
   body=zero(z['shape']);prior=body.intersection(ar[ly]);supported=body.intersection(nr[ly]);lost=prior.difference(supported)
   if not lost.is_empty:
    fn=O/(z['uuid']+'-'+bank.replace('/','_')+'-strict-owned-before-supported-DC-body-reference-loss.wkb');fn.write_bytes(lost.wkb);ownedDCrefs.append({'bank':bank,'UUID':z['uuid'],'net':z['net'],'layer':ly,'before_supported_area_mm2':prior.area,'literal_loss_type':lost.geom_type,'literal_loss_area_mm2':lost.area,'loss_WKB_sha256':sha(fn),'unsupported_before_DC_portions_not_invented_as_reference':True})
 put(O/'retained-original-fullwidth-F-before-supported-anchor-proof.json',retainedAnchors);put(O/'strict-all-owned-before-supported-DC-body-reference-losses.json',ownedDCrefs)
 lg=K.root(groups['/LOGIC_GND'],'J11001','2');"""
s=s.replace(needle,extra)
s=s.replace("'model_sha256':sha(mp),'parent_model_sha256':sha(bp)","'model_sha256':sha(mp),'bound_constructor_receipt_sha256':boundReceipt,'parent_model_sha256':sha(bp),'retained_F_anchor_before_supported_loss_count':sum(not x['literal_before_supported_loss_EMPTY']for x in retainedAnchors),'owned_before_supported_DC_body_reference_loss_count':len(ownedDCrefs)")
s=s.replace("for z in after['zones']:\n  for ly,rs in z['fills'].items():filled[ly].extend({'kind':'fill','uuid':z['uuid'],'net':z['net'],'local':float(z['clearance_mm']),'shape':sh}for sh in L.poly(rs))", "for z in after['zones']:\n  for ly,rs in z['fills'].items():filled[ly].extend({'kind':'fill','uuid':z['uuid'],'net':z['net'],'local':float(z['clearance_mm']),'shape':sh}for sh in L.poly(rs))\n for z in q:filled[z['layer']].append({'kind':'owned_physical_zone','uuid':z['uuid'],'net':z['net'],'local':float(z['clearance_mm']),'shape':z['shape']})")
exec(compile(s,str(__file__),'exec'))
