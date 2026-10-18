"""Fresh in-memory fills and exact-coordinate geometry; no board or settings save."""
import datetime, hashlib, importlib.util, json, sys
from pathlib import Path
import pcbnew

HERE=Path(__file__).resolve().parent
SRC=HERE.parent/'measure/r07-four-fag-shared/copy/board.kicad_pcb'
TOOL=Path('Z:/pcb-runs/claude-finish/tools/fix/plane_dump.py')
OUT=HERE/'native-198b-geometry'
EXPECTED='198bba53ad2cf983940c68f5e732b575d28d5fb962bc1fa4d3fd959c23a427ab'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d): p.write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
    OUT.mkdir(exist_ok=True)
    result=OUT/'geometry.json'
    if result.exists(): raise ValueError('Refuse to overwrite existing export')
    paths=[SRC,SRC.with_suffix('.kicad_pro'),SRC.with_suffix('.kicad_dru'),TOOL,Path(__file__)]
    before={str(p):sha(p) for p in paths}
    if before[str(SRC)]!=EXPECTED: raise ValueError('Wrong candidate identity')
    write(OUT/'status.json',{'phase':'RUNNING','start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inputs':before,'board_saved':False})
    mgr=pcbnew.GetSettingsManager()
    if not mgr.LoadProject(str(SRC.with_suffix('.kicad_pro'))): raise ValueError('Project load failed')
    project=mgr.GetProject(str(SRC.with_suffix('.kicad_pro')))
    if project is None: raise ValueError('Project binding unavailable')
    spec=importlib.util.spec_from_file_location('frozen_plane_dump',TOOL)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    # Preserve the native integer nanometres as exact decimal millimetres.
    module.r4=lambda v: int(v)/1e6
    module.chain=lambda ch:[[int(ch.CPoint(k).x)/1e6,int(ch.CPoint(k).y)/1e6] for k in range(ch.PointCount())]
    original_load=pcbnew.LoadBoard
    captured=[]
    def bound_load(path):
        if Path(path).resolve()!=SRC.resolve(): raise ValueError('Unexpected board path')
        b=original_load(path);b.SetProject(project);captured.append(b);return b
    def deny_save(*a,**k): raise ValueError('Saving is forbidden in this export')
    pcbnew.LoadBoard=bound_load
    module.save_board_only=deny_save
    old_argv=sys.argv
    try:
        sys.argv=[str(TOOL),str(SRC),str(result),'--refill']
        module.main()
        if len(captured)!=1: raise ValueError('Unexpected board load count')
        b=captured[0];layers=list(b.GetEnabledLayers().CuStack())
        flashes={str(t.m_Uuid.AsString()):[str(b.GetLayerName(l)) for l in layers if t.FlashLayer(l)] for t in b.GetTracks() if isinstance(t,pcbnew.PCB_VIA)}
        write(OUT/'actual-via-flashes.json',{'board_sha256':EXPECTED,'refilled_in_memory':True,'layers':[str(b.GetLayerName(l)) for l in layers],'vias':flashes})
        after={str(p):sha(p) for p in paths}
        if after!=before: raise ValueError('Frozen input changed')
        write(OUT/'receipt.json',{'verdict':'PASS','finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inputs_before':before,'inputs_after':after,'outputs':{str(result):sha(result),str(OUT/'actual-via-flashes.json'):sha(OUT/'actual-via-flashes.json')},'exact_integer_coordinates':True,'polygon_error_inside_mm':.005,'project_explicitly_bound':True,'fresh_fill_in_memory':True,'board_saved':False,'settings_saved':False,'drc':False,'adopted':False})
        write(OUT/'status.json',{'phase':'COMPLETE','board_sha256':EXPECTED,'board_saved':False})
    finally:
        sys.argv=old_argv;pcbnew.LoadBoard=original_load
        for b in captured:b.ClearProject()
        mgr.UnloadProject(project,False)
if __name__=='__main__':main()
