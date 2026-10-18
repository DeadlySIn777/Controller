"""Read-only semantic current inventory from original ROOT106 fresh exported netlist."""
import ast, hashlib, json, re
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
BASE=HERE.parent.parent
PARITY=BASE/'parity-repair/root106'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ns={'re':re}; parser=PARITY/'tools/netlist_parity.py'
 tree=ast.parse(parser.read_text())
 declarations=[n for n in tree.body if (isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='TOKEN') or (isinstance(n,ast.FunctionDef) and n.name in ('sexpr_parse','child','children','atom','norm'))]
 exec(compile(ast.Module(body=declarations,type_ignores=[]),'pinned-portable-parser','exec'),ns)
 parse,child,children,atom=(ns[k] for k in ('sexpr_parse','child','children','atom'))
 net=PARITY/'source-export/fresh.net';root=parse(net.read_text())
 pins={}; nets={}
 for node in children(child(root,'nets'),'net'):
  name=atom(node,'name');rows=[{k:atom(n,k) for k in ('ref','pin','pinfunction','pintype')} for n in children(node,'node')];nets[name]=rows
  for row in rows:pins.setdefault(row['ref'],[]).append(dict(row,net=name))
 refs=set('U11003 U11004 U11005 U11006 F11002 F11003 R11011 R11018 U11009 U11017 U11018 U19028 U19004 U19005 U19006 U19007 U19018 R19019 R19026 R19032 R19038 R19059 U14026 U14027 R14057 R14063 J11003 J11004 J11005 J11006 JD09 U10004 U10009 U10017 U10022'.split())
 parts={}
 for c in children(child(root,'components'),'comp'):
  ref=atom(c,'ref')
  if ref in refs:parts[ref]={'value':atom(c,'value'),'footprint':atom(c,'footprint'),'fields':{atom(x,'name'):x[2] if len(x)>2 else '' for x in children(child(c,'fields') or [],'field')},'sheet':atom(child(c,'sheetpath') or [],'names'),'pins':pins[ref]}
 documents={}
 for rel in ['hardware/motherboard_safety_sensor/design.json','hardware/motherboard_probe_limit_upgrade/design.json','hardware/motherboard_power_entry/design.json','hardware/motherboard_do/design.json']:
  path=ROOT/rel;j=json.loads(path.read_bytes());p=j['components'];matches={}
  for ref in sorted(refs & p.keys()):
   d=p[ref]; n=parts[ref];matches[ref]={'source_mpn':n['fields'].get('MPN'),'document_mpn':d['mpn'],'source_value':n['value'],'document_value':d['value'],'mpn_matches':n['fields'].get('MPN')==d['mpn'],'value_matches_ignoring_whitespace':re.sub(r'\s','',n['value'])==re.sub(r'\s','',d['value']),'role':d.get('role'),'document_pins':d['pins']}
  documents[rel]={'sha256':sha(path),'selected_components':matches,'source_scope':'component metadata comparison, NOT entire current hierarchy equivalence'}
 identities={str(p.resolve()):sha(p) for p in [net,parser,PARITY/'source-export/receipt.json',PARITY/'source-identity.json',HERE/'source-inventory.json']}
 for rel in documents: identities[str((ROOT/rel).resolve())]=sha(ROOT/rel)
 report={'verdict':'READ_ONLY_SOURCE_TRACE','parts':parts,'document_comparisons':documents,'read_set_sha256_before':identities,'read_set_sha256_after':{p:sha(p) for p in identities},'native_jobs':0,'gpu_jobs':0,'source_or_board_changes':0}
 (HERE/'detail.json').write_text(json.dumps(report,indent=1)+'\n')
 print(json.dumps({'all_requested_original_refs_present':set(parts)==refs,'parts':len(parts),'current_document_mpn_mismatches':[(f,r) for f,v in documents.items() for r,d in v['selected_components'].items() if not d['mpn_matches']],'setting_resistors':{r:v['value'] for r,v in parts.items() if r.startswith('R')},'read_set_unchanged':identities==report['read_set_sha256_after']}))
if __name__=='__main__': main()
