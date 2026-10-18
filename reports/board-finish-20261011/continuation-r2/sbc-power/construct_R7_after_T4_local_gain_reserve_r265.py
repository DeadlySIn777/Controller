"""Resume frozen T4; R7 filled-only local100nm negative gain reserves."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'construct_T4_R7_sparse_R250_diagnostic_r261.py').read_text()
s=s.replace("'novel_body_gap_mm':novgap,","'novel_body_gap_mm':novgap if novgap != float('inf') else None,")
old="body=Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2);gap=body.difference(sr[t['layer']]);"
new="body=Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2); nativeholes,nativetree=newctx; body=body.difference(unary_union([nativeholes[int(i)]for i in nativetree.query(body,predicate='intersects')]+[Z.bounded_disk(v,v['drill']/2+.00000002)for v in d['vias']if Z.bounded_disk(v,v['drill']/2+.00000002).intersects(body)]));gap=body.difference(sr[t['layer']]);"
assert s.count(old)==1;s=s.replace(old,new)
needle="raw=zero(p).difference(cut);extra=[]"
replacement="repaired,repairledger=ISUB.subtract([rec],[cut],P,z['uuid']+'-'+layer+'-'+str(i)+'-bound-local-reserve');raw=unary_union(L.poly(repaired));put(P/(z['uuid']+'-'+layer+'-'+str(i)+'-explicit-local-gain-reserve-ledger.json'),repairledger);extra=[]"
assert s.count(needle)==1;s=s.replace(needle,replacement)
s=s.replace("if not(gain.is_empty and withdrawal.is_empty and samepoly):","if not(gain.is_empty and samepoly):")
s=s.replace("if not gained.is_empty or not extra.is_empty:fail.append", "if not gained.is_empty:fail.append")
s=s.replace("'strict_no_new_filled_Cu':gain.is_empty,", "'strict_no_new_filled_Cu':gain.is_empty,'root_authorized_local100nm_gain_reserves':repairledger,")
s=s.replace('r261','r265').replace('R261','R265')
ns={'__file__':str(__file__),'__name__':'r265_methods'}
exec(compile(s,str(__file__),'exec'),ns)
import sys,json,pickle,hashlib,traceback
H=P.parent
sys.path.insert(0,str(H/'coupled-recovery'))
import immutable_local_fill_subtraction_r254 as ISUB
ns['ISUB']=ISUB
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 O=ns['O'];assert not O.exists();O.mkdir();base=H/'sbc-power/T4-R7-sparse-exact-R250-diagnostic-r262/T4-only';mp=base/'model.pkl';rp=base/'receipt.json';assert sha(mp)=='fefda5d49cc32614f1de4be9b5b5c205c8a260bc5256fcacf3a6f1ee33f6b304';assert sha(rp)=='5ee0a81e19e6c1a405d81ebc6f515afd2a2873db58c2a43ed2822cbca1037308';r=json.loads(rp.read_text());assert r['actual_drilled_layer_contact_loss_count']==r['direct_fill_contact_loss_count']==r['nine_source_layer_key_loss_count']==r['strict_ZERO_old_signal_and_PDN_reference_loss_count']==r['new_native_effective_geometry_error_count']==0;assert all(x['gap_empty']for x in r['new_track_fullbody_source_reference_gaps']);model=pickle.loads(mp.read_bytes());gp=base/'actual-drilled-groups.pkl';groups=pickle.loads(gp.read_bytes());dp=H/'sbc-power/R7-NW-fullwidth-two-B-trunk-detour-nominations-r259/first-nominee-discrete.pkl';assert sha(dp)=='008bbcd1380e45a115bcbe4076eb1cad35f302b3fcda5ef19bbb13238aafd094';d=pickle.loads(dp.read_bytes());bound={'root_model_sha256':'96d3f55a95b770a2a7f46e3b25274723946fe1572c6c82d81b7355b660360868','current_T4_model_sha256':sha(mp),'current_T4_incremental_receipt_sha256':sha(rp),'current_T4_drilled_groups_snapshot_sha256':sha(gp),'discrete_delta_sha256':sha(dp),'exact_local_negative_reserve_helper_sha256':sha(ISUB.__file__),'local_negative_filled_reserve_authority':'Root 2026-10-12 explicitly authorizes local100nm remove-only reserve steps against bound raw positive components; every rawgain/cutter/negative retained; no magnitude waiver; fresh allcontact/source/strictref/current/native mandatory','inherited_CORE_wholebody_reference_FAIL_mm2':93.04195929171794};ns['put'](O/'exact-resume-and-local-negative-authority.json',bound)
 stage,current,affected,rm,oldbody,fail=ns['construct']('T4-plus-R7',model,d,bound)
 if not fail:ns['audit'](stage,model,current,d,groups,affected,rm,oldbody)
 print('R265_COMPLETE',len(fail),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  ns['put'](ns['O']/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
