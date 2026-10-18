"""Bind reviewed exact ordinary nets to one native board and plane receipt."""
from pathlib import Path
import argparse,copy,json
from hardware_route_selected_additive_r02 import ROOT,sha,read,write,checked_dependencies


def bind(review,board,planes,out,selected=None):
    review,board,planes=[Path(p).resolve()for p in (review,board,planes)]
    r=read(review);p=read(planes);checked_dependencies()
    if p.get('board_sha256')!=sha(board)or p.get('passed')is not True:
        raise ValueError('Actual plane review is not passed against this exact board')
    rows=r['nets'];selected=set(rows)if selected is None else set(selected)
    if not selected or not selected<=set(rows):raise ValueError('Every selected net must belong to the frozen source review')
    sources=r['source_review_sha256'];source_files={Path(n).name:n for n in sources}
    for n,h in sources.items():
        if sha(n)!=h:raise ValueError('Frozen source review input changed: '+n)
    result=copy.deepcopy(r);result['nets']={n:rows[n]for n in sorted(selected)}
    result['source_review']=dict(path=str(review),sha256=sha(review))
    result['plane_review']=dict(path=str(planes),sha256=sha(planes))
    result['board_sha256']=sha(board);result['design_sha256']=sources[source_files['design.json']]
    result['netlist_sha256']=sources[source_files['netlist.xml']]
    for suffix,label in [('.kicad_pro','project'),('.kicad_dru','rules')]:
        f=board.with_suffix(suffix)
        if not f.is_file():raise ValueError('Exact native project/rules required: '+label)
        result[label+'_sha256']=sha(f)
    result['board_binding_required']=False
    result['plane_geometry_qualified']=True # geometry only, never impedance/EMC
    result['physical_SI_qualified']=False
    result['routing_dependencies']=checked_dependencies();write(out,result);return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('review','board','planes','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--selected',type=Path,help='JSON list of exact reviewed net names')
    a=p.parse_args();out=a.out.resolve()
    if out.exists()or not out.is_relative_to(ROOT/'reports'):raise ValueError('Use a new workspace report file')
    out.parent.mkdir(parents=True,exist_ok=True)
    r=bind(a.review,a.board,a.planes,out,read(a.selected)if a.selected else None)
    print(json.dumps(dict(exact_selected_nets=len(r['nets']),board_sha256=r['board_sha256'])))


if __name__=='__main__':main()
