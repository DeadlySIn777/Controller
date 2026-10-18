"""Read-only actual finite port census; remove only owned failed preview."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,time
from pathlib import Path
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import restore_field_current_mixed_precision_states_r366 as MS
from inventory import sha
M=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
O=H/'FIELD5-failed-In4-withdrawal-actual-source-target-port-census-r521'
OLD='61cb8179-7754-5031-bbea-0da464bf816f';NET='/motherboard_power_entry/FIELD_5V'
NEED=[('U11017','8'),('U11017','5'),('R11071','1'),('C11064','1'),('R9039','1'),('C11080','1'),('U11013','1'),('U11013','3'),('R11051','1')]
def main():
 assert not O.exists();O.mkdir();start=time.monotonic();assert sha(M)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
 g,h,b,q,c=pickle.loads(M.read_bytes());MS.restore_bound_field_current_precision_states(b,q)
 only=[z for z in c['zones']if z['uuid']==OLD];assert len(only)==1 and L.norm(only[0]['net'])==NET and set(only[0]['fills'])=={'In4.Cu'}
 after={**c,'zones':[z for z in c['zones']if z['uuid']!=OLD]};_,groups=K.physical(after,NET,K.hole_context(after));source=K.root(groups,'L11003','2');si=next(i for i,xs in enumerate(groups)if xs is source);vmap={v['uuid']:v for v in h['vias']};rows=[];targetidx=[]
 for i,xs in enumerate(groups):
  pads=sorted({r['ref']+'.'+str(r['pin'])for r in xs if r['kind']=='pad'and str(r['pin'])});targets=sorted(set(pads)&{r+'.'+p for r,p in NEED});ports=[]
  for uid in sorted({r['uuid']for r in xs if r['kind']=='via'}):
   v=vmap[uid];layers={ly:sum(r['shape'].area for r in xs if r['kind']=='via'and r['uuid']==uid and r['layer']==ly)for ly in K.LAYERS};ports.append({'uuid':uid,'raw_net':v['net'],'at_mm':[v['x'],v['y']],'diameter_mm':v['d'],'drill_mm':v['drill'],'declared_current_host_flashes':v['flashed'],'actual_finite_source_group_annular_area_by_layer':layers})
  rows.append({'group':i,'source_L11003_2':i==si,'named_pads':pads,'needed_targets':targets,'actual_ports':ports,'layer_fill_mm2':{ly:sum(r['shape'].area for r in xs if r['kind']=='fill'and r['layer']==ly)for ly in K.LAYERS},'physical_layer_key_count':len(K.keys(xs))})
  if targets and i!=si:targetidx.append(i)
 (O/'actual-FIELD5-groups-with-only-failed-In4-owned-zone-withdrawn.pkl').write_bytes(pickle.dumps(groups,protocol=5));(O/'receipt.json').write_text(json.dumps({'status':'READ_ONLY_EXACT_SOURCE_TARGET_PORT_CENSUS_NO_MODEL','parent_sha256':sha(M),'only_owned_preview_withdrawn_UUID':OLD,'source_group':si,'remaining_needed_target_groups':targetidx,'rows':rows,'full_load_A':.341130981,'routing_reservation_A':.36,'current_loop_barrels_thermal_native':'OPEN','native_original_Cu_outlines_rules_or_model_written':False,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start},indent=1)+'\n',encoding='utf-8');print('R521 receipt',sha(O/'receipt.json'),'sourcegroup',si,'targetgroups',targetidx,flush=True)
if __name__=='__main__':main()
