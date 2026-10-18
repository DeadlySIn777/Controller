"""Fresh full-native three-ground groups using actual pads/flashes/all holes."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,time,collections
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(ROOT/d))
import contact_layout as L
import ordinary_routes as O
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
N=ROOT/'R155-known-reference-native-diagnostic-r157/measure'
M=ROOT/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
OUT=H/'R157-actual-three-ground-native-all-drill-source-groups-r663'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic();assert sha(M)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';g,h,b,q,c=pickle.loads(M.read_bytes());ng=json.loads((N/'actual-full-refill-geometry.json').read_bytes());fl=json.loads((N/'actual-full-refill-via-flashes.json').read_bytes())['vias'];errors=json.loads((N/'actual-full-refill-contract.json').read_bytes())['postfill_Cu_or_flash_errors'];raws={p['net']for p in h['pads']if L.norm(p['net'])in{a[0]for a in K.ROOTS[:3]}};index=collections.defaultdict(list)
 for p in h['pads']:
  if p['net']in raws:index[p['ref'],str(p['num']),p['x'],p['y'],p['net']].append(p)
 replacements={};padledger=[]
 for p in ng['pads']:
  if p['net']not in raws:continue
  candidates=index[p['ref'],str(p['num']),*p['at'],p['net']];assert len(candidates)==1,('native exact physical pad ambiguous',p['ref'],p['num'],p['at']);old=candidates[0];new={**old,'layers':{ly:O.polys(p['poly'])for ly in p['layers']}};replacements[old['uuid']]=new;padledger.append({'UUID':old['uuid'],'ref':p['ref'],'pin':p['num'],'raw_net':p['net'],'actual_native_at_mm':p['at'],'layers':p['layers'],'actual_native_polygon_005_ERROR_INSIDE':True})
 assert set(replacements)=={p['uuid']for p in h['pads']if p['net']in raws}
 pads=[replacements.get(p['uuid'],p)for p in h['pads']];vias=[{**v,'flashed':fl[v['uuid']],'mask_provenance':'R157 FULL ACTUAL native Fill FlashLayer'}for v in h['vias']];zones=[{**z,'fills':{ly:O.polys(rs)for ly,rs in z['fills'].items()}}for z in ng['zones']if z['net']in raws];candidate={**c,'pads':pads,'vias':vias,'zones':[z for z in c['zones']if z['net']not in raws]+zones};ctx=K.hole_context(candidate);assert len(ctx[0])==len(vias)+sum(len(L.poly(p.get('hole')or[]))for p in pads)
 result={};source=[];maskrows=[]
 for net,ref,pin in K.ROOTS[:3]:
  _,xs=K.physical(candidate,net,ctx);result[net]=xs;rs=K.root(xs,ref,pin);rk=K.keys(rs);source.append({'net':net,'source':ref+'.'+pin,'actual_named_source_pad_count':len({r['uuid']for r in rs if r['kind']=='pad'and str(r['pin'])}),'actual_source_key_count':len(rk),'actual_group_count':len(xs)})
  for e in errors:
   v=next(a for a in vias if a['uuid']==e['uuid'])
   if L.norm(v['net'])!=net:continue
   rooted=[ly for ly in v['flashed']if('via',v['uuid'],ly)in rk];bygroup=[{'group_index':i,'via_actual_layers':sorted({r['layer']for r in gr if r['kind']=='via'and r['uuid']==v['uuid']}),'group_named_pad_count':len({r['uuid']for r in gr if r['kind']=='pad'and str(r['pin'])})}for i,gr in enumerate(xs)if any(r['kind']=='via'and r['uuid']==v['uuid']for r in gr)];maskrows.append({'via_UUID':v['uuid'],'raw_net':v['net'],'at_mm':[v['x'],v['y']],'actual_native_flash_layers':v['flashed'],'mask_contract_missing_layers':e['missing_original_parent_actual_flashes'],'actual_native_remaining_source_rooted_layers':rooted,'actual_via_barrel_joined_to_external_source_on_an_observed_layer':bool(rooted),'actual_via_groups':bygroup,'native_missed_layer_not_in_graph_no_phantom_annulus':True})
  cp=OUT/('actual-native-ground-'+net.rsplit('/',1)[-1]+'-groups.pkl');cp.write_bytes(pickle.dumps(xs,protocol=5));put(OUT/'checkpoint-source-counts.json',source);print('R663',net,'sourcepads',source[-1]['actual_named_source_pad_count'],'groups',len(xs),flush=True)
 gp=OUT/'actual-R157-native-three-ground-all-drilled-groups.pkl';gp.write_bytes(pickle.dumps(result,protocol=5));put(OUT/'exact-actual-native-pad-bindings.json',padledger);put(OUT/'twenty-two-old-via-real-barrel-source-membership.json',maskrows);put(OUT/'actual-native-ground-source-census.json',source)
 put(OUT/'receipt.json',{'status':'FRESH_NATIVE_R157_THREE_GROUND_SOURCE_GROUPS_COMPLETE_MASK_CONTRACT_FAILS_RETAINED','native_geometry_SHA256':sha(N/'actual-full-refill-geometry.json'),'native_flashes_SHA256':sha(N/'actual-full-refill-via-flashes.json'),'exact_pad_identity_host_SHA256':sha(M),'actual_pad_bindings_SHA256':sha(OUT/'exact-actual-native-pad-bindings.json'),'actual_all_drilled_groups_SHA256':sha(gp),'source_census':source,'mask_barrel_source_membership_SHA256':sha(OUT/'twenty-two-old-via-real-barrel-source-membership.json'),'actual_remaining_rooted_via_count':sum(r['actual_via_barrel_joined_to_external_source_on_an_observed_layer']for r in maskrows),'unrooted_vias':[r['via_UUID']for r in maskrows if not r['actual_via_barrel_joined_to_external_source_on_an_observed_layer']],'cached_parent_has_zero_stored_fills_no_contact_baseline_claim':True,'source_plating_current_reference_loop_thermal_and_required_old_masks_not_waived':True,'no_native_jobs_changes_refill_or_save':True,'elapsed_seconds':time.monotonic()-st});print('R663_COMPLETE',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
