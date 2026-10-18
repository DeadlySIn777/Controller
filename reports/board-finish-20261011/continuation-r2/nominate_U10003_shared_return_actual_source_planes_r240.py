"""Source-seed two new-owned FG plane replacements for the R239 geometry."""
import copy,hashlib,json,pickle,sys
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_declared_settings_projection_r58 as N
OUT=H/'U10003-shared-return-two-source-seeded-new-FG-plane-nomination-r240';assert not OUT.exists();OUT.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
mp=H/'R10007-HOST-current-fresh-native-pad-authority-r238/model.pkl';assert sha(mp)=='8bc676155f72e590cc8dd77f6315f0990d60b421f54a3c7928dc8e66ba48f91d';g,h,b,q,full=pickle.loads(mp.read_bytes())
rp=H/'U10003-shared-return-native-HOST-pose-joint-field-geometry-nomination-r239/receipt.json';assert sha(rp)=='18c29d4dac5745109ba34453d681f0d6bd676836f6d05aea1d0b7e32f875db79';r=json.loads(rp.read_bytes());assert all(r['results'].values());withdraw=set(r['only_nine_unadopted_field_tracks_withdrawn']);central=r['new_shared_ground_via'];FG=K.L.norm(central['net']);replace={'9fe010df-73cf-5bfb-9f7a-bd227b701c3e','ee0efe05-1705-587c-ac86-49b1a7885ef9'}
hard={**h,'tracks':[t for t in h['tracks']if t['uuid']not in withdraw]+r['exact_native_clock_track_restore']+r['new_tracks'],'vias':[v for v in h['vias']if v['uuid']!=central['uuid']]+[central]}
records,trees=K.F.build({**hard,'zones':[]});sourceview={**full,'tracks':hard['tracks'],'vias':hard['vias'],'zones':[z for z in full['zones']if z['uuid']not in replace]};_,groups=K.physical(sourceview,FG,K.hole_context(sourceview));root=K.root(groups,'J11003','2');rootkeys=K.keys(root);oldref={l:unary_union([z['shape']for z in root if z['kind']=='fill'and z['layer']==l])for l in ('In1.Cu','In4.Cu')}
point=lambda v:Point(v['x'],v['y']);ann=lambda v:point(v).buffer(v['d']/2,quad_segs=256).difference(point(v).buffer(v['drill']/2,quad_segs=256))
oldret=next(v for v in hard['vias']if v['uuid']=='73811c12-9f84-5491-bfee-0c5ee985a7a8');sig=next(v for v in hard['vias']if v['uuid']=='7f2431b3-4dcd-5b17-88ce-8aae4c3d66d4');oldA=next(v for v in hard['vias']if v['uuid']=='2938cbdd-1d38-4238-9455-504b30f06e5e');clock=next(v for v in hard['vias']if v['uuid']=='1f45e002-4f40-4087-bbed-3be260272d8f');sigports={v['uuid']:v for v in (sig,oldA,clock)};groundports={v['uuid']:v for v in (central,oldret)}
seedrows={l:{'actual_J3_before_fill_annular_overlap_mm2':oldref[l].intersection(ann(central)).area,'new_shared_via_layer_key_in_actual_source':('via',central['uuid'],l)in rootkeys}for l in oldref};assert seedrows['In1.Cu']['actual_J3_before_fill_annular_overlap_mm2']>0 and seedrows['In1.Cu']['new_shared_via_layer_key_in_actual_source']
bodytracks=r['new_tracks']+r['exact_native_clock_track_restore'];bodies=unary_union([K.A.shape({'kind':'segment',**t})for t in bodytracks]);desired=bodies.buffer(.2,quad_segs=128).union(LineString([point(central),point(oldret)]).buffer(.25,quad_segs=128))
for v in sigports.values():desired=desired.union(point(v).buffer(.7,quad_segs=128))
for v in groundports.values():desired=desired.union(point(v).buffer(.35,quad_segs=128))
win=desired.envelope.buffer(1);dom=h['domains_normalized'];gap=lambda a,c:.15 if dom[K.L.norm(a)]==dom[K.L.norm(c)]else.6;newzones=[];rows=[];ledgers=[];in1oldret=False
for layer in ('In1.Cu','In4.Cu'):
 common=[];physical_only=[];ledger=[]
 def add(shape,kind,uid,physical=False):
  if not shape.intersects(desired):return
  (physical_only if physical else common).append(shape);ledger.append({'kind':kind,'UUID':uid,'physical_only':physical,'WKB_sha256':hashlib.sha256(shape.wkb).hexdigest()})
 for j in trees[layer].query(win,predicate='intersects'):
  z=records[layer][int(j)];net=K.L.norm(z['net'])
  if net!=FG:add(N.bounded_buffer(z['shape'].intersection(win),gap(net,FG)+.025+.0001),'ACTUAL_FOREIGN_CU',z['uuid'],z['uuid']in sigports)
 for z in q:
  if z['uuid']in replace or z['layer']!=layer or K.L.norm(z['net'])==FG:continue
  add(N.bounded_buffer(z['shape'].intersection(win),max(float(z['clearance_mm']),gap(z['net'],FG))+.025),'OTHER_OWNED_PLANE_HARD',z['uuid'])
 for p in hard['pads']:
  for s in K.L.poly(p.get('hole')or[]):
   if s.intersects(win):add(N.bounded_buffer(s,.275),'NATIVE_PAD_HOLE',p['uuid'])
 for v in hard['vias']:
  if not win.covers(point(v)):continue
  if K.L.norm(v['net'])==FG:add(N.bounded_disk(v,v['drill']/2),'PHYSICAL_GROUND_BORE',v['uuid'],v['uuid']in groundports)
  else:add(N.bounded_disk(v,v['drill']/2+.275),'ACTUAL_SIGNAL_DRILL',v['uuid'],v['uuid']in sigports)
 for a in h['rule_areas']:
  if a.get('no_zones')and layer in a['layers']:
   for s in K.L.poly(a['outline']):
    if s.intersects(win):add(N.bounded_buffer(s,.025),'NATIVE_NO_ZONES',a['uuid'])
 for z in full['zones']:
  other=K.L.norm(z['net'])
  if other==FG or dom[other]==dom[FG]:continue
  for s in K.L.poly(z['fills'].get(layer,[])):
   if s.intersects(win):add(N.bounded_buffer(s.intersection(win),max(.6,float(z['clearance_mm']))+.025),'NATIVE_OTHER_DOMAIN_FILL_HARD',z['uuid'])
 intended=set_precision(desired.difference(unary_union(common)),1e-6);physical=set_precision(intended.difference(unary_union(physical_only)),1e-6);seed=oldref[layer].union(ann(central))
 if layer=='In4.Cu'and in1oldret:seed=seed.union(ann(oldret))
 keep=[p for p in K.RF.parts(physical)if p.intersection(seed).area>0 and not p.buffer(-.075).is_empty];physical=unary_union(keep);intended=unary_union([p for p in K.RF.parts(intended)if any(p.intersection(s).area>0 for s in keep)])
 if layer=='In1.Cu':in1oldret=physical.intersection(ann(oldret)).area>0
 old=next(z for z in q if z['uuid']==('9fe010df-73cf-5bfb-9f7a-bd227b701c3e'if layer=='In1.Cu'else'ee0efe05-1705-587c-ac86-49b1a7885ef9'));nz={**old,'shape':physical,'zone_outline_shape':intended};newzones.append(nz)
 caps={sig['uuid']:.525,oldA['uuid']:.575,clock['uuid']:.375};own=unary_union([N.bounded_disk(sigports[u],radius)for u,radius in caps.items()]);rawgap=bodies.difference(oldref[layer].union(physical));outside=rawgap.difference(own)
 rows.append({'layer':layer,'UUID':old['uuid'],'actual_source_seed':seedrows[layer],'source_connected_physical_components':len(keep),'physical_mm2':physical.area,'intended_mm2':intended.area,'physical_outside_intended_empty':physical.difference(intended).is_empty,'shared_return_annular_overlap_mm2':physical.intersection(ann(central)).area,'old_A_return_annular_overlap_mm2':physical.intersection(ann(oldret)).area,'full_field_body_raw_gap_mm2':rawgap.area,'outside_exact_distinct_actual_signal_caps_mm2':outside.area,'outside_exact_caps_empty':outside.is_empty,'native_old_clock_actual_inner_flashes':clock['flashed'],'old_CLOCK_cap_uses_actual_unflashed_drill_only':True,'all_after_actual_source_and_cap_authority_gates':'OPEN'})
 (OUT/(layer+'-physical.wkb')).write_bytes(physical.wkb);(OUT/(layer+'-intended.wkb')).write_bytes(intended.wkb);ledgers.append({'layer':layer,'cutters':ledger})
packet={'joint_geometry':r,'replace_only_two_FG_zones':newzones,'FG_native_actual_seed_rows':seedrows,'all_original_native_Cu_and_Host_R238_objects_retained_except_restored_clock_and_unadopted_field_bodies':True,'source_current_reference_native_gate':'OPEN'};pp=OUT/'proposed-two-plane-and-joint-geometry.pkl';pp.write_bytes(pickle.dumps(packet,protocol=5));(OUT/'cut-authorities.json').write_text(json.dumps(ledgers,indent=1)+'\n');result={'verdict':'SHARED_RETURN_REAL_SOURCE_SEEDED_FG_REFERENCE_PLANES_NOMINATED_ALL_AFTER_GATES_OPEN','base_model_sha256':sha(mp),'joint_geometry_receipt_sha256':sha(rp),'packet_sha256':sha(pp),'rows':rows,'old_9fe_ee_roles_absent_before_actual_source_seed':True,'no_cap_borrow_or_expansion':True,'native_jobs':0,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('R240_PLANES',json.dumps(rows),sha(OUT/'receipt.json'),flush=True)
