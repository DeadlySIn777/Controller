"""Derive isolated continuous legal-centre diagnostic; retain frozen R6."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
src=(HERE/'construct_c10036_paired_return_r6.py').read_text()
src=src.replace("c10036-coupled-paired-return-recipe-r6.json","c10036-continuous-return-diagnostic-r7.json")
marker=" res,exempt=A.reservations();sites="
before=src[:src.index(marker)]
after=src[src.index(" def dg(other)"):src.index(" print('C10036_LOCAL_TRANSITION_PROOF'")]
tail=r'''
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
 report={'schema':'C10036-continuous-return-diagnostic-r7','verdict':'LEGAL_CENTRE_REGION_FOUND' if candidates else 'NO_LEGAL_CENTRE_UNDER_FROZEN_CONSERVATIVE_OBSTACLES','exact_r6_source_transition_disk_radius_mm':radius,'gap_maximum_mm':maximum,'own_ground_vias_within_1mm':existing,'legal_centres_area_mm2':legal.area,'legal_components':len(parts),'legal_centres_WKB_hex':legal.wkb_hex,'candidates':candidates,'obstacles':[{'role':q['role'],'uuid':q['uuid'],'buffer_mm':q['buffer_mm'],'bounds':q['shape'].bounds,'area_mm2':q['shape'].area} for q in obstacles],'all_sources_frozen':True,'read_files_sha256':A.READS,'no_board_or_native_job':True,'elapsed_seconds':time.monotonic()-started}
 out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({k:report[k] for k in ('verdict','legal_centres_area_mm2','legal_components','candidates','own_ground_vias_within_1mm')}),flush=True)
if __name__=='__main__':main()
'''
target=HERE/'construct_c10036_continuous_return_r7.py'
assert not target.exists()
target.write_text(before+after+tail)
print(target)
