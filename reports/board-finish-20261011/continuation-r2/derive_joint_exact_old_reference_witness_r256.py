"""Rebind and exactly classify the six raw witness polygons on R253."""
from pathlib import Path
import hashlib,json,runpy
H=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=H/'bind_U10003_all_source_exact_bbox_reference_witness_r216.py';code=source.read_text().replace('binding-r216','binding-r256').replace('construction-r196','THIS_DOES_NOT_EXIST')
code=code.replace("H/'U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-THIS_DOES_NOT_EXIST/model.pkl'","H/'U10003-HOST-field-joint-current-exact-raw-precision-bound-r253/model.pkl'")
code=code.replace('dfb8050d5f45f5602692f2f4bb11c4706937a7821d57fac55a6733042314cae5','765ce30b24ed3109b7c938f964775690a99f08504c464313bcf712b078421440')
needle="_,groups=K.physical(m,'/motherboard_motors/FIELD_GND',K.hole_context(m));root=K.root(groups,'J11003','2')";assert code.count(needle)==1
replacement="""cachefile=H/'U10003-HOST-joint-independent-actual-source-contacts-oldrefs-r248/fresh-actual-drilled-affected-groups.pkl';assert sha(cachefile)=='642a32fe670eb21b4675a3d898a1ee56e6afb73e6921b16a43804f5a4f5edfc1'
  oldcurrent=H/'U10003-HOST-field-joint-current-exact-raw-precision-bound-r247/model.pkl';assert sha(oldcurrent)=='9b5ce5fcc6fcf741f73ba48cd15ab396a022115ba7110ee3d4c7fc27459cbf86';prior=pickle.loads(oldcurrent.read_bytes())[4]
  assert after['vias']==prior['vias']and after['pads']==prior['pads']
  for kind in('tracks','vias','pads','zones'):assert [x for x in after[kind]if K.L.norm(x['net'])=='/motherboard_motors/FIELD_GND']==[x for x in prior[kind]if K.L.norm(x['net'])=='/motherboard_motors/FIELD_GND']
  cache=pickle.loads(cachefile.read_bytes());groups=cache['/motherboard_motors/FIELD_GND'][0 if label=='before'else1];root=K.root(groups,'J11003','2')"""
replacement=replacement.replace("else1","else 1")
code=code.replace(needle,replacement).replace("bp,mp,wp]","bp,mp,wp,cachefile,oldcurrent]").replace('R216','R256')
target=H/'bind_U10003_joint_all_source_exact_bbox_witness_r256.py';assert not target.exists();compile(code,str(target),'exec');target.write_text(code);runpy.run_path(str(target),run_name='__main__')
rp=H/'U10003-all-source-exact-bbox-reference-witness-binding-r256/receipt.json';source2=H/'audit_U10003_all_source_exact_rational_arrangement_r217.py';c=source2.read_text().replace('arrangement-r217','arrangement-r257').replace('binding-r216','binding-r256').replace('61ba472cb0f172bed2296c3697285e1bb7a865cb6db8c8bd13764140ce66a81d',sha(rp));target2=H/'audit_U10003_joint_all_source_exact_rational_arrangement_r257.py';assert not target2.exists();compile(c,str(target2),'exec');target2.write_text(c);runpy.run_path(str(target2),run_name='__main__')
