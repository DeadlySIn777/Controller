"""Nominate physically contacted return annuli with a finite plane interior."""
import hashlib,json,runpy
from pathlib import Path
H=Path(__file__).resolve().parent
def main():
    source=H/'nominate_ao1_returns_r1.py';target=H/'nominate_ao1_returns_r2.py'
    if target.exists():raise ValueError('Fresh return nomination helper required')
    code=source.read_text(encoding='utf-8')
    changes={"OUT=HERE/'ao1-return-nomination-r1'":"OUT=HERE/'ao1-return-nomination-r2'","for radius in (.85,.9,.95,1.):":"for radius in (.85,.9,.95,.99):","at=tuple(round(q,9) for q in":"at=tuple(round(q,6) for q in","if not why and not all(refs[layer].covers(body.buffer(.025)) for layer in ('F.Cu','B.Cu')):why.append('Not fully rooted in both reference planes')":"if not why and not all(refs[layer].buffer(-.075).intersection(body.difference(hole)).area>=.004 for layer in ('F.Cu','B.Cu')):why.append('No finite 0.15-mm source-rooted plane interior at annulus')"}
    for a,b in changes.items():
        if code.count(a)!=1:raise ValueError('Exact nomination anchor differs: '+a)
        code=code.replace(a,b)
    code=code.replace("# Full guarded new annulus body must land in both actual source-rooted planes.","# Nominate partial annular contact only where both source-rooted planes contain finite .15-mm interior; final drilled graph and native contact/current remain required.")
    target.write_text(code,encoding='utf-8')
    receipt={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'derived_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'changes':changes,'source_and_final_all_drilled_graph_old_fill_contacts_clearance_checks_unchanged':True,'whole_guarded_return_disk_containment_was_nomination_only':'replaced by finite source-rooted annular interior; no final native/electrical claim','all_new_return_sites_quantized_to_native_1nm':True,'old_r1_incomplete_preserved':True}
    (H/'ao1-return-nomination-r2-derivation.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')
    runpy.run_path(str(target),run_name='__main__')
if __name__=='__main__':main()
