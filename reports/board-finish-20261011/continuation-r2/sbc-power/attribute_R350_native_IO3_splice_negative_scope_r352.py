"""Read-only exact actual negative scope witness; no area waiver or model."""
import json,sys,hashlib
from pathlib import Path
from shapely import from_wkb,set_precision
from shapely.ops import unary_union
from shapely.geometry import box
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import guarded_power_projection_r44 as Z
D=H/'sbc-power/CM79-original-IO3-record47-only-two-raw-gain-controlling-intersection-splice-proposal-r349'
O=H/'sbc-power/CM79-R350-original-record47-exact-actual-negative-scope-failure-attribution-r352'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def save(n,s):p=O/(n+'.wkb');p.write_bytes(s.wkb);return {'file':str(p.resolve()),'sha256':sha(p),'type':s.geom_type,'empty':s.is_empty,'area_mm2':s.area,'length_mm':s.length,'bounds':list(s.bounds)if not s.is_empty else None}
def main():
 assert not O.exists();O.mkdir();assert sha(D/'receipt.json')=='e15c41e4cfb28543c575827b1ba80f0f6b89e3c58b73a3369a0843beb78e2587';r=json.loads((D/'receipt.json').read_text());cut=zero(from_wkb((H/'sbc-power/CM79-R346-original-IO3-record47-exact-raw-gain-controlling-edge-attribution-r347/normal-new-primitives-only-cutter.wkb').read_bytes()));removed=zero(from_wkb(Path(r['actual_removed']['file']).read_bytes()));extra=zero(from_wkb(Path(r['additional_negative_beyond_normalcut']['file']).read_bytes()));wedges=[zero(from_wkb(Path(w['file']).read_bytes()))for row in r['rows']for w in row['exact_two_incident_wedges']];scope=zero(Z.bounded_buffer(unary_union([cut,*wedges]),.0002));whole=zero(Z.bounded_buffer(unary_union([cut,extra]),.0002));outside=removed.difference(scope);outsideWhole=removed.difference(whole);out={'verdict':'READ_ONLY_REJECTED_NATIVE_RECORD_NAMED_SCOPE_ATTRIBUTION_NO_HEAD','R349_receipt_sha256':sha(D/'receipt.json'),'bound_four_triangle_guard':save('four-incident-wedges-plus-normal-buffer200nm',scope),'strict_outside_four_incident_wedge_scope':save('actual-removed-outside-four-incident-wedge-scope',outside),'bound_actual_whole_negative_guard':save('normal-plus-exact-actual-removed-negative-buffer200nm',whole),'strict_outside_whole_actual_bound_scope':save('actual-removed-outside-whole-exact-negative-scope',outsideWhole),'outside_prior_declared_corridor':save('strict-actual-extra-outside-original-local-corridor',extra.difference(box(116,169,139,208))),'no_magnitude_waiver':True,'model_source_native_changes':0}
 (O/'receipt.json').write_text(json.dumps(out,indent=1)+'\n',encoding='utf-8');print('R352',sha(O/'receipt.json'),json.dumps(out),flush=True)
if __name__=='__main__':main()
