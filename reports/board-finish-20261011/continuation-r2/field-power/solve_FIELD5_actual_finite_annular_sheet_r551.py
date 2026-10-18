"""Contained sheet numerical screen of the exact R543 DC source bridge.

Both actual parent-source Cu and the real target annulus are frozen.
No equal sharing or full upstream/return/thermal qualification is inferred.
"""
import os,psutil
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,hashlib,time,math,gc
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point
from shapely.ops import unary_union
from scipy.ndimage import label
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
H=Path(__file__).resolve().parent
for d in('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from inventory import sha
M=H/'FIELD5-source-plane-exact-owned-edge-negative-redesign-current-r543';P=H/'FIELD5-failed-In4-withdrawal-actual-source-target-port-census-r521';A=H/'FIELD5-all-source-finite-annulus-old-reference-hard-nomination-r523';O=H/'FIELD5-R543-actual-source-Cu-finite-target-annulus-contained-sheet-r551';TARGET='0901cf4a-0f1c-4f5a-8c92-68ccf5d1bfe3'
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def put(f,v):f.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def solve(shape,source,target,step):
 inset=shape.buffer(-step/math.sqrt(2)-.000002);x0,y0,x1,y1=inset.bounds;xx=np.arange(math.floor(x0/step)*step+step/2,x1,step);yy=np.arange(math.floor(y0/step)*step+step/2,y1,step);X,Y=np.meshgrid(xx,yy);mask=shapely.contains_xy(inset,X,Y);lab,_=label(mask,np.array([[0,1,0],[1,1,1],[0,1,0]]));sm=mask&shapely.contains_xy(source.buffer(-step/math.sqrt(2)-.000002),X,Y);srcids=set(lab[sm])-{0}
 if not srcids:return {'status':'NUMERIC_SUBSET_HAS_NO_CONTAINED_SOURCE_CONTACT','step_mm':step}
 mask &= np.isin(lab,list(srcids));sm &=mask;tm=mask&shapely.contains_xy(target.buffer(-step/math.sqrt(2)-.000002),X,Y);idx=np.full(mask.shape,-1,dtype=np.int64);idx[mask]=np.arange(mask.sum());sx=idx[sm];tx=idx[tm]
 if not len(tx):return {'status':'NUMERIC_SUBSET_HAS_NO_CONTAINED_TARGET_ANNULAR_CONTACT','step_mm':step,'source_cells':len(sx),'contained_cells':int(mask.sum())}
 assert not np.intersect1d(sx,tx).size;n=int(mask.sum());pairs=[]
 for axis in(0,1):
  aa,bb=(idx[:-1,:],idx[1:,:])if axis==0 else(idx[:,:-1],idx[:,1:]);yes=(aa>=0)&(bb>=0);pairs.append((aa[yes],bb[yes]))
 aa=np.concatenate([a for a,z in pairs]);bb=np.concatenate([z for a,z in pairs]);degree=np.bincount(np.concatenate([aa,bb]),minlength=n).astype(float);mat=coo_matrix((np.concatenate([degree,-np.ones(len(aa)),-np.ones(len(bb))]),(np.concatenate([np.arange(n),aa,bb]),np.concatenate([np.arange(n),bb,aa]))),shape=(n,n)).tocsr();fixed=np.unique(np.concatenate([sx,tx]));keep=np.setdiff1d(np.arange(n),fixed);rhs=np.asarray(-mat[keep][:,tx].sum(axis=1)).ravel();u=np.zeros(n);u[tx]=1.;started=time.monotonic();u[keep]=spsolve(mat[keep][:,keep].tocsc(),rhs);resid=float(np.max(np.abs((mat@u)[keep])));forward=float(np.sum((mat@u)[tx]));back=-float(np.sum((mat@u)[sx]));assert forward>0 and resid<1e-7 and abs(forward-back)<1e-7
 row={'status':'CONDITIONAL_CONTAINED_ACTUAL_SHEET_SOLVED','step_mm':step,'contained_cells':n,'wholly_contained_source_contact_cells':len(sx),'wholly_contained_finite_target_annular_contact_cells':len(tx),'effective_sheet_squares':1/forward,'normalized_KCL_residual_A':abs(forward-back),'max_equation_residual':resid,'unit_current_peak_mesh_edge_A_per_mm':float(np.max(np.abs(u[aa]-u[bb]))/forward/step),'solve_seconds':time.monotonic()-started,'every_cell_wholly_contained_in_actual_drill_subtracted_positive_Cu':True,'source_and_target_contacts_are_real_contained_Cu_not_fabricated_disks':True};del mat,u,mask,lab,X,Y;gc.collect();return row
def main():
 assert not O.exists();O.mkdir();st=time.monotonic();assert sha(M/'model.pkl')=='474949d472a1870320b95cd494d4c96f79735b43632076d237d432d10c006416';g,h,b,q,c=pickle.loads((M/'model.pkl').read_bytes());proposal=pickle.loads((A/'only-one-new-FIELD5-actual-source-port-nominee.pkl').read_bytes());uid=proposal['q']['uuid'];actual=next(z for z in q if z['uuid']==uid);oldgroups=pickle.loads((P/'actual-FIELD5-groups-with-only-failed-In4-owned-zone-withdrawn.pkl').read_bytes());sourcegroup=K.root(oldgroups,'L11003','2');targetgroup=next(xs for xs in oldgroups if any(r['kind']=='via'and r['uuid']==TARGET for r in xs));source_Cu=unary_union([r['shape']for r in sourcegroup if r['layer']=='In2.Cu']);target=unary_union([r['shape']for r in targetgroup if r['kind']=='via'and r['uuid']==TARGET and r['layer']=='In2.Cu']);holes,tree=K.hole_context(c);body=actual['shape'];physical=body.difference(unary_union([holes[int(j)]for j in tree.query(body,predicate='intersects')]));source_all=source_Cu.intersection(physical);target=target.intersection(physical);last=proposal['path'][-1];goal=source_all.intersection(Point(last).buffer(.25,quad_segs=128));assert source_all.area>0 and target.area>0 and goal.area>0
 for name,s in(('exact-physical-sheet',physical),('actual-parent-source-all-contacts',source_all),('actual-parent-source-goal-contact',goal),('actual-finite-target-annular-contact',target)):(O/(name+'.wkb')).write_bytes(s.wkb)
 ports={'physical_sheet_SHA256':dg(physical),'source_group_real_L11003_2':True,'source_all_actual_overlap_mm2':source_all.area,'source_goal_actual_overlap_mm2':goal.area,'target_existing_native_via_UID':TARGET,'target_finite_actual_annular_overlap_mm2':target.area,'source_electrode_ideal_potential_is_boundary_condition_not_upstream_drop_or_equal_sharing_claim':True};put(O/'exact-sheet-and-finite-port-binding.json',ports);rows=[];cases=[]
 for step in(.05,.025):
  for kind,source in(('all_actual_parent_contacts_equipotential',source_all),('only_actual_goal_contact_equipotential',goal)):
   row=solve(physical,source,target,step);row['source_boundary_case']=kind;rows.append(row);put(O/'checkpoint.json',rows);print('R551',kind,step,row.get('effective_sheet_squares'),row['status'],flush=True)
   if row['status']!='CONDITIONAL_CONTAINED_ACTUAL_SHEET_SOLVED':continue
   for thickness,temp in((35,60),(25,125)):
    rho=1.724e-8*(1+.00393*(temp-20));R=row['effective_sheet_squares']*rho/(thickness*1e-6)
    for I in(.341130981,.36):cases.append({'step_mm':step,'source_boundary_case':kind,'conditional_Cu_um':thickness,'conditional_uniform_copper_temperature_C':temp,'full_FIELD5_stress_current_A':I,'regional_sheet_R_ohm':R,'regional_sheet_drop_V':I*R,'regional_sheet_Joule_W':I*I*R,'computed_peak_mesh_edge_current_A_per_mm':I*row['unit_current_peak_mesh_edge_A_per_mm'],'not_a_full_upstream_plus_return_network_or_thermal_capacity_bound':True})
 barrel=[]
 for plating,temp in((25,60),(20,125)):
  rho=1.724e-8*(1+.00393*(temp-20));area=math.pi*((.1e-3+plating*1e-6)**2-(.1e-3)**2);R=rho*.0016/area
  for I in(.341130981,.36):barrel.append({'target_via_UID':TARGET,'conditional_plating_um':plating,'conditional_uniform_Cu_C':temp,'full_barrel_length_mm':1.6,'drill_mm':.2,'barrel_R_ohm':R,'full_FIELD5_A':I,'conditional_whole_barrel_drop_V':I*R,'conditional_whole_barrel_Joule_W':I*I*R,'actual_plating_tolerance_solder_spreading_thermal_transient_and_current_sharing_OPEN':True})
 put(O/'receipt.json',{'status':'CONDITIONAL_ACTUAL_REGIONAL_SHEET_AND_SINGLE_REAL_TARGET_BARREL_NUMERICS_NOT_FULL_CURRENT_QUALIFICATION','R543_model_SHA256':sha(M/'model.pkl'),'R545_fresh_source_contact_geometry_receipt_SHA256':sha(H/'FIELD5-R543-full-exact-net-source-contact-reference-geometry-r545/receipt.json'),'R547_exact_reference_identity_with_raw_controls_FAIL_receipt_SHA256':sha(H/'FIELD5-R545-identical-reference-primitive-paired-before-controls-r547/receipt.json'),'port_binding':ports,'rows':rows,'conditional_regional_sheet_cases':cases,'conditional_target_whole_barrel_cases':barrel,'full_FIELD5_current_A':.341130981,'unchanged_routing_reservation_A':.36,'required_FAG_source_return_A':4.58442937244,'parent_source_and_destination_actual_ground_current_network_NOT_solved_here':True,'native_old_actual_target_In2_annular_contact_after_fresh_fill':'OPEN','source_old_sheet_and_all_current_actual_RTNs_resistive_contact_pad_module_connector_heat_fault_transient':'OPEN','R15528refs_CORE_ROOT42_planner_and_R54512raw_identical_control_FAIL_remain_bound':True,'native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-st});print('R551',sha(O/'receipt.json'),'max regional drop',max((r['regional_sheet_drop_V']for r in cases),default=None),flush=True)
if __name__=='__main__':main()
