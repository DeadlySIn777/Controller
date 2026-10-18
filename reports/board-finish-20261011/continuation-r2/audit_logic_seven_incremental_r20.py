"""Independent strict geometry and all affected old contacts for the R18 delta."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'): os.environ[n]='2'
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for p in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/p))
import contact_layout as C
import fast_contacts as F
from audit_field_io3_crossings_r15e import losses
import physical_reference_losses_r1 as REF

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,r):Path(p).write_text(json.dumps(r,indent=1)+'\n')
def main():
 base=H/'corrected-joint-ground-base-r11/model.pkl';mp=H/'logic-source-union-reuse-return-restoration-r18/model.pkl';out=H/'logic-seven-independent-incremental-r20'
 assert not out.exists()
 assert sha(base)=='24de27f569c8f4ae56b4172e6fc1af374c4f86c12d56215a2989eb793d2a55a8'
 assert sha(mp)=='20ae7a0558877ba76300f2163b920c77fe96c5861a930fb7b22570f665ad37b8'
 g,h,b,z,after=pickle.loads(mp.read_bytes());bg,bh,bb,bz,before=pickle.loads(base.read_bytes())
 assert g==bg and h==bh and b==bb
 byid={q['uuid']:q for q in z};bid={q['uuid']:q for q in bz};assert len(byid)==len(z)
 for uid,q in bid.items():
  n=byid[uid];assert q.keys()==n.keys()
  for k,v in q.items():assert (v.equals(n[k]) if hasattr(v,'equals') else v==n[k]),(uid,k)
 added=pickle.loads(mp.with_name('proposed-zones.pkl').read_bytes());assert len(added)==7
 assert set(byid)-set(bid)=={q['uuid'] for q in added}
 for q in added:assert q['shape'].equals(byid[q['uuid']]['shape']) and C.norm(q['net'])=='/LOGIC_GND'
 out.mkdir();records,trees=F.build({**h,'zones':[]});pe=[];ze=[]
 def need(raw,other,local):return max(.15 if h['domains_normalized'][C.norm(raw)]==h['domains_normalized'][C.norm(other)] else .6,local)+.025
 def gap(sh,q):
  if q['kind']=='via':v=q['source'];return sh.distance(Point(v['x'],v['y']))-v['d']/2
  if q['kind']=='track':t=q['source'];return sh.distance(LineString([t['a'],t['b']]))-t['w']/2
  return sh.distance(q['shape'])
 for q in added:
  for i in trees[q['layer']].query(q['shape'].buffer(1.5),predicate='intersects'):
   r=records[q['layer']][int(i)]
   if r['net']==q['net']:continue
   d=gap(q['shape'],r);n=need(q['net'],r['net'],float(q.get('clearance_mm',.15)))
   if d<n:pe.append({'zone_uuid':q['uuid'],'other_uuid':r['uuid'],'other_kind':r['kind'],'layer':q['layer'],'actual_mm':d,'required_mm':n})
  for r in z:
   if r['net']==q['net'] or r['layer']!=q['layer']:continue
   d=q['shape'].distance(r['shape']);n=need(q['net'],r['net'],max(float(q.get('clearance_mm',.15)),float(r.get('clearance_mm',.15))))
   if d<n:ze.append({'zone_uuid':q['uuid'],'other_uuid':r['uuid'],'layer':q['layer'],'actual_mm':d,'required_mm':n})
 write(out/'analytic-geometry.json',{'physical_errors':pe,'foreign_owned_zone_errors':ze,'comparison':'strict gap >= full electrical requirement +0.025mm, no deficit waiver','true_round_track_caps_and_via_radii':True})
 beforez={q['uuid']:q for q in before['zones']};changed=[];nets={'/LOGIC_GND'}
 for q in after['zones']:
  prior=beforez.get(q['uuid'])
  if prior is None or q['fills']!=prior['fills']:
   nets.add(C.norm(q['net']));changed.append({'uuid':q['uuid'],'net':q['net'],'new_zone':prior is None})
 assert {q['uuid'] for q in before['zones']}<={q['uuid'] for q in after['zones']}
 write(out/'changed-fill-net-ledger.json',changed);rows=[];groups={};oldgroups={}
 for net in sorted(nets):
  a=F.graph(before,net);n=F.graph(after,net);bad=losses(a,n);groups[net]=n;oldgroups[net]=a
  row={'net':net,'before_groups':len(a),'after_groups':len(n),'old_discrete_contact_losses':bad};rows.append(row);write(out/'contact-checkpoint.json',rows)
  print('R20_CONTACT',net,len(a),len(n),'losses',len(bad),flush=True)
 sources=[];refs=[]
 for net,ref in [('/LOGIC_GND','J11001'),('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005')]:
  a=oldgroups.get(net);n=groups.get(net)
  if a is None:a=F.graph(before,net);n=F.graph(after,net)
  ar=next(xs for xs in a if any(q['kind']=='pad' and (q['ref'],q['pin'])==(ref,'2') for q in xs));nr=next(xs for xs in n if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,'2') for q in xs))
  lost=F.discrete_keys(ar)-F.discrete_keys(nr);sources.append({'net':net,'actual_source':ref+'.2','before_named_pads':len({q['uuid'] for q in ar if q['kind']=='pad' and q['pin']}),'after_named_pads':len({q['uuid'] for q in nr if q['kind']=='pad' and q['pin']}),'lost_prior_source_keys':[list(k)for k in sorted(lost)]})
  oldref={o:unary_union([q['shape']for q in ar if q['layer']==l and q['kind']=='fill'])for o,l in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};newref={o:unary_union([q['shape']for q in nr if q['layer']==l and q['kind']=='fill'])for o,l in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]}
  bad,diag=REF.audit(before,oldref,newref,net);refs.append({'net':net,'retained_outer_reference_losses':bad,'proof':diag});write(out/'reference-checkpoint.json',refs)
  print('R20_SOURCE_REFERENCE',net,'source_losses',len(lost),'reference_losses',len(bad),flush=True)
 (out/'groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));ok=not pe and not ze and not any(q['old_discrete_contact_losses']for q in rows) and not any(q['lost_prior_source_keys']for q in sources) and not any(q['retained_outer_reference_losses']for q in refs)
 write(out/'receipt.json',{'verdict':'PASS_SEVEN_NEW_LOGIC_PIECES_INCREMENTAL_HOST_GEOMETRY_CONTACT_SOURCE_REFERENCE_NATIVE_CURRENT_OPEN'if ok else'FAIL_INCREMENTAL_SEVEN_LOGIC_PIECES_REPAIR_REQUIRED','model_sha256':sha(mp),'parent_model_sha256':sha(base),'added_zones_sha256':sha(mp.with_name('proposed-zones.pkl')),'all_original_Cu_holes_source_poses_native_outlines_unchanged_to_parent':True,'affected_net_contacts':rows,'source_roots':sources,'outer_reference_proof_sha256':sha(out/'reference-checkpoint.json'),'analytic_geometry_sha256':sha(out/'analytic-geometry.json'),'physical_error_count':len(pe),'foreign_new_zone_error_count':len(ze),'parent_known_FAG_planning_deficit':'5.26nm vs pad600473a0 remains separate explicit new-shape correction obligation','full_board_native_current_thermal_gates':'OPEN','script_sha256':sha(__file__),'adopted':False,'board_written':False,'native_jobs':0})
 print('R20_COMPLETE',ok,'physical',len(pe),'foreign',len(ze),sha(out/'receipt.json'),flush=True)
if __name__=='__main__':main()
