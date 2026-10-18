"""Pin every native zone-overlap report to exact unchanged input-zone bytes."""
import os, psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'): os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,hashlib,re,time
from pathlib import Path
from shapely.geometry import Polygon
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(ROOT/d))
from verify_source import P as SP
OUT=H/'R218-eight-native-zone-intersections-exact-input-attribution-r581'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(x):return hashlib.sha256(x).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def extract(data,uid):
 needle=('(uuid "'+uid+'")').encode()
 if needle not in data:return None
 at=data.index(needle);begin=data.rfind(b'\n\t(zone',0,at)+1;end=re.search(rb'\r?\n\t\)\r?\n',data[at:]);assert begin>0 and end
 return data[begin:at+end.end()]
def desc(ch):
 a=SP['sexpr_parse'](ch.decode());rings=[]
 for poly in SP['children'](a,'polygon'):
  rings.append([(float(x[1]),float(x[2]))for x in SP['children'](SP['child'](poly,'pts'),'xy')])
 s=Polygon(rings[0],rings[1:]);assert s.is_valid
 cfg=[x for x in a[1:]if isinstance(x,list)and x[0]not in('polygon','filled_polygon','fill_segments','uuid')]
 return {'raw_net':SP['atom'](a,'net'),'layer':SP['atom'](a,'layer'),'exact_native_profile_AST':cfg,'chunk_SHA256':hs(ch),'outline_WKB_SHA256':hs(s.wkb)},s
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic()
 files={'R218':ROOT/'FA-IO3-TMR-exact-two-zone-native-selected-diagnostic-r218/copy/board.kicad_pcb','R157':ROOT/'R155-known-reference-native-diagnostic-r157/copy/board.kicad_pcb','R9':ROOT/'SAFE-exploratory-native-trial-r9/copy/board.kicad_pcb'}
 report=H/'R218-original-IO3-TMR-native-no-refill-boundary-DRC-r567/drc.json';oldreport=ROOT/'R9-failed-flash-native-DRC-diagnostic-r113/drc.json';expected=ROOT/'R155-known-reference-native-diagnostic-r157/expected-zones.json'
 pins={str(x.resolve()):sha(x)for x in list(files.values())+[report,oldreport,expected,Path(__file__)]}
 assert sha(report)=='f96a00e35488e43f36df54ed24b402b47f77ec6a74a65bbe53e10a56bafe181a'
 data={k:p.read_bytes()for k,p in files.items()};rows=[x for x in json.loads(report.read_bytes())['violations']if x['type']=='zones_intersect'];assert len(rows)==8
 earlier=[x for x in json.loads(oldreport.read_bytes())['violations']if x['type']=='zones_intersect'];assert not earlier
 exp={x['uuid']:x for x in json.loads(expected.read_bytes())['zones']};results=[];zones={};changed_R515=set(json.loads((ROOT/'FA-IO3-TMR-exact-two-zone-native-selected-diagnostic-r218/inputs.json').read_bytes())['new_native_zone_UUIDs'])
 for i,row in enumerate(rows):
  uu=[x['uuid']for x in row['items']];assert len(uu)==2
  details=[];shapes=[]
  for uid in uu:
   chs={k:extract(v,uid)for k,v in data.items()};assert chs['R218']==chs['R157']and chs['R218']is not None;d,s=desc(chs['R218']);shapes.append(s)
   assert uid in exp and exp[uid]['raw_net']==d['raw_net']and exp[uid]['layer']==d['layer']
   rr=[]
   for poly in SP['children'](SP['sexpr_parse'](chs['R218'].decode()),'polygon'):
    ring=[[round(float(x[1])*1e6),round(float(x[2])*1e6)]for x in SP['children'](SP['child'](poly,'pts'),'xy')];rr.append(ring)
   # Expected APIs may remove only consecutive identical/closing vertices.
   def clean(r):
    out=[]
    for xy in r:
     if not out or xy!=out[-1]:out.append(xy)
    if len(out)>1 and out[0]==out[-1]:out.pop()
    return out
   assert [clean(r)for r in rr]==[clean(r)for r in exp[uid]['rings_IU']]
   dd=dict(d,UUID=uid,raw_integer_rings_exact_R157_expected=True,R218_R157_full_native_chunk_byte_identical=True,R515_changed_native_UUID=False,R9_presence=chs['R9']is not None,R9_chunk_SHA256=None if chs['R9']is None else hs(chs['R9']),R9_full_chunk_equal=None if chs['R9']is None else chs['R9']==chs['R218'])
   assert uid not in changed_R515
   if uid not in zones:
    (OUT/(uid+'.exact-unchanged-R218-R157.zone-chunk')).write_bytes(chs['R218']);zones[uid]=dd
   details.append(dd)
  hit=shapes[0].intersection(shapes[1]);(OUT/('pair-'+str(i)+'-exact-outline-intersection.wkb')).write_bytes(hit.wkb)
  same=details[0]['raw_net']==details[1]['raw_net'];layer=details[0]['layer']==details[1]['layer'];profile=details[0]['exact_native_profile_AST']==details[1]['exact_native_profile_AST'];assert same and layer and profile
  results.append({'report_index':i,'native_DRC_row':row,'zones':details,'same_exact_raw_net':same,'same_exact_layer':layer,'same_exact_native_profile_AST':profile,'intersection':{'empty':hit.is_empty,'type':hit.geom_type,'area_mm2':hit.area,'length_mm':hit.length,'bounds_mm':None if hit.is_empty else list(hit.bounds),'WKB_SHA256':hs(hit.wkb)},'attribution':'INHERITED_UNCHANGED_R157_NEW_ZONE_PAIR_NOT_CHANGED_R515_TWO_ZONE_SERIALIZATION','native_ERROR_retained':True})
 assert all(sha(p)==v for p,v in pins.items())
 put(OUT/'all-eight-exact-pair-location-native-profile-attributions.json',results)
 put(OUT/'receipt.json',{'status':'EIGHT_NATIVE_SAME_RAW_SAME_LAYER_SAME_PROFILE_ERRORS_ALL_ATTRIBUTED_NOT_RESOLVED','pins':pins,'pair_count':8,'unique_zones':len(zones),'all_reported_pairs_full_zone_bytes_exact_R157_parent':True,'all_pairs_raw_net_layer_and_profile_identical':True,'all_pairs_disjoint_from_R515_changed_native_UUID_set':True,'introduced_by_R515_two_zone_serialization_count':0,'reported_inter_net_zone_pair_count':0,'earlier_R9_native_DRC_zones_intersect_count':0,'earlier_R9_no_overlap_report_does_not_qualify_later_R157_zone_additions':True,'zone_rows':list(zones.values()),'all_native_errors_retained':'Eight touching/overlapping independently serialized new zones require later exact same-settings composition. No error waiver, geometry edit, priority change or whole-board DRC acceptance. This report attributes only the eight reported pairs, not a blanket foreign-outline clearance pass.','no_native_launch_or_inputs_edit':True,'adopted':False,'elapsed_seconds':time.monotonic()-st})
 print('R581',sha(OUT/'receipt.json'),'pairs',len(results),'unique',len(zones),flush=True)
if __name__=='__main__':main()
