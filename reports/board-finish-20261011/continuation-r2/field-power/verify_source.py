"""Independent selected-sheet pin/wire/label graph check; native export is separate."""
import ast, hashlib,json,re
from pathlib import Path
from inventory import HERE,BASE,PARSER,NET,BOARD,load,sha

SOURCE=BASE/'parity-repair/root106/source'
def parser():
 ns={'re':re};tree=ast.parse(PARSER.read_text(encoding='utf-8'))
 declarations=[n for n in tree.body if (isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='TOKEN') or (isinstance(n,ast.FunctionDef) and n.name in ('sexpr_parse','child','children','atom','norm'))]
 exec(compile(ast.Module(body=declarations,type_ignores=[]),'frozen-parser','exec'),ns)
 return ns
P=parser();parse,child,children,atom=[P[k] for k in ['sexpr_parse','child','children','atom']]
def point(n):return tuple(round(float(v),6) for v in n[1:3])
def sheet_graph(text):
 root=parse(text);lib=child(root,'lib_symbols');libpins={}
 for sym in children(lib,'symbol'):
  pinrows=[]
  for unit in children(sym,'symbol'):
   for pin in children(unit,'pin'):
    pinrows.append((atom(pin,'number'),point(child(pin,'at'))))
  libpins[sym[1]]=pinrows
 parent={}
 def find(p):
  parent.setdefault(p,p)
  while parent[p]!=p:parent[p]=parent[parent[p]];p=parent[p]
  return p
 def union(a,b):parent[find(a)]=find(b)
 for wire in children(root,'wire'):
  pts=children(child(wire,'pts'),'xy');a,b=[point(p) for p in pts];union(a,b)
 labels={}
 for kind in ['label','hierarchical_label','global_label']:
  for n in children(root,kind):labels.setdefault(find(point(child(n,'at'))),set()).add((kind,n[1]))
 symbols={};uuids=[]
 for sym in children(root,'symbol'):
  if child(sym,'lib_id') is None:continue
  props={p[1]:p[2] for p in children(sym,'property')};ref=props['Reference']
  if ref in symbols:raise ValueError('Duplicate reference '+ref)
  loc=child(sym,'at');x,y=point(loc)
  if len(loc)>3 and float(loc[3])!=0:raise ValueError('This source graph requires explicit unrotated symbol')
  row={}
  for pin,(px,py) in libpins[atom(sym,'lib_id')]:
   key=pin;p=(round(x+px,6),round(y-py,6));row[key]=sorted(labels.get(find(p),set()))
  symbols[ref]=row;uuids.append(atom(sym,'uuid'))
 if len(uuids)!=len(set(uuids)):raise ValueError('Duplicate symbol UUID')
 return symbols
def baseline_maps():
 _,pins,_=load();graphs={name:sheet_graph((SOURCE/name).read_text(encoding='utf-8')) for name in ['motherboard_power_entry.kicad_sch','motherboard_do.kicad_sch']};maps={}
 for name,g in graphs.items():
  mp={}
  for ref,ps in g.items():
   bypin={p['pin']:p['net'] for p in pins.get(ref,[])}
   for pin,labels in ps.items():
    if pin not in bypin:continue
    for typ,label in labels:
     key=(typ,label)
     if key in mp and mp[key]!=bypin[pin]:raise ValueError(f'Baseline alias conflict{name}:{key}')
     mp[key]=bypin[pin]
  maps[name]=mp
 return graphs,maps,pins
def resolve_label(maps,name,typ,label):
 if typ=='global_label':return label
 direct=maps[name].get((typ,label))
 if direct is not None:return direct
 # Local and hierarchical labels with the same text share a sheet-local net.
 # Accept that alias only when the preserved export supplies one unique net.
 candidates={v for (kind,text),v in maps[name].items() if kind in ('label','hierarchical_label') and text==label}
 return next(iter(candidates)) if len(candidates)==1 else None

def verify_variant(directory,receipt=None,text_overrides=None):
 if receipt is None:receipt=json.loads((directory/next((n for n in ['receipt-r3.json','receipt-r2.json','receipt.json'] if (directory/n).exists()))).read_text(encoding='utf-8'))
 original,maps,pins=baseline_maps();changed={(x['ref'],x['pin']):x['to'] for x in receipt['pin_net_changes']};expected={};actual={};missing=[]
 for name in original:
  text=(text_overrides or {}).get(name,(directory/'source'/name).read_text(encoding='utf-8'));g=sheet_graph(text)
  for ref in original[name]:
   for row in pins.get(ref,[]):
    pin=row['pin'];key=(ref,pin)
    if pin not in original[name][ref]:continue
    labels=g[ref][pin]
    if not labels:
     # Original NCs retain no named label; compare their graph condition.
     if original[name][ref][pin]:missing.append(key)
     continue
    wanted=changed.get(key,row['net']);resolved=[]
    for typ,label in labels:
     resolved.append(resolve_label(maps,name,typ,label))
    actual[key]=resolved;expected[key]=wanted
  for ref,part in receipt['new_components'].items():
   if ref not in g:continue
   for pin,wanted in part['pins'].items():
    key=(ref,pin);labels=g[ref][pin]
    if wanted is None:
     if labels:missing.append(key)
     continue
    resolved=[resolve_label(maps,name,typ,label) for typ,label in labels]
    actual[key]=resolved;expected[key]=wanted
 fails=[{'ref':k[0],'pin':k[1],'expected':v,'labels_resolve':actual[k]} for k,v in expected.items() if actual[k]!=[v]]
 if missing:fails.append({'unlabelled_changed_or_extra_pin':missing})
 return {'verdict':'PASS' if not fails else 'FAIL','checked_named_pin_roles':len(expected),'failures':fails,'native_export':'NOT_RUN_HOST_GRAPH_ONLY'}
def main():
 records={}
 for variant in ['a-prereg-source','ab-prereg-split-source']:
  d=HERE/variant;records[variant]=verify_variant(d);assert records[variant]['verdict']=='PASS',records[variant]
 (HERE/'source-pin-graph-r1.json').write_text(json.dumps(records,indent=1)+'\n',encoding='utf-8')
 print(json.dumps(records))
if __name__=='__main__':main()
