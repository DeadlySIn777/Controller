"""Small real SOURCE-to-isolator COM bridge, ground conduction only.

Every foreign current/FULL-native plane, old Cu, drill and barrier is HARD.
No SIGNAL shadow predicate is applied to a new same-net DC-ground track.
"""
from pathlib import Path
import sys,json,pickle,hashlib,time,re
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import R157_native_selected_actual_conversion_r673 as N
import tri_route as T
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
OUT=H/'AO1-COM-C19506-1-real-SOURCE-In4.Cu-ground-current-peers-r680';COM='/motherboard_analog_output/AO1_COM';LY='In4.Cu'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def parts(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for x in getattr(s,'geoms',[])for p in parts(x)]
def inf(s):return{'empty':s.is_empty,'area_mm2':s.area,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':K.C.sha(s.wkb)}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 ip=pin(H/'AO1-COM-six-actual-native-ground-islands-source-bridge-census-r632/actual-six-COM-islands-and-SOURCE-metals-NOMINATION_ONLY.pkl','3ed53fb76aaee578bee266481e72135e52bc0115d1caeb659b4db2e2196c409e');islands=pickle.loads(ip.read_bytes());assert all(r['all_old_nonfill_keys_retained_in_one_current_group']for r in islands['current_contact_bindings']);source=islands['source_metals'][LY];target=islands['islands'][3]['metals'][LY];assert any(p['ref']=='C19506'and p['pin']=='1'for p in islands['islands'][3]['pads']);mp=pin(H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/model.pkl','cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793');_,h,b,q,c=pickle.loads(mp.read_bytes());sp=pin(P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb','eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a');identity=K.A.N.SourceNets(sp.read_bytes());original=K.C.inventory(sp.read_bytes())[3];np=pin(P/'R155-known-reference-native-diagnostic-r157/copy/board.kicad_pcb','3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38');native=K.C.inventory(np.read_bytes())[3];gf=pin(N.R157/'actual-full-refill-geometry.json','421ce21eac9964fc53834514a560274e9527f9284c29da02fe94d37b950f1c6b');ng=json.loads(gf.read_bytes());
 rp=pin(H/'AO1-R656-seven-GROUND-additions-joint-R20-independent-source-geometry-r658/receipt.json','faa3a4649c2bf82849f135af651653eee9ccc27dc6ce9c35c48584371f10cc12');rr=json.loads(rp.read_bytes());cp=pin(rr['after_context_file'],'94ea2f68b967fac5c78a8085291b1f46de54b2f5b29a33de12253fe8119f7c23');h=pickle.loads(cp.read_bytes());c=h
 curp=pin(P/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb','7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2');cur=K.C.inventory(curp.read_bytes())[3];peerp=pin(H/'AO1-MON3-VREF-and-only-b177-5V-native-width-endpoint-source-detour-r19/MON3-VREF-plus-exact-b177-5V-controlled-detour-NOMINEE.pkl','d35097754a50017d6d4b17d4388dbced44c63547b39fbddbcda31b8a78cf4181');retired=pickle.loads(peerp.read_bytes())['deleted_original_chunks'];existing={r['uuid']for r in h['tracks']+h['vias']};heldtracks=[];heldvias=[]
 for uid,ch in cur.items():
  if uid in retired:assert ch==retired[uid];continue
  if uid in existing or not ch.lstrip().startswith((b'(segment',b'(via')):continue
  r=K.A.G.parse(uid,ch,{})
  if r['kind']=='segment':heldtracks.append({'uuid':uid,'net':r['net'],'layer':r['layer'],'a':r['a'],'b':r['b'],'w':r['w']})
  else:heldvias.append({'uuid':uid,'net':r['net'],'x':r['at'][0],'y':r['at'][1],'d':r['d'],'drill':r['drill'],'flashed':list(K.LAYERS)})
 ph={**h,'tracks':h['tracks']+heldtracks,'vias':h['vias']+heldvias};rec,trees=K.F.build({**ph,'zones':[]});win=box(334,154,374,186);clip=win.buffer(1);dom=h['domains_normalized'];gap=lambda net:.15 if dom[K.L.norm(net)]==dom[COM]else .6;obs=[];ledger=[];radius=.10
 for i in trees[LY].query(clip,predicate='intersects'):
  r=rec[LY][int(i)]
  if K.L.norm(r['net'])==COM:continue
  req=gap(r['net'])+.025+radius+(.005 if r['kind']=='pad'else 0.);mask=K.Z.bounded_buffer(r['shape'].intersection(clip),req);obs.append(mask);ledger.append({'kind':r['kind'],'UUID':r['uuid'],'net':r['net'],'guarded_axis_mm':req,'mask':mask})
 for z in c['zones']:
  if K.L.norm(z['net'])==COM:continue
  req=max(float(z['clearance_mm']),gap(z['net']))+.025+radius
  for s in K.L.poly(z['fills'].get(LY,[])):
   if s.envelope.disjoint(clip):continue
   mask=K.Z.bounded_buffer(s.intersection(clip),req);obs.append(mask);ledger.append({'kind':'current_foreign_fill_HARD','UUID':z['uuid'],'net':z['net'],'guarded_axis_mm':req,'mask':mask})
 latefile=pin(P/'field-power/R157-actual-rooted-old-barrel-minimal-local-ground-landing-nominees-r665/only-source-rooted-existing-barrel-local-ground-landing-proposals-NOT_MODEL.pkl');late=pickle.loads(latefile.read_bytes())
 for z in list(q)+late:
  if z['layer']!=LY or K.L.norm(z['net'])==COM:continue
  req=max(float(z['clearance_mm']),gap(z['net']))+.025+radius
  for role in('shape','zone_outline_shape'):
   if z[role].envelope.disjoint(clip):continue
   mask=K.Z.bounded_buffer(z[role].intersection(clip),req);obs.append(mask);ledger.append({'kind':'owned_positive_HARD','UUID':z['uuid'],'net':z['net'],'role':role,'guarded_axis_mm':req,'mask':mask})
 for z in ng['zones']:
  if K.L.norm(z['net'])==COM:continue
  ch=native[z['uuid']];m=re.search(rb'\(connect_pads(?:\s+[^()\s]+)?\s*\(clearance\s+([0-9.]+)\)',ch);assert m,z['uuid'];req=max(float(m.group(1)),gap(z['net']))+.025+radius
  for s in K.L.poly(N.O.polys(z['fills'].get(LY,[]))):
   if s.envelope.disjoint(clip):continue
   mask=K.Z.bounded_buffer(s.intersection(clip),req);obs.append(mask);ledger.append({'kind':'FULL_native_foreign_fill_HARD','UUID':z['uuid'],'net':z['net'],'guarded_axis_mm':req,'mask':mask})
 for v in ph['vias']:
  if Point(v['x'],v['y']).envelope.disjoint(clip):continue
  if K.L.norm(v['net'])==COM:continue # same-net plated contact; physical body below is drilled
  req=v['drill']/2+radius+.275;obs.append(K.Z.bounded_disk(v,req))
 for p in h['pads']:
  for s in K.L.poly(p.get('hole')or[]):
   if not s.envelope.disjoint(clip)and(K.L.norm(p['net'])!=COM or p['npth']):obs.append(K.Z.bounded_buffer(s,radius+.275))
 reserve,exempt=K.A.reservations()
 for area in h['rule_areas']:
  if LY in area['layers']and area.get('no_tracks'):obs.extend(K.Z.bounded_buffer(s,radius+.025)for s in K.L.poly(area['outline']))
 for area in reserve['keepouts']:
  if LY in area['layers']and COM not in exempt.get(area['name'],set()):obs.extend(K.Z.bounded_buffer(s,radius+.025)for s in K.L.poly(area['outline']))
 free=win.difference(unary_union(obs));attachments=[];attempts=[];selected=None;sourceSafe=source.intersection(clip).buffer(-.050025,quad_segs=128);targetSafe=target.intersection(clip).buffer(-.050025,quad_segs=128)
 for face in parts(free):
  a=face.intersection(sourceSafe);z=face.intersection(targetSafe)
  if a.is_empty or z.is_empty:continue
  x,y=nearest_points(a,z);pts,search=T.route(face,tuple(x.coords[0]),tuple(y.coords[0]));pts=[[round(px,6),round(py,6)]for px,py in pts]
  if len(pts)<2 or not face.covers(LineString(pts)):continue
  body=K.Z.bounded_buffer(LineString(pts),radius);physical_holes,ht=K.hole_context(islands['actual_ground_candidate']);physical_body=body.difference(unary_union([physical_holes[int(j)]for j in ht.query(body,predicate='intersects')]));sa=physical_body.intersection(source);ta=physical_body.intersection(target);row={'layer':LY,'points_mm':pts,'width_mm':.20,'length_mm':LineString(pts).length,'search':search,'actual_BEFORE_U14619_7_source_metal_overlap_mm2':sa.area,'actual_BEFORE_C19506_1_island_metal_overlap_mm2':ta.area,'GROUND_only_no_SIGNAL_shadow_waiver':True};attempts.append(row)
  if sa.area>.005 and ta.area>.005:selected=row;break
 tracks=[];chunks={};aftergroups=None;gains=None;oldloss=[]
 if selected:
  for a,z in zip(selected['points_mm'],selected['points_mm'][1:]):
   uid,ch=identity.serial_segment(COM,LY,a,z,.20);assert uid not in original and uid not in native;chunks[uid]=ch;tracks.append({'uuid':uid,'net':identity.raw(COM),'layer':LY,'a':a,'b':z,'w':.20})
  identity.assert_chunks(chunks);actual=islands['actual_ground_candidate'];after={**actual,'tracks':actual['tracks']+tracks};aftergroups=K.physical(after,COM,K.hole_context(after))[1];root=K.root(aftergroups,'U14619','7');oldloss=K.contact_losses([r['group']for r in islands['islands'].values()],aftergroups)[1];assert not oldloss;assert any(r['kind']=='pad'and r['uuid']=='41004407-03be-4571-be77-ee721df93cd9'for r in root);gains={'before_source_nonfill_keys':len(K.keys(islands['islands'][islands['source_group']]['group'])),'after_source_nonfill_keys':len(K.keys(root)),'after_source_refs':{ly:unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==ly])for ly in('In1.Cu','In4.Cu')}}
 packet=OUT/'only-NEW-COM-F-Cu-ground-tracks-NOMINEE.pkl';packet.write_bytes(pickle.dumps({'tracks':tracks,'vias':[],'exact_new_chunks':chunks,'original_deletes':{},'selected':selected,'actual_after_groups':aftergroups,'source_gains':gains,'hard_mask_ledger':ledger,'free_ground_axis':free},protocol=5));straight=LineString([[354.15168,177],[352.448318,169.4]]);blockers=[{k:v for k,v in r.items()if k!='mask'}for r in ledger if r['mask'].intersects(straight)];(OUT/'receipt.json').write_text(json.dumps({'verdict':'ACTUAL_COM_SOURCE_TO_C19506_1_F_CU_GROUND_BRIDGE_NOMINATED_INDEPENDENT_OPEN'if selected else'ACTUAL_COM_SOURCE_TO_C19506_1_F_CU_GROUND_BRIDGE_BOUNDED_HARD_BLOCKER_INCOMPLETE','input_SHA256':pins,'selected':selected,'attempts':attempts,'straight_nearest_gap_HARD_blockers':blockers,'source_nonfill_key_gain':None if gains is None else {k:v for k,v in gains.items()if k!='after_source_refs'},'old_six_COM_group_contact_losses':oldloss,'sparse_packet_file':str(packet.resolve()),'sparse_packet_SHA256':sha(packet),'ground_only_no_new_SIGNAL_shadow_predicate':True,'original_Cu_foreign_planes_or_holes_changed':0,'new_vias':0,'native_jobs':0,'adopted':False,'native_AFTER_source_masks_all_oldrefs_current_final_loop_SI':'OPEN','elapsed_seconds':time.monotonic()-st},indent=1,allow_nan=False)+'\n');print('R680_COMPLETE',sha(OUT/'receipt.json'),bool(selected),len(tracks),flush=True)
if __name__=='__main__':main()
