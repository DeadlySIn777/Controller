"""Continuous ordinary DI15 escape, preserving current fault and DI6 copper.

Latest frozen R59 power/protected model and R11 owned DI6 additions are hard.
Every result is nomination only until an independent full/native audit.
"""
import sys,pickle,json,math,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import tri_route as T
import construct_di6_direct_source_escape_r5 as K
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
P,G,S,C,N=A.P,A.G,A.S,A.C,A.N
NET='/motherboard_di/DI15_LOGIC';GND='/LOGIC_GND';LAYERS=K.LAYERS

def main():
 started=time.monotonic();out=HERE/'di15-reference-escape-nomination-r12.json';assert not out.exists();A.read(__file__)
 r11=json.loads(A.read(HERE/'di6-reference-corrected-full-audit-r11.json'));assert r11['clearance_errors']==[] and r11['contact_losses']==[] and r11['pad_losses']==[] and r11['unchanged_neighbor_reference_losses']==[]
 cp=pickle.loads(A.read(HERE/'di6-reference-r11-physical-checkpoint.pkl'));assert C.sha(A.read(HERE/'di6-reference-r11-physical-checkpoint.pkl'))==r11['immutable_physical_checkpoint_sha256'];h=cp['h2'];zones=cp['zones'];before=cp['after'];refs=cp['refs'];source=A.read(cp['binding']['exact_native_discrete_board_file']);identity=N.SourceNets(source);policy={L.norm(n):v for n,v in json.loads(A.read(S.CONTROLLED))['nets'].items()}.get(NET);assert policy is None or policy.get('class') in(None,'NONE')
 pads={p['ref']+'.'+str(p['num']):p for p in h['pads'] if L.norm(p['net'])==NET};assert 'U13001.25'in pads and 'U17005.9'in pads;src=pads['U13001.25'];dst=pads['U17005.9'];assert src['smd'] and dst['smd'];sourcepad=unary_union(L.poly(src['layers']['F.Cu']));targetpad=unary_union(L.poly(dst['layers']['F.Cu']));win=box(110,81,137,123);domain=h['domains_normalized'];rec,trees=F.build({**h,'zones':[]});reserve,exempt=A.reservations();hard=[]
 for r in h['rule_areas']:
  if r.get('no_tracks') or r.get('no_vias'):
   for sh in L.poly(r['outline']):
    if sh.distance(win)<2:hard.append({'uuid':r['uuid'],'layers':r['layers'],'shape':sh,'no_tracks':r.get('no_tracks'),'no_vias':r.get('no_vias'),'exempt':set()})
 for r in reserve['keepouts']:
  for sh in L.poly(r['outline']):
   if sh.distance(win)<2:hard.append({'uuid':r['name'],'layers':r['layers'],'shape':sh,'no_tracks':True,'no_vias':True,'exempt':exempt.get(r['name'],set())})
 holes=[]
 for v in h['vias']:
  if Point(v['x'],v['y']).distance(win)<2:holes.append((v['uuid'],L.norm(v['net']),Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)))
 for p in h['pads']:
  for sh in L.poly(p.get('hole') or []):
   if sh.distance(win)<2:holes.append((p['uuid'],L.norm(p['net']),sh))
 smd=[sh for p in h['pads'] if p['smd'] for l,rs in p['layers'].items() if l in('F.Cu','B.Cu') for sh in L.poly(rs) if sh.distance(win)<2]
 records={l:[rec[l][int(i)] for i in trees[l].query(win.buffer(2),predicate='intersects')] for l in LAYERS};free={};via={};priorbodies=[]
 # Exclude sites that would cut any currently source-rooted signal body.
 # This is a conservative nomination screen; independent exact losses follow.
 for t in h['tracks']:
  l=t['layer'];n=L.norm(t['net'])
  if l not in refs or n==GND or domain.get(n)!=domain.get(GND):continue
  bounds=box(min(t['a'][0],t['b'][0])-t['w']/2,min(t['a'][1],t['b'][1])-t['w']/2,max(t['a'][0],t['b'][0])+t['w']/2,max(t['a'][1],t['b'][1])+t['w']/2)
  if not bounds.intersects(win.buffer(1)):continue
  body=L.body(t) if t.get('m') is not None else A.shape({'kind':'segment',**t});covered=body.intersection(refs[l].intersection(win.buffer(2)))
  if not covered.is_empty:priorbodies.append(covered)
 prior=unary_union(priorbodies)
 for net in(NET,GND):
  for l in LAYERS:
   obs=[]
   for q in records[l]:
    n=L.norm(q['net'])
    if n==net:continue
    gap=.15 if domain.get(n)==domain.get(net) else .6;obs.append(q['shape'].buffer(gap+.030,quad_segs=128))
   for z in before['zones']:
    n=L.norm(z['net']);gap=.15 if domain.get(n)==domain.get(net) else .6
    if n==net or gap==.15:continue
    for sh in L.poly(z['fills'].get(l,[])):
     if sh.distance(win)<2:obs.append(sh.buffer(max(gap,float(z.get('clearance_mm',.15)))+.030,quad_segs=128))
   for z in zones:
    n=L.norm(z['net'])
    if z['layer']!=l or n==net or z['shape'].distance(win)>2:continue
    gap=.15 if domain.get(n)==domain.get(net) else .6;obs.append(z['shape'].buffer(max(gap,float(z.get('clearance_mm',.15)))+.030,quad_segs=128))
   obs += [sh.buffer(.280,quad_segs=128) for u,n,sh in holes if n!=net]
   obs += [q['shape'].buffer(.025,quad_segs=128) for q in hard if q['no_tracks'] and l in q['layers'] and net not in q['exempt']]
   physical=win.difference(unary_union(obs));free[net,l]=physical.buffer(-.105)
   if net==NET and l in refs:free[net,l]=free[net,l].intersection(refs[l].intersection(win.buffer(1)).buffer(-.105))
  aa=[]
  for l in LAYERS:
   obs=[]
   for q in records[l]:
    n=L.norm(q['net'])
    if n==net:continue
    gap=.15 if domain.get(n)==domain.get(net) else .6;obs.append(q['shape'].buffer(.25+gap+.030,quad_segs=128))
   for z in zones:
    n=L.norm(z['net'])
    if z['layer']!=l or n==net or z['shape'].distance(win)>2:continue
    gap=.15 if domain.get(n)==domain.get(net) else .6;obs.append(z['shape'].buffer(.25+max(gap,float(z.get('clearance_mm',.15)))+.030,quad_segs=128))
   for z in before['zones']:
    n=L.norm(z['net']);gap=.15 if domain.get(n)==domain.get(net) else .6
    if n==net or gap==.15:continue
    for sh in L.poly(z['fills'].get(l,[])):
     if sh.distance(win)<2:obs.append(sh.buffer(.25+max(gap,float(z.get('clearance_mm',.15)))+.030,quad_segs=128))
   obs += [q['shape'].buffer(.275,quad_segs=128) for q in hard if q['no_vias'] and l in q['layers'] and net not in q['exempt']]
   aa.append(win.difference(unary_union(obs)))
  r=aa[0]
  for p in aa[1:]:r=r.intersection(p)
  obs=[Point(v['x'],v['y']).buffer(.81,quad_segs=128) for v in h['vias'] if Point(v['x'],v['y']).distance(win)<2]
  obs += [sh.buffer(.380,quad_segs=128) for u,n,sh in holes]+[sh.buffer(.380,quad_segs=128) for sh in smd]
  obs.append(prior.buffer(.530 if net==NET else .105,quad_segs=128));via[net]=r.difference(unary_union(obs))
 rooted=refs['F.Cu'].intersection(refs['In3.Cu']).intersection(win);via[NET]=via[NET].intersection(rooted.buffer(-.530));via[GND]=via[GND].intersection(rooted)
 srcattach=sourcepad.buffer(-.075).intersection(free[NET,'F.Cu']);dstattach=targetpad.buffer(-.075).intersection(free[NET,'F.Cu']);sp=K.sites(srcattach,list(sourcepad.centroid.coords)[0],8);dp=K.sites(dstattach,list(targetpad.centroid.coords)[0],8);ins=K.pieces(free[NET,'In3.Cu']);pairs=[];attempts=[]
 for si,srow in enumerate(sp):
  sf=unary_union([p for p in K.pieces(free[NET,'F.Cu']) if p.covers(Point(srow['at_mm']))]);sr=via[NET].intersection(sf).intersection(Point(sourcepad.centroid).buffer(5,quad_segs=128))
  for di,drow in enumerate(dp):
   df=unary_union([p for p in K.pieces(free[NET,'F.Cu']) if p.covers(Point(drow['at_mm']))]);dr=via[NET].intersection(df).intersection(Point(targetpad.centroid).buffer(5,quad_segs=128))
   for part in ins:
    a=sr.intersection(part);b=dr.intersection(part)
    if a.is_empty or b.is_empty:continue
    for sa in K.sites(a,[118.45,90.75],8):
     pa=Point(sa['at_mm']);ra=K.sites(via[GND].intersection(pa.buffer(1,quad_segs=128).difference(pa.buffer(.825,quad_segs=128))),[sa['at_mm'][0]-.9,sa['at_mm'][1]],4)
     if not ra:continue
     for sb in K.sites(b,[131.25,112.35],8):
      pb=Point(sb['at_mm']);rb=K.sites(via[GND].intersection(pb.buffer(1,quad_segs=128).difference(pb.buffer(.825,quad_segs=128))),[sb['at_mm'][0]+.9,sb['at_mm'][1]],4)
      if not rb:continue
      pairs.append({'source_attachment':srow['at_mm'],'target_attachment':drow['at_mm'],'signals':[sa['at_mm'],sb['at_mm']],'returns':[ra[0]['at_mm'],rb[0]['at_mm']],'score_mm':sa['cost_mm']+sb['cost_mm']})
   if pairs:break
  if pairs:break
 print('DI15_CONTINUOUS_EXACT_REFERENCE_PAIRS',len(pairs),srcattach.area,dstattach.area,flush=True)
 for pair in sorted(pairs,key=lambda p:p['score_mm'])[:12]:
  attempt={**pair,'paths':[]};attempts.append(attempt);returncuts=unary_union([Point(at).buffer(.530,quad_segs=128) for at in pair['returns']])
  for l,a,b in [('F.Cu',pair['source_attachment'],pair['signals'][0]),('In3.Cu',pair['signals'][0],pair['signals'][1]),('F.Cu',pair['signals'][1],pair['target_attachment'])]:
   ff=free[NET,l].difference(returncuts);pp=[p for p in K.pieces(ff) if p.covers(Point(a)) and p.covers(Point(b))]
   if not pp:attempt['failed_layer']=l;break
   pts,search=T.route(pp[0],tuple(a),tuple(b));pts=[[round(x,6),round(y,6)] for x,y in pts];full=unary_union([A.shape({'kind':'segment','a':a,'b':b,'w':.2}) for a,b in zip(pts,pts[1:])]);attempt['paths'].append({'layer':l,'points_mm':pts,'width_mm':.2,'length_mm':LineString(pts).length,'prior_actual_rooted_reference_gap_mm2':full.difference(refs[l]).area,'search':search})
  if len(attempt['paths'])==3:break
 result={'verdict':'DI15_ORDINARY_EXACT_REFERENCE_CANDIDATE_NOMINATED_INDEPENDENT_NATIVE_OPEN' if attempts and len(attempts[-1]['paths'])==3 else'DI15_CONTINUOUS_REFERENCE_ESCAPE_INCOMPLETE','source_parent_sha256':C.sha(source),'parent_DI6_R11_receipt_sha256':C.sha(A.read(HERE/'di6-reference-corrected-full-audit-r11.json')),'parent_DI6_R11_checkpoint_sha256':C.sha(A.read(HERE/'di6-reference-r11-physical-checkpoint.pkl')),'DI6_host_reference_remains_OPEN':True,'policy':policy,'exact_raw_net':identity.raw(NET),'actual_source_pad_UUID':src['uuid'],'actual_target_pad_UUID':dst['uuid'],'source_pad_bounds_mm':sourcepad.bounds,'target_pad_bounds_mm':targetpad.bounds,'source_attachment_area_mm2':srcattach.area,'target_attachment_area_mm2':dstattach.area,'continuous_signal_legal_region_area_mm2':via[NET].area,'continuous_return_legal_region_area_mm2':via[GND].area,'source_root':'J11001.2','all_current_DI6_and_fault_copper_hard_unchanged':True,'ordinary_new_vias_all6_required':True,'no_current_deletes':True,'pairs':pairs,'attempts':attempts,'independent_final_cuts_contact_reference_returns_native_SI':'OPEN','native_jobs':0,'board_written':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started}
 out.write_text(json.dumps(result,indent=1)+'\n');print(json.dumps({'verdict':result['verdict'],'attempts':attempts,'sha256':C.sha(out.read_bytes())}),flush=True)
if __name__=='__main__':main()
