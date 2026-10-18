"""Read-only native pad keys/positions for routing priority; no connectivity/fill."""
from pathlib import Path
from collections import Counter
import ctypes,hashlib,json
H=Path(__file__).resolve().parent;OUT=H/'join-throughput-r1'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 assert not OUT.exists();OUT.mkdir()
 k=ctypes.windll.kernel32;k.GetCurrentProcess.restype=ctypes.c_void_p
 k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
 assert k.SetProcessAffinityMask(k.GetCurrentProcess(),(1<<16)|(1<<17))
 import pcbnew
 board=H/'combined-route-stage-r4/native/board.kicad_pcb';pinned=sha(board)
 b=pcbnew.LoadBoard(str(board));pads={}
 for f in b.GetFootprints():
  seen=Counter()
  for p in f.Pads():
   num=str(p.GetNumber());key=f'{f.GetReference()}.{num}#{seen[num]}';seen[num]+=1
   assert key not in pads
   pads[key]={'UUID':str(p.m_Uuid.AsString()),'raw_net':str(p.GetNetname()),
    'at_IU':[int(p.GetPosition().x),int(p.GetPosition().y)],
    'size_IU':[int(p.GetSize().x),int(p.GetSize().y)],
    'Cu_layers':[str(b.GetLayerName(l)) for l in p.GetLayerSet().Seq() if l in b.GetEnabledLayers().CuStack()]}
 assert len(pads)==9971 and sha(board)==pinned
 result={'board':str(board),'board_SHA256':pinned,'pads':pads,'native_fill_calls':0,'native_save_calls':0,'native_connectivity_rebuild_calls':0,'scope':'pad center/size/layer inventory only; routing must use actual finite geometry/native109/source floors','script_SHA256':sha(Path(__file__))}
 (OUT/'native-pad-inventory.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'NATIVE_PAD_INVENTORY_READ_ONLY','pads':len(pads)}))
if __name__=='__main__':main()
