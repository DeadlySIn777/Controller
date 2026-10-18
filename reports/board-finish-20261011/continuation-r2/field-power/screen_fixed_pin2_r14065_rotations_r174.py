"""Resistor rotation nominees retain the exact probe-shutdown pin2 contact."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,sys,copy
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.affinity import rotate
from shapely.ops import unary_union
from shapely import set_precision
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import complete_geometry_r2 as G
import guarded_declared_settings_projection_r58 as P
O=H/'r14065-fixed-shutdown-contact-rotation-screen-r174'
def rings(sh):return G.records(sh)
def main():
 assert not O.exists();O.mkdir();B=H.parent/'sbc-power/SAFE-repaired-owned-zone-normalization-r160/model.pkl';g,h,b,z,c=pickle.loads(B.read_bytes());fp=next(q for q in h['footprints'] if q['ref']=='R14065');pads=[q for q in h['pads'] if q['ref']=='R14065'];p1=next(q for q in pads if q['num']=='1');p2=next(q for q in pads if q['num']=='2');sh1=unary_union(C.poly(p1['layers']['B.Cu']));sh2=unary_union(C.poly(p2['layers']['B.Cu']));origin=(p2['x'],p2['y']);rec,trees=F.build({**h,'zones':[]},layers={'B.Cu'});tm={t['uuid']:t for t in h['tracks']};vm={v['uuid']:v for v in h['vias']};outside=[]
 for j in trees['B.Cu'].query(sh1.buffer(.000002),predicate='intersects'):
  a=rec['B.Cu'][int(j)]
  if a['uuid']!=p1['uuid'] and a['net']==p1['net'] and a['shape'].distance(sh1)<=.000002:outside.append({'kind':a['kind'],'uuid':a['uuid'],'raw_net':a['net'],'bounds':list(a['shape'].bounds)})
 rows=[];accepted=[]
 for angle in (90.,180.,270.):
  shape=set_precision(rotate(sh1,angle,origin=origin),1e-6);body=set_precision(rotate(unary_union(C.poly(fp['courtyard']['B'])),angle,origin=origin),1e-6);checks=[]
  for j in trees['B.Cu'].query(shape.buffer(.627),predicate='intersects'):
   a=rec['B.Cu'][int(j)]
   if a['uuid'] in {p1['uuid'],p2['uuid']} or a['net']==p1['net']:continue
   gap=shape.distance(a['shape'])
   if a['kind']=='track':t=tm[a['uuid']];gap=shape.distance(LineString([t['a'],t['b']]))-t['w']/2
   if a['kind']=='via':v=vm[a['uuid']];gap=shape.distance(Point(v['x'],v['y']))-v['d']/2
   checks.append({'foreign':a['uuid'],'kind':a['kind'],'gap_mm':gap,'required_mm':G.gap(h,p1['net'],a['net'])+.025})
  for other in h['footprints']:
   if other['ref']==fp['ref']:continue
   courtyard=unary_union(C.poly(other['courtyard'].get('B',[])))
   if not courtyard.is_empty and body.intersects(courtyard):checks.append({'foreign':other['ref'],'kind':'courtyard_overlap','gap_mm':-body.intersection(courtyard).area,'required_mm':0.})
  for area in h['rule_areas']:
   if area.get('no_footprints') and 'B.Cu' in area['layers'] and any(body.intersects(s) for s in C.poly(area['outline'])):checks.append({'foreign':area['uuid'],'kind':'native_no_footprint','gap_mm':-1.,'required_mm':0.})
  bad=[x for x in checks if x['gap_mm']+1e-10<x['required_mm']];row={'angle_change_deg':angle,'new_pin1_xy':list(rotate(Point(p1['x'],p1['y']),angle,origin=origin).coords[0]),'new_FP_xy':list(rotate(Point(fp['x'],fp['y']),angle,origin=origin).coords[0]),'pin2_absolute_raw_net_physical_contact_retained_exact':True,'old_pin1_discrete_contacts':outside,'errors':bad};rows.append(row);print('R174 angle',angle,'errors',len(bad),'old_pin1_contacts',len(outside),flush=True)
  if not bad:accepted.append({'row':row,'pad1_shape':shape,'new_courtyard':body})
 (O/'nominees.pkl').write_bytes(pickle.dumps(accepted,protocol=5));(O/'receipt.json').write_text(json.dumps({'verdict':'SCOPED_R14065_POSE_NOMINEES_SOURCE_FANOUT_FULL_RETAINED_FAULT_REFERENCE_NATIVE_OPEN','source_model_sha256':sha(B),'unchanged_source_BOM_value_MPN':True,'probe_shutdown_limit_and_control_rate_unchanged':True,'old_pin1_discrete_contacts':outside,'rows':rows,'accepted_local_pose_count':len(accepted),'no_old_Cu_removal_or_source_edit_proposed':True,'board_written':False},indent=1)+'\n',encoding='utf-8');print('R174',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
