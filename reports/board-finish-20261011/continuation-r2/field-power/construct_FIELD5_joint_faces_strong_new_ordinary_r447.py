"""Only when no existing barrel bridges the two faces, nominate ordinary Cu."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_FIELD5_two_layer_existing_barrel_IO3_hard_r437.py').read_text(encoding='utf-8')
s=s.replace('FIELD5-existing-ordinary-barrel-In3-In2-original-IO3-hard-nomination-r437','FIELD5-joint-In3-In2-strong-new-ordinary-IO3-oldrefs-hard-nomination-r447')
s=s.replace('import contact_layout as L','import audit_aux_exact_raw as A\nimport audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K\nimport restore_field_current_mixed_precision_states_r366 as MS\nimport contact_layout as L')
s=s.replace("g,h,b,q,c=pickle.loads(M.read_bytes());vm=", "g,h,b,q,c=pickle.loads(M.read_bytes());MS.restore_bound_field_current_precision_states(b,q);vm=")
marker=' for core in (.50,.35):'
helper='''
 actualgroups=pickle.loads((H/'REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368/actual-drilled-current-groups.pkl').read_bytes());reference_masks={net:K.source_refs(K.root(actualgroups[net],ref,pin))for net,ref,pin in K.ROOTS[:3]};landing_cache={}
 def ordinary_centres(win):
  key=tuple(win.bounds)
  if key in landing_cache:return landing_cache[key]
  query=win.buffer(2);hard=[];counts={'all_six_discrete':0,'every_SMD_and_pad_hole':0,'every_existing_hole_and_pitch':0,'every_no_via_rule':0,'old_track_supported_reference':0,'DC_owned_actual_supported_reference':0}
  for ly in K.LAYERS:
   for j in trees[ly].query(query,predicate='intersects'):
    rr=rec[ly][int(j)]
    if L.norm(rr['net'])==NET:continue
    radius=.3+G.gap(h,raw,rr['net'])+.025+.0001
    if rr['kind']=='via':v=vm[rr['uuid']];hard.append(N.bounded_disk(v,radius+v['d']/2))
    elif rr['kind']=='track'and not tm[rr['uuid']].get('m'):t=tm[rr['uuid']];hard.append(N.bounded_buffer(LineString([t['a'],t['b']]),radius+t['w']/2))
    else:hard.append(N.bounded_buffer(rr['shape'],radius))
    counts['all_six_discrete']+=1
   for qq in q:
    if qq['uuid']==OLD or qq['layer']!=ly or L.norm(qq['net'])in(NET,FG):continue
    if qq['shape'].intersects(query):hard.append(N.bounded_buffer(qq['shape'],.3+max(qq.get('clearance_mm',.15),G.gap(h,raw,qq['net']))+.025+.0001))
  for pad in h['pads']:
   shapes=L.poly(pad.get('hole')or[])
   if pad['smd']:shapes += [sh for ly,rs in pad['layers'].items()if ly in('F.Cu','B.Cu')for sh in L.poly(rs)]
   for sh in shapes:
    if sh.intersects(query):hard.append(N.bounded_buffer(sh,.15+.275+.0001));counts['every_SMD_and_pad_hole']+=1
  for v in h['vias']:
   if query.intersects(Point(v['x'],v['y'])):hard.append(N.bounded_disk(v,max(.8251,.15+v['drill']/2+.2751)));counts['every_existing_hole_and_pitch']+=1
  for ar in h['rule_areas']:
   if ar.get('no_vias'):
    for sh in L.poly(ar['outline']):
     if sh.intersects(query):hard.append(N.bounded_buffer(sh,.3251));counts['every_no_via_rule']+=1
  for net,refs in reference_masks.items():
   for t in h['tracks']:
    if t['layer']not in refs or h['domains_normalized'].get(L.norm(t['net']))!=h['domains_normalized'][net]or L.norm(t['net'])==net:continue
    bounds=box(min(t['a'][0],t['b'][0])-t['w']/2,min(t['a'][1],t['b'][1])-t['w']/2,max(t['a'][0],t['b'][0])+t['w']/2,max(t['a'][1],t['b'][1])+t['w']/2)
    if not bounds.intersects(query):continue
    body=L.body(t)if t.get('m')is not None else A.shape({'kind':'segment',**t});supported=body.intersection(refs[t['layer']])
    if not supported.is_empty:hard.append(N.bounded_buffer(supported,.3+max(.15,G.gap(h,raw,net))+.025+.0001));counts['old_track_supported_reference']+=1
   for qq in q:
    if qq['uuid']==OLD or qq['layer']not in refs or h['domains_normalized'].get(L.norm(qq['net']))!=h['domains_normalized'][net]or L.norm(qq['net'])==net or not qq['shape'].intersects(query):continue
    supported=qq['shape'].intersection(refs[qq['layer']])
    if not supported.is_empty:hard.append(N.bounded_buffer(supported,.3+max(.15,G.gap(h,raw,net))+.025+.0001));counts['DC_owned_actual_supported_reference']+=1
  answer=win.difference(unary_union(hard));f=O/('strong-ordinary-centres-'+str(len(landing_cache))+'.wkb');f.write_bytes(answer.wkb);landing_cache[key]=answer;put(O/('ordinary-centres-'+str(len(landing_cache))+'-authority.json'),{'window_mm':list(key),'shape_sha256':sha(f),'screen_counts':counts,'new_via_diameter_mm':.6,'drill_mm':.3,'all_SMD_hole_clearance_mm':.2751,'all_old_via_pitch_mm':.8251,'new_signal_return_pair_predicate':'NOT_A_SIGNAL_VIA_DC_FIELD5_SUPPLY_LOOP_CURRENT_GATES_OPEN','all_no_via_rules_hard':True,'old_SUPPORTED_ref_only_no_invented_shadow':True});return answer
'''
assert s.count(marker)==1;s=s.replace(marker,helper+marker)
old="for mid in sorted((v for v in h['vias']if v['net']==raw and sl in v['flashed']and tl in v['flashed']and win.covers(Point(v['x'],v['y']))),key=lambda v:a.distance(Point(v['x'],v['y']))+z.distance(Point(v['x'],v['y']))):"
new="""midpoints=[v for v in h['vias']if v['net']==raw and sl in v['flashed']and tl in v['flashed']and win.covers(Point(v['x'],v['y']))]
    for sf in ss:
     for tf in tt:
      joint=sf.intersection(tf).intersection(ordinary_centres(win)).buffer(-.000002)
      for piece in polys(joint):
       if piece.is_empty:continue
       for pp0 in(nearest_points(piece,a)[0],piece.representative_point()):
        pp=Point(round(pp0.x,6),round(pp0.y,6))
        if piece.covers(pp):midpoints.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/FIELD5/R447/ordinary/'+repr((pp.x,pp.y)))),'net':raw,'x':pp.x,'y':pp.y,'d':.6,'drill':.3,'span':K.LAYERS,'flashed':K.LAYERS,'prospective_not_native':True})
    for mid in sorted(midpoints,key=lambda v:a.distance(Point(v['x'],v['y']))+z.distance(Point(v['x'],v['y']))):"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('from shapely.ops import unary_union','from shapely.ops import unary_union,nearest_points')
s=s.replace("for v in h['vias']:\n         hole", "for v in h['vias']+([mid]if mid.get('prospective_not_native')else[]):\n         hole")
s=s.replace("'controller/FIELD5/R437/'", "'controller/FIELD5/R447/'")
s=s.replace("'vias':[],'removed':[],'source_barrel'", "'vias':[mid]if mid.get('prospective_not_native')else[],'removed':[],'source_barrel'")
s=s.replace("'new_holes_discrete_deletes':0", "'new_ordinary_holes':len(accepted['vias'])if accepted else 0,'discrete_deletes':0,'no_via_rules_all_hard':True,'R437_no_existing_middle_preserved':True")
exec(compile(s,str(H/'construct_FIELD5_two_layer_existing_barrel_IO3_hard_r437.py'),'exec'))
