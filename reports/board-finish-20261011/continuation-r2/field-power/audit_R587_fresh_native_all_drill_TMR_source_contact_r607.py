"""Fresh actual CPP geometry check of the one original IO3 outline repair.

The preserved R563 checker is adapted with exact substitutions; none of its
old native graph caches are reused after the new selected refill.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'audit_native_TMR_R218_resolved_r563.py'
s=source.read_text(encoding='utf-8')
def replace(old,new):
 global s
 assert old in s,old
 s=s.replace(old,new)
replace("N=H.parent/'FA-IO3-TMR-exact-two-zone-native-selected-diagnostic-r218'", "N=H/'original-IO3-TMR-outline-only-native-API-selected-FA-IO3-r587'")
replace("OUT=H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r563'", "OUT=H/'original-IO3-TMR-R587-fresh-native-all-drill-source-contact-r607'")
for old,new in {
 'a8204097f1ee9862b5cc0f68faf7a5ab2b11005898fd821062e4b16351c3bbaf':'3e311f29e40798b65f2e6ee08d79c304f1021f5bc11da0c5657992e0fa63f8a5',
 '84bb0c848cc670a82c6dbdf2cca5353f9093855072cd127c6d6453c7020e6d7e':'ea90a5639bebaec4cc8afe28b2052e3eb5c1294c5a51f1a9acd56a8fd20fe170',
 'bdd51c56b5d6611aea20f78846cdff14765bd3b99a866249c26d952f9120d6f7':'cc0c4bdc24d1c4242c015bfac82e16f98452b8515be6b7042b622426e5de6ca5',
 '6befbca6dcac6bfe812dc8be04069701338f8ef95159faf9a5cb4a114395d55e':'73ddd001ae470e124c9cfb9f48ee8b5e4272403253463806ee04809fbb06fceb',
 '2070d8576436a8c0e7db6211849cde54757ec03edc65bf9e45784c0104ed1a1b':'ab7673669661343d44d3bed42fc566f025ada8d96d38e80b753580bd294616c7',
 'native-two-zone-API.json':'native-outline-API.json',
 'two-zone-native-expected.json':'exact-native-outline-shadow-expected.json',
}.items():replace(old,new)
replace("host=pickle.loads(HG.read_bytes());baseline=pickle.loads(BG.read_bytes())", "host=pickle.loads(HG.read_bytes());baseline=pickle.loads(BG.read_bytes());prior_native_file=H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r563/fresh-native-selected-all-drilled-groups.pkl';assert sha(prior_native_file)=='714aa0188e069e636559be9a4f49c6017d5a57fe7037808af1e42622c1a45b3b';prior_native=pickle.loads(prior_native_file.read_bytes())")
start=s.index("  cache=H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r557'")
end=s.index("actual=K.root(xs,ref,pin);",start)
s=s[:start]+"  _,xs=K.physical(candidate,net,ctx);groups[net]=xs\n  assert len(ctx[0])==len(candidate['vias'])+sum(len(L.poly(p.get('hole')or[]))for p in candidate['pads'])\n  "+s[end:]
replace("[('R515_host_final',host[net]),('R155_prior_host',baseline[net])]", "[('R515_host_final',host[net]),('R155_prior_host',baseline[net]),('R218_actual_native_before',prior_native[net])]")
replace("  if net=='/IO_3V3':", "  sr['actual_native_R218_prior_source_keys_lost']=[list(x)for x in sorted(K.keys(K.root(prior_native[net],ref,pin))-actualkeys)];sr['actual_native_R218_prior_source_named_pads']=pad_count(K.root(prior_native[net],ref,pin))\n  if net=='/IO_3V3':")
# Preserve the host-before605 touch audit and separately require all actual
# prior native layer contacts. No projected-host graph substitutes for CPP.
start=s.index("  for ly in K.LAYERS:\n   metal={}")
end=s.index("  (OUT/('fresh-native-all-drilled-",start)
block=s[start:end]
assert block.count('host[net]')==2
block=block.replace('host[net]','prior_groups').replace("'net':net,'native_discrete_layer_key'", "'net':net,'baseline':contact_baseline,'native_discrete_layer_key'")
s=s[:start]+"  for contact_baseline,prior_groups in [('R515_host_before',host[net]),('R218_actual_native_before',prior_native[net])]:\n"+'\n'.join(' '+line if line else line for line in block.rstrip('\n').split('\n'))+'\n'+s[end:]
replace("x['R515_host_prior_source_keys_lost']or x['R155_prior_source_keys_lost']", "x['R515_host_prior_source_keys_lost']or x['R155_prior_source_keys_lost']or x['actual_native_R218_prior_source_keys_lost']")
replace("actual_native_intended_API_all27_settings_rings_bound", "actual_native_intended_API_all28_settings_rings_bound")
replace("'source_graph_reuse':'Exact native K.physical/all-drill graphs written before unrelated AST parser failure; actual input geometry/flashes/pad identities independently rebound. No repeated graph calculation or weakened native predicate.'", "'source_graph_reuse':'NONE. Fresh K.physical graph rebuilt from exact R587 CPP selected refill geometry, actual pads, actual via flashes and all drills; R218 graph used only as a preserved BEFORE comparator.'")
replace("rulefile]\n receipt=", "rulefile,prior_native_file,source,Path(__file__)]\n receipt=")
replace("'host_before_direct_native_fill_contact_count':len(direct)", "'host_before_direct_native_fill_contact_count':sum(x['baseline']=='R515_host_before'for x in direct),'actual_native_before_direct_fill_contact_count':sum(x['baseline']=='R218_actual_native_before'for x in direct)")
replace("'native_actual_group_pickle_SHA256'", "'actual_native_R218_relationship_loss_count':sum(len(x['losses'])for x in contact if x['baseline']=='R218_actual_native_before'),'fresh_CPP_R587_original_outline_only_test':True,'raw_R563_original5492_closed_boundary_failure_preserved':True,'R567_eight_overlap_errors_unrepaired':True,'native_actual_group_pickle_SHA256'")
exec(compile(s,str(Path(__file__)), 'exec'))
