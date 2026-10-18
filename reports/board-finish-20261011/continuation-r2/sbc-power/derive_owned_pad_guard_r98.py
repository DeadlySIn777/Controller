"""Explicit extra 20 nm pad construction reserve; required audit guard unchanged."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent
s=(H/'owned_native_pad_guards_r95.py').read_text()
assert s.count("cutter=GP.bounded_buffer(r['shape'],clear)")==1
s=s.replace("cutter=GP.bounded_buffer(r['shape'],clear)","cutter=GP.bounded_buffer(r['shape'],clear+.000020)")
assert s.count("'required_Cu_guard_mm':clear,")==1
s=s.replace("'required_Cu_guard_mm':clear,","'required_Cu_guard_mm':clear,'explicit_extra_outward_pad_construction_reserve_mm':.000020,'independent_required_gap_unchanged':True,")
s=s.replace('Ledgered outward pad-polygon cuts','Ledgered outward pad-polygon cuts with explicit additional 20 nm reserve')
out=H/'owned_native_pad_guards_r98.py';assert not out.exists();out.write_text(s);compile(s,str(out),'exec');print('PAD_20NM_EXPLICIT_RESERVE_HELPER',hashlib.sha256(out.read_bytes()).hexdigest())
