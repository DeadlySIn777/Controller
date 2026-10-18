"""Pin actual FIELD5 branch barrels and detached U10009 protected ports."""
import os,psutil
for task_env in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[task_env]='2'
task_process=psutil.Process();task_process.cpu_affinity(list(range(16,28)));task_process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,sys
from pathlib import Path
from shapely.geometry import Point,box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from inventory import sha
O=H/'FIELD5-failing-In4-branch-and-U10009-existing-ports-r381'
M=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
R=H/'REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368'
def main():
 assert not O.exists();O.mkdir();g,h,b,q,actual=pickle.loads(M.read_bytes());allgroups=pickle.loads((R/'actual-drilled-current-groups.pkl').read_bytes());z=next(z for z in q if z['uuid']=='61cb8179-7754-5031-bbea-0da464bf816f');field=L.norm(z['net']);root=K.root(allgroups[field],'L11003','2');barrels=[]
 for v in h['vias']:
  if L.norm(v['net'])!=field:continue
  physical=[r for r in root if r['kind']=='via'and r['uuid']==v['uuid']];overlap=[{'layer':r['layer'],'annular_overlap_mm2':r['shape'].intersection(z['shape']).area}for r in physical if r['layer']=='In4.Cu'and r['shape'].intersects(z['shape'])]
  barrels.append({**v,'failing_q61cb_In4_actual_annulus_contacts':overlap})
 padrows=[{k:p.get(k)for k in ('uuid','ref','num','x','y','net','layers')}for p in h['pads']if p['ref']in ('U11017','R11051','U11013','R11071','C11064','C11080','R9039')]
 removed=set(json.loads((H/'U10009-exact-VS-cycle-withdrawal-VDD-join-nomination-r379/receipt.json').read_bytes())['exact_original_VS_removed_tracks'][i]['uuid']for i in range(15));counter={**actual,'tracks':[t for t in actual['tracks']if t['uuid']not in removed]};protected='/motherboard_power_entry/FIELD_A_24V_PROTECTED';_,pg=K.physical(counter,protected,K.hole_context(counter));src=K.root(pg,'U11004','17');lower=K.root(pg,'U10009','34');vm={v['uuid']:v for v in h['vias']};lowerports=[]
 for uid in sorted({r['uuid']for r in lower if r['kind']=='via'}):
  v=vm[uid];xs=[r for r in lower if r['kind']=='via'and r['uuid']==uid];nearest=[]
  for r in xs:
   peers=[s for s in src if s['layer']==r['layer']];ss=unary_union([s['shape']for s in peers]);nearest.append({'layer':r['layer'],'actual_annulus_mm2':r['shape'].area,'same_layer_actual_source_gap_mm':r['shape'].distance(ss),'source_geometry_bounds_mm':list(ss.bounds)})
  lowerports.append({**v,'actual_layer_source_gaps':nearest})
 rows={'verdict':'READ_ONLY_NATIVE_ACTUAL_PORT_DIAGNOSIS','model_sha256':sha(M),'failing_FIELD5_q61cb_nonshape_metadata':{k:v for k,v in z.items()if k not in('shape','zone_outline_shape')},'q61cb_physical_bounds_mm':list(z['shape'].bounds),'all_FIELD5_actual_source_barrels':barrels,'local_FIELD5_pad_records':padrows,'U10009_rejected_cycle_detached_existing_actual_barrel_ports':lowerports,'U10009_detached_exact_native_pads':[{'UUID':r['uuid'],'ref':r['ref'],'pin':r['pin']}for r in lower if r['kind']=='pad'],'no_source_or_geometry_changed':True}
 (O/'receipt.json').write_text(json.dumps(rows,indent=1,allow_nan=False)+'\n',encoding='utf-8');print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'q61cb_metadata':rows['failing_FIELD5_q61cb_nonshape_metadata'],'FIELD5_contacted_barrels':[v for v in barrels if v['failing_q61cb_In4_actual_annulus_contacts']],'U10009_lower_ports':lowerports}),flush=True)
if __name__=='__main__':main()
