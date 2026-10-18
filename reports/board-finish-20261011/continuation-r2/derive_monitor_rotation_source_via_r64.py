"""Bind rotated monitor to the exact separately proven ordinary FG landing."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=H/'nominate_monitor_resistor_rotation_r61.py';dst=H/'nominate_monitor_rotation_source_via_r64.py';assert not dst.exists();s=src.read_text().replace('field-monitor-R9026-in-place-rotation-r61','field-monitor-R9026-rotation-source-via-r64').replace('controller-monitor-rotation-r61/','controller-monitor-rotation-r64/').replace('R61_','R64_')
a="target=next(p for p in h['pads']if(p['ref'],p['num'])==('U9003','7'));assert any(q['kind']=='pad'and q['uuid']==target['uuid']for q in source),'Ground target must already be physically J11003.2-rooted'"
b="landing=H/'field-monitor-ground-counterfactual-r51';lr=json.loads((landing/'receipt.json').read_bytes());ld=pickle.loads((landing/'proposed-discrete.pkl').read_bytes());assert sha(landing/'proposed-discrete.pkl')==lr['proposed_discrete_sha256']and len(ld['vias'])==1;v=ld['vias'][0];assert v['uuid']=='1069fdeb-c67f-58d9-bb46-c0c33ccfdda0'and v['d']==.5 and v['drill']==.2 and len(v['flashed'])==6 and C.norm(v['net'])==ground\n+ ann=N.bounded_disk(v,.25).difference(N.bounded_disk(v,.1));sourceIn1=unary_union([q['shape']for q in source if q['kind']=='fill'and q['layer']=='In1.Cu']);assert ann.intersection(sourceIn1).area>.01,'Exact unchanged actual J3-rooted In1 annular landing required'\n+ h['vias'].append(v);target={'ref':'@NEW_ordinary_FG_landing','uuid':v['uuid'],'x':v['x'],'y':v['y']}"
assert a in s;assert b.count('\n+ ')==2;b=b.replace('\n+ ','\n ');s=s.replace(a,b)
a="delta={'tracks':new,'vias':[],";assert a in s;s=s.replace(a,"delta={'tracks':new,'vias':[v],")
a="'new_holes':0";assert a in s;s=s.replace(a,"'new_holes':1,'ordinary_via_annular_actual_J3_source_overlap_mm2':ann.intersection(sourceIn1).area,'actual_all6_flash_SMD_aperture_native_contract':'OPEN'")
compile(s,str(dst),'exec');dst.write_text(s)
(H/'monitor-rotation-r64-derivation.json').write_text(json.dumps({'source_sha256':sha(src),'derived_sha256':sha(dst),'geometry_delta':'Same in-place180deg resistor rotation and UV2mm F path, ground lands on the exact previously source-positive ordinary R51 barrel. All R51 temporary UV deletion/newgroundtracks are discarded; no old Cu except ownedb7 is removed.','native_jobs':0,'adopted':False},indent=1)+'\n');print(dst)
