"""Exact CM sparse operations on FIELD5 successor, no older model overlay."""
from pathlib import Path
P=Path(__file__).resolve().parent
t=(P/'construct_CM_sparse_only_new_role_withdrawal_r283.py').read_text()
t=t.replace('CM-sparse-exact-current-R364-only-new-role-withdrawal-inherited-fills-FAIL-r283','CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289')
t=t.replace("s=s.replace('R279','R283')", "s=s.replace('R279','R289')")
needle="exec(compile(s,str(__file__),'exec'))"
replacement="""s=s.replace('field-power/REG-U25-DIC-SBC273-two-new-REG-actual-fill-margin-repair-r364/model.pkl','field-power/FIELD5-R385-minimal-R155-strict-filled-restoration-composition-r393/model.pkl')
s=s.replace('a39e7784abf8969b7f68176555b2c37b5227981cbc615c4bd542205e410373ad','df3e75059ea013087ddd8481e1f5bfe79e7915c2c3b4f34e2eaf1de9864acc13')
s=s.replace('d2d09cda7df82496860d7089cf0acb551e622596c9686f8d40b93181c0fd7a36','98298ff2774d8507e7edb24ed568c6f4af8f6db02a14938c8037a4bd97e13e0b')
exec(compile(s,str(__file__),'exec'))"""
assert t.count(needle)==1;t=t.replace(needle,replacement)
exec(compile(t,str(__file__),'exec'))
