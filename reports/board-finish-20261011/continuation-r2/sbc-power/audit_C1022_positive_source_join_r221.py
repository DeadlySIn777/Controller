"""One zero-gap ordinary C1022 IO3 feed, exact positive R214 predecessor."""
import copy,hashlib,json,pickle,sys,traceback
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in ('sbc-power','field-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import complete_geometry_r2 as G
import guarded_declared_settings_projection_r58 as GP
import owned_analytic_track_guards_r75 as AT
import restore_SAFE_generated_precision_states_r168 as PS
import physical_reference_losses_r2 as REF
from audit_field_io3_crossings_r15e import losses
O=H/'sbc-power/C1022-zero-gap-source-feed-independent-r221'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):Path(p).write_text(json.dumps(r,indent=1)+'\n')
def root(gs,ref,pin):return next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,pin) for q in xs))
def main():
 assert not O.exists();O.mkdir();base=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214';assert sha(base/'model.pkl')=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e';assert sha(base/'receipt.json')=='e8eaa4704155b733da2bf32b241a5dcca98d08b5d24d8e7b1ecf4e9b4df73d9e'
 g,h,b,z,before=pickle.loads((base/'model.pkl').read_bytes());PS.restore_bound_generated_precision_states(b,z);h=copy.deepcopy(h)
 nm=H/'sbc-power/remaining-original-IO3-monotone-direct-source-nominees-r220';assert sha(nm/'receipt.json')=='058c220326717e0643436e9b51f41a884c337bb1578e7c270e85a02a8582647a'
 nr=json.loads((nm/'receipt.json').read_text());row=next(r for r in nr['accepted_source_nominations'] if r['ref']=='C1022');assert row['pin']=='1'and row['width_mm']==.3 and row['new_full_body_source_reference_gap_mm2']==0
 adds=[t for t in pickle.loads((nm/'proposed-tracks.pkl').read_bytes()) if t['uuid'] in row['new_track_UUIDs']];assert len(adds)==1 and adds[0]['uuid']=='952d1350-fb0a-5422-b8b6-c2ee31a55c2d'
 t=adds[0];assert (t['net'],t['layer'],t['w'],t['a'],t['b'])==('/IO_3V3','B.Cu',.3,[157.29,92.427],[158.5821,91.6881])
 assert t['uuid'] not in {q['uuid'] for q in h['tracks']};assert all(round(v*1e6)==v*1e6 for xy in (t['a'],t['b']) for v in xy)
 h['tracks']+=adds;z,trackcuts,_=AT.normalize_owned_track_guards({**h,'tracks':adds},z)
 roleledger=[]
 from shapely import set_precision
 for q in z:
  for role in ('shape','zone_outline_shape'):
   raw=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert q[role].wkb==raw;roleledger.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':hashlib.sha256(raw).hexdigest()})
 b=copy.deepcopy(b);b['generated_precision_state_ledger']=roleledger;b['restored_generated_grid_UUIDs']=sorted(q['uuid'] for q in z)
 put(O/'exact-owned-new-track-and-cutter-ledger.json',{'track':t,'originals_deleted':[],'footprints_or_sources_changed':[],'only_this_new_track_to_owned_planes':trackcuts,'nominee_receipt_sha256':sha(nm/'receipt.json'),'full_IO3_A_retained':2.0})
 print('R221_FULL_GUARDED_PROJECTION',flush=True);after,retreat=GP.projected(g,h,z);(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,after),protocol=5));(O/'proposed-tracks.pkl').write_bytes(pickle.dumps(adds,protocol=5));put(O/'oldfill-retreats.json',retreat)
 rec,trees=F.build({**h,'zones':[]});axis=LineString([t['a'],t['b']]);checks=[];errors=[]
 def check(kind,uid,gap,req):
  r={'kind':kind,'owned_UUID':t['uuid'],'foreign_UUID':uid,'actual_gap_mm':gap,'required_mm':req};checks.append(r)
  if gap<req:errors.append(r)
 for j in trees[t['layer']].query(axis.buffer(1.5),predicate='intersects'):
  r=rec[t['layer']][int(j)]
  if r['net']==t['net']:continue
  if r['kind']=='track':a=r['source'];gap=axis.distance(LineString([a['a'],a['b']]))-(t['w']+a['w'])/2
  elif r['kind']=='via':a=r['source'];gap=axis.distance(Point(a['x'],a['y']))-(t['w']+a['d'])/2
  else:gap=axis.distance(r['shape'])-t['w']/2
  check('true_track_capsule_to_'+r['kind'],r['uuid'],gap,G.gap(h,t['net'],r['net'])+.025)
 for q in z:
  if q['layer']==t['layer'] and q['net']!=t['net'] and axis.buffer(1.5).intersects(q['shape']):check('true_track_to_owned_plane',q['uuid'],axis.distance(q['shape'])-t['w']/2,max(G.gap(h,t['net'],q['net']),float(q['clearance_mm']))+.025)
 # Every changed owned plane must retain true cap clearances.
 changed={r['zone_uuid'] for r in trackcuts}
 for q in z:
  if q['uuid'] not in changed:continue
  for j in trees[q['layer']].query(q['shape'].buffer(.7),predicate='intersects'):
   r=rec[q['layer']][int(j)]
   if r['net']==q['net']:continue
   if r['kind']=='track':a=r['source'];gap=q['shape'].distance(LineString([a['a'],a['b']]))-a['w']/2
   elif r['kind']=='via':a=r['source'];gap=q['shape'].distance(Point(a['x'],a['y']))-a['d']/2
   else:gap=q['shape'].distance(r['shape'])
   check('changed_owned_plane_to_'+r['kind'],r['uuid'],gap,max(G.gap(h,q['net'],r['net']),float(q['clearance_mm']))+.025)
 put(O/'analytic-checks.json',checks);put(O/'analytic-errors.json',errors);print('R221_ANALYTIC',len(checks),len(errors),flush=True)
 oldgroups=pickle.loads((base/'groups.pkl').read_bytes());assert len(oldgroups)==77,len(oldgroups);newgroups={};contacts=[]
 for net in sorted(oldgroups):
  new=F.graph(after,net);newgroups[net]=new;bad=losses(oldgroups[net],new);contacts.append({'net':net,'all_retained_old_discrete_relationship_losses':bad});put(O/'contact-checkpoint.json',contacts);print('R221_CONTACT',net,len(bad),flush=True)
 sources=[];refs=[]
 text=Path(REF.__file__).read_text();assert 'if loss.area>1e-9:' in text;text=text.replace('if loss.area>1e-9:','if loss.area>0:').replace("'threshold_mm2':1e-9","'threshold_mm2':0");helper=O/'strict-positive-reference-helper.py';helper.write_text(text);ns={'__file__':str(helper.resolve()),'__name__':'strict_C1022_reference'};exec(compile(text,str(helper),'exec'),ns)
 roots=[('/LOGIC_GND','J11001','2'),('/motherboard_motors/FIELD_GND','J11003','2'),('/motherboard_do/FIELD_B_0V','J11005','2'),('/motherboard_power_entry/FIELD_A_24V_PROTECTED','U11004','17'),('/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006','17'),('/IO_3V3','R18001','2'),('/CORE_1V2','L2001','2')]
 for net,ref,pin in roots:
  a,n=root(oldgroups[net],ref,pin),root(newgroups[net],ref,pin);lost=F.discrete_keys(a)-F.discrete_keys(n);sources.append({'net':net,'actual_source':ref+'.'+pin,'prior_source_keys_lost':[list(k) for k in sorted(lost)],'new_source_named_pad_UUIDs':len({q['uuid'] for q in n if q['kind']=='pad'and q['pin']})})
  if ref in ('J11001','J11003','J11005'):
   aa={out:unary_union([q['shape'] for q in a if q['kind']=='fill'and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')]};bb={out:unary_union([q['shape'] for q in n if q['kind']=='fill'and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')]};bad,proof=ns['audit'](before,aa,bb,net);refs.append({'net':net,'strict_positive_old_reference_losses':bad,'proof':proof})
 lg=root(newgroups['/LOGIC_GND'],'J11001','2');ground=unary_union([q['shape'] for q in lg if q['kind']=='fill'and q['layer']=='In4.Cu']);newbody=GP.bounded_buffer(axis,t['w']/2);gap=newbody.difference(ground);(O/'new-C1022-full-body-source-reference-gap.wkb').write_bytes(gap.wkb)
 io=root(newgroups['/IO_3V3'],'R18001','2');connected=any(q['kind']=='pad'and(q['ref'],q['pin'])==('C1022','1') for q in io)
 (O/'groups.pkl').write_bytes(pickle.dumps(newgroups,protocol=5));put(O/'contact-rows.json',contacts);put(O/'source-rows.json',sources);put(O/'reference-rows.json',refs)
 ok=not errors and not any(r['all_retained_old_discrete_relationship_losses'] for r in contacts)and not any(r['prior_source_keys_lost'] for r in sources)and not any(r['strict_positive_old_reference_losses'] for r in refs)and gap.is_empty and connected
 put(O/'receipt.json',{'verdict':'PASS_SCOPED_C1022_SOURCE_ALL77_CONTACT_SEVEN_SOURCES_STRICT_REFS_AND_TRUE_CU' if ok else 'FAIL_SCOPED_C1022_SOURCE_CONTACT_REFERENCE_OR_CU','exact_positive_R214_model_sha256':sha(base/'model.pkl'),'model_sha256':sha(O/'model.pkl'),'new_track':t,'all77_contact_rows_sha256':sha(O/'contact-rows.json'),'seven_source_rows_sha256':sha(O/'source-rows.json'),'strict_reference_rows_sha256':sha(O/'reference-rows.json'),'analytic_checks':len(checks),'analytic_errors':len(errors),'actual_C1022_1_R18001_2_source_joined':connected,'new_full_body_actual_source_reference_gap_mm2':gap.area,'known_inherited_ROOT42_raw_reference_failure_UNMODIFIED_NOT_WAIVED':True,'remaining_22_old_isolated_IO3_pads_and_original_pad_free_branch':'OPEN','full_IO3_A_retained':2.0,'branch_current_local_cap_loop_native_refill_DRC_final_peer_composition':'OPEN','no_area_or_contact_waiver':True,'new_holes':0,'source_or_FP_changes':0,'native_jobs':0,'board_written':False,'script_sha256':sha(__file__)})
 print('R221_COMPLETE',ok,sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__),'native_jobs':0,'board_written':False})
  raise
