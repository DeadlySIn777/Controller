"""Screen ordinary power escapes from the actual lost F component.

Uses the saved actual drilled current, all current peer Cu and frozen no-via
areas. This is nomination only; q/contact/reference/current/native remain open.
"""
from pathlib import Path
import sys,pickle,json,hashlib,math,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from shapely import from_wkb
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
import tri_route as T
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
out=H/'Q0-lost-power-ordinary-inner-escape-r446';assert not out.exists();out.mkdir();start=time.monotonic()
md=H/'Q0-exact-R428-current-filled-only-r436';rp=md/'receipt.json';r=json.loads(rp.read_bytes());assert sha(rp)=='0f4c4442ad12c21844ebb34f38176547601eb99a79a18abd179dfdc8f76c96b6';mp=Path(r['model_file']);assert sha(mp)==r['model_sha256'];g,h,b,q,current=pickle.loads(mp.read_bytes());POWER='/motherboard_do/DOA_FIELD_3V3';GND='/motherboard_motors/FIELD_GND';dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(K.L.norm(a))==dom.get(K.L.norm(bb))else .6;window=box(224,154,237,164)
gf=H/'Q0-R436-optimized-raw-reference-r442/actual-new-groups.pkl';groups=pickle.loads(gf.read_bytes());pRoot=K.root(groups[POWER],'U11017','1');gRoot=K.root(groups[GND],'J11003','2');lost=next(xs for xs in groups[POWER]if any(r['kind']=='pad'and(r['ref'],str(r['pin']))==('U10004','4')for r in xs));assert K.keys(lost).isdisjoint(K.keys(pRoot));attach=unary_union([r['shape']for r in lost if r['layer']=='F.Cu']);front=from_wkb((H/'Q0-lost-power-group-actual-F-escape-r444/POWER-F-free-with-all-owned-signal-peers.wkb').read_bytes());reachable=unary_union([p for p in K.RF.parts(front)if p.intersects(attach.buffer(-.04,quad_segs=128))]);assert not reachable.is_empty
records,trees=K.F.build({**h,'zones':[]});obs=[];ledger=[]
for layer in K.LAYERS:
 for j in trees[layer].query(window.buffer(1),predicate='intersects'):
  rec=records[layer][int(j)]
  if K.L.norm(rec['net'])==POWER:continue
  rad=.25+gap(POWER,rec['net'])+.030;obs.append(rec['shape'].buffer(rad,quad_segs=128));ledger.append({'kind':'Cu','UUID':rec['uuid'],'layer':layer,'radius_mm':rad})
for pad in h['pads']:
 if pad['smd']:
  for layer,rs in pad['layers'].items():
   if layer not in('F.Cu','B.Cu'):continue
   for sh in K.L.poly(rs):
    if sh.distance(window)<1:obs.append(sh.buffer(.385,quad_segs=128));ledger.append({'kind':'SMD_drill_aperture','UUID':pad['uuid'],'radius_mm':.385})
 for sh in K.L.poly(pad.get('hole')or[]):
  if sh.distance(window)<1:obs.append(sh.buffer(.385,quad_segs=128));ledger.append({'kind':'every_pad_hole','UUID':pad['uuid'],'radius_mm':.385})
for via in h['vias']:
 pp=Point(via['x'],via['y'])
 if pp.distance(window)<1:obs.append(pp.buffer(max(.815,via['drill']/2+.385),quad_segs=128));ledger.append({'kind':'ordinary_pitch_every_drill','UUID':via['uuid'],'radius_mm':max(.815,via['drill']/2+.385)})
for z in q:
 if K.L.norm(z['net'])in(POWER,GND)or z['shape'].distance(window)>=1:continue
 rad=.25+max(gap(POWER,z['net']),float(z['clearance_mm']))+.030;obs.append(z['shape'].buffer(rad,quad_segs=128));ledger.append({'kind':'owned_foreign_power_hard','UUID':z['uuid'],'layer':z['layer'],'radius_mm':rad})
for z in current['zones']:
 if z.get('prospective_not_native')or K.L.norm(z['net'])==POWER or dom.get(K.L.norm(z['net']))==dom[POWER]:continue
 for layer,rs in z['fills'].items():
  for sh in K.L.poly(rs):
   if sh.distance(window)<1:obs.append(sh.buffer(.25+max(gap(POWER,z['net']),float(z['clearance_mm']))+.030,quad_segs=128))
reserve,exempt=K.A.reservations()
for rule in h['rule_areas']:
 if rule.get('no_vias')and set(rule['layers'])&set(K.LAYERS):obs.extend(sh.buffer(.275,quad_segs=128)for sh in K.L.poly(rule['outline']))
for rule in reserve['keepouts']:
 if POWER not in exempt.get(rule['name'],set())and set(rule['layers'])&set(K.LAYERS):obs.extend(sh.buffer(.275,quad_segs=128)for sh in K.L.poly(rule['outline']))
legal=window.difference(unary_union(obs)).intersection(reachable);(out/'ordinary-all6-power-centre-area.wkb').write_bytes(legal.wkb);(out/'lost-group-reachable-F-centre-area.wkb').write_bytes(reachable.wkb);put(out/'exact-ordinary-site-obstacle-ledger.json',ledger)
returnvias=[v for v in h['vias']if K.L.norm(v['net'])==GND and all(('via',v['uuid'],l)in K.keys(gRoot)for l in('In1.Cu','In4.Cu'))];paired=[]
for v in returnvias:
 pp=Point(v['x'],v['y'])
 if pp.distance(legal)>1.0:continue
 area=legal.intersection(pp.buffer(1,quad_segs=128).difference(pp.buffer(.9,quad_segs=128)))
 if not area.is_empty:paired.append((v,area))
targetvias=[v for v in h['vias']if K.L.norm(v['net'])==POWER and any(('via',v['uuid'],l)in K.keys(pRoot)for l in('In2.Cu','In3.Cu'))];targetvias.sort(key=lambda v:Point(v['x'],v['y']).distance(attach));put(out/'nearest-actual-power-source-barrels.json',[{'UUID':v['uuid'],'at':[v['x'],v['y']],'flashed':v['flashed'],'actual_source_layers':[l for l in K.LAYERS if('via',v['uuid'],l)in K.keys(pRoot)]}for v in targetvias[:24]])
sites=[]
for ret,area in paired:
 for part in K.RF.parts(area):
  seeds=[part.representative_point()]
  x0,y0,x1,y1=part.bounds
  for xi in range(math.ceil(x0/.025),math.floor(x1/.025)+1):
   for yi in range(math.ceil(y0/.025),math.floor(y1/.025)+1):
    pp=Point(round(xi*.025,6),round(yi*.025,6))
    if part.covers(pp):seeds.append(pp)
  for pp in seeds:
   xy=[round(pp.x,6),round(pp.y,6)]
   if not part.covers(Point(xy)):continue
   spacing=math.dist(xy,[ret['x'],ret['y']])
   if .90<=spacing<=1.0:sites.append({'power_at_mm':xy,'real_return_UUID':ret['uuid'],'spacing_mm':spacing,'reachable_from_lost_F_group':True})
put(out/'ordinary-power-existing-source-return-sites.json',sites)
result={'verdict':'ORDINARY_POWER_ESCAPE_SITES_NOMINATED_INNER_ROUTES_AND_ALL_GATES_OPEN'if sites else'CURRENT_POWER_REACHABLE_F_HAS_NO_SCREENED_ORDINARY_EXISTING_RETURN_SITE','model_sha256':sha(mp),'actual_groups_sha256':sha(gf),'reachable_F_mm2':reachable.area,'ordinary_all6_centre_mm2':legal.area,'existing_paired_return_area_mm2':sum(a.area for v,a in paired),'finite_site_nomination_count':len(sites),'existing_power_source_barrel_count':len(targetvias),'no_extra_ground_via_nomination_yet':True,'all_current_r06_contacts_strict_refs_new_body_current_native_and_nativezones':'OPEN','all_inherited_failures_preserved':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),**result}),flush=True)
