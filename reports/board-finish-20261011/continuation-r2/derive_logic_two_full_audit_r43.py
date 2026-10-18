"""Bind the independent R20 audit to the exact two R42 returns and R22 parent."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
src=H/'audit_logic_seven_incremental_r20.py';dst=H/'audit_logic_two_full_r43.py'
assert not dst.exists()
t=src.read_text()
replacements={
 'for the R18 delta.':'for the two R42 returns against the exact R22 parent.',
 "corrected-joint-ground-base-r11/model.pkl":"safe-logic-five-and-fag-margin-r22/model.pkl",
 "logic-source-union-reuse-return-restoration-r18/model.pkl":"logic-two-reference-safe-return-restoration-r42/model.pkl",
 "logic-seven-independent-incremental-r20":"logic-two-independent-full-r43",
 '24de27f569c8f4ae56b4172e6fc1af374c4f86c12d56215a2989eb793d2a55a8':'014b37594d378cd3e1a606cb1c06a0ad0b1b3ffea5cb836132bfaeec80d3a52a',
 '20ae7a0558877ba76300f2163b920c77fe96c5861a930fb7b22570f665ad37b8':'a4baedbfbccc92930a22c946b1e4e5262287d59b60b2a1e529bfddfa75c398ba',
 'assert len(added)==7':'assert len(added)==2',
 "changed=[];nets={'/LOGIC_GND'}":"changed=[];nets={C.norm(q['net']) for q in before['zones']}|{'/LOGIC_GND','/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V'}",
 'R20_CONTACT':'R43_CONTACT',
 'R20_SOURCE_REFERENCE':'R43_SOURCE_REFERENCE',
 'R20_COMPLETE':'R43_COMPLETE',
 'PASS_SEVEN_NEW_LOGIC_PIECES_INCREMENTAL_HOST_GEOMETRY_CONTACT_SOURCE_REFERENCE_NATIVE_CURRENT_OPEN':'PASS_TWO_NEW_LOGIC_PIECES_FULL_OLD_ZONE_NET_CONTACT_SOURCE_REFERENCE_HOST_GEOMETRY_NATIVE_CURRENT_OPEN',
 'FAIL_INCREMENTAL_SEVEN_LOGIC_PIECES_REPAIR_REQUIRED':'FAIL_TWO_LOGIC_PIECES_FULL_CONTACT_SOURCE_REFERENCE_GEOMETRY_REPAIR_REQUIRED',
 "'parent_known_FAG_planning_deficit':'5.26nm vs pad600473a0 remains separate explicit new-shape correction obligation'":"'parent_FAG_margin':'R22 outward correction retained exactly; independent R25 strict geometry PASS'"
}
for a,b in replacements.items():assert a in t,a;t=t.replace(a,b)
assert "pe=[];ze=[]" in t;t=t.replace("pe=[];ze=[]","pe=[];ze=[];he=[];ke=[]\n holes=[(p['uuid'],p['net'],s)for p in h['pads']for s in C.poly(p.get('hole')or [])]+[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=256))for v in h['vias']]\n from shapely.strtree import STRtree\n hole_tree=STRtree([s for uid,raw,s in holes])")
marker=" for q in added:\n  for i in trees[q['layer']]"
assert marker in t
t=t.replace(marker," for q in added:\n  for i in hole_tree.query(q['shape'].buffer(.3),predicate='intersects'):\n   uid,raw,s=holes[int(i)]\n   if raw==q['net']:continue\n   d=q['shape'].distance(s)\n   if d<.275:he.append({'zone_uuid':q['uuid'],'hole_uuid':uid,'actual_mm':d,'required_mm':.275})\n  for rule in h['rule_areas']:\n   if rule.get('no_zones') and q['layer'] in rule['layers']:\n    for s in C.poly(rule['outline']):\n     if q['shape'].intersects(s.buffer(.025)):ke.append({'zone_uuid':q['uuid'],'rule_area':rule.get('uuid'),'layer':q['layer']})\n  for i in trees[q['layer']]")
t=t.replace("'physical_errors':pe,'foreign_owned_zone_errors':ze","'physical_errors':pe,'foreign_owned_zone_errors':ze,'foreign_hole_errors':he,'native_no_zone_area_errors':ke")
t=t.replace('ok=not pe and not ze and not any','ok=not pe and not ze and not he and not ke and not any')
t=t.replace("'foreign_new_zone_error_count':len(ze),","'foreign_new_zone_error_count':len(ze),'foreign_hole_error_count':len(he),'native_no_zone_area_error_count':len(ke),'all_old_zone_bearing_net_count':len(nets),")
compile(t,str(dst),'exec');dst.write_text(t)
(H/'logic-two-full-audit-r43-derivation.json').write_text(json.dumps({'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'target_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'changes':'exact R22/R42 bindings, all old zone-bearing nets, explicit foreign hole and native no-zone-area checks','board_written':False,'adopted':False},indent=1)+'\n')
print(dst)
