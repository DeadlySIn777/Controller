"""Correct current prose spacing and canonical LF report serialization; preserve failed attempt."""
from pathlib import Path
import hashlib,json,re,sys
root=Path.cwd();sys.path.insert(0,str(root/'tools'))
from check_release import check_release
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=root/'reports/motherboard-cad-publication-20261002/ROOT104-current-docs-r02';out.mkdir(exist_ok=False)
changes={}
def save(p,s):
 dest=out/p.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
 p.write_text(s,encoding='utf8',newline='\n');changes[str(p.relative_to(root))]=dict(before_sha256=sha(dest),after_sha256=sha(p))
for name in ['PROJECT_MEMORY.md','reports/ENGINEERING_STATUS.md','docs/BUILD_PLAN.md','docs/PLATFORM_ROADMAP.md','docs/CURRENT_ACCEPTANCE_GATES.md','hardware/board_review/README.md']:
 p=root/name;parts=p.read_text(encoding='utf8').split('\n\n');new=[]
 for s in parts:
  if s.startswith('**Current physical implementation:**'):
   for old,newtext in [('Source26/ROOT103','Source26/ROOT104'),('CAD29','CAD30'),('11,759','11,807'),('3,521','3,508'),('110 owned','120 owned'),('225 receiving','245 receiving')]:s=s.replace(old,newtext)
  if s.startswith(('**Current','[Fresh full r08]','[Characterization r06]','[Current native drill','[Unchanged Source26','- **Current','- **Live physical','## Current published','[Native KiCad project]')):
   s=re.sub(r'(?<=\d), (?=\d{3}\b)',',',s)
   s=re.sub(r'\b(and|intersecting|complete|all|includes|cover|revision|the|at|of|in)(?=\d)',r'\1 ',s)
   s=re.sub(r',(?=[A-Za-z])',', ',s)
   s=re.sub(r'(?<=\d)(?=MHz\b|mm\b|ms\b)', ' ',s)
  new.append(s)
 save(p,'\n\n'.join(new))
manifest=root/'manufacturing/release-manifest.json';m=json.loads(manifest.read_text())
save(manifest,json.dumps(m,indent=2)+'\n')
for stage in ['prototype','production']:
 result=check_release(m,root,stage);assert not result['ready']
 save(root/f'reports/{stage}-release-check.json',json.dumps(result,indent=2)+'\n')
(out/'receipt.json').write_text(json.dumps(dict(passed=True,changes=changes,reason='Correct numeric prose spacing/current physical paragraph and LF serialization found by two live release report tests. No PCB/source/geometry or release readiness change.',manufacturing_ready=False),indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(dict(passed=True,files=len(changes))))
