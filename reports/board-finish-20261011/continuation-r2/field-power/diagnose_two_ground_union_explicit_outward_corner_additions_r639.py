"""Nominate explicit outward new corners for two ground unions; declare all gains."""
from pathlib import Path
import ast
H=Path(__file__).resolve().parent
p=H/'diagnose_overlap_exact_inward_intersection_vertices_r617.py'
t=ast.parse(p.read_text(encoding='utf-8'));t.body.pop();ns={'__file__':str(p)};exec(compile(t,str(p),'exec'),ns);s=ns['s']
s=s.replace('R543-overlap-exact-inward-intersection-native-splice-diagnostic-r617','R543-two-ground-union-explicit-outward-corner-addition-nominees-r639')
s=s.replace('def inward_union(literal,before):','def inward_union(literal,before,outward=False):')
s=s.replace('if o1>=0 and o2>=0:found.append','if (o1<=0 and o2<=0)if outward else(o1>=0 and o2>=0):found.append')
s=s.replace('after,generated=inward_union(literal,before);actual=zero(after);','after,generated=inward_union(literal,before,outward=i in(2,3));actual=zero(after);')
s=s.replace("'both_exact_halfplane_nonnegative':True","'both_exact_halfplane_inside':not outward,'both_exact_halfplane_outside':outward,'explicit_new_corner_copper_extension_nomination':outward")
s=s.replace("'new_intersection_vertices_exact_inward_halfplanes':len(generated)","'new_intersection_vertices_exact_direction_halfplanes':len(generated),'direction':'OUTWARD_EXPLICIT_NEW_COPPER_GAIN'if i in(2,3)else'INWARD_BOUND_NEGATIVE','foreign_rules_reference_source_current_native_qualification':'OPEN'")
s=s.replace("print('R617'","print('R639'")
exec(compile(s,str(Path(__file__)),'exec'))
