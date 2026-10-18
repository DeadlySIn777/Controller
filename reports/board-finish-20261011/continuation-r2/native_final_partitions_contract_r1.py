"""Export actual full-refill geometry and verify Cu/flash obligations in one load.

The unchanged uncapped per-net partition algorithm operates on that same board.
All original and replacement/new Cu are compared in integer native units. No
board is saved; full CLI DRC is still an independent subsequent measurement.
"""
import hashlib,importlib.util,json,runpy,sys
from pathlib import Path
import pcbnew
helper,obligations,board_path,out=map(Path,sys.argv[1:5]);args=sys.argv[5:]
assert args==['--refill']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
o=json.loads(obligations.read_bytes());expected_file=Path(o['all_Cu_expected_ledger_file'])
assert sha(board_path)==o['candidate_sha256'] and sha(expected_file)==o['all_Cu_expected_ledger_sha256']
e=json.loads(expected_file.read_bytes());assert e['board_sha256']==sha(board_path)
dump=Path('Z:/pcb-runs/claude-finish/tools/fix/plane_dump.py')
pins={str(p.resolve()):sha(p)for p in (Path(__file__),helper,obligations,expected_file,board_path,board_path.with_suffix('.kicad_pro'),board_path.with_suffix('.kicad_dru'),dump)}
manager=pcbnew.GetSettingsManager();assert manager.LoadProject(str(board_path.with_suffix('.kicad_pro')))
project=manager.GetProject(str(board_path.with_suffix('.kicad_pro')));assert project is not None
original_load=pcbnew.LoadBoard;original_filler=pcbnew.ZONE_FILLER;captured=[];fills=[]
def load(p):
 assert Path(p).resolve()==board_path.resolve() and not captured
 b=original_load(str(p));b.SetProject(project);captured.append(b);return b
class Filler:
 def __init__(self,b):self.b=b;self.f=original_filler(b)
 def Fill(self,z):
  assert self.b is captured[0] and {str(q.m_Uuid.AsString())for q in z}=={str(q.m_Uuid.AsString())for q in self.b.Zones()}
  ok=bool(self.f.Fill(z));fills.append(ok);assert ok,'Actual full native fill failed';return ok
pcbnew.LoadBoard=load;pcbnew.ZONE_FILLER=Filler
saved_argv=sys.argv
try:
 sys.argv=[str(helper),str(board_path),str(out),'--refill'];runpy.run_path(str(helper),run_name='__main__')
finally:pcbnew.LoadBoard=original_load;pcbnew.ZONE_FILLER=original_filler;sys.argv=saved_argv
assert len(captured)==1 and fills==[True]
b=captured[0];p=json.loads(out.read_bytes());assert p['refilled'] and p['sha256']==sha(board_path)
tracks={str(t.m_Uuid.AsString()):t for t in b.GetTracks()};stack=list(b.GetEnabledLayers().CuStack());errors=[];flashes={};xy=lambda p:[int(p.x),int(p.y)]
if set(tracks)!=set(e['copper']):errors.append({'inventory_diff':True})
for uid,r in e['copper'].items():
 t=tracks.get(uid)
 if t is None:continue
 obs={'raw_net':str(t.GetNetname())}
 if r['kind']=='via':
  assert isinstance(t,pcbnew.PCB_VIA);obs.update(at_IU=xy(t.GetPosition()),drill_IU=int(t.GetDrillValue()),diameters_IU={str(b.GetLayerName(l)):int(t.GetWidth(l))for l in stack});flashes[uid]=[str(b.GetLayerName(l))for l in stack if t.FlashLayer(l)]
 else:
  assert not isinstance(t,(pcbnew.PCB_VIA,pcbnew.PCB_ARC));obs.update(start_IU=xy(t.GetStart()),end_IU=xy(t.GetEnd()),width_IU=int(t.GetWidth()),layer=str(b.GetLayerName(t.GetLayer())))
 for key,value in r.items():
  if key not in ('kind','chunk_sha256')and obs.get(key)!=value:errors.append({'uuid':uid,'field':key,'expected':value,'actual':obs.get(key)})
for r in o['same_UUID_existing_replacement_vias']:
 uid=r['uuid'];assert uid in flashes
 missing=set(r['required_actual_fresh_refill_flashes'])-set(flashes[uid])
 if missing:errors.append({'uuid':uid,'missing_required_old_native_flashes':sorted(missing),'actual_flashes':flashes[uid]})
all6=[str(b.GetLayerName(l))for l in stack]
for uid in o['new_ordinary_via_UUIDs']:
 if flashes.get(uid)!=all6:errors.append({'uuid':uid,'new_ordinary_actual_all6_flash_fail':flashes.get(uid)})
fp=out.parent/'actual-full-refill-via-flashes.json';put(fp,{'candidate_sha256':sha(board_path),'actual_all_zone_native_fill':True,'vias':flashes,'required_existing_replacement_vias':o['same_UUID_existing_replacement_vias'],'new_ordinary_via_UUIDs':o['new_ordinary_via_UUIDs']})
spec=importlib.util.spec_from_file_location('exact_full_native_plane_export',dump);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.r4=lambda v:int(v)/1e6;module.chain=lambda ch:[[int(ch.CPoint(k).x)/1e6,int(ch.CPoint(k).y)/1e6]for k in range(ch.PointCount())]
def captured_load(path):assert Path(path).resolve()==board_path.resolve();return b
def deny_save(*a,**k):raise ValueError('Native save forbidden')
gp=out.parent/'actual-full-refill-geometry.json';pcbnew.LoadBoard=captured_load;module.save_board_only=deny_save
try:sys.argv=[str(dump),str(board_path),str(gp)];module.main()
finally:pcbnew.LoadBoard=original_load;sys.argv=saved_argv
assert all(sha(p)==v for p,v in pins.items())
r={'verdict':'PASS_ACTUAL_FULL_NATIVE_FILL_ALL_CU_AND_EXPLICIT_FLASH_CONTRACT'if not errors else'FAIL_ACTUAL_FULL_NATIVE_FILL_CU_OR_FLASH_CONTRACT','candidate_sha256':sha(board_path),'full_native_filler_ok':True,'uncapped_partitions_sha256':sha(out),'actual_full_geometry_sha256':sha(gp),'actual_full_via_flashes_sha256':sha(fp),'postfill_Cu_or_flash_errors':errors,'input_sha256':pins,'same_loaded_project_board_for_fill_partitions_Cu_and_actual_geometry':True,'source_contacts_reference_current_thermal_DRC_SI':'SEPARATE_OPEN','native_saved':False,'adopted':False}
put(out.parent/'actual-full-refill-contract.json',r);print(json.dumps({'verdict':r['verdict'],'postfill_errors':len(errors),'actual_full_geometry_sha256':sha(gp)}),flush=True)
b.ClearProject();manager.UnloadProject(project,False)
raise SystemExit(1 if errors else 0)
