"""Preserve raw R362; correct a reused loop variable in reporting only."""
import json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent.parent
D=H/'sbc-power/CM79-R353-IO3-existing-actual-annulus-no-hole-fixed-Cu-bypass-nomination-r362'
O=H/'sbc-power/CM79-R362-exact-window-radius-metadata-correction-no-reroute-r363'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();assert (D/'receipt.json').exists();r=json.loads((D/'receipt.json').read_text());a=json.loads((D/'finite-port-layer-width-window-attempts.json').read_text());assert len(a)==r['attempt_count'];assert len(a)%6==0;fixed=[]
 for i,row in enumerate(a):
  assert row['ordinary_width_mm']==(.5,.5,.75,.75,1.,1.)[i%6]
  if i%6:assert (row['source_UUID'],row['detached_UUID'],row['layer'])==(a[i-i%6]['source_UUID'],a[i-i%6]['detached_UUID'],a[i-i%6]['layer'])
  fixed.append({**row,'raw_reported_radius_mm_preserved':row['local_window_radius_mm'],'local_window_radius_mm':(1.,3.)[i%2],'metadata_only_correction':'The actual clip was built before the terminal guard loop reused radius. No coordinates, obstacle, route, source or reference decision changed.'})
 put(O/'exact-geometry-window-corrected-attempts.json',fixed);put(O/'receipt.json',{'verdict':'REPORTING_ONLY_WINDOW_RADIUS_CORRECTION_NO_REROUTE_OR_GATE_CHANGE','raw_R362_receipt_sha256':sha(D/'receipt.json'),'raw_R362_attempts_sha256':sha(D/'finite-port-layer-width-window-attempts.json'),'corrected_attempts_sha256':sha(O/'exact-geometry-window-corrected-attempts.json'),'attempt_count':len(a),'raw_nomination_verdict':r['verdict'],'geometry_script_model_source_or_native_changes':0,'script_sha256':sha(__file__)});print('R363',sha(O/'receipt.json'),len(a),flush=True)
if __name__=='__main__':main()
