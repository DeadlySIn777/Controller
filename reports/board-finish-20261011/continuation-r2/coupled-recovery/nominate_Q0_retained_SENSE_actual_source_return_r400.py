"""One ordinary actual FIELD_GND paired return for a legal Q0 target."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'construct_Q0_four_wall_two_port_route_r350.py';prefix=base.read_text(encoding='utf-8').split('def req(a,bb):')[0].replace('Q0-four-wall-two-port-route-constructor-r350','Q0-retained-SENSE-barrel-new-source-return-nomination-r400');exec(compile(prefix,str(base),'exec'))
delete={next(t['uuid']for t in h['tracks']if t['uuid'].startswith('c76c0c67')),'7b8f7e31-baac-4ff2-8b1f-3d210fb85e0d'};target=[228.96,160.412];sourceat=[229.12,157.72];rows=[];selected=None
def req(a,bb):return .15 if dom.get(K.L.norm(a))==dom.get(K.L.norm(bb))else .6
for ti in range(144):
 theta=2*math.pi*ti/144;at=[round(target[0]+.95*math.cos(theta),6),round(target[1]+.95*math.sin(theta),6)];point=Point(at);errors=[];checks=[]
 for layer in K.LAYERS:
  for j in trees[layer].query(point.buffer(1.1),predicate='intersects'):
   r=discrete[layer][int(j)]
   if r['uuid']in delete or r['uuid']in padids or K.L.norm(r['net'])==GND:continue
   d=point.distance(LineString([r['source']['a'],r['source']['b']]))-.25-r['source']['w']/2 if r['kind']=='track'and not r['source'].get('m')else point.distance(Point(r['source']['x'],r['source']['y']))-.25-r['source']['d']/2 if r['kind']=='via'else point.distance(r['shape'])-.25;need=req(GND,r['net'])+.025
   if d<need:errors.append({'kind':'all6_foreign_'+r['kind'],'uuid':r['uuid'],'net':r['net'],'layer':layer,'gap_mm':d,'required_mm':need})
  for z in q:
   if z['layer']!=layer or K.L.norm(z['net'])==GND:continue
   d=point.distance(z['shape'])-.25;need=max(req(GND,z['net']),float(z['clearance_mm']))+.025
   if d<need:errors.append({'kind':'current_owned_power_hard','uuid':z['uuid'],'net':z['net'],'layer':layer,'gap_mm':d,'required_mm':need})
 smds=[s for p in h['pads']if p['smd']and p['uuid']not in padids for l,rs in p['layers'].items()if l in('F.Cu','B.Cu')for s in K.L.poly(rs)if s.distance(point)<1]+list(newsh.values());sm=min((point.distance(s)-.1-.005 for s in smds),default=2.);hg=min((point.distance(s)-.1-.005 for u,n,s in holes),default=2.);pitch=min(point.distance(Point(v['x'],v['y']))for v in h['vias']);newpitch=min(math.dist(at,z)for z in(target,sourceat))
 if sm<.275 or hg<.275 or pitch<.815 or newpitch<.815:errors.append({'kind':'ordinary_aperture_pitch','SMD_mm':sm,'every_hole_mm':hg,'old_via_pitch_mm':pitch,'new_via_pitch_mm':newpitch})
 for r in h['rule_areas']:
  if r.get('no_vias')and any(point.distance(s)-.25<.025 for s in K.L.poly(r['outline'])):errors.append({'kind':'native_no_vias','uuid':r['uuid']})
 for r in reserve['keepouts']:
  if GND not in exempt.get(r['name'],set())and any(point.distance(s)-.25<.025 for s in K.L.poly(r['outline'])):errors.append({'kind':'frozen_reserve','name':r['name']})
 disk=K.Z.bounded_disk({'x':at[0],'y':at[1]},.255);reference={l:disk.difference(oldrefs[l])for l in oldrefs};rawrefs={l:z.area for l,z in reference.items()}
 if any(not z.is_empty for z in reference.values()):errors.append({'kind':'actual_J11003_before_full_annular_source_cap','raw_gaps_mm2':rawrefs})
 row={'new_return_xy_mm':at,'signal_target_xy_mm':target,'target_stitch_spacing_mm':math.dist(at,target),'guarded_SMD_gap_mm':sm,'guarded_every_hole_gap_mm':hg,'nearest_old_via_pitch_mm':pitch,'all6_and_current_hard_power_errors':errors,'actual_source_rooted_before_cap_gap_mm2':rawrefs};rows.append(row)
 if not errors:selected=row;break
put(out/'finite-ordinary-new-return-site-rows.json',rows);result={'verdict':'CONCRETE_NEW_ORDINARY_TARGET_RETURN_NOMINATION_FULL_FINAL_GATES_OPEN'if selected else'FINITE_NEW_TARGET_RETURN_NOMINATION_INCOMPLETE','model_sha256':sha(model),'source_sha256':sha(source),'operator_sha256':sha(operator),'all_current_held_Gate_and_FLT_unchanged':True,'exact_two_SENSE_withdrawables':sorted(delete),'new_signal_ports_mm':[sourceat,target],'selected':selected,'only_nomination_no_source_graph_final_cut_credit':True,'actual_new_annuli_native_final_source_reference_contact_clearance_current_SI':'OPEN','board_written':False,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'selected':selected,'rows':len(rows)}),flush=True)


