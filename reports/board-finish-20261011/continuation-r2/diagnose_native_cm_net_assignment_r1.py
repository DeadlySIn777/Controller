"""Read-only observation of native via nets before and after project binding."""
import hashlib,json,sys
from pathlib import Path
import pcbnew
boardpath=Path(sys.argv[1]);output=Path(sys.argv[2])
expected=json.loads(Path(sys.argv[3]).read_bytes())
if hashlib.sha256(boardpath.read_bytes()).hexdigest()!=expected['board_sha256']:raise ValueError('Diagnostic board identity differs')
targets={r['uuid']:r for r in expected['added_vias']}
b=pcbnew.LoadBoard(str(boardpath))
def observe(phase):
    return {'phase':phase,'via_rows':[{'uuid':str(t.m_Uuid.AsString()),'net_raw':str(t.GetNetname()),'net_code':int(t.GetNetCode()),'expected':targets[str(t.m_Uuid.AsString())]} for t in b.GetTracks() if isinstance(t,pcbnew.PCB_VIA) and str(t.m_Uuid.AsString()) in targets]}
rows=[observe('immediate_after_LoadBoard')]
manager=pcbnew.GetSettingsManager();manager.LoadProject(str(boardpath.with_suffix('.kicad_pro')))
project=manager.GetProject(str(boardpath.with_suffix('.kicad_pro')));b.SetProject(project)
rows.append(observe('immediate_after_SetProject'))
output.write_text(json.dumps({'board_sha256':expected['board_sha256'],'phases':rows,'fill_connectivity_or_save_requested':False},indent=1)+'\n',encoding='utf-8')
print(json.dumps({'phases':[{'phase':r['phase'],'mismatches':[t for t in r['via_rows'] if t['net_raw'].replace('{slash}','/')!=t['expected']['net']]} for r in rows]}),flush=True)
b.ClearProject();manager.UnloadProject(project,False)
