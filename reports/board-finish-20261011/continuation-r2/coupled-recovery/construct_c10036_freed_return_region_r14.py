"""Qualify inherited gate transition with an exact ordinary rooted return."""
import sys,json,pickle,math,copy,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;FP=HERE.parent/'field-power';sys.path.insert(0,str(FP))
import contact_layout as L
import fast_contacts as F
sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import audit_ao1_positive_operation_r4 as Q
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
P,G,S,C,N=A.P,A.G,A.S,A.C,A.N
GROUND='/motherboard_do/FIELD_B_0V';GATE='/motherboard_do/DO12_RCB_GATE';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def vertices(sh):
 if sh.is_empty:return []
 if sh.geom_type=='Polygon':return list(sh.exterior.coords)+[p for r in sh.interiors for p in r.coords]
 return [p for q in sh.geoms for p in vertices(q)]
def main():
 started=time.monotonic();out=HERE/'c10036-freed-return-diagnostic-r14.json';assert not out.exists()
 priorpath=HERE/'c10036-coupled-wall-exact-recipe-r2.json';prior=json.loads(A.read(priorpath));assert C.sha(A.read(priorpath))=='1c10f6d5e79727bfc49d19d77ee1a73fd0532c7aace5f05d271c567e3873810f'
 auditpath=HERE/'c10036-exact-operation-independent-r3.json';audit=json.loads(A.read(auditpath));assert C.sha(A.read(auditpath))=='4f71a988497afbc6c49d14855b1d7ba8645e404045917159210a13e5977567ff';assert len(audit['new_reference_errors'])==1
 for key in('clearance_errors','surviving_contact_losses','native_gate_pad_relationship_losses','unchanged_neighbor_reference_losses'):assert not audit[key],key
 for p,pin in prior['read_files_sha256'].items():assert C.sha(Path(p).read_bytes())==pin,p
 rp=FP/'local-and-b5-return-audit-r25';g=pickle.loads(A.read(rp/'geometry.pkl'));zones=pickle.loads(A.read(rp/'proposed-zones.pkl'));gg=pickle.loads(A.read(rp/'groups.pkl'));root=next(xs for xs in gg[GROUND] if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11005','2') for q in xs));v=next(v for v in g['vias'] if v['uuid']=='40bdf2f9-776c-4aa5-bca6-7921f7c90b54');assert(v['x'],v['y'],v['d'],v['drill'],L.norm(v['net']))==(66.55,95.35,.6,.3,GATE)
 native=json.loads(A.read(HERE.parent/'native-198b-geometry/geometry.json'));nv=next(q for q in native['vias'] if q['uuid']==v['uuid']);assert(nv['at'],nv['w'],nv['drill'],nv['net'])==([66.55,95.35],.6,.3,v['net']);flashes=json.loads(A.read(HERE.parent/'native-198b-geometry/actual-via-flashes.json'))['vias'];assert set(flashes[v['uuid']])==set(v['flashed'])==set(LAYERS)
 source=A.read(Path(prior['source_parent']));identity=N.SourceNets(source);parsed={u:G.parse(u,ch.encode(),{}) for u,ch in prior['exact_new_chunks'].items()};removed=set(prior['removed_source_UUIDs'])|{'75409711-7adb-4e55-b9ea-c36978361c51'};addedvia=next(q for q in parsed.values() if q['kind']=='via');holes=[Point(w['x'],w['y']).buffer(w['drill']/2,quad_segs=128) for w in g['vias']]+[sh for p in g['pads'] for sh in L.poly(p.get('hole') or [])]+[Point(addedvia['at']).buffer(.1,quad_segs=128)];ht=STRtree(holes)
 planes={}
 for l in('In1.Cu','In4.Cu'):
  sh=unary_union([r['shape'].intersection(box(64,92,71,99)) for r in root if r['kind']=='fill' and r['layer']==l and r['shape'].intersects(box(64,92,71,99))]);sh=sh.difference(unary_union([holes[int(i)] for i in ht.query(sh,predicate='intersects')]));planes[l]=sh
 relevant=[]
 for r in root:
  if r['kind']!='fill' or r['layer']!='In1.Cu' or r['shape'].distance(Point(v['x'],v['y']).buffer(.3))>.4:continue
  z=next(z for z in g['zones'] if z['uuid']==r['uuid']);relevant.append({'zone_uuid':z['uuid'],'local_clearance_mm':float(z['clearance_mm']),'prospective_not_native':bool(z.get('prospective_not_native'))})
 local=max([.15]+[z['local_clearance_mm'] for z in relevant]);radius=.3+local+.025
 t=parsed[audit['new_reference_errors'][0]['uuid']];body=A.shape(t);gap=body.difference(planes['In1.Cu']);maximum=max(math.dist(p[:2],(v['x'],v['y'])) for p in vertices(gap));source_kernel_gap=L.body(t).difference(planes['In1.Cu']);assert abs(source_kernel_gap.area-audit['new_reference_errors'][0]['full_body_uncovered_mm2'])<1e-8,(source_kernel_gap.area,audit['new_reference_errors'][0]);assert maximum<=radius,(maximum,radius)
 discrete={**g,'tracks':[t for t in g['tracks'] if t['uuid'] not in removed]};rec,trees=F.build({**discrete,'zones':[]});extra=[]
 for z in parsed.values():
  ls=LAYERS if z['kind']=='via' else[z['layer']]
  for l in ls:extra.append({'net':z['net'],'layer':l,'shape':A.shape(z),'uuid':z['uuid']})
 smd=[sh for p in g['pads'] if p['smd'] for l,ps in p['layers'].items() if l in('F.Cu','B.Cu') for sh in L.poly(ps)];st=STRtree(smd);padholes=[sh for p in g['pads'] for sh in L.poly(p.get('hole') or [])];ptree=STRtree(padholes);points=[Point(w['x'],w['y']) for w in g['vias']]+[Point(addedvia['at'])];vt=STRtree(points);outline=unary_union(L.poly(g['outline'])).buffer(-.526)
 def dg(other):return .15 if g['domains_normalized'].get(L.norm(other))==g['domains_normalized'][GROUND] else .6

 res,exempt=A.reservations();centre=Point(v['x'],v['y']);window=centre.buffer(1.000001,quad_segs=256);legal=centre.buffer(.999999,quad_segs=256)
 def cut(sh,d):
  global_dummy=None
  return sh.buffer(d,quad_segs=128)
 obstacles=[]
 def add(role,uuid,sh,d):
  if sh.distance(window)<=d:
   obstacles.append({'role':role,'uuid':uuid,'buffer_mm':d,'shape':cut(sh,d).intersection(window)})
 for i,p in enumerate(points):add('ordinary pitch',str(i),p,.81002)
 for i,sh in enumerate(smd):add('SMD drill aperture',str(i),sh,.38002)
 for i,sh in enumerate(padholes):add('pad drill aperture',str(i),sh,.38002)
 for l in LAYERS:
  for i in trees[l].query(window.buffer(.95),predicate='intersects'):
   q=rec[l][int(i)]
   if L.norm(q['net'])!=GROUND:add('discrete '+l,q['uuid'],q['shape'],.25+dg(q['net'])+.025+.005)
  for q in zones+extra:
   if q['layer']==l and L.norm(q['net'])!=GROUND:add('prospective '+l,q['uuid'],q['shape'],.25+dg(q['net'])+.025+.005)
  for rule in g['rule_areas']:
   if rule.get('no_vias') and l in rule['layers']:
    for sh in L.poly(rule['outline']):add('no vias '+l,rule['uuid'],sh,.27502)
  for rule in res['keepouts']:
   if GROUND not in exempt.get(rule['name'],set()) and l in rule['layers']:
    for sh in L.poly(rule['outline']):add('reserved '+l,rule['name'],sh,.27502)
 legal=legal.intersection(outline.buffer(-.25)).difference(unary_union([q['shape'] for q in obstacles]))
 def pieces(sh):
  if sh.is_empty:return []
  if sh.geom_type=='Polygon':return [sh]
  return [p for q in sh.geoms for p in pieces(q)]
 parts=sorted(pieces(legal),key=lambda x:x.area,reverse=True);candidates=[]
 for part in parts:
  for sh in [part,part.buffer(-.002),part.buffer(-.005)]:
   if sh.is_empty:continue
   p=sh.representative_point();xy=(round(p.x,6),round(p.y,6));pp=Point(xy);disk=pp.buffer(.25,quad_segs=128);hole=pp.buffer(.1,quad_segs=128);areas={l:pl.difference(hole).buffer(-.075).intersection(disk.difference(hole)).area for l,pl in planes.items()};candidates.append({'at_mm':xy,'legal':legal.covers(pp),'source_distance_mm':pp.distance(centre),'rooted_annular_interior_mm2':areas,'component_area_mm2':part.area})
 existing=[]
 for w in g['vias']:
  p=Point(w['x'],w['y'])
  if L.norm(w['net'])!=GROUND or p.distance(centre)>1.000001:continue
  ann=p.buffer(w['d']/2,quad_segs=128).difference(p.buffer(w['drill']/2,quad_segs=128));areas={l:pl.buffer(-.075).intersection(ann).area for l,pl in planes.items()};existing.append({'via':w,'distance_mm':p.distance(centre),'rooted_annular_interior_mm2':areas})
 report={'schema':'C10036-continuous-return-diagnostic-r7','verdict':'LEGAL_CENTRE_REGION_FOUND' if candidates else 'NO_LEGAL_CENTRE_UNDER_FROZEN_CONSERVATIVE_OBSTACLES','exact_r6_source_transition_disk_radius_mm':radius,'gap_maximum_mm':maximum,'own_ground_vias_within_1mm':existing,'legal_centres_area_mm2':legal.area,'legal_components':len(parts),'legal_centres_WKB_hex':legal.wkb_hex,'candidates':candidates,'freed_by_exact_single_power_track_withdrawal':'75409711-7adb-4e55-b9ea-c36978361c51','obstacles':[{'role':q['role'],'uuid':q['uuid'],'buffer_mm':q['buffer_mm'],'bounds':q['shape'].bounds,'area_mm2':q['shape'].area} for q in obstacles],'all_sources_frozen':True,'read_files_sha256':A.READS,'no_board_or_native_job':True,'elapsed_seconds':time.monotonic()-started}
 out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({k:report[k] for k in ('verdict','legal_centres_area_mm2','legal_components','candidates','own_ground_vias_within_1mm')}),flush=True)
if __name__=='__main__':main()
