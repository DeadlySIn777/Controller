"""Local resistor flip/shift keeps all existing shutdown copper untouched."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,sys,copy
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.affinity import rotate,translate
from shapely.ops import unary_union
from shapely import set_precision
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import complete_geometry_r2 as G
import guarded_declared_settings_projection_r58 as P
O=H/'r14065-translated-flip-control-retention-screen-r175'
def main():
 assert not O.exists();O.mkdir();B=H.parent/'sbc-power/SAFE-repaired-owned-zone-normalization-r160/model.pkl';g,h,b,z,c=pickle.loads(B.read_bytes());fp=next(q for q in h['footprints'] if q['ref']=='R14065');pads=[q for q in h['pads'] if q['ref']=='R14065'];p1=next(q for q in pads if q['num']=='1');p2=next(q for q in pads if q['num']=='2');origin=(p2['x'],p2['y']);rec,trees=F.build({**h,'zones':[]},layers={'B.Cu'});tm={t['uuid']:t for t in h['tracks']};vm={v['uuid']:v for v in h['vias']};fg=next(xs for xs in F.graph(c,'/motherboard_motors/FIELD_GND') if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11003','2') for q in xs));reference=unary_union([q['shape'] for q in fg if q['kind']=='fill' and q['layer']=='In4.Cu']);rows=[];accepted=[]
 def checks_for(sh,net,kind,line=None,width=None):
  checks=[]
  for j in trees['B.Cu'].query(sh.buffer(.627),predicate='intersects'):
   a=rec['B.Cu'][int(j)]
   if a['uuid'] in {p1['uuid'],p2['uuid']} or a['net']==net:continue
   gap=sh.distance(a['shape'])
   if a['kind']=='track':t=tm[a['uuid']];gap=(line if line is not None else sh).distance(LineString([t['a'],t['b']]))-t['w']/2-(width/2 if width else 0)
   if a['kind']=='via':v=vm[a['uuid']];gap=(line if line is not None else sh).distance(Point(v['x'],v['y']))-v['d']/2-(width/2 if width else 0)
   checks.append({'owner_kind':kind,'foreign':a['uuid'],'kind':a['kind'],'gap_mm':gap,'required_mm':G.gap(h,net,a['net'])+.025})
  return checks
 for dx in (-1.,-1.5,-2.,-2.5,1.,1.5,2.,2.5):
  pose=[];checks=[]
  for pad in pads:
   sh=set_precision(translate(rotate(unary_union(C.poly(pad['layers']['B.Cu'])),180,origin=origin),xoff=dx),1e-6);pt=translate(rotate(Point(pad['x'],pad['y']),180,origin=origin),xoff=dx);pose.append({'original':pad,'xy':list(pt.coords[0]),'shape':sh});checks+=checks_for(sh,pad['net'],'new_'+pad['num'])
  body=set_precision(translate(rotate(unary_union(C.poly(fp['courtyard']['B'])),180,origin=origin),xoff=dx),1e-6)
  for other in h['footprints']:
   if other['ref']==fp['ref']:continue
   cy=unary_union(C.poly(other['courtyard'].get('B',[])))
   if not cy.is_empty and body.intersects(cy):checks.append({'foreign':other['ref'],'kind':'courtyard_overlap','gap_mm':-body.intersection(cy).area,'required_mm':0.})
  link=LineString([origin,pose[1]['xy']]);linkbody=P.bounded_buffer(link,.1);checks+=checks_for(linkbody,p2['net'],'retained_shutdown_contact_link',link,.2)
  for area in h['rule_areas']:
   if area.get('no_tracks') and 'B.Cu' in area['layers'] and any(linkbody.intersects(P.bounded_buffer(sh,.025)) for sh in C.poly(area['outline'])):checks.append({'foreign':area['uuid'],'kind':'native_no_track','gap_mm':-1.,'required_mm':0.})
  bad=[x for x in checks if x['gap_mm']+1e-10<x['required_mm']];ref_missing=linkbody.difference(reference).area;row={'translation_dx_mm':dx,'rotation_change_deg':180.,'new_FP_xy':[fp['x']+dx,2*p2['y']-fp['y']],'new_pin1_xy':pose[0]['xy'],'new_pin2_xy':pose[1]['xy'],'new_control_link_width_mm':.2,'old_shutdown_Cu_contacts_kept_at_original_pose':True,'new_link_full_actual_J3_reference_covered':ref_missing==0,'new_link_reference_missing_mm2':ref_missing,'errors':bad};rows.append(row);print('R175',dx,'errors',len(bad),'newrefmissing',ref_missing,flush=True)
  if not bad and ref_missing==0:accepted.append({'row':row,'new_pad_poses':pose,'new_courtyard':body,'new_pin2_link':link})
 (O/'nominees.pkl').write_bytes(pickle.dumps(accepted,protocol=5));(O/'receipt.json').write_text(json.dumps({'verdict':'LOCAL_POSE_AND_RETAINED_CONTROL_NOMINEES_SOURCE_BARREL_AND_FULL_FAULT_CONTACT_NATIVE_OPEN','source_SAFE_model_sha256':sha(B),'rows':rows,'accepted_local_pose_count':len(accepted),'original_pad1_has_zero_discrete_contacts_bound_R174_sha256':sha(H/'r14065-fixed-shutdown-contact-rotation-screen-r174/receipt.json'),'original_shutdown_tracks_and_vias_removed':0,'source_value_MPN_control_rate_output_limits_unchanged':True,'native_jobs':0,'board_written':False},indent=1)+'\n',encoding='utf-8');print('R175',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
