"""Constructive current full-width CORE5 transport screen on real LG In4.

Only NEW CORE5 transport is withdrawable. Native source/group and endpoint
aperture scope are explicit; successful routes remain unaccepted proposals.
"""
import os,psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
proc=psutil.Process();proc.cpu_affinity(list(range(16,28)));proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,math,time,traceback
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely import STRtree
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import tri_route as TR
import physical_reference_losses_r3_zero_r208 as RF
K=N.K;L=N.L;sha=N.sha
OUT=H/'sbc-power/CORE5-existing-LOAD-to-SOURCE-one-midport-B-In3-geography-r413'
MP=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371/model.pkl'
BASE=H/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
LG='/LOGIC_GND';NET='/mc_local_power/CORE_5V'
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 started=time.monotonic();assert not OUT.exists();OUT.mkdir();N.assert_R157_actual_before()
 assert sha(MP)=='ee6697512303f8be14aa404b75094dba75e2461d17c25396827523837c162b1b';g,h,b,q,c=pickle.loads(MP.read_bytes())
 assert sha(BASE)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';_,bh,_,_,bc=pickle.loads(BASE.read_bytes())
 native=json.loads((N.R157/'actual-full-refill-geometry.json').read_bytes());flashes=json.loads((N.R157/'actual-full-refill-via-flashes.json').read_bytes())['vias']
 actual,ctx,pads=N.convert_selected_actual(bh,bc,native,flashes,{NET},source_pcb=N.R157/'copy/board.kicad_pcb')
 original=next(t for t in actual['tracks']if t['uuid']=='dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1')
 assert(original['a'],original['b'],original['w'],original['layer'])==([112.95,202.35],[133.549999,202.35],1.25,'F.Cu')
 import copy,uuid
 anchors=[]
 for a,bp in (([112.95,202.35],[116.2,202.35]),([120.1,202.35],[133.549999,202.35])):
  anchor={**original,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CORE5-R295-source-test-anchor-'+str(a))), 'a':a,'b':bp};anchors.append(anchor)
 actual={**actual,'tracks':[t for t in actual['tracks']if t['uuid']!=original['uuid']]+anchors}
 # Only the original middle is withdrawn in this independent physical
 # source graph. Every native fill, pad, barrel, hole and mask is unchanged.
 cached=H/'CORE5-current-new-transport-full1p25-In3-real-LGIn4-screen-r295';br=json.loads((cached/'source-binding.json').read_bytes());bp=cached/'actual-full-R157-CORE5-middle-withdrawn-all-drilled-groups.pkl';assert sha(bp)==br['CORE5_actual_groups_SHA256'];coregroups=pickle.loads(bp.read_bytes());(OUT/'actual-full-R157-CORE5-middle-withdrawn-all-drilled-groups.pkl').write_bytes(pickle.dumps(coregroups,protocol=5));coreroot=K.root(coregroups,'R11022','2')
 put('exact-original-middle-withdrawal-physical-source-ledger.json',{'old_track':original,'two_full_width_source_test_anchors':anchors,'withdrawn_middle_only_mm':[[116.2,202.35],[120.1,202.35]],'native_fills_pads_holes_masks_unchanged':True,'actual_post_withdrawal_root_keys':len(K.keys(coreroot))})
 lg,_=N.bound_R663_before_groups({LG});reference=K.source_refs(K.root(lg[LG],'J11001','2'))['In3.Cu']
 put('source-binding.json',{'native_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'CORE5_actual_groups_SHA256':sha(OUT/'actual-full-R157-CORE5-middle-withdrawn-all-drilled-groups.pkl'),'CORE5_root_keys':len(K.keys(coreroot)),'CORE5_root_selector':['R11022','2'],'LG_root_selector':['J11001','2'],'all_actual_holes':len(ctx[0]),'native_CORE5_pad_bindings':len(pads)})
 print('R295_ACTUAL_CORE5_SOURCE_BOUND',len(K.keys(coreroot)),flush=True)
 rightAnchor=anchors[1];load=next(xs for xs in coregroups if any(r['kind']=='track'and r['uuid']==rightAnchor['uuid']for r in xs));loadids=sorted({r['uuid']for r in load if r['kind']=='via'});assert loadids==['765db048-1685-4652-b04d-5bf817870398','8c0a08eb-cca0-46db-814a-e18d7227c496'];starts=[(next(v for v in actual['vias']if v['uuid']==uid),next(r['shape']for r in load if r['kind']=='via'and r['uuid']==uid and r['layer']=='In3.Cu'))for uid in loadids]
 region=box(10,145,215,228);roi=region.buffer(3);full_reference=reference;reference=reference.intersection(roi);domain=h['domains_normalized'];gap=lambda n:.15 if domain.get(L.norm(n))==domain.get(NET)else .6
 withdrawn={r['exact_current_track']['uuid']for r in json.loads((H/'sbc-power/CM79-R371-exact-CORE5-new-body-gap-parallel-handoff-r390/exact-CORE5-new-tracks-and-raw-body-reference-gaps.json').read_bytes())}
 def build(layer):
  obstacles=[];ledger=[]
  def add(uid,net,kind,shape,clear):
   if L.norm(net)==NET or not shape.intersects(roi):return
   obstacles.append(shape.buffer(.625+clear+.025005,quad_segs=64));ledger.append({'UUID':uid,'net':net,'kind':kind,'clearance_mm':clear})
  for t in h['tracks']:
   if t['layer']==layerand t['uuid']not in withdrawn:add(t['uuid'],t['net'],'fixed_current_track',K.A.shape({'kind':'segment',**t}),gap(t['net']))
  for v in h['vias']:
   if layerin v['flashed']:add(v['uuid'],v['net'],'fixed_current_via',Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128),gap(v['net']))
  for p in h['pads']:
   for s in L.poly(p['layers'].get(layer,[])):add(p['uuid'],p['net'],'fixed_current_pad',s,gap(p['net']))
  for z in native['zones']:
   # Only original native LG In3 may undergo its normal automatic clearance
   # retreat. Exact per-record old source/contact/reference gates remain OPEN.
   # No original outline or filled polygon is edited or fabricated by this screen.
   if L.norm(z['net'])==LG:continue
   for s in L.poly(N.O.polys(z['fills'].get(layer,[]))):add(z['uuid'],z['net'],'actual_full_native_foreign_fill',s,max(gap(z['net']),float(z['clearance_mm'])))
  for z in q:
   if z['layer']==layer:add(z['uuid'],z['net'],'current_owned_plane',z['shape'],max(gap(z['net']),float(z.get('clearance_mm',.15))))
  for v in h['vias']:
   if L.norm(v['net'])!=NET:
    sh=Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)
    if sh.intersects(roi):obstacles.append(sh.buffer(.905005,quad_segs=64))
  for p in h['pads']:
   if L.norm(p['net'])!=NET:
    for s in L.poly(p.get('hole')or[]):
     if s.intersects(roi):obstacles.append(s.buffer(.905005,quad_segs=64))
  reserve,exempt=K.A.reservations()
  for rules,isreserve in ((h['rule_areas'],False),(reserve['keepouts'],True)):
   for rule in rules:
    if layernot in rule['layers']or(isreserve and NET in exempt.get(rule['name'],set()))or(not isreserve and not rule.get('no_tracks')):continue
    for s in L.poly(rule['outline']):
     if s.intersects(roi):obstacles.append(s.buffer(.650005,quad_segs=64))
  hard=unary_union(obstacles);board=unary_union(L.poly(h['outline'])).buffer(-1.150005);put(layer+'-hard-current-native-foreign-obstacle-ledger.json',ledger)
  return hard,board
 base={};groups={};endpoints={};endpointRows=[]
 for layer in ('B.Cu','In3.Cu'):
  hard,board=build(layer);free=reference.buffer(-.625005,quad_segs=64).intersection(region).intersection(board).difference(hard);base[layer]=(hard,board,RF.parts(free));groups[layer]={}
  terminals=[]
  for role,records in (('LOAD',load),('SOURCE',coreroot)):
   for r in records:
    if r['kind']=='via'and r['layer']==layer:
     v=next(v for v in actual['vias']if v['uuid']==r['uuid'])
     if roi.covers(Point(v['x'],v['y'])):terminals.append((role,v,r['shape']))
  for role,v,ann in terminals:
   cap=Point(v['x'],v['y']).buffer(v['d']/2+.275,quad_segs=128);window=Point(v['x'],v['y']).buffer(3,quad_segs=64)
   local=unary_union([reference.intersection(window.buffer(2)),cap]).buffer(-.625005,quad_segs=64).intersection(window).intersection(region).intersection(board).difference(hard)
   contact=ann.buffer(.624995,quad_segs=128);patches=[p for p in RF.parts(local)if not p.intersection(contact).is_empty];whole=[]
   for patch in patches:
    ids=[i for i,f in enumerate(base[layer][2])if not patch.intersection(f).is_empty]
    whole.append(unary_union([patch]+[base[layer][2][i]for i in ids]))
   face=unary_union(whole);groups[layer][(role,v['uuid'])]=face;endpoints[(layer,role,v['uuid'])]=(v,ann)
   row={'layer':layer,'role':role,'UUID':v['uuid'],'xy_mm':[v['x'],v['y']],'own_cap_mm':v['d']/2+.275,'finite_contact_axis_face_EMPTY':face.is_empty,'axis_face_area_mm2':face.area};endpointRows.append(row)
   if not face.is_empty:(OUT/(layer+'-'+role+'-'+v['uuid']+'-axis-face.wkb')).write_bytes(face.wkb)
  print('R413_LAYER',layer,len(groups[layer]),flush=True)
 put('all-original-terminal-finite-contact-axis-faces.json',endpointRows)
 result=[]
 for ll,sl in (('B.Cu','In3.Cu'),('In3.Cu','B.Cu')):
  for (role,luid),lf in groups[ll].items():
   if role!='LOAD' or lf.is_empty:continue
   for (srole,suid),sf in groups[sl].items():
    if srole!='SOURCE' or sf.is_empty:continue
    common=lf.intersection(sf);row={'LOAD_UUID':luid,'LOAD_layer':ll,'SOURCE_UUID':suid,'SOURCE_layer':sl,'common_fullwidth_actual_LGIn4_axis_geography_EMPTY':common.is_empty,'common_area_mm2':common.area,'distance_mm':lf.distance(sf),'new_power_return_all_native_planes_current_oldrefs':'OPEN'}
    if not common.is_empty:
     p=common.representative_point();row['one_geographic_point_mm']=list(p.coords[0]);(OUT/(ll+'-'+luid+'--'+sl+'-'+suid+'-midport-geography.wkb')).write_bytes(common.wkb)
    result.append(row)
 put('only-two-layer-one-middle-ordinary-transition-geography.json',result)
 put('receipt.json',{'status':'TWO_LAYER_ONE_MIDDLE_TRANSITION_STRICT_REFERENCE_GEOGRAPHY_ONLY','actual_R157_SOURCE_cache_SHA256':sha(bp),'actual_R157_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'source_keys':len(K.keys(coreroot)),'endpoint_count':len(endpointRows),'pair_count':len(result),'positive_geography_pair_count':sum(not r['common_fullwidth_actual_LGIn4_axis_geography_EMPTY']for r in result),'only_exact_named_original_terminals_caps':True,'all49_CM_original_Cu_native_fieldplanes_holes_hard':True,'new_via_return_full_native_oldsource_oldref_current_thermal':'OPEN','native_jobs_or_edits':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R413_COMPLETE',sha(OUT/'receipt.json'),sum(not r['common_fullwidth_actual_LGIn4_axis_geography_EMPTY']for r in result),flush=True)

if __name__=='__main__':
 try:main()
 except Exception:
  if OUT.exists():put('failure.json',{'traceback':traceback.format_exc(),'adopted':False})
  raise
