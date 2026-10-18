"""Source-rooted fresh copper graph, not a source-label connectivity assumption."""
import json,pickle,hashlib
from collections import defaultdict
from contact_layout import HERE,BASE,load,build,norm,O,S,identity
from shapely.strtree import STRtree
from shapely.ops import unary_union,nearest_points
from shapely.geometry import mapping
from inventory import sha
N={'FBG':'/motherboard_do/FIELD_B_0V','FAG':'/motherboard_motors/FIELD_GND','FA':'/motherboard_power_entry/FIELD_A_24V_PROTECTED','FB':'/motherboard_power_entry/FIELD_B_24V_PROTECTED','B5':'/motherboard_safety_sensor/FIELD_B_5V_PRE','A5':'/motherboard_power_entry/FIELD_5V'}
ROOTS={'FBG':('J11005','2'),'FAG':('J11003','2'),'FA':('U11004','17'),'FB':('U11006','17'),'B5':('L19001','2'),'A5':('L11003','2')}
def key(x):return ('fill',x['uuid'],x['layer'],x['contour']) if x['kind']=='fill' else (x['kind'],x['uuid'])
def graph(g,net):
 records,_=build(g,nets={net});uf=S.UF();allrows=[]
 for layer,rs in records.items():
  tree=STRtree([x['shape'] for x in rs])
  for i,x in enumerate(rs):
   uf.find(key(x));allrows.append(x)
   for j in tree.query(x['shape'].buffer(.000002),predicate='intersects'):
    if i<int(j) and x['shape'].distance(rs[int(j)]['shape'])<=.000002:uf.join(key(x),key(rs[int(j)]))
 groups=defaultdict(list)
 for x in allrows:groups[uf.find(key(x))].append(x)
 return list(groups.values())
def main():
 g,b=load();out={'board_sha256':g['sha256'],'native_actual_via_annuli':True,'in_memory_native_fresh_fill':True,'nets':{}};cache={}
 for k,n in N.items():
  groups=graph(g,n);cache[k]=groups;root=ROOTS[k];rootids=[i for i,xs in enumerate(groups) if any(x['kind']=='pad' and (x['ref'],x['pin'])==root for x in xs)];assert len(rootids)==1,(k,root,rootids);ri=rootids[0]
  rows=[]
  for i,xs in enumerate(groups):
   pads=sorted({(x['ref'],x['pin']) for x in xs if x['kind']=='pad'});fill=[identity(x) for x in xs if x['kind']=='fill'];areas={l:unary_union([x['shape'] for x in xs if x['layer']==l]).area for l in ['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']};rows.append({'group':i,'rooted':i==ri,'pads':[list(p) for p in pads],'copper_item_count':len({key(x) for x in xs}),'fill_contours':fill,'area_mm2_by_layer':areas})
  out['nets'][k]={'canonical_net':n,'source_root':list(root),'source_root_group':ri,'groups':rows,'pad_groups':sum(bool(r['pads']) for r in rows),'floating_copper_only_groups':sum(not bool(r['pads']) for r in rows),'rooted_pad_count':len(rows[ri]['pads'])}
  print(k,'pad_groups',out['nets'][k]['pad_groups'],'rooted_pads',len(rows[ri]['pads']),'rootarea',rows[ri]['area_mm2_by_layer'],flush=True)
 (HERE/'power-groups-r1.json').write_text(json.dumps(out,indent=1)+'\n',encoding='utf-8');raw=pickle.dumps(cache,protocol=5);(HERE/'power-groups-r1.pkl').write_bytes(raw);(HERE/'power-groups-r1-binding.json').write_text(json.dumps({'board_sha256':g['sha256'],'cache_sha256':hashlib.sha256(raw).hexdigest(),'receipt_sha256':sha(HERE/'power-groups-r1.json'),'geometry_binding':b},indent=1)+'\n',encoding='utf-8')
if __name__=='__main__':main()
