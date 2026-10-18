"""Read-only exact original ROOT106 field-power port inventory. No KiCad imports."""
import ast, hashlib, json, re
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
NET=BASE/'parity-repair/root106/source-export/fresh.net'
PARSER=BASE/'parity-repair/root106/tools/netlist_parity.py'
BOARD=BASE/'power-audit/fag-r07-repair/staged/r07-four-path-fag-repaired.kicad_pcb'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load():
 ns={'re':re}; tree=ast.parse(PARSER.read_text(encoding='utf-8'))
 declarations=[n for n in tree.body if (isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='TOKEN') or (isinstance(n,ast.FunctionDef) and n.name in ('sexpr_parse','child','children','atom','norm'))]
 exec(compile(ast.Module(body=declarations,type_ignores=[]),'pinned-root106-parser','exec'),ns)
 parse,child,children,atom=(ns[k] for k in ('sexpr_parse','child','children','atom'))
 root=parse(NET.read_text(encoding='utf-8')); pins={};nets={}; parts={}
 for node in children(child(root,'nets'),'net'):
  name=atom(node,'name'); rows=[{k:atom(n,k) for k in ('ref','pin','pinfunction','pintype')} for n in children(node,'node')];nets[name]=rows
  for row in rows:pins.setdefault(row['ref'],[]).append(dict(row,net=name))
 for c in children(child(root,'components'),'comp'):
  ref=atom(c,'ref');parts[ref]={'value':atom(c,'value'),'footprint':atom(c,'footprint'),'fields':{atom(x,'name'):x[2] if len(x)>2 else '' for x in children(child(c,'fields') or [],'field')},'sheet':atom(child(c,'sheetpath') or [],'names'),'pins':pins.get(ref,[])}
 return parts,pins,nets
def main():
 before={str(p):sha(p) for p in (NET,PARSER,BOARD)}
 parts,pins,nets=load()
 wanted=['FIELD_A_24V_PROTECTED','FIELD_B_24V_PROTECTED','FIELD_5V','FIELD_B_5V_PRE','DOA_FIELD_3V3','DOB_FIELD_3V3','AUX_24V_A','AUX_24V_B','AUX_5V_A','AUX_5V_B','PRB0_24V','PRB1_24V','SENS24_G0','SENS24_G1','SENS24_G2','SAFE_24V','ARM_LAMP']
 rails={tag:{net:rows for net,rows in nets.items() if net.split('{slash}')[-1]==tag} for tag in wanted}
 refs={n['ref'] for bynet in rails.values() for rows in bynet.values() for n in rows}
 neighbors={n['ref'] for ref in refs for pin in pins[ref] for n in nets[pin['net']]}
 result={'schema':'root106-complete-field-port-inventory-v2','rails':rails,'parts':{ref:parts[ref] for ref in sorted(refs|neighbors)},'inputs_before':before,'inputs_after':{p:sha(p) for p in before},'native_jobs':0,'board_or_source_edits':0}
 assert result['inputs_before']==result['inputs_after']
 (HERE/'inventory.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'rails':{k:sum(map(len,v.values())) for k,v in rails.items()},'parts':len(result['parts']),'inputs_unchanged':True}))
if __name__=='__main__':main()
