"""Pin-identical local wall inventory; unsuccessful proposals preserved."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point
H=Path(__file__).resolve().parent.parent
for d in('sbc-power','field-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
from verify_source import parse,child,children,atom
O=H/'sbc-power/U21003-actual-ordinary-escape-wall-r236'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not O.exists();O.mkdir();base=H/'sbc-power/C1022-zero-gap-source-feed-independent-r221/model.pkl';assert sha(base)=='261f92035b05f1346bc805d43df3f7b67a2c0c638892ee43c01856d57196182a';g,h,b,z,c=pickle.loads(base.read_bytes());nf=H/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net';assert sha(nf)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2';src=parse(nf.read_text());parts={atom(p,'ref'):p for p in children(child(src,'components'),'comp')};pins={}
 for net in children(child(src,'nets'),'net'):
  for p in children(net,'node'):pins.setdefault(atom(p,'ref'),[]).append({k:atom(p,k)for k in('ref','pin','pinfunction','pintype')}|{'raw_net':atom(net,'name')})
 wanted={'9cc9980a-f70a-486f-80e4-168f038bda3d','22669547-c2e6-4c89-b252-3add6e97decd','bd0f762c-7714-4e5c-b5fa-e07444b8c872','74320def-e840-42aa-bb72-d41e4a50265b'};pads=[];tracks=[]
 for p in h['pads']:
  if p['uuid']not in wanted and Point(p['x'],p['y']).distance(Point(332,145))>3:continue
  row={k:p.get(k)for k in('uuid','ref','num','net','x','y','smd','hole')};row['layer_shapes']={l:[{'bounds':q.bounds,'area':q.area,'WKB_sha256':hashlib.sha256(q.wkb).hexdigest()}for q in C.poly(rs)]for l,rs in p['layers'].items()};row['source_value']=atom(parts[p['ref']],'value')if p['ref']in parts elseNone;row['actual_fresh_source_pin_functions']=pins.get(p['ref'],[]);row['actual_host_FP']=next((fp for fp in h['footprints']if fp['ref']==p['ref']),None);pads.append(row)
 for t in h['tracks']:
  if t['uuid']in wanted:tracks.append(t)
 record={'verdict':'EXACT_LOCAL_ORDINARY_ESCAPE_WALL_INVENTORY_NO_NEW_PROPOSAL','base_sha256':sha(base),'source_sha256':sha(nf),'selected_wall_UUIDs':sorted(wanted),'actual_pads_and_part_functions':pads,'actual_tracks':tracks,'no_geometry_source_rule_changes':True,'native_jobs':0,'board_written':False,'script_sha256':sha(__file__)};(O/'receipt.json').write_text(json.dumps(record,indent=1)+'\n');print('R236_COMPLETE',sha(O/'receipt.json'),[(p['ref'],p['num'],p['net'],p['x'],p['y'],p['layer_shapes'])for p in pads if p['uuid']in wanted],flush=True)
if __name__=='__main__':main()
