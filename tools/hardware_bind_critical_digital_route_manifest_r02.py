"""Bind a critical batch to literal physically anchored return domains."""
from pathlib import Path
import argparse,json
import hardware_bind_critical_digital_route_manifest as prior
import hardware_scope_critical_reference_qualification as scope
def bind(board,planes,out,selected):
 board,planes,out=map(lambda p:Path(p).resolve(),(board,planes,out))
 g=prior.prior.read(prior.prior.ROOT/prior.executor.GEOMETRY_REVIEW)
 selected=set(selected)
 if not selected or not selected<=set(g['nets']):raise ValueError('Exact issued critical names required')
 scope.check(scope.read(planes),dict(board_sha256=scope.sha(board),nets={n:g['nets'][n]for n in selected}))
 return prior.bind(board,planes,out,selected)
FROZEN_SCOPE_SHA='1a67cd10ead4a848a1810bf0a0a42cee1fe422c8972b818311fb69cc84e12c42'
def main():
 if scope.sha(scope.__file__)!=FROZEN_SCOPE_SHA:raise ValueError('Frozen literal scope guard changed')
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('board','planes','selected','out'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();r=bind(a.board,a.planes,a.out,scope.read(a.selected))
 print(json.dumps(dict(exact_critical_nets=r['exact_nets'],whole_board_reference_qualification=False,manufacturing_ready=False)))
if __name__=='__main__':main()
