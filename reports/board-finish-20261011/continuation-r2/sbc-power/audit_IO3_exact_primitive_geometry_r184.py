"""Fresh strict true geometry; preserve the historical R178 checker/output."""
from pathlib import Path
P=Path(__file__).resolve().parent
w=(P/'audit_original_IO3_full_true_geometry_r178.py').read_text()
tail="exec(compile(s,str(P/'audit_SAFE_true_geometry_r152.py'),'exec'))"
assert w.endswith(tail+'\n')
ns={'__file__':str(Path(__file__).resolve())};exec(compile(w[:-len(tail+'\n')],str(P/'audit_original_IO3_full_true_geometry_r178.py'),'exec'),ns)
s=ns['s'].replace('original-IO3-full-independent-true-geometry-r178','IO3-exact-primitive-independent-true-geometry-r184')
exec(compile(s,str(P/'audit_SAFE_true_geometry_r152.py'),'exec'))
