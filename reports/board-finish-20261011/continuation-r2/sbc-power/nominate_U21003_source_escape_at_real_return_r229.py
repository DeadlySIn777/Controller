"""Source escape paired to an unchanged real grounded native barrel."""
import hashlib,json,pickle,sys,math,traceback,uuid
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in('sbc-power','field-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as GP
import restore_SAFE_generated_precision_states_r168 as PS
O=H/'sbc-power/U21003-real-return-paired-source-escape-r229'
RAW='/IO_3V3';RET='f6408df8-ba8b-46cd-9f4a-acb74673b7aa';LAYERS=('F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n')
def root(gs,ref,pin):return next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,pin)for q in xs))
def uid(text):return str(uuid.uuid5(uuid.NAMESPACE_URL,'U21003-R229:'+text))
def main():
 assert not O.exists();O.mkdir();mp=H/'sbc-power/C1022-zero-gap-source-feed-independent-r221/model.pkl';assert sha(mp)=='261f92035b05f1346bc805d43df3f7b67a2c0c638892ee43c01856d57196182a';g,h,b,z,c=pickle.loads(mp.read_bytes());PS.restore_bound_generated_precision_states(b,z)
 gs=pickle.loads(mp.with_name('groups.pkl').read_bytes());io=root(gs[RAW],'R18001','2');lg=root(gs['/LOGIC_GND'],'J11001','2');ret=next(v for v in h['vias']if v['uuid']==RET);assert ret==next(v for v in g['vias']if v['uuid']==RET)and(ret['x'],ret['y'],ret['d'],ret['drill'])==(333.221866,146.580047,.6,.3)and ret['flashed']==list(LAYERS)
 assert all(any(q['kind']=='via'and q['uuid']==RET and q['layer']==l for q in lg)for l in('F.Cu','In1.Cu','In4.Cu'))
 refp=H/'sbc-power/remaining-original-IO3-indexed-direct-source-nominees-r219/exact-source-ground-reference.pkl';refs=pickle.loads(refp.read_bytes());oldref=refs['F.Cu'];rp=Point(ret['x'],ret['y']);returnann=rp.buffer(.3,quad_segs=128).difference(rp.buffer(.15,quad_segs=128));returnareas={l:returnann.intersection(refs[o].buffer(-.075,quad_segs=128)).area for l,o in(('In1.Cu','F.Cu'),('In4.Cu','B.Cu'))};assert all(a>.004 for a in returnareas.values())
 sourcefills={l:[q for q in io if q['kind']=='fill'and q['layer']==l]for l in LAYERS};sourcefilltrees={l:STRtree([q['shape']for q in qs])for l,qs in sourcefills.items()};p=next(p for p in h['pads']if(p['ref'],p['num'])==('U21003','5'));a=[p['x'],p['y']];assert p['net']==RAW
 rec,trees=F.build({**h,'zones':[]});smds=[(p,sh)for p in h['pads']if p['smd']for l,rs in p['layers'].items()if l in('F.Cu','B.Cu')for sh in C.poly(rs)];st=STRtree([sh for p,sh in smds]);holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],sh)for p in h['pads']for sh in C.poly(p.get('hole')or[])];ht=STRtree([sh for uid,sh in holes]);vp=[Point(v['x'],v['y'])for v in h['vias']];vt=STRtree(vp)
 native=[]
 for q in h['zones']:
  if C.norm(q['net'])==RAW:continue
  for l,rs in q['fills'].items():
   for sh in C.poly(rs):
    if sh.distance(rp)<5:native.append((q,l,sh))
 protected=[]
 for t in h['tracks']:
  if t['layer']not in('F.Cu','B.Cu','In3.Cu')or C.norm(t['net'])=='/LOGIC_GND'or GP.G.gap(h,'/LOGIC_GND',t['net'])>.15:continue
  axis=LineString([t['a'],t['b']])
  if axis.distance(rp)>3:continue
  body=GP.bounded_buffer(axis,t['w']/2);protected.append((t,body.intersection(refs['F.Cu'if t['layer']=='F.Cu'else'B.Cu'])))
 print('R229_FROZEN_REAL_RETURN_AND_LOCAL_HARD_GEOMETRY_READY',returnareas,len(native),len(protected),flush=True)
 def screen(v,points=None):
  isvia=points is None;center=Point(v['x'],v['y'])if isvia else LineString(points);radius=.25 if isvia else .1;ls=LAYERS if isvia else('F.Cu',);errors=[];owned=[];nativecuts=[]
  for l in ls:
   for j in trees[l].query(center.buffer(radius+.8),predicate='intersects'):
    q=rec[l][int(j)]
    if C.norm(q['net'])==RAW:continue
    if q['kind']=='track':t=q['source'];gap=center.distance(LineString([t['a'],t['b']]))-radius-t['w']/2
    elif q['kind']=='via':t=q['source'];gap=center.distance(Point(t['x'],t['y']))-radius-t['d']/2
    else:gap=center.distance(q['shape'])-radius
    req=GP.G.gap(h,RAW,q['net'])+.025
    if gap<req:errors.append({'kind':'actual_discrete_Cu','UUID':q['uuid'],'layer':l,'gap_mm':gap,'required_mm':req})
   for q in z:
    if q['layer']!=l or C.norm(q['net'])==RAW:continue
    req=max(float(q['clearance_mm']),GP.G.gap(h,RAW,q['net']))+.025;cut=GP.bounded_buffer(center,max(.375,radius+req)if isvia else radius+req);hit=q['zone_outline_shape'].intersection(cut)
    if hit.is_empty:continue
    if GP.G.gap(h,RAW,q['net'])>.15:errors.append({'kind':'foreign_domain_owned_plane','UUID':q['uuid'],'layer':l,'cut_mm2':hit.area})
    else:owned.append({'UUID':q['uuid'],'layer':l,'raw_net':q['net'],'cut_shape':cut,'physical_WKB_sha256':hashlib.sha256(q['shape'].wkb).hexdigest(),'intended_WKB_sha256':hashlib.sha256(q['zone_outline_shape'].wkb).hexdigest()})
   for q,ql,sh in native:
    if ql!=l:continue
    req=max(float(q['clearance_mm']),GP.G.gap(h,RAW,q['net']))+.025;cut=GP.bounded_buffer(center,max(.375,radius+req)if isvia else radius+req);hit=sh.intersection(cut)
    if hit.is_empty:continue
    if GP.G.gap(h,RAW,q['net'])>.15:errors.append({'kind':'foreign_domain_native_fill','UUID':q['uuid'],'layer':l,'cut_mm2':hit.area})
    else:nativecuts.append({'UUID':q['uuid'],'layer':l,'raw_net':q['net'],'local_mm':q['clearance_mm'],'potential_retreat_mm2':hit.area})
  for q in h['rule_areas']:
   if not set(ls)&set(q['layers'])or not q.get('no_vias'if isvia else'no_tracks'):continue
   if any(center.distance(sh)<radius+.025 for sh in C.poly(q['outline'])):errors.append({'kind':'native_keepout','UUID':q['uuid']})
  return errors,owned,nativecuts
 attempts=[];accepted=[]
 for dist in(.875,.9,.925,.95,.975,1.):
  for i in range(96):
   angle=2*math.pi*i/96;x=round(ret['x']+dist*math.cos(angle),6);y=round(ret['y']+dist*math.sin(angle),6);pos=Point(x,y);v={'uuid':uid(repr((x,y))),'net':RAW,'x':x,'y':y,'d':.5,'drill':.2,'flashed':list(LAYERS)};errors=[]
   sj=int(st.nearest(pos));smdd=pos.distance(smds[sj][1])-.105;hj=int(ht.nearest(pos));hd=pos.distance(holes[hj][1])-.105;vi=int(vt.nearest(pos));pitch=pos.distance(vp[vi])
   if smdd<.275:errors.append({'kind':'every_SMD','gap_mm':smdd,'UUID':smds[sj][0]['uuid']})
   if hd<.275:errors.append({'kind':'every_drill','gap_mm':hd,'UUID':holes[hj][0]})
   if pitch<.815:errors.append({'kind':'pitch','gap_mm':pitch,'UUID':h['vias'][vi]['uuid']})
   if errors:attempts.append({'at':[x,y],'errors':errors});continue
   sourceareas=[];ann=pos.buffer(.25,quad_segs=128).difference(pos.buffer(.1,quad_segs=128))
   for l in('In2.Cu','In3.Cu'):
    for j in sourcefilltrees[l].query(ann,predicate='intersects'):
     q=sourcefills[l][int(j)];area=ann.intersection(q['shape'].buffer(-.025,quad_segs=128)).area
     if area>.004:sourceareas.append({'layer':l,'zone_UUID':q['uuid'],'finite_source_annular_interior_mm2':area,'actual_source_physical_fill_WKB_sha256':hashlib.sha256(q['shape'].wkb).hexdigest()})
   if not sourceareas:attempts.append({'at':[x,y],'errors':[{'kind':'no_actual_IO3_source_annulus'}]});continue
   errors,owned,nativecuts=screen(v)
   newhole=GP.bounded_disk(v,.1)
   for t,body in protected:
    if not body.intersection(newhole).is_empty:errors.append({'kind':'old_retained_reference_newhole','UUID':t['uuid'],'layer':t['layer'],'loss_mm2':body.intersection(newhole).area})
   if errors:attempts.append({'at':[x,y],'errors':errors});continue
   routes=[(a,[x,y]),(a,[a[0],y],[x,y]),(a,[x,a[1]],[x,y]),(a,[a[0],(a[1]+y)/2],[x,(a[1]+y)/2],[x,y])]
   for route in routes:
    points=[]
    for xy in route:
     xy=[round(n,6)for n in xy]
     if not points or xy!=points[-1]:points.append(xy)
    e,oc,nc=screen(v,points);body=GP.bounded_buffer(LineString(points),.1);own=GP.bounded_disk(v,.525).intersection(oldref);gap=body.difference(oldref.union(own))
    if not gap.is_empty:e.append({'kind':'new_fullbody_source_reference','gap_mm2':gap.area})
    for j in ht.query(body.buffer(.285),predicate='intersects'):
     hid,hole=holes[int(j)]
     if any(old['uuid']==hid and old['net']==RAW for old in h['vias']):continue
     if body.distance(hole)-.005<.275:e.append({'kind':'new_track_other_hole','UUID':hid})
    if e:attempts.append({'at':[x,y],'route':points,'errors':e});continue
    nt=[{'uuid':uid(v['uuid']+':track:'+str(k)),'net':RAW,'layer':'F.Cu','w':.2,'a':aa,'b':bb}for k,(aa,bb)in enumerate(zip(points,points[1:]))];accepted.append({'via':v,'tracks':nt,'unchanged_real_return':ret,'actual_return_annular_interiors':returnareas,'actual_IO3_source_annular_interiors':sourceareas,'old_source_supported_own_0p525mm_new_aperture':own,'explicit_owned_same_domain_cut_nominations':owned+oc,'native_same_domain_repour_obligations':nativecuts+nc,'source_reference_gap_mm2':gap.area});print('R229_CONCRETE_PAIRED_SOURCE_NOMINEE',x,y,len(nt),sourceareas,flush=True);break
   if accepted:break
  if accepted:break
 put(O/'attempts.json',attempts);pf=O/'nominee-objects.pkl';pf.write_bytes(pickle.dumps(accepted,protocol=5));put(O/'receipt.json',{'verdict':'CONCRETE_PAIRED_IO3_SOURCE_ESCAPE_WITH_REAL_NATIVE_RETURN_PENDING_FULL_PROJECTION'if accepted else'NO_VALID_ENUMERATED_PAIRED_IO3_SOURCE_ESCAPE','base_model_sha256':sha(mp),'native_ground_return':ret,'native_ground_return_finite_source_annuli_mm2':returnareas,'new_nominee_count':len(accepted),'nominee_object_sha256':sha(pf),'attempt_count':len(attempts),'source_reference_cache_sha256':sha(refp),'no_old_discrete_or_source_or_FP_mutation':True,'all_IO3_2A_current_loop_and_native_gates':'OPEN','native_jobs':0,'board_written':False,'script_sha256':sha(__file__)})
 print('R229_COMPLETE',len(accepted),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
