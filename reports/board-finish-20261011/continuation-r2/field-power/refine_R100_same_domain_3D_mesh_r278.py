"""Uniform midpoint refinement of the same explicitly contained R276 domain."""
from pathlib import Path
H=Path(__file__).resolve().parent
builder=(H/'solve_R100_stable_contact_condensation_r276.py').read_text(encoding='utf-8').split('exec(compile(s,')[0]
scope={'__file__':__file__,'__name__':'build_only'};exec(compile(builder,__file__,'exec'),scope);s=scope['s']
s=s.replace("O=H/'R100-stable-contact-condensation-current-r276'","O=H/'R100-same-domain-midpoint-refined-current-r278'")
old='T=T[~omit];coords,inverse=np.unique(T.reshape(-1,2),axis=0,return_inverse=True)'
new="T=T[~omit];p0,p1,p2=T[:,0],T[:,1],T[:,2];m01=(p0+p1)/2;m12=(p1+p2)/2;m20=(p2+p0)/2;T=np.concatenate([np.stack([p0,m01,m20],axis=1),np.stack([m01,p1,m12],axis=1),np.stack([m20,m12,p2],axis=1),np.stack([m01,m12,m20],axis=1)]);coords,inverse=np.unique(T.reshape(-1,2),axis=0,return_inverse=True)"
assert old in s;s=s.replace(old,new)
s=s.replace("'prior_R275_failed_unit_residual_A':.15139168067061348", "'prior_R275_failed_unit_residual_A':.15139168067061348,'uniform_midpoint_refinement_of_same_contained_domain':True,'coarse_R276_receipt_sha256':sha(H/'R100-stable-contact-condensation-current-r276/receipt.json')")
exec(compile(s,str(H/'solve_R100_real_barrel_3D_return_r274.py'),'exec'))
