"""Nominate coupled exact wall restoration around a compliant ground return."""
import hashlib,json,pickle,re,sys,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import tri_route as T
OUT=H/'U10003-exact-clock-fault-coupled-ground-return-nomination-r187'
FG='/motherboard_motors/FIELD_GND';CLK='/motherboard_do/DOA_SCLK_FIELD';FLT='/motherboard_do/DOA_FLT_N_FIELD'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def polys(s):return[p for p in([s]if s.geom_type=='Polygon'else getattr(s,'geoms',[]))if p.geom_type=='Polygon'and not p.is_empty]
def main():
 assert not OUT.exists();OUT.mkdir()
 mp=H/'U10003-preserved-branch-exact-two-port-reference-construction-r176/model.pkl';assert sha(mp)=='c13b478b0cea7b09a510c221913d3a4d0774fcc74042605c17d69b35b37a9d20'
 g,h,b,z,full=pickle.loads(mp.read_bytes());old={t['uuid']:t for t in h['tracks']};ownvia='ef759308-e664-5253-b016-ff17794eac74';ownstub='18ddb0fe-6821-5fe9-b71b-dc25ea06443b';clkid='06f5b2a7-dc39-4a5d-9309-5badd13a2347'
 faultids={'c2ade3c7-665d-484b-8009-903f3cddfa9a','856349f3-8302-4a65-b6ea-7333fbc66a3e','7b3197eb-492a-47f3-a30a-6944f85704cb'}
 deletes={ownstub,clkid,*faultids};assert deletes<=old.keys();assert all(any(q['uuid']==u for q in g['tracks'])for u in faultids|{clkid})
 via={**next(v for v in h['vias']if v['uuid']==ownvia),'x':216.04,'y':143.32,'prospective_not_native':True};signal=next(v for v in h['vias']if v['uuid']=='7f2431b3-4dcd-5b17-88ce-8aae4c3d66d4');spacing=Point(via['x'],via['y']).distance(Point(signal['x'],signal['y']));assert .90<=spacing<=1.0
 roles={'9fe010df-73cf-5bfb-9f7a-bd227b701c3e','ee0efe05-1705-587c-ac86-49b1a7885ef9'}
 hard={**h,'tracks':[t for t in h['tracks']if t['uuid']not in deletes],'vias':[v for v in h['vias']if v['uuid']!=ownvia]+[via]};z=[q for q in z if q['uuid']not in roles]
 reserved=C.BASE/'recovery-composite/c06/alternate-r07';areas=json.loads((reserved/'reserved-r07.json').read_bytes())['keepouts'];exceptions={}
 for line in(reserved/'reserve/board.kicad_dru').read_text().splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n)for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 disk=Point(via['x'],via['y']).buffer(.25,quad_segs=256);errors=[];rec,trees=F.build({**hard,'zones':[]})
 for layer in h['copper_layers']:
  for j in trees[layer].query(disk.buffer(.627),predicate='intersects'):
   q=rec[layer][int(j)];net=C.norm(q['net'])
   if net==FG:continue
   req=(.15 if h['domains_normalized'][net]==h['domains_normalized'][FG]else.6)+.025+.000020;actual=disk.distance(q['shape'])
   if actual<req:errors.append({'layer':layer,'kind':q['kind'],'UUID':q['uuid'],'actual':actual,'required':req})
 # R186 exact no-violation nomination scene and frozen rule sources additionally
 # screen every physical drill/SMD/native no-via/reservation before construction.
 added=[];rows=[]
 pad=next(p for p in h['pads']if(p['ref'],p['num'])==('U10003','9'))
 endpoints=[(FG,'B.Cu',[pad['x'],pad['y']],[via['x'],via['y']]),(CLK,'F.Cu',old[clkid]['a'],old[clkid]['b'])]
 for net,layer,a,bb in endpoints:
  answer=None;records,trees=F.build({**hard,'tracks':hard['tracks']+added,'zones':[]})
  for margin in(2.,4.,8.):
   win=box(min(a[0],bb[0])-margin,min(a[1],bb[1])-margin,max(a[0],bb[0])+margin,max(a[1],bb[1])+margin);query=win.buffer(1.);cuts=[]
   for j in trees[layer].query(query,predicate='intersects'):
    q=records[layer][int(j)];other=C.norm(q['net'])
    if other==net:continue
    gap=(.15 if h['domains_normalized'][other]==h['domains_normalized'][net]else.6)+.025+.000020;cuts.append(N.bounded_buffer(q['shape'].intersection(query),gap+.1))
   for q in z:
    other=C.norm(q['net'])
    if q['layer']!=layer or other==net or not q['shape'].intersects(query):continue
    gap=max(float(q['clearance_mm']),.15 if h['domains_normalized'][other]==h['domains_normalized'][net]else.6)+.025+.000020;cuts.append(N.bounded_buffer(q['shape'].intersection(query),gap+.1))
   for p in hard['pads']:
    if C.norm(p['net'])==net:continue
    for sh in C.poly(p.get('hole')or[]):
     if sh.intersects(query):cuts.append(N.bounded_buffer(sh,.275+.1+.000020))
   for v in hard['vias']:
    if C.norm(v['net'])!=net and query.intersects(Point(v['x'],v['y'])):cuts.append(N.bounded_disk(v,v['drill']/2+.275+.1+.000020))
   for q in full['zones']:
    other=C.norm(q['net'])
    if q['uuid']in roles or other==net or h['domains_normalized'][other]==h['domains_normalized'][net]:continue
    for sh in C.poly(q['fills'].get(layer,[])):
     if sh.intersects(query):cuts.append(N.bounded_buffer(sh.intersection(query),max(.6,float(q['clearance_mm']))+.025+.1+.000020))
   for r in h['rule_areas']:
    if r.get('no_tracks')and layer in r['layers']:cuts.extend(N.bounded_buffer(s,.025+.1+.000020)for s in C.poly(r['outline'])if s.intersects(query))
   for r in areas:
    if layer in r['layers']and net not in exceptions.get(r['name'],set()):cuts.extend(N.bounded_buffer(s,.025+.1+.000020)for s in C.poly(r['outline'])if s.intersects(query))
   free=win.difference(unary_union(cuts));faces=[p for p in polys(free)if p.covers(Point(a))and p.covers(Point(bb))];rows.append({'net':net,'layer':layer,'margin_mm':margin,'common_faces':len(faces)})
   for face in faces:
    axis=LineString([a,bb])
    if not face.covers(axis):
     try:xy,_=T.route(face,tuple(a),tuple(bb));axis=LineString([[round(x,6),round(y,6)]for x,y in xy])
     except(ValueError,AssertionError):continue
    if not face.covers(axis):continue
    xy=[list(p)for p in axis.coords];answer={'net':net,'layer':layer,'points_mm':xy,'length_mm':axis.length}
    raw=pad['net']if net==FG else old[clkid]['net']
    added.extend({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'U10003-clock-fault-ground-r187/'+net+'/'+str(i))),'net':raw,'layer':layer,'a':aa,'b':cc,'w':.2,'prospective_not_native':True}for i,(aa,cc)in enumerate(zip(xy,xy[1:]))if aa!=cc);break
   if answer:break
  print('R187_ROUTE',net,json.dumps(answer),flush=True)
  if not answer:break
 losses=[]
 if len({C.norm(t['net'])for t in added})==2 and not errors:
  test={**full,'tracks':[t for t in full['tracks']if t['uuid']not in deletes]+added,'vias':hard['vias']}
  for net in(FLT,CLK):
   before=F.graph(full,net);after=F.graph(test,net);membership={k:i for i,xs in enumerate(after)for k in F.discrete_keys(xs)}
   for i,xs in enumerate(before):
    keys=F.discrete_keys(xs)-{('track',u)for u in deletes};missing=[list(k)for k in keys if k not in membership];dest={membership[k]for k in keys if k in membership}
    if missing or len(dest)>1:losses.append({'net':net,'old_group':i,'missing':missing,'after_groups':sorted(dest)})
  delta={'delete_original_tracks':[old[u]for u in sorted(faultids|{clkid})],'replace_only_unadopted_ground_barrel':via,'replace_only_unadopted_ground_stub':ownstub,'withdraw_only_unadopted_reference_roles':sorted(roles),'new_tracks':added}
  (OUT/'proposed-sparse-delta.pkl').write_bytes(pickle.dumps(delta,protocol=5))
 else:delta=None
 result={'verdict':'EXACT_COUPLED_WALL_NOMINATION_ALL_FRESH_GATES_OPEN'if delta and not losses else'FINITE_EXACT_COUPLED_WALL_NOMINATION_FAILED','model_sha256':sha(mp),'signal_return_distance_mm':spacing,'saved_operator_window_mm':[.90,1.0],'via_true_all6_Cu_errors':errors,'rows':rows,'retained_old_clock_fault_relationship_losses':losses,'delta_sha256':sha(OUT/'proposed-sparse-delta.pkl')if delta else None,'new_ground_full_source_annuli_reference_current_native_and_full_no_via_gates':'OPEN','original_Cu_deletions_never_applied_without_complete_contact_restoration':True,'native_jobs':0,'board_written':False,'adopted':False,'manufacturing_ready':False}
 (OUT/'receipt.json').write_text(json.dumps(result,indent=1,allow_nan=False)+'\n');print('R187_COMPLETE',result['verdict'],sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
