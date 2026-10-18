"""Read-only R112 authority audit of only the saved R256 discrete delta.

No failed R246 model is imported, no fills are retreated, and no native job is
started. Full current-head source/contact/reference/native gates remain open.
"""
import copy,hashlib,json,pickle,sys,traceback
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as GP
from audit_field_io3_crossings_r15e import losses
O=H/'sbc-power/T4-R256-discrete-only-exact-R112-independent-r257'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):Path(p).write_text(json.dumps(r,indent=1)+'\n')
def root(gs,ref,pin):return next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,pin)for q in xs))
def main():
 assert not O.exists();O.mkdir()
 mp=H/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112/model.pkl';assert sha(mp)=='6312b10a88b2d3614e21760d1709866d2417b419d418e20e09055eb13b8e3b7e'
 dp=H/'sbc-power/T4-duplicate-CORE5-fullwidth-detour-nominee-r256/proposed-discrete.pkl';delta=pickle.loads(dp.read_bytes());assert not delta['vias'];adds=delta['tracks'];removed=set(delta['removed_original_track_UUIDs']);assert len(adds)==7 and len(removed)==2
 g,h,b,z,before=pickle.loads(mp.read_bytes());after=copy.deepcopy(before);old=[t for t in before['tracks']if t['uuid']in removed];assert len(old)==2
 assert all((t['net'],t['layer'],t['w'],t['a'],t['b'])==('/mc_local_power{slash}CORE_5V','F.Cu',1.25,[154.65,96.65],[167.75,96.65])for t in old)
 after['tracks']=[t for t in before['tracks']if t['uuid']not in removed]+adds
 oldbody=GP.bounded_buffer(LineString([old[0]['a'],old[0]['b']]),.625)
 cb=unary_union([GP.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2)for t in adds if C.norm(t['net'])==C.norm(old[0]['net'])])
 gb=unary_union([GP.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2)for t in adds if t['net']=='/LOGIC_GND'])
 rec,trees=F.build(after,layers={'F.Cu'});checks=[];errors=[];contacts=[]
 for t in adds:
  axis=LineString([t['a'],t['b']]);body=GP.bounded_buffer(axis,t['w']/2);novel=body.difference(oldbody)if C.norm(t['net'])==C.norm(old[0]['net'])else body
  for j in trees['F.Cu'].query(body.buffer(.8),predicate='intersects'):
   r=rec['F.Cu'][int(j)]
   if C.norm(r['net'])==C.norm(t['net']):continue
   if r['kind']=='track':q=r['source'];target=GP.bounded_buffer(LineString([q['a'],q['b']]),q['w']/2);gap=axis.distance(LineString([q['a'],q['b']]))-(t['w']+q['w'])/2
   elif r['kind']=='via':q=r['source'];target=GP.bounded_disk(q,q['d']/2);gap=axis.distance(Point(q['x'],q['y']))-(t['w']+q['d'])/2
   else:target=r['shape'];gap=axis.distance(target)-t['w']/2
   req=GP.G.gap(h,t['net'],r['net'])+.025;ng=novel.distance(target)if not novel.is_empty else float('inf');row={'new_UUID':t['uuid'],'foreign_UUID':r['uuid'],'foreign_kind':r['kind'],'foreign_raw_net':r['net'],'full_true_gap_mm':gap,'novel_body_gap_mm':ng,'required_mm':req,'inherited_unchanged_CORE5_anchor_only':gap<req and ng>=req};checks.append(row)
   if gap<req and ng<req:errors.append(row)
  for v in after['vias']:
   if C.norm(v['net'])==C.norm(t['net']):continue
   if Point(v['x'],v['y']).distance(axis)>t['w']/2+v['drill']/2+.4:continue
   hole=GP.bounded_disk(v,v['drill']/2+.00000002);gap=body.distance(hole)-.005;ng=novel.distance(hole)-.005
   row={'new_UUID':t['uuid'],'foreign_UUID':v['uuid'],'foreign_kind':'ordinary_drill','full_true_gap_mm':gap,'novel_body_gap_mm':ng,'required_mm':.275};checks.append(row)
   if gap<.275 and ng<.275:errors.append(row)
 # Ledger every finite actual R112 F contact, including fills. Retained old
 # pieces are checked as whole polygons and later by their physical graph.
 rr,_=F.build(before,nets={C.norm(old[0]['net'])},layers={'F.Cu'})
 for r in rr['F.Cu']:
  if r['uuid']in removed:continue
  inter=r['shape'].intersection(oldbody)
  if inter.area<=0:continue
  ps=[r['shape']]if r['shape'].geom_type=='Polygon'else list(r['shape'].geoms)
  for i,p in enumerate(ps):
   if p.intersection(oldbody).area<=0:continue
   contacts.append({'kind':r['kind'],'UUID':r['uuid'],'layer':r['layer'],'contour':r.get('contour'),'piece':i,'whole_original_piece_WKB_sha256':hashlib.sha256(p.wkb).hexdigest(),'old_contact_mm2':p.intersection(oldbody).area,'new_contact_mm2':p.intersection(cb).area})
 put(O/'true-geometry-checks.json',checks);put(O/'true-geometry-errors.json',errors);put(O/'every-old-shared-contact-piece.json',contacts)
 affected={C.norm(t['net'])for t in adds};gs=pickle.loads((mp.parent/'groups.pkl').read_bytes());newgs={};crow=[]
 for net in sorted(affected):
  oldgs=gs.get(net)or F.graph(before,net);ng=F.graph(after,net);newgs[net]=ng
  # Only the two explicitly owned duplicate track keys are allowed removal;
  # all relationships among every other prior physical item remain required.
  kept=[[r for r in xs if not(r['kind']=='track'and r['uuid']in removed)]for xs in oldgs];bad=losses(kept,ng)
  crow.append({'net':net,'old_groups':len(oldgs),'new_groups':len(ng),'authorized_removed_duplicate_track_UUIDs':sorted(removed)if net==C.norm(old[0]['net'])else [],'all_other_old_relationship_losses':bad});print('R257_GRAPH',net,len(bad),flush=True)
 lg=root(newgs['/LOGIC_GND'],'J11001','2');oldlg=root(gs['/LOGIC_GND'],'J11001','2');lost=F.discrete_keys(oldlg)-F.discrete_keys(lg);ref=unary_union([r['shape']for r in lg if r['kind']=='fill'and r['layer']=='In1.Cu'])
 newrefs=[]
 for t in adds:
  body=GP.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2);gap=body.difference(ref);f=O/(t['uuid']+'-fullbody-In1-source-reference-gap.wkb');f.write_bytes(gap.wkb);newrefs.append({'UUID':t['uuid'],'raw_net':t['net'],'fullbody_actual_source_reference_gap_mm2':gap.area,'gap_empty':gap.is_empty,'gap_sha256':sha(f)})
 endpoint={pin:any(r['kind']=='pad'and(r['ref'],r['pin'])==('U1001',pin)for r in lg)for pin in('T4','T1','R7')}
 pads={pin:next(p for p in before['pads']if(p['ref'],p['num'])==('U1001',pin))for pin in('T4','T1','R7')}
 padtouch={pin:gb.intersection(unary_union(C.poly(pads[pin]['layers']['F.Cu']))).area for pin in('T4','T1')}
 put(O/'affected-contact-graphs.json',crow);put(O/'new-fullbody-source-reference.json',newrefs);put(O/'literal-endpoints.json',{'pads':pads,'ground_pad_touch_mm2':padtouch,'actual_J11001_2_source_membership':endpoint,'prior_logic_root_keys_lost':[list(x)for x in sorted(lost)]})
 unchanged={key:before[key]==after[key]for key in before if key!='tracks'};assert all(unchanged.values());assert all(t in before['tracks']for t in after['tracks']if t['uuid']not in {a['uuid']for a in adds})
 ok=not errors and not any(x['new_contact_mm2']<=0 for x in contacts)and not any(r['all_other_old_relationship_losses']for r in crow)and not lost and all(r['gap_empty']for r in newrefs)and endpoint['T4']and endpoint['T1']and all(v>0 for v in padtouch.values())
 put(O/'receipt.json',{'verdict':'PASS_SCOPED_EXACT_R112_T4_DISCRETE_ONLY_GRAPH_REFERENCE_GEOMETRY'if ok else'FAIL_SCOPED_EXACT_R112_T4_DISCRETE_ONLY_AUDIT','exact_R112_model_sha256':sha(mp),'R256_discrete_delta_sha256':sha(dp),'whole_stale_model_overlay_used':False,'unchanged_nontrack_model_fields':unchanged,'true_checks':len(checks),'true_errors':len(errors),'old_shared_pieces':len(contacts),'old_shared_piece_lost_contacts':sum(x['new_contact_mm2']<=0 for x in contacts),'affected_graph_relationship_loss_count':sum(len(r['all_other_old_relationship_losses'])for r in crow),'prior_logic_source_root_key_loss_count':len(lost),'new_body_reference_gap_count':sum(not r['gap_empty']for r in newrefs),'actual_FPGA_ground_source_membership':endpoint,'exact_native_T1_barrel_topology_authority':str((H/'sbc-power/CORE-R112-exact-ground-cross-layer-topology-r249/receipt.json').resolve()),'no_original_or_prospective_plane_edit':True,'full_current_head_77nets_seven_sources_strict_old_refs_full_loaded_drop_transient_current_native':'OPEN','R7_ground_obligation_retained':True,'full_0p8A_CORE_2A_IO3_7p882A_CORE5_not_reduced':True,'native_jobs':0,'board_written':False,'script_sha256':sha(__file__)})
 print('R257_COMPLETE',ok,sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
