"""Actual source-anchored regulated feed construction, with bent dogbones.

Only owned proposed same-domain inner returns may be locally carved. Every
native physical contact, native keepout, foreign power proposal and drill is
hard. Each carve is exact and remains subject to the full ground audit.
"""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math,uuid,sys,re,copy
from pathlib import Path
from shapely import set_precision,get_num_coordinates
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from inventory import sha
import contact_layout as C
import fast_contacts as F
import tri_route as T
from regulated_outer_joins_r51 import PORTS
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'sbc-power'))
import guarded_power_projection_r44 as P
OUT=HERE/'regulated-bent-source-feeds-r69';BASE=HERE/'regulated-final-power-search-base-r70'
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'];INNER=['In1.Cu','In4.Cu','In3.Cu','In2.Cu']
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def polys(s):return [s] if s.geom_type=='Polygon' else [q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def main():
 assert not OUT.exists();OUT.mkdir();br=json.loads((BASE/'receipt.json').read_text());assert sha(BASE/'model.pkl')==br['model_sha256'];g,h,binding,planes,after=pickle.loads((BASE/'model.pkl').read_bytes());planes=copy.deepcopy(planes);hard=binding['field_regulated_search_hard_nominees'];hardplanes=hard['planes']
 pocketpath=HERE.parent/'sbc-power/core-reachable-pocket-nominees-r65/stage-2/proposed-discrete.pkl';assert sha(pocketpath)=='271abe9983bbcf70e1c25d4127828abf4ecd3d2445191fb602e6421d9bc9b4e4';pockets=pickle.loads(pocketpath.read_bytes());assert len(pockets['vias'])==2 and len(pockets['tracks'])==7
 assert not {v['uuid'] for v in pockets['vias']} & {v['uuid'] for v in h['vias']};assert not {t['uuid'] for t in pockets['tracks']} & {t['uuid'] for t in h['tracks']}
 hardh={**h,'tracks':h['tracks']+hard['discrete']['tracks']+pockets['tracks'],'vias':h['vias']+hard['discrete']['vias']+pockets['vias']};rec,trees=F.build({**hardh,'zones':[]});outline=unary_union(C.poly(h['outline'])).buffer(-.526);dom=h['domains_normalized'];nativevias={q['uuid']:q for q in hardh['vias']};nativetracks={q['uuid']:q for q in hardh['tracks']};holes=[]
 for q in hardh['pads']:
  for sh in C.poly(q.get('hole') or []):holes.append({'uuid':q['uuid'],'net':q['net'],'plated':bool(q['num']),'shape':sh})
 for q in hardh['vias']:holes.append({'uuid':q['uuid'],'net':q['net'],'plated':True,'shape':Point(q['x'],q['y']).buffer(q['drill']/2,quad_segs=64)})
 ht=STRtree([q['shape'] for q in holes]);smd=[{'uuid':q['uuid'],'shape':unary_union(C.poly(rs))} for q in h['pads'] if q['smd'] for l,rs in q['layers'].items() if l in ('F.Cu','B.Cu')];st=STRtree([q['shape'] for q in smd]);reserved=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text();exceptions={}
 for line in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 original={q['uuid']:copy.deepcopy(q) for q in planes};newvias=[];newtracks=[];adds=[];newcu=[];rows=[];missing=[];carves=[]
 for bank,net,ref,pin,policy in PORTS:
  gs=F.graph(after,net);ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));root=gs[ri];raw=next(q['net'] for q in root if q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin));domain=dom[net];returnnet='/motherboard_motors/FIELD_GND' if bank in ('FIELD5','A3V3') else '/motherboard_do/FIELD_B_0V';connected={ri};source={l:unary_union([q['shape'] for q in root if q['layer']==l]) for l in INNER}
  def gap(other):return (.15 if dom.get(C.norm(other))==domain else .6)+.025
  def maycarve(q):return q['layer'] in INNER and C.norm(q['net'])==returnnet and q['uuid'] in original
  def physical_obstacle(q):
   if q['kind']=='via':
    v=nativevias[q['uuid']];return P.bounded_disk(v,v['d']/2+gap(v['net']))
   if q['kind']=='track':
    t=nativetracks[q['uuid']];return P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+gap(t['net']))
   return P.bounded_buffer(q['shape'],gap(q['net']))
  obstacles={};legal={};cache=[]
  for l in INNER:
   walls=[physical_obstacle(q) for q in rec[l] if C.norm(q['net'])!=net]
   walls += [P.bounded_buffer(q['shape'],gap(q['net'])) for q in planes+adds+hardplanes if q['layer']==l and C.norm(q['net'])!=net and (l not in INNER or not maycarve(q))]
   walls += [P.bounded_buffer(q['shape'],.275) for q in holes if not(q['plated'] and q['net']==raw)]
   walls += [P.bounded_buffer(q['shape'],gap(q['net'])) for q in newcu if q['layer']==l and C.norm(q['net'])!=net]
   for area in h['rule_areas']:
    blocked=area.get('no_zones') if l in INNER else area.get('no_tracks')
    if blocked and l in area['layers']:walls.extend([P.bounded_buffer(s,.025) for s in C.poly(area['outline'])])
   if l in ('F.Cu','B.Cu'):
    for area in reserved['keepouts']:
     if net not in exceptions.get(area['name'],set()) and l in area['layers']:walls.extend([P.bounded_buffer(s,.025) for s in C.poly(area['outline'])])
   obstacles[l]=walls;legal[l]=set_precision(outline.difference(unary_union(walls)),1e-6)
   if l in INNER:
    for width in(.5,.35):
     count=0
     for part in polys(legal[l].buffer(-width/2-.005)):
      reachable=part.buffer(-.00002);goal=reachable.intersection(source[l])
      if goal.is_empty or goal.area<1e-8:continue
      cache.append({'layer':l,'width':width,'part':part,'reachable':reachable,'goal':goal});count+=1
     print(bank,l,'sourcefree',width,count,flush=True)
  def outer_legal(layer,win):
   # Full exact local free geometry. Spatial selection avoids unioning every
   # unrelated outer-copper item on the entire motherboard.
   query=win.buffer(.627)
   walls=[physical_obstacle(rec[layer][int(j)]) for j in trees[layer].query(query,predicate='intersects') if C.norm(rec[layer][int(j)]['net'])!=net]
   walls += [P.bounded_buffer(q['shape'],gap(q['net'])) for q in planes+adds+hardplanes if q['layer']==layer and C.norm(q['net'])!=net and q['shape'].intersects(query)]
   walls += [P.bounded_buffer(holes[int(j)]['shape'],.275) for j in ht.query(win.buffer(.276),predicate='intersects') if not(holes[int(j)]['plated'] and holes[int(j)]['net']==raw)]
   walls += [P.bounded_buffer(q['shape'],gap(q['net'])) for q in newcu if q['layer']==layer and C.norm(q['net'])!=net and q['shape'].intersects(query)]
   for area in h['rule_areas']:
    if area.get('no_tracks') and layer in area['layers']:walls.extend(P.bounded_buffer(sh,.025) for sh in C.poly(area['outline']) if sh.intersects(query))
   for area in reserved['keepouts']:
    if net not in exceptions.get(area['name'],set()) and layer in area['layers']:walls.extend(P.bounded_buffer(sh,.025) for sh in C.poly(area['outline']) if sh.intersects(query))
   return set_precision(win.intersection(outline).difference(unary_union(walls)),1e-6)
  def bridge(target):
   options=[]
   for q in cache:
    startshape=q['reachable'].intersection(target.get(q['layer'],Point().buffer(0)))
    if startshape.is_empty or startshape.area<1e-8:continue
    options.append((startshape.distance(q['goal']),q,startshape))
   for distance,q,startshape in sorted(options,key=lambda x:(-x[1]['width'],x[0])):
    l,width,part,goal=q['layer'],q['width'],q['part'],q['goal'];start,end=nearest_points(startshape,goal)
    if get_num_coordinates(part)>160000:
     reduced=part.buffer(-.015).simplify(.005,preserve_topology=True).intersection(part);parts=[s for s in polys(reduced) if s.intersects(startshape) and s.intersects(goal)]
     if not parts:continue
     part=max(parts,key=lambda s:s.area);start,end=nearest_points(part.buffer(-.00002).intersection(startshape),part.buffer(-.00002).intersection(goal))
    try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
    except(AssertionError,ValueError):continue
    points=[[round(x,6),round(y,6)] for x,y in points];line=LineString(points);core=P.bounded_buffer(line,width/2)
    if not legal[l].covers(core):continue
    native=set_precision(unary_union([s for s in polys(line.buffer(max(.6,width),quad_segs=64).intersection(legal[l])) if s.intersection(core).area>1e-9]),1e-6)
    ownholes=unary_union([q['shape'] for q in holes if q['plated'] and q['net']==raw]+[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64) for v in newvias if v['net']==raw]);body=set_precision(native.difference(ownholes),1e-6)
    if not legal[l].covers(body) or body.intersection(target[l]).area<.001 or body.intersection(source[l]).area<1e-8:continue
    return l,body,native,{'minimum_core_width_mm':width,'length_mm':line.length,'points_mm':points,'target_overlap_mm2':body.intersection(target[l]).area,'actual_same_layer_source_overlap_mm2':body.intersection(source[l]).area,'sheet_only_R35um60C_ohm':.00057003672*line.length/width,'search':search}
   return None,None,None,None
  def via_legal(xy,dia,drill,outer):
   point=Point(xy);disk=P.bounded_buffer(point,dia/2)
   if not outline.covers(disk):return False
   if any(point.distance(smd[int(j)]['shape'])-drill/2<.275+.000002 for j in st.query(point.buffer(drill/2+.276),predicate='intersects')):return False
   if any(point.distance(holes[int(j)]['shape'])-drill/2<.275+.000002 for j in ht.query(point.buffer(drill/2+.276),predicate='intersects')):return False
   if any(point.distance(Point(v['x'],v['y']))-(drill+v['drill'])/2<.275+.000002 for v in newvias):return False
   for l in LAYERS:
    if any(C.norm(rec[l][int(j)]['net'])!=net and disk.distance(rec[l][int(j)]['shape'])<gap(rec[l][int(j)]['net'])+.000002 for j in trees[l].query(disk.buffer(.627),predicate='intersects')):return False
    if any(q['layer']==l and C.norm(q['net'])!=net and not maycarve(q) and disk.distance(q['shape'])<gap(q['net'])+.000002 for q in planes+adds+hardplanes):return False
    if any(q['layer']==l and C.norm(q['net'])!=net and disk.distance(q['shape'])<gap(q['net'])+.000002 for q in newcu):return False
    for area in h['rule_areas']:
     if area.get('no_vias') and l in area['layers'] and any(disk.intersects(P.bounded_buffer(s,.025)) for s in C.poly(area['outline'])):return False
    for area in reserved['keepouts']:
     if net not in exceptions.get(area['name'],set()) and l in area['layers'] and any(disk.intersects(P.bounded_buffer(s,.025)) for s in C.poly(area['outline'])):return False
   return True
  wanted=[i for i,xs in enumerate(gs) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)]
  for gi in wanted:
   if gi in connected:continue
   xs=gs[gi];print(bank,gi,'begin',[(q.get('ref'),q.get('pin')) for q in xs if q['kind']=='pad' and q['pin']],flush=True);target={l:unary_union([q['shape'] for q in xs if q['layer']==l and q['kind']!='fill']) for l in INNER};l,body,native,route=bridge(target);answer=None;outer=None;stubpts=None;stubwidth=None;xy=None;dia=None;drill=None;chosen=None;attempts=0;legalcount=0
   if l is not None:answer='EXISTING_BARREL_SAME_LAYER_SOURCE_BRIDGE'
   if not answer:
    for a in sorted([q for q in xs if q['kind']=='pad' and q['layer'] in ('F.Cu','B.Cu')],key=lambda q:-q['shape'].area):
     outer=a['layer'];anchor=a['shape'].representative_point();win=box(anchor.x-8,anchor.y-8,anchor.x+8,anchor.y+8);outerfree=outer_legal(outer,win)
     for width in(.25,.2):
      parts=[s for s in polys(outerfree.buffer(-width/2-.005)) if s.intersects(a['shape'])];candidates=[]
      for part in parts:
       x0,y0,x1,y1=part.bounds
       for ix in range(math.ceil(x0/.4),math.floor(x1/.4)+1):
        for iy in range(math.ceil(y0/.4),math.floor(y1/.4)+1):
         point=Point(round(ix*.4,6),round(iy*.4,6))
         if part.contains(point):candidates.append((point.distance(anchor),tuple(point.coords[0]),part))
       for radius in(.6,.9,1.2,1.6,2.2,3.,4.,5.,6.,7.):
        for step in range(32):
         point=Point(round(anchor.x+radius*math.cos(step*math.pi/16),6),round(anchor.y+radius*math.sin(step*math.pi/16),6))
         if part.contains(point):candidates.append((point.distance(anchor),tuple(point.coords[0]),part))
      seen=set()
      for _,candidate,part in sorted(candidates,key=lambda x:x[0]):
       if candidate in seen:continue
       seen.add(candidate)
       for d0,h0 in((.6,.3),(.5,.2)):
        attempts+=1
        if not via_legal(candidate,d0,h0,outer):continue
        legalcount+=1;point=Point(candidate);disk=point.buffer(d0/2,quad_segs=64);hole=point.buffer(h0/2,quad_segs=64);ann=disk.difference(hole);target0={layer:ann for layer in INNER};layer,b0,n0,r0=bridge(target0)
        if layer is None:continue
        startshape=part.buffer(-.00002).intersection(a['shape'])
        if startshape.is_empty:continue
        start=startshape.representative_point()
        try:points,search=T.route(part,tuple(start.coords[0]),candidate)
        except(AssertionError,ValueError):continue
        points=[[round(x,6),round(y,6)] for x,y in points];line=LineString(points);stub=P.bounded_buffer(line,width/2)
        if not outerfree.covers(stub) or stub.intersection(a['shape']).area<.001 or line.length>30:continue
        l,body,native,route=layer,b0,n0,r0;answer='BENT_OUTER_ORDINARY_DOGBONE';xy=candidate;dia=d0;drill=h0;stubpts=points;stubwidth=width;chosen=C.identity(a);break
       if answer:break
      if answer:break
     if answer:break
   if not answer:
    missing.append({'bank':bank,'group':gi,'pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']],'strong_via_attempts':attempts,'ordinary_legal_centres':legalcount});print(bank,gi,'NO_SOURCE_BRIDGE_OR_BENT_DOGBONE',attempts,legalcount,flush=True)
   else:
    if xy is not None:body=set_precision(body.difference(Point(xy).buffer(drill/2,quad_segs=64)),1e-6)
    zid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-regulated-r69/{bank}/{gi}/{l}'));z={'uuid':zid,'net':raw,'layer':l,'shape':body,'zone_outline_shape':native,'clearance_mm':.15,'physical_Cu_drill_subtracted':True,'label':f'{bank}-r69-{gi}'};adds.append(z);viauid=None;trackuids=[];shapes={l:body}
    if xy is not None:
     viauid=str(uuid.uuid5(uuid.NAMESPACE_URL,zid+'/via'));v={'uuid':viauid,'net':raw,'x':xy[0],'y':xy[1],'d':dia,'drill':drill,'flashed':LAYERS,'prospective_not_native':True};newvias.append(v);disk=P.bounded_buffer(Point(xy),dia/2)
     for layer in LAYERS:shapes[layer]=unary_union([shapes.get(layer,Point().buffer(0)),disk]);newcu.append({'uuid':viauid,'net':raw,'layer':layer,'shape':disk})
     stub=LineString(stubpts);shapes[outer]=unary_union([shapes[outer],P.bounded_buffer(stub,stubwidth/2)])
     for j,(aa,bb) in enumerate(zip(stubpts,stubpts[1:])):
      if aa==bb:continue
      uid=str(uuid.uuid5(uuid.NAMESPACE_URL,zid+f'/stub/{j}'));t={'uuid':uid,'net':raw,'layer':outer,'a':aa,'b':bb,'w':stubwidth,'prospective_not_native':True};newtracks.append(t);trackuids.append(uid);newcu.append({'uuid':uid,'net':raw,'layer':outer,'shape':C.body(t)})
     for layer in INNER:source[layer]=unary_union([source[layer],Point(xy).buffer(dia/2,quad_segs=64).difference(Point(xy).buffer(drill/2,quad_segs=64))])
    source[l]=unary_union([source[l],body]);connected.add(gi)
    for layer in INNER:source[layer]=unary_union([source[layer]]+[q['shape'] for q in xs if q['layer']==layer])
    for q in cache:q['goal']=q['reachable'].intersection(source[q['layer']])
    for q in planes:
     if not maycarve(q) or q['layer'] not in shapes:continue
     cutter=P.bounded_buffer(shapes[q['layer']],gap(q['net']));before=q['shape'];outlinebefore=q.get('zone_outline_shape',before);new=set_precision(set_precision(before,1e-6).difference(cutter),1e-6);newoutline=set_precision(set_precision(outlinebefore,1e-6).difference(cutter),1e-6)
     if before.equals(new) and outlinebefore.equals(newoutline):continue
     key=q['uuid']+'-by-'+zid;rf=OUT/(key+'.removed.wkb');af=OUT/(key+'.quantization-added.wkb');cf=OUT/(key+'.cutter.wkb');rf.write_bytes(before.difference(new).wkb);af.write_bytes(new.difference(before).wkb);cf.write_bytes(cutter.wkb);carves.append({'owned_new_return_uuid':q['uuid'],'raw_return_net':q['net'],'layer':q['layer'],'positive_bridge_uuid':zid,'positive_via_uuid':viauid,'physical_before_sha256':P.digest(before),'physical_after_sha256':P.digest(new),'intended_before_sha256':P.digest(outlinebefore),'intended_after_sha256':P.digest(newoutline),'removed_area_mm2':before.difference(new).area,'positive_quantization_area_mm2':new.difference(before).area,'removed_file_sha256':sha(rf),'positive_delta_sha256':sha(af),'cutter_file':str(cf.resolve()),'cutter_sha256':sha(cf),'clearance_and_guard_mm':gap(q['net'])});q['shape']=new;q['zone_outline_shape']=newoutline
    row={'bank':bank,'group':gi,'verdict':answer,'actual_source':ref+'.'+pin,'raw_net':raw,'pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']],'source_outer_pad':chosen,'new_via_uuid':viauid,'new_via_xy':xy,'diameter_drill_mm':[dia,drill] if dia else None,'stub_layer':outer,'stub_width_mm':stubwidth,'stub_points_mm':stubpts,'stub_UUIDs':trackuids,'source_bridge_uuid':zid,'source_bridge_layer':l,'source_bridge':route,'complete_normal_feed_policy_A':policy,'actual_pin_current_barrel_drop_fault_qualification':'OPEN'};rows.append(row);print(bank,gi,answer,l,route['length_mm'],flush=True)
   write(OUT/'checkpoint.json',{'complete':False,'rows':rows,'remaining':missing,'owned_return_carves':carves});(OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps({'vias':newvias,'tracks':newtracks},protocol=5));(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5));(OUT/'owned-new-return-updates.pkl').write_bytes(pickle.dumps([q for q in planes if not q['shape'].equals(original[q['uuid']]['shape'])],protocol=5))
 write(OUT/'receipt.json',{'verdict':'CONSTRUCTED_ALL_REGULATED_TARGETS_FRESH_GRAPH_AND_MUTUAL_GATES_REQUIRED' if not missing else 'REGULATED_COUPLED_CONSTRUCTION_INCOMPLETE','rows':rows,'remaining':missing,'new_vias':len(newvias),'new_segments':len(newtracks),'new_inner_planes':len(adds),'proposed_discrete_sha256':sha(OUT/'proposed-discrete.pkl'),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'owned_return_updates_sha256':sha(OUT/'owned-new-return-updates.pkl'),'owned_return_carves':carves,'input_base_receipt_sha256':sha(BASE/'receipt.json'),'input_model_sha256':sha(BASE/'model.pkl'),'native_jobs':0,'board_written':False,'all_old_return_contacts_actual_new_source_graph_global_reference_native_and_current_gates':'MANDATORY_OPEN'});print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
