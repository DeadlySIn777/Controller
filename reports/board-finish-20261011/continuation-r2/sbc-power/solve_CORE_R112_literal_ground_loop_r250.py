"""Four literal ground Cu legs from regulator GND4 to FPGA GND A1.

This is one real single-path full-load stress case, not equal current sharing
or a blanket 31-pad/pin/thermal rating. Known two bare FPGA grounds stay open.
"""
import hashlib,json,pickle,sys,math,time,traceback
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point,box
from shapely.ops import unary_union
from scipy.ndimage import label
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
H=Path(__file__).resolve().parent.parent
for d in('sbc-power','field-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import guarded_declared_settings_projection_r58 as GP
O=H/'sbc-power/CORE-R112-literal-four-leg-ground-loop-r250'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n')
def pieces(sh):return[sh]if sh.geom_type=='Polygon'else[p for p in getattr(sh,'geoms',[])if p.geom_type=='Polygon']
def solve(shape,sa,ta,step):
 margin=step/math.sqrt(2)+.00000002;inset=shape.buffer(-margin);x0,y0,x1,y1=shape.bounds;xx=np.arange(math.floor(x0/step)*step+step/2,x1,step);yy=np.arange(math.floor(y0/step)*step+step/2,y1,step);X,Y=np.meshgrid(xx,yy);mask=shapely.contains_xy(inset,X,Y);labels,ncomp=label(mask,np.array([[0,1,0],[1,1,1],[0,1,0]]));sm=mask&shapely.contains_xy(sa.buffer(-margin),X,Y);components=set(labels[sm])-{0};tm=mask&shapely.contains_xy(ta.buffer(-margin),X,Y)
 if not components or not (tm&np.isin(labels,list(components))).any():return{'cell_size_mm':step,'source_cells':int(sm.sum()),'target_cells':int(tm.sum()),'conservative_contained_path':False}
 mask&=np.isin(labels,list(components));sm&=mask;tm&=mask;idx=np.full(mask.shape,-1,dtype=np.int64);idx[mask]=np.arange(mask.sum());sx=idx[sm];tx=idx[tm];n=int(mask.sum());edges=[]
 for ax in(0,1):
  aa,bb=(idx[:-1,:],idx[1:,:])if ax==0 else(idx[:,:-1],idx[:,1:]);ok=(aa>=0)&(bb>=0);edges.append((aa[ok],bb[ok]))
 aa=np.concatenate([v[0]for v in edges]);bb=np.concatenate([v[1]for v in edges]);degree=np.bincount(np.concatenate([aa,bb]),minlength=n).astype(float);A=coo_matrix((np.concatenate([degree,-np.ones(len(aa)),-np.ones(len(bb))]),(np.concatenate([np.arange(n),aa,bb]),np.concatenate([np.arange(n),bb,aa]))),shape=(n,n)).tocsr();fixed=np.unique(np.concatenate([sx,tx]));unknown=np.setdiff1d(np.arange(n),fixed);rhs=np.asarray(-A[unknown][:,tx].sum(axis=1)).ravel();u=np.zeros(n);u[tx]=1.;started=time.monotonic();u[unknown]=spsolve(A[unknown][:,unknown].tocsc(),rhs);flux=A@u;resid=float(np.max(np.abs(flux[unknown])));forward=float(flux[tx].sum());reverse=float(-flux[sx].sum());assert forward>0 and resid<1e-7 and abs(forward-reverse)<1e-7
 return{'cell_size_mm':step,'contained_cells':n,'source_cells':len(sx),'target_cells':len(tx),'conservative_contained_path':True,'effective_sheet_squares':1/forward,'KCL_residual':abs(forward-reverse),'equation_residual':resid,'solve_seconds':time.monotonic()-started}
def main():
 assert not O.exists();O.mkdir();base=H/'sbc-power/CORE-R112-exact-ground-cross-layer-topology-r249';assert sha(base/'receipt.json')=='754100d0e83334eee6db787757903020ec4fe22058893f2ef4beaa82ebf0a72d';mp=H/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112/model.pkl';assert sha(mp)=='6312b10a88b2d3614e21760d1709866d2417b419d418e20e09055eb13b8e3b7e';g,h,b,z,c=pickle.loads(mp.read_bytes());vias={v['uuid']:v for v in h['vias']};source=vias['07ec511d-7db2-4d0a-b3e6-724f14592d86'];cross=vias['009de6d1-a266-4015-9fa1-fd0e2e809155'];target=vias['2712cb19-4473-49e1-832c-7afe543955d9'];sp=next(p for p in h['pads']if(p['ref'],p['num'])==('U2001','4'));tp=next(p for p in h['pads']if(p['ref'],p['num'])==('U1001','A1'));ends=json.loads((base/'actual-regulator-FPGA-return-route-witnesses.json').read_text());ea=next(e for e in ends if(e['ref'],e['pin'])==('U1001','A1'));assert[v['UUID']for v in ea['fewest_layer_crossing_witness_ONLY_not_shortest_or_lowest_resistance_route']]==[source['uuid'],cross['uuid'],target['uuid']]
 layers={l:pieces(shapely.from_wkb((base/(l+'-exact-drilled-source-ground-union.wkb')).read_bytes()))for l in('F.Cu','In1.Cu','In4.Cu')}
 def ann(v):return Point(v['x'],v['y']).buffer(v['d']/2-.00000002,quad_segs=128).difference(GP.bounded_disk(v,v['drill']/2+.00000002))
 legs=[('regulator_GND4_to_actual_07ec','F.Cu',661,unary_union(C.poly(sp['layers']['F.Cu'])),ann(source),None,(.05,.025,.0125)),('source_ground_actual_07ec_to_actual_009d','In1.Cu',88,ann(source),ann(cross),None,(.075,.05)),('cross_actual_009d_to_FPGA_ground_actual_2712','In4.Cu',1,ann(cross),ann(target),box(145,50,228,112),(.075,.05)),('FPGA_actual_2712_to_GND_A1','F.Cu',315,ann(target),unary_union(C.poly(tp['layers']['F.Cu'])),None,(.025,.0125,.00625))]
 rows=[];latest=[]
 for role,l,i,sa,ta,clip,steps in legs:
  shape=layers[l][i];assert sa.intersection(shape).area>0 and ta.intersection(shape).area>0
  if clip is not None:shape=shape.intersection(clip)
  sa=sa.intersection(shape);ta=ta.intersection(shape);f=O/(role+'-physical-sheet.wkb');f.write_bytes(shape.wkb);gr=[]
  for step in steps:
   rr=solve(shape,sa,ta,step);row={'role':role,'layer':l,'literal_global_ground_face_node':[l,i],'physical_shape_WKB_sha256':sha(f),'physical_sheet_area_mm2':shape.area,'actual_source_terminal_Cu_mm2':sa.area,'actual_target_terminal_Cu_mm2':ta.area,'each_leg_full_0p8A_single_ground_pin_stress_case_not_equal_distribution':True,**rr};gr.append(row);rows.append(row);put(O/'checkpoint.json',rows);print('R250_GROUND_LOOP_LEG',json.dumps(row),flush=True)
  success=[r for r in gr if r['conservative_contained_path']];latest.append(success[-1]if success else None)
 cases=[];feed=json.loads((H/'sbc-power/CORE-R112-wide-actual-annular-contained-sheet-r247/receipt.json').read_text());assert sha(H/'sbc-power/CORE-R112-wide-actual-annular-contained-sheet-r247/receipt.json')=='6604bebdb45eda2e89bacde9bf3b5f53f3588743dfbb3fadfc072b2962c1238c'
 if all(latest):
  for cu in(35,25):
   for temp in(60,100,125):
    rho=1.7241e-8*(1+.00393*(temp-20));squares=sum(r['effective_sheet_squares']for r in latest);rs=squares*rho/(cu*1e-6);barrels=[]
    for v,length in((source,.255),(cross,.765),(target,1.020)):
     d=v['drill']*1e-3;t=.020e-3;rr=rho*(length*1e-3)/(math.pi*((d/2+t)**2-(d/2)**2));barrels.append({'UUID':v['uuid'],'actual_flashes':v['flashed'],'used_vertical_mm_CONDITIONAL_stack_spacing':length,'conditional_finished_plating_um':20,'R_ohm':rr})
    rb=sum(r['R_ohm']for r in barrels);fd=next(r['sheet_plus_two_used_barrels_drop_V']for r in feed['conditional_supply_cases']if r['conditional_Cu_um']==cu and r['conditional_copper_temperature_C']==temp);drop=.8*(rs+rb);cases.append({'conditional_Cu_um':cu,'conditional_temperature_C':temp,'full_0p8A_CORE_and2A_IO3_retained':True,'literal_four_leg_return_sheet_squares':squares,'return_sheet_R_ohm':rs,'three_actual_return_used_barrels':barrels,'return_drop_V':drop,'new_feed_plus_this_actual_single_path_return_drop_V':fd+drop,'remaining_1p185_to1p15V_budget_V':.035-fd-drop,'all_other_shared_logic_currents_regulator_older_In3_supply_VOS_local_spreading_ripple_and_transients_not_included':True})
 put(O/'literal-loop-cases.json',cases);put(O/'receipt.json',{'verdict':'LITERAL_FOUR_CU_LEG_AND_THREE_BARREL_GROUND_RETURN_CONDITIONAL_STRESS_NUMERICS_FULL31PIN_SHARED_LOOP_OPEN','model_sha256':sha(mp),'R249_topology_sha256':sha(base/'receipt.json'),'actual_U2001_GND4_pad_UUID':sp['uuid'],'actual_U1001_GND_A1_pad_UUID':tp['uuid'],'mesh_rows':rows,'literal_series_legs_last_grid_success':all(latest),'conditional_loop_cases':cases,'actual_native_used_mask_barrels_no_private_barrel_or_extra_flash_exemption':True,'two_original_FPGA_GND_R7_T4_still_bare':True,'other28_connected_ground_pin_transfer_paths_3p993A_shared_ground_current_complete_load_assignment_local_cap_loop_ESL_effectiveC_transient_VOS_source_native_and_thermal':'OPEN','mesh_grid_convergence_and_fixed_terminal_equipotential_BOUNDARY_not_physical_rating':True,'no_current_equal_sharing_or_full_readiness_inference':True,'board_written':False,'native_jobs':0,'script_sha256':sha(__file__)})
 print('R250_COMPLETE',sha(O/'receipt.json'),'loop_cases',len(cases),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
