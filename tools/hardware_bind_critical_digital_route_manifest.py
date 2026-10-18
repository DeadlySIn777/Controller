"""Bind only issued critical prototype geometry to an exact qualified native board."""
from pathlib import Path
import argparse,copy,json
import hardware_route_critical_digital_additive as executor
prior=executor.prior

def bind(board,planes,out,selected):
 board,planes,out=map(lambda p:Path(p).resolve(),(board,planes,out))
 if out.exists()or not out.is_relative_to(prior.ROOT/'reports'):
  raise ValueError('Use a new immutable workspace report file')
 geometry=prior.ROOT/executor.GEOMETRY_REVIEW;source=prior.ROOT/executor.SOURCE_REVIEW
 g=prior.read(geometry);r=prior.read(source);p=prior.read(planes)
 if p.get('passed')is not True or p.get('board_sha256')!=prior.sha(board):
  raise ValueError('Actual same-board reference-plane qualification required')
 selected=set(selected)
 if not selected or not selected<=set(g['nets']):
  raise ValueError('Every exact selected critical name requires issued geometry review')
 result=copy.deepcopy(g)
 result.update(schema_version=3,type='critical_digital_prototype',
  source_review=dict(path=str(source),sha256=prior.sha(source)),
  geometry_review=dict(path=str(geometry),sha256=prior.sha(geometry)),
  plane_review=dict(path=str(planes),sha256=prior.sha(planes)),
  board_sha256=prior.sha(board),design_sha256=r['source_design_sha256'],
  netlist_sha256=r['source_netlist_sha256'],nets={n:g['nets'][n]for n in sorted(selected)},
  exact_nets=len(selected),route_execution=False,operating_profile_qualified=False,
  manufacturing_ready=False,live_source_or_board_mutated=False)
 for suffix,label in [('.kicad_pro','project'),('.kicad_dru','rules')]:
  f=board.with_suffix(suffix)
  if not f.is_file():raise ValueError('Exact native project/rules required:'+label)
  result[label+'_sha256']=prior.sha(f)
 executor.frozen_review_check(result,prior.ROOT/'hardware/motherboard/design.json',prior.ROOT/'hardware/motherboard/netlist.xml')
 out.parent.mkdir(parents=True,exist_ok=True);prior.write(out,result)
 return result
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('board','planes','selected','out'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();r=bind(a.board,a.planes,a.out,prior.read(a.selected))
 print(json.dumps(dict(exact_critical_nets=r['exact_nets'],board_sha256=r['board_sha256'],manufacturing_ready=False)))
if __name__=='__main__':main()
