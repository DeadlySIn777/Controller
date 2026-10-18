"""Inspect current-source digital roles omitted from historical ROOT104 catalog."""
import ast,hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
NET=HERE/'cap-signal-native-r1/measure/fresh.net';PARSER=BASE/'parity-repair/root106/tools/netlist_parity.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    paths=[NET,PARSER,HERE/'remaining-net-census-r2.json',HERE/'native-198b-geometry/geometry.json'];pins={str(p.resolve()):sha(p) for p in [*paths,Path(__file__)]}
    tree=ast.parse(PARSER.read_text(encoding='utf-8'));ns={'re':re}
    nodes=[n for n in tree.body if (isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='TOKEN') or (isinstance(n,ast.FunctionDef) and n.name in ('sexpr_parse','child','children','atom','norm'))]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'current-source-net-roles','exec'),ns)
    parse,child,children,atom=[ns[k] for k in ('sexpr_parse','child','children','atom')];root=parse(NET.read_text(encoding='utf-8'))
    comps={atom(c,'ref'):{'value':atom(c,'value'),'sheet':atom(child(c,'sheetpath') or [],'names')} for c in children(child(root,'components'),'comp')}
    nets={atom(n,'name'):[{k:atom(v,k) for k in ('ref','pin','pinfunction','pintype')} for v in children(n,'node')] for n in children(child(root,'nets'),'net')}
    census=json.loads(paths[2].read_bytes());geom=json.loads(paths[3].read_bytes());domains={ns['norm'](n):d for n,d in geom['nets'].items()}
    rows=[]
    signal=re.compile(r'(HEALTH|READY|PERMIT|REQUEST|ALARM|ENABLE|FAULT|INHIBIT|_LOGIC$|_HOST$|_MCU$|_N$)',re.I)
    excluded=re.compile(r'(CLK|SCLK|SCK|XTAL|OSC|USB|HDMI|MDI|_SW$|PHASE|BOOT|VREF|DVDT|ILIM|AGND|_COM$|_GND$|_RTN$|_0V$|_[0-9]+V|POWER|PWR|SUPPLY|ANALOG)',re.I)
    for row in census['rows']:
        n=row['normalized_net']
        if row['category']!='unclassified_ROOT106' or domains.get(n)!='DOM_LOGIC' or not signal.search(n) or excluded.search(n):continue
        ports=nets.get(n)
        if not ports:raise ValueError('Current-source role missing '+n)
        if any(p['pintype'] in ('power_in','power_out') for p in ports):continue
        enriched=[{**p,**comps[p['ref']]} for p in ports]
        rows.append({**row,'domain':'DOM_LOGIC','current_source_ports':enriched,'classification':'SOURCE_ROLE_REVIEW_REQUIRED'})
    target=HERE/'current-logic-source-role-inventory-r1.json'
    if target.exists():raise ValueError('Fresh inventory required')
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Source changed '+p)
    target.write_text(json.dumps({'rows':rows,'inputs':pins,'native_jobs':0,'board_edits':0,'source_role_names_are_not_automatic_routing_authority':True},indent=1)+'\n',encoding='utf-8')
    for row in rows:
        print(row['net'],row['missing_joins'],[(p['ref'],p['pin'],p['value'],p['pinfunction'],p['pintype']) for p in row['current_source_ports'] if p['ref'].startswith('U')],flush=True)
    print('CURRENT_SOURCE_CANDIDATES',len(rows),flush=True)
if __name__=='__main__':main()
