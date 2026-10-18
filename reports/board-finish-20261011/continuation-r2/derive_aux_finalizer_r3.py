"""Derive an explicit-layer native retry, preserving failed r1/r2 outputs."""
import ast,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    src=HERE/'finalize_aux_native_r2.py';raw=src.read_text(encoding='utf-8');tree=ast.parse(raw)
    for n in ast.walk(tree):
        if isinstance(n,ast.Constant) and isinstance(n.value,str):
            n.value=n.value.replace('source-proof-r2.json','source-proof-r3.json').replace('finalizer-inputs-r2.json','finalizer-inputs-r3.json').replace('proof-r2.json','proof-r3.json').replace('finalizer-status-r2.json','finalizer-status-r3.json').replace('aux-native-finalizer-r2','aux-native-finalizer-r3')
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');at=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='proof' for t in n.targets))
    code='''
source_tree=ast.parse(Path(M.__file__).read_text(encoding='utf-8'))
source_fn=next(n for n in source_tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_source_checks')
source_changed=[]
for node in ast.walk(source_fn):
    if isinstance(node,ast.Constant) and isinstance(node.value,str):
        replacements={'native_entry.py':str((HERE/'native_entry_width_r3.py').resolve()),'source-export.log':'source-export-r3.log','fresh.net':'fresh-r3.net','native-parity.json':'native-parity-r3.json','native-parity.log':'native-parity-r3.log'}
        if node.value in replacements:
            source_changed.append([node.value,replacements[node.value]])
            node.value=replacements[node.value]
source_namespace=dict(M.__dict__)
exec(compile(ast.fix_missing_locations(ast.Module(body=[source_fn],type_ignores=[])),'aux-r3-native-source-check','exec'),source_namespace)
M.run_source_checks=source_namespace['run_source_checks']
retry_contract={'schema':'aux-native-layer-width-retry-r3','original_runner_sha256':sha(M.__file__),'native_helper_sha256':sha(HERE/'native_entry_width_r3.py'),'native_helper_derivation_sha256':sha(HERE/'native-width-derivation-r3.json'),'source_check_changes':source_changed,'derived_source_check':ast.unparse(source_fn),'original_assertion_stop_receipt':str((OUT/'native-assert-stop-r2.json').resolve()),'all_layer_annuli_identity_and_source_gates_retained':True,'native_refill_repeated':False,'adopted':False}
write(OUT/'source-check-derivation-r3.json',retry_contract)
'''
    fn.body[at:at]=ast.parse(code).body
    out=HERE/'finalize_aux_native_r3.py';out.write_text(ast.unparse(ast.fix_missing_locations(tree))+'\n',encoding='utf-8')
    (HERE/'finalizer-derivation-r3.json').write_text(json.dumps({'source_path':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'derived_path':str(out),'derived_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'changes':['Distinct r3 output names preserve all original failures','Native source check uses corrected explicit-layer width helper','Original board measurement and complete dual no-loss/DRC/project/source gates reused']},indent=1)+'\n',encoding='utf-8')
if __name__=='__main__':main()
