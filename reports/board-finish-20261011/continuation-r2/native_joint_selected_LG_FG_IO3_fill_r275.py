"""Selected LG/FG/IO3 fill, exact local landings only; no native save."""
import os,ctypes
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
from ctypes import wintypes
kt=ctypes.windll.kernel32;kt.GetCurrentProcess.restype=wintypes.HANDLE;kt.SetProcessAffinityMask.argtypes=(wintypes.HANDLE,ctypes.c_size_t);kt.SetPriorityClass.argtypes=(wintypes.HANDLE,wintypes.DWORD)
assert kt.SetProcessAffinityMask(kt.GetCurrentProcess(),sum(1<<i for i in range(16,28)));assert kt.SetPriorityClass(kt.GetCurrentProcess(),0x4000)
import datetime,hashlib,importlib.util,json,sys
from pathlib import Path
import pcbnew
board_path,expected_path,mask_path,out=map(Path,sys.argv[1:5]);out.mkdir()
tool=Path('Z:/pcb-runs/claude-finish/tools/fix/plane_dump.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
inputs=[Path(__file__),tool,board_path,board_path.with_suffix('.kicad_pro'),board_path.with_suffix('.kicad_dru'),expected_path,mask_path];pins={str(p.resolve()):sha(p)for p in inputs};expected=json.loads(expected_path.read_bytes());assert sha(board_path)==expected['board_sha256'];oldmask=json.loads(mask_path.read_bytes())['vias']
manager=pcbnew.GetSettingsManager();assert manager.LoadProject(str(board_path.with_suffix('.kicad_pro')));project=manager.GetProject(str(board_path.with_suffix('.kicad_pro')));assert project is not None;board=pcbnew.LoadBoard(str(board_path));board.SetProject(project)
raws={'/LOGIC_GND','/motherboard_motors{slash}FIELD_GND','/IO_3V3'};selected=pcbnew.ZONES();selectedids=[]
for z in board.Zones():
 if not z.GetIsRuleArea()and str(z.GetNetname())in raws:selected.append(z);selectedids.append(str(z.m_Uuid.AsString()))
assert selectedids
put(out/'status.json',{'phase':'SELECTED_THREE_ROOT_AFFECTED_NET_NATIVE_FILL_RUNNING','UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selected_raw_nets':sorted(raws),'selected_zone_UUIDs':selectedids,'no_save':True,'no_full_refill':True})
assert bool(pcbnew.ZONE_FILLER(board).Fill(selected))
spec=importlib.util.spec_from_file_location('exact_R275_selected_native_dump',tool);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.r4=lambda v:int(v)/1e6;module.chain=lambda ch:[[int(ch.CPoint(k).x)/1e6,int(ch.CPoint(k).y)/1e6]for k in range(ch.PointCount())]
load=pcbnew.LoadBoard;argv=sys.argv
def captured(p):
 assert Path(p).resolve()==board_path.resolve();return board
def deny_save(*a,**k):raise ValueError('Native diagnostic save forbidden')
pcbnew.LoadBoard=captured;module.save_board_only=deny_save
try:sys.argv=[str(tool),str(board_path),str(out/'geometry.json')];module.main()
finally:pcbnew.LoadBoard=load;sys.argv=argv
actual={str(t.m_Uuid.AsString()):t for t in board.GetTracks()};layers=list(board.GetEnabledLayers().CuStack());fl={};errors=[];maskerrors=[]
assert set(actual)==set(expected['copper'])
for uid,exp in expected['copper'].items():
 t=actual[uid];obs={'raw_net':str(t.GetNetname())}
 if exp['kind']=='via':
  assert isinstance(t,pcbnew.PCB_VIA);obs.update(at_IU=[int(t.GetPosition().x),int(t.GetPosition().y)],drill_IU=int(t.GetDrillValue()),diameters_IU={str(board.GetLayerName(l)):int(t.GetWidth(l))for l in layers});fl[uid]=[str(board.GetLayerName(l))for l in layers if t.FlashLayer(l)]
  if obs['raw_net']in raws and uid in oldmask:
   lost=set(oldmask[uid])-set(fl[uid])
   if lost:maskerrors.append({'UUID':uid,'raw_net':obs['raw_net'],'lost_R157_actual_selected_ground_layers':sorted(lost),'R157_native_layers':oldmask[uid],'new_selected_layers':fl[uid]})
 else:obs.update(start_IU=[int(t.GetStart().x),int(t.GetStart().y)],end_IU=[int(t.GetEnd().x),int(t.GetEnd().y)],width_IU=int(t.GetWidth()),layer=str(board.GetLayerName(t.GetLayer())))
 for key,val in exp.items():
  if key not in('kind','chunk_sha256')and obs.get(key)!=val:errors.append({'UUID':uid,'field':key,'expected':val,'actual':obs.get(key)})
for uid in expected['required_NEW_ordinary_all6']:
 if set(fl[uid])!={str(board.GetLayerName(l))for l in layers}:errors.append({'UUID':uid,'new_ordinary_actual_all6_flash_failure':fl[uid]})
put(out/'actual-via-flashes.json',{'board_sha256':sha(board_path),'fresh_fill_scope':'LG_FG_IO3_ALL_SELECTED_ZONES_ONLY','selected_raw_nets':sorted(raws),'selected_zone_UUIDs':selectedids,'vias':fl})
assert all(sha(p)==v for p,v in pins.items())
record={'status':'SELECTED_THREE_ROOT_AFFECTED_NET_CPP_COMPLETE_SOURCE_REFERENCE_FLASH_REVIEW_OPEN','candidate_SHA256':sha(board_path),'selected_raw_nets':sorted(raws),'selected_zone_UUIDs':selectedids,'actual_geometry_SHA256':sha(out/'geometry.json'),'actual_via_flashes_SHA256':sha(out/'actual-via-flashes.json'),'all_discrete_post_fill_errors':errors,'prior_R157_actual_selected_ground_flash_losses':maskerrors,'input_SHA256':pins,'all_other_nets_fills_and_source':'UNVALIDATED_NOT_FULL_REFILL','native_current_SI_loop_thermal_old_REQUIRED_mask_qualification':'OPEN_INDEPENDENT_CHECK','no_save':True,'adopted':False};put(out/'receipt.json',record);print(json.dumps({'status':record['status'],'Cu_errors':len(errors),'old_ground_actual_mask_losses':len(maskerrors)}),flush=True);board.ClearProject();manager.UnloadProject(project,False);raise SystemExit(0 if not errors else 1)
