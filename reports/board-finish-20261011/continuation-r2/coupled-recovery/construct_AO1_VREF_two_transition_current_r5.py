"""Reuse exact current regions for a bounded F/In3/B VREF connection."""
from pathlib import Path
import sys,json,pickle,hashlib,time,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import audit_ao1_positive_operation_r4 as SERIAL
import tri_route as T
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
OUT=H/'AO1-VREF-two-NEW-transitions-current-F-In3-B-constructor-r5'
VREF='/motherboard_analog_output/AO1_VREF';COM='/motherboard_analog_output/AO1_COM'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,o):(OUT/n).write_text(json.dumps(o,indent=1,allow_nan=False)+'\n')
def parts(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for g in s.geoms for p in parts(g)]if hasattr(s,'geoms')else[]
def info(s):return{'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def sites(s,desired,limit=72):
 rows=[]
 for p in parts(s):
  a=p.representative_point();b=nearest_points(p,Point(desired))[0]
  for q in(a,b,Point((a.x+b.x)/2,(a.y+b.y)/2)):
   at=[round(q.x,6),round(q.y,6)]
   if p.covers(Point(at))and all(math.dist(at,z)>.015 for z in rows):rows.append(at)
 return sorted(rows,key=lambda p:math.dist(p,desired))[:limit]
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 rp=pin(H/'AO1-VREF-ONLY-NEW-native-intent-current-port-constructor-r4/receipt.json');r=json.loads(rp.read_bytes());cp=pin(rp.parent/'exact-current-Cu-continuous-source-only-regions.pkl',r['region_cache_SHA256']);data=pickle.loads(cp.read_bytes());source=data['source_refs'];free=data['free'];vr=data['viaregions'];sf=data['sourcefree'];ep=[375.498,129.0];returns=data['returnregion'];icom=free[VREF,'In3.Cu'].intersection(source['In4.Cu'].buffer(-.100005));ports={};endpointcomponents={}
 for ly in('F.Cu','B.Cu'):
  cc=[p for p in parts(sf[ly])if p.covers(Point(ep))];endpointcomponents[ly]=cc;ports[ly]=vr[VREF].intersection(unary_union(cc)).intersection(icom);(OUT/(ly.replace('.','-')+'-new-SG-port-region.wkb')).write_bytes(ports[ly].wkb)
 put('continuous-ports-and-endpoint-components.json',{'ports':{l:info(s)for l,s in ports.items()},'endpoint_components':{l:[info(s)for s in ps]for l,ps in endpointcomponents.items()},'ordinary_return_region':info(returns),'In3_SOURCE_reference_free':info(icom)})
 beforecache=pin(H/'AO1-saved-four-add-exact-current-native-screen-r1/pinned-current-local-Cu-native-before-source-only-screen.pkl','0349ddad81a9dc6dd0ef106c3a65ce03e0ff44ae3d04244e882bbe0475590a2e');context=pickle.loads(beforecache.read_bytes());local=context['current'];put('local-near-endpoint-original-native-pads.json',[{k:p[k]for k in('uuid','ref','num','net','x','y','smd')}for p in local['pads']if Point(p['x'],p['y']).distance(Point(ep))<4])
 ats={ly:sites(p,[376.6,129.0],144)for ly,p in ports.items()};attempts=[];selected=None
 pairs=sorted(((a,b)for a in ats['F.Cu']for b in ats['B.Cu']if math.dist(a,b)>=.815),key=lambda q:math.dist(*q))[:512]
 def retpoints(a):
  ring=Point(a).buffer(.999,quad_segs=128).difference(Point(a).buffer(.901,quad_segs=128));return sites(returns.intersection(ring),[a[0],a[1]+.95],12)
 for a,b in pairs:
  for ra in retpoints(a):
   for rb in retpoints(b):
    if min(math.dist(a,rb),math.dist(b,ra),math.dist(ra,rb))<.815:continue
    if not .90<=math.dist(a,ra)<=1 or not .90<=math.dist(b,rb)<=1:continue
    ob=unary_union([K.Z.bounded_buffer(Point(q),.625010)for q in(ra,rb)]);paths=[];attempt={'F_SG_mm':a,'B_SG_mm':b,'F_RETURN_mm':ra,'B_RETURN_mm':rb,'paths':paths};attempts.append(attempt)
    for ly,start,end,fr in(('F.Cu',ep,a,sf['F.Cu']),('In3.Cu',a,b,icom),('B.Cu',b,ep,sf['B.Cu'])):
     ff=fr.difference(ob);cc=[p for p in parts(ff)if p.covers(Point(start))and p.covers(Point(end))]
     if not cc:break
     pts,search=T.route(cc[0],start,end);pts=[[round(x,6),round(y,6)]for x,y in pts]
     if len(pts)<2 or not cc[0].covers(LineString(pts)):break
     paths.append({'layer':ly,'points_mm':pts,'width_mm':.2,'search':search,'length_mm':LineString(pts).length})
    if len(paths)==3:selected=attempt;break
   if selected:break
  if selected:break
 put('bounded-current-three-leg-port-route-attempts.json',attempts);nt=[];nv=[];chunks={};sp=pin(ROOT/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb','7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2');ident=K.A.N.SourceNets(sp.read_bytes());native=K.C.inventory(sp.read_bytes())[3]
 if selected:
  for path in selected['paths']:
   for a,b in zip(path['points_mm'],path['points_mm'][1:]):
    uid,ch=ident.serial_segment(VREF,path['layer'],a,b,.2);chunks[uid]=ch;nt.append({'uuid':uid,'net':ident.raw(VREF),'layer':path['layer'],'a':a,'b':b,'w':.2})
  for net,at in((VREF,selected['F_SG_mm']),(VREF,selected['B_SG_mm']),(COM,selected['F_RETURN_mm']),(COM,selected['B_RETURN_mm'])):
   uid,ch=SERIAL.serial_via(ident,net,at);chunks[uid]=ch;nv.append({'uuid':uid,'net':ident.raw(net),'x':at[0],'y':at[1],'d':.5,'drill':.2,'flashed':list(K.LAYERS)})
  ident.assert_chunks(chunks);assert set(chunks).isdisjoint(native)
 packet=OUT/'ONLY_NEW-VREF-three-layer-segments-two-signal-two-ordinary-returns-NOMINEE.pkl';packet.write_bytes(pickle.dumps({'tracks':nt,'vias':nv,'exact_new_chunks':chunks,'deleted_original_chunks':{},'selected':selected},protocol=5));result={'verdict':'CONSTRUCTIVE_ONLY_NEW_VREF_F_In3_B_HOST_NOMINEE_ALL_REQUALIFICATION_OPEN'if selected else'BOUNDED_ONLY_NEW_TWO_TRANSITION_SEARCH_NO_COMPLETE_CURRENT_ROUTE','port_summary':{l:info(s)for l,s in ports.items()},'port_site_counts':{l:len(ps)for l,ps in ats.items()},'pair_count':len(pairs),'attempts':len(attempts),'selected':selected,'tracks':len(nt),'vias':len(nv),'packet_file':str(packet.resolve()),'packet_SHA256':sha(packet),'layer_segments':3 if selected else None,'all_original_DAC_SDI_MON_Cu_exact':True,'original_deletes_or_moves':0,'source_current_full_native_ref_SI_gates':'OPEN','native_jobs':0,'adopted':False,'input_SHA256':pins,'elapsed_seconds':time.monotonic()-st};put('receipt.json',result);print(json.dumps({k:result[k]for k in('verdict','port_site_counts','pair_count','attempts','selected','elapsed_seconds')}),flush=True)
if __name__=='__main__':main()
