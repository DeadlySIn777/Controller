"""Independent R73-only contact/source/ref delta vs exact R69, no inherited waiver."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
from audit_field_io3_crossings_r15e import losses
import physical_reference_losses_r2 as REF
import guarded_declared_settings_projection_r58 as GP
O=H/'sbc-power/ROOT-R73-independent-all76-five-sources-strict-refs-r208'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):Path(p).write_text(json.dumps(r,indent=1)+'\n')
def main():
 assert not O.exists();O.mkdir();mp=H/'SAFE-monitor-real-source-reference-patch-r73/model.pkl';bp=H/'SAFE-native-monitor-rotation-composition-r69/model.pkl'
 assert sha(mp)=='719da50c88dc6e2c64b988f81c850875f5f228e9f7407eab5c3cd17e8a44f011' and sha(bp)=='89f414490faa8cfdb485fe3ce408d21f1030d67eab7e20e326a581bc5791ff17'
 g,h,b,z,after=pickle.loads(mp.read_bytes());bg,bh,bb,bz,before=pickle.loads(bp.read_bytes());assert g==bg and h==bh
 prior={q['uuid']:q for q in bz};added=[q for q in z if q['uuid'] not in prior];assert len(added)==1 and added[0]['uuid']=='93bd9369-a6ff-537a-8678-5c84db255e75'
 for q in z:
  if q['uuid'] in prior:
   assert q['shape'].wkb==prior[q['uuid']]['shape'].wkb and q['zone_outline_shape'].wkb==prior[q['uuid']]['zone_outline_shape'].wkb
 text=Path(REF.__file__).read_text();assert 'if loss.area>1e-9:' in text;text=text.replace('if loss.area>1e-9:','if loss.area>0:').replace("'threshold_mm2':1e-9","'threshold_mm2':0");hf=O/'strict-positive-reference-helper.py';hf.write_text(text);ns={'__file__':str(hf.resolve()),'__name__':'strict_monitor_reference'};exec(compile(text,str(hf),'exec'),ns)
 nets={C.norm(q['net']) for q in before['zones']};assert len(nets)==76;rows=[];ag={};ng={}
 for net in sorted(nets):
  ag[net]=F.graph(before,net);ng[net]=F.graph(after,net);bad=losses(ag[net],ng[net]);rows.append({'net':net,'old_discrete_contact_losses':bad,'before_groups':len(ag[net]),'after_groups':len(ng[net])});put(O/'contact-checkpoint.json',rows);print('R208_CONTACT',net,len(bad),flush=True)
 sources=[];refs=[]
 for net,ref in [('/LOGIC_GND','J11001'),('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005'),('/IO_3V3','R18001'),('/CORE_1V2','L2001')]:
  root=lambda groups:next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,'2') for q in xs));old,new=root(ag[net]),root(ng[net]);lost=F.discrete_keys(old)-F.discrete_keys(new)
  sources.append({'net':net,'actual_source':ref+'.2','before_named_physical_pad_UUIDs':len({q['uuid'] for q in old if q['kind']=='pad'and q['pin']}),'after_named_physical_pad_UUIDs':len({q['uuid'] for q in new if q['kind']=='pad'and q['pin']}),'lost_prior_source_keys':[list(k) for k in sorted(lost)]})
  if ref in ('J11001','J11003','J11005'):
   a={out:unary_union([q['shape'] for q in old if q['kind']=='fill'and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')]};n={out:unary_union([q['shape'] for q in new if q['kind']=='fill'and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')]};bad,proof=ns['audit'](before,a,n,net);refs.append({'net':net,'retained_reference_losses':bad,'proof':proof});put(O/'reference-checkpoint.json',refs);print('R208_REF',net,len(bad),flush=True)
 fg=next(xs for xs in ng['/motherboard_motors/FIELD_GND'] if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11003','2') for q in xs))
 op=H/'SAFE-native-monitor-rotation-composition-r69/owned-operation.pkl';d=pickle.loads(op.read_bytes())['exact_monitor_delta'];uv=[t for t in d['tracks'] if C.norm(t['net'])!='/motherboard_motors/FIELD_GND'];assert len(uv)==1
 body=GP.bounded_buffer(LineString([uv[0]['a'],uv[0]['b']]),uv[0]['w']/2);ground=unary_union([q['shape'] for q in fg if q['kind']=='fill'and q['layer']=='In1.Cu']);gap=body.difference(ground);gf=O/'new-monitor-UV-full-body-source-reference-gap.wkb';gf.write_bytes(gap.wkb)
 membership=any(q['kind']=='pad'and(q['ref'],q['pin'])==('R9026','2') for q in fg)
 ok=not any(r['old_discrete_contact_losses'] for r in rows)and not any(r['lost_prior_source_keys'] for r in sources)and not any(r['retained_reference_losses'] for r in refs)and gap.is_empty and membership
 (O/'groups.pkl').write_bytes(pickle.dumps(ng,protocol=5));put(O/'receipt.json',{'verdict':'PASS_ROOT_R73_ONLY_INCREMENTAL_ALL76_FIVE_SOURCES_STRICT_OLD_REFS_AND_NEW_UV' if ok else 'FAIL_ROOT_R73_ONLY_INCREMENTAL_SCOPE','model_sha256':sha(mp),'baseline_R69_sha256':sha(bp),'all76_rows':rows,'five_sources':sources,'strict_reference_file':str((O/'reference-checkpoint.json').resolve()),'strict_reference_sha256':sha(O/'reference-checkpoint.json'),'new_UV_reference_gap_mm2':gap.area,'new_UV_reference_gap_sha256':sha(gf),'R9026_ground_actual_J3_source_rooted':membership,'known_inherited_ROOT42_raw_reference_failure_unmodified_and_NOT_WAIVED':True,'source_Vin_threshold_current_loop_native_DRC_final_composition':'OPEN','no_area_waiver':True,'board_written':False,'native_jobs':0,'script_sha256':sha(__file__)});print('R208_COMPLETE',ok,sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
