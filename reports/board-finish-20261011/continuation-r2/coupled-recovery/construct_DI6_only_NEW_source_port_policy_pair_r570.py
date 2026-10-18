"""Move only the not-yet-installed DI6 source port around current power.

Continuous regions keep every original/new peer power role and all physical
Cu hard. Same-domain ORIGINAL fill may form normal prospective antipads;
its exact cut/contact/source/ref proof is deliberately still OPEN here.
"""
from pathlib import Path
import sys,json,pickle,hashlib,math,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_ao1_positive_operation_r4 as SERIAL
import tri_route as T
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely import set_precision
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'DI6-only-NEW-source-port-current-policy-pair-constructor-r570'
LG='/LOGIC_GND';NET='/motherboard_di/DI6_LOGIC'
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def info(s):return{'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':K.C.sha(s.wkb)}
def pieces(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for v in s.geoms for p in pieces(v)]if hasattr(s,'geoms')else[]
def sites(s,desired,limit=32):
 rows=[]
 for p in pieces(s):
  a=p.representative_point();z=nearest_points(p,Point(desired))[0]
  for pt in(a,z,Point((a.x+z.x)/2,(a.y+z.y)/2)):
   at=[round(pt.x,6),round(pt.y,6)]
   if s.covers(Point(at))and all(math.dist(at,u)>.015 for u in rows):rows.append(at)
 return sorted(rows,key=lambda x:math.dist(x,desired))[:limit]
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,v=None):
  p=Path(p);s=sha(p);assert v is None or v==s;pins[str(p.resolve())]=s;return p
 mp=pin(H/'DIC-retired-cutter-policy-coupled-current-r556/model.pkl','95d1636e90b8d11530cbc6ba461c60f7e68272e08d1e7cd4b5863bf0a43b46d5');g,h,b,q,c=pickle.loads(mp.read_bytes());gp=pin(H/'DIC-policy-coupled-actual-current-independent-r562/actual-new-all-drilled-groups.pkl','2c1e577fdad9358b88578a6338f934924e6ced9186ca8dc06a37e652bba9ec8c');gg=pickle.loads(gp.read_bytes());root=K.root(gg[LG],'J11001','2');refs={ly:unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==ly])for ly in('In1.Cu','In4.Cu')}
 rp=pin(H/'di6-native-owned-ledger-r14/receipt.json','6d7dcdc50a10393138761a0067fb73325eace8307800358d72723adcbb1afd79');r14=json.loads(rp.read_bytes());sourcefile=pin(P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb','eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a');source=sourcefile.read_bytes();ident=K.A.N.SourceNets(source);native=K.C.inventory(source)[3];saved=[];savedvias=[]
 for row in r14['exact_new_chunk_files']:
  cp=pin(row['chunk_file'],row['chunk_sha256']);p=K.A.G.parse(row['UUID'],cp.read_bytes(),{});assert row['UUID']not in native
  if p['kind']=='segment':saved.append({'uuid':row['UUID'],'net':ident.raw(p['net']),'layer':p['layer'],'a':p['a'],'b':p['b'],'w':p['w']})
  else:savedvias.append({'uuid':row['UUID'],'net':ident.raw(p['net']),'x':p['at'][0],'y':p['at'][1],'d':p['d'],'drill':p['drill'],'flashed':list(K.LAYERS)})
 savedsource=next(v for v in savedvias if K.L.norm(v['net'])==NET);savedret=next(v for v in savedvias if K.L.norm(v['net'])==LG);prefixend=[114.276775,102.254746];start=[119.176252,97.39558];retained=[t for t in saved if t['layer']=='In3.Cu'and t['uuid']!='eec928da-f55c-53ac-89ea-2e4674309615'];assert len(retained)==5
 win=box(110,95,125,104);rec,trees=K.F.build({**h,'zones':[]});domain=h['domains_normalized'];req=lambda a,n:.15 if domain[K.L.norm(a)]==domain[K.L.norm(n)]else .6;holes,ht=K.hole_context(h);localholes=[s for j,s in enumerate(holes)if not s.envelope.disjoint(win.buffer(1))];smd=[s for p in h['pads']if p['smd']for ly,rs in p['layers'].items()if ly in('F.Cu','B.Cu')for s in K.L.poly(rs)if not s.envelope.disjoint(win.buffer(1))];reservation,exempt=K.A.reservations();nativeids=set(native);nativezones=[]
 for z in c['zones']:
  for ly,rs in z['fills'].items():
   nativezones.extend((z,ly,s)for s in K.L.poly(rs)if not s.envelope.disjoint(win.buffer(1)))
 # Keep the exact selected landing proposals as hard bodies, no source credit.
 peerfile=pin(P/'field-power/R157-actual-rooted-old-barrel-minimal-local-ground-landing-nominees-r665/only-source-rooted-existing-barrel-local-ground-landing-proposals-NOT_MODEL.pkl');peer=pickle.loads(peerfile.read_bytes());put(OUT/'R665-peer-schema.json',{'type':type(peer).__name__,'keys':list(peer)if isinstance(peer,dict)else None});peerrows=peer['zones']if isinstance(peer,dict)and'zones'in peer else peer
 if isinstance(peerrows,dict):peerrows=list(peerrows.values())
 heldpeer=[]
 for row in peerrows:
  z=row.get('zone',row)
  if 'shape'not in z:continue
  if not z['shape'].envelope.disjoint(win.buffer(1)):heldpeer.append(z)
 allledger=[];free={};viaregions={}
 for net in(NET,LG):
  viaobs=[]
  for ly in K.LAYERS:
   tob=[];vob=[]
   for j in trees[ly].query(win.buffer(1),predicate='intersects'):
    row=rec[ly][int(j)];other=K.L.norm(row['net'])
    if other==net:continue
    gap=req(other,net)+.025+.005;tob.append(K.Z.bounded_buffer(row['shape'],gap+.105));vob.append(K.Z.bounded_buffer(row['shape'],gap+.255));allledger.append({'signal_net':net,'layer':ly,'kind':row['kind'],'UUID':row['uuid'],'raw_net':row['net'],'body_WKB_SHA256':K.C.sha(row['shape'].wkb)})
   for z,zz,s in nativezones:
    if zz!=ly or K.L.norm(z['net'])==net:continue
    # Only existing same-domain native fill is refill-withdrawable. Every
    # owned positive role and cross-domain native fill stays hard.
    if z['uuid']in nativeids and req(z['net'],net)==.15:continue
    gap=max(float(z['clearance_mm']),req(z['net'],net))+.025+.005;tob.append(K.Z.bounded_buffer(s,gap+.105));vob.append(K.Z.bounded_buffer(s,gap+.255))
   for z in q+heldpeer:
    if z['layer']!=ly or K.L.norm(z['net'])==net:continue
    gap=max(float(z['clearance_mm']),req(z['net'],net))+.025+.005
    for role in('shape','zone_outline_shape'):
     if role in z:tob.append(K.Z.bounded_buffer(z[role],gap+.105));vob.append(K.Z.bounded_buffer(z[role],gap+.255))
   for area in h['rule_areas']:
    if ly not in area['layers']:continue
    for s in K.L.poly(area['outline']):
     if area.get('no_tracks'):tob.append(K.Z.bounded_buffer(s,.130))
     if area.get('no_vias'):vob.append(K.Z.bounded_buffer(s,.280))
   for area in reservation['keepouts']:
    if ly in area['layers']and net not in exempt.get(area['name'],set()):
     for s in K.L.poly(area['outline']):tob.append(K.Z.bounded_buffer(s,.130));vob.append(K.Z.bounded_buffer(s,.280))
   # Every unowned drill is a physical barrier, independent of flash mask.
   tob.extend(K.Z.bounded_buffer(s,.385)for s in localholes);vob.extend(K.Z.bounded_buffer(s,.385)for s in localholes)
   free[net,ly]=win.difference(unary_union(tob));viaobs.extend(vob)
  viaobs.extend(K.Z.bounded_disk(v,.815)for v in h['vias']if not Point(v['x'],v['y']).envelope.disjoint(win.buffer(1)))
  viaobs.extend(K.Z.bounded_buffer(s,.385)for s in smd);viaregions[net]=win.difference(unary_union(viaobs));print('R570_REGION',net,viaregions[net].area,flush=True)
 fref=refs['In1.Cu'].buffer(-.105);iref=refs['In4.Cu'].buffer(-.105);ff=free[NET,'F.Cu'].intersection(fref);ii=free[NET,'In3.Cu'].intersection(iref);fc=[s for s in pieces(ff)if s.covers(Point(start))];ic=[s for s in pieces(ii)if s.covers(Point(prefixend))];region=viaregions[NET].intersection(unary_union(fc)).intersection(unary_union(ic));rf=viaregions[LG].intersection(refs['In1.Cu']).intersection(refs['In4.Cu']);regionfile=OUT/'continuous-NEW-signal-port-sites.wkb';regionfile.write_bytes(region.wkb);print('R570_CONTINUOUS',len(fc),len(ic),region.area,'return',rf.area,flush=True)
 attempts=[];selected=None
 for at in sites(region,[savedsource['x'],savedsource['y']],60):
  ring=Point(at).buffer(.999,quad_segs=128).difference(Point(at).buffer(.901,quad_segs=128));retregion=rf.intersection(ring)
  for rt in sites(retregion,[savedret['x'],savedret['y']],6):
   d=math.dist(at,rt)
   if not .90<=d<=1.0:continue
   retob=K.Z.bounded_buffer(Point(rt),.630);paths=[];attempt={'signal_at_mm':at,'return_at_mm':rt,'distance_mm':d,'paths':paths};attempts.append(attempt)
   for ly,a,bb,fr in(('F.Cu',start,at,ff),('In3.Cu',at,prefixend,ii)):
    candidates=[s for s in pieces(fr.difference(retob))if s.covers(Point(a))and s.covers(Point(bb))]
    if not candidates:break
    pts,search=T.route(candidates[0],tuple(a),tuple(bb));pts=[[round(x,6),round(y,6)]for x,y in pts]
    if len(pts)<2:break
    line=LineString(pts)
    if not candidates[0].covers(line):break
    paths.append({'layer':ly,'points_mm':pts,'width_mm':.2,'search':search,'length_mm':line.length})
   if len(paths)==2:selected=attempt;break
  if selected:break
 put(OUT/'finite-continuous-candidate-path-attempts.json',attempts);nt=[];nv=[];chunks={}
 if selected:
  for path in selected['paths']:
   for a,bb in zip(path['points_mm'],path['points_mm'][1:]):
    uid,ch=SERIAL.serial_track(ident,NET,a,bb,.2,path['layer']);chunks[uid]=ch;nt.append({'uuid':uid,'net':ident.raw(NET),'a':a,'b':bb,'layer':path['layer'],'w':.2})
  for t in retained:cp=next(z for z in r14['exact_new_chunk_files']if z['UUID']==t['uuid']);chunks[t['uuid']]=Path(cp['chunk_file']).read_bytes();nt.append(t)
  for net,at,old in((NET,selected['signal_at_mm'],savedsource),(LG,selected['return_at_mm'],savedret)):
   uid,ch=SERIAL.serial_via(ident,net,at);ch=ch.replace(uid.encode(),old['uuid'].encode());uid=old['uuid'];chunks[uid]=ch;nv.append({**old,'x':at[0],'y':at[1]})
  ident.assert_chunks(chunks);assert set(chunks).isdisjoint(native);print('R570_POSITIVE',selected['signal_at_mm'],selected['return_at_mm'],len(nt),flush=True)
 packet=OUT/'only-NEW-DI6-signal-source-pair-and-nine-path-successor-NOMINEE.pkl';packet.write_bytes(pickle.dumps({'tracks':nt,'vias':nv,'exact_new_chunks':chunks,'deleted_original_chunks':{},'selected':selected,'held_R665_peer_rows':heldpeer},protocol=5));put(OUT/'read-layer-native-owned-copper-hard-ledger.json',allledger)
 result={'verdict':'CONTINUOUS_NEW_DI6_PORT_AND_POLICY_PAIR_CONSTRUCTED_INDEPENDENT_ALL_GATES_OPEN'if selected else'CONTINUOUS_NEW_DI6_PORT_OR_POLICY_PAIR_BOUNDED_INCOMPLETE','exact_current_model_SHA256':sha(mp),'original_eedf_source_SHA256':sha(sourcefile),'saved_R14_pinned_recipe_SHA256':sha(rp),'nominee_packet_file':str(packet.resolve()),'nominee_packet_SHA256':sha(packet),'selected':selected,'native_original_Cu_deleted_moved_restored':0,'only_NEW_source_port_and_first_F_In3_escape_vary':True,'all_five_saved_tail_In3_tracks_exact':bool(selected),'held_R665_peer_count':len(heldpeer),'exact_same_domain_original_fill_normal_antipads_need_fullcontact_source_reference':True,'full_source_ref_current_native_SI_minfeature':'OPEN','old_R14_window_FAIL_and_native_remoteMOTION210nm_FAIL_preserved':True,'native_jobs':0,'board_written':False,'adopted':False,'input_SHA256':pins,'elapsed_seconds':time.monotonic()-st};put(OUT/'receipt.json',result);print('R570_COMPLETE',sha(OUT/'receipt.json'),result['verdict'],flush=True)
if __name__=='__main__':main()
