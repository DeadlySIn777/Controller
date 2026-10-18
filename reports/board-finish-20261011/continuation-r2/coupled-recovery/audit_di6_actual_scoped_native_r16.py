"""Bind the selected eedf+eleven-item DI6 clone to actual fresh GND fill.

Source/root/reference/contact diagnostics only; other PDN proposals receive
no native credit. No native invocation, source write, board save or adoption.
"""
import sys,json,pickle,copy,math,time,collections
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import audit_c10036_r24_full_independent_r30 as Q
import physical_reference_losses_r1 as RF
from shapely.geometry import Point
from shapely.ops import unary_union
P,G,S,C,N=A.P,A.G,A.S,A.C,A.N
GROUND='/LOGIC_GND';NET='/motherboard_di/DI6_LOGIC';LAYERS=Q.LAYERS
SIG='65920d23-af51-5551-a4a2-bc8273927a44';RET='eea4f681-f21b-5b3a-a1af-7c6ba82e51a1';SRC='8cb51ce7-ffcc-432a-90f1-6f2c2e13b06f';TARGET='3a0b46f2-c120-45e5-b93f-8d687e955639'

def vertices(sh):
 if sh.is_empty:return []
 if sh.geom_type=='Polygon':return list(sh.exterior.coords)+[p for r in sh.interiors for p in r.coords]
 return [p for q in getattr(sh,'geoms',[]) for p in vertices(q)]
def root_refs(g):
 uf,groups=Q.physical(g,GROUND);roots=[xs for xs in groups if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11001','2') for q in xs)];assert len(roots)==1;root=roots[0];refs={l:unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']==plane]) for l,plane in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')]};return uf,groups,root,refs
def main():
 started=time.monotonic();out=HERE/'di6-actual-native-reference-independent-r16.json';assert not out.exists();A.read(__file__);A.read(Q.__file__);A.read(RF.__file__);d=HERE.parent/'di6-native-diagnostic-r1';rr=json.loads(A.read(d/'scoped-native-fill/receipt.json'));overall=json.loads(A.read(d/'receipt.json'));ngraw=A.read(d/'scoped-native-fill/geometry.json');nfraw=A.read(d/'scoped-native-fill/actual-via-flashes.json');assert C.sha(ngraw)==rr['geometry_sha256'];assert C.sha(nfraw)==rr['actual_via_flashes_sha256']
 for p,pin in rr['input_sha256'].items():assert C.sha(A.read(p))==pin,p
 assert overall['all_native_discrete']['verdict']=='PASS' and overall['source_API_summary']['parity_defects']==0 and overall['native_fill_exit']==0;ng=json.loads(ngraw);fl=json.loads(nfraw)['vias'];nativeboard=A.read(d/'copy/board.kicad_pcb');assert C.sha(nativeboard)==rr['candidate_sha256']==overall['candidate_sha256'];ni=C.inventory(nativeboard)
 ledger=json.loads(A.read(HERE/'di6-native-owned-ledger-r14/receipt.json'));assert C.sha(A.read(HERE/'di6-native-owned-ledger-r14/receipt.json'))=='6d7dcdc50a10393138761a0067fb73325eace8307800358d72723adcbb1afd79';prior=json.loads(A.read(ledger['host_independent_receipt']));assert C.sha(A.read(ledger['host_independent_receipt']))=='d6468fbf689a15f94e157318067358eec8c323eda202355194f9cde41879a8cb';parent=A.read(ledger['source_parent']);assert C.sha(parent)==ledger['source_parent_sha256']=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';pi=C.inventory(parent);identity=N.SourceNets(parent);identity.assert_no_collisions(nativeboard);new={u:ch.encode() for u,ch in prior['exact_new_chunks'].items()};assert len(new)==11 and ni[0]==pi[0] and ni[2]==pi[2] and set(ni[3])==set(pi[3])|set(new);assert all(ni[3][u]==ch for u,ch in pi[3].items());assert all(ni[3][u]==ch for u,ch in new.items())
 templatepath=HERE.parent/'field-power/local-and-b5-return-audit-r25/discrete.pkl';template=pickle.loads(A.read(templatepath));assert C.sha(A.read(templatepath))=='b5d9b9e5f7f8ca8171e9f7f84bdc28dcd5641e04f1c877c8cf8ef988ce6833b1';base=copy.deepcopy(template);base['tracks']=[];base['vias']=[]
 for u,ch in pi[4].items():
  q=G.parse(u,ch,{})
  if q['kind']=='via':base['vias'].append({'uuid':u,'net':identity.raw(q['net']),'x':q['at'][0],'y':q['at'][1],'d':q['d'],'drill':q['drill'],'flashed':fl[u]})
  else:assert q['kind']=='segment';base['tracks'].append({'uuid':u,'net':identity.raw(q['net']),'a':q['a'],'b':q['b'],'w':q['w'],'layer':q['layer']})
 final=copy.deepcopy(base);final['tracks']=[{'uuid':t['uuid'],'net':t['net'],'a':t['s'],'b':t['e'],'w':t['w'],'layer':t['layer']} for t in ng['tracks']];final['vias']=[{'uuid':v['uuid'],'net':v['net'],'x':v['at'][0],'y':v['at'][1],'d':v['w'],'drill':v['drill'],'flashed':fl[v['uuid']]} for v in ng['vias']];assert len(final['tracks'])==len(pi[4])-len(base['vias'])+9 and len(final['vias'])==len(base['vias'])+2
 # Whole unchanged footprint chunks give exact full pad/physical hole source
 # authority; bind actual exported pose/net/layer and first-layer outline.
 ngpads=[p for p in ng['pads'] if L.norm(p['net']) in(GROUND,NET)];lookup=collections.defaultdict(list)
 for p in ngpads:lookup[p['ref'],str(p['num'])].append(p)
 selected=[p for p in base['pads'] if L.norm(p['net']) in(GROUND,NET)];assert len(selected)==len(ngpads);padbinding=[]
 for model in(base,final):
  for p in model['pads']:
   if L.norm(p['net']) not in(GROUND,NET):continue
   matches=[n for n in lookup[p['ref'],str(p['num'])] if n['net']==p['net'] and math.dist((p['x'],p['y']),n['at'])<=.000001 and set(p['layers'])==set(n['layers'])];assert matches,(p['uuid'],p['ref'],p['num']);n=matches[0];p['layers'][n['layers'][0]]=A.polys(n['poly'])
 for p in selected:padbinding.append({'UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'exact_FP_chunks_and_actual_native_pose_net_layers':True})
 oldzones={z['uuid']:z for z in base['zones'] if L.norm(z['net'])==GROUND};actualzones={z['uuid']:z for z in ng['zones'] if L.norm(z['net'])==GROUND};assert set(actualzones)==set(rr['selected_zone_UUIDs'])==set(oldzones);final['zones']=[z for z in final['zones'] if L.norm(z['net'])!=GROUND]
 for u,z in actualzones.items():final['zones'].append({'uuid':u,'net':z['net'],'fills':{l:A.polys(rs) for l,rs in z['fills'].items()},'clearance_mm':oldzones[u]['clearance_mm'],'priority':oldzones[u]['priority'],'native_actual_selected_refill':True})
 parsed={u:G.parse(u,ch,{}) for u,ch in new.items()};nt={t['uuid']:t for t in ng['tracks']};nv={v['uuid']:v for v in ng['vias']};exact=[]
 for u,q in parsed.items():
  n=nv[u] if q['kind']=='via' else nt[u];assert n['net']==identity.raw(q['net'])
  if q['kind']=='via':assert(n['at'],n['w'],n['drill'])==(q['at'],q['d'],q['drill']);assert set(fl[u])==set(LAYERS)
  else:assert(n['s'],n['e'],n['w'],n['layer'])==(q['a'],q['b'],q['w'],q['layer'])
  exact.append({'UUID':u,'kind':q['kind'],'exact_raw_net_native_IU_geometry':True,'actual_flash_layers':fl[u] if q['kind']=='via' else None})
 print('DI6_ACTUAL_FRESH_DRILLED_LOGIC_ROOT',flush=True);uf,groups,root,refs=root_refs(final);rk=Q.discrete_keys(root);sig=nv[SIG];ret=nv[RET];ann=Point(ret['at']).buffer(.25,quad_segs=128).difference(Point(ret['at']).buffer(.1,quad_segs=128));paired={'source_root':'J11001.2','signal_UUID':SIG,'signal_at_mm':sig['at'],'return_UUID':RET,'return_at_mm':ret['at'],'distance_mm':math.dist(sig['at'],ret['at']),'actual_signal_all6':fl[SIG],'actual_return_all6':fl[RET],'return_source_rooted':('via',RET) in rk,'finite_source_rooted_annular_interior_mm2':{l:refs[l].buffer(-.075).intersection(ann).area for l in('F.Cu','In3.Cu')}}
 allrefs={l:unary_union([q['shape'] for xs in groups for q in xs if q['kind']=='fill' and q['layer']==plane]) for l,plane in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')]};qualified=paired['return_source_rooted'] and .81<=paired['distance_mm']<=1 and all(a>=.004 for a in paired['finite_source_rooted_annular_interior_mm2'].values());reference=[];errors=[];gdir=HERE/'di6-actual-r16-reference-gaps';gdir.mkdir()
 for u,q in parsed.items():
  if q['kind']!='segment':continue
  assert q['net']==NET and q['layer'] in('F.Cu','In3.Cu');body=A.shape(q);gap=body.difference(refs[q['layer']]);maxrad=max((math.dist(p[:2],sig['at']) for p in vertices(gap)),default=0);own=not gap.is_empty and maxrad<=.525 and qualified;row={'UUID':u,'layer':q['layer'],'full_body_actual_source_reference_gap_mm2':gap.area,'full_body_any_GND_reference_gap_mm2_diagnostic_only':body.difference(allrefs[q['layer']]).area,'exact_own_transition_radius_mm':.525,'maximum_gap_vertex_radius_mm':maxrad,'qualified_own_transition':own,'radius_expansion_mm':0,'gap_after_qualified_exact_own_transition_mm2':0 if own else gap.area,'reference_pass':gap.area<=1e-9 or own}
  if not row['reference_pass']:p=gdir/(u+'.wkb');p.write_bytes(gap.wkb);row.update(gap_WKB_path=str(p),gap_WKB_sha256=C.sha(gap.wkb));errors.append(row)
  reference.append(row)
 # Exact discrete electrical joins use actual native annuli and full bodies.
 su,sg=Q.physical(final,NET)
 signalgroup=next(xs for xs in sg if any(q['kind']=='pad' and q['uuid']==SRC for q in xs));keys=Q.discrete_keys(signalgroup);joined=('via',SIG) in keys and ('via','0ff4e506-7bc1-48ad-91fd-aeb598e74c7a') in keys and any(q['kind']=='track' and q['uuid']==TARGET for q in signalgroup);sourcepad=next(p for p in final['pads'] if p['uuid']==SRC);first=parsed[prior['actual_source_pad_attachment']['new_first_segment_UUID']];last=parsed[prior['target_same_layer_attachment']['exact_new_last_segment_UUID']];sourceoverlap=A.shape(first).intersection(unary_union(L.poly(sourcepad['layers']['F.Cu']))).area;targettrack=next(t for t in final['tracks'] if t['uuid']==TARGET);targetoverlap=A.shape(last).intersection(A.shape({'kind':'segment',**targettrack})).area
 print('DI6_ACTUAL_PRIOR_CACHE_CONTACT_BASELINE',flush=True);ou,og,oroot,oldrefs=root_refs(base);mapping=collections.defaultdict(set)
 for i,xs in enumerate(groups):
  for k in Q.discrete_keys(xs):mapping[k].add(i)
 obligations=[];lostcontacts=[]
 for i,xs in enumerate(og):
  keys=Q.discrete_keys(xs);parts=set().union(*(mapping.get(k,{'MISSING'}) for k in keys)) if keys else set();row={'old_group':i,'surviving_discrete_keys':[list(k) for k in sorted(keys)],'actual_native_components':sorted(str(p) for p in parts)};obligations.append(row)
  if len(parts)>1 or 'MISSING' in parts:lostcontacts.append(row)
 neighbor,proof=RF.audit(base,oldrefs,refs,GROUND);saved=HERE/'di6-native-r16-actual-model.pkl';saved.write_bytes(pickle.dumps({'base':base,'actual':final,'groups':groups,'root':root,'root_reference':refs,'all_GND_reference':allrefs,'DI6_groups':sg},protocol=5));passed=not(errors or lostcontacts or neighbor) and qualified and joined and sourceoverlap>=.004 and targetoverlap>=.004
 report={'verdict':'ACTUAL_SELECTED_NATIVE_DI6_REFERENCE_CONTACT_RETURN_PASS' if passed else'ACTUAL_SELECTED_NATIVE_DI6_REFERENCE_OR_CONTACT_OPEN','scope':'Exact eedf+11DI6 items; all LOGIC_GND zones fresh only; R78/field/FG/C/AO proposals excluded','native_candidate_sha256':C.sha(nativeboard),'fresh_native_geometry_sha256':C.sha(ngraw),'fresh_native_flashes_sha256':C.sha(nfraw),'exact_source_FP_unowned_entities':True,'exact_new_native_discrete':exact,'actual_selected_pad_binding':padbinding,'actual_GND_pad_groups':sum(any(q['kind']=='pad' for q in xs) for xs in groups),'actual_source_rooted_pad_count':len({q['uuid'] for q in root if q['kind']=='pad'}),'actual_paired_return':paired,'actual_DI6_source_target_same_group':joined,'actual_source_pad_contact_mm2':sourceoverlap,'actual_retained_In3_target_contact_mm2':targetoverlap,'no_added_target_transition':True,'new_full_body_reference':reference,'reference_errors':errors,'prior_contact_baseline_provenance':'Exact eedf discrete/all actual flash masks; pinned original198b native source fill cache via R25 template. Not a second fresh eedf baseline; all differences remain explicit OPEN.','all_prior_GND_contact_obligations':obligations,'prior_GND_contact_losses':lostcontacts,'unchanged_neighbor_prior_reference_losses':neighbor,'independent_reference_delta_proof':proof,'saved_actual_model':str(saved),'saved_actual_model_sha256':C.sha(saved.read_bytes()),'final_R78_field_FG_C_AO_composition_allboard_native_DRC_current_r06_r07_SI':'OPEN','adopted':False,'native_jobs':0,'board_written':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started}
 for p,pin in A.READS.items():assert C.sha(Path(p).read_bytes())==pin,p
 out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'receipt':str(out),'verdict':report['verdict'],'reference_errors':len(errors),'contact_losses':len(lostcontacts),'neighbor_losses':len(neighbor),'joined':joined,'paired':paired,'sha256':C.sha(out.read_bytes())}),flush=True)
if __name__=='__main__':main()
