"""Restore every old B/In3 contact and the In2 bridge around a real legal port."""
import copy,hashlib,json,pickle,re,sys,uuid
from pathlib import Path
from shapely import from_wkb
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import tri_route as T
OUT=H/'U10003-complete-relocated-fault-barrel-route-nomination-r170';NET='/motherboard_do/DOA_FLT_N_FIELD';FG='/motherboard_motors/FIELD_GND'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def polys(s):return [p for p in ([s]if s.geom_type=='Polygon'else getattr(s,'geoms',[]))if p.geom_type=='Polygon'and not p.is_empty]
def main():
 assert not OUT.exists();OUT.mkdir()
 mp=H/'U10003-sparse-current-ground-fault-construction-r153/model.pkl';assert sha(mp)=='2d7b4c1ff29121e909602f9d76c89c02b4f7d8e5bb6d8a3f3bf5fad7fa1fd1d8';g,h,b,z,full=pickle.loads(mp.read_bytes())
 olduid='1dfba07d-0355-46e7-abf9-ae2e8d1c9843';oldvia=next(v for v in h['vias']if v['uuid']==olduid);assert(oldvia['x'],oldvia['y'],oldvia['d'],oldvia['drill'])==(213.45,143.75,.6,.3)
 legalfile=H/'U10003-exact-actual-paired-signal-barrel-ordinary-signal-replacement-faces-r169/EXACT_NEW_GROUND_PORT_CENTRE-legal.wkb';legal=from_wkb(legalfile.read_bytes());inner=legal.buffer(-.0001);assert not inner.is_empty
 p=inner.representative_point();site=[round(p.x,6),round(p.y,6)];assert legal.covers(Point(site))
 via={**oldvia,'x':site[0],'y':site[1],'d':.5,'drill':.2,'prospective_not_native':True,'mask_provenance':'HOST_RELOCATION_ONLY_ALL_ORIGINAL_NATIVE_MASKS_REQUIRE_FRESH_ACTUAL_NATIVE_FILL'}
 deletes={'9b04445f-38cf-4932-ac07-a2fa592e7b0a','ec60e344-6c18-4565-8eef-32449e4e88bd','c4e9e150-1f69-573b-bb70-d4d00441eba5','cc078be4-6bc9-5dd0-9194-ede561b48077'}
 oldtracks={t['uuid']:t for t in h['tracks']};assert deletes<=set(oldtracks)
 hard={**h,'tracks':[t for t in h['tracks']if t['uuid']not in deletes],'vias':[v for v in h['vias']if v['uuid']!=olduid]+[via]};records,trees=F.build({**hard,'zones':[]})
 reserved=C.BASE/'recovery-composite/c06/alternate-r07';areas=json.loads((reserved/'reserved-r07.json').read_bytes())['keepouts'];exceptions={}
 for line in(reserved/'reserve/board.kicad_dru').read_text().splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n)for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 ground_role_withdraw={'bde7a0cf-1ad7-5a04-b956-9f8848bb3f2a','9fe010df-73cf-5bfb-9f7a-bd227b701c3e','ee0efe05-1705-587c-ac86-49b1a7885ef9'}
 endpoints=[('B.Cu',[213.65,143.549999],site),('In3.Cu',site,[212.65,144.549999]),('In2.Cu',[218.35,142.15],site)];rows=[];tracks=[]
 for layer,a,bb in endpoints:
  answer=None
  for margin in (2.,4.,8.):
   win=box(min(a[0],bb[0])-margin,min(a[1],bb[1])-margin,max(a[0],bb[0])+margin,max(a[1],bb[1])+margin);query=win.buffer(1.);cuts=[]
   for j in trees[layer].query(query,predicate='intersects'):
    q=records[layer][int(j)];other=C.norm(q['net'])
    if other==NET:continue
    gap=(.15 if h['domains_normalized'][other]==h['domains_normalized'][NET]else.6)+.025+.000020;cuts.append(N.bounded_buffer(q['shape'].intersection(query),gap+.1))
   for q in z:
    other=C.norm(q['net'])
    if q['layer']!=layer or other==NET or not q['shape'].intersects(query):continue
    if q['uuid']in ground_role_withdraw:assert other==FG;continue
    gap=max(float(q['clearance_mm']),.15 if h['domains_normalized'][other]==h['domains_normalized'][NET]else.6)+.025+.000020;cuts.append(N.bounded_buffer(q['shape'].intersection(query),gap+.1))
   for p in hard['pads']:
    if C.norm(p['net'])==NET:continue
    for sh in C.poly(p.get('hole')or[]):
     if sh.intersects(query):cuts.append(N.bounded_buffer(sh,.275+.1+.000020))
   for v in hard['vias']:
    if C.norm(v['net'])!=NET and query.intersects(Point(v['x'],v['y'])):cuts.append(N.bounded_disk(v,v['drill']/2+.275+.1+.000020))
   for q in full['zones']:
    other=C.norm(q['net'])
    if other==NET or h['domains_normalized'][other]==h['domains_normalized'][NET]:continue
    for sh in C.poly(q['fills'].get(layer,[])):
     if sh.intersects(query):cuts.append(N.bounded_buffer(sh.intersection(query),max(.6,float(q['clearance_mm']))+.025+.1+.000020))
   for r in h['rule_areas']:
    if r.get('no_tracks')and layer in r['layers']:cuts.extend(N.bounded_buffer(s,.025+.1+.000020)for s in C.poly(r['outline'])if s.intersects(query))
   for r in areas:
    if layer in r['layers']and NET not in exceptions.get(r['name'],set()):cuts.extend(N.bounded_buffer(s,.025+.1+.000020)for s in C.poly(r['outline'])if s.intersects(query))
   free=win.difference(unary_union(cuts));faces=[p for p in polys(free)if p.covers(Point(a))and p.covers(Point(bb))];rows.append({'layer':layer,'margin_mm':margin,'common_faces':len(faces)})
   for face in faces:
    axis=LineString([a,bb])
    if not face.covers(axis):
     try:xy,_=T.route(face,tuple(a),tuple(bb));xy=[[round(x,6),round(y,6)]for x,y in xy];axis=LineString(xy)
     except (ValueError,AssertionError):continue
    if not face.covers(axis):continue
    xy=[list(p)for p in axis.coords];answer={'layer':layer,'points_mm':xy,'length_mm':axis.length,'full_reference_old_relationship_current_native_status':'OPEN'}
    for i,(aa,cc)in enumerate(zip(xy,xy[1:])):
     if aa!=cc:tracks.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'U10003-relocated-fault-r170/'+layer+'/'+str(i))),'net':oldvia['net'],'layer':layer,'a':aa,'b':cc,'w':.2,'prospective_not_native':True})
    break
   if answer:break
  print('R170_LAYER',layer,json.dumps(answer),flush=True)
  if not answer:break
 if len({t['layer']for t in tracks})==3:
  delta={'tracks':tracks,'same_UUID_existing_via_replacement':via,'exact_old_via':oldvia,'delete_tracks':[oldtracks[u]for u in sorted(deletes)],'ground_owned_local_negative_withdrawal_UUIDs':sorted(ground_role_withdraw)}
  (OUT/'proposed-sparse-delta.pkl').write_bytes(pickle.dumps(delta,protocol=5))
 else:delta=None
 receipt={'verdict':'COMPLETE_THREE_LAYER_OLD_CONTACT_RESTORATION_NOMINATED_ALL_REFERENCE_SOURCE_CURRENT_NATIVE_OPEN'if delta else'FINITE_RELOCATED_PORT_OLD_CONTACT_RESTORATION_NO_COMPLETE_NOMINEE','model_sha256':sha(mp),'legal_axis_file_sha256':sha(legalfile),'old_signal_barrel_UUID':olduid,'old_signal_site_mm':[213.45,143.75],'proposed_ordinary_signal_site_mm':site,'new_signal_diameter_drill_mm':[.5,.2],'actual_nearby_ground_site_mm':[216.04,142.95],'signal_ground_distance_mm':Point(site).distance(Point(216.04,142.95)),'rows':rows,'complete_sparse_delta_sha256':sha(OUT/'proposed-sparse-delta.pkl')if delta else None,'physical_geometry_changed':False,'old_B_In3_contacts_every_source_mask_and_complete_return_reference_required':True,'native_jobs':0,'adopted':False,'manufacturing_ready':False}
 put(OUT/'receipt.json',receipt);print('R170_RECEIPT',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
