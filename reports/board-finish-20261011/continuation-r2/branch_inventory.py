"""Portable read-only source inventory for remaining field branch loads."""
import ast,hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'parity-repair/root106'
NET=BASE/'source-export/fresh.net';PARSER=BASE/'tools/netlist_parity.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    before={str(p):sha(p) for p in [NET,PARSER]}
    tree=ast.parse(PARSER.read_text(encoding='utf-8'));ns={'re':re}
    nodes=[n for n in tree.body if (isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='TOKEN') or (isinstance(n,ast.FunctionDef) and n.name in ('sexpr_parse','child','children','atom','norm'))]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'portable-parser','exec'),ns)
    parse,child,children,atom=[ns[k] for k in ('sexpr_parse','child','children','atom')]
    root=parse(NET.read_text(encoding='utf-8'))
    comps={atom(c,'ref'):{'value':atom(c,'value'),'datasheet':atom(c,'datasheet'),'fields':{atom(x,'name'):x[2] if len(x)>2 else '' for x in children(child(c,'fields') or [],'field')},'sheet':atom(child(c,'sheetpath') or [],'names')} for c in children(child(root,'components'),'comp')}
    nets={};pins={}
    for n in children(child(root,'nets'),'net'):
        name=atom(n,'name');row=[{k:atom(v,k) for k in ('ref','pin','pinfunction','pintype')} for v in children(n,'node')];nets[name]=row
        for v in row:pins.setdefault(v['ref'],[]).append({**v,'net':name})
    switchrefs=['U19004','U19005','U19006','U14026','U14027','U19007','U19018']
    railnames={p['net'] for r in switchrefs for p in pins[r] if re.sub(r'_\d+$','',p['pinfunction']) in ('IN','OUT','VS','GND','EP_GND')}
    if len(railnames)!=13:raise ValueError('Branch port count mismatch: '+str(sorted(railnames)))
    # Include every passive directly touching a branch and all resistive monitor paths two hops away.
    refs=set(switchrefs)
    frontier=set(railnames)
    for depth in range(3):
        rr={n['ref'] for name in frontier for n in nets[name] if n['ref'].startswith(('R','U','J','D'))}
        refs|=rr
        frontier={p['net'] for r in rr if r.startswith('R') for p in pins[r]}
    selected={r:{**comps[r],'pins':pins.get(r,[])} for r in sorted(refs)}
    out=HERE/'branch-load-audit';out.mkdir(exist_ok=True)
    target=out/'inventory-r2.json'
    if target.exists():raise ValueError('Existing inventory')
    report={'source_sha256_before':before,'source_sha256_after':{str(p):sha(p) for p in [NET,PARSER]},'selected_components':selected,'branch_rails':sorted(railnames),'native_jobs':0}
    target.write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8')
    for r in switchrefs:print(r,comps[r]['value'],[(p['pin'],p['pinfunction'],p['net'].split('/')[-1]) for p in pins[r]])
    print('Branch passives:')
    for r,c in selected.items():
        if r.startswith('R') and any(p['net'] in railnames and not any(tag in p['net'] for tag in ('FIELD_GND','FIELD_B_0V')) for p in c['pins']):print(r,c['value'],c['fields'].get('MPN'),[(p['pin'],p['net'].split('/')[-1]) for p in c['pins']])
if __name__=='__main__':main()
