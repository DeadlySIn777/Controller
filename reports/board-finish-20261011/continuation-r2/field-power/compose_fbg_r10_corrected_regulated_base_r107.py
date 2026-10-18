"""Bind the new exact FBG existing-annulus spine to corrected REG geometry."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
from inventory import sha
from regulated_outer_joins_r51 import PORTS
H=Path(__file__).resolve().parent;ROOT=H.parent;sys.path.insert(0,str(ROOT/'sbc-power'))
import guarded_power_projection_r44 as P
O=H/'corrected-regulated-fbg-r10-search-base-r107'

def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir()
 bp=H/'corrected-regulated-joint-search-base-r106';assert sha(bp/'model.pkl')=='3f9086799fb85283714126d51b1e7cc8dc477ffe8a3ed0b1c06edd91071dcf39'
 g,h,b,z,prior=pickle.loads((bp/'model.pkl').read_bytes());b=copy.deepcopy(b);z=copy.deepcopy(z)
 fp=ROOT/'fbg-lazy-existing-return-restoration-r10';assert sha(fp/'model.pkl')=='b84fefaed0fd708f859073fc6209663336f4fea29e88e60296ae7248af6c7184';assert sha(fp/'proposed-zones.pkl')=='71b394897846e693fcb4abdbc41c71b5c93ec50c6e31c6ef206890b6662bc5fb'
 peer=pickle.loads((fp/'proposed-zones.pkl').read_bytes());assert len(peer)==1 and peer[0]['uuid']=='df0142e5-1eec-5c16-a3af-fd791397b3d9'
 assert not ({q['uuid'] for q in peer}&{q['uuid'] for q in z})
 owned=pickle.loads((bp/'owned-regulated-planes.pkl').read_bytes());ownedids={q['uuid'] for q in owned};led=[];out=[]
 for q in z:
  if q['uuid'] not in ownedids:out.append(q);continue
  before=q['shape'];outline=q.get('zone_outline_shape',before);cuts=[]
  for x in peer:
   if x['layer']!=q['layer'] or x['net']==q['net']:continue
   req=max(.15 if h['domains_normalized'].get(C.norm(q['net']))==h['domains_normalized'].get(C.norm(x['net'])) else .6,float(q.get('clearance_mm',.15)),float(x.get('clearance_mm',.15)))+.025
   if outline.distance(x['shape'])<req+.000003:cuts.append(P.bounded_buffer(x['shape'].intersection(outline.buffer(req+.00001)),req))
  if cuts:
   cutter=unary_union(cuts);body=set_precision(set_precision(before,1e-6).difference(cutter),1e-6);newout=set_precision(set_precision(outline,1e-6).difference(cutter),1e-6);led.append({'uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'before_sha256':P.digest(before),'after_sha256':P.digest(body),'outline_before_sha256':P.digest(outline),'outline_after_sha256':P.digest(newout),'physical_removed_mm2':before.difference(body).area,'physical_added_mm2':body.difference(before).area,'cutter_sha256':P.digest(cutter)});(O/(q['uuid']+'.before.wkb')).write_bytes(before.wkb);(O/(q['uuid']+'.after.wkb')).write_bytes(body.wkb);(O/(q['uuid']+'.cutter.wkb')).write_bytes(cutter.wkb);q={**q,'shape':body,'zone_outline_shape':newout}
  out.append(q)
 z=out+peer;hard=b['field_regulated_search_hard_nominees'];hard['source_qualified_peer_ROOT_spine_UUIDs_hard']=hard.get('source_qualified_peer_ROOT_spine_UUIDs_hard',[])+[q['uuid'] for q in peer];b['root_FBG_R10_exact_model_sha256']=sha(fp/'model.pkl');b['root_FBG_R10_exact_new_shape_sha256']=sha(fp/'proposed-zones.pkl')
 print('R107 full current projection',len(z),'zones',flush=True);after,oldfill=P.projected(g,h,z);groups={};census=[]
 for bank,net,ref,pin,policy in PORTS:
  gs=F.graph(after,net);groups[net]=gs;ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));census.append({'bank':bank,'net':net,'source_group':ri,'actual_source':ref+'.'+pin,'remaining':[{'group':i,'pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']]} for i,xs in enumerate(gs) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)]});print(bank,'remaining',len(census[-1]['remaining']),flush=True)
 (O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,after),protocol=5));(O/'source-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));(O/'owned-regulated-planes.pkl').write_bytes(pickle.dumps([q for q in z if q['uuid'] in ownedids],protocol=5));write(O/'source-census.json',census);write(O/'REG-root-spine-clips.json',led);write(O/'oldfill-retreats.json',oldfill)
 write(O/'receipt.json',{'verdict':'FROZEN_CURRENT_REG_SEARCH_BASE_NOT_FINAL_ACCEPTANCE','model_sha256':sha(O/'model.pkl'),'prior_R106_model_sha256':sha(bp/'model.pkl'),'R10_model_sha256':sha(fp/'model.pkl'),'R10_spine_shapes_sha256':sha(fp/'proposed-zones.pkl'),'R10_spine_geometry_retained_exact':True,'R10_additions':1,'REG_only_clip_sha256':sha(O/'REG-root-spine-clips.json'),'source_census_sha256':sha(O/'source-census.json'),'source_groups_sha256':sha(O/'source-groups.pkl'),'oldfill_retreat_sha256':sha(O/'oldfill-retreats.json'),'owned_REG19_plane_sha256':sha(O/'owned-regulated-planes.pkl'),'new_discrete':0,'native_jobs':0,'board_written':False,'full_old_contact_REFERENCE_source_current_and_native_gates':'OPEN'});print('R107 frozen',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
