"""Correct additive inventory assertion; R372 failure stays intact, no native job ran."""
from pathlib import Path
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/attest_R371_new_LG_native_profile_only_clone_r372.py'
s=p.read_text(encoding='utf-8').replace('r372','r373').replace('R372','R373')
needle="assert out[0]==iv[0]and out[2]==iv[2]and out[4]==iv[4]"
assert s.count(needle)==1
s=s.replace(needle,"assert out[0]==iv[0]and out[2]==iv[2];assert set(out[4])==set(iv[4])|{row['UUID']for row in rows}and all(out[4][u]==ch for u,ch in iv[4].items());assert out[5]==iv[5]+[A.C.definition(zone.read_bytes())]")
exec(compile(s,str(__file__),'exec'))
