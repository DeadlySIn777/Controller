"""Attribute saved CORE5 gaps against actual full native BEFORE copper.

Read-only constructive screen. No foreign carving, fill substitution or adoption.
"""
import os, psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'): os.environ[name]='2'
proc=psutil.Process(); proc.cpu_affinity(list(range(16,28))); proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,time
from pathlib import Path
from shapely import from_wkb,STRtree
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'): sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K; L=N.L; O=N.O; sha=N.sha
HAND=H/'sbc-power/CM79-R371-exact-CORE5-new-body-gap-parallel-handoff-r390'
MODEL=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371/model.pkl'
OUT=H/'CORE5-R390-actual-full-native-In1-source-shadow-blocker-screen-r290'
LG='/LOGIC_GND'; POWER='/mc_local_power/CORE_5V'
def put(n,x): (OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def info(s): return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds':list(s.bounds) if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 started=time.monotonic(); assert not OUT.exists(); OUT.mkdir()
 assert sha(MODEL)=='ee6697512303f8be14aa404b75094dba75e2461d17c25396827523837c162b1b'
 assert sha(HAND/'receipt.json')=='9e6502a12b7cdffd519a29ad548fcfe3cb7d877eb17a8b63567359c9e8fe579f'
 N.assert_R157_actual_before(); g,h,b,q,c=pickle.loads(MODEL.read_bytes())
 rows=json.loads((HAND/'exact-CORE5-new-tracks-and-raw-body-reference-gaps.json').read_bytes()); tm={t['uuid']:t for t in h['tracks']}
 groups,_=N.bound_R663_before_groups({LG}); root=K.root(groups[LG],'J11001','2'); source=K.source_refs(root)['F.Cu']
 native=json.loads((N.R157/'actual-full-refill-geometry.json').read_bytes())
 rawgaps=[]
 for row in rows:
  assert row['required_actual_reference_plane']=='In1.Cu' and tm[row['exact_current_track']['uuid']]==row['exact_current_track']
  p=Path(row['exact_raw_gap_wkb_path']); assert sha(p)==row['WKB_sha256']; rawgaps.append(from_wkb(p.read_bytes()))
 roi=unary_union(rawgaps).buffer(1.0)
 obstacles=[]
 def gap(net): return .15 if h['domains_normalized'].get(L.norm(net))==h['domains_normalized'].get(LG) else .6
 def add(uid,net,kind,shape,clear,local=None):
  if L.norm(net)==LG or not shape.intersects(roi.buffer(clear+.025)): return
  guard=shape.buffer(clear+.025,quad_segs=64)
  obstacles.append({'UUID':uid,'raw_net':net,'kind':kind,'required_mm':clear,'local_mm':local,'shape':shape,'guard':guard})
 for z in native['zones']:
  if 'In1.Cu' not in z['fills'] or L.norm(z['net'])==LG: continue
  for s in L.poly(O.polys(z['fills']['In1.Cu'])): add(z['uuid'],z['net'],'ACTUAL_FULL_NATIVE_foreign_fill',s,max(gap(z['net']),float(z['clearance_mm'])),float(z['clearance_mm']))
 for t in h['tracks']:
  if t['layer']=='In1.Cu': add(t['uuid'],t['net'],'current_track',K.A.shape({'kind':'segment',**t}),gap(t['net']))
 for v in h['vias']:
  if 'In1.Cu' in v['flashed']: add(v['uuid'],v['net'],'current_flashed_via',Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128),gap(v['net']))
 for p in h['pads']:
  for s in L.poly(p['layers'].get('In1.Cu',[])): add(p['uuid'],p['net'],'current_pad',s,gap(p['net']))
 for z in q:
  if z['layer']=='In1.Cu': add(z['uuid'],z['net'],'CURRENT_owned_physical_plane',z['shape'],max(gap(z['net']),float(z.get('clearance_mm',.15))),float(z.get('clearance_mm',.15)))
 for v in h['vias']:
  # Every real drill is hard. Same-ground drill contributes only physical void.
  clear=0 if L.norm(v['net'])==LG else .275
  shape=Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)
  if shape.buffer(clear+.025).intersects(roi): obstacles.append({'UUID':v['uuid'],'raw_net':v['net'],'kind':'current_physical_drill','required_mm':clear,'local_mm':None,'shape':shape,'guard':shape.buffer(clear+.025,quad_segs=64)})
 for p in h['pads']:
  for s in L.poly(p.get('hole')or[]):
   if s.buffer(.3).intersects(roi): obstacles.append({'UUID':p['uuid'],'raw_net':p['net'],'kind':'current_pad_or_NPTH_hole','required_mm':.275,'local_mm':None,'shape':s,'guard':s.buffer(.3,quad_segs=64)})
 for rule in h['rule_areas']:
  if 'In1.Cu' in rule['layers'] and rule.get('no_zones'):
   for s in L.poly(rule['outline']):
    if s.intersects(roi): obstacles.append({'UUID':rule['uuid'],'raw_net':'','kind':'native_no_zones','required_mm':0,'local_mm':None,'shape':s,'guard':s})
 tree=STRtree([x['guard']for x in obstacles]); result=[]
 for row,raw in zip(rows,rawgaps):
  t=row['exact_current_track']; body=K.A.shape({'kind':'segment',**t}); fresh=body.difference(source)
  # A screen window, not an accepted zone: positive SOURCE support must cover
  # the entire body and separately attach with finite width after current cuts.
  window=fresh.buffer(.15,quad_segs=64); hits=[]; blocked=[]
  for j in tree.query(window,predicate='intersects'):
   ob=obstacles[int(j)]; hit=window.intersection(ob['guard']); direct=fresh.intersection(ob['guard'])
   hits.append({k:v for k,v in ob.items() if k not in('shape','guard')}|{'window_hit':info(hit),'literal_body_gap_guard_hit':info(direct)})
   blocked.append(ob['guard'])
  allowed=window.difference(unary_union(blocked)); uncovered=fresh.difference(allowed)
  prefix=t['uuid']; (OUT/(prefix+'-actual-full-before-reference-gap.wkb')).write_bytes(fresh.wkb); (OUT/(prefix+'-new-shadow-screen-allowed.wkb')).write_bytes(allowed.wkb); (OUT/(prefix+'-new-shadow-screen-uncovered.wkb')).write_bytes(uncovered.wkb)
  result.append({'UUID':prefix,'layer':t['layer'],'saved_raw_gap':info(raw),'ACTUAL_FULL_BEFORE_source_fill_gap':info(fresh),'screen_window':info(window),'positive_shadow_screen_uncovered':info(uncovered),'actual_source_contact_area_mm2':allowed.intersection(source).area,'hard_blockers':hits,'positive_only_shadow_without_carve_covers_actual_gap':uncovered.is_empty})
  print('R290_CORE5',prefix,'blockers',len(hits),'uncovered',uncovered.area,flush=True)
 put('per-exact-new-CORE5-body-actual-source-shadow-hard-blockers.json',result)
 put('receipt.json',{'status':'READ_ONLY_ACTUAL_FULL_NATIVE_CORE5_REFERENCE_SHADOW_BLOCKER_SCREEN_COMPLETE','hand_off_SHA256':sha(HAND/'receipt.json'),'model_SHA256':sha(MODEL),'actual_full_native_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'actual_source_groups_SHA256':'a24dcae5ae52ae71e548e7f75f2d1ec746324187cf1dc5ab67e01a4ef6f347b7','body_count':len(rows),'raw_saved_gap_count':sum(not s.is_empty for s in rawgaps),'actual_full_before_gap_count':sum(not r['ACTUAL_FULL_BEFORE_source_fill_gap']['EMPTY']for r in result),'uncovered_screen_body_count':sum(not r['positive_shadow_screen_uncovered']['EMPTY']for r in result),'hard_obstacle_count':len(obstacles),'positive_source_shadow_not_emitted':True,'source_native_and_current_peers_not_carved':True,'no_cap_exemption_or_global_impossibility_claim':True,'native_jobs':0,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started})
 print('R290_COMPLETE',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__': main()
