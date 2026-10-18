"""Attribute rejected return-reference cuts without accepting a projection."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'): os.environ[name]='2'
import psutil
proc=psutil.Process();proc.cpu_affinity(list(range(16,28)));proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for name in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/name))
import regional_guarded_declared_projection_r140 as P
import contact_layout as C
import fast_contacts as F
import physical_reference_losses_r1 as REF
from inventory import sha
from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
O=H/'owned-FBG-local-vs-global-trim-attribution-r246'
def write(p,d):p.write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir()
 base=H/'R54-native-wider-IO3-monitor-joint-audit-r214';g,h,b,z,before=pickle.loads((base/'model.pkl').read_bytes());restore_bound_generated_precision_states(b,z)
 groups=pickle.loads((base/'groups.pkl').read_bytes());ground='/motherboard_do/FIELD_B_0V';root=next(xs for xs in groups[ground] if any(x['kind']=='pad' and(x['ref'],x['pin'])==('J11005','2') for x in xs))
 native_source=[x['shape'] for x in root if x['kind']=='fill' and x['layer']=='In1.Cu'];oldref=unary_union(native_source)
 uid='d8d8bdad-3845-5659-b172-4d0e231cdadc';qold=next(q for q in z if q['uuid']==uid)
 parent=H/'B3-envelope-scoped-LOGIC-projection-r233';_,_,pb,pz,_=pickle.loads((parent/'derived-full-input-model.pkl').read_bytes());restore_bound_generated_precision_states(pb,pz);qprior=next(q for q in pz if q['uuid']==uid)
 cases={'R233_before_guard_trim':qprior}
 for rev in ('r240','r241'):
  f=H/('B3-subset-inherited-FBG-native-LOGIC-guard-correction-'+rev)/'corrected-owned-FBG-zone.pkl';cases[rev]=pickle.loads(f.read_bytes())[0]
 native_other=unary_union([x['shape'] for x in root if x['kind']=='fill' and x['layer']=='In1.Cu' and x['uuid']!=uid])
 rows=[];allparts=[];nativeids={t['uuid'] for t in g['tracks']}
 for t in h['tracks']:
  if t['uuid'] not in nativeids or t['layer']!='F.Cu' or C.norm(t['net'])==ground or h['domains_normalized'].get(C.norm(t['net']))!=h['domains_normalized'][ground]:continue
  body=REF.A.shape({'kind':'segment',**t});part=body.intersection(oldref)
  if not part.intersects(qold['shape'].buffer(.001)):continue
  losses={}
  for label,q in cases.items():
   retained=unary_union([native_other,q['shape']]);losses[label]=part.difference(retained).area
  if any(v>1e-9 for v in losses.values()):rows.append({'native_track_UUID':t['uuid'],'raw_net':t['net'],'old_reference_part_mm2':part.area,'loss_mm2':losses})
  if part.area>1e-12:allparts.append(part)
 mask=unary_union(allparts);(O/'exact-old-FBG-required-reference-mask.wkb').write_bytes(mask.wkb)
 print('R246 losses', {label:sum(r['loss_mm2'][label]>1e-9 for r in rows) for label in cases},flush=True)
 # Eliminate positive nm snap slivers only in the exact neighbourhood where
 # they occurred. Preserve the unrelated old return boundary verbatim.
 q=copy.deepcopy(cases['r240']);localops=[]
 for role in ('shape','zone_outline_shape'):
  prior=qprior[role];initial=q[role];iterations=[]
  for i in range(8):
   gain=set_precision(q[role],0).difference(set_precision(prior,0))
   if gain.area<1e-12:break
   cut=P.bounded_buffer(gain,.000003);old=q[role];q[role]=set_precision(old.difference(cut),1e-6)
   iterations.append({'iteration':i,'gain_mm2':gain.area,'gain_sha256':P.digest(gain),'local_cutter_sha256':P.digest(cut),'removed_mm2':old.difference(q[role]).area,'inward_local_reserve_mm':.000003})
  assert q[role].difference(prior).area<1e-12,(role,'gain remains',q[role].difference(prior).area)
  localops.append({'role':role,'before_R240_sha256':P.digest(initial),'after_sha256':P.digest(q[role]),'removed_mm2':initial.difference(q[role]).area,'added_mm2':q[role].difference(initial).area,'iterations':iterations})
 localref=unary_union([native_other,q['shape']]);local_losses=[{'native_track_UUID':r['native_track_UUID'],'reference_lost_mm2':REF.A.shape({'kind':'segment',**next(t for t in h['tracks'] if t['uuid']==r['native_track_UUID'])}).intersection(oldref).difference(localref).area} for r in rows]
 (O/'local-only-snap-corrected-FBG-zone.pkl').write_bytes(pickle.dumps([q],protocol=5));write(O/'old-reference-loss-attribution.json',rows);write(O/'local-only-snap-ledger.json',localops);write(O/'local-only-reference-diagnostic.json',local_losses)
 foreign=[]
 for native in before['zones']:
  if C.norm(native['net'])==ground or 'In1.Cu' not in native['fills']:continue
  sh=unary_union(C.poly(native['fills']['In1.Cu']))
  if sh.is_empty or not sh.intersects(q['shape'].buffer(.7)):continue
  req=max(P.G.gap(h,q['net'],native['net']),float(q.get('clearance_mm',.15)),float(native['clearance_mm']))+.025
  gap=q['shape'].distance(sh)
  if gap<req+.001:foreign.append({'native_UUID':native['uuid'],'raw_net':native['net'],'required_mm':req,'actual_mm':gap,'PASS':gap+1e-10>=req})
 write(O/'all-actual-native-foreign-near-guards.json',foreign)
 write(O/'receipt.json',{'verdict':'LOCAL_RETURN_TRIM_ATTRIBUTION_ONLY_NOT_ACCEPTED','baseline_sha256':sha(base/'model.pkl'),'parent_sha256':sha(parent/'derived-full-input-model.pkl'),'counts':{label:sum(r['loss_mm2'][label]>1e-9 for r in rows) for label in cases},'local_snap_reference_losses':sum(r['reference_lost_mm2']>1e-9 for r in local_losses),'local_snap_zone_sha256':sha(O/'local-only-snap-corrected-FBG-zone.pkl'),'all_native_foreign_near_guard_errors':sum(not r['PASS'] for r in foreign),'mask_sha256':sha(O/'exact-old-FBG-required-reference-mask.wkb'),'no_board_or_native_mutation':True})
 print('R246 complete',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
