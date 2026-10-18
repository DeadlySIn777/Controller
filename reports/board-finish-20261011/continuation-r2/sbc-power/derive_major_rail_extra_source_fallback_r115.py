"""Freeze a distinct lazy search on the explicit source-barrel layer hypothesis."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent.parent
s=(H/'sbc-power/construct_major_rail_lazy_annuli_r108.py').read_text()
def replace(old,new):
    global s
    assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
replace("OUT=H/'sbc-power/major-rail-lazy-existing-annulus-feeds-r108';", "OUT=H/'sbc-power/major-rail-extra-source-layer-feeds-r115';")
replace(" rec,trees=F.build({**h,'zones':[]});outline=unary_union(C.poly(h['outline'])).buffer(-.526)", """ peer_zones=[];hard_h={**h,'vias':list(h['vias']),'tracks':list(h['tracks'])};peer_bindings=[]
 for peer in spec.get('hard_only_peer_proposals',[]):
  qf=Path(peer['zones_file']);df=Path(peer['discrete_file']);rf=Path(peer['receipt_file'])
  assert sha(qf)==peer['zones_sha256'] and sha(df)==peer['discrete_sha256'] and sha(rf)==peer['receipt_sha256']
  qs=pickle.loads(qf.read_bytes());ds=pickle.loads(df.read_bytes());assert len(qs)==peer['expected_zone_shapes']
  peer_zones+=qs
  for kind in ('vias','tracks'):
   by={q['uuid']:q for q in hard_h[kind]}
   for q in ds[kind]:
    if q['uuid'] in by:assert q==by[q['uuid']]
    else:hard_h[kind].append(q)
  peer_bindings.append(peer)
 binding['major_rail_hard_only_later_foreign_proposals']=peer_bindings
 rec,trees=F.build({**hard_h,'zones':[]});outline=unary_union(C.poly(h['outline'])).buffer(-.526)""")
replace(" for v in h['vias']]", " for v in hard_h['vias']]")
replace("   for q in zones+adds:", "   for q in zones+adds+peer_zones:")
replace("     zz,guard=N.normalize_owned_via_guards(h,[z]);", "     zz,guard=N.normalize_owned_via_guards(hard_h,[z]);")
replace("     zz,track_guard,_=AT.normalize_owned_track_guards(h,[z]);", "     zz,track_guard,_=AT.normalize_owned_track_guards(hard_h,[z]);")
replace("controller-major-rail-lazy-existing-annuli-r108/", "controller-major-rail-extra-source-annuli-r115/")
replace("'label':'Major rail lazy existing-annulus feed R108'", "'label':'Major rail explicitly prospective extra-source-layer feed R115'")
replace("print('MAJOR_RAIL_LAZY_R108_FROZEN'", "print('MAJOR_RAIL_EXTRA_SOURCE_R115_FROZEN'")
replace("'geometry_width_does_not_grant_current_or_sharing':True", "'geometry_width_does_not_grant_current_or_sharing':True,'explicit_source_layer_hypothesis_requires_native_flash_refill_and_full_foreign_contact_proof':True,'hard_only_peer_proposals':peer_bindings")
out=H/'sbc-power/construct_major_rail_extra_source_fallback_r115.py';assert not out.exists();out.write_text(s);compile(s,str(out),'exec')
print('EXTRA_SOURCE_FALLBACK_DERIVED',hashlib.sha256(out.read_bytes()).hexdigest())
