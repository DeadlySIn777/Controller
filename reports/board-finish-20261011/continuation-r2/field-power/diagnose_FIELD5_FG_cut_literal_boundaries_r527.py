"""Frozen read-only operand/grid attribution; never emit a candidate model."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,hashlib,time,traceback
from pathlib import Path
from shapely import set_precision,get_precision,from_wkb
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import guarded_declared_settings_projection_r58 as N
import restore_field_current_mixed_precision_states_r366 as MS
from inventory import sha
M=H/'FA-IO3-native-TMR-minimal-current-two-owned-zone-packet-r515/model.pkl'
A=H/'FIELD5-all-source-finite-annulus-old-reference-hard-nomination-r523'
O=H/'FIELD5-R525-raw-FG-gain-and-literal-boundary-attribution-r527'
FG='e2fe644a-2849-5c69-8ebb-d1e94909cd4c'
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def lit(s):
 a=set_precision(s,0);assert a.wkb==s.wkb;return a
def sm(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds':None if s.is_empty else s.bounds,'WKB_SHA256':dg(s)}
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def save(f,s):f.write_bytes(s.wkb);return {'file':str(f.resolve()),'sha256':sha(f),**sm(s)}
def parts(s):
 if s.is_empty:return []
 return list(s.geoms)if hasattr(s,'geoms')else[s]
def main():
 assert not O.exists();O.mkdir();start=time.monotonic()
 assert sha(M)=='4f70c8271d57724e41005d19c178ba597059085e7192955d7605cf20d501f862'
 g,h,b,q,c=pickle.loads(M.read_bytes());MS.restore_bound_field_current_precision_states(b,q)
 ground=next(z for z in q if z['uuid']==FG);new=pickle.loads((A/'only-one-new-FIELD5-actual-source-port-nominee.pkl').read_bytes())['q']
 intent=set_precision(new['zone_outline_shape'],1e-6,mode='valid_output');gridcut=N.bounded_buffer(intent,.1751);cut=lit(gridcut);locality=lit(N.bounded_buffer(cut,2.));save(O/'actual-normal-cut.wkb',cut);save(O/'declared-2mm-locality.wkb',locality);rows=[]
 for role in ('shape','zone_outline_shape'):
  gridbefore=ground[role];before=lit(gridbefore);save(O/(role+'-exact-parent.wkb'),before)
  raw=before.difference(cut)
  variants={'literal_zero_direct_difference':raw,'R525_literal_difference_then_global_nm':set_precision(raw,1e-6,mode='valid_output'),'restored_nm_operands_overlay':gridbefore.difference(gridcut)}
  for name,out in variants.items():
   d=O/(role+'-'+name);d.mkdir();after=lit(out);gain=after.difference(before);loss=before.difference(after);outside_gain=gain.difference(locality);outside_change=before.symmetric_difference(after).difference(locality);after_out=after.difference(cut);before_out=before.difference(cut);direct_outside_loss=before_out.difference(after_out);direct_outside_gain=after_out.difference(before_out)
   row={'role':role,'variant':name,'before_grid_mm':get_precision(gridbefore),'after_grid_mm':get_precision(out),'after':save(d/'after.wkb',after),'gain':save(d/'literal-gain.wkb',gain),'loss':save(d/'literal-loss.wkb',loss),'gain_outside_2mm':save(d/'literal-gain-outside-2mm.wkb',outside_gain),'change_outside_2mm':save(d/'literal-change-outside-2mm.wkb',outside_change),'outside_primary_direct_loss':save(d/'outside-primary-direct-loss.wkb',direct_outside_loss),'outside_primary_direct_gain':save(d/'outside-primary-direct-gain.wkb',direct_outside_gain),'literal_gained_fragments':[]}
   for i,z in enumerate(parts(gain)):
    row['literal_gained_fragments'].append({'index':i,**sm(z),'distance_to_actual_cut_mm':z.distance(cut),'distance_to_old_boundary_mm':z.distance(before.boundary),'outside_2mm':sm(z.difference(locality))})
   rows.append(row);print(role,name,'gain',gain.area,'outside2',outside_gain.area,'loss-outside',direct_outside_loss.area,flush=True)
 put(O/'receipt.json',{'status':'READ_ONLY_EXACT_OPERAND_AND_MODEL_GRID_ATTRIBUTION_NO_CANDIDATE','exact_parent_model_SHA256':sha(M),'nominee_SHA256':sha(A/'only-one-new-FIELD5-actual-source-port-nominee.pkl'),'R525_failure_retained':True,'actual_required_guard_mm':.175,'extra_construction_reserve_mm':.0001,'rows':rows,'no_primitive_WKB_or_current_copper_mutation':True,'native_jobs':0,'accepted':False,'elapsed_seconds':time.monotonic()-start})
 print('R527',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'no_model_or_acceptance':True})
  raise
