"""Read actual net/classes of overlapping negative-control coupon tracks."""
import json,sys
from pathlib import Path
import pcbnew
boardpath=Path(sys.argv[1]);projectpath=boardpath.with_suffix('.kicad_pro');m=pcbnew.GetSettingsManager()
if not m.LoadProject(str(projectpath)):raise ValueError('Native coupon project load failed')
p=m.GetProject(str(projectpath));b=pcbnew.LoadBoard(str(boardpath));b.SetProject(p)
rows=[{'uuid':str(t.m_Uuid.AsString()),'raw_native_net':str(t.GetNetname()),'actual_effective_netclass':str(t.GetNetClassName()),'width_mm':pcbnew.ToMM(t.GetWidth())} for t in b.GetTracks()]
Path(sys.argv[2]).write_text(json.dumps({'rows':rows,'no_save_or_refill':True},indent=1)+'\n',encoding='utf-8');print(json.dumps(rows),flush=True)
b.ClearProject();m.UnloadProject(p,False)
