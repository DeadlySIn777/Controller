"""One finer contained-grid solve on exactly the frozen R551 real electrodes."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,hashlib,time,importlib.util
from pathlib import Path
from shapely import from_wkb
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(ROOT/d))
from inventory import sha
OLD=H/'FIELD5-R543-actual-source-Cu-finite-target-annulus-contained-sheet-r551';OUT=H/'FIELD5-R543-same-real-annuli-contained-mesh-refinement-r579'
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic();assert sha(OLD/'receipt.json')=='982948739ae8cdffd9555da66c15ec4196b5d2cdfb6a2b6bdd694927c80b1309';old=json.loads((OLD/'receipt.json').read_bytes())
 helper=H/'solve_FIELD5_actual_finite_annular_sheet_r551.py';spec=importlib.util.spec_from_file_location('exact_frozen_R551_contained_solver',helper);S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
 files={role:OLD/(name+'.wkb')for role,name in [('physical','exact-physical-sheet'),('source_all','actual-parent-source-all-contacts'),('source_goal','actual-parent-source-goal-contact'),('target','actual-finite-target-annular-contact')]};sh={k:from_wkb(v.read_bytes())for k,v in files.items()};pins={str(f.resolve()):sha(f)for f in files.values()};pins[str(helper.resolve())]=sha(helper)
 assert hashlib.sha256(sh['physical'].wkb).hexdigest()==old['port_binding']['physical_sheet_SHA256'];assert sh['source_all'].area==old['port_binding']['source_all_actual_overlap_mm2']and sh['source_goal'].area==old['port_binding']['source_goal_actual_overlap_mm2']and sh['target'].area==old['port_binding']['target_finite_actual_annular_overlap_mm2']
 rows=[];cases=[]
 for kind,source in [('all_actual_parent_contacts_equipotential',sh['source_all']),('only_actual_goal_contact_equipotential',sh['source_goal'])]:
  row=S.solve(sh['physical'],source,sh['target'],.0125);row['source_boundary_case']=kind;prior=next(x for x in old['rows']if x['step_mm']==.025 and x['source_boundary_case']==kind);row['same_real_port_grid_025_squares']=prior.get('effective_sheet_squares');row['fraction_change_from_grid025']=row.get('effective_sheet_squares',0)/prior['effective_sheet_squares']-1 if row['status']=='CONDITIONAL_CONTAINED_ACTUAL_SHEET_SOLVED'else None;rows.append(row);put(OUT/'checkpoint.json',rows);print('R579',kind,row.get('effective_sheet_squares'),row['status'],flush=True)
  if row['status']!='CONDITIONAL_CONTAINED_ACTUAL_SHEET_SOLVED':continue
  for thickness,temp in [(35,60),(25,125)]:
   rho=1.724e-8*(1+.00393*(temp-20));R=row['effective_sheet_squares']*rho/(thickness*1e-6)
   for I in [.341130981,.36]:cases.append({'step_mm':.0125,'source_boundary_case':kind,'conditional_Cu_um':thickness,'conditional_uniform_copper_temperature_C':temp,'full_FIELD5_A':I,'regional_sheet_R_ohm':R,'regional_sheet_drop_V':I*R,'regional_sheet_Joule_W':I*I*R,'peak_mesh_edge_current_A_per_mm':I*row['unit_current_peak_mesh_edge_A_per_mm'],'no_upstream_return_loop_thermal_capacity_claim':True})
 assert all(sha(Path(f))==v for f,v in pins.items());put(OUT/'receipt.json',{'status':'CONDITIONAL_FROZEN_ACTUAL_SHEET_MESH_REFINEMENT_NOT_COMPLETE_POWER_QUALIFICATION','input_R551_SHA256':sha(OLD/'receipt.json'),'input_R543_model_SHA256':old['R543_model_SHA256'],'pins':pins,'port_binding':old['port_binding'],'helper_required_shape_source_target_erosions_cell_containment_and_guards_unchanged':True,'rows':rows,'conditional_regional_sheet_cases':cases,'prior_grids_05_025_and_full_numerical_conditions':str((OLD/'receipt.json').resolve()),'source_equipotential_cases_are_boundary_conditions_not_equal_pin_sharing_or_full_upstream_drop':True,'actual_qualified_Cu_plating_temperature_connector_package_sheet_transient_switching_and_full_FAG_return_mesh':'OPEN','FIELD5_native_actual_target_In2_flash_finite_annular_contact_after_fresh_fill':'OPEN','new_FAG_cut_and_four_actual_TPS_RTN_support_current':'OPEN','FIELD5_voltage_drop_budget_NOT_derived_from_48V_FA_FB_policy':True,'raw_R545_R547_R155_CORE_ROOT42_reference_and_native_failures_preserved':True,'native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-st});print('R579',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
