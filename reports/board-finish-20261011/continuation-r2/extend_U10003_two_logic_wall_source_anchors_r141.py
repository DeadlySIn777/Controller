"""Find literal existing chain anchors supported by the actual J11001 plane."""
import hashlib,json,pickle,sys,collections
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
OUT=H/'U10003-two-logic-wall-exact-extended-anchors-r141'
IDS=('eeb33c09-9494-4734-b174-e3c3ceffd73b','8f7ea41c-9cfd-4c25-a376-00657f6105ed')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def nm(p):return tuple(int(round(x*1000000))for x in p)
def main():
 assert not OUT.exists();OUT.mkdir();mp=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl';assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e';g,h,b,z,full=pickle.loads(mp.read_bytes());groups=pickle.loads(mp.with_name('groups.pkl').read_bytes());root=next(xs for xs in groups['/LOGIC_GND']if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11001','2')for q in xs));rows=[]
 for uid in IDS:
  target=next(t for t in h['tracks']if t['uuid']==uid);layer=target['layer'];ref_layer='In1.Cu'if layer=='F.Cu'else'In4.Cu';ref=unary_union([q['shape']for q in root if q['layer']==ref_layer and q['kind']=='fill']);safe=ref.buffer(-.100020,quad_segs=128);tracks=[t for t in h['tracks']if t['net']==target['net']and t['layer']==layer];incident=collections.defaultdict(list)
  for t in tracks:
   for p in(t['a'],t['b']):incident[nm(p)].append(t)
  visited={uid};chain=[target];anchors=[];walks=[]
  for original in(target['a'],target['b']):
   p=original;walk=[];reason=None
   for step in range(80):
    if safe.covers(Point(p)):reason='FULL_POINT_WITH_.100020_SOURCE_PLANE_MARGIN';break
    options=[t for t in incident[nm(p)]if t['uuid']not in visited]
    if len(options)!=1:reason='CHAIN_END_OR_BRANCH_REQUIRES_INDEPENDENT_MULTI_TERMINAL_REPAIR';break
    t=options[0];visited.add(t['uuid']);chain.append(t);walk.append(t);p=t['b']if nm(t['a'])==nm(p)else t['a']
   anchors.append(p);walks.append({'original_mm':original,'anchor_mm':p,'source_supported':safe.covers(Point(p)),'reason':reason,'walked_UUIDs':[t['uuid']for t in walk],'branch_candidates_at_anchor':[t['uuid']for t in incident[nm(p)]if t['uuid']not in visited]})
  row={'wall_UUID':uid,'net_raw':target['net'],'layer':layer,'actual_reference_layer':ref_layer,'anchors_mm':anchors,'exact_old_chain_delete_nominees':chain,'walks':walks,'all_anchors_source_supported':all(q['source_supported']for q in walks)};rows.append(row);print(json.dumps({k:row[k]for k in('wall_UUID','anchors_mm','walks','all_anchors_source_supported')}),flush=True)
 receipt={'verdict':'LITERAL_CHAIN_ANCHOR_NOMINATION_ONLY_ALL_RESTORE_GATES_OPEN','parent_model_sha256':sha(mp),'rows':rows,'native_jobs':0,'board_written':False,'adopted':False};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print('R141',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
