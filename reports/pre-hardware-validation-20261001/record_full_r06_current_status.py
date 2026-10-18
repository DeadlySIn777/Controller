"""Bind current status summaries to the completed immutable ROOT102 full run."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'reports/pre-hardware-validation-20261001/full-analog-plant-r06'
r=json.loads((P/'report.json').read_text())
assert r['status_counts']=={'BLOCKED':9,'NOT_RUN':1,'PASS':20} and r['source_hashes_unchanged']
assert r['original_source_file_count']==3765
assert json.loads((P/'host-cases/receipt.json').read_text())['passed_tests']==1880
assert json.loads((P/'native-cases/receipt.json').read_text())['passed_tests']==235
assert r['started_from']['board_sha256']=='769541d11876ea0050240ec065f6b0b85bff19c7c8324f1c26b9b637212a8af5'
changes=[]
for name in ('PROJECT_MEMORY.md','reports/ENGINEERING_STATUS.md','docs/CURRENT_ACCEPTANCE_GATES.md'):
    path=ROOT/name;old=path.read_text();new=old
    replacements={
      '[Full disconnected r05]':'[Full disconnected r06]',
      'pre-hardware-validation-20261001/full-two-cap-r05/report.json':'pre-hardware-validation-20261001/full-analog-plant-r06/report.json',
      'passed **17 stages**, left **9 blocked**':'passed **20 stages**, left **9 blocked**',
      '**1,876 host cases and 235 native KiCad cases pass**':'**1,880 host cases and 235 native KiCad cases pass**',
      '**3,327 scoped source hashes**':'**3,765 scoped source hashes**',
      'This supersedes the earlier r101 regression as the current exact-board run.':'This supersedes r05 as the current exact-board run and freshly includes 96 passive filter cases, 12 manufacturer-buffer cases, and the isolated mechanics fixture with 1,114 checks and 12 compiled negative controls. The ROOT102 PCB and Source26 electrical design are unchanged.'}
    for a,b in replacements.items():
        assert new.count(a)==1,(name,a,new.count(a))
        new=new.replace(a,b)
    path.write_text(new,encoding='utf8')
    changes.append({'path':name,'before_sha256':hashlib.sha256(old.encode()).hexdigest(),'after_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(P/'current-status-binding.json').write_text(json.dumps({'report_sha256':hashlib.sha256((P/'report.json').read_bytes()).hexdigest(),'changes':changes,'electrical_source_or_PCB_modified':False,'manufacturing_ready':False},indent=2)+'\n')
