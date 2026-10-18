"""Latest exact C/CORE/ROOT base plus corrected U19008 and retained REG scope."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,sys,copy
from pathlib import Path
from shapely import set_precision,STRtree,from_wkb
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
from inventory import sha
from regulated_outer_joins_r51 import PORTS
H=Path(__file__).resolve().parent;ROOT=H.parent;sys.path.insert(0,str(ROOT/'sbc-power'))
import guarded_power_projection_r44 as P
import owned_analytic_track_guards_r75 as TG
O=H/'corrected-regulated-joint-search-base-r103';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();bp=H/'c24-only-core91-root4-source-context-r100';assert sha(bp/'model.pkl')=='9129edacd232c8156118a14a0a0594943142e59bd96e34f470c21eb8ae28e697';g,h,b,z,prior=pickle.loads((bp/'model.pkl').read_bytes());z=copy.deepcopy(z);old={t['uuid']:t for t in h['tracks']};ur=H/'u19008-corrected-native-owned-recipe-r102/receipt.json';assert sha(ur)=='1d012f2eb0b92b3dac83bab686c1506f1783251a19ff3536f361915f39e29003';r=json.loads(ur.read_text());remove={q['uuid'] for q in r['exact_original_deletes']};assert remove<=set(old)
 dp=H/'u19008-outside-reservation-branch-tree-r89/proposed-discrete.pkl';ud=pickle.loads(dp.read_bytes());rp=H/'u19008-retained-logic-barrel-relocation-r95/owned-replacements.pkl';replace=pickle.loads(rp.read_bytes());qm=H/'u19008-source-return-reference-r99/proposed-zones.pkl';uq=pickle.loads(qm.read_bytes());assert sha(dp)=='23c9a1f413da1723268203a6fe319a7b17505bba1df463136be671491c030a42' and sha(rp)=='1d3052cb375c149f8243ea53b917ecdb0f014b9578446b9cf6a9396fc7a3fa81' and sha(qm)=='728c56d5fc0ee145822e9d823883d6928cd65f80b1afd5696810e5aa281bded9'
 regs=H/'regulated-current-power-search-base-r80';rd=pickle.loads((regs/'retained-regulated-discrete.pkl').read_bytes());assert sha(regs/'retained-regulated-discrete.pkl')=='baf86ab1cb4f8c382e65bcb3834bf1397bb44fa27fcb18eef07b17783f95ecb4';owned=pickle.loads((regs/'proposed-zones.pkl').read_bytes());assert sha(regs/'proposed-zones.pkl')=='1e6cd04e076412c03fb7b7189647478f3fd262b3dd79129b8bd03ab88b6b08b5';assert len(owned)==18 and len(rd['vias'])==17 and len(rd['tracks'])==17
 ac=H/'regulated-adaptive-source-feeds-r76';term=json.loads((ac/'owned-termination-r1.json').read_text());assert sha(ac/'owned-termination-r1.json')=='cb703afd6d098e3e91a71e53b6818c40b71e1bc0eea598d2b28a586af7e93e9e';hashes=term['accepted_checkpoint_and_object_hashes'];assert sha(ac/'proposed-discrete.pkl')==hashes['proposed-discrete.pkl'] and sha(ac/'proposed-zones.pkl')==hashes['proposed-zones.pkl'];ad=pickle.loads((ac/'proposed-discrete.pkl').read_bytes());aq=pickle.loads((ac/'proposed-zones.pkl').read_bytes());assert len(ad['vias'])==1 and len(ad['tracks'])==1 and len(aq)==1;owned+=aq
 oldrep={'vias':{q['uuid']:q for q in replace['vias']},'tracks':{q['uuid']:q for q in replace['tracks']}};newd={k:ud[k]+rd[k]+ad[k] for k in ('tracks','vias')}
 for k in ('tracks','vias'):
  assert not ({q['uuid'] for q in newd[k]}&{q['uuid'] for q in h[k]});h[k]=[oldrep[k].get(q['uuid'],q) for q in h[k] if q['uuid'] not in remove]+newd[k]
 z+=uq;rec,trees=F.build({**h,'zones':[]});viamap={v['uuid']:v for v in h['vias']};trackmap={t['uuid']:t for t in h['tracks']};shapeled=[];corrected=[];peerpath=ROOT/'coupled-recovery/c10036-peer-reference-mask-r26.wkb';assert sha(peerpath)=='c15b7bc932faf123137a73c2a7ea3020e78da2e6aca94fba8cd72f5ef51e5b55';mask=from_wkb(peerpath.read_bytes());peerrecords=z+[{'uuid':'C10036-all-retained-B-power-reference-mask','net':'/motherboard_do{slash}FIELD_B_0V','layer':'In4.Cu','shape':mask,'clearance_mm':.25}]
 for q in owned:
  before=q['shape'];out=q.get('zone_outline_shape',before);cuts=[]
  def gap(raw,local=.15):return max(.15 if h['domains_normalized'].get(C.norm(raw))==h['domains_normalized'].get(C.norm(q['net'])) else .6,local)+.025
  for j in trees[q['layer']].query(out.buffer(.627),predicate='intersects'):
   x=rec[q['layer']][int(j)]
   if x['net']==q['net']:continue
   req=gap(x['net'])
   if x['kind']=='track':t=trackmap[x['uuid']];cut=P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+req)
   elif x['kind']=='via':v=viamap[x['uuid']];cut=P.bounded_disk(v,v['d']/2+req)
   else:cut=P.bounded_buffer(x['shape'],req)
   if cut.intersects(out):cuts.append(cut)
  for x in peerrecords:
   if x['layer']!=q['layer'] or x['net']==q['net'] or not x['shape'].intersects(out.buffer(.627)):continue
   cut=P.bounded_buffer(x['shape'].intersection(out.buffer(.627)),gap(x['net'],float(x.get('clearance_mm',.15))))
   if cut.intersects(out):cuts.append(cut)
  cutter=unary_union(cuts);body=set_precision(set_precision(before,1e-6).difference(cutter),1e-6);outline=set_precision(set_precision(out,1e-6).difference(cutter),1e-6);new={**q,'shape':body,'zone_outline_shape':outline};corrected.append(new);shapeled.append({'uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'before_sha256':P.digest(before),'after_sha256':P.digest(body),'intended_before_sha256':P.digest(out),'intended_after_sha256':P.digest(outline),'physical_removed_mm2':before.difference(body).area,'quantization_added_mm2':body.difference(before).area,'cutter_sha256':P.digest(cutter)})
 # Replay newly owned discrete changes on actual latest peer planes. All
 # original outline definitions stay immutable; each proposal change is bound.
 updates=[];cutsledger=[]
 for q in z:
  before=q['shape'];out=q.get('zone_outline_shape',before);cuts=[]
  for t in newd['tracks']+replace['tracks']:
   if t['layer']!=q['layer'] or t['net']==q['net']:continue
   req=max(.15 if h['domains_normalized'].get(C.norm(t['net']))==h['domains_normalized'].get(C.norm(q['net'])) else .6,float(q.get('clearance_mm',.15)))+.025;cut=P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+req)
   if cut.intersects(out):cuts.append(cut)
  if cuts:
   cutter=unary_union(cuts);body=set_precision(set_precision(before,1e-6).difference(cutter),1e-6);outline=set_precision(set_precision(out,1e-6).difference(cutter),1e-6);q={**q,'shape':body,'zone_outline_shape':outline};cutsledger.append({'uuid':q['uuid'],'before_sha256':P.digest(before),'after_sha256':P.digest(body),'intended_before_sha256':P.digest(out),'intended_after_sha256':P.digest(outline),'removed_mm2':before.difference(body).area,'added_mm2':body.difference(before).area,'cutter_sha256':P.digest(cutter)})
  updates.append(q)
 z,guards=P.normalize_owned_via_guards(h,updates+corrected);z,trackguards=TG.normalize_owned_track_guards(h,z);ownedids={q['uuid'] for q in owned};corrected=[q for q in z if q['uuid'] in ownedids];b=copy.deepcopy(b);b['field_regulated_search_hard_nominees']={'already_composed':True,'discrete':{'vias':[],'tracks':[]},'planes':[],'C_fixed_uuid':'e852cf0c-fa5e-506c-9a4e-0e91a7593d93','never_carve_C_or_its_retained_reference_mask':True,'source_qualified_peer_ROOT_spine_UUIDs_hard':[q['uuid'] for q in pickle.loads((ROOT/'protected-field-return-r4-snapshot-4/proposed-zones.pkl').read_bytes())]};b['corrected_U19008_same_UUID_native_operations_sha256']=sha(ur)
 print('R103 full current projection',len(z),'zones',len(h['vias']),'vias',flush=True);after,oldfill=P.projected(g,h,z);census=[];groups={}
 for bank,net,ref,pin,policy in PORTS:
  gs=F.graph(after,net);groups[net]=gs;ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));census.append({'bank':bank,'net':net,'source_group':ri,'actual_source':ref+'.'+pin,'remaining':[{'group':i,'pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']]} for i,xs in enumerate(gs) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)]});print(bank,'remaining',len(census[-1]['remaining']),flush=True)
 (O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,after),protocol=5));(O/'source-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));(O/'owned-regulated-planes.pkl').write_bytes(pickle.dumps(corrected,protocol=5));(O/'owned-new-discrete.pkl').write_bytes(pickle.dumps(newd,protocol=5));write(O/'new_owned_old_original_deletes.json',[old[u] for u in sorted(remove)]);write(O/'source-census.json',census);write(O/'regulated-peer-shape-ledger.json',shapeled);write(O/'current-peer-track-cuts.json',cutsledger);write(O/'foreign-via-guards.json',guards);write(O/'full-analytic-track-guards.json',trackguards);write(O/'oldfill-retreats.json',oldfill)
 write(O/'receipt.json',{'verdict':'LATEST_CORRECTED_FULL_HARD_SEARCH_BASE_NOT_ACCEPTED_SOURCE_CURRENT_OR_NATIVE_COMPLETE','model_sha256':sha(O/'model.pkl'),'input_C_CORE91_ROOT4_sha256':sha(bp/'model.pkl'),'corrected_U19008_native_recipe_sha256':sha(ur),'retained17_REG_discrete_sha256':sha(regs/'retained-regulated-discrete.pkl'),'accepted_R76_termination_sha256':sha(ac/'owned-termination-r1.json'),'owned_REG19_plane_sha256':sha(O/'owned-regulated-planes.pkl'),'owned_new_discrete_sha256':sha(O/'owned-new-discrete.pkl'),'source_census_sha256':sha(O/'source-census.json'),'source_groups_sha256':sha(O/'source-groups.pkl'),'regulated_peer_clip_sha256':sha(O/'regulated-peer-shape-ledger.json'),'current_peer_track_cuts_sha256':sha(O/'current-peer-track-cuts.json'),'foreign_via_guard_sha256':sha(O/'foreign-via-guards.json'),'full_track_guard_sha256':sha(O/'full-analytic-track-guards.json'),'oldfill_retreat_sha256':sha(O/'oldfill-retreats.json'),'all_old_source_relationship_REFERENCE_actual_native_flash_current_transient_thermal_gates':'OPEN','native_jobs':0,'board_written':False});print('R103 frozen',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
