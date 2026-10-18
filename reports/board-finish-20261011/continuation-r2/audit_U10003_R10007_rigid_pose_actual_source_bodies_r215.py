"""Test the nominated pads against real source Cu after removing both old pads."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely import affinity
from shapely.geometry import Point,box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
OUT=H/'U10003-R10007-rigid-pose-actual-source-bodies-r215'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not OUT.exists();OUT.mkdir();rp=H/'U10003-R10007-shared-return-exact-nine-body-rigid-pose-nomination-r214/receipt.json';assert sha(rp)=='a645e05be1d9db7bc161891c18cd77f1ad80fb9487903e39d2d8417a77748b7d';r=json.loads(rp.read_bytes());mp=H/'U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl';assert sha(mp)==r['model_sha256'];g,h,b,q,current=pickle.loads(mp.read_bytes());fp=r['original_footprint'];pads={p['num']:p for p in r['original_pads']};ids={p['uuid']for p in pads.values()};LG='/LOGIC_GND';SIG='/motherboard_do/DOA_SDI_HOST';assert K.L.norm(pads['1']['net'])==SIG and K.L.norm(pads['2']['net'])==LG
 without={**current,'pads':[p for p in current['pads']if p['uuid']not in ids]};ctx=K.hole_context(without);_,lg=K.physical(without,LG,ctx);root=K.root(lg,'J11001','2');_,oldlg=K.physical(current,LG,K.hole_context(current));oldroot=K.root(oldlg,'J11001','2');loss=sorted(k for k in K.keys(oldroot)-K.keys(root)if not(k[0]=='pad'and k[1]in ids));assert not loss
 _,signal=K.physical(without,SIG,ctx);signalrows=[{'group':i,'discrete_keys':len(K.keys(xs)),'actual_pads':[{'ref':x['ref'],'pin':x['pin'],'UUID':x['uuid'],'layer':x['layer']}for x in xs if x['kind']=='pad']}for i,xs in enumerate(signal)];LGbody=unary_union([x['shape']for x in root if x['layer']=='B.Cu']);ref=unary_union([x['shape']for x in root if x['kind']=='fill'and x['layer']=='In4.Cu']);SIGbody=unary_union([x['shape']for xs in signal for x in xs if x['layer']=='B.Cu']);rows=[];win=box(208,135,232,158)
 for name,s in [('actual-J1-B-source',LGbody.intersection(win)),('actual-J1-In4-reference',ref.intersection(win)),('actual-retained-SDI-B-Cu',SIGbody.intersection(win))]:(OUT/(name+'.wkb')).write_bytes(s.wkb)
 for nominee in r['nominees']:
  angle,dx,dy=nominee['pose'];trans=lambda s:affinity.translate(affinity.rotate(s,angle,origin=(fp['x'],fp['y'])),dx,dy);row={'pose':nominee['pose'],'pad_body_reference':[]}
  for num,p in pads.items():
   s=trans(unary_union(K.L.poly(p['layers']['B.Cu'])));gap=s.difference(ref);target=LGbody if num=='2'else SIGbody;row['pad_body_reference'].append({'pin':num,'new_center_mm':nominee['pad_centres_mm'][num],'full_actual_J1_In4_reference_gap_mm2':gap.area,'reference_gap_empty':gap.is_empty,'finite_actual_retained_B_Cu_overlap_mm2':s.intersection(target).area,'actual_retained_B_Cu_distance_mm':s.distance(target)});(OUT/(str(angle)+'-pin'+num+'-full-actual-source-reference-gap.wkb')).write_bytes(gap.wkb)
  rows.append(row)
 result={'verdict':'ACTUAL_SOURCE_PAD_FEASIBILITY_ONLY_JOINT_ROUTES_AND_NATIVE_OPEN','nomination_receipt_sha256':sha(rp),'model_sha256':sha(mp),'both_old_pad_UUIDs_removed_before_all_source_queries':sorted(ids),'all_prior_actual_J1_source_keys_retained_after_old_pad_withdrawal':True,'actual_SDI_retained_group_rows':signalrows,'rows':rows,'source_reference_and_new_body_gaps_not_waived':True,'scope':'Source bodies before any planned R10007 or clock/fault/ground rewiring; no model mutation or graph adoption','native_jobs':0,'adopted':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('R215_COMPLETE',sha(OUT/'receipt.json'),json.dumps(rows),flush=True)
if __name__=='__main__':main()
