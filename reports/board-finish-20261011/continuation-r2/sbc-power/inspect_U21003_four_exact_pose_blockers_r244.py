"""Pin immutable primitive blockers before changing another pose coordinate."""
import hashlib,json,pickle
from pathlib import Path
H=Path(__file__).resolve().parent.parent;O=H/'sbc-power/U21003-four-exact-pose-blockers-r244'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not O.exists();O.mkdir();a=H/'sbc-power/U21003-rotated-pose-independent-wall-scope-r242';assert sha(a/'receipt.json')=='d2e8e8f829449693632cb973b64d3e5d260f071dfebd9b2f2b48fb7ab75a4cb4';d=H/'sbc-power/U21003-cap-pullup-rotated-return-nominees-r241';g,h,b,z,c=pickle.loads((d/'owned-cap-translation-host-checkpoint.pkl').read_bytes());errs=json.loads((a/'errors.json').read_text());wanted={e['other_UUID']for e in errs if'other_UUID'in e};rows=[]
 for kind in('tracks','vias','pads'):
  for q in h[kind]:
   if q['uuid']in wanted:rows.append({'kind':kind,'exact_original_or_unchanged_discrete_record':q})
 (O/'receipt.json').write_text(json.dumps({'verdict':'LITERAL_PRIMITIVE_POSE_CONFLICT_AUTHORITY_NO_MUTATION','R242_receipt_sha256':sha(a/'receipt.json'),'R241_model_sha256':sha(d/'owned-cap-translation-host-checkpoint.pkl'),'rows':rows,'all_foreign_analog_sense_and_limited_power_remain_hard':True,'native_jobs':0,'board_written':False,'script_sha256':sha(__file__)},indent=1)+'\n');print('R244_COMPLETE',sha(O/'receipt.json'),rows,flush=True)
if __name__=='__main__':main()
