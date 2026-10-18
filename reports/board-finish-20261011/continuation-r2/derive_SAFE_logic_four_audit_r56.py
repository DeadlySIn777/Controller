"""Bind independent R43 geometry to R55 and compare all contacts to R42."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=H/'audit_logic_two_full_r43.py';dst=H/'audit_SAFE_logic_four_full_r56.py'
assert not dst.exists()
s=src.read_text()
replacements={
 'safe-logic-five-and-fag-margin-r22/model.pkl':'sbc-power/SAFE-repaired-owned-zone-normalization-r160/model.pkl',
 'logic-two-reference-safe-return-restoration-r42/model.pkl':'SAFE-logic-four-return-restoration-r55/model.pkl',
 'logic-two-independent-full-r43':'SAFE-logic-four-independent-full-r56',
 '014b37594d378cd3e1a606cb1c06a0ad0b1b3ffea5cb836132bfaeec80d3a52a':'d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b',
 'a4baedbfbccc92930a22c946b1e4e5262287d59b60b2a1e529bfddfa75c398ba':'5499e67855ab47dcf207a3421c5bb630b56af52031e06c90e270312baf03232b',
 'assert len(added)==2':'assert len(added)==1',
 'R43_CONTACT':'R56_CONTACT','R43_SOURCE_REFERENCE':'R56_SOURCE_REFERENCE','R43_COMPLETE':'R56_COMPLETE',
 'PASS_TWO_NEW_LOGIC_PIECES_FULL_OLD_ZONE_NET_CONTACT_SOURCE_REFERENCE_HOST_GEOMETRY_NATIVE_CURRENT_OPEN':'PASS_SAFE_FOUR_PAD_RESTORATION_FULL_ROOT42_CONTACT_SOURCE_REFERENCE_NATIVE_CURRENT_OPEN',
 'FAIL_TWO_LOGIC_PIECES_FULL_CONTACT_SOURCE_REFERENCE_GEOMETRY_REPAIR_REQUIRED':'FAIL_SAFE_FOUR_PAD_RESTORATION_ROOT42_CONTACT_SOURCE_REFERENCE_GEOMETRY_REPAIR_REQUIRED',
 "'all_original_Cu_holes_source_poses_native_outlines_unchanged_to_parent':True":"'all_original_Cu_holes_source_poses_native_outlines_unchanged_to_R160_parent':True,'contact_reference_baseline_root42_model_sha256':sha(contactbase)",
 "'parent_FAG_margin':'R22 outward correction retained exactly; independent R25 strict geometry PASS'":"'parent_existing36_owned_shapes_strict_R161_receipt_sha256':sha(parentstrict)"
}
for a,b in replacements.items():assert a in s,a;s=s.replace(a,b)
needle=" beforez={q['uuid']:q for q in before['zones']};changed=[];"
replacement=" contactbase=H/'logic-two-reference-safe-return-restoration-r42/model.pkl';assert sha(contactbase)=='a4baedbfbccc92930a22c946b1e4e5262287d59b60b2a1e529bfddfa75c398ba'\n parentstrict=H/'sbc-power/SAFE-repaired-independent-true-geometry-r161/receipt.json';assert sha(parentstrict)=='c69486b72b0391cfd4064368febec14b12e81c47ce4fd2b1484bddcf06f47991' and json.loads(parentstrict.read_bytes())['verdict']=='PASS_STRICT_TRUE_GEOMETRY_SCOPE'\n _,_,_,_,before=pickle.loads(contactbase.read_bytes())\n beforez={q['uuid']:q for q in before['zones']};changed=[];"
assert needle in s;s=s.replace(needle,replacement)
s=s.replace("holes=[(p['uuid'],p['net'],s)for p in h['pads']for s in C.poly(p.get('hole')or [])]+[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=256))for v in h['vias']]","holes=[(p['uuid'],p['net'],s,0.0)for p in h['pads']for s in C.poly(p.get('hole')or [])]+[(v['uuid'],v['net'],Point(v['x'],v['y']),v['drill']/2)for v in h['vias']]")
s=s.replace("hole_tree=STRtree([s for uid,raw,s in holes])","hole_tree=STRtree([s for uid,raw,s,radius in holes])")
s=s.replace("hole_tree.query(q['shape'].buffer(.3),predicate='intersects')","hole_tree.query(q['shape'].buffer(1.5),predicate='intersects')")
s=s.replace("uid,raw,s=holes[int(i)]","uid,raw,s,radius=holes[int(i)]").replace("d=q['shape'].distance(s)\n   if d<.275:","d=q['shape'].distance(s)-radius\n   if d<.275:")
compile(s,str(dst),'exec');dst.write_text(s)
(H/'SAFE-logic-four-r56-audit-derivation.json').write_text(json.dumps({'source_file':str(src),'source_sha256':sha(src),'derived_file':str(dst),'derived_sha256':sha(dst),'geometry_delta_parent':'R160 exact36 previously strict-passed owned shapes','all76_contact_source_old_reference_baseline':'R42 exact last accepted ground model','true_foreign_drill_radius_subtraction':True,'native_jobs':0,'adopted':False},indent=1)+'\n')
print(dst)
