"""Repair only a frozen report wrapper; preserve R102 failed output."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;src=H/'nominate_DI15_ground_handoff_branches_r102.py';b=src.read_bytes();s=b.decode().replace('r102','r104')
s=s.replace("legal=pickle.loads(b)['reference_only_new_ground_legal'];raw38", "R80_geometry_sha256=C.sha(b);legal=pickle.loads(b)['reference_only_new_ground_legal'];raw38")
s=s.replace("'R80_legal_geometry_sha256':C.sha(b)", "'R80_legal_geometry_sha256':R80_geometry_sha256")
dst=H/'nominate_DI15_ground_handoff_branches_r104.py';assert not dst.exists();dst.write_text(s);compile(s,str(dst),'exec');out=H/'prepare-handoff-wrapper-r104.json';assert not out.exists();out.write_text(json.dumps({'source_sha256':hashlib.sha256(b).hexdigest(),'derived_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'delta':'Save R80 raw geometry SHA before the local interval variable b reuses its name; no geometric/predicate/source change. Original R102 failed after finding0 guarded branch sites, no receipt/operation/adoption.'},indent=1)+'\n');print(dst)
