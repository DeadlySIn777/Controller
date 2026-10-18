from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'audit_ao1_native_com_reference_r1.py').read_text()
def change(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
change('from pathlib import Path',"from pathlib import Path\nfrom decimal import Decimal,ROUND_HALF_UP\ndef native_mm(v):return float((Decimal(str(v))*Decimal(1000000)).to_integral_value(rounding=ROUND_HALF_UP)/Decimal(1000000))\ndef native_at(v):return tuple(native_mm(x) for x in v)")
s=s.replace('reference-independent-r1','reference-independent-r2')
change("else:assert tuple(n['s'])==tuple(z['a']) and tuple(n['e'])==tuple(z['b']) and n['w']==z['w'] and n['layer']==z['layer'],u", "else:\n   assert tuple(n['s'])==native_at(z['a']) and tuple(n['e'])==native_at(z['b']) and n['w']==z['w'] and n['layer']==z['layer'],u\n   z['a'],z['b']=list(n['s']),list(n['e'])\n   target=next(t for t in g['tracks'] if t['uuid']==u);target['a'],target['b']=list(n['s']),list(n['e'])")
change("'exact_raw_native_geometry':True","'exact_raw_native_geometry_and_declared_1nm_lattice':True")
q=HERE/'audit_ao1_native_com_reference_r2.py';assert not q.exists();q.write_text(s)
