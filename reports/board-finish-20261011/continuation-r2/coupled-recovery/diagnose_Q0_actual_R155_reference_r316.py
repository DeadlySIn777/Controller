"""Saved Q0 endpoints on the exact current head; nominate actual local reference repair."""
from pathlib import Path
import sys,json,pickle,hashlib
H=Path(__file__).resolve().parent;P=H.parent;sys.dont_write_bytecode=True
for p in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from shapely.geometry import Point,box
from shapely.ops import unary_union,nearest_points
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
model=P/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert sha(model)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';g,h,b,q,current=pickle.loads(model.read_bytes())
audit=P/'field-power/REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368/receipt.json';assert sha(audit)=='e4a9373b5816de6926cc3b3cea82d1751e5db6cb70d9f150443dff577afff29e'
groupfile=audit.parent/'actual-drilled-current-groups.pkl';gh=sha(groupfile);groups=pickle.loads(groupfile.read_bytes());ground='/motherboard_motors/FIELD_GND';net='/motherboard_do/DOA_Q0_READY_N';root=K.root(groups[ground],'J11003','2');ref=K.source_refs(root)['F.Cu'];context=K.hole_context(current);_,sg=K.physical(current,net,context);desired={p['uuid']for p in current['pads']if K.L.norm(p['net'])==net and(p['ref'],str(p['num']))in{('R10016','1'),('U10004','1')}};assert len(desired)==2
needed=[xs for xs in sg if desired&{r['uuid']for r in xs if r['kind']=='pad'}];assert len(needed)==2
out=H/'Q0-current-R155-source-reference-blockers-r316';assert not out.exists();out.mkdir();window=box(219,148,241,176);(out/'actual-J11003-In1-rooted-reference-local.wkb').write_bytes(ref.intersection(window).wkb);rows=[];physical=K.L.body
for i,xs in enumerate(needed):
 term=unary_union([r['shape']for r in xs if r['layer']=='F.Cu']);gap=term.difference(ref);near=nearest_points(term,ref);overlaps=[]
 for gi,gg in enumerate(groups[ground]):
  if gg is root:continue
  plane=unary_union([r['shape']for r in gg if r['kind']=='fill'and r['layer']=='In1.Cu']);area=term.intersection(plane).area
  if not area:continue
  pair=nearest_points(plane,ref);overlaps.append({'old_ground_group_index':gi,'actual_unrooted_In1_body_overlap_mm2':area,'distance_to_actual_source_In1_mm':pair[0].distance(pair[1]),'closest_actual_unrooted_point_mm':[pair[0].x,pair[0].y],'closest_actual_rooted_point_mm':[pair[1].x,pair[1].y],'all_old_group_ground_pad_identities':sorted({(r['uuid'],r['ref'],str(r['pin']))for r in gg if r['kind']=='pad'}),'old_group_via_layer_keys':sorted({(r['uuid'],r['layer'])for r in gg if r['kind']=='via'})})
  (out/('group%d-ground-component%d-In1-local.wkb'%(i,gi))).write_bytes(plane.intersection(window).wkb)
 vias=[]
 for v in current['vias']:
  if K.L.norm(v['net'])!=ground:continue
  d=term.distance(Point(v['x'],v['y']))
  if d>8:continue
  keys=sorted({r['layer']for r in root if r['kind']=='via'and r['uuid']==v['uuid']});vias.append({'uuid':v['uuid'],'at_mm':[v['x'],v['y']],'native_diameter_drill_mm':[v['d'],v['drill']],'actual_rooted_layer_keys':keys,'distance_to_target_F_group_mm':d})
 vias.sort(key=lambda r:r['distance_to_target_F_group_mm'])
 (out/('group%d-current-F-body.wkb'%i)).write_bytes(term.wkb);(out/('group%d-unreferenced-F-body.wkb'%i)).write_bytes(gap.wkb)
 rows.append({'group':i,'exact_current_group_pad_identities':sorted({(r['uuid'],r['ref'],str(r['pin']))for r in xs if r['kind']=='pad'}),'all_actual_group_layer_keys':sorted(K.keys(xs)),'F_body_area_mm2':term.area,'actual_source_In1_overlap_mm2':term.intersection(ref).area,'actual_source_In1_full_body_gap_mm2':gap.area,'distance_to_rooted_In1_mm':near[0].distance(near[1]),'nearest_target_F_point_mm':[near[0].x,near[0].y],'nearest_actual_rooted_In1_point_mm':[near[1].x,near[1].y],'overlapping_unrooted_actual_ground_In1_groups':overlaps,'nearest_actual_FIELD_GND_barrels':vias[:12]})
receipt={'verdict':'Q0_CURRENT_EXACT_SOURCE_REFERENCE_LOCAL_DIAGNOSIS_ONLY','model_file':str(model),'model_sha256':sha(model),'R368_audit_file':str(audit),'R368_audit_sha256':sha(audit),'R368_current_drilled_groups_file':str(groupfile),'R368_current_drilled_groups_sha256':gh,'root':'J11003.2','ground_net':ground,'signal_net':net,'rows':rows,'all_current_R155_R368_reference_production_failures_preserved':True,'no_ground_plane_by_name_or_generic_disk_credit':True,'nomination_not_independent_full_graph_or_native_acceptance':True,'native_jobs':0,'model_or_board_written':False,'adopted':False,'helper_sha256':sha(__file__)};put(out/'receipt.json',receipt);print(json.dumps({'receipt_file':str(out/'receipt.json'),'receipt_sha256':sha(out/'receipt.json'),'rows':rows}),flush=True)
