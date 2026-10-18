import json,hashlib,ast,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
NET=BASE/'parity-repair/root106/source-export/fresh.net'
PARSER=BASE/'parity-repair/root106/tools/netlist_parity.py'
def load():
    namespace={'re':re};tree=ast.parse(PARSER.read_text(encoding='utf-8'))
    ds=[n for n in tree.body if (isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='TOKEN') or (isinstance(n,ast.FunctionDef) and n.name in ('sexpr_parse','child','children','atom','norm'))]
    exec(compile(ast.Module(body=ds,type_ignores=[]),'pinned-parser','exec'),namespace)
    parse,child,children,atom=(namespace[k] for k in ('sexpr_parse','child','children','atom'))
    tree=parse(NET.read_text(encoding='utf-8'))
    comps={atom(c,'ref'):{'value':atom(c,'value'),'footprint':atom(c,'footprint'),'datasheet':atom(c,'datasheet'),'fields':{atom(x,'name'):x[2] if len(x)>2 else '' for x in children(child(c,'fields') or [],'field')},'sheet':atom(child(c,'sheetpath') or [],'names')} for c in children(child(tree,'components'),'comp')}
    pins={}
    for net in children(child(tree,'nets'),'net'):
        name=atom(net,'name')
        for node in children(net,'node'):
            ref,num=atom(node,'ref'),atom(node,'pin');pins.setdefault(ref,{})[num]=name
    return comps,pins
def main():
    c,p=load();selected={r:{'component':v,'pins':p.get(r,{})} for r,v in c.items() if re.fullmatch('[CLRUF]11[0-9]+',r)}
    print('COUNT',len(c),len(selected));print('ROOT106NEW',json.dumps({r:selected.get(r) for r in ['L11001','C11088','C11089','C11090','C11091','C11092','C11093','C11094','U11038']},indent=2))
    dest=HERE/'integrated-source-inventory.json';dest.write_text(json.dumps({'source_hashes':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in (NET,PARSER)},'component_count':len(c),'all_component_refs':sorted(c),'power_namespace':selected},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
