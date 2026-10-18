"""Rotate one monitor resistor in place and connect its ground to the actual local ground pad."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import copy,hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision
from shapely.affinity import rotate
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import complete_geometry_r2 as G
import core_inner_feed_r18 as I
import tri_route as T
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
def parts(s):
 if s.is_empty:return []
 if s.geom_type=='Polygon':return [s]
 return [q for p in getattr(s,'geoms',[])for q in parts(p)]
def main():
 mp=H/'safe-logic-five-and-fag-margin-r22/model.pkl';assert sha(mp)=='014b37594d378cd3e1a606cb1c06a0ad0b1b3ffea5cb836132bfaeec80d3a52a'
 out=H/'field-monitor-R9026-rotation-source-via-r64';assert not out.exists();out.mkdir();g,h,b,z,current=pickle.loads(mp.read_bytes());h=copy.deepcopy(h)
 old=next(t for t in h['tracks']if t['uuid']=='b7ddd466-0bed-4b5a-968d-9ef0ce166364');h['tracks']=[t for t in h['tracks']if t['uuid']!=old['uuid']]
 fp=next(q for q in h['footprints']if q['ref']=='R9026');origin=(fp['x'],fp['y']);priorpads=copy.deepcopy([p for p in h['pads']if p['ref']=='R9026']);assert fp['value']=='10000R 0.01% 5ppm'and len(priorpads)==2
 for p in h['pads']:
  if p['ref']!='R9026':continue
  p['x']=round(2*origin[0]-p['x'],6);p['y']=round(2*origin[1]-p['y'],6)
  p['layers']={l:G.records(set_precision(rotate(unary_union(C.poly(rings)),180,origin=origin),1e-6,mode='pointwise'))for l,rings in p['layers'].items()}
 fp['owned_native_rotation_pending_degrees']=180
 moved=[p for p in h['pads']if p['ref']=='R9026'];uv=next(p for p in moved if p['num']=='1');fgpad=next(p for p in moved if p['num']=='2');ground=C.norm(fgpad['net'])
 groups=F.graph(current,ground);source=next(xs for xs in groups if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11003','2')for q in xs));landing=H/'field-monitor-ground-counterfactual-r51';lr=json.loads((landing/'receipt.json').read_bytes());ld=pickle.loads((landing/'proposed-discrete.pkl').read_bytes());assert sha(landing/'proposed-discrete.pkl')==lr['proposed_discrete_sha256']and len(ld['vias'])==1;v=ld['vias'][0];assert v['uuid']=='1069fdeb-c67f-58d9-bb46-c0c33ccfdda0'and v['d']==.5 and v['drill']==.2 and len(v['flashed'])==6 and C.norm(v['net'])==ground
 ann=N.bounded_disk(v,.25).difference(N.bounded_disk(v,.1));sourceIn1=unary_union([q['shape']for q in source if q['kind']=='fill'and q['layer']=='In1.Cu']);assert ann.intersection(sourceIn1).area>.01,'Exact unchanged actual J3-rooted In1 annular landing required'
 h['vias'].append(v);target={'ref':'@NEW_ordinary_FG_landing','uuid':v['uuid'],'x':v['x'],'y':v['y']}
 refs={l:unary_union([q['shape']for q in source if q['kind']=='fill'and q['layer']==l])for l in ('In1.Cu','In4.Cu')}
 peer=H/'field-power/regulated-four-retained-hard-snapshot-r127';pd=pickle.loads((peer/'proposed-discrete.pkl').read_bytes());pq=pickle.loads((peer/'proposed-zones.pkl').read_bytes());I.p.WINDOW=box(.526,.526,449.474,234.474);win=box(342,55,353,68);outline=unary_union(C.poly(h['outline'])).buffer(-.626);new=[];rows=[]
 def route(raw,start,end,own_target):
  domain=h['domains_normalized'][C.norm(raw)];mh={**h,'tracks':h['tracks']+pd['tracks']+new,'vias':h['vias']+pd['vias']};records,trees=F.build({**mh,'zones':[]});obs=[]
  for i in trees['F.Cu'].query(win.buffer(2),predicate='intersects'):
   q=records['F.Cu'][int(i)]
   if q['net']==raw:continue
   n=(.15 if h['domains_normalized'][C.norm(q['net'])]==domain else .6)+.025+.000020
   if q['kind']=='track':t=q['source'];obs.append(N.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+.1+n))
   elif q['kind']=='via':v=q['source'];obs.append(N.bounded_disk(v,v['d']/2+.1+n))
   else:obs.append(N.bounded_buffer(q['shape'],.1+n))
  holes=[s for p in mh['pads']for s in C.poly(p.get('hole')or [])]+[N.bounded_disk(v,v['drill']/2)for v in mh['vias']]
  obs.extend(N.bounded_buffer(s,.1+.275+.000020)for s in holes if win.buffer(2).intersects(s))
  hard=I.p.hard_shapes(mh,I.L.live.reservations(),C.norm(raw),'F.Cu');courtyard_changes=[]
  if own_target['ref']=='U9003':
   tfp=next(p for p in h['footprints']if p['ref']=='U9003');courts=[s.buffer(.6)for rings in tfp.get('courtyard',{}).values()for s in C.poly(rings)];corridor=box(end[0]-.11,end[1]-1.5,end[0]+.11,end[1]+.025)
   altered=[]
   for s in hard:
    if any(s.equals(q)for q in courts):altered.append(s.difference(corridor));courtyard_changes.append({'target':'U9003.7','limited_own_conservative_outer_exit_corridor':list(corridor.bounds),'actual_foreign_pads_Cu_drills_native_keepouts_and_all_reservations_unchanged':True})
    else:altered.append(s)
   hard=altered
  obs.extend(N.bounded_buffer(s,.1+.025+.000020)for s in hard if win.buffer(2).intersects(s))
  for q in z+pq:
   if q['net']==raw or q['layer']!='F.Cu'or not win.buffer(2).intersects(q['shape']):continue
   n=max(.15 if h['domains_normalized'][C.norm(q['net'])]==domain else .6,float(q.get('clearance_mm',.15)))+.025+.000020;obs.append(N.bounded_buffer(q['shape'],.1+n))
  free=set_precision(win.intersection(outline).difference(unary_union(obs)),1e-6);faces=[p for p in parts(free)if p.covers(Point(start))and p.covers(Point(end))];row={'net':raw,'start':start,'end':end,'source_legal':free.covers(Point(start)),'target_legal':free.covers(Point(end)),'common_faces':len(faces),'courtyard_changes':courtyard_changes}
  for face in faces:
   try:points,proof=T.route(face,start,end)
   except(AssertionError,ValueError):continue
   points=[[round(x,6),round(y,6)]for x,y in points]
   if not face.covers(LineString(points)):continue
   ts=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-monitor-rotation-r64/'+raw+'/'+repr((a,bb)))),'net':raw,'a':a,'b':bb,'w':.2,'layer':'F.Cu'}for a,bb in zip(points,points[1:])];row.update(points=points,length_mm=LineString(points).length,constructor=proof,replacement_tracks=ts)
   if C.norm(raw)!=ground:row['new_UV_full_body_reference_gap_mm2']={l:N.bounded_buffer(LineString(points),.1).difference(refs[l]).area for l in refs}
   return ts,row
  return [],row
 uvtracks,ur=route(uv['net'],[uv['x'],uv['y']],old['b'],uv);rows.append(ur);new+=uvtracks;print('R64_UV',len(uvtracks),ur.get('length_mm'),flush=True)
 if uvtracks:
  groundtracks,gr=route(fgpad['net'],[fgpad['x'],fgpad['y']],[target['x'],target['y']],target);rows.append(gr);new+=groundtracks;print('R64_GROUND',len(groundtracks),gr.get('length_mm'),flush=True)
 else:groundtracks=[]
 delta={'tracks':new,'vias':[v],'removed_old_track':old,'old_R9026_pads':priorpads,'new_R9026_pads':moved,'R9026_rotation_deg':180,'unchanged_FP_center_mm':list(origin),'same_value_exact_pad_UUID_nets_dimensions':True,'native_rotation_attestation':'OPEN'};(out/'owned-delta.pkl').write_bytes(pickle.dumps(delta,protocol=5))
 put(out/'receipt.json',{'verdict':'ROTATED_MONITOR_SIGNAL_AND_LOCAL_GROUND_PATHS_GEOMETRY_NOMINATION'if uvtracks and groundtracks else'ROTATED_MONITOR_FINITE_ROUTE_INCOMPLETE','parent_sha256':sha(mp),'rows':rows,'delta_sha256':sha(out/'owned-delta.pkl'),'unchanged_ground_target_UUID':target['uuid'],'actual_J3_source_root_target':True,'source_native_rotation_exact_pads_old_contacts_references_current_threshold_gates':'OPEN','new_holes':1,'ordinary_via_annular_actual_J3_source_overlap_mm2':ann.intersection(sourceIn1).area,'actual_all6_flash_SMD_aperture_native_contract':'OPEN','native_jobs':0,'adopted':False,'board_written':False})
 print('R64_COMPLETE',bool(uvtracks and groundtracks),flush=True)
if __name__=='__main__':main()
