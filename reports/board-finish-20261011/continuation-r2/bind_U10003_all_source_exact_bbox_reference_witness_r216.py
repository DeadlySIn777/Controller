"""Exhaustive rational bounding-envelope source binding for the R199 witnesses."""
import hashlib,json,pickle,sys
from fractions import Fraction as Q
from pathlib import Path
from shapely import from_wkb
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_FIELD5_R453_literal_rational_line_membership_r189 as X
OUT=H/'U10003-all-source-exact-bbox-reference-witness-binding-r216'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bounds(s):
 ps=X.read_polys(s);pts=[p for rings in ps for ring in rings for p in ring];return(tuple(min(p[i]for p in pts)for i in(0,1)),tuple(max(p[i]for p in pts)for i in(0,1)))
def disjoint(a,b):return any(a[1][i]<b[0][i]or b[1][i]<a[0][i]for i in(0,1))
def main():
 assert not OUT.exists();OUT.mkdir();bp=H/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262/model.pkl';mp=H/'U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl'
 assert sha(bp)=='64a1f6e1597c9d757b187c3b6db85d79685ee376399bdd4738f915b87b1a0144'and sha(mp)=='dfb8050d5f45f5602692f2f4bb11c4706937a7821d57fac55a6733042314cae5';_,_,_,_,before=pickle.loads(bp.read_bytes());_,_,_,_,after=pickle.loads(mp.read_bytes());wp=H/'U10003-R196-unchanged-net-physical-identity-and-strict-oldrefs-r199/3aabe7ec-baf5-4304-ac89-079b0a62e545-direct-old-reference-loss.wkb';assert sha(wp)=='d303bde81af60cb3e7e74fd742bc249c278876fcf5d656526ac39de350eff06a';wb=bounds(from_wkb(wp.read_bytes()));rows=[];selected=[]
 for label,m in [('before',before),('after',after)]:
  _,groups=K.physical(m,'/motherboard_motors/FIELD_GND',K.hole_context(m));root=K.root(groups,'J11003','2')
  for r in root:
   if r['kind']!='fill' or r['layer']!='In1.Cu':continue
   sh=r['shape'];sb=bounds(sh);excluded=disjoint(sb,wb);row={'side':label,'UUID':r['uuid'],'actual_drilled_shape_WKB_sha256':hashlib.sha256(sh.wkb).hexdigest(),'exact_vertex_bounds':[[str(x)for x in t]for t in sb],'excluded_by_exact_rational_disjoint_bbox':excluded};rows.append(row)
   if not excluded:
    p=OUT/(label+'-'+str(len(selected))+'-'+r['uuid']+'.wkb');p.write_bytes(sh.wkb);selected.append({**row,'file':str(p),'sha256':sha(p),'individual_actual_drilled_shape_WKB_sha256':sha(p)})
 inputs={str(Path(p).resolve()):sha(p)for p in[Path(__file__),Path(X.__file__),Path(K.__file__),bp,mp,wp]}
 result={'verdict':'EXHAUSTIVE_EXACT_RATIONAL_BBOX_ALL_ACTUAL_J3_SOURCE_PIECES_BOUND','actual_identity':{'source_pad':'J11003.2','source_net':'/motherboard_motors/FIELD_GND','layer':'In1.Cu'},'raw_reference_loss_sha256':sha(wp),'exact_witness_bounds':[[str(x)for x in t]for t in wb],'all_rooted_In1_piece_rows':rows,'actual_individual_source_rows':selected,'all_omitted_pieces_excluded_only_by_exact_rational_disjoint_vertex_envelope':True,'no_GE0S_boolean_or_buffer_for_broad_phase':True,'inputs_sha256':inputs,'raw_R199_fail_preserved':True,'native_jobs':0,'adopted':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('R216_COMPLETE',len(rows),len(selected),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
