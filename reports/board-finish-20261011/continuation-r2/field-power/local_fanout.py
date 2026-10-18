"""Four-part field-B LDO cluster fanout and feed witnesses; no native jobs."""
import copy,json,math,sys,time
from collections import defaultdict
from shapely.geometry import Point,LineString,box,mapping
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import affinity
from contact_layout import HERE,BASE,load,build,poly,norm,S,footprint_shape,identity
from inventory import sha
GND='/motherboard_do/FIELD_B_0V';IN='/motherboard_safety_sensor/FIELD_B_5V_PRE';OUT='DOB_DO_FIELD_3V3';PG='/motherboard_power_entry/FB_PGOOD'
def main():
 g,binding=load();static,trees=build(g,layers={'F.Cu','B.Cu'})
 proposals=json.loads((HERE/'new-LDO-placement-r3.json').read_text(encoding='utf-8'))['placement_candidates']
 model=json.loads((HERE/'normal-model-r2.json').read_text(encoding='utf-8'))
 src=json.loads((HERE/'ab-prereg-split-source/receipt-r3.json').read_text(encoding='utf-8'))
 candidates=[];oldpads={}
 for p in g['pads']:oldpads.setdefault((p['ref'],p['num']),[]).append(p)
 courts=[]
 for f in g['footprints']:courts.extend(q for ps in f['courtyard'].values() for q in poly(ps))
 court_tree=STRtree(courts)
 def fit(ref,xy,addedcourts):
  f,c=footprint_shape(g,ref);dx,dy=xy[0]-f['x'],xy[1]-f['y'];c=affinity.translate(c,dx,dy)
  if any(c.intersects(courts[i]) for i in court_tree.query(c,predicate='intersects')) or any(c.intersects(q) for q in addedcourts):return None
  for p in [p for p in g['pads'] if p['ref']==ref]:
   for layer,ps in p['layers'].items():
    sh=affinity.translate(unary_union(poly(ps)),dx,dy)
    for i in trees[layer].query(sh.buffer(.625),predicate='intersects'):
     r=static[layer][i]
     if r['kind']=='fill':continue
     if sh.distance(r['shape'])<(.15 if r['domain']=='DOM_FIELD_B' else .6)+.025:return None
  return c
 # Prefer the nearer southern candidate. Also try every independently fitted
 # cluster; failed fanouts are retained, not accepted as electrical connection.
 order=sorted(proposals,key=lambda p:math.dist(p['U11038']['position_mm'],[129.44,141.2]))
 for proposal in order:
  poses={'U11038':proposal['U11038']['position_mm'],**{p['ref']:p['position_mm'] for p in proposal['passives']}}
  u=poses['U11038'];basecourt=fit('U11018',u,[])
  assert basecourt is not None
  # Optimize the input bypass pad-to-IN/ground loop, with unchanged cap pose.
  fixedcourts=[basecourt]+[fit(src['new_components'][r]['clone'],poses[r],[]) for r in ['C11093','R11088']]
  cands=[]
  for ix in range(-12,13):
   for iy in range(-12,13):
    xy=(u[0]+ix/2,u[1]+iy/2);c=fit('C11076',xy,fixedcourts)
    if c is None:continue
    p1=(xy[0]-1.475,xy[1]);p2=(xy[0]+1.475,xy[1]);score=math.dist(p1,(u[0]+.975,u[1]+2.2))+math.dist(p2,u)
    cands.append((score,xy))
  if cands:poses['C11092']=list(min(cands)[1])
  pads={};new=[]
  for ref,part in src['new_components'].items():
   clone=part['clone'];f,_=footprint_shape(g,clone);delta=(poses[ref][0]-f['x'],poses[ref][1]-f['y'])
   for p in [p for p in g['pads'] if p['ref']==clone and p['num']]:
    n=part['pins'][p['num']]
    if n is None:n=p['net'].replace(clone,ref)
    n=norm(n);sh=affinity.translate(unary_union(poly(p['layers'].get('F.Cu',[]))),*delta)
    at=(p['x']+delta[0],p['y']+delta[1]);pads[ref+'.'+p['num']]={'net':n,'shape':sh,'at':at,'ref':ref,'pin':p['num']}
    new.append({'kind':'pad','net':n,'shape':sh,'domain':'DOM_FIELD_B','ref':ref,'pin':p['num']})
  rows=[];accepted=[];window=box(u[0]-10,u[1]-10,u[0]+10,u[1]+10)
  def free(net,width,area):
   obstacles=[];fill_void=[]
   for i in trees['F.Cu'].query(area.buffer(2),predicate='intersects'):
    r=static['F.Cu'][i]
    if norm(r['net'])==net:continue
    if r['kind']=='fill':fill_void.append(identity(r));continue
    clearance=.15 if r['domain']=='DOM_FIELD_B' else .6
    obstacles.append(r['shape'].buffer(clearance+width/2+.025))
   for r in new+accepted:
    if norm(r['net'])!=net:obstacles.append(r['shape'].buffer(.15+width/2+.025))
   for a in g['rule_areas']:
    if 'F.Cu' in a['layers'] and a.get('no_tracks'):obstacles.extend(q.buffer(width/2+.025) for q in poly(a['outline']))
   return area.difference(unary_union(obstacles)),fill_void
  def route(a,b,net,width,scope='local'):
   aa,bb=pads[a],pads[b];fr,voids=free(net,width,window)
   seeds=lambda p:[(p['at'],{'key':p['ref']+'.'+p['pin'],'uuid':'PROPOSED-'+p['ref']+'.'+p['pin'],'kind':'new_pad'})]
   path,search=S.astar(fr.buffer(-.00001),seeds(aa),seeds(bb),time.monotonic()+3,node_cap=50000)
   row={'from':a,'to':b,'net':net,'width_mm':width,'search':search,'scope':scope}
   if path and not fr.covers(LineString(path['points_mm'])):
    search={'reason':'rounded path escaped strict free geometry; withheld','nodes':search['nodes']};row['search']=search;path=None
   if path:
    line=LineString(path['points_mm'])
    row.update(verdict='HOST_PATH',path=path,mandatory_fill_voids=voids)
    accepted.append({'kind':'track','net':net,'shape':line.buffer(width/2),'domain':'DOM_FIELD_B'})
   else:row['verdict']='NO_PATH_IN_BOUND'
   rows.append(row);return bool(path)
  # A minimum .25mm local supply/return width exceeds the normal31.236mA
  # load, plus1mA LDO ground reserve; .35mm input supports the .14A bus target.
  jobs=[('U11038.8','U11038.5',IN,.25),('U11038.8','C11092.1',IN,.35),('U11038.1','C11093.1',OUT,.25),('C11093.1','R11088.1',OUT,.25),('U11038.9','U11038.4',GND,.25),('U11038.9','C11092.2',GND,.35),('U11038.9','C11093.2',GND,.35),('U11038.9','R11088.2',GND,.25)]
  for a,b,n,w in jobs:route(a,b,n,w)
  candidates.append({'poses_mm':poses,'local_fanout':rows,'all_local_fanout_paths_found':all(x['verdict']=='HOST_PATH' for x in rows),'new_pad_positions':{k:{kk:v for kk,v in p.items() if kk!='shape'} for k,p in pads.items()},'current_basis':{'DO3V3_complete_output_envelope_a':model['computed_local_output_envelopes_a']['DOB_DO3V3_new_dedicated'],'LDO_ground_reserve_a':.001,'new_LDO_continuous_input_target_a':.041,'combined_B5PRE_continuous_routing_target_a':.140,'capacitor_feed_steady_a':0,'capacitor_startup_a':'TIME_DEPENDENT_UNQUALIFIED; not replaced with DC0','new_input_cap_f':2.2e-6,'new_output_cap_f':22e-6},'return_qualified':False,'PG_attachment_pending':True,'upstream_input_pending':True,'DO_load_attachment_pending':True})
  (HERE/'local-fanout-checkpoint.json').write_text(json.dumps(candidates,indent=1)+'\n',encoding='utf-8')
  print('cluster',u,'local paths',sum(x['verdict']=='HOST_PATH' for x in rows),'of',len(rows),flush=True)
  if candidates[-1]['all_local_fanout_paths_found']:break
 result={'candidate_sha256':g['sha256'],'source_export_receipt_sha256':sha(HERE/'ab-prereg-split-source/source-export/receipt-r2.json'),'candidates':candidates,'board_written':False,'native_jobs':0,'all_new_source_sinks_connected':False,'note':'Host local fanouts remain separate from B5PRE/PG/source-return and new DO load spine. Fill voids preserve native clearances and require fresh native continuity/DRC checks, not waivers.'}
 (HERE/'new-LDO-local-fanout-r1.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'clusters_tested':len(candidates),'complete_local_cluster':any(x['all_local_fanout_paths_found'] for x in candidates)}))
if __name__=='__main__':main()
