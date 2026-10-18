"""Read native IU drill metadata only; Fill0/Save0."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import pcbnew,json,hashlib,time,gc
from pathlib import Path
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3];OLD=PROJECT/'reports/board-finish-20261011/continuation-r2';OUT=HERE/'read-only-native-drill-IU-r1'
SOURCES={'before':(OLD/'R155-known-reference-native-diagnostic-r157/measure/copy/board.kicad_pcb','3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38'),'after':(OLD/'combined-R753-one-full-native-fill-cached-DRC-r299/filled-copy/board.kicad_pcb','6d7719335455a1941c28de1ebd750e862915d483049dd90226e054bd559e1632')}
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def put(n,r):(OUT/n).write_text(json.dumps(r,indent=1)+'\n',encoding='utf-8')
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();counts={}
 for side,(source,expected)in SOURCES.items():
  assert sha(source)==expected;b=pcbnew.LoadBoard(str(source));pads=[];vias=[]
  for fp in b.GetFootprints():
   for p in fp.Pads():
    drill=p.GetDrillSize()
    if max(drill.x,drill.y)==0:continue
    at=p.GetPosition();offset=p.GetOffset()
    pads.append({'UUID':p.m_Uuid.AsString(),'ref':fp.GetReference(),'pin':p.GetNumber(),'raw_net':p.GetNetname(),'at_IU':[at.x,at.y],'drill_IU':[drill.x,drill.y],'drill_shape_enum':int(p.GetDrillShape()),'round_drill_enum':int(pcbnew.PAD_DRILL_SHAPE_CIRCLE),'orientation_degrees':p.GetOrientationDegrees(),'copper_offset_IU':[offset.x,offset.y],'attribute_enum':int(p.GetAttribute())})
  for v in b.GetTracks():
   if not isinstance(v,pcbnew.PCB_VIA):continue
   at=v.GetPosition();vias.append({'UUID':v.m_Uuid.AsString(),'raw_net':v.GetNetname(),'at_IU':[at.x,at.y],'drill_IU':v.GetDrillValue(),'via_type_enum':int(v.GetViaType()),'layers':[b.GetLayerName(l)for l in b.GetEnabledLayers().CuStack()if v.GetLayerSet().Contains(l)]})
  put(side+'-native-holes.json',{'board':str(source),'board_SHA256':expected,'pads':pads,'vias':vias});counts[side]={'drilled_pads':len(pads),'vias':len(vias)}
  assert sha(source)==expected;del b;gc.collect();print('READ_NATIVE_HOLES',side,counts[side],flush=True)
 put('receipt.json',{'status':'NATIVE_IU_DRILL_METADATA_READ_ONLY_BOUND','counts':counts,'native_Fill_calls':0,'native_Save_calls':0,'source_inputs_unchanged':True,'adopted':False,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),*[q[0]for q in SOURCES.values()])},'elapsed_seconds':time.monotonic()-st})
if __name__=='__main__':main()
