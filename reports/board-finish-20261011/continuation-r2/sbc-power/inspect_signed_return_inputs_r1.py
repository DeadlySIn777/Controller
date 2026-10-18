"""Pin-specific native source inventory for conserved return scenarios."""
import ast,json,hashlib,re
from pathlib import Path
import inspect_integrated_source as I
HERE=Path(__file__).resolve().parent
I.NET=HERE.parent/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net'
def main():
    comps,pins=I.load()
    ns={'re':re};tree=ast.parse(I.PARSER.read_text(encoding='utf-8'))
    ds=[n for n in tree.body if (isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='TOKEN') or (isinstance(n,ast.FunctionDef) and n.name in ('sexpr_parse','child','children','atom','norm'))]
    exec(compile(ast.Module(body=ds,type_ignores=[]),'pinned-parser','exec'),ns)
    parse,child,children,atom=(ns[k] for k in ('sexpr_parse','child','children','atom'))
    root=parse(I.NET.read_text(encoding='utf-8'));nativecomps={atom(c,'ref'):c for c in children(child(root,'components'),'comp')};libs={}
    for lib in children(child(root,'libparts'),'libpart'):
        libs[(atom(lib,'lib'),atom(lib,'part'))]={atom(p,'num'):{'name':atom(p,'name'),'type':atom(p,'type')} for p in children(child(lib,'pins') or [],'pin')}
    wanted=['J11001','J11002','U11001','U11007','U11008','U2001','U2002','U16001','U14812','U14813','U17017','U17018','J15001','J15002','U15012','U15026','U15018','U11012','U14601','U14619','U14701','U14702','U14703']
    rows={}
    for ref in wanted:
        n=nativecomps[ref];lib=child(n,'libsource');lp=libs[(atom(lib,'lib'),atom(lib,'part'))]
        rows[ref]={'component':comps[ref],'pins':{p:{'net_raw':net,**lp.get(p,{})} for p,net in pins[ref].items()}}
    core=[{'ref':r,'pin':p,'component':comps[r],'pin_definition':libs[(atom(child(nativecomps[r],'libsource'),'lib'),atom(child(nativecomps[r],'libsource'),'part'))].get(p,{}),'net_raw':net} for r,ps in pins.items() for p,net in ps.items() if net.endswith('CORE_5V')]
    result={'source':str(I.NET.resolve()),'sha256':hashlib.sha256(I.NET.read_bytes()).hexdigest(),'components':len(comps),'source_roles':rows,'all_CORE5_nodes':core}
    out=HERE/'signed-return-inputs-r1.json';out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('RETURN_INPUTS',len(comps),len(core),result['sha256']);print(json.dumps({ref:{p:q for p,q in row['pins'].items() if q.get('type') in ('power_in','power_out') or any(k in q.get('name','').upper() for k in ('GND','VIN','VDD','VCC','VOUT'))} for ref,row in rows.items()},indent=2))
if __name__=='__main__':main()
