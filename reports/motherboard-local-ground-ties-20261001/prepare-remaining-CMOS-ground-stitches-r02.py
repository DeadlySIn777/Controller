"""Use exact local literal-fill coverage only during candidate search."""
import hashlib,json
from pathlib import Path
here=Path(__file__).parent
root=here.parents[1]
base=here/'route-remaining-CMOS-ground-stitches-r01.py'
target=here/'route-remaining-CMOS-ground-stitches-r02.py'
helper=root/'tools/hardware_index_literal_reference_coverage.py'
assert not target.exists() and helper.is_file()
text=base.read_text()
text=text.replace('from hardware_collect_native_reference_fills import collect_native_reference_fills','from hardware_collect_native_reference_fills import collect_native_reference_fills\nfrom hardware_index_literal_reference_coverage import LiteralReferenceCoverage')
text=text.replace(";geometry=Geometry(b)",";geometry=Geometry(b)\n index=LiteralReferenceCoverage(b,{'/LOGIC_GND'},[pcbnew.In1_Cu,pcbnew.In4_Cu])")
old="covered(circle(tuple(xy(e)),pcbnew.FromMM(.26)),fills['/LOGIC_GND',adjacent])"
assert text.count(old)==1
text=text.replace(old,"index.candidate_covered(circle(tuple(xy(e)),pcbnew.FromMM(.26)),'/LOGIC_GND',adjacent)")
text=text.replace("src/'netlist.xml',Path(__file__))}","src/'netlist.xml',Path(__file__),ROOT/'tools/hardware_index_literal_reference_coverage.py')}")
assert 'covered(circle(tuple(v.GetPosition()),pcbnew.FromMM(.26)),finalfills' in text
assert 'physical_reference_contact(v,layer,co)' in text
target.write_text(text)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
scope=json.loads((here/'remaining-CMOS-ground-scope-r01.json').read_text())
scope.update(parent_generator_sha256=sha(base),generator_sha256=sha(target),literal_index_helper_sha256=sha(helper),search_only_exact_literal_tile_prefilter=True,final_actual_frozen_full_union_guard_retained=True)
(here/'remaining-CMOS-ground-scope-r02.json').write_text(json.dumps(scope,indent=2)+'\n')
print(dict(prepared=True,generator_sha256=sha(target),final_frozen_guard_unchanged=True))
