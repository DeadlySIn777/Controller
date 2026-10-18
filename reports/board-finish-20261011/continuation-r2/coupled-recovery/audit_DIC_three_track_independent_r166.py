"""Independent exact-chunk DIC audit and accepted canonical IO3 mutual screen.

Rebuilds four all6 ordinary vias, every native-rule/body/hole contact, full
affected groups and actual source refs. No producer projection/route reused.
"""
import sys,json,pickle,math,time,copy,collections,re
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import audit_c10036_r24_full_independent_r30 as Q
import guarded_power_projection_r44 as Z
import complete_geometry_r2 as GE
import physical_reference_losses_r2 as RF
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
C=A.C;NET='/motherboard_io_control/DIC_IOL1_CS_BUFFER';CS='/fpga_core/IOL1_L0_CS_N';RSP='/motherboard_io_control/DIC_IOL1_RSP_BUFFER';GND='/LOGIC_GND';LAYERS=Q.LAYERS
def layerkeys(rows):return {(q['kind'],q['uuid'],q['layer']) for q in rows if q['kind']!='fill'}
def source_ref(g):
 uf,groups=Q.physical(g,GND);root=next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],str(q['pin']))==('J11001','2') for q in xs));return uf,groups,root,{outer:unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']==plane]) for outer,plane in(('F.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu'))}
def main():
 started=time.monotonic();out=H/'DIC-three-track-independent-r166.json';assert not out.exists();rp=H/'DIC-three-track-coupled-r164.json';recipe=json.loads(A.read(rp));assert C.sha(A.read(rp))=='cdb152ede9fbb637191668297405e07af5be24f7e984dc23687dd37d5209ca4b';sel=recipe['selected'];raw=A.read(sel['model_file']);assert C.sha(raw)==sel['model_sha256']=='7e11621fb23ee9fdabdbed66ca3edf51841848d231c50f02370305e5fc5e16b5';producer=pickle.loads(raw);cur=producer['current'];before=cur['after'];h0=cur['h'];source=A.read(cur['binding']['exact_native_discrete_board_file']);assert C.sha(source)==recipe['source_parent_sha256'];identity=A.N.SourceNets(source);inv=C.inventory(source);A.read(__file__)
 for module in(A,L,F,Q,Z,GE,RF):A.read(module.__file__)
 removed=set(sel['exact_deleted_chunks']);assert removed==set(recipe['removed_exact_source_UUIDs']);assert len(removed)==3
 for uid,ch in sel['exact_deleted_chunks'].items():assert inv[3][uid]==ch.encode() and source.count(ch.encode())==1
 added={uid:ch.encode() for uid,ch in sel['exact_new_chunks'].items()};identity.assert_chunks(added);assert not set(added)&set(inv[3]);parsed={uid:A.G.parse(uid,ch,{}) for uid,ch in added.items()};nt=[];nv=[]
 for uid,q in parsed.items():
  if q['kind']=='segment':assert q['net'] in(NET,CS,RSP) and q['layer'] in('F.Cu','B.Cu') and q['w']==.2;nt.append({'uuid':uid,'net':identity.raw(q['net']),'layer':q['layer'],'a':q['a'],'b':q['b'],'w':q['w']})
  else:
   assert q['kind']=='via' and q['net'] in(NET,GND) and(q['d'],q['drill'])==(.5,.2);assert not any(tok in added[uid] for tok in(b'remove_unused_layers',b'keep_end_layers',b'zone_connection'));nv.append({'uuid':uid,'net':identity.raw(q['net']),'x':q['at'][0],'y':q['at'][1],'d':q['d'],'drill':q['drill'],'flashed':list(LAYERS)})
 assert len(nt)==15 and len(nv)==4;oldids={q['uuid'] for k in('tracks','vias') for q in h0[k]};assert not set(added)&oldids;h=copy.deepcopy(h0);h['tracks']=[q for q in h0['tracks'] if q['uuid'] not in removed]+nt;h['vias']=h0['vias']+nv;assert h['pads']==h0['pads'] and h['rule_areas']==h0['rule_areas'];assert {q['uuid']:q for q in h['tracks']}=={q['uuid']:q for q in producer['h']['tracks']} and {q['uuid']:q for q in h['vias']}=={q['uuid']:q for q in producer['h']['vias']};assert all(v.get('flashed') is not None for v in h['vias']);policies={L.norm(n):p for n,p in json.loads(A.read(A.S.CONTROLLED))['nets'].items()};assert all(policies.get(n,{}).get('class') in(None,'NONE') for n in(NET,CS,RSP));dom=h['domains_normalized'];gap=lambda a,b:.15 if dom.get(L.norm(a))==dom.get(L.norm(b)) else .6
 # Native local clearance is read from each exact old chunk. Prospective
 # canonical planes retain their explicitly bound recipe parameters.
 zone_local={}
 for z in before['zones']:
  assert 'clearance_mm' in z;local=float(z['clearance_mm'])
  if z['uuid'] in inv[3]:
   match=re.search(rb'\(connect_pads(?:\s+[^()\s]+)?\s*\(clearance\s+([0-9.]+)\)',inv[3][z['uuid']]);assert match and float(match.group(1))==local
  zone_local[z['uuid']]=local
 afterzones=[];cutledger=[];affected={NET,CS,RSP,GND}
 for oldz in before['zones']:
  z={**oldz,'fills':{}};net=L.norm(z['net']);local=zone_local[z['uuid']]
  for layer,records in oldz['fills'].items():
   original=unary_union(L.poly(records));cuts=[];details=[]
   for t in nt:
    if t['layer']!=layer or L.norm(t['net'])==net:continue
    radius=t['w']/2+max(local,gap(t['net'],net))+.025;cut=Z.bounded_buffer(LineString([t['a'],t['b']]),radius)
    if cut.intersects(original):cuts.append(cut);details.append({'kind':'track','UUID':t['uuid'],'outward_radius_mm':radius,'exact_WKB_sha256':C.sha(cut.wkb)})
   for v in nv:
    radius=v['drill']/2 if L.norm(v['net'])==net else max(v['drill']/2+.275,v['d']/2+max(local,gap(v['net'],net))+.025);cut=Z.bounded_disk(v,radius)
    if cut.intersects(original):cuts.append(cut);details.append({'kind':'via','UUID':v['uuid'],'outward_radius_mm':radius,'exact_WKB_sha256':C.sha(cut.wkb)})
   final=original.difference(unary_union(cuts));z['fills'][layer]=GE.records(final)
   if cuts:affected.add(net);cutledger.append({'zone_UUID':z['uuid'],'raw_net':z['net'],'layer':layer,'exact_local_mm':local,'before_WKB_sha256':C.sha(original.wkb),'after_WKB_sha256':C.sha(final.wkb),'removed_mm2':original.difference(final).area,'physical_piece_count':len(GE.records(final)),'cuts':details})
  afterzones.append(z)
 after={**before,'tracks':h['tracks'],'vias':h['vias'],'zones':afterzones};assert {z['uuid']:z['fills'] for z in afterzones}=={z['uuid']:z['fills'] for z in producer['after']['zones']}
 print('DIC_R166_SERIALIZED_OPERATION_AND_INDEPENDENT_PROJECTION_BOUND',flush=True);records,trees=F.build({**h,'zones':[]});errors=[];clear=[];smd=[(p['uuid'],p['ref'],p['num'],q) for p in h['pads'] if p['smd'] for l,rs in p['layers'].items() if l in('F.Cu','B.Cu') for q in L.poly(rs)];st=STRtree([q[3] for q in smd]);holes=[(v['uuid'],L.norm(v['net']),Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)) for v in h['vias']]+[(p['uuid'],L.norm(p['net']),q) for p in h['pads'] for q in L.poly(p.get('hole') or [])];ht=STRtree([q[2] for q in holes]);aperture=[];reserve,exempt=A.reservations();outline=unary_union(L.poly(h['outline'])).buffer(-.525)
 for item in nv+nt:
  isvia='d'in item;net=L.norm(item['net']);body=Point(item['x'],item['y']).buffer(item['d']/2,quad_segs=128) if isvia else A.shape({'kind':'segment',**item});layers=LAYERS if isvia else[item['layer']];mins=[]
  for layer in layers:
   near=[]
   for i in trees[layer].query(body.buffer(.7),predicate='intersects'):
    q=records[layer][int(i)]
    if L.norm(q['net'])==net:continue
    distance=body.distance(q['shape']);required=gap(net,q['net'])+.025;near.append((distance,q['uuid'],q['net'],required))
    if distance<required-1e-8:errors.append({'kind':'all_layer_foreign_Cu','UUID':item['uuid'],'layer':layer,'other_UUID':q['uuid'],'raw_net':q['net'],'distance_mm':distance,'required_mm':required})
   for z in cur['zones']:
    if z['layer']!=layer or L.norm(z['net'])==net:continue
    distance=body.distance(z['shape']);required=max(gap(net,z['net']),float(z['clearance_mm']))+.025
    if distance<required-1e-8:errors.append({'kind':'held_positive_zone','UUID':item['uuid'],'layer':layer,'other_UUID':z['uuid'],'distance_mm':distance,'required_mm':required})
   mins.append({'layer':layer,'nearest_foreign_Cu':min(near) if near else None})
  if not outline.covers(body):errors.append({'kind':'board_edge','UUID':item['uuid']})
  for q in h['rule_areas']:
   if set(layers)&set(q['layers']) and q.get('no_vias' if isvia else'no_tracks') and any(body.distance(p)<.025 for p in L.poly(q['outline'])):errors.append({'kind':'native_rule_area','UUID':item['uuid'],'rule_UUID':q['uuid']})
  for q in reserve['keepouts']:
   if net not in exempt.get(q['name'],set()) and set(layers)&set(q['layers']) and any(body.distance(p)<.025 for p in L.poly(q['outline'])):errors.append({'kind':'frozen_reservation','UUID':item['uuid'],'rule_name':q['name']})
  if isvia:
   point=Point(item['x'],item['y']);sm=smd[int(st.nearest(point))];smdgap=point.distance(sm[3])-item['drill']/2-.005;nearholes=[(point.distance(q[2])-item['drill']/2-.005,q[0]) for q in holes if q[0]!=item['uuid']];holegap=min(nearholes);pitch=min((point.distance(Point(v['x'],v['y'])),v['uuid']) for v in h['vias'] if v['uuid']!=item['uuid']);q={'UUID':item['uuid'],'at_mm':[item['x'],item['y']],'guarded_SMD_hole_edge_mm':smdgap,'nearest_SMD':[sm[0],sm[1],sm[2]],'every_guarded_drill_gap':holegap,'ordinary_pitch':pitch,'required_SMD_drill_edge_mm':.275,'required_pitch_mm':.815};aperture.append(q)
   if smdgap<.275 or holegap[0]<.275 or pitch[0]<.815:errors.append({'kind':'ordinary_SMD_every_hole_pitch',**q})
  else:
   for i in ht.query(body.buffer(.285),predicate='intersects'):
    q=holes[int(i)]
    if q[1]!=net and body.distance(q[2])-.005<.275:errors.append({'kind':'track_foreign_physical_hole','UUID':item['uuid'],'other_UUID':q[0],'guarded_gap_mm':body.distance(q[2])-.005,'required_mm':.275})
  clear.append({'UUID':item['uuid'],'all_used_layers':layers,'clearance':mins})
 # Current accepted canonical IO3 groups: screen physical AND intended roles.
 io=H.parent/'sbc-power/IO3-minimal-validated-integration-packet-r190/receipt.json';ior=json.loads(A.read(io));assert C.sha(A.read(io))=='4e6544cff59e0ebd16d8bd5b6ae7e9b43df0b74320c481d7febdeb141b53d63a';iob=A.read(ior['replacement_objects_file']);assert C.sha(iob)=='0e11b1715f08612c6c385e113ff1ae8344bc56727c2367b2a2dbfd2d16300610';ioobjects=pickle.loads(iob);ioitems=ioobjects.values() if isinstance(ioobjects,dict) else ioobjects;ioitems=list(ioitems);mutual=[];mutualerrors=[]
 for z in ioitems:
  if not isinstance(z,dict) or 'shape' not in z:continue
  for item in nv+nt:
   isvia='d'in item
   if not isvia and item['layer']!=z['layer']:continue
   if L.norm(item['net'])==L.norm(z['net']):continue
   body=Point(item['x'],item['y']).buffer(item['d']/2,quad_segs=128) if isvia else A.shape({'kind':'segment',**item});req=max(float(z['clearance_mm']),gap(item['net'],z['net']))+.025
   for role in('shape','zone_outline_shape'):
    if role not in z:continue
    distance=body.distance(z[role]);q={'new_UUID':item['uuid'],'IO3_group_UUID':z['uuid'],'IO3_layer':z['layer'],'role':role,'distance_mm':distance,'guarded_required_mm':req,'exact_IO3_role_WKB_sha256':C.sha(z[role].wkb)};mutual.append(q)
    if distance<req-1e-8:mutualerrors.append(q)
 cp=H/'DIC-three-track-independent-r166-physical-checkpoint.pkl';assert not cp.exists();cp.write_bytes(pickle.dumps({'before':before,'after':after,'h':h,'nv':nv,'nt':nt,'cur':cur,'new':added,'removed':removed,'clearance_errors':errors,'ordinary_aperture':aperture,'IO3_mutual_errors':mutualerrors},protocol=5));print(json.dumps({'phase':'DIC_R166_full_geometry_checkpoint','SHA256':C.sha(cp.read_bytes()),'Cu_errors':len(errors),'IO3_mutual_errors':len(mutualerrors),'aperture':aperture}),flush=True)
 ou,oldgroups,oldroot,oldrefs=source_ref(before);nu,newgroups,newroot,newrefs=source_ref(after);lostsource=sorted(layerkeys(oldroot)-layerkeys(newroot));contacts=[];lostcontacts=[];localcontacts=[];graphs={GND:(nu,newgroups)}
 for net in sorted(affected):
  print('DIC_R166_COMPLETE_CONTACT_NET '+net,flush=True)
  if net==GND:prior=oldgroups;groups=newgroups;uf=nu
  else:_,prior=Q.physical(before,net);uf,groups=Q.physical(after,net)
  graphs[net]=(uf,groups);mapping=collections.defaultdict(set)
  for i,xs in enumerate(groups):
   for key in layerkeys(xs):mapping[key].add(i)
  for i,xs in enumerate(prior):
   keys=layerkeys(xs)-{(k,uid,l) for k,uid,l in layerkeys(xs) if k=='track' and uid in removed};indices=set().union(*(mapping.get(k,{'MISSING'}) for k in keys)) if keys else set();q={'raw_normalized_net':net,'original_group':i,'all_surviving_pad_track_via_layer_keys':[list(k) for k in sorted(keys)],'candidate_groups':[str(x) for x in sorted(indices,key=str)]};contacts.append(q)
   if len(indices)>1 or 'MISSING'in indices:lostcontacts.append(q)
  oldfill=[q for xs in prior for q in xs if q['kind']=='fill'];oldmetal=[q for xs in prior for q in xs if q['kind']!='fill' and q['uuid'] not in removed];finalfill=collections.defaultdict(list)
  for xs in groups:
   for q in xs:
    if q['kind']=='fill':finalfill[q['uuid'],q['layer']].append(q['shape'])
  changed={(q['zone_UUID'],q['layer']) for q in cutledger if L.norm(q['raw_net'])==net}
  for layer in LAYERS:
   metal=[q for q in oldmetal if q['layer']==layer];tree=STRtree([q['shape'] for q in metal])
   for fill in oldfill:
    if fill['layer']!=layer or(fill['uuid'],layer) not in changed:continue
    newpieces=finalfill[fill['uuid'],layer]
    for j in tree.query(fill['shape'].buffer(.000002),predicate='intersects'):
     q=metal[int(j)]
     if q['shape'].distance(fill['shape'])>.000002:continue
     hits=[i for i,shape in enumerate(newpieces) if shape.distance(q['shape'])<=.000002];localcontacts.append({'net':net,'zone_UUID':fill['uuid'],'layer':layer,'old_fill_piece_WKB_sha256':C.sha(fill['shape'].wkb),'old_contact_item':[q['kind'],q['uuid'],layer],'candidate_same_zone_physical_piece_contacts':hits,'retained_electrical_group_components':[str(x) for x in sorted(mapping.get((q['kind'],q['uuid'],layer),{'MISSING'}),key=str)],'direct_contact_retained':bool(hits)})
 # Actual native pad-identity guards on every rerouted signal net, all3baselines.
 counts=collections.Counter();padmap={}
 for p in before['pads']:
  label=p['ref']+'.'+str(p['num']);idx=counts[label];counts[label]+=1;padmap[label+'#'+str(idx)]=p['uuid']
 nativechecks=[];padloss=[]
 for label,path in(('current198b',A.G.REPORT/'measure/r07-four-fag-shared/partitions.json'),('r06',A.P.R.R06_PART),('r07',A.P.R.R07_PART)):
  native={L.norm(n):xs for n,xs in json.loads(A.read(path))['nets'].items()}
  for net in(NET,CS,RSP):
   for rel in native[net]:
    ids=[padmap[x] for x in rel];components={graphs[net][0].find(('pad',uid)) for uid in ids};q={'baseline':label,'net':net,'exact_native_pad_labels':rel,'actual_pad_UUIDs':ids,'candidate_components':len(components)};nativechecks.append(q)
    if len(components)>1:padloss.append(q)
 pairproof=[];own=[];nvby={q['uuid']:q for q in nv}
 for q in sel['paired_returns_after_all_four_holes']:
  sig=nvby[q['signal_UUID']];ret=nvby[q['return_UUID']];p=Point(ret['x'],ret['y']);ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));areas={plane:ann.intersection(newrefs[outer].buffer(-.075,quad_segs=128)).area for plane,outer in(('In1.Cu','F.Cu'),('In4.Cu','B.Cu'))};distance=math.dist([sig['x'],sig['y']],[ret['x'],ret['y']]);proof={'signal_UUID':sig['uuid'],'return_UUID':ret['uuid'],'distance_mm':distance,'actual_J11001_2_return_rooted':('via',ret['uuid'],'In1.Cu') in layerkeys(newroot) and('via',ret['uuid'],'In4.Cu') in layerkeys(newroot),'finite_actual_annular_interior_mm2':areas,'unchanged_exact_own_radius_mm':.525,'radius_expansion_mm':0,'new_actual_native_all6_annuli_gate':'OPEN'};pairproof.append(proof)
  if proof['actual_J11001_2_return_rooted'] and .815<=distance<=1 and all(a>.004 for a in areas.values()):own.append((sig['uuid'],Z.bounded_disk(sig,.525)))
 ownshape=unary_union([shape for uid,shape in own]);reference=[];referrors=[]
 for t in nt:
  body=A.shape({'kind':'segment',**t});allowed=newrefs[t['layer']].union(ownshape if L.norm(t['net'])==NET else Point());missing=body.difference(allowed);q={'UUID':t['uuid'],'raw_net':t['net'],'signal_layer':t['layer'],'actual_source_reference_layer':'In1.Cu' if t['layer']=='F.Cu' else'In4.Cu','full_body_reference_gap_mm2':missing.area,'exact_same_net_qualified_own_aperture_UUIDs':[uid for uid,shape in own] if L.norm(t['net'])==NET else[],'radius_expansion_mm':0};reference.append(q)
  if not missing.is_empty:referrors.append(q)
 neighbors,neighborproof=RF.audit(before,oldrefs,newrefs,GND,removed=removed);passed=not(errors or lostsource or lostcontacts or padloss or referrors or neighbors or mutualerrors) and len(own)==2;result={'verdict':'DIC_INDEPENDENT_EXACT_FROZEN_HOST_GATES_PASS_NATIVE_LATEST_COMPOSITION_OPEN' if passed else'DIC_INDEPENDENT_EXACT_FROZEN_HOST_GATES_INCOMPLETE','R164_receipt_sha256':C.sha(A.read(rp)),'source_parent_sha256':C.sha(source),'current_model_sha256':recipe['current_model_sha256'],'exact3_deleted_chunks_sha256':C.sha(b''.join(sel['exact_deleted_chunks'][uid].encode() for uid in sorted(removed))),'exact19_added_chunks_sha256':C.sha(b''.join(added[uid] for uid in sorted(added))),'all_untouched_current_Cu_pad_rule_metadata_exact':True,'ordinary_all6_geometry_and_hard_predicates':clear,'clearance_errors':errors,'ordinary_every_SMD_drill_pitch':aperture,'independent_exact_projected_zone_cut_ledger':cutledger,'all_affected_net_layer_contact_obligations':contacts,'lost_contacts':lostcontacts,'complete_changed_fill_old_contact_ledger':localcontacts,'direct_same_zone_contacts_not_retained':[q for q in localcontacts if not q['direct_contact_retained']],'actual_prior_J1_source_layer_keys_lost':[list(k) for k in lostsource],'current_r06_r07_actual_pad_guards':nativechecks,'pad_losses':padloss,'actual_source_paired_returns':pairproof,'all_new_full_body_reference':reference,'reference_errors':referrors,'unchanged_neighbour_reference_losses':neighbors,'exact_reference_delta_audit':neighborproof,'accepted_IO3_R190_receipt_sha256':C.sha(A.read(io)),'accepted_IO3_exact_group_physical_and_intended_mutual_screen':mutual,'IO3_mutual_errors':mutualerrors,'physical_checkpoint_file':str(cp),'physical_checkpoint_sha256':C.sha(cp.read_bytes()),'latest_R183_ROOT55_U10017_R195_all_power_source_current_and_combined_DIC_native_r06_r07_DRC_SI':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(result,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':result['verdict'],'geometry':len(errors),'contacts':len(lostcontacts),'source':len(lostsource),'pads':len(padloss),'new_reference':len(referrors),'old_reference':len(neighbors),'IO3_mutual':len(mutualerrors),'pairs':pairproof}),flush=True)
if __name__=='__main__':main()
