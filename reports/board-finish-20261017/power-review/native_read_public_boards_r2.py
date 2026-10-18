"""Native load-only portability smoke check; absolutely no Fill or Save calls."""
import ctypes
k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p;k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t];k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32];h=k.GetCurrentProcess();assert k.SetProcessAffinityMask(h,(1<<16)|(1<<17));assert k.SetPriorityClass(h,0x4000)
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,time
import pcbnew
ROOT=Path(__file__).resolve().parents[3];PKG=ROOT/'tmp/github-controller-public-20261018';OUT=Path(__file__).resolve().parent/'public-package-independent-review-r2';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 OUT.mkdir(exist_ok=True);rows=[];started=time.monotonic()
 for label in('baseline','staged'):
  p=PKG/'board'/label/'board.kicad_pcb';before=sha(p);b=pcbnew.LoadBoard(str(p));fps=list(b.GetFootprints());tracks=list(b.GetTracks());zones=list(b.Zones());vias=sum(isinstance(t,pcbnew.PCB_VIA)for t in tracks);pads=sum(len(list(f.Pads()))for f in fps);filled=sum(z.GetFilledPolysList(ly).OutlineCount()for z in zones for ly in(pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu)if z.HasFilledPolysForLayer(ly));assert len(fps)==2723 and pads==9971 and filled==0 and before==sha(p);rows.append({'project':label,'board_SHA256':before,'footprints':len(fps),'pads':pads,'tracks':len(tracks)-vias,'vias':vias,'native_board_zones_including_ruleareas':len(zones),'all6_filled_polygon_contours':filled,'native_load_success':True,'board_bytes_unchanged':True});del b,fps,tracks,zones
 r={'utc':datetime.now(timezone.utc).isoformat(),'status':'BOTH_PUBLIC_LOOSE_BOARDS_NATIVE_LOAD_ONLY_PASS_NO_FILL_SAVE','native_version':pcbnew.GetBuildVersion(),'rows':rows,'Fill_calls':0,'Save_calls':0,'DRC_calls':0,'package_modified':False,'elapsed_seconds':time.monotonic()-started,'script_SHA256':sha(Path(__file__))};(OUT/'native-load-only-receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'rows':rows,'seconds':r['elapsed_seconds']}))
if __name__=='__main__':main()
