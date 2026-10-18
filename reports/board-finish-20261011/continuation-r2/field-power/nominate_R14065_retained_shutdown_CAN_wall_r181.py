"""One actual CAN-wall coupling, preserving the shutdown pad and old contacts."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import copy,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision
from shapely.affinity import rotate
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import complete_geometry_r2 as G
import guarded_declared_settings_projection_r58 as P
O=H/'R14065-shutdown-preserving-one-CAN-wall-nominees-r181'
def write(p,v):p.write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();B=H.parent/'sbc-power/SAFE-repaired-owned-zone-normalization-r160/model.pkl';g,h,b,z,c=pickle.loads(B.read_bytes());fp=next(q for q in h['footprints'] if q['ref']=='R14065');pads=[q for q in h['pads'] if q['ref']=='R14065'];p1=next(q for q in pads if q['num']=='1');p2=next(q for q in pads if q['num']=='2');origin=(p2['x'],p2['y']);p1old=unary_union(C.poly(p1['layers']['B.Cu']));p2old=unary_union(C.poly(p2['layers']['B.Cu']));p1new=set_precision(rotate(p1old,180,origin=origin),1e-6);p2new=set_precision(rotate(p2old,180,origin=origin),1e-6);assert p2old.equals(p2new)
 uid='e97700e6-80b1-4c0e-a1ed-1be39dede491';wall=next(t for t in h['tracks'] if t['uuid']==uid);assert wall['net']=='/motherboard_comms/CAN_RXD' and wall['layer']=='B.Cu' and wall['w']==.2
 h2=copy.deepcopy(h);h2['tracks']=[t for t in h2['tracks'] if t['uuid']!=uid];changed=next(q for q in h2['pads'] if q['uuid']==p1['uuid']);xy=rotate(Point(p1['x'],p1['y']),180,origin=origin);changed['x'],changed['y']=xy.x,xy.y;changed['layers']['B.Cu']=G.records(p1new)
 body=set_precision(rotate(unary_union(C.poly(fp['courtyard']['B'])),180,origin=origin),1e-6)
 rec,trees=F.build({**h2,'zones':[]});tm={t['uuid']:t for t in h2['tracks']};vm={v['uuid']:v for v in h2['vias']};oldbody=C.body(wall);outside=[]
 for j in trees['B.Cu'].query(oldbody.buffer(.000002),predicate='intersects'):
  a=rec['B.Cu'][int(j)]
  if a['net']==wall['net'] and a['shape'].distance(oldbody)<=.000002:outside.append({'kind':a['kind'],'uuid':a['uuid'],'shape':a['shape'],'bounds':list(a['shape'].bounds)})
 core=F.graph(c,'/LOGIC_GND');root=next(xs for xs in core if any(q['kind']=='pad' and(q.get('ref'),q.get('pin'))==('J11001','2') for q in xs));ref=unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']=='In4.Cu']);poses=[]
 for offset in (0.,.2,.4,.6,.8,1.):
  pts=[wall['a'],[round(wall['b'][0]+offset,6),wall['a'][1]],[round(wall['b'][0]+offset,6),wall['b'][1]],wall['b']];tracks=[];checks=[];shapes=[]
  for index,(a,bb) in enumerate(zip(pts,pts[1:])):
   if a==bb:continue
   t={**wall,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,f'R14065-CAN-coupled-r181/{offset}/{index}')),'a':a,'b':bb};tracks.append(t);line=LineString([a,bb]);sh=P.bounded_buffer(line,.1);shapes.append(sh)
   for j in trees['B.Cu'].query(sh.buffer(.627),predicate='intersects'):
    q=rec['B.Cu'][int(j)]
    if q['net']==t['net']:continue
    gap=line.distance(q['shape'])-.1
    if q['kind']=='track':tt=tm[q['uuid']];gap=line.distance(LineString([tt['a'],tt['b']]))-(.2+tt['w'])/2
    if q['kind']=='via':v=vm[q['uuid']];gap=line.distance(Point(v['x'],v['y']))-(.2+v['d'])/2
    req=G.gap(h2,t['net'],q['net'])+.025
    if gap<req+1e-10:checks.append({'new':t['uuid'],'foreign':q['uuid'],'kind':q['kind'],'actual_mm':gap,'required_mm':req})
   for q in z:
    if q['layer']!='B.Cu' or q['net']==t['net']:continue
    req=max(G.gap(h2,t['net'],q['net']),float(q.get('clearance_mm',.15)))+.025;gap=line.distance(q['shape'])-.1
    if gap<req+1e-10:checks.append({'new':t['uuid'],'foreign':q['uuid'],'kind':'new_plane','actual_mm':gap,'required_mm':req})
   for area in h2['rule_areas']:
    if area.get('no_tracks') and 'B.Cu' in area['layers'] and any(sh.intersects(P.bounded_buffer(s,.025)) for s in C.poly(area['outline'])):checks.append({'new':t['uuid'],'foreign':area['uuid'],'kind':'native_no_track'})
  joined=unary_union(shapes);miss=joined.difference(ref).area;lost=[q['uuid'] for q in outside if not joined.intersects(q['shape'])];courtyards=[q['ref'] for q in h2['footprints'] if q['ref']!='R14065' and body.intersects(unary_union(C.poly(q['courtyard'].get('B',[]))))];row={'offset_mm':offset,'new_CAN_length_mm':sum(LineString([t['a'],t['b']]).length for t in tracks),'errors':checks,'outside_contact_losses':lost,'courtyard_overlaps':courtyards,'new_CAN_uncovered_actual_J1_In4_reference_mm2':miss,'new_FP_xy':list(rotate(Point(fp['x'],fp['y']),180,origin=origin).coords[0]),'new_pin1_xy':[xy.x,xy.y],'retained_shutdown_pin2_unchanged_shape_raw_net':True}
  poses.append(row);print('R181',offset,len(checks),'contacts',len(lost),'reference_gap',miss,flush=True)
  if not checks and not lost and not courtyards and miss<1e-9:(O/f'accepted-CAN-offset-{offset}.pkl').write_bytes(pickle.dumps({'tracks':tracks,'new_pad1':changed,'FP':fp,'new_courtyard':body,'new_FP_xy':row['new_FP_xy']},protocol=5))
 write(O/'receipt.json',{'verdict':'LOCAL_COUPLED_NOMINEES_ONLY_FULL_SOURCE_GROUND_FEED_CURRENT_NATIVE_OPEN','source_model_sha256':sha(B),'exact_old_CAN_track':wall,'old_track_outside_contact_ledger':[{k:v for k,v in q.items() if k!='shape'} for q in outside],'new_R14065_source_value_MPN_and_pad_raw_nets_unchanged':True,'rows':poses,'board_written':False,'native_jobs':0});print('R181',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
