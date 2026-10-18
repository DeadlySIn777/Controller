"""Exact C24 and U19008 scoped operations on the corrected joint power base."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys,copy
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from inventory import sha
import contact_layout as C
import fast_contacts as F
from regulated_outer_joins_r51 import PORTS
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(ROOT/'sbc-power'))
import guarded_power_projection_r44 as P
OUT=HERE/'c-u19008-actual-regulated-search-base-r84'
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();bp=HERE/'regulated-current-power-search-base-r80';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'model.pkl')==br['model_sha256'];g,h,binding,zones,_=pickle.loads((bp/'model.pkl').read_bytes())
 corep=ROOT/'sbc-power/core-pocket-outward-round-guards-r69/new-CORE-zones.pkl';assert sha(corep)=='7009e3cb3d2e8b53b0cb9deedac1806770dba51d70b7071d62f253e99683c310';corrected=pickle.loads(corep.read_bytes());ids={q['uuid'] for q in corrected};assert ids<={q['uuid'] for q in zones};zones=[next(q for q in corrected if q['uuid']==z['uuid']) if z['uuid'] in ids else z for z in zones]
 cp=ROOT/'coupled-recovery/c10036-r25-reference-bridge-recipe-r24.json';assert sha(cp)=='016762020a735b19c932b4f0dc7a1d36b07854844c207f65aba6965caf438f6e';cr=json.loads(cp.read_text());remove=set(cr['removed_source_UUIDs']);oldtracks={t['uuid']:t for t in h['tracks']};assert remove<=set(oldtracks)
 cdis={'vias':[],'tracks':[]}
 for x in cr['new_items']:
  if x['kind']=='via':v={'uuid':x['uuid'],'net':x['raw_net'],'x':x['at_mm'][0],'y':x['at_mm'][1],'d':x['diameter_mm'],'drill':x['drill_mm'],'flashed':LAYERS,'prospective_not_native':True};cdis['vias'].append(v)
  else:cdis['tracks'].append({'uuid':x['uuid'],'net':x['raw_net'],'layer':x['layer'],'a':x['a'],'b':x['b'],'w':x['width_mm'],'prospective_not_native':True})
 czp=Path(cr['new_zone_manifest']['prospective_zone_pickle']);assert sha(czp)=='31efc84c7050c348390b36fce6c3c8cfeb683aa6a9a6cd19272ac1eff2bd7496';cz=pickle.loads(czp.read_bytes());cz=cz[0] if isinstance(cz,list) else cz;assert cz['uuid']=='e852cf0c-fa5e-506c-9a4e-0e91a7593d93';cz=copy.deepcopy(cz);cz['clearance_mm']=.25;cz['C_exact_frozen_native_recipe_owner']='recover14';cz['priority_adapter_owned_separately_by_root_and_SBC']=True
 up=HERE/'u19008-coupled-power-wall-nomination-r82';assert sha(up/'receipt.json')=='e2d5a98972b6ec856e41362f47374f6f47b5b57d01d114d65aa3cff01e842963';ur=json.loads((up/'receipt.json').read_text());assert not ur['failures'];assert sha(up/'proposed-discrete.pkl')==ur['proposed_discrete_sha256'];ud=pickle.loads((up/'proposed-discrete.pkl').read_bytes());old=ur['owned_old_power_track'];assert oldtracks[old['uuid']]==old;remove.add(old['uuid'])
 for t in ud['tracks']:
  if t['w']==.8:t['locked']=True
 h={**h,'tracks':[t for t in h['tracks'] if t['uuid'] not in remove]+cdis['tracks']+ud['tracks'],'vias':h['vias']+cdis['vias']+ud['vias']}
 assert len({t['uuid'] for t in h['tracks']})==len(h['tracks']);assert len({v['uuid'] for v in h['vias']})==len(h['vias'])
 # Keep the exact owned C outline as a hard obligation. Drills are physical
 # voids, not fabricated outline holes; the frozen native chunk is unchanged.
 nativeC=cz.get('zone_outline_shape',cz['shape']);ownholes=[]
 for v in h['vias']:
  if v['net']==cz['net'] and Point(v['x'],v['y']).distance(nativeC)<v['drill']/2:ownholes.append(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64))
 cz['zone_outline_shape']=nativeC;cz['shape']=set_precision(nativeC.difference(unary_union(ownholes)),1e-6)
 trackclips=[];updated=[]
 for z in zones:
  before=z['shape'];outline=z.get('zone_outline_shape',before);cuts=[]
  for t in cdis['tracks']+ud['tracks']:
   if t['layer']!=z['layer'] or t['net']==z['net']:continue
   req=max(.15 if h['domains_normalized'].get(C.norm(t['net']))==h['domains_normalized'].get(C.norm(z['net'])) else .6,float(z.get('clearance_mm',.15)))+.025
   cut=P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+req)
   if cut.intersects(outline):cuts.append(cut)
  if cuts:
   union=unary_union(cuts);body=set_precision(set_precision(before,1e-6).difference(union),1e-6);newoutline=set_precision(set_precision(outline,1e-6).difference(union),1e-6);trackclips.append({'uuid':z['uuid'],'raw_net':z['net'],'layer':z['layer'],'physical_before_sha256':P.digest(before),'physical_after_sha256':P.digest(body),'intended_before_sha256':P.digest(outline),'intended_after_sha256':P.digest(newoutline),'removed_area_mm2':before.difference(body).area,'positive_added_area_mm2':body.difference(before).area,'cutter_sha256':P.digest(union)});z={**z,'shape':body,'zone_outline_shape':newoutline}
  updated.append(z)
 zones,guards=P.normalize_owned_via_guards(h,updated);zones.append(cz)
 binding=copy.deepcopy(binding);binding['field_regulated_search_hard_nominees']={'already_composed':True,'discrete':{'vias':[],'tracks':[]},'planes':[],'not_source_contact_or_current_credit':True,'C_fixed_uuid':cz['uuid'],'C_full_peer_reference_cutter':str((bp/'C10036_full_reference_cutter.wkb').resolve()),'never_carve_C_or_its_retained_reference_mask':True}
 print('project actual C24 and paired U19008 against corrected CORE69',len(zones),flush=True);after,retreats=P.projected(g,h,zones);groups={};census=[]
 for bank,net,ref,pin,policy in PORTS:
  gs=F.graph(after,net);groups[net]=gs;ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));census.append({'bank':bank,'net':net,'actual_source':ref+'.'+pin,'source_group':ri,'remaining':[{'group':i,'pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']]} for i,xs in enumerate(gs) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)]});print(bank,'remaining',len(census[-1]['remaining']),flush=True)
 gn='/motherboard_do/FIELD_B_0V';gs=F.graph(after,gn);ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11005','2') for q in xs));roots={q['uuid'] for q in gs[ri]};ground={'actual_source':'J11005.2','new_U19008_ground_via':ud['vias'][1]['uuid'],'new_U19008_ground_via_source_rooted':ud['vias'][1]['uuid'] in roots,'U19008_ground_pad_source_rooted':all(q['uuid'] in roots for q in h['pads'] if q['ref']=='U19008' and C.norm(q['net'])==gn),'C10036_both_new_ground_vias_source_rooted':[{'uuid':v['uuid'],'rooted':v['uuid'] in roots} for v in cdis['vias']]};print('FB return local status',ground,flush=True)
 (OUT/'model.pkl').write_bytes(pickle.dumps((g,h,binding,zones,after),protocol=5));(OUT/'source-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));(OUT/'U19008-proposed-discrete.pkl').write_bytes(pickle.dumps(ud,protocol=5));write(OUT/'owned-track-removals.json',[oldtracks[u] for u in sorted(remove)]);write(OUT/'owned-track-proposal-clips.json',trackclips);write(OUT/'foreign-via-guard-ledger.json',guards);write(OUT/'oldfill-retreat-ledger.json',retreats);write(OUT/'source-census.json',census);write(OUT/'local-ground-source-status.json',ground)
 write(OUT/'receipt.json',{'verdict':'ACTUAL_C_AND_PAIRED_U19008_SEARCH_MODEL_SOURCE_AND_FULL_JOINT_GATES_OPEN','model_sha256':sha(OUT/'model.pkl'),'input_R80_receipt_sha256':sha(bp/'receipt.json'),'corrected_CORE69_bridge_pickle_sha256':sha(corep),'exact_C24_recipe_sha256':sha(cp),'exact_C_zone_pickle_sha256':sha(czp),'exact_U19008_nomination_receipt_sha256':sha(up/'receipt.json'),'U19008_proposed_discrete_sha256':sha(OUT/'U19008-proposed-discrete.pkl'),'owned_track_removals_sha256':sha(OUT/'owned-track-removals.json'),'owned_track_proposal_clips_sha256':sha(OUT/'owned-track-proposal-clips.json'),'foreign_via_guard_ledger_sha256':sha(OUT/'foreign-via-guard-ledger.json'),'oldfill_retreat_ledger_sha256':sha(OUT/'oldfill-retreat-ledger.json'),'source_census_sha256':sha(OUT/'source-census.json'),'local_ground_source_status':ground,'C_geometry_and_native_priority_adapter_separate':True,'board_written':False,'native_jobs':0,'source_no_loss_reference_all_Cu_aperture_reserved_area_current_native_flash_and_DRC_gates':'OPEN'})
 print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
