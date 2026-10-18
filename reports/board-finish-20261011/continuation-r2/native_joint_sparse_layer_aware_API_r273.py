"""Read-only current sparse clone API attestation; no fill or save."""
import ctypes,os,sys,json,hashlib,runpy
from ctypes import wintypes
from pathlib import Path
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
k=ctypes.windll.kernel32;k.GetCurrentProcess.restype=wintypes.HANDLE;k.SetProcessAffinityMask.argtypes=[wintypes.HANDLE,ctypes.c_size_t];k.SetPriorityClass.argtypes=[wintypes.HANDLE,wintypes.DWORD];handle=k.GetCurrentProcess();assert k.SetProcessAffinityMask(handle,sum(1<<i for i in range(16,28)));assert k.SetPriorityClass(handle,0x4000)
import pcbnew
H=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
specfile,boardfile,out=map(Path,sys.argv[1:]);spec=json.loads(specfile.read_bytes());assert sha(boardfile)==spec['candidate_sha256'];source=Path(spec['source_native_file']);assert sha(source)==spec['source_native_SHA256']
sys.path.insert(0,str(H));import native_declared_selected_zone_contract_r2 as Z
args=sys.argv[:];sys.argv=[str(Path(Z.__file__)),str(specfile),str(boardfile),str(out.parent/'native-two-FG-zone-API.json')];assert Z.main()==0;sys.argv=args
manager=pcbnew.GetSettingsManager();assert manager.LoadProject(str(boardfile.with_suffix('.kicad_pro')));a=pcbnew.LoadBoard(str(source));b=pcbnew.LoadBoard(str(boardfile));errors=[]
def record(t,board):
 pos=lambda p:[int(p.x),int(p.y)]
 if isinstance(t,pcbnew.PCB_VIA):return {'kind':'via','net':str(t.GetNetname()),'xy_IU':pos(t.GetPosition()),'diameter_IU':int(t.GetWidth(pcbnew.F_Cu)),'drill_IU':int(t.GetDrillValue()),'layers':[str(board.GetLayerName(l))for l in board.GetEnabledLayers().CuStack()if t.IsOnLayer(l)],'locked':bool(t.IsLocked())}
 r={'kind':'arc'if isinstance(t,pcbnew.PCB_ARC)else'segment','net':str(t.GetNetname()),'a_IU':pos(t.GetStart()),'b_IU':pos(t.GetEnd()),'width_IU':int(t.GetWidth()),'layer':str(board.GetLayerName(t.GetLayer())),'locked':bool(t.IsLocked())}
 if isinstance(t,pcbnew.PCB_ARC):r['mid_IU']=pos(t.GetMid())
 return r
old={str(t.m_Uuid.AsString()):record(t,a)for t in a.GetTracks()};new={str(t.m_Uuid.AsString()):record(t,b)for t in b.GetTracks()};deleted=set(spec['removed_original_Cu_UUIDs']);added={x['uuid']for x in spec['new_Cu']};assert set(new)==set(old)-deleted|added
for uid,x in old.items():
 if uid not in deleted and new[uid]!=x:errors.append({'kind':'older_native_Cu_changed','UUID':uid,'before':x,'after':new[uid]})
nm=lambda x:int(round(x*1e6))
for t in spec['new_Cu']:
 actual=new[t['uuid']]
 if t['kind']=='segment':expected={'kind':'segment','net':t['raw_net'],'a_IU':list(map(nm,t['a'])),'b_IU':list(map(nm,t['b'])),'width_IU':nm(t['w']),'layer':t['layer'],'locked':t['locked']}
 else:expected={'kind':'via','net':t['raw_net'],'xy_IU':list(map(nm,t['at'])),'diameter_IU':nm(t['d']),'drill_IU':nm(t['drill']),'layers':['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'],'locked':False}
 if actual!=expected:errors.append({'kind':'new_native_Cu_mismatch','UUID':t['uuid'],'expected':expected,'actual':actual})
fp=next(f for f in b.GetFootprints()if f.GetReference()=='R10007');assert [fp.GetPosition().x/1e6,fp.GetPosition().y/1e6,fp.GetOrientationDegrees()%360]==spec['R10007_pose'];ap=Path(spec['R10007_native_attestation_file']);assert sha(ap)==spec['R10007_native_attestation_SHA256'];expectedpads={p['UUID']:p for p in json.loads(ap.read_bytes())['native_attestation']['native_pads']};actualpads=[]
for p in fp.Pads():
 uid=str(p.m_Uuid.AsString());e=expectedpads[uid];assert p.GetNumber()==e['num']and str(p.GetNetname())==e['net']and [p.GetPosition().x/1e6,p.GetPosition().y/1e6]==[e['x'],e['y']];assert p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD;layers={}
 for ly in b.GetEnabledLayers().CuStack():
  if p.IsOnLayer(ly):
   poly=pcbnew.SHAPE_POLY_SET();p.TransformShapeToPolygon(poly,ly,0,pcbnew.FromMM(.005),pcbnew.ERROR_INSIDE);layers[str(b.GetLayerName(ly))]=[[[[poly.Outline(i).CPoint(j).x/1e6,poly.Outline(i).CPoint(j).y/1e6]for j in range(poly.Outline(i).PointCount())],[[[poly.Hole(i,k).CPoint(j).x/1e6,poly.Hole(i,k).CPoint(j).y/1e6]for j in range(poly.Hole(i,k).PointCount())]for k in range(poly.HoleCount(i))]]for i in range(poly.OutlineCount())]
 assert layers==e['layers'];actualpads.append({'UUID':uid,'position_IU':[p.GetPosition().x,p.GetPosition().y],'native_inside_masks_exact_R237':True})
assert sha(boardfile)==spec['candidate_sha256']and sha(source)==spec['source_native_SHA256'];result={'status':'PASS_NATIVE_JOINT_ALL_RETAINED_Cu_13_NEW_TRACKS_4_VIAS_LOCKS_R10007_MASKS_TWO_ZONE_RINGS'if not errors else'FAIL_NATIVE_JOINT_SPARSE_API','candidate_SHA256':sha(boardfile),'source_SHA256':sha(source),'spec_SHA256':sha(specfile),'retained_old_Cu':len(old)-len(deleted),'new_Cu':len(added),'native_two_zone_report_SHA256':sha(out.parent/'native-two-FG-zone-API.json'),'R10007_pads':actualpads,'errors':errors,'all_original_zone_rule_source_chunk_identity':'host exact sparse R268 receipt','native_refill_all_source_current_reference_allactualflashes_fullDRC':'OPEN','native_saved':False,'native_refilled':False,'adopted':False,'manufacturing_ready':False};out.write_text(json.dumps(result,indent=1)+'\n');print('R269_API',result['status'],len(errors),flush=True);raise SystemExit(0 if not errors else 1)
