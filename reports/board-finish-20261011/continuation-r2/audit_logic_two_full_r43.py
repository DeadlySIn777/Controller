"""Independent strict geometry and all affected old contacts for the two R42 returns against the exact R22 parent."""
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
 base=H/'safe-logic-five-and-fag-margin-r22/model.pkl';mp=H/'logic-two-reference-safe-return-restoration-r42/model.pkl';out=H/'logic-two-independent-full-r43'
 assert not out.exists()
 assert sha(base)=='014b37594d378cd3e1a606cb1c06a0ad0b1b3ffea5cb836132bfaeec80d3a52a'
 assert sha(mp)=='a4baedbfbccc92930a22c946b1e4e5262287d59b60b2a1e529bfddfa75c398ba'
 g,h,b,z,after=pickle.loads(mp.read_bytes());bg,bh,bb,bz,before=pickle.loads(base.read_bytes())
 assert g==bg and h==bh and b==bb
 byid={q['uuid']:q for q in z};bid={q['uuid']:q for q in bz};assert len(byid)==len(z)
 for uid,q in bid.items():
  n=byid[uid];assert q.keys()==n.keys()
  for k,v in q.items():assert (v.equals(n[k]) if hasattr(v,'equals') else v==n[k]),(uid,k)
 added=pickle.loads(mp.with_name('proposed-zones.pkl').read_bytes());assert len(added)==2
 assert set(byid)-set(bid)=={q['uuid'] for q in added}
 for q in added:assert q['shape'].equals(byid[q['uuid']]['shape']) and C.norm(q['net'])=='/LOGIC_GND'
 out.mkdir();records,trees=F.build({**h,'zones':[]});pe=[];ze=[];he=[];ke=[]
 holes=[(p['uuid'],p['net'],s)for p in h['pads']for s in C.poly(p.get('hole')or [])]+[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=256))for v in h['vias']]
 from shapely.strtree import STRtree
 hole_tree=STRtree([s for uid,raw,s in holes])
 def need(raw,other,local):return max(.15 if h['domains_normalized'][C.norm(raw)]==h['domains_normalized'][C.norm(other)] else .6,local)+.025
 def gap(sh,q):
  if q['kind']=='via':v=q['source'];return sh.distance(Point(v['x'],v['y']))-v['d']/2
  if q['kind']=='track':t=q['source'];return sh.distance(LineString([t['a'],t['b']]))-t['w']/2
  return sh.distance(q['shape'])
 for q in added:
  for i in hole_tree.query(q['shape'].buffer(.3),predicate='intersects'):
   uid,raw,s=holes[int(i)]
   if raw==q['net']:continue
   d=q['shape'].distance(s)
   if d<.275:he.append({'zone_uuid':q['uuid'],'hole_uuid':uid,'actual_mm':d,'required_mm':.275})
  for rule in h['rule_areas']:
   if rule.get('no_zones') and q['layer'] in rule['layers']:
    for s in C.poly(rule['outline']):
     if q['shape'].intersects(s.buffer(.025)):ke.append({'zone_uuid':q['uuid'],'rule_area':rule.get('uuid'),'layer':q['layer']})
  for i in trees[q['layer']].query(q['shape'].buffer(1.5),predicate='intersects'):
   r=records[q['layer']][int(i)]
   if r['net']==q['net']:continue
   d=gap(q['shape'],r);n=need(q['net'],r['net'],float(q.get('clearance_mm',.15)))
   if d<n:pe.append({'zone_uuid':q['uuid'],'other_uuid':r['uuid'],'other_kind':r['kind'],'layer':q['layer'],'actual_mm':d,'required_mm':n})
  for r in z:
   if r['net']==q['net'] or r['layer']!=q['layer']:continue
   d=q['shape'].distance(r['shape']);n=need(q['net'],r['net'],max(float(q.get('clearance_mm',.15)),float(r.get('clearance_mm',.15))))
   if d<n:ze.append({'zone_uuid':q['uuid'],'other_uuid':r['uuid'],'layer':q['layer'],'actual_mm':d,'required_mm':n})
 write(out/'analytic-geometry.json',{'physical_errors':pe,'foreign_owned_zone_errors':ze,'foreign_hole_errors':he,'native_no_zone_area_errors':ke,'comparison':'strict gap >= full electrical requirement +0.025mm, no deficit waiver','true_round_track_caps_and_via_radii':True})
 beforez={q['uuid']:q for q in before['zones']};changed=[];nets={C.norm(q['net']) for q in before['zones']}|{'/LOGIC_GND','/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V'}
 for q in after['zones']:
  prior=beforez.get(q['uuid'])
  if prior is None or q['fills']!=prior['fills']:
   nets.add(C.norm(q['net']));changed.append({'uuid':q['uuid'],'net':q['net'],'new_zone':prior is None})
 assert {q['uuid'] for q in before['zones']}<={q['uuid'] for q in after['zones']}
 write(out/'changed-fill-net-ledger.json',changed);rows=[];groups={};oldgroups={}
 for net in sorted(nets):
  a=F.graph(before,net);n=F.graph(after,net);bad=losses(a,n);groups[net]=n;oldgroups[net]=a
  row={'net':net,'before_groups':len(a),'after_groups':len(n),'old_discrete_contact_losses':bad};rows.append(row);write(out/'contact-checkpoint.json',rows)
  print('R43_CONTACT',net,len(a),len(n),'losses',len(bad),flush=True)
 sources=[];refs=[]
 for net,ref in [('/LOGIC_GND','J11001'),('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005')]:
  a=oldgroups.get(net);n=groups.get(net)
  if a is None:a=F.graph(before,net);n=F.graph(after,net)
  ar=next(xs for xs in a if any(q['kind']=='pad' and (q['ref'],q['pin'])==(ref,'2') for q in xs));nr=next(xs for xs in n if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,'2') for q in xs))
  lost=F.discrete_keys(ar)-F.discrete_keys(nr);sources.append({'net':net,'actual_source':ref+'.2','before_named_pads':len({q['uuid'] for q in ar if q['kind']=='pad' and q['pin']}),'after_named_pads':len({q['uuid'] for q in nr if q['kind']=='pad' and q['pin']}),'lost_prior_source_keys':[list(k)for k in sorted(lost)]})
  oldref={o:unary_union([q['shape']for q in ar if q['layer']==l and q['kind']=='fill'])for o,l in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};newref={o:unary_union([q['shape']for q in nr if q['layer']==l and q['kind']=='fill'])for o,l in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]}
  bad,diag=REF.audit(before,oldref,newref,net);refs.append({'net':net,'retained_outer_reference_losses':bad,'proof':diag});write(out/'reference-checkpoint.json',refs)
  print('R43_SOURCE_REFERENCE',net,'source_losses',len(lost),'reference_losses',len(bad),flush=True)
 (out/'groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));ok=not pe and not ze and not he and not ke and not any(q['old_discrete_contact_losses']for q in rows) and not any(q['lost_prior_source_keys']for q in sources) and not any(q['retained_outer_reference_losses']for q in refs)
 write(out/'receipt.json',{'verdict':'PASS_TWO_NEW_LOGIC_PIECES_FULL_OLD_ZONE_NET_CONTACT_SOURCE_REFERENCE_HOST_GEOMETRY_NATIVE_CURRENT_OPEN'if ok else'FAIL_TWO_LOGIC_PIECES_FULL_CONTACT_SOURCE_REFERENCE_GEOMETRY_REPAIR_REQUIRED','model_sha256':sha(mp),'parent_model_sha256':sha(base),'added_zones_sha256':sha(mp.with_name('proposed-zones.pkl')),'all_original_Cu_holes_source_poses_native_outlines_unchanged_to_parent':True,'affected_net_contacts':rows,'source_roots':sources,'outer_reference_proof_sha256':sha(out/'reference-checkpoint.json'),'analytic_geometry_sha256':sha(out/'analytic-geometry.json'),'physical_error_count':len(pe),'foreign_new_zone_error_count':len(ze),'foreign_hole_error_count':len(he),'native_no_zone_area_error_count':len(ke),'all_old_zone_bearing_net_count':len(nets),'parent_FAG_margin':'R22 outward correction retained exactly; independent R25 strict geometry PASS','full_board_native_current_thermal_gates':'OPEN','script_sha256':sha(__file__),'adopted':False,'board_written':False,'native_jobs':0})
 print('R43_COMPLETE',ok,'physical',len(pe),'foreign',len(ze),sha(out/'receipt.json'),flush=True)
if __name__=='__main__':main()
