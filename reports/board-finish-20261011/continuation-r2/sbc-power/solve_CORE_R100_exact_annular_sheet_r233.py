"""Contained-cell DC sheet sensitivity on the exact materialized CORE feed."""
import hashlib,json,pickle,sys,math,time,traceback
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point
from scipy.ndimage import label
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
H=Path(__file__).resolve().parent.parent
for d in('sbc-power','field-power'):sys.path.insert(0,str(H/d))
import restore_SAFE_generated_precision_states_r168 as PS
O=H/'sbc-power/CORE-R100-actual-annular-contained-sheet-r233'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n')
def main():
 assert not O.exists();O.mkdir();mp=H/'CORE-In2-owned-notch-materialized-source-proposal-r100/model.pkl';assert sha(mp)=='db01ba8f89c614c72b19688ec6479c96e8524259f1968eaa2dd3f2caeef49635';g,h,b,z,c=pickle.loads(mp.read_bytes());PS.restore_bound_generated_precision_states(b,z);q=next(q for q in z if q['uuid']=='b0453302-df03-561f-9bc4-0560bc66658a');shape=q['shape'];vs={v['uuid']:v for v in h['vias']};source=vs['8e2d3546-318d-571e-a2af-6f143fbdb5ba'];target=vs['0c3c4802-aa2d-55ad-a84b-6e2acf573601'];assert all(v['net']=='/CORE_1V2'and(v['d'],v['drill'])==(.5,.2)for v in(source,target))
 def ann(v):p=Point(v['x'],v['y']);return p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128))
 sa,ta=ann(source),ann(target);rows=[]
 for step in(.05,.025,.0125):
  margin=step/math.sqrt(2)+.00000002;inset=shape.buffer(-margin);x0,y0,x1,y1=shape.bounds;xx=np.arange(math.floor(x0/step)*step+step/2,x1,step);yy=np.arange(math.floor(y0/step)*step+step/2,y1,step);X,Y=np.meshgrid(xx,yy);mask=shapely.contains_xy(inset,X,Y);labels,ncomp=label(mask,np.array([[0,1,0],[1,1,1],[0,1,0]]));sm=mask&shapely.contains_xy(sa.buffer(-margin),X,Y);components=set(labels[sm])-{0};assert components,'no conservative whole source-annulus cell';mask&=np.isin(labels,list(components));sm&=mask;tm=mask&shapely.contains_xy(ta.buffer(-margin),X,Y);assert tm.any(),('source/target conservative annular cells disconnected',step);idx=np.full(mask.shape,-1,dtype=np.int64);idx[mask]=np.arange(mask.sum());sx=idx[sm];tx=idx[tm];n=int(mask.sum());edges=[]
  for ax in(0,1):
   aa,bb=(idx[:-1,:],idx[1:,:])if ax==0 else(idx[:,:-1],idx[:,1:]);ok=(aa>=0)&(bb>=0);edges.append((aa[ok],bb[ok]))
  aa=np.concatenate([v[0]for v in edges]);bb=np.concatenate([v[1]for v in edges]);degree=np.bincount(np.concatenate([aa,bb]),minlength=n).astype(float);A=coo_matrix((np.concatenate([degree,-np.ones(len(aa)),-np.ones(len(bb))]),(np.concatenate([np.arange(n),aa,bb]),np.concatenate([np.arange(n),bb,aa]))),shape=(n,n)).tocsr();fixed=np.unique(np.concatenate([sx,tx]));unknown=np.setdiff1d(np.arange(n),fixed);rhs=np.asarray(-A[unknown][:,tx].sum(axis=1)).ravel();u=np.zeros(n);u[tx]=1.;started=time.monotonic();u[unknown]=spsolve(A[unknown][:,unknown].tocsc(),rhs);flux=A@u;resid=float(np.max(np.abs(flux[unknown])));forward=float(flux[tx].sum());reverse=float(-flux[sx].sum());assert forward>0 and resid<1e-7 and abs(forward-reverse)<1e-7
  row={'cell_size_mm':step,'contained_cells':n,'whole_actual_source_annular_cells':len(sx),'whole_actual_target_annular_cells':len(tx),'effective_sheet_squares':1/forward,'source_sink_KCL_residual':abs(forward-reverse),'max_equation_residual':resid,'solve_seconds':time.monotonic()-started,'every_square_wholly_inside_exact_drilled_physical_Cu':True,'every_terminal_square_wholly_inside_nominal_annulus':True,'fixed_annular_potential_is_explicit_contact_boundary_assumption':True};rows.append(row);put(O/'checkpoint.json',rows);print('R233_SHEET_GRID',json.dumps(row),flush=True)
  if len(rows)>1 and abs(rows[-2]['effective_sheet_squares']/rows[-1]['effective_sheet_squares']-1)<.01:break
 cases=[];I=.8
 for cu in(35,25):
  for temp in(20,60,100,125):
   rho=1.7241e-8*(1+.00393*(temp-20));R=rows[-1]['effective_sheet_squares']*rho/(cu*1e-6);barrel=rho*.000255/(math.pi*(.0002*.00002+.00002**2));drop=I*(R+2*barrel);cases.append({'conditional_Cu_um':cu,'conditional_copper_temperature_C':temp,'full_conserved_CORE_rail_current_A':I,'exact_new_In2_sheet_R_ohm':R,'conditional_two_In2_In3_0p255mm_20um_barrels_R_ohm':2*barrel,'sheet_plus_two_used_barrels_drop_V':drop,'sheet_plus_barrel_heat_W':I*I*(R+2*barrel),'remaining_1p185V_low_source_to1p15V_local_pin_budget_V':.035-drop,'return_spreading_old_native_In3_F_or_B_fanout_ripple_transient_not_assumed_zero':True})
 conv=[{'coarse_mm':a['cell_size_mm'],'fine_mm':bb['cell_size_mm'],'relative_effective_squares_difference':abs(a['effective_sheet_squares']/bb['effective_sheet_squares']-1)}for a,bb in zip(rows,rows[1:])];put(O/'receipt.json',{'verdict':'EXACT_NEW_CORE_FEED_CONTAINED_ANNULAR_SHEET_NUMERICS_CONDITIONAL_INPUTS_FULL_LOOP_OPEN','exact_model_sha256':sha(mp),'physical_shape_WKB_sha256':hashlib.sha256(shape.wkb).hexdigest(),'physical_sheet_area_mm2':shape.area,'raw_net':q['net'],'layer':q['layer'],'source_port':source,'target_port':target,'rows':rows,'convergence':conv,'conditional_supply_cases':cases,'full_CORE_0p8A_and_IO3_2A_retained':True,'no_equal_layer_via_FPGA_pad_current_sharing_assumed':True,'native_all6_actual_source_landing_and_materialized_fill_validation':'OPEN','actual_source_and_old_branch_spreading_local_decaps_VOS_RETURN_mesh_shared_ground_drop_current_limit_startup_fault_thermal_plating_tolerances':'OPEN','no_voltage_or_reference_or_current_readiness_gate_flipped':True,'board_written':False,'native_jobs':0,'script_sha256':sha(__file__)})
 print('R233_COMPLETE',sha(O/'receipt.json'),'squares',rows[-1]['effective_sheet_squares'],'worst_conditional_drop',max(x['sheet_plus_two_used_barrels_drop_V']for x in cases),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
