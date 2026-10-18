"""Inspect actual retained source/main-group ports and finite extra-flash obstacles; no edits."""
import os
for n in('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import fast_contacts as F
import contact_layout as C
import guarded_declared_settings_projection_r58 as N
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 folder=H/'SAFE-old-source-ground-reference-power-scope-proposal-r74';rp=folder/'receipt.json';assert sha(rp)=='add5e6c16ffbc1a3b8b24f80268d451c169220268e83871fb2f391b88a4b0c92';r=json.loads(rp.read_bytes());assert r['verdict']=='REMOVE_ONLY_REFERENCE_REPAIR_SOURCE_LOSS_REPAIR_REQUIRED'
 mp=folder/'model.pkl';assert sha(mp)==r['model_sha256'];g,h,b,z,current=pickle.loads(mp.read_bytes());groups=pickle.loads((folder/'source-groups.pkl').read_bytes())['/CORE_1V2'];source=next(xs for xs in groups if any(q['kind']=='pad'and(q['ref'],q['pin'])==('L2001','2')for q in xs));rr={q['uuid']for q in source};vby={q['uuid']:q for q in h['vias']};raw='/CORE_1V2';record,tree=F.build({**h,'zones':[]});origin=Point(236.212,94.61);rows=[]
 for xs in groups:
  named=[q for q in xs if q['kind']=='pad'and q['pin']];vids={q['uuid']for q in xs if q['kind']=='via'}
  if not named:continue
  ports=[vby[uid]for uid in vids];ports.sort(key=lambda v:origin.distance(Point(v['x'],v['y'])))
  rows.append({'is_actual_L2001_source':xs is source,'discrete_keys':len(F.discrete_keys(xs)),'named_pads':[{'UUID':q['uuid'],'ref':q['ref'],'pin':q['pin'],'layer':q['layer']}for q in named],'actual_vias':ports,'layer_source_Cu_bounds':{l:list(unary_union([q['shape']for q in xs if q['layer']==l and q['kind']!='via']).bounds)for l in('F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu')}})
 checks=[]
 eligible={q['uuid']for xs in groups for q in xs if q['kind']=='via'and any(p['kind']=='pad'and p['ref']=='U1001'for p in xs)}|{'f6ad6a15-3a41-4605-9ad5-72f4ba7d5d92'}
 for uid in sorted(eligible):
  v=vby[uid];physical=N.bounded_disk(v,v['d']/2).difference(N.bounded_disk(v,v['drill']/2));p=Point(v['x'],v['y'])
  for l in('In1.Cu','In2.Cu','In3.Cu','In4.Cu'):
   if l in v['flashed']:continue
   obs=[]
   for i in tree[l].query(p.buffer(1.5),predicate='intersects'):
    q=record[l][int(i)]
    if q['net']==raw:continue
    guard=(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][raw]else .6)+.025+.000020
    actual=p.distance(q['shape'])-v['d']/2
    if actual<guard:obs.append({'UUID':q['uuid'],'net':q['net'],'kind':q['kind'],'actual_edge_gap_mm':actual,'required_mm':guard})
   owned=[]
   for q in z:
    if q['layer']!=l or q['net']==raw:continue
    guard=max(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][raw]else .6,float(q.get('clearance_mm',.15)))+.025+.000020
    if p.distance(q['shape'])-v['d']/2<guard:owned.append({'UUID':q['uuid'],'raw_net':q['net'],'actual_edge_gap_mm':p.distance(q['shape'])-v['d']/2,'required_mm':guard,'owned_remove_only_notch_only_possible_after_all_source_ref_gates':True})
   checks.append({'actual_via':v,'new_prospective_layer':l,'is_current_source_port':uid in rr,'foreign_old_Cu_blockers':obs,'new_owned_plane_obstacles':owned,'extra_flash_authorization_and_native_annuli_NOT_GRANTED':True})
 out=H/'CORE-source-split-exact-ports-r76';assert not out.exists();out.mkdir();(out/'receipt.json').write_text(json.dumps({'verdict':'READ_ONLY_ACTUAL_SOURCE_AND_MAIN_CORE_PORTS_EXTRA_FLASH_OBSTACLES','parent_model_sha256':sha(mp),'groups':rows,'candidate_existing_barrel_extra_layers':checks,'all_original_masks_and_source_FAIL_preserved':True,'no_board_or_host_model_changes':True,'native_jobs':0,'adopted':False},indent=1)+'\n')
 print('R76_PORTS',[(q['is_actual_L2001_source'],len(q['named_pads']),len(q['actual_vias']))for q in rows],flush=True)
 for q in checks:
  print('R76_EXTRA_LAYER',q['actual_via']['uuid'][:8],q['new_prospective_layer'],'oldblockers',len(q['foreign_old_Cu_blockers']),'newplanes',len(q['new_owned_plane_obstacles']),flush=True)
if __name__=='__main__':main()
