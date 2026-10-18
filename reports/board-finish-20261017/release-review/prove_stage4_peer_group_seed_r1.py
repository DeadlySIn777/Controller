"""Independent finite-Cu witnesses for current-peer connectivity DSU seeds.

This is a control for the routing agent's K.physical requalification, not a
replacement connectivity model and not proof of unfinished native AFTER gates.
"""
import os,sys
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='2'
from pathlib import Path
from collections import defaultdict,deque
import hashlib,json,math,pickle,time
import psutil
p=psutil.Process();p.cpu_affinity([16,17]);p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import shapely
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely import STRtree
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'reports/board-finish-20261017'
OLD=ROOT/'reports/board-finish-20261011/continuation-r2'
for d in (OLD/'field-power',OLD/'sbc-power',OLD/'coupled-recovery'):sys.path.insert(0,str(d))
import R157_native_selected_actual_conversion_r673 as N
norm=N.L.norm
CURRENT=BASE/'combined-route-stage-r4';CACHE=BASE/'actual-full-audit-repaired-r1/r763'
OUT=BASE/'release-review/stage4-current-peer-group-seed-r1';OUT.mkdir(exist_ok=False);(OUT/'witnesses').mkdir()
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
inputs=[CURRENT/'native/board.kicad_pcb',CURRENT/'all-copper-expected.json',CURRENT/'construction-receipt.json',
 OLD/'combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json',
 CACHE/'actual-combined-full-after-model.pkl',CACHE/'actual-combined-full-after-all-net-groups.pkl',CACHE/'actual-graph-cache-receipt.json',
 BASE/'routing/parent-audit-review/actual-project-epsilon-NPTH-cloned-deflation-r2/all-actual-native-NPTH-conductor-and-layer-observations.json',Path(__file__)]
binding={str(f):sha(f) for f in inputs}
assert binding[str(inputs[0])]=='ce8aa2cd5bb9c2128733618d5241a10acebdd637e4a0b5f726fea40801444c55'
assert binding[str(inputs[4])]=='c71985a7bce58538be801c092a3dc92f8ae4f2766a6e43fc1d8a42b910a91806'
assert binding[str(inputs[5])]=='c89a4df063cf1a817763a7298f7f511f88fbddbc55471e2b2b8786544aec24cd'
current_doc=json.loads(inputs[1].read_text());current=current_doc['copper'];old=json.loads(inputs[3].read_text())['copper']
assert current_doc['board_sha256']==binding[str(inputs[0])]
physical=lambda r:{k:v for k,v in r.items() if k not in {'chunk_sha256','locked_yes'}}
changed={uid:r for uid,r in current.items() if uid not in old or physical(r)!=physical(old[uid])}
removed=set(old)-set(current)
print('LOAD_BOUND_ACTUAL_GROUPS',len(changed),'current additions/physical changes',flush=True)
h=pickle.loads(inputs[4].read_bytes());groups=pickle.loads(inputs[5].read_bytes())
nocu={r['UUID']for r in json.loads(inputs[7].read_text())if r['IsNPTHWithNoCopper'] and not any(l['CanFlashLayer'] or l['FlashLayer']for l in r['layer_observations'])}
EPS=.00001;MINAREA=.000001
def hole_circle(at,r):return Point(at).buffer((r+EPS)/math.cos(math.pi/512),quad_segs=128)
holes=[]
for uid,r in current.items():
 if r['kind']=='via':holes.append((uid,hole_circle([x/1e6 for x in r['at_IU']],r['drill_IU']/2e6)))
for pad in h['pads']:
 for sh in N.L.poly(pad.get('hole')or[]):holes.append((pad['uuid'],sh.buffer(.005+EPS)))
ht=STRtree([s for _,s in holes])
def true_cu(shape):
 if shape.is_empty:return shape
 cuts=[holes[int(i)][1] for i in ht.query(shape)]
 return shape.difference(unary_union(cuts)) if cuts else shape
peer_layers={};peer_by_net=defaultdict(list)
for uid,r in changed.items():
 net=norm(r['raw_net']);rows={}
 if r['kind']=='segment':
  a=[x/1e6 for x in r['start_IU']];b=[x/1e6 for x in r['end_IU']]
  rows[r['layer']]=true_cu(LineString([a,b]).buffer(r['width_IU']/2e6-EPS,quad_segs=128))
 elif r['kind']=='via':
  # A new ordinary via is one barrel node across its explicitly required mask.
  # Native AFTER must confirm that mask before this conditional seed is used
  # to claim final board connectivity or relationship preservation.
  layers=list(r['diameters_IU']);assert set(layers)==set(N.K.LAYERS)
  if uid not in old:assert uid in current_doc['required_NEW_ordinary_all6']
  for layer,d in r['diameters_IU'].items():
   rows[layer]=true_cu(Point([x/1e6 for x in r['at_IU']]).buffer(d/2e6-EPS,quad_segs=128))
 else:raise AssertionError(r['kind'])
 assert all(not sh.is_empty for sh in rows.values()),uid
 peer_layers[uid]=rows;peer_by_net[net].append(uid)
parent={};adj=defaultdict(list);links=[]
def find(n):
 parent.setdefault(n,n)
 while parent[n]!=n:parent[n]=parent[parent[n]];n=parent[n]
 return n
def link(a,b,row):
 index=len(links);row.update(link_id=index,a=a,b=b);links.append(row)
 adj[a].append((b,index));adj[b].append((a,index));parent[find(a)]=find(b)
def save_witness(shape):
 data=shape.wkb;digest=hashlib.sha256(data).hexdigest();f=OUT/'witnesses'/(digest+'.wkb')
 if not f.exists():f.write_bytes(data)
 return {'finite_area_mm2':shape.area,'bounds_mm':list(shape.bounds),'WKB_file':str(f),'WKB_SHA256':digest}
required={}
for net,uids in peer_by_net.items():
 gg=groups.get(net,[]);by_layer=defaultdict(list)
 for gi,gr in enumerate(gg):
  required[net,gi]=any(r['kind']=='pad' and r.get('pin') for r in gr)
  for r in gr:
   if r['uuid'] not in removed and r['uuid'] not in nocu:
    by_layer[r['layer']].append((gi,r))
 trees={ly:STRtree([r['shape'] for _,r in rr])for ly,rr in by_layer.items()}
 for uid in uids:
  node='peer:'+uid;find(node);best={}
  for ly,shape in peer_layers[uid].items():
   if ly not in trees:continue
   for j in trees[ly].query(shape,predicate='intersects'):
    gi,r=by_layer[ly][int(j)]
    # Erode old finite Cu too. Positive witnesses cannot rely on tangency,
    # padded obstacle envelopes, or nominal barrel discs through a drill.
    w=true_cu(shape.intersection(r['shape'].buffer(-EPS)))
    if w.area<=MINAREA:continue
    key=gi
    if key not in best or w.area>best[key][0].area:best[key]=(w,r,ly)
  for gi,(w,r,ly) in best.items():
   link(node,'old:'+net+':'+str(gi),{'kind':'finite_current_peer_to_retained_actual_group',
    'net':net,'old_group':gi,'old_group_has_named_pad':required[net,gi],
    'peer_UUID':uid,'old_contact_UUID':r['uuid'],'old_contact_kind':r['kind'],
    'old_contact_ref':r.get('ref'),'old_contact_pin':r.get('pin'),'layer':ly,**save_witness(w)})
 for i,uid in enumerate(uids):
  for other in uids[i+1:]:
   best=None
   for ly in set(peer_layers[uid])&set(peer_layers[other]):
    w=peer_layers[uid][ly].intersection(peer_layers[other][ly])
    if w.area>MINAREA and (best is None or w.area>best[0].area):best=w,ly
   if best:
    w,ly=best;link('peer:'+uid,'peer:'+other,{'kind':'finite_current_peer_to_peer',
      'net':net,'peer_UUIDs':[uid,other],'layer':ly,**save_witness(w)})
 print('FINITE_PEER_CONTACTS',net,len(uids),'peer objects',flush=True)

def path(a,b):
 queue=deque([a]);prev={a:None}
 while queue:
  n=queue.popleft()
  if n==b:break
  for other,index in adj[n]:
   if other not in prev:prev[other]=(n,index);queue.append(other)
 assert b in prev
 result=[];n=b
 while prev[n] is not None:n,index=prev[n];result.append(index)
 return list(reversed(result))
components=defaultdict(list)
for net,gg in groups.items():
 if net not in peer_by_net:continue
 for gi in range(len(gg)):
  node='old:'+net+':'+str(gi)
  if node in parent:components[net,find(node)].append(gi)
edges=[]
for (net,component),gs in components.items():
 gs=sorted(gs)
 for other in gs[1:]:
  edges.append({'net':net,'old_group_edge':[gs[0],other],
   'both_groups_have_named_pads':required[net,gs[0]] and required[net,other],
   'witness_link_ids':path('old:'+net+':'+str(gs[0]),'old:'+net+':'+str(other))})
output={'status':'INDEPENDENT_FINITE_CURRENT_PEER_GROUP_DSU_SEED_CONDITIONAL_OLD_RELATIONSHIPS',
 'current_head_SHA256':binding[str(inputs[0])],'current_expected_Cu_SHA256':binding[str(inputs[1])],
 'actual_R299_model_SHA256':binding[str(inputs[4])],'actual_R299_groups_SHA256':binding[str(inputs[5])],
 'changed_or_added_current_Cu_UUIDs':sorted(changed),'removed_baseline_Cu_UUIDs':sorted(removed),
 'peer_layers':{u:sorted(rr)for u,rr in peer_layers.items()},
 'seed_edges':edges,'finite_contact_links':links,
 'conservative_contact_geometry':{'inward_Cu_mm':EPS,'outward_hole_extra_mm':EPS,'pad_hole_extra_mm':.005+EPS,'minimum_positive_area_mm2':MINAREA,
  'all_current_via_holes_and_source_pad_holes_removed':True,'native_NPTH_noCu_excluded':len(nocu)},
 'explicit_retired_old_relationship_preservation_condition':{
  'condition':'Every retained actual R299 old group must remain physically connected after authorized old Cu/hole retirements and source edits. These group-DSU merges are conditional on that separately proved invariant; do not treat this seed as proof of old relationships or native AFTER connectivity.',
  'authorized_removed_vias':current_doc['authorized_removed_actual_full_R157_via_UUIDs'],
  'exact_physical_retirement_survivors':current_doc['exact_physical_retirement_survivors'],
  'new_ordinary_masks_to_be_confirmed_by_native_AFTER':current_doc['required_NEW_ordinary_all6'],
  'native_full_after_old_relationship_reference_mask_gate':'OPEN_REQUIRED',
  'usage':'Use to suppress redundant candidate old-group joins at generation time. Routing-agent K.physical current-peer rebuild is the primary generation model; compare these independent finite witnesses before claiming join credit.'},
 'input_SHA256':binding,'inputs_unchanged':all(sha(f)==v for f,v in binding.items()),
 'native_jobs':0,'source_or_PCB_changes':False,'physical_authority':False,'manufacturing_ready':False}
assert output['inputs_unchanged']
(OUT/'seed.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({'status':output['status'],'peer_objects':len(changed),'finite_links':len(links),
 'seed_edges':len(edges),'named_pad_join_seed_edges':sum(e['both_groups_have_named_pads']for e in edges),'seed_SHA256':sha(OUT/'seed.json')}),flush=True)
