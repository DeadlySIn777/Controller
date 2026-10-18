"""Restore two owned AUX tracks around an actual-source FIELD5 static feed."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import copy,pickle,json,sys,uuid,re
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
import contact_layout as C
import fast_contacts as F
import tri_route as T
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import complete_geometry_r2 as G
import guarded_declared_settings_projection_r58 as P
O=H/'R11054-coupled-no-hole-FIELD5-AUX-feed-r198'
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def polys(s):return[s] if s.geom_type=='Polygon' else[q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def main():
 assert not O.exists();O.mkdir();B=H/'R11054-rotated-AUX-source-search-base-r194';assert sha(B/'model.pkl')=='344b9416a4e86e12ca3587d2a4e1439e1ddd943510afcf3f33ae1fa9282827f3';g,h,b,z,c=pickle.loads((B/'model.pkl').read_bytes());h=copy.deepcopy(h)
 R=H/'R11054-fault-preserving-exact-AUX-wall-r192';r=json.loads((R/'receipt.json').read_text(encoding='utf-8'));d=pickle.loads((R/'nomination.pkl').read_bytes());withdraw={q['uuid'] for q in d['tracks']};h['tracks']=[q for q in h['tracks'] if q['uuid'] not in withdraw]
 # Host FP geometry has explicit physical pads/courtyard. Correct metadata to
 # the exact native root-only rotation (-90+180=90); do not infer angle zero.
 fp=next(q for q in h['footprints'] if q['ref']=='R11054');assert fp['x']==221 and fp['y']==42.9;fp['rot']=90
 field=next(q for q in h['pads'] if(q['ref'],q['num'])==('R11054','1'));fieldnet=field['net'];fieldshape=unary_union(C.poly(field['layers']['F.Cu']));groups=F.graph(c,fieldnet);root=next(xs for xs in groups if any(q['kind']=='pad' and(q.get('ref'),q.get('pin'))==('L11003','2') for q in xs));goal=unary_union([q['shape'] for q in root if q['layer']=='F.Cu' and q['kind']!='fill']);assert not goal.is_empty
 print('R198 actual FIELD5 F source distance',fieldshape.distance(goal),flush=True)
 owned=r['owned_original_two_tracks'];aux=owned[0]['net'];a=Point(owned[0]['a']);bb=Point(owned[1]['b']);rec,trees=F.build({**h,'zones':[]});tm={q['uuid']:q for q in h['tracks']};vm={q['uuid']:q for q in h['vias']};outline=unary_union(C.poly(h['outline'])).buffer(-.526)
 res=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text(encoding='utf-8'));dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text(encoding='utf-8');exceptions={}
 for line in dru.splitlines():
  mm=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if mm:exceptions[mm[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",mm[2])}
 mask_cache={}
 def route(net,start,end,width,margin,extra):
  aa,cc=nearest_points(start,end);win=box(min(aa.x,cc.x)-margin,min(aa.y,cc.y)-margin,max(aa.x,cc.x)+margin,max(aa.y,cc.y)+margin).intersection(outline);walls=[]
  for j in trees['F.Cu'].query(win.buffer(.627),predicate='intersects'):
   q=rec['F.Cu'][int(j)]
   if q['net']==net:continue
   guard=G.gap(h,net,q['net'])+.025+width/2+.00002
   if q['kind']=='track':t=tm[q['uuid']];walls.append(P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+guard))
   elif q['kind']=='via':v=vm[q['uuid']];walls.append(P.bounded_buffer(Point(v['x'],v['y']),v['d']/2+guard))
   else:walls.append(P.bounded_buffer(q['shape'],guard))
  for q in z:
   if q['layer']=='F.Cu' and q['net']!=net and q['shape'].intersects(win.buffer(.627)):walls.append(P.bounded_buffer(q['shape'],max(G.gap(h,net,q['net']),float(q.get('clearance_mm',.15)))+.025+width/2+.00002))
  for q in h['rule_areas']:
   if q.get('no_tracks') and 'F.Cu' in q['layers']:walls.extend(P.bounded_buffer(s,.025+width/2+.00002) for s in C.poly(q['outline']) if s.intersects(win))
  for q in res['keepouts']:
   if 'F.Cu' in q['layers'] and C.norm(net) not in exceptions.get(q['name'],set()):walls.extend(P.bounded_buffer(s,.025+width/2+.00002) for s in C.poly(q['outline']) if s.intersects(win))
  for sh,raw in extra:walls.append(P.bounded_buffer(sh,G.gap(h,net,raw)+.025+width/2+.00002))
  free=set_precision(win.difference(unary_union(walls)),1e-6);options=[]
  for part in polys(free):
   st=part.buffer(-.000002).intersection(start);en=part.buffer(-.000002).intersection(end)
   if st.is_empty or en.is_empty:continue
   options.append((st.distance(en),part,st,en))
  if not options:return None
  _,part,st,en=min(options,key=lambda q:q[0]);aa,cc=nearest_points(st,en)
  if aa.distance(cc)<.000001:return None
  pts,search=T.route(part,tuple(aa.coords[0]),tuple(cc.coords[0]));pts=[[round(x,6),round(y,6)] for x,y in pts];line=LineString(pts);assert free.covers(line);body=P.bounded_buffer(line,width/2)
  return {'points_mm':pts,'length_mm':line.length,'width_mm':width,'body':body,'search':search,'raw_net':net,'source_Cu_overlap_mm2':body.intersection(start).area,'destination_Cu_overlap_mm2':body.intersection(end).area}
 answer=None;attempts=[];avoid=[]
 for trial in range(8):
  power=None
  for width in (.2,.25):
   for margin in (1.5,3.,6.,12.):
    power=route(fieldnet,fieldshape,goal,width,margin,[(s,aux) for s in avoid])
    if power:break
   if power:break
  if not power:attempts.append({'trial':trial,'verdict':'NO_ACTUAL_SOURCE_F_FIELD5_ROUTE'});break
  companion=None
  for margin in (1.5,3.,6.,12.):
   companion=route(aux,a,bb,.2,margin,[(power['body'],fieldnet)])
   if companion:break
  print('R198 trial',trial,'power',power['length_mm'],'AUX',companion['length_mm'] if companion else None,flush=True)
  if companion:answer={'FIELD5':power,'AUX5_B':companion};break
  attempts.append({'trial':trial,'FIELD5_route':{k:v for k,v in power.items() if k!='body'},'verdict':'NO_AUX_RESTORE_AROUND_FIELD5'});avoid.append(power['body'])
 tracks=[];rows=[]
 if answer:
  for role,rr in answer.items():
   ids=[]
   for i,(aa,cc) in enumerate(zip(rr['points_mm'],rr['points_mm'][1:])):
    if aa==cc:continue
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-R11054-coupled-source-AUX-r198/{role}/{i}'));tracks.append({'uuid':uid,'net':rr['raw_net'],'a':aa,'b':cc,'w':rr['width_mm'],'layer':'F.Cu','locked':True,'prospective_not_native':True});ids.append(uid)
   rows.append({'role':role,'new_track_UUIDs':ids,'route':{k:v for k,v in rr.items() if k!='body'}})
  (O/'nomination.pkl').write_bytes(pickle.dumps({'tracks':tracks,'new_pad1':field,'new_FP':fp,'owned_original_two_tracks':owned,'replaced_diagnostic_R192_nominee_track_UUIDs':sorted(withdraw),'routes':answer},protocol=5))
 write(O/'receipt.json',{'verdict':'COUPLED_NO_HOLE_FIELD5_AND_EXACT_AUX_RESTORE_NOMINATED' if answer else 'COUPLED_NO_HOLE_FIELD5_AUX_REPAIR_INCOMPLETE','input_model_sha256':sha(B/'model.pkl'),'actual_source':'L11003.2','static_pullup_current_upper_A':.0005230769230769231,'owned_original_two_tracks':owned,'new_FP_pose_mm_deg':[221,42.9,90],'old_native_FP_pose_mm_deg':[221,41.25,-90],'R192_added_host_rot_metadata180_superseded_without_changing_absolute_pad_or_courtyard_geometry':True,'pin2_fault_pad_UUID_raw_net_and_absolute_geometry_unchanged':True,'width_current_BOM_limits_and_all_fitted_channels_preserved':True,'rows':rows,'attempts':attempts,'new_holes':0,'nomination_sha256':sha(O/'nomination.pkl') if answer else None,'complete_source_contact_old_reference_AUX_current_drop_and_native_gates':'OPEN','native_jobs':0,'board_written':False});print('R198_RECEIPT',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
