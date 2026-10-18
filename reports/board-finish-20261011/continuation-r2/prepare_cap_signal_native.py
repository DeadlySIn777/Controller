"""Freeze exact native C11068 move plus separately audited ordinary signal route."""
import ast,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
import native_pose_signal_contract as V
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,indent=1)+'\n',encoding='utf-8')
def main():
    out=HERE/'cap-signal-native-r1';out.mkdir(exist_ok=False)
    source=HERE.parent/'power-audit/fag-r07-repair/staged/r07-four-path-fag-repaired.kicad_pcb'
    paths={'source':source,'r07':Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb'),'cap_audit':HERE/'coupled-recovery/aux-cap-native-independent-audit-r1.json','cap_composition':HERE/'coupled-recovery/aux-cap-native-composition-r1.json','cap_recipe':HERE/'coupled-recovery/aux-cap-bside-r4-exact-native-nets.json','native_attestation':HERE/'cap-native-r3/native-attestation.json','native_footprint':HERE/'cap-native-r3/C11068-native-flipped.chunk','cap_candidate':HERE/'coupled-recovery/aux-cap-native-r1-host-only.kicad_pcb','signal_audit':HERE/'escape-signal-audit-r1/audit.json','signal_plan':HERE/'new-via-escape-r2/result.json'}
    spec={'schema':'native-cap-and-signal-r1',**{k:{'path':str(p.resolve()),'sha256':sha(p)} for k,p in paths.items()}}
    candidate,proof=V.reconstruct(spec);board=out/'cap-signal-host-only.kicad_pcb';board.write_bytes(candidate);spec['candidate_sha256']=V.sha(candidate)
    inv=V.C.inventory(candidate);r07=V.C.inventory(paths['r07'].read_bytes());vias=[u for u,ch in inv[4].items() if u not in r07[4] and V.C.pcbtext.chunk_kind(ch)=='via'];spec.update(added_vias_from_r07=len(vias),added_via_uuids=vias)
    old=HERE/'measure_aux_r1.py';tree=ast.parse(old.read_text(encoding='utf-8'));changes=[]
    for n in tree.body:
        if isinstance(n,ast.ImportFrom) and n.module=='copper_recipe_contract':n.module='native_pose_signal_contract'
    changes.append('Exact owned footprint/copper constructor; preserves every unowned native entity')
    count=0
    for n in ast.walk(tree):
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)==2 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='pure-add candidate changes footprints/pads/poses':
            n.args=[ast.parse('construction["retained_footprints_exact_except_attested_owned_move"]',mode='eval').body,ast.Constant('Unowned footprint/pad/pose change')];count+=1
    if count!=1:raise ValueError('Exact footprint guard derivation mismatch')
    changes.append('Pure-add footprint equality replaced only by exact one-footprint native attestation and all-other-footprint byte equality')
    count=0
    for n in ast.walk(tree):
        if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Div) and isinstance(n.left,ast.Name) and n.left.id=='STAGE' and isinstance(n.right,ast.Constant) and n.right.value=='native_entry.py':
            n.left=ast.Name(id='OWN',ctx=ast.Load());n.right=ast.Constant('native_entry_width_r3.py');count+=1
        elif isinstance(n,ast.BinOp) and isinstance(n.op,ast.Div) and isinstance(n.left,ast.Name) and n.left.id=='STAGE' and isinstance(n.right,ast.Constant) and n.right.value=='ready-r1.json':
            n.left=ast.Name(id='OWN',ctx=ast.Load());n.right=ast.Constant('cap-signal-native-r1/ready-r1.json')
    if count!=2:raise ValueError('Native width helper derivation mismatch')
    tree.body.insert(next(i for i,n in enumerate(tree.body) if isinstance(n,ast.FunctionDef)),ast.parse('OWN=Path(__file__).resolve().parent').body[0])
    for n in tree.body:
        if isinstance(n,ast.FunctionDef) and n.name=='main':
            i=next(i for i,s in enumerate(n.body) if isinstance(s,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='args' for t in s.targets))
            n.body[i+1:i+1]=ast.parse('for key,value in vars(args).items():\n    if isinstance(value,Path):setattr(args,key,value.resolve())').body
            sources=next(s for s in ast.walk(n) if isinstance(s,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='sources' for t in s.targets))
            sources.value=ast.BinOp(left=sources.value,op=ast.Add(),right=ast.parse('[OWN/"native_pose_signal_contract.py",OWN/"cap-signal-native-r1/runner-derivation-owned-r1.json",OWN/"prepare_cap_signal_native.py"]',mode='eval').body)
    changes.extend(['Layer-specific KiCad10 via width getter; exact native UUID/net/position/drill and six-layer annuli checks retained','All CLI argument paths made absolute before clone/native launch','Own ready receipt freezes derived helpers and construction; all source, project, rules, native binary, both r06/live no-loss and unsuppressed DRC gates retained'])
    runner=HERE/'measure_cap_signal_r1.py';runner.write_text(ast.unparse(ast.fix_missing_locations(tree))+'\n',encoding='utf-8')
    deriv=out/'runner-derivation-owned-r1.json';write(deriv,{'original':str(old),'original_sha256':sha(old),'derived':str(runner),'derived_sha256':sha(runner),'changes':changes,'adopted':False})
    pins={str(p.resolve()):sha(p) for p in [*paths.values(),board,runner,old,deriv,Path(V.__file__),Path(__file__),HERE/'native_entry_width_r3.py']}
    for k in ('cap_audit','cap_composition','signal_audit','cap_recipe'):
        obj=json.loads(paths[k].read_bytes())
        for field in ('read_files_sha256','inputs'):
            if field in obj:pins.update(obj[field])
    spec['inputs']=pins;specpath=out/'construction.json';write(specpath,spec)
    proof=V.validate_construction(specpath,board);write(out/'host-construction-check.json',proof)
    stage=HERE.parent/'recovery-composite/c06/four-fag';ready=json.loads((stage/'ready-r1.json').read_bytes());ready['files'].update(V.construction_hashes(specpath));ready['files'][str((stage/'ready-r1.json').resolve())]=sha(stage/'ready-r1.json');ready['derived_owned_changes']=changes
    write(out/'ready-r1.json',ready)
    print(json.dumps({'candidate':str(board),'candidate_sha256':V.sha(candidate),'added_vias_from_r07':len(vias),'construction':proof}),flush=True)
if __name__=='__main__':main()
