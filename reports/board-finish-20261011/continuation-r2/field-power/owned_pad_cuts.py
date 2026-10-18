"""Owned-pad copper separation proposal with unchanged-pad continuity replay."""
import copy,hashlib,json,pickle,re,sys,uuid
from collections import defaultdict
from shapely.geometry import LineString
from shapely.ops import unary_union
from contact_layout import HERE,BASE,BOARD,load,build,norm,poly,body,O,S,contacts,identity
from inventory import sha
OUT=HERE/'owned-pad-cuts-r1'
def partitions(g,net):
 records,_=build(g,nets={net});uf=S.UF();allrows=[]
 def key(x):return ('fill',x['uuid'],x['layer'],x['contour']) if x['kind']=='fill' else (x['kind'],x['uuid'])
 for layer,rows in records.items():
  tree=O.STRtree([x['shape'] for x in rows])
  for i,x in enumerate(rows):
   uf.find(key(x));allrows.append(x)
   for j in tree.query(x['shape'].buffer(.000002),predicate='intersects'):
    if i<int(j) and x['shape'].distance(rows[int(j)]['shape'])<=.000002:uf.join(key(x),key(rows[int(j)]))
 groups=defaultdict(set)
 for x in allrows:
  if x['kind']=='pad':groups[uf.find(key(x))].add((x['ref'],x['pin']))
 return {frozenset(ps) for ps in groups.values() if ps}
def main():
 if OUT.exists():raise ValueError('Refuse immutable cut proposal')
 OUT.mkdir();g,binding=load();h=copy.deepcopy(g)
 ledger=json.loads((HERE/'ab-prereg-split-source/receipt-r3.json').read_text(encoding='utf-8'))
 private=json.loads((HERE/'private-DO-copper-r1.json').read_text(encoding='utf-8'));assert private['native_partition_replay_exact']
 nodes={(x['ref'],x['pin']):x for x in ledger['pin_net_changes']};retags={r['uuid'] for c in private['private_moved_pad_components'] for r in c['copper_items']}
 records,trees=build(g,nets={norm(x['from']) for x in nodes.values()});byids=O.C.inventory(BOARD.read_bytes())[3]
 voids=defaultdict(list)
 for p in h['pads']:
  x=nodes.get((p['ref'],p['num']))
  if x is None:continue
  for layer,ps in p['layers'].items():voids[(norm(x['from']),layer)].append(unary_union(poly(ps)))
  p['net']=x['to']
 newtracks=[];cuts=[];retagrows=[]
 for t in h['tracks']:
  oldnet=norm(t['net']);old=byids[t['uuid']]
  if t['uuid'] in retags:
   t['net']='DOB_DO_FIELD_3V3';retagrows.append({'uuid':t['uuid'],'kind':'track','old_sha256':hashlib.sha256(old).hexdigest(),'geometry_and_UUID_unchanged':True});newtracks.append(t);continue
  shapes=voids.get((oldnet,t['layer']))
  if not shapes:newtracks.append(t);continue
  clearance=unary_union([s.buffer(.15+t['w']/2+.025+.005) for s in shapes])
  line=LineString([t['a'],t['b']])
  if not line.intersects(clearance):newtracks.append(t);continue
  if t.get('kind')=='arc':raise ValueError('Arc contact requires exact independent arc clipping')
  kept=line.difference(clearance);lines=[kept] if kept.geom_type=='LineString' and not kept.is_empty else [p for p in getattr(kept,'geoms',[]) if p.geom_type=='LineString' and p.length>.000001]
  replacements=[]
  for i,ln in enumerate(lines):
   nt=copy.deepcopy(t);nt['a']=[round(v,6) for v in ln.coords[0]];nt['b']=[round(v,6) for v in ln.coords[-1]]
   if i:nt['uuid']=str(uuid.uuid5(uuid.NAMESPACE_URL,'Controller-owned-field-pad-cut-r1/'+t['uuid']+'/'+str(i)))
   newtracks.append(nt);text=old.decode('utf-8')
   for key,xy in [('start',nt['a']),('end',nt['b'])]:text,n=re.subn(r'\('+key+r' [-\d.eE+]+ [-\d.eE+]+\)','('+key+' '+' '.join(format(v,'.10g') for v in xy)+')',text);assert n==1
   text=text.replace(t['uuid'],nt['uuid']);path=OUT/(nt['uuid']+'.segment-chunk');path.write_bytes(text.encode('utf-8'))
   replacements.append({'uuid':nt['uuid'],'start_mm':nt['a'],'end_mm':nt['b'],'sha256':sha(path),'path':str(path.resolve())})
  hits=contacts(records,trees,body(t),t['layer'],omit=t['uuid'])
  cuts.append({'uuid':t['uuid'],'old_chunk_sha256':hashlib.sha256(old).hexdigest(),'net':t['net'],'layer':t['layer'],'old_start_mm':t['a'],'old_end_mm':t['b'],'width_mm':t['w'],'exact_old_contacts':hits,'replacement_segments':replacements,'whole_owned_segment_removed':not replacements,'cut_basis':'New pad boundary +0.15mm same-domain clearance +half original track width +0.025mm planner margin +0.005mm inscribed-pad polygon error. Preserves all outside centerline geometry.'})
 h['tracks']=newtracks
 for v in h['vias']:
  if v['uuid'] in retags:v['net']='DOB_DO_FIELD_3V3';retagrows.append({'uuid':v['uuid'],'kind':'via','old_sha256':hashlib.sha256(byids[v['uuid']]).hexdigest(),'geometry_and_UUID_unchanged':True})
 replay={};changed=set(nodes)
 for net in sorted({norm(x['from']) for x in nodes.values()}):
  old=partitions(g,net);after=partitions(h,net)
  expected={frozenset(p for p in group if p not in changed) for group in old};expected.discard(frozenset())
  actual={frozenset(p for p in group if p not in changed) for group in after};actual.discard(frozenset())
  replay[net]={'verdict':'PASS' if expected==actual else 'FAIL','projected_old_groups':len(expected),'projected_after_groups':len(actual),'lost_projected_group_memberships':[sorted([list(p) for p in group]) for group in expected-actual],'unexpected_projected_group_memberships':[sorted([list(p) for p in group]) for group in actual-expected]}
 # Zone definitions and fills are not deleted or rewritten in this host delta.
 # Every affected input/EN/VDD pad is SMD; refill clearance is a separate gate.
 result={'candidate_sha256':g['sha256'],'source_ledger_sha256':sha(HERE/'ab-prereg-split-source/receipt-r3.json'),'cuts':cuts,'private_net_only_retags':retagrows,'unaffected_named_pad_graph_replay':replay,'graph_gate':'PASS' if all(x['verdict']=='PASS' for x in replay.values()) else 'FAIL_WITHHOLD_INTEGRATION','original_copper_geometry_preserved_outside_owned_pad_voids':True,'ordinary_margin_mm':.025,'same_domain_clearance_mm':.15,'native_polygon_error_mm':.005,'board_written':False,'native_jobs':0,'all_source_sinks_connected':False}
 (OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
 data=pickle.dumps(h,protocol=5);(OUT/'prospective-geometry.pkl').write_bytes(data)
 (OUT/'geometry-binding.json').write_text(json.dumps({'model_sha256':hashlib.sha256(data).hexdigest(),'old_geometry_binding':binding,'receipt_sha256':sha(OUT/'receipt.json'),'candidate_sha256':g['sha256'],'new_source_geometry_only':True,'zone_refill_pending':True},indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'cuts':len(cuts),'whole_owned_segments_removed':sum(x['whole_owned_segment_removed'] for x in cuts),'private_retags':len(retagrows),'graph_gate':result['graph_gate'],'replay':replay}))
if __name__=='__main__':main()
