import sys,json,hashlib
from pathlib import Path
import pcbnew
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def polygons(sh):return [[[[sh.Outline(i).CPoint(k).x/1e6,sh.Outline(i).CPoint(k).y/1e6]for k in range(sh.Outline(i).PointCount())],[[[sh.Hole(i,j).CPoint(k).x/1e6,sh.Hole(i,j).CPoint(k).y/1e6]for k in range(sh.Hole(i,j).PointCount())]for j in range(sh.HoleCount(i))]]for i in range(sh.OutlineCount())]
specfile,boardfile,out=map(Path,sys.argv[1:]);s=json.loads(specfile.read_bytes());assert sha(boardfile)==s['candidate_sha256'];b=pcbnew.LoadBoard(str(boardfile));layers=list(b.GetEnabledLayers().CuStack());fp=next(f for f in b.GetFootprints()if f.GetReference()=='R7035');assert fp.m_Uuid.AsString()==s['FP_UUID'];assert [fp.GetPosition().x,fp.GetPosition().y]==[81147000,27700000]and fp.GetOrientationDegrees()%360==180;rows=[]
for p in fp.Pads():
 uid=p.m_Uuid.AsString();e=s['expected_pads'][uid];pos=p.GetPosition();assert [pos.x,pos.y]==e['at_IU']and p.GetNumber()==e['pin']and p.GetNetname()==e['raw_net'];assert p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD;inside={};outside={}
 for layer in layers:
  if not p.IsOnLayer(layer):continue
  ip=pcbnew.SHAPE_POLY_SET();op=pcbnew.SHAPE_POLY_SET();p.TransformShapeToPolygon(ip,layer,0,1,pcbnew.ERROR_INSIDE);p.TransformShapeToPolygon(op,layer,0,1,pcbnew.ERROR_OUTSIDE);inside[b.GetLayerName(layer)]=polygons(ip);outside[b.GetLayerName(layer)]=polygons(op)
 assert list(inside)==['F.Cu'];rows.append({'uuid':uid,'ref':'R7035','num':p.GetNumber(),'net':p.GetNetname(),'x':pos.x/1e6,'y':pos.y/1e6,'layers':inside,'outside_layers':outside,'smd':True,'npth':False,'hole':None,'absolute_pad_angle_deg':p.GetOrientationDegrees(),'size_IU':[p.GetSize().x,p.GetSize().y],'drill_IU':[p.GetDrillSize().x,p.GetDrillSize().y],'native_shape_enum':int(p.GetShape(pcbnew.F_Cu))})
assert set(s['expected_pads'])=={p['uuid']for p in rows};vias=[];found={t.m_Uuid.AsString():t for t in b.GetTracks()if isinstance(t,pcbnew.PCB_VIA)}
for uid,e in s['expected_new_vias'].items():
 v=found[uid];pos=v.GetPosition();assert [pos.x,pos.y]==e['at_IU']and v.GetNetname()==e['raw_net']and v.GetDrillValue()==200000;ds={b.GetLayerName(l):int(v.GetWidth(l))for l in layers};assert set(ds.values())=={500000};fl=[b.GetLayerName(l)for l in layers if v.FlashLayer(l)];assert fl==['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'];vias.append({'uuid':uid,'net':v.GetNetname(),'xy_IU':[pos.x,pos.y],'diameters_IU':ds,'drill_IU':int(v.GetDrillValue()),'actual_flashed_layers':fl,'native_save_refill':False})
r36=next(f for f in b.GetFootprints()if f.GetReference()=='R7036');assert r36.m_Uuid.AsString()=='ebbcc18b-afda-47c3-b654-467b84dfb86b'and[r36.GetPosition().x,r36.GetPosition().y]==[77237000,26200000]and r36.GetOrientationDegrees()%360==0
out.write_text(json.dumps({'verdict':'PASS_NATIVE_R7035_REAL_ROOT_POSE_PAD_UUID_NET_AND_THREE_VIA_MASKS_READONLY','candidate_sha256':sha(boardfile),'spec_sha256':sha(specfile),'FP_pose_mm_deg':[81.147,27.7,180],'FP_UUID':fp.m_Uuid.AsString(),'native_pads':rows,'native_pad_polygon_inner_outer_error_IU':1,'new_native_vias':vias,'R7036_actual_original_pose':True,'no_native_save_or_refill':True,'complete_current_source_native_afterfill_DRC_loop_thermal':'OPEN'},indent=1)+'\n');print('R399_NATIVE_ACTUAL_PAD_AND_VIA_MASK_PASS',flush=True)
