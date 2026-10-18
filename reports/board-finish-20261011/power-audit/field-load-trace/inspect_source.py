"""Read-only original ROOT106 netlist/component/current-role inventory, no native imports."""
import ast
import hashlib
import json
from pathlib import Path
import re
HERE=Path(__file__).resolve().parent
BASE=HERE.parent.parent
PARITY=BASE/'parity-repair/root106'
NET=PARITY/'source-export/fresh.net'
PARSER=PARITY/'tools/netlist_parity.py'
SPEC=HERE.parent/'constraint-snapshot/0-field_pdn_spec.json'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 namespace={'re':re};tree=ast.parse(PARSER.read_text())
 declarations=[n for n in tree.body if (isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='TOKEN') or (isinstance(n,ast.FunctionDef) and n.name in ('sexpr_parse','child','children','atom','norm'))]
 exec(compile(ast.Module(body=declarations,type_ignores=[]),'pinned-portable-parser','exec'),namespace)
 parse,child,children,atom=(namespace[k] for k in ('sexpr_parse','child','children','atom'))
 root=parse(NET.read_text(encoding='utf-8'));component_nodes=children(child(root,'components'),'comp')
 components={atom(c,'ref'):{'value':atom(c,'value'),'footprint':atom(c,'footprint'),'datasheet':atom(c,'datasheet'),
  'fields':{atom(x,'name'):x[2] if len(x)>2 else '' for x in children(child(c,'fields') or [],'field')},
  'properties':{atom(x,'name'):atom(x,'value') for x in children(c,'property')},
  'sheet':atom(child(c,'sheetpath') or [],'names'),'libsource':child(c,'libsource')} for c in component_nodes}
 nets={};pins={}
 for net in children(child(root,'nets'),'net'):
  name=atom(net,'name');nodes=[{k:atom(node,k) for k in ('ref','pin','pinfunction','pintype')} for node in children(net,'node')]
  nets[name]=nodes
  for n in nodes:pins.setdefault(n['ref'],[]).append(dict(n,net=name))
 spec=json.loads(SPEC.read_bytes());refs={ref for r in spec['rails'] for c in r['clusters'] for ref,pin in c['pads']}
 refs|={ref for r in spec['rails'] for ref,pin in r['source']['pads']}
 refs|={'U11004','U11006','U11009','U11017','U11018','U19007','U19018','U19004','U19005','U19006','R11012','R11019'}
 # Include every resistor at exact ILIM nets of the selected switches.
 for ref in ('U11004','U11006','U19007','U19018','U19004','U19005','U19006','U14026','U14027'):
  for n in pins.get(ref,[]):
   if any(tag in n['net'].upper() for tag in ('ILIM','RCL','LIM')):
    refs|={x['ref'] for x in nets[n['net']]}
 selected={ref:{'component':components.get(ref),'pins':pins.get(ref,[])} for ref in sorted(refs)}
 role_inventory={}
 for rail in spec['rails']:
  normalized=rail['net'].replace('{slash}','/')
  record={'net':normalized,'design_a':rail['design_a'],'limit_a':rail['limit_a'],'source':rail['source'],'clusters':[]}
  for c in rail['clusters']:
   matches=[];missing=[]
   for ref,pin in c['pads']:
    found=[n for n in pins.get(ref,[]) if n['net'].replace('{slash}','/')==normalized and (pin=='*' or n['pin']==pin)]
    matches.extend(found)
    if not found:missing.append([ref,pin])
   record['clusters'].append({**c,'resolved_exact_net_roles':matches,'unresolved_requested_selectors':missing})
  role_inventory[rail['id']]=record
 identity_paths=[PARSER,NET,SPEC,PARITY/'source-export/receipt.json',PARITY/'source-identity.json',
  PARITY/'source/motherboard_power_entry.kicad_sch',PARITY/'source/motherboard_safety_sensor.kicad_sch',PARITY/'source/motherboard_do.kicad_sch',PARITY/'source/motherboard_terminals.kicad_sch']
 identities={str(p.resolve()):digest(p) for p in identity_paths}
 report={'verdict':'SOURCE_ROLE_INVENTORY_ONLY','original_ROOT106':True,'components':selected,'rail_roles':role_inventory,
  'source_sha256_before':identities,'source_sha256_after':{p:digest(p) for p in identities},'native_jobs':0,'gpu_jobs':0}
 (HERE/'source-inventory.json').write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'components':len(selected),'rails':{rid:{'documented_sum':sum(c['amps'] for c in r['clusters']),'unresolved_selectors':[u for c in r['clusters'] for u in c['unresolved_requested_selectors']]} for rid,r in role_inventory.items()},
  'ilim_parts':{ref:v for ref,v in selected.items() if ref.startswith('R') and any('ILIM' in n['net'] for n in v['pins'])},'receipt':str(HERE/'source-inventory.json')}))
if __name__=='__main__':main()
