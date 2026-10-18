"""Preserve R274's NumPy-bool serialization failure; numeric model unchanged."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'solve_R100_real_barrel_3D_return_r274.py').read_text(encoding='utf-8')
s=s.replace("O=H/'R100-real-barrel-3D-return-current-r274'","O=H/'R100-real-barrel-3D-return-current-r275'")
s=s.replace('json.dumps(v,indent=1)',"json.dumps(v,indent=1,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))")
s=s.replace('json.dumps(connect)',"json.dumps(connect,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))")
exec(compile(s,str(H/'solve_R100_real_barrel_3D_return_r274.py'),'exec'))
