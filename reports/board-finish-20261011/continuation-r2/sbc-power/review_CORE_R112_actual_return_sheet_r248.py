"""Actual J1-rooted return sheets and exact local device/cap ground ledger.

The two physical ground ports are measured separately on each inner return
layer at the full rail load. Their identity/annuli are literal; neither their
local fanout nor parallel layer sharing is treated as already qualified.
"""
import hashlib,json,pickle,sys,math,time,traceback
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
from scipy.ndimage import label
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
H=Path(__file__).resolve().parent.parent
for d in('sbc-power','field-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import guarded_declared_settings_projection_r58 as GP
import restore_SAFE_generated_precision_states_r168 as PS
O=H/'sbc-power/CORE-R112-actual-return-sheet-and-local-loop-r248'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(sh):return hashlib.sha256(sh.wkb).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n')
def root(gs,ref,pin):return next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,pin)for q in xs))
def main():
 assert not O.exists();O.mkdir();mp=H/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112/model.pkl';assert sha(mp)=='6312b10a88b2d3614e21760d1709866d2417b419d418e20e09055eb13b8e3b7e';g,h,b,z,c=pickle.loads(mp.read_bytes());PS.restore_bound_generated_precision_states(b,z);gp=mp.parent/'groups.pkl';groups=pickle.loads(gp.read_bytes());lg=root(groups['/LOGIC_GND'],'J11001','2');keys={(q['kind'],q['uuid'],q['layer'])for q in lg if q['kind']!='fill'};vias={v['uuid']:v for v in h['vias']};sp=vias['c68f8d3c-e3bc-4deb-ad5f-9208c48cd820'];tp=vias['1fc85fd7-343f-4eef-968f-235ed3564d01'];assert all(v['net']=='/LOGIC_GND'and(v['d'],v['drill'])==(.6,.3)for v in(sp,tp));assert all(('via',v['uuid'],l)in keys for v in(sp,tp)for l in('In1.Cu','In4.Cu'))
 endpoint=[];groundvias=[v for v in h['vias']if v['net']=='/LOGIC_GND'and any(('via',v['uuid'],l)in keys for l in('In1.Cu','In4.Cu'))]
 for p in h['pads']:
  if p['net']!='/LOGIC_GND'or p['ref']not in({'U1001','U2001','C2002'}|{'C'+str(n)for n in range(1001,1010)}|{'C'+str(n)for n in range(1024,1028)}):continue
  near=sorted(groundvias,key=lambda v:math.dist([v['x'],v['y']],[p['x'],p['y']]))[:3];endpoint.append({'ref':p['ref'],'pin':p['num'],'UUID':p['uuid'],'at':[p['x'],p['y']],'actual_pad_layers':list(p['layers']),'actual_J1_rooted_layer_keys':[l for l in p['layers']if('pad',p['uuid'],l)in keys],'nearest_actual_source_ground_barrels':[{'UUID':v['uuid'],'at':[v['x'],v['y']],'distance_mm':math.dist([v['x'],v['y']],[p['x'],p['y']]),'actual_rooted_layers':[l for l in v['flashed']if('via',v['uuid'],l)in keys]}for v in near],'short_local_pad_to_barrel_current_path_and_GND_pin_potential_NOT_inferred_from_global_membership':True})
 put(O/'literal-regulator-FPGA-decoupler-ground-endpoints.json',endpoint)
 # Conservative voids: every actual native/new drill is circumscribed and
 # includes an explicit 20nm construction reserve; no barrel centre is Cu.
 clip=box(150,60,255,130);holes=[GP.bounded_disk(v,v['drill']/2+.00000002)for v in h['vias']if clip.distance(Point(v['x'],v['y']))<v['drill']/2]+[sh.buffer(.00000002)for p in h['pads']for sh in C.poly(p.get('hole')or[])if sh.intersects(clip)];holes=unary_union(holes)
 def ann(v):return Point(v['x'],v['y']).buffer(v['d']/2-.00000002,quad_segs=128).difference(GP.bounded_disk(v,v['drill']/2+.00000002))
 sa,ta=ann(sp),ann(tp);rows=[];terminal_rows=[]
 for layer in('In1.Cu','In4.Cu'):
  shape=unary_union([q['shape']for q in lg if q['layer']==layer]).intersection(clip).difference(holes);f=O/(layer+'-exact-source-rooted-region-physical.wkb');f.write_bytes(shape.wkb);ss=sa.intersection(shape);tt=ta.intersection(shape);terminal_rows.append({'layer':layer,'source_actual_annular_Cu_mm2':ss.area,'target_actual_annular_Cu_mm2':tt.area,'sheet_WKB_sha256':sha(f),'regional_boundary_mm':[150,60,255,130],'omitted_outside_regional_and_other_layer_parallel_copper_is_not_credited':True})
  for step in(.075,.05,.0375):
   margin=step/math.sqrt(2)+.00000002;inset=shape.buffer(-margin);x0,y0,x1,y1=shape.bounds;xx=np.arange(math.floor(x0/step)*step+step/2,x1,step);yy=np.arange(math.floor(y0/step)*step+step/2,y1,step);X,Y=np.meshgrid(xx,yy);mask=shapely.contains_xy(inset,X,Y);labels,ncomp=label(mask,np.array([[0,1,0],[1,1,1],[0,1,0]]));sm=mask&shapely.contains_xy(ss.buffer(-margin),X,Y);components=set(labels[sm])-{0};tm=mask&shapely.contains_xy(tt.buffer(-margin),X,Y)
   if not components or not (tm&np.isin(labels,list(components))).any():
    row={'layer':layer,'cell_size_mm':step,'conservative_source_annulus_cells':int(sm.sum()),'conservative_target_annulus_cells':int(tm.sum()),'regional_full_cell_same_layer_path':False,'this_does_not_prove_global_or_cross_layer_no_path':True};rows.append(row);put(O/'checkpoint.json',rows);print('R248_RETURN_NO_CONTAINED_PATH',json.dumps(row),flush=True);continue
   mask&=np.isin(labels,list(components));sm&=mask;tm&=mask;idx=np.full(mask.shape,-1,dtype=np.int64);idx[mask]=np.arange(mask.sum());sx=idx[sm];tx=idx[tm];n=int(mask.sum());edges=[]
   for ax in(0,1):
    aa,bb=(idx[:-1,:],idx[1:,:])if ax==0 else(idx[:,:-1],idx[:,1:]);ok=(aa>=0)&(bb>=0);edges.append((aa[ok],bb[ok]))
   aa=np.concatenate([v[0]for v in edges]);bb=np.concatenate([v[1]for v in edges]);degree=np.bincount(np.concatenate([aa,bb]),minlength=n).astype(float);A=coo_matrix((np.concatenate([degree,-np.ones(len(aa)),-np.ones(len(bb))]),(np.concatenate([np.arange(n),aa,bb]),np.concatenate([np.arange(n),bb,aa]))),shape=(n,n)).tocsr();fixed=np.unique(np.concatenate([sx,tx]));unknown=np.setdiff1d(np.arange(n),fixed);rhs=np.asarray(-A[unknown][:,tx].sum(axis=1)).ravel();u=np.zeros(n);u[tx]=1.;started=time.monotonic();u[unknown]=spsolve(A[unknown][:,unknown].tocsc(),rhs);flux=A@u;resid=float(np.max(np.abs(flux[unknown])));forward=float(flux[tx].sum());reverse=float(-flux[sx].sum());assert forward>0 and resid<1e-7 and abs(forward-reverse)<1e-7
   sq=1/forward;rho=1.7241e-8*(1+.00393*(125-20));row={'layer':layer,'cell_size_mm':step,'contained_cells':n,'whole_actual_source_annular_cells':len(sx),'whole_actual_target_annular_cells':len(tx),'regional_full_cell_same_layer_path':True,'effective_sheet_squares':sq,'source_sink_KCL_residual':abs(forward-reverse),'max_equation_residual':resid,'solve_seconds':time.monotonic()-started,'conditional_25um_125C_sheet_R_ohm':sq*rho/(25e-6),'full_0p8A_this_return_sheet_drop_V':.8*sq*rho/(25e-6),'actual_barrels_local_F_or_B_fanout_other_load_ground_gradient_and_return_pin_potential_not_included':True,'each_layer_case_uses_FULL_0p8A_not_equal_parallel_sharing':True};rows.append(row);put(O/'checkpoint.json',rows);print('R248_RETURN_SHEET',json.dumps(row),flush=True)
  del X,Y,mask,labels
 put(O/'literal-actual-return-ports.json',{'source':sp,'target':tp,'nearest_CORE_port_ground_role_only_not_actual_FPGA_or_U2001_terminal_substitution':True,'source_actual_original_record':next(v for v in g['vias']if v['uuid']==sp['uuid']),'target_actual_original_record':next(v for v in g['vias']if v['uuid']==tp['uuid']),'layer_annular_rows':terminal_rows})
 put(O/'receipt.json',{'verdict':'ACTUAL_SOURCE_ROOTED_REGIONAL_RETURN_SHEET_PARTIAL_NUMERICS_LOCAL_FULL_LOOP_OPEN','model_sha256':sha(mp),'groups_sha256':sha(gp),'ground_endpoint_rows':len(endpoint),'return_rows':rows,'ports_sha256':sha(O/'literal-actual-return-ports.json'),'endpoint_ledger_sha256':sha(O/'literal-regulator-FPGA-decoupler-ground-endpoints.json'),'full_0p8A_CORE_2A_IO3_retained':True,'literal_source_ground_GND4_vs_FPGA_all_GND_pins_shared_current_potential_barrels_and_supply_old_In3_fanout_decap_loop_ESL_transients_native_full_loop':'OPEN','no_equal_current_sharing_fixed_via_rating_or_zero_return_ASSUMPTION':True,'no_known_raw_reference_ledger_changed_or_waived':True,'board_written':False,'native_jobs':0,'script_sha256':sha(__file__)})
 print('R248_COMPLETE',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
