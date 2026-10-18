"""Exact three-owned-track DIC CS recovery, F/B/F and four ordinary vias.

Separate constructive nomination. No source/FP/project/rule/native mutation.
Every pre-existing relationship and reference remains an independent gate.
"""
import sys,json,pickle,time,math,copy,collections
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import complete_geometry_r2 as GE
import guarded_power_projection_r44 as Z
import construct_di6_direct_source_escape_r5 as K
import audit_c10036_r24_full_independent_r30 as Q
import audit_ao1_positive_operation_r4 as SERIAL
import tri_route as T
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
C=A.C;GND='/LOGIC_GND';NET='/motherboard_io_control/DIC_IOL1_CS_BUFFER';CS='/fpga_core/IOL1_L0_CS_N';RSP='/motherboard_io_control/DIC_IOL1_RSP_BUFFER';LAYERS=Q.LAYERS
def physical_centres(h,cur,net,layer,win):
 rec,trees=F.build({**h,'zones':[]});dom=h['domains_normalized'];obs=[]
 for i in trees[layer].query(win.buffer(1),predicate='intersects'):
  q=rec[layer][int(i)];n=L.norm(q['net'])
  if n!=net:obs.append(Z.bounded_buffer(q['shape'],(.15 if dom.get(n)==dom[net] else .6)+.030))
 for z in cur['zones']:
  n=L.norm(z['net'])
  if z['layer']==layer and n!=net and z['shape'].distance(win)<1:obs.append(Z.bounded_buffer(z['shape'],max(float(z.get('clearance_mm',.15)),.15 if dom.get(n)==dom[net] else .6)+.030))
 for z in cur['after']['zones']:
  n=L.norm(z['net'])
  if n==net or dom.get(n)==dom[net]:continue
  obs.extend(Z.bounded_buffer(q,max(float(z.get('clearance_mm',.15)),.6)+.030) for q in L.poly(z['fills'].get(layer,[])) if q.distance(win)<1)
 for v in h['vias']:
  if L.norm(v['net'])!=net and Point(v['x'],v['y']).distance(win)<1:obs.append(Z.bounded_disk(v,v['drill']/2+.280))
 for p in h['pads']:
  if L.norm(p['net'])!=net:obs.extend(Z.bounded_buffer(q,.280) for q in L.poly(p.get('hole') or []) if q.distance(win)<1)
 reserve,exempt=A.reservations()
 for q in h['rule_areas']:
  if layer in q['layers'] and q.get('no_tracks'):obs.extend(Z.bounded_buffer(p,.025) for p in L.poly(q['outline']) if p.distance(win)<1)
 for q in reserve['keepouts']:
  if layer in q['layers'] and net not in exempt.get(q['name'],set()):obs.extend(Z.bounded_buffer(p,.025) for p in L.poly(q['outline']) if p.distance(win)<1)
 return win.difference(unary_union(obs)).buffer(-.105,quad_segs=128)
def project(cur,h,nt,nv):
 fills=[];ledger=[];dom=h['domains_normalized']
 for old in cur['after']['zones']:
  z={**old,'fills':{}};net=L.norm(z['net']);local=float(z.get('clearance_mm',.15))
  for layer,records in old['fills'].items():
   shape=unary_union(L.poly(records));cuts=[];details=[]
   for t in nt:
    n=L.norm(t['net'])
    if layer!=t['layer'] or n==net:continue
    radius=t['w']/2+max(local,.15 if dom.get(n)==dom.get(net) else .6)+.025;cut=Z.bounded_buffer(LineString([t['a'],t['b']]),radius)
    if cut.intersects(shape):cuts.append(cut);details.append({'kind':'new_track','UUID':t['uuid'],'outward_radius_mm':radius})
   for v in nv:
    n=L.norm(v['net']);radius=v['drill']/2 if n==net else max(v['drill']/2+.275,v['d']/2+max(local,.15 if dom.get(n)==dom.get(net) else .6)+.025);cut=Z.bounded_disk(v,radius)
    if cut.intersects(shape):cuts.append(cut);details.append({'kind':'new_via','UUID':v['uuid'],'outward_radius_mm':radius})
   final=shape.difference(unary_union(cuts));z['fills'][layer]=GE.records(final)
   if cuts:ledger.append({'zone_UUID':old['uuid'],'layer':layer,'raw_net':old['net'],'local_clearance_mm':local,'before_WKB_sha256':C.sha(shape.wkb),'after_WKB_sha256':C.sha(final.wkb),'removed_mm2':shape.difference(final).area,'physical_piece_count':len(GE.records(final)),'cuts':details})
  fills.append(z)
 return {**cur['after'],'tracks':h['tracks'],'vias':h['vias'],'zones':fills},ledger
def refs_for(g):
 _,groups=Q.physical(g,GND);root=next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],str(q['pin']))==('J11001','2') for q in xs));refs={l:unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']==l]) for l in('In1.Cu','In4.Cu')};return root,refs,groups
def current_preservation(oldgroups,newgroups,removed):
 mapping=collections.defaultdict(set)
 for i,xs in enumerate(newgroups):
  for k in Q.discrete_keys(xs):mapping[k].add(i)
 obligations=[];lost=[]
 for i,xs in enumerate(oldgroups):
  keys=Q.discrete_keys(xs)-{('track',u) for u in removed};indices=set().union(*(mapping.get(k,{'MISSING'}) for k in keys)) if keys else set();q={'old_group':i,'surviving_discrete_keys':[list(k) for k in sorted(keys)],'new_groups':[str(x) for x in sorted(indices,key=str)]};obligations.append(q)
  if 'MISSING' in indices or len(indices)>1:lost.append(q)
 return obligations,lost
def main():
 started=time.monotonic();out=H/'DIC-three-track-coupled-r164.json';assert not out.exists();A.read(__file__);rp=H/'DIC-source-and-three-blocker-authority-r162.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='97d8792f596a22ab3a65527b3ab19a50cc4d9496034a0a41e17c077b29baeda1';basep=H/'di15-safe-root-r42-DI6-bind-r118.json';base=json.loads(A.read(basep));raw=A.read(base['model_path']);assert C.sha(raw)==r['current_model_sha256'];cur=pickle.loads(raw);h0=cur['h'];source=A.read(cur['binding']['exact_native_discrete_board_file']);assert C.sha(source)==r['source_parent_sha256'];identity=A.N.SourceNets(source);inventory=C.inventory(source);removed={q['UUID'] for q in r['exact_owned_three_blockers']};deletes={u:inventory[3][u] for u in removed};policy={L.norm(n):q for n,q in json.loads(A.read(A.S.CONTROLLED))['nets'].items()};assert all(policy.get(n) is None or policy[n].get('class') in(None,'NONE') for n in(NET,CS,RSP));beforegroups={n:Q.physical(cur['after'],n)[1] for n in(NET,CS,RSP)};win=box(121,86,137,102);target=[130.775665,90.219031];targetret=[130.919793,91.036421];attempts=[];selected=None
 for src in r['source_endpoint_options']:
  h=copy.deepcopy(h0);h['tracks']=[q for q in h['tracks'] if q['uuid'] not in removed];nv=[];nt=[];chunks={};points=[(NET,src['at_mm']),(NET,target),(GND,src['pair']['return']),(GND,targetret)];newpoints=[p for n,p in points];mutual=[{'a_mm':a,'b_mm':b,'distance_mm':math.dist(a,b)} for i,a in enumerate(newpoints) for b in newpoints[i+1:]];row={'source_nomination':src,'target_signal_at_mm':target,'target_return_at_mm':targetret,'new_mutual_pitch':mutual,'routes':[]};attempts.append(row)
  if any(q['distance_mm']<.815 for q in mutual):row['failure']='new_mutual_pitch';continue
  for net,pos in points:
   uid,ch=SERIAL.serial_via(identity,net,pos);assert uid not in inventory[3] and uid not in chunks;nv.append({'uuid':uid,'net':identity.raw(net),'x':pos[0],'y':pos[1],'d':.5,'drill':.2,'flashed':list(LAYERS)});chunks[uid]=ch
  h['vias']+=nv;pre,preledger=project(cur,h,[],nv);root,refs,groups=refs_for(pre);row['prior_LG_source_keys_lost_after_holes']=[list(k) for k in sorted(Q.discrete_keys(cur['root'])-Q.discrete_keys(root))];pairproof=[]
  for signal,ret in((nv[0],nv[2]),(nv[1],nv[3])):
   p=Point(ret['x'],ret['y']);ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));pairproof.append({'signal_UUID':signal['uuid'],'signal_at_mm':[signal['x'],signal['y']],'return_UUID':ret['uuid'],'return_at_mm':[ret['x'],ret['y']],'distance_mm':math.dist([signal['x'],signal['y']],[ret['x'],ret['y']]),'actual_source_annular_contacts_mm2':{l:ann.intersection(ref).area for l,ref in refs.items()},'signal_exact_own_aperture_radius_mm':.525,'radius_expansion_mm':0,'native_all6_flash_and_refill':'OPEN'})
  row['paired_returns_after_all_four_holes']=pairproof
  if row['prior_LG_source_keys_lost_after_holes'] or any(q['distance_mm']>1 or any(a<.004 for a in q['actual_source_annular_contacts_mm2'].values()) for q in pairproof):row['failure']='source_or_pair_after_holes';continue
  # First reroute the exact two blocker nets; then add DIC F/B/F against them.
  requested=[(CS,'F.Cu',[131.449999,90.35],[130.449999,91.35]),(RSP,'B.Cu',[133.049999,93.35],[129.15,89.45]),(NET,'F.Cu',src['F_attachment'],src['at_mm']),(NET,'B.Cu',src['at_mm'],target)]
  targetgroup=next(xs for xs in beforegroups[NET] if any(q['kind']=='pad' and q['uuid'] in r['actual_current_pad_UUIDs'] and q['shape'].distance(Point(target))<4 for q in xs));targetmetal=unary_union([q['shape'] for q in targetgroup if q['layer']=='F.Cu']);targetattach=nearest_points(targetmetal.buffer(-.05,quad_segs=128),Point(target))[0];requested.append((NET,'F.Cu',target,list(targetattach.coords)[0]))
  for net,layer,a,b in requested:
   plane='In1.Cu' if layer=='F.Cu' else 'In4.Cu';own=unary_union([Z.bounded_disk(v,.525) for v in nv if L.norm(v['net'])==net]);free=physical_centres(h,cur,net,layer,win).intersection(refs[plane].union(own).intersection(win.buffer(1)).buffer(-.105,quad_segs=128));parts=[q for q in K.pieces(free) if q.covers(Point(a)) and q.covers(Point(b))];q={'raw_net':identity.raw(net),'layer':layer,'actual_source_reference_layer':plane,'requested_endpoints_mm':[a,b],'continuous_components':len(parts),'a_physical_and_reference_covered':free.covers(Point(a)),'b_physical_and_reference_covered':free.covers(Point(b))};row['routes'].append(q);print(json.dumps({'phase':'DIC_exact_coupled_route','net':net,'layer':layer,'continuous_components':len(parts),'endpoints_covered':[q['a_physical_and_reference_covered'],q['b_physical_and_reference_covered']]}),flush=True)
   if not parts:row['failure']='physical_or_reference_route_'+net;break
   path,search=T.route(parts[0],tuple(a),tuple(b));path=[[round(x,6),round(y,6)] for x,y in path];body=unary_union([A.shape({'kind':'segment','a':pa,'b':pb,'w':.2}) for pa,pb in zip(path,path[1:])]);gap=body.difference(refs[plane].union(own));q.update({'points_mm':path,'length_mm':LineString(path).length,'width_mm':.2,'actual_full_body_gap_mm2':gap.area,'exact_used_own_aperture_UUIDs':[v['uuid'] for v in nv if L.norm(v['net'])==net],'search':search})
   if not gap.is_empty:row['failure']='strict_body_reference';break
   for pa,pb in zip(path,path[1:]):
    uid,ch=identity.serial_segment(net,layer,pa,pb,.2);assert uid not in inventory[3] and uid not in chunks;chunks[uid]=ch;t={'uuid':uid,'net':identity.raw(net),'layer':layer,'a':pa,'b':pb,'w':.2};nt.append(t);h['tracks'].append(t)
  if row.get('failure'):continue
  identity.assert_chunks(chunks);after,ledger=project(cur,h,nt,nv);root,finalrefs,groups=refs_for(after);lostroot=sorted(Q.discrete_keys(cur['root'])-Q.discrete_keys(root));contacts={};losses=[]
  for n in(NET,CS,RSP):
   obligations,lost=current_preservation(beforegroups[n],Q.physical(after,n)[1],removed);contacts[n]=obligations;losses.extend({'net':n,**q} for q in lost)
  wanted=set(r['actual_current_pad_UUIDs']);joined=[xs for xs in Q.physical(after,NET)[1] if wanted<= {q['uuid'] for q in xs if q['kind']=='pad'}];finalbody=[]
  for q in row['routes']:
   net=L.norm(q['raw_net']);own=unary_union([Z.bounded_disk(v,.525) for v in nv if L.norm(v['net'])==net]);body=unary_union([A.shape({'kind':'segment','a':a,'b':b,'w':.2}) for a,b in zip(q['points_mm'],q['points_mm'][1:])]);finalbody.append({'raw_net':q['raw_net'],'layer':q['layer'],'gap_mm2':body.difference(finalrefs[q['actual_source_reference_layer']].union(own)).area})
  row.update({'final_LG_source_keys_lost':[list(k) for k in lostroot],'surviving_contact_losses':losses,'exact_r06_target_pad_relationship_joined':bool(joined),'final_new_full_body_reference':finalbody})
  if lostroot or losses or not joined or any(q['gap_mm2']>0 for q in finalbody):continue
  model=H/'DIC-three-track-coupled-r164-model.pkl';assert not model.exists();model.write_bytes(pickle.dumps({'current':cur,'h':h,'after':after,'new_tracks':nt,'new_vias':nv,'removed_UUIDs':sorted(removed),'exact_deleted_chunks':deletes,'exact_new_chunks':chunks,'refs':finalrefs,'root':root,'groups':groups,'source_relationship_pad_UUIDs':sorted(wanted),'paired_returns':pairproof,'all_current_contact_obligations':contacts},protocol=5));selected={**row,'model_file':str(model),'model_sha256':C.sha(model.read_bytes()),'exact_deleted_chunks':{u:c.decode() for u,c in deletes.items()},'exact_new_chunks':{u:c.decode() for u,c in chunks.items()},'projection_ledger':ledger};break
 report={'verdict':'DIC_EXACT_THREE_TRACK_COUPLED_CONSTRUCTION_POSITIVE_INDEPENDENT_OPEN' if selected else'DIC_EXACT_THREE_TRACK_COUPLED_CONSTRUCTION_INCOMPLETE','source_parent_sha256':C.sha(source),'current_model_sha256':r['current_model_sha256'],'R162_authority_sha256':C.sha(A.read(rp)),'removed_exact_source_UUIDs':sorted(removed),'attempts':attempts,'selected':selected,'signal_layer_chain':['F.Cu','B.Cu','F.Cu'],'signal_layer_segments':3,'new_ordinary_all6_vias_per_attempt':4,'source_FP_project_rules_zone_outlines_changed':0,'full_current_r06_r07_all_net_contacts_reference_native_clearance_SI_signed_power_current':'OPEN','independent_every_SMD_and_hole_aperture_site_body_audit':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'attempts':len(attempts),'selected':selected}),flush=True)
if __name__=='__main__':main()
