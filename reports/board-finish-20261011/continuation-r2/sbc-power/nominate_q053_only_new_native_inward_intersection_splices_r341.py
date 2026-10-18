"""Retain both failed constructors; splice only new owned cut intersections."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent.parent
p=H/'field-power/nominate_FIELD5_FG_inward_new_intersection_splice_r535.py'
s=p.read_text(encoding='utf-8')
s=s.replace("H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))", "H=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(H/'sbc-power'))")
s=s.replace("D=H/'FIELD5-R525-raw-FG-gain-and-literal-boundary-attribution-r527';O=H/'FIELD5-new-cut-intersections-only-inward-native-splice-proposal-r535'", "D=H/'sbc-power/q053-R338-raw-gain-controlling-edge-and-declared-corridor-attribution-r339';O=H/'sbc-power/q053-only-new-native-inward-intersection-splice-proposal-r341'")
s=s.replace('Point,LineString,Polygon,MultiPolygon','Point,LineString,Polygon,MultiPolygon,box')
s=s.replace("assert not O.exists();O.mkdir();st=time.monotonic();", "assert not O.exists();O.mkdir();st=time.monotonic();assert hashlib.sha256((D/'receipt.json').read_bytes()).hexdigest()=='c9d0fac1b6e01d61b7c732952c12557b4fe3e8ff1bcb95a7d3ddba4e7ee5bf91';(O/'exact-expanded-owned-intersection-splice-proposal.py').write_text(s,encoding='utf-8');")
s=s.replace("local=from_wkb((D/'declared-2mm-locality.wkb').read_bytes())", "local=box(116,169,139,208)")
s=s.replace("(D/(role+'-literal_zero_direct_difference')/'after.wkb')", "(D/(role+'-literal-zero-direct-after.wkb'))")
s=s.replace("(D/'actual-normal-cut.wkb')", "(D/'actual-normal-cut.wkb')")
s=s.replace("row={'role':role", "assert gain.is_empty,('new-intersection splice literal gain',role,sm(gain));assert outside.is_empty,('owned negative wedge outside declared local corridor',role,sm(outside));assert remotee<=edges(after)and remotev<=vertices(after),('original vertex or complete edge changed outside local owned corridor',role);row={'role':role")
s=s.replace('all_complete_parent_edges_disjoint_2mm_identical','all_complete_parent_edges_disjoint_declared_corridor_identical').replace('all_parent_vertices_disjoint_2mm_identical','all_parent_vertices_disjoint_declared_corridor_identical').replace('extra_negative_corridor_2mm_EMPTY','extra_negative_outside_declared_corridor_EMPTY')
s=s.replace('outside_prior_2mm_locality','outside_declared_owner_corridor').replace('additional-negative-wedges-outside-2mm','additional-negative-wedges-outside-declared-corridor')
s=s.replace('only-proposed-FG-two-roles.pkl','only-proposed-q053-two-roles.pkl').replace('R527_input_receipt_sha256','R339_input_receipt_sha256').replace('R535','R341')
s=s.replace('SCOPED_INTEGER_INTERSECTION_SPLICE_NEGATIVE_WEDGE_PROPOSAL_ONLY_NO_MODEL','Q053_ONLY_NEW_NATIVE_INTERSECTION_SPLICE_STRICT_NEGATIVE_LOCAL_PROPOSAL_ONLY_NO_MODEL')
exec(compile(s,str(__file__),'exec'))
