"""True new-plane geometry plus exact role/fill/direct-contact supplement."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'Q0-R504-owned-roles-and-direct-contacts-r508-derived-auditor.py'
code=base.read_text()
replacements={
 'Q0-R504-owned-roles-and-direct-contacts-r508':'Q0-R518-new-ground-plane-owned-roles-direct-contacts-r522',
 "mp=H/'Q0-owned-actual-fill-strict-local-negative-successor-r504/model.pkl'":"mp=H/'Q0-two-SMD-reference-only-owned-FA-recess-current-r518/model.pkl'",
 'f738f9a4891664324f3e09511276036e77d94e12471713762d7998121d10593a':'6a042063ca93b82533b30dcefed2366b5f80efaab6e5e06e1c862314d3193d50',
 'Q0-R504-explicit-final-current-r506':'Q0-R518-full-current-contacts-source-reference-r520',
 '8eeddecee7280d2e881282eca828c3e2a209a82c89601e38bfc61fd82c88f38a':'2a729246c74cc0e9ab25eba0da73a36455850ce5cc044abc9f8788c49515b87d',
 'R506_actual_reference_source_contact_receipt_sha256':'R520_actual_reference_source_contact_receipt_sha256',
 " a=by0[z['uuid']]":" if z['uuid']=='637c65c4-b144-5c66-8c11-42e9f8bf96bc':continue\n a=by0[z['uuid']]",
}
for old,new in replacements.items():assert old in code,old;code=code.replace(old,new)
needle="put(out/'all-new-primitives-to-actual-current-owned-physical-roles.json',checks)"
assert code.count(needle)==1
addition="""# The only positive new plane uses its literal nm physical boundary and
# current actual native flash masks; every foreign cap is measured exactly.
ground=next(z for z in q if z['uuid']=='637c65c4-b144-5c66-8c11-42e9f8bf96bc');plane=set_precision(ground['shape'],0);GND=K.L.norm(ground['net']);layer=ground['layer'];assert layer=='In1.Cu';positiveChecks=[]
def positive(kind,other,raw,d,local=.25):
 requirement=max(.25,float(local),gap(ground['net'],raw));row={'kind':kind,'new_owned_ground_UUID':ground['uuid'],'other_UUID':other,'raw_net':raw,'layer':layer,'true_gap_mm':d,'native_requirement_mm':requirement,'planner_requirement_mm':requirement+.025};positiveChecks.append(row)
 if d<requirement:nativebad.append(row)
 if d<requirement+.025:plannerbad.append(row)
records,trees=K.F.build({**h,'zones':[]})
for j in trees[layer].query(plane.buffer(.9),predicate='intersects'):
 r=records[layer][int(j)]
 if K.L.norm(r['net'])==GND:continue
 if r['kind']=='track'and not r['source'].get('m'):t=r['source'];d=LineString([t['a'],t['b']]).distance(plane)-t['w']/2
 elif r['kind']=='via':v=r['source'];width=v['d']if layer in v['flashed']else v['drill'];d=Point(v['x'],v['y']).distance(plane)-width/2
 else:d=r['shape'].distance(plane)
 positive('true_new_ground_to_native_'+r['kind'],r['uuid'],r['net'],d)
for z in q:
 if z['layer']!=layer or K.L.norm(z['net'])==GND or z['shape'].distance(plane)>.9:continue
 positive('true_new_ground_to_current_owned_physical_role',z['uuid'],z['net'],set_precision(z['shape'],0).distance(plane),z['clearance_mm'])
for z in after['zones']:
 if K.L.norm(z['net'])==GND:continue
 for p in K.L.poly(z['fills'].get(layer,[])):
  if p.distance(plane)>.9:continue
  positive('true_new_ground_to_current_actual_filled_piece',z['uuid'],z['net'],p.distance(plane),z['clearance_mm'])
for v in h['vias']:
 if K.L.norm(v['net'])==GND:continue
 d=Point(v['x'],v['y']).distance(plane)-v['drill']/2
 if d>.9:continue
 row={'kind':'new_ground_every_foreign_drill','other_UUID':v['uuid'],'raw_net':v['net'],'layer':layer,'guarded_drill_edge_gap_mm':d-.005,'required_mm':.275};positiveChecks.append(row)
 if d-.005<.275:plannerbad.append(row)
for p in h['pads']:
 if K.L.norm(p['net'])==GND:continue
 for hole in K.L.poly(p.get('hole')or[]):
  d=hole.distance(plane)
  if d>.9:continue
  row={'kind':'new_ground_every_foreign_pad_drill','other_UUID':p['uuid'],'raw_net':p['net'],'layer':layer,'guarded_drill_edge_gap_mm':d-.005,'required_mm':.275};positiveChecks.append(row)
  if d-.005<.275:plannerbad.append(row)
for r in h['rule_areas']:
 if layer in r['layers']and r.get('no_zones')and any(s.distance(plane)<.025 for s in K.L.poly(r['outline'])):nativebad.append({'kind':'new_ground_native_no_zones','UUID':r['uuid']})
put(out/'only-positive-new-ground-true-cap-hole-pad-native-rule-and-current-peer-ledger.json',positiveChecks)
"""
code=code.replace(needle,addition+needle)
code=code.replace("'current_owned_true_checks':len(checks)","'current_owned_true_checks':len(checks),'new_positive_ground_true_checks':len(positiveChecks),'new_ground_UUID':ground['uuid'],'whole_moved_SMD_body_reference_gate_empty':all(r['new_whole_SMD_body_gap_empty']for r in audit['new_SMD_whole_body_reference_rows'])")
derived=H/'Q0-R518-new-ground-plane-owned-roles-direct-contacts-r522-derived-auditor.py';assert not derived.exists();derived.write_text(code)
exec(compile(code,str(derived),'exec'))
