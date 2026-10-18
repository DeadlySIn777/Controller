"""Actual layered contact network, conditional sheet/barrel DC numerics only."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
pr=psutil.Process();pr.cpu_affinity(list(range(16,28)));pr.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,time,math,gc,hashlib,sys
from pathlib import Path
import numpy as np
import shapely
from scipy.sparse import coo_matrix,save_npz
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu
from inventory import sha
H=Path(__file__).resolve().parent;IN=H/'R100-contained-real-barrel-3D-mesh-r273';O=H/'R100-real-barrel-3D-return-current-r274';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'];Z=[.0175,.2725,.6375,.8925,1.2575,1.5125];CU=35.;PLATING=20.;TEMP=60.;RS=1.724e-8*(1+.00393*(TEMP-20))/(CU*1e-6);POSITIVE=4.816879372438923
def write(p,v):p.write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
class UF:
 def __init__(self,n):self.p=np.arange(n)
 def find(self,i):
  while self.p[i]!=i:self.p[i]=self.p[self.p[i]];i=int(self.p[i])
  return i
 def union(self,ids):
  if not len(ids):return
  base=self.find(int(ids[0]))
  for i in ids:
   root=self.find(int(i));self.p[root]=base
def main():
 assert not O.exists();O.mkdir();ir=json.loads((IN/'receipt.json').read_text());assert ir['R100_model_sha256']=='db01ba8f89c614c72b19688ec6479c96e8524259f1968eaa2dd3f2caeef49635';ports=pickle.loads((IN/'ports.pkl').read_bytes());assert sha(IN/'ports.pkl')==ir['port_pickle_sha256'];pby={p['UUID']:p for p in ports};rows=[];cols=[];values=[];meshes={};electrodes={};count=0;missing=[];summaries=[]
 for layer in LAYERS:
  T=np.load(IN/(layer.replace('.','-')+'-triangles.npy'));coords,inverse=np.unique(T.reshape(-1,2),axis=0,return_inverse=True);nodes=inverse.reshape(-1,3);uf=UF(len(coords));local={};xx,yy=coords[:,0],coords[:,1]
  for port in ports:
   q=port['layer_contact_shapes'].get(layer)
   if q is None:continue
   x0,y0,x1,y1=q.bounds;inside=(xx>=x0)&(xx<=x1)&(yy>=y0)&(yy<=y1);ids=np.flatnonzero(inside);ids=ids[shapely.intersects_xy(q,xx[ids],yy[ids])]
   if not len(ids):missing.append({'UUID':port['UUID'],'kind':port['kind'],'ref':port.get('ref'),'pin':port.get('pin'),'layer':layer,'reason':'NO_CONTAINED_MESH_VERTEX_IN_LITERAL_CONTACT'});continue
   local[port['UUID']]=ids;uf.union(ids)
  roots=np.array([uf.find(i) for i in range(len(coords))]);_,compact=np.unique(roots,return_inverse=True);ndof=int(compact.max()+1);dofs=compact[nodes]+count
  for uid,ids in local.items():electrodes[uid,layer]=int(compact[ids[0]]+count)
  v=T;det=(v[:,1,0]-v[:,0,0])*(v[:,2,1]-v[:,0,1])-(v[:,2,0]-v[:,0,0])*(v[:,1,1]-v[:,0,1]);area=np.abs(det)/2;assert np.all(area>1e-20),('degenerate mesh triangle',layer,float(area.min()));grad=np.stack([np.c_[v[:,1,1]-v[:,2,1],v[:,2,0]-v[:,1,0]],np.c_[v[:,2,1]-v[:,0,1],v[:,0,0]-v[:,2,0]],np.c_[v[:,0,1]-v[:,1,1],v[:,1,0]-v[:,0,0]]],axis=1)/det[:,None,None];K=area[:,None,None]*np.einsum('tik,tjk->tij',grad,grad);active=~((dofs[:,0]==dofs[:,1])&(dofs[:,1]==dofs[:,2]));rows.append(np.repeat(dofs[active],3,axis=1).reshape(-1));cols.append(np.tile(dofs[active],(1,3)).reshape(-1));values.append(K[active].reshape(-1));meshes[layer]={'dofs':dofs,'K':K,'grad':grad,'area':area,'centres':T.mean(axis=1)};count+=ndof;summary={'layer':layer,'triangles':len(T),'unique_vertices':len(coords),'after_literal_electrode_collapse_dofs':ndof,'actual_contact_electrodes':len(local),'minimum_triangle_area_mm2':float(area.min())};summaries.append(summary);write(O/'assembly-checkpoint.json',summaries);print(json.dumps(summary),flush=True);del T,coords,inverse,nodes,roots,compact,uf;gc.collect()
 barrel=[];br=[];bc=[];bv=[]
 for port in ports:
  if not port['barrel_is_plated']:continue
  contact=[(i,electrodes[port['UUID'],l]) for i,l in enumerate(LAYERS) if (port['UUID'],l) in electrodes];diam=port['plated_hole_mm']*.001;t=PLATING*1e-6
  for (i,a),(j,b) in zip(contact,contact[1:]):
   length=(Z[j]-Z[i])*.001;R=1.724e-8*(1+.00393*(TEMP-20))*length/(math.pi*(diam*t+t*t));G=RS/R;assert a!=b and G>0;br.extend([a,b,a,b]);bc.extend([a,b,b,a]);bv.extend([G,G,-G,-G]);barrel.append({'UUID':port['UUID'],'kind':port['kind'],'ref':port.get('ref'),'pin':port.get('pin'),'a':a,'b':b,'layer_a':LAYERS[i],'layer_b':LAYERS[j],'nominal_path_mm':length*1000,'drill_mm':port['plated_hole_mm'],'conditional_R_ohm':R,'G_normalized':G})
 sheet=coo_matrix((np.concatenate(values),(np.concatenate(rows),np.concatenate(cols))),shape=(count,count)).tocsr();bar=coo_matrix((bv,(br,bc)),shape=(count,count)).tocsr();A=(sheet+bar).tocsr();source=next(p for p in ports if p.get('ref')=='J11003' and p.get('pin')=='2');sourceid=source['UUID'];ground=electrodes[sourceid,'F.Cu'];nc,components=connected_components(A,directed=False);keep=np.flatnonzero(components==components[ground]);keep=keep[keep!=ground];mapping=np.full(count,-1,dtype=np.int64);mapping[keep]=np.arange(len(keep));Ag=A[keep][:,keep].tocsc();assert np.all(Ag.diagonal()>0);write(O/'missing-literal-mesh-contact-electrodes.json',missing);write(O/'barrel-link-binding.json',barrel);save_npz(O/'normalized-sheet-matrix.npz',sheet);save_npz(O/'normalized-barrel-matrix.npz',bar);(O/'electrode-node-binding.pkl').write_bytes(pickle.dumps({'electrodes':electrodes,'source_UUID':sourceid,'source_F_node':ground,'component_labels':components,'kept_grounded_nodes':keep,'physical_ports':ports},protocol=5))
 loads=[]
 for p in ports:
  if p.get('ref')=='JD09' and p.get('pin') in ('A9','A10','A11','A12'):
   for l in ('F.Cu','B.Cu'):
    node=electrodes.get((p['UUID'],l));loads.append({'UUID':p['UUID'],'port':p['ref']+'.'+p['pin'],'layer':l,'node':node,'in_source_mesh_component':node is not None and components[node]==components[ground]})
 srcB=electrodes.get((sourceid,'B.Cu'));connect={'unknowns':len(keep),'all_components':int(nc),'kept_F_source_component_nodes':len(keep)+1,'missing_contact_electrode_count':len(missing),'load_ports':loads,'source_B_in_same_mesh':srcB is not None and components[srcB]==components[ground]};write(O/'actual-3D-contained-connectivity.json',connect);print(json.dumps(connect),flush=True)
 if not all(q['in_source_mesh_component'] for q in loads) or not connect['source_B_in_same_mesh']:
  write(O/'receipt.json',{'verdict':'CONTAINED_3D_CURRENT_SUBNETWORK_CONTACT_OR_TOPOLOGY_INCOMPLETE_NO_CURRENT_ACCEPTANCE','input_mesh_receipt_sha256':sha(IN/'receipt.json'),'R100_model_sha256':ir['R100_model_sha256'],'connectivity':connect,'native_jobs':0,'board_written':False,'adopted':False});return
 print('R274 factoring actual 3D',len(keep),Ag.nnz,flush=True);start=time.monotonic();fac=splu(Ag,permc_spec='MMD_AT_PLUS_A');rhs=np.zeros((len(keep),len(loads)+1))
 for i,q in enumerate(loads):rhs[mapping[q['node']],i]=1
 rhs[mapping[srcB],-1]=1;u=fac.solve(rhs);res=float(np.max(np.abs(Ag@u-rhs)));assert res<1e-6,('unit_current_equation_residual',res);full=np.zeros((count,len(loads)+1));full[keep]=u;scenarios=[]
 removed=shapely.from_wkb((H/'R100-contained-connector-parallel-current-review-r271/exact-removed-FAG-In2.wkb').read_bytes());nearnotch=removed.buffer(.5)
 for source_layer in ('F.Cu','B.Cu'):
  for i,q in enumerate(loads):
   v=full[:,i].copy()
   if source_layer=='B.Cu':v-=full[:,-1];v-=v[srcB]
   unitR=float(v[q['node']]);assert unitR>0;branch=[];maxb=None
   for e in barrel:
    amps=e['G_normalized']*(v[e['a']]-v[e['b']])*POSITIVE;row={k:e[k] for k in ['UUID','kind','ref','pin','layer_a','layer_b','nominal_path_mm','drill_mm','conditional_R_ohm']};row.update(current_A=amps,conditional_segment_Joule_loss_W=amps*amps*e['conditional_R_ohm']);branch.append(row)
    if maxb is None or abs(amps)>abs(maxb['current_A']):maxb=row
   layerrows=[];sheetenergy=0.
   for l,m in meshes.items():
    vl=v[m['dofs']];E=float(np.einsum('ti,tij,tj->',vl,m['K'],vl));assert E>-1e-7;E=max(E,0);sheetenergy+=E;gradient=np.einsum('ti,tij->tj',vl,m['grad']);J=np.linalg.norm(gradient,axis=1)*POSITIVE;near=shapely.intersects_xy(nearnotch,m['centres'][:,0],m['centres'][:,1]);layerrows.append({'layer':l,'conditional_sheet_Joule_loss_W':E*RS*POSITIVE**2,'maximum_numerical_triangle_sheet_current_A_per_mm':float(J.max()),'maximum_numerical_triangle_sheet_current_near_exact_notch_A_per_mm':float(J[near].max()) if near.any() else None})
   barrelpower=sum(r['conditional_segment_Joule_loss_W'] for r in branch);power=(sheetenergy*RS*POSITIVE**2)+barrelpower;expected=unitR*RS*POSITIVE**2;delta=abs(power-expected);assert delta<max(1e-6,expected*1e-5),(power,expected,delta);case={'source_port':'J11003.2','source_layer_contact':source_layer,'target_port':q['port'],'target_layer_contact':q['layer'],'stress_complete_positive_FA_cut_A':POSITIVE,'actual_signed_source_normal_A':4.584429372438923,'conditional_sheet_plus_all_real_barrel_R_ohm':unitR*RS,'conditional_stress_drop_V':unitR*RS*POSITIVE,'conditional_total_Joule_loss_W':expected,'conditional_all_barrel_Joule_loss_W':barrelpower,'maximum_absolute_barrel_segment_current':maxb,'power_KCL_energy_residual_W':delta,'sheet_layer_results':layerrows};scenarios.append(case);fname=O/(q['port'].replace('.','-')+'-'+q['layer'].replace('.','-')+'-source-'+source_layer.replace('.','-')+'-all-barrel-currents.json');write(fname,branch);write(O/'scenario-checkpoint.json',scenarios)
 write(O/'unit-current-responses.pkl.json',{'port_order':loads,'source_B_last_column':True,'matrix_unknowns':len(keep),'max_unit_equation_residual_A':res});np.savez_compressed(O/'unit-current-responses.npz',solution=full);rec={'verdict':'CONDITIONAL_R100_MAJOR_RETURN_CUT_ACTUAL_3D_SHEET_BARREL_NUMERICS_FULL_LOAD_THERMAL_NATIVE_GATES_OPEN','input_contained_mesh_receipt_sha256':sha(IN/'receipt.json'),'R100_model_sha256':ir['R100_model_sha256'],'full_signed146_port_receipt_sha256':ir['complete_signed146_port_receipt_sha256'],'complete_positive_FA_cut_A':POSITIVE,'actual_signed_FA_source_A':4.584429372438923,'numerical_Cu_um':CU,'numerical_plating_um':PLATING,'numerical_uniform_temperature_C':TEMP,'serialized_nominal_layer_copper_centres_mm':Z,'mesh_summaries':summaries,'physical_contact_ports':len(ports),'actual_layer_barrel_segments':len(barrel),'connectivity':connect,'unit_equation_residual_A':res,'factor_solve_elapsed_seconds':time.monotonic()-start,'stress_scenarios':scenarios,'unrooted_literal_current_endpoints':ir['unrooted_full_load_endpoints'],'separate_RTNs_sha256':ir['separate_RTN_physical_receipt_sha256'],'limits':['All original/new geometries are frozen; the explicitly contained numerical subset is not a board edit or native fill proof.','This solves the actual source/connector major-cut 3D subnetwork; all147 literal signed endpoint injections and internal RTN support are still required.','Worst all positive4.816879A at one connector contact is a stress screen; actual negative converter current is not used as capacity credit.','Electrode annuli/SMD contacts are equipotential mesh boundary conditions; solder/contact/pad spreading is not bounded.','Nominal layer height/Cu/plating/temperature and finite-element convergence/actual board thermal boundary remain unqualified.','No continuous-current, fault-current or manufacturing-readiness acceptance.'],'native_jobs':0,'board_written':False,'adopted':False,'continuous_current_thermal_qualified':False};write(O/'receipt.json',rec);print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'max_conditional_drop_V':max(q['conditional_stress_drop_V'] for q in scenarios),'max_barrel_segment_A':max(abs(q['maximum_absolute_barrel_segment_current']['current_A']) for q in scenarios),'worst_energy_residual_W':max(q['power_KCL_energy_residual_W'] for q in scenarios)}),flush=True)
if __name__=='__main__':main()
