"""Actual-R157 CM79 ground-port screen with original CORE5 trunk held.

All only-new CM copper is an explicit hard obstacle for foreign nets and
its holes/pitch remain held. Old native same-domain plane clearance is an
explicit normal-fill operation; foreign owned roles are never carved.
"""
import sys,json,pickle,math,time,traceback,copy
from pathlib import Path
from shapely.geometry import Point,box,LineString
from shapely.ops import unary_union
from shapely import STRtree
P=Path(__file__).resolve().parent;H=P.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import fast_contacts as F
import tri_route as TR
import physical_reference_losses_r3_zero_r208 as RF
K=N.K;L=N.L;A=K.A;sha=N.sha
NET='/LOGIC_GND';OUT=P/'CM79-direct-DC-original-Cu-hole-cell-attribution-r421'
BASE=H/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
CMP=P/'CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/only-new-CM-ordinary-discrete-no-deletes.pkl'
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 started=time.monotonic();assert not OUT.exists();OUT.mkdir();N.assert_R157_actual_before()
 assert sha(BASE)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';g,h,b,q,c=pickle.loads(BASE.read_bytes());cm=pickle.loads(CMP.read_bytes())
 native=json.loads((N.R157/'actual-full-refill-geometry.json').read_bytes());flashes=json.loads((N.R157/'actual-full-refill-via-flashes.json').read_bytes())['vias']
 actual,ctx,bindings=N.convert_selected_actual(h,c,native,flashes,{NET},source_pcb=N.R157/'copy/board.kicad_pcb')
 # Foreign-zone guards use the full actual native refill, not old host fills.
 actual['zones']=[{**z,'fills':{ly:N.O.polys(rs)for ly,rs in z['fills'].items()}}for z in native['zones']]
 baselineTrackIds={t['uuid']for t in actual['tracks']};baselineViaIds={v['uuid']for v in actual['vias']};assert not baselineTrackIds&{t['uuid']for t in cm['tracks']};assert not baselineViaIds&{v['uuid']for v in cm['vias']}
 actual['tracks']+=copy.deepcopy(cm['tracks']);actual['vias']+=copy.deepcopy(cm['vias']);rec,trees=F.build(actual)
 source,_=N.bound_R663_before_groups({NET});groups=source[NET];root=K.root(groups,'J11001','2');refs=K.source_refs(root);pad=next(p for p in actual['pads']if(p['ref'],str(p['num']))==('J15002','79'));padCu=unary_union(L.poly(pad['layers']['F.Cu']));padGuard=padCu.buffer(.275,quad_segs=128)
 region=box(110,193,124,209);roi=region.buffer(2);domain=h['domains_normalized'];gap=lambda n:.15 if domain.get(L.norm(n))==domain.get(NET)else .6
 refPlanes={ly:unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==ly and r['shape'].intersects(roi)])for ly in ('In1.Cu','In4.Cu')}
 nativeZones={z['uuid']:z for z in native['zones']};holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in actual['vias']]+[(p['uuid'],sh)for p in actual['pads']for sh in L.poly(p.get('hole')or[])];ht=STRtree([s for uid,s in holes]);vp=[Point(v['x'],v['y'])for v in actual['vias']];vt=STRtree(vp)
 smds=[(p['uuid'],sh)for p in actual['pads']if not p.get('hole')for ly in('F.Cu','B.Cu')for sh in L.poly(p['layers'].get(ly,[]))];st=STRtree([s for uid,s in smds]);courts=[(f['ref'],sh)for f in h['footprints']for ss in f['courtyard'].values()for sh in L.poly(ss)];ct=STRtree([s for ref,s in courts]);reserve,exempt=A.reservations()
 masks={ly:[]for ly in refPlanes}
 for layer,rlayer in [('F.Cu','In1.Cu'),('In2.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')]:
  for r in rec[layer]:
   if r['kind']=='fill'or domain.get(L.norm(r['net']))!=domain.get(NET)or not r['shape'].intersects(roi):continue
   mask=r['shape'].intersection(refPlanes[rlayer])
   if not mask.is_empty:masks[rlayer].append({'UUID':r['uuid'],'kind':r['kind'],'shape':mask})
  for z in q:
   if z['layer']==layer and domain.get(L.norm(z['net']))==domain.get(NET)and z['shape'].intersects(roi):
    mask=z['shape'].intersection(refPlanes[rlayer])
    if not mask.is_empty:masks[rlayer].append({'UUID':z['uuid'],'kind':'held_owned_before_reference_mask','shape':mask})
 for ly in refPlanes:
  for r in root:
   if r['kind']=='via'and r['layer']==ly and r['shape'].intersects(roi):masks[ly].append({'UUID':r['uuid'],'kind':'actual_J1_SOURCE_annulus','shape':r['shape'].intersection(refPlanes[ly])})
 mt={ly:STRtree([r['shape']for r in masks[ly]])for ly in masks}
 policy=Path('Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md');assert sha(policy)=='392e2155400e156d180ac5a786b2d7e4a41c2dcc945bfc7a8de9b9e21b02dde5';policytext=policy.read_text(encoding='utf-8');assert "A new signal via's return requirement"in policytext
 savedPath=P/'CM79-actual-R157-retained-CORE-ground-port-census-r417/finite-new-LG-ordinary-via-true-native-mask-census.json';saved=json.loads(savedPath.read_bytes());legal=[]
 for row in saved:
  retained=[r for r in row['deficits']if r['kind']!='real_courtyard_no_D4']
  if not retained:legal.append({**row,'deficits':retained,'removed_SIGNAL_only_courtyard_deficits':[r for r in row['deficits']if r['kind']=='real_courtyard_no_D4']})
 put('exact-saved-census-DC-ground-scope-delta.json',{'R417_census_SHA256':sha(savedPath),'operator_file':str(policy),'operator_SHA256':sha(policy),'D4_line':227,'scope_quote':"A new signal via's return requirement",'no_new_SIGNAL_via_no_D4_pair_or_spacing_use':True,'ordinary_pitch815um_all_true_Cu_SMD_drill_rules_masks_held':True,'saved_site_count':len(saved),'DC_ground_eligible_count':len(legal),'only_removed_predicate':'SIGNAL-specific courtyard rejection','raw_signal_shadow_FAILs_retained_from_R417_R418_R419':True})
 put('only-real-before-SOURCE-LG-DC-ground-ports.json',legal)
 # F transport remains .20; original full dc1a is a hard foreign obstacle.
 cuts=[]
 for r in rec['F.Cu']:
  if L.norm(r['net'])!=NET and r['shape'].intersects(roi):cuts.append(r['shape'].buffer(.1+max(gap(r['net']),float(nativeZones[r['uuid']]['clearance_mm'])if r['kind']=='fill'and r['uuid']in nativeZones else .15)+.025005,quad_segs=64))
 for z in q:
  if z['layer']=='F.Cu'and L.norm(z['net'])!=NET and z['shape'].intersects(roi):cuts.append(z['shape'].buffer(.1+max(gap(z['net']),float(z.get('clearance_mm',.15)))+.025005,quad_segs=64))
 for uid,sh in holes:
  if sh.intersects(roi):cuts.append(sh.buffer(.380005,quad_segs=64))
 for rules,isreserve in [(h['rule_areas'],False),(reserve['keepouts'],True)]:
  for rule in rules:
   if 'F.Cu'not in rule['layers']or(isreserve and NET in exempt.get(rule['name'],set()))or(not isreserve and not rule.get('no_tracks')):continue
   for sh in L.poly(rule['outline']):
    if sh.intersects(roi):cuts.append(sh.buffer(.125005,quad_segs=64))
 hard=unary_union(cuts);board=unary_union(L.poly(h['outline'])).buffer(-.625005);reference=refs['F.Cu'].intersection(roi)
 free=region.intersection(board).difference(hard);point=Point(pad['x'],pad['y']);faces=[p for p in RF.parts(free)if p.covers(point)];boundary=unary_union([p.boundary for p in faces]).buffer(.00001);cmids={r['uuid']for kind in ('tracks','vias')for r in cm[kind]};cuRows=[];holeRows=[]
 for r in rec['F.Cu']:
  if L.norm(r['net'])==NET or not r['shape'].intersects(region):continue
  obstacle=r['shape'].buffer(.1+max(gap(r['net']),float(nativeZones[r['uuid']]['clearance_mm'])if r['kind']=='fill'and r['uuid']in nativeZones else .15)+.025005,quad_segs=64)
  if not obstacle.intersection(boundary).is_empty:cuRows.append({'UUID':r['uuid'],'kind':r['kind'],'net':r['net'],'only_new_CM':r['uuid']in cmids,'bounds_mm':list(r['shape'].bounds),'source':r.get('source',{}).get('uuid')})
 for uid,sh in holes:
  if sh.intersects(roi)and not sh.buffer(.380005,quad_segs=64).intersection(boundary).is_empty:holeRows.append({'UUID':uid,'only_new_CM':uid in cmids,'true_original_drill_bounds_mm':list(sh.bounds)})
 for i,f in enumerate(faces):(OUT/('actual-DC-F-contact-axis-cell-'+str(i)+'.wkb')).write_bytes(f.wkb)
 put('exact-DC-cell-original-Cu-and-hole-boundary.json',{'direct_ground_DC_no_signal_shadow_gate':True,'original_pad':{'UUID':pad['uuid'],'xy_mm':[pad['x'],pad['y']]},'actual_foreign_Cu_hole_rule_free_start_face_count':len(faces),'faces':[{'area_mm2':f.area,'bounds_mm':list(f.bounds)}for f in faces],'boundary_actual_foreign_Cu':cuRows,'boundary_all_true_holes':holeRows})
 trialPath=P/'CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371/model.pkl';_,th,_,_,_=pickle.loads(trialPath.read_bytes());targets=['b7dc346a-8a46-4b4c-ae3d-c5990ddefc96','b1e550d5-047a-447c-a64c-45c2a92c14b0','dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1'];delta=[]
 for uid in targets:
  delta.append({'UUID':uid,'exact_R157_base_items':[x for kind in ('tracks','vias')for x in h[kind]if x['uuid']==uid],'frozen_historical_R371_items':[x for kind in ('tracks','vias')for x in th[kind]if x['uuid']==uid]})
 put('saved-R371-versus-actual-base-exact-wall-dependency.json',{'R371_model_SHA256':sha(trialPath),'actual_BASE_SHA256':sha(BASE),'only_exact_named_wall_barrel_presence_delta':delta,'not_current_source_native_equivalence':True})
 put('receipt.json',{'status':'DC_CONTACT_CELL_BLOCKER_AND_FROZEN_TRIAL_DEPENDENCY_ATTRIBUTION','actual_R157_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'operator_SHA256':sha(policy),'actual_F_Cu_hole_rule_face_count':len(faces),'original_foreign_Cu_boundary_count':len(cuRows),'hole_boundary_count':len(holeRows),'native_jobs_or_edits':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R421_COMPLETE',sha(OUT/'receipt.json'),len(faces),len(cuRows),len(holeRows),flush=True)

if __name__=='__main__':
 try:main()
 except Exception:
  if OUT.exists():put('failure.json',{'traceback':traceback.format_exc(),'adopted':False})
  raise
