"""Read-only own-barrel intent audit plus U11017 local wall inventory."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json
from pathlib import Path
from shapely.geometry import Point,box,LineString
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import guarded_power_projection_r44 as P
O=H/'regulated-intended-barrel-landings-r131'
def write(path,data):path.write_text(json.dumps(data,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();base=H.parent/'safe-logic-five-and-fag-margin-r22';assert sha(base/'model.pkl')=='014b37594d378cd3e1a606cb1c06a0ad0b1b3ffea5cb836132bfaeec80d3a52a';g,h,b,z,_=pickle.loads((base/'model.pkl').read_bytes());d=pickle.loads((H/'regulated-four-retained-hard-snapshot-r127/proposed-discrete.pkl').read_bytes());h={**h,'vias':h['vias']+d['vias'],'tracks':h['tracks']+d['tracks']};qs=pickle.loads((H/'regulated-four-retained-hard-snapshot-r127/proposed-zones.pkl').read_bytes())+pickle.loads((H/'regulated-reference-safe-source-replacements-r121/proposed-zones.pkl').read_bytes());u19=next(q for q in z if q['uuid']=='266df662-7714-534d-872b-6b881b1cc9e1') if any(q['uuid']=='266df662-7714-534d-872b-6b881b1cc9e1' for q in z) else None
 # The owned U19 ground outline is selected by the frozen native recipe IDs,
 # never guessed from a normalized raw-net alias or display label.
 owned=pickle.loads((H/'u19008-guarded-native-owned-recipe-r110/proposed-zones.pkl').read_bytes())
 ids={q['uuid'] for q in owned};qs+= [q for q in z if q['uuid'] in ids]
 rows=[]
 for q in qs:
  physical=q['shape'];intent=q.get('zone_outline_shape',physical)
  for v in h['vias']:
   if C.norm(v['net'])!=C.norm(q['net']):continue
   ann=P.bounded_disk(v,v['d']/2).difference(P.bounded_disk(v,v['drill']/2));overlap=physical.intersection(ann).area
   if overlap<=1e-9:continue
   center=Point(v['x'],v['y']);rows.append({'zone_uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'via_uuid':v['uuid'],'xy_mm':[v['x'],v['y']],'actual_or_prospective_flash_layers':v['flashed'],'physical_annular_overlap_mm2':overlap,'intended_outline_covers_center':intent.covers(center),'intended_center_gap_mm':intent.distance(center),'intent_shape_sha256':P.digest(intent),'physical_shape_sha256':P.digest(physical),'same_raw_token':v['net']==q['net'],'actual_flash_on_plane_layer':q['layer'] in v['flashed']})
 write(O/'landing-rows.json',rows)
 rec,trees=F.build({**h,'zones':[]},layers={'F.Cu'});window=box(218.5,187,226,194);near=[]
 for idx in trees['F.Cu'].query(window,predicate='intersects'):
  a=rec['F.Cu'][int(idx)];row={k:a.get(k) for k in ('kind','uuid','net','ref','pin')};row['bounds']=list(a['shape'].bounds)
  if a['kind']=='track':row.update(next(t for t in h['tracks'] if t['uuid']==a['uuid']))
  if a['kind']=='via':row.update(next(v for v in h['vias'] if v['uuid']==a['uuid']))
  near.append(row)
 write(O/'u11017-local-physical-inventory.json',near);fail=[r for r in rows if not r['intended_outline_covers_center'] or not r['same_raw_token']];write(O/'receipt.json',{'verdict':'OWNED_BARREL_INTENT_PASS' if not fail else 'OWNED_BARREL_INTENT_REPAIR_REQUIRED','R22_model_sha256':sha(base/'model.pkl'),'six_REG_plus_U19_outline_count':len(qs),'actual_annular_attachment_rows':len(rows),'intent_center_or_raw_failures':len(fail),'landing_rows_sha256':sha(O/'landing-rows.json'),'local_U17_inventory_sha256':sha(O/'u11017-local-physical-inventory.json'),'native_flash_contact_current_qualification':'OPEN','board_written':False,'native_jobs':0});print('R131',sha(O/'receipt.json'),'rows',len(rows),'fails',len(fail),flush=True)
if __name__=='__main__':main()
