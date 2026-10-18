"""Bind exact ordinary112 to actual anchored pieces, retaining every failure."""
from pathlib import Path
import argparse,json
import hardware_bind_ordinary_route_manifest as binder
import hardware_route_ordinary_wip_r05 as issued
import hardware_scope_anchored_reference_pieces as pieces
def bind(board,planes,out,selected):
 issued.dependencies();board,planes,out=map(lambda p:Path(p).resolve(),(board,planes,out))
 if out.exists()or not out.is_relative_to(issued.engine.ROOT/'reports'):raise ValueError('New immutable report required')
 review=issued.engine.ROOT/issued.SOURCE;r=issued.engine.read(review);selected=set(selected)
 if not selected or not selected<=set(r['nets']):raise ValueError('Exact frozen ordinary112 names required')
 proof=pieces.verify_receipt(planes,board,{n:r['nets'][n]for n in selected});out.parent.mkdir(parents=True,exist_ok=True)
 result=binder.bind(review,board,planes,out,selected)
 result.update(whole_board_reference_qualification=False,whole_return_net_qualification=False,scope_only=True,
  plane_geometry_qualified=False,source_anchored_piece_eligibility_only=True,full_failed_reference_piece_ledger=proof['complete_unanchored_components'],
  manufacturing_ready=False,physical_SI_qualified=False)
 issued.INPUT_BOARD=board;issued.frozen_review_check(result,issued.engine.ROOT/'hardware/motherboard/design.json',issued.engine.ROOT/'hardware/motherboard/netlist.xml')
 issued.engine.write(out,result);return result
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('board','planes','selected','out'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();r=bind(a.board,a.planes,a.out,issued.engine.read(a.selected));print(json.dumps(dict(exact_selected_nets=len(r['nets']),whole_board_reference_qualification=False,manufacturing_ready=False)))
if __name__=='__main__':main()
