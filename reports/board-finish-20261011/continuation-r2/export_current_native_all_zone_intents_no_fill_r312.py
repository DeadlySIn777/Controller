"""Read every exact current zone outline/profile; no fill or source save."""
import sys,json,hashlib,datetime,importlib.util
from pathlib import Path
import pcbnew
board,expected,out=map(Path,sys.argv[1:4]);assert not out.exists();out.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
e=json.loads(expected.read_bytes());assert sha(board)==e['board_sha256']=='7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2'
dump=Path('Z:/pcb-runs/claude-finish/tools/fix/plane_dump.py')
spec=importlib.util.spec_from_file_location('R312_native_outline_reader',dump);D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
D.r4=lambda n:int(n)/1e6
D.chain=lambda ch:[[int(ch.CPoint(k).x)/1e6,int(ch.CPoint(k).y)/1e6]for k in range(ch.PointCount())]
inputs={str(p.resolve()):sha(p)for p in (Path(__file__),board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru'),expected,dump)}
manager=pcbnew.GetSettingsManager();assert manager.LoadProject(str(board.with_suffix('.kicad_pro')))
project=manager.GetProject(str(board.with_suffix('.kicad_pro')));assert project is not None
b=pcbnew.LoadBoard(str(board));b.SetProject(project)
def no_save(*a,**k):raise ValueError('Read-only intent export cannot save board')
pcbnew.SaveBoard=no_save
rows=[];allzones=[(q,None)for q in b.Zones()]
for f in b.GetFootprints():allzones.extend((q,str(f.GetReference()))for q in f.Zones())
for q,owner in allzones:
 rec={'UUID':str(q.m_Uuid.AsString()),'raw_name':str(q.GetZoneName()),'footprint_owner':owner,'layers':[str(b.GetLayerName(l))for l in q.GetLayerSet().CuStack()],'outline_mm_exact_native_IU_div_1e6':D.polyset(q.Outline()),'locked_yes':bool(q.IsLocked()),'rule_area':bool(q.GetIsRuleArea())}
 if q.GetIsRuleArea():rec.update(no_fill=bool(q.GetDoNotAllowZoneFills()),no_tracks=bool(q.GetDoNotAllowTracks()),no_vias=bool(q.GetDoNotAllowVias()),no_pads=bool(q.GetDoNotAllowPads()),no_footprints=bool(q.GetDoNotAllowFootprints()))
 else:
  rec.update(raw_net=str(q.GetNetname()),priority=int(q.GetAssignedPriority()),island_removal_native_enum=int(q.GetIslandRemovalMode()),minimum_island_area_IU2=int(q.GetMinIslandArea()),local_clearance_IU=None if q.GetLocalClearance()is None else int(q.GetLocalClearance()),minimum_thickness_IU=int(q.GetMinThickness()))
 rows.append(rec)
assert len(list(b.Zones()))==850 and len({r['UUID']for r in rows})==len(rows)
fp=out/'all-current-native-intended-zone-outlines-and-profiles.json';fp.write_text(json.dumps(rows,indent=1,allow_nan=False)+'\n',encoding='utf-8')
assert all(sha(p)==v for p,v in inputs.items()),'Read-only native input changed'
receipt={'status':'ALL_CURRENT_NATIVE_INTENTS_READ_ONLY_NO_FILL_NOT_CONTACT_EVIDENCE','UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_SHA256':sha(board),'native_board_zone_count':len(list(b.Zones())),'native_total_including_footprint_zone_count':len(rows),'native_integer_coordinate_resolution_mm':1e-6,'intended_export_SHA256':sha(fp),'input_SHA256':inputs,'SOURCE_contact_reference_flash_and_current_qualification':'OPEN_REQUIRES_GENUINE_FULL_NATIVE_AFTER','CPP_Fill_calls':0,'SaveBoard_calls':0,'native_slot':'existing shared2','new_heavy_slots':0,'adopted':False}
(out/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print('R312_NATIVE_INTENTS',len(rows),sha(out/'receipt.json'),flush=True)
b.ClearProject();manager.UnloadProject(project,False)
