"""Bind a literal frozen ordinary112 subset without claiming global planes pass."""
from pathlib import Path
import argparse,json
import hardware_bind_ordinary_route_manifest as prior
import hardware_route_ordinary_wip_r04 as issued
import hardware_scope_critical_reference_qualification as scope

def bind(board,planes,out,selected):
 issued.dependencies();board,planes,out=map(lambda p:Path(p).resolve(),(board,planes,out))
 if out.exists()or not out.is_relative_to(issued.engine.ROOT/'reports'):
  raise ValueError('Use a new immutable workspace report file')
 review=issued.engine.ROOT/issued.SOURCE;r=scope.read(review);selected=set(selected)
 if not selected or not selected<=set(r['nets']):raise ValueError('Exact frozen ordinary112 names required')
 scope.check(scope.read(planes),dict(board_sha256=scope.sha(board),nets={n:r['nets'][n]for n in selected}))
 out.parent.mkdir(parents=True,exist_ok=True)
 result=prior.bind(review,board,planes,out,selected)
 result.update(whole_board_reference_qualification=False,scope_only=True,
  plane_geometry_qualified=False,selected_source_anchored_reference_qualified=True,
  manufacturing_ready=False,physical_SI_qualified=False)
 issued.frozen_review_check(result,issued.engine.ROOT/'hardware/motherboard/design.json',
                            issued.engine.ROOT/'hardware/motherboard/netlist.xml')
 scope.read(out);issued.engine.write(out,result);return result
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('board','planes','selected','out'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();r=bind(a.board,a.planes,a.out,scope.read(a.selected))
 print(json.dumps(dict(exact_selected_nets=len(r['nets']),whole_board_reference_qualification=False,manufacturing_ready=False)))
if __name__=='__main__':main()
