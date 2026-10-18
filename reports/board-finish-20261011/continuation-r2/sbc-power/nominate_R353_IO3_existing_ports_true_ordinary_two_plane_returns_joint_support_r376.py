"""Existing IO3 ports with actual .90–1.0 two-plane LG returns, then joint support."""
from pathlib import Path
H=Path(__file__).resolve().parent.parent
t=(H/'sbc-power/nominate_R353_IO3_existing_annulus_joint_minimal_LG_support_hard_foreign_r366.py').read_text(encoding='utf-8')
needle="exec(compile(t,str(__file__),'exec'))";assert t.count(needle)==1
extra=r'''
t=t.replace('r366','r376').replace('R366','R376')
inner="exec(compile(s,str(__file__),'exec'))";assert t.count(inner)==2 or t.count(inner)==1
insert=r"""
s=s.replace('pairs=pairs[:48]','pairs=pairs')
needle2="vmap={v['uuid']:v for v in h['vias']}"
assert needle2 in s
tail="""+"'''"+r""";lgports=[]
 for v in h['vias']:
  if L.norm(v['net'])!='/LOGIC_GND':continue
  anns={ly:zero(unary_union([rr['shape']for rr in lg if rr['kind']=='via'and rr['uuid']==v['uuid']and rr['layer']==ly]))for ly in ('In1.Cu','In4.Cu')};areas={ly:anns[ly].intersection(references[ly]).area for ly in anns}
  if all(a>0 for a in areas.values()):lgports.append({'UUID':v['uuid'],'xy':[v['x'],v['y']],'actual_two_source_plane_annulus_overlaps_mm2':areas,'current_original_or_preexisting_masks_unchanged':True})
 lgtree=STRtree([Point(*v['xy'])for v in lgports]);pairCensus=[];filtered=[]
 for pair in pairs:
  paired={}
  for side in ('source_existing_annulus','detached_existing_annulus'):
   pp=pair[side];p=Point(pp['x'],pp['y']);vv=[]
   for j in lgtree.query(p.buffer(1.000001),predicate='intersects'):
    lgp=lgports[int(j)];distance=p.distance(Point(*lgp['xy']))
    if .9<=distance<=1.:vv.append({**lgp,'ordinary_IO3_to_LG_center_distance_mm':distance})
   paired[side]=vv
  row={'layer':pair['layer'],'source_IO3_UUID':pair['source_existing_annulus']['UUID'],'detached_IO3_UUID':pair['detached_existing_annulus']['UUID'],'source_return_count':len(paired['source_existing_annulus']),'detached_return_count':len(paired['detached_existing_annulus']),'actual_ordinary_two_source_plane_returns':paired};pairCensus.append(row)
  if all(paired.values()):filtered.append({**pair,'actual_ordinary_two_source_plane_returns':paired})
 put(O/'all-saved-cross-group-port-pair-true-two-plane-ordinary-return-census.json',pairCensus);put(O/'only-existing-ordinary-return-qualified-pairs.json',filtered);pairs=filtered[:48]
 """+"'''"+r"""
s=s.replace(needle2,needle2+tail)
s=s.replace("'exact_reference_terminal_authority':portcaps", "'exact_reference_terminal_authority':portcaps,'existing_actual_ordinary_two_source_plane_LG_return_pairs':pair['actual_ordinary_two_source_plane_returns']")
"""
t=t.replace(inner,insert+'\n'+inner)
'''
t=t.replace(needle,extra+'\n'+needle)
exec(compile(t,str(__file__),'exec'))
