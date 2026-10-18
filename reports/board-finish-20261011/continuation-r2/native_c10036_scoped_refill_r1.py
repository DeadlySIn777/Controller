"""Fresh native FBG fill only; other zones and whole-board DRC remain open."""
import datetime,hashlib,importlib.util,json,sys
from pathlib import Path
import pcbnew
board_path,expected_path,out=map(Path,sys.argv[1:4]);out.mkdir()
tool=Path('Z:/pcb-runs/claude-finish/tools/fix/plane_dump.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def state(phase,**d):write(out/'status.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':phase,'board_saved':False,**d})
pins={str(p.resolve()):sha(p) for p in (Path(__file__),tool,board_path,board_path.with_suffix('.kicad_pro'),board_path.with_suffix('.kicad_dru'),expected_path)}
expected=json.loads(expected_path.read_bytes());assert sha(board_path)==expected['board_sha256']
manager=pcbnew.GetSettingsManager();assert manager.LoadProject(str(board_path.with_suffix('.kicad_pro')))
project=manager.GetProject(str(board_path.with_suffix('.kicad_pro')));assert project is not None
board=pcbnew.LoadBoard(str(board_path));board.SetProject(project)
selected=pcbnew.ZONES();selected_ids=[]
raw='/motherboard_do{slash}FIELD_B_0V'
for z in board.Zones():
    if not z.GetIsRuleArea() and str(z.GetNetname())==raw:selected.append(z);selected_ids.append(str(z.m_Uuid.AsString()))
assert selected_ids,'No exact FBG native zones'
state('SCOPED_NATIVE_FILL_RUNNING',selected_raw_net=raw,selected_zone_UUIDs=selected_ids)
okay=bool(pcbnew.ZONE_FILLER(board).Fill(selected));assert okay,'Selected native fill failed'
state('EXPORTING_SELECTED_FRESH_GEOMETRY',selected_zone_UUIDs=selected_ids)
spec=importlib.util.spec_from_file_location('exact_scoped_plane_export',tool);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.r4=lambda v:int(v)/1e6
module.chain=lambda ch:[[int(ch.CPoint(k).x)/1e6,int(ch.CPoint(k).y)/1e6] for k in range(ch.PointCount())]
original_load=pcbnew.LoadBoard;original_argv=sys.argv
def captured_load(path):
    assert Path(path).resolve()==board_path.resolve();return board
def deny_save(*a,**k):raise ValueError('Native saving forbidden in scoped evidence')
pcbnew.LoadBoard=captured_load;module.save_board_only=deny_save
try:
    sys.argv=[str(tool),str(board_path),str(out/'geometry.json')];module.main()
finally:pcbnew.LoadBoard=original_load;sys.argv=original_argv
stack=list(board.GetEnabledLayers().CuStack());actual={str(t.m_Uuid.AsString()):t for t in board.GetTracks()};errors=[];flashes={};xy=lambda p:[int(p.x),int(p.y)]
if set(actual)!=set(expected['copper']):errors.append({'inventory_diff':True})
for uid,exp in expected['copper'].items():
    t=actual.get(uid)
    if t is None:continue
    obs={'raw_net':str(t.GetNetname())}
    if exp['kind']=='via':
        assert isinstance(t,pcbnew.PCB_VIA);obs.update(at_IU=xy(t.GetPosition()),drill_IU=int(t.GetDrillValue()),diameters_IU={str(board.GetLayerName(l)):int(t.GetWidth(l)) for l in stack});flashes[uid]=[str(board.GetLayerName(l)) for l in stack if t.FlashLayer(l)]
    else:obs.update(start_IU=xy(t.GetStart()),end_IU=xy(t.GetEnd()),width_IU=int(t.GetWidth()),layer=str(board.GetLayerName(t.GetLayer())))
    for key,value in exp.items():
        if key not in ('kind','chunk_sha256') and obs.get(key)!=value:errors.append({'uuid':uid,'field':key,'expected':value,'actual':obs.get(key)})
write(out/'actual-via-flashes.json',{'board_sha256':sha(board_path),'fresh_fill_scope':'FBG only','selected_zone_UUIDs':selected_ids,'vias':flashes})
assert all(sha(p)==v for p,v in pins.items())
record={'verdict':'PASS_SCOPED_FBG_NATIVE_REFILL_EXPORT_RAW_COPPER' if not errors else 'FAIL_SCOPED_NATIVE_COPPER_MUTATION','candidate_sha256':sha(board_path),'selected_zone_UUIDs':selected_ids,'selected_raw_net':raw,'filler_ok':okay,'all_discrete_post_fill_errors':errors,'geometry_sha256':sha(out/'geometry.json'),'actual_via_flashes_sha256':sha(out/'actual-via-flashes.json'),'input_sha256':pins,'all_other_zone_fills':'Stored or otherwise unvalidated: do not treat this as an all-board fresh refill','old_cache_healing_reference_and_source_root_contact':'Requires independent exact host comparison of these actual selected polygons, not assumed by this export','whole_board_source_continuity_refill_DRC_SI_analog_current_thermal_and_final_power_composition':'OPEN','board_or_project_saved':False,'adopted':False}
write(out/'receipt.json',record);state('COMPLETE_SELECTED_NATIVE_REFILL_EXPORT_REVIEW_OPEN',verdict=record['verdict']);print(json.dumps({'verdict':record['verdict'],'zones':len(selected_ids),'post_fill_Cu_errors':len(errors)}),flush=True)
board.ClearProject();manager.UnloadProject(project,False)
raise SystemExit(0 if not errors else 1)
