"""Replace absent DI6 withdrawal with a direct ordinary source escape.

Keeps every current FAULT item exact. Continuous physical regions nominate
sites; full independent fill/contact/reference/native gates remain required.
"""
import sys,pickle,json,math,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import contact_layout as L
import tri_route as T
import audit_aux_exact_raw as A
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.affinity import translate
P,G,S,C,N=A.P,A.G,A.S,A.C,A.N
NET='/motherboard_di/DI6_LOGIC';GND='/LOGIC_GND';FAULT='/motherboard_io_control/DI_SENSOR_G2_FAULT';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def pieces(sh):return [sh] if sh.geom_type=='Polygon' else [q for q in getattr(sh,'geoms',[]) if q.geom_type=='Polygon']
def sites(region,desired,limit=20):
 rows=[]
 for p in pieces(region):
  if p.area<1e-9:continue
  r=p.representative_point();n=nearest_points(p,Point(desired))[0]
  for q in (r,n,Point((r.x+n.x)/2,(r.y+n.y)/2)):
   at=[round(q.x,6),round(q.y,6)]
   if region.covers(Point(at)) and all(math.dist(at,z['at_mm'])>.025 for z in rows):rows.append({'at_mm':at,'region_area_mm2':p.area,'cost_mm':math.dist(at,desired)})
 return sorted(rows,key=lambda q:q['cost_mm'])[:limit]
def main():
 started=time.monotonic();out=HERE/'di6-direct-source-escape-r5.json';assert not out.exists();cache=pickle.loads(A.read(HERE/'di6-fault-local-components-r3.pkl'));h=cache['h'];restored=set(cache['parsed_restored']);h={**h,'tracks':[t for t in h['tracks'] if t['uuid'] not in restored],'vias':[v for v in h['vias'] if v['uuid'] not in restored]};source=A.read(Path(cache['source_parent']));identity=N.SourceNets(source);q=cache['blocker'];h['tracks']=h['tracks']+[{'uuid':q['uuid'],'net':identity.raw(q['net']),'layer':q['layer'],'a':q['a'],'b':q['b'],'w':q['w']}]
 r9=HERE.parent/'protected24-on-corrected-core-r9';z9=pickle.loads(A.read(r9/'proposed-zones.pkl'));d9=pickle.loads(A.read(r9/'proposed-discrete.pkl'));assert C.sha(A.read(r9/'proposed-zones.pkl'))=='e88d9750d99e46cb875925a338e4901e5085f5cf84a239d459d01053d57aeb16';assert C.sha(A.read(r9/'proposed-discrete.pkl'))=='005a19f7e01d9208f01e2677eefb3de9c2d34994037fd97e3f78340b6ff82a8c'
 for k in ('tracks','vias'):
  ids={v['uuid']:v for v in h[k]}
  for v in d9[k]:
   if v['uuid'] not in ids:h[k].append(v)
   else:assert ids[v['uuid']]==v
 rec={l:[r for r in cache['records'][l] if r['uuid'] not in restored] for l in LAYERS};rec[q['layer']].append({'uuid':q['uuid'],'net':q['net'],'layer':q['layer'],'kind':'track','shape':A.shape(q)})
 for z in z9:rec[z['layer']].append({'uuid':z['uuid'],'net':L.norm(z['net']),'layer':z['layer'],'kind':'fill','shape':z['shape'],'prospective':True})
 for k in ('tracks','vias'):
  oldids={v['uuid'] for v in cache['h'][k]}
  for v in d9[k]:
   if v['uuid'] in oldids:continue
   for l in v['flashed'] if k=='vias' else[v['layer']]:rec[l].append({'uuid':v['uuid'],'net':L.norm(v['net']),'layer':l,'kind':k[:-1],'shape':Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128) if k=='vias' else A.shape({'kind':'segment',**v})})
 win=box(108,92,125,123);domain=h['domains_normalized'];holes=[r for r in cache['holes'] if r['uuid'] not in restored];hard=cache['hard'];start=[119.136,97.3745];end=[113.95,119.35];free={};via={}
 for net in (NET,GND):
  for l in LAYERS:
   ob=[]
   for r in rec[l]:
    if r['net']==net:continue
    gap=.15 if domain.get(net)==domain.get(r['net']) else .6
    if r['kind']=='fill' and not r.get('prospective',False) and gap==.15:continue
    ob.append(r['shape'].buffer(gap+.025+.005,quad_segs=128))
   for r in holes:
    if r['net']!=net:ob.append(r['shape'].buffer(.275+.005,quad_segs=128))
   for r in hard[l]:
    if net not in r['exempt']:ob.append(r['shape'].buffer(.025,quad_segs=128))
   bodyfree=win.difference(unary_union(ob));free[net,l]=bodyfree.buffer(-.105)
  # Every ordinary annulus/drill is screened on all six copper layers.
  areas=[]
  for l in LAYERS:
   ob=[]
   for r in rec[l]:
    if r['net']==net or(r['kind']=='fill' and not r.get('prospective',False) and domain.get(r['net'])==domain.get(net)):continue
    gap=.15 if domain.get(r['net'])==domain.get(net) else .6;ob.append(r['shape'].buffer(.25+gap+.025+.005,quad_segs=128))
   for r in hard[l]:
    if net not in r['exempt']:ob.append(r['shape'].buffer(.275,quad_segs=128))
   areas.append(win.difference(unary_union(ob)))
  r=areas[0]
  for p in areas[1:]:r=r.intersection(p)
  ob=[Point(v['x'],v['y']).buffer(.81,quad_segs=128) for v in h['vias'] if Point(v['x'],v['y']).distance(win)<2]
  ob += [z['shape'].buffer(.1+.275+.005,quad_segs=128) for z in holes]
  ob += [sh.buffer(.1+.275+.005,quad_segs=128) for p in h['pads'] if p['smd'] for l,rs in p['layers'].items() if l in('F.Cu','B.Cu') for sh in L.poly(rs) if sh.distance(win)<2]
  via[net]=r.difference(unary_union(ob))
 fs=[p for p in pieces(free[NET,'F.Cu']) if p.covers(Point(start))];ins=[p for p in pieces(free[NET,'In3.Cu']) if p.covers(Point(end))];region=via[NET].intersection(unary_union(fs)).intersection(unary_union(ins)).intersection(Point(start).buffer(5,quad_segs=128));regionfile=HERE/'di6-direct-ordinary-sites-r5.wkb';regionfile.write_bytes(region.wkb)
 # Rooted cached native planes are nomination only; exact latest cuts and
 # physical root/contact rebuild are mandatory in the independent audit.
 refs=h['_rooted_refs'];returnregion=via[GND].intersection(refs['In1.Cu']).intersection(refs['In4.Cu']);options=[]
 for s in sites(region,[119.1,98.4],60):
  ss=Point(s['at_mm']);ring=ss.buffer(1,quad_segs=128).difference(ss.buffer(.825,quad_segs=128));ret=sites(returnregion.intersection(ring),[s['at_mm'][0]+.9,s['at_mm'][1]],8)
  if ret:options.append({**s,'returns':ret})
 print('DI6_DIRECT_CONTINUOUS_REGIONS',len(fs),len(ins),region.area,'pairs',len(options),flush=True);attempts=[]
 for s in options[:12]:
  for ret in s['returns'][:3]:
   at=s['at_mm'];rt=ret['at_mm'];rbody=Point(rt).buffer(.25+.175+.1+.005,quad_segs=128);own=Point(at).buffer(.25+.275,quad_segs=128);attempt={'signal':at,'return':rt,'paths':[]};attempts.append(attempt)
   for l,a,b in [('F.Cu',start,at),('In3.Cu',at,end)]:
    # No stale-cache healing credit. Candidate physical source reference is
    # recomputed after all final cuts in a separate audit before acceptance.
    ff=free[NET,l].difference(rbody);pp=[p for p in pieces(ff) if p.covers(Point(a)) and p.covers(Point(b))]
    if not pp:break
    pts,search=T.route(pp[0],tuple(a),tuple(b));pts=[[round(x,6),round(y,6)] for x,y in pts];attempt['paths'].append({'layer':l,'points_mm':pts,'width_mm':.2,'length_mm':LineString(pts).length,'search':search})
   if len(attempt['paths'])==2:
    print('DI6_DIRECT_PHYSICAL_RECIPE',json.dumps(attempt),flush=True);break
  if attempts and len(attempts[-1]['paths'])==2:break
 result={'verdict':'PHYSICAL_ORDINARY_DI6_REPLACEMENT_NOMINATED_ALL_REFERENCE_CONTACT_NATIVE_OPEN' if attempts and len(attempts[-1]['paths'])==2 else'CONTINUOUS_DI6_SITE_OR_PATH_NOMINATION_INCOMPLETE','source_parent_sha256':C.sha(source),'parent_model_sha256':C.sha(A.read(HERE.parent/'sbc-power/remaining-core-accepted-checkpoints-r50/stage-10/accepted-checkpoint-model.pkl')),'root9_hard_zones_sha256':C.sha(A.read(r9/'proposed-zones.pkl')),'root9_hard_discrete_sha256':C.sha(A.read(r9/'proposed-discrete.pkl')),'all_current_fault_Cu_preserved':True,'withdrawn_original_DI6_UUIDs_not_blindly_restored':sorted(restored|{'583bf99d-e1f6-45d5-a5cc-692686cd56e9'}),'original_drill_conflict_preserved':True,'actual_source_pad':{'ref':'U13001','pin':'12','uuid':'8cb51ce7-ffcc-432a-90f1-6f2c2e13b06f','F_mm':start,'raw_net':identity.raw(NET)},'actual_existing_target_via':{'uuid':'0ff4e506-7bc1-48ad-91fd-aeb598e74c7a','at_mm':end,'raw_net':identity.raw(NET)},'continuous_ordinary_signal_region_area_mm2':region.area,'continuous_region_WKB_sha256':C.sha(region.wkb),'signal_sites_with_nominal_rooted_return':options,'attempts':attempts,'reference_not_qualified_from_cached_planes':True,'native_jobs':0,'board_written':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started}
 out.write_text(json.dumps(result,indent=1)+'\n');print('DI6_DIRECT_RECEIPT',C.sha(out.read_bytes()),flush=True)
if __name__=='__main__':main()
