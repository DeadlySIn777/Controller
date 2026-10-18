"""Native parser proof for exact13 additive FG/In3 segments and four old ports."""
import ctypes
k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p;k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t];k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32];h=k.GetCurrentProcess();assert k.SetProcessAffinityMask(h,(1<<16)|(1<<17));assert k.SetPriorityClass(h,0x4000)
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
import pcbnew
HERE=Path(__file__).resolve().parent;OUT=HERE/'additive-FG48-native-readback-r37b';M=HERE/'additive-FG48-stage3-sparse-packet-r36/manifest.json';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not OUT.exists();OUT.mkdir();d=json.loads(M.read_text());p=Path(d['native_readback_only_fixture']);assert sha(p)==d['native_readback_only_fixture_SHA256'];b=pcbnew.LoadBoard(str(p));alltracks={t.m_Uuid.AsString():t for t in b.GetTracks()};zone=next(z for z in b.Zones()if z.m_Uuid.AsString()==d['native_FG_comparison_zone_UUID']);rows=[]
 for op in d['operations']:
  t=alltracks[op['UUID']];assert t.GetWidth()==round(op['native_width_mm']*1e6)and t.GetLayer()==pcbnew.In3_Cu and t.IsLocked();a=t.GetStart();z=t.GetEnd();assert[a.x,a.y]==[round(v*1e6)for v in op['native_start_mm']]and[z.x,z.y]==[round(v*1e6)for v in op['native_end_mm']];assert t.GetNetCode()==zone.GetNetCode()and t.GetNetname()==zone.GetNetname();rows.append({'UUID':t.m_Uuid.AsString(),'start_IU':[a.x,a.y],'end_IU':[z.x,z.y],'width_IU':t.GetWidth(),'layer':t.GetLayerName(),'locked':True,'same_native_FG_net_code':True})
 for uid in d['retained_existing_via_UUIDs']:
  v=alltracks[uid];assert isinstance(v,pcbnew.PCB_VIA)and v.GetNetCode()==zone.GetNetCode();assert v.GetWidth(pcbnew.In3_Cu)==600000 and v.GetDrillValue()==300000
 assert len(alltracks)==len(rows)+4;r={'utc':datetime.now(timezone.utc).isoformat(),'status':'EXACT_NATIVE13_LOCKED_IN3_SEGMENTS_AND4_RETAINED_06_03_FG_PORTS_PASS_NO_FILL','input_sha256':{str(f):sha(f)for f in(M,p,Path(__file__))},'native_version':pcbnew.GetBuildVersion(),'rows':rows,'retained_old_via_UUIDs':d['retained_existing_via_UUIDs'],'native_FG_net_name':zone.GetNetname(),'fill_called':False,'DRC_called':False,'actual_native_clearance_fill_minwidth_source_reference_current_signed_KCL_material_thermal_SI':'OPEN; parser evidence only','adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'tracks':len(rows)}))
if __name__=='__main__':main()
