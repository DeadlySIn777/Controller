"""Freeze literal old/new fill primitives and local wedge causes; no geometry changes."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,time,hashlib
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import audit_aux_exact_raw as A
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
M=H/'R543-four-unions-bound-exact-line-owned-scopes-r631/model.pkl'
P=H/'FIELD5-source-plane-exact-owned-edge-negative-redesign-current-r543/model.pkl'
B=H/'FIELD5-R543-full-exact-net-source-contact-reference-geometry-r545'
D=H/'four-minimal-owned-unions-actual-all-drill-source-contact-reference-r635'
OUT=H/'three-owned-union-reference-loss-individual-primitive-attribution-r637'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(s):return hashlib.sha256(s.wkb).hexdigest()
def ds(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hs(s)}
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def save(name,s):
 f=OUT/(name+'.wkb');f.write_bytes(s.wkb);return {'file':str(f),'file_SHA256':sha(f),**ds(s)}
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic();assert sha(M)=='8dacfdb44f609ecbd3fcfb9280aac624eca7d03e3bf6d50ada3dbe3ac230887a';assert sha(P)=='474949d472a1870320b95cd494d4c96f79735b43632076d237d432d10c006416';assert sha(D/'receipt.json')=='2eab63509cd43f768e1da9c776c9b564bc51bd8679cb9a685dc41152433bd112'
 g,h,b,q,c=pickle.loads(M.read_bytes());pg,ph,pb,pq,pc=pickle.loads(P.read_bytes());assert g==pg and h==ph
 r=json.loads((D/'receipt.json').read_bytes());oldfile=B/'actual-drilled-current-groups.pkl';newfile=D/'actual-drilled-current-groups.pkl';assert sha(oldfile)==r['before_actual_group_SHA256']and sha(newfile)==r['actual_current_groups_SHA256'];old=pickle.loads(oldfile.read_bytes());new=pickle.loads(newfile.read_bytes())
 pkt=M.parent/'only-four-current-member-to-inward-union-and-local-current-record-operations.pkl';assert sha(pkt)=='64d4ab1f883da3becc6b23fb5e23121b6b5ae68563549578f41d833f78952822';packet=pickle.loads(pkt.read_bytes());roots={n:(ref,pin)for n,ref,pin in K.ROOTS};tracks={t['uuid']:t for t in pc['tracks']};rows=[];paircache={}
 for ix,fail in enumerate(r['incremental_reference_losses']):
  assert fail['kind']=='old_routed_track';net=fail['bank'];ref,pin=roots[net];ly=K.MAP[fail['layer']]
  if (net,ly)not in paircache:
   aa=[v for v in K.root(old[net],ref,pin)if v['kind']=='fill'and v['layer']==ly];nn=[v for v in K.root(new[net],ref,pin)if v['kind']=='fill'and v['layer']==ly];ar=unary_union(sorted([v['shape']for v in aa],key=hs));nr=unary_union(sorted([v['shape']for v in nn],key=hs));parts=RF.parts(ar.difference(nr));paircache[net,ly]=(aa,nn,ar,nr,parts,STRtree(parts))
  aa,nn,ar,nr,parts,tree=paircache[net,ly];t=tracks[fail['uuid']];body=A.shape({'kind':'segment',**t})if t.get('m')is None else L.body(t);ids=tree.query(body.envelope.buffer(1e-9),predicate='intersects');selected=unary_union([parts[int(j)]for j in ids]);assert hs(selected)==fail['exact_local_delta_WKB_sha256'];loss=body.intersection(selected);assert not loss.is_empty and loss.area==fail['prior_source_reference_lost_mm2']
  header=f"track-{ix}-{t['uuid']}";witness=save(header+'-strict-before-minus-after-reference-loss',loss);save(header+'-actual-track-body',body);save(header+'-selected-reference-delta',selected);envelope=loss.envelope.buffer(.000005)
  # Preserve each literal source primitive independently; no union predicate substitutes for it.
  candidates=[]
  for side,items in (('before',aa),('after',nn)):
   for j,v in enumerate(items):
    if v['shape'].envelope.intersects(envelope):
     sf=save(header+f'-{side}-individual-primitive-{j}',v['shape']);candidates.append({'side':side,'source_fill_UUID':v['uuid'],'source_fill_layer':v['layer'],'literal_geometry':sf,'raw_witness_intersection':ds(v['shape'].intersection(loss)),'raw_witness_difference':ds(loss.difference(v['shape']))})
  owned=[]
  for pi,p in enumerate(packet):
   if L.norm(p['new_q']['net'])!=net or p['new_q']['layer']!=ly:continue
   for role in ('shape','zone_outline_shape'):
    z=unary_union([set_precision(x[role],0)for x in p['exact_before_q']]);after=set_precision(p['new_q'][role],0);removed=z.difference(after);hit=loss.intersection(removed);owned.append({'union_UUID':p['new_q']['uuid'],'role':role,'explicit_owned_negative_geometry':save(header+f'-owned-role-{role}-negative',removed),'loss_intersects_named_negative':ds(hit)})
  # Record the literal per-primitive coverage, separately from the raw global-union FAIL.
  after_hits=[v['shape']for v in nn if v['shape'].envelope.intersects(envelope)];local_union=unary_union(after_hits);local_missing=loss.difference(local_union);rows.append({'failed_reference_row':fail,'exact_original_track_metadata':t,'actual_reference_source':ref+'.'+pin,'reference_layer':ly,'frozen_raw_witness':witness,'old_and_new_individual_source_primitives':candidates,'named_owned_negative_interaction':owned,'direct_witness_minus_individual_after_union':save(header+'-direct-witness-minus-local-after-primitives',local_missing),'raw_FAIL_is_not_waived':True,'exact_rational_point_or_region_certificate':'NOT_YET_RUN'});print('R637',t['uuid'],'bounds',list(loss.bounds),'localMissing',ds(local_missing),'primitiveCount',len(candidates),flush=True)
 put(OUT/'three-exact-failure-primitive-attributions.json',rows);put(OUT/'receipt.json',{'status':'READ_ONLY_THREE_REFERENCE_FAILURE_LOCAL_SOURCE_PRIMITIVES_AND_NAMED_OWNED_NEGATIVES_FROZEN','R635_FAIL_receipt_SHA256':sha(D/'receipt.json'),'R631_model_SHA256':sha(M),'R543_before_model_SHA256':sha(P),'three_track_raw_reference_FAILs_retained':True,'attribution_SHA256':sha(OUT/'three-exact-failure-primitive-attributions.json'),'no_geometry_source_native_or_current_qualification':True,'elapsed_seconds':time.monotonic()-st});print('R637 receipt',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
