"""Diagnostic gate for a future bound structural replay model.

The original full-plane body formula is tested for every raw RF candidate
and every previously frozen R429 reference witness, including candidates
that the fresh accelerator might omit. This is scoped, not an all-board
literal reference certification. All raw accelerator failures are retained.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,time,argparse
from pathlib import Path
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import audit_aux_exact_raw as A
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
from inventory import sha
B=H.parent/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262'
G=H/'FIELD5-R393-current-independent-all-contact-source-reference-audit-r395'
R429=H/'FIELD5-R423-original-rim-fresh-drilled-source-reference-gate-r429'
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--model',type=Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();O=args.output
 assert not O.exists();O.mkdir();started=time.monotonic();assert sha(args.model)==args.sha256
 g,h,b,q,c=pickle.loads(args.model.read_bytes());_,bh,_,_,before=pickle.loads((B/'model.pkl').read_bytes());old=pickle.loads((G/'actual-drilled-before-groups.pkl').read_bytes());prior=json.loads((R429/'receipt.json').read_text(encoding='utf-8'));removed={t['uuid']for t in bh['tracks']}-{t['uuid']for t in h['tracks']};ctx=K.hole_context(c);groups={};rows=[];tracks={t['uuid']:t for t in before['tracks']}
 for net,ref,pin in K.ROOTS[:3]:
  _,n=K.physical(c,net,ctx);groups[net]=n;a=old[net];_,contactbad=K.contact_losses(a,n,removed);ar=K.root(a,ref,pin);nr=K.root(n,ref,pin);lost=K.keys(ar)-{('track',u,ly)for u in removed for ly in K.LAYERS}-K.keys(nr);oldrefs,newrefs=K.source_refs(ar),K.source_refs(nr);bad,proof=RF.audit(before,oldrefs,newrefs,net,removed)
  frozen=next(r for r in prior['rows']if r['net']==net)['old_strict_zero_reference_losses'];ids={r['uuid']for r in bad+frozen};direct=[]
  for uid in sorted(ids):
   t=tracks[uid];ly=t['layer'];body=L.body(t)if t.get('m')is not None else A.shape({'kind':'segment',**t});gap=body.intersection(oldrefs[ly]).difference(newrefs[ly]);f=O/(uid+'-original-full-plane-direct-reference-gap.wkb');f.write_bytes(gap.wkb);direct.append({'uuid':uid,'raw_net':t['net'],'layer':ly,'formula':'(full_actual_body intersect immutable_before_source_reference) minus candidate_source_reference','is_empty':gap.is_empty,'type':gap.geom_type,'area_mm2':gap.area,'length_mm':gap.length,'bounds_mm':None if gap.is_empty else list(gap.bounds),'WKB_file':str(f.resolve()),'WKB_sha256':sha(f),'no_area_or_length_waiver':True})
  row={'net':net,'source':ref+'.'+pin,'old_contact_losses':contactbad,'prior_source_keys_lost':[list(k)for k in sorted(lost)],'raw_RF_candidate_losses':bad,'raw_RF_proof':proof,'original_formula_scoped_rows':direct,'original_formula_scoped_nonempty_count':sum(not r['is_empty']for r in direct),'actual_named_source_pad_count':len({r['uuid']for r in nr if r['kind']=='pad'and str(r['pin'])})};rows.append(row);put(O/'checkpoint.json',rows);print('R455 bank',net,'contacts',len(contactbad),'source',len(lost),'rawRF',len(bad),'direct',row['original_formula_scoped_nonempty_count'],flush=True)
 io='/IO_3V3';_,n=K.physical(c,io,ctx);groups[io]=n;_,contactbad=K.contact_losses(old[io],n,removed);ar=K.root(old[io],'R18001','2');nr=K.root(n,'R18001','2');iolost=K.keys(ar)-{('track',u,ly)for u in removed for ly in K.LAYERS}-K.keys(nr)
 io3={'old_contact_losses':contactbad,'prior_source_keys_lost':[list(k)for k in sorted(iolost)],'actual_named_source_pad_count':len({r['uuid']for r in nr if r['kind']=='pad'and str(r['pin'])}),'all_actual_immutable_before_IO3_keys_retained':not contactbad and not iolost};put(O/'IO3-source-contact.json',io3);print('R455 IO3',len(contactbad),len(iolost),flush=True)
 net='/motherboard_power_entry/FIELD_5V';_,n=K.physical(c,net,ctx);groups[net]=n;nr=K.root(n,'L11003','2');present={(r['ref'],str(r['pin']))for r in nr if r['kind']=='pad'};need=[('U11017','8'),('U11017','5'),('R11071','1'),('C11064','1'),('R9039','1'),('C11080','1'),('U11013','1'),('U11013','3'),('R11051','1')];missing=[p for p in need if p not in present]
 f=O/'actual-checked-five-net-groups.pkl';f.write_bytes(pickle.dumps(groups,protocol=5));rec={'status':'DIAGNOSTIC_SCOPED_SOURCE_AND_ORIGINAL_FORMULA_RESULTS_ONLY','model_file':str(args.model.resolve()),'model_sha256':sha(args.model),'model_raw_construction_flags_retained':b.get('FIELD5_minimal_R385_revision',b.get('field_current_successor',{})),'rows':rows,'IO3':io3,'FIELD5_nine_targets_missing':missing,'actual_groups_sha256':sha(f),'all_board_literal_reference_scope':'NOT_CLAIMED_RF_CANDIDATES_AND_ALL_PRIOR_R429_WITNESSES_ONLY','construction_raw_FAILURES_not_waived':True,'full_all_net_new_true_margin_current_native':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started};put(O/'receipt.json',rec);print('R455 receipt',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
