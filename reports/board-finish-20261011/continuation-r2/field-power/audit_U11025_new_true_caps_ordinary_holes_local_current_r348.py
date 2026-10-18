"""Independent full caps/physical annuli/all-SMD guard and conditional local drop."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys,math
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import complete_geometry_r2 as G
R=H/'U11025-joint-health-return-legal-face-construction-r344';O=H/'U11025-independent-full-caps-aperture-current-r348'
def main():
 assert not O.exists();O.mkdir();_,h,_,_,_=pickle.loads((R/'model.pkl').read_bytes());d=pickle.loads((R/'proposed-discrete.pkl').read_bytes());newids={q['uuid'] for k in ('vias','tracks') for q in d[k]};rec,trees=F.build({**h,'zones':[]});tm={q['uuid']:q for q in h['tracks']};vm={q['uuid']:q for q in h['vias']};checks=[]
 for t in d['tracks']:
  ax=LineString([t['a'],t['b']])
  for i in trees[t['layer']].query(ax.buffer(t['w']/2+.627),predicate='intersects'):
   q=rec[t['layer']][int(i)]
   if q['uuid']==t['uuid'] or q['net']==t['net']:continue
   req=G.gap(h,t['net'],q['net'])+.025;gap=ax.distance(q['shape'])-t['w']/2
   if q['kind']=='track':other=tm[q['uuid']];gap=ax.distance(LineString([other['a'],other['b']]))-(t['w']+other['w'])/2
   elif q['kind']=='via':v=vm[q['uuid']];gap=ax.distance(Point(v['x'],v['y']))-t['w']/2-v['d']/2
   checks.append({'new_UUID':t['uuid'],'foreign_UUID':q['uuid'],'kind':'true_track_caps_to_'+q['kind'],'layer':t['layer'],'required_mm':req,'actual_mm':gap,'PASS':gap+1e-10>=req})
 v=d['vias'][0];point=Point(v['x'],v['y'])
 for l in v['span']:
  for i in trees[l].query(point.buffer(v['d']/2+.627),predicate='intersects'):
   q=rec[l][int(i)]
   if q['uuid']==v['uuid'] or q['net']==v['net']:continue
   req=G.gap(h,v['net'],q['net'])+.025;gap=point.distance(q['shape'])-v['d']/2
   if q['kind']=='track':t=tm[q['uuid']];gap=point.distance(LineString([t['a'],t['b']]))-(v['d']+t['w'])/2
   elif q['kind']=='via':other=vm[q['uuid']];gap=point.distance(Point(other['x'],other['y']))-(v['d']+other['d'])/2
   checks.append({'new_UUID':v['uuid'],'foreign_UUID':q['uuid'],'kind':'actual_all6_via_envelope_to_'+q['kind'],'layer':l,'required_mm':req,'actual_mm':gap,'PASS':gap+1e-10>=req})
 for pad in h['pads']:
  if pad['smd']:
   for layer,rows in pad['layers'].items():
    for shape in C.poly(rows):
     gap=point.distance(shape)-v['drill']/2
     if gap<1:checks.append({'new_UUID':v['uuid'],'foreign_UUID':pad['uuid'],'kind':'drill_to_every_SMD_including_same_net','layer':layer,'required_mm':.275,'actual_mm':gap,'PASS':gap+1e-10>=.275})
  for shape in C.poly(pad.get('hole') or []):
   gap=point.distance(shape)-v['drill']/2
   if gap<1:checks.append({'new_UUID':v['uuid'],'foreign_UUID':pad['uuid'],'kind':'drill_to_actual_pad_hole','required_mm':.275,'actual_mm':gap,'PASS':gap+1e-10>=.275})
 for other in h['vias']:
  if other['uuid']==v['uuid']:continue
  gap=point.distance(Point(other['x'],other['y']))-(v['drill']+other['drill'])/2
  if gap<1:checks.append({'new_UUID':v['uuid'],'foreign_UUID':other['uuid'],'kind':'new_drill_to_every_old_or_peer_drill','required_mm':.275,'actual_mm':gap,'PASS':gap+1e-10>=.275})
 length=sum(LineString([t['a'],t['b']]).length for t in d['tracks'] if t['net']==v['net']);rho=1.724e-8*(1+.00393*(125-20));track_R=rho*(length*.001)/(.2e-3*25e-6);barrel_area=math.pi*((.1e-3+20e-6)**2-(.1e-3)**2);barrel_R=rho*1.6e-3/barrel_area;local={'scope':'only_U11025_2_1mA_branch_not_whole_FA_4_584429A','current_A':.001,'full_new_F_ground_length_mm':length,'all_new_F_ground_width_mm':.2,'screen_outer_Cu_um':25,'screen_barrel_plating_um':20,'screen_whole_barrel_length_mm':1.6,'screen_Cu_temperature_C':125,'rho_ohm_m':rho,'F_track_R_ohm':track_R,'whole_barrel_R_ohm':barrel_R,'conditional_local_track_plus_full_barrel_drop_V':.001*(track_R+barrel_R),'conditional_local_track_plus_barrel_loss_W':.001**2*(track_R+barrel_R),'unknown_parent_sheet_spreading_contact_actual_thickness_temperature_and_transient_impedance_not_included':True,'no_guaranteed_capacity_or_physical_measurement_claim':True}
 errors=[q for q in checks if not q['PASS']];(O/'true-copper-and-ordinary-aperture-checks.json').write_text(json.dumps(checks,indent=1)+'\n',encoding='utf-8');(O/'conditional_local_branch_current-drop.json').write_text(json.dumps(local,indent=1)+'\n',encoding='utf-8');out={'verdict':'INDEPENDENT_NEW_CU_AND_ORDINARY_APERTURE_PASS_CONDITIONAL_LOCAL_CURRENT_SCREEN_NATIVE_OPEN' if not errors else 'INDEPENDENT_NEW_U11025_CU_APERTURE_REJECTED','R344_receipt_SHA256':sha(R/'receipt.json'),'R344_model_SHA256':sha(R/'model.pkl'),'checks':len(checks),'errors':errors,'local_branch_screen':local,'no_source_or_reference_credit_from_this_gate':True,'full_actual_filled_Cu_current_native_allseverity_gate':'OPEN','native_jobs':0,'board_written':False,'adopted':False};(O/'receipt.json').write_text(json.dumps(out,indent=1)+'\n',encoding='utf-8');print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'checks':len(checks),'errors':len(errors),'local_conditional_drop_V':local['conditional_local_track_plus_full_barrel_drop_V']}),flush=True)
if __name__=='__main__':main()
