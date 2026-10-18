"""Read-only exact source/guard attribution of the R469 direct witnesses."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,time
from pathlib import Path
from shapely import from_wkb,set_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import complete_geometry_r2 as G
import guarded_declared_settings_projection_r58 as N
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import restore_field_current_mixed_precision_states_r366 as MS
from inventory import sha
R=H/'FIELD5-R465-A-preserved-grafts-direct-source-reference-gate-r469'
M=H/'FIELD5-R385-minimal-R155-A-array-exact-individual-graft-witnesses-r465'
O=H/'FIELD5-R465-direct-reference-actual-guards-source-attribution-r471'
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def desc(sh):return {'empty':sh.is_empty,'type':sh.geom_type,'area_mm2':sh.area,'length_mm':sh.length,'bounds_mm':None if sh.is_empty else list(sh.bounds)}
def main():
 assert not O.exists();O.mkdir();start=time.monotonic();assert sha(R/'receipt.json')=='d9e9ac9ebae83eb9de4e238d0aba85e2ac5340374da11f811c48891ced0f6c6f'
 assert sha(M/'model.pkl')=='eba30a6936c18658ee129a7eb8422d55010efefb49a6be3fbec7800ff90bd3d6'
 g,h,b,q,c=pickle.loads((M/'model.pkl').read_bytes());MS.restore_bound_field_current_precision_states(b,q);groups=pickle.loads((R/'actual-checked-five-net-groups.pkl').read_bytes());receipt=json.loads((R/'receipt.json').read_text(encoding='utf-8'));net='/LOGIC_GND';ar=K.root(groups[net],'J11001','2');allfill={ly:unary_union([r['shape']for xs in groups[net]for r in xs if r['kind']=='fill'and r['layer']==ly])for ly in K.LAYERS};source={ly:unary_union([r['shape']for r in ar if r['kind']=='fill'and r['layer']==ly])for ly in K.LAYERS};former=from_wkb((M/'withdrawn-old-feed-In4.Cu-explicit-500nm-original-negative-rim-restoration-envelope.wkb').read_bytes());row=next(x for x in receipt['rows']if x['net']==net);rows=[];cache={}
 for old in row['original_formula_scoped_rows']:
  if old['is_empty']:continue
  gap=from_wkb(Path(old['WKB_file']).read_bytes());layer=K.MAP[old['layer']];guards=[]
  for qq in q:
   if qq['layer']!=layer or L.norm(qq['net'])==net:continue
   local=max(.25,G.gap(h,net,qq['net']),qq.get('clearance_mm',.15))+.025
   if qq['zone_outline_shape'].distance(gap)>local+.001:continue
   key=(qq['uuid'],local)
   if key not in cache:cache[key]=set_precision(N.bounded_buffer(qq['zone_outline_shape'],local),0)
   hit=gap.intersection(cache[key]);guards.append({'UUID':qq['uuid'],'raw_net':qq['net'],'layer':layer,'declared_guard_mm':local,'gap_vs_intended_outline_distance_mm':gap.distance(qq['zone_outline_shape']),'guard_WKB_sha256':sha_bytes(cache[key].wkb),'gap_intersection_guard':desc(hit)})
  restore=[]
  for f in M.glob('*'+layer+'-parent-*-only-new-graft.wkb'):
   sh=from_wkb(f.read_bytes())
   if sh.is_empty or not sh.envelope.intersects(gap.envelope):continue
   hit=gap.intersection(sh)
   if not hit.is_empty:restore.append({'file':str(f.resolve()),'sha256':sha(f),'hit':desc(hit)})
  out={'track_UUID':old['uuid'],'raw_net':old['raw_net'],'reference_layer':layer,'raw_direct_gap':desc(gap),'gap_file':old['WKB_file'],'gap_sha256':old['WKB_sha256'],'actual_ALL_filled_overlap':desc(gap.intersection(allfill[layer])),'actual_source_filled_overlap':desc(gap.intersection(source[layer])),'actual_filled_not_source_overlap':desc(gap.intersection(allfill[layer].difference(source[layer]))),'former_authorized_restore_overlap':desc(gap.intersection(former))if layer=='In4.Cu'else None,'retained_NEW_positive_guard_attribution':guards,'new_graft_piece_overlap':restore};rows.append(out);put(O/'checkpoint.json',rows);print('R471',old['uuid'],'area',gap.area,'guardhits',len(guards),'restorehits',len(restore),flush=True)
 put(O/'receipt.json',{'status':'READ_ONLY_DIRECT_REFERENCE_GAP_ATTRIBUTION_RAW_FAILURES_PRESERVED','model_sha256':sha(M/'model.pkl'),'R469_receipt_sha256':sha(R/'receipt.json'),'rows':rows,'no_geometry_or_model_change':True,'no_area_zero_waiver':True,'guard_attribution_conservative_LG_local_clearance_mm':.25,'source_current_reference_native_adoption':'NOT_GRANTED','elapsed_seconds':time.monotonic()-start});print('R471 receipt',sha(O/'receipt.json'),flush=True)
def sha_bytes(raw):
 import hashlib
 return hashlib.sha256(raw).hexdigest()
if __name__=='__main__':main()
