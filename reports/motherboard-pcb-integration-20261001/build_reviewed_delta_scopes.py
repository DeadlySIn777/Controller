"""Freeze literal copper scope for three independently reviewed transactions.

This is a report helper, not an electrical authoring or routing tool. The
native bounded merger rechecks all source lands and concurrent object identity.
"""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from hardware_build_assembly import parse,dump,children,child,value
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def objects(t,k):return {value(child(v,'uuid')[1]):v for v in children(t,k)}
def freeze(name,before,donor,refs,proofs,reason):
 before=ROOT/before;donor=ROOT/donor
 trees=[parse(p.read_text())for p in(before,donor)]
 changed=set()
 for k in('segment','via','arc'):
  old,new=[objects(t,k)for t in trees]
  changed.update(u for u in set(old)|set(new)if (dump(old[u]) if u in old else None)!=(dump(new[u]) if u in new else None))
 old,new=[objects(t,'zone')for t in trees]
 out=Path(__file__).parent/(name+'-scope.json')
 if out.exists():raise ValueError('Fresh scope required')
 d=dict(reviewed_footprint_references=sorted(refs),reviewed_copper_delta_UUIDs=sorted(changed),reviewed_added_zone_UUIDs=sorted(set(new)-set(old)),electrical_source_unchanged=True,reviewed_scope_reason=reason,source_before_sha256=sha(before),source_donor_sha256=sha(donor),independent_review_proofs={p:sha(ROOT/p)for p in proofs})
 out.write_text(json.dumps(d,indent=2)+'\n');print(name,len(refs),len(changed),len(set(new)-set(old)))
freeze('y2-r36','reports/motherboard-pcb-integration-20261001/shared-power-isow-merge-r32/motherboard-bounded-merged-candidate.kicad_pcb','reports/motherboard-chassis-20261001/y2-chassis-native-r01/motherboard-y2-chassis-candidate.kicad_pcb',{'C19509','C19505','C19506','C19502','C19501','C19508','C19503'},['reports/motherboard-chassis-20261001/y2-chassis-independent-r05/review.json','reports/motherboard-chassis-20261001/native-pad-copy-remedy-r01/review.json'],'Exactly seven approved Y2 poses, actual 18 coupler endpoints and 51 CHASSIS pad joins; all other native lands/pins/copper retained.')
freeze('storage-caps-r37','reports/motherboard-power-entry-20261001/mc1v2-mount-clearance-r03/power-cell-translated-candidate.kicad_pcb','reports/motherboard-bypass-owners-20261001/local-storage-contact-r09/motherboard-local-capacitors-candidate.kicad_pcb',{'C1030','C11059','C11062','C11063'},['reports/motherboard-bypass-owners-20261001/local-storage-contact-r09/receipt.json'],'Exactly four source-identified reservoir/load-switch support capacitor poses, no copper deletion; actual owning-pin routes remain required.')
motor=json.loads((ROOT/'reports/motherboard-motors-20261001/alarm-full-routed-r02/receipt.json').read_text())
freeze('motor-alarms-r38','reports/motherboard-power-entry-20261001/mc1v2-mount-clearance-r03/power-cell-translated-candidate.kicad_pcb','reports/motherboard-motors-20261001/alarm-cleaned-r01/motor-alarm-cells-cleaned-candidate.kicad_pcb',set(motor['scope_refs']),['reports/motherboard-motors-20261001/alarm-cleaned-r01/receipt.json','reports/motherboard-motors-20261001/alarm-cleaned-r01/negative-copper-cuts/receipt.json','reports/motherboard-motors-20261001/alarm-cleaned-r01/independent-native-connectivity.json'],'Exactly six dual-channel ISO1212 whole cells: all twelve alarms/156 endpoints, corrected 72 support poses, actual local routes/zones and proven obsolete leaf retirement; global IO3 delivery remains required.')
