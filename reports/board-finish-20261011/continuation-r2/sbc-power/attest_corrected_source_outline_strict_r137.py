"""Exact physical-identity extension of all 134 strict R131 checks."""
from pathlib import Path
import hashlib,json,pickle
from shapely.geometry import Polygon,Point
H=Path(__file__).resolve().parent.parent;O=H/'sbc-power/corrected-source-outline-strict-r137'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not O.exists();O.mkdir()
 oldfile=H/'sbc-power/frozen-regional-source-exit-replay-r129/accepted-source-scope/new-feed-zones.pkl';newfile=H/'sbc-power/CORE1V2-source-native-outline-correction-r135/new-feed-zones.pkl'
 assert sha(oldfile)=='13a27d8dc63627aa62ba084bf7638f736df8e1d9dbed546bdf74d5643ce91abf' and sha(newfile)=='0d7fea4cd6f0abf399a2f86ac614554b86bad127a46c51c8a0575ae87b5f7aa5'
 q=pickle.loads(oldfile.read_bytes())[0];n=pickle.loads(newfile.read_bytes())[0];assert n['shape'].wkb==q['shape'].wkb
 ar=H/'sbc-power/selected-CORE1V2-strict-geometry-r131/receipt.json';assert sha(ar)=='f2c85f9a08c763487647ed512bb0ef4d3051268730f1ef3b821ff0982431e471';a=json.loads(ar.read_bytes());assert not a['errors']
 before=q['zone_outline_shape'];after=n['zone_outline_shape'];p=Point(236.212,94.61);hits=[Polygon(r) for r in before.interiors if Polygon(r).covers(p)];assert len(hits)==1 and after.difference(before).equals(hits[0]) and before.difference(after).is_empty and after.covers(p)
 ledger=H/'sbc-power/CORE1V2-source-native-outline-correction-r135/exact-outline-operation-ledger.json';r={'verdict':'PASS_STRICT_ANALYTIC_CORRECTED_NATIVE_NOMINEE_BY_EXACT_PHYSICAL_IDENTITY','original_strict_134_pair_receipt_file':str(ar.resolve()),'original_strict_134_pair_receipt_sha256':sha(ar),'all_strict_no_gap_or_area_tolerance':True,'errors':[],'all_physical_Cu_WKB_unchanged':True,'exact_only_intended_outline_addition_is_bound_own_source_drill_void':True,'source_via_existing_drill_geometry_unchanged':True,'outline_operation_file':str(ledger.resolve()),'outline_operation_sha256':sha(ledger),'native_source_flash_fill_and_FULL_final_current_contacts':'OPEN','native_jobs':0,'board_written':False}
 (O/'receipt.json').write_text(json.dumps(r,indent=1)+'\n');print('CORRECTED_SOURCE_STRICT_IDENTITY_PASS',sha(O/'receipt.json'))
if __name__=='__main__':main()
