"""Demonstrate native DRC catches a too-wide small-pad escape on a COPY."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import pcbnew

root=Path(__file__).resolve().parent
source=root/'routed-v2/motion-card-power-routed.kicad_pcb'
bundle=json.loads((root/'routed-v2/route-bundle.json').read_text())
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
out=root/'negative-control'
if out.exists():
    raise FileExistsError('Preserve existing negative-control evidence')
out.mkdir()
target=out/'too-wide-pad-escape.kicad_pcb'
shutil.copy2(source.with_suffix('.kicad_pro'),target.with_suffix('.kicad_pro'))
shutil.copy2(source.parent/'fp-lib-table',out/'fp-lib-table')
for folder in source.parent.glob('*.pretty'):
    shutil.copytree(folder,out/folder.name)
board=pcbnew.LoadBoard(str(source))
uid=bundle['selected_connections'][0]['segments'][0]['uuid']
track=next(t for t in board.GetTracks() if t.m_Uuid.AsString()==uid)
assert abs(pcbnew.ToMM(track.GetWidth())-.2)<.000001
track.SetWidth(pcbnew.FromMM(.6))
pcbnew.SaveBoard(str(target),board)
command=['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json',
         '--all-track-errors','--severity-all','--output',str(out/'drc.json'),str(target)]
result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace')
(out/'drc.txt').write_text(result.stdout+result.stderr)
assert result.returncode==0
drc=json.loads((out/'drc.json').read_text())
matched=[v for v in drc['violations'] if v['type']=='clearance' and any(i.get('uuid')==uid for i in v.get('items',[]))]
unchanged=hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
review={'status':'PASS' if matched and unchanged else 'FAIL','source_copy_sha256':source_hash,
        'source_copy_unchanged':unchanged,'mutation':'First U2001 SW pad escape widened from0.2mm to0.6mm on separate negative-control copy',
        'native_clearance_violations_involving_mutated_track':matched,
        'geometry_change_accepted_for_controller':False,'manufacturing_ready':False}
(out/'review.json').write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps({'status':review['status'],'detected_clearance_violations':len(matched),'source_copy_unchanged':unchanged},indent=2))
raise SystemExit(0 if review['status']=='PASS' else 2)
