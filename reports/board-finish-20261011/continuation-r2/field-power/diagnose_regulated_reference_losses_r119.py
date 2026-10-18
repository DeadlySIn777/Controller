"""Bind exact reference losses to new REG bodies; no acceptance or geometry edit."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json
from pathlib import Path
from shapely.ops import unary_union
from shapely.geometry import LineString
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import guarded_power_projection_r44 as P
import complete_geometry_r2 as G
O=H/'regulated-reference-contact-diagnostic-r119'
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();base=H/'corrected-regulated-native-bound-search-base-r111';current=H/'regulated-source-contact-reference-audit-r116'
 g,oldh,b,oldq,prior=pickle.loads((base/'model.pkl').read_bytes());_,h,b,z,after=pickle.loads((current/'model.pkl').read_bytes());ng=pickle.loads((current/'groups.pkl').read_bytes());r=json.loads((current/'receipt.json').read_text());assert sha(current/'model.pkl')==r['model_sha256']
 newq=pickle.loads((current/'proposed-zones.pkl').read_bytes());d=pickle.loads((H/'regulated-quantized-inner-source-feeds-r114/proposed-discrete.pkl').read_bytes());refs=json.loads((current/'reference-losses.json').read_text());contacts=json.loads((current/'ground-contacts.json').read_text());tmap={t['uuid']:t for t in prior['tracks']};pads={q['uuid']:q for q in h['pads']};summary=[];masks={};oldgroups={}
 for row in refs:
  net=row['ground_net'];root=row['source'].split('.')[0];ogs=F.graph(prior,net);oldgroups[net]=ogs;oi=next(i for i,xs in enumerate(ogs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(root,'2') for q in xs));gs=ng[net];ni=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(root,'2') for q in xs));losses=[]
  for layer,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]:
   oldref=unary_union([q['shape'] for q in ogs[oi] if q['kind']=='fill' and q['layer']==inner]);newref=unary_union([q['shape'] for q in gs[ni] if q['kind']=='fill' and q['layer']==inner]);mask=unary_union([C.body(tmap[x['uuid']]).intersection(oldref) for x in row['retained_outer_track_reference_losses'] if x['layer']==layer]);masks[(net,inner)]=mask;(O/(root+'-'+inner+'-retained-reference-mask.wkb')).write_bytes(mask.wkb)
   for x in row['retained_outer_track_reference_losses']:
    if x['layer']!=layer:continue
    body=C.body(tmap[x['uuid']]);lost=body.intersection(oldref).difference(newref);causes=[]
    for q in newq:
     if q['layer']!=inner or C.norm(q['net'])==net:continue
     gap=max(G.gap(h,net,q['net']),float(q.get('clearance_mm',.15)))+.025;cut=P.bounded_buffer(q['shape'],gap);area=lost.intersection(cut).area
     if area>1e-9:causes.append({'kind':'new_REG_plane','uuid':q['uuid'],'raw_net':q['net'],'area_mm2':area})
    for v in d['vias']:
     gap=G.gap(h,net,v['net'])+.025;radius=max(v['drill']/2+.275,v['d']/2+gap);area=lost.intersection(P.bounded_disk(v,radius)).area
     if area>1e-9:causes.append({'kind':'new_REG_via','uuid':v['uuid'],'raw_net':v['net'],'area_mm2':area})
    losses.append({**x,'lost_region_WKB_SHA256':P.digest(lost),'lost_region_bounds':list(lost.bounds),'causes':causes})
  cr=next(q for q in contacts if q['net']==net);lostpads=[{'uuid':uid,'ref':pads[uid]['ref'],'pin':pads[uid]['num'],'layers':list(pads[uid]['layers'])} for kind,uid in cr['prior_source_keys_lost'] if kind=='pad'];summary.append({'ground':net,'lost_prior_source_keys':cr['prior_source_keys_lost'],'lost_pads':lostpads,'reference_losses':losses});print(root,'reference',len(losses),'lostpads',lostpads,flush=True)
 write(O/'detail.json',summary);(O/'reference-masks.pkl').write_bytes(pickle.dumps(masks,protocol=5));(O/'old-ground-groups.pkl').write_bytes(pickle.dumps(oldgroups,protocol=5));write(O/'receipt.json',{'verdict':'BOUND_DIAGNOSTIC_ONLY','R116_receipt_sha256':sha(current/'receipt.json'),'R111_model_sha256':sha(base/'model.pkl'),'detail_sha256':sha(O/'detail.json'),'masks_sha256':sha(O/'reference-masks.pkl'),'old_groups_sha256':sha(O/'old-ground-groups.pkl'),'geometry_changed':False,'board_written':False,'native_jobs':0});print('R119',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
