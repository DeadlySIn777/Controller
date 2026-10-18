"""Use the actual new signal port to find a legal return within the saved 1mm gate."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'diagnose_U10003_exact_paired_return_faces_r164.py';code=source.read_text()
code=code.replace('return-legal-faces-r164','new-signal-port-sub-mm-paired-return-faces-r177')
code=code.replace('U10003-sparse-current-ground-fault-construction-r153','U10003-preserved-branch-exact-two-port-reference-construction-r176')
code=code.replace('2d7b4c1ff29121e909602f9d76c89c02b4f7d8e5bb6d8a3f3bf5fad7fa1fd1d8','c13b478b0cea7b09a510c221913d3a4d0774fcc74042605c17d69b35b37a9d20')
old="def polys(s):return [s]if s.geom_type=='Polygon'else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon']"
new="def polys(s):return [s]if s.geom_type=='Polygon'and not s.is_empty else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon'and not p.is_empty]"
assert code.count(old)==1;code=code.replace(old,new)
needle="rows=[];allcandidates=[]";assert code.count(needle)==1
code=code.replace(needle,"new_sig=[v for v in h['vias']if v.get('prospective_not_native')and C.norm(v['net'])=='/motherboard_do/DOA_FLT_N_FIELD'];assert len(new_sig)==1;ports=new_sig;rows=[];allcandidates=[]")
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
