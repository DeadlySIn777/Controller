"""Concrete physical-vs-reference wall diagnosis; source plane proposal only."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'construct_Q0_two_native_walls_downshifted_F_In3_F_r388.py';s=base.read_text(encoding='utf-8-sig').split('from Q0_retained_FLT_source_supported_aperture_r384 import support_FLT')[0].replace('Q0-two-native-walls-downshifted-F-In3-F-r388','Q0-two-walls-actual-plane-patch-diagnosis-r390');exec(compile(s,str(base),'exec'))
from Q0_retained_FLT_source_supported_aperture_r384 import support_FLT
oldFLTvia=next(v for v in h['vias']if v['uuid'].startswith('a01ff36f'));fltOwn,fltLedger=support_FLT(K,current,{**h,'vias':h['vias']+newvias},trueRoot,iv,oldFLTvia,GND,'/motherboard_do/DOA_FLT_N_FIELD','In1.Cu');rows=[]
def reference_plane_allowed(plane):
 obs=[]
 for j in trees[plane].query(window.buffer(2),predicate='intersects'):
  r=discrete[plane][int(j)]
  if K.L.norm(r['net'])==GND:continue
  obs.append(K.Z.bounded_buffer(r['shape'],max(.25,req(GND,r['net']))+.025))
 for v in newvias:
  if K.L.norm(v['net'])!=GND:obs.append(K.Z.bounded_disk(v,.25+max(.25,req(GND,v['net']))+.025))
  else:obs.append(K.Z.bounded_disk(v,.1))
 for u,n,hole in holes:
  if n==GND:obs.append(hole)
  else:obs.append(K.Z.bounded_buffer(hole,.275+.005))
 for z in current['zones']:
  if K.L.norm(z['net'])==GND:continue
  for shape in K.L.poly(z['fills'].get(plane,[])):
   if shape.distance(window)<2:obs.append(K.Z.bounded_buffer(shape,max(.25,float(z['clearance_mm']),req(GND,z['net']))+.025))
 for z in q:
  if z['layer']==plane and K.L.norm(z['net'])!=GND and z['shape'].distance(window)<2:obs.append(K.Z.bounded_buffer(z['shape'],max(.25,float(z['clearance_mm']),req(GND,z['net']))+.025))
 for r in h['rule_areas']:
  if plane in r['layers']and r.get('no_zones'):obs.extend(K.Z.bounded_buffer(shape,.025)for shape in K.L.poly(r['outline']))
 return window.difference(unary_union(obs))
for label,net,layer,plane,ends,extra in [('SENSE','/motherboard_do/DOA_Q0_ISNS','B.Cu','In4.Cu',[[228.96,156.45],[228.96,159.6]],unary_union([])),('FLT','/motherboard_do/DOA_FLT_N_FIELD','F.Cu','In1.Cu',[[229.35,158.45],[228.5,157.6]],fltOwn)]:
 phys=free(net,layer,window.buffer(3));old=free(net,layer,refs[plane].union(extra));pp=reference_plane_allowed(plane);candidate=phys.intersection(pp.buffer(-.205,quad_segs=128).union(refs[plane].union(extra).buffer(-.105,quad_segs=128)));partrows=[];nom=None
 for i,part in enumerate(K.RF.parts(phys)):
  inside=[part.covers(Point(x))for x in ends]
  if any(inside):partrows.append({'physical_component':i,'contains_endpoints':inside,'bounds':part.bounds,'area_mm2':part.area})
 for part in K.RF.parts(candidate):
  if not all(part.covers(Point(x))for x in ends):continue
  path,search=T.route(part,tuple(ends[0]),tuple(ends[1]));path=[[round(x,6),round(y,6)]for x,y in path]
  if not part.covers(LineString(path)):continue
  body=K.Z.bounded_buffer(LineString(path),.1);patch=K.Z.bounded_buffer(LineString(path),.2).intersection(pp);newref=refs[plane].union(patch).union(extra);gap=body.difference(newref)
  if not gap.is_empty:continue
  nom={'path_mm':path,'path_length_mm':LineString(path).length,'source_reference_patch_layer':plane,'source_reference_patch_width_mm':.4,'proposed_source_reference_patch_area_mm2':patch.area,'patch_overlap_existing_actual_source_mm2':patch.intersection(refs[plane]).area,'native_owner_profile_PROPOSAL_only':{'clearance_mm':.25,'min_thickness_mm':.15,'connect_pads_mode':'FULL_SOLID','priority':125,'island_removal_mode':1,'thermal_gap_mm':.15,'thermal_bridge_width_mm':.3},'actual_full_track_reference_gap_empty':True,'independent_source_graph_all_contacts_current_refs_native_stackup_SI':'OPEN','search':search};(out/(label+'-proposed-exact-ground-reference-patch.wkb')).write_bytes(patch.wkb);(out/(label+'-proposed-exact-body.wkb')).write_bytes(body.wkb);break
 row={'label':label,'raw_net':net,'track_layer':layer,'reference_layer':plane,'endpoints_mm':ends,'all_exact_physical_endpoint_components':partrows,'candidate_plane_patch':nom,'physical_endpoint_common_component':any(all(x['contains_endpoints'])for x in partrows),'current_reference_endpoint_common_component':any(all(part.covers(Point(x))for x in ends)for part in K.RF.parts(old))};rows.append(row);print('Q0_PHYSICAL_REFERENCE_WALL',label,row['physical_endpoint_common_component'],bool(nom),flush=True)
put(out/'physical-reference-and-ground-patch-nominations.json',rows);report={'verdict':'EXACT_NEW_OWNED_REFERENCE_PATCH_NOMINATION_OR_PHYSICAL_CAUSAL_DIAGNOSIS','model_sha256':sha(model),'source_sha256':sha(source),'operator_sha256':sha(operator),'R388_receipt_sha256':sha(H/'Q0-two-native-walls-downshifted-F-In3-F-r388/receipt.json'),'rows':rows,'all_current_native_and_peer_foreign_Cu_planes_outlines_hard':True,'no_foreign_plane_carve_no_generic_ground_credit':True,'no_source_pass_until_fresh_full_drilled_source_graph':True,'board_written':False,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',report);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'rows':rows,'elapsed_seconds':time.monotonic()-start}),flush=True)
