"""Stable exact equipotential element condensation; explicit numeric subset loss."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'solve_R100_real_barrel_3D_return_r274.py').read_text(encoding='utf-8')
s=s.replace("O=H/'R100-real-barrel-3D-return-current-r274'","O=H/'R100-stable-contact-condensation-current-r276'")
s=s.replace('json.dumps(v,indent=1)',"json.dumps(v,indent=1,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))")
s=s.replace('json.dumps(connect)',"json.dumps(connect,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))")
old="  T=np.load(IN/(layer.replace('.','-')+'-triangles.npy'));coords,inverse=np.unique(T.reshape(-1,2),axis=0,return_inverse=True);nodes=inverse.reshape(-1,3);uf=UF(len(coords));local={};xx,yy=coords[:,0],coords[:,1]"
new="""  T=np.load(IN/(layer.replace('.','-')+'-triangles.npy'));det0=(T[:,1,0]-T[:,0,0])*(T[:,2,1]-T[:,0,1])-(T[:,2,0]-T[:,0,0])*(T[:,1,1]-T[:,0,1]);a0=np.abs(det0)/2;omit=a0<1e-12;np.save(O/(layer.replace('.','-')+'-explicit-omitted-numerical-triangles.npy'),T[omit]);write(O/(layer.replace('.','-')+'-numeric-subset-loss.json'),{'minimum_admitted_triangle_mm2':1e-12,'omitted_count':int(omit.sum()),'omitted_area_mm2':float(a0[omit].sum()),'only_numerical_subnetwork_loss_no_board_geometry_edit':True});T=T[~omit];coords,inverse=np.unique(T.reshape(-1,2),axis=0,return_inverse=True);nodes=inverse.reshape(-1,3);uf=UF(len(coords));local={};xx,yy=coords[:,0],coords[:,1]"""
assert old in s;s=s.replace(old,new)
old="K=area[:,None,None]*np.einsum('tik,tjk->tij',grad,grad);active=~((dofs[:,0]==dofs[:,1])&(dofs[:,1]==dofs[:,2]));rows.append"
new="""K=area[:,None,None]*np.einsum('tik,tjk->tij',grad,grad);all_same=(dofs[:,0]==dofs[:,1])&(dofs[:,1]==dofs[:,2]);K[all_same]=0
  # With two identical electrode DOFs, the exact triangle energy is
  # area*|grad(N_unique)|^2*(V_unique-V_repeated)^2. Assemble that directly
  # instead of adding large cancelling stiffness entries.
  two=(~all_same)&((dofs[:,0]==dofs[:,1])|(dofs[:,0]==dofs[:,2])|(dofs[:,1]==dofs[:,2]));ti=np.flatnonzero(two)
  for it in ti:
   unique=2 if dofs[it,0]==dofs[it,1] else 1 if dofs[it,0]==dofs[it,2] else 0;repeat=0 if unique else 1;ge=area[it]*float(grad[it,unique]@grad[it,unique]);K[it]=0;K[it,unique,unique]=ge;K[it,repeat,repeat]=ge;K[it,unique,repeat]=-ge;K[it,repeat,unique]=-ge
  active=~all_same;rows.append"""
assert old in s;s=s.replace(old,new)
s=s.replace("gradient=np.einsum('ti,tij->tj',vl,m['grad'])","gradient=np.einsum('ti,tij->tj',vl-vl[:,0,None],m['grad'])")
s=s.replace("'mesh_summaries':summaries","'mesh_summaries':summaries,'explicit_tiny_numeric_triangle_loss':[json.loads((O/(l.replace('.','-')+'-numeric-subset-loss.json')).read_text()) for l in LAYERS],'prior_R275_failed_unit_residual_A':.15139168067061348,'two_equal_electrode_DOF_triangle_energy_condensation_is_algebraically_exact':True")
exec(compile(s,str(H/'solve_R100_real_barrel_3D_return_r274.py'),'exec'))
