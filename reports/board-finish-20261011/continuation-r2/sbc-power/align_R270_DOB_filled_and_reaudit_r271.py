"""Align only current DOB actual filled Cu to literal repaired physical role."""
import sys,json,pickle,hashlib,copy
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import immutable_local_fill_subtraction_r254 as IM
import guarded_power_projection_r44 as Z
import construct_R7_after_T4_local_gain_reserve_r265 as M
O=H/'sbc-power/R270-true-literal-DOB-current-filled-alignment-requalification-r271'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dig(s):return hashlib.sha256(s.wkb).hexdigest()
def zero(s):n=set_precision(s,0);assert n.wkb==s.wkb;return n
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n')
def main():
 assert not O.exists();O.mkdir();rp=H/'sbc-power/DOB-R265-true-literal-zero-grid-role-local-negative-repair-r270';mp=rp/'model-with-repaired-roles-actual-filled-records-unchanged.pkl';assert sha(mp)=='4fd6a1e2a2fe0c625f967cb213dc63256709673b501c11d637416d65dd2f0be8';g,h,b,q,c=pickle.loads(mp.read_bytes());P=O/'T4-plus-R7';P.mkdir();c=copy.deepcopy(c);uid='f4863c44-a057-598a-aef7-adca7cfb15f1';physical=zero(next(z for z in q if z['uuid']==uid)['shape']);target=next(z for z in c['zones']if z['uuid']==uid);layer='In4.Cu';rs=target['fills'][layer];original=unary_union(L.poly(rs));steps=[]
 for it in range(16):
  actual=unary_union(L.poly(rs));outside=zero(actual).difference(physical)
  if outside.is_empty:break
  of=P/(uid+'-'+str(it)+'-literal-actual-filled-outside-physical-role.wkb');of.write_bytes(outside.wkb);cut=outside if it==0 else zero(Z.bounded_buffer(outside,.0001));cf=P/(uid+'-'+str(it)+'-exact-physical-alignment-negative-cut.wkb');cf.write_bytes(cut.wkb);rs,ledger=IM.subtract(rs,[cut],P,uid+'-'+str(it)+'-literal-role-physical-alignment');steps.append({'iteration':it,'actual_literal_outside_role_sha256':sha(of),'actual_literal_outside_role_area_mm2':outside.area,'negative_alignment_cut_sha256':sha(cf),'additional_local100nm_only_if_required':it>0,'immutable_per_record_zero_gain_ledger':ledger})
 final=unary_union(L.poly(rs));remaining=zero(final).difference(physical);assert remaining.is_empty;assert zero(final).difference(zero(original)).is_empty;target['fills'][layer]=rs;put(P/'only-DOB-filled-literal-role-alignment-ledger.json',steps)
 prior=H/'sbc-power/T4-R7-sparse-exact-R250-diagnostic-r265/T4-plus-R7';fills=json.loads((prior/'exact-current-filled-record-new-primitive-ledger.json').read_text());fills.append({'UUID':uid,'raw_net':target['net'],'layer':layer,'before_WKB_sha256':dig(original),'after_WKB_sha256':dig(final),'strict_no_reclaimed_Cu':True,'strict_literal_actual_Cu_inside_repaired_physical_role':True,'removed_mm2':original.difference(final).area,'only_new_ground_antipad_and_explicit_local_role_gain_correction':True,'source_alignment_steps':steps});put(P/'exact-current-filled-record-new-primitive-ledger.json',fills);(P/'model.pkl').write_bytes(pickle.dumps((g,h,b,q,c),protocol=5));put(P/'construction-receipt.json',{'verdict':'TRUE_LITERAL_ROLE_AND_ACTUAL_FILLED_DOB_REPAIR_CONSTRUCTOR_PASS_INDEPENDENT_FULL_SOURCE_PEER_GUARDS_OPEN','model_sha256':sha(P/'model.pkl'),'R270_role_repair_model_sha256':sha(mp),'actual_DOBfilled_subset_of_old_and_repaired_physical':True,'native_jobs':0,'board_written':False,'adopted':False})
 base=H/'sbc-power/T4-R7-sparse-exact-R250-diagnostic-r262/T4-only';model=pickle.loads((base/'model.pkl').read_bytes());groups=pickle.loads((base/'actual-drilled-groups.pkl').read_bytes());dp=H/'sbc-power/R7-NW-fullwidth-two-B-trunk-detour-nominations-r259/first-nominee-discrete.pkl';d=pickle.loads(dp.read_bytes());oldtracks=[t for t in model[1]['tracks']if t['uuid']in d['removed_original_track_UUIDs']];from shapely.geometry import LineString
 oldbody={(L.norm(t['net']),t['layer']):unary_union([Z.bounded_buffer(LineString([x['a'],x['b']]),x['w']/2)for x in oldtracks if(x['net'],x['layer'])==(t['net'],t['layer'])])for t in oldtracks};affected={L.norm(x['net'])for x in d['tracks']+d['vias']}|{L.norm(r['raw_net'])for r in fills};M.ns['audit'](P,model,(g,h,b,q,c),d,groups,affected,set(d['removed_original_track_UUIDs']),oldbody);print('R271_COMPLETE',sha(P/'receipt.json'),sha(P/'model.pkl'),flush=True)
if __name__=='__main__':main()
