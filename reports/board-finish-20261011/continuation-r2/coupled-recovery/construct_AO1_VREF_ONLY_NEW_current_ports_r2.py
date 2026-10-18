"""Replan only new VREF F/B paths and one ordinary SOURCE_COM return.

Current discrete copper is pinned R753/R300. Full native BEFORE source
provides the nomination reference; AFTER-native/replay/current gates open.
"""
from pathlib import Path
import sys,json,pickle,hashlib,time,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import audit_ao1_positive_operation_r4 as SERIAL
import tri_route as T
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
OUT=H/'AO1-VREF-ONLY-NEW-current-port-continuous-constructor-r2'
COM='/motherboard_analog_output/AO1_COM';VREF='/motherboard_analog_output/AO1_VREF'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,o):(OUT/n).write_text(json.dumps(o,indent=1,allow_nan=False)+'\n')
def parts(s):
 if s.is_empty:return []
 if s.geom_type=='Polygon':return[s]
 return [p for g in s.geoms for p in parts(g)]if hasattr(s,'geoms')else[]
def info(s):return{'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def sites(s,desired,limit=72):
 rows=[]
 for p in parts(s):
  a=p.representative_point();b=nearest_points(p,Point(desired))[0]
  for pt in(a,b,Point((a.x+b.x)/2,(a.y+b.y)/2)):
   at=[round(pt.x,6),round(pt.y,6)]
   if p.covers(Point(at))and all(math.dist(at,q)>.015 for q in rows):rows.append(at)
 return sorted(rows,key=lambda p:math.dist(p,desired))[:limit]
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,want=None):
  p=Path(p);s=sha(p);assert want is None or s==want;pins[str(p.resolve())]=s;return p
 cp=pin(H/'AO1-saved-four-add-exact-current-native-screen-r1/pinned-current-local-Cu-native-before-source-only-screen.pkl','0349ddad81a9dc6dd0ef106c3a65ce03e0ff44ae3d04244e882bbe0475590a2e');saved=pickle.loads(cp.read_bytes());c=saved['full_before'];local=saved['current'];refs=saved['source_refs'];vias=saved['current_vias'];win=saved['win'];rec,trees=K.F.build(local);dom=c['domains_normalized'];req=lambda a,b:.15 if dom[K.L.norm(a)]==dom[K.L.norm(b)]else .6
 reserve,exempt=K.A.reservations();smd=[s for p in local['pads']if p['smd']for ly,rs in p['layers'].items()if ly in('F.Cu','B.Cu')for s in K.L.poly(rs)];holes=[(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128),v['net'],False)for v in local['vias']]+[(s,p['net'],p['npth'])for p in local['pads']for s in K.L.poly(p.get('hole')or[])];actualzones=[]
 for z in c['zones']:
  for ly,rs in z['fills'].items():
   for s in K.L.poly(rs):
    if not s.envelope.disjoint(win.buffer(1)):actualzones.append((z,ly,s))
 free={};regions={};hard=[]
 for net in(VREF,COM):
  allvia=[]
  for ly in K.LAYERS:
   trackobs=[];viaobs=[]
   for r in rec[ly]:
    if K.L.norm(r['net'])==net:continue
    gap=req(net,r['net'])+.025+.000005
    trackobs.append(K.Z.bounded_buffer(r['shape'],gap+.100005));viaobs.append(K.Z.bounded_buffer(r['shape'],gap+.255));hard.append({'net':net,'layer':ly,'kind':r['kind'],'UUID':r['uuid'],'other_net':r['net']})
   for z,zly,s in actualzones:
    if zly!=ly or K.L.norm(z['net'])==net:continue
    # Source-native same-domain fill may form its own normal local antipad;
    # every cross-domain native fill stays fixed and hard.
    if req(net,z['net'])==.15:continue
    gap=max(float(z['clearance_mm']),req(net,z['net']))+.025+.000005
    trackobs.append(K.Z.bounded_buffer(s.intersection(win.buffer(1)),gap+.100005));viaobs.append(K.Z.bounded_buffer(s.intersection(win.buffer(1)),gap+.255));hard.append({'net':net,'layer':ly,'kind':'cross-domain_actual_native_fill','UUID':z['uuid'],'other_net':z['net']})
   for rule in c['rule_areas']:
    if ly not in rule['layers']:continue
    for s in K.L.poly(rule['outline']):
     if not s.envelope.disjoint(win.buffer(1)):
      if rule.get('no_tracks'):trackobs.append(K.Z.bounded_buffer(s,.130))
      if rule.get('no_vias'):viaobs.append(K.Z.bounded_buffer(s,.280))
   for rule in reserve['keepouts']:
    if ly not in rule['layers']or net in exempt.get(rule['name'],set()):continue
    for s in K.L.poly(rule['outline']):
     if not s.envelope.disjoint(win.buffer(1)):trackobs.append(K.Z.bounded_buffer(s,.130));viaobs.append(K.Z.bounded_buffer(s,.280))
   trackobs.extend(K.Z.bounded_buffer(s,.375005)for s,n,np in holes if K.L.norm(n)!=net or np);viaobs.extend(K.Z.bounded_buffer(s,.380005)for s,n,np in holes)
   free[net,ly]=win.difference(unary_union(trackobs));allvia.extend(viaobs)
  allvia.extend(K.Z.bounded_disk(v,.815)for v in local['vias']);allvia.extend(K.Z.bounded_buffer(s,.380005)for s in smd);regions[net]=win.difference(unary_union(allvia));print('AO1_R2_PORT_REGION',net,regions[net].area,flush=True)
 endpoint=[375.498,129.0];sourcefree={};components={}
 for ly in('F.Cu','B.Cu'):
  sourcefree[ly]=free[VREF,ly].intersection(refs[K.MAP[ly]].buffer(-.100005));components[ly]=[p for p in parts(sourcefree[ly])if p.covers(Point(endpoint))];print('AO1_R2_ENDPOINT_COMPONENTS',ly,len(components[ly]),flush=True)
 signalregion=regions[VREF].intersection(unary_union(components['F.Cu'])).intersection(unary_union(components['B.Cu']));returnregion=regions[COM].intersection(refs['In1.Cu'].buffer(-.255)).intersection(refs['In4.Cu'].buffer(-.255))
 for n,s in(('signal-region',signalregion),('return-region',returnregion)):(OUT/(n+'.wkb')).write_bytes(s.wkb)
 attempts=[];selected=None
 sgpts=sites(signalregion,[376.6,129.0],128)
 for at in sgpts:
  ring=Point(at).buffer(.999,quad_segs=128).difference(Point(at).buffer(.901,quad_segs=128));rr=returnregion.intersection(ring)
  for rt in sites(rr,[at[0],at[1]+.95],12):
   distance=math.dist(at,rt)
   if not .90<=distance<=1.0:continue
   paths=[];attempt={'signal_at_mm':at,'return_at_mm':rt,'distance_mm':distance,'paths':paths};attempts.append(attempt)
   returnob=K.Z.bounded_buffer(Point(rt),.625010)
   for ly in('F.Cu','B.Cu'):
    ff=sourcefree[ly].difference(returnob);cc=[p for p in parts(ff)if p.covers(Point(endpoint))and p.covers(Point(at))]
    if not cc:break
    pts,search=T.route(cc[0],endpoint,at);pts=[[round(x,6),round(y,6)]for x,y in pts]
    if len(pts)<2 or not cc[0].covers(LineString(pts)):break
    paths.append({'layer':ly,'points_mm':pts,'width_mm':.2,'search':search,'length_mm':LineString(pts).length})
   if len(paths)==2:selected=attempt;break
  if selected:break
 put('bounded-exact-current-port-path-attempts.json',attempts);tracks=[];nv=[];chunks={}
 sourcefile=pin(ROOT/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/board.kicad_pcb');identity=K.A.N.SourceNets(sourcefile.read_bytes());native=K.C.inventory(sourcefile.read_bytes())[3]
 if selected:
  for path in selected['paths']:
   for a,b in zip(path['points_mm'],path['points_mm'][1:]):
    uid,ch=identity.serial_segment(VREF,path['layer'],a,b,.2);chunks[uid]=ch;tracks.append({'uuid':uid,'net':identity.raw(VREF),'a':a,'b':b,'w':.2,'layer':path['layer']})
  for net,at in((VREF,selected['signal_at_mm']),(COM,selected['return_at_mm'])):
   uid,ch=SERIAL.serial_via(identity,net,at);chunks[uid]=ch;nv.append({'uuid':uid,'net':identity.raw(net),'x':at[0],'y':at[1],'d':.5,'drill':.2,'flashed':list(K.LAYERS)})
  identity.assert_chunks(chunks);assert set(chunks).isdisjoint(native)
 packet=OUT/'only-NEW-AO1-VREF-tracks-and-two-ordinary-vias-NOMINEE.pkl';packet.write_bytes(pickle.dumps({'tracks':tracks,'vias':nv,'exact_new_chunks':chunks,'deleted_original_chunks':{},'selected':selected},protocol=5));put('hard-current-discrete-and-cross-domain-plane-roles.json',hard)
 cache=OUT/'exact-current-Cu-continuous-source-only-regions.pkl';cache.write_bytes(pickle.dumps({'sourcefree':sourcefree,'free':free,'viaregions':regions,'signalregion':signalregion,'returnregion':returnregion,'source_refs':refs},protocol=5))
 result={'verdict':'ONLY_NEW_VREF_POLICY_PORT_AND_F_B_PATH_CONSTRUCTED_ALL_REQUALIFICATION_OPEN'if selected else'ONLY_NEW_VREF_CONTINUOUS_PORTS_BOUNDED_NO_COMPLETE_PATH','source_endpoint_mm':endpoint,'endpoint_component_counts':{l:len(v)for l,v in components.items()},'signal_region':info(signalregion),'return_region':info(returnregion),'signal_site_count':len(sgpts),'attempt_count':len(attempts),'selected':selected,'packet_file':str(packet.resolve()),'packet_SHA256':sha(packet),'region_cache_SHA256':sha(cache),'new_tracks':len(tracks),'new_vias':len(nv),'deleted_or_moved_original_Cu':0,'old_DAC_SDI_MON_copper_all_retained':True,'raw_all_contact_reference_native_current_SI_gates':'OPEN','current_FULL_AFTER_planes_pending':True,'native_jobs':0,'adopted':False,'input_SHA256':pins,'elapsed_seconds':time.monotonic()-st};put('receipt.json',result);print(json.dumps({k:result[k]for k in('verdict','endpoint_component_counts','signal_site_count','attempt_count','selected','elapsed_seconds')}),flush=True)
if __name__=='__main__':main()
