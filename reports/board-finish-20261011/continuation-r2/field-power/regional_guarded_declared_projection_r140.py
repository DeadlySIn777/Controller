"""Equivalent local cutter union for each original native filled polygon.

Discard only cutters disjoint from the exact original before unary union.
This uses A\\union(B_i) == A\\union(B_i intersecting A), without expanding
any physical polygon or relaxing a clearance/reference threshold. Original
native definitions and all outward cutter primitives remain unchanged.
"""
import inspect,hashlib
import guarded_declared_settings_projection_r58 as P
source=inspect.getsource(P.projected)
old="cache[key]=(rows,unary_union([r[1] for r in rows]));return cache[key]"
new="cache[key]=rows;return rows"
assert source.count(old)==1;source=source.replace(old,new)
old="original=unary_union(p.base.polygons(records));rows,cut=cutters(z['net'],layer,local)"
new="original=unary_union(p.base.polygons(records));rows=[r for r in cutters(z['net'],layer,local) if r[1].intersects(original)];cut=unary_union([r[1] for r in rows])"
assert source.count(old)==1;source=source.replace(old,new)
namespace=dict(vars(P));exec(compile(source,__file__,'exec'),namespace)
projected=namespace['projected']
BASE_FUNCTION_SHA256=hashlib.sha256(inspect.getsource(P.projected).encode()).hexdigest()
DERIVED_FUNCTION_SHA256=hashlib.sha256(source.encode()).hexdigest()
bounded_buffer=P.bounded_buffer
bounded_disk=P.bounded_disk
digest=P.digest
normalize_owned_via_guards=P.normalize_owned_via_guards
