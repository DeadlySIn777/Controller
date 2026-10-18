"""Independently bind C10036 to actual selected native FIELD_B_0V refill.

No proposed field/core power body receives actual-native credit. Every hole
and source-rooted annulus is physical; no native invocation or board mutation.
"""
import sys,json,pickle,math,time,collections,copy
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import audit_c10036_r24_full_independent_r30 as H
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union
P,G,S,C,N=A.P,A.G,A.S,A.C,A.N
GROUND=H.GROUND;GATE=H.GATE;POWER=H.POWER;LAYERS=H.LAYERS
def vertices(sh):
 if sh.is_empty:return []
 if sh.geom_type=='Polygon':return list(sh.exterior.coords)+[p for r in sh.interiors for p in r.coords]
 return [p for q in sh.geoms for p in vertices(q)]
def main():
 started=time.monotonic();out=HERE/'c10036-actual-native-reference-independent-r33.json';assert not out.exists();d=HERE.parent/'c10036-native-diagnostic-r1';rr=json.loads(A.read(d/'scoped-native-fill/receipt.json'));overall=json.loads(A.read(d/'receipt.json'));ngraw=A.read(d/'scoped-native-fill/geometry.json');nfraw=A.read(d/'scoped-native-fill/actual-via-flashes.json')
 assert C.sha(ngraw)==rr['geometry_sha256']=='64028d4193fa88c3535226230726bad019b136c64fde60a35f0eaf959e8e4a2c';assert C.sha(nfraw)==rr['actual_via_flashes_sha256']=='3e056b707977322b5090c799e76a9c587ea971bc2d2e881bc9c282c83ac42629'
 for p,pin in rr['input_sha256'].items():assert C.sha(A.read(p))==pin,p
 assert overall['all_native_discrete']['verdict']=='PASS' and overall['source_API_summary']['parity_defects']==0;ng=json.loads(ngraw);fl=json.loads(nfraw)['vias'];nativeboard=A.read(d/'copy/board.kicad_pcb');assert C.sha(nativeboard)==rr['candidate_sha256']==overall['candidate_sha256'];ni=C.inventory(nativeboard)
 recipepath=HERE/'c10036-r25-reference-bridge-recipe-r24.json';recipe=json.loads(A.read(recipepath));assert C.sha(A.read(recipepath))=='016762020a735b19c932b4f0dc7a1d36b07854844c207f65aba6965caf438f6e';auditpath=HERE/'c10036-r24-independent-complete-r30.json';prior=json.loads(A.read(auditpath));assert C.sha(A.read(auditpath))=='b4cd12824af78c21a2d52f2c785ca1f7b3cfef3790158e18ee49832f01456038'
 parent=A.read(recipe['source_parent']);assert C.sha(parent)==recipe['source_parent_sha256']=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';pi=C.inventory(parent);identity=N.SourceNets(parent);identity.assert_no_collisions(nativeboard);assert ni[5]==pi[5]
 removed=set(recipe['removed_source_UUIDs']);new={u:ch.encode() for u,ch in recipe['exact_new_chunks'].items()};newzones={u:ch.encode() for u,ch in recipe['exact_new_zone_chunks'].items()};assert all(u not in ni[3] and pi[3][u]==recipe['exact_removed_chunks'][u].encode() for u in removed);assert all(ni[3][u]==ch for u,ch in new.items());assert all(ni[3][u]==ch for u,ch in newzones.items());assert all(ni[3][u]==ch for u,ch in pi[3].items() if u not in removed);assert set(ni[3])==((set(pi[3])-removed)|set(new)|set(newzones))
 rp=HERE.parent/'field-power/local-and-b5-return-audit-r25';template=pickle.loads(A.read(rp/'discrete.pkl'));assert C.sha(A.read(rp/'discrete.pkl'))=='b5d9b9e5f7f8ca8171e9f7f84bdc28dcd5641e04f1c877c8cf8ef988ce6833b1';base=copy.deepcopy(template);pitems={u:G.parse(u,ch,{}) for u,ch in pi[4].items()};tracks=[];vias=[]
 for u,q in pitems.items():
  if q['kind']=='via':vias.append({'uuid':u,'net':identity.raw(q['net']),'x':q['at'][0],'y':q['at'][1],'d':q['d'],'drill':q['drill'],'flashed':fl[u]})
  else:
   assert q['kind']=='segment';tracks.append({'uuid':u,'net':identity.raw(q['net']),'a':q['a'],'b':q['b'],'w':q['w'],'layer':q['layer']})
 base['tracks']=tracks;base['vias']=vias;base['zones']=template['zones'];final=copy.deepcopy(base);final['tracks']=[];final['vias']=[]
 for t in ng['tracks']:final['tracks'].append({'uuid':t['uuid'],'net':t['net'],'a':t['s'],'b':t['e'],'w':t['w'],'layer':t['layer']})
 for v in ng['vias']:final['vias'].append({'uuid':v['uuid'],'net':v['net'],'x':v['at'][0],'y':v['at'][1],'d':v['w'],'drill':v['drill'],'flashed':fl[v['uuid']]})
 assert len(final['tracks'])==86161 and len(final['vias'])==7909
 ngpads=[p for p in ng['pads'] if L.norm(p['net'])==GROUND];lookup={(p['ref'],p['num']):p for p in ngpads};assert len(lookup)==len(ngpads);bp=[p for p in base['pads'] if L.norm(p['net'])==GROUND];assert len(bp)==len(ngpads)
 padbinding=[]
 for model in (base,final):
  for p in model['pads']:
   if L.norm(p['net'])!=GROUND:continue
   n=lookup[p['ref'],p['num']];assert p['net']==n['net'] and math.dist((p['x'],p['y']),n['at'])<=.000001 and set(p['layers'])==set(n['layers']);p['layers'][n['layers'][0]]=A.polys(n['poly'])
 for p in bp:padbinding.append({'uuid':p['uuid'],'ref':p['ref'],'pin':p['num'],'exact_unchanged_FP_chunk_and_actual_native_pose_layers':True})
 actualzones={z['uuid']:z for z in ng['zones'] if L.norm(z['net'])==GROUND};assert set(actualzones)==set(rr['selected_zone_UUIDs']);oldzones={z['uuid']:z for z in base['zones'] if L.norm(z['net'])==GROUND};assert set(actualzones)==(set(oldzones)|set(newzones));final['zones']=[z for z in final['zones'] if L.norm(z['net'])!=GROUND]
 for u,z in actualzones.items():final['zones'].append({'uuid':u,'net':z['net'],'fills':{l:A.polys(rs) for l,rs in z['fills'].items()},'clearance_mm':.25 if u in newzones else oldzones[u]['clearance_mm'],'priority':124 if u in newzones else oldzones[u]['priority'],'native_actual_selected_refill':True})
 parsed={u:G.parse(u,ch,{}) for u,ch in new.items()};nt={t['uuid']:t for t in ng['tracks']};nv={v['uuid']:v for v in ng['vias']};exact=[]
 for u,q in parsed.items():
  n=nv[u] if q['kind']=='via' else nt[u];assert n['net']==identity.raw(q['net'])
  if q['kind']=='via':assert(n['at'],n['w'],n['drill'])==(q['at'],q['d'],q['drill']);assert set(fl[u])==set(LAYERS)
  else:assert(n['s'],n['e'],n['w'],n['layer'])==(q['a'],q['b'],q['w'],q['layer'])
  exact.append({'uuid':u,'kind':q['kind'],'exact_raw_native_geometry':True,'actual_flash_layers':fl[u] if q['kind']=='via' else None})
 print('C10036_NATIVE_SOURCE_PHYSICAL_GRAPH',flush=True);uf,groups=H.physical(final,GROUND);root=[xs for xs in groups if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11005','2') for q in xs)];assert len(root)==1;root=root[0];rk=H.discrete_keys(root);refs={outl:unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']==plane]) for outl,plane in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]}
 groundstate={'source_root':'J11005.2','actual_native_FBG_pad_groups':sum(any(q['kind']=='pad' for q in xs) for xs in groups),'rooted_native_pad_count':len({q['uuid'] for q in root if q['kind']=='pad'}),'target_C10036_2_source_rooted':any(q['kind']=='pad' and(q['ref'],q['pin'])==('C10036','2') for q in root),'new_returns_source_rooted':{u:('via',u) in rk for u,q in parsed.items() if q['kind']=='via'},'actual_reference_area_mm2':{l:sh.area for l,sh in refs.items()}}
 allfills={outl:unary_union([q['shape'] for xs in groups for q in xs if q['kind']=='fill' and q['layer']==plane]) for outl,plane in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};inherited=nv['40bdf2f9-776c-4aa5-bca6-7921f7c90b54'];assert(inherited['at'],inherited['w'],inherited['drill'],inherited['net'])==([66.55,95.35],.6,.3,identity.raw(GATE));assert set(fl[inherited['uuid']])==set(LAYERS)
 retuid=recipe['new_return_UUID'];ret=nv[retuid];ann=Point(ret['at']).buffer(.25,quad_segs=128).difference(Point(ret['at']).buffer(.1,quad_segs=128));paired={'inherited_signal_uuid':inherited['uuid'],'return_uuid':retuid,'signal_at_mm':inherited['at'],'return_at_mm':ret['at'],'distance_mm':math.dist(inherited['at'],ret['at']),'actual_flash_layers':fl[retuid],'finite_rooted_annular_interior_mm2':{l:sh.buffer(-.075).intersection(ann).area for l,sh in refs.items()},'finite_any_FBG_annular_interior_mm2_diagnostic_only':{l:sh.buffer(-.075).intersection(ann).area for l,sh in allfills.items()},'return_source_rooted':('via',retuid) in rk}
 reference=[];errors=[];gapdir=HERE/'c10036-native-r33-reference-gaps';gapdir.mkdir()
 for u,q in parsed.items():
  if q['kind']!='segment' or q['net']==GROUND:continue
  body=A.shape(q);gap=body.difference(refs[q['layer']]);pts=vertices(gap);rad=max((math.dist(p[:2],inherited['at']) for p in pts),default=0);own=q['net']==GATE and bool(pts) and rad<=.575 and paired['return_source_rooted'] and all(a>=.004 for a in paired['finite_rooted_annular_interior_mm2'].values());row={'uuid':u,'net':q['net'],'layer':q['layer'],'full_body_actual_source_reference_gap_mm2':gap.area,'full_body_any_FBG_reference_gap_mm2_diagnostic_only':body.difference(allfills[q['layer']]).area,'exact_own_transition_radius_mm':.575 if q['net']==GATE else None,'maximum_gap_vertex_radius_mm':rad if q['net']==GATE else None,'qualified_own_transition_exception':own,'gap_after_actual_rooted_own_transition_mm2':0 if own else gap.area,'reference_pass':gap.area<=1e-9 or own}
  if not row['reference_pass']:p=gapdir/(u+'.wkb');p.write_bytes(gap.wkb);row.update(gap_WKB_path=str(p),gap_WKB_sha256=C.sha(gap.wkb));errors.append(row)
  reference.append(row)
 print('C10036_NATIVE_PRIOR_FBG_CONTACT_GRAPH',flush=True);olduf,oldgroups=H.physical(base,GROUND);oldroot=next(xs for xs in oldgroups if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11005','2') for q in xs));mapping=collections.defaultdict(set)
 for i,xs in enumerate(groups):
  for k in H.discrete_keys(xs):mapping[k].add(i)
 contactloss=[];obligations=[]
 for i,xs in enumerate(oldgroups):
  keys=H.discrete_keys(xs);parts=set().union(*(mapping.get(k,{'MISSING'}) for k in keys)) if keys else set();row={'old_group':i,'surviving_discrete_keys':[list(k) for k in sorted(keys)],'actual_native_components':sorted(str(p) for p in parts)};obligations.append(row)
  if len(parts)>1 or 'MISSING' in parts:contactloss.append(row)
 oldrefs={outl:unary_union([q['shape'] for q in oldroot if q['kind']=='fill' and q['layer']==plane]) for outl,plane in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};neighbor=[]
 for t in base['tracks']:
  if t['uuid'] in removed or t['layer'] not in refs or L.norm(t['net'])==GROUND or base['domains_normalized'].get(L.norm(t['net']))!=base['domains_normalized'][GROUND]:continue
  lost=A.shape({'kind':'segment',**t}).intersection(oldrefs[t['layer']]).difference(refs[t['layer']])
  if lost.area>1e-9:neighbor.append({'uuid':t['uuid'],'raw_net':t['net'],'layer':t['layer'],'prior_source_reference_lost_mm2':lost.area})
 saved=HERE/'c10036-native-r33-actual-model.pkl';saved.write_bytes(pickle.dumps({'base':base,'actual':final,'groups':groups,'root_reference':refs,'all_FBG_reference':allfills},protocol=5));passed=not(errors or contactloss or neighbor) and groundstate['target_C10036_2_source_rooted'] and all(groundstate['new_returns_source_rooted'].values()) and paired['return_source_rooted'] and all(a>=.004 for a in paired['finite_rooted_annular_interior_mm2'].values())
 report={'verdict':'ACTUAL_SELECTED_NATIVE_FBG_REFERENCE_CONTACT_AND_RETURN_PASS' if passed else'ACTUAL_SELECTED_NATIVE_FBG_REFERENCE_OR_SOURCE_CONTACT_OPEN','scope':'Only exact eedf plus C24 operation, all selected FBG zones fresh; no R25/new PDN proposals credited','native_candidate_sha256':C.sha(nativeboard),'fresh_native_geometry_sha256':C.sha(ngraw),'fresh_native_flash_sha256':C.sha(nfraw),'source_parent_sha256':C.sha(parent),'exact_operation_and_unchanged_FPs_source_entities':True,'exact_new_native_discrete':exact,'actual_FBG_pad_binding':padbinding,'actual_ground_source_status':groundstate,'actual_paired_return':paired,'new_full_body_reference':reference,'reference_errors':errors,'all_prior_FBG_contact_obligations':obligations,'lost_prior_FBG_contact_groups':contactloss,'unchanged_neighbor_prior_source_reference_losses':neighbor,'saved_actual_model_path':str(saved),'saved_actual_model_sha256':C.sha(saved.read_bytes()),'whole_board_power_proposal_recomposition_fullnative_DRC_current_r06_r07_and_SI':'OPEN','adopted':False,'native_jobs':0,'board_written':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started}
 for p,pin in A.READS.items():assert C.sha(Path(p).read_bytes())==pin,p
 out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'receipt':str(out),'verdict':report['verdict'],'ground':groundstate,'paired':paired,'reference_errors':len(errors),'contact_losses':len(contactloss),'neighbor_losses':len(neighbor),'sha256':C.sha(out.read_bytes())}),flush=True)
if __name__=='__main__':main()
