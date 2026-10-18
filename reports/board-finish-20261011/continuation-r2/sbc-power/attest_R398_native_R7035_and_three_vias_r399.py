"""Read-only native actual pose, inner/outer pad polygons and three via masks."""
import sys,json,pickle,hashlib,shutil,os,subprocess,time,traceback
from pathlib import Path
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_aux_exact_raw as A
O=H/'sbc-power/CM79-R398-native-R7035-real-pose-three-via-mask-readonly-r399'
N=H/'sbc-power/CM79-R397-exact-five-tracks-three-ordinary-vias-R7035-real-pose-r398'
D=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371'
R=H/'sbc-power/CM79-R366-no-hole-IO3-plus-positive-J1-In4-support-fresh-current-independent-r369'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
API=r'''import sys,json,hashlib
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
'''
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(N/'receipt.json')=='15645748433749a8fb4008de17719cdd7938ffeabe83b0dc8c1aa18d8e135fe5';pack=pickle.loads((N/'exact-five-tracks-three-vias-R7035-pose-only-packet.pkl').read_bytes());source=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';raw=source.read_bytes();iv=A.C.inventory(raw);oldfp=Path(pack['exact_FP_before_file']);newfp=Path(pack['exact_FP_after_file']);assert iv[3][pack['FP_UUID']]==oldfp.read_bytes();adds={}
 for row in json.loads((N/'exact-new-Cu-operation-ledger.json').read_text()):p=Path(row['file']);assert sha(p)==row['sha256'];adds[row['uuid']]=p.read_bytes()
 for row in json.loads((R/'only-nine-exact-new-IO3-native-chunks.json').read_text()):p=Path(row['exact_native_chunk_path']);assert sha(p)==row['exact_native_chunk_sha256'];adds[row['UUID']]=p.read_bytes()
 z=json.loads((D/'exact-one-new-positive-LG-native-profile-and-rings.json').read_text());zp=Path(z['exact_native_chunk_path']);assert sha(zp)==z['exact_native_chunk_sha256'];adds[z['UUID']]=zp.read_bytes();assert len(adds)==18 and not(set(adds)&set(iv[3]));chunks=[newfp.read_bytes()if ch==oldfp.read_bytes()else ch for ch in iv[1]];data=iv[0]+b''.join(chunks)+b''.join(adds.values())+iv[2];out=A.C.inventory(data);assert set(out[3])==set(iv[3])|set(adds);assert all(out[3][u]==ch for u,ch in iv[3].items()if u!=pack['FP_UUID']);assert out[3][pack['FP_UUID']]==newfp.read_bytes();A.N.SourceNets(raw).assert_chunks(adds);copydir=O/'copy';copydir.mkdir();board=copydir/'board.kicad_pcb';board.write_bytes(data)
 for name in('board.kicad_pro','board.kicad_dru'):shutil.copy2(H/'sbc-native-contract-r1/copy'/name,copydir/name)
 expected={p['old']['uuid']:{'pin':str(p['old']['num']),'raw_net':p['old']['net'],'at_IU':[round(p['xy'][0]*1e6),round(p['xy'][1]*1e6)]}for p in pack['R7035_source_scope']['pads']}if False else{}
 for p in pack['R7035_source_scope']['pads']:
  x=81.147-(p['x']-84.547);y=27.7-(p['y']-24.7);expected[p['uuid']]={'pin':str(p['num']),'raw_net':p['net'],'at_IU':[round(x*1e6),round(y*1e6)]}
 spec={'candidate_sha256':sha(board),'FP_UUID':pack['FP_UUID'],'expected_pads':expected,'expected_new_vias':{v['uuid']:{'raw_net':v['net'],'at_IU':[round(v['x']*1e6),round(v['y']*1e6)]}for v in pack['vias']}};put(O/'expected-exact-native-pose-and-three-vias.json',spec);helper=O/'native_R7035_pose_three_via_readonly_r399.py';helper.write_text(API,encoding='utf-8');wrapper=Path('Z:/pcb-runs/claude-finish/tools/heavym.sh');api=Path('C:/Program Files/KiCad/10.0/bin/python.exe');cmd=['C:/Program Files/Git/usr/bin/sh.exe',str(wrapper),'kicad',str(api),str(helper),str(O/'expected-exact-native-pose-and-three-vias.json'),str(board),str(O/'actual-native-API.json')];pins={str(p.resolve()):sha(p)for p in[source,oldfp,newfp,N/'receipt.json',N/'exact-five-tracks-three-vias-R7035-pose-only-packet.pkl',helper,O/'expected-exact-native-pose-and-three-vias.json',wrapper,api,*copydir.iterdir()]};put(O/'inputs.json',{'pins':pins,'command':cmd,'slot':'existing_main1','new_slots':0,'scope':'Serialization clone old eedf + R371 nineIO3/oneLG + R398 five tracks/threevias/one real FP root move; exact pose/mask read-only, not full current/refill/source/DRC'});put(O/'status.json',{'phase':'EXACT_NATIVE_POSE_AND_VIA_API_QUEUED_MAIN1'});env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH'];print('R399_API_START',sha(board),flush=True)
 with(O/'native-API.log').open('w',encoding='utf-8')as log:run=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
 assert run.returncode==0;assert all(sha(p)==v for p,v in pins.items());r=json.loads((O/'actual-native-API.json').read_text());assert r['verdict'].startswith('PASS_');put(O/'receipt.json',{'verdict':'PASS_NATIVE_EXACT_R7035_PAD_POSE_THREE_ORDINARY_VIA_MASKS_READONLY','R398_receipt_sha256':sha(N/'receipt.json'),'R398_packet_sha256':sha(N/'exact-five-tracks-three-vias-R7035-pose-only-packet.pkl'),'clone_sha256':sha(board),'actual_native_API_sha256':sha(O/'actual-native-API.json'),'actual_R7035_two_pad_inner_outer_polygons_exported_error_IU':1,'all_three_new_via_actual_beforefill_flashed_layers':6,'all_original_other_native_chunks_exact':True,'all_R7036_original_native_pose_and_source_function_held':True,'native_save_refill_or_fullcurrent_claim':False,'actual_afterfill_source_oldrelationships_oldrefs_allmasks_current_thermal':'OPEN','adopted':False,'elapsed_seconds':time.monotonic()-started});put(O/'status.json',json.loads((O/'receipt.json').read_text()));print('R399',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
