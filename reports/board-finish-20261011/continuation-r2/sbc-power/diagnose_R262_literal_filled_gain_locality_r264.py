"""Literal failed-operation geometry sizes/locality, no correction/adoption."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely import from_wkb
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
O=H/'sbc-power/R262-literal-filled-gain-locality-r264'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def row(s):return{'geometry_type':s.geom_type,'empty':s.is_empty,'area_mm2':s.area,'bounds':list(s.bounds)if not s.is_empty else None,'length_mm':s.length,'WKB_sha256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 assert not O.exists();O.mkdir();P=H/'sbc-power/T4-R7-sparse-exact-R250-diagnostic-r262/T4-plus-R7';failure=P/'strict-construction-failures.json';fs=json.loads(failure.read_text());bp=H/'sbc-power/T4-R7-sparse-exact-R250-diagnostic-r262/T4-only/model.pkl';g,h,b,q,c=pickle.loads(bp.read_bytes());zs={z['uuid']:z for z in c['zones']};rows=[]
 for r in fs:
  if r['kind']!='filled_record_exact_scope_or_gain_failure':continue
  uid,l,i=r['UUID'],r['layer'],r['record'];prefix=uid+'-'+l+'-'+str(i);gain=from_wkb((P/(prefix+'-gain.wkb')).read_bytes());extra=from_wkb((P/(prefix+'-extra-withdrawal.wkb')).read_bytes());raw=from_wkb((P/(prefix+'-rawremaining.wkb')).read_bytes());before=L.poly(zs[uid]['fills'][l])[i]
  rows.append({'UUID':uid,'layer':l,'record':i,'exact_old_record_sha256':hashlib.sha256(before.wkb).hexdigest(),'literal_positive_gain':row(gain),'literal_extra_negative_withdrawal':row(extra),'gain_is_literal_subset_of_old_record':gain.difference(before).is_empty,'gain_distance_to_old_boundary_mm':gain.distance(before.boundary)if not gain.is_empty else None,'extra_distance_to_old_boundary_mm':extra.distance(before.boundary)if not extra.is_empty else None,'failed_raw_remaining':row(raw),'new_primitive_cuts':r['cuts']})
 result={'verdict':'EXACT_FAILED_FILLED_OPERATION_LOCALITY_NO_TOLERANCE_OR_REPAIR','base_T4_model_sha256':sha(bp),'frozen_failure_sha256':sha(failure),'rows':rows,'no_original_source_board_or_geometry_mutated':True,'native_jobs':0,'board_written':False};f=O/'receipt.json';f.write_text(json.dumps(result,indent=1)+'\n');print('R264_COMPLETE',sha(f),json.dumps(rows),flush=True)
if __name__=='__main__':main()
