"""Bind frozen native rules and exact aggregate guard to a later actual board."""
import argparse,ast,math,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
import pcbnew
from hardware_merge_bounded_pcb_delta import objects,zone_definition,without_generated_fills
from hardware_build_assembly import parse
ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
assert not a.out.exists()
BASE=ROOT/'reports/motherboard-pcb-integration-20261001/source26-FPGA38-rule-r76/motherboard-literal38-neck-rule-candidate.kicad_pcb'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
review=read(BASE.parent/'review.json');proposal=read(BASE.parent/'proposal.json')
assert review['passed'] and review['board_sha256']==sha(BASE)
literal_path=ROOT/proposal['frozen_proposal']['path'];assert sha(literal_path)==proposal['frozen_proposal']['sha256']
literal=read(literal_path);names=set(literal['nets']);assert len(names)==38
for suffix in ['.kicad_pro','.kicad_dru']:
    assert a.board.with_suffix(suffix).read_bytes()==BASE.with_suffix(suffix).read_bytes()
area=proposal['new_F_rule_area_uuid']
old=objects(parse(without_generated_fills(BASE.read_text())),'zone')
new=objects(parse(without_generated_fills(a.board.read_text())),'zone')
assert zone_definition(old[area])==zone_definition(new[area])
# Execute only the exact retained pure aggregate function. The original script
# entry point, board mutation, network retrieval and fixture creation never run.
guard=ROOT/'reports/motherboard-critical-routing-20261001/prepare_fpga_neck_rule_r03.py'
tree=ast.parse(guard.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='aggregate_guard')
namespace=dict(names=names,pcbnew=pcbnew,math=math)
exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),namespace)
b=pcbnew.LoadBoard(str(a.board));aggregate=namespace['aggregate_guard'](b)
result=dict(passed=True,board_sha256=sha(a.board),original_rule_review_sha256=sha(BASE.parent/'review.json'),
            frozen_native_rule_proposal_sha256=sha(literal_path),exact_literal_signal_nets=38,
            maximum_aggregate_per_net_mm=1.,actual_aggregate_guard=aggregate,
            exact_native_project_and_rule_files_unchanged=True,exact_F_rule_area_unchanged=True,
            guard_source_sha256=sha(guard),guard_function=ast.get_source_segment(guard.read_text(),node),
            factory_exact_2oz_process_confirmation_outstanding=True,manufacturing_ready=False,
            source_or_board_mutated=False)
a.out.write_text(json.dumps(result,indent=2)+'\n');print(dict(passed=True,narrow_segments=len(aggregate['narrow_segments'])))
