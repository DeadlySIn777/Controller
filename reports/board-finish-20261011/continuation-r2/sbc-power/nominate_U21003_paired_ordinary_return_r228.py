"""Find real ordinary source-return barrels at the exact old IO3 port.

Only same-domain owned-new pours may need explicitly ledgered antipads.
Every old discrete piece, SMD/drill guard and retained reference is hard.
"""
import hashlib,json,pickle,sys,math,traceback,uuid
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in ('sbc-power','field-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as GP
import restore_SAFE_generated_precision_states_r168 as PS
O=H/'sbc-power/U21003-ordinary-source-paired-return-nominees-r228'
RAW='/LOGIC_GND';SIG='62cc5cf0-31b2-4fe2-ad0f-9a063afe6073';LAYERS=('F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n')
def main():
 assert not O.exists();O.mkdir();mp=H/'sbc-power/C1022-zero-gap-source-feed-independent-r221/model.pkl';assert sha(mp)=='261f92035b05f1346bc805d43df3f7b67a2c0c638892ee43c01856d57196182a'
 g,h,b,z,c=pickle.loads(mp.read_bytes());PS.restore_bound_generated_precision_states(b,z);oldv=next(v for v in g['vias']if v['uuid']==SIG);sig=next(v for v in h['vias']if v['uuid']==SIG);assert sig==oldv and(sig['x'],sig['y'],sig['d'],sig['drill'])==(331.75,145.1,.6,.3);assert sig['flashed']==list(LAYERS)
 rec,trees=F.build({**h,'zones':[]});refp=H/'sbc-power/remaining-original-IO3-indexed-direct-source-nominees-r219/exact-source-ground-reference.pkl';refs=pickle.loads(refp.read_bytes())
 smds=[(p,sh)for p in h['pads']if p['smd']for l,rs in p['layers'].items()if l in('F.Cu','B.Cu')for sh in C.poly(rs)];st=STRtree([sh for p,sh in smds]);viaPts=[Point(v['x'],v['y'])for v in h['vias']];vt=STRtree(viaPts);holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],sh)for p in h['pads']for sh in C.poly(p.get('hole')or[])];ht=STRtree([sh for uid,sh in holes]);nativefills=[]
 for q in h['zones']:
  if C.norm(q['net'])==RAW:continue
  for l in LAYERS:
   for sh in C.poly(q['fills'].get(l,[])):
    if sh.distance(Point(sig['x'],sig['y']))<2:nativefills.append((q,l,sh))
 # Only actual already-supported old F/B/In3 bodies are protected here.
 oldrefs=[]
 for t in h['tracks']:
  if t['layer']not in('F.Cu','B.Cu','In3.Cu')or C.norm(t['net'])==RAW:continue
  if GP.G.gap(h,RAW,t['net'])>.15:continue
  axis=LineString([t['a'],t['b']])
  if axis.distance(Point(sig['x'],sig['y']))>2:continue
  body=GP.bounded_buffer(axis,t['w']/2);oldrefs.append((t,body.intersection(refs['F.Cu'if t['layer']=='F.Cu'else'B.Cu'])))
 print('R228_EXACT_LOCAL_OBSTACLES_READY',len(nativefills),len(oldrefs),flush=True);attempts=[];accepted=[]
 for radius in(.875,.9,.925,.95,.975,1.0):
  for index in range(96):
   angle=2*math.pi*index/96;x=round(sig['x']+radius*math.cos(angle),6);y=round(sig['y']+radius*math.sin(angle),6);p=Point(x,y);v={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'U21003-paired-return-r228:'+repr((x,y)))),'net':RAW,'x':x,'y':y,'d':.5,'drill':.2,'flashed':list(LAYERS)};errs=[]
   # Strong guarded hole edge to every SMD and drill, plus ordinary pitch.
   sj=int(st.nearest(p));smdd=p.distance(smds[sj][1])-.1-.005
   if smdd<.275:errs.append({'kind':'every_SMD_guard','distance_mm':smdd,'pad_UUID':smds[sj][0]['uuid']})
   hj=int(ht.nearest(p));hd=p.distance(holes[hj][1])-.1-.005
   if hd<.275:errs.append({'kind':'every_drill_guard','distance_mm':hd,'UUID':holes[hj][0]})
   vi=int(vt.nearest(p));pitch=p.distance(viaPts[vi])
   if pitch<.815:errs.append({'kind':'ordinary_pitch','distance_mm':pitch,'UUID':h['vias'][vi]['uuid']})
   if errs:attempts.append({'at':[x,y],'errors':errs});continue
   for l in LAYERS:
    for j in trees[l].query(p.buffer(1.2),predicate='intersects'):
     q=rec[l][int(j)]
     if C.norm(q['net'])==RAW:continue
     req=GP.G.gap(h,RAW,q['net'])+.025
     if q['kind']=='track':a=q['source'];gap=p.distance(LineString([a['a'],a['b']]))-.25-a['w']/2
     elif q['kind']=='via':a=q['source'];gap=p.distance(Point(a['x'],a['y']))-.25-a['d']/2
     else:gap=p.distance(q['shape'])-.25
     if gap<req:errs.append({'kind':'hard_actual_discrete_Cu','layer':l,'UUID':q['uuid'],'raw_net':q['net'],'gap_mm':gap,'required_mm':req})
   for q in h['rule_areas']:
    if q.get('no_vias')and any(p.distance(sh)<.25+.025 for sh in C.poly(q['outline'])):errs.append({'kind':'actual_no_vias','UUID':q['uuid']})
   if errs:attempts.append({'at':[x,y],'errors':errs});continue
   ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));areas={l:ann.intersection(refs[out].buffer(-.075,quad_segs=128)).area for l,out in(('In1.Cu','F.Cu'),('In4.Cu','B.Cu'))}
   if any(a<.004 for a in areas.values()):errs.append({'kind':'no_finite_source_annular_interior','areas_mm2':areas})
   hole=GP.bounded_disk(v,.1)
   for t,sh in oldrefs:
    if not sh.intersection(hole).is_empty:errs.append({'kind':'retained_source_reference_hole','track_UUID':t['uuid'],'layer':t['layer'],'lost_mm2':sh.intersection(hole).area})
   newcuts=[]
   for q in z:
    clear=max(.15,float(q['clearance_mm']),GP.G.gap(h,RAW,q['net']))+.025
    if C.norm(q['net'])==RAW:continue
    cut=GP.bounded_disk(v,max(.1+.275,.25+clear));hit=q['zone_outline_shape'].intersection(cut)
    if hit.is_empty:continue
    if GP.G.gap(h,RAW,q['net'])>.15:errs.append({'kind':'hard_foreign_domain_owned_plane','UUID':q['uuid'],'layer':q['layer'],'overlap_guard_mm2':hit.area})
    else:newcuts.append({'zone_UUID':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'radius_mm':max(.375,.25+clear),'intended_removed_mm2':hit.area,'old_physical_WKB_sha256':hashlib.sha256(q['shape'].wkb).hexdigest(),'old_intended_WKB_sha256':hashlib.sha256(q['zone_outline_shape'].wkb).hexdigest()})
   nativecuts=[]
   for q,l,sh in nativefills:
    clear=max(float(q['clearance_mm']),GP.G.gap(h,RAW,q['net']))+.025;cut=GP.bounded_disk(v,max(.375,.25+clear));hit=sh.intersection(cut)
    if not hit.is_empty:nativecuts.append({'zone_UUID':q['uuid'],'raw_net':q['net'],'layer':l,'native_local_mm':q['clearance_mm'],'projected_removed_mm2':hit.area,'cut_radius_mm':max(.375,.25+clear)})
   attempts.append({'at':[x,y],'errors':errs,'explicit_owned_antipad_nominations':newcuts,'native_repour_obligations':nativecuts,'real_source_annular_interior_mm2':areas})
   if not errs:
    accepted.append({'via':v,'existing_IO3_source_via':sig,'distance_mm':math.dist([x,y],[sig['x'],sig['y']]),'real_source_annular_interior_mm2':areas,'explicit_owned_antipad_nominations':newcuts,'native_repour_obligations':nativecuts,'aperture_witness_not_yet_qualified':True});print('R228_REAL_RETURN_NOMINEE',x,y,areas,len(newcuts),flush=True)
  if accepted:break
 put(O/'attempts.json',attempts);(O/'nominee-objects.pkl').write_bytes(pickle.dumps(accepted,protocol=5));put(O/'receipt.json',{'verdict':'CONCRETE_ORDINARY_PAIRED_SOURCE_RETURN_NOMINEES_PENDING_EXACT_PROJECTION_AND_FULLCONTACT_REFERENCE'if accepted else'NO_ORDINARY_SOURCE_RETURN_NOMINEE_IN_ENUMERATED_RING','positive_base_model_sha256':sha(mp),'existing_signal_via':sig,'source_reference_cache_sha256':sha(refp),'attempts':len(attempts),'accepted_nominees':accepted,'exact_local_cap_pin_nets':[{'ref':p['ref'],'pin':p['num'],'net':p['net'],'x':p['x'],'y':p['y']}for p in h['pads']if p['ref']in('C21001','C21002','C21003','U21003')],'no_geometry_or_source_or_rule_mutation':True,'native_jobs':0,'board_written':False,'script_sha256':sha(__file__)})
 print('R228_COMPLETE',len(accepted),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
