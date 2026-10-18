"""Conditional field A output-return sheet drop; no fabricated qualification."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math,time
import numpy as np
import shapely
from shapely.geometry import Point
from shapely.ops import unary_union
from scipy.ndimage import label
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from contact_layout import HERE,poly,norm
from power_groups import ROOTS
from inventory import sha
OUT=HERE/'return-sheet-mesh-r1';STEP=.25;RS=.00057003672
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();gp=HERE/'composed-field-geometry-r3/geometry.pkl';r=json.loads((gp.parent/'receipt.json').read_text(encoding='utf-8'));assert sha(gp)==r['geometry_sha256'];g=pickle.loads(gp.read_bytes());groups=pickle.loads((gp.parent/'ground-groups.pkl').read_bytes());gs=groups['FAG'];root=next(xs for xs in gs if any(q['kind']=='pad' and (q['ref'],q['pin'])==ROOTS['FAG'] for q in xs));source=next(p for p in g['pads'] if (p['ref'],p['num'])==ROOTS['FAG']);target={p['num']:p for p in g['pads'] if p['ref']=='JD09' and p['num'] in ['A9','A10','A11','A12']};assert len(target)==4
 holes=unary_union([h for p in g['pads'] for h in poly(p.get('hole') or [])]+[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=32) for v in g['vias']]);rows=[]
 for layer in ['In1.Cu','In4.Cu','In2.Cu']:
  copper=unary_union([q['shape'] for q in root if q['layer']==layer]).difference(holes)
  # A contained square subset is used. No cell crossing a copper boundary
  # or any drilled hole is admitted just because its center is conductive.
  inset=copper.buffer(-STEP/math.sqrt(2)-.00001);x0,y0,x1,y1=inset.bounds;xx=np.arange(math.floor(x0/STEP)*STEP+STEP/2,x1,STEP);yy=np.arange(math.floor(y0/STEP)*STEP+STEP/2,y1,STEP);X,Y=np.meshgrid(xx,yy);mask=shapely.contains_xy(inset,X,Y);lab,_=label(mask,np.array([[0,1,0],[1,1,1],[0,1,0]]));sourcepoly=unary_union(poly(source['layers'][layer])).difference(holes);sm=mask & shapely.contains_xy(sourcepoly,X,Y);srcids=set(lab[sm])- {0};assert srcids,(layer,'No discretized source annular contact');mask &= np.isin(lab,list(srcids));sm &=mask;idx=np.full(mask.shape,-1,dtype=np.int64);idx[mask]=np.arange(mask.sum());sx=idx[sm];n=int(mask.sum());flatX=X[mask];flatY=Y[mask]
  edges=[]
  for axis in [0,1]:
   if axis==0:a=idx[:-1,:];b=idx[1:,:]
   else:a=idx[:,:-1];b=idx[:,1:]
   ok=(a>=0)&(b>=0);edges.append((a[ok],b[ok]))
  aa=np.concatenate([a for a,b in edges]);bb=np.concatenate([b for a,b in edges]);degree=np.bincount(np.concatenate([aa,bb]),minlength=n).astype(float);A=coo_matrix((np.concatenate([degree,-np.ones(len(aa)),-np.ones(len(bb))]),(np.concatenate([np.arange(n),aa,bb]),np.concatenate([np.arange(n),bb,aa]))),shape=(n,n)).tocsr();print(layer,'cells',n,'sourcecells',len(sx),flush=True)
  for pin,pad in target.items():
   targetpoly=unary_union(poly(pad['layers'][layer])).difference(holes);tm=mask & shapely.contains_xy(targetpoly,X,Y);tx=idx[tm];assert len(tx),(layer,pin,'No discretized target contact');fixed=np.unique(np.concatenate([sx,tx]));unknown=np.setdiff1d(np.arange(n),fixed);b=np.asarray(-A[unknown][:,tx].sum(axis=1)).ravel();start=time.monotonic();u=np.zeros(n);u[tx]=1.;u[unknown]=spsolve(A[unknown][:,unknown].tocsc(),b);residual=np.max(np.abs((A@u)[unknown]));I=float(np.sum((A@u)[tx])/RS);assert I>0 and residual<1e-7;R=1/I
   row={'layer':layer,'return_terminal':'JD09.'+pin,'real_source':'J11003.2','cell_size_mm':STEP,'contained_sheet_cells':n,'source_annular_contact_cells':len(sx),'target_annular_contact_cells':len(tx),'sheet_resistance_ohm':R,'mesh_equation_max_residual':residual,'elapsed_seconds':time.monotonic()-start,'source_output_pad_annuli_equipotential_boundary_assumption':True,'plated_barrel_contact_and_board_thermal_not_in_sheet_solve':True,'all_native_drill_holes_removed':True,'Cu_um':35,'copper_temperature_C':60,'resistivity_m_ohm':RS*.000035};rows.append(row);print(layer,pin,'sheetR_mOhm',R*1000,flush=True);write(OUT/'checkpoint.json',rows)
 combinations=[]
 for pin in target:
  for layers in [['In1.Cu','In4.Cu'],['In1.Cu','In4.Cu','In2.Cu']]:
   branch=[q for q in rows if q['return_terminal']=='JD09.'+pin and q['layer'] in layers];G=sum(1/q['sheet_resistance_ohm'] for q in branch);R=1/G
   combinations.append({'return_terminal':'JD09.'+pin,'layers':layers,'parallel_sheet_R_ohm':R,'conditional_6p5A_copper_policy_sheet_drop_V':6.5*R,'conditional_4p816879A_full_positive_FA_groundcut_sheet_drop_V':4.81687937244*R,'sheet_drop_within_unchanged_0p48V_per_net_budget_at6p5A':6.5*R<=.48,'branch_current_at6p5A':{q['layer']:6.5/q['sheet_resistance_ohm']/G for q in branch},'branch_sheet_power_W_at6p5A':{q['layer']:(6.5/q['sheet_resistance_ohm']/G)**2*q['sheet_resistance_ohm'] for q in branch},'network_is_endpoint_parallel_only_existing_crosslayer_via_shortcuts_not_used':True})
 result={'verdict':'CONDITIONAL_PARTIAL_SHEET_MODEL','original_composed_geometry_sha256':sha(gp),'source_export_sha256':r['source_export_sha256'],'rows':rows,'endpoint_parallel_combinations':combinations,'stackup':'Existing nominal35um inner Cu; thickness tolerance, plating, interfaces and actual board temperature are not qualified.','cell_construction':'All cells contained in actual prospective root-connected Cu minus native holes via half-diagonal inward buffer; four-neighbor conductivity. One grid is a numerical model, not a convergence proof.','scope':'Existing source-rooted FAG output-return subnetwork, worst all cut current at each one of four actual return terminals. Full signed rail/other local loads, future CORE crossing carve and complete foreign continuity are not solved by this partial model.','future_CORE_field_mutual_change_requires_recompute':True,'native_jobs':0,'board_written':False,'continuous_current_thermal_qualification':False,'manufacturing_ready':False};write(OUT/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(OUT/'receipt.json'),'combinations':combinations}))
if __name__=='__main__':main()
