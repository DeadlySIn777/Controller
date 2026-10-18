import hashlib,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;p=HERE/'apply_cap_native.py';q=HERE/'apply_cap_native_r3.py'
raw=p.read_text(encoding='utf-8').replace("OUT=HERE/'cap-native-r1'","OUT=HERE/'cap-native-r3'")
old="or p.GetLayer()!=pcbnew.B_Cu:raise ValueError"
new="or not p.IsOnLayer(pcbnew.B_Cu) or p.IsOnLayer(pcbnew.F_Cu):raise ValueError"
if raw.count(old)!=1:raise ValueError('Native pad layer attestation derivation differs')
q.write_text(raw.replace(old,new),encoding='utf-8');out=HERE/'cap-native-r3';out.mkdir();project=out/'project';shutil.copytree(HERE/'cap-native-r1/project',project)
paths=[x for x in project.rglob('*') if x.is_file()]+[q,Path(__file__),HERE/'coupled-recovery/aux-cap-bside-r3.json',HERE/'coupled-recovery/aux-cap-recipe-audit-r1.json',HERE/'cap-native-r2/pad-diagnostic.json',Path('Z:/pcb-runs/claude-finish/tools/integrate/pcbtext.py'),Path('C:/Program Files/KiCad/10.0/bin/python.exe'),Path('C:/Program Files/KiCad/10.0/bin/Lib/site-packages/_pcbnew.pyd')]
(out/'inputs.json').write_text(json.dumps({'files':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths},'source_helper_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'only_change':'PAD actual Cu membership is tested with IsOnLayer(B.Cu) and !IsOnLayer(F.Cu); PAD.GetLayer returns nominal0 even for actualB SMD','slot':'existing test KiCad','new_slots':0,'adopted':False},indent=1)+'\n',encoding='utf-8')
print('Prepared actual-layer native pad attestation')
