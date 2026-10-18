"""Preserve strict three-segment limit while testing original B transport."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;src=H/'construct_DIC_CS_continuous_F_In3_F_r96.py';b=src.read_bytes();s=b.decode().replace("'In3.Cu'","'B.Cu'").replace('In3','B').replace('r96','r98')
s=s.replace("LAYERS=['F.Cu','In1.Cu','In2.Cu','B.Cu','In4.Cu','B.Cu']", "LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']")
dst=H/'construct_DIC_CS_continuous_F_B_F_r98.py';assert not dst.exists();dst.write_text(s);compile(s,str(dst),'exec');out=H/'prepare-DIC-CS-B-transport-r98.json';assert not out.exists();out.write_text(json.dumps({'source_sha256':hashlib.sha256(b).hexdigest(),'derived_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'delta':'Only signal transport B rather than In3; F remains actual In1 reference, B actual In4, actual In1/In4 pairs, all6 ordinary masks and F/B SMD copper retained; max F/B/F three segments.'},indent=1)+'\n');print(dst)
