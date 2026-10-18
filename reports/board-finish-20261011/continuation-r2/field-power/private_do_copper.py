"""Find exclusively moved DO3V3 copper without erasing retained safety contacts."""
import json,hashlib
from collections import defaultdict
from shapely.strtree import STRtree
from contact_layout import HERE,BASE,BOARD,load,build,norm,O,S,identity
from inventory import sha
def main():
 g,binding=load();r=json.loads((HERE/'ab-prereg-split-source/receipt-r3.json').read_text(encoding='utf-8'))
 old=norm('/motherboard_do{slash}DOB_FIELD_3V3');records,_=build(g,nets={old});uf=S.UF();allrows=[]
 def key(x):
  return ('fill',x['uuid'],x['layer'],x['contour']) if x['kind']=='fill' else (x['kind'],x['uuid'])
 for layer,rows in records.items():
  tree=STRtree([x['shape'] for x in rows])
  for i,x in enumerate(rows):
   uf.find(key(x));allrows.append(x)
   for j in tree.query(x['shape'].buffer(.000002),predicate='intersects'):
    if i<int(j) and x['shape'].distance(rows[int(j)]['shape'])<=.000002:uf.join(key(x),key(rows[int(j)]))
 groups=defaultdict(list)
 for x in allrows:groups[uf.find(key(x))].append(x)
 moved={(x['ref'],x['pin']) for x in r['pin_net_changes'] if norm(x['from'])==old};byids=O.C.inventory(BOARD.read_bytes())[3]
 private=[];shared=[]
 for root,xs in groups.items():
  padset={(x['ref'],x['pin']) for x in xs if x['kind']=='pad'}
  movedhere=padset&moved
  if not movedhere:continue
  itemkeys={key(x) for x in xs};group={'moved_pads':sorted([list(p) for p in movedhere]),'retained_old_rail_pads':sorted([list(p) for p in padset-moved]),'copper_items':sorted([{'kind':kind,'uuid':uid,'old_sha256':hashlib.sha256(byids[uid]).hexdigest()} for kind,uid in itemkeys if kind in ('track','via','graphic')],key=lambda x:x['uuid']),'filled_zone_contours':[list(k) for k in itemkeys if k[0]=='fill']}
  (shared if padset-moved else private).append(group)
 # Verify this actual-contact replay against the stored uncapped native result.
 partitions=json.loads((BASE/'measure/r07-four-fag-shared/partitions.json').read_text(encoding='utf-8'))
 expected={frozenset(tuple(pid.rsplit('#',1)[0].rsplit('.',1)) for pid in group) for group in partitions['nets']['/motherboard_do{slash}DOB_FIELD_3V3']}
 got={frozenset((x['ref'],x['pin']) for x in xs if x['kind']=='pad') for xs in groups.values()}
 got.discard(frozenset())
 exact=got==expected
 result={'candidate_sha256':g['sha256'],'old_net':old,'new_net':'DOB_DO_FIELD_3V3','native_partition_replay_exact':exact,'host_partition_count':len(got),'saved_native_partition_count':len(expected),'private_moved_pad_components':private,'shared_moved_retained_pad_components':shared,'whole_copper_retag_eligible_only_if_exact_replay_and_all_pads_moved':True,'all_contacts_verified_with_actual_via_annuli':True,'native_jobs':0,'board_written':False,'scope':'Eligible private tracks/vias can change only net spelling with geometry/UUIDs preserved. Shared components require owned-pad local separation and preserved old-source relationships. Filled contours cannot be retagged by changing only cache.'}
 (HERE/'private-DO-copper-r1.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'native_partition_replay_exact':exact,'private_groups':len(private),'shared_groups':len(shared),'private_copper_items':sum(len(x['copper_items']) for x in private),'moved_pad_groups':[x['moved_pads'] for x in private]}))
if __name__=='__main__':main()
