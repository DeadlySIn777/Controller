"""Construct DIC with one exact CMD blocker added after strict additive locus failure.

Exact original four deletes and fixed CS/RSP replacements are retained;
only unaccepted DIC path and ordinary new transition locations are varied.
"""
import sys,json,pickle,time,math,copy
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_aux_exact_raw as A
import contact_layout as L
import guarded_power_projection_r44 as Z
import construct_di6_direct_source_escape_r5 as K
import audit_c10036_r24_full_independent_r30 as Q
import audit_ao1_positive_operation_r4 as SERIAL
import construct_DIC_three_track_coupled_r164 as B
import physical_reference_losses_r2 as RF
import tri_route as T
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
C=A.C;NET=B.NET;GND=B.GND;CS=B.CS;RSP=B.RSP;CMD='/motherboard_io_control/DIC_IOL1_CMD_BUFFER';LAYERS=B.LAYERS

def main():
 started=time.monotonic();out=H/'DIC-actual-paired-CMD-construction-r186.json';assert not out.exists();A.read(__file__);rp=H/'DIC-neighbour-safe-site-nomination-r170.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='94bd456d0c2849dfd3a7bf0df56f9949826c1a8b651da1d3095cc6a51301d769';assert next(q['options'] for q in r['nominations'] if q['kind']=='target');r176p=H/'DIC-source-reachable-paired-locus-r176.json';assert C.sha(A.read(r176p))=='b612ab99c8dbe5bb58b4a5c33a9b2f5b88ef88382aaad1eaf768a96c5073658c';cmdrp=H/'DIC-CMD-fresh-ordinary-return-r184.json';cmdr=json.loads(A.read(cmdrp));assert C.sha(A.read(cmdrp))=='14632c0e8a423fa209e47ca0eb4006d97e4f4ff49a2a38ba8e13be321876ffde';assert cmdr['new_return_options'];r164p=H/'DIC-three-track-coupled-r164.json';r164=json.loads(A.read(r164p));assert C.sha(A.read(r164p))=='cdb152ede9fbb637191668297405e07af5be24f7e984dc23687dd37d5209ca4b';raw=A.read(r164['selected']['model_file']);assert C.sha(raw)=='7e11621fb23ee9fdabdbed66ca3edf51841848d231c50f02370305e5fc5e16b5';prior=pickle.loads(raw);cur=prior['current'];source=A.read(cur['binding']['exact_native_discrete_board_file']);assert C.sha(source)==r164['source_parent_sha256'];identity=A.N.SourceNets(source);inv=C.inventory(source);removed=set(prior['removed_UUIDs'])|{'811a28fc-3124-4526-b8b8-287522e6a219'};deletes={**prior['exact_deleted_chunks'],'811a28fc-3124-4526-b8b8-287522e6a219':inv[3]['811a28fc-3124-4526-b8b8-287522e6a219']};assert b'(locked yes)' in deletes['811a28fc-3124-4526-b8b8-287522e6a219'];assert all(inv[3][u]==deletes[u] and source.count(deletes[u])==1 for u in removed);h0=cur['h'];beforegroups={n:Q.physical(cur['after'],n)[1] for n in(NET,CS,RSP,CMD)};fixed=[q for q in prior['new_tracks'] if L.norm(q['net'])!=NET];fixedchunks={q['uuid']:prior['exact_new_chunks'][q['uuid']] for q in fixed};assert len(fixed)==6;sourceopts=[{'signal':[127.057072,98.292323],'pairs':[{'return':[126.466153,97.716620],'return_new':True,'old_return_UUID':None,'distance_mm':.824996490156163}]}];targetopts=next(q['options'] for q in r['nominations'] if q['kind']=='target');targetopts=[{**q,'pairs':[{**p,'return_new':True,'old_return_UUID':None} for p in q['pairs']]} for q in targetopts];policy={L.norm(n):q for n,q in json.loads(A.read(A.S.CONTROLLED))['nets'].items()};assert policy.get(CMD,{}).get('class') in(None,'NONE');win=box(121,86,137,102);oldrefs={l:cur['refs'][l] for l in('F.Cu','B.Cu','In3.Cu')} if all(l in cur['refs'] for l in('F.Cu','B.Cu','In3.Cu')) else None;attempts=[];selected=None
 # All sources remain physically exact nominees; bounded sequence prioritizes
 # the smallest shift and a real old return before a new drilled return.
 candidates=[]
 for so in sourceopts[:12]:
  for to in targetopts[:4]:
   sp=sorted(so['pairs'],key=lambda q:(q['return_new'],q['distance_mm']))[:3];tp=sorted(to['pairs'],key=lambda q:(q['return_new'],q['distance_mm']))[:2]
   for a in sp:
    for b in tp:
     for cmdp in cmdr['new_return_options']:candidates.append((so,to,a,b,cmdp))
 for so,to,sr,tr,cmdp in candidates:
  h=copy.deepcopy(h0);h['tracks']=[q for q in h['tracks'] if q['uuid'] not in removed]+copy.deepcopy(fixed);nt=copy.deepcopy(fixed);nv=[];chunks=dict(fixedchunks);pairs=[];newpoints=[so['signal'],to['signal']]+[p['return'] for p in(sr,tr) if p['return_new']]+[cmdp['return_at_mm']];row={'source_signal_at_mm':so['signal'],'target_signal_at_mm':to['signal'],'source_pair_nominee':sr,'target_pair_nominee':tr,'CMD_actual_signal_new_pair_nominee':cmdp,'routes':[]};attempts.append(row)
  if any(math.dist(a,b)<.815 for i,a in enumerate(newpoints) for b in newpoints[i+1:]):row['failure']='new_mutual_pitch';continue
  signals=[]
  for pos in(so['signal'],to['signal']):
   uid,ch=SERIAL.serial_via(identity,NET,pos);v={'uuid':uid,'net':identity.raw(NET),'x':pos[0],'y':pos[1],'d':.5,'drill':.2,'flashed':list(LAYERS)};signals.append(v);nv.append(v);chunks[uid]=ch
  for signal,p in zip(signals,(sr,tr)):
   if p['return_new']:
    uid,ch=SERIAL.serial_via(identity,GND,p['return']);v={'uuid':uid,'net':identity.raw(GND),'x':p['return'][0],'y':p['return'][1],'d':.5,'drill':.2,'flashed':list(LAYERS)};nv.append(v);chunks[uid]=ch
   else:
    v=next(v for v in h['vias'] if v['uuid']==p['old_return_UUID']);assert [v['x'],v['y']]==p['return'] and L.norm(v['net'])==GND and all(l in v['flashed'] for l in('In1.Cu','In4.Cu'))
   pairs.append((signal,v,p['return_new']))
  cmdsignal=next(v for v in h['vias'] if v['uuid']=='1f815e33-e973-46e2-833e-96fee8d37fcf');assert L.norm(cmdsignal['net'])==CMD and(cmdsignal['x'],cmdsignal['y'],cmdsignal['d'],cmdsignal['drill'])==(128.549999,100.55,.6,.3);uid,ch=SERIAL.serial_via(identity,GND,cmdp['return_at_mm']);cmdreturn={'uuid':uid,'net':identity.raw(GND),'x':cmdp['return_at_mm'][0],'y':cmdp['return_at_mm'][1],'d':.5,'drill':.2,'flashed':list(LAYERS)};nv.append(cmdreturn);chunks[uid]=ch;pairs.append((cmdsignal,cmdreturn,True));h['vias']+=nv;pre,_=B.project(cur,h,nt,nv);root,refs,_=B.refs_for(pre);lostroot=Q.discrete_keys(cur['root'])-Q.discrete_keys(root)
  pairproof=[]
  for signal,ret,isnew in pairs:
   p=Point(ret['x'],ret['y']);ann=p.buffer(ret['d']/2,quad_segs=128).difference(p.buffer(ret['drill']/2,quad_segs=128));pairproof.append({'signal_UUID':signal['uuid'],'signal_at_mm':[signal['x'],signal['y']],'return_UUID':ret['uuid'],'return_at_mm':[ret['x'],ret['y']],'return_new':isnew,'return_exact_diameter_drill_mm':[ret['d'],ret['drill']],'distance_mm':math.dist([signal['x'],signal['y']],[ret['x'],ret['y']]),'actual_source_interior_annular_contacts_mm2':{l:ann.intersection(sh.buffer(-.075,quad_segs=128)).area for l,sh in refs.items()},'signal_exact_own_radius_mm':(.575 if L.norm(signal['net'])==CMD else .525),'signal_raw_net':signal['net'],'signal_new':signal['uuid'] in{q['uuid'] for q in nv},'actual_retained_signal_flash_layers':signal['flashed'],'radius_expansion_mm':0})
  row['paired_returns_after_all_holes']=pairproof
  if lostroot or any(q['distance_mm']>1 or any(a<.004 for a in q['actual_source_interior_annular_contacts_mm2'].values()) for q in pairproof):row['failure']='source_or_real_pair_after_holes';continue
  # Attach to exact current source/target pad component metal, never centroid.
  groups=beforegroups[NET];wanted=set(prior['source_relationship_pad_UUIDs']);sg=next(xs for xs in groups if any(q['kind']=='pad' and q['uuid']=='73d7d605-feb4-47ae-b36a-40896fba4ee9' for q in xs));tg=next(xs for xs in groups if any(q['kind']=='pad' and q['uuid']=='c9bab2fa-e6cb-45f7-b879-a934865b0e12' for q in xs));attach=[]
  for xs,pos in((sg,so['signal']),(tg,to['signal'])):
   metal=unary_union([q['shape'] for q in xs if q['layer']=='F.Cu']);p=nearest_points(metal.buffer(-.05,quad_segs=128),Point(pos))[0];attach.append([round(x,6) for x in p.coords[0]])
  requested=[(CMD,'B.Cu',[123.05,95.05],[128.549999,100.55]),(NET,'F.Cu',attach[0],so['signal']),(NET,'B.Cu',so['signal'],to['signal']),(NET,'F.Cu',to['signal'],attach[1])];own=unary_union([Z.bounded_disk(v,.525) for v in signals])
  for route_net,layer,a,b in requested:
   plane='In1.Cu' if layer=='F.Cu' else'In4.Cu';scope=own if route_net==NET else Z.bounded_disk(cmdsignal,.575);free=B.physical_centres(h,cur,route_net,layer,win).intersection(refs[plane].union(scope).intersection(win.buffer(1)).buffer(-.105,quad_segs=128));parts=[q for q in K.pieces(free) if q.covers(Point(a)) and q.covers(Point(b))];q={'raw_net':identity.raw(route_net),'layer':layer,'actual_source_reference_layer':plane,'requested_endpoints_mm':[a,b],'continuous_components':len(parts)};row['routes'].append(q);print('DIC_R186_EXACT_ROUTE',len(attempts),layer,len(parts),flush=True)
   if not parts:row['failure']='no_strict_physical_reference_component_'+layer;break
   path,search=T.route(parts[0],tuple(a),tuple(b));path=[[round(x,6),round(y,6)] for x,y in path];body=unary_union([A.shape({'kind':'segment','a':pa,'b':pb,'w':.2}) for pa,pb in zip(path,path[1:])]);q.update({'points_mm':path,'length_mm':LineString(path).length,'width_mm':.2,'actual_full_body_gap_mm2':body.difference(refs[plane].union(scope)).area,'search':search})
   if q['actual_full_body_gap_mm2']>0:row['failure']='strict_new_full_body_reference';break
   for pa,pb in zip(path,path[1:]):
    uid,ch=identity.serial_segment(route_net,layer,pa,pb,.2);ch=ch.replace(b'(width 0.2)',b'(width 0.2) (locked yes)') if route_net==CMD else ch;assert route_net!=CMD or b'(locked yes)' in ch;assert uid not in inv[3] and uid not in chunks;t={'uuid':uid,'net':identity.raw(route_net),'layer':layer,'a':pa,'b':pb,'w':.2};nt.append(t);h['tracks'].append(t);chunks[uid]=ch
  if row.get('failure'):continue
  identity.assert_chunks(chunks);after,ledger=B.project(cur,h,nt,nv);root,finalrefs,groups=B.refs_for(after);lostroot=sorted(Q.discrete_keys(cur['root'])-Q.discrete_keys(root));contacts={};losses=[]
  for n in(NET,CS,RSP,CMD):
   obligations,lost=B.current_preservation(beforegroups[n],Q.physical(after,n)[1],removed);contacts[n]=obligations;losses.extend({'net':n,**q} for q in lost)
  joined=any(wanted<={q['uuid'] for q in xs if q['kind']=='pad'} for xs in Q.physical(after,NET)[1]);oldroot,orefs,_=B.refs_for(cur['after']);oref={'F.Cu':orefs['In1.Cu'],'B.Cu':orefs['In4.Cu'],'In3.Cu':orefs['In4.Cu']};nref={'F.Cu':finalrefs['In1.Cu'],'B.Cu':finalrefs['In4.Cu'],'In3.Cu':finalrefs['In4.Cu']};neighbours,nproof=RF.audit(cur['after'],oref,nref,GND,removed=removed);fullbodies=[]
  for t in nt:
   plane='In1.Cu' if t['layer']=='F.Cu' else'In4.Cu';scope=own if L.norm(t['net'])==NET else (Z.bounded_disk(cmdsignal,.575) if L.norm(t['net'])==CMD else Point());body=A.shape({'kind':'segment',**t});fullbodies.append({'UUID':t['uuid'],'raw_net':t['net'],'layer':t['layer'],'gap_mm2':body.difference(finalrefs[plane].union(scope)).area})
  row.update({'final_LG_source_keys_lost':[list(k) for k in lostroot],'surviving_contact_losses':losses,'exact_r06_target_pad_relationship_joined':joined,'unchanged_neighbour_reference_losses':neighbours,'exact_neighbour_delta_proof':nproof,'all_final_new_full_body_reference':fullbodies})
  if lostroot or losses or not joined or neighbours or any(q['gap_mm2']>0 for q in fullbodies):continue
  model=H/'DIC-actual-paired-CMD-construction-r186-model.pkl';assert not model.exists();model.write_bytes(pickle.dumps({'current':cur,'h':h,'after':after,'new_tracks':nt,'new_vias':nv,'removed_UUIDs':sorted(removed),'exact_deleted_chunks':deletes,'exact_new_chunks':chunks,'refs':finalrefs,'root':root,'groups':groups,'source_relationship_pad_UUIDs':sorted(wanted),'paired_returns':pairproof,'all_current_contact_obligations':contacts},protocol=5));selected={**row,'model_file':str(model),'model_sha256':C.sha(model.read_bytes()),'exact_deleted_chunks':{u:ch.decode() for u,ch in deletes.items()},'exact_new_chunks':{u:ch.decode() for u,ch in chunks.items()},'projection_ledger':ledger,'new_track_count':len(nt),'new_via_count':len(nv)};break
 report={'verdict':'DIC_EXACT_REAL_PAIRED_CMD_CONSTRUCTION_POSITIVE_INDEPENDENT_OPEN' if selected else'DIC_EXACT_REAL_PAIRED_CMD_CONSTRUCTION_INCOMPLETE','source_parent_sha256':C.sha(source),'current_model_sha256':r164['current_model_sha256'],'R170_receipt_sha256':C.sha(A.read(rp)),'R176_source_reachable_paired_locus_failure_sha256':C.sha(A.read(r176p)),'R184_CMD_new_ordinary_return_sha256':C.sha(A.read(cmdrp)),'CMD_original_signal_via_pose_diameter_drill_annuli_unchanged':True,'no_SAME_PLANE_policy_exception':True,'new_CMD_segments_preserve_locked_yes':True,'removed_exact_source_UUIDs':sorted(removed),'attempts':attempts,'selected':selected,'signal_layer_chain':['F.Cu','B.Cu','F.Cu'],'signal_layer_segments':3,'source_FP_project_rules_zone_outlines_changed':0,'full_latest_mutual_independent_layer_contacts_native_r06_r07_DRC_current_SI':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'attempts':len(attempts),'selected':None if not selected else{'model_sha256':selected['model_sha256'],'new_tracks':selected['new_track_count'],'new_vias':selected['new_via_count']}}),flush=True)
if __name__=='__main__':main()
