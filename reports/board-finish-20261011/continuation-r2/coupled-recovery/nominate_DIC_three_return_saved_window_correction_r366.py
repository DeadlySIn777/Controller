"""Only three DIC ground-return locations; preserve every signal/native item."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'construct_Q0_four_wall_two_port_route_r350.py';prefix=base.read_text(encoding='utf-8').split('def req(a,bb):')[0].replace('Q0-four-wall-two-port-route-constructor-r350','DIC-three-return-saved-window-correction-r366');exec(compile(prefix,str(base),'exec'))
LG='/LOGIC_GND';viaBy={v['uuid']:v for v in h['vias']};lookup=lambda s:next(v for v in h['vias']if v['uuid'].startswith(s));signal=[lookup(s)for s in('7a5d26bb','55ab5777','1f815e33')];oldreturn=[lookup(s)for s in('99cc6bf8','9ef5dbc8','0330815c')];removed={v['uuid']for v in oldreturn};actualLG=K.root(groups[LG],'J11001','2');LGrefs={l:unary_union([r['shape']for r in actualLG if r['kind']=='fill'and r['layer']==l])for l in('In1.Cu','In4.Cu')};localdomains=h['domains_normalized'];results=[];chosen=[];allrows=[];smd=[s for p in h['pads']if p['smd']for l,rs in p['layers'].items()if l in('F.Cu','B.Cu')for s in K.L.poly(rs)];smdtree=STRtree(smd);holelist=[r for r in holes if r[0]not in removed];holetree=STRtree([r[2]for r in holelist]);OUT={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu','B.Cu':'In4.Cu','In3.Cu':'In4.Cu'}
def req(a,bb):return .15 if localdomains.get(K.L.norm(a))==localdomains.get(K.L.norm(bb))else .6
for sig,old in zip(signal,oldreturn):
 theta0=math.atan2(old['y']-sig['y'],old['x']-sig['x']);nom=[]
 for radius in(.95,.925,.975):
  for step in [0]+[s for k in range(1,49)for s in(k,-k)]:
   theta=theta0+step*math.pi/96;at=[round(sig['x']+radius*math.cos(theta),6),round(sig['y']+radius*math.sin(theta),6)];nom.append((math.dist(at,[old['x'],old['y']]),at))
 nom.sort();select=None;rows=[]
 for move,at in nom:
  p=Point(at);bad=[]
  for layer in K.LAYERS:
   for j in trees[layer].query(p.buffer(1.1),predicate='intersects'):
    r=discrete[layer][int(j)]
    if r['uuid']in removed or K.L.norm(r['net'])==LG:continue
    d=p.distance(LineString([r['source']['a'],r['source']['b']]))-.25-r['source']['w']/2 if r['kind']=='track'and not r['source'].get('m')else p.distance(Point(r['source']['x'],r['source']['y']))-.25-r['source']['d']/2 if r['kind']=='via'else p.distance(r['shape'])-.25;need=req(LG,r['net'])+.025
    if d<need:bad.append({'kind':'all6_'+r['kind'],'uuid':r['uuid'],'raw_net':r['net'],'layer':layer,'gap_mm':d,'required_mm':need})
   for z in q:
    if z['layer']!=layer or K.L.norm(z['net'])==LG:continue
    d=p.distance(z['shape'])-.25;need=max(req(LG,z['net']),float(z['clearance_mm']))+.025
    if d<need:bad.append({'kind':'current_owned_peer_power_hard','uuid':z['uuid'],'raw_net':z['net'],'layer':layer,'gap_mm':d,'required_mm':need})
  sm=p.distance(smd[int(smdtree.nearest(p))])-.1-.005;hd=p.distance(holelist[int(holetree.nearest(p))][2])-.1-.005;pitch=min(math.dist(at,[v['x'],v['y']])for v in h['vias']if v['uuid']not in removed);newpitch=min((math.dist(at,x['new_xy_mm'])for x in chosen),default=100.)
  if sm<.275 or hd<.275 or pitch<.815 or newpitch<.815:bad.append({'kind':'ordinary_SMD_every_hole_pitch','SMD_mm':sm,'every_hole_mm':hd,'old_retained_pitch_mm':pitch,'new_pair_pitch_mm':newpitch})
  for r in h['rule_areas']:
   if r.get('no_vias')and any(p.distance(s)-.25<.025 for s in K.L.poly(r['outline'])):bad.append({'kind':'native_no_vias','uuid':r['uuid']})
  for r in reserve['keepouts']:
   if LG not in exempt.get(r['name'],set())and any(p.distance(s)-.25<.025 for s in K.L.poly(r['outline'])):bad.append({'kind':'frozen_reserve','name':r['name']})
  drill=K.Z.bounded_disk({'x':at[0],'y':at[1]},.1);ann=Point(at).buffer(.25,quad_segs=128).difference(Point(at).buffer(.1,quad_segs=128));refs={l:{'finite_actual_before_source_annular_contact_mm2':ann.intersection(LGrefs[l]).area,'finite_inner_contact_mm2':ann.buffer(-.025,quad_segs=128).intersection(LGrefs[l]).area}for l in LGrefs}
  if any(z['finite_inner_contact_mm2']<.005 for z in refs.values()):bad.append({'kind':'actual_source_annulus','layer_witness':refs})
  neighbors=[]
  for outer,inner in OUT.items():
   delta=drill.intersection(LGrefs[inner])
   for j in trees[outer].query(delta.envelope.buffer(.000000001),predicate='intersects'):
    r=discrete[outer][int(j)]
    if r['kind']!='track'or K.L.norm(r['net'])==LG or localdomains.get(K.L.norm(r['net']))!=localdomains[LG]:continue
    loss=r['shape'].intersection(delta)
    if not loss.is_empty:neighbors.append({'uuid':r['uuid'],'raw_net':r['net'],'layer':outer,'new_own_GND_drill_actual_source_reference_loss_mm2':loss.area})
  if neighbors:bad.append({'kind':'strict_zero_retained_actual_source_track_reference','losses':neighbors})
  row={'old_return_UUID':old['uuid'],'old_xy_mm':[old['x'],old['y']],'signal_UUID':sig['uuid'],'signal_xy_mm':[sig['x'],sig['y']],'old_designated_spacing_mm':math.dist([old['x'],old['y']],[sig['x'],sig['y']]),'new_xy_mm':at,'new_saved_window_spacing_mm':math.dist(at,[sig['x'],sig['y']]),'ground_move_mm':move,'guarded_SMD_mm':sm,'guarded_every_hole_mm':hd,'actual_before_source_annuli':refs,'errors':bad};rows.append(row)
  if not bad:select=row;chosen.append(row);break
 allrows.extend(rows);results.append({'signal_UUID':sig['uuid'],'selected':select,'candidate_count':len(rows)});print('DIC_RETURN_WINDOW_NOMINATION',sig['uuid'],bool(select),len(rows),flush=True)
put(out/'exact-three-return-site-rows.json',allrows);put(out/'selected-minimal-ground-return-relocations.json',chosen);report={'verdict':'CONCRETE_THREE_GROUND_RETURN_WINDOW_NOMINATION_FULL_SPARSE_GATE_OPEN'if len(chosen)==3 else'DIC_RETURN_WINDOW_NOMINATION_INCOMPLETE','model_file':str(model),'model_sha256':sha(model),'source_sha256':sha(source),'operator_file':str(operator),'operator_sha256':sha(operator),'R368_actual_drilled_source_groups_sha256':sha(groupsfile),'existing_real_return_window_before_relocation_diagnosis_file':str(H/'Q0-B-port-and-DIC-existing-return-diagnosis-r354/receipt.json'),'existing_real_return_window_before_relocation_diagnosis_sha256':sha(H/'Q0-B-port-and-DIC-existing-return-diagnosis-r354/receipt.json'),'selected_count':len(chosen),'results':results,'only_three_unadopted_new_DIC_return_Cu_relocations_proposed':True,'all_DIC_signal_tracks_ports_original_CMD_all_other_Cu_unchanged':True,'new_ordinary_all6_flash_native_API_full_source_old_contacts_full_reference_current_SI':'OPEN','no_reclaimed_old_hole_fill_or_generic_disk_credit':True,'all_R155_R368_RAW_28_R7_CORE_ROOT42_native_and_old_designated_pair_FAIL_preserved':True,'native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',report);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'selected_count':len(chosen),'selected':chosen}),flush=True)
