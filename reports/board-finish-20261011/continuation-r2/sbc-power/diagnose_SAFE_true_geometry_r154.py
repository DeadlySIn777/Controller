"""Map independent SAFE errors back to exact owned zone constituents."""
from pathlib import Path
import pickle,json,hashlib,collections
H=Path(__file__).resolve().parent.parent;O=H/'sbc-power/SAFE-independent-geometry-diagnosis-r154'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not O.exists();O.mkdir();mp=H/'sbc-power/safe-owned-zone-normalization-r149/model.pkl';g,h,b,z,c=pickle.loads(mp.read_bytes());by={q['uuid']:q for q in z}
 rf=H/'sbc-power/SAFE-independent-true-geometry-r152/receipt.json';r=json.loads(rf.read_bytes());assert r['model_sha256']==sha(mp)
 pairs=[]
 for e in r['errors']:
  a=by.get(e['owned_UUID']);bb=by.get(e['other_UUID'])
  if bb is not None:
   overlap=a['shape'].intersection(bb['shape']);pairs.append({**e,'A_raw_net':a['net'],'B_raw_net':bb['net'],'overlap_mm2':overlap.area,'overlap_bounds_mm':list(overlap.bounds) if not overlap.is_empty else None,'A_constituents':a['constituent_proposal_UUIDs'],'B_constituents':bb['constituent_proposal_UUIDs']})
 errors=collections.Counter(e['gate'] for e in r['errors']);actual=[e for e in r['errors'] if e['actual_gap_mm']<e['required_gap_mm']-.025]
 result={'verdict':'EXACT_ERROR_DIAGNOSIS_NO_WAIVERS','model_sha256':sha(mp),'independent_receipt_sha256':sha(rf),'error_counts':dict(errors),'below_ordinary_gap_count':len(actual),'below_ordinary_gap_rows':actual,'mutual_owned_plane_error_rows':pairs,'ordinary_new_via_hole_errors':[e for e in r['errors'] if e['gate'].startswith('NEW_via')],'all_geometry_and_contact_corrections_still_required':True,'native_jobs':0,'board_written':False}
 (O/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('SAFE_ERROR_COUNTS',dict(errors),'below_ordinary',len(actual));print('ACTUAL_MUTUAL',[p for p in pairs if p['actual_gap_mm']==0])
if __name__=='__main__':main()
