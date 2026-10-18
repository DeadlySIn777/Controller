"""Targeted existing C11076 relocation; preserve support graph and owned contacts."""
import copy,json,pickle,hashlib,time,math,re
from collections import defaultdict
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import affinity
from contact_layout import HERE,BASE,BOARD,load,build,norm,poly,body,O,S,contacts,identity,footprint_shape
from inventory import sha
from owned_pad_cuts import partitions
from verify_source import parse,atom,children,child
OUT=HERE/'local-bypass-move-r2'
def main():
 if OUT.exists():raise ValueError('Refuse immutable bypass proposal')
 OUT.mkdir();g,b=load();bind=json.loads((HERE/'owned-pad-cuts-r1/geometry-binding.json').read_text(encoding='utf-8'));raw=(HERE/'owned-pad-cuts-r1/prospective-geometry.pkl').read_bytes();assert hashlib.sha256(raw).hexdigest()==bind['model_sha256'];h=pickle.loads(raw)
 oldf,court=footprint_shape(g,'C11076');oldps=[p for p in g['pads'] if p['ref']=='C11076'];C='C11076';B5='/motherboard_safety_sensor/FIELD_B_5V_PRE';GND='/motherboard_do/FIELD_B_0V';rec,trees=build(h,layers={'F.Cu','B.Cu'})
 courts=[q for f in g['footprints'] if f['ref']!=C for ps in f['courtyard'].values() for q in poly(ps)];ct=STRtree(courts);hard=defaultdict(list)
 for a in g['rule_areas']:
  if a.get('no_footprints') or a.get('no_pads'):
   for l in a['layers']:hard[l].extend(poly(a['outline']))
 outline=unary_union(poly(g['outline'])).buffer(-.5)
 def moved_shape(sh,xy,rot):return affinity.translate(affinity.rotate(sh,-rot,origin=(oldf['x'],oldf['y'])),xy[0]-oldf['x'],xy[1]-oldf['y'])
 def moved_point(pt,xy,rot):
  a=math.radians(-rot);dx,dy=pt[0]-oldf['x'],pt[1]-oldf['y'];return (xy[0]+dx*math.cos(a)-dy*math.sin(a),xy[1]+dx*math.sin(a)+dy*math.cos(a))
 def placed(xy,rot):
  c=moved_shape(court,xy,rot)
  if not outline.covers(c) or any(c.intersects(courts[i]) for i in ct.query(c,predicate='intersects')) or any(c.intersects(q) for q in hard['F.Cu']):return None
  ps=[]
  for p in [p for p in h['pads'] if p['ref']==C]:
   q=copy.deepcopy(p);q['x'],q['y']=moved_point((p['x'],p['y']),xy,rot)
   for l,s in q['layers'].items():
    shapes=moved_shape(unary_union(poly(s)),xy,rot)
    for i in trees[l].query(shapes.buffer(.625),predicate='intersects'):
     r=rec[l][i]
     if r['uuid']==p['uuid'] or r['kind']=='fill' or norm(r['net'])==norm(q['net']):continue
     if shapes.distance(r['shape'])<(.15 if r['domain']=='DOM_FIELD_B' else .6)+.025:return None
    q.setdefault('placed_shapes',{})[l]=shapes
   ps.append(q)
  return ps
 u=[p for p in h['pads'] if p['ref']=='U11018'];ut={p['num']:p for p in u};found=[];legal=0;window=box(118,128,143,153)
 original_pin={p['num']:p for p in oldps}
 def metric(v):
  xy,rot=v;p1=moved_point((original_pin['1']['x'],original_pin['1']['y']),xy,rot);p2=moved_point((original_pin['2']['x'],original_pin['2']['y']),xy,rot)
  return math.dist(p1,(ut['8']['x'],ut['8']['y']))+math.dist(p2,(ut['9']['x'],ut['9']['y']))
 candidates=sorted([((129.44+ix*.5,139+iy*.5),rot) for ix in range(-18,19) for iy in range(-18,19) for rot in [0,90,180,270]],key=metric)
 for xy,rot in candidates:
  ps=placed(xy,rot)
  if ps is None:continue
  legal+=1;cp={p['num']:p for p in ps};added=[];rows=[]
  def free(net,w):
   obs=[];void=[]
   for i in trees['F.Cu'].query(window.buffer(2),predicate='intersects'):
    r=rec['F.Cu'][i]
    if r['uuid'] in {p['uuid'] for p in ps} or norm(r['net'])==net:continue
    if r['kind']=='fill':void.append(identity(r));continue
    obs.append(r['shape'].buffer((.15 if r['domain']=='DOM_FIELD_B' else .6)+w/2+.025))
   for p in ps:
    if norm(p['net'])!=net:obs.append(p['placed_shapes']['F.Cu'].buffer(.15+w/2+.025))
   for r in added:
    if r['net']!=net:obs.append(r['shape'].buffer(.15+w/2+.025))
   for p in h['pads']:
    for q in poly(p.get('hole') or []):
     if q.intersects(window):obs.append(q.buffer(.25+w/2+.025))
   for a in h['rule_areas']:
    if a.get('no_tracks') and 'F.Cu' in a['layers']:obs.extend(q.buffer(w/2+.025) for q in poly(a['outline']))
   return window.difference(unary_union(obs)),void
  for pin,to,net,w in [('1','8',B5,.35),('1','5',B5,.35),('2','9',GND,.35)]:
   a,bp=cp[pin],ut[to];fr,voids=free(net,w);path,search=S.astar(fr.buffer(-.00001),[((a['x'],a['y']),{'uuid':a['uuid'],'kind':'pad','ref':C,'pin':pin})],[((bp['x'],bp['y']),{'uuid':bp['uuid'],'kind':'pad','ref':'U11018','pin':to})],time.monotonic()+1,node_cap=16000)
   if path and not fr.covers(LineString(path['points_mm'])):path=None
   row={'from':C+'.'+pin,'to':'U11018.'+to,'net':net,'width_mm':w,'search':search,'verdict':'HOST_PATH' if path else 'NO_LOCAL_PATH'}
   if path:row.update(path=path,mandatory_fill_voids=voids);added.append({'net':net,'shape':LineString(path['points_mm']).buffer(w/2)})
   rows.append(row)
   if not path:break
  found.append({'pose_mm':xy,'rotation_deg':rot,'geometric_loop_minimum_mm':metric((xy,rot)),'paths':rows,'all_local_paths_found':len(rows)==3 and all(r['verdict']=='HOST_PATH' for r in rows)})
  if found[-1]['all_local_paths_found']:break
  if legal>=80:break
 result={'board_sha256':g['sha256'],'source_export_unchanged':True,'source_delta_unchanged_exact14plus4':True,'cap_ref':C,'original_pose_mm':[oldf['x'],oldf['y']],'orientation_optimized':True,'legal_placements_tested':legal,'candidates':found,'original_pad_support_contacts':{},'native_jobs':0,'board_written':False,'new_components':0,'all_source_and_return_qualified':False}
 records,t=build(g,nets={norm(p['net']) for p in oldps})
 for p in oldps:result['original_pad_support_contacts'][p['num']]={l:contacts(records,t,unary_union(poly(sh)),l,omit=p['uuid']) for l,sh in p['layers'].items()}
 if found and found[-1]['all_local_paths_found']:
  xy=found[-1]['pose_mm'];rot=found[-1]['rotation_deg'];moved=copy.deepcopy(h)
  for p in moved['pads']:
   if p['ref']!=C:continue
   p['x'],p['y']=moved_point((p['x'],p['y']),xy,rot)
   for l,ps in p['layers'].items():
    for polygon in ps:
     for ring in [polygon[0]]+polygon[1]:
      for pt in ring:pt[:]=moved_point(pt,xy,rot)
  # Projecting the physically moved cap pad proves the retained old support
  # network is unchanged; its new source/return membership is a separate gate.
  net=GND;before=partitions(h,net);after=partitions(moved,net);excluded={(C,'2')}
  proj=lambda gs:{frozenset(p for p in gr if p not in excluded) for gr in gs}- {frozenset()}
  expect,actual=proj(before),proj(after);result['retained_support_graph_gate']='PASS' if expect==actual else 'FAIL';result['retained_support_graph']={'groups_before':len(expect),'groups_after':len(actual),'lost':[list(p) for gr in expect-actual for p in gr]}
  fp=next(ch for ch in O.C.inventory(BOARD.read_bytes())[3].values() if O.C.pcbtext.chunk_kind(ch)=='footprint' and S.overlay_tool.base.ref_of(ch)==C)
  text=fp.decode('utf-8');text,n=re.subn(r'\(at ([\d.eE+-]+) ([\d.eE+-]+)( [\d.eE+-]+)?\)',lambda m:'(at '+format(xy[0],'.10g')+' '+format(xy[1],'.10g')+' '+format(rot,'.10g')+')',text,count=1);assert n==1
  from stage_board_chunks import netpads
  native_raw={norm(p['net']):p['net'] for p in g['pads'] if p['net']};text=netpads(text,{'1':native_raw[B5]});(OUT/'C11076.footprint-chunk').write_bytes(text.encode('utf-8'));result['footprint_delta']={'old_sha256':hashlib.sha256(fp).hexdigest(),'new_sha256':sha(OUT/'C11076.footprint-chunk'),'new_path':str((OUT/'C11076.footprint-chunk').resolve()),'existing_pad_UUIDs_preserved':True,'only_object_changes':'Footprint position; C11076.1 exact native net reassignment already in frozen AB source ledger.'}
  raw=pickle.dumps(moved,protocol=5);(OUT/'prospective-geometry.pkl').write_bytes(raw);result['prospective_geometry_sha256']=hashlib.sha256(raw).hexdigest()
 (OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print(json.dumps({'legal_placements_tested':legal,'complete_local_bypass':bool(found and found[-1]['all_local_paths_found']),'pose':found[-1]['pose_mm'] if found else None,'retained_support_graph_gate':result.get('retained_support_graph_gate')}))
if __name__=='__main__':main()
