"""Freeze changed actual-fill proof; preserve final-writing error in R248."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent
src=H/'audit_CORE_R246_actual_R214_independent_r248.py'
dst=H/'audit_CORE_R250_actual_R214_independent_r252.py'
assert not dst.exists()
t=src.read_text()
for a,b in {
 'CORE-R246-vs-actual-R214-independent-r248':'CORE-R250-vs-actual-R214-independent-r252',
 'R248_':'R252_',
 'CORE_R246_VS_R214':'CORE_R250_VS_R214',
 'CORE-R112-per-polygon-immutable-owned-construction-r246':'CORE-R112-per-polygon-immutable-owned-construction-r250',
 'fd437ea4e5a9139eb4698598ba20f715bf357e841ba257f4f33dd7c1e76b7e82':'9de23083359b26f15e8d7b9f8e3692e940fec1ed1e8feb54015318eb45013a96',
 '32b60c225aa42347e3739c41d297c0f6047ee87978b42270958678fc6b51e685':'96d3f55a95b770a2a7f46e3b25274723946fe1572c6c82d81b7355b660360868',
 'R246_constructor_receipt_sha256':'R250_constructor_receipt_sha256',
 'R246_model_sha256':'R250_model_sha256',
 'R246_actual_filled_constructor_receipt_sha256':'R250_actual_filled_constructor_receipt_sha256',
 'R246_actual_filled_model_sha256':'R250_actual_filled_model_sha256',
}.items():
 assert a in t,a
 t=t.replace(a,b)
assert t.count("changed=A.read(frozen/'model.pkl')")==1
t=t.replace("changed=A.read(frozen/'model.pkl')","actualFilledRaw=A.read(frozen/'model.pkl')").replace('C.sha(changed)','C.sha(actualFilledRaw)').replace('pickle.loads(changed)','pickle.loads(actualFilledRaw)')
dst.write_text(t);compile(t,str(dst),'exec')
print(hashlib.sha256(dst.read_bytes()).hexdigest())
