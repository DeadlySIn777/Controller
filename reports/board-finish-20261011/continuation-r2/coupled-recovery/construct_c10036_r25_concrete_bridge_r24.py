"""Couple one exact .3mm B supply-track rework to the C10036 ground repair."""
import sys,json,pickle,math,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;FP=HERE.parent/'field-power';sys.path.insert(0,str(FP))
import contact_layout as L
import fast_contacts as F
import tri_route as T
sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import audit_ao1_positive_operation_r4 as Q
from shapely.geometry import Point,LineString,box,Polygon
from shapely import set_precision
import uuid
from emit_logic_zones_r1 import render
from verify_source import parse,children,child,atom
from shapely.ops import unary_union
from shapely.strtree import STRtree
P,G,S,C,N=A.P,A.G,A.S,A.C,A.N
GROUND='/motherboard_do/FIELD_B_0V';GATE='/motherboard_do/DO12_RCB_GATE';POWER='/motherboard_do/DOB_FIELD_3V3';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'];U='75409711-7adb-4e55-b9ea-c36978361c51'
def pieces(sh):
 if sh.is_empty:return []
 if sh.geom_type=='Polygon':return [sh]
 return [p for q in sh.geoms for p in pieces(q)]
def main():
 started=time.monotonic();out=HERE/'c10036-r25-reference-bridge-recipe-r24.json';assert not out.exists();rp=FP/'local-and-b5-return-audit-r25'
 priorpath=HERE/'c10036-coupled-wall-exact-recipe-r2.json';prior=json.loads(A.read(priorpath));assert C.sha(A.read(priorpath))=='1c10f6d5e79727bfc49d19d77ee1a73fd0532c7aace5f05d271c567e3873810f';g=pickle.loads(A.read(rp/'geometry.pkl'));zones=pickle.loads(A.read(rp/'proposed-zones.pkl'));gg=pickle.loads(A.read(rp/'groups.pkl'));root=next(xs for xs in gg[GROUND] if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11005','2') for q in xs));source=A.read(Path(prior['source_parent']));identity=N.SourceNets(source);parsed={u:G.parse(u,ch.encode(),{}) for u,ch in prior['exact_new_chunks'].items()};old=next(t for t in g['tracks'] if t['uuid']==U);assert(old['a'],old['b'],old['w'],old['layer'],L.norm(old['net']))==([64.65,95.85],[67.35,93.15],.3,'B.Cu',POWER)
 r41=FP/'regulated-field-source-feeds-r41';pins={'receipt.json':'0a187b439429cca6e5df72168bc06c523a6d4db4638f594822db69cd89ded006','proposed-discrete.pkl':'d4bfc0e5740ee166c220f8a1946df8a6f9ac89a7fee19d74948b4a4d2e6eb8c4','proposed-zones.pkl':'a0c0a6144a1b8da8675ac52578ceb49808981e68f53450cba69d3143908190ee'}
 for name,pin in pins.items():assert C.sha(A.read(r41/name))==pin,name
 h41=pickle.loads(A.read(r41/'proposed-discrete.pkl'));z41=pickle.loads(A.read(r41/'proposed-zones.pkl'));oldids={t['uuid'] for key in('tracks','vias') for t in g[key]};new41={**g,**h41,'tracks':[t for t in h41['tracks'] if t['uuid'] not in oldids],'vias':[t for t in h41['vias'] if t['uuid'] not in oldids],'pads':[],'zones':[],'shapes':[]};rrec,_=F.build(new41)
 removed=set(prior['removed_source_UUIDs'])|{U};h={**g,'tracks':[t for t in g['tracks'] if t['uuid'] not in removed],'zones':[]};rec,trees=F.build(h);extra=[]
 for q in parsed.values():
  for l in LAYERS if q['kind']=='via' else[q['layer']]:extra.append({'uuid':q['uuid'],'net':q['net'],'layer':l,'shape':A.shape(q)})
 returnxy=(66.55,94.45);returnpoint=Point(returnxy);returnbody=returnpoint.buffer(.25,quad_segs=128);returnhole=returnpoint.buffer(.1,quad_segs=128)
 def gap(net,other):return .15 if g['domains_normalized'].get(L.norm(net))==g['domains_normalized'].get(L.norm(other)) else .6
 res,exempt=A.reservations();aperture=[];returnbad=[]
 for l in LAYERS:
  for q in rec[l]+rrec[l]+[q for q in extra+zones+z41 if q['layer']==l]:
   if L.norm(q['net'])==GROUND or returnbody.distance(q['shape'])>.7:continue
   d=returnbody.distance(q['shape']);req=gap(GROUND,q['net'])+.025
   if d<req-1e-8:returnbad.append({'layer':l,'uuid':q['uuid'],'net':q['net'],'distance_mm':d,'required_mm':req})
 smd=[sh for p in g['pads'] if p['smd'] for l,rs in p['layers'].items() if l in('F.Cu','B.Cu') for sh in L.poly(rs)];smdgap=min(returnpoint.distance(sh)-.105 for sh in smd);assert smdgap>=.275
 allv=g['vias']+new41['vias']+[{'x':q['at'][0],'y':q['at'][1],'drill':q['drill'],'uuid':q['uuid']} for q in parsed.values() if q['kind']=='via'];pitch=min(returnpoint.distance(Point(w['x'],w['y'])) for w in allv);assert pitch>=.81
 alld=[Point(w['x'],w['y']).buffer(w['drill']/2,quad_segs=128) for w in allv]+[sh for p in g['pads'] for sh in L.poly(p.get('hole') or [])];drillgap=min(returnpoint.distance(sh)-.105 for sh in alld);assert drillgap>=.275;allholes=alld+[returnhole];ht=STRtree(allholes);planes={}
 for l in('In1.Cu','In4.Cu'):
  sh=unary_union([q['shape'].intersection(box(62,90,71,99)) for q in root if q['kind']=='fill' and q['layer']==l and q['shape'].intersects(box(62,90,71,99))]);sh=sh.difference(unary_union([allholes[int(i)] for i in ht.query(sh,predicate='intersects')]));planes[l]=sh
 ann=returnbody.difference(returnhole);contact={l:sh.buffer(-.075).intersection(ann).area for l,sh in planes.items()};assert all(a>=.004 for a in contact.values())
 for l in LAYERS:extra.append({'uuid':'PROPOSED_PAIRED_RETURN','net':GROUND,'layer':l,'shape':returnbody})
 outline=unary_union(L.poly(g['outline'])).buffer(-.526);win=box(62,90,71,99).intersection(outline);obstacles=[];obledger=[]
 for q in rec['B.Cu']+rrec['B.Cu']+[q for q in extra if q['layer']=='B.Cu']:
  if L.norm(q['net'])==POWER:continue
  d=gap(POWER,q['net'])+.025+.005
  if q['shape'].distance(win)<d:obstacles.append(q['shape'].buffer(d,quad_segs=128));obledger.append({'uuid':q['uuid'],'net':q['net'],'gap_guard_mm':d})
 # Original same-domain fills may legally retreat only under a later complete
 # physical contact audit. New proposed R41 meshes are hard for mutual screen.
 for q in zones+z41:
  if q['layer']!='B.Cu' or L.norm(q['net'])==POWER or(q in zones and gap(POWER,q['net'])<.6):continue
  if q['shape'].distance(win)<1:obstacles.append(q['shape'].buffer(gap(POWER,q['net'])+.025+.005,quad_segs=128))
 for rule in g['rule_areas']:
  if rule.get('no_tracks') and 'B.Cu' in rule['layers']:obstacles.extend(sh.buffer(.025) for sh in L.poly(rule['outline']) if sh.intersects(win))
 for rule in res['keepouts']:
  if POWER not in exempt.get(rule['name'],set()) and 'B.Cu' in rule['layers']:obstacles.extend(sh.buffer(.025) for sh in L.poly(rule['outline']) if sh.intersects(win))

 blegal=win.difference(unary_union(obstacles));gob=[]
 for q in rec['In4.Cu']+rrec['In4.Cu']+[q for q in extra if q['layer']=='In4.Cu']+zones+z41:
  if q.get('layer')!='In4.Cu' or L.norm(q['net'])==GROUND or q['uuid']=='630264b1-3d8f-5604-aedd-209dc0a5eaa3':continue
  req=max(.25,gap(GROUND,q['net']))+.025+.005
  if q['shape'].distance(win)<req:gob.append(q['shape'].buffer(req,quad_segs=128))
 for rule in g['rule_areas']:
  if rule.get('no_zones') and 'In4.Cu' in rule['layers']:gob.extend(sh.buffer(.025) for sh in L.poly(rule['outline']) if sh.intersects(win))
 for rule in res['keepouts']:
  if GROUND not in exempt.get(rule['name'],set()) and 'In4.Cu' in rule['layers']:gob.extend(sh.buffer(.025) for sh in L.poly(rule['outline']) if sh.intersects(win))
 glegal=win.difference(unary_union(gob));legal=blegal.buffer(-.156).intersection(glegal.buffer(-.156));options=[part for part in pieces(legal) if part.covers(Point(old['a'])) and part.covers(Point(old['b']))];nomination=None;bridge=None

 for part in sorted(options,key=lambda x:x.area,reverse=True):
  try:pts,search=T.route(part,tuple(old['a']),tuple(old['b']))
  except(AssertionError,ValueError):continue
  pts=[[round(x,6),round(y,6)] for x,y in pts];body=LineString(pts).buffer(.15,quad_segs=128)
  if blegal.covers(body):
   bridge=set_precision(LineString(pts).buffer(.25,quad_segs=128).intersection(glegal.buffer(-.000003)),1e-6);assert bridge.geom_type=='Polygon' and glegal.covers(bridge);assert bridge.covers(body);assert bridge.covers(LineString(pts).buffer(.155,quad_segs=128));assert bridge.intersection(planes['In4.Cu']).area>.05;nomination={'points_mm':pts,'width_mm':.3,'layer':'B.Cu','length_mm':LineString(pts).length,'source_rooted_full_body_gap_mm2':body.difference(unary_union([planes['In4.Cu'],bridge])).area,'added_source_ground_reference_bridge_bulk_width_mm':.5,'added_source_ground_reference_bridge_continuous_core_width_mm':.31,'added_source_ground_reference_bridge_area_mm2':bridge.area,'finite_native_rooted_reference_overlap_mm2':bridge.intersection(planes['In4.Cu']).area,'route_search':search};break
 report={'schema':'C10036-power-coupled-return-constructor-r11','verdict':'CONCRETE_COUPLED_RECIPE_INDEPENDENT_AUDIT_PENDING' if nomination and not returnbad else 'LOCAL_POWER_RETURN_NOMINATION_INCOMPLETE','return_at_mm':returnxy,'return_guarded_SMD_gap_mm':smdgap,'return_guarded_drill_gap_mm':drillgap,'return_pitch_mm':pitch,'return_finite_annular_source_interior_mm2':contact,'return_clearance_errors':returnbad,'B_power_route':nomination,'power_route_options':len(options),'exact_old_power_track':old,'B_route_obstacles':obledger,'R41_mutual_inputs_sha256':pins,'R41_mutual_reference_verdict':'OPEN_FAIL_UNTIL_SEPARATE_SOURCE_FEED_MESH_CORRECTION','R41_conflicting_prospective_In4_mesh_UUID':'630264b1-3d8f-5604-aedd-209dc0a5eaa3','R41_mesh_not_integrated_or_qualified_by_R25_constructor':True,'other_R41_new_barrels_stubs_and_meshes_remain_hard':True,'prior_recipe_sha256':C.sha(A.read(priorpath)),'board_emitted':False,'native_jobs':0}
 if nomination and not returnbad:
  token=b'\n\t\t(uuid "'+U.encode()+b'")';i=source.index(token);a=source.rfind(b'\n\t(',0,i)+1;b=source.find(b'\n\t(',i)+1;chunk=source[a:b];assert C.pcbtext.chunk_uuid(chunk)==U;pr=G.parse(U,chunk,{});assert(pr['net'],pr['layer'],pr['w'],pr['a'],pr['b'])==(POWER,'B.Cu',.3,old['a'],old['b']);new=dict(prior['exact_new_chunks']);newitems=list(prior['new_items']);ru,rch=Q.serial_via(identity,GROUND,returnxy);new[ru]=rch.decode();newitems.append({'uuid':ru,'kind':'via','raw_net':identity.raw(GROUND),'at_mm':returnxy,'diameter_mm':.5,'drill_mm':.2,'role':'Inherited-DO12-gate-qualified-paired-ground-return'})
  for a,b in zip(nomination['points_mm'],nomination['points_mm'][1:]):
   u,ch=identity.serial_segment(POWER,'B.Cu',a,b,.3);new[u]=ch.decode();newitems.append({'uuid':u,'kind':'segment','raw_net':identity.raw(POWER),'layer':'B.Cu','a':a,'b':b,'width_mm':.3,'role':'DOB_FIELD_3V3-local-power-clearance-detour'})
  identity.assert_chunks({u:ch.encode() for u,ch in new.items()});zid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/C10036/DO12/B-power/In4-source-ground-bridge/r24/'+C.sha(bridge.wkb)));zonechunk=render(zid,identity.raw(GROUND),'In4.Cu',bridge).replace('(priority 20)','(priority 124)').replace('(clearance 0.15)','(clearance 0.25)').replace('Retained LOGIC_GND return repair','C10036 source-ground In4 reference bridge');ast=parse(zonechunk);assert atom(ast,'net')==identity.raw(GROUND) and atom(ast,'layer')=='In4.Cu' and atom(ast,'priority')=='124';rings=[[(float(p[1]),float(p[2])) for p in child(pp,'pts')[1:]] for pp in children(ast,'polygon')];rt=Polygon(rings[0],rings[1:]);assert rt.is_valid and rt.symmetric_difference(bridge).area<1e-12;assert not children(ast,'filled_polygon');zrow={'uuid':zid,'net':identity.raw(GROUND),'layer':'In4.Cu','shape':bridge,'clearance_mm':.25,'priority':124,'minimum_thickness_mm':.15,'prospective_not_native':True};wkbpath=HERE/'c10036-reference-bridge-r24.wkb';wkbpath.write_bytes(bridge.wkb);modelpath=HERE/'c10036-reference-bridge-r24.pkl';modelpath.write_bytes(pickle.dumps(zrow,protocol=5));report={**prior,**report,'exact_removed_chunks':{**prior['exact_removed_chunks'],U:chunk.decode()},'exact_new_chunks':new,'removed_source_UUIDs':sorted(removed),'new_items':newitems,'new_return_UUID':ru,'exact_new_zone_chunks':{zid:zonechunk},'new_zone_manifest':{'uuid':zid,'raw_net':identity.raw(GROUND),'layer':'In4.Cu','priority':124,'local_clearance_mm':.25,'minimum_thickness_mm':.15,'bulk_width_mm':.5,'finite_continuous_core_width_mm':.31,'terminal_clip_only_to_exact_foreign_clearance_legal_area':True,'core_width_mm':.31,'geometry_WKB_path':str(wkbpath),'geometry_WKB_sha256':C.sha(bridge.wkb),'prospective_zone_pickle':str(modelpath),'prospective_zone_pickle_sha256':C.sha(modelpath.read_bytes()),'native_existing_zone_outlines_and_settings_unchanged':True,'native_fill_and_body_reference':'OPEN'},'exact_inherited_gate_transition':{'uuid':'40bdf2f9-776c-4aa5-bca6-7921f7c90b54','at_mm':[66.55,95.35],'diameter_drill_mm':[.6,.3],'own_native_local_clearance_mm':.25,'own_exact_disk_radius_mm':.575,'no_disk_radius_expansion_mm':0,'return_distance_mm':.9},'source_current_r06_r07_copper_reference_and_final_mutual_power_native_gates':'OPEN'}
 report['read_files_sha256']=A.READS;report['elapsed_seconds']=time.monotonic()-started;out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({k:report[k] for k in('verdict','B_power_route','return_clearance_errors','power_route_options','return_finite_annular_source_interior_mm2')}),flush=True);print('RECEIPT_SHA256',C.sha(out.read_bytes()),flush=True)
if __name__=='__main__':main()

