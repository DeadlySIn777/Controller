"""Exact R25 same-net wall detour and ordinary ground escape nomination."""
import sys,json,pickle,hashlib,math,re,uuid,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;FP=HERE.parent/'field-power';sys.path.insert(0,str(FP))
import contact_layout as C
import fast_contacts as F
import tri_route as T
import diagnose_c10036_wall_r1 as D
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
GROUND='/motherboard_do/FIELD_B_0V';GATE='/motherboard_do/DO12_RCB_GATE'
def polys(s):return [s] if s.geom_type=='Polygon' else[q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def main():
 started=time.monotonic();out=HERE/'c10036-coupled-wall-constructor-r1.json';assert not out.exists();reads={}
 def read(p):
  raw=p.read_bytes();reads[str(p.resolve())]=hashlib.sha256(raw).hexdigest();return raw
 r=FP/'local-and-b5-return-audit-r25'
 for name,pin in D.PINS.items():assert hashlib.sha256(read(r/name)).hexdigest()==pin
 g=pickle.loads(read(r/'geometry.pkl'));zones=pickle.loads(read(r/'proposed-zones.pkl'));gg=pickle.loads(read(r/'groups.pkl'))
 old=json.loads(read(HERE/'c10036-wall-diagnosis-r1.json'));removed={t['uuid'] for t in old['wall_tracks']};pad=next(p for p in g['pads'] if(p['ref'],p['num'])==('C10036','2'));src=unary_union(C.poly(pad['layers']['F.Cu']))
 h={**g,'tracks':[t for t in g['tracks'] if t['uuid'] not in removed]};rec,trees=F.build({**h,'zones':[]});outline=unary_union(C.poly(g['outline'])).buffer(-.526)
 res=json.loads(read(C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json'));dru=read(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').decode();exceptions={}
 for line in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 def gap(net,other):return .15 if g['domains_normalized'].get(C.norm(net))==g['domains_normalized'].get(C.norm(other)) else .6
 def obs(net,layer,extra=()):
  oo=[q['shape'].buffer(gap(net,q['net'])+.025) for q in rec[layer] if C.norm(q['net'])!=net]
  # Same-domain fills may retreat only under later full-contact projection.
  oo += [q['shape'].buffer(gap(net,q['net'])+.025) for q in zones if q['layer']==layer and C.norm(q['net'])!=net and gap(net,q['net'])==.6]
  oo += [q['shape'].buffer(gap(net,q['net'])+.025) for q in extra if q['layer']==layer and C.norm(q['net'])!=net]
  for rule in g['rule_areas']:
   if rule.get('no_tracks') and layer in rule['layers']:oo += [sh.buffer(.025) for sh in C.poly(rule['outline'])]
  for rule in res['keepouts']:
   if net not in exceptions.get(rule['name'],set()) and layer in rule['layers']:oo += [sh.buffer(.025) for sh in C.poly(rule['outline'])]
  return oo
 cache={}
 def route(net,source,target,width=.2,extra=()):
  a,b=nearest_points(source,target)
  if not extra:
   oo,ot=cache.setdefault(net,(None,None))
   if oo is None:oo=obs(net,'F.Cu');ot=STRtree(oo);cache[net]=(oo,ot)
  else:oo=obs(net,'F.Cu',extra);ot=STRtree(oo)
  for margin in(2.,5.,12.):
   win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);legal=win.difference(unary_union([oo[int(i)] for i in ot.query(win,predicate='intersects')]))
   options=[]
   for part in polys(legal.buffer(-width/2-.006)):
    aa=part.buffer(-.00002).intersection(source.buffer(width/2-.026));bb=part.buffer(-.00002).intersection(target.buffer(width/2-.026))
    if not aa.is_empty and not bb.is_empty:options.append((aa.distance(bb),part,aa,bb))
   for _,part,aa,bb in sorted(options,key=lambda q:q[0]):
    st,en=nearest_points(aa,bb)
    try:pts,search=T.route(part,tuple(st.coords[0]),tuple(en.coords[0]))
    except(AssertionError,ValueError):continue
    pts=[[round(x,6),round(y,6)] for x,y in pts];body=LineString(pts).buffer(width/2,quad_segs=64)
    if legal.buffer(.000001).covers(body) and body.intersection(source).area>.001 and body.intersection(target).area>.001:return {'points':pts,'width_mm':width,'layer':'F.Cu','search':search,'length_mm':LineString(pts).length,'shape':body}
  return None
 own=unary_union([q['shape'] for q in rec['F.Cu'] if C.norm(q['net'])==GATE]);start=Point(66.45,95.55).buffer(.1,quad_segs=64);end=Point(72.95,95.85).buffer(.1,quad_segs=64)
 basegate=route(GATE,start,end);print('WITHDRAWN_WALL_GATE_F_ROUTE',bool(basegate),flush=True)
 groundroot=next(xs for xs in gg[GROUND] if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11005','2') for q in xs));source={l:unary_union([q['shape'] for q in groundroot if q['layer']==l]) for l in LAYERS}
 smd=[unary_union(C.poly(rs)) for q in g['pads'] if q['smd'] for l,rs in q['layers'].items() if l in('F.Cu','B.Cu')];smtree=STRtree(smd);padholes=[sh for p in g['pads'] for sh in C.poly(p.get('hole') or [])];htree=STRtree(padholes);vpoints=[Point(v['x'],v['y']) for v in g['vias']];vt=STRtree(vpoints)
 foreign={l:[q for q in zones if q['layer']==l and C.norm(q['net'])!=GROUND] for l in LAYERS};fts={l:STRtree([q['shape'] for q in foreign[l]]) for l in LAYERS};nearestobs={l:[q for q in rec[l] if C.norm(q['net'])!=GROUND] for l in LAYERS};ots={l:STRtree([q['shape'] for q in nearestobs[l]]) for l in LAYERS}
 candidates=[];attempts=0;counts={};success=None
 for radius in(.6,.9,1.2,1.6,2.2,3.,4.,5.,6.,8.,10.,12.):
  for step in range(64):
   xy=(round(pad['x']+radius*math.cos(step*math.pi/32),6),round(pad['y']+radius*math.sin(step*math.pi/32),6));pt=Point(xy);disk=pt.buffer(.25,quad_segs=64);hole=pt.buffer(.1,quad_segs=64);attempts+=1
   if not outline.covers(disk):continue
   if any(pt.distance(smd[int(i)])-.1<.28-1e-9 for i in smtree.query(pt.buffer(.381),predicate='intersects')):continue
   if any(pt.distance(padholes[int(i)])-.1<.28-1e-9 for i in htree.query(pt.buffer(.381),predicate='intersects')):continue
   if any(pt.distance(vpoints[int(i)])<max(.81,.1+g['vias'][int(i)]['drill']/2+.275)-1e-9 for i in vt.query(pt.buffer(1.2),predicate='intersects')):continue
   fail=False
   for l in LAYERS:
    if any(disk.distance(nearestobs[l][int(i)]['shape'])<gap(GROUND,nearestobs[l][int(i)]['net'])+.025-1e-9 for i in ots[l].query(disk.buffer(.7),predicate='intersects')):fail=True;break
    if any(disk.distance(foreign[l][int(i)]['shape'])<gap(GROUND,foreign[l][int(i)]['net'])+.025-1e-9 for i in fts[l].query(disk.buffer(.7),predicate='intersects')):fail=True;break
    for rule in g['rule_areas']:
     if rule.get('no_vias') and l in rule['layers'] and any(disk.distance(sh)<.025 for sh in C.poly(rule['outline'])):fail=True
    for rule in res['keepouts']:
     if GROUND not in exceptions.get(rule['name'],set()) and l in rule['layers'] and any(disk.distance(sh)<.025 for sh in C.poly(rule['outline'])):fail=True
   if fail:continue
   ann=disk.difference(hole);contacts={l:ann.intersection(source[l]).area for l in LAYERS[1:-1]};lands=[l for l,a in contacts.items() if a>.025]
   if not lands:continue
   gr=route(GROUND,src,disk)
   candidates.append({'at_mm':xy,'source_rooted_annular_overlap_mm2':contacts,'ground_route_found':bool(gr)})
   if not gr:continue
   print('GROUND_ESCAPE',xy,gr['length_mm'],flush=True)
   extra=[{'net':pad['net'],'layer':l,'shape':disk} for l in LAYERS]+[{'net':pad['net'],'layer':'F.Cu','shape':gr['shape']}]
   gate=route(GATE,start,end,extra=extra)
   if not gate:continue
   success={'ground_via_at_mm':xy,'source_root':'J11005.2','inner_annular_contacts_mm2':contacts,'ground_route':{k:v for k,v in gr.items() if k!='shape'},'gate_route':{k:v for k,v in gate.items() if k!='shape'}};print('COUPLED_F_ROUTE_FOUND',json.dumps(success),flush=True);break
  if success:break
 row={'verdict':'CONCRETE_HOST_NOMINATION_REQUIRES_INDEPENDENT_CONTACT_REFERENCE_AUDIT' if success else 'FINITE_F_DETOUR_SEARCH_NO_RECIPE','source_R25_hashes':reads,'removed_wall_UUIDs':sorted(removed),'ground_pad_native_uuid':pad['uuid'],'source_root':'J11005.2','ordinary_size_drill_mm':[.5,.2],'all_SMD_drill_minimum_mm':.275,'polygon_uncertainty_guard_mm':.005,'all_drill_minimum_mm':.275,'ordinary_centre_pitch_mm':.81,'ordinary_via_all6_clearance':True,'base_gate_F_route_found':bool(basegate),'attempted_sites':attempts,'source_rooted_annular_candidates':candidates,'success':success,'all_current_r06_contact_reference_gates':'OPEN','board_emitted':False,'native_jobs':0,'elapsed_seconds':time.monotonic()-started}
 out.write_text(json.dumps(row,indent=1)+'\n');print(json.dumps({'receipt':str(out),'verdict':row['verdict'],'attempts':attempts,'annular_candidates':len(candidates)}),flush=True)
if __name__=='__main__':main()
