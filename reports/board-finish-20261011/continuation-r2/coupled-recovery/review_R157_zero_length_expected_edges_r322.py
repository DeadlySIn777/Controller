"""Independent integer-only review of R160 expected edge correction; no pcbnew."""
from pathlib import Path
import json,hashlib,collections
H=Path(__file__).resolve().parent;P=H.parent;S=P/'R155-known-reference-native-diagnostic-r157'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def canonical(r):
 r=[tuple(p)for p in r]
 if len(r)>1 and r[0]==r[-1]:r.pop()
 return min(tuple(t[i:]+t[:i])for t in(r,list(reversed(r)))for i,p in enumerate(t)if p==min(r))
def edges(r):return collections.Counter((tuple(a),tuple(b))for a,b in zip(r,r[1:]+r[:1])if a!=b)
def area2(r):return sum(a[0]*b[1]-b[0]*a[1]for a,b in zip(r,r[1:]+r[:1]))
diag=P/'R157-zone-coordinate-diagnosis-r158.json';assert sha(diag)=='e07f923441e1776d675fa3034424ea368f7ea6370af94a8e2cbc1bde4b930bcd';d=read(diag);old=read(S/'expected-zones.json');newfile=S/'exact-adjacent-duplicate-vertices-r160/expected-zones.json';new=read(newfile);board=S/'copy/board.kicad_pcb';assert sha(board)==d['candidate_sha256']==old['candidate_sha256']==new['candidate_sha256']=='3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38'
assert {k:v for k,v in old.items()if k!='zones'}=={k:v for k,v in new.items()if k!='zones'}and len(old['zones'])==len(new['zones'])==200
bound={x['uuid']:x for x in d['rows']};changes=[]
for before,after in zip(old['zones'],new['zones']):
 assert {k:v for k,v in before.items()if k!='rings_IU'}=={k:v for k,v in after.items()if k!='rings_IU'}
 if before['rings_IU']==after['rings_IU']:continue
 uid=before['uuid'];assert uid in bound and before['rings_IU']==bound[uid]['raw_expected_rings_IU'];assert len(before['rings_IU'])==len(after['rings_IU'])==len(bound[uid]['raw_native_rings_IU'])
 for i,(a,b,native)in enumerate(zip(before['rings_IU'],after['rings_IU'],bound[uid]['raw_native_rings_IU'])):
  assert all(isinstance(v,int)for point in a+b+native for v in point)
  clean=[point for j,point in enumerate(a)if not j or point!=a[j-1]];assert b==clean and edges(a)==edges(b)and area2(a)==area2(b)and canonical(b)==canonical(native)
  assert len(a)-len(b)==(1 if i==0 else 0)
 changes.append({'uuid':uid,'removed_exact_adjacent_zero_length_outer_edges':1,'all_nondegenerate_directed_edges_same_multiset':True,'exact_integer_doubled_signed_area_same':True,'cleaned_raw_expected_matches_original_raw_native_cyclic_ring_exact':True,'all_other_metadata_rings_identical':True})
assert {x['uuid']for x in changes}=={'0929ae75-1efc-5015-af08-223abac05c5e','61cb8179-7754-5031-bbea-0da464bf816f'}
assert (H/'R320-own-quadratic-ring-review-stopped-preserved.json').is_file()
out=H/'R157-zero-length-expected-edge-independent-review-r322';assert not out.exists();out.mkdir();receipt={'verdict':'PASS_INTEGER_ONLY_TWO_EXACT_ZERO_LENGTH_EXPECTED_EDGES_NO_GEOMETRY_CHANGE','candidate_sha256':sha(board),'expected_before_file':str(S/'expected-zones.json'),'expected_before_sha256':sha(S/'expected-zones.json'),'expected_after_file':str(newfile),'expected_after_sha256':sha(newfile),'diagnosis_file':str(diag),'diagnosis_sha256':sha(diag),'corrector_file':str(P/'attest_R157_exact_native_adjacent_duplicate_vertices_r160.py'),'corrector_sha256':sha(P/'attest_R157_exact_native_adjacent_duplicate_vertices_r160.py'),'changes':changes,'all198_other_zone_expected_rows_exact':True,'no_coords_rounding_sorting_tolerance_replacement_or_new_native_read':True,'native_contract_r2_settings_and_every_ring_check_remains_unchanged':True,'strict_reference_acceptance':'FAIL unchanged','fullfill_contact_source_DRC_current':'OPEN','native_jobs':0,'candidate_or_host_written':False,'adopted':False,'helper_sha256':sha(__file__)};(out/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(json.dumps({'receipt_file':str(out/'receipt.json'),'receipt_sha256':sha(out/'receipt.json')}),flush=True)
