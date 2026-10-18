"""Construct joint B supply / In4 actual source-ground bridge geometry."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'construct_c10036_power_return_r12.py').read_text().replace('c10036-power-paired-return-recipe-r12.json','c10036-joint-reference-bridge-recipe-r18.json')
s=s.replace('from shapely.geometry import Point,LineString,box','from shapely.geometry import Point,LineString,box,Polygon\nfrom shapely import set_precision\nimport uuid\nfrom emit_logic_zones_r1 import render\nfrom verify_source import parse,children,child,atom')
old=" legal=win.difference(unary_union(obstacles)).intersection(planes['In4.Cu']);options=[part for part in pieces(legal.buffer(-.156)) if part.covers(Point(old['a'])) and part.covers(Point(old['b']))];nomination=None"
new=r'''
 blegal=win.difference(unary_union(obstacles));gob=[]
 for q in rec['In4.Cu']+rrec['In4.Cu']+[q for q in extra if q['layer']=='In4.Cu']+zones+z41:
  if q.get('layer')!='In4.Cu' or L.norm(q['net'])==GROUND:continue
  req=max(.25,gap(GROUND,q['net']))+.025+.005
  if q['shape'].distance(win)<req:gob.append(q['shape'].buffer(req,quad_segs=128))
 for rule in g['rule_areas']:
  if rule.get('no_zones') and 'In4.Cu' in rule['layers']:gob.extend(sh.buffer(.025) for sh in L.poly(rule['outline']) if sh.intersects(win))
 for rule in res['keepouts']:
  if GROUND not in exempt.get(rule['name'],set()) and 'In4.Cu' in rule['layers']:gob.extend(sh.buffer(.025) for sh in L.poly(rule['outline']) if sh.intersects(win))
 glegal=win.difference(unary_union(gob));legal=blegal.buffer(-.156).intersection(glegal.buffer(-.256));options=[part for part in pieces(legal) if part.covers(Point(old['a'])) and part.covers(Point(old['b']))];nomination=None;bridge=None
'''
assert old in s;s=s.replace(old,new)
s=s.replace("if legal.covers(body):nomination={'points_mm'", "if blegal.covers(body):\n   bridge=set_precision(LineString(pts).buffer(.25,quad_segs=128),1e-6);assert glegal.covers(bridge);assert bridge.intersection(planes['In4.Cu']).area>.05;nomination={'points_mm'")
s=s.replace("'source_rooted_full_body_gap_mm2':body.difference(planes['In4.Cu']).area", "'source_rooted_full_body_gap_mm2':body.difference(unary_union([planes['In4.Cu'],bridge])).area,'added_source_ground_reference_bridge_width_mm':.5,'added_source_ground_reference_bridge_area_mm2':bridge.area,'finite_native_rooted_reference_overlap_mm2':bridge.intersection(planes['In4.Cu']).area")
s=s.replace("identity.assert_chunks({u:ch.encode() for u,ch in new.items()});report=",r'''identity.assert_chunks({u:ch.encode() for u,ch in new.items()});zid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/C10036/DO12/B-power/In4-source-ground-bridge/r18/'+C.sha(bridge.wkb)));zonechunk=render(zid,identity.raw(GROUND),'In4.Cu',bridge).replace('(priority 20)','(priority 124)').replace('(clearance 0.15)','(clearance 0.25)').replace('Retained LOGIC_GND return repair','C10036 source-ground In4 reference bridge');ast=parse(zonechunk);assert atom(ast,'net')==identity.raw(GROUND) and atom(ast,'layer')=='In4.Cu' and atom(ast,'priority')=='124';rings=[[(float(p[1]),float(p[2])) for p in child(pp,'pts')[1:]] for pp in children(ast,'polygon')];rt=Polygon(rings[0],rings[1:]);assert rt.is_valid and rt.symmetric_difference(bridge).area<1e-12;assert not children(ast,'filled_polygon');zrow={'uuid':zid,'net':identity.raw(GROUND),'layer':'In4.Cu','shape':bridge,'clearance_mm':.25,'priority':124,'minimum_thickness_mm':.15,'prospective_not_native':True};wkbpath=HERE/'c10036-reference-bridge-r18.wkb';wkbpath.write_bytes(bridge.wkb);modelpath=HERE/'c10036-reference-bridge-r18.pkl';modelpath.write_bytes(pickle.dumps(zrow,protocol=5));report=''')
s=s.replace("'new_return_UUID':ru,", "'new_return_UUID':ru,'exact_new_zone_chunks':{zid:zonechunk},'new_zone_manifest':{'uuid':zid,'raw_net':identity.raw(GROUND),'layer':'In4.Cu','priority':124,'local_clearance_mm':.25,'minimum_thickness_mm':.15,'core_width_mm':.5,'geometry_WKB_path':str(wkbpath),'geometry_WKB_sha256':C.sha(bridge.wkb),'prospective_zone_pickle':str(modelpath),'prospective_zone_pickle_sha256':C.sha(modelpath.read_bytes()),'native_existing_zone_outlines_and_settings_unchanged':True,'native_fill_and_body_reference':'OPEN'},")
t=HERE/'construct_c10036_joint_reference_bridge_r18.py';assert not t.exists();t.write_text(s);print(t)
