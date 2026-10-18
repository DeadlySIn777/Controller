"""Fresh current all-six ordinary return positions, finite source annuli.

Remove the saved planner's full source-centre containment requirement only
for nomination. Neither clearance, hole/SMD margins, pitch, real source
annular contact nor final full body/contact/current/native gates is waived.
"""
import sys,json,pickle,time,math
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import construct_di6_direct_source_escape_r5 as K
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
C=A.C;GND='/LOGIC_GND';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def main():
 started=time.monotonic();out=HERE/'fresh-partial-annular-return-nomination-r106.json';assert not out.exists();A.read(__file__);rp=HERE/'di15-safe-root-r22-DI6-bind-r62.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='a8234fa46de66b43eeefcf2bfbdb3d8563bf862a2ce60c46212b17e77ea314be';raw=A.read(r['model_path']);assert C.sha(raw)==r['model_sha256'];cur=pickle.loads(raw);h=cur['h'];g=cur['after'];domains=h['domains_normalized'];win=box(110,81,137,123);rec,trees=F.build({**h,'zones':[]});reserve,exempt=A.reservations();region=win;ledger=[]
 for layer in LAYERS:
  obstacles=[];counts={'discrete':0,'new_zone':0,'crossdomain_old_fill':0,'real_rules':0}
  for i in trees[layer].query(win.buffer(2),predicate='intersects'):
   q=rec[layer][int(i)];net=L.norm(q['net'])
   if net==GND:continue
   required=.25+(.15 if domains.get(net)==domains[GND] else .6)+.030;obstacles.append(q['shape'].buffer(required,quad_segs=128));counts['discrete']+=1
  for z in cur['zones']:
   net=L.norm(z['net'])
   if z['layer']!=layer or net==GND or z['shape'].distance(win)>2:continue
   required=.25+max(float(z.get('clearance_mm',.15)),.15 if domains.get(net)==domains[GND] else .6)+.030;obstacles.append(z['shape'].buffer(required,quad_segs=128));counts['new_zone']+=1
  for z in g['zones']:
   net=L.norm(z['net'])
   if net==GND or domains.get(net)==domains[GND]:continue
   for shape in L.poly(z['fills'].get(layer,[])):
    if shape.distance(win)>2:continue
    required=.25+max(float(z.get('clearance_mm',.15)),.6)+.030;obstacles.append(shape.buffer(required,quad_segs=128));counts['crossdomain_old_fill']+=1
  for q in h['rule_areas']:
   if layer in q['layers'] and q.get('no_vias'):
    for shape in L.poly(q['outline']):
     if shape.distance(win)<2:obstacles.append(shape.buffer(.275,quad_segs=128));counts['real_rules']+=1
  for q in reserve['keepouts']:
   if layer in q['layers'] and GND not in exempt.get(q['name'],set()):
    for shape in L.poly(q['outline']):
     if shape.distance(win)<2:obstacles.append(shape.buffer(.275,quad_segs=128));counts['real_rules']+=1
  region=region.difference(unary_union(obstacles));ledger.append({'layer':layer,'counts':counts,'remaining_area_mm2':region.area})
 drill_masks=[];smd_masks=[]
 for v in h['vias']:
  point=Point(v['x'],v['y'])
  if point.distance(win)<2:drill_masks.extend([point.buffer(max(.815,v['drill']/2+.380),quad_segs=128)])
 for p in h['pads']:
  drill_masks.extend(sh.buffer(.380,quad_segs=128) for sh in L.poly(p.get('hole') or []) if sh.distance(win)<2)
  if p['smd']:smd_masks.extend(sh.buffer(.380,quad_segs=128) for l,rs in p['layers'].items() if l in('F.Cu','B.Cu') for sh in L.poly(rs) if sh.distance(win)<2)
 physical=region.difference(unary_union(drill_masks+smd_masks));planes={l:cur['source_planes'][l] for l in('In1.Cu','In4.Cu')};queries=[]
 rh=json.loads(A.read(HERE/'DI15-ground-handoff-branches-r104.json'));assert C.sha(A.read(HERE/'DI15-ground-handoff-branches-r104.json'))=='e92bccfec99e74b6dd72ad3b731a951e9adfa6154d3bc8376937054b3b7230e6';r90=json.loads(A.read(HERE/'di15-adjacent-reference-handoff-geometric-nomination-r90.json'));line=LineString(r90['nominees'][0]['In2_points_mm'])
 for q in rh['handoff_branch_eligibility']:queries.append({'kind':'DI15_In1_In3_reference_handoff','marker':q['signal_handoff_at_mm'],'region':physical.intersection(Point(q['signal_handoff_at_mm']).buffer(1,quad_segs=128)).difference(line.buffer(.535,quad_segs=128))})
 dicp=HERE/'DIC-CS-existing-B-or-F-dive-nomination-r98.json';dic=json.loads(A.read(dicp));assert C.sha(A.read(dicp))=='876406c8c52b0ecd3a95793f415b5597ca64c0f183b07ffe64c9e03ee93efe21';draw=A.read(dic['saved_model']);assert C.sha(draw)==dic['saved_model_sha256'];dc=pickle.loads(draw);net='/motherboard_io_control/DIC_IOL1_CS_BUFFER';fa=dc['terms']['F.Cu'][1].buffer(-.05,quad_segs=128).intersection(dc['free']['F.Cu']);target_reachable=unary_union([p for p in K.pieces(dc['free']['F.Cu']) if p.intersects(fa)]);source_reachable=unary_union([p for p in K.pieces(dc['free']['F.Cu']) if p.intersects(dc['terms']['F.Cu'][0].buffer(-.05,quad_segs=128))]);commonB=unary_union([p for p in K.pieces(dc['free']['B.Cu']) if p.intersects(dc['via'][net].intersection(source_reachable))]);signal_region=dc['via'][net].intersection(target_reachable).intersection(commonB).intersection(Point(dc['terms']['F.Cu'][1].centroid).buffer(5,quad_segs=128))
 for site in K.sites(signal_region,list(dc['terms']['F.Cu'][1].centroid.coords)[0],16):
  at=site['at_mm'];p=Point(at);queries.append({'kind':'DIC_CS_F_B_target_pair','marker':at,'region':physical.intersection(p.buffer(1,quad_segs=128).difference(p.buffer(.825,quad_segs=128)))})
 rows=[]
 for query in queries:
  rr=query['region'];options=[]
  for s in K.sites(rr,query['marker'],32):
   at=s['at_mm'];point=Point(at);ann=point.buffer(.25,quad_segs=128).difference(point.buffer(.1,quad_segs=128));contacts={l:ann.intersection(sh).area for l,sh in planes.items()}
   if not all(x>.004 for x in contacts.values()):continue
   options.append({'at_mm':at,'pair_to_signal_or_handoff_mm':math.dist(at,query['marker']),'finite_actual_J1_original_annular_contact_mm2':contacts,'original_GND_plane_center_membership_diagnostic_only':{l:sh.covers(point) for l,sh in planes.items()},'ordinary_new_via_diameter_drill_mm':[.5,.2]})
  rows.append({'kind':query['kind'],'signal_or_handoff_at_mm':query['marker'],'fresh_guarded_all6_ordinary_region_mm2':rr.area,'finite_real_source_annular_options':options})
 cache=HERE/'fresh-partial-annular-return-r106-geometry.pkl';assert not cache.exists();cache.write_bytes(pickle.dumps({'current':cur,'physical_GND_return_region':physical,'planes':planes,'queries':queries,'DIC_current':dc,'DIC_target_signal_region':signal_region},protocol=5));report={'verdict':'FRESH_CURRENT_ORDINARY_PARTIAL_ANNULAR_RETURNS_NOMINATED_FULL_GATES_OPEN' if any(q['finite_real_source_annular_options'] for q in rows) else'FRESH_CURRENT_ORDINARY_RETURN_QUERY_REGIONS_NO_FINITE_NOMINEE','source_model_sha256':r['model_sha256'],'R62_receipt_sha256':C.sha(A.read(rp)),'every_actual_layer_mask_ledger':ledger,'all6_physical_return_area_mm2':physical.area,'queries':rows,'DIC_target_signal_region_mm2':signal_region.area,'source_plane_center_containment_never_required_for_annular_contact':True,'ordinary_SMD_drill_edge_min_guarded_mm':.275,'ordinary_every_hole_edge_min_guarded_mm':.275,'ordinary_pitch_min_guarded_mm':.81,'all_raw_native_positive_power_and_real_rules_hard':True,'no_saved_prior_body_nomination_mask_grants_no_reference_waiver':True,'full_old_new_contact_reference_source_current_r06_r07_native_SI_DRC':'OPEN','saved_geometry_file':str(cache),'saved_geometry_sha256':C.sha(cache.read_bytes()),'native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'queries':rows}),flush=True)
if __name__=='__main__':main()
