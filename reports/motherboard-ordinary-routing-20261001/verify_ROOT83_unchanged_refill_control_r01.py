from pathlib import Path
import sys,json
sys.path[:0]=[str(Path('tools').resolve()),str(Path(__file__).parent)]
import pcbnew
import check_io3_backbone_preservation_r07 as power
from hardware_route_logic_return import identity,pad_identity
p=Path(__file__).parent;out=p/'ROOT83-unchanged-refill-control-r01';base=Path('reports/motherboard-pcb-integration-20261001/source26-reference-closure-and-spurs-r83/motherboard-bounded-merged-candidate.kicad_pcb');after=out/base.name
b=pcbnew.LoadBoard(str(base));a=pcbnew.LoadBoard(str(after))
assert {t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}=={t.m_Uuid.AsString():identity(t)for t in a.GetTracks()}
assert {q.m_Uuid.AsString():pad_identity(q)for q in b.GetPads()}=={q.m_Uuid.AsString():pad_identity(q)for q in a.GetPads()}
try:
 proof=power.review(b,a);result=dict(passed=True,actual_power_geometry=proof)
except Exception as ex:result=dict(passed=False,reason=str(ex))
result.update(before_sha256=power.sha(base),after_sha256=power.sha(after),all_Cu_and_pad_properties_unchanged=True,helper_sha256=power.sha(Path(power.__file__)),diagnostic_unchanged_native_refill_only=True)
(out/'power-review.json').write_text(json.dumps(result,indent=2));print(json.dumps(dict(passed=result['passed'],reason=result.get('reason'))))
