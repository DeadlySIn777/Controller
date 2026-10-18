"""Attribute retained references to actual restored/source-filled pieces."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,sys,time
from pathlib import Path
from shapely.geometry import LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import audit_aux_exact_raw as A
import contact_layout as L
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from inventory import sha
R=H/'FIELD5-R393-current-independent-all-contact-source-reference-audit-r395'
M=H/'FIELD5-R385-minimal-R155-strict-filled-restoration-composition-r393/model.pkl'
O=H/'FIELD5-R393-retained-reference-restored-source-membership-diagnosis-r409'
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();started=time.monotonic()
 assert sha(R/'receipt.json')=='670c62f794e68f7e6a6bbd25fb5d0b5b59f18c3fea076aef76009bb1dd789303'
 g,h,b,q,c=pickle.loads(M.read_bytes());old=pickle.loads((R/'actual-drilled-before-groups.pkl').read_bytes());new=pickle.loads((R/'actual-drilled-current-groups.pkl').read_bytes());tm={t['uuid']:t for t in h['tracks']};rows=[]
 roots={'/LOGIC_GND':('J11001','2'),'/motherboard_motors/FIELD_GND':('J11003','2'),'/motherboard_do/FIELD_B_0V':('J11005','2')}
 for bank in json.loads((R/'three-bank-strict-zero-reference-rows.json').read_text()):
  net=bank['net'];rr=roots[net];ar=K.root(old[net],*rr);nr=K.root(new[net],*rr);a=K.source_refs(ar);n=K.source_refs(nr);rootkeys=K.keys(nr)
  for loss in bank['strict_ZERO_retained_old_reference_losses']:
   t=tm[loss['uuid']];body=A.shape({'kind':'segment',**t});layer=t['layer'];inner=K.MAP[layer];gap=body.intersection(a[layer]).difference(n[layer]);gf=O/(t['uuid']+'-literal-current-source-reference-gap.wkb');gf.write_bytes(gap.wkb);matches=[]
   for i,xs in enumerate(new[net]):
    if K.keys(xs)&rootkeys:continue
    for r in xs:
     if r['kind']!='fill'or r['layer']!=inner or not r['shape'].intersects(gap):continue
     hit=r['shape'].intersection(gap);matches.append({'group':i,'physical_key_count':len(K.keys(xs)),'fill_UUID':r['uuid'],'group_pad_UUIDs':sorted({r['uuid']for r in xs if r['kind']=='pad'}),'hit_mm2':hit.area,'hit_empty':hit.is_empty,'fill_bounds_mm':r['shape'].bounds})
   allfill=unary_union([r['shape']for xs in new[net]for r in xs if r['kind']=='fill'and r['layer']==inner and r['shape'].intersects(body)])
   rows.append({'bank':net,'track_UUID':t['uuid'],'raw_signal_net':t['net'],'route_layer':layer,'reference_layer':inner,'raw_R395_loss_mm2':loss['prior_source_reference_lost_mm2'],'recomputed_literal_gap_mm2':gap.area,'recomputed_literal_gap_empty':gap.is_empty,'gap_file':str(gf.resolve()),'gap_sha256':sha(gf),'gap_bounds_mm':None if gap.is_empty else gap.bounds,'current_filled_but_unrooted_piece_matches':matches,'not_in_any_current_physical_fill_mm2':gap.difference(allfill).area,'not_in_any_current_physical_fill_empty':gap.difference(allfill).is_empty})
   put(O/'checkpoint.json',rows)
 put(O/'receipt.json',{'verdict':'EXACT_RETAINED_REFERENCE_REMAINDERS_DIAGNOSIS_ONLY','R393_model_sha256':sha(M),'R395_receipt_sha256':sha(R/'receipt.json'),'rows':rows,'native_jobs':0,'geometry_changed':False,'adopted':False,'elapsed_seconds':time.monotonic()-started});print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'rows':len(rows),'unrooted_matches':sum(bool(r['current_filled_but_unrooted_piece_matches'])for r in rows)}),flush=True)
if __name__=='__main__':main()
