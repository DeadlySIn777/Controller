"""Preserve finite Cu unions before Freerouting's polygon path normalization.

Split every path containing a collinear direction reversal into atomic wires.
Each exact original finite segment survives, with all wire metadata unchanged.
This is an interchange correction, never a native board edit or routing result.
"""
import argparse, collections, copy, hashlib, json
from decimal import Decimal
from pathlib import Path
from hardware_build_assembly import parse, dump, child, children, value

def points(path):
    assert len(path)>=7 and len(path)%2==1
    return [(Decimal(path[i]),Decimal(path[i+1])) for i in range(3,len(path),2)]

def reversals(path):
    pts=points(path); result=[]
    for i,(a,b,c) in enumerate(zip(pts,pts[1:],pts[2:]),1):
        u=(b[0]-a[0],b[1]-a[1]);v=(c[0]-b[0],c[1]-b[1])
        if u[0]*v[1]-u[1]*v[0]==0 and u[0]*v[0]+u[1]*v[1]<0: result.append(i)
    return result

def atoms(wiring):
    result=collections.Counter()
    for w in children(wiring,'wire'):
        path=child(w,'path')
        if path is None: continue
        meta=copy.deepcopy(w);meta.remove(child(meta,'path'))
        for a,b in zip(points(path),points(path)[1:]):
            result[(dump(meta),path[1],Decimal(path[2]),tuple(sorted((a,b))))]+=1
    return result

def transform(tree):
    wiring=child(tree,'wiring');before=atoms(wiring);rows=[];replacement=[]
    for index,node in enumerate(wiring):
        if not isinstance(node,list) or not node or node[0]!='wire':replacement.append(node);continue
        path=child(node,'path')
        if path is None or not reversals(path): replacement.append(node);continue
        scopes=[]
        for i in range(3,len(path)-2,2):
            new=copy.deepcopy(node);p=child(new,'path');p[:]=path[:3]+path[i:i+4]
            scopes.append(new)
        rows.append({'wire_index':index,'net':value(child(node,'net')[1]),'original':copy.deepcopy(node),'reversal_corner_indices':reversals(path),'replacement':copy.deepcopy(scopes)})
        replacement.extend(scopes)
    wiring[:]=replacement
    assert atoms(wiring)==before,'Finite centerline segment/width/metadata multiset changed'
    assert not any(reversals(p) for w in children(wiring,'wire') if (p:=child(w,'path')) is not None)
    return rows,sum(before.values())

def main():
    p=argparse.ArgumentParser();p.add_argument('--dsn',required=True);p.add_argument('--output',required=True);p.add_argument('--receipt',required=True);a=p.parse_args()
    source=Path(a.dsn).resolve();dest=Path(a.output).resolve();receipt=Path(a.receipt).resolve()
    assert source!=dest and not dest.exists() and not receipt.exists()
    original=source.read_bytes();tree=parse(original.decode());before=copy.deepcopy(tree)
    rows,count=transform(tree)
    # Every section outside wiring remains structurally exact; via scopes remain exact.
    assert [x for x in tree if not isinstance(x,list) or not x or x[0]!='wiring']==[x for x in before if not isinstance(x,list) or not x or x[0]!='wiring']
    assert children(child(tree,'wiring'),'via')==children(child(before,'wiring'),'via')
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(dump(tree)+'\n',encoding='utf-8')
    loaded=parse(dest.read_text());assert atoms(child(loaded,'wiring'))==atoms(child(before,'wiring'))
    assert source.read_bytes()==original
    r={'status':'DSN_RETRACE_SPLIT_FINITE_CU_MULTISET_EXACT_NATIVE_ROUTING_QUALIFICATION_OPEN','input':str(source),'input_SHA256':hashlib.sha256(original).hexdigest(),'output':str(dest),'output_SHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'tool_SHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'affected_paths':len(rows),'all_finite_atoms':count,'atomic_wires_added':sum(len(x['replacement'])-1 for x in rows),'proof':'Identical exact finite segment/width/wire-metadata multiset implies identical swept Cu union; no geometric tolerance or per-net repair. All other sections/vias exact.','native_fill_calls':0,'adopted':False,'rows':rows}
    receipt.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2))

if __name__=='__main__': main()
