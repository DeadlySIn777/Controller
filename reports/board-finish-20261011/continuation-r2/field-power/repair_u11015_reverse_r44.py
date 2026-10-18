"""Close actual remaining field grounds with curved ordinary dogbones.

Each new barrel must overlap already source-rooted inner Cu. All hole/SMD
guards are exact and dynamic; no isolated cached fill is a landing goal.
"""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,math,uuid,re
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from shapely import set_precision,get_num_coordinates
from inventory import sha
import contact_layout as C
import fast_contacts as F
import tri_route as T
HERE=Path(__file__).resolve().parent;OUT=HERE/'u11015-reverse-companion-repair-r44'
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def polys(s):return[s] if s.geom_type=='Polygon' else[q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();bp=HERE/'local-and-b5-return-audit-r25';br=json.loads((bp/'receipt.json').read_text());assert br['verdict']=='PASS_RETAINED_CONTACTS_AND_ORDINARY_APERTURES_CURRENT_NATIVE_PENDING';assert sha(bp/'geometry.pkl')==br['geometry_sha256'];g=pickle.loads((bp/'geometry.pkl').read_bytes());assert sha(bp/'proposed-zones.pkl')==br['proposed_zones_sha256'];planes=pickle.loads((bp/'proposed-zones.pkl').read_bytes());prior=HERE/'u11015-ilim-wall-repair-r24';pr=json.loads((prior/'receipt.json').read_text());dvscope=json.loads((HERE/'u11015-dvdt-scope-r30/receipt.json').read_text());dvold=dvscope['tracks'];assert len(dvold)==2;owned=pr['owned_original_track_removals']+dvold;removed={q['uuid'] for q in owned};assert len(removed)==6;outside=pr['exact_outside_contact_ledger'][:];dr0,_=F.build(g,nets={'/motherboard_power_entry/AUX24_A_DVDT'})
 for t in dvold:
  sh=C.body(t);outside.append({'removed_original_track':t,'retained_same_raw_net_outside_contacts':[C.identity(q)|{'contact_Cu_area_mm2':sh.intersection(q['shape']).area} for q in dr0['B.Cu'] if q['uuid'] not in removed and sh.intersection(q['shape']).area>1e-9]})
 assert {q['uuid'] for row in outside[4:] for q in row['retained_same_raw_net_outside_contacts']}=={'71b4e700-5181-4c1e-87f6-5cb0b5998511','53303a9a-a99f-4da1-a500-5af3783fa537'}
 for t in owned:assert next(q for q in g['tracks'] if q['uuid']==t['uuid'])==t
 g={**g,'tracks':[t for t in g['tracks'] if t['uuid'] not in removed]};seedpath=HERE/'u11015-three-net-inner-ILIM-repair-r32';seedr=json.loads((seedpath/'receipt.json').read_text());assert sha(seedpath/'proposed-discrete.pkl')==seedr['proposed_discrete_sha256'];seed=pickle.loads((seedpath/'proposed-discrete.pkl').read_bytes());fixed_vias=[q for q in seed['vias'] if q['net']=='/motherboard_power_entry/AUX24_A_ILIM'];fixed_tracks=[q for q in seed['tracks'] if q['net']=='/motherboard_power_entry/AUX24_A_ILIM'];assert len(fixed_vias)==2 and len(fixed_tracks)==3
 for t in fixed_tracks:
  if t['layer']=='B.Cu':
   source_pin=('U11015','7') if t['uuid']=='64d60863-d80a-5e18-87f4-2c6c1881d62c' else ('R11056','1');p0=next(q for q in g['pads'] if(q['ref'],q['num'])==source_pin);sh=unary_union(C.poly(p0['layers']['B.Cu']));v=min(fixed_vias,key=lambda v:Point(v['x'],v['y']).distance(sh));t['a']=[round(sh.centroid.x,6),round(sh.centroid.y,6)];t['b']=[v['x'],v['y']]
 g={**g,'tracks':g['tracks']+fixed_tracks,'vias':g['vias']+fixed_vias};rec,trees=F.build({**g,'zones':[]});outline=unary_union(C.poly(g['outline'])).buffer(-.526);res=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text();exceptions={}
 for line in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 ilim='/motherboard_power_entry/AUX24_A_ILIM';ip0=next(q for q in rec['B.Cu'] if q['kind']=='pad' and(q['ref'],q['pin'])==('U11015','7'));ip1=next(q for q in rec['B.Cu'] if q['kind']=='pad' and(q['ref'],q['pin'])==('R11056','1'));iraw=ip0['net'];assert iraw==ip1['net'];idom=g['domains_normalized'][ilim]
 def igap(other):return .15 if g['domains_normalized'].get(C.norm(other))==idom else .6
 io=[q['shape'].buffer(igap(q['net'])+.025) for q in rec['B.Cu'] if C.norm(q['net'])!=ilim]+[q['shape'].buffer(igap(q['net'])+.025) for q in planes if q['layer']=='B.Cu' and C.norm(q['net'])!=ilim]
 for rule in g['rule_areas']:
  if rule.get('no_tracks') and 'B.Cu' in rule['layers']:io.extend([s.buffer(.025) for s in C.poly(rule['outline'])])
 for rule in res['keepouts']:
  if ilim not in exceptions.get(rule['name'],set()) and 'B.Cu' in rule['layers']:io.extend([s.buffer(.025) for s in C.poly(rule['outline'])])
 it=STRtree(io)
 def restore_ilim(groundbody,disk):
  a,b=nearest_points(ip0['shape'],ip1['shape']);width=.2
  for margin in(3.,8.,16.):
   win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);ii=it.query(win,predicate='intersects');legal=win.difference(unary_union([io[int(j)] for j in ii]+[groundbody.buffer(.175),disk.buffer(.175)]));options=[]
   for part in polys(legal.buffer(-width/2-.005)):
    aa=part.buffer(-.00002).intersection(ip0['shape'].buffer(width/2-.025));bb=part.buffer(-.00002).intersection(ip1['shape'].buffer(width/2-.025))
    if not aa.is_empty and not bb.is_empty:options.append((aa.distance(bb),part,aa,bb))
   if not options:continue
   _,part,aa,bb=min(options,key=lambda q:q[0]);start,end=nearest_points(aa,bb)
   try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
   except(AssertionError,ValueError):continue
   pts=[[round(x,6),round(y,6)] for x,y in points]
   if len(set(tuple(p) for p in pts))<2:continue
   line=LineString(pts);body=line.buffer(width/2,quad_segs=32)
   if not legal.buffer(.000001).covers(body) or body.intersection(ip0['shape']).area<.001 or body.intersection(ip1['shape']).area<.001:continue
   return{'points':pts,'length_mm':line.length,'width_mm':width,'search':search,'body':body}
  return None
 dnet='/motherboard_power_entry/AUX24_A_DVDT';dp0=next(q for q in rec['B.Cu'] if q['kind']=='pad' and(q['ref'],q['pin'])==('U11015','8'));dp1=next(q for q in rec['B.Cu'] if q['kind']=='pad' and(q['ref'],q['pin'])==('C11068','1'));draw=dp0['net'];assert draw==dp1['net'];do=[q['shape'].buffer(igap(q['net'])+.025) for q in rec['B.Cu'] if C.norm(q['net'])!=dnet]+[q['shape'].buffer(igap(q['net'])+.025) for q in planes if q['layer']=='B.Cu' and C.norm(q['net'])!=dnet]
 for rule in g['rule_areas']:
  if rule.get('no_tracks') and 'B.Cu' in rule['layers']:do.extend([s.buffer(.025) for s in C.poly(rule['outline'])])
 for rule in res['keepouts']:
  if dnet not in exceptions.get(rule['name'],set()) and 'B.Cu' in rule['layers']:do.extend([s.buffer(.025) for s in C.poly(rule['outline'])])
 dt=STRtree(do)
 def restore_dvdt(groundbody,disk,ilimbody):
  a,b=nearest_points(dp0['shape'],dp1['shape']);width=.2
  for margin in(3.,8.,16.):
   win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);ii=dt.query(win,predicate='intersects');legal=win.difference(unary_union([do[int(j)] for j in ii]+[groundbody.buffer(.175),disk.buffer(.175),ilimbody.buffer(.175)]));options=[]
   for part in polys(legal.buffer(-width/2-.005)):
    aa=part.buffer(-.00002).intersection(dp0['shape'].buffer(width/2-.025));bb=part.buffer(-.00002).intersection(dp1['shape'].buffer(width/2-.025))
    if not aa.is_empty and not bb.is_empty:options.append((aa.distance(bb),part,aa,bb))
   if not options:continue
   _,part,aa,bb=min(options,key=lambda q:q[0]);start,end=nearest_points(aa,bb)
   try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
   except(AssertionError,ValueError):continue
   pts=[[round(x,6),round(y,6)] for x,y in points]
   if len(set(tuple(p) for p in pts))<2:continue
   line=LineString(pts);body=line.buffer(width/2,quad_segs=32)
   if not legal.buffer(.000001).covers(body) or body.intersection(dp0['shape']).area<.001 or body.intersection(dp1['shape']).area<.001:continue
   return{'points':pts,'length_mm':line.length,'width_mm':width,'search':search,'body':body}
  return None
 pending_signal_cu=[]
 def outer_ilim(src,dst,extras):
  a,b=nearest_points(src,dst);width=.2
  for margin in(3.,8.,16.):
   win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);ii=it.query(win,predicate='intersects');legal=win.difference(unary_union([io[int(j)] for j in ii]+extras));options=[]
   for part in polys(legal.buffer(-.105)):
    aa=part.buffer(-.00002).intersection(src.buffer(.075));bb=part.buffer(-.00002).intersection(dst.buffer(.075))
    if not aa.is_empty and not bb.is_empty:options.append((aa.distance(bb),part,aa,bb))
   if not options:continue
   _,part,aa,bb=min(options,key=lambda q:q[0]);a1,b1=nearest_points(aa,bb)
   try:points,search=T.route(part,tuple(a1.coords[0]),tuple(b1.coords[0]))
   except(AssertionError,ValueError):continue
   pts=[[round(x,6),round(y,6)] for x,y in points];a0=nearest_points(src,Point(pts[0]))[0];b0=nearest_points(dst,Point(pts[-1]))[0];pts[0]=[round(a0.x,6),round(a0.y,6)];pts[-1]=[round(b0.x,6),round(b0.y,6)]
   if len(set(tuple(p) for p in pts))<2:continue
   line=LineString(pts);body=line.buffer(.1,quad_segs=32)
   if legal.buffer(.000001).covers(body) and body.intersection(src).area>.001 and body.intersection(dst).area>.001:return {'points':pts,'body':body,'search':search,'length_mm':line.length}
  return None
 def ilim_dive(groundbody,grounddisk,groundhole):
  sources=[];destinations=[];extras=[groundbody.buffer(.175),grounddisk.buffer(.175)];inner_masks={};inner_trees={}
  for l in LAYERS[1:-1]:
   oo=[q['shape'].buffer(igap(q['net'])+.025) for q in rec[l] if C.norm(q['net'])!=ilim]+[q['shape'].buffer(igap(q['net'])+.025) for q in planes if q['layer']==l and C.norm(q['net'])!=ilim]
   for q in g['pads']:
    if not q['num'] or q['net']!=iraw:oo.extend([sh.buffer(.275) for sh in C.poly(q.get('hole') or [])])
   for v in g['vias']:
    if v['net']!=iraw:oo.append(Point(v['x'],v['y']).buffer(v['drill']/2+.275,quad_segs=32))
   oo.append(grounddisk.buffer(.175))
   for rule in g['rule_areas']:
    if rule.get('no_tracks') and l in rule['layers']:oo.extend([sh.buffer(.025) for sh in C.poly(rule['outline'])])
   for rule in res['keepouts']:
    if ilim not in exceptions.get(rule['name'],set()) and l in rule['layers']:oo.extend([sh.buffer(.025) for sh in C.poly(rule['outline'])])
   inner_masks[l]=oo;inner_trees[l]=STRtree(oo)
  def good_disk(xy):
   pt=Point(xy);disk=pt.buffer(.25,quad_segs=32);hole=pt.buffer(.1,quad_segs=64)
   if not outline.covers(disk) or disk.distance(grounddisk)<.175-1e-9 or disk.distance(groundbody)<.175-1e-9 or hole.distance(groundhole)<.275-1e-9:return None
   if any(pt.distance(smd[int(j)])-.1<.275-1e-9 for j in st.query(pt.buffer(.376),predicate='intersects')):return None
   if any(pt.distance(ph[int(j)])-.1<.275-1e-9 for j in ht.query(pt.buffer(.376),predicate='intersects')):return None
   if any(math.hypot(xy[0]-v['x'],xy[1]-v['y'])-(.2+v['drill'])/2<.275-1e-9 for v in g['vias']):return None
   for l in LAYERS:
    if any(C.norm(rec[l][int(j)]['net'])!=ilim and disk.distance(rec[l][int(j)]['shape'])<igap(rec[l][int(j)]['net'])+.025-1e-9 for j in trees[l].query(disk.buffer(.65),predicate='intersects')):return None
    if any(q['layer']==l and C.norm(q['net'])!=ilim and disk.distance(q['shape'])<igap(q['net'])+.025-1e-9 for q in planes):return None
    for rule in g['rule_areas']:
     if rule.get('no_vias') and l in rule['layers'] and any(disk.intersects(sh.buffer(.025)) for sh in C.poly(rule['outline'])):return None
    for rule in res['keepouts']:
     if ilim not in exceptions.get(rule['name'],set()) and l in rule['layers'] and any(disk.intersects(sh.buffer(.025)) for sh in C.poly(rule['outline'])):return None
   return disk,hole
  for pad,pool in[(ip0,sources),(ip1,destinations)]:
   anchor=pad['shape'].representative_point()
   for radius in(.75,.8,.9,1.2,1.6,2.2,3.,4.,5.):
    for step in range(16):
     xy=(round(anchor.x+radius*math.cos(step*math.pi/8),6),round(anchor.y+radius*math.sin(step*math.pi/8),6));ok=good_disk(xy)
     if ok is None:continue
     disk,hole=ok;rr=outer_ilim(pad['shape'],disk,extras)
     if rr:pool.append({'xy':xy,'disk':disk,'hole':hole,'outer':rr})
    if len(pool)>=12:break
   if not pool:return None
  for a in sources[:16]:
   for b in destinations[:24]:
    if a['hole'].distance(b['hole'])<.275-1e-9:continue
    ann0=a['disk'].difference(a['hole']);ann1=b['disk'].difference(b['hole']);aa0,bb0=nearest_points(ann0,ann1)
    for l in('In3.Cu','In2.Cu','In4.Cu','In1.Cu'):
     for margin in(3.,8.,16.):
      win=box(min(aa0.x,bb0.x)-margin,min(aa0.y,bb0.y)-margin,max(aa0.x,bb0.x)+margin,max(aa0.y,bb0.y)+margin).intersection(outline);ii=inner_trees[l].query(win,predicate='intersects');legal=win.difference(unary_union([inner_masks[l][int(j)] for j in ii]));options=[]
      for part in polys(legal.buffer(-.105)):
       aa=part.buffer(-.00002).intersection(ann0);bb=part.buffer(-.00002).intersection(ann1)
       if not aa.is_empty and not bb.is_empty:options.append((aa.distance(bb),part,aa,bb))
      if not options:continue
      _,part,aa,bb=min(options,key=lambda q:q[0]);a1,b1=nearest_points(aa,bb)
      try:points,search=T.route(part,tuple(a1.coords[0]),tuple(b1.coords[0]))
      except(AssertionError,ValueError):continue
      pts=[[round(x,6),round(y,6)] for x,y in points];line=LineString(pts);body=line.buffer(.1,quad_segs=32)
      if not legal.buffer(.000001).covers(body) or body.intersection(ann0).area<.001 or body.intersection(ann1).area<.001:continue
      seed=f'controller-U11015-ILIM-dive-r36/{a["xy"]}/{b["xy"]}/{l}';vs=[];ts=[];cc=[]
      for role,q in[('source',a),('destination',b)]:
       vid=str(uuid.uuid5(uuid.NAMESPACE_URL,seed+'/'+role));v={'uuid':vid,'net':iraw,'x':q['xy'][0],'y':q['xy'][1],'d':.5,'drill':.2,'flashed':LAYERS,'prospective_not_native':True};vs.append(v)
       for layer in LAYERS:cc.append({'uuid':vid+'@'+layer,'net':iraw,'layer':layer,'shape':q['disk']})
       for j,(p0,p1) in enumerate(zip(q['outer']['points'],q['outer']['points'][1:])):
        if p0!=p1:ts.append({'uuid':str(uuid.uuid5(uuid.UUID(vid),'outer'+str(j))),'net':iraw,'layer':'B.Cu','a':p0,'b':p1,'w':.2,'prospective_not_native':True})
      for j,(p0,p1) in enumerate(zip(pts,pts[1:])):
       if p0!=p1:ts.append({'uuid':str(uuid.uuid5(uuid.UUID(vs[0]['uuid']),'inner'+str(j))),'net':iraw,'layer':l,'a':p0,'b':p1,'w':.2,'prospective_not_native':True})
      for t in ts:cc.append({'uuid':t['uuid'],'net':iraw,'layer':t['layer'],'shape':C.body(t)})
      return {'points':[],'body':unary_union([q['shape'] for q in cc if q['layer']=='B.Cu']),'length_mm':sum(LineString([t['a'],t['b']]).length for t in ts),'inner_layer':l,'inner_points_mm':pts,'inner_length_mm':line.length,'width_mm':.2,'search':search,'extra_vias':vs,'extra_tracks':ts,'all_cu':cc,'native_flash_required':{'via_UUIDs':[v['uuid'] for v in vs],'layers':['B.Cu',l]}}
  return None
 smd=[unary_union(C.poly(rs)) for q in g['pads'] if q['smd'] for l,rs in q['layers'].items() if l in('F.Cu','B.Cu')];st=STRtree(smd);ph=[s for q in g['pads'] for s in C.poly(q.get('hole') or [])];ht=STRtree(ph);newvias=fixed_vias[:];newtracks=fixed_tracks[:];newcu=[];newzones=[];rows=[]
 for bank,net,rootref in[('FA','/motherboard_motors/FIELD_GND','J11003')]:
  groups=F.graph(g,net);root=next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],q['pin'])==(rootref,'2') for q in xs));raw=next(q['net'] for q in root if q['kind']=='pad');domain=g['domains_normalized'][net];source={l:unary_union([q['shape'] for q in root if q['layer']==l]) for l in LAYERS[1:-1]};obs={};ots={};foreign={l:[q for q in planes+newzones if q['layer']==l and C.norm(q['net'])!=net] for l in LAYERS};ft={l:STRtree([q['shape'] for q in foreign[l]]) for l in LAYERS}
  def gap(other):return .15 if g['domains_normalized'].get(C.norm(other))==domain else .6
  for l in('F.Cu','B.Cu'):
   oo=[q['shape'].buffer(gap(q['net'])+.025) for q in rec[l] if C.norm(q['net'])!=net]+[q['shape'].buffer(gap(q['net'])+.025) for q in foreign[l]]
   for rule in g['rule_areas']:
    if rule.get('no_tracks') and l in rule['layers']:oo.extend([s.buffer(.025) for s in C.poly(rule['outline'])])
   for rule in res['keepouts']:
    if net not in exceptions.get(rule['name'],set()) and l in rule['layers']:oo.extend([s.buffer(.025) for s in C.poly(rule['outline'])])
   obs[l]=oo;ots[l]=STRtree(oo)
  def routed(src,dst,layer,width):
   a,b=nearest_points(src,dst)
   for margin in(2.,5.,12.):
    win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);ii=ots[layer].query(win,predicate='intersects');legal=win.difference(unary_union([obs[layer][int(j)] for j in ii]+[q['shape'].buffer(gap(q['net'])+.025) for q in newcu if q['layer']==layer and C.norm(q['net'])!=net]));options=[]
    for part in polys(legal.buffer(-width/2-.005)):
     aa=part.buffer(-.00002).intersection(src.buffer(width/2-.025));bb=part.buffer(-.00002).intersection(dst.buffer(width/2-.025))
     if not aa.is_empty and not bb.is_empty:options.append((aa.distance(bb),part,aa,bb))
    if not options:continue
    _,part,aa,bb=min(options,key=lambda q:q[0]);start,end=nearest_points(aa,bb)
    try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
    except(AssertionError,ValueError):continue
    pts=[[round(x,6),round(y,6)] for x,y in points]
    if len(set(tuple(p) for p in pts))<2:continue
    line=LineString(pts);body=line.buffer(width/2,quad_segs=32)
    if not legal.buffer(.000001).covers(body) or body.intersection(src).area<.001 or body.intersection(dst).area<.001:continue
    return{'points':pts,'length_mm':line.length,'width_mm':width,'search':search,'body':body}
   return None
  innerobs={};innerTrees={}
  for l in LAYERS[1:-1]:
   oo=[q['shape'].buffer(gap(q['net'])+.025) for q in rec[l] if C.norm(q['net'])!=net]+[q['shape'].buffer(gap(q['net'])+.025) for q in foreign[l]]
   for p0 in g['pads']:
    if not p0['num'] or p0['net']!=raw:oo.extend([sh.buffer(.275) for sh in C.poly(p0.get('hole') or [])])
   for v0 in g['vias']:
    if v0['net']!=raw:oo.append(Point(v0['x'],v0['y']).buffer(v0['drill']/2+.275,quad_segs=32))
   for rule in g['rule_areas']:
    if rule.get('no_zones') and l in rule['layers']:oo.extend([sh.buffer(.025) for sh in C.poly(rule['outline'])])
   innerobs[l]=oo;innerTrees[l]=STRtree(oo)
  ownholes=unary_union([sh for p0 in g['pads'] if p0['num'] and p0['net']==raw for sh in C.poly(p0.get('hole') or [])]+[Point(v0['x'],v0['y']).buffer(v0['drill']/2,quad_segs=64) for v0 in g['vias'] if v0['net']==raw])
  def bridge(disk,hole):
   ann=disk.difference(hole);options=[]
   for l in('In1.Cu','In4.Cu','In2.Cu','In3.Cu'):
    if source[l].is_empty:continue
    if ann.intersection(source[l]).area>.025:return l,None,None,None
    a,b=nearest_points(ann,source[l]);options.append((a.distance(b),l,a,b))
   for dist,l,a,b in sorted(options,key=lambda q:q[0]):
    if dist>180:continue
    for margin in(8.,22.,45.):
     win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);ii=innerTrees[l].query(win,predicate='intersects');legal=win.difference(unary_union([innerobs[l][int(j)] for j in ii]+[q['shape'].buffer(gap(q['net'])+.025) for q in newzones+pending_signal_cu if q['layer']==l and C.norm(q['net'])!=net]));available=[]
     for width in(.5,.35):
      for part in polys(legal.buffer(-width/2-.005)):
       aa=part.buffer(-.00002).intersection(ann);bb=part.buffer(-.00002).intersection(source[l])
       if not aa.is_empty and not bb.is_empty:available.append((aa.distance(bb),part,aa,bb,width))
      if not available:continue
      _,part,aa,bb,width=min(available,key=lambda q:q[0]);start,end=nearest_points(aa,bb)
      if get_num_coordinates(part)>160000:
       smaller=part.buffer(-.015).simplify(.005,preserve_topology=True).intersection(part);pieces=[q for q in polys(smaller) if q.intersects(aa) and q.intersects(bb)]
       if not pieces:continue
       part=max(pieces,key=lambda q:q.area);start,end=nearest_points(part.buffer(-.00002).intersection(aa),part.buffer(-.00002).intersection(bb))
      try:pts,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
      except(AssertionError,ValueError):continue
      line=LineString(pts);core=line.buffer(width/2,quad_segs=32)
      if not legal.buffer(.000001).covers(core):continue
      nativeoutline=set_precision(unary_union([q for q in polys(line.buffer(.6,quad_segs=32).intersection(legal)) if q.intersection(core).area>1e-9]),1e-6);holes=unary_union([ownholes,hole]+[Point(v0['x'],v0['y']).buffer(v0['drill']/2,quad_segs=64) for v0 in newvias if v0['net']==raw]);effective=set_precision(nativeoutline.difference(holes),1e-6)
      if not legal.buffer(.000002).covers(effective) or not effective.buffer(.000002).covers(core.difference(holes)) or effective.intersection(ann).area<.01 or effective.intersection(source[l]).area<1e-8:continue
      return l,effective,nativeoutline,{'points_mm':pts,'length_mm':line.length,'minimum_core_width_mm':width,'source_rooted_Cu_overlap_mm2':effective.intersection(source[l]).area,'via_annular_Cu_overlap_mm2':effective.intersection(ann).area,'search':search,'sheet_only_R35um60C_ohm':.00057003672*line.length/width}
   return None,None,None,None
  wanted=[(i,xs) for i,xs in enumerate(groups) if xs is not root and any(q['kind']=='pad' and(q['ref'],q['pin'])==('U11015','6') for q in xs)];assert len(wanted)==1
  for gi,xs in wanted:
   result=None;attempts=0;annularCandidates=0
   for layer in('F.Cu','B.Cu'):
    pads=[q for q in xs if q['kind']=='pad' and q['layer']==layer];src=unary_union([q['shape'] for q in xs if q['kind']!='fill' and q['layer']==layer])
    if src.is_empty:continue
    for a in sorted(pads,key=lambda q:-q['shape'].area):
     anchor=a['shape'].representative_point()
     for dia,drill in((.5,.2),(.6,.3)):
      for radius in(.6,.75,.8,.9,1.2,1.6,2.2,3.,4.,5.,6.,8.,10.,12.):
       for step in range(32):
        xy=(round(anchor.x+radius*math.cos(step*math.pi/16),6),round(anchor.y+radius*math.sin(step*math.pi/16),6));pt=Point(xy);disk=pt.buffer(dia/2,quad_segs=32);hole=pt.buffer(drill/2,quad_segs=64);attempts+=1
        if not outline.covers(disk):continue
        if any(pt.distance(smd[int(j)])-drill/2<.275-1e-9 for j in st.query(pt.buffer(drill/2+.276),predicate='intersects')):continue
        if any(pt.distance(ph[int(j)])-drill/2<.275-1e-9 for j in ht.query(pt.buffer(drill/2+.276),predicate='intersects')):continue
        if any(math.hypot(xy[0]-v['x'],xy[1]-v['y'])-(drill+v['drill'])/2<.275-1e-9 for v in g['vias']+newvias):continue
        inner=None
        bad=False
        for l in LAYERS:
         if any(C.norm(rec[l][int(j)]['net'])!=net and disk.distance(rec[l][int(j)]['shape'])<gap(rec[l][int(j)]['net'])+.025-1e-9 for j in trees[l].query(disk.buffer(.65),predicate='intersects')):bad=True;break
         if any(disk.distance(foreign[l][int(j)]['shape'])<gap(foreign[l][int(j)]['net'])+.025-1e-9 for j in ft[l].query(disk.buffer(.65),predicate='intersects')):bad=True;break
         if any(q['layer']==l and C.norm(q['net'])!=net and disk.distance(q['shape'])<gap(q['net'])+.025-1e-9 for q in newcu):bad=True;break
         for rule in g['rule_areas']:
          if rule.get('no_vias') and l in rule['layers'] and any(disk.intersects(s.buffer(.025)) for s in C.poly(rule['outline'])):bad=True;break
         if bad:break
         for rule in res['keepouts']:
          if net not in exceptions.get(rule['name'],set()) and l in rule['layers'] and any(disk.intersects(s.buffer(.025)) for s in C.poly(rule['outline'])):bad=True;break
         if bad:break
        if bad:continue
        annularCandidates+=1
        for width in(.25,.2):
         rr=routed(src,disk,layer,width)
         if rr is None:continue
         ir={'points':[],'body':unary_union([q['shape'] for q in rec['B.Cu'] if q['uuid'] in {t['uuid'] for t in fixed_tracks}|{v['uuid'] for v in fixed_vias}]),'width_mm':.2,'length_mm':sum(LineString([t['a'],t['b']]).length for t in fixed_tracks),'inner_layer':'In3.Cu','native_flash_required':{'via_UUIDs':[v['uuid'] for v in fixed_vias],'layers':['B.Cu','In3.Cu']},'reverse_order_fixed_ILIM_via_UUIDs':[v['uuid'] for v in fixed_vias],'reverse_order_fixed_ILIM_segment_UUIDs':[t['uuid'] for t in fixed_tracks]}
         pending_signal_cu=[]
         dr=restore_dvdt(rr['body'],disk,ir['body'])
         if dr is None:continue
         inner,bridgebody,nativeoutline,bridgeinfo=bridge(disk,hole)
         if inner is None:continue
         uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-U11015-reverse-companion-r44/{bank}/{gi}/{xy}/{dia}'));v={'uuid':uid,'net':raw,'x':xy[0],'y':xy[1],'d':dia,'drill':drill,'flashed':LAYERS,'prospective_not_native':True};newvias.append(v);uids=[]
         if bridgebody is not None:
          zid=str(uuid.uuid5(uuid.UUID(uid),'inner-source-bridge'));newzones.append({'uuid':zid,'net':raw,'layer':inner,'shape':bridgebody,'zone_outline_shape':nativeoutline,'clearance_mm':.15,'physical_Cu_drill_subtracted':True});source[inner]=unary_union([source[inner],bridgebody])
         else:zid=None
         for l in LAYERS:newcu.append({'uuid':uid+'@'+l,'net':raw,'layer':l,'shape':disk})
         for j,(aa,bb) in enumerate(zip(rr['points'],rr['points'][1:])):
          if aa==bb:continue
          sid=str(uuid.uuid5(uuid.UUID(uid),'stub'+str(j)));t={'uuid':sid,'net':raw,'layer':layer,'a':aa,'b':bb,'w':width,'prospective_not_native':True};newtracks.append(t);uids.append(sid);newcu.append({'uuid':sid,'net':raw,'layer':layer,'shape':C.body(t)});(OUT/(sid+'.segment-chunk')).write_text('\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*aa,*bb,width,layer,raw,sid),encoding='utf-8',newline='')
         irids=[]
         for j,(aa,bb) in enumerate(zip(ir['points'],ir['points'][1:])):
          if aa==bb:continue
          sid=str(uuid.uuid5(uuid.UUID(uid),'ILIM-companion'+str(j)));tt={'uuid':sid,'net':iraw,'layer':'B.Cu','a':aa,'b':bb,'w':.2,'prospective_not_native':True};newtracks.append(tt);irids.append(sid);newcu.append({'uuid':sid,'net':iraw,'layer':'B.Cu','shape':C.body(tt)})
          (OUT/(sid+'.segment-chunk')).write_text('\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*aa,*bb,.2,iraw,sid),encoding='utf-8',newline='')
         for sv in ir.get('extra_vias',[]):
          newvias.append(sv);vid=sv['uuid'];(OUT/(vid+'.via-chunk')).write_text('\t(via\n\t\t(at %.6f %.6f)\n\t\t(size %.2f)\n\t\t(drill %.2f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(sv['x'],sv['y'],.5,.2,iraw,vid),encoding='utf-8',newline='')
         for tt in ir.get('extra_tracks',[]):
          newtracks.append(tt);irids.append(tt['uuid']);(OUT/(tt['uuid']+'.segment-chunk')).write_text('\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*tt['a'],*tt['b'],.2,tt['layer'],iraw,tt['uuid']),encoding='utf-8',newline='')
         newcu+=ir.get('all_cu',[])
         drids=[]
         for j,(aa,bb) in enumerate(zip(dr['points'],dr['points'][1:])):
          if aa==bb:continue
          sid=str(uuid.uuid5(uuid.UUID(uid),'DVDT-companion'+str(j)));tt={'uuid':sid,'net':draw,'layer':'B.Cu','a':aa,'b':bb,'w':.2,'prospective_not_native':True};newtracks.append(tt);drids.append(sid);newcu.append({'uuid':sid,'net':draw,'layer':'B.Cu','shape':C.body(tt)})
          (OUT/(sid+'.segment-chunk')).write_text('\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*aa,*bb,.2,draw,sid),encoding='utf-8',newline='')
         (OUT/(uid+'.via-chunk')).write_text('\t(via\n\t\t(at %.6f %.6f)\n\t\t(size %.2f)\n\t\t(drill %.2f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*xy,dia,drill,raw,uid),encoding='utf-8',newline='');result={'via':v,'native_flash_required':[layer,inner],'real_source_root':rootref+'.2','physical_source_overlap_mm2':disk.difference(hole).intersection(source[inner]).area,'inner_bridge_UUID':zid,'inner_bridge_route':bridgeinfo,'outer_route':{k:v for k,v in rr.items() if k!='body'},'new_segment_UUIDs':uids,'ILIM_restore_route':{k:v for k,v in ir.items() if k not in('body','all_cu')},'ILIM_restore_segment_UUIDs':[t['uuid'] for t in fixed_tracks]+irids,'DVDT_restore_route':{k:v for k,v in dr.items() if k!='body'},'DVDT_restore_segment_UUIDs':drids};break
        if result:break
       if result:break
      if result:break
     if result:break
    if result:break
   rows.append({'domain':bank,'r19_group':gi,'physical_pads':[C.identity(q) for q in xs if q['kind']=='pad'],'verdict':'CONSTRUCTED' if result else 'NO_DIRECT_ROOTED_INNER_LANDING','repair':result,'via_candidates':attempts,'all_layer_legal_rooted_annulus_candidates':annularCandidates});print(bank,gi,rows[-1]['verdict'],attempts,annularCandidates,flush=True);write(OUT/'checkpoint.json',rows);(OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps({'vias':newvias,'tracks':newtracks},protocol=5));(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(newzones,protocol=5))
 write(OUT/'receipt.json',{'verdict':'CONSTRUCTED_ALL_REMAINING_GROUND_FEEDS_MUTUAL_NATIVE_CURRENT_PENDING' if all(q['repair'] for q in rows) else 'REMAINING_GROUND_FEEDS_INCOMPLETE','rows':rows,'new_vias':len(newvias),'new_segments':len(newtracks),'proposed_discrete_sha256':sha(OUT/'proposed-discrete.pkl'),'parent_r25_receipt_sha256':sha(bp/'receipt.json'),'scoped_r24_failed_receipt_sha256':sha(prior/'receipt.json'),'rejected_R32_independent_clearance_receipt_sha256':sha(HERE/'u11015-r32-independent-discrete-audit-r33/receipt.json'),'signal_via_annuIi_clear_every_new_ground_stub_Cu':True,'R36_incomplete_receipt_sha256':sha(HERE/'u11015-three-net-mutual-fix-r36/receipt.json'),'ILIM_fixed_before_ground_and_DVDT_search':True,'ILIM_stub_endpoint_centers_on_actual_pad_and_via_Cu_boundary':True,'owned_original_track_removals':owned,'exact_outside_contact_ledger':outside,'C11068_timing_cap_value_pose_and_U11015_DVDT_pin_role_unchanged':True,'source_components_BOM_node_roles_limits_unchanged':True,'RTN_pins_remain_distinct_from_GND6':True,'all_layer_prospective_annuli_not_native_evidence':True,'hole_to_every_SMD_guard_mm':.275,'dynamic_all_drill_edge_guard_mm':.275,'minimum_track_width_mm':.20,'new_source_rooted_inner_planes':len(newzones),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'new_plane_intended_outline_separate_from_drill_subtracted_physical_Cu':True,'endpoint_centers_may_be_outside_source_only_with_checked_physical_Cu_overlap_mm2':.001,'minimum_endpoint_penetration_mm':.025,'source_rooted_inner_annuli_only':True,'full_mutual_aperture_contact_native_current_gates':'OPEN','board_written':False,'native_jobs':0});print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
