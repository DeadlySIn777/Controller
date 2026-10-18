"""Prepare bounded-cache wrapper and preserve both sides of shared rail scope."""
from pathlib import Path
import hashlib,json
p=Path(__file__).parent
source=p/'route-adjacent-same-side-bypass-r06.py';target=p/'route-adjacent-same-side-bypass-r07.py';assert not target.exists()
s=source.read_text().replace('from check_same_side_bypass_r01 import check_group, surface_path','from check_same_side_bypass_r02 import check_group, surface_path, BoundSameSideCheck')
s=s.replace("Path(__file__).with_name('check_same_side_bypass_r01.py')","Path(__file__).with_name('check_same_side_bypass_r02.py')")
s=s.replace('shared=SourceAnchoredPiecesCheck(reviewed,declarations,source_mapping)','shared=BoundSameSideCheck(reviewed,declarations,source_mapping)')
old="    declarations[cp.GetNetname()]=dict(return_net=cr.GetNetname(),reference_layers={b.GetLayerName(outer):'In1.Cu'if outer==pcbnew.F_Cu else'In4.Cu'},allow_vias=False,reference_corridor_margin_mm=.10)"
new="""    declaration=declarations.setdefault(cp.GetNetname(),dict(return_net=cr.GetNetname(),reference_layers={},allow_vias=False,reference_corridor_margin_mm=.10))
    if declaration['return_net']!=cr.GetNetname():raise ValueError('One supply net cannot silently change its own return')
    declaration['reference_layers'][b.GetLayerName(outer)]='In1.Cu'if outer==pcbnew.F_Cu else'In4.Cu'"""
assert s.count(old)==1;s=s.replace(old,new,1)
s=s.replace('Every return via must join the actual own-domain filled\nreference copper on both sides; every new power transition requires a nearby\nactual own-return stitch.', 'Every receiving return must have a bounded actual surface trace to its own\nSOURCE-anchored adjacent filled reference. Supply layer transitions are\nforbidden in this separate trial. Existing101 loops retain their original checks.')
target.write_text(s)
record=dict(prepared=True,not_run=True,parent_trial_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),trial_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),cache_wrapper_sha256=hashlib.sha256((p/'check_same_side_bypass_r02.py').read_bytes()).hexdigest(),prior_101_guards_unchanged=True,multiple_surface_rail_declarations_union_only=True)
(p/'bound-adjacent-trial-preparation-r01.json').write_text(json.dumps(record,indent=2)+'\n')
print('Prepared board-bound separate adjacent-only trial')
