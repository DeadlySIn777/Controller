"""Fresh independent literal clearance gate with exact nm boundary proofs."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'audit_SAFE_true_geometry_r152.py').read_text()
s=s.replace("O=H/'sbc-power/SAFE-independent-true-geometry-r152'","O=H/'sbc-power/SAFE-repaired-independent-true-geometry-r161'")
needle="mp=Path(sys.argv[1]);old,h,b,z,current=pickle.loads(mp.read_bytes());errors=[];counts={};web=[]"
replacement='''mp=Path(sys.argv[1]);old,h,b,z,current=pickle.loads(mp.read_bytes());errors=[];counts={};web=[]
 assert not [t['uuid'] for t in h['tracks'] if t.get('m') is not None], 'Arc geometry needs an independent exact curve gate'
 exact_file=H/'sbc-power/SAFE-exact-integer-boundary-apertures-r155/receipt.json'
 assert sha(exact_file)=='8010edc2e497ccceaad0980136606f137aa095eb7bda8457f549589c890f3045'
 exact=json.loads(exact_file.read_bytes());assert exact['verdict']=='PASS_EXACT_INTEGER_NM_BOUNDARY_APERTURES'
 exact_pairs={(r['via_exact_record']['uuid'],r['pad_UUID']):r for r in exact['rows']};exact_rows=[]'''
assert needle in s;s=s.replace(needle,replacement)
needle="  if gap<req:errors.append({'gate':kind,'owned_UUID':q['uuid'],'other_UUID':other['uuid'],'actual_gap_mm':gap,'required_gap_mm':req,**extra})"
replacement='''  if gap<req:
   pair=(q['uuid'],other['uuid'])
   if kind=='NEW_via_hole_every_SMD_Cu' and pair in exact_pairs:
    row=exact_pairs[pair];assert q==row['via_exact_record'] and req==.275
    observed={(l,hashlib.sha256(sh.wkb).hexdigest()) for l,rs in other['layers'].items() for sh in C.poly(rs)}
    expected={(r['layer'],r['actual_native_polygon_sha256']) for r in row['actual_native_polygon_pieces']}
    assert observed==expected and row['PASS'] and all(r['exact_squared_comparison_PASS'] for r in row['actual_native_polygon_pieces'])
    exact_rows.append({'via_UUID':q['uuid'],'pad_UUID':other['uuid'],'frozen_exact_integer_nm_proof_sha256':sha(exact_file),'unchanged_native_point_drill_and_all_SMD_polygon_hashes_match':True,'no_epsilon_or_geometry_change':True})
   else:errors.append({'gate':kind,'owned_UUID':q['uuid'],'other_UUID':other['uuid'],'actual_gap_mm':gap,'required_gap_mm':req,**extra})'''
assert needle in s;s=s.replace(needle,replacement)
s=s.replace("'strict_true_track_caps_native_pad_polygons_actual_layer_annuli_all_drills':True", "'strict_true_track_caps_native_pad_polygons_actual_layer_annuli_all_drills':True,'exact_integer_boundary_aperture_rows':exact_rows,'exact_integer_boundary_aperture_receipt_sha256':sha(exact_file),'no_arc_approximation_assertion_passed':True")
exec(compile(s,str(p/'audit_SAFE_true_geometry_r152.py'),'exec'))
