"""Exact rooted signed-simplex coefficients; missing physical choices stay open."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
pr=psutil.Process();pr.cpu_affinity(list(range(16,28)));pr.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math,gc,time,sys
from pathlib import Path
import numpy as np
import shapely
from scipy.sparse import load_npz
from scipy.sparse.linalg import splu
from inventory import sha
import solve_R100_real_barrel_3D_return_r274 as M
H=Path(__file__).resolve().parent;BASE=H/'R100-stable-contact-condensation-current-r276';O=H/'R100-rooted-signed-simplex-current-bound-r277';INPUT=H/'R100-full-signed-FA-return-mesh-input-r269';IN=H/'R100-contained-real-barrel-3D-mesh-r273';NET='/motherboard_motors/FIELD_GND'
def write(p,v):p.write_text(json.dumps(v,indent=1,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();r=json.loads((BASE/'receipt.json').read_text());b=pickle.loads((BASE/'electrode-node-binding.pkl').read_bytes());ledger=json.loads((INPUT/'receipt.json').read_text());electrodes=b['electrodes'];keep=b['kept_grounded_nodes'];ground=b['source_F_node'];components=b['component_labels'];portby={p['UUID']:p for p in b['physical_ports']};rows=json.loads((BASE/'barrel-link-binding.json').read_text());A=(load_npz(BASE/'normalized-sheet-matrix.npz')+load_npz(BASE/'normalized-barrel-matrix.npz')).tocsr();Ag=A[keep][:,keep].tocsc();mapping=np.full(A.shape[0],-1,np.int64);mapping[keep]=np.arange(len(keep));termrows=[];nodes=set();unmapped=[]
 for t in ledger['FA_terms']:
  if t['name']=='Actual external source return sink':continue
  options=[];missing=[]
  for e in t['eligible_physical_endpoints']:
   p=portby.get(e['physical_pad_uuid']);eps=[]
   if p is not None and e['raw_net'].replace('{slash}','/')==NET:
    for l in p['layer_contact_shapes']:
     n=electrodes.get((p['UUID'],l))
     if n is not None and components[n]==components[ground]:eps.append({'node':n,'ref':e['ref'],'pin':e['pin'],'UUID':p['UUID'],'layer':l});nodes.add(n)
   if eps:options.extend(eps)
   else:missing.append({k:e[k] for k in ['ref','pin','physical_pad_uuid','raw_net']})
  termrows.append({'name':t['name'],'signed_current_A':t['signed_current_a'],'kind':t['kind'],'rooted_feasible_electrode_options':options,'unresolved_physical_choices':missing,'all_original_choices_qualified_in_current_mesh':not missing})
  if missing:unmapped.append({'term':t['name'],'signed_current_A':t['signed_current_a'],'physical_choices':missing,'retained_conserved_rooted_options':len(options)})
 order=sorted(nodes-{ground});lookup={n:i for i,n in enumerate(order)};fac=splu(Ag,permc_spec='MMD_AT_PLUS_A');U=np.lib.format.open_memmap(O/'unit-current-coefficients.npy',mode='w+',dtype='float64',shape=(A.shape[0],len(order)));U[:]=0;resmax=0.
 for start in range(0,len(order),16):
  batch=order[start:start+16];rhs=np.zeros((len(keep),len(batch)))
  for i,n in enumerate(batch):rhs[mapping[n],i]=1
  u=fac.solve(rhs);res=float(np.max(np.abs(Ag@u-rhs)));assert res<1e-6,('unit residual',res);resmax=max(resmax,res);U[keep,start:start+len(batch)]=u;U.flush();print('R277 actual electrode columns',start+len(batch),'of',len(order),'residual',res,flush=True)
 # Unit sheet scaling includes finite actual layer-to-layer plated-barrel R.
 response=np.array([[e['G_normalized']*(U[e['a']]-U[e['b']]) for e in rows]])[0];voltage=np.asarray(U[order])*M.RS
 def envelopes(coeff):
  lo=np.zeros(coeff.shape[0]);hi=lo.copy();used=[];missing_current=0.
  for t in termrows:
   opts=t['rooted_feasible_electrode_options'];I=t['signed_current_A']
   if not opts:missing_current+=I;continue
   columns=[lookup[q['node']] for q in opts if q['node']!=ground];zero=any(q['node']==ground for q in opts);values=coeff[:,columns]*I if columns else np.zeros((len(lo),0))
   if zero:values=np.c_[values,np.zeros(len(lo))]
   assert values.shape[1];lo+=values.min(axis=1);hi+=values.max(axis=1);used.append(t['name'])
  return lo,hi,used,missing_current
 low,high,used,missing_current=envelopes(response);barbounds=[]
 for e,lo,hi in zip(rows,low,high):
  row={k:e[k] for k in ['UUID','kind','ref','pin','layer_a','layer_b','nominal_path_mm','drill_mm','conditional_R_ohm']};row.update(rooted_simplex_signed_current_interval_A=[float(lo),float(hi)],rooted_simplex_max_abs_current_A=float(max(abs(lo),abs(hi))),full_original_physical_choice_bound=False);barbounds.append(row)
 write(O/'all-real-barrel-rooted-simplex-current-bounds.json',barbounds);vlo,vhi,_,_=envelopes(voltage);voltagebounds=[{'node':n,'rooted_simplex_voltage_interval_V':[float(a),float(bb)]} for n,a,bb in zip(order,vlo,vhi)];write(O/'all-physical-electrode-rooted-simplex-voltage-bounds.json',voltagebounds)
 # Reconstruct the exact In2 numerical element indexing to expose the actual
 # current-density coefficient around the removed return notch.
 LAYERS=M.LAYERS;offset=0;notchgrad=None;notchrows=[]
 removed=shapely.from_wkb((H/'R100-contained-connector-parallel-current-review-r271/exact-removed-FAG-In2.wkb').read_bytes());near=removed.buffer(.5)
 for layer in LAYERS:
  T=np.load(IN/(layer.replace('.','-')+'-triangles.npy'));det0=(T[:,1,0]-T[:,0,0])*(T[:,2,1]-T[:,0,1])-(T[:,2,0]-T[:,0,0])*(T[:,1,1]-T[:,0,1]);T=T[np.abs(det0)/2>=1e-12];coords,inverse=np.unique(T.reshape(-1,2),axis=0,return_inverse=True);ni=inverse.reshape(-1,3);uf=M.UF(len(coords));xx,yy=coords[:,0],coords[:,1]
  for p in b['physical_ports']:
   q=p['layer_contact_shapes'].get(layer)
   if q is None:continue
   x0,y0,x1,y1=q.bounds;ids=np.flatnonzero((xx>=x0)&(xx<=x1)&(yy>=y0)&(yy<=y1));ids=ids[shapely.intersects_xy(q,xx[ids],yy[ids])];uf.union(ids)
  rr=np.array([uf.find(i) for i in range(len(coords))]);_,compact=np.unique(rr,return_inverse=True);ndof=int(compact.max()+1)
  if layer=='In2.Cu':
   centres=T.mean(axis=1);sel=shapely.intersects_xy(near,centres[:,0],centres[:,1]);tt=T[sel];ds=compact[ni[sel]]+offset;det=(tt[:,1,0]-tt[:,0,0])*(tt[:,2,1]-tt[:,0,1])-(tt[:,2,0]-tt[:,0,0])*(tt[:,1,1]-tt[:,0,1]);grad=np.stack([np.c_[tt[:,1,1]-tt[:,2,1],tt[:,2,0]-tt[:,1,0]],np.c_[tt[:,2,1]-tt[:,0,1],tt[:,0,0]-tt[:,2,0]],np.c_[tt[:,0,1]-tt[:,1,1],tt[:,1,0]-tt[:,0,0]]],axis=1)/det[:,None,None];v=np.asarray(U[ds]);gcoef=np.einsum('tic,tij->tjc',v-v[:,0,None,:],grad);lx,hx,_,_=envelopes(gcoef[:,0,:]);ly,hy,_,_=envelopes(gcoef[:,1,:]);upper=np.sqrt(np.maximum(np.abs(lx),np.abs(hx))**2+np.maximum(np.abs(ly),np.abs(hy))**2)
   for center,a,bb,c,d,e in zip(centres[sel],lx,hx,ly,hy,upper):notchrows.append({'triangle_centre_mm':center.tolist(),'rooted_simplex_sheet_current_X_interval_A_per_mm':[float(a),float(bb)],'rooted_simplex_sheet_current_Y_interval_A_per_mm':[float(c),float(d)],'conservative_component_enclosure_norm_A_per_mm':float(e),'unresolved_26mA_and_RTN_choices_not_credited':True})
  offset+=ndof
  if layer=='In2.Cu':break
 write(O/'exact-notch-neighbourhood-rooted-simplex-sheet-current-bounds.json',notchrows);write(O/'literal-term-to-actual-electrode-options.json',termrows);used_current=sum(t['signed_current_A'] for t in termrows if t['rooted_feasible_electrode_options']);source_expected=4.584429372438923;residual=source_expected-used_current;maxordinary=max((q for q in barbounds if q['kind']=='via'),key=lambda q:q['rooted_simplex_max_abs_current_A']);rec={'verdict':'ROOTED_SIGNED_SIMPLEX_CURRENT_ENVELOPE_NUMERICALLY_SOLVED_UNRESOLVED_PHYSICAL_CHOICES_BLOCK_FULL_LOAD_QUALIFICATION','R100_model_sha256':r['R100_model_sha256'],'R276_major_cut_receipt_sha256':sha(BASE/'receipt.json'),'complete_signed146_receipt_sha256':r['full_signed146_port_receipt_sha256'],'raw_net':NET,'normal_exact_source_sink_A':source_expected,'rooted_model_implicit_source_extraction_A':used_current,'explicit_missing_source_KCL_A':residual,'missing_singleton_positive_load_A':missing_current,'unresolved_literal_physical_choices':unmapped,'rooted_signed_terms_included_once':len(used),'nonnegative_simplex_vertex_extrema_per_term_then_Minkowski_sum':True,'unknown_weights_not_equal_sharing':True,'actual_boundary_electrode_columns':len(order),'max_unit_equation_residual_A':resmax,'conditional_physical_inputs':{'Cu_um':M.CU,'plating_um':M.PLATING,'uniform_Cu_temperature_C':M.TEMP,'manufacturing_guaranteed':False},'maximum_conditional_rooted_electrode_voltage_upper_V':float(vhi.max()),'maximum_conditional_rooted_ordinary_barrel_current_interval':maxordinary,'maximum_conditional_rooted_In2_notch_neighbourhood_sheet_current_norm_A_per_mm':max([q['conservative_component_enclosure_norm_A_per_mm'] for q in notchrows],default=None),'number_notch_neighbourhood_triangles':len(notchrows),'native_jobs':0,'board_written':False,'adopted':False,'full_original146_physical_current_paths_qualified':False,'full_normal_load_KCL_acceptance':False,'actual_new_annuli_current_thermal_native_qualification':False};write(O/'receipt.json',rec);print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'missing_KCL_A':residual,'max_ordinary':maxordinary,'notch_max_A_per_mm':rec['maximum_conditional_rooted_In2_notch_neighbourhood_sheet_current_norm_A_per_mm']},default=lambda x:x.item() if isinstance(x,np.generic) else str(x)),flush=True)
if __name__=='__main__':main()
