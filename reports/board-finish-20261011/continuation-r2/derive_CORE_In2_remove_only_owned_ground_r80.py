"""Construct around actual Cu while permitting only bounded cuts in one new owned In2 ground plane."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=H/'repair_CORE_In2_existing_port_feed_r79.py';dst=H/'repair_CORE_In2_owned_ground_feed_r80.py';assert not dst.exists();s=src.read_text().replace('CORE-In2-existing-port-feed-r79','CORE-In2-owned-ground-feed-r80').replace('r79/','r80/').replace(' R79',' R80')
def sub(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
sub("targets=[pads(xs) for xs in initial if xs is not rr and pads(xs)]", "targets=[pads(xs) for xs in initial if xs is not rr and any(q['kind']=='pad' and q['ref']=='U1001' for q in xs)];assert len(targets)==1 and len(targets[0])==21")
sub("if q['layer']==layer and q['net']!=raw and search.intersects(q['shape']):obs.append", "if q['layer']==layer and q['net']!=raw and not(layer=='In2.Cu'and q['uuid']=='6b1d4fb8-c0e5-531b-acf4-26ef99b34597'and C.norm(q['net'])=='/LOGIC_GND')and search.intersects(q['shape']):obs.append")
sub("current,full_retreat=N.projected(old,h,zones+adds);fullroot", """cut_rows=[]
  if adds:
   cutter=unary_union([N.bounded_buffer(q['shape'],.175+.000020)for q in adds if q['layer']=='In2.Cu'])
   changed=[]
   for q in zones:
    if q['uuid']!='6b1d4fb8-c0e5-531b-acf4-26ef99b34597':changed.append(q);continue
    assert q['layer']=='In2.Cu'and C.norm(q['net'])=='/LOGIC_GND'and float(q.get('clearance_mm',.15))==.15
    n=copy.deepcopy(q);n['shape']=q['shape'].difference(cutter);n['zone_outline_shape']=q['zone_outline_shape'].difference(cutter)
    assert n['shape'].difference(q['shape']).is_empty and n['zone_outline_shape'].difference(q['zone_outline_shape']).is_empty and not n['shape'].is_empty
    cut_rows.append({'UUID':q['uuid'],'only_new_owned_ground_plane_remove_only':True,'before_physical_WKB_sha256':hashlib.sha256(q['shape'].wkb).hexdigest(),'after_physical_WKB_sha256':hashlib.sha256(n['shape'].wkb).hexdigest(),'removed_mm2':q['shape'].difference(n['shape']).area,'added_mm2':0.,'outward_CORE_supply_Cu_guard_mm':.175+.000020,'all_native_original_zone_outlines_and_old_Cu_unchanged':True});changed.append(n)
   assert len(cut_rows)==1;zones=changed
  write(OUT/'bounded-new-owned-In2-ground-remove-only-ledger.json',cut_rows)
  current,full_retreat=N.projected(old,h,zones+adds);fullroot""")
sub("model=OUT/'model.pkl';model.write_bytes", """ground_sources=[]
 for gn,ref in[('/LOGIC_GND','J11001'),('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005')]:
  prior=root(F.graph(pickle.loads(mp.read_bytes())[4],gn),ref);after=root(F.graph(current,gn),ref);lost=F.discrete_keys(prior)-F.discrete_keys(after);ground_sources.append({'net':gn,'actual_source':ref+'.2','prior_source_keys_lost':[list(k)for k in sorted(lost)],'named_source_pads':len(pads(after))});write(OUT/'all3-ground-source-checkpoint.json',ground_sources);print('R80_GROUND_SOURCE',gn,len(lost),len(pads(after)),flush=True)
 model=OUT/'model.pkl';model.write_bytes""")
sub("'new_zone_shapes':len(adds)", "'new_zone_shapes':len(adds),'only_one_new_owned_LG_In2_bounded_remove_only_ledger_sha256':sha(OUT/'bounded-new-owned-In2-ground-remove-only-ledger.json'),'prior_ground_source_checks':ground_sources,'all76_contacts_truegeometry_oldreferences_extraIn2_native_current_stability':'OPEN','host_retention_and_adoption_flags_NOT_GRANTED':True,'generated_precision_ledger_after_new_geometry_requires_exact_rebind':True")
compile(s,str(dst),'exec');dst.write_text(s)
(H/'CORE-In2-owned-ground-feed-r80-derivation.json').write_text(json.dumps({'prior_constructor_sha256':sha(src),'derived_constructor_sha256':sha(dst),'scope':'Only the21pad actualFPGA/main group. Actual oldCu/holes/nativekeepouts/newIO3/U10017/fieldreturns hard; only canonical newLGIn2 UUID6b1 may receive bounded COREfeed .175020 outward remove-only cut. Oldoriginalnativezone outlines unchanged. All3groundsource checkpoints and all76/reference/geometry/current/native required.','no_global_ground_plane_or_contact_waiver':True,'full_CORE1V2_load_A':.8,'source_In2_native_flash_and_current_qualification':'OPEN','native_jobs':0,'adopted':False},indent=1)+'\n');print(dst)
