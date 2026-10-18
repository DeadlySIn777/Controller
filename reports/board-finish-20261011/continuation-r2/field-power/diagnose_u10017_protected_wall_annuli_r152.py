"""Source/outside-contact and actual native annular ports for owned VS wall."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,copy
from pathlib import Path
from shapely.geometry import LineString
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;O=H/'u10017-protected-wall-port-diagnosis-r152'
def write(p,d):p.write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();base=H/'paired-regional-six-regulated-full-contact-audit-r142/REG_R130-regional-model.pkl';g,h,b,z,after=pickle.loads(base.read_bytes());tm={q['uuid']:q for q in h['tracks']};vm={q['uuid']:q for q in h['vias']};old=tm['5c6ebac9-c76a-41f1-8cb8-45e2321f2e89'];protected=C.norm(old['net']);without=copy.deepcopy(after);without['tracks']=[q for q in without['tracks'] if q['uuid']!=old['uuid']];gs=F.graph(without,protected);ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==('U11006','17') for q in xs));(O/'groups.pkl').write_bytes(pickle.dumps(gs,protocol=5));body=C.body(old);rows=[]
 for i,xs in enumerate(gs):
  if not any(q['shape'].intersects(body) for q in xs):continue
  ports={q['uuid']:vm[q['uuid']] for q in xs if q['kind']=='via'}
  rows.append({'group':i,'actual_source_rooted':i==ri,'discrete_count':len(F.discrete_keys(xs)),'named_pads':[C.identity(q) for q in xs if q['kind']=='pad' and q.get('pin')],'actual_native_or_explicit_prospective_vias':[{'uuid':v['uuid'],'xy':[v['x'],v['y']],'dia_drill':[v['d'],v['drill']],'actual_model_flash_layers':v.get('flashed'),'prospective':v.get('prospective_not_native',False),'distance_to_old_wall_mm':LineString([old['a'],old['b']]).distance(C.body({'a':[v['x'],v['y']],'b':[v['x'],v['y']],'w':v['d']}))} for v in ports.values()]})
 write(O/'wall-contact-groups.json',rows);write(O/'receipt.json',{'verdict':'EXACT_PROTECTED_WALL_CONTACT_PORT_DIAGNOSTIC','parent_model_sha256':sha(base),'owned_wall_UUID':old['uuid'],'raw_net':old['net'],'group_rows_sha256':sha(O/'wall-contact-groups.json'),'groups_sha256':sha(O/'groups.pkl'),'no_original_definition_or_copper_mutated':True});print('R152',sha(O/'receipt.json'),json.dumps([{'group':r['group'],'actual_source_rooted':r['actual_source_rooted'],'discrete_count':r['discrete_count'],'pads':len(r['named_pads']),'ports':r['actual_native_or_explicit_prospective_vias']} for r in rows]),flush=True)
if __name__=='__main__':main()
