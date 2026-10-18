"""Bounded new field-LDO spine screen with explicit route/return limits."""
import json,pickle,time,math,hashlib
from collections import defaultdict
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import affinity
from contact_layout import HERE,BASE,load,build,norm,poly,S,identity
from inventory import sha
OUT=HERE/'new-LDO-spines-r1.json'
def main():
 if OUT.exists():raise ValueError('Refuse immutable spine screen')
 binding=json.loads((HERE/'owned-pad-cuts-r1/geometry-binding.json').read_text(encoding='utf-8'));raw=(HERE/'owned-pad-cuts-r1/prospective-geometry.pkl').read_bytes();assert hashlib.sha256(raw).hexdigest()==binding['model_sha256'];g=pickle.loads(raw)
 cuts=json.loads((HERE/'owned-pad-cuts-r1/receipt.json').read_text(encoding='utf-8'));assert cuts['graph_gate']=='PASS'
 static,trees=build(g,layers={'F.Cu','B.Cu'})
 local=json.loads((HERE/'new-LDO-local-fanout-r1.json').read_text(encoding='utf-8'));chosen=next(x for x in local['candidates'] if x['all_local_fanout_paths_found'])
 ledger=json.loads((HERE/'ab-prereg-split-source/receipt-r3.json').read_text(encoding='utf-8'));pads={};add=[]
 for ref,part in ledger['new_components'].items():
  f=next(f for f in g['footprints'] if f['ref']==part['clone']);d=(chosen['poses_mm'][ref][0]-f['x'],chosen['poses_mm'][ref][1]-f['y'])
  for p in [p for p in g['pads'] if p['ref']==part['clone'] and p['num']]:
   n=part['pins'][p['num']] or p['net'].replace(part['clone'],ref);n=norm(n);sh=affinity.translate(unary_union(poly(p['layers'].get('F.Cu',[]))),*d);at=(p['x']+d[0],p['y']+d[1]);pads[ref+'.'+p['num']]={'at':at,'net':n,'layer':'F.Cu','uuid':'NEW-'+ref+'.'+p['num'],'kind':'pad'};add.append({'shape':sh,'net':n,'domain':'DOM_FIELD_B','kind':'pad','layer':'F.Cu','uuid':'NEW-'+ref+'.'+p['num']})
 for p in g['pads']:
  if p['num']:
   for layer in ['F.Cu','B.Cu']:
    if layer in p['layers']:pads[p['ref']+'.'+p['num']+'@'+layer]={'at':(p['x'],p['y']),'net':norm(p['net']),'layer':layer,'uuid':p['uuid'],'kind':'pad'}
 for path in chosen['local_fanout']:add.append({'shape':LineString(path['path']['points_mm']).buffer(path['width_mm']/2),'net':path['net'],'domain':'DOM_FIELD_B','kind':'track','layer':'F.Cu','uuid':'LOCAL-'+path['from']})
 retained=json.loads((BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text(encoding='utf-8'))
 # Hard reservations are retained in this engineering screen. No old router
 # keepout is silently waived to make a new source appear routable.
 hard=defaultdict(list)
 for a in g['rule_areas']:
  if a.get('no_tracks'):
   for layer in a['layers']:hard[layer].extend(poly(a['outline']))
 for a in retained['keepouts']:
  for layer in a['layers']:hard[layer].extend(poly(a['outline']))
 outline=unary_union(poly(g['outline']))
 def free(net,layer,width,window):
  obs=[];voids=[]
  for i in trees[layer].query(window.buffer(2),predicate='intersects'):
   r=static[layer][i]
   if norm(r['net'])==net:continue
   if r['kind']=='fill':voids.append(identity(r));continue
   obs.append(r['shape'].buffer((.15 if r['domain']=='DOM_FIELD_B' else .6)+width/2+.025))
  for p in g['pads']:
   # NPTH/drill obstacles are independent of copper/pad layer presence.
   for h in poly(p.get('hole') or []):
    if h.intersects(window):obs.append(h.buffer(.25+width/2+.025))
  for r in add:
   if r['layer']==layer and r['net']!=net:obs.append(r['shape'].buffer(.15+width/2+.025))
  obs.extend(s.buffer(width/2+.025) for s in hard[layer] if s.intersects(window))
  return window.intersection(outline.buffer(-.5-width/2-.025)).difference(unary_union(obs)),voids
 rows=[]
 jobs=[('U11038.8','U11018.8@F.Cu','/motherboard_safety_sensor/FIELD_B_5V_PRE',.35,.041),('U11038.3','R22002.1@F.Cu','/motherboard_power_entry/FB_PGOOD',.2,.0003453),('U11038.9','U8005.14@F.Cu','/motherboard_do/FIELD_B_0V',.35,.041)]
 # The source/partial rail is separate from these attachment witnesses. Every
 # moved pad must eventually join the new source, including isolated groups.
 for x in ledger['pin_net_changes']:
  if x['to']=='DOB_DO_FIELD_3V3':
   key=x['ref']+'.'+x['pin'];dest=next((key+'@'+l for l in ['F.Cu','B.Cu'] if key+'@'+l in pads),None)
   jobs.append(('U11038.1',dest,'DOB_DO_FIELD_3V3',.25,.040))
 for a,b,n,w,iout in jobs:
  if b is None:raise ValueError('Missing moved load pad')
  aa,bb=pads[a],pads[b];row={'from':a,'to':b,'net':n,'width_mm':w,'routing_current_target_a':iout,'attempts':[],'return_qualified':False,'source_feed_qualified':False}
  if aa['layer']!=bb['layer']:row.update(verdict='REQUIRES_REVIEWED_LAYER_LANDINGS',reason='Opposite-face existing load; no new through-via assumed or attached by proximity.');rows.append(row);continue
  for margin in [8,24]:
   win=LineString([aa['at'],bb['at']]).envelope.buffer(margin,cap_style=3).envelope;fr,voids=free(n,aa['layer'],w,win)
   path,search=S.astar(fr.buffer(-.00001),[(aa['at'],aa)],[(bb['at'],bb)],time.monotonic()+8,node_cap=250000)
   row['attempts'].append({'margin_mm':margin,'search':search})
   if path and fr.covers(LineString(path['points_mm'])):
    row.update(verdict='HOST_PATH',path=path,layer=aa['layer'],mandatory_fill_voids=voids,normal_resistance_60C_mohm=.57003672*path['length_mm']/w,normal_drop_v=.00057003672*path['length_mm']/w*iout)
    add.append({'shape':LineString(path['points_mm']).buffer(w/2),'net':n,'domain':'DOM_FIELD_B','kind':'track','layer':aa['layer'],'uuid':'SPINE-'+a+'-'+b});break
  if 'verdict' not in row:row['verdict']='NO_PATH_IN_TWO_WINDOWS'
  rows.append(row);print(n,a,b,row['verdict'],flush=True)
  checkpoint={'candidate_sha256':g['sha256'],'rows':rows,'source_or_board_written':False,'native_jobs':0,'complete':False};(HERE/'spine-checkpoint.json').write_text(json.dumps(checkpoint,indent=1)+'\n',encoding='utf-8')
 result={'candidate_sha256':g['sha256'],'rows':rows,'local_cluster_all_eight_paths':True,'all_spines_found':all(x['verdict']=='HOST_PATH' for x in rows),'retained_reservations':True,'source_and_return_qualified':False,'source_export_native_pass':True,'partial_power_and_cap_startup_limits':'No normal DC path calculation bounds capacitor charging or PG fault timing. No new source supply/return graph qualification is inferred from nearest same-net attachments.','board_written':False,'native_jobs':0,'new_vias':0,'scope':'Bounded outer-layer spine screen; no global impossibility claim; native actual layer landings and return qualification required for missing paths.'}
 OUT.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print(json.dumps({'host_spines':sum(r['verdict']=='HOST_PATH' for r in rows),'required_spines':len(rows)}))
if __name__=='__main__':main()
