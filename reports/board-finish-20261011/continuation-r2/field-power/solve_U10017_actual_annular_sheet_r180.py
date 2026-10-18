"""Source-bound conservative sheet mesh of the exact full-current bypass."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math,time
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point,LineString
from scipy.ndimage import label
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from inventory import sha
H=Path(__file__).resolve().parent;B=H/'SAFE-U10017-wider-full-branch-audit-r178'
O=H/'U10017-actual-annular-sheet-full-branch-r180'
def write(p,v):p.write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();r=json.loads((B/'receipt.json').read_text(encoding='utf-8'));assert r['verdict']=='SAFE_U10017_ONLY_WIDER_FULL_BRANCH_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS';assert sha(B/'model.pkl')==r['model_sha256'];O.mkdir()
 g,h,b,z,c=pickle.loads((B/'model.pkl').read_bytes());q=next(q for q in z if q['uuid']=='e8ec0287-e6d1-597d-8ad8-c4ab74280f6c');vs={v['uuid']:v for v in h['vias']};source=vs['a7ee4fd8-3850-567a-b9d7-3b25a458757a'];target=vs['c55416b9-e522-5cbf-9523-ddb093be9249'];neck=next(t for t in h['tracks'] if t['uuid']=='f7771804-1031-58d5-b67f-e44f3ded6f0a');assert neck['w']==.6
 assert source['net']==target['net']==q['net'];assert q['layer']=='In2.Cu';shape=q['shape'];ann=lambda v:Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128));sa=ann(source);ta=ann(target);rows=[]
 for step in (.05,.025,.0125):
  inset=shape.buffer(-step/math.sqrt(2)-.00000002);x0,y0,x1,y1=shape.bounds;xx=np.arange(math.floor(x0/step)*step+step/2,x1,step);yy=np.arange(math.floor(y0/step)*step+step/2,y1,step);X,Y=np.meshgrid(xx,yy);mask=shapely.contains_xy(inset,X,Y);labels,ncomp=label(mask,np.array([[0,1,0],[1,1,1],[0,1,0]]));sm=mask&shapely.contains_xy(sa,X,Y);source_components=set(labels[sm])-{0};assert source_components;mask &=np.isin(labels,list(source_components));sm &=mask;tm=mask&shapely.contains_xy(ta,X,Y);assert tm.any(),('contained mesh cannot connect true source/target annuli',step);idx=np.full(mask.shape,-1,dtype=np.int64);idx[mask]=np.arange(mask.sum());sx=idx[sm];tx=idx[tm];n=int(mask.sum());edges=[]
  for axis in (0,1):
   aa,bb=(idx[:-1,:],idx[1:,:]) if axis==0 else (idx[:,:-1],idx[:,1:]);ok=(aa>=0)&(bb>=0);edges.append((aa[ok],bb[ok]))
  aa=np.concatenate([v[0] for v in edges]);bb=np.concatenate([v[1] for v in edges]);degree=np.bincount(np.concatenate([aa,bb]),minlength=n).astype(float);A=coo_matrix((np.concatenate([degree,-np.ones(len(aa)),-np.ones(len(bb))]),(np.concatenate([np.arange(n),aa,bb]),np.concatenate([np.arange(n),bb,aa]))),shape=(n,n)).tocsr();fixed=np.unique(np.concatenate([sx,tx]));unknown=np.setdiff1d(np.arange(n),fixed);rhs=np.asarray(-A[unknown][:,tx].sum(axis=1)).ravel();u=np.zeros(n);u[tx]=1;start=time.monotonic();u[unknown]=spsolve(A[unknown][:,unknown].tocsc(),rhs);flux=A@u;resid=float(np.max(np.abs(flux[unknown])));forward=float(flux[tx].sum());reverse=float(-flux[sx].sum());assert forward>0 and resid<1e-7 and abs(forward-reverse)<1e-7;effective_squares=1/forward
  row={'cell_size_mm':step,'contained_cells':n,'actual_source_annular_cells':len(sx),'actual_target_annular_cells':len(tx),'effective_sheet_squares':effective_squares,'unit_sheet_source_sink_KCL_residual':abs(forward-reverse),'unit_mesh_equation_max_residual':resid,'solve_seconds':time.monotonic()-start,'every_cell_wholly_contained_in_exact_guarded_physical_Cu':True};rows.append(row);write(O/'checkpoint.json',rows);print(json.dumps(row),flush=True)
 cases=[];I=2.2686163215869097;length=LineString([neck['a'],neck['b']]).length
 for cu in (35,25):
  for temp in (20,60,105,125):
   rho=1.724e-8*(1+.00393*(temp-20));sheet=rho/(cu*1e-6);Rsheet=rows[-1]['effective_sheet_squares']*sheet;Rneck=sheet*length/neck['w'];cases.append({'conditional_Cu_um':cu,'conditional_uniform_copper_temperature_C':temp,'exact_full_nine_pad_current_upper_A':I,'In2_sheet_R_ohm':Rsheet,'new_F_neck_R_ohm':Rneck,'sheet_plus_new_neck_drop_V':I*(Rsheet+Rneck),'sheet_plus_new_neck_loss_W':I*I*(Rsheet+Rneck),'neck_uniform_width_model_excludes_pad_spreading':True})
 barrel=[]
 for plating in (20,25,30):
  for temp in (20,60,105,125):
   rho=1.724e-8*(1+.00393*(temp-20));parts=[]
   for v in (source,target):
    Rb=rho*.0016/(math.pi*(v['drill']*.001*plating*1e-6+(plating*1e-6)**2));parts.append({'via_UUID':v['uuid'],'drill_mm':v['drill'],'full_1p6mm_ideal_cylinder_R_ohm':Rb})
   Rb=sum(v['full_1p6mm_ideal_cylinder_R_ohm'] for v in parts);barrel.append({'conditional_plating_um':plating,'conditional_temperature_C':temp,'both_full_length_barrels_conservative_DC_series_screen':parts,'at_full_nine_pad_current_drop_V':I*Rb,'at_full_nine_pad_current_loss_W':I*I*Rb,'actual_layer_height_path_and_barrel_thermal_not_qualified':True})
 convergence=[{'coarser_mm':a['cell_size_mm'],'finer_mm':bb['cell_size_mm'],'effective_squares_relative_difference':abs(a['effective_sheet_squares']/bb['effective_sheet_squares']-1)} for a,bb in zip(rows,rows[1:])]
 rec={'verdict':'EXACT_SOURCE_BOUND_FULL_CURRENT_CONTAINED_SHEET_NUMERICS_WITH_CONDITIONAL_PHYSICAL_INPUTS','baseline_full76_source_contact_reference_receipt_sha256':sha(B/'receipt.json'),'exact_model_sha256':sha(B/'model.pkl'),'physical_shape_WKB_sha256':__import__('hashlib').sha256(shape.wkb).hexdigest(),'raw_net':q['net'],'source_port':source['uuid']+'.In2.Cu','target_port':target['uuid']+'.In2.Cu','nominal_stack_copper_um':35,'signed_full_branch_current_interval_A':[.26061632158690984,I],'parent_exact_current_bound_receipt_sha256':sha(H.parent/'u10017-nine-pad-protected-bypass-current-bound-r48/receipt.json'),'rows':rows,'grid_convergence':convergence,'sheet_and_neck_cases':cases,'barrel_sensitivity_cases':barrel,'annuli_assumed_equipotential_is_explicit_mesh_boundary_only':True,'current_sharing_is_not_equal_VS_or_via_assumed':True,'unchanged_output_limits_and_all_simultaneous_loads':True,'open_gates':['native filled actual In2 flashes on BOTH source and target barrels','full upstream protected supply/return sheet and package-pin network','qualified Cu/plating tolerances and thermal boundary conditions','pad/barrel solder spreading and transient fault current','physical board temperature rise and measured worst-case drop'],'manufacturing_ready':False,'board_written':False,'native_jobs':0};write(O/'receipt.json',rec);print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'convergence':convergence,'worst_sheet_neck_drop_V':max(v['sheet_plus_new_neck_drop_V'] for v in cases)}),flush=True)
if __name__=='__main__':main()
