"""Test actual retained AUX connectivity before assuming a companion is necessary."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import copy,json,pickle
from pathlib import Path
from shapely.geometry import Point
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;O=H/'R11054-AUX-retained-endpoint-groups-r201'
def main():
 assert not O.exists();O.mkdir();B=H/'R11054-rotated-AUX-source-search-base-r194/model.pkl';assert sha(B)=='344b9416a4e86e12ca3587d2a4e1439e1ddd943510afcf3f33ae1fa9282827f3';g,h,b,z,c=pickle.loads(B.read_bytes());R=H/'R11054-fault-preserving-exact-AUX-wall-r192';d=pickle.loads((R/'nomination.pkl').read_bytes());r=json.loads((R/'receipt.json').read_text(encoding='utf-8'));remove={q['uuid'] for q in d['tracks']};after={**c,'tracks':[q for q in c['tracks'] if q['uuid'] not in remove]};net=C.norm(r['owned_original_two_tracks'][0]['net']);old=F.graph(c,net);new=F.graph(after,net);rows=[]
 for i,xs in enumerate(new):
  a=Point(r['owned_original_two_tracks'][0]['a']);bb=Point(r['owned_original_two_tracks'][1]['b']);rows.append({'group':i,'physical_keys':len(F.discrete_keys(xs)),'pads':sorted({(q['ref'],q['pin']) for q in xs if q['kind']=='pad'}),'at_source_retained_endpoint':any(q['layer']=='F.Cu' and q['shape'].covers(a) for q in xs),'at_target_retained_endpoint':any(q['layer']=='F.Cu' and q['shape'].covers(bb) for q in xs),'existing_actual_and_prospective_via_UUIDs':sorted({q['uuid'] for q in xs if q['kind']=='via'})})
 print(json.dumps(rows),flush=True);(O/'receipt.json').write_text(json.dumps({'verdict':'EXACT_RETAINED_AUX_COMPONENT_DIAGNOSTIC_ONLY','input_model_sha256':sha(B),'R192_nominee_four_tracks_withdrawn':sorted(remove),'original_two_tracks_remain_explicit_owned_deletes':r['owned_original_two_tracks'],'original_R192_AUX_group_count':len(old),'after_owned_two_track_delete_group_count':len(new),'rows':rows,'source_current_full76_reference_native_acceptance':'OPEN','board_written':False,'native_jobs':0},indent=1)+'\n',encoding='utf-8');print('R201',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
