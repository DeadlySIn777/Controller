"""Read-only, no-refill, exact-IU cached eedf parent geometry export."""
import os,ctypes
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
assert ctypes.windll.kernel32.SetProcessAffinityMask(ctypes.windll.kernel32.GetCurrentProcess(),sum(1<<i for i in range(16,28)))
assert ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(),0x4000)
import datetime,hashlib,importlib.util,json,sys
from pathlib import Path
import pcbnew
board_path,mask_path,out=map(Path,sys.argv[1:4]);out.mkdir()
tool=Path('Z:/pcb-runs/claude-finish/tools/fix/plane_dump.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
inputs=[Path(__file__),tool,board_path,board_path.with_suffix('.kicad_pro'),board_path.with_suffix('.kicad_dru'),mask_path]
pins={str(p.resolve()):sha(p)for p in inputs}
assert sha(board_path)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
assert sha(mask_path)=='323b9e9ff0b668fb6d94c974e8597200123f5bccd3786446ed84c52de3d34d1a'
assert sha(tool)=='9c5f611e0c83c0a3725e2663817574c059d9f1ddb02df3b60acd45724973d35a'
expected=json.loads(mask_path.read_bytes())['retained_original_via_masks'];assert len(expected)==7907
manager=pcbnew.GetSettingsManager();assert manager.LoadProject(str(board_path.with_suffix('.kicad_pro')))
project=manager.GetProject(str(board_path.with_suffix('.kicad_pro')));assert project is not None
board=pcbnew.LoadBoard(str(board_path));board.SetProject(project)
put(out/'status.json',{'phase':'EXACT_EEDF_CACHED_NO_REFILL_EXPORT_RUNNING','UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input_SHA256':pins,'no_save':True,'no_refill':True})
spec=importlib.util.spec_from_file_location('native_eedf_cached_exact_export',tool);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.r4=lambda v:int(v)/1e6
module.chain=lambda ch:[[int(ch.CPoint(k).x)/1e6,int(ch.CPoint(k).y)/1e6]for k in range(ch.PointCount())]
load=pcbnew.LoadBoard;argv=sys.argv
def captured_load(p):
 assert Path(p).resolve()==board_path.resolve();return board
def deny_save(*a,**k):raise ValueError('No board/project save authorized for cached BEFORE export')
pcbnew.LoadBoard=captured_load;module.save_board_only=deny_save
try:
 sys.argv=[str(tool),str(board_path),str(out/'cached-geometry.json')];module.main()
finally:pcbnew.LoadBoard=load;sys.argv=argv
layers=list(board.GetEnabledLayers().CuStack());vias={};errors=[]
for t in board.GetTracks():
 if not isinstance(t,pcbnew.PCB_VIA):continue
 uid=str(t.m_Uuid.AsString());vias[uid]={'raw_net':str(t.GetNetname()),'at_IU':[int(t.GetPosition().x),int(t.GetPosition().y)],'drill_IU':int(t.GetDrillValue()),'diameters_IU':{str(board.GetLayerName(l)):int(t.GetWidth(l))for l in layers},'actual_FlashLayer':[str(board.GetLayerName(l))for l in layers if t.FlashLayer(l)]}
for uid,mask in expected.items():
 if uid not in vias or vias[uid]['actual_FlashLayer']!=mask:errors.append({'UUID':uid,'expected_parent_actual_masks':mask,'observed':vias.get(uid)})
put(out/'actual-cached-native-via-geometry-and-flashes.json',{'board_SHA256':sha(board_path),'evidence_class':'UNTOUCHED_EEDF_CACHED_NATIVE_BEFORE_NO_REFILL','vias':vias})
assert all(sha(p)==v for p,v in pins.items()),'Original input mutated'
record={'verdict':'PASS_EXACT_CACHED_EEDF_EXPORT_PARENT_7907_MASKS'if not errors else 'FAIL_CACHED_PARENT_MASKS','evidence_class':'UNTOUCHED_EEDF_CACHED_NATIVE_BEFORE_NO_REFILL','board_SHA256':sha(board_path),'input_SHA256':pins,'geometry_SHA256':sha(out/'cached-geometry.json'),'actual_via_geometry_and_flashes_SHA256':sha(out/'actual-cached-native-via-geometry-and-flashes.json'),'original_parent_mask_count':len(expected),'native_via_count':len(vias),'errors':errors,'no_refill':True,'no_board_or_project_save':True,'all_original_input_bytes_unchanged':True,'cached_pours_are_not_refilled_evidence':True,'source_current_reference_thermal_DRC':'OPEN_SEPARATE_GATES','adopted':False}
put(out/'receipt.json',record);put(out/'status.json',record);print(json.dumps({'verdict':record['verdict'],'errors':len(errors),'native_vias':len(vias)}),flush=True)
board.ClearProject();manager.UnloadProject(project,False)
raise SystemExit(0 if not errors else 1)
