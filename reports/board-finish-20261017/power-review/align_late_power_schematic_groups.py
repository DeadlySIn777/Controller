"""Translate six connected source-only groups to the 1.27 mm connection grid."""
from pathlib import Path
from decimal import Decimal,ROUND_HALF_UP
import hashlib,json,re,shutil
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'reports/board-finish-20261017/corrected-baseline-r1/native'
OUT=HERE/'late-power-schematic-grid-r3'
TARGETS=('C11092','C11093','C11094','C11095','R11088','U11038')
TOKEN=re.compile(r'\s*(\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+)',re.S)
COORD=re.compile(r'\((at|xy) ([-+\d.eE]+) ([-+\d.eE]+)')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def parse(text):
    stack=[[]]
    for m in TOKEN.finditer(text):
        t=m[1]
        if t=='(':stack.append([])
        elif t==')':stack[-2].append(stack.pop())
        else:stack[-1].append(json.loads(t)if t.startswith('"')else t)
    assert len(stack)==1 and len(stack[0])==1
    return stack[0][0]

def children(n,k):return[x for x in n if isinstance(x,list)and x and x[0]==k]
def child(n,k):
    v=children(n,k);assert len(v)==1,(k,len(v));return v[0]
def atom(n,k):return child(n,k)[1]
def top_spans(text):
    depth=0;quoted=False;escaped=False;start=None;result=[]
    for i,c in enumerate(text):
        if quoted:
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c=='"':quoted=False
            continue
        if c=='"':quoted=True
        elif c=='(':
            if depth==1:start=i
            depth+=1
        elif c==')':
            depth-=1
            if depth==1 and start is not None:result.append((start,i+1));start=None
    assert depth==0 and not quoted
    return result

def pins(lib):
    result=[]
    def walk(node):
        if isinstance(node,list)and node:
            if node[0]=='pin' and children(node,'at'):
                a=child(node,'at');result.append((Decimal(a[1]),Decimal(a[2])))
            else:
                for sub in node:walk(sub)
    walk(lib);return result

def main():
    assert not OUT.exists();OUT.mkdir();dest=OUT/'source';dest.mkdir()
    files=[p for p in SOURCE.iterdir()if p.is_file()and(p.suffix in('.kicad_sch','.kicad_sym','.kicad_pro')or p.name in('sym-lib-table','fp-lib-table'))]
    inputs={str(p):sha(p)for p in files};inputs[str(Path(__file__))]=sha(Path(__file__))
    # Retain native libraries locally so the fresh ERC has the exact old resources.
    for p in files:shutil.copyfile(p,dest/p.name)
    for p in SOURCE.iterdir():
        if p.is_dir()and p.suffix=='.pretty':shutil.copytree(p,dest/p.name)
    oldpath=SOURCE/'motherboard_power_entry.kicad_sch';text=oldpath.read_text();spans=top_spans(text)
    nodes=[parse(text[a:b])for a,b in spans]
    libs={n[1]:n for n in children(next(n for n in nodes if n[0]=='lib_symbols'),'symbol')}
    owners={};deltas={};plans=[];grid=Decimal('1.27')
    for ref in TARGETS:
        indices=[i for i,n in enumerate(nodes)if n[0]=='symbol'and any(q[1]=='Reference'and q[2]==ref for q in children(n,'property'))]
        assert len(indices)==1;index=indices[0];symbol=nodes[index];at=child(symbol,'at');assert at[3]=='0'
        x,y=Decimal(at[1]),Decimal(at[2]);dx=(x/grid).to_integral_value(rounding=ROUND_HALF_UP)*grid-x;dy=(y/grid).to_integral_value(rounding=ROUND_HALF_UP)*grid-y
        assert dx or dy
        points={((x+px).quantize(Decimal('0.000001')),(y-py).quantize(Decimal('0.000001')))for px,py in pins(libs[atom(symbol,'lib_id')])};assert points
        selected={index};changed=True
        while changed:
            changed=False
            for i,node in enumerate(nodes):
                if i in selected:continue
                if node[0]=='wire':
                    pts=child(node,'pts');ends={(Decimal(p[1]),Decimal(p[2]))for p in children(pts,'xy')}
                    if ends&points:selected.add(i);points|=ends;changed=True
                elif node[0]in('label','global_label','hierarchical_label','no_connect','junction'):
                    pos=child(node,'at');pt=(Decimal(pos[1]),Decimal(pos[2]))
                    if pt in points:selected.add(i);changed=True
        for i in selected:
            assert i not in owners,('Shared physical node needs coupled move',ref,owners.get(i))
            owners[i]=ref;deltas[i]=(dx,dy)
        assert all(((px+dx)/grid)%1==0 and ((py+dy)/grid)%1==0 for px,py in points)
        plans.append({'ref':ref,'old_center_mm':[str(x),str(y)],'new_center_mm':[str(x+dx),str(y+dy)],'delta_mm':[str(dx),str(dy)],'selected_kinds':{k:sum(nodes[i][0]==k for i in selected)for k in sorted({nodes[i][0]for i in selected})},'all_pin_wire_label_NC_connection_points_on_1_27mm_grid':True})
    replacements={};changes=[]
    for i,(dx,dy)in deltas.items():
        a,b=spans[i];old=text[a:b]
        def replace(m):
            xx=Decimal(m[2])+dx;yy=Decimal(m[3])+dy
            return f'({m[1]} {format(xx,"f")} {format(yy,"f")}'
        new=COORD.sub(replace,old)
        assert COORD.sub('(COORD X Y',old)==COORD.sub('(COORD X Y',new)
        uid=atom(nodes[i],'uuid')
        changes.append({'owner_ref':owners[i],'kind':nodes[i][0],'uuid':uid,'old_chunk_sha256':hashlib.sha256(old.encode()).hexdigest(),'new_chunk_sha256':hashlib.sha256(new.encode()).hexdigest()})
        replacements[i]=new
    pieces=[];position=0
    for i,(a,b)in enumerate(spans):pieces.extend([text[position:a],replacements.get(i,text[a:b])]);position=b
    pieces.append(text[position:]);after=''.join(pieces);(dest/oldpath.name).write_text(after)
    assert len(changes)==41, len(changes)
    assert sum(c['kind']=='symbol'for c in changes)==6
    assert sum(c['kind']=='wire'for c in changes)==16
    assert all(sha(Path(p))==v for p,v in inputs.items())
    receipt={'utc':datetime.now(timezone.utc).isoformat(),'verdict':'ISOLATED_RIGID_SCHEMATIC_GROUP_GRID_CORRECTION_NATIVE_EXPORT_ERC_PENDING','input_sha256':inputs,'connection_grid_mm':'1.27','coordinate_change_scope':'Six source component+label+stub+NC groups; coordinate fields only. Symbol definitions, values, MPNs, footprints, UUIDs, pin types, net text and project rules unchanged.','group_moves':plans,'exact_changed_top_level_chunks':changes,'modified_file':str(dest/oldpath.name),'modified_file_sha256':sha(dest/oldpath.name),'all_other_source_files_byte_identical':True,'native_root':str(dest/'board.kicad_sch'),'PCB_written':False,'electrical_limits_changed':False,'adopted':False,'manufacturing_ready':False}
    (OUT/'construction-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'verdict':receipt['verdict'],'groups':len(plans),'changed_chunks':len(changes),'moves':plans}))

if __name__=='__main__':main()
