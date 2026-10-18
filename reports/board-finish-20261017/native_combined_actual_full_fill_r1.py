"""One full native fill; preserve exact Cu, emit real cache and diagnostics.

No source input is saved. Only a distinct diagnostic copy receives the actual
CPP-generated filled polygons; manufacturing/adoption remain false.
"""
import os,ctypes
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
from ctypes import wintypes
kt=ctypes.windll.kernel32;kt.GetCurrentProcess.restype=wintypes.HANDLE;kt.SetProcessAffinityMask.argtypes=(wintypes.HANDLE,ctypes.c_size_t);kt.SetPriorityClass.argtypes=(wintypes.HANDLE,wintypes.DWORD)
assert kt.SetProcessAffinityMask(kt.GetCurrentProcess(),sum(1<<i for i in range(16,28)));assert kt.SetPriorityClass(kt.GetCurrentProcess(),0x4000)
import datetime,hashlib,importlib.util,json,runpy,sys
from pathlib import Path
import pcbnew
board_path,expected_file,out,filled_path=map(Path,sys.argv[1:5]);assert not out.exists()and not filled_path.exists();out.mkdir()
helper=Path('Z:/pcb-runs/claude-finish/tools/net_partitions.py');dump=Path('Z:/pcb-runs/claude-finish/tools/fix/plane_dump.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,x):(out/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def state(phase,**x):put('status.json',{'phase':phase,'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'adopted':False,**x});print('R298',phase,flush=True)
e=json.loads(expected_file.read_bytes());assert sha(board_path)==e['board_sha256'];mask=Path(e['baseline_full_native_mask_file']);assert sha(mask)==e['baseline_full_native_mask_SHA256'];oldmask=json.loads(mask.read_bytes())['vias']
assert set(e['authorized_removed_actual_full_R157_via_UUIDs']) == {'2193173a-497d-48d4-8833-92e9133ec64a','67c69f6a-075b-465b-96c4-89a8aff35b02'}
assert set(oldmask)-set(e['copper']) == set(e['authorized_removed_actual_full_R157_via_UUIDs'])
assert set(e['exact_physical_retirement_survivors']) == set(e['authorized_removed_actual_full_R157_via_UUIDs'])
for retired,survivor in e['exact_physical_retirement_survivors'].items():
 assert set(oldmask[retired]) == set(oldmask[survivor]) == {'F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'}
 assert survivor in e['copper'] and e['copper'][survivor]['kind']=='via'

inputs=[Path(__file__),board_path,board_path.with_suffix('.kicad_pro'),board_path.with_suffix('.kicad_dru'),expected_file,mask,helper,dump];pins={str(p.resolve()):sha(p)for p in inputs};put('input-pins.json',pins)
manager=pcbnew.GetSettingsManager();assert manager.LoadProject(str(board_path.with_suffix('.kicad_pro')));project=manager.GetProject(str(board_path.with_suffix('.kicad_pro')));assert project is not None
original_load=pcbnew.LoadBoard;original_filler=pcbnew.ZONE_FILLER;captured=[];fills=[]
def copper_state(b):
 result={};stack=list(b.GetEnabledLayers().CuStack());flashes={}
 for t in b.GetTracks():
  uid=str(t.m_Uuid.AsString());row={'raw_net':str(t.GetNetname()),'locked_yes':bool(t.IsLocked())}
  if isinstance(t,pcbnew.PCB_VIA):
   row.update(kind='via',at_IU=[int(t.GetPosition().x),int(t.GetPosition().y)],drill_IU=int(t.GetDrillValue()),diameters_IU={str(b.GetLayerName(l)):int(t.GetWidth(l))for l in stack});flashes[uid]=[str(b.GetLayerName(l))for l in stack if t.FlashLayer(l)]
  else:
   row.update(kind='arc'if isinstance(t,pcbnew.PCB_ARC)else'segment',start_IU=[int(t.GetStart().x),int(t.GetStart().y)],end_IU=[int(t.GetEnd().x),int(t.GetEnd().y)],width_IU=int(t.GetWidth()),layer=str(b.GetLayerName(t.GetLayer())))
   if row['kind']=='arc':row['mid_IU']=[int(t.GetMid().x),int(t.GetMid().y)]
  result[uid]=row
 return result,flashes
def errors_expected(state):
 errors=[]
 if set(state)!=set(e['copper']):errors.append({'kind':'Cu_UUID_inventory','missing':sorted(set(e['copper'])-set(state)),'extra':sorted(set(state)-set(e['copper']))})
 for uid,row in e['copper'].items():
  observed=state.get(uid,{})
  for k,v in row.items():
   if k!='chunk_sha256'and observed.get(k)!=v:errors.append({'kind':'integer_native_Cu_or_lock','UUID':uid,'field':k,'expected':v,'observed':observed.get(k)})
 return errors
def pad_pose_state(b):
 return {'footprints':{str(f.m_Uuid.AsString()):[str(f.GetReference()),str(f.GetValue()),int(f.GetPosition().x),int(f.GetPosition().y),float(f.GetOrientation().AsDegrees()),str(b.GetLayerName(f.GetLayer()))]for f in b.GetFootprints()},'pads':{str(p.m_Uuid.AsString()):[str(p.GetNumber()),str(p.GetNetname()),int(p.GetPosition().x),int(p.GetPosition().y),sorted(str(b.GetLayerName(l))for l in p.GetLayerSet().Seq())]for f in b.GetFootprints()for p in f.Pads()}}
def load(p):
 assert Path(p).resolve()==board_path.resolve()and not captured
 b=original_load(str(p));b.SetProject(project);cu,_=copper_state(b);errors=errors_expected(cu);put('before-native-Cu-errors.json',errors);assert not errors,'Serialized native integer Cu or lock mismatch before fill'
 captured.append(b);put('before-native-all-FP-pad-pose.json',pad_pose_state(b));return b
class Filler:
 def __init__(self,b):self.b=b;self.f=original_filler(b)
 def Fill(self,z):
  assert self.b is captured[0]and{str(q.m_Uuid.AsString())for q in z}=={str(q.m_Uuid.AsString())for q in self.b.Zones()}
  state('FULL_ALL_NET_CPP_FILL_RUNNING',zone_count=len(list(self.b.Zones())))
  ok=bool(self.f.Fill(z));fills.append(ok);assert ok,'CPP all-net fill failed';return ok
pcbnew.LoadBoard=load;pcbnew.ZONE_FILLER=Filler;argv=sys.argv
try:sys.argv=[str(helper),str(board_path),str(out/'partitions.json'),'--refill'];runpy.run_path(str(helper),run_name='__main__')
finally:pcbnew.LoadBoard=original_load;pcbnew.ZONE_FILLER=original_filler;sys.argv=argv
assert len(captured)==1 and fills==[True];b=captured[0];parts=json.loads((out/'partitions.json').read_bytes());assert parts['refilled']and parts['sha256']==sha(board_path)
after,flashes=copper_state(b);cuerrors=errors_expected(after);pose=pad_pose_state(b);beforepose=json.loads((out/'before-native-all-FP-pad-pose.json').read_bytes());assert pose==beforepose,'Native full fill altered FP/pad poses or membership'
maskerrors=[]
for uid,old in oldmask.items():
 if uid not in flashes:
  if uid not in e['authorized_removed_actual_full_R157_via_UUIDs']:maskerrors.append({'UUID':uid,'missing_required_retained_actual_FULL_R157_via':True,'old':old})
  continue
 lost=set(old)-set(flashes[uid])
 if lost:maskerrors.append({'UUID':uid,'missing_actual_FULL_R157_layers':sorted(lost),'old':old,'new':flashes[uid]})
all6={str(b.GetLayerName(l))for l in b.GetEnabledLayers().CuStack()}
for uid in e['required_NEW_ordinary_all6']:
 if set(flashes.get(uid,[]))!=all6:maskerrors.append({'UUID':uid,'NEW_ordinary_all6_failure':flashes.get(uid)})
put('actual-full-refill-via-flashes.json',{'candidate_sha256':sha(board_path),'actual_all_zone_native_fill':True,'vias':flashes,'required_NEW_ordinary_all6':e['required_NEW_ordinary_all6']})
spec=importlib.util.spec_from_file_location('combined_R298_actual_full_native_export',dump);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.r4=lambda v:int(v)/1e6;module.chain=lambda ch:[[int(ch.CPoint(k).x)/1e6,int(ch.CPoint(k).y)/1e6]for k in range(ch.PointCount())]
def captured_load(p):assert Path(p).resolve()==board_path.resolve();return b
def deny_save(*a,**k):raise ValueError('Exporter must not save source board')
pcbnew.LoadBoard=captured_load;module.save_board_only=deny_save
try:sys.argv=[str(dump),str(board_path),str(out/'actual-full-refill-geometry.json')];module.main()
finally:pcbnew.LoadBoard=original_load;sys.argv=argv
assert not cuerrors,'Native full fill changed exact discrete Cu'
assert filled_path.parent.is_dir();state('REAL_NATIVE_FULL_FILLED_DIAGNOSTIC_COPY_SAVE')
pcbnew.SaveBoard(str(filled_path),b);assert filled_path.is_file()
# Reload genuine saved CPP output and verify every Cu integer/lock and pad pose.
saved=original_load(str(filled_path));saved.SetProject(project);saved.BuildConnectivity();savedcu,savedflashes=copper_state(saved);savederrors=errors_expected(savedcu);assert not savederrors and pad_pose_state(saved)==pose
put('saved-native-reload-Cu-errors.json',savederrors);put('saved-native-reload-via-flashes.json',{'saved_board_SHA256':sha(filled_path),'vias':savedflashes,'matches_in_memory_full_native_flash_sets':{u:set(v)for u,v in savedflashes.items()}=={u:set(v)for u,v in flashes.items()}})
assert {u:set(v)for u,v in savedflashes.items()}=={u:set(v)for u,v in flashes.items()},'Saved genuine native cache FlashLayer sets differ; evidence retained and cached CLI forbidden'
assert all(sha(p)==v for p,v in pins.items()),'Frozen input changed'
record={'status':'FULL_ALL_NET_NATIVE_CPP_DIAGNOSTIC_COMPLETE_EXACT_CU_SOURCE_REFERENCE_CURRENT_DRC_OPEN','candidate_SHA256':sha(board_path),'actual_full_geometry_SHA256':sha(out/'actual-full-refill-geometry.json'),'actual_full_flash_SHA256':sha(out/'actual-full-refill-via-flashes.json'),'partitions_SHA256':sha(out/'partitions.json'),'full_native_CPP_Fill_calls':1,'discrete_Cu_errors':cuerrors,'old_actual_or_NEW_ordinary_mask_errors':maskerrors,'all_FP_pad_pose_and_net_membership_unchanged_by_fill':True,'genuine_CPP_filled_diagnostic_copy_file':str(filled_path.resolve()),'genuine_CPP_filled_diagnostic_copy_SHA256':sha(filled_path),'native_saved_reload_Cu_pose_match':True,'input_SHA256':pins,'same_loaded_board_for_all_zones_partitions_Cu_geometry_flash':True,'inherited_R7_CORE_current_source_ref_SI_thermal_fab_failures':'RETAINED_NO_ADOPTION','full_native_DRC_schematic_parity_source_contact_direct_and_all_old_body_reference':'OPEN','adopted':False,'manufacturing_ready':False}
put('receipt.json',record);state('FULL_NATIVE_DIAGNOSTIC_COMPLETE',Cu_errors=len(cuerrors),mask_errors=len(maskerrors));saved.ClearProject();b.ClearProject();manager.UnloadProject(project,False)
