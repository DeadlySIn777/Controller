"""Bounded source-only alternate layer FAG ground dive and return.

One existing .6/.3 through-via at the west stub and at most one new .6/.3
through-via on the east. No board/native/GPU output; fullgroup gates are separate.
"""
import hashlib
import json
import math
import time
from pathlib import Path
import plan_repair as P
from shapely.geometry import Point,LineString
from shapely.ops import unary_union

def free_layer(model,width,window,layer,via_index,own_vias,allowed):
 obstacles=[]
 for i in model.trees[layer].query(window.buffer(2),predicate='intersects'):
  r=model.records[layer][i]
  if r['kind']=='hole':
   if r.get('uuid') in allowed:
    v=via_index.get(r['uuid']) or own_vias.get(r['uuid'])
    if not v or P.S.norm(v['net'])!=P.NET:raise ValueError('wrong-net hole attachment')
    continue
   gap=.25
  else:
   if r['net']==P.NET:continue
   gap=.15 if r.get('domain')==P.DOMAIN else .6
  obstacles.append(r['shape'].buffer(gap+width/2+P.MARGIN))
 for v in own_vias.values():
  if v['uuid'] not in allowed:
   obstacles.append(Point(v['x'],v['y']).buffer(v['drill']/2+.25+width/2+P.MARGIN))
 hard=list(model.hard.get(layer,[]))
 # Ground return paths do not get permission to bridge isolation courtyards
 # simply because they are on an alternate copper layer.
 if layer!='In3.Cu':hard += [r for r in model.hard['In3.Cu'] if r['kind']=='barrier_courtyard']
 for r in hard:
  if P.NET not in r['exempt']:obstacles.append(r['shape'].buffer(width/2+P.MARGIN))
 return window.intersection(model.outline.buffer(-.5-width/2-P.MARGIN)).difference(unary_union(obstacles))

def path_free(f,a,b,seconds=9,cap=30000):
 if f.covers(LineString([a,b])):return {'points_mm':[list(a),list(b)]},{'reason':'exact direct','nodes':0}
 r={'uuid':'exact-anchor','kind':'verified physical copper anchor'}
 return P.S.astar(f,[(tuple(a),r)],[(tuple(b),r)],time.monotonic()+seconds,node_cap=cap)

def main():
 out=P.HERE/'alternate-lower.json'
 if out.exists():raise ValueError('distinct immutable receipt required')
 for source in(Path(__file__),Path(P.__file__),P.HERE/'repair-plan.json',P.HERE/'lower-diagnosis.json',
               P.HERE/'layer-anchors.json',Path(P.I.__file__),Path(P.R.__file__),Path(P.S.__file__)):
  P.S.read(source)
 rows,old=P.I.own_additions();g,_,overlay=P.R.overlay_and_targets();r,e=P.exemptions()
 print('MODEL_START',flush=True);model=P.S.Model(g,r,e);print('MODEL_READY',flush=True)
 vias={v['uuid']:v for v in g['vias']}
 removed=set(P.REMOVED_VIAS)|{u for n in P.NETWORKS for u in n['remove']}
 kept={u:r for u,r in rows.items() if u not in removed}
 owned={u:{'uuid':u,'net':P.NET,'x':r['at'][0],'y':r['at'][1],'d':r['d'],'drill':r['drill']} for u,r in kept.items() if r['kind']=='via'}
 n=P.NETWORKS[1];east,west=n['anchors']
 window=unary_union([P.centre(rows[u]) for u in n['remove']]).envelope.buffer(8,cap_style=3).envelope
 target=vias['48bb17dc-e15c-4500-87b2-9784faa6bd96'];target_at=(target['x'],target['y'])
 if P.S.norm(target['net'])!=P.NET or (target['d'],target['drill'])!=(.6,.3):raise ValueError('target changed')
 retained_stub=kept['2b903a9f-df92-4263-bf2c-3a15ea640cab']
 if not P.shape(retained_stub).intersects(Point(target_at).buffer(target['d']/2)):raise ValueError('west existing stub contact absent')
 barriers={r['refdes'] for r in json.loads(P.S.read(Path('Z:/pcb-runs/domains/barriers.json')))['barriers']}
 in3=free_layer(model,.3,window,'In3.Cu',vias,owned,set())
 components=list(getattr(in3,'geoms',[in3]))
 reachable=unary_union([c for c in components if c.covers(Point(east))])
 if reachable.is_empty:raise ValueError('east physical attachment blocked')
 # Bound the one new landing to a3mm circle and0.25mm grid, closest first.
 points=sorted({(round(east[0]+i*.25,6),round(east[1]+j*.25,6)) for i in range(-12,13) for j in range(-12,13)
                if math.hypot(i*.25,j*.25)<=3.000001},key=lambda p:(math.dist(p,east),p))
 viable=[];counts={};rejected=[]
 for at in points:
  if not reachable.covers(Point(at)):continue
  row={'uuid':'PLAN:single-new-return-via','kind':'via','net':P.NET,'at':at,'d':.6,'drill':.3}
  audit=P.audit_row(row,model,vias,owned,barriers)
  failures=list(audit['failures'])
  # New ordinary vias cannot drill an existing same-net SMD land.
  for layer in g['copper_layers']:
   for i in model.trees[layer].query(P.shape(row).buffer(.1),predicate='intersects'):
    rec=model.records[layer][i]
    if rec['kind']=='pad' and rec['net']==P.NET and P.shape(row).distance(rec['shape'])<.1-1e-6:
     failures.append({'kind':'same_net_pad_web','uuid':rec['uuid'],'layer':layer})
  if failures:
   for failure in failures:counts[failure['kind']]=counts.get(failure['kind'],0)+1
   if len(rejected)<16:rejected.append({'at':at,'failures':failures})
  else:viable.append(row)
  if len(viable)>=24:break
 print('LANDINGS',len(viable),'rejected',counts,flush=True)
 attempts=[];selected=None
 # Each option is exactly In3->one alternate layer->In3 through the retained
 # west via; neither speculative plane contact nor repeated switches substitute.
 for layer in('F.Cu','B.Cu','In1.Cu','In4.Cu','In2.Cu'):
  f=free_layer(model,.3,window,layer,vias,owned,{target['uuid']})
  option={'layer':layer,'west_exact_attachment_free':f.covers(Point(target_at)),
          'attempts':[],'foreign_fill_policy':'all pinned older foreign fills preserved; no prospective antipad allowance'}
  if option['west_exact_attachment_free']:
   for via in viable[:8]:
    at=via['at']
    if not f.covers(Point(at)):continue
    middle,search=path_free(f,at,target_at)
    attempt={'new_via_at':at,'middle_search':search,'middle_path':middle}
    if middle:
     approach,approach_search=path_free(in3,east,at)
     attempt.update(in3_approach=approach,in3_search=approach_search)
     if approach:
      selected={'layer':layer,'new_via':via,'existing_return_via':target,
                'segments':[{'layer':'In3.Cu','width_mm':.3,**approach},{'layer':layer,'width_mm':.3,**middle}],
                'layer_segments':3,'new_vias':1,'physical_west_contact':{
                  'retained_owned_stub_uuid':retained_stub['uuid'],'retained_existing_via_uuid':target['uuid'],
                  'copper_overlap_mm2':P.shape(retained_stub).intersection(Point(target_at).buffer(.3)).area},
                'plane_rooted_equivalence_proved':False,'current_scope_A':.096}
    option['attempts'].append(attempt)
    if selected:break
  attempts.append(option);print('LAYER',layer,'free',option['west_exact_attachment_free'],'attempts',len(option['attempts']),'found',selected is not None,flush=True)
  if selected:break
 for path,sha in P.S.READS.items():
  if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=sha:raise ValueError('input changed:'+path)
 result={'schema':'fag-r07-bounded-alternate-layer-v1','scope':'partial0.096A FIELD_A return only',
         'verdict':'ALTERNATE_PATH_FOUND_WHOLE_GROUP_REAUDIT_REQUIRED' if selected else 'NO_BOUNDED_SINGLE_DIVE_RETURN_PATH',
         'r07_sha256':P.R.R07_SHA,'donor_sha256':old['donor_sha256'],'overlay':overlay,'network':n,
         'window':list(window.bounds),'existing_west_via':target,'landing_grid_mm':.25,'landing_radius_mm':3,
         'viable_landing_count':len(viable),'max_landings_checked_per_layer':8,'landing_rejection_counts':counts,
         'first_rejected_landings':rejected,'attempts':attempts,'selected':selected,
         'board_emitted':False,'native_jobs':0,'gpu_jobs':0,'source_files_sha256':P.S.READS,
         'limits':['No fullgroup success claimed until exact retained250 and all replacement paths are reaudited',
                   'No native no-loss/DRC/refill/plane-root/current-sharing/thermal/fault proof',
                   'All foreign fills/hole/0.6mmcross-domain/barrier/reserved constraints preserved',
                   'Ordinary0.6/0.3mm newvia must meet0.8mm spacing; no D4/BGA/domain waivers',
                   'At most1 new throughvia and1 retained throughvia transition; exactlyone dive-and-return',
                   'No bounded path implies only this owned-window/search scope, not global impossibility']}
 out.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'verdict':result['verdict'],'selected':selected,'counts':counts},indent=1),flush=True)

if __name__=='__main__':main()
