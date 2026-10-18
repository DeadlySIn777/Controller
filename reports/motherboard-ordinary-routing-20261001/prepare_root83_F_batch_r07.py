"""Reuse actual collision/reference checks with finite SOURCE-pair A* routing."""
from pathlib import Path
p=Path(__file__).parent
s=(p/'route_root81_OUT_PERMIT_pair_r06.py').read_text()
s=s[:s.index('jobs=[]')]
s=s.replace('math,copy,shutil,itertools,time','math,copy,shutil,itertools,time,heapq')
s=s.replace('source26-C19042-local-bypass-r81','source26-reference-closure-and-spurs-r83').replace('source26-r81-r01/domain-map.json','source26-r83-r01/domain-map.json')
s=s.replace('import pcbnew','import pcbnew\nimport hardware_zone_motherboard_returns as zoneutils')
src=(p.parent/'motherboard-critical-routing-20261001/route_actual_FPGA_flash_MISO_F_only_r02.py').read_text()
path=src[src.index('def path('):src.index('\n\n\nstart=')]
path=path.replace('width=.35','width=.20').replace('clear(points,layer,width,space)','clear(points,name,layer,width,space)').replace('],layer,width,space)','],name,layer,width,space)')
path=path.replace('count>120000 or time.monotonic()-t0>240','count>25000 or time.monotonic()-t0>15')
s+=path+'''

jobs=[]
for name,row in m['nets'].items():
 candidates=[p for p in ps.values()if p.GetNetname()==name and p.IsOnLayer(pcbnew.F_Cu)and p.GetParentFootprint().GetReference()!='U1001']
 for p,q in itertools.combinations(candidates,2):
  length=math.dist(mm(p.GetPosition()),mm(q.GetPosition()))
  if 0<length<=25:jobs.append((length,name,p,q))
attempts=0
for length,name,p,q in sorted(jobs,key=lambda x:x[0]):
 b.BuildConnectivity()
 if q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(p)}:continue
 if attempts>=65 or len(groups)>=32:break
 attempts+=1
 fills={pcbnew.F_Cu:full_fills[pcbnew.F_Cu]}
 pair=[p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),q.GetParentFootprint().GetReference()+'.'+q.GetNumber()]
 points=path(mm(p.GetPosition()),mm(q.GetPosition()),pcbnew.F_Cu)
 if not points:
  blocked.append(dict(net=name,source_pair=pair,span_mm=length,reason='Finite actual F geometry/reference search has no accepted full path'))
  print(json.dumps(dict(blocked=pair,attempt=attempts)),flush=True);continue
 signal=[add_segment(a,z,name,pcbnew.F_Cu)for a,z in zip(points,points[1:])]
 groups.append(dict(net=name,source_pair=pair,source_pad_UUIDs=[p.m_Uuid.AsString(),q.m_Uuid.AsString()],signal_UUIDs=[u for u in signal if u],ground_UUIDs=[],new_copper_UUIDs=[u for u in signal if u],F_path_mm=points))
 print(json.dumps(dict(added_pair=pair,net=name,newCu=len(signal),attempt=attempts)),flush=True)
dest=OUT/'motherboard-ordinary-F-batch-candidate.kicad_pcb'
pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(BASE.with_suffix(suffix),dest.with_suffix(suffix))
for f in BASE.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
assert all(e.sha(p)==h for p,h in frozen.items())
e.write(OUT/'proposed-groups.json',dict(input_sha256=frozen,base_sha256=e.sha(BASE),groups=groups,blocked=blocked,new_copper_UUIDs=[t.m_Uuid.AsString()for t in added],actual_signal_layers=['F.Cu'],actual_common_reference='In1.Cu',no_added_drills=True,native_refill_DRC_full_return_and_SOURCE_validation_pending=True,manufacturing_ready=False))
print(json.dumps(dict(groups=len(groups),newCu=len(added),blocked=len(blocked))),flush=True)
'''
dest=p/'route_root83_F_batch_r07.py';dest.write_text(s);compile(s,str(dest),'exec')
