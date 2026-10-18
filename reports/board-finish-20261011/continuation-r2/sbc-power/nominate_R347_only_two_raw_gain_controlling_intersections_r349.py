"""Separate minimal nomination; move only intersections named by raw gain."""
from pathlib import Path
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/nominate_R347_original_record_new_intersection_inward_splice_r348.py'
s=p.read_text(encoding='utf-8').replace('r348','r349').replace('R348','R349').replace('only-new-intersection-native-inward-splice-proposal-r349','only-two-raw-gain-controlling-intersection-splice-proposal-r349')
needle='for v in sorted(newv):'
assert needle in s
replacement="""gainWitness=from_wkb((D/'literal-raw-positive-component.wkb').read_bytes());gainPolys=list(gainWitness.geoms)if hasattr(gainWitness,'geoms')else[gainWitness];selected=set();locators=[]
 for gp in gainPolys:
  for x in gp.exterior.coords:
   if tuple(x)in oldv:continue
   v=min(newv,key=lambda v:Point(v).distance(Point(x)));dist=Point(v).distance(Point(x));assert dist<.000000000001;selected.add(v);locators.append({'exact_raw_gain_vertex':tuple(x),'identified_raw_cut_intersection':v,'binary64_locator_distance_mm':dist,'no_gain_magnitude_waiver':True})
 put(O/'exact-raw-gain-two-intersection-locator.json',{'all_new_intersections':len(newv),'only_exact_raw_gain_controlled_intersections':sorted(selected),'exact_locators':locators})
 for v in sorted(selected):"""
s=s.replace(needle,replacement)
exec(compile(s,str(__file__),'exec'))
