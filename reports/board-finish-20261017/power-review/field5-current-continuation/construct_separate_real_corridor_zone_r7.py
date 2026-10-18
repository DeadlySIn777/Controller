"""Bind positive physical source to the literal safe support, inventory overlay boundary."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'construct_separate_real_corridor_zone_r6.py').read_text().replace("'separate-real-corridor-zone-construction-r6'","'separate-real-corridor-zone-construction-r7'")
s=s.replace("assert support.difference(allowed).is_empty;assert delta.difference(support).is_empty", "assert support.difference(allowed).is_empty;put('raw-difference-overlay-control.json',{'literal_full_new_source_support_outside_robust_allowed_area':sm(support.difference(allowed)),'raw_delta_minus_its_minuend':sm(delta.difference(support)),'positive_source_authority':'Entire new literal support is constrained; raw overlay residual is retained, and no electrical clearance claim depends on treating it as absent.'})")
exec(compile(s,str(HERE/'construct_separate_real_corridor_zone_r6.py'),'exec'),globals())
