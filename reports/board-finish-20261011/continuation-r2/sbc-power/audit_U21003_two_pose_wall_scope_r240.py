"""Independently screen both local FP poses and all exact nominated tracks."""
import json,hashlib,pickle,sys,math
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in('sbc-power','field-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as GP
import audit_aux_exact_raw as A
O=H/'sbc-power/U21003-two-pose-independent-wall-scope-r240'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n')
def main():
 assert not O.exists();O.mkdir();d=H/'sbc-power/U21003-cap-pullup-translated-return-nominees-r238';assert sha(d/'receipt.json')=='c2b8d56cbdbcd81befd83620526fe72646b3b677f78c785eae457a540608e09b';mp=d/'owned-cap-translation-host-checkpoint.pkl';g,h,b,z,c=pickle.loads(mp.read_bytes());nt=pickle.loads((d/'new-track-objects.pkl').read_bytes());assert len(nt)==8;rec,trees=F.build({**h,'zones':[]});ids={t['uuid']for t in nt};pnew=[p for p in h['pads']if p['ref']in('C21003','R21001')];assert len(pnew)==4;checks=[];errors=[];refs=pickle.loads((H/'sbc-power/remaining-original-IO3-indexed-direct-source-nominees-r219/exact-source-ground-reference.pkl').read_bytes());holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],sh)for p in h['pads']for sh in C.poly(p.get('hole')or[])];ht=STRtree([sh for u,sh in holes]);res,ex=A.reservations()
 def check(row,ok):checks.append({**row,'PASS':bool(ok)});errors.extend([]if ok else[row])
 for p in pnew:
  for l,rs in p['layers'].items():
   for body in C.poly(rs):
    for j in trees[l].query(body.buffer(.7),predicate='intersects'):
     q=rec[l][int(j)]
     if q['uuid']==p['uuid']or C.norm(q['net'])==C.norm(p['net']):continue
     if q['kind']=='track':tt=q['source'];gap=body.distance(LineString([tt['a'],tt['b']]))-tt['w']/2
     elif q['kind']=='via':vv=q['source'];gap=body.distance(Point(vv['x'],vv['y']))-vv['d']/2
     else:gap=body.distance(q['shape'])
     req=GP.G.gap(h,p['net'],q['net'])+.025;check({'kind':'new_actual_SMD_to_Cu','ref':p['ref'],'pin':p['num'],'UUID':p['uuid'],'layer':l,'other_UUID':q['uuid'],'other_raw_net':q['net'],'gap_mm':gap,'required_mm':req},gap>=req)
    for j in ht.query(body.buffer(.5),predicate='intersects'):
     hid,hole=holes[int(j)];gap=body.distance(hole)-.005;check({'kind':'moved_SMD_to_every_drill','ref':p['ref'],'pin':p['num'],'other_UUID':hid,'gap_mm':gap,'required_mm':.275},gap>=.275)
    for q in z:
     if q['layer']!=l or C.norm(q['net'])==C.norm(p['net'])or body.distance(q['shape'])>.7:continue
     req=max(GP.G.gap(h,p['net'],q['net']),q['clearance_mm'])+.025;gap=body.distance(q['shape']);check({'kind':'moved_pad_to_owned_plane','ref':p['ref'],'pin':p['num'],'other_UUID':q['uuid'],'gap_mm':gap,'required_mm':req,'owned_new_anti_or_rebuild_not_yet_authorized_by_scope':True},gap>=req)
 for t in nt:
  axis=LineString([t['a'],t['b']]);l=t['layer'];body=GP.bounded_buffer(axis,t['w']/2)
  for j in trees[l].query(body.buffer(.7),predicate='intersects'):
   q=rec[l][int(j)]
   if q['uuid']==t['uuid']or C.norm(q['net'])==C.norm(t['net']):continue
   if q['kind']=='track':tt=q['source'];gap=axis.distance(LineString([tt['a'],tt['b']]))-(tt['w']+t['w'])/2
   elif q['kind']=='via':vv=q['source'];gap=axis.distance(Point(vv['x'],vv['y']))-(vv['d']+t['w'])/2
   else:gap=axis.distance(q['shape'])-t['w']/2
   req=GP.G.gap(h,t['net'],q['net'])+.025;check({'kind':'new_true_track_caps_to_Cu','UUID':t['uuid'],'layer':l,'net':t['net'],'other_UUID':q['uuid'],'other_net':q['net'],'gap_mm':gap,'required_mm':req},gap>=req)
  for q in z:
   if q['layer']!=l or C.norm(q['net'])==C.norm(t['net'])or body.distance(q['shape'])>.7:continue
   gap=axis.distance(q['shape'])-t['w']/2;req=max(GP.G.gap(h,t['net'],q['net']),q['clearance_mm'])+.025;check({'kind':'new_true_track_to_owned_plane','UUID':t['uuid'],'other_UUID':q['uuid'],'gap_mm':gap,'required_mm':req},gap>=req)
  for hid,hole in holes:
   if hole.distance(body)>.6:continue
   owner=next((v for v in h['vias']if v['uuid']==hid),None)
   if owner and C.norm(owner['net'])==C.norm(t['net']):continue
   gap=body.distance(hole)-.005;check({'kind':'new_track_foreign_hole','UUID':t['uuid'],'other_UUID':hid,'gap_mm':gap,'required_mm':.275},gap>=.275)
  if C.norm(t['net'])!='/LOGIC_GND':
   gap=body.difference(refs[l]);f=O/(t['uuid']+'-newbody-old-source-reference-gap.wkb');f.write_bytes(gap.wkb);check({'kind':'new_full_body_actual_source_reference','UUID':t['uuid'],'layer':l,'gap_mm2':gap.area,'known_supervisor_own_old_port_requires_separate_real_return_support':t['uuid']in{'dacd74a9-a633-56ef-97f7-77f91d8317f7','7e747c9a-8b6b-5198-9997-d1e34f52ed83'}},gap.is_empty)
  for q in res['keepouts']:
   if l in q['layers']and C.norm(t['net'])not in ex.get(q['name'],set())and any(body.distance(sh)<.025 for sh in C.poly(q['outline'])):check({'kind':'source_bound_reservation','UUID':t['uuid'],'rule':q['name']},False)
 fpchecks=[]
 for fp in h['footprints']:
  if fp['ref']not in('C21003','R21001'):continue
  for side,rs in fp['courtyard'].items():
   body=unary_union(C.poly(rs))
   for other in h['footprints']:
    if other['ref']==fp['ref']or side not in other['courtyard']:continue
    oo=unary_union(C.poly(other['courtyard'][side]))
    if body.distance(oo)>.1:continue
    row={'kind':'moved_FP_actual_same_side_courtyard','ref':fp['ref'],'other_ref':other['ref'],'side':side,'distance_mm':body.distance(oo),'overlap_mm2':body.intersection(oo).area};fpchecks.append(row)
    if not body.intersection(oo).is_empty:errors.append(row)
 put(O/'all-checks.json',checks);put(O/'errors.json',errors);put(O/'courtyard-checks.json',fpchecks);put(O/'receipt.json',{'verdict':'SCOPED_TWO_POSE_AND_EIGHT_TRACK_GEOMETRY_REFERENCE_PASS_FULLCONTACT_NATIVE_OPEN'if not errors else'REJECTED_TWO_POSE_OR_TRACK_SCOPED_FAILURES_NO_EMISSION','R238_recipe_sha256':sha(d/'receipt.json'),'checkpoint_model_sha256':sha(mp),'new_tracks':len(nt),'moved_pad_count':len(pnew),'checks':len(checks),'errors':len(errors),'exact_fields_and_rule_negatives_no_constraints_waived':True,'source_all_old_contacts_and_real_ordinary_return_full_ref_native':'OPEN','native_jobs':0,'board_written':False,'script_sha256':sha(__file__)});print('R240_COMPLETE',len(checks),len(errors),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
