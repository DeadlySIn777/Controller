import hashlib,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=HERE/'apply_cap_native.py';q=HERE/'apply_cap_native_r2.py';raw=p.read_text(encoding='utf-8').replace("OUT=HERE/'cap-native-r1'","OUT=HERE/'cap-native-r2'")
old="if observed!=before or at!=expected[uid]['at_mm'] or p.GetLayer()!=pcbnew.B_Cu:raise ValueError('Native transformed pad differs '+uid+' '+repr(at))"
new="""if observed!=before or at!=expected[uid]['at_mm'] or p.GetLayer()!=pcbnew.B_Cu:
                write(OUT/'pad-diagnostic.json',{'uuid':uid,'before':before,'after':observed,'at':at,'expected_at':expected[uid]['at_mm'],'GetLayer':int(p.GetLayer()),'IsOnLayer_F':p.IsOnLayer(pcbnew.F_Cu),'IsOnLayer_B':p.IsOnLayer(pcbnew.B_Cu)})
                raise ValueError('Native transformed pad differs '+uid+' '+repr(at))"""
if old not in raw:raise ValueError('Native diagnostic derivation differs')
q.write_text(raw.replace(old,new),encoding='utf-8');out=HERE/'cap-native-r2';out.mkdir();project=out/'project';shutil.copytree(HERE/'cap-native-r1/project',project)
paths=[x for x in project.rglob('*') if x.is_file()]+[q,Path(__file__),HERE/'coupled-recovery/aux-cap-bside-r3.json',HERE/'coupled-recovery/aux-cap-recipe-audit-r1.json',Path('Z:/pcb-runs/claude-finish/tools/integrate/pcbtext.py'),Path('C:/Program Files/KiCad/10.0/bin/python.exe'),Path('C:/Program Files/KiCad/10.0/bin/Lib/site-packages/_pcbnew.pyd')]
(out/'inputs.json').write_text(json.dumps({'files':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths},'slot':'existing test KiCad','new_slots':0,'adopted':False},indent=1)+'\n',encoding='utf-8')
print('Prepared distinct native pad diagnostic')
