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
OUT=H/'AO1-COM-actual-SOURCE-to-U14623-nine-In4-finite-ground-bridge-r634';COM='/motherboard_analog_output/AO1_COM';LY='In4.Cu'
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
 ip=pin(H/'AO1-COM-six-actual-native-ground-islands-source-bridge-census-r632/actual-six-COM-islands-and-SOURCE-metals-NOMINATION_ONLY.pkl','3ed53fb76aaee578bee266481e72135e52bc0115d1caeb659b4db2e2196c409e');islands=pickle.loads(ip.read_bytes());assert all(r['all_old_nonfill_keys_retained_in_one_current_group']for r in islands['current_contact_bindings']);source=islands['source_metals'][LY];target=islands['islands'][2]['metals'][LY];assert any(p['ref']=='U14623'and p['pin']=='9'for p in islands['islands'][2]['pads']);mp=pin(H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/model.pkl','cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793');_,h,b,q,c=pickle.loads(mp.read_bytes());sp=pin(P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb','eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a');identity=K.A.N.SourceNets(sp.read_bytes());original=K.C.inventory(sp.read_bytes())[3];np=pin(P/'R155-known-reference-native-diagnostic-r157/copy/board.kicad_pcb','3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38');native=K.C.inventory(np.read_bytes())[3];gf=pin(N.R157/'actual-full-refill-geometry.json','421ce21eac9964fc53834514a560274e9527f9284c29da02fe94d37b950f1c6b');ng=json.loads(gf.read_bytes());vp=pin(H/'AO1-R19-VREF-only-four-chunk-current-requalification-handoff-r616/saved-VREF-only-add-stencil.json','4263f3b08ca71eda5c332bd62e759eb8f67c740da238bd33b0d6f918fba88eef');vr=json.loads(vp.read_bytes());peertracks=[];peervias=[]
 for uid,row in vr['exact_new_chunks'].items():
  p=pin(row['file'],row['SHA256']);r=K.A.G.parse(uid,p.read_bytes(),{})
  if r['kind']=='segment':peertracks.append({'uuid':uid,'net':r['net'],'layer':r['layer'],'a':r['a'],'b':r['b'],'w':r['w']})
  else:peervias.append({'uuid':uid,'net':r['net'],'x':r['at'][0],'y':r['at'][1],'d':r['d'],'drill':r['drill'],'flashed':list(K.LAYERS)})
 ph={**h,'tracks':h['tracks']+peertracks,'vias':h['vias']+peervias};rec,trees=K.F.build({**ph,'zones':[]});win=box(354,145,373,163);clip=win.buffer(1);dom=h['domains_normalized'];gap=lambda net:.15 if dom[K.L.norm(net)]==dom[COM]else .6;obs=[];ledger=[];radius=.15
 for i in trees[LY].query(clip,predicate='intersects'):
  r=rec[LY][int(i)]
  if K.L.norm(r['net'])==COM:continue
  req=gap(r['net'])+.025+radius;mask=K.Z.bounded_buffer(r['shape'].intersection(clip),req);obs.append(mask);ledger.append({'kind':r['kind'],'UUID':r['uuid'],'net':r['net'],'guarded_axis_mm':req,'mask':mask})
 for z in c['zones']:
  if K.L.norm(z['net'])==COM:continue
  req=max(float(z['clearance_mm']),gap(z['net']))+.025+radius
  for s in K.L.poly(z['fills'].get(LY,[])):
   if s.envelope.disjoint(clip):continue
   mask=K.Z.bounded_buffer(s.intersection(clip),req);obs.append(mask);ledger.append({'kind':'current_foreign_fill_HARD','UUID':z['uuid'],'net':z['net'],'guarded_axis_mm':req,'mask':mask})
 for z in q:
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
  req=v['drill']/2+radius+(.000025 if K.L.norm(v['net'])==COM else .275);obs.append(K.Z.bounded_disk(v,req))
 for p in h['pads']:
  for s in K.L.poly(p.get('hole')or[]):
   if not s.envelope.disjoint(clip):obs.append(K.Z.bounded_buffer(s,radius+(.000025 if K.L.norm(p['net'])==COM and not p['npth']else .275)))
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
  body=K.Z.bounded_buffer(LineString(pts),radius);sa=body.intersection(source);ta=body.intersection(target);row={'layer':LY,'points_mm':pts,'width_mm':.30,'length_mm':LineString(pts).length,'search':search,'actual_BEFORE_U14619_7_source_metal_overlap_mm2':sa.area,'actual_BEFORE_U14623_9_island_metal_overlap_mm2':ta.area,'GROUND_only_no_SIGNAL_shadow_waiver':True};attempts.append(row)
  if sa.area>.005 and ta.area>.005:selected=row;break
 tracks=[];chunks={};aftergroups=None;gains=None;oldloss=[]
 if selected:
  for a,z in zip(selected['points_mm'],selected['points_mm'][1:]):
   uid,ch=identity.serial_segment(COM,LY,a,z,.30);assert uid not in original and uid not in native;chunks[uid]=ch;tracks.append({'uuid':uid,'net':identity.raw(COM),'layer':LY,'a':a,'b':z,'w':.30})
  identity.assert_chunks(chunks);actual=islands['actual_ground_candidate'];after={**actual,'tracks':actual['tracks']+tracks};aftergroups=K.physical(after,COM,K.hole_context(after))[1];root=K.root(aftergroups,'U14619','7');oldloss=K.contact_losses([r['group']for r in islands['islands'].values()],aftergroups)[1];assert not oldloss;assert any(r['kind']=='pad'and r['uuid']=='013f67e9-bc46-4e7d-8c0e-0cf4e9cf6e4b'for r in root);gains={'before_source_nonfill_keys':len(K.keys(islands['islands'][islands['source_group']]['group'])),'after_source_nonfill_keys':len(K.keys(root)),'after_source_refs':{ly:unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==ly])for ly in('In1.Cu','In4.Cu')}}
 packet=OUT/'only-NEW-COM-In4-ground-tracks-source-isolator-NOMINEE.pkl';packet.write_bytes(pickle.dumps({'tracks':tracks,'vias':[],'exact_new_chunks':chunks,'original_deletes':{},'selected':selected,'actual_after_groups':aftergroups,'source_gains':gains,'hard_mask_ledger':ledger,'free_ground_axis':free},protocol=5));straight=LineString([[361.995154,153.873904],[366.004844,154.726098]]);blockers=[{k:v for k,v in r.items()if k!='mask'}for r in ledger if r['mask'].intersects(straight)];(OUT/'receipt.json').write_text(json.dumps({'verdict':'ACTUAL_COM_SOURCE_TO_ISOLATOR_IN4_GROUND_BRIDGE_NOMINATED_INDEPENDENT_OPEN'if selected else'ACTUAL_COM_SOURCE_TO_ISOLATOR_IN4_GROUND_BRIDGE_BOUNDED_HARD_BLOCKER_INCOMPLETE','input_SHA256':pins,'selected':selected,'attempts':attempts,'straight_nearest_gap_HARD_blockers':blockers,'source_nonfill_key_gain':None if gains is None else {k:v for k,v in gains.items()if k!='after_source_refs'},'old_six_COM_group_contact_losses':oldloss,'sparse_packet_file':str(packet.resolve()),'sparse_packet_SHA256':sha(packet),'ground_only_no_new_SIGNAL_shadow_predicate':True,'original_Cu_foreign_planes_or_holes_changed':0,'new_vias':0,'native_jobs':0,'adopted':False,'native_AFTER_source_masks_all_oldrefs_current_final_loop_SI':'OPEN','elapsed_seconds':time.monotonic()-st},indent=1,allow_nan=False)+'\n');print('R634_COMPLETE',sha(OUT/'receipt.json'),bool(selected),len(tracks),flush=True)
if __name__=='__main__':main()
