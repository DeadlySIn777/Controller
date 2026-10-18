"""Materialize the prior routing implementation before applying the new return filter."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent.parent
wrapper=H/'sbc-power/nominate_R353_IO3_existing_annulus_joint_minimal_LG_support_hard_foreign_r366.py'
failed=H/'sbc-power/nominate_R353_IO3_existing_ports_true_ordinary_two_plane_returns_joint_support_r376.py'
failure=H/'sbc-power/R376-wrapper-source-syntax-failure.json'
assert not failure.exists()
failure.write_text(json.dumps({'failure':'IndentationError in nested wrapper, before any executable body or native/model changes','source_sha256':hashlib.sha256(failed.read_bytes()).hexdigest(),'native_jobs':0},indent=1)+'\n',encoding='utf-8')
expanded_source=H/'sbc-power/exact-expanded-R366-read-only-route-base-for-R377.py'
assert not expanded_source.exists()
w=wrapper.read_text(encoding='utf-8')
mark="exec(compile(t,str(__file__),'exec'))"
assert w.count(mark)==1
replacement="t=t.replace(\"exec(compile(s,str(__file__),'exec'))\",\"expanded_source.write_text(s,encoding='utf-8')\");exec(compile(t,str(__file__),'exec'))"
w=w.replace(mark,replacement)
exec(compile(w,str(__file__),'exec'))
s=expanded_source.read_text(encoding='utf-8').replace('r366','r377').replace('R366','R377')
s=s.replace('pairs=pairs[:48]','pairs=pairs')
needle="vmap={v['uuid']:v for v in h['vias']}"
assert needle in s
tail=";lgports=[]\n for v in h['vias']:\n  if L.norm(v['net'])!='/LOGIC_GND':continue\n  anns={ly:zero(unary_union([rr['shape']for rr in lg if rr['kind']=='via'and rr['uuid']==v['uuid']and rr['layer']==ly]))for ly in ('In1.Cu','In4.Cu')};areas={ly:anns[ly].intersection(references[ly]).area for ly in anns}\n  if all(a>0 for a in areas.values()):lgports.append({'UUID':v['uuid'],'xy':[v['x'],v['y']],'actual_two_source_plane_annulus_overlaps_mm2':areas,'current_original_or_preexisting_masks_unchanged':True})\n lgtree=STRtree([Point(*v['xy'])for v in lgports]);pairCensus=[];filtered=[]\n for pair in pairs:\n  paired={}\n  for side in ('source_existing_annulus','detached_existing_annulus'):\n   pp=pair[side];p=Point(pp['x'],pp['y']);vv=[]\n   for j in lgtree.query(p.buffer(1.000001),predicate='intersects'):\n    lgp=lgports[int(j)];distance=p.distance(Point(*lgp['xy']))\n    if .9<=distance<=1.:vv.append({**lgp,'ordinary_IO3_to_LG_center_distance_mm':distance})\n   paired[side]=vv\n  row={'layer':pair['layer'],'source_IO3_UUID':pair['source_existing_annulus']['UUID'],'detached_IO3_UUID':pair['detached_existing_annulus']['UUID'],'source_return_count':len(paired['source_existing_annulus']),'detached_return_count':len(paired['detached_existing_annulus']),'actual_ordinary_two_source_plane_returns':paired};pairCensus.append(row)\n  if all(paired.values()):filtered.append({**pair,'actual_ordinary_two_source_plane_returns':paired})\n put(O/'all-saved-cross-group-port-pair-true-two-plane-ordinary-return-census.json',pairCensus);put(O/'only-existing-ordinary-return-qualified-pairs.json',filtered);pairs=filtered[:48]\n "
s=s.replace(needle,needle+tail)
s=s.replace("'exact_reference_terminal_authority':portcaps", "'exact_reference_terminal_authority':portcaps,'existing_actual_ordinary_two_source_plane_LG_return_pairs':pair['actual_ordinary_two_source_plane_returns']")
O=H/'sbc-power/CM79-R353-IO3-existing-actual-annulus-no-hole-fixed-Cu-bypass-nomination-r377'
assert not O.exists()
Path(H/'sbc-power/exact-expanded-current-ordinary-return-route-r377.py').write_text(s,encoding='utf-8')
exec(compile(s,str(__file__),'exec'))

