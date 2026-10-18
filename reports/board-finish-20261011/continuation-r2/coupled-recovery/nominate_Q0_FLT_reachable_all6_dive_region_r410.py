"""Continuous ordinary FLT site region with all original power hard."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'diagnose_Q0_power_FLT_coupled_exact_components_r408.py'
prefix=base.read_text().split("POWER='/motherboard_do/DOA_FIELD_3V3';rows=[]")[0].replace('Q0-power-FLT-coupled-exact-components-r408','Q0-FLT-reachable-all6-dive-region-r410');exec(compile(prefix,str(base),'exec'))
delete.remove('7bb3c794-cbe6-40a7-abfb-5a3ab7df28ff');work=box(228.3,157.9,232,161)
phys=free(FLT,'F.Cu',window.buffer(3));parts=[p for p in K.RF.parts(phys)if p.covers(Point(229.35,158.45))];assert len(parts)==1;reachable=parts[0].intersection(work);obs=[];ledger=[]
def add(sh,row):
 if sh.intersects(work):obs.append(sh);ledger.append({**row,'cutter_WKB_sha256':K.C.sha(sh.wkb)})
for layer in K.LAYERS:
 for j in trees[layer].query(work.buffer(2),predicate='intersects'):
  r=discrete[layer][int(j)]
  if r['uuid']in delete or r['uuid']in padids or K.L.norm(r['net'])==FLT:continue
  add(K.Z.bounded_buffer(r['shape'],.25+req(FLT,r['net'])+.030),{'kind':'actual_foreign_'+r['kind'],'uuid':r['uuid'],'raw_net':r['net'],'layer':layer,'native_geometry':r['source']})
 for z in q:
  if z['layer']==layer and K.L.norm(z['net'])not in(FLT,GND)and z['shape'].distance(work)<2:add(K.Z.bounded_buffer(z['shape'].intersection(work.buffer(3)),.25+max(req(FLT,z['net']),z['clearance_mm'])+.030),{'kind':'current_peer_owned_q_hard','uuid':z['uuid'],'raw_net':z['net'],'layer':layer})
for n,sh in newsh.items():
 if K.L.norm(pads[n]['net'])!=FLT:add(K.Z.bounded_buffer(sh,.25+req(FLT,pads[n]['net'])+.030),{'kind':'translated_R10016_pad','pin':n,'layer':'F.Cu'})
for p in h['pads']:
 if p['smd']and p['uuid']not in padids:
  for layer,rs in p['layers'].items():
   if layer in('F.Cu','B.Cu'):
    for sh in K.L.poly(rs):
     if sh.distance(work)<1:add(K.Z.bounded_buffer(sh,.380),{'kind':'every_SMD_new_drill','uuid':p['uuid'],'ref':p['ref'],'pin':p['num'],'layer':layer})
for n,sh in newsh.items():add(K.Z.bounded_buffer(sh,.380),{'kind':'translated_SMD_new_drill','pin':n})
for uid,net,sh in holes:
 if sh.distance(work)<1:add(K.Z.bounded_buffer(sh,.380),{'kind':'every_existing_drill','uuid':uid})
for v in h['vias']:
 if Point(v['x'],v['y']).distance(work)<1:add(K.Z.bounded_disk(v,.815),{'kind':'ordinary_existing_via_pitch','uuid':v['uuid']})
for v in newvias:
 add(K.Z.bounded_disk(v,.815),{'kind':'ordinary_new_via_pitch','uuid':v['uuid']})
 if K.L.norm(v['net'])!=FLT:add(K.Z.bounded_disk(v,.5+req(FLT,v['net'])+.030),{'kind':'new_all6_foreign_via','uuid':v['uuid'],'raw_net':v['net']})
for r in h['rule_areas']:
 if r.get('no_vias'):
  for sh in K.L.poly(r['outline']):add(K.Z.bounded_buffer(sh,.275),{'kind':'native_no_vias','uuid':r['uuid']})
for r in reserve['keepouts']:
 if FLT not in exempt.get(r['name'],set()):
  for sh in K.L.poly(r['outline']):add(K.Z.bounded_buffer(sh,.275),{'kind':'exact_frozen_disallow_via','name':r['name']})
legal=reachable.difference(unary_union(obs));put(out/'continuous-all6-ordinary-mask-ledger.json',ledger);(out/'continuous-all6-ordinary-FLT-site-region.wkb').write_bytes(legal.wkb)
returns={v['uuid']:v for v in h['vias']if K.L.norm(v['net'])==GND and any(r['kind']=='via'and r['uuid']==v['uuid']and r['layer']=='In1.Cu'for r in trueRoot)and any(r['kind']=='via'and r['uuid']==v['uuid']and r['layer']=='In4.Cu'for r in trueRoot)};returns.update({v['uuid']:v for v in newvias if K.L.norm(v['net'])==GND});nom=[]
for rid,rv in returns.items():
 if Point(rv['x'],rv['y']).distance(legal)>1.01:continue
 ring=Point(rv['x'],rv['y']).buffer(.995,quad_segs=256).difference(Point(rv['x'],rv['y']).buffer(.905,quad_segs=256));fr=legal.intersection(ring).buffer(-.003,quad_segs=128)
 if fr.is_empty:continue
 pt=nearest_points(Point(229.35,158.45),fr)[1];at=[round(x,6)for x in pt.coords[0]]
 if not fr.covers(Point(at)):continue
 cap=K.Z.bounded_disk({'x':at[0],'y':at[1]},.255);gaps={l:cap.difference(oldrefs[l])for l in oldrefs};ann=K.Z.bounded_disk(rv,rv['d']/2).difference(K.Z.bounded_disk(rv,rv['drill']/2));contact={l:ann.buffer(-.025,quad_segs=128).intersection(refs[l].difference(K.Z.bounded_disk({'x':at[0],'y':at[1]},.525))).area for l in refs}
 nom.append({'new_FLT_port_mm':at,'existing_or_already_nominated_ground_return':rid,'return_mm':[rv['x'],rv['y']],'spacing_mm':math.dist(at,[rv['x'],rv['y']]),'before_rooted_full_cap_gap_mm2':{l:s.area for l,s in gaps.items()},'before_rooted_full_cap_gap_empty':all(s.is_empty for s in gaps.values()),'return_finite_after_annular_interior_mm2':contact,'return_source_nomination_pass':all(s.is_empty for s in gaps.values())and all(a>.002 for a in contact.values()),'new_native_final_source_contact_reference_SI_gates':'OPEN'})
put(out/'actual-existing-or-already-nominated-return-paired-site-nominations.json',nom)
r={'verdict':'CONTINUOUS_ORDINARY_FALL6_SITE_NOMINATION_ONLY','model_sha256':sha(model),'source_sha256':sha(source),'all_original_power_retained':True,'ordinary_reachable_FLT_F_region_mm2':reachable.area,'actual_all6_SMD_everyhole_pitch_reserve_legal_region_mm2':legal.area,'actual_legal_region_empty':legal.is_empty,'actual_return_paired_nominees':nom,'all_current_field_power_and_every_original_foreign_Cu_hard':True,'full_board_source_contact_reference_current_native':'OPEN','board_written':False,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',r);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'reachable_mm2':reachable.area,'legal_mm2':legal.area,'nominees':nom}),flush=True)
