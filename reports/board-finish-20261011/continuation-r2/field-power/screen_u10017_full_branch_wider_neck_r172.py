"""Screen wider owned source neck against true analytic local geometry."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pathlib,pickle,json,sys,copy,math
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from inventory import sha
import contact_layout as C
import fast_contacts as F
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import guarded_declared_settings_projection_r58 as P
import complete_geometry_r2 as G
O=H/'u10017-wider-owned-source-neck-screen-r172'
def main():
 assert not O.exists();O.mkdir();R=H/'u17-u10017-reference-safe-incremental-audit-r162';g,h,b,z,c=pickle.loads((R/'model.pkl').read_bytes());track=next(t for t in h['tracks'] if t['uuid']=='f7771804-1031-58d5-b67f-e44f3ded6f0a');line=LineString([track['a'],track['b']]);rec,trees=F.build({**h,'zones':[]},layers={'F.Cu'});tm={t['uuid']:t for t in h['tracks']};vm={v['uuid']:v for v in h['vias']};rows=[];accepted=None
 for width in (1.,.8,.6,.5,.4):
  checks=[];body=P.bounded_buffer(line,width/2)
  for j in trees['F.Cu'].query(body.buffer(.627),predicate='intersects'):
   a=rec['F.Cu'][int(j)]
   if C.norm(a['net'])==C.norm(track['net']):continue
   gap=line.distance(a['shape'])-width/2
   if a['kind']=='track':t=tm[a['uuid']];gap=line.distance(LineString([t['a'],t['b']]))-(width+t['w'])/2
   if a['kind']=='via':v=vm[a['uuid']];gap=line.distance(Point(v['x'],v['y']))-(width+v['d'])/2
   checks.append({'foreign':a['uuid'],'kind':a['kind'],'actual_gap_mm':gap,'required_mm':G.gap(h,track['net'],a['net'])+.025})
  for q in z:
   if q['layer']=='F.Cu' and C.norm(q['net'])!=C.norm(track['net']):
    gap=line.distance(q['shape'])-width/2;req=max(G.gap(h,track['net'],q['net']),float(q.get('clearance_mm',.15)))+.025
    if gap<req+.01:checks.append({'foreign':q['uuid'],'kind':'owned_plane','actual_gap_mm':gap,'required_mm':req})
  for area in h['rule_areas']:
   if area.get('no_tracks') and 'F.Cu' in area['layers']:
    for sh in C.poly(area['outline']):
     if body.intersects(P.bounded_buffer(sh,.025)):checks.append({'foreign':area['uuid'],'kind':'native_no_track','actual_gap_mm':-1.,'required_mm':0.})
  bad=[r for r in checks if r['actual_gap_mm']+1e-10<r['required_mm']];rows.append({'width_mm':width,'checks':checks,'errors':bad});print('R172 width',width,'checks',len(checks),'errors',len(bad),flush=True)
  if not bad:accepted={**copy.deepcopy(track),'w':width};break
 if accepted:(O/'owned-replacement-track.pkl').write_bytes(pickle.dumps(accepted,protocol=5))
 current=2.2686163215869097;physics=[]
 for width in (.3,accepted['w'] if accepted else .3):
  for temp in (60.,125.):
   rho=1.724e-8*(1+.00393*(temp-20));res=rho*(line.length/1000)/(width/1000*35e-6);physics.append({'nominal_35um_copper_temperature_C':temp,'width_mm':width,'length_mm':line.length,'resistance_ohm':res,'worst_simplex_DC_drop_V':current*res,'I2R_W':current*current*res,'unknown_actual_temperature_rise':True})
 (O/'receipt.json').write_text(json.dumps({'verdict':'WIDER_LOCAL_CU_ANALYTIC_NOMINEE_FULL_SOURCE_REFERENCE_NATIVE_CURRENT_OPEN' if accepted else 'NO_WIDER_ANALYTIC_NECK','baseline_R162_sha256':sha(R/'receipt.json'),'exact_track_UUID':track['uuid'],'old_width_mm':track['w'],'selected_width_mm':accepted['w'] if accepted else None,'all_current_device_output_limits_unchanged':True,'checks_by_width':rows,'nominal_35um_resistance_screen_not_thermal_or_current_rating':physics,'actual_full_branch_bound_A':current,'original_Cu_edits':0,'only_owned_new_track_width_change':True,'native_jobs':0,'board_written':False,'full_coupled_oldfill_source_reference_barrel_plating_transient_gate':'OPEN'},indent=1)+'\n',encoding='utf-8');print('R172 complete',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
