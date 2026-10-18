"""Actual foreign Cu guard and literal untouched-net checks for R253."""
import hashlib,json,pickle,sys,collections
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
OUT=H/'joint-R253-two-new-FG-planes-true-foreign-and-untouched-physics-r258';assert not OUT.exists();OUT.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
bp=H/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262/model.pkl';mp=H/'U10003-HOST-field-joint-current-exact-raw-precision-bound-r253/model.pkl';assert sha(bp)=='64a1f6e1597c9d757b187c3b6db85d79685ee376399bdd4738f915b87b1a0144'and sha(mp)=='765ce30b24ed3109b7c938f964775690a99f08504c464313bcf712b078421440'
g,h0,b0,q0,c0=pickle.loads(bp.read_bytes());g1,h,b,q,c=pickle.loads(mp.read_bytes());assert g1==g
scope={'/IO_3V3','/LOGIC_GND','/motherboard_do/DOA_FLT_N_FIELD','/motherboard_do/DOA_SDI_HOST','/motherboard_motors/FIELD_GND'};norm=K.L.norm
for kind in('tracks','vias','pads','zones'):
 assert [x for x in c0[kind]if norm(x['net'])not in scope]==[x for x in c[kind]if norm(x['net'])not in scope],kind
oldq={z['uuid']:z for z in q0}
for z in q:
 if norm(z['net'])in scope:continue
 old=oldq[z['uuid']];assert all(z[r].wkb==old[r].wkb for r in('shape','zone_outline_shape'));assert {k:v for k,v in z.items()if k not in('shape','zone_outline_shape')}=={k:v for k,v in old.items()if k not in('shape','zone_outline_shape')}
oldvia={v['uuid']:v for v in h0['vias']};newvia=[v for v in h['vias']if v['uuid']not in oldvia];records,trees=K.F.build(c0);drillhits=[]
for v in newvia:
 hole=Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)
 for ly in K.LAYERS:
  for j in trees[ly].query(hole,predicate='intersects'):
   r=records[ly][int(j)]
   if norm(r['net'])in scope:continue
   sh=hole.intersection(r['shape'])
   if not sh.is_empty:drillhits.append({'new_drill':v['uuid'],'old_UUID':r['uuid'],'kind':r['kind'],'net':norm(r['net']),'layer':ly,'literal_area_mm2':sh.area,'literal_length_mm':sh.length})
fg='/motherboard_motors/FIELD_GND';planes=[z for z in q if z['uuid']in{'9fe010df-73cf-5bfb-9f7a-bd227b701c3e','ee0efe05-1705-587c-ac86-49b1a7885ef9'}];assert len(planes)==2
rec,tr=K.F.build({**h,'zones':[]});dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom[norm(a)]==dom[norm(bb)]else.6;rows=[];errors=[];nativeerrors=[];enclosures=[]
for z in planes:
 sh=z['shape'];ly=z['layer'];out=sh.difference(z['zone_outline_shape']);enclosures.append({'UUID':z['uuid'],'physical_outside_intent_empty':out.is_empty,'literal_area_mm2':out.area,'literal_length_mm':out.length})
 for j in tr[ly].query(sh.buffer(.8),predicate='intersects'):
  r=rec[ly][int(j)];net=norm(r['net'])
  if net==fg:continue
  if r['kind']=='via':v=r['source'];d=sh.distance(Point(v['x'],v['y']))-v['d']/2
  elif r['kind']=='track'and not r['source'].get('m'):t=r['source'];d=sh.distance(LineString([t['a'],t['b']]))-t['w']/2
  else:d=sh.distance(r['shape'])
  req=max(float(z['clearance_mm']),gap(net,fg))+.025;row={'zone':z['uuid'],'layer':ly,'foreign_kind':r['kind'],'foreign_UUID':r['uuid'],'net':net,'actual_gap_mm':d,'required_planner_gap_mm':req};rows.append(row)
  if d<req:errors.append(row)
 for peer in c['zones']:
  if norm(peer['net'])==fg:continue
  rr=unary_union(K.L.poly(peer['fills'].get(ly,[])))
  if rr.is_empty or rr.distance(sh)>.8:continue
  d=rr.distance(sh);req=max(float(z['clearance_mm']),float(peer['clearance_mm']),gap(peer['net'],fg))+.025;row={'zone':z['uuid'],'layer':ly,'foreign_kind':'actual_native_or_owned_filled_plane','foreign_UUID':peer['uuid'],'net':norm(peer['net']),'actual_gap_mm':d,'required_planner_gap_mm':req};rows.append(row)
  if d<req:errors.append(row)
 for rule in h['rule_areas']:
  if rule.get('no_zones')and ly in rule['layers']:
   other=unary_union(K.L.poly(rule['outline']));hit=sh.intersection(other);intent=z['zone_outline_shape'].intersection(other)
   if not hit.is_empty or not intent.is_empty:nativeerrors.append({'zone':z['uuid'],'rule':rule['uuid'],'physical_hit_empty':hit.is_empty,'intended_hit_empty':intent.is_empty})
 untouched={norm(x['net'])for kind in('tracks','vias','pads','zones')for x in c0[kind]}-scope
 print('R258_PLANE',ly,len(rows),len(errors),flush=True)
holes,ht=K.hole_context(c);_,groups=K.physical(c,'/LOGIC_GND',(holes,ht));root=K.root(groups,'J11001','2');ref=unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']=='In4.Cu']);smdbody=[]
for p in h['pads']:
 if p['ref']!='R10007':continue
 body=unary_union(K.L.poly(p['layers']['B.Cu']));remaining=body.difference(ref);smdbody.append({'pad':p['num'],'UUID':p['uuid'],'whole_body_actual_J1_In4_reference_gap_empty':remaining.is_empty,'area_mm2':remaining.area,'length_mm':remaining.length})
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
put('all-new-FG-foreign-planner-guards.json',rows);put('all-new-FG-foreign-planner-failures.json',errors);put('all-new-FG-native-nozone-errors.json',nativeerrors);put('new-drill-old-unselected-Cu-hits.json',drillhits);put('both-moved-HOST-resistor-whole-body-J1-reference.json',smdbody)
ok=not errors and not nativeerrors and not drillhits and all(x['physical_outside_intent_empty']for x in enclosures)and all(x['whole_body_actual_J1_In4_reference_gap_empty']for x in smdbody)
put('receipt.json',{'status':'SCOPED_NEW_PLANES_AND_UNTOUCHED_PHYSICS_PASS_NATIVE_OPEN'if ok else'SCOPED_NEW_PLANE_OR_UNTOUCHED_PHYSICS_REPAIR_REQUIRED','base_SHA256':sha(bp),'model_SHA256':sha(mp),'untouched_nets':len(untouched),'all_unselected_Cu_pad_FP_and_filled_arrays_exact':True,'new_drill_unselected_native_Cu_hit_count':len(drillhits),'new_FG_true_guard_count':len(rows),'new_FG_true_guard_failure_count':len(errors),'native_nozone_error_count':len(nativeerrors),'physical_intent_enclosures':enclosures,'both_actual_moved_HOST_resistor_pads':smdbody,'native_integer_splice_actual_fill_fullDRC_source_currents_SI':'OPEN','native_jobs':0,'adopted':False,'manufacturing_ready':False});print('R258_COMPLETE',ok,sha(OUT/'receipt.json'),flush=True)
