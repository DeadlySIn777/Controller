"""Bounded only-new F/In3/B two-SG topology with controlled MON4 detour."""
from pathlib import Path
import sys,json,pickle,hashlib,time,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import audit_ao1_positive_operation_r4 as SERIAL
import tri_route as T
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
OUT=H/'AO1-MON4-two-SG-F-In3-B-source-preserving-joint-search-r17'
MON='/motherboard_analog_output/AO1_MON_12V';VREF='/motherboard_analog_output/AO1_VREF';COM='/motherboard_analog_output/AO1_COM'
DELS={'6b5d7465-3e16-4492-82be-cd9ae2fb2ad5','e0c09d60-50a7-411e-9a56-ce39e23f1bff','16ac4bda-32bd-47a3-8cc4-404758a78d41','6a7a6862-5b3a-4764-bead-1acf9ac7b861'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,o):(OUT/n).write_text(json.dumps(o,indent=1,allow_nan=False)+'\n')
def pieces(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for g in s.geoms for p in pieces(g)]if hasattr(s,'geoms')else[]
def info(s):return{'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def sites(s,desired,limit=30):
 rows=[]
 for p in pieces(s):
  a=p.representative_point();b=nearest_points(p,Point(desired))[0]
  for q in(a,b,Point((a.x+b.x)/2,(a.y+b.y)/2)):
   at=[round(q.x,6),round(q.y,6)]
   if p.covers(Point(at))and all(math.dist(at,z)>.015 for z in rows):rows.append(at)
 return sorted(rows,key=lambda p:math.dist(p,desired))[:limit]
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 rr=pin(H/'AO1-joint-MON4-adjoining-boundary-all-old-source-body-protected-r16/receipt.json');r=json.loads(rr.read_bytes());cf=pin(rr.parent/'exact-current-coupled-prospective-reference-inputs.pkl',r['context_cache_SHA256']);ctx=pickle.loads(cf.read_bytes());c=ctx['actual_full_before'];d=ctx['VREF_guard_regions'];refs=d['source_refs'];sf=d['sourcefree'];vr=d['viaregions'];mfbase=ctx['MON_baseline_free'];ep=[375.498,129.0];win=ctx['current_local_minus_MON3']['outline'];i3=d['free'][VREF,'In3.Cu'].intersection(refs['In4.Cu'].buffer(-.100005));protect=[];rad=max(float(z['clearance_mm'])for z in c['zones']if K.L.norm(z['net'])==COM)+.25+.000005
 for t in c['tracks']:
  ly=t['layer'];net=K.L.norm(t['net'])
  if t['uuid']in DELS or net==COM or c['domains_normalized'].get(net)!=c['domains_normalized'][COM]or ly not in K.MAP:continue
  body=K.L.body(t)
  if body.envelope.disjoint(i3.envelope):continue
  covered=body.intersection(refs[K.MAP[ly]])
  if not covered.is_empty:protect.append(K.Z.bounded_buffer(covered,rad))
 safe=vr[VREF].difference(unary_union(protect));ports={}
 for ly in('F.Cu','B.Cu'):
  cc=[p for p in pieces(sf[ly])if p.covers(Point(ep))];ports[ly]=safe.intersection(unary_union(cc)).intersection(i3).buffer(-.000010)
 put('exact-old-source-protected-two-SG-port-regions.json',{l:info(s)for l,s in ports.items()});fs=[]
 for desired in([376.1,126.9],[372.8,130.5],[371.8,127.8],[376.8,130.8]):
  for at in sites(ports['F.Cu'],desired,48):
   if all(math.dist(at,z)>.015 for z in fs):fs.append(at)
 returns=d['returnregion'];attempts=[];chosen=None;paircount=0
 def rings(at):return Point(at).buffer(.999,quad_segs=128).difference(Point(at).buffer(.901,quad_segs=128))
 def return_options(a,b):
  shared=returns.intersection(rings(a)).intersection(rings(b));rr=[]
  for q in sites(shared,[(a[0]+b[0])/2,(a[1]+b[1])/2],12):rr.append([q])
  if rr:return rr
  aa=sites(returns.intersection(rings(a)).difference(K.Z.bounded_buffer(Point(b),.815)),[a[0],a[1]+.95],4);bb=sites(returns.intersection(rings(b)).difference(K.Z.bounded_buffer(Point(a),.815)),[b[0],b[1]+.95],4)
  return[[ra,rb]for ra in aa for rb in bb if math.dist(ra,rb)>=.815][:8]
 for index,a in enumerate(fs[:48]):
  nearby=ports['B.Cu'].intersection(Point(a).buffer(8)).difference(Point(a).buffer(.825));bs=[]
  for desired in([a[0]+1,a[1]],[a[0]-1,a[1]],[375.8,130.8],ep):
   for b in sites(nearby,desired,8):
    if all(math.dist(b,z)>.015 for z in bs):bs.append(b)
  for b in bs[:20]:
   paircount+=1
   for rts in return_options(a,b):
    if any(not(.90<=math.dist(a,q)<=1 and .90<=math.dist(b,q)<=1)for q in rts)and len(rts)==1:continue
    if len(rts)==2 and(not .90<=math.dist(a,rts[0])<=1 or not .90<=math.dist(b,rts[1])<=1):continue
    returnob=unary_union([K.Z.bounded_buffer(Point(q),.625010)for q in rts]);paths=[];trial={'F_SG_mm':a,'B_SG_mm':b,'ordinary_returns_mm':rts,'paths':paths};attempts.append(trial)
    for ly,start,end,fr in(('F.Cu',ep,a,sf['F.Cu']),('In3.Cu',a,b,i3),('B.Cu',b,ep,sf['B.Cu'])):
     ff=fr.difference(returnob);cc=[p for p in pieces(ff)if p.covers(Point(start))and p.covers(Point(end))]
     if not cc:break
     pts,search=T.route(cc[0],start,end);pts=[[round(x,6),round(y,6)]for x,y in pts]
     if len(pts)<2 or not cc[0].covers(LineString(pts)):break
     paths.append({'layer':ly,'points_mm':pts,'width_mm':.2,'length_mm':LineString(pts).length,'search':search})
    if len(paths)!=3:continue
    cutters=[K.Z.bounded_buffer(LineString(paths[0]['points_mm']),.375010),K.Z.bounded_buffer(Point(a),.625010),K.Z.bounded_buffer(Point(b),.625010)]+[K.Z.bounded_buffer(Point(q),.525010)for q in rts];mf=mfbase.difference(unary_union(cutters));start=[369.35,125.15];end=[375.25,130.049999];mc=[p for p in pieces(mf)if p.covers(Point(start))and p.covers(Point(end))];trial['MON_common_components']=len(mc)
    if not mc:continue
    pts,search=T.route(mc[0],start,end);pts=[[round(x,6),round(y,6)]for x,y in pts]
    if len(pts)<2 or not mc[0].covers(LineString(pts)):continue
    trial['MON_detour']={'layer':'F.Cu','points_mm':pts,'width_mm':.2,'locked_yes':True,'length_mm':LineString(pts).length,'search':search};chosen=trial;break
   if chosen:break
  put('progress.json',{'F_ports_completed':index+1,'F_port_count':min(len(fs),48),'SG_pair_count':paircount,'attempts':len(attempts),'elapsed_seconds':time.monotonic()-st});print('AO1_R17_PROGRESS',index+1,len(fs),paircount,len(attempts),flush=True)
  if chosen or paircount>=256:break
 put('bounded-two-SG-three-leg-and-MON4-attempts.json',attempts);sp=pin(ROOT/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb','7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2');ident=K.A.N.SourceNets(sp.read_bytes());native=K.C.inventory(sp.read_bytes())[3];nt=[];nv=[];chunks={};deleted={}
 if chosen:
  for path in chosen['paths']+[chosen['MON_detour']]:
   net=MON if path.get('locked_yes')else VREF
   for a,b in zip(path['points_mm'],path['points_mm'][1:]):
    uid,ch=ident.serial_segment(net,path['layer'],a,b,.2)
    if net==MON:ch=ch.replace(b'\t\t(layer ',b'\t\t(locked yes)\n\t\t(layer ');assert b'(locked yes)'in ch
    chunks[uid]=ch;nt.append({'uuid':uid,'net':ident.raw(net),'layer':path['layer'],'a':a,'b':b,'w':.2,'locked_yes':net==MON})
  for net,at in [(VREF,chosen['F_SG_mm']),(VREF,chosen['B_SG_mm'])]+[(COM,at)for at in chosen['ordinary_returns_mm']]:
   uid,ch=SERIAL.serial_via(ident,net,at);chunks[uid]=ch;nv.append({'uuid':uid,'net':ident.raw(net),'x':at[0],'y':at[1],'d':.5,'drill':.2,'flashed':list(K.LAYERS)})
  deleted={u:native[u]for u in sorted(DELS)}
  for uid,ch in deleted.items():assert b'(locked yes)'in ch and K.A.G.parse(uid,ch,{})['net']==MON
  ident.assert_chunks(chunks);assert set(chunks).isdisjoint(native)
 packet=OUT/'MON4-controlled-detour-and-only-NEW-VREF-F-In3-B-protected-NOMINEE.pkl';packet.write_bytes(pickle.dumps({'tracks':nt,'vias':nv,'exact_new_chunks':chunks,'deleted_original_chunks':deleted,'selected':chosen},protocol=5));result={'verdict':'CONSTRUCTIVE_CONTROLLED_MON4_AND_ONLY_NEW_VREF_THREE_LEG_PROTECTED_NOMINEE'if chosen else'BOUNDED_MON4_AND_TWO_SG_THREE_LEG_SEARCH_INCOMPLETE','selected':chosen,'F_signal_sites':len(fs),'SG_pair_count':paircount,'attempts':len(attempts),'new_tracks':len(nt),'new_vias':len(nv),'max_new_VREF_layer_segments':3,'old_SOURCE_body_threshold_or_cap_waivers':0,'only_original_MON4_controlled_replaced':sorted(deleted),'SDI_5V_and_other_original_Cu_fixed':True,'packet_file':str(packet.resolve()),'packet_SHA256':sha(packet),'all_physical_source_old_ref_native_current_analog_SI_gates':'OPEN','native_jobs':0,'adopted':False,'input_SHA256':pins,'elapsed_seconds':time.monotonic()-st};put('receipt.json',result);print(json.dumps({k:result[k]for k in('verdict','F_signal_sites','SG_pair_count','attempts','new_tracks','new_vias','selected','elapsed_seconds')}),flush=True)
if __name__=='__main__':main()
