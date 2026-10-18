"""Exact changed-pad contact obligations and bounded new-field-LDO placements."""
import hashlib,json,math,pickle,sys,time
from pathlib import Path
from collections import defaultdict
from shapely.geometry import Point,LineString,box,mapping
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import affinity
from inventory import HERE,BASE,BOARD,sha
sys.path.insert(0,str(BASE/'continuation-r2'))
import ordinary_routes as O
S=O.S;body=S.overlay_tool.base.body;poly=S.poly;norm=S.norm

def load():
 binding=json.loads((HERE/'geometry-model-binding.json').read_text(encoding='utf-8'))
 for p,h in binding['inputs'].items():
  if sha(p)!=h:raise ValueError('Geometry input changed '+p)
 raw=(HERE/'geometry-model.pkl').read_bytes();assert hashlib.sha256(raw).hexdigest()==binding['cache_sha256']
 return pickle.loads(raw),binding
def build(g,nets=None,layers=None):
 records=defaultdict(list);domain=g['domains_normalized'];flashes=json.loads((BASE/'continuation-r2/native-198b-geometry/actual-via-flashes.json').read_text(encoding='utf-8'))['vias']
 def add(layer,shape,**r):
  if layers is not None and layer not in layers:return
  if nets is not None and norm(r.get('net','')) not in nets:return
  records[layer].append(dict(r,layer=layer,shape=shape,domain=domain.get(norm(r.get('net','')))))
 for p in g['pads']:
  for layer,polygons in p['layers'].items():
   for sh in poly(polygons):add(layer,sh,kind='pad',net=p['net'],ref=p['ref'],pin=p['num'],uuid=p['uuid'])
 for t in g['tracks']:add(t['layer'],body(t),kind='track',net=t['net'],uuid=t['uuid'],source=t)
 for v in g['vias']:
  for layer in flashes[v['uuid']]:add(layer,Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=32),kind='via',net=v['net'],uuid=v['uuid'],source=v)
 for z in g['zones']:
  for layer,polygons in z['fills'].items():
   for i,sh in enumerate(poly(polygons)):add(layer,sh,kind='fill',net=z['net'],uuid=z['uuid'],contour=i)
 for graphic in g['shapes']:
  for sh in poly(graphic['poly']):add(graphic['layer'],sh,kind='graphic',net=graphic['net'],uuid=graphic['uuid'])
 return records,{l:STRtree([r['shape'] for r in rs]) for l,rs in records.items()}
def identity(r):return {k:v for k,v in r.items() if k not in ['shape','source']}
def contacts(records,trees,shape,layer,omit=None,tolerance=.005):
 result=[]
 if layer not in trees:return result
 for i in trees[layer].query(shape.buffer(tolerance),predicate='intersects'):
  r=records[layer][i]
  if omit is not None and r.get('uuid')==omit:continue
  distance=r['shape'].distance(shape)
  if distance>tolerance:continue
  area=r['shape'].intersection(shape).area
  row=identity(r);row.update(distance_mm=distance,overlap_mm2=area,contact='POLYGON_CONTACT' if distance<=.000002 else 'WITHIN_NATIVE_POLYGON_ERROR_REQUIRES_API_CHECK')
  if r['kind']=='track':row.update(start_mm=r['source']['a'],end_mm=r['source']['b'],width_mm=r['source']['w'])
  result.append(row)
 return result
def transform(shape,old,new):
 # KiCad positive rotation is clockwise in the board's downwards Y coordinate.
 # The cloned U11018 orientation is retained in this first placement proposal.
 return affinity.translate(shape,xoff=new[0]-old[0],yoff=new[1]-old[1])
def footprint_shape(g,ref):
 f=next(x for x in g['footprints'] if x['ref']==ref)
 courts=unary_union([q for ps in f['courtyard'].values() for q in poly(ps)])
 return f,courts
def main():
 fill_retreat='--allow-fill-retreat' in sys.argv
 start=time.time();g,binding=load();rec=json.loads((HERE/'ab-prereg-split-source/receipt-r3.json').read_text(encoding='utf-8'))
 oldnets={norm(x['from']) for x in rec['pin_net_changes']}
 records,trees=build(g,nets=oldnets)
 copper=O.C.inventory(BOARD.read_bytes())[3];rows=[];touchtracks={}
 for move in rec['pin_net_changes']:
  pads=[p for p in g['pads'] if p['ref']==move['ref'] and p['num']==move['pin']]
  assert len(pads)==1
  p=pads[0];assert norm(p['net'])==norm(move['from'])
  hit={layer:contacts(records,trees,unary_union(poly(ps)),layer,omit=p['uuid']) for layer,ps in p['layers'].items()}
  for values in hit.values():
   for x in values:
    if x['kind']=='track':touchtracks[x['uuid']]=x
  rows.append({**move,'physical_pad_uuid':p['uuid'],'physical_pad_position_mm':[p['x'],p['y']],'parent_native_footprint_sha256':sha_chunk(copper,p['ref']),'old_net_direct_contacts':hit,'board_action':'Change this pad net only after its old-net contact geometry is isolated. Preserve every recorded old copper contact beyond the owned pad end; zone outlines remain unchanged and fills must be recomputed.'})
 shared=[]
 bytrack={t['uuid']:t for t in g['tracks']}
 for uid,row in touchtracks.items():
  t=bytrack[uid];allhits=contacts(records,trees,body(t),t['layer'],omit=uid)
  shared.append({'uuid':uid,'old_chunk_sha256':hashlib.sha256(copper[uid]).hexdigest(),'net':t['net'],'layer':t['layer'],'start_mm':t['a'],'end_mm':t['b'],'width_mm':t['w'],'all_old_net_pad_copper_and_fresh_fill_contacts':allhits,'removal_authority':'NONE for the whole segment; propose only a local owned-pad cut after all retained contact intervals are evaluated. Do not rip up a shared plane trunk or shared stub.'})
 contact={'schema':'root106-AB-existing-pad-contact-obligations-r1','candidate_sha256':g['sha256'],'moves':rows,'touching_track_obligations':shared,'actual_via_flashes':True,'fresh_fill_in_memory':True,'polygon_inside_error_mm':.005,'originals_preserved':True,'native_jobs':0,'board_written':False,'source_board_parity':'NEW_SOURCE_ONLY; BOARD_CHANGE_PENDING'}
 contactfile=HERE/'changed-pad-contact-r1.json'
 contactbytes=(json.dumps(contact,indent=1)+'\n').encode('utf-8')
 if contactfile.exists():
  prior=json.loads(contactfile.read_text(encoding='utf-8'))
  assert prior['candidate_sha256']==g['sha256']
  assert {(x['ref'],x['pin'],x['from'],x['to']) for x in prior['moves']}=={(x['ref'],x['pin'],x['from'],x['to']) for x in rows}
 else:contactfile.write_bytes(contactbytes)
 print(json.dumps({'changed_pads':len(rows),'touching_tracks':len(shared),'direct_contacts':{x['ref']+'.'+x['pin']:sum(len(v) for v in x['old_net_direct_contacts'].values()) for x in rows}}),flush=True)
 # Place only the four new parts. Existing footprints stay at their inherited
 # pose. Field-B ground fill may retreat for same-domain rail pads on refill;
 # foreign-domain copper/fill and physical courtyard/rule obstacles stay hard.
 records,trees=build(g,layers={'F.Cu','B.Cu'})
 courts={l:[] for l in ['F','B']}
 for f in g['footprints']:
  for side,ps in f['courtyard'].items():courts[side].extend(poly(ps))
 courttrees={s:STRtree(q) for s,q in courts.items()}
 templates={ref:footprint_shape(g,ref) for ref in ['U11018','C11076','C11077','R11065']}
 # Native rule areas that explicitly prohibit footprints/pads are hard.
 hard=defaultdict(list)
 for area in g['rule_areas']:
  if area.get('no_footprints') or area.get('no_pads'):
   for l in area['layers']:hard[l].extend(poly(area['outline']))
 outline=unary_union(poly(g['outline'])).buffer(-.5)
 def legal(ref,pose,extra=()):
  f,court=templates[ref];shift=(pose[0]-f['x'],pose[1]-f['y']);layer='F.Cu' if f['side']=='F' else 'B.Cu';side=f['side'];newcourt=affinity.translate(court,*shift)
  if not outline.covers(newcourt):return False,None
  if any(newcourt.intersects(courts[side][i]) for i in courttrees[side].query(newcourt,predicate='intersects')):return False,None
  if any(newcourt.intersects(x) for x in hard[layer]):return False,None
  if any(newcourt.intersects(x) for x in extra):return False,None
  for p in g['pads']:
   if p['ref']!=ref:continue
   for pl,ps in p['layers'].items():
    sh=affinity.translate(unary_union(poly(ps)),*shift)
    for i in trees[pl].query(sh.buffer(.625),predicate='intersects'):
     old=records[pl][i]
     if old['kind']=='fill' and (old['domain']=='DOM_FIELD_B' or fill_retreat):continue
     gap=.15 if old['domain']=='DOM_FIELD_B' else .6
     if sh.distance(old['shape'])<gap+.025:return False,None
  return True,newcourt
 seeds=[('B_LDO_existing',(129.44,139)),('B5PRE_existing',(235.212,183.59)),('B_DO_isolator',(221.116,86.275)),('B_DO_driver',(144.14,101.838))]
 if '--expanded' in sys.argv:seeds.extend([(str(c),c) for c in [(350,210),(400,210),(415,160),(390,120),(350,70),(420,40),(80,200),(140,210)]])
 candidates=[]
 for region,center in seeds:
  found=0;u_allowed=0
  for radius in range(3,19):
   perimeter=[(center[0]+dx,center[1]+dy) for dx in range(-radius,radius+1) for dy in range(-radius,radius+1) if max(abs(dx),abs(dy))==radius]
   for xy in perimeter:
    ok,ucourt=legal('U11018',xy)
    if not ok:continue
    u_allowed+=1
    picked=[];extra=[ucourt]
    for old,new in [('C11076','C11092'),('C11077','C11093'),('R11065','R11088')]:
     foundpart=None
     offsets=[(dx,dy) for dx in range(-6,7) for dy in range(-6,7) if 3<=max(abs(dx),abs(dy))<=6]
     for dx,dy in sorted(offsets,key=lambda p:p[0]*p[0]+p[1]*p[1]):
      pt=(xy[0]+dx,xy[1]+dy);valid,court=legal(old,pt,extra)
      if valid:foundpart=(pt,court);break
     if foundpart is None:break
     pt,court=foundpart;picked.append({'ref':new,'clone':old,'position_mm':list(pt),'orientation_unchanged':True});extra.append(court)
    if len(picked)!=3:continue
    candidates.append({'region':region,'U11038':{'clone':'U11018','position_mm':list(xy),'orientation_unchanged':True},'passives':picked,'new_part_courtyards':[mapping(x) for x in extra],'physical_copper_courtyard_rule_screen':'PASS_STATIC_COPPER_WITH_DECLARED_FILL_CLEARANCE_VOIDS' if fill_retreat else 'PASS_WITH_UNCHANGED_OLD_COPPER','fill_treatment':'Declared local clearance voids on mandatory fresh refill; same domain0.15mm/foreign domain0.6mm, no zone outline edit; foreign reference continuity must survive' if fill_retreat else 'Local same-domain clearance voids on mandatory fresh refill, no zone outline edit','scope':'Placement only; local pad fanout, input/PG/output/return routes and capacitor loop lengths must pass before board proposal.'});found+=1
    if found>=2:break
   if found>=2:break
  print('placement',region,found,'U_allowed',u_allowed,flush=True)
 result={'candidate_sha256':g['sha256'],'new_parts':rec['new_components'],'placement_candidates':candidates,'geometry_source':binding,'track_clearance_mm':.15,'domain_clearance_mm':.6,'margin_mm':.025,'board_written':False,'native_jobs':0,'route_complete':False,'elapsed_seconds':time.time()-start,'limits':['Bounded18mm neighborhoods, existing orientations retained.','Candidates require input/output/PG and return routes and qualified LDO input/output bypass loop; placement alone does not establish routability.','All proposed additions must be re-screened against root route batch before integration.']}
 dest=HERE/('new-LDO-placement-r3.json' if '--expanded' in sys.argv else ('new-LDO-placement-r2.json' if fill_retreat else 'new-LDO-placement-r1.json'))
 if dest.exists():raise ValueError('Refuse prior placement receipt')
 dest.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'placement_candidates':len(candidates),'elapsed_s':time.time()-start}))
def sha_chunk(native,ref):
 for chunk in native.values():
  if O.C.pcbtext.chunk_kind(chunk)=='footprint' and S.overlay_tool.base.ref_of(chunk)==ref:return hashlib.sha256(chunk).hexdigest()
 raise ValueError('Missing native footprint '+ref)
if __name__=='__main__':main()
