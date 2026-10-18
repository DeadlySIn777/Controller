"""Additive ordinary F-only recovery nominees for DOA Q0 and PEN enable.

Actual current pad groups/source-rooted adjacent plane are authoritative.
No copper withdrawal, new hole, reference handoff, native run or adoption.
"""
import sys,json,pickle,time,math,collections
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import audit_c10036_r24_full_independent_r30 as Q
import construct_di6_direct_source_escape_r5 as K
import tri_route as T
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
C=A.C
REQUESTS=[('/motherboard_do/DOA_Q0_READY_N','/motherboard_motors/FIELD_GND',('J11003','2')),('/motherboard_process/PEN_ENABLE_LOGIC','/LOGIC_GND',('J11001','2'))]
def main():
 started=time.monotonic();out=HERE/'ordinary-Q0-PEN-F-only-nomination-r70.json';assert not out.exists();A.read(__file__);rp=HERE/'di15-safe-root-r22-DI6-bind-r62.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='a8234fa46de66b43eeefcf2bfbdb3d8563bf862a2ce60c46212b17e77ea314be';raw=A.read(r['model_path']);assert C.sha(raw)==r['model_sha256'];cur=pickle.loads(raw);h=cur['h'];g=cur['after'];domains=h['domains_normalized'];source=A.read(cur['binding']['exact_native_discrete_board_file']);identity=A.N.SourceNets(source);inventory=C.inventory(source);graph=json.loads(A.read(HERE/'conflict-graph.json'));policy={L.norm(n):v for n,v in json.loads(A.read(A.S.CONTROLLED))['nets'].items()};rec,trees=F.build({**h,'zones':[]});reserve,exempt=A.reservations();rows=[];newchunks={}
 for net,ground,sourcepad in REQUESTS:
  assert policy.get(net,{}).get('class') in(None,'NONE');assert domains.get(net) is not None and domains.get(net)==domains.get(ground),'Wrong source-ground domain';lost=next(q for q in graph['lost_route_rows'] if q['net']==net);labels=lost['native_lost_relationships'][0]['r06_pad_relationship'];pads={(p['ref'],str(p['num'])):p for p in h['pads'] if L.norm(p['net'])==net};desired=[]
  for label in labels:
   prefix,ordinal=label.rsplit('#',1);ref,pin=prefix.rsplit('.',1);assert ordinal=='0';desired.append(pads[ref,pin]['uuid'])
  _,groups=Q.physical(g,net);needed=[]
  for i,xs in enumerate(groups):
   if {q['uuid'] for q in xs if q['kind']=='pad'}&set(desired):needed.append((i,xs))
  row={'net':net,'raw_net':identity.raw(net),'policy':policy.get(net),'original_r06_native_relationship':labels,'exact_current_pad_UUIDs':desired,'current_required_group_count':len(needed),'ground':ground,'actual_ground_source':list(sourcepad),'candidate':None};rows.append(row)
  if len(needed)!=2:row['not_constructed_reason']='This F-only nominee owns exactly one missing pair between two current groups';continue
  if ground=='/LOGIC_GND':groot=cur['root']
  else:
   print('ORDINARY_RECOVERY_FIELD_ACTUAL_DRILLED_SOURCE_BEGIN',net,flush=True);_,gg=Q.physical(g,ground);groot=next(xs for xs in gg if any(q['kind']=='pad' and(q['ref'],str(q['pin']))==sourcepad for q in xs))
  reference=unary_union([q['shape'] for q in groot if q['kind']=='fill' and q['layer']=='In1.Cu']);term=[unary_union([q['shape'] for q in xs if q['layer']=='F.Cu']) for _,xs in needed];pair=nearest_points(*term);distance=pair[0].distance(pair[1]);win=box(min(p.x for p in pair)-8,min(p.y for p in pair)-8,max(p.x for p in pair)+8,max(p.y for p in pair)+8);obs=[]
  for i in trees['F.Cu'].query(win.buffer(1),predicate='intersects'):
   q=rec['F.Cu'][int(i)];n=L.norm(q['net'])
   if n==net:continue
   gap=.15 if domains.get(net)==domains.get(n) else .6;obs.append(q['shape'].buffer(gap+.030,quad_segs=128))
  for z in cur['zones']:
   n=L.norm(z['net'])
   if z['layer']!='F.Cu' or n==net or z['shape'].distance(win)>1:continue
   gap=max(.15 if domains.get(net)==domains.get(n) else .6,float(z.get('clearance_mm',.15)))+.030;obs.append(z['shape'].buffer(gap,quad_segs=128))
  for z in g['zones']:
   n=L.norm(z['net'])
   if n==net or domains.get(n)==domains.get(net):continue
   for sh in L.poly(z['fills'].get('F.Cu',[])):
    if sh.distance(win)<1:obs.append(sh.buffer(max(.6,float(z.get('clearance_mm',.15)))+.030,quad_segs=128))
  for v in h['vias']:
   if L.norm(v['net'])!=net and Point(v['x'],v['y']).distance(win)<1:obs.append(Point(v['x'],v['y']).buffer(v['drill']/2+.280,quad_segs=128))
  for p in h['pads']:
   if L.norm(p['net'])==net:continue
   obs.extend(sh.buffer(.280,quad_segs=128) for sh in L.poly(p.get('hole') or []) if sh.distance(win)<1)
  for q in h['rule_areas']:
   if 'F.Cu' in q['layers'] and q.get('no_tracks'):obs.extend(sh.buffer(.025,quad_segs=128) for sh in L.poly(q['outline']))
  for q in reserve['keepouts']:
   if 'F.Cu' in q['layers'] and net not in exempt.get(q['name'],set()):obs.extend(sh.buffer(.025,quad_segs=128) for sh in L.poly(q['outline']))
  free=win.difference(unary_union(obs)).buffer(-.105,quad_segs=128).intersection(reference.intersection(win.buffer(1)).buffer(-.105,quad_segs=128));attach=[q.buffer(-.05,quad_segs=128).intersection(free) for q in term];row.update(closest_existing_F_Cu_distance_mm=distance,window_bounds_mm=win.bounds,reference_WKB_sha256=C.sha(reference.wkb),attachment_regions_mm2=[p.area for p in attach]);nominees=[]
  for i,part in enumerate(K.pieces(free)):
   aa=[a.intersection(part) for a in attach]
   if any(a.is_empty for a in aa):continue
   pa,pb=nearest_points(*aa);a=[round(pa.x,6),round(pa.y,6)];b=[round(pb.x,6),round(pb.y,6)]
   if not all(part.covers(Point(p)) for p in(a,b)):continue
   pts,search=T.route(part,tuple(a),tuple(b));pts=[[round(x,6),round(y,6)] for x,y in pts]
   if len(pts)<2:continue
   body=unary_union([A.shape({'kind':'segment','a':a,'b':b,'w':.2}) for a,b in zip(pts,pts[1:])]);gap=body.difference(reference);chunks={};parsed=[]
   for a,b in zip(pts,pts[1:]):
    u,ch=identity.serial_segment(net,'F.Cu',a,b,.2);assert u not in inventory[3] and u not in {q['uuid'] for q in h['tracks']}|{q['uuid'] for q in h['vias']};chunks[u]=ch;parsed.append({'uuid':u,'net':identity.raw(net),'layer':'F.Cu','w':.2,'a':a,'b':b})
   identity.assert_chunks(chunks);candidate={'component':i,'points_mm':pts,'width_mm':.2,'length_mm':LineString(pts).length,'new_tracks':parsed,'exact_new_chunks':{u:b.decode() for u,b in chunks.items()},'full_body_source_rooted_In1_reference_gap_mm2':gap.area,'actual_current_F_contact_overlap_mm2':[body.intersection(q).area for q in term],'new_layer_transitions':0,'new_holes':0,'source_connected_ref_plane':'actual '+sourcepad[0]+'.'+sourcepad[1]+' In1','search':search};nominees.append(candidate)
   if gap.area<1e-10 and all(x>.004 for x in candidate['actual_current_F_contact_overlap_mm2']):row['candidate']=candidate;newchunks.update(chunks);break
  row['tested_nominees']=nominees;print('ORDINARY_F_ONLY_RESULT',net,bool(row['candidate']),row['attachment_regions_mm2'],flush=True)
 report={'verdict':'ORDINARY_F_ONLY_RECOVERY_NOMINEES_INDEPENDENT_FULL_NATIVE_OPEN','current_exact_model_sha256':r['model_sha256'],'R62_receipt_sha256':C.sha(A.read(rp)),'source_parent_sha256':C.sha(source),'rows':rows,'new_exact_chunks':{u:b.decode() for u,b in newchunks.items()},'ready_nominees_count':sum(q['candidate'] is not None for q in rows),'old_items_deleted':0,'new_holes':0,'current_all_contacts_r06_r07_power_fill_source_keys_reference_native_DRC_SI':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'positive':report['ready_nominees_count'],'rows':[{k:v for k,v in q.items() if k not in('tested_nominees','policy')} for q in rows]}),flush=True)
if __name__=='__main__':main()
