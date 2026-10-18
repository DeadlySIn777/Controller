"""Strict actual native partition diagnostics while DRC remains pending."""
import hashlib,importlib.util,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;REPORT=HERE.parent.parent.parent.parent
spec=importlib.util.spec_from_file_location('actual_strict_guard',REPORT/'gate-repair/partition_guard.py')
G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 out=REPORT/'measure/r07-four-fag-shared';root=Path('Z:/pcb-runs/claude-finish')
 paths={'candidate':REPORT/'power-audit/fag-r07-repair/staged/r07-four-path-fag-repaired.kicad_pcb','r07':root/'integrate/revs/r07-ripup-signals-1.kicad_pcb','live':root/'integrate/board.kicad_pcb','r06':root/'integrate/revs/r06-stitch-plane-pads-2.kicad_pcb','after':out/'partitions.json','before_r07':root/'integrate/measure/r07-ripup-signals-1/partitions.json','before_r06':root/'integrate/measure/r06-stitch-plane-pads-2/partitions.json','guard':Path(G.__file__),'script':Path(__file__)}
 raw={role:path.read_bytes() for role,path in paths.items()};a=json.loads(raw['after']);r07=json.loads(raw['before_r07']);r06=json.loads(raw['before_r06'])
 G.check_board(a,paths['candidate']);G.check_board(r07,paths['r07']);G.check_board(r06,paths['r06'])
 if sha(raw['live'])!=sha(raw['r07']):raise ValueError('Actual live changed')
 guards={'r07_live':G.compare(r07,a),'r06':G.compare(r06,a)}
 for role,path in paths.items():
  if path.read_bytes()!=raw[role]:raise ValueError('Diagnostic source changed during read:'+role)
 result={'schema':'actual-dual-native-partition-diagnostic-v1','verdict':'NATIVE_PARTITION_DIAGNOSTIC_DRC_PENDING','candidate_sha256':sha(raw['candidate']),'connectivity':guards,'observed_source_hashes':{str(paths[role]):sha(data) for role,data in raw.items()},'native_jobs':0,'adopted':False,'manufacturing_ready':False,'scope':'Actual uncapped refilled native pad partitions; not final acceptance before raw DRC and final frozen checks'}
 destination=HERE/'actual-native-guards.json'
 if destination.exists():raise ValueError('Fresh diagnostic required')
 destination.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({role:{k:g[k] for k in ('verdict','completed','lost','before_sha256','after_sha256')} for role,g in guards.items()},indent=1))
if __name__=='__main__':main()
