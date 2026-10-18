"""Contained post-notch sheet solves; complete endpoint/RTN gates stay explicit."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math,time,hashlib,gc
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point
from shapely.ops import unary_union
from scipy.ndimage import label
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu
from inventory import sha
import contact_layout as C
H=Path(__file__).resolve().parent;ROOT=H.parent;IN=H/'R100-full-signed-FA-return-mesh-input-r269';O=H/'R100-contained-connector-parallel-current-review-r271'
POSITIVE=4.816879372438923;SIGNED=4.584429372438923
def write(p,v):p.write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def digest(g):return hashlib.sha256(g.wkb).hexdigest()
def solve(shape,layer,step,ports,holes,variant,cutshape):
 start=time.monotonic();inset=shape.buffer(-step/math.sqrt(2)-.00000002);x0,y0,x1,y1=shape.bounds;xx=np.arange(math.floor(x0/step)*step+step/2,x1,step);yy=np.arange(math.floor(y0/step)*step+step/2,y1,step);X,Y=np.meshgrid(xx,yy);mask=shapely.contains_xy(inset,X,Y);labels,_=label(mask,np.array([[0,1,0],[1,1,1],[0,1,0]]));sourcepoly=unary_union(C.poly(ports['J11003.2']['pin_layers_polygons'][layer])).difference(holes);sm=mask&shapely.contains_xy(sourcepoly,X,Y);source_labels=set(labels[sm])-{0}
 if not source_labels:return {'variant':variant,'layer':layer,'step_mm':step,'status':'NO_CONTAINED_ACTUAL_SOURCE_ANNULUS','geometry_sha256':digest(shape)}
 mask &=np.isin(labels,list(source_labels));sm &=mask;idx=np.full(mask.shape,-1,dtype=np.int64);idx[mask]=np.arange(mask.sum());n=int(mask.sum());port_ids={};targetlabels={};missing=[]
 for name,port in ports.items():
  if name=='J11003.2':continue
  q=unary_union(C.poly(port['pin_layers_polygons'][layer])).difference(holes);tm=mask&shapely.contains_xy(q,X,Y);port_ids[name]=idx[tm];targetlabels[name]=sorted(set(labels[tm])-{0})
  if not len(port_ids[name]):missing.append(name)
 if missing:return {'variant':variant,'layer':layer,'step_mm':step,'status':'SOURCE_LAYER_CONTAINED_SUBNETWORK_MISSES_TARGETS','missing_targets':missing,'contained_source_annular_cells':int(sm.sum()),'source_connected_cells':n,'geometry_sha256':digest(shape)}
 # Collapse each actual connector annulus to one explicitly equipotential
 # boundary electrode. No mesh edge crosses an excluded square or a drill.
 remap=np.arange(n)+5;remap[idx[sm]]=0
 for i,name in enumerate(port_ids,1):remap[port_ids[name]]=i
 _,compressed=np.unique(remap,return_inverse=True);ground=int(compressed[idx[sm][0]]);assert ground==0
 edges=[]
 for axis in (0,1):
  aa,bb=(idx[:-1,:],idx[1:,:]) if axis==0 else (idx[:,:-1],idx[:,1:]);ok=(aa>=0)&(bb>=0);edges.append((aa[ok],bb[ok]))
 aa=np.concatenate([e[0] for e in edges]);bb=np.concatenate([e[1] for e in edges]);a=compressed[aa];bbmap=compressed[bb];count=int(compressed.max()+1);rows=np.r_[a,bbmap,a,bbmap];cols=np.r_[a,bbmap,bbmap,a];values=np.r_[np.ones(2*len(a)),-np.ones(2*len(a))];A=coo_matrix((values,(rows,cols)),shape=(count,count)).tocsr()[1:,1:];portnodes={name:int(compressed[ids[0]])-1 for name,ids in port_ids.items()};rhs=np.zeros((count-1,len(portnodes)))
 for i,node in enumerate(portnodes.values()):rhs[node,i]=1
 print(variant,layer,step,'contained',n,'unknowns',count-1,'factorizing',flush=True);fac=splu(A.tocsc());u=fac.solve(rhs);res=float(np.max(np.abs(A@u-rhs)));assert res<1e-7;full=np.vstack([np.zeros((1,u.shape[1])),u]);voltage=full[compressed];R=np.array([[u[node,j] for j in range(len(portnodes))] for node in portnodes.values()]);assert np.all(np.diag(R)>0);injection=0;calc=[]
 # Mesh is unit sheet resistance. Real rho/thickness scaling is applied later.
 midx=(X[mask][aa]+X[mask][bb])/2;midy=(Y[mask][aa]+Y[mask][bb])/2;nearcut=shapely.intersects_xy(cutshape.buffer(.5),midx,midy);edgeI=voltage[aa]-voltage[bb]
 for i,name in enumerate(portnodes):
  source_flux=float(np.sum(np.where(a==0,-edgeI[:,i],0)+np.where(bbmap==0,edgeI[:,i],0)));assert abs(source_flux-1)<1e-7
  calc.append({'target':name,'effective_sheet_squares':float(R[i,i]),'source_KCL_residual_for_1A':abs(source_flux-1),'max_abs_sheet_edge_current_A_for_1A':float(np.max(np.abs(edgeI[:,i]))),'max_abs_edge_A_per_mm_for_1A':float(np.max(np.abs(edgeI[:,i]))/step),'max_abs_edge_A_per_mm_near_notch_for_1A':float(np.max(np.abs(edgeI[nearcut,i]))/step) if nearcut.any() else None,'actual_target_annular_contained_cells':len(port_ids[name])})
 row={'variant':variant,'layer':layer,'step_mm':step,'status':'CONDITIONAL_CONTAINED_SHEET_SOLVED','geometry_sha256':digest(shape),'contained_square_cells':n,'reduced_unknowns':count-1,'source_annular_contained_cells':int(sm.sum()),'target_rows':calc,'port_order':list(portnodes),'four_port_transfer_sheet_squares':R.tolist(),'equation_residual_A_for_1A':res,'elapsed_seconds':time.monotonic()-start,'all_cells_entirely_in_exact_R100_physical_Cu_minus_drills':True,'electrode_equipotential_is_numerical_boundary_only':True,'internal_existing_barrel_shortcuts_not_used':True};del fac,A,u,voltage,edgeI;gc.collect();return row
def main():
 assert not O.exists();O.mkdir();rec=json.loads((IN/'receipt.json').read_text());assert rec['model_sha256']=='db01ba8f89c614c72b19688ec6479c96e8524259f1968eaa2dd3f2caeef49635';ports={e['ref']+'.'+e['pin']:e for e in rec['physical_endpoint_rows'] if e['ref'] in ('JD09','J11003')};assert len(ports)==5;holes=shapely.from_wkb((IN/'own-physical-drill-voids.wkb').read_bytes());afterq=shapely.from_wkb((IN/'e2fe-after-notch-physical.wkb').read_bytes())
 parent=ROOT/'joint-positive-head-signal-reference-mask-proposal-r83/model.pkl';_,_,_,zp,_=pickle.loads(parent.read_bytes());beforeq=next(q['shape'] for q in zp if q['uuid']=='e2fe644a-2849-5c69-8ebb-d1e94909cd4c');assert digest(beforeq)=='26446bf9b029ef75f92dfe919f68a41432c0aa4f372efcd7b6115ee701fb2b68';removed=beforeq.difference(afterq);assert abs(removed.area-25.800423139024772)<1e-8;del zp;gc.collect();(O/'exact-removed-FAG-In2.wkb').write_bytes(removed.wkb);rows=[]
 for layer in ('In1.Cu','In4.Cu','In2.Cu'):
  shape=shapely.from_wkb((IN/(layer.replace('.','-')+'-physical-sheet.wkb')).read_bytes());variants=[('actual_post_notch_R100',shape)]
  if layer=='In2.Cu':variants.append(('notch_only_restored_sensitivity_not_board_candidate',unary_union([shape,removed]).difference(holes)))
  for variant,s in variants:
   for step in (.25,.125):
    row=solve(s,layer,step,ports,holes,variant,removed);rows.append(row);write(O/'checkpoint.json',rows);print(json.dumps({k:v for k,v in row.items() if k not in ['four_port_transfer_sheet_squares','target_rows']}),flush=True)
 cases=[]
 for step in (.25,.125):
  for pin in ('A10','A11','A12','A9'):
   for thickness in (35,25):
    for temp in (60,125):
     rho=1.724e-8*(1+.00393*(temp-20));sheet=rho/(thickness*1e-6);branches=[]
     for row in rows:
      if row['step_mm']!=step or row['variant']!='actual_post_notch_R100' or row['status']!='CONDITIONAL_CONTAINED_SHEET_SOLVED':continue
      t=next(t for t in row['target_rows'] if t['target']=='JD09.'+pin);branches.append((row,t,t['effective_sheet_squares']*sheet))
     G=sum(1/R for _,_,R in branches);R=1/G if G else None
     if R is None:continue
     share={row['layer']:POSITIVE/Ri/G for row,t,Ri in branches};cases.append({'step_mm':step,'target':'JD09.'+pin,'conditional_Cu_um':thickness,'conditional_uniform_Cu_temperature_C':temp,'stressed_positive_cut_A':POSITIVE,'actual_signed_source_A':SIGNED,'parallel_sheet_R_ohm':R,'positive_cut_sheet_drop_V':POSITIVE*R,'positive_cut_sheet_loss_W':POSITIVE**2*R,'calculated_layer_currents_A':share,'calculated_layer_sheet_loss_W':{row['layer']:share[row['layer']]**2*Ri for row,t,Ri in branches},'calculated_layer_peak_mesh_edge_A_per_mm':{row['layer']:share[row['layer']]*t['max_abs_edge_A_per_mm_for_1A'] for row,t,Ri in branches},'layer_branches_only_with_actual_contained_source_and_target_contacts':[row['layer'] for row,t,Ri in branches],'negative_buck_cancellation_not_used_as_capacity_credit':True})
 barrel=[]
 for plating in (20,25,30):
  for temp in (60,125):
   rho=1.724e-8*(1+.00393*(temp-20));values=[]
   for name in ('J11003.2','JD09.A10'):
    hp=unary_union(C.poly(ports[name]['physical_hole']));diameter=2*math.sqrt(hp.area/math.pi);t=plating*1e-6;Rb=rho*.0016/(math.pi*(diameter*.001*t+t*t));values.append({'port':name,'hole_equivalent_diameter_mm':diameter,'full_1p6mm_ideal_cylinder_R_ohm':Rb})
   Rb=sum(q['full_1p6mm_ideal_cylinder_R_ohm'] for q in values);barrel.append({'assumed_plating_um':plating,'assumed_Cu_temperature_C':temp,'plating_guaranteed':False,'common_series_full_length_connector_barrels':values,'positive_cut_common_barrel_drop_V':POSITIVE*Rb,'positive_cut_common_barrel_loss_W':POSITIVE**2*Rb,'interface_solder_contact_spreading_not_bounded':True})
 missing=[e for e in rec['physical_endpoint_rows'] if e['actual_same_field_ground_net'] and not e['root_connected']];RTN=[t for t in rec['FA_terms'] if any('RTN' in e['raw_net'] for e in t['eligible_physical_endpoints'])];r={'verdict':'EXACT_R100_CONDITIONAL_MAJOR_RETURN_CUT_NUMERICS_FULL_LOAD_QUALIFICATION_BLOCKED_BY_EXPLICIT_ENDPOINTS_RTN_AND_PHYSICAL_INPUTS','R100_model_sha256':rec['model_sha256'],'R100_receipt_sha256':rec['parent_receipt_sha256'],'exact_R98_route_receipt_sha256':rec['CORE_R98_route_receipt_sha256'],'exact_owned_remove_only_cut_ledger_sha256':rec['owned_remove_only_role_cuts_sha256'],'input_r269_receipt_sha256':sha(IN/'receipt.json'),'complete146_signed_port_receipt_sha256':rec['complete_signed146_term_receipt_sha256'],'signed_actual_source_A':SIGNED,'complete_positive_FA_cut_A':POSITIVE,'negative_converter_ground_A':-.23245,'exact_removed_FAG_In2_mm2':removed.area,'rows':rows,'parallel_current_sensitivity_cases':cases,'connector_common_full_barrel_sensitivity':barrel,'unrooted_literal_same_FAG_current_endpoints':[{k:e[k] for k in ['ref','pin','physical_pad_uuid','current_R100_pad_at_mm']} for e in missing],'separate_RTN_simplex_terms':RTN,'correction_to_r269_RTNs':'The R269 RTN_device_pin_screen used unrelated U11019–U11022 references and is not authoritative. This receipt replaces it with exact signed-source U11015/U11016 pins5/11; raw RTN/GND ports remain distinct.','limitations':['Major connector-return subnetwork only; internal cross-layer via shortcuts and all147 literal current injections are not solved here.','Concentrating the entire positive cut at one JD09 port is a deliberate stress screen, not a relocation of actual load current.','Contained finite grid omits real Cu; grid convergence and sheet temperature/plating tolerances are not manufacturing guarantees.','Two bare physical current endpoints and four distinct RTN support ports require concrete qualified paths before full-load acceptance.','No sheet drop alone proves continuous current or thermal capacity; board cooling/package/transient/interface gates remain open.'],'native_jobs':0,'board_written':False,'adopted':False,'continuous_current_thermal_qualified':False};write(O/'receipt.json',r);print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'conditional_cases':len(cases),'solved_rows':sum(q['status']=='CONDITIONAL_CONTAINED_SHEET_SOLVED' for q in rows),'maximum_conditional_parallel_sheet_drop_V':max([q['positive_cut_sheet_drop_V'] for q in cases],default=None)}),flush=True)
if __name__=='__main__':main()
