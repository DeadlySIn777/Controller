"""Check saved four-only-add VREF branch against pinned current native Cu.

No board writes, fill substitution or native job. Full AFTER refill is still
pending; SOURCE reference here is the actual full native BEFORE group only.
"""
from pathlib import Path
import sys,json,pickle,hashlib,time,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in (H,ROOT/'sbc-power',ROOT/'field-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
OUT=H/'AO1-saved-four-add-exact-current-native-screen-r1'
COM='/motherboard_analog_output/AO1_COM';VREF='/motherboard_analog_output/AO1_VREF'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(name,obj):(OUT/name).write_text(json.dumps(obj,indent=1,allow_nan=False)+'\n')
def info(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or s==v;pins[str(p.resolve())]=v;return p
 before=pin(ROOT/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763/actual-full-R157-before-model.pkl','dbeba66691d45ee12206f77e5060b4c845681014d19b3d9e633e9aed08a2b0c2');c=pickle.loads(before.read_bytes());assert isinstance(c,dict)
 gf=pin(before.parent/'actual-full-R157-before-all-net-groups.pkl','d808a9bbe54bb24d6232baf4bddddb260db7a82a891c6b50ca6355ed79e6482a');groups=pickle.loads(gf.read_bytes());root=K.root(groups[COM],'U14619','7');refs={ly:unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==ly])for ly in('In1.Cu','In4.Cu')}
 ep=pin(ROOT/'combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json','13a6a92d39e33f05a38107c7b9348c29847239671ee5b4c0ffa48a89536dead3');expected=json.loads(ep.read_bytes());put('compact-input-schema.json',{'model_keys':list(c),'expected_keys':list(expected),'copper_first':next(iter(expected['copper'].values()))})
 posefile=pin(ROOT/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full/before-native-all-FP-pad-pose.json');pose=json.loads(posefile.read_bytes());win=box(366,121,382,136);localpads=[p for p in c['pads']if win.buffer(1).covers(Point(p['x'],p['y']))]
 for p in localpads:
  x=pose['pads'][p['uuid']];assert str(x[0])==str(p['num'])and x[1]==p['net']and(x[2]/1e6,x[3]/1e6)==(p['x'],p['y'])
 tracks=[];vias=[];basevia={v['uuid']:v for v in c['vias']}
 for uid,e in expected['copper'].items():
  if e['kind']=='via':
   d=set(e['diameters_IU'].values());assert len(d)==1;v={'uuid':uid,'net':e['raw_net'],'x':e['at_IU'][0]/1e6,'y':e['at_IU'][1]/1e6,'d':next(iter(d))/1e6,'drill':e['drill_IU']/1e6,'flashed':basevia[uid]['flashed']if uid in basevia else list(K.LAYERS)};vias.append(v)
  else:
   assert e['kind']=='segment';t={'uuid':uid,'net':e['raw_net'],'layer':e['layer'],'a':[x/1e6 for x in e['start_IU']],'b':[x/1e6 for x in e['end_IU']],'w':e['width_IU']/1e6};tracks.append(t)
 local={**c,'tracks':[t for t in tracks if not LineString([t['a'],t['b']]).envelope.disjoint(win.buffer(1))],'vias':[v for v in vias if win.buffer(1).covers(Point(v['x'],v['y']))],'pads':localpads,'zones':[]};records,trees=K.F.build(local)
 sf=pin(H/'AO1-R19-VREF-only-four-chunk-current-requalification-handoff-r616/saved-VREF-only-add-stencil.json','4263f3b08ca71eda5c332bd62e759eb8f67c740da238bd33b0d6f918fba88eef');stencil=json.loads(sf.read_bytes());new=[]
 for uid,row in stencil['exact_new_chunks'].items():
  p=pin(row['file'],row['SHA256']);item=K.A.G.parse(uid,p.read_bytes(),{});assert uid not in expected['copper'];new.append(item)
 def axis(p):return Point(p['at'])if p['kind']=='via'else LineString([p['a'],p['b']])
 def radius(p):return p['d']/2 if p['kind']=='via'else p['w']/2
 dom=c['domains_normalized'];req=lambda a,b:.15 if dom[K.L.norm(a)]==dom[K.L.norm(b)]else .6
 checks=[];errors=[]
 for p in new:
  ax=axis(p);rad=radius(p);layers=K.LAYERS if p['kind']=='via'else[p['layer']]
  for ly in layers:
   for j in trees[ly].query(ax.buffer(rad+.8),predicate='intersects'):
    r=records[ly][int(j)]
    if K.L.norm(r['net'])==p['net']:continue
    if r['kind']=='via':rv=r['source'];gap=ax.distance(Point(rv['x'],rv['y']))-rad-rv['d']/2
    elif r['kind']=='track':rt=r['source'];gap=ax.distance(LineString([rt['a'],rt['b']]))-rad-rt['w']/2
    else:gap=ax.distance(r['shape'])-rad
    row={'new_UUID':p['uuid'],'other_UUID':r['uuid'],'kind':r['kind'],'layer':ly,'other_net':r['net'],'true_gap_mm':gap,'required_with_planner_mm':req(p['net'],r['net'])+.025};checks.append(row)
    if gap<row['required_with_planner_mm']:errors.append(row)
  if p['kind']=='via':
   at=Point(p['at']);near=min(vias,key=lambda v:at.distance(Point(v['x'],v['y'])));gap=at.distance(Point(near['x'],near['y']));row={'new_UUID':p['uuid'],'kind':'ordinary_all-via_pitch','other_UUID':near['uuid'],'distance_mm':gap,'required_mm':.815};checks.append(row)
   if gap<.815:errors.append(row)
   smd=[(q,s)for q in localpads if q['smd']for ly,rs in q['layers'].items()if ly in('F.Cu','B.Cu')for s in K.L.poly(rs)];near=min(smd,key=lambda q:at.distance(q[1]));gap=at.distance(near[1])-.1;row={'new_UUID':p['uuid'],'kind':'all-SMD_drill','other_UUID':near[0]['uuid'],'ref':near[0]['ref'],'pin':near[0]['num'],'gap_mm':gap,'required_mm':.275};checks.append(row)
   if gap<.275:errors.append(row)
 sg=next(p for p in new if p['kind']=='via'and p['net']==VREF);ret=next(p for p in new if p['kind']=='via'and p['net']==COM);source=[]
 for p in new:
  if p['kind']!='segment':continue
  ly=K.MAP[p['layer']];body=axis(p).buffer(.1,quad_segs=128);own=Point(sg['at']).buffer(.525,quad_segs=128);gap=body.difference(own).difference(refs[ly]);name='saved-'+p['uuid']+'-raw-body-source-gap.wkb';(OUT/name).write_bytes(gap.wkb);source.append({'UUID':p['uuid'],'reference_layer':ly,'actual_full_BEFORE_SOURCE_only':True,'own_signal_radius_mm':.525,'raw_body_gap':info(gap),'file':str((OUT/name).resolve())})
 ann=Point(ret['at']).buffer(.25,quad_segs=128).difference(Point(ret['at']).buffer(.1,quad_segs=128));rs=[{'layer':ly,'annular_source_intersection':info(ann.intersection(refs[ly])),'annular_outside_SOURCE':info(ann.difference(refs[ly]))}for ly in refs]
 localoriginal=[t for t in local['tracks']if t['uuid']in stencil['old_coupled_recipe_deletion_UUIDs_DIAGNOSTIC_ONLY']]+[v for v in local['vias']if v['uuid']in stencil['old_coupled_recipe_deletion_UUIDs_DIAGNOSTIC_ONLY']]
 put('all-saved-current-discrete-guard-checks.json',checks);put('saved-current-discrete-guard-errors.json',errors);put('actual-source-body-before-screen.json',source);put('actual-current-old-coupled-originals.json',localoriginal);put('current-local-native-AO1-source-pads.json',[{k:p[k]for k in('uuid','ref','num','net','x','y','smd')}for p in localpads if p['net']in(VREF,COM)])
 cache=OUT/'pinned-current-local-Cu-native-before-source-only-screen.pkl';cache.write_bytes(pickle.dumps({'current':local,'full_before':c,'current_vias':vias,'source_refs':refs,'new':new,'source_root':root,'win':win,'expected':expected},protocol=5))
 r={'verdict':'SAVED_FOUR_ONLY_ADD_BRANCH_DISCRETE_BLOCKED'if errors else'SAVED_FOUR_ONLY_ADD_DISCRETE_GUARDS_CLEAR_SOURCE_ALL_GATES_OPEN','errors':len(errors),'checks':len(checks),'source_body_raw_gap_count':sum(not x['raw_body_gap']['EMPTY']for x in source),'return_pair_mm':math.dist(sg['at'],ret['at']),'return_source':rs,'local_native_pad_pose_count':len(localpads),'diagnostic_originals_still_current_count':len(localoriginal),'input_SHA256':pins,'cache_file':str(cache.resolve()),'cache_SHA256':sha(cache),'raw_current_AFTER_source_fill_pending':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st};put('receipt.json',r);print(json.dumps({k:r[k]for k in('verdict','errors','source_body_raw_gap_count','return_pair_mm','diagnostic_originals_still_current_count','elapsed_seconds')}) ,flush=True)
if __name__=='__main__':main()
