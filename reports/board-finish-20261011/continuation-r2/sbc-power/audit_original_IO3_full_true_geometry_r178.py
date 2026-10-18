"""Independent full literal geometry after IO3 equal-settings canonical union."""
from pathlib import Path
P=Path(__file__).resolve().parent
w=(P/'audit_SAFE_repaired_true_geometry_r161.py').read_text();tail="exec(compile(s,str(p/'audit_SAFE_true_geometry_r152.py'),'exec'))";assert w.endswith(tail+'\n')
ns={'__file__':str(Path(__file__).resolve())};exec(compile(w[:-len(tail+'\n')],str(P/'audit_SAFE_repaired_true_geometry_r161.py'),'exec'),ns)
s=ns['s'].replace('SAFE-repaired-independent-true-geometry-r161','original-IO3-full-independent-true-geometry-r178')
exec(compile(s,str(P/'audit_SAFE_true_geometry_r152.py'),'exec'))
