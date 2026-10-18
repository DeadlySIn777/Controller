"""Read-only native stage4 DSN export; no Fill/SaveBoard or original mutation."""
import os,sys,time,json,hashlib
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
from pathlib import Path
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pcbnew
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];SOURCE=ROOT/'reports/board-finish-20261017/combined-route-stage-r4/native/board.kicad_pcb'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def write(n,v):(HERE/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 t=time.monotonic();files=[SOURCE,SOURCE.with_suffix('.kicad_pro'),SOURCE.with_suffix('.kicad_dru'),Path(__file__)];pins={str(f):sha(f)for f in files};assert pins[str(SOURCE)]=='ce8aa2cd5bb9c2128733618d5241a10acebdd637e4a0b5f726fea40801444c55'
 manager=pcbnew.GetSettingsManager();pro=SOURCE.with_suffix('.kicad_pro');assert manager.LoadProject(str(pro));project=manager.GetProject(str(pro));assert project is not None
 b=pcbnew.LoadBoard(str(SOURCE));b.SetProject(project);dest=HERE/'stage4-native-raw.dsn';assert not dest.exists();ok=pcbnew.ExportSpecctraDSN(b,str(dest));assert ok and dest.is_file()
 write('raw-export-ready.json',{'status':'NATIVE_GLOBAL_DSN_EXPORTED_RAW_INTERCHANGE_NOT_ELECTRICAL_PASS','board':str(SOURCE),'board_SHA256':pins[str(SOURCE)],'DSN':str(dest),'DSN_SHA256':sha(dest),'native_version':pcbnew.GetBuildVersion(),'loaded_actual_project':True,'DSN_bytes':dest.stat().st_size,'elapsed_seconds':time.monotonic()-t,'input_SHA256':pins,'inputs_unchanged':all(sha(f)==v for f,v in pins.items()),'Fill_calls':0,'SaveBoard_calls':0,'native_routing_runs':0});print('RAW_DSN_READY',str(dest),sha(dest),flush=True)
 tracks=list(b.GetTracks());fps=list(b.GetFootprints());pads=[q for fp in fps for q in fp.Pads()];layers=[b.GetLayerName(i)for i in b.GetEnabledLayers().Seq()if pcbnew.IsCopperLayer(i)];layers=sorted(layers,key=lambda n:0 if n=='F.Cu'else 99 if n=='B.Cu'else int(n[2:-3]));zones=list(b.Zones())
 write('native-export-census.json',{'native_version':pcbnew.GetBuildVersion(),'physical_copper_layers':layers,'native_copper_layer_count':b.GetCopperLayerCount(),'native_track_and_via_objects':len(tracks),'native_locked_copper_objects':sum(t.IsLocked()for t in tracks),'footprints':len(fps),'pads':len(pads),'board_zones':len(zones),'board_ruleareas':sum(z.GetIsRuleArea()for z in zones),'board_nets':len(b.GetNetsByNetcode()),'GetDRCEpsilon_IU':b.GetDesignSettings().GetDRCEpsilon(),'new_native_routing_or_fill':False,'sources_unchanged':all(sha(f)==v for f,v in pins.items()),'input_SHA256':pins});print('NATIVE_DSN_CENSUS_DONE',flush=True)
if __name__=='__main__':main()
