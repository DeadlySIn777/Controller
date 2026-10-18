"""Ground-pad B routes to actual existing source barrels; no fault rip-up."""
import hashlib,json,pickle,re,sys,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import tri_route as T
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
OUT=H/'U10003-existing-source-ground-B-routes-no-fault-ripup-r185'
NET='/motherboard_motors/FIELD_GND';L='B.Cu'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def polys(s):return[p for p in([s]if s.geom_type=='Polygon'else getattr(s,'geoms',[]))if p.geom_type=='Polygon'and not p.is_empty]
def main():
 assert not OUT.exists();OUT.mkdir()
 mp=H/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262/model.pkl'
 assert sha(mp)=='64a1f6e1597c9d757b187c3b6db85d79685ee376399bdd4738f915b87b1a0144'
 g,h,b,z,full=pickle.loads(mp.read_bytes());pad=next(p for p in h['pads']if(p['ref'],p['num'])==('U10003','9'));assert C.norm(pad['net'])==NET
 start=Point(pad['x'],pad['y']);records,trees=F.build({**h,'zones':[]})
 _,groups=K.physical(full,NET,K.hole_context(full));root=K.root(groups,'J11003','2')
 ref={l:unary_union([q['shape']for q in root if q['layer']==l and q['kind']=='fill'])for l in('In1.Cu','In4.Cu')}
 reserved=C.BASE/'recovery-composite/c06/alternate-r07';areas=json.loads((reserved/'reserved-r07.json').read_bytes())['keepouts'];exceptions={}
 for line in(reserved/'reserve/board.kicad_dru').read_text().splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n)for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 rows=[];nominees=[]
 for via in sorted([v for v in h['vias']if C.norm(v['net'])==NET and Point(v['x'],v['y']).distance(start)<12],key=lambda v:Point(v['x'],v['y']).distance(start)):
  end=Point(via['x'],via['y']);ann=end.buffer(via['d']/2,quad_segs=256).difference(end.buffer(via['drill']/2,quad_segs=256))
  support={l:ann.intersection(s).area if l in via['flashed']else 0 for l,s in ref.items()}
  if not any(support.values()):rows.append({'UUID':via['uuid'],'no_actual_before_source_plane_annulus':True});continue
  for margin in(2.,4.,8.):
   win=box(min(start.x,end.x)-margin,min(start.y,end.y)-margin,max(start.x,end.x)+margin,max(start.y,end.y)+margin);query=win.buffer(1.);cuts=[]
   for j in trees[L].query(query,predicate='intersects'):
    q=records[L][int(j)];other=C.norm(q['net'])
    if other==NET:continue
    gap=(.15 if h['domains_normalized'][other]==h['domains_normalized'][NET]else.6)+.025+.000020;cuts.append(N.bounded_buffer(q['shape'].intersection(query),gap+.1))
   for q in z:
    other=C.norm(q['net'])
    if q['layer']!=L or other==NET or not q['shape'].intersects(query):continue
    gap=max(float(q['clearance_mm']),.15 if h['domains_normalized'][other]==h['domains_normalized'][NET]else.6)+.025+.000020;cuts.append(N.bounded_buffer(q['shape'].intersection(query),gap+.1))
   for p in h['pads']:
    if C.norm(p['net'])==NET:continue
    for sh in C.poly(p.get('hole')or[]):
     if sh.intersects(query):cuts.append(N.bounded_buffer(sh,.275+.1+.000020))
   for v in h['vias']:
    if C.norm(v['net'])!=NET and query.intersects(Point(v['x'],v['y'])):cuts.append(N.bounded_disk(v,v['drill']/2+.275+.1+.000020))
   for q in full['zones']:
    other=C.norm(q['net'])
    if other==NET or h['domains_normalized'][other]==h['domains_normalized'][NET]:continue
    for sh in C.poly(q['fills'].get(L,[])):
     if sh.intersects(query):cuts.append(N.bounded_buffer(sh.intersection(query),max(.6,float(q['clearance_mm']))+.025+.1+.000020))
   for r in h['rule_areas']:
    if r.get('no_tracks')and L in r['layers']:cuts.extend(N.bounded_buffer(s,.025+.1+.000020)for s in C.poly(r['outline'])if s.intersects(query))
   for r in areas:
    if L in r['layers']and NET not in exceptions.get(r['name'],set()):cuts.extend(N.bounded_buffer(s,.025+.1+.000020)for s in C.poly(r['outline'])if s.intersects(query))
   free=win.difference(unary_union(cuts));faces=[p for p in polys(free)if p.covers(start)and p.covers(end)]
   row={'UUID':via['uuid'],'margin_mm':margin,'start_free':free.covers(start),'end_free':free.covers(end),'common_faces':len(faces),'before_actual_source_annular_overlap_mm2':support};rows.append(row);print('R185_FACE',json.dumps(row),flush=True)
   for face in faces:
    axis=LineString([start,end])
    if not face.covers(axis):
     try:xy,_=T.route(face,tuple(start.coords[0]),tuple(end.coords[0]));axis=LineString([[round(x,6),round(y,6)]for x,y in xy])
     except(ValueError,AssertionError):continue
    if not face.covers(axis):continue
    xy=[list(p)for p in axis.coords];body=axis.buffer(.1,quad_segs=256)
    tracks=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'U10003-existing-FG-no-ripup-r185/'+via['uuid']+'/'+str(i))),'net':pad['net'],'layer':L,'a':a,'b':bb,'w':.2,'prospective_not_native':True}for i,(a,bb)in enumerate(zip(xy,xy[1:]))if a!=bb]
    nominees.append({'existing_return_via_UUID':via['uuid'],'points_mm':xy,'tracks':tracks,'length_mm':axis.length,'before_source_annular_overlap_mm2':support,'new_ground_fullbody_raw_reference_gap_mm2':{l:body.difference(s).area for l,s in ref.items()},'old_fault_tracks_vias_masks_all_exact_unchanged':True,'new_holes':0});break
   if nominees and nominees[-1]['existing_return_via_UUID']==via['uuid']:break
 result={'verdict':'EXISTING_SOURCE_GROUND_B_ROUTE_NOMINATED_ALL_FRESH_GATES_OPEN'if nominees else'FINITE_EXISTING_SOURCE_GROUND_B_ROUTE_NO_NOMINEE','model_sha256':sha(mp),'rows':rows,'nominees':nominees,'native_jobs':0,'board_written':False,'adopted':False,'manufacturing_ready':False,'every_old_native_Cu_and_owned_role_unchanged':True}
 (OUT/'receipt.json').write_text(json.dumps(result,indent=1,allow_nan=False)+'\n');(OUT/'proposed-nominees.pkl').write_bytes(pickle.dumps(nominees,protocol=5));print('R185_COMPLETE',len(nominees),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
