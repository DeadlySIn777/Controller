"""Exact current source/target nearest ports and real outer blockers."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,sys
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import nearest_points,unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import fast_contacts as F
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import complete_geometry_r2 as G
from inventory import sha
O=H/'remaining-four-regulated-exact-outer-port-diagnosis-r371'
B=H/'REG-U25-DIC-SBC273-two-new-REG-actual-fill-margin-repair-r364'
C=H/'all-five-regulated-actual-drilled-literal-source-census-r370'
def main():
 assert not O.exists();O.mkdir();assert sha(B/'model.pkl')=='a39e7784abf8969b7f68176555b2c37b5227981cbc615c4bd542205e410373ad';g,h,b,z,current=pickle.loads((B/'model.pkl').read_bytes());groups=pickle.loads((C/'all-five-actual-drilled-regulated-groups.pkl').read_bytes());rec,trees=F.build(current);tm={r['uuid']:r for r in h['tracks']};vm={r['uuid']:r for r in h['vias']};rows=[]
 for rail,net,source,sp,ref,pin,layer in [('FIELD5','/motherboard_power_entry/FIELD_5V','L11003','2','U9004','10','F.Cu'),('A3','/motherboard_do/DOA_FIELD_3V3','U11017','1','U10009','4','B.Cu'),('A3','/motherboard_do/DOA_FIELD_3V3','U11017','1','R14065','1','B.Cu'),('BDO3','DOB_DO_FIELD_3V3','U11038','1','U10022','4','B.Cu')]:
  root=K.root(groups[net],source,sp);pad=next(r for r in h['pads']if(r['ref'],str(r['num']))==(ref,pin));shape=unary_union(L.poly(pad['layers'][layer]));anchor=Point(pad['x'],pad['y']);choices=[]
  for item in root:
   if item['layer']!=layer:continue
   start,end=nearest_points(shape,item['shape']);line=LineString([start,end]);blocks=[]
   for j in trees[layer].query(line.buffer(.925),predicate='intersects'):
    foreign=rec[layer][int(j)]
    if L.norm(foreign['net'])==net:continue
    req=G.gap(h,pad['net'],foreign['net'])+.025
    dist=line.distance(foreign['shape'])-.1
    if foreign['kind']=='track'and not tm[foreign['uuid']].get('m'):t=tm[foreign['uuid']];dist=line.distance(LineString([t['a'],t['b']]))-.1-t['w']/2
    elif foreign['kind']=='via':v=vm[foreign['uuid']];dist=line.distance(Point(v['x'],v['y']))-.1-v['d']/2
    if dist<req:blocks.append({'kind':foreign['kind'],'UUID':foreign['uuid'],'raw_net':foreign['net'],'actual_mm':dist,'required_mm':req})
   choices.append({'source_kind':item['kind'],'source_UUID':item['uuid'],'source_ref':item.get('ref'),'source_pin':item.get('pin'),'distance_mm':line.length,'direct_start_end_mm':[list(start.coords[0]),list(end.coords[0])],'direct_full_.20_foreign_blockers':blocks})
  choices=sorted(choices,key=lambda x:(x['distance_mm'],len(x['direct_full_.20_foreign_blockers'])))[:12]
  rows.append({'rail':rail,'target':ref+'.'+pin,'target_native_UUID':pad['uuid'],'raw_net':pad['net'],'layer':layer,'native_pad_centre_mm':[pad['x'],pad['y']],'native_pad_bounds_mm':list(shape.bounds),'exact_source_nearest_outer_ports':choices})
 (O/'receipt.json').write_text(json.dumps({'verdict':'READ_ONLY_EXACT_CURRENT_OUTER_BLOCKER_DIAGNOSIS','model_sha256':sha(B/'model.pkl'),'source_census_receipt_sha256':sha(C/'receipt.json'),'rows':rows,'no_original_or_new_copper_changed':True,'routing_full_source_reference_current_native':'OPEN'},indent=1)+'\n',encoding='utf-8');print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'targets':[{'target':r['target'],'centre':r['native_pad_centre_mm'],'nearest':r['exact_source_nearest_outer_ports'][:2]}for r in rows]}),flush=True)
if __name__=='__main__':main()
