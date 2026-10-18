"""Freeze a native AUX measurement recipe and derive its measured runner."""
import ast,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
import copper_recipe_contract as V
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    out=HERE/'aux-native-r1';out.mkdir(exist_ok=False)
    audit_path=HERE/'coupled-recovery/aux-exact-audit-r3.json';recipe_path=HERE/'coupled-recovery/aux-power-escape-r2.json';audit=json.loads(audit_path.read_bytes());recipe=json.loads(recipe_path.read_bytes())
    candidate=HERE/'coupled-recovery/aux-power-escape-r2-host-only.kicad_pcb';source=HERE.parent/'power-audit/fag-r07-repair/staged/r07-four-path-fag-repaired.kicad_pcb'
    original=Path('Z:/pcb-runs/claude-finish/integrate/revs/r06-stitch-plane-pads-2.kicad_pcb');r07=Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb')
    src=HERE.parent/'recovery-composite/c06/four-fag/measure_combined_r1.py';tree=ast.parse(src.read_text(encoding='utf-8'));changes=[]
    stage=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='STAGE' for x in n.targets));stage.value=ast.Call(func=ast.Name(id='Path',ctx=ast.Load()),args=[ast.Constant(value=str(src.parent.resolve()))],keywords=[]);changes.append('Resource STAGE retains original frozen source/project/native-entry paths')
    index=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.FunctionDef));tree.body.insert(index,ast.ImportFrom(module='copper_recipe_contract',names=[ast.alias(name='validate_construction'),ast.alias(name='construction_hashes')],level=0));changes.append('Exact copper-replacement constructor replaces pure-add constructor; other guards unchanged')
    count=0
    for fn in tree.body:
        if isinstance(fn,ast.FunctionDef) and fn.name in ('prepare_source','run_source_checks'):
            for node in ast.walk(fn):
                if isinstance(node,ast.Compare) and len(node.comparators)==1 and isinstance(node.comparators[0],ast.Constant) and node.comparators[0].value==7:
                    expr='json.loads(args.construction.read_bytes())["added_vias_from_r07"]' if fn.name=='prepare_source' else 'len(json.loads((out / "native-via-spec.json").read_bytes())["added_vias"])'
                    node.comparators[0]=ast.parse(expr,mode='eval').body;count+=1
    if count!=2:raise ValueError('Native runner derivation no longer matches')
    changes.append('Two via-count checks use the frozen complete candidate-minus-r07 via inventory; per-via native identity/flash checks retained')
    runner=HERE/'measure_aux_r1.py';runner.write_text(ast.unparse(ast.fix_missing_locations(tree))+'\n',encoding='utf-8')
    der=HERE/'native-runner-derivation-r1.json';der.write_text(json.dumps({'original_path':str(src.resolve()),'original_sha256':sha(src),'derived_path':str(runner),'derived_sha256':sha(runner),'changes':changes,'all_other_native_guards_unchanged':True,'adopted':False},indent=1)+'\n',encoding='utf-8')
    pins=dict(recipe['read_files_sha256']);pins.update(audit['read_files_sha256'])
    for p in [audit_path,recipe_path,candidate,source,original,r07,src,runner,der,Path(V.__file__),Path(__file__)]:pins[str(p.resolve())]=sha(p)
    before,after=V.C.inventory(r07.read_bytes()),V.C.inventory(candidate.read_bytes());vias=[u for u,ch in after[4].items() if u not in before[4] and V.C.pcbtext.chunk_kind(ch)=='via']
    ident=lambda p:{'path':str(p.resolve()),'sha256':sha(p)}
    spec={'schema':'native-aux-recipe-r1','source':ident(source),'original_r06':ident(original),'r07':ident(r07),'audit':ident(audit_path),'recipe':ident(recipe_path),'candidate':ident(candidate),'added_vias_from_r07':len(vias),'added_via_uuids':vias,'inputs':pins,'native_jobs':0,'adopted':False}
    specpath=out/'construction.json';specpath.write_text(json.dumps(spec,indent=1)+'\n',encoding='utf-8');validation=V.validate_construction(specpath,candidate)
    (out/'host-construction-check.json').write_text(json.dumps(validation,indent=1)+'\n',encoding='utf-8');print(json.dumps({'construction':str(specpath),'candidate':str(candidate),'added_vias':len(vias),'validation':validation}),flush=True)
if __name__=='__main__':main()
