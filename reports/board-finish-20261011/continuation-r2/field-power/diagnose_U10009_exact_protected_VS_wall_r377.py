"""Read-only exact local VS wall, pad and outside-contact inventory."""
import os,psutil
for task_env in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[task_env]='2'
task_process=psutil.Process();task_process.cpu_affinity(list(range(16,28)));task_process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from inventory import sha
O=H/'U10009-exact-protected-VS-coupled-wall-diagnosis-r377'
M=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
def main():
 assert not O.exists();O.mkdir();assert sha(M)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
 g,h,b,q,c=pickle.loads(M.read_bytes());win=box(262,168,273,176);pads=[];tracks=[];vias=[]
 for p in h['pads']:
  if p['ref']=='U10009' or Point(p['x'],p['y']).intersects(win):
   pads.append({k:p.get(k)for k in ('uuid','ref','num','net','x','y','layers','drill')})
 for t in h['tracks']:
  if t['layer']!='B.Cu' or t.get('m'):continue
  body=LineString([t['a'],t['b']]).buffer(t['w']/2)
  if not body.intersects(win):continue
  tracks.append({**t,'axis_length_mm':LineString([t['a'],t['b']]).length,'crosses_window_boundary':not win.covers(body)})
 for v in h['vias']:
  if Point(v['x'],v['y']).buffer(v['d']/2).intersects(win):vias.append(v)
 pad=next(p for p in h['pads']if p['ref']=='U10009'and str(p['num'])=='4');protected=next(p['net']for p in h['pads']if p['ref']=='U10009'and 'FIELD_A_24V_PROTECTED' in p['net'])
 _,physical=K.physical(c,L.norm(protected),K.hole_context(c));vs=[p for p in h['pads']if p['ref']=='U10009'and p['net']==protected];groups=[]
 for gp in physical:
  selected=[p['uuid']for p in vs if any(r['kind']=='pad'and r['uuid']==p['uuid']for r in gp)]
  if selected:groups.append({'physical_keys':len(K.keys(gp)),'VS_pad_UUIDs':selected,'B_tracks':[r['uuid']for r in gp if r['kind']=='track'and r['layer']=='B.Cu'],'all_via_UUIDs':sorted({r['uuid']for r in gp if r['kind']=='via'})})
 rec={'verdict':'READ_ONLY_EXACT_U10009_VS_WALL_AND_NATIVE_PHYSICAL_CONTACT_DIAGNOSIS','parent_model_sha256':sha(M),'window_mm':list(win.bounds),'VDD_target_UUID':pad['uuid'],'raw_VDD_net':pad['net'],'raw_protected_VS_net':protected,'all_U10009_VS_physical_pads':[{k:p[k]for k in ('uuid','num','x','y','layers')}for p in vs],'local_pads':pads,'local_B_tracks':tracks,'local_vias':vias,'VS_existing_physical_groups':groups,'no_geometry_source_rules_or_native_changed':True,'full_output_limits_preserved':{'DO_channels':16,'per_channel_A':.5},'coupled_repair_and_current_native_gates':'OPEN'}
 (O/'receipt.json').write_text(json.dumps(rec,indent=1,allow_nan=False)+'\n',encoding='utf-8')
 print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'VS_pads':rec['all_U10009_VS_physical_pads'],'B_tracks':[{k:t[k]for k in ('uuid','net','a','b','w')}for t in tracks],'VS_group_counts':[{'keys':x['physical_keys'],'pads':x['VS_pad_UUIDs'],'vias':len(x['all_via_UUIDs'])}for x in groups]}),flush=True)
if __name__=='__main__':main()

