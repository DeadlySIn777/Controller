"""Identify the exact three IO3 pads and their former layer-fill contacts."""
import os
for key in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='2'
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for folder in('field-power','sbc-power'):sys.path.insert(0,str(H/folder))
import contact_layout as C
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 after_dir=H/'CORE-wide-immutable-R214-materialized-source-proposal-r107';assert sha(after_dir/'receipt.json')=='e5de8de38a5d7ff1c2069591bfd0691f9fb37740e1e554a3c5c4e338ad6dbb78';r=json.loads((after_dir/'receipt.json').read_bytes());assert sha(after_dir/'model.pkl')==r['model_sha256']=='5d0f30107f8e0189cec7c48b4abfb21dfc460b7ec22962042e62abb6e9686261';g,h,b,z,after=pickle.loads((after_dir/'model.pkl').read_bytes());base=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214';assert sha(base/'model.pkl')=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e';before=pickle.loads((base/'model.pkl').read_bytes())[4];prior=H/'joint-positive-head-signal-reference-mask-proposal-r83';refilled=pickle.loads((prior/'model.pkl').read_bytes())[4];src=next(q for q in r['sources']if q['net']=='/IO_3V3');lost=src['prior_source_keys_lost'];rows=[]
 for kind,uid in lost:
  q=next(t for t in h[{'pad':'pads','track':'tracks','via':'vias'}[kind]]if t['uuid']==uid);row={'kind':kind,'UUID':uid,'raw_net':q['net']}
  if kind=='pad':row.update(ref=q['ref'],pin=q['num'],at_mm=[q['x'],q['y']],layers=list(q['layers']));layers=q['layers'];shapes={l:unary_union(C.poly(v))for l,v in layers.items()}
  elif kind=='track':row.update(layer=q['layer'],a=q['a'],b=q['b'],w=q['w']);shapes={q['layer']:C.body(q)}
  else:row.update(at_mm=[q['x'],q['y']],diameter_drill_mm=[q['d'],q['drill']],flashed=q['flashed']);shapes={l:Point(q['x'],q['y']).buffer(q['d']/2).difference(Point(q['x'],q['y']).buffer(q['drill']/2))for l in q['flashed']}
  contacts=[]
  for native in before['zones']:
   if C.norm(native['net'])!='/IO_3V3':continue
   match={t['uuid']:t for t in after['zones']}.get(native['uuid']);ps={t['uuid']:t for t in refilled['zones']}.get(native['uuid'])
   for layer,shape in shapes.items():
    old=unary_union(C.poly(native['fills'].get(layer,[])))
    if old.is_empty or old.distance(shape)>2e-6:continue
    new=unary_union(C.poly(match['fills'].get(layer,[])))if match else old.difference(old);oldre=unary_union(C.poly(ps['fills'].get(layer,[])))if ps else old.difference(old);contacts.append({'native_or_owned_IO3_zone_UUID':native['uuid'],'layer':layer,'old_contact_mm2':old.intersection(shape).area,'new_contact_mm2':new.intersection(shape).area,'new_shape_distance_mm':new.distance(shape),'R83_reconstructed_prior_contact_mm2':oldre.intersection(shape).area,'possible_explicit_owned_minimal_IO3_bridge_needed_not_implicit_reclaimed_fill_credit':True})
  row['exact_old_layer_fill_contacts']=contacts;rows.append(row)
 out=H/'CORE-wide-IO3-exact-lost-source-contact-diagnosis-r110';assert not out.exists();out.mkdir();result={'verdict':'EXACT_IO3_SOURCE_LOSS_CONTACT_DIAGNOSIS_ONLY','wider_rejected_model_sha256':r['model_sha256'],'prior_IO3_593_to590_and7keys_NOT_WAIVED':True,'literal_lost_items':rows,'no_model_or_board_changed':True,'native_jobs':0,'adopted':False};(out/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('R110_LOST_IO3',[{k:v for k,v in row.items()if k!='exact_old_layer_fill_contacts'}for row in rows],sha(out/'receipt.json'),flush=True)
if __name__=='__main__':main()
