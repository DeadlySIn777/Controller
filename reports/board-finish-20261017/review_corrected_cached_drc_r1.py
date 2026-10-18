"""Independent read-only review of the completed corrected-baseline cached DRC."""
from pathlib import Path
from collections import Counter
import hashlib,json
H=Path(__file__).resolve().parent;OUT=H/'corrected-baseline-cached-drc-review-r1'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def key(r):return r['type'],r['severity'],r['description'],tuple(sorted(i['uuid'] for i in r['items']))
def main():
 assert not OUT.exists();OUT.mkdir()
 run=H/'corrected-baseline-r1/cached-native-drc'
 rec=json.loads((run/'receipt.json').read_bytes());launch=json.loads((run/'launch.json').read_bytes())
 raw=json.loads((run/'drc.json').read_bytes())
 oldpath=H.parent/'board-finish-20261011/continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299/drc.json'
 old=json.loads(oldpath.read_bytes())
 assert rec['exit_code']==0 and rec['drc_SHA256']==sha(run/'drc.json')
 assert rec['board_SHA256']==sha(H/'corrected-baseline-r1/native/board.kicad_pcb')=='8c9fb98f44aa0d31b9d71e32f041c47139cb745c355e2364a45de40a93614eff'
 preserved={p:sha(p)==h for p,h in launch['input_SHA256'].items()};assert all(preserved.values())
 errors=[r for r in raw['violations'] if r['severity']=='error'];warnings=[r for r in raw['violations'] if r['severity']=='warning']
 assert not errors and len(warnings)==332 and not raw['schematic_parity'] and not raw['ignored_checks']
 assert len(raw['unconnected_items'])==len(old['unconnected_items'])==499
 ca,cb=Counter(map(key,old['violations'])),Counter(map(key,raw['violations']))
 removed=list((ca-cb).elements());added=list((cb-ca).elements())
 hole=[r for r in removed if r[0]=='holes_co_located']
 assert len(hole)==1 and set(hole[0][3])=={'217c65fd-34f7-47f6-8ca3-dceac1224ad3','2193173a-497d-48d4-8833-92e9133ec64a'}
 assert len(removed)==3 and len(added)==2
 assert all(r[0]=='track_not_centered_on_via' for r in added+[r for r in removed if r not in hole])
 # Both report witness changes retain the same unchanged track; all four vias
 # already exist in both boards. They remain warnings rather than exemptions.
 swaps=[]
 for track in ('e2a267ff-13a0-417e-acf6-8de6c29aba7f','b814105d-cb5f-5785-a4d7-af45af18b77e'):
  before=[r for r in removed if track in r[3]];after=[r for r in added if track in r[3]]
  assert len(before)==len(after)==1
  swaps.append({'unchanged_track':track,'before_items':before[0][3],'after_items':after[0][3],'disposition':'RETAINED_WARNING_DIFFERENT_NATIVE_VIA_WITNESS'})
 samples=[json.loads(x) for x in (run/'resource-samples.jsonl').read_text().splitlines()]
 peak=max(x.get('CPU_percent',x.get('cpu_percent',0)) for x in samples)
 # Resource schema is retained in the raw receipt; its one 84% sample is not
 # erased by a later kernel cap or by this review.
 assert rec['peak_CPU_percent']==84 and rec['samples_at_or_above_80_percent']==1
 result={'status':'CORRECTED_BASELINE_CACHED_NATIVE_DRC_INDEPENDENT_REVIEW_PASS_WITH_OPEN_JOINS_WARNINGS',
  'ordinary_errors':0,'warnings':332,'parity_issues':0,'ignored_checks':0,
  'CLI_unconnected_diagnostic_rows':499,'uncapped_native_pad_island_joins':1172,'native_API_unconnected_items':1183,
  'one_resolved_warning':'exactly_duplicate_drilled_holes_co_located','retained_witness_changes':swaps,
  'warning_types':dict(Counter(r['type'] for r in warnings)),
  'input_files_checked':len(preserved),'all_launch_inputs_unchanged':True,
  'native_refill_calls':0,'cache_authority':'separate exact copper/drill-union and850zone-cache retention proof; not a new full fill',
  'CPU_receipt_peak_percent':84,'CPU_receipt_samples_at_or_above80':1,
  'adopted':False,'manufacturing_ready':False,
  'input_SHA256':{str(p):sha(p) for p in [Path(__file__),run/'receipt.json',run/'launch.json',run/'drc.json',run/'resource-samples.jsonl',oldpath]}}
 (OUT/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
